"""Unit-pin the manufacturing VERIFIER (A2, 2026-10-06; distinct from test_manufacture.py which pins the
Conductor door). Six Sigma DPMO 233 ~ 5.0 sigma; RSS tolerance stack sqrt(0.1^2+0.2^2+0.2^2)=0.3.
Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import manufacturing as MF


def test_sigma_level():
    assert MF.verify_sigma_level({"dpmo": 233, "claimed_sigma": 5.0}).status == "CONFIRMED"
    assert MF.verify_sigma_level({"dpmo": 233, "claimed_sigma": 3.0}).status == "MISMATCH"
    assert MF.verify_sigma_level({}).status == "NOT_APPLICABLE"


def test_tolerance_stack_rss():
    assert MF.verify_tolerance_stack_rss({"tolerances": [0.1, 0.2, 0.2], "claimed_rss": 0.3}).status == "CONFIRMED"
    assert MF.verify_tolerance_stack_rss({"tolerances": [0.1, 0.2, 0.2], "claimed_rss": 0.5}).status == "MISMATCH"
