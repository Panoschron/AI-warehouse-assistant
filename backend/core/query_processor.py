from backend import app_settings 
from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
model = SentenceTransformer(app_settings.DEFAULT_EMBEDDING_MODEL)
import faiss 



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

def search_index(index_faiss, query_vector: List, top_k:int =5) -> List[int]:
    """Search the FAISS index with the query vector and return top_k results."""

    print(f"Searching index with top_k={top_k}")

    D = """  Distances of the nearest neighbors between the query and indexed vectors """
    I = """ Indices of the nearest neighbors """

    D, I = index_faiss.search(np.array([query_vector]), top_k)

    print(f"Search results indices: {I[0]}")
    print(f"Search results distances: {D[0]}")
    return I[0].tolist()



if __name__ == "__main__":
    sample_query = "Ρακόρ 1/2 αρσενικό με ουρά 1/2"
    normalized_query = process_query(sample_query)
    query_vector = vectorize_query(model, normalized_query)
    print(f"Query Vector: {query_vector}")
    path_index = (str(app_settings.FAIS_INDEX_FILE))
    print(f"Loading FAISS index from: {path_index}")
    index_faiss = faiss.read_index(path_index)
    top_k_indices = search_index(index_faiss, query_vector, top_k=5)
    print(f"Top K Indices: {top_k_indices}")



