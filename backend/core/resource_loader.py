from pathlib import Path
from typing import List, Dict, Tuple
import json
import logging

import faiss  # type: ignore
from sentence_transformers import SentenceTransformer

from backend import app_settings

logger = logging.getLogger(__name__)


def load_model(model_name: str) -> SentenceTransformer:
    """Load the SentenceTransformer model."""
    return SentenceTransformer(model_name)


def load_index(index_path: Path) -> faiss.Index:
    """Load FAISS index from disk."""
    p = Path(index_path)
    if not p.exists():
        raise FileNotFoundError(f"FAISS index not found: {p}")
    return faiss.read_index(str(p))


def load_metadata(metadata_path: Path) -> List[Dict]:
    """Load metadata.jsonl into memory."""
    p = Path(metadata_path)
    if not p.exists():
        raise FileNotFoundError(f"Metadata file not found: {p}")
    entries: List[Dict] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    return entries


def ensure_demo_index() -> None:
    """Build the FAISS index from the committed sample CSV when artifacts are missing."""
    index_path = Path(app_settings.FAISS_INDEX_FILE)
    metadata_path = Path(app_settings.META_DATA_FILE)
    if index_path.exists() and metadata_path.exists():
        return

    sample = Path(app_settings.SAMPLE_CATALOG_CSV)
    if not sample.exists():
        raise FileNotFoundError(
            f"FAISS index missing ({index_path}) and sample catalog not found ({sample}). "
            "Add the sample CSV or run: python -m backend.scripts.build_demo_index"
        )

    logger.warning("FAISS index missing; building demo index from %s", sample)
    from backend.scripts.build_index import IndexBuilder

    IndexBuilder(
        excel_path=sample,
        out_dir=Path(app_settings.EMBEDDINGS_DIR),
        embedding_model=app_settings.DEFAULT_EMBEDDING_MODEL,
    ).run()


def load_resources(model_name: str, index_path: Path, metadata_path: Path) -> Tuple[SentenceTransformer, faiss.Index, List[Dict]]:
    """Load all heavy resources once."""
    model = load_model(model_name)
    index = load_index(index_path)
    meta_entries = load_metadata(metadata_path)
    return model, index, meta_entries