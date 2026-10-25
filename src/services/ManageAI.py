import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def chat_with_ollama(prompt: str) -> str:
    """Send a chat prompt to Ollama's hosted OpenAI-compatible API."""
    api_key = os.getenv("OLLAMA_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OLLAMA_API_KEY is not set. Add it to the project .env file.")

    client = OpenAI(api_key=api_key, base_url="https://ollama.com/v1", timeout=60.0)
    response = client.chat.completions.create(
        model="gemma4:31b",
        messages=[{"role": "user", "content": prompt}],
    )
    reply = response.choices[0].message.content
    if not reply:
        raise RuntimeError("Ollama returned an empty response.")
    return reply


def chat_with_deepseek(prompt: str) -> str:
    """Keep the existing DeepSeek provider callable without embedding its key."""
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set.")

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com", timeout=60.0)
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
    )
    reply = response.choices[0].message.content
    if not reply:
        raise RuntimeError("DeepSeek returned an empty response.")
    return reply
