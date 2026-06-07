import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

"""
TruthLens Proxy Server
Intercepts LLM calls, evaluates them, logs to SQLite, returns scores.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from proxy.core import TruthLensProxy, TruthLensResponse
from proxy.database import init_db, get_evaluations, get_analytics, export_csv

init_db()

app = FastAPI(
    title="TruthLens Proxy",
    description="Intercept any LLM call and get automatic trust evaluation.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

proxy = TruthLensProxy(
    eval_model=os.getenv("TRUTHLENS_EVAL_MODEL", "llama3"),
    include_claims=os.getenv("TRUTHLENS_CLAIMS", "false").lower() == "true",
    auto_log=True,
)


# ── Request schemas ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    provider: str                         # openai | anthropic | gemini | ollama
    model: str                            # gpt-4o | claude-sonnet-4-6 | llama3 | etc
    messages: List[Dict[str, str]]        # [{"role": "user", "content": "..."}]
    sources: Optional[List[str]] = None  # grounding documents
    api_key: Optional[str] = None        # provider API key (or set via env var)
    temperature: float = 0.7
    max_tokens: int = 1000
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    tags: Optional[List[str]] = None
    include_claims: bool = False


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "name": "TruthLens Proxy",
        "version": "0.1.0",
        "endpoints": ["/chat", "/analytics", "/history", "/export", "/health"],
    }


@app.get("/health")
def health():
    try:
        import httpx
        r = httpx.get("http://localhost:11434/api/tags", timeout=3)
        ollama_ok = r.status_code == 200
        models = [m["name"] for m in r.json().get("models", [])]
    except Exception:
        ollama_ok = False
        models = []
    return {
        "status": "ok",
        "ollama": "connected" if ollama_ok else "unreachable",
        "available_models": models,
        "eval_model": proxy.eval_model,
    }


@app.post("/chat", response_model=TruthLensResponse)
def chat(req: ChatRequest):
    """
    Main proxy endpoint. Send any LLM request and get back
    the response + automatic TruthLens evaluation scores.

    Example:
        POST /chat
        {
            "provider": "openai",
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Who made Python?"}],
            "sources": ["Python was created by Guido van Rossum in 1991."],
            "api_key": "sk-..."
        }
    """
    try:
        provider_kwargs = {}
        if req.api_key:
            provider_kwargs["api_key"] = req.api_key

        # Use per-request include_claims if specified
        p = proxy
        if req.include_claims and not proxy.include_claims:
            p = TruthLensProxy(
                eval_model=proxy.eval_model,
                include_claims=True,
                auto_log=True,
            )

        return p.chat(
            provider=req.provider,
            model=req.model,
            messages=req.messages,
            sources=req.sources,
            session_id=req.session_id,
            user_id=req.user_id,
            tags=req.tags,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            **provider_kwargs,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics")
def analytics():
    """Aggregate trust scores, hallucination rates, and trends across all logged calls."""
    return get_analytics()


@app.get("/history")
def history(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    session_id: Optional[str] = None,
    min_trust: Optional[float] = None,
    max_trust: Optional[float] = None,
    limit: int = Query(50, le=500),
    offset: int = 0,
):
    """Browse all logged evaluations with filtering."""
    return {
        "evaluations": get_evaluations(
            provider=provider, model=model, session_id=session_id,
            min_trust=min_trust, max_trust=max_trust,
            limit=limit, offset=offset,
        )
    }


@app.post("/export")
def export(path: str = "truthlens_export.csv"):
    """Export all evaluations to CSV for research analysis."""
    n = export_csv(path)
    return {"exported": n, "path": path}

