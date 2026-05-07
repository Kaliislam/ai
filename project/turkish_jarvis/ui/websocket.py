"""FastAPI WebSocket handler — TurkishJARVIS real-time chat."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket bağlantılarını ve session'ları yönetir."""

    def __init__(
        self,
        llm_client: Any | None = None,
        conversation_store: Any | None = None,
        episodic_memory: Any | None = None,
        long_term_memory: Any | None = None,
        rag: Any | None = None,
        tool_registry: Any | None = None,
        personality_builder: Any | None = None,
        stt_engine: Any | None = None,
        tts_engine: Any | None = None,
    ):
        self.llm = llm_client
        self.conv_store = conversation_store
        self.episodic = episodic_memory
        self.longterm = long_term_memory
        self.rag = rag
        self.tools = tool_registry
        self.personality = personality_builder
        self.stt = stt_engine
        self.tts = tts_engine

        # active_connections: websocket -> {session_id, settings}
        self.active_connections: dict[WebSocket, dict] = {}

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        session_id = str(uuid.uuid4())
        self.active_connections[websocket] = {
            "session_id": session_id,
            "voice_enabled": False,
            "personality": "professional_friendly",
        }
        logger.info("WebSocket connected: session=%s", session_id)
        await self._send_json(websocket, {
            "type": "connected",
            "session_id": session_id,
            "message": "Jarvis WebSocket bağlantısı kuruldu.",
        })

    async def disconnect(self, websocket: WebSocket) -> None:
        info = self.active_connections.pop(websocket, {})
        logger.info("WebSocket disconnected: session=%s", info.get("session_id"))

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def handle(self, websocket: WebSocket) -> None:
        """Bir WebSocket bağlantısını lifecycle boyunca yönetir."""
        await self.connect(websocket)
        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    await self._send_json(websocket, {
                        "type": "error",
                        "error": "Geçersiz JSON formatı.",
                    })
                    continue

                msg_type = payload.get("type", "message")

                if msg_type == "message":
                    await self._handle_text_message(websocket, payload)
                elif msg_type == "audio":
                    await self._handle_audio_message(websocket, payload)
                elif msg_type == "settings":
                    await self._handle_settings(websocket, payload)
                elif msg_type == "ping":
                    await self._send_json(websocket, {"type": "pong"})
                else:
                    await self._send_json(websocket, {
                        "type": "error",
                        "error": f"Bilinmeyen mesaj tipi: {msg_type}",
                    })

        except WebSocketDisconnect:
            logger.info("Client disconnected normally.")
        except Exception as exc:
            logger.exception("WebSocket handler error")
            try:
                await self._send_json(websocket, {
                    "type": "error",
                    "error": f"Sunucu hatası: {exc}",
                })
            except Exception:
                pass
        finally:
            await self.disconnect(websocket)

    # ------------------------------------------------------------------
    # Message handlers
    # ------------------------------------------------------------------

    async def _handle_text_message(
        self,
        websocket: WebSocket,
        payload: dict,
    ) -> None:
        text = payload.get("text", "")
        session_id = payload.get("session_id") or self._get_session(websocket)
        enable_voice = payload.get("enable_voice", False)

        if not text or not text.strip():
            await self._send_json(websocket, {
                "type": "error",
                "error": "Boş mesaj.",
            })
            return

        # Processing indicator
        await self._send_json(websocket, {"type": "status", "status": "thinking"})

        try:
            result = await self._process_message(
                message=text.strip(),
                session_id=session_id,
                enable_voice=enable_voice,
            )
        except Exception as exc:
            logger.exception("WS text processing error")
            await self._send_json(websocket, {
                "type": "error",
                "error": f"İşleme hatası: {exc}",
            })
            return

        response_payload = {
            "type": "response",
            "text": result.get("response", ""),
            "session_id": result.get("session_id", session_id),
            "tool_calls_used": result.get("tool_calls_used", []),
        }

        if result.get("voice_url"):
            response_payload["voice_url"] = result["voice_url"]
            response_payload["voice_available"] = True

        await self._send_json(websocket, response_payload)

    async def _handle_audio_message(
        self,
        websocket: WebSocket,
        payload: dict,
    ) -> None:
        """Base64 ses verisi alır, STT ile metne çevirir, işler."""
        import base64
        import os
        import tempfile

        audio_b64 = payload.get("audio", "")
        session_id = payload.get("session_id") or self._get_session(websocket)
        enable_voice = payload.get("enable_voice", True)
        mime_type = payload.get("mime_type", "audio/wav")

        if not audio_b64:
            await self._send_json(websocket, {
                "type": "error",
                "error": "Boş ses verisi.",
            })
            return

        await self._send_json(websocket, {"type": "status", "status": "transcribing"})

        # Decode and save temp file
        ext = ".wav" if "wav" in mime_type else ".webm"
        try:
            audio_bytes = base64.b64decode(audio_b64)
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
        except Exception as exc:
            await self._send_json(websocket, {
                "type": "error",
                "error": f"Ses dosyası decode hatası: {exc}",
            })
            return

        # STT
        transcript = ""
        try:
            if self.stt is not None:
                transcript = await self.stt.transcribe(tmp_path)
            else:
                transcript = "[Sesli mesaj — STT mevcut değil]"
        except Exception as exc:
            logger.exception("WS STT error")
            await self._send_json(websocket, {
                "type": "error",
                "error": f"Ses tanıma hatası: {exc}",
            })
            return
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        # Send transcription back
        await self._send_json(websocket, {
            "type": "transcription",
            "text": transcript,
        })

        await self._send_json(websocket, {"type": "status", "status": "thinking"})

        try:
            result = await self._process_message(
                message=transcript,
                session_id=session_id,
                enable_voice=enable_voice,
            )
        except Exception as exc:
            logger.exception("WS audio processing error")
            await self._send_json(websocket, {
                "type": "error",
                "error": f"İşleme hatası: {exc}",
            })
            return

        response_payload = {
            "type": "response",
            "text": result.get("response", ""),
            "session_id": result.get("session_id", session_id),
            "tool_calls_used": result.get("tool_calls_used", []),
        }

        if result.get("voice_url"):
            response_payload["voice_url"] = result["voice_url"]
            response_payload["voice_available"] = True

        await self._send_json(websocket, response_payload)

    async def _handle_settings(
        self,
        websocket: WebSocket,
        payload: dict,
    ) -> None:
        settings = payload.get("settings", {})
        conn = self.active_connections.setdefault(websocket, {})
        if "voice_enabled" in settings:
            conn["voice_enabled"] = bool(settings["voice_enabled"])
        if "personality" in settings:
            conn["personality"] = settings["personality"]
        await self._send_json(websocket, {
            "type": "settings_ack",
            "settings": conn,
        })

    # ------------------------------------------------------------------
    # Core processing (same pipeline as HTTP /chat)
    # ------------------------------------------------------------------

    async def _process_message(
        self,
        message: str,
        session_id: str,
        enable_voice: bool = False,
    ) -> dict:
        if not self.llm:
            return {
                "response": "LLM istemcisi henüz yapılandırılmamış.",
                "session_id": session_id,
                "tool_calls_used": [],
                "voice_url": None,
            }

        if not session_id:
            session_id = str(uuid.uuid4())

        # 1. History
        history: list[dict] = []
        if self.conv_store is not None:
            try:
                history = self.conv_store.get_history(session_id, limit=20)
            except Exception:
                logger.exception("WS history fetch error")

        # 2. Episodic
        episodic_context = ""
        if self.episodic is not None:
            try:
                memories = self.episodic.search(message, k=3)
                if memories:
                    episodic_context = "\n".join(
                        f"- {m.get('text', m)}" for m in memories
                    )
            except Exception:
                logger.exception("WS episodic search error")

        # 3. Preferences
        user_prefs: dict = {}
        if self.longterm is not None:
            try:
                user_prefs = self.longterm.get_all_preferences(session_id)
            except Exception:
                logger.exception("WS preferences fetch error")

        # 4. Tools
        tool_schemas: list[dict] = []
        if self.tools is not None:
            try:
                tool_schemas = self.tools.get_schemas()
            except Exception:
                logger.exception("WS tool schemas error")

        # 5. System prompt
        system_prompt = "Sen TurkishJARVIS'sin. Kullanıcıya yardımcı ol."
        if self.personality is not None:
            try:
                system_prompt = self.personality.build(
                    user_preferences=user_prefs,
                    memory_context=episodic_context,
                    tool_schemas=tool_schemas,
                )
            except Exception:
                logger.exception("WS system prompt build error")

        # 6. LLM messages
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})

        # 7. LLM call
        try:
            llm_result = await self.llm.chat(messages, tools=tool_schemas or None)
        except Exception as exc:
            logger.exception("WS LLM chat error")
            raise RuntimeError(f"LLM hatası: {exc}")

        content = llm_result.get("content", "")
        tool_calls = llm_result.get("tool_calls") or []
        tool_names_used: list[str] = []

        # 8. Tool execution
        if tool_calls and self.tools is not None:
            for tc in tool_calls:
                name = tc.get("function", {}).get("name") if isinstance(tc, dict) else getattr(tc, "function", {}).get("name", "")
                if not name:
                    continue
                arguments = tc.get("function", {}).get("arguments", {}) if isinstance(tc, dict) else getattr(getattr(tc, "function", None), "arguments", {})
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                try:
                    tool_result = self.tools.execute(name, arguments)
                    tool_names_used.append(name)
                    messages.append({
                        "role": "tool",
                        "name": name,
                        "content": str(tool_result),
                    })
                except Exception:
                    logger.exception("WS tool execution error: %s", name)
                    messages.append({
                        "role": "tool",
                        "name": name,
                        "content": "Araç çalıştırma hatası.",
                    })

            try:
                llm_result = await self.llm.chat(messages, tools=tool_schemas or None)
                content = llm_result.get("content", "")
            except Exception as exc:
                logger.exception("WS LLM re-chat error")
                content = f"Araç sonuçları işlenirken hata: {exc}"

        # 9. Save conversation
        if self.conv_store is not None:
            try:
                self.conv_store.add_message(session_id, "user", message)
                self.conv_store.add_message(session_id, "assistant", content, tool_calls=tool_names_used)
            except Exception:
                logger.exception("WS conversation save error")

        # 10. TTS
        voice_url: str | None = None
        if enable_voice and self.tts is not None and content:
            try:
                voice_path = await self.tts.synthesize(content)
                if voice_path and os.path.exists(voice_path):
                    voice_url = voice_path
            except Exception:
                logger.exception("WS TTS error")

        return {
            "response": content,
            "session_id": session_id,
            "tool_calls_used": tool_names_used,
            "voice_url": voice_url,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_session(self, websocket: WebSocket) -> str:
        return self.active_connections.get(websocket, {}).get("session_id", str(uuid.uuid4()))

    async def _send_json(self, websocket: WebSocket, data: dict) -> None:
        try:
            await websocket.send_json(data)
        except Exception:
            logger.warning("Failed to send WS message")
