# -*- coding: utf-8 -*-
"""Text-to-Speech wrapper using Piper CLI via subprocess."""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from turkish_jarvis.config import JARVISConfig, get_config

logger = logging.getLogger(__name__)


class TTSClient:
    """Wrapper that calls the `piper` CLI to synthesise speech."""

    def __init__(self, config: JARVISConfig | None = None) -> None:
        self.config = config or get_config()
        self.model_path = Path(self.config.tts_model_path)
        self.config_path = Path(self.config.tts_config_path)

    def _validate(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(f"Piper model not found: {self.model_path}")
        if not self.config_path.exists():
            raise FileNotFoundError(f"Piper config not found: {self.config_path}")

    async def synthesize(
        self,
        text: str,
        output_path: str | None = None,
        speaker_id: int | None = None,
    ) -> str:
        """Asynchronously synthesize text and return the path to the WAV file.

        If *output_path* is not given a temporary file is created.
        """
        return await asyncio.to_thread(
            self._synthesize_sync,
            text,
            output_path,
            speaker_id,
        )

    def _synthesize_sync(
        self,
        text: str,
        output_path: str | None = None,
        speaker_id: int | None = None,
    ) -> str:
        """Synchronous implementation of synthesize."""
        self._validate()

        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)

        cmd: list[str] = [
            "piper",
            "-m", str(self.model_path),
            "-c", str(self.config_path),
            "-f", output_path,
        ]
        if speaker_id is not None:
            cmd.extend(["-s", str(speaker_id)])

        logger.debug("TTS command: %s", " ".join(cmd))

        try:
            subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            logger.error("Piper TTS failed: %s", exc.stderr.decode("utf-8", errors="ignore"))
            raise RuntimeError("TTS synthesis failed") from exc

        return output_path

    async def synthesize_to_bytes(self, text: str, speaker_id: int | None = None) -> bytes:
        """Asynchronously synthesize text and return raw WAV bytes."""
        return await asyncio.to_thread(
            self._synthesize_to_bytes_sync,
            text,
            speaker_id,
        )

    def _synthesize_to_bytes_sync(self, text: str, speaker_id: int | None = None) -> bytes:
        """Synchronous implementation of synthesize_to_bytes."""
        self._validate()

        cmd: list[str] = [
            "piper",
            "-m", str(self.model_path),
            "-c", str(self.config_path),
        ]
        if speaker_id is not None:
            cmd.extend(["-s", str(speaker_id)])

        result = subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            capture_output=True,
            check=True,
        )
        return result.stdout
