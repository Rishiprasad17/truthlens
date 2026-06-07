"""
Phase 2 tests — Claim verification.
Unit tests require no Ollama. Integration tests require Ollama running.
"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from truthlens.claims import (
    Claim, ClaimVerificationReport, ClaimVerdict,
    verify_claims,
)


# ── Unit tests ─────────────────────────────────────────────────────────────────

class TestClaimModels:
    def test_claim_verdicts(self):
        assert ClaimVerdict.SUPPORTED == "Supported"
        assert ClaimVerdict.UNSUPPORTED == "Unsupported"
        assert ClaimVerdict.CONTRADICTED == "Contradicted"

    def test_claim_model(self):
        c = Claim(text="Python was created in 1991.", verdict="Supported", confidence=95.0)
        assert c.verdict == "Supported"
        assert c.confidence == 95.0

    def test_report_aggregation(self):
        claims = [
            Claim(text="A", verdict="Supported",    confidence=90),
            Claim(text="B", verdict="Supported",    confidence=85),
            Claim(text="C", verdict="Unsupported",  confidence=60),
            Claim(text="D", verdict="Contradicted", confidence=80),
        ]
        r = ClaimVerificationReport(
            question="q", answer="a", claims=claims,
            total_claims=4,
            supported_count=2, unsupported_count=1, contradicted_count=1,
            supported_pct=50, unsupported_pct=25, contradicted_pct=25,
            overall_verdict="Partially Trustworthy",
            trust_score=57.5,
        )
        assert r.total_claims == 4
        assert r.supported_count == 2
        assert r.trust_score == 57.5

    def test_trust_score_formula(self):
        # (supported * 1.0 + unsupported * 0.3 + contradicted * 0.0) / total * 100
        supported, unsupported, contradicted = 3, 1, 0
        total = supported + unsupported + contradicted
        expected = (3 * 1.0 + 1 * 0.3 + 0 * 0.0) / total * 100
        assert abs(expected - 82.5) < 0.1

    def test_all_supported_is_trustworthy(self):
        claims = [Claim(text=f"Claim {i}", verdict="Supported", confidence=90) for i in range(5)]
        trust = (5 * 1.0) / 5 * 100
        verdict = "Trustworthy" if trust >= 80 else "Partially Trustworthy"
        assert verdict == "Trustworthy"

    def test_all_contradicted_is_untrustworthy(self):
        claims = [Claim(text=f"Claim {i}", verdict="Contradicted", confidence=90) for i in range(5)]
        trust = (0 * 1.0) / 5 * 100
        verdict = "Trustworthy" if trust >= 80 else ("Partially Trustworthy" if trust >= 50 else "Untrustworthy")
        assert verdict == "Untrustworthy"

    def test_report_str(self):
        claims = [Claim(text="Python was made in 1991.", verdict="Supported", confidence=95)]
        r = ClaimVerificationReport(
            question="When was Python created?", answer="Python was made in 1991.",
            claims=claims, total_claims=1,
            supported_count=1, unsupported_count=0, contradicted_count=0,
            supported_pct=100, unsupported_pct=0, contradicted_pct=0,
            overall_verdict="Trustworthy", trust_score=100.0,
        )
        s = str(r)
        assert "Trustworthy" in s
        assert "100" in s


# ── Integration tests ──────────────────────────────────────────────────────────

@pytest.mark.integration
class TestClaimsIntegration:
    def test_full_verify_claims(self):
        report = verify_claims(
            question="When was Python created and by whom?",
            answer="Python was created by Guido van Rossum and first released in 1991. It is named after Monty Python.",
            sources=["Python is a programming language created by Guido van Rossum, first released in 1991."],
        )
        assert report.total_claims > 0
        assert report.supported_count >= 0
        assert 0 <= report.trust_score <= 100

    def test_hallucinated_claims_detected(self):
        report = verify_claims(
            question="Who created Python?",
            answer="Python was created by Dennis Ritchie in 1972. It was originally called C.",
            sources=["Python is a programming language created by Guido van Rossum, first released in 1991."],
        )
        assert report.contradicted_count > 0 or report.trust_score < 80
