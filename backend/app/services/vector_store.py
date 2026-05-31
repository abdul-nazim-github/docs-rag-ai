"""
Vector store manager — creates, persists, and queries a FAISS index.

Uses OpenAI embeddings to vectorize document chunks and stores the index
on disk so it survives server restarts.
"""

from __future__ import annotations

import logging
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manage a FAISS vector store backed by OpenAI embeddings."""

    def __init__(self) -> None:
        self._embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY,
        )
        self._store: FAISS | None = None

        # Attempt to load an existing index from disk
        self._try_load_existing_index()

    # ── Public API ─────────────────────────────────────────────────────────────

    @property
    def is_ready(self) -> bool:
        """Return True if the vector store has been initialised with documents."""
        return self._store is not None

    @property
    def document_count(self) -> int:
        """Return the number of vectors currently in the store."""
        if self._store is None:
            return 0
        return self._store.index.ntotal  # type: ignore[union-attr]

    def add_documents(self, documents: list[Document]) -> int:
        """
        Add document chunks to the vector store and persist to disk.

        Args:
            documents: List of LangChain Document chunks.

        Returns:
            Total number of vectors after insertion.
        """
        if not documents:
            logger.warning("add_documents called with empty list — skipping.")
            return self.document_count

        if self._store is None:
            # Create a brand-new FAISS index
            logger.info("Creating new FAISS index with %d chunks.", len(documents))
            self._store = FAISS.from_documents(documents, self._embeddings)
        else:
            # Merge new documents into the existing index
            logger.info("Adding %d chunks to existing FAISS index.", len(documents))
            self._store.add_documents(documents)

        self._save_index()
        return self.document_count

    def similarity_search(self, query: str, k: int = 4) -> list[Document]:
        """
        Retrieve the top-k most relevant document chunks for a query.

        Args:
            query: User question / search string.
            k: Number of results to return.

        Returns:
            List of matching Document objects.

        Raises:
            RuntimeError: If no documents have been indexed yet.
        """
        if self._store is None:
            raise RuntimeError(
                "No documents have been indexed yet. "
                "Upload at least one document before querying."
            )

        return self._store.similarity_search(query, k=k)

    def get_retriever(self, k: int = 4):
        """
        Return a LangChain-compatible retriever backed by this vector store.

        Args:
            k: Number of documents to retrieve per query.

        Returns:
            A VectorStoreRetriever instance.

        Raises:
            RuntimeError: If no documents have been indexed yet.
        """
        if self._store is None:
            raise RuntimeError(
                "No documents have been indexed yet. "
                "Upload at least one document before querying."
            )

        return self._store.as_retriever(search_kwargs={"k": k})

    def reset(self) -> None:
        """Delete the in-memory index and remove persisted files."""
        self._store = None
        index_path = settings.faiss_index_abs_path
        if index_path.exists():
            import shutil

            shutil.rmtree(index_path)
            logger.info("Deleted FAISS index at %s", index_path)

    # ── Private helpers ────────────────────────────────────────────────────────

    def _try_load_existing_index(self) -> None:
        """Load a previously persisted FAISS index if it exists on disk."""
        index_path = settings.faiss_index_abs_path
        if index_path.exists() and any(index_path.iterdir()):
            try:
                logger.info("Loading existing FAISS index from %s", index_path)
                self._store = FAISS.load_local(
                    str(index_path),
                    self._embeddings,
                    allow_dangerous_deserialization=True,
                )
                logger.info(
                    "Loaded FAISS index with %d vectors.", self.document_count
                )
            except Exception:
                logger.exception("Failed to load FAISS index — starting fresh.")
                self._store = None

    def _save_index(self) -> None:
        """Persist the current FAISS index to disk."""
        if self._store is None:
            return
        index_path = settings.faiss_index_abs_path
        index_path.mkdir(parents=True, exist_ok=True)
        self._store.save_local(str(index_path))
        logger.info("Saved FAISS index to %s", index_path)


# ── Module-level singleton ─────────────────────────────────────────────────────
vector_store_manager = VectorStoreManager()
