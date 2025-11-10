from openai import OpenAI
from backend import app_settings
import os

client = OpenAI(api_key=app_settings.OPENAI_API_KEY)



def generate_response(prompt: str, model: str = app_settings.OPEN_AI_MODEL) -> str:
    print(f"Generating response with model: {model} and prompt: {prompt}")
    response = client.responses.create(
        model=model,
        instructions="You are a concise warehouse assistant. Answer briefly and navigate the employee to the right resources.",
        input=prompt,
        temperature=0.2,
    )


    return response.output_text
