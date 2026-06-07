# TruthLens — Getting Started Guide

> Complete setup guide for students and developers.
> No experience required. Estimated time: 15 minutes.

---

## What is TruthLens?

TruthLens is a tool that sits next to any AI chatbot and automatically checks:
- Is this answer actually grounded in real sources?
- Did the AI hallucinate anything?
- How trustworthy is this response?

It gives every AI response a **Trust Score out of 100**.

---

## What You Need (Prerequisites)

Before starting, install these three things:

### 1. Python (required)
- Go to: **https://python.org/downloads**
- Download Python 3.10 or newer
- **Important:** During install, check the box that says **"Add Python to PATH"**
- Verify: Open a terminal and type `python --version`

### 2. Node.js (required for dashboard)
- Go to: **https://nodejs.org**
- Download the **LTS version** (recommended)
- Verify: Open a terminal and type `node --version`

### 3. Ollama (required — runs AI models locally)
- Go to: **https://ollama.ai**
- Download and install for your operating system
- After installing, open a terminal and run:
  ```
  ollama pull llama3
  ```
  This downloads the AI model (~4GB, takes a few minutes)

---

## Installation

### Step 1 — Download TruthLens
Download the zip file and extract it to a folder, for example:
- Windows: `C:\truthlens`
- Mac/Linux: `~/truthlens`

### Step 2 — Run the installer

**Windows:**
```
Double-click install.bat
```
Or in PowerShell:
```powershell
cd C:\truthlens
.\install.bat
```

**Mac/Linux:**
```bash
cd ~/truthlens
chmod +x install.sh
./install.sh
```

The installer will:
- Install all Python packages automatically
- Install all dashboard packages automatically
- Set up the TruthLens CLI

---

## Starting TruthLens

### Windows (easiest)
```
Double-click start.bat
```
That's it. The browser opens automatically at `http://localhost:5173`.

### Mac/Linux
```bash
cd ~/truthlens
./start.sh
```

### Manual start (if the above doesn't work)
Open **3 terminal windows** and run one command in each:

**Terminal 1 — API:**
```bash
cd C:\truthlens
python -m uvicorn api.main:app --port 8000
```

**Terminal 2 — Proxy:**
```bash
cd C:\truthlens
python -m uvicorn proxy.server:app --port 8001
```

**Terminal 3 — Dashboard:**
```bash
cd C:\truthlens\dashboard
npm run dev
```

Then open your browser at: **http://localhost:5173**

---

## Your First Evaluation

Once the dashboard is open:

1. Click **Evaluate** in the left sidebar
2. Fill in:
   - **Question:** `Who created Python?`
   - **Answer:** `Python was created by Guido van Rossum in 1991.`
   - **Sources:** `Python is a programming language created by Guido van Rossum, first released in 1991.`
