#requirements:
#httpx==0.27.2

import json
import os
import re

import httpx


def chat_json(system: str, user: str, temperature: float = 0.2) -> dict:
    url = os.environ["OLLAMA_URL"].rstrip("/")
    model = os.environ.get("OLLAMA_LLM_MODEL", "qwen3")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": temperature},
    }
    with httpx.Client(timeout=300.0) as client:
        r = client.post(f"{url}/api/chat", json=payload)
        r.raise_for_status()
        content = r.json()["message"]["content"]
    text = content.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError(f"Could not parse JSON from model response: {text[:500]}")


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    url = os.environ["OLLAMA_URL"].rstrip("/")
    model = os.environ.get("OLLAMA_EMBED_MODEL", "bge-m3")
    with httpx.Client(timeout=300.0) as client:
        r = client.post(f"{url}/api/embed", json={"model": model, "input": texts})
        r.raise_for_status()
        data = r.json()
    return data.get("embeddings") or [data["embedding"]]


def truncate_text(text: str, max_chars: int = 12000) -> str:
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return f"{text[:half]}\n\n[... gekuerzt ...]\n\n{text[-half:]}"
