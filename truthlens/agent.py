import time
from typing import List, Dict, Any, Optional
from .models import AgentReport
from .ollama_client import get_client

AGENT_SYSTEM = """You are TruthLens Agent Evaluator. Assess the quality of an AI agent's execution trace.

Evaluate these dimensions (0-100 each):
1. tool_usage_accuracy: Did the agent use the right tools with correct parameters?
2. planning_quality: Was the agent's multi-step plan logical and efficient?
3. task_completion: Was the final task goal achieved?
4. decision_tracing_score: Are the agent's decision points clear and well-reasoned?

Respond ONLY with valid JSON:
{
  "tool_usage_accuracy": <0-100>,
  "planning_quality": <0-100>,
  "task_completion": <0-100>,
  "decision_tracing_score": <0-100>,
  "reasoning": {
    "tool_usage_accuracy": "<one sentence>",
    "planning_quality": "<one sentence>",
    "task_completion": "<one sentence>",
    "decision_tracing_score": "<one sentence>"
  }
}"""


def evaluate_agent(
    task: str,
    agent_trace: List[Dict[str, Any]],
    final_output: str,
    model: Optional[str] = None,
) -> AgentReport:
    """
    Evaluate an AI agent's execution trace.

    Args:
        task: The original task description
        agent_trace: List of steps, each a dict with 'thought', 'tool', 'input', 'output'
        final_output: The agent's final answer/result
        model: Ollama model name

    Returns:
        AgentReport with agent quality metrics
    """
    client = get_client(model)

    trace_text = ""
    for i, step in enumerate(agent_trace):
        trace_text += f"\nStep {i+1}:\n"
        if "thought" in step:
            trace_text += f"  Thought: {step['thought']}\n"
        if "tool" in step:
            trace_text += f"  Tool: {step['tool']}\n"
            trace_text += f"  Input: {step.get('input', '')}\n"
            trace_text += f"  Output: {step.get('output', '')}\n"

    prompt = f"""TASK: {task}

AGENT EXECUTION TRACE:
{trace_text}

FINAL OUTPUT:
{final_output}

Evaluate the agent's performance."""

    t0 = time.perf_counter()
    result = client.chat_json(AGENT_SYSTEM, prompt)
    latency_ms = (time.perf_counter() - t0) * 1000

    tu = float(result.get("tool_usage_accuracy", 0))
    pq = float(result.get("planning_quality", 0))
    tc = float(result.get("task_completion", 0))
    dt = float(result.get("decision_tracing_score", 0))

    agent_score = round(tu * 0.25 + pq * 0.25 + tc * 0.35 + dt * 0.15, 1)

    return AgentReport(
        task=task,
        tool_usage_accuracy=tu,
        planning_quality=pq,
        task_completion=tc,
        decision_tracing_score=dt,
        agent_score=agent_score,
        reasoning=result.get("reasoning", {}),
        model=client.model,
        latency_ms=round(latency_ms, 1),
    )
