"""SQLite-based conversation store with automatic table creation."""

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ConversationStore:
    """Thread-safe SQLite store for conversation history.

    Attributes:
        db_path: Path to the SQLite database file.
        _local: threading.local for connection-per-thread safety.
    """

    def __init__(self, db_path: str = "./data/jarvis.db") -> None:
        """Initialize the store and ensure tables exist.

        Args:
            db_path: SQLite database file path.
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
        """Create required tables if they do not exist."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_calls TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS session_summaries (
                session_id TEXT PRIMARY KEY,
                summary TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conv_session
            ON conversations(session_id, created_at DESC)
            """
        )
        conn.commit()
        conn.close()

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> int:
        """Add a message to a conversation session.

        Args:
            session_id: Unique identifier for the conversation session.
            role: Message role (e.g., 'user', 'assistant', 'system').
            content: Message text content.
            tool_calls: Optional list of tool call dictionaries.

        Returns:
            The auto-incremented ID of the inserted row.
        """
        conn = self._get_conn()
        tool_calls_json = json.dumps(tool_calls, ensure_ascii=False) if tool_calls else None
        cursor = conn.execute(
            """
            INSERT INTO conversations (session_id, role, content, tool_calls, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                role,
                content,
                tool_calls_json,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    def get_history(self, session_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Retrieve recent messages for a session, newest first.

        Args:
            session_id: Session identifier.
            limit: Maximum number of messages to return.

        Returns:
            List of message dictionaries ordered by creation time descending.
        """
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT id, session_id, role, content, tool_calls, created_at
            FROM conversations
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (session_id, limit),
        )
        rows = cursor.fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            tool_calls = None
            if row["tool_calls"]:
                try:
                    tool_calls = json.loads(row["tool_calls"])
                except json.JSONDecodeError:
                    tool_calls = None
            result.append(
                {
                    "id": row["id"],
                    "session_id": row["session_id"],
                    "role": row["role"],
                    "content": row["content"],
                    "tool_calls": tool_calls,
                    "created_at": row["created_at"],
                }
            )
        return list(reversed(result))

    def create_summary(self, session_id: str) -> str:
        """Create or refresh a simple summary for a session.

        The summary is a truncated concatenation of user and assistant
        messages. In production this may call an LLM.

        Args:
            session_id: Session identifier.

        Returns:
            The generated summary text.
        """
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT role, content FROM conversations
            WHERE session_id = ?
            ORDER BY created_at ASC
            """,
            (session_id,),
        )
        rows = cursor.fetchall()
        parts: list[str] = []
        for row in rows:
            role = row["role"]
            content = row["content"]
            if role in ("user", "assistant"):
                parts.append(f"{role}: {content[:200]}")
        summary = "\n".join(parts)[:2000] or "No messages yet."
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            INSERT INTO session_summaries (session_id, summary, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                summary=excluded.summary,
                updated_at=excluded.updated_at
            """,
            (session_id, summary, now),
        )
        conn.commit()
        return summary

    def get_all_sessions(self) -> list[str]:
        """Return all unique session IDs ordered by most recent activity.

        Returns:
            List of session identifier strings.
        """
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT DISTINCT session_id, MAX(created_at) as last_at
            FROM conversations
            GROUP BY session_id
            ORDER BY last_at DESC
            """
        )
        rows = cursor.fetchall()
        return [row["session_id"] for row in rows]

    def clear(self, session_id: str) -> None:
        """Delete all messages and summary for a session.

        Args:
            session_id: Session identifier to clear.
        """
        conn = self._get_conn()
        conn.execute(
            "DELETE FROM conversations WHERE session_id = ?", (session_id,)
        )
        conn.execute(
            "DELETE FROM session_summaries WHERE session_id = ?", (session_id,)
        )
        conn.commit()
