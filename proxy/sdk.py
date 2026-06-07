"""
TruthLens SDK
=============
Two-line integration for any Python application.

    from truthlens.sdk import TruthLens

    tl = TruthLens(provider="openai", model="gpt-4o")
    response = tl.chat("Who created Python?", sources=[...])
    print(response.trust_score)
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from typing import List, Optional, Dict, Any
from proxy.core import TruthLensProxy, TruthLensResponse


class TruthLens:
    """
    The simplest way to add trust evaluation to any AI application.

    Examples
    --------
    # OpenAI
    tl = TruthLens(provider="openai", model="gpt-4o", api_key="sk-...")
    response = tl.chat("What is photosynthesis?", sources=["Photosynthesis is..."])

    # Anthropic
    tl = TruthLens(provider="anthropic", model="claude-sonnet-4-6", api_key="sk-ant-...")
    response = tl.chat("Explain quantum computing")

    # Gemini
    tl = TruthLens(provider="gemini", model="gemini-1.5-flash", api_key="AI...")
    response = tl.chat("Who was Einstein?")

    # Local Ollama (no API key needed)
    tl = TruthLens(provider="ollama", model="llama3")
    response = tl.chat("What is the capital of France?")

    # With claim-level verification
    tl = TruthLens(provider="openai", model="gpt-4o", include_claims=True)
    response = tl.chat("...", sources=["..."])
    for claim in response.claims:
        print(f"{claim['verdict']}: {claim['text']}")
    """

    def __init__(
        self,
        provider: str = "ollama",
        model: str = "llama3",
        api_key: Optional[str] = None,
        eval_model: str = "llama3",
        include_claims: bool = False,
        auto_log: bool = True,
        db_path: str = "./truthlens.db",
        system_prompt: Optional[str] = None,
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.system_prompt = system_prompt
        self._provider_kwargs = {"api_key": api_key} if api_key else {}

        self._proxy = TruthLensProxy(
            eval_model=eval_model,
            include_claims=include_claims,
            auto_log=auto_log,
            db_path=db_path,
        )

    def chat(
        self,
        message: str,
        sources: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> TruthLensResponse:
        """Send a message and get back the response with trust scores."""
        messages = []
        sp = system_prompt or self.system_prompt
        if sp:
            messages.append({"role": "system", "content": sp})
        messages.append({"role": "user", "content": message})

        return self._proxy.chat(
            provider=self.provider,
            model=self.model,
            messages=messages,
            sources=sources,
            session_id=session_id,
            user_id=user_id,
            tags=tags,
            temperature=temperature,
            max_tokens=max_tokens,
            **self._provider_kwargs,
        )

    def chat_with_history(
        self,
        messages: List[Dict[str, str]],
        sources: Optional[List[str]] = None,
        **kwargs,
    ) -> TruthLensResponse:
        """Send a full conversation history."""
        return self._proxy.chat(
            provider=self.provider,
            model=self.model,
            messages=messages,
            sources=sources,
            **self._provider_kwargs,
            **kwargs,
        )

    def get_analytics(self) -> Dict[str, Any]:
        """Get aggregate stats for all logged evaluations."""
        from proxy.database import get_analytics
        return get_analytics()

    def export_csv(self, path: str = "truthlens_export.csv") -> int:
        """Export all evaluations to CSV. Returns number of rows exported."""
        from proxy.database import export_csv
        return export_csv(path)

    def get_history(self, limit: int = 50) -> List[Dict]:
        """Get recent evaluation history."""
        from proxy.database import get_evaluations
        return get_evaluations(
            provider=self.provider,
            model=self.model,
            limit=limit,
        )
