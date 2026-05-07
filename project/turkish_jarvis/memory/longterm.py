"""SQLite long-term preference store with JSON value support."""

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any


class LongTermMemory:
    """Thread-safe SQLite store for user preferences and long-term facts.

    Values are serialized to JSON so complex types (lists, dicts, bool,
    int, float) can be stored transparently.
    """

    def __init__(self, db_path: str = "./data/jarvis.db") -> None:
        """Initialize the store and ensure the preferences table exists.

        Args:
            db_path: SQLite database file path (may share the conv DB).
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
        """Create the preferences table if it does not exist."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS preferences (
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (user_id, key)
            )
            """
        )
        conn.commit()
        conn.close()

    def set_preference(self, user_id: str, key: str, value: Any) -> None:
        """Store a preference value (JSON-serialized).

        Args:
            user_id: Identifier for the user.
            key: Preference key.
            value: Any JSON-serializable value.
        """
        conn = self._get_conn()
        json_value = json.dumps(value, ensure_ascii=False)
        conn.execute(
            """
            INSERT INTO preferences (user_id, key, value, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(user_id, key) DO UPDATE SET
                value=excluded.value,
                updated_at=excluded.updated_at
            """,
            (user_id, key, json_value),
        )
        conn.commit()

    def get_preference(self, user_id: str, key: str) -> Any:
        """Retrieve a single preference value.

        Args:
            user_id: User identifier.
            key: Preference key.

        Returns:
            The deserialized value, or None if not found.
        """
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT value FROM preferences WHERE user_id = ? AND key = ?",
            (user_id, key),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        try:
            return json.loads(row["value"])
        except json.JSONDecodeError:
            return row["value"]

    def get_all_preferences(self, user_id: str) -> dict[str, Any]:
        """Retrieve all preferences for a user.

        Args:
            user_id: User identifier.

        Returns:
            Dictionary of preference key-value pairs.
        """
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT key, value FROM preferences WHERE user_id = ?",
            (user_id,),
        )
        rows = cursor.fetchall()
        result: dict[str, Any] = {}
        for row in rows:
            key = row["key"]
            raw = row["value"]
            try:
                result[key] = json.loads(raw)
            except json.JSONDecodeError:
                result[key] = raw
        return result
