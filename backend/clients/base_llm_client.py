"""Abstract base class for LLM clients."""
from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMClient(ABC):
    """Abstract interface for LLM clients."""
    
    @abstractmethod
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate text from prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instructions

            
        Returns:
            Generated text
        """
        pass