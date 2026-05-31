"""
API schemas — Pydantic models for request / response validation.

All API contracts are defined here so both routes and clients have a
single source of truth.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Query ──────────────────────────────────────────────────────────────────────


class QueryRequest(BaseModel):
    """Incoming user question."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The question to ask about the uploaded documents.",
        examples=["What is the main topic of this document?"],
    )


class SourceInfo(BaseModel):
    """A single source citation returned alongside an answer."""

    filename: str = Field(..., description="Name of the source document.")
    snippet: str = Field(..., description="Relevant excerpt from the source.")


class QueryResponse(BaseModel):
    """Generated answer with source citations."""

    answer: str = Field(..., description="The AI-generated answer.")
    sources: list[SourceInfo] = Field(
        default_factory=list,
        description="Document sources used to generate the answer.",
    )


# ── Upload ─────────────────────────────────────────────────────────────────────


class UploadResponse(BaseModel):
    """Result of a document upload and indexing operation."""

    filename: str = Field(..., description="Name of the uploaded file.")
    chunks: int = Field(..., description="Number of text chunks created.")
    message: str = Field(..., description="Human-readable status message.")


# ── Documents ──────────────────────────────────────────────────────────────────


class DocumentInfo(BaseModel):
    """Metadata for an uploaded document."""

    filename: str = Field(..., description="Name of the file.")
    size: int = Field(..., description="File size in bytes.")
    uploaded_at: str = Field(..., description="ISO-8601 upload timestamp.")


class DocumentListResponse(BaseModel):
    """List of all uploaded documents."""

    documents: list[DocumentInfo] = Field(default_factory=list)
    total: int = Field(0, description="Total number of uploaded documents.")


# ── Health ─────────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    """Application health status."""

    status: str = Field("ok", description="Health status string.")
    indexed_documents: int = Field(
        0, description="Number of vectors in the FAISS index."
    )
    model: str = Field(..., description="Active OpenAI model name.")
