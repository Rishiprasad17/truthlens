import time
from typing import List, Optional
from .models import RAGReport
from .ollama_client import get_client

RAG_SYSTEM = """You are TruthLens RAG Evaluator. Assess the quality of a Retrieval-Augmented Generation pipeline.

Evaluate these dimensions (0-100 each):
1. retrieval_precision: Are the retrieved chunks relevant to the question?
2. retrieval_recall: Do the retrieved chunks cover all aspects needed to answer?
3. context_utilization: How well does the answer actually USE the retrieved context?
4. evidence_coverage: What fraction of the answer's claims are backed by retrieved evidence?
5. answer_relevance: Is the final answer directly responsive to the question?

Respond ONLY with valid JSON:
{
  "retrieval_precision": <0-100>,
  "retrieval_recall": <0-100>,
  "context_utilization": <0-100>,
  "evidence_coverage": <0-100>,
  "answer_relevance": <0-100>,
  "reasoning": {
    "retrieval_precision": "<one sentence>",
    "retrieval_recall": "<one sentence>",
    "context_utilization": "<one sentence>",
    "evidence_coverage": "<one sentence>",
    "answer_relevance": "<one sentence>"
  }
}"""


def evaluate_rag(
    question: str,
    answer: str,
    retrieved_chunks: List[str],
    model: Optional[str] = None,
) -> RAGReport:
    """
    Evaluate a RAG pipeline's retrieval and generation quality.

    Args:
        question: The original query
        answer: The generated answer
        retrieved_chunks: The chunks retrieved and passed to the LLM
        model: Ollama model name

    Returns:
        RAGReport with retrieval and generation metrics
    """
    client = get_client(model)

    chunks_text = "\n\n".join(
        f"[Chunk {i+1}]\n{c}" for i, c in enumerate(retrieved_chunks)
    )
    prompt = f"""QUESTION: {question}

RETRIEVED CHUNKS:
{chunks_text}

GENERATED ANSWER:
{answer}

Evaluate the RAG pipeline quality."""

    t0 = time.perf_counter()
    result = client.chat_json(RAG_SYSTEM, prompt)
    latency_ms = (time.perf_counter() - t0) * 1000

    p = float(result.get("retrieval_precision", 0))
    r = float(result.get("retrieval_recall", 0))
    cu = float(result.get("context_utilization", 0))
    ec = float(result.get("evidence_coverage", 0))
    ar = float(result.get("answer_relevance", 0))

    rag_score = round(p * 0.20 + r * 0.20 + cu * 0.25 + ec * 0.20 + ar * 0.15, 1)

    return RAGReport(
        question=question,
        retrieval_precision=p,
        retrieval_recall=r,
        context_utilization=cu,
        evidence_coverage=ec,
        answer_relevance=ar,
        rag_score=rag_score,
        reasoning=result.get("reasoning", {}),
        model=client.model,
        latency_ms=round(latency_ms, 1),
    )
