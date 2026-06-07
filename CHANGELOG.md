# Changelog

## [1.0.0] — 2025-06-07

### First public release

**Core evaluation engine**
- 5-metric trust scoring: groundedness, faithfulness, citation accuracy, consistency, hallucination risk
- Composite Trust Score (0–100)
- Powered by local Ollama — no external API keys required for evaluation

**Claim-level verification (Phase 2)**
- Atomic claim extraction from AI responses
- Per-claim labeling: Supported / Unsupported / Contradicted
- Evidence extraction and source attribution

**RAG pipeline evaluation**
- Retrieval precision and recall
- Context utilization and evidence coverage
- Answer relevance scoring

**Agent evaluation**
- Tool usage accuracy
- Planning quality
- Task completion
- Decision tracing

**Benchmark runner (Phase 3)**
- Run hundreds of test cases automatically
- Per-domain and per-difficulty breakdowns
- CSV and JSON export for research

**Multi-model leaderboard (Phase 4)**
- Compare any number of models on identical datasets
- Domain winner analysis
- Ranked leaderboard with full metric breakdown

**Middleware proxy**
- Support for OpenAI, Anthropic, Gemini, and Ollama
- Automatic evaluation on every LLM call
- SQLite logging of all evaluations
- Analytics API with trend data
- 2-line Python SDK integration

**Dashboard**
- 10-page React dashboard
- Live evaluation with radar charts
- Benchmark runner with progress tracking
- Model leaderboard with bar and radar charts
- Proxy analytics with trend graphs
- Research paper generator

**Research paper generator**
- Auto-populated with real benchmark data
- Markdown and LaTeX output
- Full paper structure with research questions

**CLI**
- `truthlens start` — launch everything + open browser
- `truthlens proxy` — start middleware proxy
- `truthlens evaluate` — evaluate from terminal
- `truthlens benchmark` — run benchmark
- `truthlens setup` — check dependencies

**Developer tools**
- Chrome extension for ChatGPT, Claude, Gemini
- One-click Windows installer (install.bat)
- One-click start scripts (start.bat / start.sh)
- 36 unit tests
