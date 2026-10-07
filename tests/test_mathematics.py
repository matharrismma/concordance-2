"""Unit-pin the mathematics verifier's numeric core (A2, 2026-10-06). The numeric evaluator the whole
engine seals through: 2+2 = 4. A wrong claim is caught; a missing field is NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import mathematics as MA


def test_numeric():
    assert MA.verify_numeric({"numeric_expr": "2+2", "claimed_value": 4}).status == "CONFIRMED"
    assert MA.verify_numeric({"numeric_expr": "2+2", "claimed_value": 5}).status == "MISMATCH"
    assert MA.verify_numeric({}).status == "NOT_APPLICABLE"


def test_numeric_with_functions():
    assert MA.verify_numeric({"numeric_expr": "sqrt(2)*sqrt(2)", "claimed_value": 2.0}).status == "CONFIRMED"
