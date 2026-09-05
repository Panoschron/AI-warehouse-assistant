"""Runtime settings. Secrets come from the environment only — never commit keys."""
from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent

DATA_DIR = BACKEND_DIR / "storage" / "samples"
EXPORT_DIR = BACKEND_DIR / "storage"
EMBEDDINGS_DIR = EXPORT_DIR / "embeddings"
SAMPLE_CATALOG_CSV = DATA_DIR / "softone_warehouse_catalog.csv"

FAISS_INDEX_FILE = EMBEDDINGS_DIR / "index.faiss"
META_DATA_FILE = EMBEDDINGS_DIR / "metadata.jsonl"

DEFAULT_EMBEDDING_MODEL = os.environ.get(
    "EMBEDDING_MODEL",
    "paraphrase-multilingual-MiniLM-L12-v2",
)
DEFAULT_TOP_K = int(os.environ.get("DEFAULT_TOP_K", "5"))

# Cosine / inner-product floor for a "real" match. FAISS always returns k neighbors;
# below this, treat the hit as noise so empty-state queries stay empty.
MIN_MATCH_SCORE = float(os.environ.get("MIN_MATCH_SCORE", "0.40"))

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPEN_AI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

REQUIREMENTS_FILE = ROOT_DIR / "requirements.txt"