3. Click **Run Evaluation**
4. Wait 30-60 seconds (it's thinking)
5. See your Trust Score!

---

## Dashboard Pages Explained

| Page | What it does |
|------|-------------|
| **Evaluate** | Check any AI answer against source documents |
| **Claims** | See exactly which sentences are supported vs hallucinated |
| **RAG Eval** | Evaluate a RAG pipeline's retrieval quality |
| **Agent Eval** | Evaluate an AI agent's task execution |
| **Compare** | Compare two or more models on the same question |
| **Benchmark** | Run 100s of test cases automatically |
| **Leaderboard** | Rank multiple models by trust score |
| **Proxy** | See live analytics from the proxy server |
| **Paper** | Generate a research paper with your results |
| **History** | Browse past evaluations |

---

## Integrating with Your AI Chatbot

### If you're building in Python

**Before TruthLens** (normal code):
```python
import openai

response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Who created Python?"}]
)
answer = response.choices[0].message.content
print(answer)
```

**After TruthLens** (2 line change):
```python
from proxy.sdk import TruthLens

tl = TruthLens(provider="openai", model="gpt-4o", api_key="your-key")
response = tl.chat(
    message="Who created Python?",
    sources=["Python was created by Guido van Rossum in 1991."]
)

print(response.content)            # same AI answer as before
print(response.trust_score)        # NEW: 95.0
print(response.hallucination_risk) # NEW: Low
print(response.groundedness)       # NEW: 96.0%
```

That's the only change. Everything else stays the same.

---

### If you're building in JavaScript/TypeScript

```javascript
// Instead of calling OpenAI directly, call the TruthLens proxy
const response = await fetch("http://localhost:8001/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    provider: "openai",
    model: "gpt-4o",
    api_key: "your-openai-key",
    messages: [{ role: "user", content: userMessage }],
    sources: yourDocuments  // optional but recommended
  })
})

const data = await response.json()
console.log(data.content)            // AI answer
console.log(data.trust_score)        // 95.0
console.log(data.hallucination_risk) // "Low"
```

---

### Supported AI Providers

| Provider | Model examples | API Key needed? |
|----------|---------------|-----------------|
| **Ollama** (local) | llama3, mistral, phi3 | No — free |
| **OpenAI** | gpt-4o, gpt-3.5-turbo | Yes — openai.com |
| **Anthropic** | claude-sonnet-4-6 | Yes — console.anthropic.com |
| **Gemini** | gemini-1.5-flash | Yes — aistudio.google.com |

---

## Setting Up API Keys

You don't need API keys to use TruthLens with Ollama (local models).

If you want to test OpenAI, Anthropic, or Gemini:

### OpenAI
1. Go to: https://platform.openai.com/api-keys
2. Create a new key
3. Pass it as `api_key` in your request

### Anthropic
1. Go to: https://console.anthropic.com
2. Create a new key
3. Pass it as `api_key` in your request

### Gemini
1. Go to: https://aistudio.google.com/app/apikey
2. Create a new key
3. Pass it as `api_key` in your request

---

## Running the Benchmark (Research)

The benchmark runs hundreds of test cases automatically and produces research-ready output.

### Quick test (built-in dataset):
```powershell
# Make sure API is running first, then:
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/benchmark" `
  -ContentType "application/json" `
  -Body '{"use_sample": true}'
```

Or use the **Benchmark** tab in the dashboard — select "Sample Dataset" and click Run.

### Your own dataset:
Create a file `my_cases.json`:
```json
[
  {
    "id": "case_001",
    "domain": "science",
    "difficulty": "easy",
    "question": "What is photosynthesis?",
    "answer": "Photosynthesis converts sunlight into energy.",
    "sources": ["Photosynthesis is the process by which plants use light to produce glucose."]
  }
]
```

Then run it through the Benchmark tab by uploading the JSON.

### Export results for research:
```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:8001/export"
```
Opens `truthlens_export.csv` — import into Excel or Python for analysis.

---

## Common Problems and Fixes

### "Ollama is not running"
```bash
ollama serve
```
Then try again.

### "No models found"
```bash
ollama pull llama3
```

### "Port already in use"
Run `stop.bat` then `start.bat` again.

### "npm not found"
Install Node.js from https://nodejs.org

### Evaluation takes too long (>2 minutes)
This is normal on CPU. Try a smaller model:
```bash
ollama pull phi3
```
Then use `"model": "phi3"` in your requests.

### Dashboard shows blank page
Make sure all 3 servers are running (API on 8000, Proxy on 8001, Dashboard on 5173).

---

## Stopping TruthLens

**Windows:**
```
Double-click stop.bat
```
Or press any key in the `start.bat` window.

**Mac/Linux:**
Press `Ctrl+C` in each terminal window.

---

## Project Structure (for developers)

```
truthlens/
├── start.bat              ← Windows: double-click to start everything
├── stop.bat               ← Windows: double-click to stop everything
├── install.bat            ← Windows: run once to install
├── install.sh             ← Mac/Linux: run once to install
│
├── truthlens/             ← Core Python evaluation library
│   ├── evaluator.py       ← Trust score, groundedness, faithfulness
│   ├── claims.py          ← Claim-level verification
│   ├── benchmark.py       ← Benchmark runner
│   ├── leaderboard.py     ← Multi-model leaderboard
│   └── paper_generator.py ← Research paper auto-generator
│
├── proxy/                 ← Middleware proxy layer
│   ├── sdk.py             ← Python SDK (2-line integration)
│   ├── server.py          ← Proxy server (port 8001)
│   ├── providers.py       ← OpenAI, Anthropic, Gemini, Ollama adapters
│   └── database.py        ← SQLite storage for all evaluations
│
├── api/                   ← Main API server (port 8000)
├── dashboard/             ← React dashboard (port 5173)
├── tests/                 ← 36 unit tests
└── paper/PAPER.md         ← Research paper draft
```

---

## For Research Students

TruthLens is designed to support research on AI trustworthiness. Here's how to use it for a research project:

### Step 1 — Build your dataset
Create 50-100 question/answer/source triples covering different domains (science, history, medicine, finance).

### Step 2 — Run the benchmark
Use the Benchmark tab to evaluate all cases automatically. Results saved to SQLite and CSV.

### Step 3 — Compare models
Use the Leaderboard tab to run the same dataset through multiple models (llama3, mistral, phi3).

### Step 4 — Export and analyze
Export to CSV → open in Python/Excel → compute statistics → make charts.

### Step 5 — Generate paper
Use the Paper tab → select your benchmark run → download the populated research paper draft.

### Research questions you can answer:
- Which model has the lowest hallucination rate?
- How does trust score vary by domain?
- Does model size correlate with groundedness?
- What is the relationship between retrieval quality and trust?

---

## Getting Help

- Check this guide first
- Open an issue on GitHub
- Email: truthlens@yourorg.com

---

*TruthLens is open source under the MIT License.*
*Built for researchers, developers, and students.*
