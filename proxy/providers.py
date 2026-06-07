"""
TruthLens Proxy — LLM Provider Adapters

Each adapter normalizes a different LLM API into a common format:
    call(messages, model, **kwargs) -> ProxyResponse
"""
import time
import os
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ProxyResponse(BaseModel):
    content: str
    model: str
    provider: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: float
    raw: Optional[Dict[str, Any]] = None


class Message(BaseModel):
    role: str   # system | user | assistant
    content: str


# ── OpenAI ─────────────────────────────────────────────────────────────────────

class OpenAIAdapter:
    provider = "openai"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")

    def call(
        self,
        messages: List[Message],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> ProxyResponse:
        import httpx
        t0 = time.perf_counter()
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"},
            json=payload, timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        latency = (time.perf_counter() - t0) * 1000
        return ProxyResponse(
            content=data["choices"][0]["message"]["content"],
            model=data.get("model", model),
            provider=self.provider,
            input_tokens=data.get("usage", {}).get("prompt_tokens"),
            output_tokens=data.get("usage", {}).get("completion_tokens"),
            latency_ms=round(latency, 1),
            raw=data,
        )


# ── Anthropic ──────────────────────────────────────────────────────────────────

class AnthropicAdapter:
    provider = "anthropic"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

    def call(
        self,
        messages: List[Message],
        model: str = "claude-sonnet-4-6",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> ProxyResponse:
        import httpx
        t0 = time.perf_counter()

        # Separate system from user/assistant messages
        system = next((m.content for m in messages if m.role == "system"), None)
        chat_msgs = [{"role": m.role, "content": m.content}
                     for m in messages if m.role != "system"]

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": chat_msgs,
        }
        if system:
            payload["system"] = system

        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=payload, timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        latency = (time.perf_counter() - t0) * 1000
        return ProxyResponse(
            content=data["content"][0]["text"],
            model=data.get("model", model),
            provider=self.provider,
            input_tokens=data.get("usage", {}).get("input_tokens"),
            output_tokens=data.get("usage", {}).get("output_tokens"),
            latency_ms=round(latency, 1),
            raw=data,
        )


# ── Gemini ─────────────────────────────────────────────────────────────────────

class GeminiAdapter:
    provider = "gemini"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set")

    def call(
        self,
        messages: List[Message],
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> ProxyResponse:
        import httpx
        t0 = time.perf_counter()

        # Convert to Gemini format
        contents = []
        for m in messages:
            if m.role == "system":
                contents.append({"role": "user", "parts": [{"text": f"[System]: {m.content}"}]})
            else:
                role = "model" if m.role == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": m.content}]})

        payload = {
            "contents": contents,
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        resp = httpx.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        latency = (time.perf_counter() - t0) * 1000

        content = data["candidates"][0]["content"]["parts"][0]["text"]
        usage = data.get("usageMetadata", {})
        return ProxyResponse(
            content=content,
            model=model,
            provider=self.provider,
            input_tokens=usage.get("promptTokenCount"),
            output_tokens=usage.get("candidatesTokenCount"),
            latency_ms=round(latency, 1),
            raw=data,
        )


# ── Ollama ─────────────────────────────────────────────────────────────────────

class OllamaAdapter:
    provider = "ollama"

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")

    def call(
        self,
        messages: List[Message],
        model: str = "llama3",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> ProxyResponse:
        import httpx
        t0 = time.perf_counter()
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        resp = httpx.post(f"{self.base_url}/api/chat", json=payload, timeout=180)
        resp.raise_for_status()
        data = resp.json()
        latency = (time.perf_counter() - t0) * 1000
        return ProxyResponse(
            content=data["message"]["content"],
            model=data.get("model", model),
            provider=self.provider,
            input_tokens=data.get("prompt_eval_count"),
            output_tokens=data.get("eval_count"),
            latency_ms=round(latency, 1),
            raw=data,
        )


# ── Factory ────────────────────────────────────────────────────────────────────

ADAPTERS = {
    "openai":    OpenAIAdapter,
    "anthropic": AnthropicAdapter,
    "gemini":    GeminiAdapter,
    "ollama":    OllamaAdapter,
}

def get_adapter(provider: str, **kwargs):
    if provider not in ADAPTERS:
        raise ValueError(f"Unknown provider: {provider}. Choose from: {list(ADAPTERS.keys())}")
    return ADAPTERS[provider](**kwargs)
