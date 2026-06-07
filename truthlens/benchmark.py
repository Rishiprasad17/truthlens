"""
Phase 3: Benchmark Runner

Runs hundreds of test cases through the evaluation pipeline,
produces aggregate metrics, and saves results for research analysis.
"""
import json
import csv
import time
import os
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field
from concurrent.futures import ThreadPoolExecutor, as_completed

from .evaluator import evaluate
from .claims import verify_claims
from .models import EvaluationReport, HallucinationRisk


# ── Data models ────────────────────────────────────────────────────────────────

class BenchmarkCase(BaseModel):
    id: str
    question: str
    answer: str
    sources: List[str]
    ground_truth: Optional[str] = None       # expected correct answer (optional)
    domain: Optional[str] = None             # e.g. "medical", "finance", "science"
    difficulty: Optional[str] = None         # "easy" | "medium" | "hard"
    expected_verdict: Optional[str] = None   # for research: known ground truth label
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CaseResult(BaseModel):
    case_id: str
    domain: Optional[str] = None
    difficulty: Optional[str] = None
    groundedness: float
    faithfulness: float
    citation_accuracy: float
    consistency_score: float
    hallucination_risk: str
    trust_score: float
    total_claims: Optional[int] = None
    supported_pct: Optional[float] = None
    contradicted_pct: Optional[float] = None
    model: str
    latency_ms: float
    error: Optional[str] = None


class BenchmarkStats(BaseModel):
    total_cases: int
    successful_cases: int
    failed_cases: int

    # Score distributions
    avg_groundedness: float
    avg_faithfulness: float
    avg_citation_accuracy: float
    avg_trust_score: float
    min_trust_score: float
    max_trust_score: float
    std_trust_score: float

    # Hallucination breakdown
    low_risk_count: int
    medium_risk_count: int
    high_risk_count: int
    low_risk_pct: float
    medium_risk_pct: float
    high_risk_pct: float

    # Performance
    avg_latency_ms: float
    total_latency_ms: float

    # Per-domain breakdown
    domain_stats: Dict[str, Dict[str, float]] = Field(default_factory=dict)

    # Per-difficulty breakdown
    difficulty_stats: Dict[str, Dict[str, float]] = Field(default_factory=dict)

    model: str
    run_id: str
    timestamp: str


class BenchmarkReport(BaseModel):
    run_id: str
    model: str
    timestamp: str
    cases: List[CaseResult]
    stats: BenchmarkStats
    config: Dict[str, Any] = Field(default_factory=dict)


# ── Benchmark runner ───────────────────────────────────────────────────────────

def _run_case(
    case: BenchmarkCase,
    model: Optional[str],
    include_claims: bool,
) -> CaseResult:
    """Run a single benchmark case."""
    t0 = time.perf_counter()
    try:
        report = evaluate(
            question=case.question,
            answer=case.answer,
            sources=case.sources,
            model=model,
        )

        claims_data = {}
        if include_claims:
            try:
                claims_report = verify_claims(
                    question=case.question,
                    answer=case.answer,
                    sources=case.sources,
                    model=model,
                )
                claims_data = {
                    "total_claims": claims_report.total_claims,
                    "supported_pct": claims_report.supported_pct,
                    "contradicted_pct": claims_report.contradicted_pct,
                }
            except Exception:
                pass

        latency_ms = (time.perf_counter() - t0) * 1000

        return CaseResult(
            case_id=case.id,
            domain=case.domain,
            difficulty=case.difficulty,
            groundedness=report.groundedness,
            faithfulness=report.faithfulness,
            citation_accuracy=report.citation_accuracy,
            consistency_score=report.consistency_score,
            hallucination_risk=report.hallucination_risk.value,
            trust_score=report.trust_score,
            model=report.model,
            latency_ms=round(latency_ms, 1),
            **claims_data,
        )

    except Exception as e:
        latency_ms = (time.perf_counter() - t0) * 1000
        return CaseResult(
            case_id=case.id,
            domain=case.domain,
            difficulty=case.difficulty,
            groundedness=0, faithfulness=0, citation_accuracy=0,
            consistency_score=0, hallucination_risk="Unknown", trust_score=0,
            model=model or "unknown",
            latency_ms=round(latency_ms, 1),
            error=str(e),
        )


