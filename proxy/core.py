"""
TruthLens Proxy — Core Engine

Intercepts any LLM call, gets the response, evaluates it,
logs everything to SQLite, and returns both to the caller.
"""
import time
import uuid
import json
import sys
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from proxy.providers import get_adapter, Message, ProxyResponse
from proxy.database import init_db, log_evaluation
from truthlens.evaluator import evaluate
from truthlens.claims import verify_claims
from truthlens.models import HallucinationRisk


# ── Response model ─────────────────────────────────────────────────────────────

class TruthLensResponse(BaseModel):
    # Original LLM response
    content: str
    model: str
    provider: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: float

    # TruthLens evaluation
    trust_score: float
    groundedness: float
    faithfulness: float
    citation_accuracy: float
    consistency_score: float
    hallucination_risk: str
    eval_latency_ms: float

    # Claim breakdown (if enabled)
    claims: Optional[List[Dict]] = None
    total_claims: Optional[int] = None
    supported_pct: Optional[float] = None
    contradicted_pct: Optional[float] = None

    # Meta
    request_id: str
    timestamp: str
    reasoning: Optional[Dict[str, str]] = None
    unsupported_claims: Optional[List[str]] = None

    def summary(self) -> str:
        risk_icon = {"Low": "✓", "Medium": "⚠", "High": "✗"}.get(self.hallucination_risk, "?")
        return (
            f"[TruthLens] Trust: {self.trust_score:.0f}/100 | "
            f"Ground: {self.groundedness:.0f}% | "
            f"Faith: {self.faithfulness:.0f}% | "
            f"Hallucination: {risk_icon} {self.hallucination_risk}"
        )


# ── Proxy ──────────────────────────────────────────────────────────────────────

class TruthLensProxy:
    """
    Drop-in proxy for any LLM API that adds automatic trust evaluation.

    Usage:
        proxy = TruthLensProxy(eval_model="llama3")

        response = proxy.chat(
            provider="openai",
            model="gpt-4o",
            messages=[{"role": "user", "content": "Who created Python?"}],
            sources=["Python was created by Guido van Rossum in 1991."],
        )

        print(response.content)        # the AI's answer
        print(response.trust_score)    # 95.0
        print(response.hallucination_risk)  # Low
    """

    def __init__(
        self,
        eval_model: str = "llama3",
        eval_provider: str = "ollama",
        include_claims: bool = False,
        auto_log: bool = True,
        db_path: Optional[str] = None,
    ):
        self.eval_model = eval_model
        self.eval_provider = eval_provider
        self.include_claims = include_claims
        self.auto_log = auto_log

        if db_path:
            os.environ["TRUTHLENS_DB"] = db_path

        if auto_log:
            init_db()

    def chat(
        self,
        provider: str,
        model: str,
        messages: List[Dict[str, str]],
        sources: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **provider_kwargs,
    ) -> TruthLensResponse:
        """
        Send a chat request through the proxy.

        Args:
            provider: "openai" | "anthropic" | "gemini" | "ollama"
            model: Model name (e.g. "gpt-4o", "claude-sonnet-4-6", "llama3")
            messages: List of {"role": ..., "content": ...} dicts
            sources: Source documents for grounding evaluation
            session_id: Optional session identifier for grouping
            user_id: Optional user identifier
            tags: Optional list of tags for filtering
            temperature: LLM temperature
            max_tokens: Max output tokens

        Returns:
            TruthLensResponse with original content + evaluation scores
        """
        request_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        # Normalize messages
        msg_objects = [Message(role=m["role"], content=m["content"]) for m in messages]
        system_prompt = next((m["content"] for m in messages if m["role"] == "system"), None)
        user_prompt = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")

        # Step 1: Call the LLM
        adapter = get_adapter(provider, **provider_kwargs)
        llm_response: ProxyResponse = adapter.call(
            messages=msg_objects,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Step 2: Evaluate the response
        eval_sources = sources or []
        t_eval = time.perf_counter()

        eval_report = evaluate(
            question=user_prompt,
            answer=llm_response.content,
            sources=eval_sources if eval_sources else [user_prompt],
            model=self.eval_model,
        )

        claims_data = {}
        claims_list = None
        if self.include_claims and eval_sources:
            claims_report = verify_claims(
                question=user_prompt,
                answer=llm_response.content,
                sources=eval_sources,
                model=self.eval_model,
            )
            claims_data = {
                "total_claims": claims_report.total_claims,
                "supported_count": claims_report.supported_count,
                "unsupported_count": claims_report.unsupported_count,
                "contradicted_count": claims_report.contradicted_count,
                "supported_pct": claims_report.supported_pct,
                "contradicted_pct": claims_report.contradicted_pct,
            }
            claims_list = [c.model_dump() for c in claims_report.claims]

        eval_latency = (time.perf_counter() - t_eval) * 1000

        # Step 3: Log to database
        if self.auto_log:
            log_evaluation({
                "request_id": request_id,
                "timestamp": timestamp,
                "provider": provider,
                "model": llm_response.model,
                "prompt": user_prompt,
                "system_prompt": system_prompt,
                "sources": json.dumps(eval_sources) if eval_sources else None,
                "response": llm_response.content,
                "input_tokens": llm_response.input_tokens,
                "output_tokens": llm_response.output_tokens,
                "latency_ms": llm_response.latency_ms,
                "groundedness": eval_report.groundedness,
                "faithfulness": eval_report.faithfulness,
                "citation_accuracy": eval_report.citation_accuracy,
                "consistency_score": eval_report.consistency_score,
                "hallucination_risk": eval_report.hallucination_risk.value,
                "trust_score": eval_report.trust_score,
                "eval_latency_ms": round(eval_latency, 1),
                "total_claims": claims_data.get("total_claims"),
                "supported_count": claims_data.get("supported_count"),
                "unsupported_count": claims_data.get("unsupported_count"),
                "contradicted_count": claims_data.get("contradicted_count"),
                "supported_pct": claims_data.get("supported_pct"),
                "contradicted_pct": claims_data.get("contradicted_pct"),
                "tags": json.dumps(tags) if tags else None,
                "session_id": session_id,
                "user_id": user_id,
                "eval_model": self.eval_model,
                "error": None,
            })

        return TruthLensResponse(
            content=llm_response.content,
            model=llm_response.model,
            provider=provider,
            input_tokens=llm_response.input_tokens,
            output_tokens=llm_response.output_tokens,
            latency_ms=llm_response.latency_ms,
            trust_score=eval_report.trust_score,
            groundedness=eval_report.groundedness,
            faithfulness=eval_report.faithfulness,
            citation_accuracy=eval_report.citation_accuracy,
            consistency_score=eval_report.consistency_score,
            hallucination_risk=eval_report.hallucination_risk.value,
            eval_latency_ms=round(eval_latency, 1),
            claims=claims_list,
            total_claims=claims_data.get("total_claims"),
            supported_pct=claims_data.get("supported_pct"),
            contradicted_pct=claims_data.get("contradicted_pct"),
            request_id=request_id,
            timestamp=timestamp,
            reasoning=eval_report.reasoning,
            unsupported_claims=eval_report.unsupported_claims,
        )
