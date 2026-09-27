"""BYOM — a user's model is a gated external worker: stripped in, never trusted raw, checked out.

Pins the Phase 4 contract (project_byom_bring_your_own_model_pays_to_train_us): the airlock fails
closed (PII leak → the model never runs); the model's output is TRUSTED only if our verifier holds,
REJECTED if it contradicts one, and an honest GAP when nothing is checkable; only non-rejected outcomes
are captured for public_review, never auto-published. All deps injected — no real model or corpus.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import byom  # noqa: E402


def _airlock_ok(text, operate, minimal=True):
    """A fake airlock that de-identifies to a fixed skeleton and RUNS operate on it (clean zone)."""
    skeleton = "SKELETON"
    return SimpleNamespace(ok=True, leaked=False, checked=skeleton, result=operate(skeleton))


def _airlock_leak(text, operate, minimal=True):
    """A fake airlock that QUARANTINES — operate must never run."""
    return SimpleNamespace(ok=False, leaked=True, checked=None, result=None)


def test_airlock_quarantine_never_runs_the_model():
    ran = {"called": False}
    def model_call(skel):
        ran["called"] = True
        return "should not happen"
    out = byom.run_byom("my SSN is 123-45-6789, compute x", model_call,
                        airlock_fn=_airlock_leak, discern_fn=lambda t: None, verify_fn=lambda s: {})
    assert out["ok"] is False and out["leaked"] is True
    assert ran["called"] is False, "the external model must NOT run when the airlock quarantines"


def test_model_output_verified_is_trusted_and_captured():
    claim = {"claim": {"domain": "mathematics", "spec": {"mode": "arithmetic", "params": {"expr": "2+2"}}}}
    out = byom.run_byom("is 2+2 four", lambda skel: "2+2=4", verifiers=["mathematics"],
                        airlock_fn=_airlock_ok,
                        discern_fn=lambda t: claim,
                        verify_fn=lambda steps: {"verdict": "HOLDS", "trail": [{"id": "s"}]})
    assert out["ok"] and out["trust"] == "verified"
    assert out["checked"] == "SKELETON"                      # seal binds to the clean skeleton
    assert out["capture"] and out["capture"]["status"] == "public_review"
    assert out["capture"]["generated"] is True               # filed for review, not published


def test_model_output_that_contradicts_a_verifier_is_rejected_and_not_captured():
    claim = {"claim": {"domain": "mathematics", "spec": {"mode": "arithmetic", "params": {"expr": "2+2"}}}}
    out = byom.run_byom("is 2+2 five", lambda skel: "2+2=5", verifiers=["mathematics"],
                        airlock_fn=_airlock_ok,
                        discern_fn=lambda t: claim,
                        verify_fn=lambda steps: {"verdict": "BROKEN", "trail": [{"id": "s"}]})
    assert out["trust"] == "rejected"
    assert out["capture"] is None, "a claim our verifier broke must not be captured as training truth"


def test_no_checkable_claim_is_an_honest_gap_still_captured():
    out = byom.run_byom("tell me about hope", lambda skel: "a reflection on hope", verifiers=["mathematics"],
                        airlock_fn=_airlock_ok,
                        discern_fn=lambda t: {"kind": "guidance", "claim": None},
                        verify_fn=lambda steps: (_ for _ in ()).throw(AssertionError("no steps → no verify")))
    assert out["verify"] is None and out["trust"] == "unverified"
    assert out["capture"] and out["capture"]["status"] == "public_review"


def test_our_engine_error_does_not_reject_the_model():
    """SYSTEM_ERROR is OUR failure, not their falsehood — the model is not rejected on our bug."""
    assert byom._trust({"verdict": "SYSTEM_ERROR"}) == "unverified"
    assert byom._trust({"verdict": "HOLDS"}) == "verified"
    assert byom._trust({"verdict": "BROKEN"}) == "rejected"
    assert byom._trust(None) == "unverified"


def test_byom_ssrf_guard_blocks_internal_targets():
    """A user's model lives on a PUBLIC endpoint — never localhost/private/link-local/reserved."""
    for bad in ["http://127.0.0.1/v1", "http://10.0.0.1/v1", "http://192.168.1.5/v1",
                "http://169.254.169.254/latest", "http://[::1]/v1", "ftp://example.com/v1", "not a url"]:
        try:
            byom._guard_url(bad)
            assert False, f"SSRF guard should have blocked {bad!r}"
        except ValueError:
            pass
    assert byom._guard_url("https://8.8.8.8/v1") == "https://8.8.8.8/v1"   # a public IP literal is fine


def test_openai_adapter_builds_a_callable_and_validates():
    mc = byom.openai_adapter({"base_url": "https://8.8.8.8/v1", "api_key": "k", "model": "gpt"})
    assert callable(mc)
    for bad in [{"base_url": "http://127.0.0.1", "api_key": "k", "model": "m"},   # SSRF
                {"base_url": "https://8.8.8.8", "api_key": "k", "model": ""}]:    # missing model
        try:
            byom.openai_adapter(bad)
            assert False, f"should reject {bad}"
        except ValueError:
            pass


if __name__ == "__main__":
    import pytest
    sys.exit(int(pytest.main([__file__, "-q"])))
