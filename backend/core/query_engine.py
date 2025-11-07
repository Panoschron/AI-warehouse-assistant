import logging
from importlib.resources import path
from backend import app_settings 
from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss 
import json
from pathlib import Path



logger = logging.getLogger(__name__)


def process_query(query: str) -> str:
    logger.info(f"Processing query: %s", query)
    normalized_query_text = query.strip().lower()
    print(f"Normalized query: {normalized_query_text}")
    return normalized_query_text



def vectorize_query(model, normalized_query_text: str) -> List:
    """Vectorize the normalized query text using the provided model."""

    print(f"Vectorizing query using model: {model}")
    sentence_model = model
    print(f"Using sentence model: {sentence_model}")
    query_vector = sentence_model.encode(
        normalized_query_text,
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    print(f"Query vector: {query_vector}")

    return query_vector



def search_index(index_faiss, query_vector: List, top_k:int =5) -> List[int]:
    """Search the FAISS index with the query vector and return top_k results."""

    print(f"Searching index with top_k={top_k}")

    # D = """  Distances of the nearest neighbors between the query and indexed vectors """
    # I = """ Indices of the nearest neighbors """
    
    query_matrix = np.array([query_vector], dtype="float32")
    D, I = index_faiss.search(query_matrix, top_k)

    print(f"Search results indices: {I[0]}")
    print(f"Search results distances: {D[0]}")
    return D[0].tolist(), I[0].tolist()
    


def load_metadata(path_metadata: Path) -> List[Dict]:
    """Load metadata.jsonl once into memory."""
    entries: List[Dict] = []
    with open(path_metadata, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    logger.info("Loaded %d metadata entries from %s", len(entries), path_metadata)
    return entries

def get_results_from_entries(distances: List[float], indices: List[int], meta_entries: List[Dict]) -> List[Dict]:
    """Map FAISS results to metadata entries already in memory."""
    results: List[Dict] = []
    for dist, idx in zip(distances, indices):
        if 0 <= idx < len(meta_entries):
            entry = meta_entries[idx]
            results.append({"index": idx, "distance": dist, "metadata": entry})
    return results





if __name__ == "__main__":
    sample_query = "Ρακόρ 1/2 αρσενικό με ουρά 1/2"
    normalized_query = process_query(sample_query)
    query_vector = vectorize_query(model, normalized_query)
    print(f"Query Vector: {query_vector}")
    path_index = (str(app_settings.FAISS_INDEX_FILE))
    print(f"Loading FAISS index from: {path_index}")
    index_faiss = faiss.read_index(path_index)
    distances, indices = search_index(index_faiss, query_vector, top_k=5)
    path_metadata = app_settings.META_DATA_FILE
    results = get_results_from_entries(distances, indices, path_metadata)
    print(f"Final Results: {results}")



