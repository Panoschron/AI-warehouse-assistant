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
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        # Έλεγχος και ενεργοποίηση GPU
        print(f"Initial device: {self.model.device}")
        try:
            import torch
            if torch.cuda.is_available():
                print(f"✓ CUDA available! GPU: {torch.cuda.get_device_name(0)}")
                self.model = self.model.to('cuda')
                print(f"✓ Model moved to GPU: {self.model.device}")
            else:
                print("✗ CUDA not available, using CPU")
        except ImportError:
            print("✗ PyTorch not found or no CUDA support, using CPU")
        
        self.docs: List = []
        self.embeddings: np.ndarray | None = None

    def set_docs(self, docs: List):
        self.docs = docs

    def encode_docs(self, docs: List, batch_size: int = 128):
        texts = [d.text for d in docs]
        print(f"\nEncoding {len(texts)} documents...")
        print(f"Batch size: {batch_size}")
        print(f"Device: {self.model.device}")
        
        embs = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        self.docs = docs
        self.embeddings = embs
        print(f"✓ Encoding complete! Shape: {embs.shape}")
        return embs

    def encode_from_corpus_or_rows(
        self,
        corpus_path: Optional[Path] = None,
        rows: Optional[List[Dict]] = None,
        batch_size: int = 128
    ):
        """
        Προσπαθεί να φορτώσει docs από corpus_path (JSONL). Αν δεν υπάρχει,
        φτιάχνει corpus από rows με τον SimpleCorpusBuilder.
        Επιστρέφει το numpy array embeddings.
        """
        docs: List[Doc] = []
        if corpus_path and Path(corpus_path).exists():
            print(f"Loading corpus from: {corpus_path}")
            with Path(corpus_path).open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    docs.append(Doc(id=obj.get("id"), text=obj.get("text", ""), metadata=obj.get("metadata", {})))
            print(f"✓ Loaded {len(docs)} documents from corpus")
        else:
            if not rows:
                raise RuntimeError("No corpus file and no rows provided to build corpus.")
            print(f"Building corpus from {len(rows)} rows...")
            builder = SimpleCorpusBuilder()
            builder.build(rows)
            docs = builder.docs
            print(f"✓ Built corpus with {len(docs)} documents")

        return self.encode_docs(docs, batch_size=batch_size)

    def save(self, out_dir: Path | str):
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        if self.embeddings is None:
            raise RuntimeError("No embeddings to save. Call encode_docs(...) first.")

        print(f"\nSaving embeddings to: {out_dir}")
        
        # save numpy embeddings
        np.save(out_dir / "embeddings.npy", self.embeddings)
        print(f"✓ Saved embeddings.npy ({self.embeddings.shape})")

        # save metadata (id + original metadata) as jsonl
        with (out_dir / "metadata.jsonl").open("w", encoding="utf-8") as f:
            for d in self.docs:
                f.write(json.dumps({"id": d.id, "metadata": d.metadata}, ensure_ascii=False) + "\n")
        print(f"✓ Saved metadata.jsonl ({len(self.docs)} entries)")

        # try to build and save faiss index (best-effort)
        try:
            import faiss
            dim = int(self.embeddings.shape[1])
            
            if len(self.embeddings) > 10000:
                print(f"Building IVF FAISS index for {len(self.embeddings)} vectors...")
                nlist = min(int(np.sqrt(len(self.embeddings))), 100)
                quantizer = faiss.IndexFlatIP(dim)
                index = faiss.IndexIVFFlat(quantizer, dim, nlist, faiss.METRIC_INNER_PRODUCT)
                index.train(self.embeddings)
                index.add(self.embeddings)
                index.nprobe = 10
                print(f"✓ Built IVF index with {nlist} clusters")
            else:
                print(f"Building Flat FAISS index for {len(self.embeddings)} vectors...")
                index = faiss.IndexFlatIP(dim)
                index.add(self.embeddings)
                print(f"✓ Built Flat index")
            
            faiss.write_index(index, str(out_dir / "index.faiss"))
            print(f"✓ Saved index.faiss")
        except Exception as e:
            print(f"✗ Could not build FAISS index: {e}")

        return out_dir