# backend/core/embeddings.py
from pathlib import Path
from typing import List, Dict, Optional
import json
from sentence_transformers import SentenceTransformer
import numpy as np
from backend.build_index.corpus import SimpleCorpusBuilder, Doc
from backend.app_settings import DEFAULT_EMBEDDING_MODEL


class EmbeddingManager:
    """
    Encode a list of Doc objects and save embeddings + metadata.
    Optional: build a FAISS index if faiss is installed.
    """
    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.docs: List = []
        self.embeddings: np.ndarray | None = None

    def set_docs(self, docs: List):
        self.docs = docs

    def encode_docs(self, docs: List, batch_size: int = 64):
        texts = [d.text for d in docs]
        embs = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        self.docs = docs
        self.embeddings = embs
        return embs

    def encode_from_corpus_or_rows(
        self,
        corpus_path: Optional[Path] = None,
        rows: Optional[List[Dict]] = None,
        batch_size: int = 64
    ):
        """
        Προσπαθεί να φορτώσει docs από corpus_path (JSONL). Αν δεν υπάρχει,
        φτιάχνει corpus από rows με τον SimpleCorpusBuilder.
        Επιστρέφει το numpy array embeddings.
        """
        docs: List[Doc] = []
        if corpus_path and Path(corpus_path).exists():
            with Path(corpus_path).open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    docs.append(Doc(id=obj.get("id"), text=obj.get("text", ""), metadata=obj.get("metadata", {})))
        else:
            if not rows:
                raise RuntimeError("No corpus file and no rows provided to build corpus.")
            builder = SimpleCorpusBuilder()
            builder.build(rows)
            docs = builder.docs

        return self.encode_docs(docs, batch_size=batch_size)

    def save(self, out_dir: Path | str):
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        if self.embeddings is None:
            raise RuntimeError("No embeddings to save. Call encode_docs(...) first.")

        # save numpy embeddings
        np.save(out_dir / "embeddings.npy", self.embeddings)

        # save metadata (id + original metadata) as jsonl
        with (out_dir / "metadata.jsonl").open("w", encoding="utf-8") as f:
            for d in self.docs:
                f.write(json.dumps({"id": d.id, "metadata": d.metadata}, ensure_ascii=False) + "\n")

        # try to build and save faiss index (best-effort)
        try:
            import faiss
            dim = int(self.embeddings.shape[1])
            index = faiss.IndexFlatIP(dim)  # inner product on normalized vectors ~ cosine
            index.add(self.embeddings)
            faiss.write_index(index, str(out_dir / "index.faiss"))
        except Exception:
            # faiss optional — ignore if not available
            pass

        return out_dir