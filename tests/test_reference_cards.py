"""The deep verifier reference data becomes git-tracked cards, and the corpus loads them.

Matt: "We should have an extremely comprehensive depth of cards in each area, and we have done
the work. They just aren't getting connected. The content should be on the github at the least."

Guards: the backfill reveals the real reference data (not invented) with deterministic ids
(pay once, stable across runs), and `corpus.load_cards` merges reference_cards.jsonl as a source
so an element or a constant is a card in the same keeping as Scripture.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-refcard-")

import backfill_reference_cards as bf  # noqa: E402


def test_every_element_becomes_a_faithful_card():
    cards = bf._elements()
    assert len(cards) == 118                       # the whole periodic table
    h = cards[0]
    assert h["id"] == "card_ref_el_001" and h["kind"] == "reference"
    assert "Hydrogen" in h["title"] and "1 proton" in h["body"]
    assert h["shelf"] == "chemistry" and h["generated"] is False
    assert "H" in h["bands"]                        # searchable by symbol


def test_every_constant_becomes_a_faithful_card():
    cards = bf._constants()
    assert len(cards) >= 20
    by_id = {c["id"]: c for c in cards}
    c = by_id["card_ref_pc_speed_of_light"]
    assert "299792458" in c["title"] and c["shelf"] == "physics"
    assert c["source"]["authority_tier"] == "reference" and c["generated"] is False


def test_crops_and_nutrients_are_carded_faithfully():
    crops = {c["id"]: c for c in bf._crops()}
    tom = crops["card_ref_crop_tomato"]
    assert "solanaceae" in tom["body"] and "pH 6.0–6.8" in tom["body"]
    assert tom["shelf"] == "agriculture"
    nutr = {c["id"]: c for c in bf._nutrients()}
    fe = nutr["card_ref_rda_iron"]
    assert "27 mg/day" in fe["body"] and "pregnant" in fe["body"]  # a real DRI value
    assert fe["shelf"] == "nutrition" and fe["generated"] is False


def test_ids_are_deterministic_pay_once():
    def _all():
        return bf._elements() + bf._constants() + bf._crops() + bf._nutrients()
    a = {c["id"] for c in _all()}
    b = {c["id"] for c in _all()}
    assert a == b                                   # same content, same ids, every run
    assert len(a) == sum(len(fn()) for _, fn in bf.EMITTERS)   # no id collisions across emitters


def test_corpus_merges_reference_cards_as_a_source():
    """A reference card written beside cards.jsonl is loaded into the one keeping.

    Hermetic: we own CONCORDANCE_CARDS_JSONL for the call and restore it, so the suite's
    shared data-dir (SOP-11 — first import pins it) cannot bleed in."""
    d = Path(tempfile.mkdtemp(prefix="nh-refmerge-"))
    (d / "cards.jsonl").write_text(
        json.dumps({"id": "card_seed", "kind": "note", "title": "seed"}) + "\n", encoding="utf-8")
    (d / "reference_cards.jsonl").write_text(
        "\n".join(json.dumps(c) for c in bf._elements()[:3]) + "\n", encoding="utf-8")
    from concordance import corpus
    saved = os.environ.get("CONCORDANCE_CARDS_JSONL")
    os.environ["CONCORDANCE_CARDS_JSONL"] = str(d / "cards.jsonl")
    try:
        cards = corpus.load_cards()                 # path=None → merges the extra sources
    finally:
        if saved is None:
            os.environ.pop("CONCORDANCE_CARDS_JSONL", None)
        else:
            os.environ["CONCORDANCE_CARDS_JSONL"] = saved
    assert "card_seed" in cards                     # the primary source
    assert "card_ref_el_001" in cards               # AND the reference source, one graph
    assert cards["card_ref_el_001"]["kind"] == "reference"


def test_bridges_graft_the_two_trees_reciprocally():
    """A reference card and the Easton card of the same subject are linked BOTH ways at load,
    without mutating cards.jsonl — the science points to Scripture and Scripture to the science."""
    from concordance import corpus
    d = Path(tempfile.mkdtemp(prefix="nh-refbridge-"))
    gold_ref = {"id": "card_ref_el_079", "kind": "reference", "title": "Gold (Au) — element 79",
                "shelf": "chemistry", "subject": "gold"}
    (d / "cards.jsonl").write_text(
        json.dumps({"id": "card_easton_gold", "kind": "dictionary", "shelf": "dictionary",
                    "title": "Easton: Gold"}) + "\n", encoding="utf-8")
    (d / "reference_cards.jsonl").write_text(json.dumps(gold_ref) + "\n", encoding="utf-8")
    (d / "reference_bridges.jsonl").write_text(
        json.dumps({"a": "card_ref_el_079", "b": "card_easton_gold",
                    "relationship": "names_the_created_thing", "evidence": "Scripture names gold."})
        + "\n", encoding="utf-8")
    saved = os.environ.get("CONCORDANCE_CARDS_JSONL")
    os.environ["CONCORDANCE_CARDS_JSONL"] = str(d / "cards.jsonl")
    try:
        cards = corpus.load_cards()
    finally:
        if saved is None:
            os.environ.pop("CONCORDANCE_CARDS_JSONL", None)
        else:
            os.environ["CONCORDANCE_CARDS_JSONL"] = saved
    # the element card links to the Easton card...
    assert any(x["to_card_id"] == "card_easton_gold"
               for x in cards["card_ref_el_079"]["connections"])
    # ...and the Easton card links back to the element card (reciprocal, cards.jsonl untouched)
    assert any(x["to_card_id"] == "card_ref_el_079"
               for x in cards["card_easton_gold"]["connections"])


def test_bridge_compute_is_exact_subject_only_no_false_positives():
    from bridge_reference_to_scripture import compute
    refs = [{"id": "r1", "subject": "gold", "title": "Gold (Au) — element 79"},
            {"id": "r2", "subject": "argon", "title": "Argon (Ar) — element 18"}]
    base = [{"id": "e1", "shelf": "dictionary", "title": "Easton: Gold"},
            {"id": "e2", "shelf": "dictionary", "title": "Easton: No"},      # stopword, never a bridge
            {"id": "e3", "shelf": "classics", "title": "Gold"}]              # not a dictionary card
    edges = compute(refs, base)
    assert len(edges) == 1 and edges[0]["a"] == "r1" and edges[0]["b"] == "e1"  # only gold->Easton:Gold


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} reference-card tests passed — the deep work is carded, in git, in the graph.")
