"""User preference learning: explicit storage and simple implicit inference."""

import json
import re
import sqlite3
import threading
from pathlib import Path
from typing import Any


class PreferenceLearner:
    """Learns and stores user preferences from explicit statements and
    simple implicit signals (corrections).

    Stores data in SQLite so it survives restarts.
    """

    def __init__(self, db_path: str = "./data/jarvis.db") -> None:
        """Initialize the learner and ensure tables exist.

        Args:
            db_path: Path to the SQLite database.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()

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
        """Create preference and correction tables."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS learned_preferences (
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'explicit',
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (user_id, key)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                original TEXT NOT NULL,
                correction TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()
        conn.close()

    def save_explicit(
        self,
        user_id: str,
        key: str,
        value: Any,
    ) -> None:
        """Explicitly save a user preference.

        Args:
            user_id: User identifier.
            key: Preference key.
            value: Preference value (JSON-serializable).
        """
        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO learned_preferences (user_id, key, value, source, updated_at)
            VALUES (?, ?, ?, 'explicit', datetime('now'))
            ON CONFLICT(user_id, key) DO UPDATE SET
                value=excluded.value,
                source='explicit',
                updated_at=excluded.updated_at
            """,
            (user_id, key, json.dumps(value, ensure_ascii=False)),
        )
        conn.commit()

    def extract_implicit(
        self,
        user_id: str,
        user_message: str,
        assistant_message: str | None = None,
    ) -> list[dict[str, Any]]:
        """Attempt to infer preferences from a user message.

        Very simple heuristics are used (e.g., "asla ... istemem",
        "her zaman ... severim", corrections like "yanlış: ...").

        Args:
            user_id: User identifier.
            user_message: Raw user message text.
            assistant_message: Optional previous assistant message for context.

        Returns:
            List of inferred preference dicts with 'key', 'value', 'source'.
        """
        inferred: list[dict[str, Any]] = []
        text = user_message.lower()

        # Simple Turkish patterns
        like_patterns = [
            r"(\w+)\s+seviyorum",
            r"(\w+)\s+severim",
            r"(\w+)\s+hoşuma\s+gider",
        ]
        dislike_patterns = [
            r"(\w+)\s+sevmiyorum",
            r"(\w+)\s+istemem",
            r"(\w+)\s+hoşuma\s+gitmiyor",
        ]
        for pat in like_patterns:
            for match in re.finditer(pat, text):
                topic = match.group(1)
                inferred.append(
                    {
                        "key": f"likes_{topic}",
                        "value": True,
                        "source": "implicit",
                    }
                )
        for pat in dislike_patterns:
            for match in re.finditer(pat, text):
                topic = match.group(1)
                inferred.append(
                    {
                        "key": f"likes_{topic}",
                        "value": False,
                        "source": "implicit",
                    }
                )

        # Correction pattern: "yanlış: ..." or "doğrusu: ..."
        correction_match = re.search(r"(?:yanl[ıi][şs]|do[ğg]rusu)\s*[:;]\s*(.+)", text)
        if correction_match and assistant_message:
            correction = correction_match.group(1).strip()
            self.save_correction(user_id, assistant_message, correction)
            inferred.append(
                {
                    "key": "last_correction",
                    "value": correction,
                    "source": "implicit_correction",
                }
            )

        # Store inferred preferences
        conn = self._get_conn()
        for item in inferred:
            if item["source"] == "implicit":
                conn.execute(
                    """
                    INSERT INTO learned_preferences (user_id, key, value, source, updated_at)
                    VALUES (?, ?, ?, 'implicit', datetime('now'))
                    ON CONFLICT(user_id, key) DO UPDATE SET
                        value=excluded.value,
                        source='implicit',
                        updated_at=excluded.updated_at
                    """,
                    (
                        user_id,
                        item["key"],
                        json.dumps(item["value"], ensure_ascii=False),
                    ),
                )
        conn.commit()
        return inferred

    def save_correction(
        self,
        user_id: str,
        original: str,
        correction: str,
    ) -> int:
        """Store a user correction for future reference.

        Args:
            user_id: User identifier.
            original: The incorrect assistant output.
            correction: User-provided correction.

        Returns:
            The row ID of the inserted correction.
        """
        conn = self._get_conn()
        cursor = conn.execute(
            """
            INSERT INTO corrections (user_id, original, correction, created_at)
            VALUES (?, ?, ?, datetime('now'))
            """,
            (user_id, original, correction),
        )
        conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    def get_preferences(self, user_id: str) -> dict[str, Any]:
        """Return all learned preferences for a user.

        Args:
            user_id: User identifier.

        Returns:
            Dictionary of key-value pairs (explicit override implicit).
        """
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT key, value, source FROM learned_preferences
            WHERE user_id = ?
            ORDER BY updated_at ASC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        result: dict[str, Any] = {}
        for row in rows:
            key = row["key"]
            raw = row["value"]
            try:
                value = json.loads(raw)
            except json.JSONDecodeError:
                value = raw
            result[key] = value
        return result

    def get_recent_corrections(
        self, user_id: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Return recent corrections for a user.

        Args:
            user_id: User identifier.
            limit: Maximum number of corrections.

        Returns:
            List of correction dictionaries.
        """
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT id, original, correction, created_at
            FROM corrections
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = cursor.fetchall()
        return [
            {
                "id": row["id"],
                "original": row["original"],
                "correction": row["correction"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