def _compute_stats(
    results: List[CaseResult],
    model: str,
    run_id: str,
) -> BenchmarkStats:
    """Compute aggregate statistics from results."""
    import math

    successful = [r for r in results if r.error is None]
    n = len(successful)

    if n == 0:
        return BenchmarkStats(
            total_cases=len(results), successful_cases=0, failed_cases=len(results),
            avg_groundedness=0, avg_faithfulness=0, avg_citation_accuracy=0,
            avg_trust_score=0, min_trust_score=0, max_trust_score=0, std_trust_score=0,
            low_risk_count=0, medium_risk_count=0, high_risk_count=0,
            low_risk_pct=0, medium_risk_pct=0, high_risk_pct=0,
            avg_latency_ms=0, total_latency_ms=0,
            model=model, run_id=run_id, timestamp=datetime.utcnow().isoformat(),
        )

    trust_scores = [r.trust_score for r in successful]
    mean_trust = sum(trust_scores) / n
    std_trust = math.sqrt(sum((x - mean_trust) ** 2 for x in trust_scores) / n)

    low = sum(1 for r in successful if r.hallucination_risk == "Low")
    med = sum(1 for r in successful if r.hallucination_risk == "Medium")
    high = sum(1 for r in successful if r.hallucination_risk == "High")

    # Per-domain stats
    domain_stats: Dict[str, Dict[str, float]] = {}
    domains = set(r.domain for r in successful if r.domain)
    for domain in domains:
        dr = [r for r in successful if r.domain == domain]
        domain_stats[domain] = {
            "count": len(dr),
            "avg_trust_score": round(sum(r.trust_score for r in dr) / len(dr), 1),
            "avg_groundedness": round(sum(r.groundedness for r in dr) / len(dr), 1),
            "hallucination_high_pct": round(sum(1 for r in dr if r.hallucination_risk == "High") / len(dr) * 100, 1),
        }

    # Per-difficulty stats
    difficulty_stats: Dict[str, Dict[str, float]] = {}
    difficulties = set(r.difficulty for r in successful if r.difficulty)
    for diff in difficulties:
        dr = [r for r in successful if r.difficulty == diff]
        difficulty_stats[diff] = {
            "count": len(dr),
            "avg_trust_score": round(sum(r.trust_score for r in dr) / len(dr), 1),
            "avg_groundedness": round(sum(r.groundedness for r in dr) / len(dr), 1),
        }

    total_latency = sum(r.latency_ms for r in results)

    return BenchmarkStats(
        total_cases=len(results),
        successful_cases=n,
        failed_cases=len(results) - n,
        avg_groundedness=round(sum(r.groundedness for r in successful) / n, 1),
        avg_faithfulness=round(sum(r.faithfulness for r in successful) / n, 1),
        avg_citation_accuracy=round(sum(r.citation_accuracy for r in successful) / n, 1),
        avg_trust_score=round(mean_trust, 1),
        min_trust_score=round(min(trust_scores), 1),
        max_trust_score=round(max(trust_scores), 1),
        std_trust_score=round(std_trust, 1),
        low_risk_count=low, medium_risk_count=med, high_risk_count=high,
        low_risk_pct=round(low / n * 100, 1),
        medium_risk_pct=round(med / n * 100, 1),
        high_risk_pct=round(high / n * 100, 1),
        avg_latency_ms=round(total_latency / len(results), 1),
        total_latency_ms=round(total_latency, 1),
        domain_stats=domain_stats,
        difficulty_stats=difficulty_stats,
        model=model,
        run_id=run_id,
        timestamp=datetime.utcnow().isoformat(),
    )


def run_benchmark(
    cases: List[BenchmarkCase],
    model: Optional[str] = None,
    include_claims: bool = False,
    max_workers: int = 1,
    progress_callback=None,
) -> BenchmarkReport:
    """
    Run a full benchmark over a list of test cases.

    Args:
        cases: List of BenchmarkCase objects
        model: Ollama model name
        include_claims: Also run claim-level verification (slower)
        max_workers: Parallel workers (keep at 1 for single Ollama instance)
        progress_callback: Optional callable(completed, total) for progress updates

    Returns:
        BenchmarkReport with all results and aggregate stats
    """
    run_id = f"run_{int(time.time())}"
    results: List[CaseResult] = []

    if max_workers == 1:
        for i, case in enumerate(cases):
            result = _run_case(case, model, include_claims)
            results.append(result)
            if progress_callback:
                progress_callback(i + 1, len(cases))
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(_run_case, case, model, include_claims): case for case in cases}
            completed = 0
            for future in as_completed(futures):
                results.append(future.result())
                completed += 1
                if progress_callback:
                    progress_callback(completed, len(cases))

    stats = _compute_stats(results, model or "default", run_id)

    return BenchmarkReport(
        run_id=run_id,
        model=model or "default",
        timestamp=datetime.utcnow().isoformat(),
        cases=results,
        stats=stats,
        config={
            "include_claims": include_claims,
            "max_workers": max_workers,
            "total_cases": len(cases),
        },
    )


