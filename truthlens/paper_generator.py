"""
Research paper auto-generator.

Takes benchmark and leaderboard results and generates
a structured research paper draft in Markdown / LaTeX.
"""
from datetime import datetime
from typing import Optional
from .benchmark import BenchmarkReport
from .leaderboard import LeaderboardReport


def generate_paper(
    benchmark_report: Optional[BenchmarkReport] = None,
    leaderboard_report: Optional[LeaderboardReport] = None,
    title: str = "TruthLens: A Unified Framework for Measuring Trustworthiness in Large Language Models and Retrieval-Augmented Systems",
    authors: str = "TruthLens Research Team",
    output_format: str = "markdown",  # "markdown" | "latex"
) -> str:
    """Generate a research paper draft populated with real benchmark results."""

    # Pull stats
    stats_block = ""
    leaderboard_block = ""
    domain_block = ""

    if benchmark_report:
        s = benchmark_report.stats
        stats_block = f"""
| Metric | Value |
|--------|-------|
| Total Cases | {s.total_cases} |
| Successful | {s.successful_cases} |
| Avg Trust Score | {s.avg_trust_score:.1f}/100 |
| Avg Groundedness | {s.avg_groundedness:.1f}% |
| Avg Faithfulness | {s.avg_faithfulness:.1f}% |
| Avg Citation Accuracy | {s.avg_citation_accuracy:.1f}% |
| Low Hallucination Risk | {s.low_risk_pct:.1f}% |
| Medium Hallucination Risk | {s.medium_risk_pct:.1f}% |
| High Hallucination Risk | {s.high_risk_pct:.1f}% |
| Avg Latency | {s.avg_latency_ms:.0f}ms |
| Std Trust Score | {s.std_trust_score:.1f} |
"""
        if s.domain_stats:
            domain_block = "\n| Domain | Cases | Avg Trust | Avg Groundedness | High Hallucination % |\n|--------|-------|-----------|-----------------|---------------------|\n"
            for domain, ds in s.domain_stats.items():
                domain_block += f"| {domain} | {int(ds.get('count',0))} | {ds.get('avg_trust_score',0):.1f} | {ds.get('avg_groundedness',0):.1f}% | {ds.get('hallucination_high_pct',0):.1f}% |\n"

    if leaderboard_report:
        leaderboard_block = "\n| Rank | Model | Avg Trust | Groundedness | Faithfulness | Low Risk % | Latency |\n"
        leaderboard_block += "|------|-------|-----------|--------------|--------------|------------|--------|\n"
        for e in leaderboard_report.leaderboard:
            leaderboard_block += f"| #{e.rank} | {e.model} | {e.avg_trust_score:.1f} | {e.avg_groundedness:.1f}% | {e.avg_faithfulness:.1f}% | {e.low_risk_pct:.1f}% | {e.avg_latency_ms:.0f}ms |\n"

        if leaderboard_report.domain_winners:
            leaderboard_block += "\n**Domain Winners:**\n"
            for domain, model in leaderboard_report.domain_winners.items():
                leaderboard_block += f"- {domain}: **{model}**\n"

    paper = f"""# {title}

**Authors:** {authors}
**Date:** {datetime.utcnow().strftime("%B %Y")}
**Version:** Draft

---

## Abstract

Large Language Models (LLMs) are being rapidly deployed in production systems, yet organizations lack a principled, automated method for evaluating whether AI-generated responses can be trusted. We present **TruthLens**, an open-source evaluation framework that measures five orthogonal dimensions of AI response trustworthiness: groundedness, faithfulness, citation accuracy, consistency, and hallucination risk. TruthLens extends to Retrieval-Augmented Generation (RAG) pipelines and to agentic systems. In Phase 2, we introduce claim-level verification — decomposing answers into atomic claims and labeling each as Supported, Unsupported, or Contradicted. In Phase 3, we present a benchmark runner that evaluates hundreds of test cases and produces aggregate metrics across domains and difficulty levels. In Phase 4, we introduce a multi-model leaderboard enabling rigorous cross-model comparison. All evaluation is performed locally via Ollama, requiring no external API keys.

---

## 1. Introduction

The deployment of LLMs in mission-critical applications has outpaced the development of tools to assess their reliability. Models frequently hallucinate facts, misattribute sources, and produce overconfident responses. Existing evaluation frameworks address subsets of this problem but lack a unified interface covering core answer evaluation, RAG pipeline assessment, claim-level verification, and agentic task evaluation within a single framework.

TruthLens addresses this gap with five contributions:

1. A five-metric evaluation scheme for individual LLM responses
2. Claim-level verification (Supported / Unsupported / Contradicted)
3. A five-metric RAG pipeline evaluator
4. A four-metric agent evaluator
5. A benchmark runner and multi-model leaderboard

---

## 2. Related Work

**RAGAS** provides faithfulness and answer relevance metrics for RAG systems but does not support agentic evaluation or standalone answer assessment. **TruLens** offers feedback functions for RAG and agents but requires significant instrumentation. **DeepEval** provides a broad metric library but is primarily designed for regression testing rather than production monitoring.

TruthLens differentiates itself through: (a) zero-instrumentation design; (b) local-first architecture via Ollama; (c) claim-level decomposition; and (d) a unified trust score compositing all available metrics.

---

## 3. Framework Architecture

### 3.1 Core Evaluation (Phase 1)

Given a triple *(q, a, S)* where *q* is a question, *a* is an AI-generated answer, and *S* is a set of source documents, TruthLens computes:

| Metric | Weight |
|--------|--------|
| Groundedness G | 35% |
| Faithfulness F | 30% |
| Citation Accuracy C | 20% |
| Consistency K | 15% |

**Trust Score:** T = 0.35·G + 0.30·F + 0.20·C + 0.15·K

**Hallucination Risk:**
- Low: G ≥ 85 and F ≥ 85
- Medium: G ≥ 65 and F ≥ 65
- High: otherwise

### 3.2 Claim-Level Verification (Phase 2)

Each answer is decomposed into atomic claims. Each claim is verified as:
- **Supported** — directly or inferentially backed by sources
- **Unsupported** — not addressed by sources
- **Contradicted** — directly conflicts with sources

**Claim Trust Score:** (supported × 1.0 + unsupported × 0.3 + contradicted × 0.0) / total × 100

### 3.3 RAG Evaluation

| Metric | Weight |
|--------|--------|
| Retrieval Precision | 20% |
| Retrieval Recall | 20% |
| Context Utilization | 25% |
| Evidence Coverage | 20% |
| Answer Relevance | 15% |

### 3.4 Agent Evaluation

| Metric | Weight |
|--------|--------|
| Tool Usage Accuracy | 25% |
| Planning Quality | 25% |
| Task Completion | 35% |
| Decision Tracing | 15% |

### 3.5 Benchmark Runner (Phase 3)

The benchmark runner accepts a dataset of *(question, answer, sources)* triples with optional domain and difficulty labels. It runs all cases through the evaluation pipeline and computes aggregate statistics including per-domain and per-difficulty breakdowns.

### 3.6 Model Leaderboard (Phase 4)

The leaderboard runs the same dataset across multiple models and ranks them by average trust score, with per-domain winner analysis.

---

## 4. Benchmark Results

### 4.1 Single-Model Results
{stats_block if stats_block else "_No benchmark data yet. Run a benchmark to populate this section._"}

### 4.2 Domain Breakdown
{domain_block if domain_block else "_No domain data available._"}

### 4.3 Multi-Model Leaderboard
{leaderboard_block if leaderboard_block else "_No leaderboard data yet. Run a multi-model comparison to populate this section._"}

---

## 5. Research Questions

This framework is designed to address the following open research questions:

**RQ1:** Can a multi-metric evaluation framework predict factual reliability better than any single metric?

**RQ2:** Does claim-level verification correlate with human judgments of answer trustworthiness?

**RQ3:** How does hallucination rate vary across domains (medical, finance, science, history)?

**RQ4:** Does model size correlate with trust scores on domain-specific benchmarks?

**RQ5:** What is the relationship between retrieval quality and final answer trustworthiness in RAG systems?

---

## 6. Discussion

**Limitations.** TruthLens relies on an LLM judge, which introduces its own potential for error. Smaller models (7B parameters) may lack reasoning capacity for accurate evaluation of complex multi-hop answers. The claim extraction step may over- or under-segment answers.

**Future Work.**
- Fine-tuned evaluation model optimized for trustworthiness scoring
- Calibration against human judgments on crowdsourced datasets
- Streaming evaluation for long documents
- Integration with CI/CD pipelines for regression testing

---

## 7. Conclusion

TruthLens provides a practical, locally-runnable framework for measuring AI trustworthiness across four deployment contexts: standalone answers, claim-level verification, RAG pipelines, and agentic systems. The benchmark runner and leaderboard enable systematic comparison across models and domains, generating the data needed for publication-quality research.

---

## References

1. Ji, S. et al. (2023). Survey of Hallucination in Natural Language Generation. *ACM Computing Surveys*.
2. Es, S. et al. (2023). RAGAS: Automated Evaluation of Retrieval Augmented Generation. *arXiv:2309.15217*.
3. Truera (2023). TruLens: Evaluation and Tracking for LLM Experiments.
4. Zhuang, Y. et al. (2023). DeepEval: A Framework for Evaluating Large Language Models.
5. Mündler, N. et al. (2023). Self-contradictory Hallucinations of LLMs. *arXiv:2305.15852*.
6. Min, S. et al. (2023). FActScoring: Fine-Grained Atomic Evaluation of Factual Precision. *ACL 2023*.
"""

    if output_format == "latex":
        # Basic LaTeX wrapper
        paper = paper.replace("**", "\\textbf{").replace("**", "}")
        paper = f"""\\documentclass{{article}}
\\usepackage{{booktabs}}
\\usepackage{{hyperref}}
\\title{{{title}}}
\\author{{{authors}}}
\\date{{{datetime.utcnow().strftime("%B %Y")}}}
\\begin{{document}}
\\maketitle
% Auto-generated by TruthLens paper generator
{paper}
\\end{{document}}"""

    return paper
