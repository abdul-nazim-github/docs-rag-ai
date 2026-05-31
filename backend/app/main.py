"""
FastAPI application entry point.

Configures:
    - CORS middleware (origin read from FRONTEND_URL env var)
    - API router inclusion
    - Startup directory creation
    - Logging

Start with:
    uv run uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan ───────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan — runs once at startup and shutdown.

    Startup:
        - Ensure upload and vectorstore directories exist.
        - Log configuration summary.

    Shutdown:
        - (nothing to clean up currently)
    """
    # ── Startup ────────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("  Docs RAG AI — Starting up")
    logger.info("=" * 60)

    # Create required directories
    settings.upload_dir_abs_path.mkdir(parents=True, exist_ok=True)
    settings.faiss_index_abs_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("  Model        : %s", settings.OPENAI_MODEL)
    logger.info("  FAISS path   : %s", settings.faiss_index_abs_path)
    logger.info("  Upload dir   : %s", settings.upload_dir_abs_path)
    logger.info("  Frontend URL : %s", settings.FRONTEND_URL)
    logger.info("=" * 60)

    yield

    # ── Shutdown ───────────────────────────────────────────────────────────
    logger.info("Docs RAG AI — Shutting down.")


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Docs RAG AI",
    description=(
        "Retrieval-Augmented Generation API — upload documents, "
        "index them into a FAISS vector store, and query them "
        "using OpenAI language models."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS — read allowed origin from environment ───────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────────────────────────────────
app.include_router(router)
