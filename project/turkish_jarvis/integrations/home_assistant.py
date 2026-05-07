"""Home Assistant Integration.

Provides REST API access and WebSocket real-time event streaming.
Exposes Home Assistant entities as LLM-callable tools.

Environment / Config:
    HA_URL      – Home Assistant base URL (default: http://homeassistant.local:8123)
    HA_TOKEN    – Long-lived access token
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class HAEntity:
    """Represents a Home Assistant entity."""

    entity_id: str
    state: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    last_changed: Optional[str] = None
    last_updated: Optional[str] = None
    context_id: Optional[str] = None

    @property
    def domain(self) -> str:
        return self.entity_id.split(".")[0]

    @property
    def friendly_name(self) -> str:
        return self.attributes.get("friendly_name", self.entity_id)

    @property
    def is_on(self) -> bool:
        return self.state.lower() in ("on", "true", "1", "home", "open", "playing")


@dataclass
class HAEvent:
    """Represents a Home Assistant event."""

    event_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    origin: Optional[str] = None
    time_fired: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class HomeAssistantClient:
    """Async Home Assistant REST + WebSocket client.

    Usage:
        ha = HomeAssistantClient(url="http://localhost:8123", token="YOUR_TOKEN")
        await ha.connect()
        lights = ha.list_entities(domain="light")
        await ha.turn_on("light.salon")
        await ha.disconnect()
    """

    def __init__(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        self.url = (url or os.getenv("HA_URL", "http://homeassistant.local:8123")).rstrip("/")
        self.token = token or os.getenv("HA_TOKEN", "")
        self.timeout = timeout
        self._session: Optional[Any] = None
        self._ws: Optional[Any] = None
        self._ws_task: Optional[asyncio.Task[None]] = None
        self._state_cache: Dict[str, HAEntity] = {}
        self._event_callbacks: List[Callable[[HAEvent], Coroutine[Any, Any, None]]] = []
        self._connected = False
        self._msg_id = 1

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def _ensure_session(self) -> None:
        if self._session is None:
            try:
                import aiohttp  # type: ignore[import-untyped]
            except ImportError as exc:
                raise RuntimeError("aiohttp is required for HomeAssistantClient") from exc
            self._session = aiohttp.ClientSession()

    async def _rest_get(self, path: str) -> Any:
        await self._ensure_session()
        assert self._session is not None
        async with self._session.get(
            f"{self.url}{path}", headers=self._headers(), timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _rest_post(self, path: str, payload: Dict[str, Any]) -> Any:
        await self._ensure_session()
        assert self._session is not None
        async with self._session.post(
            f"{self.url}{path}",
            headers=self._headers(),
            json=payload,
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Establish REST session and WebSocket connection."""
        await self._ensure_session()
        # Preload entity states
        await self.refresh_states()
        # WebSocket
        ws_url = self.url.replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket"
        self._ws = await self._session.ws_connect(ws_url)
        # Auth
        auth_msg = await self._ws.receive()
        if auth_msg.type == aiohttp.WSMsgType.TEXT:  # type: ignore[name-defined]
            data = json.loads(auth_msg.data)
            if data.get("type") == "auth_required":
                await self._ws.send_json({"type": "auth", "access_token": self.token})
                auth_result = await self._ws.receive()
                result = json.loads(auth_result.data)
                if result.get("type") != "auth_ok":
                    raise RuntimeError(f"HA WebSocket auth failed: {result}")
        # Subscribe to state-changed events
        await self._ws.send_json({
            "id": self._next_id(),
            "type": "subscribe_events",
            "event_type": "state_changed",
        })
        self._ws_task = asyncio.create_task(self._ws_loop())
        self._connected = True
        logger.info("Home Assistant WebSocket connected")

    async def disconnect(self) -> None:
        """Close connections."""
        if self._ws_task is not None:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
        if self._ws is not None:
            await self._ws.close()
        if self._session is not None:
            await self._session.close()
            self._session = None
        self._connected = False

    def _next_id(self) -> int:
        i = self._msg_id
        self._msg_id += 1
        return i

    # ------------------------------------------------------------------
    # WebSocket loop
    # ------------------------------------------------------------------

    async def _ws_loop(self) -> None:
        while True:
            try:
                msg = await self._ws.receive()
            except Exception as exc:
                logger.error("HA WebSocket error: %s", exc)
                break
            if msg.type in (
                aiohttp.WSMsgType.CLOSED,  # type: ignore[name-defined]
                aiohttp.WSMsgType.CLOSING,  # type: ignore[name-defined]
                aiohttp.WSMsgType.ERROR,  # type: ignore[name-defined]
            ):
                break
            if msg.type == aiohttp.WSMsgType.TEXT:  # type: ignore[name-defined]
                try:
                    data = json.loads(msg.data)
                except json.JSONDecodeError:
                    continue
                self._handle_ws_message(data)

    def _handle_ws_message(self, data: Dict[str, Any]) -> None:
        msg_type = data.get("type")
        if msg_type == "event":
            event = HAEvent(
                event_type=data.get("event", {}).get("event_type", ""),
                data=data.get("event", {}).get("data", {}),
                origin=data.get("event", {}).get("origin"),
                time_fired=data.get("event", {}).get("time_fired"),
                context=data.get("event", {}).get("context"),
            )
            # Update cache for state_changed
            if event.event_type == "state_changed":
                new_state = event.data.get("new_state")
                if new_state:
                    entity = self._dict_to_entity(new_state)
                    self._state_cache[entity.entity_id] = entity
            # Dispatch to callbacks
            for cb in self._event_callbacks:
                asyncio.create_task(cb(event))

    # ------------------------------------------------------------------
    # Entity helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _dict_to_entity(d: Dict[str, Any]) -> HAEntity:
        return HAEntity(
            entity_id=d["entity_id"],
            state=d.get("state", "unknown"),
            attributes=d.get("attributes", {}),
            last_changed=d.get("last_changed"),
            last_updated=d.get("last_updated"),
            context_id=d.get("context", {}).get("id") if isinstance(d.get("context"), dict) else None,
        )

    async def refresh_states(self) -> None:
        """Reload all entity states via REST."""
        states = await self._rest_get("/api/states")
        self._state_cache = {s["entity_id"]: self._dict_to_entity(s) for s in states}

    def list_entities(self, domain: Optional[str] = None) -> List[HAEntity]:
        """Return entities, optionally filtered by domain."""
        entities = list(self._state_cache.values())
        if domain:
            entities = [e for e in entities if e.domain == domain]
        return entities

    async def get_state(self, entity_id: str) -> HAEntity:
        """Read the current state of an entity (REST)."""
        data = await self._rest_get(f"/api/states/{entity_id}")
        entity = self._dict_to_entity(data)
        self._state_cache[entity_id] = entity
        return entity

    # ------------------------------------------------------------------
    # Control helpers
    # ------------------------------------------------------------------

    async def turn_on(self, entity_id: str, **service_data: Any) -> Dict[str, Any]:
        """Turn on a switch / light / etc."""
        domain = entity_id.split(".")[0]
        payload = {"entity_id": entity_id, **service_data}
        return await self._rest_post(f"/api/services/{domain}/turn_on", payload)

    async def turn_off(self, entity_id: str, **service_data: Any) -> Dict[str, Any]:
        """Turn off a switch / light / etc."""
        domain = entity_id.split(".")[0]
        payload = {"entity_id": entity_id, **service_data}
        return await self._rest_post(f"/api/services/{domain}/turn_off", payload)

    async def toggle(self, entity_id: str) -> Dict[str, Any]:
        """Toggle a switch / light / etc."""
        domain = entity_id.split(".")[0]
        return await self._rest_post(f"/api/services/{domain}/toggle", {"entity_id": entity_id})

    async def set_climate(
        self,
        entity_id: str,
        temperature: Optional[float] = None,
        hvac_mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Set climate entity temperature and/or mode."""
        payload: Dict[str, Any] = {"entity_id": entity_id}
        if temperature is not None:
            payload["temperature"] = temperature
        if hvac_mode is not None:
            payload["hvac_mode"] = hvac_mode
        return await self._rest_post("/api/services/climate/set_temperature", payload)

    async def call_service(
        self,
        domain: str,
        service: str,
        service_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generic service call."""
        return await self._rest_post(
            f"/api/services/{domain}/{service}",
            service_data or {},
        )

    # ------------------------------------------------------------------
    # Event callbacks
    # ------------------------------------------------------------------

    def add_event_listener(
        self,
        callback: Callable[[HAEvent], Coroutine[Any, Any, None]],
    ) -> None:
        """Register an async callback for HA events."""
        self._event_callbacks.append(callback)

    def remove_event_listener(
        self,
        callback: Callable[[HAEvent], Coroutine[Any, Any, None]],
    ) -> None:
        """Unregister an async callback."""
        if callback in self._event_callbacks:
            self._event_callbacks.remove(callback)

    # ------------------------------------------------------------------
    # LLM Tool integration
    # ------------------------------------------------------------------

    def to_llm_tools(self) -> List[Dict[str, Any]]:
        """Export built-in Home Assistant actions as LLM tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "ha_turn_on",
                    "description": "Turn on a Home Assistant entity (light, switch, etc.)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "entity_id": {
                                "type": "string",
                                "description": "Entity ID, e.g. light.salon",
                            },
                        },
                        "required": ["entity_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "ha_turn_off",
                    "description": "Turn off a Home Assistant entity.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "entity_id": {
                                "type": "string",
                                "description": "Entity ID, e.g. light.salon",
                            },
                        },
                        "required": ["entity_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "ha_get_state",
                    "description": "Get the current state of a Home Assistant entity.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "entity_id": {
                                "type": "string",
                                "description": "Entity ID, e.g. sensor.temperature",
                            },
                        },
                        "required": ["entity_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "ha_list_lights",
                    "description": "List all light entities and their states.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "ha_list_sensors",
                    "description": "List all sensor entities and their states.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "ha_set_climate",
                    "description": "Set climate temperature and/or HVAC mode.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "entity_id": {"type": "string"},
                            "temperature": {"type": "number"},
                            "hvac_mode": {
                                "type": "string",
                                "enum": ["off", "heat", "cool", "auto", "dry", "fan_only"],
                            },
                        },
                        "required": ["entity_id"],
                    },
                },
            },
        ]

    async def dispatch_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Dispatch an LLM tool call to Home Assistant."""
        if name == "ha_turn_on":
            return await self.turn_on(arguments["entity_id"])
        if name == "ha_turn_off":
            return await self.turn_off(arguments["entity_id"])
        if name == "ha_get_state":
            ent = await self.get_state(arguments["entity_id"])
            return {"entity_id": ent.entity_id, "state": ent.state, "attributes": ent.attributes}
        if name == "ha_list_lights":
            return [
                {"entity_id": e.entity_id, "state": e.state, "name": e.friendly_name}
                for e in self.list_entities("light")
            ]
        if name == "ha_list_sensors":
            return [
                {"entity_id": e.entity_id, "state": e.state, "name": e.friendly_name}
                for e in self.list_entities("sensor")
            ]
        if name == "ha_set_climate":
            return await self.set_climate(
                arguments["entity_id"],
                temperature=arguments.get("temperature"),
                hvac_mode=arguments.get("hvac_mode"),
            )
        raise ValueError(f"Unknown HA tool: {name}")

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "HomeAssistantClient":
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Any],
        exc_val: Optional[Any],
        exc_tb: Optional[Any],
    ) -> None:
        await self.disconnect()
