"""
Phase 3 & 4 tests — Benchmark runner and Leaderboard.
Unit tests require no Ollama. Integration tests require Ollama running.
"""
import pytest, json, math, tempfile, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from truthlens.benchmark import (
    BenchmarkCase, CaseResult, BenchmarkStats, BenchmarkReport,
    _compute_stats, generate_sample_dataset, save_dataset, load_dataset,
    export_csv, save_report,
)
from truthlens.leaderboard import ModelLeaderboardEntry, LeaderboardReport
from truthlens.paper_generator import generate_paper
from truthlens.models import HallucinationRisk


# ── Fixtures ───────────────────────────────────────────────────────────────────

def make_result(case_id, trust, risk, domain=None, difficulty=None, latency=500):
    return CaseResult(
        case_id=case_id, domain=domain, difficulty=difficulty,
        groundedness=trust, faithfulness=trust - 2,
        citation_accuracy=trust + 1, consistency_score=trust,
        hallucination_risk=risk, trust_score=trust,
        model="llama3", latency_ms=latency,
    )


def make_report(results, model="llama3"):
    stats = _compute_stats(results, model, "run_test")
    return BenchmarkReport(
        run_id="run_test", model=model, timestamp="2025-01-01T00:00:00",
        cases=results, stats=stats,
    )


# ── BenchmarkCase ──────────────────────────────────────────────────────────────

class TestBenchmarkCase:
    def test_basic_fields(self):
        c = BenchmarkCase(id="1", question="q", answer="a", sources=["s"])
        assert c.id == "1"
        assert c.domain is None

    def test_with_metadata(self):
        c = BenchmarkCase(id="1", question="q", answer="a", sources=["s"],
                          domain="science", difficulty="hard", metadata={"note": "x"})
        assert c.domain == "science"
        assert c.metadata["note"] == "x"

    def test_sample_dataset(self):
        ds = generate_sample_dataset()
        assert len(ds) == 5
        assert all(isinstance(c, BenchmarkCase) for c in ds)
        domains = {c.domain for c in ds}
        assert "science" in domains
        assert "finance" in domains


# ── Stats computation ──────────────────────────────────────────────────────────

class TestStatsComputation:
    def test_basic_stats(self):
        results = [
            make_result("1", 90, "Low", "science", "easy"),
            make_result("2", 70, "Medium", "finance", "hard"),
            make_result("3", 50, "High", "science", "medium"),
        ]
        stats = _compute_stats(results, "llama3", "run_1")
        assert stats.total_cases == 3
        assert stats.successful_cases == 3
        assert stats.avg_trust_score == pytest.approx((90 + 70 + 50) / 3, abs=0.5)

    def test_hallucination_counts(self):
        results = [
            make_result("1", 90, "Low"),
            make_result("2", 90, "Low"),
            make_result("3", 70, "Medium"),
            make_result("4", 40, "High"),
        ]
        stats = _compute_stats(results, "llama3", "run_2")
        assert stats.low_risk_count == 2
        assert stats.medium_risk_count == 1
        assert stats.high_risk_count == 1
        assert stats.low_risk_pct == 50.0

    def test_domain_breakdown(self):
        results = [
            make_result("1", 90, "Low", domain="science"),
            make_result("2", 80, "Low", domain="science"),
            make_result("3", 60, "Medium", domain="finance"),
        ]
        stats = _compute_stats(results, "llama3", "run_3")
        assert "science" in stats.domain_stats
        assert "finance" in stats.domain_stats
        assert stats.domain_stats["science"]["count"] == 2
        assert stats.domain_stats["science"]["avg_trust_score"] == pytest.approx(85.0, abs=0.5)

    def test_std_deviation(self):
        results = [make_result(str(i), score, "Low") for i, score in enumerate([80, 80, 80])]
        stats = _compute_stats(results, "llama3", "run_4")
        assert stats.std_trust_score == pytest.approx(0.0, abs=0.1)

    def test_empty_results(self):
        stats = _compute_stats([], "llama3", "run_5")
        assert stats.total_cases == 0
        assert stats.avg_trust_score == 0

    def test_failed_cases_excluded(self):
        results = [
            make_result("1", 90, "Low"),
            CaseResult(case_id="2", groundedness=0, faithfulness=0, citation_accuracy=0,
                       consistency_score=0, hallucination_risk="Unknown", trust_score=0,
                       model="llama3", latency_ms=100, error="timeout"),
        ]
        stats = _compute_stats(results, "llama3", "run_6")
        assert stats.failed_cases == 1
        assert stats.successful_cases == 1
        assert stats.avg_trust_score == 90.0

    def test_min_max_scores(self):
        results = [make_result(str(i), s, "Low") for i, s in enumerate([60, 80, 95])]
        stats = _compute_stats(results, "llama3", "run_7")
        assert stats.min_trust_score == 60.0
        assert stats.max_trust_score == 95.0


