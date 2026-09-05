"""Query preprocessing and normalization."""
import logging

logger = logging.getLogger(__name__)

# Tiny Greeklish / alias map so demo queries like "rakor" still retrieve.
_ALIASES = {
    "rakor": "ρακόρ",
    "rakkor": "ρακόρ",
}


class QueryProcessor:
    """Handles query text preprocessing."""

    def __init__(self, lowercase: bool = True, strip: bool = True):
        self.lowercase = lowercase
        self.strip = strip

    def process(self, query: str) -> str:
        """Normalize and clean query text."""
        if not query:
            raise ValueError("Query cannot be empty")

        processed = query

        if self.strip:
            processed = processed.strip()

        if self.lowercase:
            processed = processed.lower()

        extras = []
        for token in processed.split():
            alias = _ALIASES.get(token)
            if alias and alias not in processed:
                extras.append(alias)
        if extras:
            processed = f"{processed} {' '.join(extras)}"

        logger.debug(f"Processed query: '{query}' -> '{processed}'")
        return processed