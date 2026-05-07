"""LangChain RAG pipeline v2.0 with ChromaDB, batch ingestion,
source-attribution queries, document management, and improved embeddings.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    TextLoader,
    UnstructuredMarkdownLoader,
)
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline v2.0.

    Features
    --------
    * Single or batch document ingestion (TXT, Markdown, PDF).
    * Source-attributed queries (returns chunk + originating file path).
    * Document deletion by ID or by source file.
    * Document listing with metadata.
    * Support for ``nomic-embed-text`` and ``bge-m3`` embedding models.
    * Persistent ChromaDB vector store with configurable chunking.
    """

    # Recommended embedding models (fast, high-quality, multilingual)
    RECOMMENDED_EMBEDDING_MODELS: list[dict[str, str]] = [
        {
            "name": "nomic-embed-text",
            "description": "Hafif, hızlı, çok dilli embedding. 768 boyut. Türkçe için başarılı.",
            "dimensions": "768",
            "lang": "multilingual",
        },
        {
            "name": "bge-m3",
            "description": "FlagEmbedding M3 — yoğun + seyrek vektör, 1024 boyut. Çok dilli (Türkçe dahil).",
            "dimensions": "1024",
            "lang": "multilingual",
        },
    ]

    def __init__(
        self,
        persist_dir: str = "./data/chroma",
        collection_name: str = "rag_documents",
        ollama_base_url: str = "http://localhost:11434",
        ollama_model: str = "nomic-embed-text",
        chunk_size: int = 800,
        chunk_overlap: int = 100,
    ) -> None:
        """Initialize the RAG pipeline.

        Args:
            persist_dir: ChromaDB persistence directory.
            collection_name: Collection name for RAG documents.
            ollama_base_url: Ollama server base URL.
            ollama_model: Embedding model name.  Recommended values:
                ``'nomic-embed-text'`` (fast, 768-dim) or ``'bge-m3'``
                (dense+sparse, 1024-dim, stronger for multilingual).
            chunk_size: Maximum characters per text chunk.
            chunk_overlap: Overlap between consecutive chunks.
        """
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.ollama_model = ollama_model
        self.embeddings = OllamaEmbeddings(
            base_url=ollama_base_url,
            model=ollama_model,
        )
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_dir,
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    # ================================================================= #
    # Ingestion (single + batch)
    # ================================================================= #

    def add_document(
        self,
        file_path: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[str]:
        """Load a single document, split it, and store chunks.

        Args:
            file_path: Path to TXT, Markdown, or PDF file.
            metadata: Optional metadata to attach to all chunks.

        Returns:
            List of chunk IDs added to the vector store.

        Raises:
            ValueError: If the file type is not supported.
            FileNotFoundError: If the file does not exist.
        """
        return self._ingest_one(file_path, metadata)

    def add_documents_batch(
        self,
        paths: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, list[str] | str]:
        """Ingest multiple documents in one call.

        Args:
            paths: List of file paths.
            metadata: Optional shared metadata for every chunk.

        Returns:
            Dictionary ``{file_path: [chunk_ids] | "error: …"}``.
        """
        results: dict[str, list[str] | str] = {}
        for p in paths:
            try:
                results[p] = self._ingest_one(p, metadata)
            except Exception as exc:
                results[p] = f"error: {type(exc).__name__}: {exc}"
        return results

    def _ingest_one(
        self, file_path: str, metadata: dict[str, Any] | None = None
    ) -> list[str]:
        """Internal ingestion logic for a single file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        suffix = path.suffix.lower()
        if suffix == ".txt":
            loader = TextLoader(str(path), encoding="utf-8")
        elif suffix in (".md", ".markdown"):
            loader = UnstructuredMarkdownLoader(str(path))
        elif suffix == ".pdf":
            try:
                from langchain_community.document_loaders import PyPDFLoader
                loader = PyPDFLoader(str(path))
            except Exception as exc:
                raise ImportError(
                    "PDF support requires `pypdf` or `PyMuPDF`."
                ) from exc
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

        docs = loader.load()
        # Enrich metadata
        base_meta = {
            "source": str(path),
            "filename": path.name,
            "file_type": suffix.lstrip("."),
            "ingested_at": hashlib.sha256(str(path).encode()).hexdigest()[:8],
        }
        if metadata:
            base_meta.update(metadata)

        for doc in docs:
            doc.metadata.update(base_meta)

        chunks = self.splitter.split_documents(docs)
        ids = self.vectorstore.add_documents(chunks)
        return ids

    # ================================================================= #
    # Querying (with sources)
    # ================================================================= #

    def query(
        self, question: str, k: int = 5, filter_dict: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Run a similarity search and return raw chunks.

        Args:
            question: User query string.
            k: Number of top chunks to retrieve (max 10).
            filter_dict: Optional Chroma metadata filter.

        Returns:
            List of chunk dictionaries with ``content`` and ``metadata``.
        """
        docs: list[Document] = self.vectorstore.similarity_search(
            question,
            k=min(k, 10),
            filter=filter_dict,
        )
        return [{"content": d.page_content, "metadata": d.metadata} for d in docs]

    def query_with_sources(
        self, question: str, k: int = 5, filter_dict: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Run a similarity search and return an aggregated, source-attributed result.

        Args:
            question: User query string.
            k: Number of top chunks to retrieve (max 10).
            filter_dict: Optional Chroma metadata filter.

        Returns:
            Dictionary with the following keys:

            * ``question`` — the original query.
            * ``chunks`` — list of chunk dicts (content + metadata).
            * ``sources`` — deduplicated list of source file paths.
            * ``source_count`` — number of unique sources.
        """
        chunks = self.query(question, k=k, filter_dict=filter_dict)
        sources = sorted({c["metadata"].get("source", "unknown") for c in chunks})
        return {
            "question": question,
            "chunks": chunks,
            "sources": sources,
            "source_count": len(sources),
        }

    # ================================================================= #
    # Document management (delete / list)
    # ================================================================= #

    def delete_document(
        self, doc_id: str | None = None, source_path: str | None = None
    ) -> int:
        """Delete chunks from the vector store by ID or by originating source path.

        At least one of ``doc_id`` or ``source_path`` must be provided.

        Args:
            doc_id: Exact chunk ID to delete.
            source_path: Delete every chunk whose ``metadata.source`` equals this path.

        Returns:
            Number of deleted chunks.

        Raises:
            ValueError: If neither ``doc_id`` nor ``source_path`` is given.
        """
        if doc_id is None and source_path is None:
            raise ValueError("Provide at least doc_id or source_path.")

        if doc_id is not None:
            try:
                self.vectorstore._collection.delete(ids=[doc_id])
                return 1
            except Exception:
                return 0

        # Delete by source path using metadata filter
        if source_path is not None:
            try:
                self.vectorstore._collection.delete(
                    where={"source": source_path}
                )
                # ChromaDB delete does not return a count; approximate via peek
                return -1  # unknown count
            except Exception:
                return 0

        return 0  # pragma: no cover

    def list_documents(self, limit: int = 1000) -> list[dict[str, Any]]:
        """Return a deduplicated list of ingested documents with metadata.

        Args:
            limit: Maximum number of chunks to inspect.

        Returns:
            List of document metadata dicts: ``source``, ``filename``,
            ``file_type``, and any custom metadata fields.
        """
        try:
            data = self.vectorstore._collection.get(limit=limit)
        except Exception:
            return []

        metas = data.get("metadatas") or []
        seen: set[str] = set()
        results: list[dict[str, Any]] = []
        for meta in metas:
            if not meta:
                continue
            source = meta.get("source", "unknown")
            if source in seen:
                continue
            seen.add(source)
            results.append(
                {
                    "source": source,
                    "filename": meta.get("filename", Path(source).name),
                    "file_type": meta.get("file_type", "unknown"),
                    **{k: v for k, v in meta.items() if k not in ("source", "filename", "file_type")},
                }
            )
        return results

    # ================================================================= #
    # Utility
    # ================================================================= #

    def get_embedding_model_info(self) -> dict[str, str]:
        """Return information about the currently configured embedding model."""
        return {
            "model": self.ollama_model,
            "persist_dir": self.persist_dir,
            "collection": self.collection_name,
        }
