# warehouse_ai/engine.py
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional
from warehouse_ai.data import ExcelReader
from warehouse_ai.corpus import SimpleCorpusBuilder, Doc
from warehouse_ai.embeddings import EmbeddingManager, DEFAULT_EMBED_MODEL
import app_settings



@dataclass
class EngineConfig:
    excel_path: Optional[Path] = None  # θα το ορίσεις στο run_engine.py
    sheet: int | str = 0               # ποιο φύλλο να διαβάσουμε
    preview_rows: int = 20             # πόσες γραμμές στην προεπισκόπηση
    embedding_model: str = DEFAULT_EMBED_MODEL
    embedding_batch_size: int = 32

class Engine:
    """
    Λεπτός wrapper πάνω από τον Reader (μόνο στάδιο 1).
    Μελλοντικά θα προστεθούν corpus / embeddings / search.
    """
    def __init__(self, cfg: EngineConfig):
        self.cfg = cfg
        self.reader = ExcelReader()
        self.excel_path: Optional[Path] = cfg.excel_path
        self.rows: List[Dict[str, str]] = []
        self.docs: List[Doc] = []

    # --- Setup ---
    def set_excel_path(self, path: str | Path) -> None:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Excel δεν βρέθηκε: {p}")
        self.excel_path = p

    # --- Reader operations ---
    def list_sheets(self) -> List[str]:
        if not self.excel_path:
            raise RuntimeError("Κάλεσε πρώτα set_excel_path(...)")
        return self.reader.list_sheets(self.excel_path)

    def load(self, sheet: int | str | None = None) -> int:
        if not self.excel_path:
            raise RuntimeError("Κάλεσε πρώτα set_excel_path(...)")
        use_sheet = self.cfg.sheet if sheet is None else sheet
        self.rows = self.reader.read_from_path(self.excel_path, sheet=use_sheet)
        return len(self.rows)

    def preview_rows(self, n: Optional[int] = None) -> str:
        if not self.rows:
            raise RuntimeError("Δεν υπάρχουν rows. Κάλεσε πρώτα load().")
        return self.reader.preview(self.rows, n or self.cfg.preview_rows)

    def export_rows(self, out_path: str | Path = "rows.jsonl") -> Path:
        if not self.rows:
            raise RuntimeError("Δεν υπάρχουν rows. Κάλεσε πρώτα load().")
        return self.reader.export_rows_jsonl(self.rows, Path(out_path))
    
    def export_corpus(self, out_path: str | Path = "corpus.jsonl") -> Path:
        if not self.rows:
            raise RuntimeError("Δεν υπάρχουν rows. Κάλεσε πρώτα load().")
        builder = SimpleCorpusBuilder()
        builder.build(self.rows)
        return builder.export_corpus_jsonl(out_path)
    
    def export_embeddings(self, out_dir: str | Path = "embeddings") -> Path:
        emb_mgr = EmbeddingManager(self.cfg.embedding_model)
        corpus_file = Path(app_settings.EXPORT_DIR) / "corpus.jsonl"
        emb_mgr.encode_from_corpus_or_rows(corpus_path=corpus_file, rows=self.rows, batch_size=self.cfg.embedding_batch_size)
        emb_mgr.save(out_dir)
        return Path(out_dir)
