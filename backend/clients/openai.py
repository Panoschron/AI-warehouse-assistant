from opeanai import OpenAI
from backend import app_settings

client = OpenAI(api_key=app_settings.OPENAI_API_KEY)

def generate_response(prompt: str , model: str = app_settings.OPEN_AI_MODEL) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a warehouse assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=300,
    )
    return response.choices[0].message.content
    

    