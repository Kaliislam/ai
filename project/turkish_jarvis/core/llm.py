# -*- coding: utf-8 -*-
"""Ollama LLM async client with auto-detect, fallback, tool-calling and streaming."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import aiohttp

from turkish_jarvis.config import JARVISConfig, get_config

logger = logging.getLogger("jarvis.llm")


class LLMClient:
    """Async client for Ollama chat API with auto-detect and fallback support."""

    def __init__(self, config: JARVISConfig | None = None) -> None:
        self.config = config or get_config()
        self.base_url = self.config.ollama_base_url.rstrip("/")
        # Auto-detect best available model at startup
        self.model = self.config.auto_select_model()
        self.timeout = aiohttp.ClientTimeout(total=self.config.ollama_timeout)
        logger.info("🧠 LLMClient hazır: model=%s", self.model)

    async def _try_chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        stream: bool = False,
    ) -> dict[str, Any] | None:
        """Attempt a chat request with given model. Returns None on failure."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        if tools and not stream:
            payload["tools"] = tools

        url = f"{self.base_url}/api/chat"
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload) as response:
                    response.raise_for_status()
                    data = await response.json()
                    # Check for Ollama-level errors
                    if data.get("error"):
                        logger.warning("Ollama error with %s: %s", model, data["error"])
                        return None
                    return data
        except aiohttp.ClientResponseError as exc:
            if exc.status == 404:
                logger.warning("Model '%s' Ollama'da bulunamadı.", model)
            else:
                logger.warning("LLM request failed for %s: %s", model, exc)
            return None
        except Exception as exc:
            logger.warning("LLM request failed for %s: %s", model, exc)
            return None

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Send a chat request to Ollama with fallback chain.

        If the configured model fails, tries fallback models automatically.
        """
        # Try primary model first
        data = await self._try_chat(self.model, messages, tools, stream=False)
        if data is not None:
            return self._parse_response(data)

        # Try fallback models
        fallbacks = [m.strip() for m in self.config.ollama_fallback_models.split(",")]
        for fallback in fallbacks:
            if fallback == self.model:
                continue
            logger.info("🔄 Fallback deneniyor: %s", fallback)
            data = await self._try_chat(fallback, messages, tools, stream=False)
            if data is not None:
                logger.info("✅ Fallback başarılı: %s", fallback)
                # Update working model for subsequent calls
                self.model = fallback
                return self._parse_response(data)

        # All failed
        logger.error("❌ Tüm modeller başarısız: %s ve %s", self.model, fallbacks)
        return {
            "content": (
                "Üzgünüm efendim, LLM servisi şu anda yanıt vermiyor. "
                "Lütfen Ollama'nın çalıştığından emin olun: `ollama list`"
            ),
            "tool_calls": None,
        }

    def _parse_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse Ollama response into standard format."""
        message = data.get("message", {})
        content = message.get("content", "")
        tool_calls_raw = message.get("tool_calls")
        tool_calls: list[dict[str, Any]] | None = None
        if tool_calls_raw:
            tool_calls = [
                {
                    "name": tc.get("function", {}).get("name", ""),
                    "arguments": tc.get("function", {}).get("arguments", {}),
                }
                for tc in tool_calls_raw
            ]
        return {"content": content, "tool_calls": tool_calls}

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
    ) -> AsyncIterator[str]:
        """Stream chunks from Ollama chat API with fallback."""
        models_to_try = [self.model] + [
            m.strip() for m in self.config.ollama_fallback_models.split(",")
            if m.strip() != self.model
        ]

        for model in models_to_try:
            payload: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "stream": True,
            }
            url = f"{self.base_url}/api/chat"
            try:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.config.ollama_stream_timeout)
                ) as session:
                    async with session.post(url, json=payload) as response:
                        response.raise_for_status()
                        async for line in response.content:
                            if not line:
                                continue
                            try:
                                chunk = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            msg = chunk.get("message", {})
                            content = msg.get("content", "")
                            if content:
                                yield content
                            if chunk.get("done", False):
                                return  # Successful completion
                        return  # Stream ended without done flag
            except Exception as exc:
                logger.warning("Streaming failed for %s: %s", model, exc)
                continue

        # All models failed
        yield (
            "Üzgünüm efendim, LLM servisi şu anda yanıt vermiyor. "
            "Lütfen Ollama'nın çalıştığından emin olun."
        )

    async def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_executor: dict[str, Any],
    ) -> dict[str, Any]:
        """Chat loop that handles tool calls until a final text response."""
        # First turn
        response = await self.chat(messages, tools=tools)

        # Handle tool calls iteratively (max 5 rounds to prevent loops)
        max_rounds = 5
        for _ in range(max_rounds):
            if not response.get("tool_calls"):
                break
            for tc in response["tool_calls"]:
                name = tc.get("name", "")
                args = tc.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                func = tool_executor.get(name)
                if func is None:
                    result = f"Hata: '{name}' aracı bulunamadı."
                else:
                    try:
                        if asyncio.iscoroutinefunction(func):
                            if isinstance(args, dict):
                                result = await func(**args)
                            else:
                                result = await func(args)
                        else:
                            if isinstance(args, dict):
                                result = func(**args)
                            else:
                                result = func(args)
                    except Exception as exc:  # noqa: BLE001
                        result = f"'{name}' çalıştırılırken hata: {exc}"
                messages.append(
                    {
                        "role": "tool",
                        "name": name,
                        "content": str(result),
                    }
                )
            response = await self.chat(messages, tools=tools)
        return response

    def get_model_info(self) -> dict[str, Any]:
        """Return current model metadata."""
        from turkish_jarvis.config import USER_MODELS
        return USER_MODELS.get(self.model, {"name": self.model})
