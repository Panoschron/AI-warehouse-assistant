import sys, os
from pathlib import Path
from warehouse_ai import Engine, EngineConfig 
import app_settings as cfg
from scripts.env_check import check_and_install_packages 


if __name__ == "__main__":
    print("=== Warehouse AI — Step 1: Readers via Engine ===")

    # Βεβαιώσου ότι όλες οι απαιτήσεις είναι ικανοποιημένες
    success = check_and_install_packages()
    
    # 1) Ρυθμίσεις (directory-based)
    excel_path = cfg.DATA_DIR / "products.xlsx"

    if not excel_path.exists():
        raise FileNotFoundError(f"❌ Δεν βρέθηκε το Excel: {excel_path}")

    # 2) Δημιουργία engine (δώσε κατευθείαν το path στο config)
    eng = Engine(EngineConfig(excel_path=excel_path, sheet=0, preview_rows=10))

    # 3) Λίστα φύλλων
    sheets = eng.list_sheets()
    print("📑 Φύλλα:", sheets)

    # 4) Φόρτωση δεδομένων
    total = eng.load()  # ή eng.load(1) / eng.load("SheetName")
    print(f"📦 Σύνολο γραμμών: {total}")

    # 5) Προεπισκόπηση
    print("\n🧾 Προεπισκόπηση Rows:")
    print(eng.preview_rows())

    # 6) Export σε JSONL (στο exports/)
    rows_path = cfg.EXPORT_DIR / "rows.jsonl"
    out = eng.export_rows(rows_path)
    print(f"\n💾 Αποθηκεύτηκε: {out.resolve()}")

    # 7) Export Corpus σε JSONL (στο exports/)
    corpus_path = cfg.EXPORT_DIR / "corpus.jsonl"
    out_corpus = eng.export_corpus(corpus_path)
    print(f"\n💾 Αποθηκεύτηκε: {out_corpus.resolve()}")

    print("\n✅ Τέλος — στάδιο Readers έτοιμο.")
    
    # 8) Export Embeddings (στο exports/embeddings/)
    embeddings_dir = cfg.EXPORT_DIR / "embeddings"
    out_embeddings = eng.export_embeddings(embeddings_dir)
    print(f"\n💾 Αποθηκεύτηκαν embeddings στο: {out_embeddings.resolve()}")