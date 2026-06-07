"""TruthLens CLI v1.0.0"""
import argparse, sys, os, json, time, subprocess, webbrowser
from pathlib import Path

ROOT = Path(__file__).parent.parent

def ok(msg):   print(f"  [OK]  {msg}")
def info(msg): print(f"  [->]  {msg}")
def err(msg):  print(f"  [!!]  {msg}")
def bold(msg): return f"\033[1m{msg}\033[0m"

def print_banner():
    print(f"""
  TruthLens v1.0.0
  The trust and evaluation layer for AI systems
  {"="*46}
""")

def check_ollama():
    try:
        import httpx
        r = httpx.get("http://localhost:11434/api/tags", timeout=3)
        return r.status_code == 200
    except: return False

def wait_for_api(timeout=25):
    import httpx
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get("http://localhost:8000/health", timeout=2)
            if r.status_code == 200: return True
        except: pass
        time.sleep(1)
    return False

def cmd_setup(args):
    print_banner()
    ok(f"Python {sys.version.split()[0]}")
    try:
        import httpx, pydantic, fastapi, uvicorn
        ok("All Python packages installed")
    except ImportError as e:
        err(f"Missing package: {e}")
        err("Run: pip install -r requirements.txt")

    try:
        result = subprocess.run(["node", "--version"], capture_output=True)
        ok(f"Node.js {result.stdout.decode().strip()}")
    except: err("Node.js not found — install from https://nodejs.org")

    if check_ollama():
        ok("Ollama is running")
        import httpx
        r = httpx.get("http://localhost:11434/api/tags", timeout=3)
        models = [m["name"] for m in r.json().get("models", [])]
        if models: ok(f"Models: {', '.join(models)}")
        else: err("No models — run: ollama pull llama3")
    else:
        err("Ollama not running")
        info("Install: https://ollama.ai")
        info("Start:   ollama serve")
        info("Model:   ollama pull llama3")
    print()

def cmd_start(args):
    print_banner()
    if not check_ollama():
        err("Ollama not running. Run: ollama serve")
        sys.exit(1)

    dashboard = ROOT / "dashboard"
    if not (dashboard / "node_modules").exists():
        info("Installing dashboard (first time, ~1 min)...")
        subprocess.run(["npm", "install"], cwd=dashboard, capture_output=True)
        ok("Dashboard ready")

    info("Starting API...")
    api = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    if not wait_for_api():
        err("API failed to start. Is port 8000 free?")
        api.terminate(); sys.exit(1)
    ok("API running at http://localhost:8000")

    info("Starting proxy...")
    proxy = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "proxy.server:app", "--host", "0.0.0.0", "--port", "8001"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(2)
    ok("Proxy running at http://localhost:8001")

    info("Starting dashboard...")
    dash = subprocess.Popen(
        ["npm", "run", "dev"], cwd=dashboard,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(3)
    ok("Dashboard running at http://localhost:5173")

    webbrowser.open("http://localhost:5173")

    print(f"""
  {bold("TruthLens is running!")}

  Dashboard  ->  http://localhost:5173
  API        ->  http://localhost:8000/docs
  Proxy      ->  http://localhost:8001/chat

  Press Ctrl+C to stop.
""")
    try:
        api.wait()
    except KeyboardInterrupt:
        info("Stopping...")
        api.terminate(); proxy.terminate(); dash.terminate()
        ok("Stopped.")

def cmd_proxy(args):
    print_banner()
    port = args.port or 8001
    os.environ["TRUTHLENS_EVAL_MODEL"] = args.eval_model or "llama3"
    info(f"Starting proxy on port {port}...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "proxy.server:app",
         "--host", "0.0.0.0", "--port", str(port), "--reload"],
        cwd=ROOT
    )
    print(f"""
  Proxy URL  ->  http://localhost:{port}/chat
  Analytics  ->  http://localhost:{port}/analytics
  Docs       ->  http://localhost:{port}/docs

  Press Ctrl+C to stop.
""")
    try: proc.wait()
    except KeyboardInterrupt: proc.terminate(); ok("Stopped.")

