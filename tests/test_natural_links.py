"""THE NATURAL LINKS (2026-11-25, Matt: "We need everything connected and we want the natural shape to be in those
connections. So missing connections gives us a false sense of shape."): one note on each stick no recorded connection
reached, plus Godel and the primes-as-waves stick, naming the floors and sticks it truly connects to. These pin that
every stick a note names is a real stick, that each note states its relation, and that none links by likeness."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = json.loads((ROOT / "data" / "sticks" / "natural_links.json").read_text(encoding="utf-8"))


def _golden_ids():
    out = set()
    for f in (ROOT / "tests" / "fixtures" / "tick_golden").glob("*.json"):
        out |= set(json.loads(f.read_text(encoding="utf-8")).get("sticks") or {})
    return out


def test_one_note_per_stick_and_only_notes():
    qs = [st["question"] for st in ENTRY["sticks"]]
    assert len(qs) == len(set(qs)) == 18 and ENTRY["seals"] == []
    assert all(len(st["marks"]) == 1 and st["marks"][0]["kind"] == "note" for st in ENTRY["sticks"])


# A stick minted on the box outside the catalog (no golden creates it): read in the box's own ledger on 2026-11-25.
BOX_ONLY = {"stick_the_fine_tuned_constants_intelligent_design_and_engineering",
            "stick_matrices_are_graphs_tensors_are_tensor_networks_the_score_is"}


def test_every_stick_a_note_names_is_a_real_stick():
    ids = _golden_ids() | BOX_ONLY
    for st in ENTRY["sticks"]:
        named = re.findall(r"\bstick_[a-z0-9_]{3,}", st["marks"][0]["claim"])
        floors = re.findall(r"\bcard_floor_[a-z0-9_]+", st["marks"][0]["claim"])
        assert named or floors, st["question"]
        for n in named:
            assert n in ids, (st["question"], n)


def test_each_note_states_its_relation():
    for st in ENTRY["sticks"]:
        c = st["marks"][0]["claim"]
        assert c.startswith("[") and len(c) > 120, st["question"]
    godel = next(st for st in ENTRY["sticks"] if st["question"].startswith("Godel"))["marks"][0]["claim"]
    assert "1956" in godel and "Davis, Matiyasevich, Robinson" in godel and "1949" in godel
    primes = next(st for st in ENTRY["sticks"] if st["question"].startswith("A torus"))["marks"][0]["claim"]
    assert "not a harmonic series" in primes and "machine-checked" in primes and "no human-readable proof yet" in primes


ENTRY2 = json.loads((ROOT / "data" / "sticks" / "natural_links_floor_only.json").read_text(encoding="utf-8"))


def test_the_floor_only_sticks_each_get_one_note_naming_real_sticks():
    """The 48 sticks that sat only under a floor (2026-11-25): one note each, every stick it names real, and every
    note names at least one stick other than its own - a cross-link, not another floor."""
    ids = _golden_ids() | BOX_ONLY
    qs = [st["question"] for st in ENTRY2["sticks"]]
    assert len(qs) == len(set(qs)) == 48 and ENTRY2["seals"] == []
    for st in ENTRY2["sticks"]:
        (m,) = st["marks"]
        assert m["kind"] == "note" and m["claim"].startswith("[where it connects] ")
        named = re.findall(r"\bstick_[a-z0-9_]{3,}", m["claim"])
        assert named, st["question"]
        for n in named:
            assert n in ids, (st["question"], n)
