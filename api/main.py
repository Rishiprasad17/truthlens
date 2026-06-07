from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys, os, time, json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from truthlens import (
    evaluate, evaluate_rag, evaluate_agent, compare_models, verify_claims,
    run_benchmark, run_leaderboard, generate_paper,
    BenchmarkCase, BenchmarkReport, LeaderboardReport,
    generate_sample_dataset, save_report, export_csv,
)
from truthlens.models import EvaluationReport, RAGReport, AgentReport, ComparisonReport
from truthlens.claims import ClaimVerificationReport
from truthlens.ollama_client import OllamaClient, OLLAMA_BASE_URL

REPORTS_DIR = Path(os.getenv("TRUTHLENS_REPORTS_DIR", "./reports"))
REPORTS_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="TruthLens API",
    description="The trust and evaluation layer for AI systems.",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory benchmark job store ──────────────────────────────────────────────
benchmark_jobs: Dict[str, Any] = {}


# ── Request schemas ────────────────────────────────────────────────────────────

class EvaluateRequest(BaseModel):
    question: str
    answer: str
    sources: List[str]
    model: Optional[str] = None
    consistency_runs: int = 1

class RAGRequest(BaseModel):
    question: str
    answer: str
    retrieved_chunks: List[str]
    model: Optional[str] = None

class AgentRequest(BaseModel):
    task: str
    agent_trace: List[Dict[str, Any]]
    final_output: str
    model: Optional[str] = None

class CompareRequest(BaseModel):
    question: str
    answers: Dict[str, str]
    sources: List[str]

class ClaimsRequest(BaseModel):
    question: str
    answer: str
    sources: List[str]
    model: Optional[str] = None

class BenchmarkRequest(BaseModel):
    cases: Optional[List[Dict[str, Any]]] = None
    use_sample: bool = False
    model: Optional[str] = None
    include_claims: bool = False

class LeaderboardRequest(BaseModel):
    cases: Optional[List[Dict[str, Any]]] = None
    use_sample: bool = False
    models: List[str]
    include_claims: bool = False

class PaperRequest(BaseModel):
    run_id: Optional[str] = None
    title: str = "TruthLens: A Unified Framework for Measuring Trustworthiness in LLMs"
    authors: str = "TruthLens Research Team"
    output_format: str = "markdown"


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"name": "TruthLens API", "version": "0.3.0", "status": "running"}

@app.get("/health")
def health():
    try:
        client = OllamaClient()
        models = client.list_models()
        return {"status": "ok", "ollama": "connected", "available_models": models}
    except Exception as e:
        return {"status": "degraded", "ollama": "unreachable", "error": str(e)}

