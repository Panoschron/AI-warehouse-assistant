# run_engine.py
import sys, os
from pathlib import Path
sys.path.append(os.path.dirname(__file__))  # για local import του package

from warehouse_ai import Engine, EngineConfig

if __name__ == "__main__":
    print("=== Warehouse AI — Step 1: Readers via Engine ===")

    # 1) Ρυθμίσεις
    excel_path = Path(r"C:\Users\CHRONOPOULOS\Desktop\ΦΙΛΤΡΑ\ΦΙΛΤΡΑ.xlsx")  # <-- βάλε το δικό σου

    # 2) Δημιουργία engine
    eng = Engine(EngineConfig(excel_path=None, sheet=0, preview_rows=10))
    eng.set_excel_path(excel_path)

    # 3) Λίστα φύλλων
    sheets = eng.list_sheets()
    print("📑 Φύλλα:", sheets)

    # 4) Φόρτωση δεδομένων
    total = eng.load()  # διαβάζει το φύλλο sheet=0 (ή άλλαξε με eng.load(1) / eng.load("SheetName"))
    print(f"📦 Σύνολο γραμμών: {total}")

    # 5) Προεπισκόπηση
    print("\n🧾 Προεπισκόπηση Rows:")
    print(eng.preview_rows())

    # 6) (προαιρετικό) Export σε JSONL
    out = eng.export_rows("rows.jsonl")
    print(f"\n💾 Αποθηκεύτηκε: {out.resolve()}")

    print("\n✅ Τέλος — στάδιο Readers έτοιμο.")
    
    # 7) (προαιρετικό) Export Corpus σε JSONL
    out_corpus = eng.export_corpus("corpus.jsonl")
    print(f"\n💾 Αποθηκεύτηκε: {out_corpus.resolve()}")