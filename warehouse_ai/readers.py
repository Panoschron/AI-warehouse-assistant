# warehouse_ai/readers.py
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import json

def _clean_col(c: str) -> str:
    """Καθαρίζει ονόματα στηλών (trim, αντικατάσταση \n, συμπτύξη πολλαπλών κενών)."""
    if c is None:
        return ""
    c = str(c).strip().replace("\n", " ")
    return " ".join(c.split())

def _norm_val(v) -> Optional[str]:
    """Καθαρίζει τιμές κελιών (trim, κενό/NaN -> None)."""
    if v is None:
        return None
    s = str(v).strip()
    return s if s and s.lower() != "nan" else None

class ExcelReader:
    """ΟΛΗ η λογική ανάγνωσης/προεπισκόπησης/εξαγωγής Excel."""
    def list_sheets(self, path: Path) -> List[str]:
        xl = pd.ExcelFile(path)
        return list(xl.sheet_names)

    def read_from_path(self, path: Path, sheet: int | str = 0) -> List[Dict[str, str]]:
        df = pd.read_excel(path, sheet_name=sheet, dtype=str)
        df.columns = [_clean_col(c) for c in df.columns]
        rows: List[Dict[str, str]] = []
        for _, r in df.iterrows():
            row = {c: _norm_val(r[c]) for c in df.columns}
            rows.append({k: v for k, v in row.items() if v is not None})
        return rows

    def preview(self, rows: List[Dict[str, str]], n: int = 20) -> str:
        lines: List[str] = []
        for i, row in enumerate(rows[:n], start=1):
            parts = [f"{k}: {v}" for k, v in row.items()]
            lines.append(f"[{i:02d}] " + " | ".join(parts))
        return "\n".join(lines)

    def export_jsonl(self, rows: List[Dict[str, str]], out_path: Path) -> Path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        return out_path
