# -*- coding: utf-8 -*-
"""Security utilities — input sanitization and basic validation."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Dangerous path fragments that should never appear in user-supplied paths
_BAD_PATH_FRAGMENTS: list[str] = [
    "..",
    "~",
    "/etc/",
    "/usr/",
    "/bin/",
    "/sbin/",
    "/lib",
    "/proc/",
    "/sys/",
    "/dev/",
    "C:\\\\",
    "\\\\",
]

# Shell metacharacters we refuse outright
_SHELL_METACHARS = re.compile(r"[;&|`$(){}\[\]<>]")

# Basic pattern to detect possible prompt-injection delimiters
_PROMPT_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"forget\s+(your\s+)?(instructions|training)", re.IGNORECASE),
    re.compile(r"system\s*:", re.IGNORECASE),
    re.compile(r"new\s+system\s+prompt", re.IGNORECASE),
    re.compile(r"DAN\s+mode", re.IGNORECASE),
]


def sanitize_text(text: str, max_length: int = 4000) -> str:
    """Strip control characters and truncate *text* to a safe length."""
    # Remove null bytes and other control chars except newline/tab
    cleaned = "".join(ch for ch in text if ch == "\n" or ch == "\t" or (ord(ch) >= 32))
    return cleaned[:max_length]


def validate_path(user_path: str, base_dir: str | Path | None = None) -> Path:
    """Validate a user-supplied filesystem path.

    Raises:
        ValueError: If the path contains suspicious fragments or escapes
            the allowed *base_dir*.
    """
    if _SHELL_METACHARS.search(user_path):
        raise ValueError("Path contains illegal shell metacharacters")

    for fragment in _BAD_PATH_FRAGMENTS:
        if fragment in user_path:
            raise ValueError(f"Path contains forbidden fragment: {fragment!r}")

    path = Path(user_path).resolve()

    if base_dir is not None:
        base = Path(base_dir).resolve()
        try:
            path.relative_to(base)
        except ValueError as exc:
            raise ValueError(f"Path escapes allowed base directory: {base}") from exc

    return path


def detect_prompt_injection(text: str) -> tuple[bool, list[str]]:
    """Scan *text* for known prompt-injection patterns.

    Returns ``(detected, reasons)``.
    """
    reasons: list[str] = []
    for pattern in _PROMPT_INJECTION_PATTERNS:
        if pattern.search(text):
            reasons.append(f"Matched pattern: {pattern.pattern}")
    return bool(reasons), reasons


def sanitize_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sanitize a list of chat messages in-place.

    Truncates overly long ``content`` fields and strips control chars.
    """
    cleaned: list[dict[str, Any]] = []
    for msg in messages:
        role = str(msg.get("role", "")).lower()
        content = msg.get("content", "")
        if isinstance(content, str):
            content = sanitize_text(content)
        cleaned.append({"role": role, "content": content})
    return cleaned


def redact_sensitive_keys(data: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow copy of *data* with known sensitive keys redacted."""
    sensitive = {"password", "token", "secret", "api_key", "key", "auth"}
    return {
        k: "***REDACTED***" if any(s in k.lower() for s in sensitive) else v
        for k, v in data.items()
    }
