"""OpenAI LLM client implementation."""
from openai import OpenAI
import logging
from typing import Optional
from backend import app_settings
from backend.clients.base_llm_client import BaseLLMClient

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT client."""
    
    def __init__(
        self, 
        api_key: str = app_settings.OPENAI_API_KEY,
        model: str = app_settings.OPEN_AI_MODEL
    ):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate response using OpenAI API."""


        response = self.client.responses.create(
                model=self.model,
                instructions=system_prompt,
                input=prompt
            )

        print(f"OpenAI response: {response}")    
        return response.output_text
    

            
        

# Backward compatibility
def generate_response(prompt: str, model: str = app_settings.OPEN_AI_MODEL) -> str:
    """Legacy function for backward compatibility."""
    client = OpenAIClient(model=model)
    return client.generate(prompt)