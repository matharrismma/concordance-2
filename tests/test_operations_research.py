"""Unit-pin the operations_research verifier (A2, 2026-10-06). 0/1 knapsack: items (w2,v3) and (w3,v4),
capacity 5 -> optimal value 7. Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import operations_research as OR


def test_knapsack_01():
    items = [{"weight": 2, "value": 3}, {"weight": 3, "value": 4}]
    assert OR.verify_knapsack_01({"items": items, "capacity": 5, "claimed_optimal_value": 7}).status == "CONFIRMED"
    assert OR.verify_knapsack_01({"items": items, "capacity": 5, "claimed_optimal_value": 10}).status == "MISMATCH"
    assert OR.verify_knapsack_01({}).status == "NOT_APPLICABLE"
