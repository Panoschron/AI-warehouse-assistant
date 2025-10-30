from backend import app_settings
from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
model = SentenceTransformer(app_settings.DEFAULT_EMBEDDING_MODEL)

def process_query(query: str) -> str:
    """Process and normalize the input query string.""" 

    print(f"Processing query: {query}")
    normalized_query_text = query.strip().lower()
    print(f"Normalized query: {normalized_query_text}")
    return normalized_query_text


def vectorize_query(model, normalized_query_text: str) -> List:
    """Vectorize the normalized query text using the provided model."""

    print(f"Vectorizing query using model: {model}")
    sentence_model = model 
    query_embedding = sentence_model.encode(
        normalized_query_text,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return query_embedding

if __name__ == "__main__":
    sample_query = "What is the capital of France?"
    normalized_query = process_query(sample_query)
    query_vector = vectorize_query(model, normalized_query)
    print(f"Query Vector: {query_vector}")