# ── File I/O ───────────────────────────────────────────────────────────────────

class TestFileIO:
    def test_save_load_dataset(self):
        cases = generate_sample_dataset()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_dataset(cases, path)
            loaded = load_dataset(path)
            assert len(loaded) == len(cases)
            assert loaded[0].id == cases[0].id
        finally:
            os.unlink(path)

    def test_export_csv(self):
        results = [make_result("1", 90, "Low", "science", "easy")]
        report = make_report(results)
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name
        try:
            export_csv(report, path)
            with open(path) as f:
                content = f.read()
            assert "case_id" in content
            assert "trust_score" in content
            assert "science" in content
        finally:
            os.unlink(path)

    def test_save_report_json(self):
        results = [make_result("1", 85, "Low")]
        report = make_report(results)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_report(report, path)
            with open(path) as f:
                data = json.load(f)
            assert data["run_id"] == "run_test"
            assert data["stats"]["total_cases"] == 1
        finally:
            os.unlink(path)


# ── Leaderboard ────────────────────────────────────────────────────────────────

class TestLeaderboard:
    def test_leaderboard_entry(self):
        e = ModelLeaderboardEntry(
            rank=1, model="llama3", avg_trust_score=92.0,
            avg_groundedness=94.0, avg_faithfulness=91.0,
            avg_citation_accuracy=95.0, low_risk_pct=85.0,
            high_risk_pct=5.0, avg_latency_ms=800.0,
            total_cases=50, run_id="run_1",
        )
        assert e.rank == 1
        assert e.avg_trust_score == 92.0

    def test_leaderboard_ranking(self):
        entries = [
            ModelLeaderboardEntry(rank=0, model="llama3", avg_trust_score=92.0, avg_groundedness=90, avg_faithfulness=88, avg_citation_accuracy=90, low_risk_pct=80, high_risk_pct=5, avg_latency_ms=800, total_cases=5, run_id="r1"),
            ModelLeaderboardEntry(rank=0, model="mistral", avg_trust_score=85.0, avg_groundedness=83, avg_faithfulness=82, avg_citation_accuracy=87, low_risk_pct=70, high_risk_pct=10, avg_latency_ms=600, total_cases=5, run_id="r2"),
        ]
        entries.sort(key=lambda e: e.avg_trust_score, reverse=True)
        for i, e in enumerate(entries):
            e.rank = i + 1
        assert entries[0].model == "llama3"
        assert entries[0].rank == 1
        assert entries[1].rank == 2


# ── Paper generator ────────────────────────────────────────────────────────────

class TestPaperGenerator:
    def test_basic_paper(self):
        paper = generate_paper()
        assert "TruthLens" in paper
        assert "Abstract" in paper
        assert "Conclusion" in paper

    def test_paper_with_custom_title(self):
        paper = generate_paper(title="My Custom Title", authors="Alice, Bob")
        assert "My Custom Title" in paper
        assert "Alice, Bob" in paper

    def test_paper_sections(self):
        paper = generate_paper()
        for section in ["Introduction", "Related Work", "Framework Architecture", "Research Questions", "Discussion"]:
            assert section in paper, f"Missing section: {section}"

    def test_paper_with_benchmark_data(self):
        results = [
            make_result("1", 92, "Low", "science"),
            make_result("2", 78, "Medium", "finance"),
            make_result("3", 55, "High", "medical"),
        ]
        report = make_report(results)
        paper = generate_paper(benchmark_report=report)
        assert str(report.stats.total_cases) in paper
        assert str(report.stats.avg_trust_score) in paper

    def test_latex_format(self):
        paper = generate_paper(output_format="latex")
        assert "\\documentclass" in paper
        assert "\\begin{document}" in paper

    def test_research_questions_present(self):
        paper = generate_paper()
        assert "RQ1" in paper
        assert "RQ2" in paper
