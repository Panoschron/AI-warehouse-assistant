from dataclasses import dataclass
from typing import List, Dict
from pathlib import Path
import json

@dataclass
class Doc:
    """
    Αντιπροσωπεύει ΕΝΑ προϊόν / εγγραφή από το Excel,
    σε μορφή έτοιμη για AI επεξεργασία (embeddings, αναζήτηση κ.λπ.).
    """
    id: str
    text: str
    metadata: Dict[str, str]

    def __repr__(self):
       short_text = self.text[:50] + ("..." if len(self.text) > 50 else "")
       return f"Doc(id={self.id!r}, text={short_text!r})"
    


class SimpleCorpusBuilder:
    """
    Δημιουργεί μια λίστα από Doc αντικείμενα (το corpus).
    Παίρνει ως είσοδο τις raw γραμμές από τον Reader.
    """

    def __init__(self):
    # εδώ μπορείς να κρατάς προσωρινά δεδομένα αν θες
      self.docs: List[Doc] = []
    
    def build(self, rows: List[Dict[str,str]]) -> List[Doc]:
      """
        Παίρνει λίστα από dicts (γραμμές Excel) και επιστρέφει λίστα Doc αντικειμένων.
        """
      docs: List[Doc] = []
      
      # Βήμα 1: επανάληψη σε κάθε γραμμή
      for i, row in enumerate(rows):
        text = "|".join(f"{k}: {v}" for k, v in row.items())
        doc_id = row.get("Κωδικός", f"row-{i}")
        doc = Doc(id=doc_id, text=text, metadata=row)
        docs.append(doc)
      self.docs = docs
      return docs
    
    def export_corpus_jsonl(self, out_path: str | Path = "corpus.jsonl") -> Path:
      out_path = Path(out_path)
      out_path.parent.mkdir(parents=True, exist_ok=True)
      with out_path.open("w", encoding="utf-8") as f:
        for doc in self.docs:
          f.write(json.dumps({
            "id": doc.id,
            "text": doc.text,
            "metadata": doc.metadata
          }, ensure_ascii=False) + "\n")
      return out_path