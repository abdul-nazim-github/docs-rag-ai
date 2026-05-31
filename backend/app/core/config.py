"""
Application configuration — loads all settings from environment variables.

Usage:
    from app.core.config import settings
    print(settings.OPENAI_MODEL)

All values are read from the `.env` file (or environment) at startup.
Nothing is hardcoded.
"""

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ── Resolve base directory (backend/) ──────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Typed settings object — validated at startup."""

    # ── OpenAI ─────────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4.1-mini"

    # ── Storage paths (relative to backend/) ───────────────────────────────────
    FAISS_INDEX_PATH: str = "vectorstore/faiss_index"
    UPLOAD_DIR: str = "data/uploads"
    DOCUMENTS_REGISTRY: str = "data/documents.json"

    # ── CORS ───────────────────────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Validators ─────────────────────────────────────────────────────────────

    @field_validator("OPENAI_API_KEY")
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        """Ensure the OpenAI API key is provided and non-empty."""
        if not v or not v.strip():
            raise ValueError(
                "OPENAI_API_KEY is required. "
                "Set it in backend/.env or as an environment variable."
            )
        return v.strip()

    # ── Computed helpers ───────────────────────────────────────────────────────

    @property
    def BASE_DIR(self) -> Path:
        """Absolute path to the base directory (backend/)."""
        return BASE_DIR

    @property
    def faiss_index_abs_path(self) -> Path:
        """Absolute path to the FAISS index directory."""
        return BASE_DIR / self.FAISS_INDEX_PATH

    @property
    def upload_dir_abs_path(self) -> Path:
        """Absolute path to the upload directory."""
        return BASE_DIR / self.UPLOAD_DIR

    @property
    def documents_registry_abs_path(self) -> Path:
        """Absolute path to the documents registry JSON file."""
        return BASE_DIR / self.DOCUMENTS_REGISTRY

    @property
    def cors_origins(self) -> list[str]:
        """List of allowed CORS origins derived from FRONTEND_URL."""
        return [self.FRONTEND_URL]


# ── Singleton ──────────────────────────────────────────────────────────────────
settings = Settings()  # type: ignore[call-arg]
