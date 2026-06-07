import time
from typing import List, Optional
from .models import EvaluationReport, HallucinationRisk
from .ollama_client import get_client

EVAL_SYSTEM = """You are TruthLens, an expert AI evaluation engine. Your job is to rigorously assess whether an AI-generated answer is trustworthy, grounded, and accurate.

You evaluate five dimensions:
1. Groundedness (0-100): How strongly is the answer supported by the provided source documents?
2. Faithfulness (0-100): Does the answer accurately reflect the information in the sources without distortion?
3. Citation Accuracy (0-100): Are the references and citations used valid and correctly attributed?
4. Consistency (0-100): Would this answer remain stable if the question were rephrased slightly?
5. Hallucination Risk: LOW if groundedness >= 85 and faithfulness >= 85, MEDIUM if >= 65, else HIGH.

Respond ONLY with a JSON object matching this exact schema:
{
  "groundedness": <number 0-100>,
  "faithfulness": <number 0-100>,
  "citation_accuracy": <number 0-100>,
  "consistency_score": <number 0-100>,
  "hallucination_risk": "Low" | "Medium" | "High",
  "unsupported_claims": [<list of verbatim claims from the answer that are NOT supported by sources>],
  "reasoning": {
    "groundedness": "<one sentence explanation>",
    "faithfulness": "<one sentence explanation>",
    "citation_accuracy": "<one sentence explanation>",
    "consistency_score": "<one sentence explanation>"
  }
}"""


def _build_prompt(question: str, answer: str, sources: List[str]) -> str:
    sources_text = "\n\n".join(
        f"[Source {i+1}]\n{src}" for i, src in enumerate(sources)
    )
    return f"""QUESTION:
{question}

AI-GENERATED ANSWER:
{answer}

SOURCE DOCUMENTS:
{sources_text}

Evaluate the answer against the sources."""


def _compute_trust_score(g: float, f: float, c: float, cons: float) -> float:
    return round(g * 0.35 + f * 0.30 + c * 0.20 + cons * 0.15, 1)


def evaluate(
    question: str,
    answer: str,
    sources: List[str],
    model: Optional[str] = None,
    consistency_runs: int = 1,
) -> EvaluationReport:
    """
    Evaluate a question-answer pair against source documents.

    Args:
        question: The original user query
        answer: The AI-generated response to evaluate
        sources: List of source document strings used for context
        model: Ollama model name (defaults to TRUTHLENS_MODEL env var or llama3)
        consistency_runs: Number of runs for consistency scoring (1 = skip)

    Returns:
        EvaluationReport with all metrics
    """
    client = get_client(model)
    prompt = _build_prompt(question, answer, sources)

    t0 = time.perf_counter()
    result = client.chat_json(EVAL_SYSTEM, prompt)
    latency_ms = (time.perf_counter() - t0) * 1000

    # Consistency: run again and compare scores
    consistency_score = result.get("consistency_score", 85.0)
    if consistency_runs > 1:
        scores = [result.get("groundedness", 80)]
        for _ in range(consistency_runs - 1):
            r2 = client.chat_json(EVAL_SYSTEM, prompt)
            scores.append(r2.get("groundedness", 80))
        variance = max(scores) - min(scores)
        consistency_score = max(0, 100 - variance * 2)

    g = float(result.get("groundedness", 0))
    f = float(result.get("faithfulness", 0))
    c = float(result.get("citation_accuracy", 0))
    cons = float(consistency_score)

    risk_str = result.get("hallucination_risk", "Medium")
    try:
        risk = HallucinationRisk(risk_str)
    except ValueError:
        risk = HallucinationRisk.MEDIUM

    return EvaluationReport(
        question=question,
        answer=answer,
        groundedness=g,
        faithfulness=f,
        citation_accuracy=c,
        consistency_score=cons,
        hallucination_risk=risk,
        trust_score=_compute_trust_score(g, f, c, cons),
        reasoning=result.get("reasoning", {}),
        unsupported_claims=result.get("unsupported_claims", []),
        model=client.model,
        latency_ms=round(latency_ms, 1),
    )
