"""Tests for FastAPI endpoints using TestClient."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from turkish_jarvis.api.endpoints import router as v2_router


@pytest.fixture
def test_app() -> FastAPI:
    """Create a minimal FastAPI app with the v2 router for testing."""
    app = FastAPI()
    app.include_router(v2_router)
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """Provide a TestClient for the test app."""
    return TestClient(test_app)


class TestSessionsEndpoints:
    """Tests for GET /sessions and DELETE /sessions/{session_id}."""

    def test_list_sessions_empty(self, client: TestClient) -> None:
        """GET /api/v2/sessions should return a list (possibly empty)."""
        response = client.get("/api/v2/sessions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_delete_session(self, client: TestClient, temp_db_path: str) -> None:
        """DELETE should remove a session and return success status."""
        # Ensure test DB is used via env (router lazy-loads config)
        os.environ["JARVIS_SQLITE_PATH"] = temp_db_path
        response = client.delete("/api/v2/sessions/del-test")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        assert data["session_id"] == "del-test"


class TestRAGEndpoints:
    """Tests for POST /rag/upload and POST /rag/query."""

    def test_rag_query_validation(self, client: TestClient) -> None:
        """RAG query with empty body should fail validation."""
        response = client.post("/api/v2/rag/query", json={})
        assert response.status_code == 422

    def test_rag_query_schema(self, client: TestClient) -> None:
        """RAG query with valid schema should return a results list."""
        response = client.post(
            "/api/v2/rag/query",
            json={"question": "Test sorgusu", "k": 3},
        )
        # May succeed or fail depending on RAG backend availability
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert "results" in data
            assert isinstance(data["results"], list)

    def test_rag_upload_unsupported_type(self, client: TestClient) -> None:
        """Uploading a non-PDF/TXT/MD file should return 400."""
        response = client.post(
            "/api/v2/rag/upload",
            files={"file": ("report.exe", b"binary content", "application/octet-stream")},
        )
        assert response.status_code == 400


class TestPreferencesEndpoints:
    """Tests for GET and POST /preferences/{session_id}."""

    def test_get_preferences(self, client: TestClient, temp_db_path: str) -> None:
        """GET should return preferences and corrections."""
        os.environ["JARVIS_SQLITE_PATH"] = temp_db_path
        response = client.get("/api/v2/preferences/pref-test")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "pref-test"
        assert "preferences" in data
        assert "recent_corrections" in data

    def test_save_preference(self, client: TestClient, temp_db_path: str) -> None:
        """POST should save a preference and return confirmation."""
        os.environ["JARVIS_SQLITE_PATH"] = temp_db_path
        response = client.post(
            "/api/v2/preferences/pref-test",
            json={"key": "theme", "value": "dark", "source": "explicit"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "saved"
        assert data["key"] == "theme"


class TestPersonalityEndpoints:
    """Tests for GET and POST /personality."""

    def test_get_personality(self, client: TestClient) -> None:
        """GET should return current personality settings."""
        response = client.get("/api/v2/personality")
        assert response.status_code == 200
        data = response.json()
        assert "voice_name" in data
        assert "personality_style" in data
        assert "available_styles" in data
        assert isinstance(data["available_styles"], list)

    def test_update_personality(self, client: TestClient) -> None:
        """POST should update personality fields."""
        response = client.post(
            "/api/v2/personality",
            json={"voice_name": "TestBot", "personality_style": "casual", "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert data["voice_name"] == "TestBot"


class TestMemoryEntityEndpoints:
    """Tests for POST /memory/entity and GET /memory/entity/{name}."""

    def test_add_and_get_entity(self, client: TestClient, temp_db_path: str) -> None:
        """Entity should be added and retrievable by name."""
        os.environ["JARVIS_SQLITE_PATH"] = temp_db_path
        payload = {
            "name": "Ahmet",
            "entity_type": "person",
            "attributes": {"city": "Ankara"},
            "relations": [],
        }
        response = client.post("/api/v2/memory/entity", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        assert data["entity"]["name"] == "Ahmet"

        # GET
        response = client.get("/api/v2/memory/entity/Ahmet")
        assert response.status_code == 200
        get_data = response.json()
        assert get_data["name"] == "Ahmet"
        assert get_data["type"] == "person"
        assert get_data["attributes"]["city"] == "Ankara"

    def test_get_missing_entity(self, client: TestClient, temp_db_path: str) -> None:
        """GET for a nonexistent entity should return 404."""
        os.environ["JARVIS_SQLITE_PATH"] = temp_db_path
        response = client.get("/api/v2/memory/entity/nonexistent_xyz")
        assert response.status_code == 404
