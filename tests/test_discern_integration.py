"""Discern's deep mode against the real gate — the archetype: discern proposes, verify disposes.

Slow: the candidate gate runs the derivation moat. Kept apart from the instant discern seed suite. This
proves the whole point of the candidate engine — a wide field is proposed BLIND to the generator's
weight, and the gate eliminates to the true survivor, so a confident-but-wrong answer buys no favor.
"""
from concordance import candidates as cand
from concordance import discern
from concordance.config import EngineConfig


def test_the_gate_narrows_a_field_to_the_true_survivor_ignoring_weight():
    # discern PROPOSES the field; the false candidate carries the HIGHER weight.
    p = discern.field("what is 2 + 2", [{"raw_text": "2 + 2 = 4", "proposal_weight": 0.01},
                                        {"raw_text": "2 + 2 = 5", "proposal_weight": 0.99}])
    assert p["kind"] == "field" and p["confirms"] is False        # discern only proposed

    cand.narrow(p["cset"], EngineConfig())                        # the gate DISPOSES
    by_text = {c["raw_text"]: c for c in p["cset"]["candidates"]}
    assert by_text["2 + 2 = 4"]["verification_status"] == "pass"   # the true one survives
    assert by_text["2 + 2 = 5"]["verification_status"] == "reject" # the confident-but-wrong one falls
