"""MCP (Model Context Protocol) Client Implementation.

Supports STDIO and SSE transports for connecting to MCP servers.
Discovers tools, fetches schemas, and registers them into a local tool registry.

Example configuration (mcpServers):
    {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
        },
        "web_search": {
            "url": "http://localhost:3000/sse"
        }
    }

References:
    - https://github.com/modelcontextprotocol
"""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import sys
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Coroutine, Dict, List, Optional, Type

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class MCPToolSchema:
    """Represents a tool schema from an MCP server."""

    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str
    handler: Optional[Callable[..., Coroutine[Any, Any, Any]]] = None


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""

    name: str
    command: Optional[str] = None
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    url: Optional[str] = None
    timeout: float = 30.0


# ---------------------------------------------------------------------------
# Transport layer
# ---------------------------------------------------------------------------


class MCPTransport(ABC):
    """Abstract base for MCP transports."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish the transport connection."""

    @abstractmethod
    async def send(self, message: Dict[str, Any]) -> None:
        """Send a JSON-RPC message."""

    @abstractmethod
    async def receive(self) -> Optional[Dict[str, Any]]:
        """Receive a JSON-RPC message."""

    @abstractmethod
    async def close(self) -> None:
        """Close the transport."""


class StdioTransport(MCPTransport):
    """STDIO transport using subprocess pipes."""

    def __init__(self, command: str, args: List[str], env: Dict[str, str]) -> None:
        self.command = command
        self.args = args
        self.env = env
        self._process: Optional[asyncio.subprocess.Process] = None
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

    async def connect(self) -> None:
        env = {**sys.environ, **self.env}
        self._process = await asyncio.create_subprocess_exec(
            self.command,
            *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        self._reader = self._process.stdout
        self._writer = self._process.stdin
        logger.info("STDIO transport connected: %s %s", self.command, " ".join(self.args))

    async def send(self, message: Dict[str, Any]) -> None:
        if self._writer is None:
            raise RuntimeError("Transport not connected")
        payload = json.dumps(message, ensure_ascii=False) + "\n"
        self._writer.write(payload.encode("utf-8"))
        await self._writer.drain()

    async def receive(self) -> Optional[Dict[str, Any]]:
        if self._reader is None:
            raise RuntimeError("Transport not connected")
        try:
            line = await asyncio.wait_for(self._reader.readline(), timeout=30.0)
        except asyncio.TimeoutError:
            return None
        if not line:
            return None
        try:
            return json.loads(line.decode("utf-8"))
        except json.JSONDecodeError as exc:
            logger.warning("Malformed JSON from MCP server: %s", exc)
            return None

    async def close(self) -> None:
        if self._process is not None:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()
            self._process = None
        self._reader = None
        self._writer = None


class SseTransport(MCPTransport):
    """Server-Sent Events (SSE) transport over HTTP."""

    def __init__(self, url: str) -> None:
        self.url = url
        self._session: Optional[Any] = None
        self._event_source: Optional[Any] = None
        self._pending: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self._task: Optional[asyncio.Task[None]] = None
        self._closed = False

    async def connect(self) -> None:
        try:
            import aiohttp  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError("aiohttp is required for SSE transport") from exc

        self._session = aiohttp.ClientSession()
        resp = await self._session.get(self.url, headers={"Accept": "text/event-stream"})
        self._event_source = resp
        self._task = asyncio.create_task(self._read_loop(resp))
        logger.info("SSE transport connected: %s", self.url)

    async def _read_loop(self, resp: Any) -> None:
        buffer = ""
        async for chunk in resp.content.iter_chunked(1024):
            if self._closed:
                break
            buffer += chunk.decode("utf-8", errors="replace")
            while "\n\n" in buffer:
                block, buffer = buffer.split("\n\n", 1)
                event_data: Optional[str] = None
                for line in block.splitlines():
                    if line.startswith("data: "):
                        event_data = line[len("data: "):]
                if event_data:
                    try:
                        msg = json.loads(event_data)
                        await self._pending.put(msg)
                    except json.JSONDecodeError:
                        pass

    async def send(self, message: Dict[str, Any]) -> None:
        # SSE is read-only for events; POST backchannel if supported
        # Fallback: queue locally for caller to POST if needed
        logger.debug("SSE send not implemented in pure mode: %s", message)

    async def receive(self) -> Optional[Dict[str, Any]]:
        try:
            return await asyncio.wait_for(self._pending.get(), timeout=30.0)
        except asyncio.TimeoutError:
            return None

    async def close(self) -> None:
        self._closed = True
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._event_source is not None:
            await self._event_source.release()
        if self._session is not None:
            await self._session.close()


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class MCPClient:
    """Manages connections to multiple MCP servers and exposes their tools.

    Usage:
        config = {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
            },
            "web_search": {"url": "http://localhost:3000/sse"}
        }
        client = MCPClient(config)
        await client.connect_all()
        tools = client.list_tools()
        result = await client.call_tool("filesystem", "list_files", {"path": "/tmp"})
        await client.disconnect_all()
    """

    def __init__(
        self,
        servers_config: Dict[str, Dict[str, Any]],
        tool_registry: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.servers_config = servers_config
        self.tool_registry: Dict[str, Any] = tool_registry or {}
        self._transports: Dict[str, MCPTransport] = {}
        self._tools: Dict[str, List[MCPToolSchema]] = {}
        self._pending_requests: Dict[str, asyncio.Future[Dict[str, Any]]] = {}
        self._read_tasks: Dict[str, asyncio.Task[None]] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect_all(self) -> None:
        """Connect to every configured MCP server."""
        for name, cfg in self.servers_config.items():
            transport = self._create_transport(name, cfg)
            self._transports[name] = transport
            await transport.connect()
            self._read_tasks[name] = asyncio.create_task(self._receive_loop(name, transport))
            await self._initialize(name, transport)
            await self._discover_tools(name, transport)
            logger.info("MCP server '%s' connected with %d tools", name, len(self._tools.get(name, [])))

    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        for task in self._read_tasks.values():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        for transport in self._transports.values():
            await transport.close()
        self._transports.clear()
        self._read_tasks.clear()
        self._tools.clear()

    def _create_transport(self, name: str, cfg: Dict[str, Any]) -> MCPTransport:
        if "url" in cfg:
            return SseTransport(url=cfg["url"])
        return StdioTransport(
            command=cfg.get("command", ""),
            args=cfg.get("args", []),
            env=cfg.get("env", {}),
        )

    # ------------------------------------------------------------------
    # Protocol helpers
    # ------------------------------------------------------------------

    def _make_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": method,
            "params": params or {},
        }

    async def _send_and_wait(
        self,
        server_name: str,
        transport: MCPTransport,
        request: Dict[str, Any],
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        future: asyncio.Future[Dict[str, Any]] = asyncio.get_event_loop().create_future()
        self._pending_requests[request["id"]] = future
        await transport.send(request)
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            raise RuntimeError(f"MCP request {request['id']} timed out")
        finally:
            self._pending_requests.pop(request["id"], None)

    async def _receive_loop(self, server_name: str, transport: MCPTransport) -> None:
        while True:
            try:
                msg = await transport.receive()
            except Exception as exc:
                logger.error("MCP receive error on '%s': %s", server_name, exc)
                break
            if msg is None:
                break
            msg_id = msg.get("id")
            if msg_id and msg_id in self._pending_requests:
                future = self._pending_requests.pop(msg_id)
                if not future.done():
                    future.set_result(msg)
            # Log notifications
            if "method" in msg and "id" not in msg:
                logger.debug("MCP notification from '%s': %s", server_name, msg)

    # ------------------------------------------------------------------
    # Initialization & discovery
    # ------------------------------------------------------------------

    async def _initialize(self, server_name: str, transport: MCPTransport) -> None:
        req = self._make_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "turkish-jarvis", "version": "2.0.0"},
        })
        resp = await self._send_and_wait(server_name, transport, req)
        if "error" in resp:
            raise RuntimeError(f"MCP init error on '{server_name}': {resp['error']}")
        logger.debug("MCP server '%s' initialized: %s", server_name, resp.get("result", {}))

    async def _discover_tools(self, server_name: str, transport: MCPTransport) -> None:
        req = self._make_request("tools/list")
        resp = await self._send_and_wait(server_name, transport, req)
        if "error" in resp:
            logger.warning("Failed to list tools on '%s': %s", server_name, resp["error"])
            return
        tools = resp.get("result", {}).get("tools", [])
        schemas: List[MCPToolSchema] = []
        for t in tools:
            schema = MCPToolSchema(
                name=t["name"],
                description=t.get("description", ""),
                input_schema=t.get("inputSchema", {}),
                server_name=server_name,
            )
            schemas.append(schema)
        self._tools[server_name] = schemas
        self._register_in_registry(schemas)

    def _register_in_registry(self, schemas: List[MCPToolSchema]) -> None:
        """Register MCP tools into the local tool registry (dict-based)."""
        for schema in schemas:
            key = f"mcp_{schema.server_name}_{schema.name}"
            schema.handler = self._wrap_tool_handler(schema)
            self.tool_registry[key] = schema
            logger.debug("Registered MCP tool: %s", key)

    def _wrap_tool_handler(
        self, schema: MCPToolSchema
    ) -> Callable[..., Coroutine[Any, Any, Any]]:
        async def handler(**kwargs: Any) -> Any:
            return await self.call_tool(schema.server_name, schema.name, kwargs)
        return handler

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_tools(self) -> List[MCPToolSchema]:
        """Return all discovered tool schemas across all servers."""
        return [tool for tools in self._tools.values() for tool in tools]

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Any:
        """Call a tool on a specific MCP server."""
        transport = self._transports.get(server_name)
        if transport is None:
            raise RuntimeError(f"Server '{server_name}' is not connected")
        req = self._make_request("tools/call", {"name": tool_name, "arguments": arguments})
        resp = await self._send_and_wait(server_name, transport, req)
        if "error" in resp:
            raise RuntimeError(f"Tool call error: {resp['error']}")
        return resp.get("result", {})

    def get_tool_schema(self, server_name: str, tool_name: str) -> Optional[MCPToolSchema]:
        """Get schema for a specific tool."""
        for tool in self._tools.get(server_name, []):
            if tool.name == tool_name:
                return tool
        return None

    def to_llm_tools(self) -> List[Dict[str, Any]]:
        """Convert all discovered MCP tools to an LLM-compatible tool list.

        Compatible with OpenAI / Anthropic function-calling format.
        """
        tools: List[Dict[str, Any]] = []
        for schema in self.list_tools():
            tools.append({
                "type": "function",
                "function": {
                    "name": f"mcp_{schema.server_name}_{schema.name}",
                    "description": schema.description,
                    "parameters": schema.input_schema,
                },
            })
        return tools

    async def __aenter__(self) -> "MCPClient":
        await self.connect_all()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        await self.disconnect_all()
