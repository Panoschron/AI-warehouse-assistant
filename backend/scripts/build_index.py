"""
Builds the warehouse vector index:
- Read Excel
- Build corpus
- Encode embeddings
- Save embeddings.npy, metadata.jsonl, index.faiss
- Export rows.jsonl, corpus.jsonl
"""

from __future__ import annotations
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List

import backend.app_settings as cfg
from backend.build_index.reader import ExcelReader
from backend.build_index.corpus import SimpleCorpusBuilder
from backend.build_index.embeddings import EmbeddingManager
from backend.scripts.env_check import check_and_install_packages


class IndexBuilder:
    def __init__(
        self,
        excel_path: Path,
        sheet: int | str = 0,
        preview_rows: int = 10,
        out_dir: Optional[Path] = None,
        embedding_model: Optional[str] = None,
        batch_size: int = 32,
    ):
        if not excel_path.exists():
            raise FileNotFoundError(f"Excel not found: {excel_path}")

        self.excel_path = excel_path
        self.sheet = sheet
        self.preview_rows = preview_rows
        self.out_dir = Path(out_dir) if out_dir else (cfg.EXPORT_DIR / "embeddings")
        self.embedding_model = embedding_model or getattr(cfg, "DEFAULT_EMBEDDING_MODEL", None)
        self.batch_size = batch_size

        # runtime state
        self.reader = ExcelReader()
        self.rows: List[Dict[str, Any]] = []
        self.docs = []
        self.embeddings = None
        self.saved_dir: Optional[Path] = None
        self.rows_path: Path = cfg.EXPORT_DIR / "rows.jsonl"
        self.corpus_path: Path = cfg.EXPORT_DIR / "corpus.jsonl"

        # ensure dirs
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.rows_path.parent.mkdir(parents=True, exist_ok=True)
        self.corpus_path.parent.mkdir(parents=True, exist_ok=True)

    def read_rows(self) -> None:
        sheets = self.reader.list_sheets(self.excel_path)
        self.rows = self.reader.read_from_path(self.excel_path, sheet=self.sheet)
        print(f"✔ Read {len(self.rows)} rows from sheet '{self.sheet}' (available sheets: {sheets})")

    def show_preview(self) -> None:
        if self.preview_rows > 0 and self.rows:
            print("\nPreview:")
            print(self.reader.preview(self.rows, n=self.preview_rows))

    def export_rows(self) -> None:
        self.reader.export_rows_jsonl(self.rows, self.rows_path)
        print(f"✔ Saved rows: {self.rows_path.resolve()}")

    def build_and_export_corpus(self) -> None:
        builder = SimpleCorpusBuilder()
        self.docs = builder.build(self.rows)
        builder.export_corpus_jsonl(self.corpus_path)
        print(f"✔ Saved corpus: {self.corpus_path.resolve()} ({len(self.docs)} docs)")

    def encode_and_save(self) -> None:
        emb_mgr = EmbeddingManager(model_name=self.embedding_model) if self.embedding_model else EmbeddingManager()
        self.embeddings = emb_mgr.encode_from_corpus_or_rows(
            corpus_path=self.corpus_path, rows=self.rows, batch_size=self.batch_size
        )
        self.saved_dir = emb_mgr.save(self.out_dir)
        print(f"✔ Saved embeddings dir: {self.saved_dir.resolve()}")

    def summary(self) -> Dict[str, Any]:
        assert self.saved_dir is not None, "Embeddings not saved yet"
        index_path = self.saved_dir / "index.faiss"
        emb_path = self.saved_dir / "embeddings.npy"
        meta_path = self.saved_dir / "metadata.jsonl"
        info = {
            "excel_path": str(self.excel_path),
            "sheet": self.sheet,
            "rows": len(self.rows),
            "docs": len(self.docs),
            "embeddings_shape": tuple(self.embeddings.shape) if self.embeddings is not None else None,
            "rows_path": str(self.rows_path),
            "corpus_path": str(self.corpus_path),
            "embeddings_dir": str(self.saved_dir),
            "embeddings_file": str(emb_path),
            "metadata_file": str(meta_path),
            "faiss_index_file": str(index_path) if index_path.exists() else None,
        }
        print("\nSummary:")
        for k, v in info.items():
            print(f"- {k}: {v}")
        return info

    def run(self) -> Dict[str, Any]:
        self.read_rows()
        self.show_preview()
        self.export_rows()
        self.build_and_export_corpus()
        self.encode_and_save()
        return self.summary()


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build vector index (rows -> corpus -> embeddings -> FAISS)")
    p.add_argument("--excel", type=str, default=str(cfg.DATA_DIR / "BigBasket_products.csv"), help="Path to Excel file")
    p.add_argument("--sheet", type=str, default="0", help="Sheet index or name (default: 0)")
    p.add_argument("--preview-rows", type=int, default=10, help="Preview first N rows")
    p.add_argument("--out-dir", type=str, default=str(cfg.EXPORT_DIR / "embeddings"), help="Output dir for embeddings/index")
    p.add_argument("--embedding-model", type=str, default=getattr(cfg, "DEFAULT_EMBEDDING_MODEL", None), help="SentenceTransformer model name")
    p.add_argument("--batch-size", type=int, default=32, help="Embedding batch size")
    return p.parse_args()


def main():
    check_and_install_packages()
    args = _parse_args()

    # coerce sheet to int if numeric
    try:
        sheet_arg: int | str = int(args.sheet)
    except ValueError:
        sheet_arg = args.sheet

    builder = IndexBuilder(
        excel_path=Path(args.excel),
        sheet=sheet_arg,
        preview_rows=args.preview_rows,
        out_dir=Path(args.out_dir),
        embedding_model=args.embedding_model,
        batch_size=args.batch_size,
    )
    builder.run()


if __name__ == "__main__":
    main()