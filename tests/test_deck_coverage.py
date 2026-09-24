"""The deck ↔ shelf coverage guard (tools/check_deck_coverage.py) — the durable §4 win.

The tool's live run needs the corpus; its DIFF is pure and is pinned here so the classification
logic (dead token / unrouted content / pending-unseeded / ops-excluded) can never regress. A live
run against the box (or the local corpus) is the e2e half — this is the CODE half.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

_spec = importlib.util.spec_from_file_location(
    "check_deck_coverage", ROOT / "tools" / "check_deck_coverage.py")
cov = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cov)


def test_coverage_classifies_every_case():
    by_shelf = {
        "physics": 24,        # produced + routed  -> fine
        "theories": 217,      # produced + routed  -> fine
        "newshelf": 7,        # produced, NOT routed, not ops -> UNROUTED (drift)
        "seals": 862,         # produced but OPS   -> excluded, not drift
        "spine": 65,          # produced but OPS   -> excluded
        "languages": 0,       # routed, not produced, PENDING -> pending (not dead)
    }
    deck_shelves = {"physics", "theories", "languages", "deadtoken"}
    rep = cov.coverage(by_shelf, deck_shelves)
    assert rep["unrouted_content_shelves"] == ["newshelf"]          # the one real gap
    assert rep["dead_deck_shelves"] == ["deadtoken"]                # routed but no card carries it
    assert rep["pending_deck_shelves"] == ["languages"]             # kept, awaiting data — not drift
    assert "seals" not in rep["unrouted_content_shelves"]           # ops shelves are excluded
    assert "spine" not in rep["unrouted_content_shelves"]


def test_clean_when_everything_is_routed():
    rep = cov.coverage({"physics": 24, "theories": 217}, {"physics", "theories"})
    assert rep["dead_deck_shelves"] == [] and rep["unrouted_content_shelves"] == []


def test_zero_count_shelf_is_not_counted_as_produced():
    # a shelf present in the map with 0 cards is NOT produced — routing it would be a dead token
    rep = cov.coverage({"empty": 0}, {"empty"})
    assert rep["dead_deck_shelves"] == ["empty"] and rep["unrouted_content_shelves"] == []
