"""TurkishJARVIS API v2.0 endpoints.

Provides REST endpoints for session management, RAG, preferences,
personality settings, and graph memory.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from turkish_jarvis.config import get_config
from turkish_jarvis.memory.conversation import ConversationStore
from turkish_jarvis.memory.episodic import EpisodicMemory
from turkish_jarvis.memory.longterm import LongTermMemory
from turkish_jarvis.memory.rag import RAGPipeline
from turkish_jarvis.personality.preferences import PreferenceLearner
from turkish_jarvis.personality.system_prompt import SystemPromptBuilder
from turkish_jarvis.utils.security import detect_prompt_injection, sanitize_text, validate_path

router = APIRouter(prefix="/api/v2", tags=["jarvis-v2"])

# ---------------------------------------------------------------------------
# Lazy singletons (mirrors main.py pattern)
# ---------------------------------------------------------------------------

_config = None

def _get_config() -> Any:
    global _config
    if _config is None:
        _config = get_config()
    return _config


def _get_conv_store() -> ConversationStore:
    cfg = _get_config()
    return ConversationStore(db_path=getattr(cfg, "sqlite_path", "./data/jarvis.db"))


def _get_preference_learner() -> PreferenceLearner:
    cfg = _get_config()
    return PreferenceLearner(db_path=getattr(cfg, "sqlite_path", "./data/jarvis.db"))


def _get_longterm() -> LongTermMemory:
    cfg = _get_config()
    return LongTermMemory(db_path=getattr(cfg, "sqlite_path", "./data/jarvis.db"))


def _get_rag() -> RAGPipeline:
    cfg = _get_config()
    return RAGPipeline(
        persist_dir=getattr(cfg, "chroma_persist_dir", "./data/chroma"),
        ollama_base_url=getattr(cfg, "ollama_base_url", "http://localhost:11434"),
        ollama_model=getattr(cfg, "ollama_model", "qwen2.5:14b"),
    )


# ---------------------------------------------------------------------------
# Graph Memory (simple SQLite-backed graph)
# ---------------------------------------------------------------------------

class GraphMemory:
    """Lightweight graph memory backed by SQLite."""

    def __init__(self, db_path: str = "./data/jarvis.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
            )
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self) -> None:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS graph_entities (
                name TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL DEFAULT 'unknown',
                attributes TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS graph_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                relation TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(source, target, relation)
            )
            """
        )
        conn.commit()
        conn.close()

    def add_entity(self, name: str, entity_type: str, attributes: dict[str, Any]) -> None:
        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO graph_entities (name, entity_type, attributes, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(name) DO UPDATE SET
                entity_type=excluded.entity_type,
                attributes=excluded.attributes,
                updated_at=excluded.updated_at
            """,
            (name, entity_type, json.dumps(attributes, ensure_ascii=False)),
        )
        conn.commit()

    def get_entity(self, name: str) -> dict[str, Any] | None:
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM graph_entities WHERE name = ?",
            (name,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {
            "name": row["name"],
            "type": row["entity_type"],
            "attributes": json.loads(row["attributes"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def add_relation(self, source: str, target: str, relation: str) -> None:
        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO graph_relations (source, target, relation)
            VALUES (?, ?, ?)
            ON CONFLICT DO NOTHING
            """,
            (source, target, relation),
        )
        conn.commit()

    def get_relations(self, name: str) -> list[dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT * FROM graph_relations
            WHERE source = ? OR target = ?
            ORDER BY created_at DESC
            """,
            (name, name),
        )
        rows = cursor.fetchall()
        return [
            {
                "id": row["id"],
                "source": row["source"],
                "target": row["target"],
                "relation": row["relation"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]


_graph_memory: GraphMemory | None = None


def _get_graph_memory() -> GraphMemory:
    global _graph_memory
    if _graph_memory is None:
        cfg = _get_config()
        _graph_memory = GraphMemory(db_path=getattr(cfg, "sqlite_path", "./data/jarvis.db"))
    return _graph_memory


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="RAG sorgu metni")
    k: int = Field(default=5, ge=1, le=20, description="Döndürülecek chunk sayısı")


class RAGQueryResponse(BaseModel):
    results: list[dict[str, Any]]


class PreferenceSaveRequest(BaseModel):
    key: str = Field(..., min_length=1, max_length=128)
    value: Any
    source: str = Field(default="explicit", pattern=r"^(explicit|implicit)$")


class PersonalitySettings(BaseModel):
    voice_name: str = Field(default="Jarvis", max_length=64)
    personality_style: str = Field(default="professional_friendly", max_length=64)
    language: str = Field(default="tr", pattern=r"^(tr|en)$")


class EntityCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    entity_type: str = Field(default="unknown", max_length=64)
    attributes: dict[str, Any] = Field(default_factory=dict)
    relations: list[dict[str, str]] = Field(default_factory=list)


class EntityResponse(BaseModel):
    name: str
    type: str
    attributes: dict[str, Any]
    relations: list[dict[str, Any]]
    created_at: str | None = None
    updated_at: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/sessions", response_model=list[str])
async def list_sessions() -> list[str]:
    """Tüm session ID'lerini listele (en son aktif olan önce)."""
    try:
        store = _get_conv_store()
        return store.get_all_sessions()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Session listesi alınamadı: {exc}") from exc


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> dict[str, str]:
    """Bir session'ı ve tüm mesajlarını sil."""
    try:
        store = _get_conv_store()
        conn = store._get_conn()
        conn.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM session_summaries WHERE session_id = ?", (session_id,))
        conn.commit()
        return {"status": "deleted", "session_id": session_id}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Session silinemedi: {exc}") from exc


@router.post("/rag/upload")
async def rag_upload(file: UploadFile = File(...)) -> dict[str, Any]:
    """Bir dosyayı (PDF/TXT/MD) RAG vektör veritabanına yükle."""
    allowed_extensions = {".txt", ".md", ".markdown", ".pdf"}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen dosya türü: {suffix}. İzin verilen: {allowed_extensions}",
        )

    upload_dir = Path("./data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / (hashlib.sha256((file.filename or "unknown").encode()).hexdigest()[:16] + suffix)

    try:
        contents = await file.read()
        file_path.write_bytes(contents)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Dosya yazma hatası: {exc}") from exc

    try:
        rag = _get_rag()
        ids = rag.add_document(str(file_path))
        return {
            "status": "ok",
            "file_name": file.filename,
            "stored_path": str(file_path),
            "chunks_added": len(ids),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RAG işleme hatası: {exc}") from exc


@router.post("/rag/query", response_model=RAGQueryResponse)
async def rag_query(request: RAGQueryRequest) -> dict[str, Any]:
    """RAG vektör veritabanında similarity search yap."""
    try:
        rag = _get_rag()
        results = rag.query(request.question, k=request.k)
        return {"results": results}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RAG sorgu hatası: {exc}") from exc


@router.get("/preferences/{session_id}")
async def get_preferences(session_id: str) -> dict[str, Any]:
    """Bir kullanıcı/session için öğrenilmiş tercihleri getir."""
    try:
        learner = _get_preference_learner()
        prefs = learner.get_preferences(session_id)
        corrections = learner.get_recent_corrections(session_id, limit=5)
        return {
            "session_id": session_id,
            "preferences": prefs,
            "recent_corrections": corrections,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Tercihler alınamadı: {exc}") from exc


@router.post("/preferences/{session_id}")
async def save_preference(session_id: str, request: PreferenceSaveRequest) -> dict[str, str]:
    """Bir kullanıcı/session için tercih kaydet."""
    try:
        learner = _get_preference_learner()
        learner.save_explicit(session_id, request.key, request.value)
        return {
            "status": "saved",
            "session_id": session_id,
            "key": request.key,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Tercih kaydedilemedi: {exc}") from exc


@router.get("/personality")
async def get_personality() -> dict[str, Any]:
    """Mevcut kişilik ayarlarını döndür."""
    cfg = _get_config()
    builder = SystemPromptBuilder(voice_name=getattr(cfg, "voice_name", "Jarvis"))
    return {
        "voice_name": getattr(cfg, "voice_name", "Jarvis"),
        "personality_style": getattr(cfg, "personality_style", "professional_friendly"),
        "available_styles": ["professional_friendly", "formal", "casual", "witty"],
        "system_prompt_preview": builder.build()[:200],
    }


@router.post("/personality")
async def update_personality(settings: PersonalitySettings) -> dict[str, str]:
    """Kişilik ayarlarını güncelle (çalışma süresi boyunca)."""
    cfg = _get_config()
    # Update the in-memory config object fields
    cfg.voice_name = settings.voice_name
    cfg.personality_style = settings.personality_style
    os.environ["JARVIS_VOICE_NAME"] = settings.voice_name
    return {
        "status": "updated",
        "voice_name": settings.voice_name,
        "personality_style": settings.personality_style,
        "language": settings.language,
    }


@router.post("/memory/entity")
async def add_entity(request: EntityCreateRequest) -> dict[str, Any]:
    """Graph memory'e yeni bir entity ekle."""
    try:
        gm = _get_graph_memory()
        gm.add_entity(request.name, request.entity_type, request.attributes)
        for rel in request.relations:
            gm.add_relation(
                rel.get("source", request.name),
                rel.get("target", ""),
                rel.get("relation", "related"),
            )
        entity = gm.get_entity(request.name)
        relations = gm.get_relations(request.name)
        return {
            "status": "created",
            "entity": {
                "name": entity["name"],
                "type": entity["type"],
                "attributes": entity["attributes"],
                "relations": relations,
            } if entity else None,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Entity eklenemedi: {exc}") from exc


@router.get("/memory/entity/{name}")
async def get_entity(name: str) -> EntityResponse:
    """Graph memory'den bir entity ve ilişkilerini getir."""
    try:
        gm = _get_graph_memory()
        entity = gm.get_entity(name)
        if entity is None:
            raise HTTPException(status_code=404, detail=f"Entity bulunamadı: {name}")
        relations = gm.get_relations(name)
        return EntityResponse(
            name=entity["name"],
            type=entity["type"],
            attributes=entity["attributes"],
            relations=relations,
            created_at=entity.get("created_at"),
            updated_at=entity.get("updated_at"),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Entity sorgu hatası: {exc}") from exc
