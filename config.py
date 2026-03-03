"""
config.py — Backward-compatibility shim.
All new code should import from core.config.settings directly.
This file re-exports the values that legacy modules (if any) still reference.
"""
from core.config import settings

# Legacy flat exports (used by old imports)
OPENROUTER_API_KEY  = settings.OPENROUTER_API_KEY
OPENROUTER_BASE_URL = settings.OPENROUTER_BASE_URL
MODEL_NAME      = settings.MODEL_NAME
MAX_TOKENS      = settings.MAX_TOKENS
RETRY_DELAY     = settings.RETRY_DELAY
MAX_RETRIES     = settings.MAX_RETRIES
OUTPUT_DIR      = settings.OUTPUT_DIR
CHROMA_PATH     = settings.CHROMA_PATH
INPUT_PDF_DIR   = settings.INPUT_PDF_DIR
EMBEDDING_MODEL = settings.EMBEDDING_MODEL
CHUNK_SIZE      = settings.CHUNK_SIZE
CHUNK_OVERLAP   = settings.CHUNK_OVERLAP