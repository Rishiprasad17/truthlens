"""
TruthLens Proxy — Usage Examples

Shows how to integrate TruthLens with OpenAI, Anthropic, Gemini, and Ollama
in 2 lines of code.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from proxy.sdk import TruthLens


# ── Example 1: Ollama (local, no API key) ──────────────────────────────────────

def example_ollama():
    print("\n" + "="*50)
    print("Example 1: Ollama (local)")
    print("="*50)

    tl = TruthLens(
        provider="ollama",
        model="llama3",
        eval_model="llama3",
    )

    response = tl.chat(
        message="Who created Python and when was it first released?",
        sources=[
            "Python is a high-level programming language created by Guido van Rossum. "
            "It was first released in 1991."
        ],
    )

    print(f"\nAnswer: {response.content[:200]}...")
    print(f"\n{response.summary()}")
    print(f"Latency: {response.latency_ms:.0f}ms (eval: {response.eval_latency_ms:.0f}ms)")


# ── Example 2: OpenAI ──────────────────────────────────────────────────────────

def example_openai():
    print("\n" + "="*50)
    print("Example 2: OpenAI GPT-4o")
    print("="*50)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Skipping: OPENAI_API_KEY not set")
        return

    tl = TruthLens(
        provider="openai",
        model="gpt-4o",
        api_key=api_key,
        include_claims=True,
    )

    response = tl.chat(
        message="What caused the 2008 financial crisis?",
        sources=[
            "The 2008 financial crisis was caused by the collapse of the US housing bubble. "
            "Risky mortgage lending and complex financial instruments spread risk globally. "
            "Lehman Brothers filed for bankruptcy in September 2008."
        ],
        tags=["finance", "history"],
        session_id="research-session-001",
    )

    print(f"\nAnswer: {response.content[:200]}...")
    print(f"\n{response.summary()}")

    if response.claims:
        print(f"\nClaim breakdown ({response.total_claims} claims):")
        for claim in response.claims[:3]:
            icon = {"Supported": "✓", "Unsupported": "?", "Contradicted": "✗"}.get(claim["verdict"], "?")
            print(f"  {icon} {claim['verdict']}: {claim['text'][:80]}...")


# ── Example 3: Anthropic ───────────────────────────────────────────────────────

def example_anthropic():
    print("\n" + "="*50)
    print("Example 3: Anthropic Claude")
    print("="*50)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Skipping: ANTHROPIC_API_KEY not set")
        return

    tl = TruthLens(
        provider="anthropic",
        model="claude-sonnet-4-6",
        api_key=api_key,
        system_prompt="You are a helpful assistant. Be concise.",
    )

    response = tl.chat(
        message="How does photosynthesis work?",
        sources=[
            "Photosynthesis is a process by which plants convert light energy into glucose. "
            "It uses carbon dioxide and water, releasing oxygen as a byproduct. "
            "It occurs in chloroplasts."
        ],
    )

    print(f"\nAnswer: {response.content[:200]}...")
    print(f"\n{response.summary()}")


# ── Example 4: Multi-model research comparison ────────────────────────────────

def example_research_comparison():
    print("\n" + "="*50)
    print("Example 4: Research — Multi-model comparison")
    print("="*50)

    question = "What is the speed of light?"
    sources = ["The speed of light in a vacuum is approximately 299,792,458 metres per second (m/s)."]

    models = [
        ("ollama", "llama3", {}),
        ("ollama", "mistral", {}),
    ]

    results = []
    for provider, model, kwargs in models:
        try:
            tl = TruthLens(provider=provider, model=model, **kwargs)
            r = tl.chat(question, sources=sources)
            results.append((model, r))
            print(f"\n  {model}: trust={r.trust_score:.0f} ground={r.groundedness:.0f}% faith={r.faithfulness:.0f}%")
        except Exception as e:
            print(f"\n  {model}: skipped ({e})")

    if results:
        winner = max(results, key=lambda x: x[1].trust_score)
        print(f"\n  Winner: {winner[0]} (trust score: {winner[1].trust_score:.0f}/100)")


# ── Example 5: Analytics ──────────────────────────────────────────────────────

def example_analytics():
    print("\n" + "="*50)
    print("Example 5: Analytics & Export")
    print("="*50)

    tl = TruthLens(provider="ollama", model="llama3")
    analytics = tl.get_analytics()

    if analytics.get("total", 0) == 0:
        print("  No evaluations logged yet. Run other examples first.")
        return

    print(f"  Total evaluations: {analytics['total']}")
    print(f"  Avg trust score:   {analytics['avg_trust']}/100")
    print(f"  Avg groundedness:  {analytics['avg_groundedness']}%")
    print(f"  High risk count:   {analytics['high_risk_count']}")

    if analytics.get("by_model"):
        print("\n  By model:")
        for m in analytics["by_model"]:
            print(f"    {m['model']}: trust={m['avg_trust']:.1f} ({m['count']} calls)")

    # Export for research
    n = tl.export_csv("truthlens_research_export.csv")
    print(f"\n  Exported {n} rows to truthlens_research_export.csv")


if __name__ == "__main__":
    example_ollama()
    example_openai()
    example_anthropic()
    example_research_comparison()
    example_analytics()
