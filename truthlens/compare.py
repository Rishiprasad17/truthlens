import time
from typing import List, Optional
from .models import ComparisonReport, ModelScore, HallucinationRisk
from .evaluator import evaluate
from .ollama_client import OllamaClient, OLLAMA_BASE_URL


def compare_models(
    question: str,
    answers: dict,
    sources: List[str],
) -> ComparisonReport:
    """
    Compare multiple model answers against the same question and sources.

    Args:
        question: The original query
        answers: Dict of {model_name: answer_string}
        sources: Shared source documents

    Returns:
        ComparisonReport ranking all models
    """
    scores: List[ModelScore] = []

    for model_name, answer in answers.items():
        report = evaluate(
            question=question,
            answer=answer,
            sources=sources,
            model=model_name,
        )
        scores.append(ModelScore(
            model=model_name,
            groundedness=report.groundedness,
            faithfulness=report.faithfulness,
            citation_accuracy=report.citation_accuracy,
            hallucination_risk=report.hallucination_risk,
            trust_score=report.trust_score,
            latency_ms=report.latency_ms,
        ))

    scores.sort(key=lambda s: s.trust_score, reverse=True)
    winner = scores[0]

    reasoning = (
        f"{winner.model} achieved the highest trust score ({winner.trust_score:.0f}/100) "
        f"with groundedness {winner.groundedness:.0f}% and faithfulness {winner.faithfulness:.0f}%."
    )

    return ComparisonReport(
        question=question,
        models=scores,
        winner=winner.model,
        reasoning=reasoning,
    )
