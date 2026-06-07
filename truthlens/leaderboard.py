"""
Phase 4: Model Leaderboard

Run the same benchmark dataset across multiple models and
produce a ranked leaderboard with statistical comparisons.
"""
import time
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field

from .benchmark import BenchmarkCase, BenchmarkReport, BenchmarkStats, run_benchmark


class ModelLeaderboardEntry(BaseModel):
    rank: int
    model: str
    avg_trust_score: float
    avg_groundedness: float
    avg_faithfulness: float
    avg_citation_accuracy: float
    low_risk_pct: float
    high_risk_pct: float
    avg_latency_ms: float
    total_cases: int
    run_id: str


class LeaderboardReport(BaseModel):
    timestamp: str
    dataset_size: int
    models_evaluated: List[str]
    leaderboard: List[ModelLeaderboardEntry]
    winner: str
    per_model_reports: Dict[str, BenchmarkReport] = Field(default_factory=dict)
    domain_winners: Dict[str, str] = Field(default_factory=dict)  # domain -> best model

    def __str__(self):
        lines = [
            "=" * 60,
            "  TruthLens Model Leaderboard",
            "=" * 60,
            f"  Dataset: {self.dataset_size} cases",
            f"  Models:  {len(self.models_evaluated)}",
            "",
            f"  {'Rank':<5} {'Model':<20} {'Trust':>6} {'Ground':>7} {'Faith':>7} {'Low Risk':>9} {'Latency':>9}",
            f"  {'-'*5} {'-'*20} {'-'*6} {'-'*7} {'-'*7} {'-'*9} {'-'*9}",
        ]
        for e in self.leaderboard:
            lines.append(
                f"  #{e.rank:<4} {e.model:<20} {e.avg_trust_score:>5.1f} "
                f"{e.avg_groundedness:>6.1f}% {e.avg_faithfulness:>6.1f}% "
                f"{e.low_risk_pct:>8.1f}% {e.avg_latency_ms:>7.0f}ms"
            )
        lines += ["=" * 60, f"  Winner: {self.winner}"]
        if self.domain_winners:
            lines.append("  Domain Winners:")
            for domain, model in self.domain_winners.items():
                lines.append(f"    {domain}: {model}")
        return "\n".join(lines)


def run_leaderboard(
    cases: List[BenchmarkCase],
    models: List[str],
    include_claims: bool = False,
    progress_callback=None,
) -> LeaderboardReport:
    """
    Run the same benchmark across multiple models and produce a leaderboard.

    Args:
        cases: Shared benchmark dataset
        models: List of Ollama model names to compare
        include_claims: Include claim-level verification
        progress_callback: Optional callable(model, completed, total)

    Returns:
        LeaderboardReport with ranked results
    """
    per_model_reports: Dict[str, BenchmarkReport] = {}

    for model in models:
        def cb(completed, total, m=model):
            if progress_callback:
                progress_callback(m, completed, total)

        report = run_benchmark(
            cases=cases,
            model=model,
            include_claims=include_claims,
            progress_callback=cb,
        )
        per_model_reports[model] = report

    # Build leaderboard sorted by avg_trust_score
    entries: List[ModelLeaderboardEntry] = []
    for model, report in per_model_reports.items():
        s = report.stats
        entries.append(ModelLeaderboardEntry(
            rank=0,  # set below
            model=model,
            avg_trust_score=s.avg_trust_score,
            avg_groundedness=s.avg_groundedness,
            avg_faithfulness=s.avg_faithfulness,
            avg_citation_accuracy=s.avg_citation_accuracy,
            low_risk_pct=s.low_risk_pct,
            high_risk_pct=s.high_risk_pct,
            avg_latency_ms=s.avg_latency_ms,
            total_cases=s.total_cases,
            run_id=report.run_id,
        ))

    entries.sort(key=lambda e: e.avg_trust_score, reverse=True)
    for i, e in enumerate(entries):
        e.rank = i + 1

    # Domain winners
    domain_winners: Dict[str, str] = {}
    all_domains = set()
    for report in per_model_reports.values():
        all_domains.update(report.stats.domain_stats.keys())

    for domain in all_domains:
        best_model = max(
            per_model_reports.keys(),
            key=lambda m: per_model_reports[m].stats.domain_stats.get(domain, {}).get("avg_trust_score", 0)
        )
        domain_winners[domain] = best_model

    return LeaderboardReport(
        timestamp=datetime.utcnow().isoformat(),
        dataset_size=len(cases),
        models_evaluated=models,
        leaderboard=entries,
        winner=entries[0].model if entries else "none",
        per_model_reports=per_model_reports,
        domain_winners=domain_winners,
    )
