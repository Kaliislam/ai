# -*- coding: utf-8 -*-
"""Voice Activity Detection wrapper using Silero VAD."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import torch

logger = logging.getLogger(__name__)

# Global cache so the model is loaded only once
_vad_model: torch.jit.ScriptModule | None = None
_vad_utils: Any = None


def _load_vad_model() -> tuple[torch.jit.ScriptModule, Any]:
    """Lazy-load Silero VAD model and utilities."""
    global _vad_model, _vad_utils  # noqa: PLW0603
    if _vad_model is None:
        logger.info("Loading Silero VAD model…")
        model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            onnx=False,
        )
        _vad_model = model
        _vad_utils = utils
    return _vad_model, _vad_utils


class VADClient:
    """Simple wrapper around Silero VAD."""

    def __init__(self, threshold: float = 0.5, sample_rate: int = 16000) -> None:
        self.threshold = threshold
        self.sample_rate = sample_rate
        self._model: torch.jit.ScriptModule | None = None
        self._utils: Any = None

    def _ensure_model(self) -> tuple[torch.jit.ScriptModule, Any]:
        if self._model is None:
            self._model, self._utils = _load_vad_model()
        return self._model, self._utils

    def is_speech(
        self,
        audio: np.ndarray | torch.Tensor | bytes,
    ) -> tuple[bool, float]:
        """Return (speech_detected, confidence) for the given audio chunk.

        *audio* may be a NumPy array, torch Tensor, or raw PCM bytes
        (int16).  The chunk must be 30 ms or longer at the configured
        sample rate.
        """
        model, _ = self._ensure_model()

        # Normalise input to torch Tensor of floats
        if isinstance(audio, bytes):
            audio = np.frombuffer(audio, dtype=np.int16)
        if isinstance(audio, np.ndarray):
            tensor = torch.from_numpy(audio.astype(np.float32))
        elif isinstance(audio, torch.Tensor):
            tensor = audio
        else:
            raise TypeError(f"Unsupported audio type: {type(audio)}")

        # Ensure mono, contiguous, float32
        if tensor.ndim > 1:
            tensor = tensor.squeeze()
        tensor = tensor.float()

        with torch.inference_mode():
            confidence = model(tensor, self.sample_rate).item()

        return confidence > self.threshold, confidence

    def get_speech_timestamps(
        self,
        audio: np.ndarray | torch.Tensor | bytes,
    ) -> list[dict[str, float]]:
        """Return list of speech timestamps {'start': s, 'end': s}."""
        model, utils = self._ensure_model()
        get_ts = utils[0]

        if isinstance(audio, bytes):
            audio = np.frombuffer(audio, dtype=np.int16)
        if isinstance(audio, np.ndarray):
            tensor = torch.from_numpy(audio.astype(np.float32))
        elif isinstance(audio, torch.Tensor):
            tensor = audio
        else:
            raise TypeError(f"Unsupported audio type: {type(audio)}")

        if tensor.ndim > 1:
            tensor = tensor.squeeze()
        tensor = tensor.float()

        with torch.inference_mode():
            timestamps = get_ts(
                tensor,
                model,
                threshold=self.threshold,
                sampling_rate=self.sample_rate,
            )
        return [{"start": float(ts["start"]), "end": float(ts["end"])} for ts in timestamps]
