"""Build prompts for LLM from search results."""
from typing import List, Dict


class PromptBuilder:
    """Constructs prompts for LLM queries."""
    
    def __init__(
        self, 
        system_prompt: str = "Είσαι ένας έξυπνος βοηθός αποθήκης.",
        max_context_items: int = 3
    ):
        self.system_prompt = system_prompt
        self.max_context_items = max_context_items
    
    def build_context(self, results: List[Dict]) -> str:
        """Extract and format context from search results.
        
        Args:
            results: Formatted search results
            
        Returns:
            Formatted context string
        """
        context_items = []
        
        for i, result in enumerate(results[:self.max_context_items], 1):
            metadata = result.get('metadata', {}).get('metadata', {})
            
            # Format each field
            fields = []
            for key, value in metadata.items():
                if value:  # Skip empty values
                    fields.append(f"{key}: {value}")
            
            item_text = " | ".join(fields)
            context_items.append(f"{i}. {item_text}")
        
        return "\n".join(context_items)
    
    def build_prompt(self, query: str, results: List[Dict]) -> str:
        """Build complete prompt for LLM.
        
        Args:
            query: User's original query
            results: Search results
            
        Returns:
            Complete prompt string
        """
        context = self.build_context(results)
        
        if not context:
            return f"""Δεν βρέθηκαν σχετικά προϊόντα για την αναζήτηση: "{query}"

Απάντησε ευγενικά ότι δεν υπάρχουν διαθέσιμα αποτελέσματα."""
        
        prompt = f"""Χρησιμοποιώντας τα παρακάτω προϊόντα από την αποθήκη:

{context}

Απάντησε στην ερώτηση: "{query}"

Οδηγίες:
- Δώσε σύντομη και χρήσιμη απάντηση στα Ελληνικά
- Αναφέρε συγκεκριμένα προϊόντα όταν είναι σχετικά
- Αν χρειάζεται, πρότεινε εναλλακτικές
- Μην εφευρίσκεις πληροφορίες που δεν υπάρχουν στο context"""

        return prompt