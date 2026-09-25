"""Composition — the auditor chains claims the author stated (2026-09-25).

`compose_uses` sets a `uses` edge only when the prose explicitly chains two claims: a connective
("so"/"therefore"/…) between them AND a shared number. The moat then gates the link — a conclusion
resting on a false premise no longer stands on its own, even when its own arithmetic checks out.
Nothing is invented; no connective or no shared number means no edge, and a miss stays a miss.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance.audit import extract, compose_uses, audit, _spec_numbers  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402

CFG = EngineConfig(skip_schema_validation=True)


def _by_extractor(steps, name):
    return next(s for s in steps if s["extractor"] == name)


def test_spec_numbers_reads_both_shapes():
    # {WRAPPER: {...}} shape (values) and {mode, params} shape (numbers inside expr strings)
    assert 24.0 in _spec_numbers({"GEOM_VERIFY": {"rect_length": 4, "rect_width": 6,
                                                  "claimed_rect_area": 24}})
    assert {24.0, 2.0, 48.0} <= _spec_numbers({"mode": "equality",
                                               "params": {"expr_a": "24.0*2.0", "expr_b": "48.0"}})
    # a boolean is not a number
    assert _spec_numbers({"GEOM_VERIFY": {"claimed_valid_triangle": True}}) == set()


def test_chain_sets_a_uses_edge():
    text = "A rectangle 4 by 6 has area 24, so 24 x 2 = 48."
    steps = extract(text)
    compose_uses(steps, text)
    prod = _by_extractor(steps, "product")
    rect = _by_extractor(steps, "rectangle")
    assert rect["id"] in prod.get("uses", []), [s.get("uses") for s in steps]


def test_chain_confirms_end_to_end():
    res = audit("A rectangle 4 by 6 has area 24, so 24 x 2 = 48.", CFG, seal=False)
    assert res["verdict"] == "HOLDS"
    prod = next(r for r in res["results"] if r["extractor"] == "product")
    assert prod.get("uses")            # the edge surfaced in the report


def test_false_premise_stops_the_conclusion():
    # 4x6 = 24, so the "area 25" premise is FALSE. The arithmetic 25x2=50 is true IN ISOLATION,
    # but it rests on the false premise, so the chained derivation does not let it stand alone.
    res = audit("A rectangle 4 by 6 has area 25, so 25 x 2 = 50.", CFG, seal=False)
    assert res["verdict"] == "BROKEN"
    rect = next(r for r in res["results"] if r["extractor"] == "rectangle")
    prod = next(r for r in res["results"] if r["extractor"] == "product")
    assert rect["status"] == "MISMATCH"
    assert prod["status"] == "CONFIRMED"                 # true in isolation
    assert prod.get("builds_on_unconfirmed")             # …but it does not stand — rests on the break


def test_no_connective_no_edge():
    """No "so"/"therefore" between them → the claims are independent, no edge (a miss stays a miss)."""
    text = "A rectangle 4 by 6 has area 24. Also, 24 x 2 = 48."
    steps = extract(text)
    compose_uses(steps, text)
    assert not _by_extractor(steps, "product").get("uses")


def test_no_shared_number_no_edge():
    """Connective present, but the second claim reuses none of the first's numbers → no dependency."""
    text = "A rectangle 4 by 6 has area 24, so 3 x 5 = 15."
    steps = extract(text)
    compose_uses(steps, text)
    assert not _by_extractor(steps, "product").get("uses")


def test_single_claim_never_self_links():
    steps = extract("A rectangle 4 by 6 has area 24.")
    compose_uses(steps, "A rectangle 4 by 6 has area 24.")
    assert all(not s.get("uses") for s in steps)


if __name__ == "__main__":
    import pytest
    raise SystemExit(int(pytest.main([__file__, "-q"])))
