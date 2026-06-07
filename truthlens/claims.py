"""
Phase 2: Claim-level verification.

Breaks an AI answer into individual atomic claims and verifies each one
against source documents as: Supported, Unsupported, or Contradicted.
"""
import time
from typing import List, Optional
from pydantic import BaseModel, Field
from .ollama_client import get_client


# ── Data models ────────────────────────────────────────────────────────────────

class ClaimVerdict(str):
    SUPPORTED = "Supported"
    UNSUPPORTED = "Unsupported"
    CONTRADICTED = "Contradicted"


class Claim(BaseModel):
    text: str                          # the atomic claim extracted from the answer
    verdict: str                       # Supported | Unsupported | Contradicted
    confidence: float = Field(..., ge=0, le=100)
    evidence: Optional[str] = None     # quote or paraphrase from sources supporting verdict
    source_index: Optional[int] = None # which source document (0-indexed)
    reasoning: str = ""


class ClaimVerificationReport(BaseModel):
    question: str
    answer: str
    claims: List[Claim]

    # Aggregate stats
    total_claims: int
    supported_count: int
    unsupported_count: int
    contradicted_count: int

    supported_pct: float
    unsupported_pct: float
    contradicted_pct: float

    # Overall verdict
    overall_verdict: str   # "Trustworthy" | "Partially Trustworthy" | "Untrustworthy"
    trust_score: float

    model: str = "unknown"
    latency_ms: Optional[float] = None

    def __str__(self):
        lines = [
            "=" * 50,
            "  TruthLens — Claim Verification Report",
            "=" * 50,
            f"  Total Claims:    {self.total_claims}",
            f"  ✓ Supported:     {self.supported_count} ({self.supported_pct:.0f}%)",
            f"  ? Unsupported:   {self.unsupported_count} ({self.unsupported_pct:.0f}%)",
            f"  ✗ Contradicted:  {self.contradicted_count} ({self.contradicted_pct:.0f}%)",
            f"  Trust Score:     {self.trust_score:.0f}/100",
            f"  Verdict:         {self.overall_verdict}",
            "=" * 50,
        ]
        for i, c in enumerate(self.claims, 1):
            icon = {"Supported": "✓", "Unsupported": "?", "Contradicted": "✗"}.get(c.verdict, "?")
            lines.append(f"\n  [{i}] {icon} {c.verdict.upper()} (conf: {c.confidence:.0f}%)")
            lines.append(f"      Claim: {c.text}")
            if c.evidence:
                lines.append(f"      Evidence: {c.evidence}")
        return "\n".join(lines)


# ── Prompts ────────────────────────────────────────────────────────────────────

EXTRACT_CLAIMS_SYSTEM = """You are a precise fact-extraction engine. Your job is to decompose an AI-generated answer into atomic, verifiable claims.

Rules:
- Each claim must be a single, self-contained factual statement
- Claims must be atomic (one fact per claim, not compound)
- Preserve the original meaning exactly
- Exclude opinions, hedges ("it seems"), and questions
- Include numbers, dates, names, and causal claims as separate claims

Respond ONLY with valid JSON:
{
  "claims": ["claim 1", "claim 2", ...]
}"""

VERIFY_CLAIM_SYSTEM = """You are a rigorous fact-checker. Given a single claim and a set of source documents, determine whether the claim is:

- "Supported": The claim is directly or inferentially supported by the sources
- "Unsupported": The claim is neither supported nor contradicted — the sources simply don't address it
- "Contradicted": The claim directly conflicts with information in the sources

Respond ONLY with valid JSON:
{
  "verdict": "Supported" | "Unsupported" | "Contradicted",
  "confidence": <0-100>,
  "evidence": "<relevant quote or paraphrase from sources, or null>",
  "source_index": <0-based index of the most relevant source, or null>,
  "reasoning": "<one sentence explanation>"
}"""


# ── Core functions ─────────────────────────────────────────────────────────────

def extract_claims(answer: str, model: Optional[str] = None) -> List[str]:
    """Extract atomic claims from an AI answer."""
    client = get_client(model)
    prompt = f"Extract all atomic factual claims from this answer:\n\n{answer}"
    result = client.chat_json(EXTRACT_CLAIMS_SYSTEM, prompt)
    return result.get("claims", [])


def verify_claim(
    claim: str,
    sources: List[str],
    model: Optional[str] = None,
) -> Claim:
    """Verify a single claim against source documents."""
    client = get_client(model)
    sources_text = "\n\n".join(f"[Source {i}]\n{s}" for i, s in enumerate(sources))
    prompt = f"""CLAIM: {claim}

SOURCES:
{sources_text}

Verify this claim against the sources."""

    result = client.chat_json(VERIFY_CLAIM_SYSTEM, prompt)

    verdict = result.get("verdict", "Unsupported")
    if verdict not in ("Supported", "Unsupported", "Contradicted"):
        verdict = "Unsupported"

    return Claim(
        text=claim,
        verdict=verdict,
        confidence=float(result.get("confidence", 50)),
        evidence=result.get("evidence"),
        source_index=result.get("source_index"),
        reasoning=result.get("reasoning", ""),
    )


def verify_claims(
    question: str,
    answer: str,
    sources: List[str],
    model: Optional[str] = None,
) -> ClaimVerificationReport:
    """
    Phase 2 core function: extract and verify all claims in an answer.

    Args:
        question: The original query
        answer: The AI-generated answer
        sources: Source documents to verify against
        model: Ollama model name

    Returns:
        ClaimVerificationReport with per-claim verdicts and aggregate stats
    """
    client = get_client(model)
    t0 = time.perf_counter()

    # Step 1: Extract atomic claims
    raw_claims = extract_claims(answer, model)

    # Step 2: Verify each claim
    verified: List[Claim] = []
    for claim_text in raw_claims:
        claim = verify_claim(claim_text, sources, model)
        verified.append(claim)

    latency_ms = (time.perf_counter() - t0) * 1000

    # Step 3: Aggregate
    total = len(verified)
    supported = sum(1 for c in verified if c.verdict == "Supported")
    unsupported = sum(1 for c in verified if c.verdict == "Unsupported")
    contradicted = sum(1 for c in verified if c.verdict == "Contradicted")

    def pct(n): return round((n / total * 100) if total > 0 else 0, 1)

    # Trust score: supported claims contribute fully,
    # unsupported partially, contradicted heavily penalized
    if total > 0:
        trust_score = round(
            (supported * 1.0 + unsupported * 0.3 + contradicted * 0.0) / total * 100, 1
        )
    else:
        trust_score = 0.0

    if trust_score >= 80:
        overall_verdict = "Trustworthy"
    elif trust_score >= 50:
        overall_verdict = "Partially Trustworthy"
    else:
        overall_verdict = "Untrustworthy"

    return ClaimVerificationReport(
        question=question,
        answer=answer,
        claims=verified,
        total_claims=total,
        supported_count=supported,
        unsupported_count=unsupported,
        contradicted_count=contradicted,
        supported_pct=pct(supported),
        unsupported_pct=pct(unsupported),
        contradicted_pct=pct(contradicted),
        overall_verdict=overall_verdict,
        trust_score=trust_score,
        model=client.model,
        latency_ms=round(latency_ms, 1),
    )
