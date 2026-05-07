"""Tests for configuration loading (config.py)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from turkish_jarvis.config import JARVISConfig, get_config


class TestJARVISConfig:
    """Unit tests for JARVISConfig Pydantic settings."""

    def test_default_values(self, clean_env: None) -> None:
        """Config should load with sensible defaults when no env vars are set."""
        cfg = JARVISConfig()
        assert cfg.ollama_base_url == "http://localhost:11434"
        assert cfg.ollama_model == "qwen2.5:14b"
        assert cfg.ollama_timeout == 120
        assert cfg.stt_model == "large-v3"
        assert cfg.sample_rate == 16000
        assert cfg.personality_style == "professional_friendly"

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch, clean_env: None) -> None:
        """Environment variables prefixed with JARVIS_ should override defaults."""
        monkeypatch.setenv("JARVIS_OLLAMA_MODEL", "llama3.2")
        monkeypatch.setenv("JARVIS_SAMPLE_RATE", "44100")
        cfg = JARVISConfig()
        assert cfg.ollama_model == "llama3.2"
        assert cfg.sample_rate == 44100

    def test_singleton_get_config(self, clean_env: None) -> None:
        """get_config() should return the same cached instance (singleton)."""
        cfg1 = get_config()
        cfg2 = get_config()
        assert cfg1 is cfg2

    def test_paths_exist_as_strings(self, clean_env: None) -> None:
        """Database and model paths should be non-empty strings."""
        cfg = JARVISConfig()
        assert isinstance(cfg.chroma_persist_dir, str)
        assert isinstance(cfg.sqlite_path, str)
        assert cfg.chroma_persist_dir != ""
        assert cfg.sqlite_path != ""

    def test_env_file_encoding(self, clean_env: None) -> None:
        """Config class should specify UTF-8 env file encoding."""
        assert JARVISConfig.Config.env_file_encoding == "utf-8"
