"""
core/config.py — Centralized, environment-based configuration for BA Agent.
All other modules should import from here (or from the root config.py shim).
"""
import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    # ── OpenRouter API ─────────────────────────────────────────────
    OPENROUTER_API_KEY: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    OPENROUTER_BASE_URL: str = field(default_factory=lambda: os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"))

    # Primary model definition
    MODEL_NAME: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "meta-llama/llama-3.3-70b-instruct"))

    # LLM generation settings
    MAX_TOKENS: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS", "8000")))
    TEMPERATURE: float = field(default_factory=lambda: float(os.getenv("TEMPERATURE", "0.7")))

    # ── Retry ─────────────────────────────────────────────────────
    RETRY_DELAY: int = field(default_factory=lambda: int(os.getenv("RETRY_DELAY", "4")))
    MAX_RETRIES: int = field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))

    # ── Database ──────────────────────────────────────────────────
    # Default: SQLite (zero-setup). Swap DATABASE_URL in .env for PostgreSQL.
    DATABASE_URL: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./ba_agent.db")
    )

    # ── Paths ─────────────────────────────────────────────────────
    OUTPUT_DIR: str = field(default_factory=lambda: os.getenv("OUTPUT_DIR", "output"))
    CHROMA_PATH: str = field(default_factory=lambda: os.getenv("CHROMA_PATH", "data/vector_store"))
    INPUT_PDF_DIR: str = field(default_factory=lambda: os.getenv("INPUT_PDF_DIR", "data/input_pdfs"))

    # ── Embeddings ────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200


# Singleton instance — import this everywhere
settings = Settings()
