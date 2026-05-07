# -*- coding: utf-8 -*-
"""Pipeline orchestrator that wires STT → LLM → TTS."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from turkish_jarvis.config import JARVISConfig, get_config
from turkish_jarvis.core.llm import LLMClient
from turkish_jarvis.core.stt import STTClient
from turkish_jarvis.core.tts import TTSClient

logger = logging.getLogger(__name__)


class Pipeline:
    """End-to-end voice/text pipeline.

    Typical flow::

        text_input -> LLM -> text_output (+ optional TTS)
        audio_input -> STT -> LLM -> text_output (+ TTS)
    """

    def __init__(
        self,
        llm: LLMClient | None = None,
        stt: STTClient | None = None,
        tts: TTSClient | None = None,
        config: JARVISConfig | None = None,
    ) -> None:
        self.config = config or get_config()
        self.llm = llm or LLMClient(self.config)
        self.stt = stt or STTClient(self.config)
        self.tts = tts or TTSClient(self.config)

    async def run(
        self,
        user_input: str,
        mode: str = "text",
        messages: list[dict[str, Any]] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_executor: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute the full pipeline.

        Parameters
        ----------
        user_input:
            Either plain text or a filesystem path to an audio file.
        mode:
            ``"text"`` | ``"voice"`` — voice mode also triggers TTS.
        messages:
            Previous conversation messages for context.
        tools:
            Tool schemas to hand to the LLM.
        tool_executor:
            Mapping ``name -> callable`` for executing returned tool calls.

        Returns
        -------
        dict with keys ``text`` (str), ``audio_path`` (str | None),
        and ``raw_response`` (dict).
        """
        messages = messages or []

        # ----- STT -----------------------------------------------------------
        if mode == "voice":
            logger.info("Running STT on %s", user_input)
            stt_result = await asyncio.to_thread(self.stt.transcribe_file, user_input)
            user_text = stt_result.get("text", "")
            logger.info("STT result: %s", user_text)
        else:
            user_text = user_input

        if not user_text.strip():
            return {
                "text": "Üzgünüm, bir şey anlayamadım.",
                "audio_path": None,
                "raw_response": {},
            }

        messages.append({"role": "user", "content": user_text})

        # ----- LLM -----------------------------------------------------------
        if tools and tool_executor:
            llm_response = await self.llm.chat_with_tools(
                messages,
                tools=tools,
                tool_executor=tool_executor,
            )
        else:
            llm_response = await self.llm.chat(messages, tools=tools)

        assistant_text = llm_response.get("content", "")

        # Store assistant reply in conversation history
        messages.append({"role": "assistant", "content": assistant_text})

        # ----- TTS -----------------------------------------------------------
        audio_path: str | None = None
        if mode == "voice" and assistant_text.strip():
            try:
                audio_path = self.tts.synthesize(assistant_text)
                logger.info("TTS output: %s", audio_path)
            except Exception:  # noqa: BLE001
                logger.exception("TTS synthesis failed")

        return {
            "text": assistant_text,
            "audio_path": audio_path,
            "raw_response": llm_response,
            "messages": messages,
        }

    async def stream(
        self,
        user_input: str,
        mode: str = "text",
        messages: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Non-streaming wrapper that collects chunks for compatibility.

        This is a convenience entry-point; true streaming should be
        handled directly via ``LLMClient.stream_chat`` in the UI layer.
        """
        messages = messages or []
        messages.append({"role": "user", "content": user_input})

        full_text_parts: list[str] = []
        async for chunk in self.llm.stream_chat(messages):
            full_text_parts.append(chunk)

        assistant_text = "".join(full_text_parts)
        messages.append({"role": "assistant", "content": assistant_text})

        audio_path: str | None = None
        if mode == "voice" and assistant_text.strip():
            try:
                audio_path = await self.tts.synthesize(assistant_text)
            except Exception:  # noqa: BLE001
                logger.exception("TTS synthesis failed")

        return {
            "text": assistant_text,
            "audio_path": audio_path,
            "messages": messages,
        }
