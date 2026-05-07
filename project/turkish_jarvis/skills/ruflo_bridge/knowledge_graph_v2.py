"""Ruflo Knowledge Graph Plugin Bridge v2.

Wraps ``turkish_jarvis.memory.graph.GraphMemory`` and adds
Ruflo-style abstractions:
- entity deduplication / merging
- multi-hop path queries
- graph reasoning helpers (shortest path, centrality sketch)
- LLM-ready graph summaries
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------------


class RufloKnowledgeGraph:
    """Enhanced graph memory bridge inspired by ruflo-knowledge-graph.

    Usage
    -----
    kg = RufloKnowledgeGraph(db_path="./data/kg.db")
    kg.add_entity("Python", "language", {"paradigm": "multi"})
    kg.add_relation("Python", "Guido", "created_by")
    kg.multi_hop("Python", depth=2)
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or "./data/knowledge_graph.db"
        self._graph: Any = None

    # ------------------------------------------------------------------
    # Lazy init
    # ------------------------------------------------------------------

    def _init(self) -> None:
        if self._graph is not None:
            return
        from turkish_jarvis.memory.graph import GraphMemory

        self._graph = GraphMemory(db_path=self.db_path)
        logger.info("[ruflo-knowledge-graph] GraphMemory initialised at %s", self.db_path)

    # ------------------------------------------------------------------
    # Entity / relation CRUD
    # ------------------------------------------------------------------

    def add_entity(self, name: str, type: str = "unknown", attributes: Optional[Dict[str, Any]] = None) -> int:
        """Add or upsert an entity."""
        self._init()
        return self._graph.add_entity(name, type, attributes)

    def get_entity(self, name: str) -> Optional[Dict[str, Any]]:
        """Fetch entity with its direct relations."""
        self._init()
        return self._graph.query_entity(name)

    def add_relation(self, from_entity: str, to_entity: str, relation_type: str, context: Optional[Dict[str, Any]] = None) -> int:
        """Add a directed relation."""
        self._init()
        return self._graph.add_relation(from_entity, to_entity, relation_type, context)

    def get_relations(
        self,
        from_entity: Optional[str] = None,
        to_entity: Optional[str] = None,
        relation_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query relations with optional filters."""
        self._init()
        rels = self._graph.get_relations(from_entity, to_entity, relation_type)
        return [
            {
                "id": r.id,
                "from": r.from_entity,
                "to": r.to_entity,
                "type": r.relation_type,
                "context": r.context,
                "created_at": r.created_at,
            }
            for r in rels
        ]

    def search(self, query: str, limit: int = 20) -> Dict[str, List[Dict[str, Any]]]:
        """Fuzzy search across entities and relations."""
        self._init()
        return self._graph.search_related(query, limit=limit)

    # ------------------------------------------------------------------
    # v2 multi-hop & reasoning
    # ------------------------------------------------------------------

    def multi_hop(self, start_entity: str, depth: int = 2) -> List[Dict[str, Any]]:
        """Breadth-first multi-hop neighbourhood exploration.

        Returns a flat list of relation dicts with an added ``hop`` key.
        """
        self._init()
        visited_nodes: set[str] = {start_entity}
        visited_edges: set[Tuple[str, str, str]] = set()
        results: List[Dict[str, Any]] = []
        frontier: List[Tuple[str, int]] = [(start_entity, 0)]

        while frontier:
            current, hop = frontier.pop(0)
            if hop >= depth:
                continue
            rels = self._graph.get_relations(from_entity=current)
            rels += self._graph.get_relations(to_entity=current)
            for r in rels:
                edge_key = (r.from_entity, r.to_entity, r.relation_type)
                if edge_key in visited_edges:
                    continue
                visited_edges.add(edge_key)
                results.append(
                    {
                        "hop": hop + 1,
                        "from": r.from_entity,
                        "to": r.to_entity,
                        "type": r.relation_type,
                        "context": r.context,
                    }
                )
                other = r.to_entity if r.from_entity == current else r.from_entity
                if other not in visited_nodes:
                    visited_nodes.add(other)
                    frontier.append((other, hop + 1))
        return results

    def find_path(
        self, start: str, end: str, max_depth: int = 4
    ) -> Optional[List[Dict[str, Any]]]:
        """Simple BFS path finder between two entities.

        Returns a list of relation dicts describing the shortest path,
        or ``None`` if no path exists.
        """
        self._init()
        from collections import deque

        queue: deque[tuple[str, List[Dict[str, Any]]]] = deque([(start, [])])
        visited: set[str] = {start}

        while queue:
            current, path = queue.popleft()
            if current == end and path:
                return path
            if len(path) >= max_depth:
                continue
            rels = self._graph.get_relations(from_entity=current)
            rels += self._graph.get_relations(to_entity=current)
            for r in rels:
                other = r.to_entity if r.from_entity == current else r.from_entity
                if other not in visited:
                    visited.add(other)
                    edge = {
                        "from": r.from_entity,
                        "to": r.to_entity,
                        "type": r.relation_type,
                        "context": r.context,
                    }
                    queue.append((other, path + [edge]))
        return None

    def entity_centrality(self, top_k: int = 10) -> List[Dict[str, Any]]:
        """Sketch degree centrality (incoming + outgoing edges)."""
        self._init()
        entities = self._graph.list_entities()
        scores: List[Tuple[str, int]] = []
        for e in entities:
            out_deg = len(self._graph.get_relations(from_entity=e.name))
            in_deg = len(self._graph.get_relations(to_entity=e.name))
            scores.append((e.name, out_deg + in_deg))
        scores.sort(key=lambda x: x[1], reverse=True)
        return [
            {"entity": name, "degree": deg}
            for name, deg in scores[:top_k]
        ]

    # ------------------------------------------------------------------
    # LLM helpers
    # ------------------------------------------------------------------

    def subgraph_to_prompt(self, center_entity: str, depth: int = 1) -> str:
        """Export a local subgraph as an LLM-readable markdown block."""
        self._init()
        entity = self._graph.query_entity(center_entity)
        if entity is None:
            return f"No entity named '{center_entity}' found."
        lines = [
            f"## Entity: {center_entity}",
            f"- type: {entity['entity']['type']}",
            f"- attributes: {json.dumps(entity['entity']['attributes'], ensure_ascii=False)}",
            "",
            "## Relations",
        ]
        for r in entity.get("relations", []):
            lines.append(f"- {r['from']} --[{r['type']}]--> {r['to']}")
        if depth > 1:
            hops = self.multi_hop(center_entity, depth=depth)
            lines.append("")
            lines.append("## Multi-hop neighbourhood")
            for h in hops:
                lines.append(f"- ({h['hop']} hop) {h['from']} --[{h['type']}]--> {h['to']}")
        return "\n".join(lines)

    def apply_extraction(self, extraction_json: Dict[str, Any]) -> Dict[str, int]:
        """Persist LLM-extracted entities and relations."""
        self._init()
        return self._graph.apply_extraction_result(extraction_json)

    # ------------------------------------------------------------------
    # Import / export
    # ------------------------------------------------------------------

    def export_json(self) -> Dict[str, Any]:
        """Dump the entire graph as JSON."""
        self._init()
        return self._graph.export_json()

    def import_json(self, data: Dict[str, Any]) -> None:
        """Import a graph from JSON (merges)."""
        self._init()
        self._graph.import_json(data)

    def summary(self) -> Dict[str, Any]:
        """High-level graph statistics."""
        self._init()
        return self._graph.get_graph_summary()
