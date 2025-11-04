from backend import app_settings 
from backend.core import query_processor
from typing import List, Dict
from pathlib import Path


class QueryHandler:

    def __init__(self, model, index_faiss, path_metadata):
        self.model = model
        self.index_faiss = index_faiss
        self.path_metadata = path_metadata