"""Conductor M1 — the classifier.

Proves: nine-type routing on clear cases, CRISIS-first (a cry for help is never a quote), CLARIFY
below 0.7, and the benchmark harness at 100% on a SEED set.

The SEED below is SYNTHETIC placeholder data — clearly-phrased, one-per-type. It exercises the rules
and the harness. It is NOT the ship gate: SOP-02 requires 50 of Matt's REAL work orders, in the
shop's own words (disguised cases marked), labeled by Matt and no one else. The classifier ships at
100% on THAT set, not this one.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from conductor.classify import classify, run_benchmark, is_crisis, TYPES, CLARIFY_THRESHOLD  # noqa: E402

SEED = [
    {"text": "Can you quote 200 flanges?", "primary": "QUOTE"},
    {"text": "Need a bid on this bracket, how much?", "primary": "QUOTE"},
    {"text": "The end mill is worn, need a new cutter for job 12", "primary": "TOOLING"},
    {"text": "Check tool life on the reamer before we run it", "primary": "TOOLING"},
    {"text": "What's the lead time on 50 parts?", "primary": "SCHEDULE"},
    {"text": "Can you schedule this for next week, due date is Friday", "primary": "SCHEDULE"},
    {"text": "First article inspection on the housing", "primary": "QUALITY"},
    {"text": "This part is out of spec, needs rework", "primary": "QUALITY"},
    {"text": "Order material — 6061 bar stock for the job", "primary": "MATERIAL"},
    {"text": "Need the mill cert for the 4140", "primary": "MATERIAL"},
    {"text": "Preventive maintenance on the lathe next week", "primary": "MAINTENANCE"},
    {"text": "The mill is down, breakdown on machine 2", "primary": "MAINTENANCE"},
    {"text": "What's the setup sheet for this fixture?", "primary": "PROCESS"},
    {"text": "Program the part — speeds and feeds question", "primary": "PROCESS"},
    {"text": "What did we quote last time for these brackets?", "primary": "HISTORICAL"},
    {"text": "Pull the previous job — we ran this before", "primary": "HISTORICAL"},
    {"text": "Someone is hurt in the back, call 911", "primary": "CRISIS"},
]


def test_seed_benchmark_is_100_percent():
    res = run_benchmark(SEED)
    assert res["accuracy"] == 1.0, res["misses"]


def test_every_type_appears_in_the_seed():
    covered = {c["primary"] for c in SEED}
    assert covered == set(TYPES), set(TYPES) - covered


def test_crisis_is_first_even_disguised():
    # a casual message hiding a cry for help must route CRISIS, never SCHEDULE/QUOTE
    c = classify("hey when you get a sec, someone got hurt bad on the saw")
    assert c.crisis and c.work_type == "CRISIS"


def test_crisis_beats_a_quote_shell():
    c = classify("quick quote question — actually wait, he's bleeding, call 911")
    assert c.work_type == "CRISIS"


def test_unknown_work_clarifies():
    c = classify("hey can you take a look at this thing when you get a chance")
    assert c.clarify and c.work_type == "CLARIFY"
    assert c.confidence < CLARIFY_THRESHOLD


def test_confident_type_is_not_clarify():
    c = classify("Can you quote 200 flanges?")
    assert c.work_type == "QUOTE" and not c.clarify and c.confidence >= CLARIFY_THRESHOLD


def test_is_crisis_helper():
    assert is_crisis("someone is hurt, call 911") is True
    assert is_crisis("need a quote on 50 brackets") is False


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
