"""Graph memory module: entity-relation-event network backed by SQLite.

Stores people, places, concepts, and their relationships in a graph structure
using plain SQLite tables. Supports automatic entity/relation extraction
from LLM responses via prompt-based extraction.

Tables:
    entities  – id, name, type, attributes (JSON), created_at
    relations – id, from_entity, to_entity, relation_type, context (JSON), created_at
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    """A node in the memory graph."""

    id: int
    name: str
    type: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None


@dataclass
class Relation:
    """An edge in the memory graph."""

    id: int
    from_entity: str
    to_entity: str
    relation_type: str
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Graph Memory
# ---------------------------------------------------------------------------


class GraphMemory:
    """SQLite-backed graph memory for entities and relations.

    Usage:
        mem = GraphMemory(db_path="/tmp/memory.db")
        mem.add_entity("Ahmet", "person", {"job": "muhendis"})
        mem.add_relation("Ahmet", "Istanbul", "lives_in", {"since": "2020"})
        results = mem.search_related("Ahmet")
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or ":memory:"
        self._conn: sqlite3.Connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL DEFAULT 'unknown',
                    attributes TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_entity TEXT NOT NULL,
                    to_entity TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    context TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_relations_from ON relations(from_entity)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_relations_to ON relations(to_entity)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(relation_type)"
            )

    # ------------------------------------------------------------------
    # Entity CRUD
    # ------------------------------------------------------------------

    def add_entity(
        self,
        name: str,
        type: str = "unknown",
        attributes: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Add or update an entity. Returns the row id."""
        attrs_json = json.dumps(attributes or {}, ensure_ascii=False)
        cursor = self._conn.execute(
            "SELECT id FROM entities WHERE name = ?",
            (name,),
        )
        row = cursor.fetchone()
        if row:
            self._conn.execute(
                "UPDATE entities SET type = ?, attributes = ?, created_at = CURRENT_TIMESTAMP WHERE id = ?",
                (type, attrs_json, row["id"]),
            )
            self._conn.commit()
            return row["id"]
        cursor = self._conn.execute(
            "INSERT INTO entities (name, type, attributes) VALUES (?, ?, ?)",
            (name, type, attrs_json),
        )
        self._conn.commit()
        return cursor.lastrowid

    def get_entity(self, name: str) -> Optional[Entity]:
        """Fetch an entity by exact name."""
        row = self._conn.execute(
            "SELECT * FROM entities WHERE name = ?",
            (name,),
        ).fetchone()
        if row is None:
            return None
        return Entity(
            id=row["id"],
            name=row["name"],
            type=row["type"],
            attributes=json.loads(row["attributes"]),
            created_at=row["created_at"],
        )

    def query_entity(self, name: str) -> Optional[Dict[str, Any]]:
        """Fetch entity with its direct relations (convenience method)."""
        entity = self.get_entity(name)
        if entity is None:
            return None
        relations = self._conn.execute(
            """
            SELECT * FROM relations
            WHERE from_entity = ? OR to_entity = ?
            ORDER BY created_at DESC
            """,
            (name, name),
        ).fetchall()
        return {
            "entity": {
                "id": entity.id,
                "name": entity.name,
                "type": entity.type,
                "attributes": entity.attributes,
            },
            "relations": [
                {
                    "from": r["from_entity"],
                    "to": r["to_entity"],
                    "type": r["relation_type"],
                    "context": json.loads(r["context"]),
                }
                for r in relations
            ],
        }

    def list_entities(self, type: Optional[str] = None) -> List[Entity]:
        """List all entities, optionally filtered by type."""
        if type:
            rows = self._conn.execute(
                "SELECT * FROM entities WHERE type = ? ORDER BY name",
                (type,),
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM entities ORDER BY name").fetchall()
        return [
            Entity(
                id=r["id"],
                name=r["name"],
                type=r["type"],
                attributes=json.loads(r["attributes"]),
                created_at=r["created_at"],
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Relation CRUD
    # ------------------------------------------------------------------

    def add_relation(
        self,
        from_entity: str,
        to_entity: str,
        relation_type: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Add a relation between two entities. Returns the row id."""
        ctx_json = json.dumps(context or {}, ensure_ascii=False)
        cursor = self._conn.execute(
            "INSERT INTO relations (from_entity, to_entity, relation_type, context) VALUES (?, ?, ?, ?)",
            (from_entity, to_entity, relation_type, ctx_json),
        )
        self._conn.commit()
        return cursor.lastrowid

    def get_relations(
        self,
        from_entity: Optional[str] = None,
        to_entity: Optional[str] = None,
        relation_type: Optional[str] = None,
    ) -> List[Relation]:
        """Query relations with optional filters."""
        conditions: List[str] = []
        params: List[str] = []
        if from_entity:
            conditions.append("from_entity = ?")
            params.append(from_entity)
        if to_entity:
            conditions.append("to_entity = ?")
            params.append(to_entity)
        if relation_type:
            conditions.append("relation_type = ?")
            params.append(relation_type)
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = self._conn.execute(
            f"SELECT * FROM relations {where} ORDER BY created_at DESC",
            params,
        ).fetchall()
        return [
            Relation(
                id=r["id"],
                from_entity=r["from_entity"],
                to_entity=r["to_entity"],
                relation_type=r["relation_type"],
                context=json.loads(r["context"]),
                created_at=r["created_at"],
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_related(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search entities and relations matching the query string."""
        like = f"%{query}%"
        entity_rows = self._conn.execute(
            "SELECT * FROM entities WHERE name LIKE ? OR type LIKE ? OR attributes LIKE ? LIMIT ?",
            (like, like, like, limit),
        ).fetchall()
        relation_rows = self._conn.execute(
            "SELECT * FROM relations WHERE from_entity LIKE ? OR to_entity LIKE ? OR relation_type LIKE ? OR context LIKE ? LIMIT ?",
            (like, like, like, like, limit),
        ).fetchall()
        return {
            "entities": [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "type": r["type"],
                    "attributes": json.loads(r["attributes"]),
                }
                for r in entity_rows
            ],
            "relations": [
                {
                    "id": r["id"],
                    "from": r["from_entity"],
                    "to": r["to_entity"],
                    "type": r["relation_type"],
                    "context": json.loads(r["context"]),
                }
                for r in relation_rows
            ],
        }

    def get_graph_summary(self) -> Dict[str, Any]:
        """Return high-level graph statistics."""
        entity_count = self._conn.execute(
            "SELECT COUNT(*) AS c FROM entities"
        ).fetchone()["c"]
        relation_count = self._conn.execute(
            "SELECT COUNT(*) AS c FROM relations"
        ).fetchone()["c"]
        types = self._conn.execute(
            "SELECT type, COUNT(*) AS c FROM entities GROUP BY type"
        ).fetchall()
        return {
            "entity_count": entity_count,
            "relation_count": relation_count,
            "entity_types": {r["type"]: r["c"] for r in types},
        }

    # ------------------------------------------------------------------
    # LLM extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def build_extraction_prompt(text: str) -> str:
        """Return a prompt that asks an LLM to extract entities and relations.

        The LLM should respond with a JSON object containing:
            {"entities": [{"name": str, "type": str, "attributes": dict}],
             "relations": [{"from": str, "to": str, "type": str, "context": dict}]}
        """
        return (
            "Extract entities and relations from the following text.\n"
            "Respond ONLY with a JSON object in this exact shape:\n"
            '{"entities": [{"name": "...", "type": "...", "attributes": {}}], '
            '"relations": [{"from": "...", "to": "...", "type": "...", "context": {}}]}\n'
            "Entity types: person, place, organization, event, concept, object.\n"
            "Relation types: knows, works_at, lives_in, visited, part_of, related_to, etc.\n\n"
            f"Text:\n{text}\n"
        )

    def apply_extraction_result(self, extraction_json: Dict[str, Any]) -> Dict[str, int]:
        """Persist entities and relations returned by an LLM extractor.

        Returns counts of inserted items.
        """
        inserted_entities = 0
        inserted_relations = 0
        for ent in extraction_json.get("entities", []):
            name = ent.get("name", "").strip()
            if not name:
                continue
            self.add_entity(
                name=name,
                type=ent.get("type", "unknown"),
                attributes=ent.get("attributes", {}),
            )
            inserted_entities += 1
        for rel in extraction_json.get("relations", []):
            fr = rel.get("from", "").strip()
            to = rel.get("to", "").strip()
            rtype = rel.get("type", "").strip()
            if fr and to and rtype:
                self.add_relation(
                    from_entity=fr,
                    to_entity=to,
                    relation_type=rtype,
                    context=rel.get("context", {}),
                )
                inserted_relations += 1
        return {
            "entities_inserted": inserted_entities,
            "relations_inserted": inserted_relations,
        }

    # ------------------------------------------------------------------
    # Import / export
    # ------------------------------------------------------------------

    def export_json(self) -> Dict[str, Any]:
        """Dump the entire graph as JSON."""
        return {
            "entities": [
                {
                    "id": e.id,
                    "name": e.name,
                    "type": e.type,
                    "attributes": e.attributes,
                    "created_at": e.created_at,
                }
                for e in self.list_entities()
            ],
            "relations": [
                {
                    "id": r.id,
                    "from": r.from_entity,
                    "to": r.to_entity,
                    "type": r.relation_type,
                    "context": r.context,
                    "created_at": r.created_at,
                }
                for r in self.get_relations()
            ],
        }

    def import_json(self, data: Dict[str, Any]) -> None:
        """Import a graph from JSON (merges, does not clear)."""
        for ent in data.get("entities", []):
            self.add_entity(
                name=ent["name"],
                type=ent.get("type", "unknown"),
                attributes=ent.get("attributes", {}),
            )
        for rel in data.get("relations", []):
            self.add_relation(
                from_entity=rel["from"],
                to_entity=rel["to"],
                relation_type=rel["type"],
                context=rel.get("context", {}),
            )

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the SQLite connection."""
        self._conn.close()

    def __enter__(self) -> "GraphMemory":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
