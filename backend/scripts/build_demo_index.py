"""Rebuild the demo FAISS index from the committed SoftOne-like sample CSV."""
from pathlib import Path

from backend import app_settings
from backend.scripts.build_index import IndexBuilder


def main() -> None:
    csv_path = Path(app_settings.SAMPLE_CATALOG_CSV)
    out_dir = Path(app_settings.EMBEDDINGS_DIR)
    if not csv_path.exists():
        raise FileNotFoundError(f"Sample catalog not found: {csv_path}")

    IndexBuilder(
        excel_path=csv_path,
        out_dir=out_dir,
        embedding_model=app_settings.DEFAULT_EMBEDDING_MODEL,
    ).run()
    print(f"\nDemo index ready. Query API after: uvicorn backend.server:app --reload")


if __name__ == "__main__":
    main()
