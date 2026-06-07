# TruthLens

> **The trust and evaluation layer for AI systems.**

[![PyPI version](https://img.shields.io/badge/pypi-v1.0.0-blue)](https://pypi.org/project/truthlens)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

TruthLens automatically scores any AI response for **groundedness**, **faithfulness**, **hallucination risk**, and overall **trustworthiness** — in 2 lines of code.

---

## Install

```bash
pip install truthlens-ai
```

Requires [Ollama](https://ollama.ai) for local evaluation (free), or any LLM API key.

---

## Quick Start

```python
from truthlens import TruthLens

# Local — no API key needed
tl = TruthLens(provider="ollama", model="llama3")
response = tl.chat(
    "Who created Python?",
    sources=["Python was created by Guido van Rossum, first released in 1991."]
)

print(response.content)             # AI's answer
print(response.trust_score)         # 95.0
print(response.hallucination_risk)  # Low
print(response.summary())
# [TruthLens] Trust: 95/100 | Ground: 96% | Faith: 94% | Hallucination: ✓ Low
```

---

## Supported Providers

```python
# OpenAI
tl = TruthLens(provider="openai",     model="gpt-4o",              api_key="sk-...")
# Anthropic
tl = TruthLens(provider="anthropic",  model="claude-sonnet-4-6",   api_key="sk-ant-...")
# Gemini
tl = TruthLens(provider="gemini",     model="gemini-1.5-flash",    api_key="AI...")
# Local Ollama (free)
tl = TruthLens(provider="ollama",     model="llama3")
```

---

## What Gets Scored

| Metric                 | Description                                    |
| ---------------------- | ---------------------------------------------- |
| **Trust Score**        | Composite 0–100                                |
| **Groundedness**       | How strongly the answer is backed by sources   |
| **Faithfulness**       | Whether the answer accurately reflects sources |
| **Citation Accuracy**  | Whether references are valid                   |
| **Hallucination Risk** | Low / Medium / High                            |

---

## Claim-Level Verification

```python
tl = TruthLens(provider="ollama", model="llama3", include_claims=True)
response = tl.chat("Tell me about Python", sources=["..."])

for claim in response.claims:
    print(f"{claim['verdict']}: {claim['text']}")
# Supported:    Python was created by Guido van Rossum
# Unsupported:  Python was initially called ABC
```

---

## RAG Evaluation

```python
from truthlens import evaluate_rag

report = evaluate_rag(
    question="What is photosynthesis?",
    answer=generated_answer,
    retrieved_chunks=your_chunks,
)
print(report.rag_score)  # 90.1
```

---

## Benchmark Runner

```python
from truthlens import run_benchmark, generate_sample_dataset

report = run_benchmark(generate_sample_dataset(), model="llama3")
print(report.stats.avg_trust_score)  # 87.3
```

---

## REST API (Proxy Server)

```bash
truthlens proxy
```

Then from any language:

```javascript
const r = await fetch("http://localhost:8001/chat", {
  method: "POST",
  body: JSON.stringify({
    provider: "openai",
    model: "gpt-4o",
    api_key: "sk-...",
    messages: [{ role: "user", content: "Who created Python?" }],
    sources: ["Python was created by Guido van Rossum in 1991."],
  }),
});
const data = await r.json();
console.log(data.trust_score); // 95.0
```

---

## Dashboard

```bash
truthlens start
```

Opens at `http://localhost:5173` — 10 pages covering evaluate, claims, RAG, agent, benchmark, leaderboard, proxy analytics, and paper generation.

---

## CLI

```bash
truthlens setup                          # check dependencies
truthlens start                          # start everything + open browser
truthlens proxy                          # start proxy server
truthlens evaluate -q "..." -a "..." -s "..."   # evaluate from terminal
truthlens benchmark --sample             # run built-in benchmark
```

---

## Research

TruthLens is designed to support AI trustworthiness research.

**Research questions:**

- RQ1: Can multi-metric evaluation predict factual reliability better than single metrics?
- RQ2: Does claim-level verification correlate with human judgments?
- RQ3: How does hallucination rate vary across domains?
- RQ4: Does model size correlate with trust scores?

See [`paper/PAPER.md`](paper/PAPER.md) for the research paper draft.

---

## Project Structure

```
truthlens/
├── truthlens/          ← Core evaluation library
│   ├── evaluator.py    ← 5-metric trust scoring
│   ├── claims.py       ← Claim-level verification
│   ├── rag.py          ← RAG pipeline evaluation
│   ├── agent.py        ← Agent trace evaluation
│   ├── benchmark.py    ← Benchmark runner
│   ├── leaderboard.py  ← Multi-model leaderboard
│   └── paper_generator.py ← Research paper generator
├── proxy/              ← Middleware proxy layer
│   ├── sdk.py          ← Python SDK (2-line integration)
│   ├── server.py       ← FastAPI proxy (port 8001)
│   ├── providers.py    ← OpenAI/Anthropic/Gemini/Ollama
│   └── database.py     ← SQLite evaluation logs
├── api/                ← Main API server (port 8000)
├── dashboard/          ← React dashboard (port 5173)
├── tests/              ← 36 unit tests
├── paper/              ← Research paper draft
├── start.bat           ← Windows: one-click start
├── start.sh            ← Mac/Linux: one-click start
└── GETTING_STARTED.md  ← Full setup guide
```

---

## Contributing

1. Fork the repo
2. Create your branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -m "Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## License

MIT © TruthLens Contributors
