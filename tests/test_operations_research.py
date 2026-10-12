"""Unit-pin the operations_research verifier (A2, 2026-10-06). 0/1 knapsack: items (w2,v3) and (w3,v4),
capacity 5 -> optimal value 7. Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import operations_research as OR


def test_knapsack_01():
    items = [{"weight": 2, "value": 3}, {"weight": 3, "value": 4}]
    assert OR.verify_knapsack_01({"items": items, "capacity": 5, "claimed_optimal_value": 7}).status == "CONFIRMED"
    assert OR.verify_knapsack_01({"items": items, "capacity": 5, "claimed_optimal_value": 10}).status == "MISMATCH"
    assert OR.verify_knapsack_01({}).status == "NOT_APPLICABLE"


def test_critical_path_valid_dag():
    """A real DAG must compute its makespan, not be mistaken for a cycle (regression: the
    topo-sort's successor adjacency list was never populated, so every dependent task was
    unreachable and any chain read as a cycle). Chain A->B->D with durations 3,5,4 -> 12."""
    chain = [{"id": "A", "duration": 3, "depends_on": []},
             {"id": "B", "duration": 5, "depends_on": ["A"]},
             {"id": "D", "duration": 4, "depends_on": ["B"]}]
    res = OR.verify_critical_path({"tasks": chain, "claimed_makespan": 12})
    assert res.status == "CONFIRMED", res
    assert res.data["actual_makespan"] == 12.0
    assert res.data["topological_order"] == ["A", "B", "D"]
    # Wrong claim on the same DAG is a MISMATCH, not an ERROR.
    assert OR.verify_critical_path({"tasks": chain, "claimed_makespan": 99}).status == "MISMATCH"


def test_critical_path_diamond():
    """Branching + join (A->B, A->C, B&D->D) exercises multiple predecessors:
    A(3)->B(5)->D(4)=12 is the critical path; the C(2) branch is not."""
    tasks = [{"id": "A", "duration": 3, "depends_on": []},
             {"id": "B", "duration": 5, "depends_on": ["A"]},
             {"id": "C", "duration": 2, "depends_on": ["A"]},
             {"id": "D", "duration": 4, "depends_on": ["B", "C"]}]
    assert OR.verify_critical_path({"tasks": tasks, "claimed_makespan": 12}).status == "CONFIRMED"


def test_critical_path_true_cycle_errors():
    """A genuine cycle A<->B must still be reported as an ERROR (unverifiable)."""
    cycle = [{"id": "A", "duration": 3, "depends_on": ["B"]},
             {"id": "B", "duration": 5, "depends_on": ["A"]}]
    res = OR.verify_critical_path({"tasks": cycle, "claimed_makespan": 8})
    assert res.status == "ERROR"
    assert "cycle" in res.detail
