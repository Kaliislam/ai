"""ChromaDB-based episodic memory with sentence-transformers embeddings."""

import hashlib
from typing import Any

import chromadb
from chromadb.config import Settings


class EpisodicMemory:
    """Vector episodic memory backed by ChromaDB.

    Each episode is stored as a document with optional metadata and
    retrieved via similarity search.
    """

    def __init__(
        self,
        persist_dir: str = "./data/chroma",
        collection_name: str = "episodic_memory",
    ) -> None:
        """Initialize the ChromaDB client and collection.

        Args:
            persist_dir: Directory where ChromaDB persists data.
            collection_name: Name of the ChromaDB collection to use.
        """
        self.client = chromadb.Client(
            Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=persist_dir,
                anonymized_telemetry=False,
            )
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, text: str, metadata: dict[str, Any] | None = None) -> str:
        """Store a new episode in vector memory.

        Args:
            text: The episode text to embed and store.
            metadata: Optional key-value metadata.

        Returns:
            The generated document ID (SHA-256 hash of the text).
        """
        doc_id = hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]
        self.collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[doc_id],
        )
        return doc_id

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        """Search for relevant episodes using cosine similarity.

        Args:
            query: The text query.
            k: Number of top results to return.

        Returns:
            List of result dictionaries containing text, metadata, and distance.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=min(k, self.collection.count() or 1),
            include=["metadatas", "documents", "distances"],
        )
        episodes: list[dict[str, Any]] = []
        if not results["ids"]:
            return episodes
        ids = results["ids"][0]
        docs = results["documents"][0] if results["documents"] else []
        metas = results["metadatas"][0] if results["metadatas"] else []
        dists = results["distances"][0] if results["distances"] else []
        for idx, doc_id in enumerate(ids):
            episodes.append(
                {
                    "id": doc_id,
                    "text": docs[idx] if idx < len(docs) else "",
                    "metadata": metas[idx] if idx < len(metas) else {},
                    "distance": dists[idx] if idx < len(dists) else None,
                }
            )
        return episodes
