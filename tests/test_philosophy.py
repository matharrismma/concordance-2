"""Unit-pin the philosophy verifier (A2, 2026-10-06). Consequentialism judges by outcomes; virtue ethics
does not. The catalog classification must match the claim. Missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import philosophy as PL


def test_ethical_framework():
    assert PL.verify_ethical_framework({"framework_name": "consequentialist",
                                        "claimed_focuses_on_outcomes": True}).status == "CONFIRMED"
    assert PL.verify_ethical_framework({"framework_name": "consequentialist",
                                        "claimed_focuses_on_outcomes": False}).status == "MISMATCH"
    assert PL.verify_ethical_framework({}).status == "NOT_APPLICABLE"