def cmd_evaluate(args):
    if not args.question or not args.answer or not args.sources:
        err("Required: --question --answer --sources"); sys.exit(1)
    import httpx
    info(f"Evaluating...")
    try:
        r = httpx.post("http://localhost:8000/evaluate", json={
            "question": args.question,
            "answer": args.answer,
            "sources": [args.sources],
            "model": args.model or None,
        }, timeout=180)
        r.raise_for_status()
        d = r.json()
    except httpx.ConnectError:
        err("API not running. Start with: truthlens start"); sys.exit(1)

    risk_colors = {"Low": "\033[92m", "Medium": "\033[93m", "High": "\033[91m"}
    rc = risk_colors.get(d["hallucination_risk"], "")
    reset = "\033[0m"
    print(f"""
  {"="*44}
  {bold("TruthLens Evaluation Report")}
  {"="*44}
  Trust Score:        {bold(str(round(d["trust_score"])))}/100
  Groundedness:       {d["groundedness"]:.0f}%
  Faithfulness:       {d["faithfulness"]:.0f}%
  Citation Accuracy:  {d["citation_accuracy"]:.0f}%
  Hallucination Risk: {rc}{d["hallucination_risk"]}{reset}
  {"="*44}
  Model: {d["model"]}  |  {d["latency_ms"]:.0f}ms
""")

def cmd_benchmark(args):
    import httpx
    payload = {"use_sample": True} if args.sample else {"cases": json.load(open(args.file))}
    payload["model"] = args.model or None
    try:
        r = httpx.post("http://localhost:8000/benchmark", json=payload, timeout=30)
        job_id = r.json()["job_id"]
    except httpx.ConnectError:
        err("API not running. Start with: truthlens start"); sys.exit(1)
    info(f"Running benchmark (job: {job_id})...")
    while True:
        job = httpx.get(f"http://localhost:8000/benchmark/{job_id}", timeout=10).json()
        p, t = job.get("progress", 0), job.get("total", 1)
        pct = int(p / t * 30) if t else 0
        print(f"\r  [{'#'*pct}{'-'*(30-pct)}] {p}/{t}", end="", flush=True)
        if job["status"] == "done": print(); break
        elif job["status"] == "error": print(); err(job.get("error")); sys.exit(1)
        time.sleep(1.5)
    s = job["result"]["stats"]
    print(f"""
  {"="*44}
  Benchmark Results — {s["total_cases"]} cases
  {"="*44}
  Avg Trust:    {bold(str(s["avg_trust_score"]))}/100
  Groundedness: {s["avg_groundedness"]}%
  Low Risk:     {s["low_risk_pct"]}%
  High Risk:    {s["high_risk_pct"]}%
  {"="*44}
""")

def main():
    p = argparse.ArgumentParser(prog="truthlens", description="TruthLens v1.0.0")
    s = p.add_subparsers(dest="command")

    s.add_parser("setup",  help="Check all dependencies")
    s.add_parser("start",  help="Start everything and open browser")

    px = s.add_parser("proxy", help="Start the LLM proxy server")
    px.add_argument("--port", "-p", type=int, default=8001)
    px.add_argument("--eval-model", "-e", default="llama3")

    ev = s.add_parser("evaluate", help="Evaluate a Q/A pair")
    ev.add_argument("--question", "-q")
    ev.add_argument("--answer",   "-a")
    ev.add_argument("--sources",  "-s")
    ev.add_argument("--model",    "-m", default=None)

    bm = s.add_parser("benchmark", help="Run benchmark")
    bm.add_argument("--sample", action="store_true")
    bm.add_argument("--file",   "-f")
    bm.add_argument("--model",  "-m", default=None)

    args = p.parse_args()

    if   args.command == "setup":     cmd_setup(args)
    elif args.command == "start":     cmd_start(args)
    elif args.command == "proxy":     cmd_proxy(args)
    elif args.command == "evaluate":  cmd_evaluate(args)
    elif args.command == "benchmark": cmd_benchmark(args)
    else:
        print_banner()
        p.print_help()
        print()

if __name__ == "__main__":
    main()
