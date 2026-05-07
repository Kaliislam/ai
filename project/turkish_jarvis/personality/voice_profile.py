"""Voice profile management v2.0: Piper TTS voice selection,
tone mapping, speech-speed tuning, and an expanded voice catalogue.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any


class VoiceProfile:
    """Manages TTS voice profile settings per user.

    Features
    --------
    * Piper voice model selection (Turkish + English catalogue).
    * Personality-tone mapping (professional / warm / humorous).
    * Speech-speed, pitch, and volume adjustments.
    * SQLite-backed persistence with thread-safe connections.
    """

    # ------------------------------------------------------------------ #
    # Defaults
    # ------------------------------------------------------------------ #
    DEFAULTS: dict[str, Any] = {
        "voice_model": "tr_TR-dfki-medium",
        "voice_model_path": "./models/piper/tr_TR-dfki-medium.onnx",
        "voice_config_path": "./models/piper/tr_TR-dfki-medium.onnx.json",
        "speed": 1.0,
        "pitch": 1.0,
        "volume_gain_db": 0.0,
        "language": "tr",
        "tone": "professional",  # professional | warm | humorous
        "pace": "normal",  # slow | normal | fast
    }

    # ------------------------------------------------------------------ #
    # Personality → Piper parameter mapping
    # ------------------------------------------------------------------ #
    # These are *suggested* speed/pitch overrides that the caller may apply
    # when synthesising speech.  They are not forced; the user can override.
    TONE_PRESETS: dict[str, dict[str, float]] = {
        "professional": {"speed": 1.0, "pitch": 1.0, "volume_gain_db": 0.0},
        "warm": {"speed": 0.95, "pitch": 1.02, "volume_gain_db": 1.5},
        "humorous": {"speed": 1.08, "pitch": 1.05, "volume_gain_db": 2.0},
    }

    # ------------------------------------------------------------------ #
    # Pace → speed mapping
    # ------------------------------------------------------------------ #
    PACE_SPEED_MAP: dict[str, float] = {
        "slow": 0.82,
        "normal": 1.0,
        "fast": 1.18,
    }

    def __init__(self, db_path: str = "./data/jarvis.db") -> None:
        """Initialise the voice profile store.

        Args:
            db_path: SQLite database file path.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()

    # ------------------------------------------------------------------ #
    # SQLite helpers
    # ------------------------------------------------------------------ #

    def _get_conn(self) -> sqlite3.Connection:
        """Get a thread-local SQLite connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
            )
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self) -> None:
        """Create the voice_profiles table if it does not exist."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS voice_profiles (
                user_id TEXT PRIMARY KEY,
                settings TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()
        conn.close()

    def _ensure_defaults(self, settings: dict[str, Any]) -> dict[str, Any]:
        """Fill in any missing keys with default values."""
        merged = dict(self.DEFAULTS)
        merged.update(settings)
        return merged

    def _save(self, user_id: str, settings: dict[str, Any]) -> None:
        """Persist settings to the database."""
        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO voice_profiles (user_id, settings, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(user_id) DO UPDATE SET
                settings=excluded.settings,
                updated_at=excluded.updated_at
            """,
            (user_id, json.dumps(settings, ensure_ascii=False)),
        )
        conn.commit()

    # ------------------------------------------------------------------ #
    # Public CRUD
    # ------------------------------------------------------------------ #

    def get_settings(self, user_id: str) -> dict[str, Any]:
        """Retrieve the complete voice profile for a user.

        Args:
            user_id: User identifier.

        Returns:
            Dictionary of voice settings with defaults applied.
        """
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT settings FROM voice_profiles WHERE user_id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return dict(self.DEFAULTS)
        try:
            settings = json.loads(row["settings"])
        except json.JSONDecodeError:
            settings = {}
        return self._ensure_defaults(settings)

    def set_voice(self, user_id: str, voice_model: str) -> None:
        """Set the Piper voice model for a user.

        Args:
            user_id: User identifier.
            voice_model: Piper voice model name (e.g. ``'tr_TR-dfki-medium'``).
        """
        settings = self.get_settings(user_id)
        settings["voice_model"] = voice_model
        settings["voice_model_path"] = f"./models/piper/{voice_model}.onnx"
        settings["voice_config_path"] = f"./models/piper/{voice_model}.onnx.json"
        self._save(user_id, settings)

    def set_speed(self, user_id: str, speed: float) -> None:
        """Set the speech speed multiplier directly.

        Args:
            user_id: User identifier.
            speed: Speed multiplier (e.g. ``0.8`` slower, ``1.2`` faster).
        """
        settings = self.get_settings(user_id)
        settings["speed"] = max(0.5, min(2.0, speed))
        self._save(user_id, settings)

    def set_pace(self, user_id: str, pace: str) -> None:
        """Set speech pace by named preset.

        Args:
            user_id: User identifier.
            pace: One of ``'slow'``, ``'normal'``, ``'fast'``.
        """
        if pace not in self.PACE_SPEED_MAP:
            raise ValueError(f"Unknown pace '{pace}'. Choose from {list(self.PACE_SPEED_MAP)}.")
        settings = self.get_settings(user_id)
        settings["pace"] = pace
        settings["speed"] = self.PACE_SPEED_MAP[pace]
        self._save(user_id, settings)

    def set_pitch(self, user_id: str, pitch: float) -> None:
        """Set the pitch multiplier.

        Args:
            user_id: User identifier.
            pitch: Pitch multiplier (e.g. ``0.9`` lower, ``1.1`` higher).
        """
        settings = self.get_settings(user_id)
        settings["pitch"] = max(0.5, min(2.0, pitch))
        self._save(user_id, settings)

    def set_volume_gain(self, user_id: str, gain_db: float) -> None:
        """Set the volume gain in decibels.

        Args:
            user_id: User identifier.
            gain_db: Gain in dB (e.g. ``-6.0`` quieter, ``+6.0`` louder).
        """
        settings = self.get_settings(user_id)
        settings["volume_gain_db"] = max(-20.0, min(20.0, gain_db))
        self._save(user_id, settings)

    def set_tone(self, user_id: str, tone: str) -> dict[str, float]:
        """Apply a personality-tone preset.

        Args:
            user_id: User identifier.
            tone: One of ``'professional'``, ``'warm'``, ``'humorous'``.

        Returns:
            The applied preset dictionary (speed, pitch, volume_gain_db).
        """
        if tone not in self.TONE_PRESETS:
            raise ValueError(f"Unknown tone '{tone}'. Choose from {list(self.TONE_PRESETS)}.")
        preset = self.TONE_PRESETS[tone]
        settings = self.get_settings(user_id)
        settings["tone"] = tone
        settings.update(preset)
        self._save(user_id, settings)
        return dict(preset)

    # ------------------------------------------------------------------ #
    # Expanded voice catalogue
    # ------------------------------------------------------------------ #

    def list_available_voices(self) -> list[dict[str, Any]]:
        """Return a curated catalogue of Piper voices for Turkish and English.

        Returns:
            List of voice metadata dictionaries.
        """
        return [
            {
                "id": "tr_TR-dfki-medium",
                "language": "tr",
                "gender": "male",
                "name": "Turkish DFKI Medium",
                "description": "Doğal Türkçe erkek sesi, orta kalite. Günlük konuşma ve teknik anlatım için uygundur.",
                "recommended_for": ["professional", "warm"],
            },
            {
                "id": "tr_TR-fahrettin-medium",
                "language": "tr",
                "gender": "male",
                "name": "Turkish Fahrettin Medium",
                "description": "Daha genç ve dinamik Türkçe erkek sesi. Samimi ve enerjik tonlar için uygundur.",
                "recommended_for": ["warm", "humorous"],
            },
            {
                "id": "en_US-lessac-medium",
                "language": "en",
                "gender": "female",
                "name": "English Lessac Medium",
                "description": "Natural US English female voice, medium quality. Clear and professional.",
                "recommended_for": ["professional", "warm"],
            },
            {
                "id": "en_US-ryan-high",
                "language": "en",
                "gender": "male",
                "name": "English Ryan High",
                "description": "High-quality US English male voice. Authoritative and crisp.",
                "recommended_for": ["professional"],
            },
            {
                "id": "en_GB-semaine-medium",
                "language": "en",
                "gender": "male",
                "name": "English Semaine Medium",
                "description": "British English male voice, medium quality. Classic and balanced.",
                "recommended_for": ["professional", "warm"],
            },
            {
                "id": "en_GB-southern_english_female-medium",
                "language": "en",
                "gender": "female",
                "name": "English Southern Female Medium",
                "description": "Southern British English female voice. Warm and approachable.",
                "recommended_for": ["warm", "humorous"],
            },
        ]

    def recommend_voice(self, language: str = "tr", tone: str = "professional") -> dict[str, Any] | None:
        """Recommend a voice based on language and desired personality tone.

        Args:
            language: Preferred language (``'tr'`` or ``'en'``).
            tone: Desired tone (``'professional'``, ``'warm'``, ``'humorous'``).

        Returns:
            Best-matching voice metadata, or ``None`` if no match.
        """
        voices = self.list_available_voices()
        candidates = [
            v for v in voices
            if v.get("language") == language and tone in v.get("recommended_for", [])
        ]
        return candidates[0] if candidates else None