@app.post("/evaluate", response_model=EvaluationReport)
def evaluate_endpoint(req: EvaluateRequest):
    try:
        return evaluate(question=req.question, answer=req.answer, sources=req.sources,
                        model=req.model, consistency_runs=req.consistency_runs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate/rag", response_model=RAGReport)
def evaluate_rag_endpoint(req: RAGRequest):
    try:
        return evaluate_rag(question=req.question, answer=req.answer,
                            retrieved_chunks=req.retrieved_chunks, model=req.model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate/agent", response_model=AgentReport)
def evaluate_agent_endpoint(req: AgentRequest):
    try:
        return evaluate_agent(task=req.task, agent_trace=req.agent_trace,
                              final_output=req.final_output, model=req.model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate/claims", response_model=ClaimVerificationReport)
def verify_claims_endpoint(req: ClaimsRequest):
    try:
        return verify_claims(question=req.question, answer=req.answer,
                             sources=req.sources, model=req.model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compare", response_model=ComparisonReport)
def compare_endpoint(req: CompareRequest):
    try:
        return compare_models(question=req.question, answers=req.answers, sources=req.sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/benchmark")
def benchmark_endpoint(req: BenchmarkRequest, background_tasks: BackgroundTasks):
    """Start a benchmark run. Returns a job_id to poll for results."""
    job_id = f"job_{int(time.time() * 1000)}"
    benchmark_jobs[job_id] = {"status": "running", "progress": 0, "total": 0, "result": None}

    cases = generate_sample_dataset() if req.use_sample else [BenchmarkCase(**c) for c in (req.cases or [])]
    if not cases:
        raise HTTPException(status_code=400, detail="Provide cases or set use_sample=true")

    benchmark_jobs[job_id]["total"] = len(cases)

    def run():
        def cb(completed, total):
            benchmark_jobs[job_id]["progress"] = completed
        try:
            report = run_benchmark(cases=cases, model=req.model,
                                   include_claims=req.include_claims, progress_callback=cb)
            save_report(report, str(REPORTS_DIR / f"{report.run_id}.json"))
            export_csv(report, str(REPORTS_DIR / f"{report.run_id}.csv"))
            benchmark_jobs[job_id]["status"] = "done"
            benchmark_jobs[job_id]["result"] = report.model_dump()
            benchmark_jobs[job_id]["run_id"] = report.run_id
        except Exception as e:
            benchmark_jobs[job_id]["status"] = "error"
            benchmark_jobs[job_id]["error"] = str(e)

    background_tasks.add_task(run)
    return {"job_id": job_id, "total_cases": len(cases)}

@app.get("/benchmark/{job_id}")
def benchmark_status(job_id: str):
    if job_id not in benchmark_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    job = benchmark_jobs[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job.get("progress", 0),
        "total": job.get("total", 0),
        "run_id": job.get("run_id"),
        "result": job.get("result") if job["status"] == "done" else None,
        "error": job.get("error"),
    }

@app.post("/leaderboard")
def leaderboard_endpoint(req: LeaderboardRequest, background_tasks: BackgroundTasks):
    job_id = f"lb_{int(time.time() * 1000)}"
    benchmark_jobs[job_id] = {"status": "running", "current_model": "", "result": None}

    cases = generate_sample_dataset() if req.use_sample else [BenchmarkCase(**c) for c in (req.cases or [])]
    if not cases:
        raise HTTPException(status_code=400, detail="Provide cases or set use_sample=true")

    def run():
        def cb(model, completed, total):
            benchmark_jobs[job_id]["current_model"] = model
            benchmark_jobs[job_id]["progress"] = completed
            benchmark_jobs[job_id]["total"] = total
        try:
            report = run_leaderboard(cases=cases, models=req.models,
                                     include_claims=req.include_claims, progress_callback=cb)
            benchmark_jobs[job_id]["status"] = "done"
            # Serialize without nested reports to keep response lean
            result = report.model_dump()
            result.pop("per_model_reports", None)
            benchmark_jobs[job_id]["result"] = result
        except Exception as e:
            benchmark_jobs[job_id]["status"] = "error"
            benchmark_jobs[job_id]["error"] = str(e)

    background_tasks.add_task(run)
    return {"job_id": job_id, "models": req.models, "dataset_size": len(cases)}

@app.get("/leaderboard/{job_id}")
def leaderboard_status(job_id: str):
    if job_id not in benchmark_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    job = benchmark_jobs[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "current_model": job.get("current_model", ""),
        "progress": job.get("progress", 0),
        "total": job.get("total", 0),
        "result": job.get("result") if job["status"] == "done" else None,
        "error": job.get("error"),
    }

@app.post("/paper")
def generate_paper_endpoint(req: PaperRequest):
    """Generate a research paper draft, optionally populated with benchmark results."""
    benchmark_report = None
    leaderboard_report = None

    if req.run_id:
        report_path = REPORTS_DIR / f"{req.run_id}.json"
        if report_path.exists():
            from truthlens.benchmark import BenchmarkReport as BR
            with open(report_path) as f:
                benchmark_report = BR(**json.load(f))

    try:
        paper = generate_paper(
            benchmark_report=benchmark_report,
            leaderboard_report=leaderboard_report,
            title=req.title,
            authors=req.authors,
            output_format=req.output_format,
        )
        return {"paper": paper, "format": req.output_format}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports")
def list_reports():
    reports = []
    for f in REPORTS_DIR.glob("*.json"):
        try:
            with open(f) as fp:
                data = json.load(fp)
            reports.append({
                "run_id": data.get("run_id"),
                "model": data.get("model"),
                "timestamp": data.get("timestamp"),
                "total_cases": data.get("stats", {}).get("total_cases"),
                "avg_trust_score": data.get("stats", {}).get("avg_trust_score"),
            })
        except Exception:
            pass
    return {"reports": sorted(reports, key=lambda r: r.get("timestamp", ""), reverse=True)}

@app.get("/models")
def list_models():
    try:
        client = OllamaClient()
        return {"models": client.list_models()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ollama unreachable: {e}")
