# -*- coding: utf-8 -*-
"""Wake-word detection stub using openWakeWord."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

from turkish_jarvis.config import JARVISConfig, get_config

logger = logging.getLogger(__name__)


class WakeWordClient:
    """Stub / lightweight wrapper around openWakeWord inference.

    The real library (`openwakeword`) requires heavy dependencies (ONNX,
    tflite).  This wrapper keeps the same API and will transparently
    delegate to the library when it is importable, otherwise it falls
    back to a no-op stub so the rest of the pipeline can still be
    tested and developed.
    """

    def __init__(self, config: JARVISConfig | None = None) -> None:
        self.config = config or get_config()
        self.model_path = Path(self.config.wakeword_model)
        self.threshold: float = self.config.wakeword_threshold
        self._predictor: Any = None
        self._enabled: bool = False

    def _load(self) -> None:
        """Attempt to load the real openWakeWord predictor."""
        if self._predictor is not None:
            return
        try:
            # openwakeword is an optional heavy dependency
            from openwakeword import Model  # type: ignore[import-untyped]

            if not self.model_path.exists():
                logger.warning("Wake-word model not found: %s", self.model_path)
                return

            self._predictor = Model(
                wakeword_model_paths=[str(self.model_path)],
                inference_framework="tflite",
            )
            self._enabled = True
            logger.info("openWakeWord loaded from %s", self.model_path)
        except ImportError:
            logger.warning(
                "openwakeword not installed; wake-word detection is disabled"
            )
        except Exception:  # noqa: BLE001
            logger.exception("Failed to load openWakeWord model")

    def detect(
        self,
        audio_frame: np.ndarray,
        sample_rate: int = 16000,
    ) -> dict[str, Any]:
        """Return detection result for a single audio frame.

        Result format::

            {
                "detected": bool,
                "confidence": float,   # 0.0 … 1.0
                "model": str | None,
            }
        """
        self._load()

        if not self._enabled or self._predictor is None:
            return {"detected": False, "confidence": 0.0, "model": None}

        try:
            predictions = self._predictor.predict(audio_frame)
            if not predictions:
                return {"detected": False, "confidence": 0.0, "model": None}

            # predictions is a dict {model_name: score}
            best_model = max(predictions, key=predictions.get)  # type: ignore[arg-type]
            confidence = float(predictions[best_model])
            detected = confidence > self.threshold
            return {
                "detected": detected,
                "confidence": confidence,
                "model": best_model,
            }
        except Exception:  # noqa: BLE001
            logger.exception("Wake-word inference failed")
            return {"detected": False, "confidence": 0.0, "model": None}
