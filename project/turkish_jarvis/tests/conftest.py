"""Pytest fixtures for TurkishJARVIS test suite."""

from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any, Generator

import pytest

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("PYTHONPATH", str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for the entire test session."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def temp_db_path(temp_dir: Path) -> str:
    """Provide a temporary SQLite database path."""
    return str(temp_dir / "test_jarvis.db")


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unset JARVIS_ env vars to keep config predictable during tests."""
    for key in list(os.environ):
        if key.startswith("JARVIS_"):
            monkeypatch.delenv(key, raising=False)


@pytest.fixture
def sqlite_connection(temp_db_path: str) -> Generator[sqlite3.Connection, None, None]:
    """Provide a raw SQLite connection to a fresh test database."""
    conn = sqlite3.connect(temp_db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()
