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

# Combined (cosine + lexical bonus) floor. Misspell / alias hits like
# "rakor" land ~0.50 only after the bonus — do not raise this to "fix" junk.
MIN_MATCH_SCORE = float(os.environ.get("MIN_MATCH_SCORE", "0.40"))
# Cosine-only (no shared tokens) hits in this tiny catalog cluster ~0.40–0.65
# for Latin junk. Require a much stronger embedding score when ungrounded.
MIN_SEMANTIC_SCORE = float(os.environ.get("MIN_SEMANTIC_SCORE", "0.75"))
# After a real leader is found, drop also-rans this far below the top score.
RELATIVE_SCORE_GAP = float(os.environ.get("RELATIVE_SCORE_GAP", "0.18"))

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPEN_AI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

REQUIREMENTS_FILE = ROOT_DIR / "requirements.txt"
