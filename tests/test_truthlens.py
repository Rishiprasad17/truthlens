"""
TruthLens tests.
Run with: pytest tests/ -v

Note: integration tests require Ollama running locally.
Use TRUTHLENS_MODEL env var to specify model.
"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from truthlens.models import (
    EvaluationReport, RAGReport, AgentReport, ComparisonReport,
    HallucinationRisk, ModelScore
)


# ── Unit tests (no Ollama required) ────────────────────────────────────────────

class TestModels:
    def test_evaluation_report_trust_score_bounds(self):
        r = EvaluationReport(
            question="q", answer="a",
            groundedness=96, faithfulness=94, citation_accuracy=100,
            consistency_score=92, hallucination_risk=HallucinationRisk.LOW,
            trust_score=95.8
        )
        assert 0 <= r.trust_score <= 100

    def test_hallucination_risk_enum(self):
        assert HallucinationRisk("Low") == HallucinationRisk.LOW
        assert HallucinationRisk("Medium") == HallucinationRisk.MEDIUM
        assert HallucinationRisk("High") == HallucinationRisk.HIGH

    def test_report_str(self):
        r = EvaluationReport(
            question="q", answer="a",
            groundedness=80, faithfulness=75, citation_accuracy=90,
            consistency_score=85, hallucination_risk=HallucinationRisk.MEDIUM,
            trust_score=81.25
        )
        s = str(r)
        assert "Trust Score" in s
        assert "Hallucination Risk" in s

    def test_rag_report(self):
        r = RAGReport(
            question="q",
            retrieval_precision=90, retrieval_recall=85,
            context_utilization=80, evidence_coverage=88, answer_relevance=92,
            rag_score=87.1
        )
        assert r.rag_score == 87.1

    def test_agent_report(self):
        r = AgentReport(
            task="t",
            tool_usage_accuracy=95, planning_quality=88,
            task_completion=100, decision_tracing_score=82,
            agent_score=92.8
        )
        assert r.task_completion == 100


class TestScoring:
    def test_trust_score_formula(self):
        from truthlens.evaluator import _compute_trust_score
        score = _compute_trust_score(96, 94, 100, 92)
        assert abs(score - (96*0.35 + 94*0.30 + 100*0.20 + 92*0.15)) < 0.01

    def test_trust_score_zero(self):
        from truthlens.evaluator import _compute_trust_score
        assert _compute_trust_score(0, 0, 0, 0) == 0.0

    def test_trust_score_perfect(self):
        from truthlens.evaluator import _compute_trust_score
        assert _compute_trust_score(100, 100, 100, 100) == 100.0


# ── Integration tests (require Ollama) ─────────────────────────────────────────

@pytest.mark.integration
class TestEvaluate:
    def test_basic_evaluate(self):
        from truthlens import evaluate
        report = evaluate(
            question="What is the capital of France?",
            answer="The capital of France is Paris.",
            sources=["France is a country in Western Europe. Its capital city is Paris."],
        )
        assert report.groundedness > 50
        assert report.trust_score > 0
        assert report.hallucination_risk in list(HallucinationRisk)

    def test_hallucinated_answer(self):
        from truthlens import evaluate
        report = evaluate(
            question="What year was Python created?",
            answer="Python was created in 1975 by Dennis Ritchie.",
            sources=["Python is a programming language created by Guido van Rossum and first released in 1991."],
        )
        assert report.hallucination_risk != HallucinationRisk.LOW or report.trust_score < 80

    def test_rag_evaluate(self):
        from truthlens import evaluate_rag
        report = evaluate_rag(
            question="What is photosynthesis?",
            answer="Photosynthesis is the process by which plants convert sunlight into food.",
            retrieved_chunks=["Photosynthesis is the biological process by which plants use light energy to produce glucose."],
        )
        assert report.rag_score > 0
        assert report.retrieval_precision >= 0
