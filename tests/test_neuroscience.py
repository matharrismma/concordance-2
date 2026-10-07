"""Unit-pin the neuroscience verifier (A2, 2026-10-06). Weber-Fechner: sensation S = k*ln(stimulus/ref)
(k=1, 100/10 -> ln(10) ~ 2.3026). Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import neuroscience as NE


def test_weber_fechner():
    assert NE.verify_weber_fechner({"stimulus": 100, "reference": 10, "weber_k": 1.0,
                                    "claimed_sensation": 2.3026}).status == "CONFIRMED"
    assert NE.verify_weber_fechner({"stimulus": 100, "reference": 10, "weber_k": 1.0,
                                    "claimed_sensation": 5.0}).status == "MISMATCH"
    assert NE.verify_weber_fechner({}).status == "NOT_APPLICABLE"
