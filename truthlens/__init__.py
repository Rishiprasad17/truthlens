from .evaluator import evaluate
from .rag import evaluate_rag
from .agent import evaluate_agent
from .compare import compare_models
from .claims import verify_claims, extract_claims
from .benchmark import run_benchmark, load_dataset, save_dataset, save_report, export_csv, generate_sample_dataset, BenchmarkCase, BenchmarkReport, BenchmarkStats, CaseResult
from .leaderboard import run_leaderboard, LeaderboardReport, ModelLeaderboardEntry
from .paper_generator import generate_paper
from .models import EvaluationReport, RAGReport, AgentReport, ComparisonReport
from .claims import ClaimVerificationReport, Claim

__version__ = "1.0.0"

def TruthLens(*args, **kwargs):
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from proxy.sdk import TruthLens as _TL
    return _TL(*args, **kwargs)
