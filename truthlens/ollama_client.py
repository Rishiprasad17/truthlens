import httpx
import json
import os
from typing import Any, Dict, Optional

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("TRUTHLENS_MODEL", "llama3")


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = DEFAULT_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def chat(self, system: str, user: str, temperature: float = 0.1) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"temperature": temperature},
        }
        response = httpx.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    def chat_json(self, system: str, user: str, temperature: float = 0.1) -> Dict[str, Any]:
        system_with_json = system + "\n\nYou MUST respond with valid JSON only. No preamble, no markdown, no explanation outside the JSON object."
        raw = self.chat(system_with_json, user, temperature)
        # strip markdown code fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip().rstrip("```").strip()
        return json.loads(raw)

    def list_models(self):
        response = httpx.get(f"{self.base_url}/api/tags", timeout=10)
        response.raise_for_status()
        return [m["name"] for m in response.json().get("models", [])]


_default_client: Optional[OllamaClient] = None


def get_client(model: Optional[str] = None) -> OllamaClient:
    global _default_client
    if model:
        return OllamaClient(model=model)
    if _default_client is None:
        _default_client = OllamaClient()
    return _default_client
