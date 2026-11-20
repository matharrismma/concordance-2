"""The domestic shelf — the guards that make this seed trustworthy.

Three failures are possible here and each gets a test, because each has already happened somewhere
in this keeping:

  1. THE GATE THAT NEVER FIRES. The seed refuses to write if a card body carries a treatment term
     from Buchan (1791) or a polemical one from Cobbett (1833). A gate that has never been shown to
     fire is not a gate — the exact-title boost sat at 9.0x for weeks while firing once in 76,010
     candidates. So the denylists are tested by feeding them something that MUST be caught.
  2. THE FILE NOBODY READS. `corpus._EXTRA_CARD_SOURCES` is an explicit allowlist. A sibling JSONL
     that is not in it is invisible no matter how good the cards are.
  3. THE SHELF NO FACE READS. `foods` is a dead shelf name today precisely because the food seed
     writes `agriculture` while `faces.py` asks for `foods`. A card on an unread shelf cannot be
     reached, so every shelf this seed writes is checked against the faces' own shelf sets.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _seed():
    """Import tools/card_domestic.py as a module (it is a script, not a package member)."""
    path = ROOT / "tools" / "card_domestic.py"
    spec = importlib.util.spec_from_file_location("card_domestic", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["card_domestic"] = mod
    spec.loader.exec_module(mod)
    return mod


def _built(mod):
    """The cards the seed WOULD write, without writing them."""
    cards = []
    for slug, shelf, box, title, src, keywords, body in mod.CARDS:
        cards.append({"id": f"card_domestic_{slug}", "shelf": shelf, "box": box, "title": title,
                      "body": f"{body}  — {src}.", "generated": False,
                      "connections": [{"to_card_id": "x", "relationship": "member_of"}]})
    return cards


# ── 1. the gates fire ──────────────────────────────────────────────────────────────────────
def test_the_hazard_gate_catches_a_treatment_passage():
    """Buchan on treatment can kill a reader. If this passage got through, the gate is decorative."""
    mod = _seed()
    smuggled = [{"id": "card_domestic_smuggled", "shelf": "sanitation", "body":
                 "Let the patient be bled freely, and give ten grains of calomel at bed-time.",
                 "generated": False,
                 "connections": [{"to_card_id": "x", "relationship": "member_of"}]}]
    faults = mod._check(smuggled)
    assert faults, "the hazard denylist did not fire on bleeding and calomel"
    assert any("HAZARD" in f for f in faults)


def test_the_prejudice_gate_catches_a_polemical_passage():
    mod = _seed()
    smuggled = [{"id": "card_domestic_smuggled", "shelf": "foods", "body":
                 "whose mode of living is but one remove from that of the pig too",
                 "generated": False,
                 "connections": [{"to_card_id": "x", "relationship": "member_of"}]}]
    faults = mod._check(smuggled)
    assert faults, "the prejudice denylist did not fire"
    assert any("PREJUDICE" in f for f in faults)


def test_the_gate_catches_an_orphan_and_a_generated_card():
    mod = _seed()
    faults = mod._check([{"id": "card_domestic_orphan", "shelf": "foods", "body": "clean text",
                          "generated": True, "connections": []}])
    assert any("orphan" in f for f in faults)
    assert any("generated" in f for f in faults)


# ── 2. the real cards pass their own gates ─────────────────────────────────────────────────
def test_every_real_card_passes_both_denylists():
    mod = _seed()
    assert not mod._check(_built(mod))


def test_the_denylists_are_not_empty():
    """An empty tuple would make every test above pass for the wrong reason."""
    mod = _seed()
    assert len(mod.HAZARD) >= 10
    assert len(mod.PREJUDICE) >= 10


def test_every_card_is_attributed_to_a_public_domain_edition():
    mod = _seed()
    for c in _built(mod):
        assert "public domain" in c["body"], f"{c['id']} carries no public-domain attribution"
        assert "Project Gutenberg" in c["body"], f"{c['id']} names no source edition"


# ── 3. the shelf and the file are reachable ────────────────────────────────────────────────
def test_the_seeds_file_is_registered_with_the_corpus():
    from concordance import corpus
    assert "domestic_cards.jsonl" in corpus.EXTRA_CARD_SOURCES, (
        "the shelf is invisible: a sibling JSONL not in EXTRA_CARD_SOURCES is never loaded")


def test_every_shelf_this_seed_writes_is_a_shelf_some_face_reads():
    """The lesson of `foods`: the food seed writes `agriculture` while three faces ask for `foods`,
    so that shelf reads zero. A shelf no face reads cannot be reached by a question."""
    from concordance import faces
    mod = _seed()
    read: set[str] = set()
    for face in faces._FACES.values():
        read |= set((face or {}).get("shelves") or ())
    assert read, "could not read the faces' shelf sets"
    written = {shelf for _, shelf, *_ in mod.CARDS}
    unreachable = written - read
    assert not unreachable, f"these shelves no face reads: {sorted(unreachable)}"


@pytest.mark.parametrize("shelf", ["sanitation", "foods"])
def test_both_shelves_actually_receive_cards(shelf):
    mod = _seed()
    assert sum(1 for _, s, *_ in mod.CARDS if s == shelf) >= 4
