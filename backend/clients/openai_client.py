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
        api_key: str = "",
        model: str = app_settings.OPEN_AI_MODEL,
    ):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required to construct OpenAIClient")
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
            input=prompt,
        )
        return response.output_text


def build_llm_client() -> Optional[OpenAIClient]:
    """Return an OpenAI client only when a key is present in the environment."""
    api_key = (app_settings.OPENAI_API_KEY or "").strip()
    if not api_key:
        logger.info("OPENAI_API_KEY not set; using template explains (offline demo)")
        return None
    return OpenAIClient(api_key=api_key, model=app_settings.OPEN_AI_MODEL)


# Backward compatibility
def generate_response(prompt: str, model: str = app_settings.OPEN_AI_MODEL) -> str:
    """Legacy function for backward compatibility."""
    client = OpenAIClient(api_key=app_settings.OPENAI_API_KEY, model=model)
    return client.generate(prompt)
