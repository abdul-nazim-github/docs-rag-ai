"""
Document service — orchestrates document registry management, uploads,
deletions, and vector store synchronization (FAISS rebuilds).
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.document_processor import document_processor
from app.services.vector_store import vector_store_manager

logger = logging.getLogger(__name__)


class DocumentService:
    """Manages the lifecycle of uploaded documents and synchronises with FAISS."""

    def __init__(self) -> None:
        self.registry_path = settings.documents_registry_abs_path

    def _ensure_registry_exists(self) -> None:
        """Create documents.json if it does not exist."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.registry_path.exists():
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump({"documents": []}, f, indent=2)

    def load_registry(self) -> list[dict[str, Any]]:
        """Load documents registry from JSON file."""
        self._ensure_registry_exists()
        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("documents", [])
        except Exception:
            logger.exception(
                "Failed to load document registry from %s", self.registry_path
            )
            return []

    def save_registry(self, documents: list[dict[str, Any]]) -> None:
        """Save documents registry to JSON file."""
        self._ensure_registry_exists()
        try:
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump({"documents": documents}, f, indent=2)
        except Exception:
            logger.exception(
                "Failed to save document registry to %s", self.registry_path
            )
            raise

    def initialize(self) -> None:
        """
        On FastAPI startup:
        * Read documents.json
        * Load existing uploaded documents
        * Load FAISS index if available
        * If index missing: Rebuild from uploaded documents
        """
        logger.info("Initializing DocumentService...")
        self._ensure_registry_exists()
        docs = self.load_registry()

        # Validate that registered files actually exist on disk, remove missing files from registry
        valid_docs = []
        changed = False
        for doc in docs:
            doc_path = Path(doc["path"])
            abs_path = (
                settings.BASE_DIR / doc_path
                if not doc_path.is_absolute()
                else doc_path
            )
            if abs_path.exists():
                valid_docs.append(doc)
            else:
                logger.warning(
                    "Document in registry missing from disk: %s", doc["filename"]
                )
                changed = True

        if changed:
            logger.info("Updating registry to remove missing files.")
            self.save_registry(valid_docs)
            docs = valid_docs

        # Check if FAISS index is ready
        if not vector_store_manager.is_ready:
            logger.warning(
                "FAISS index missing or uninitialized at startup. Rebuilding from uploaded documents..."
            )
            if docs:
                self.rebuild_vectorstore(docs)
            else:
                logger.info("No documents to index. Vector store remains empty.")
        else:
            logger.info(
                "FAISS index is loaded and ready with %d vectors.",
                vector_store_manager.document_count,
            )

    def upload_document(self, filename: str, content: bytes) -> tuple[dict[str, Any], int]:
        """
        Process uploaded file:
        * Save to uploads directory
        * Add metadata to documents.json
        * Process document into chunks
        * Generate embeddings
        * Store chunks with metadata
        """
        upload_dir = settings.upload_dir_abs_path
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / filename

        # Save to disk
        file_path.write_bytes(content)
        size = len(content)

        # Generate metadata
        doc_id = str(uuid.uuid4())
        uploaded_at = datetime.now(timezone.utc).isoformat()
        relative_path = str(file_path.relative_to(settings.BASE_DIR))

        doc_entry = {
            "id": doc_id,
            "filename": filename,
            "uploaded_at": uploaded_at,
            "path": relative_path,
            "size": size,
        }

        registry = self.load_registry()
        # Remove any existing entry with the same filename to handle overwrites cleanly
        registry = [d for d in registry if d["filename"] != filename]
        registry.append(doc_entry)
        self.save_registry(registry)

        # Process document chunks
        try:
            chunks = document_processor.process_file(file_path)
            for chunk in chunks:
                chunk.metadata = {
                    "document_id": doc_id,
                    "filename": filename,
                    "source": filename,  # Keep source for backwards compatibility with citations
                }
            vector_store_manager.add_documents(chunks)
        except Exception:
            logger.exception("Failed to process and index uploaded file: %s", filename)
            # Rollback file write and registry write on failure
            file_path.unlink(missing_ok=True)
            registry = [d for d in registry if d["id"] != doc_id]
            self.save_registry(registry)
            raise

        return doc_entry, len(chunks)

    def list_documents(self) -> list[dict[str, Any]]:
        """Return the list of all registered documents."""
        return self.load_registry()

    def delete_document(self, doc_id: str) -> None:
        """
        Delete document process:
        * Step 1: Remove file from uploads directory
        * Step 2: Remove document from documents.json
        * Step 3: Remove all chunks belonging to that document from FAISS
        * Step 4: Persist updated database (rebuild index from scratch)
        """
        registry = self.load_registry()
        target_doc = None
        for doc in registry:
            if doc["id"] == doc_id:
                target_doc = doc
                break

        if not target_doc:
            raise FileNotFoundError(f"Document with ID '{doc_id}' not found.")

        # Step 1: Remove file from uploads
        doc_path = Path(target_doc["path"])
        abs_path = (
            settings.BASE_DIR / doc_path
            if not doc_path.is_absolute()
            else doc_path
        )
        abs_path.unlink(missing_ok=True)
        logger.info("Deleted file from disk: %s", abs_path)

        # Step 2: Remove document from documents.json
        updated_registry = [d for d in registry if d["id"] != doc_id]
        self.save_registry(updated_registry)

        # Step 3 & 4: Rebuild vector index from remaining documents
        logger.info("Synchronizing FAISS index after deletion...")
        self.rebuild_vectorstore(updated_registry)

    def rebuild_vectorstore(self, registry_docs: list[dict[str, Any]]) -> None:
        """Rebuild the vector store from scratch using remaining registry documents."""
        vector_store_manager.reset()

        if not registry_docs:
            logger.info("No documents remaining. FAISS index reset to empty.")
            return

        all_chunks = []
        for doc in registry_docs:
            doc_path = Path(doc["path"])
            abs_path = (
                settings.BASE_DIR / doc_path
                if not doc_path.is_absolute()
                else doc_path
            )

            if not abs_path.exists():
                logger.error(
                    "Registry file missing on disk during rebuild: %s", abs_path
                )
                continue

            try:
                chunks = document_processor.process_file(abs_path)
                for chunk in chunks:
                    chunk.metadata = {
                        "document_id": doc["id"],
                        "filename": doc["filename"],
                        "source": doc["filename"],
                    }
                all_chunks.extend(chunks)
            except Exception:
                logger.exception("Failed to process '%s' during index rebuild", doc["filename"])

        if all_chunks:
            logger.info("Re-indexing all remaining chunks into FAISS...")
            vector_store_manager.add_documents(all_chunks)
            logger.info(
                "FAISS index rebuild complete. Total vectors: %d",
                vector_store_manager.document_count,
            )
        else:
            logger.warning("No chunks produced. Vector store remains uninitialized.")


# ── Module-level singleton ─────────────────────────────────────────────────────
document_service = DocumentService()
