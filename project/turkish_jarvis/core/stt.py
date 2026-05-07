# -*- coding: utf-8 -*-
"""Speech-to-Text wrapper using faster-whisper."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from faster_whisper import WhisperModel

from turkish_jarvis.config import JARVISConfig, get_config

logger = logging.getLogger(__name__)


class STTClient:
    """Async-friendly wrapper around faster-whisper."""

    def __init__(self, config: JARVISConfig | None = None) -> None:
        self.config = config or get_config()
        self._model: WhisperModel | None = None

    def _load_model(self) -> WhisperModel:
        """Lazy-load the Whisper model."""
        if self._model is None:
            logger.info(
                "Loading STT model '%s' (device=%s, compute_type=%s)",
                self.config.stt_model,
                self.config.stt_device,
                self.config.stt_compute_type,
            )
            self._model = WhisperModel(
                self.config.stt_model,
                device=self.config.stt_device,
                compute_type=self.config.stt_compute_type,
            )
        return self._model

    def transcribe_file(
        self,
        audio_path: str,
        language: str = "tr",
        beam_size: int = 5,
    ) -> dict[str, Any]:
        """Transcribe an audio file to text.

        Returns a dict with keys: text, segments, info.
        """
        model = self._load_model()
        segments, info = model.transcribe(
            audio_path,
            language=language,
            beam_size=beam_size,
            vad_filter=True,
        )
        text_parts: list[str] = []
        segment_list: list[dict[str, Any]] = []
        for seg in segments:
            text_parts.append(seg.text.strip())
            segment_list.append(
                {
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text.strip(),
                }
            )
        return {
            "text": " ".join(text_parts).strip(),
            "segments": segment_list,
            "info": {
                "language": info.language,
                "language_probability": info.language_probability,
            },
        }

    async def transcribe(
        self,
        audio_path: str,
        language: str = "tr",
        beam_size: int = 5,
    ) -> str:
        """Async wrapper that returns only the transcribed text."""
        result = await asyncio.to_thread(
            self.transcribe_file,
            audio_path,
            language=language,
            beam_size=beam_size,
        )
        return result.get("text", "")
