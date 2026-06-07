from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class HallucinationRisk(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class EvaluationReport(BaseModel):
    question: str
    answer: str
    groundedness: float = Field(..., ge=0, le=100, description="% answer supported by sources")
    faithfulness: float = Field(..., ge=0, le=100, description="% answer faithful to retrieved info")
    citation_accuracy: float = Field(..., ge=0, le=100, description="% citations verified")
    hallucination_risk: HallucinationRisk
    consistency_score: float = Field(..., ge=0, le=100, description="stability across runs")
    trust_score: float = Field(..., ge=0, le=100, description="composite trust score")
    reasoning: Dict[str, str] = Field(default_factory=dict, description="per-metric explanations")
    unsupported_claims: List[str] = Field(default_factory=list)
    model: str = "unknown"
    latency_ms: Optional[float] = None

    def __str__(self):
        lines = [
            f"{'='*40}",
            f"  TruthLens Evaluation Report",
            f"{'='*40}",
            f"  Groundedness:      {self.groundedness:.0f}%",
            f"  Faithfulness:      {self.faithfulness:.0f}%",
            f"  Citation Accuracy: {self.citation_accuracy:.0f}%",
            f"  Consistency:       {self.consistency_score:.0f}%",
            f"  Hallucination Risk: {self.hallucination_risk.value}",
            f"  Trust Score:       {self.trust_score:.0f}/100",
            f"{'='*40}",
        ]
        if self.unsupported_claims:
            lines.append("  Unsupported Claims:")
            for c in self.unsupported_claims:
                lines.append(f"    - {c}")
        return "\n".join(lines)


class RAGReport(BaseModel):
    question: str
    retrieval_precision: float = Field(..., ge=0, le=100)
    retrieval_recall: float = Field(..., ge=0, le=100)
    context_utilization: float = Field(..., ge=0, le=100)
    evidence_coverage: float = Field(..., ge=0, le=100)
    answer_relevance: float = Field(..., ge=0, le=100)
    rag_score: float = Field(..., ge=0, le=100, description="composite RAG quality score")
    reasoning: Dict[str, str] = Field(default_factory=dict)
    model: str = "unknown"
    latency_ms: Optional[float] = None


class AgentReport(BaseModel):
    task: str
    tool_usage_accuracy: float = Field(..., ge=0, le=100)
    planning_quality: float = Field(..., ge=0, le=100)
    task_completion: float = Field(..., ge=0, le=100)
    decision_tracing_score: float = Field(..., ge=0, le=100)
    agent_score: float = Field(..., ge=0, le=100)
    reasoning: Dict[str, str] = Field(default_factory=dict)
    model: str = "unknown"
    latency_ms: Optional[float] = None


class ModelScore(BaseModel):
    model: str
    groundedness: float
    faithfulness: float
    citation_accuracy: float
    hallucination_risk: HallucinationRisk
    trust_score: float
    latency_ms: Optional[float] = None


class ComparisonReport(BaseModel):
    question: str
    models: List[ModelScore]
    winner: str
    reasoning: str
