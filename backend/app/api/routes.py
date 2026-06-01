"""
API routes — all HTTP endpoints for the RAG application.

Endpoints:
    POST   /api/upload or /upload                     Upload and index a document
    POST   /api/query or /query                       Query the RAG chain (streaming)
    GET    /api/documents or /documents               List uploaded documents registry
    DELETE /api/documents/{id} or /documents/{id}     Delete a document by unique ID
    GET    /api/health or /health                     Health check
"""

from __future__ import annotations

import logging
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from app.api.schemas import (
    DocumentRegistryItem,
    HealthResponse,
    QueryRequest,
    UploadResponse,
)
from app.core.config import settings
from app.services.document_processor import SUPPORTED_EXTENSIONS
from app.services.rag_chain import rag_chain
from app.services.vector_store import vector_store_manager
from app.services.document_service import document_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["rag"])


# ── Upload ─────────────────────────────────────────────────────────────────────


@router.post(
    "/api/upload",
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

    try:
        content = await file.read()
        doc_entry, chunks_count = document_service.upload_document(
            file.filename, content
        )
    except Exception as exc:
        logger.exception("Failed to upload and process file: %s", file.filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process and index file: {exc}",
        ) from exc

    return UploadResponse(
        filename=file.filename,
        chunks=chunks_count,
        message=f"Successfully uploaded and indexed '{file.filename}' ({chunks_count} chunks).",
    )


# ── Query ──────────────────────────────────────────────────────────────────────


@router.post(
    "/api/query",
    summary="Query the RAG chain (streaming)",
)
async def query_documents(request: QueryRequest) -> StreamingResponse:
    """
    Ask a question about the uploaded documents. The RAG chain retrieves
    relevant context and streams generated answers in real time using OpenAI.
    """
    async def event_generator():
        try:
            async for chunk in rag_chain.stream_query(request.question):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as exc:
            logger.exception("RAG streaming query failed: %s", request.question)
            yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ── Documents ──────────────────────────────────────────────────────────────────


@router.get(
    "/api/documents",
    response_model=list[DocumentRegistryItem],
    summary="List uploaded documents from registry",
)
async def list_documents() -> list[DocumentRegistryItem]:
    """Return metadata registry for all uploaded documents."""
    try:
        registry_docs = document_service.list_documents()
        return [DocumentRegistryItem(**doc) for doc in registry_docs]
    except Exception as exc:
        logger.exception("Failed to list documents from registry")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load documents list: {exc}",
        ) from exc


@router.delete(
    "/api/documents/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a specific document by its unique ID",
)
async def delete_document(document_id: str) -> dict:
    """
    Delete an uploaded document by its ID, clearing it from the file storage,
    registry metadata, and FAISS index.
    """
    try:
        document_service.delete_document(document_id)
        return {
            "success": True,
            "message": "Document deleted successfully",
        }
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Failed to delete document: %s", document_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {exc}",
        ) from exc


# ── Health ─────────────────────────────────────────────────────────────────────


@router.get(
    "/api/health",
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
