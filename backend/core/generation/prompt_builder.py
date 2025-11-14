"""Build prompts for LLM from search results.

Note: The number of context items is not controlled here.
Pass in the already-trimmed results list (e.g., length == top_k).
"""
from typing import List, Dict


class PromptBuilder:
    """Constructs prompts for LLM queries."""
    
    def __init__(
        self,
        system_prompt: str = "Είσαι ένας έξυπνος βοηθός αποθήκης και πρέπει να βοηθήσεις τον εργαζόμενο να εντοπίσει ή να βρει πληροφορίες για αυτό που ψάχνει.",
    ):
        self.system_prompt = system_prompt
    
    def build_context(self, results: List[Dict]) -> str:
        """Extract and format context from search results.
        
        Args:
            results: Formatted search results
            
        Returns:
            Formatted context string
        """
        context_items = []
        
        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {}).get('metadata', {})
            
            # Format each field
            fields = []
            for key, value in metadata.items():
                if value:  # Skip empty values
                    fields.append(f"{key}: {value}")
            
            item_text = " | ".join(fields)
            context_items.append(f"{i}. {item_text}")
        
        print(f"Built context: {context_items}")
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
- Αναφέρε συγκεκριμένα προϊόντα όταν είναι σχετικά
- Αν χρειάζεται, πρότεινε εναλλακτικές
- Μην εφευρίσκεις πληροφορίες που δεν υπάρχουν στο context"""

        return prompt