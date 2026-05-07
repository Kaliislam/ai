# -*- coding: utf-8 -*-
"""Configuration for TurkishJARVIS using Pydantic Settings.

Kullanıcının mevcut Ollama modellerine göre optimize edilmiş:
- qwen3-coder:30b  (default - Türkçe + tool calling + coding)
- llama3.1:70b     (yüksek performans modu - çok ağır)
- gemma4:latest    (hafif alternatif - 9.6GB)
- deepseek-r1:8b   (reasoning/math modu)
- mistral:latest   (genel amaçlı - 4.4GB)
- qwen3:4b         (hafif mod - 2.5GB)
- gemma3:4b        (ultra hafif - 3.3GB)
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from pydantic_settings import BaseSettings

logger = logging.getLogger("jarvis.config")


# ---------------------------------------------------------------------------
# Kullanıcının mevcut modelleri (bu sohbette bildirilen)
# ---------------------------------------------------------------------------
USER_MODELS: dict[str, dict[str, Any]] = {
    "llama3.1:70b": {
        "size": "40GB+",
        "vram": "48GB+",
        "ram": "64GB+",
        "strengths": ["en güçlü", "çok dilli", "tool calling"],
        "turkish": "iyi",
        "speed": "yavaş (~5-10 tok/s)",
        "tier": "premium",
    },
    "gemma4:latest": {
        "size": "9.6GB",
        "vram": "12GB+",
        "ram": "16GB+",
        "strengths": ["yeni", "verimli", "güçlü"],
        "turkish": "orta-iyi",
        "speed": "orta (~15-25 tok/s)",
        "tier": "recommended",
    },
    "deepseek-r1:8b": {
        "size": "5.2GB",
        "vram": "8GB+",
        "ram": "12GB+",
        "strengths": ["reasoning", "math", "logic"],
        "turkish": "temel",
        "speed": "hızlı (~25-40 tok/s)",
        "tier": "specialized",
    },
    "qwen3-coder:30b": {
        "size": "18GB",
        "vram": "20GB+",
        "ram": "24GB+",
        "strengths": ["Türkçe", "coding", "tool calling", "multilingual"],
        "turkish": "çok iyi",
        "speed": "orta-yavaş (~10-20 tok/s)",
        "tier": "recommended",  # Default olarak bu seçiliyor
    },
    "qwen3:4b": {
        "size": "2.5GB",
        "vram": "4GB+",
        "ram": "8GB+",
        "strengths": ["çok hafif", "Türkçe"],
        "turkish": "iyi",
        "speed": "çok hızlı (~40-60 tok/s)",
        "tier": "light",
    },
    "mistral:latest": {
        "size": "4.4GB",
        "vram": "6GB+",
        "ram": "10GB+",
        "strengths": ["genel amaçlı", "hızlı", "güçlü"],
        "turkish": "orta",
        "speed": "hızlı (~30-50 tok/s)",
        "tier": "balanced",
    },
    "gemma3:4b": {
        "size": "3.3GB",
        "vram": "4GB+",
        "ram": "8GB+",
        "strengths": ["ultra hafif", "verimli"],
        "turkish": "temel",
        "speed": "çok hızlı (~50-70 tok/s)",
        "tier": "light",
    },
}


# ---------------------------------------------------------------------------
# Auto-detect available models
# ---------------------------------------------------------------------------

def _detect_available_models(base_url: str = "http://localhost:11434") -> list[str]:
    """Query Ollama for locally available models."""
    try:
        resp = httpx.get(f"{base_url}/api/tags", timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def _select_best_model(
    available: list[str],
    preferred: str,
    fallback_chain: list[str],
) -> str:
    """Select best available model with fallback chain."""
    candidates = [preferred] + fallback_chain
    for cand in candidates:
        # Exact match
        if cand in available:
            return cand
        # Tag-less match (e.g., 'gemma4' matches 'gemma4:latest')
        base = cand.split(":")[0]
        for av in available:
            if av.split(":")[0] == base:
                return av
    # Ultimate fallback
    return available[0] if available else preferred


class JARVISConfig(BaseSettings):
    """Application settings loaded from environment variables with defaults.

    Kullanıcının mevcut modellerine göre optimize edilmiş yapılandırma:
    - Default: qwen3-coder:30b (Türkçe + tool calling + zaten yüklü)
    - Fallback: gemma4:latest → mistral:latest → qwen3:4b
    - Premium: llama3.1:70b (manuel seçim gerekir)
    """

    # Ollama LLM
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3-coder:30b"  # Kullanıcının en iyi Türkçe+tool modeli
    ollama_timeout: int = 180  # 30B model için daha uzun timeout
    ollama_fallback_models: str = "gemma4:latest,mistral:latest,qwen3:4b"
    ollama_auto_detect: bool = True  # Ollama'dan mevcut modelleri tespit et
    ollama_stream_timeout: int = 300  # Streaming için ek süre

    # Speech-to-Text
    stt_model: str = "large-v3"
    stt_device: str = "auto"
    stt_compute_type: str = "int8"

    # Text-to-Speech
    tts_model_path: str = "./models/piper/tr_TR-dfki-medium.onnx"
    tts_config_path: str = "./models/piper/tr_TR-dfki-medium.json"

    # Wakeword
    wakeword_model: str = "./models/openwakeword/jarvis.tflite"
    wakeword_threshold: float = 0.5

    # Voice Activity Detection
    vad_threshold: float = 0.5

    # Vector DB & SQLite
    chroma_persist_dir: str = "./data/chroma"
    sqlite_path: str = "./data/jarvis.db"

    # Personality
    voice_name: str = "Jarvis"
    personality_style: str = "professional_friendly"

    # Audio
    sample_rate: int = 16000

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    class Config:
        env_prefix = "JARVIS_"
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_model_info(self) -> dict[str, Any]:
        """Return info about the currently configured model."""
        model = self.ollama_model
        return USER_MODELS.get(model, {"name": model, "tier": "unknown"})

    def get_available_models(self) -> list[str]:
        """Detect currently available Ollama models."""
        return _detect_available_models(self.ollama_base_url)

    def auto_select_model(self) -> str:
        """Auto-select best available model from Ollama."""
        if not self.ollama_auto_detect:
            return self.ollama_model

        available = self.get_available_models()
        if not available:
            logger.warning("Ollama'da hiç model bulunamadı, default kullanılıyor.")
            return self.ollama_model

        fallbacks = [m.strip() for m in self.ollama_fallback_models.split(",")]
        selected = _select_best_model(available, self.ollama_model, fallbacks)

        if selected != self.ollama_model:
            logger.info(
                "🔄 Auto-detect: '%s' yerine '%s' kullanılıyor (mevcut modellerden).",
                self.ollama_model, selected,
            )
        else:
            logger.info("✅ Model '%s' Ollama'da mevcut.", selected)

        return selected


# Singleton instance for global access
_config: JARVISConfig | None = None


def get_config() -> JARVISConfig:
    """Return cached config instance (singleton)."""
    global _config
    if _config is None:
        _config = JARVISConfig()
    return _config
