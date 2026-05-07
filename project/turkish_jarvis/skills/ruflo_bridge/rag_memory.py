"""Ruflo RAG Memory Plugin Bridge.

Wraps the existing ``turkish_jarvis.memory.rag.RAGPipeline`` and adds
Ruflo-style memory abstractions: conversation-aware retrieval,
historical context injection, and a unified query layer that
combines vector search with short-term episodic memory.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------------


class RufloRAGMemory:
    """Unified retrieval bridge: RAG vector store + episodic memory.

    Parameters
    ----------
    persist_dir : str
        ChromaDB persistence directory.
    collection_name : str
        ChromaDB collection name.
    ollama_model : str
        Embedding model name (e.g. ``nomic-embed-text``).
    """

    def __init__(
        self,
        persist_dir: str = "./data/chroma",
        collection_name: str = "ruflo_rag_memory",
        ollama_base_url: str = "http://localhost:11434",
        ollama_model: str = "nomic-embed-text",
        chunk_size: int = 800,
        chunk_overlap: int = 100,
    ) -> None:
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.ollama_model = ollama_model
        self._rag: Any = None
        self._episodic: Any = None
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._ollama_base_url = ollama_base_url

    # ------------------------------------------------------------------
    # Lazy init
    # ------------------------------------------------------------------

    def _init_rag(self) -> None:
        if self._rag is not None:
            return
        from turkish_jarvis.memory.rag import RAGPipeline

        self._rag = RAGPipeline(
            persist_dir=self.persist_dir,
            collection_name=self.collection_name,
            ollama_base_url=self._ollama_base_url,
            ollama_model=self.ollama_model,
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
        )
        logger.info("[ruflo-rag-memory] RAGPipeline initialised")

    def _init_episodic(self) -> None:
        if self._episodic is not None:
            return
        try:
            from turkish_jarvis.memory.episodic import EpisodicMemory

            self._episodic = EpisodicMemory()
            logger.info("[ruflo-rag-memory] EpisodicMemory initialised")
        except Exception as exc:
            logger.warning("[ruflo-rag-memory] EpisodicMemory unavailable: %s", exc)
            self._episodic = None

    # ------------------------------------------------------------------
    # Document ingestion
    # ------------------------------------------------------------------

    def add_document(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        """Ingest a single document into the vector store."""
        self._init_rag()
        ids = self._rag.add_document(file_path, metadata=metadata)
        logger.info("[ruflo-rag-memory] added %s -> %d chunks", file_path, len(ids))
        return ids

    def add_documents(self, paths: List[str], metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Batch ingest multiple documents."""
        self._init_rag()
        results = self._rag.add_documents_batch(paths, metadata=metadata)
        ok = sum(1 for v in results.values() if isinstance(v, list))
        logger.info("[ruflo-rag-memory] batch added %d/%d ok", ok, len(paths))
        return results

    # ------------------------------------------------------------------
    # Retrieval (RAG + episodic hybrid)
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        k: int = 5,
        include_history: bool = True,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Hybrid retrieval: vector chunks + recent episodic memory.

        Returns
        -------
        dict with keys ``chunks``, ``sources``, ``history_context``.
        """
        self._init_rag()
        rag_result = self._rag.query_with_sources(query, k=k, filter_dict=filter_dict)

        history_context = ""
        if include_history:
            self._init_episodic()
            if self._episodic is not None:
                try:
                    recent = self._episodic.get_recent(limit=5)
                    if recent:
                        history_context = "\n".join(
                            f"- [{r.get('timestamp', '?')}] {r.get('content', '')[:200]}"
                            for r in recent
                        )
                except Exception as exc:
                    logger.debug("[ruflo-rag-memory] episodic fetch failed: %s", exc)

        return {
            "query": query,
            "chunks": rag_result.get("chunks", []),
            "sources": rag_result.get("sources", []),
            "source_count": rag_result.get("source_count", 0),
            "history_context": history_context,
        }

    def retrieve_to_prompt(
        self,
        query: str,
        k: int = 5,
        include_history: bool = True,
    ) -> str:
        """Retrieve and format everything into a single LLM prompt string."""
        result = self.retrieve(query, k=k, include_history=include_history)
        lines = [
            "## Retrieved Context",
            "",
        ]
        for i, chunk in enumerate(result["chunks"][:k], 1):
            content = chunk.get("content", "")[:600]
            meta = chunk.get("metadata", {})
            source = meta.get("source", "unknown")
            lines.append(f"### Chunk {i} (source: {source})")
            lines.append(content)
            lines.append("")
        if result.get("history_context"):
            lines.append("## Recent Memory")
            lines.append(result["history_context"])
            lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Management
    # ------------------------------------------------------------------

    def delete_document(self, doc_id: Optional[str] = None, source_path: Optional[str] = None) -> int:
        """Delete by chunk ID or source path."""
        self._init_rag()
        return self._rag.delete_document(doc_id=doc_id, source_path=source_path)

    def list_documents(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """List ingested documents."""
        self._init_rag()
        return self._rag.list_documents(limit=limit)

    def stats(self) -> Dict[str, Any]:
        """Quick stats about the RAG store."""
        self._init_rag()
        docs = self._rag.list_documents(limit=10000)
        return {
            "total_documents": len(docs),
            "collection": self.collection_name,
            "embedding_model": self.ollama_model,
            "persist_dir": self.persist_dir,
        }

    # ------------------------------------------------------------------
    # Episodic memory passthrough
    # ------------------------------------------------------------------

    def remember(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store a short-term memory entry."""
        self._init_episodic()
        if self._episodic is None:
            logger.warning("[ruflo-rag-memory] episodic memory unavailable; dropping entry")
            return
        try:
            self._episodic.store(content, metadata=metadata)
        except Exception as exc:
            logger.warning("[ruflo-rag-memory] remember failed: %s", exc)

    def recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent episodic entries."""
        self._init_episodic()
        if self._episodic is None:
            return []
        try:
            return self._episodic.get_recent(limit=limit)
        except Exception as exc:
            logger.warning("[ruflo-rag-memory] recent_memories failed: %s", exc)
            return []