# ── Dataset helpers ────────────────────────────────────────────────────────────

def load_dataset(path: str) -> List[BenchmarkCase]:
    """Load benchmark cases from a JSON file."""
    with open(path) as f:
        data = json.load(f)
    return [BenchmarkCase(**item) for item in data]


def save_dataset(cases: List[BenchmarkCase], path: str):
    """Save benchmark cases to a JSON file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump([c.model_dump() for c in cases], f, indent=2)


def save_report(report: BenchmarkReport, path: str):
    """Save a benchmark report to JSON."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(report.model_dump(), f, indent=2)


def export_csv(report: BenchmarkReport, path: str):
    """Export benchmark results to CSV for analysis."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "case_id", "domain", "difficulty",
        "groundedness", "faithfulness", "citation_accuracy",
        "consistency_score", "hallucination_risk", "trust_score",
        "total_claims", "supported_pct", "contradicted_pct",
        "model", "latency_ms", "error",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for case in report.cases:
            writer.writerow({k: getattr(case, k, None) for k in fields})


# ── Sample dataset generator ───────────────────────────────────────────────────

def generate_sample_dataset() -> List[BenchmarkCase]:
    """Generate a small sample dataset for testing the benchmark runner."""
    return [
        BenchmarkCase(
            id="fin_001",
            domain="finance",
            difficulty="medium",
            question="What caused the 2008 financial crisis?",
            answer="The 2008 financial crisis was primarily caused by the collapse of the US housing bubble, fueled by risky mortgage lending and complex financial instruments like mortgage-backed securities. Investment banks like Lehman Brothers held massive exposure to these assets.",
            sources=["The 2008 financial crisis stemmed from a collapse in the US housing market. Risky subprime mortgage lending and securitization of these loans into mortgage-backed securities spread risk throughout the global financial system. Lehman Brothers filed for bankruptcy in September 2008."],
        ),
        BenchmarkCase(
            id="sci_001",
            domain="science",
            difficulty="easy",
            question="What is photosynthesis?",
            answer="Photosynthesis is the process by which plants use sunlight, water, and carbon dioxide to produce glucose and oxygen. It occurs in the chloroplasts of plant cells.",
            sources=["Photosynthesis is a biological process used by plants and other organisms to convert light energy into chemical energy stored in glucose. The process uses carbon dioxide and water and releases oxygen as a byproduct."],
        ),
        BenchmarkCase(
            id="sci_002",
            domain="science",
            difficulty="hard",
            question="How does CRISPR-Cas9 work?",
            answer="CRISPR-Cas9 uses a guide RNA to direct the Cas9 protein to a specific DNA sequence, where it makes a precise double-strand break. The cell's repair mechanisms then fix the break, allowing gene editing.",
            sources=["CRISPR-Cas9 is a genome editing tool derived from a bacterial immune system. The Cas9 enzyme is guided by a short RNA sequence (guide RNA) to a target DNA location where it creates a double-stranded break. DNA repair mechanisms can then be exploited to edit the genome."],
        ),
        BenchmarkCase(
            id="hist_001",
            domain="history",
            difficulty="easy",
            question="When did World War II end?",
            answer="World War II ended in 1945. The war in Europe ended on May 8, 1945 (V-E Day), and the war in the Pacific ended on September 2, 1945 (V-J Day) when Japan formally surrendered.",
            sources=["World War II concluded in 1945. Germany surrendered on May 8, 1945, celebrated as Victory in Europe Day. Japan's formal surrender occurred on September 2, 1945 aboard USS Missouri, marking Victory over Japan Day."],
        ),
        BenchmarkCase(
            id="med_001",
            domain="medical",
            difficulty="hard",
            question="How do mRNA vaccines work?",
            answer="mRNA vaccines introduce messenger RNA into cells, instructing them to produce a harmless piece of a pathogen (like the spike protein of SARS-CoV-2). The immune system responds to this protein and builds immunity.",
            sources=["mRNA vaccines work by delivering genetic instructions to cells. The mRNA encodes a specific antigen — in the case of COVID-19 vaccines, the spike protein of SARS-CoV-2. Cells use this mRNA to produce the antigen, which then triggers an immune response without using live virus."],
        ),
    ]
