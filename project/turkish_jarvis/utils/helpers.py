# -*- coding: utf-8 -*-
"""Helper utilities for TurkishJARVIS."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import tempfile
import uuid
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def generate_session_id() -> str:
    """Return a random UUID4 string suitable for a conversation session."""
    return str(uuid.uuid4())


def slugify(text: str) -> str:
    """Convert *text* to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text[:64]


def truncate_text(text: str, max_length: int = 500, suffix: str = "…") -> str:
    """Truncate *text* to *max_length* characters."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def compute_hash(content: str | bytes, algorithm: str = "sha256") -> str:
    """Return a hex digest of *content*."""
    hasher = hashlib.new(algorithm)
    if isinstance(content, str):
        hasher.update(content.encode("utf-8"))
    else:
        hasher.update(content)
    return hasher.hexdigest()


def safe_json_loads(data: str | bytes | None, default: Any = None) -> Any:
    """Safely parse JSON, returning *default* on failure."""
    if data is None:
        return default
    try:
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        return json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return default


def ensure_dir(path: str | Path) -> Path:
    """Create the directory (and parents) if it does not exist."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def temp_audio_path(suffix: str = ".wav") -> str:
    """Return a temporary audio file path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    # Close the file descriptor so other processes can write to it.
    import os

    os.close(fd)
    return path


def format_duration(seconds: float) -> str:
    """Return a human-readable duration string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m {secs}s"


def chunk_list(items: list[Any], chunk_size: int) -> list[list[Any]]:
    """Split *items* into sub-lists of at most *chunk_size*."""
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]
