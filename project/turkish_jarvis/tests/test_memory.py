"""Tests for memory modules: conversation, episodic, and long-term."""

from __future__ import annotations

from typing import Any

import pytest

from turkish_jarvis.memory.conversation import ConversationStore
from turkish_jarvis.memory.episodic import EpisodicMemory
from turkish_jarvis.memory.longterm import LongTermMemory


class TestConversationStore:
    """Unit tests for SQLite-backed conversation store."""

    def test_add_and_get_history(self, temp_db_path: str) -> None:
        """Messages added to a session should appear in history."""
        store = ConversationStore(db_path=temp_db_path)
        sid = "test-session-1"
        store.add_message(sid, "user", "Merhaba")
        store.add_message(sid, "assistant", "Merhaba! Size nasıl yardımcı olabilirim?")
        history = store.get_history(sid, limit=10)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_get_history_respects_limit(self, temp_db_path: str) -> None:
        """get_history should return at most *limit* messages."""
        store = ConversationStore(db_path=temp_db_path)
        sid = "test-session-limit"
        for i in range(5):
            store.add_message(sid, "user", f"msg {i}")
        history = store.get_history(sid, limit=3)
        assert len(history) == 3

    def test_tool_calls_roundtrip(self, temp_db_path: str) -> None:
        """Tool calls should be JSON-serialized and deserialized correctly."""
        store = ConversationStore(db_path=temp_db_path)
        sid = "tc-session"
        tc = [{"function": {"name": "weather", "arguments": {"city": "İstanbul"}}}]
        store.add_message(sid, "assistant", "Hava durumu:", tool_calls=tc)
        history = store.get_history(sid)
        assert history[0]["tool_calls"] is not None
        assert history[0]["tool_calls"][0]["function"]["name"] == "weather"

    def test_get_all_sessions(self, temp_db_path: str) -> None:
        """get_all_sessions should return distinct session IDs."""
        store = ConversationStore(db_path=temp_db_path)
        store.add_message("session-a", "user", "x")
        store.add_message("session-b", "user", "y")
        sessions = store.get_all_sessions()
        assert "session-a" in sessions
        assert "session-b" in sessions

    def test_create_summary(self, temp_db_path: str) -> None:
        """create_summary should produce non-empty summary text."""
        store = ConversationStore(db_path=temp_db_path)
        sid = "sum-session"
        store.add_message(sid, "user", "Nasılsın?")
        store.add_message(sid, "assistant", "İyiyim, teşekkürler.")
        summary = store.create_summary(sid)
        assert isinstance(summary, str)
        assert len(summary) > 0


class TestEpisodicMemory:
    """Unit tests for ChromaDB-backed episodic memory."""

    def test_add_and_search(self, temp_dir: Path) -> None:
        """An added episode should be retrievable via similarity search."""
        persist = str(temp_dir / "chroma_test")
        memory = EpisodicMemory(persist_dir=persist, collection_name="test_episodes")
        doc_id = memory.add("Kullanıcı İstanbul'da yaşıyor.", metadata={"topic": "location"})
        assert isinstance(doc_id, str)
        assert len(doc_id) > 0
        results = memory.search("Kullanıcı nerede yaşıyor?", k=3)
        assert len(results) >= 1
        assert "İstanbul" in results[0]["text"]

    def test_search_empty_collection(self, temp_dir: Path) -> None:
        """Searching an empty collection should return an empty list."""
        persist = str(temp_dir / "chroma_empty")
        memory = EpisodicMemory(persist_dir=persist, collection_name="test_empty")
        results = memory.search("anything", k=3)
        assert results == []


class TestLongTermMemory:
    """Unit tests for SQLite-backed long-term preference store."""

    def test_set_and_get_preference(self, temp_db_path: str) -> None:
        """Preferences should be stored and retrievable."""
        mem = LongTermMemory(db_path=temp_db_path)
        mem.set_preference("user-1", "theme", "dark")
        value = mem.get_preference("user-1", "theme")
        assert value == "dark"

    def test_get_missing_returns_none(self, temp_db_path: str) -> None:
        """Getting a missing preference should return None."""
        mem = LongTermMemory(db_path=temp_db_path)
        assert mem.get_preference("user-x", "nonexistent") is None

    def test_json_complex_types(self, temp_db_path: str) -> None:
        """Lists and dicts should round-trip through JSON serialization."""
        mem = LongTermMemory(db_path=temp_db_path)
        mem.set_preference("user-2", "favs", ["a", "b", "c"])
        mem.set_preference("user-2", "opts", {"lang": "tr", "voice": True})
        assert mem.get_preference("user-2", "favs") == ["a", "b", "c"]
        assert mem.get_preference("user-2", "opts") == {"lang": "tr", "voice": True}

    def test_get_all_preferences(self, temp_db_path: str) -> None:
        """get_all_preferences should return all keys for a user."""
        mem = LongTermMemory(db_path=temp_db_path)
        mem.set_preference("user-3", "a", 1)
        mem.set_preference("user-3", "b", 2)
        all_prefs = mem.get_all_preferences("user-3")
        assert all_prefs == {"a": 1, "b": 2}
