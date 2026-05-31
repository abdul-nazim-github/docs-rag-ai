"""
API routes — all HTTP endpoints for the RAG application.

Endpoints:
    POST   /api/upload              Upload and index a document
    POST   /api/query               Query the RAG chain
    GET    /api/documents           List uploaded documents
    DELETE /api/documents/{filename} Delete a specific document
    GET    /api/health              Health check
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, status

from app.api.schemas import (
    DocumentInfo,
    DocumentListResponse,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    SourceInfo,
    UploadResponse,
)
from app.core.config import settings
from app.services.document_processor import SUPPORTED_EXTENSIONS, document_processor
from app.services.rag_chain import rag_chain
from app.services.vector_store import vector_store_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["rag"])


# ── Upload ─────────────────────────────────────────────────────────────────────


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index a document",
)
async def upload_document(file: UploadFile) -> UploadResponse:
    """
    Upload a document file, process it into chunks, and add to the
    FAISS vector store.
    """
    # Validate filename
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )

    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file type: '{ext}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            ),
        )

    # Ensure upload directory exists
    upload_dir = settings.upload_dir_abs_path
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save file to disk
    file_path = upload_dir / file.filename
    try:
        content = await file.read()
        file_path.write_bytes(content)
        logger.info("Saved uploaded file: %s (%d bytes)", file.filename, len(content))
    except Exception as exc:
        logger.exception("Failed to save uploaded file: %s", file.filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {exc}",
        ) from exc

    # Process into chunks
    try:
        chunks = document_processor.process_file(file_path)
    except Exception as exc:
        logger.exception("Failed to process file: %s", file.filename)
        # Clean up the saved file on processing failure
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to process file: {exc}",
        ) from exc

    # Index chunks into FAISS
    try:
        vector_store_manager.add_documents(chunks)
    except Exception as exc:
        logger.exception("Failed to index file: %s", file.filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index file: {exc}",
        ) from exc

    return UploadResponse(
        filename=file.filename,
        chunks=len(chunks),
        message=f"Successfully uploaded and indexed '{file.filename}' ({len(chunks)} chunks).",
    )


# ── Query ──────────────────────────────────────────────────────────────────────


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Query the RAG chain",
)
async def query_documents(request: QueryRequest) -> QueryResponse:
    """
    Ask a question about the uploaded documents. The RAG chain retrieves
    relevant context and generates an answer using OpenAI.
    """
    try:
        result = await rag_chain.query(request.question)
    except Exception as exc:
        logger.exception("RAG query failed: %s", request.question)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {exc}",
        ) from exc

    return QueryResponse(
        answer=result["answer"],
        sources=[SourceInfo(**s) for s in result["sources"]],
    )


# ── Documents ──────────────────────────────────────────────────────────────────


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List uploaded documents",
)
async def list_documents() -> DocumentListResponse:
    """Return metadata for all uploaded documents."""
    upload_dir = settings.upload_dir_abs_path
    if not upload_dir.exists():
        return DocumentListResponse(documents=[], total=0)

    documents: list[DocumentInfo] = []
    for file_path in sorted(upload_dir.iterdir()):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            stat = file_path.stat()
            documents.append(
                DocumentInfo(
                    filename=file_path.name,
                    size=stat.st_size,
                    uploaded_at=datetime.fromtimestamp(
                        stat.st_mtime, tz=timezone.utc
                    ).isoformat(),
                )
            )

    return DocumentListResponse(documents=documents, total=len(documents))


@router.delete(
    "/documents/{filename}",
    status_code=status.HTTP_200_OK,
    summary="Delete a specific document",
)
async def delete_document(filename: str) -> dict:
    """
    Delete an uploaded document from disk.

    Note: This removes the file but does NOT remove its vectors from the
    FAISS index. To fully refresh the index, re-upload all remaining documents.
    """
    upload_dir = settings.upload_dir_abs_path
    file_path = upload_dir / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{filename}' not found.",
        )

    file_path.unlink()
    logger.info("Deleted document: %s", filename)

    return {
        "message": f"Document '{filename}' deleted successfully.",
        "note": (
            "The vectors for this document are still in the FAISS index. "
            "Re-upload remaining documents to refresh the index if needed."
        ),
    }


# ── Health ─────────────────────────────────────────────────────────────────────


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
)
async def health_check() -> HealthResponse:
    """Return the application health status and index statistics."""
    return HealthResponse(
        status="ok",
        indexed_documents=vector_store_manager.document_count,
        model=settings.OPENAI_MODEL,
    )
