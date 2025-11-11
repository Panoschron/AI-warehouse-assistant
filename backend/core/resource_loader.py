from pathlib import Path
from typing import List, Dict, Tuple
import json

import faiss  # type: ignore
from sentence_transformers import SentenceTransformer


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


def load_resources(model_name: str, index_path: Path, metadata_path: Path) -> Tuple[SentenceTransformer, faiss.Index, List[Dict]]:
    """Load all heavy resources once."""
    model = load_model(model_name)
    index = load_index(index_path)
    meta_entries = load_metadata(metadata_path)
    return model, index, meta_entries