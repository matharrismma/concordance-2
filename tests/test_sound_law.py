"""SOUND LAWS + THE INDO-EUROPEAN FLOOR (Matt, 2026-10-09: "How do we use this for linguistics?" - "build it"). The
sound-law verifier certifies a regular correspondence on cited cognate pairs with 0 false positives; the IE family is
a floor on the one map where cognates are the confluences. Pinned: Grimm's law confirms on real cognates; a non-change
'law' errors; a non-cognate pair is caught; the IE floor's parts are the branches and its confluences are the cognate
sets; the seed validates and merges idempotently."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="nh-sl-")
os.environ.setdefault("CONCORDANCE_DATA_DIR", TMP)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import seed_indo_european as IE  # noqa: E402
from concordance import chains, corpus  # noqa: E402
from concordance.verifiers import sound_law as SL  # noqa: E402


def _v(spec):
    return SL.verify_sound_law(spec)


def test_grimms_law_confirms_on_cited_cognates():
    r = _v({"pairs": [["pater", "father"], ["piscis", "fish"], ["pes", "foot"], ["plenus", "full"], ["pellis", "fell"]],
            "source_onset": "p", "target_onset": "f", "law": "Grimm p->f"})
    assert r.status == "CONFIRMED" and r.data["holds"] == 5 and r.data["exceptions"] == []
    r = _v({"pairs": [["cornu", "horn"], ["canis", "hound"], ["centum", "hundred"], ["caput", "head"], ["cor", "heart"]],
            "source_onset": "c", "target_onset": "h"})
    assert r.status == "CONFIRMED" and r.data["holds"] == 5


def test_zero_false_positives_on_sound_laws():
    # a non-cognate (or wrong) pair breaks the regularity -> MISMATCH, never a false CONFIRMED
    r = _v({"pairs": [["pater", "father"], ["mater", "mother"]], "source_onset": "p", "target_onset": "f"})
    assert r.status == "MISMATCH" and r.data["holds"] == 1 and len(r.data["exceptions"]) == 1
    # a 'law' that is not a change is an error, not a vacuous confirm
    assert _v({"pairs": [["pater", "father"]], "source_onset": "p", "target_onset": "p"}).status == "ERROR"
    # no artifact -> honest gap
    assert SL.run({})[0].status == "NOT_APPLICABLE"


def test_it_routes_through_verify_derivation():
    from concordance.derivation import verify_derivation as V
    r = V([{"id": "s", "domain": "sound_law", "spec": {"SOUNDLAW_VERIFY": {
        "pairs": [["tres", "three"], ["tu", "thou"], ["tenuis", "thin"]], "source_onset": "t", "target_onset": "th"}}}])
    assert r["verdict"] == "HOLDS"


def _graph():
    cards = {c["id"]: json.loads(json.dumps(c)) for c in IE.CARDS}
    cards.setdefault("card_k_floor_of_discovery", {"id": "card_k_floor_of_discovery", "title": "Floor", "connections": []})
    ov = Path(TMP) / "o.jsonl"
    ov.write_text("\n".join(json.dumps(e) for e in IE.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, ov)
    return cards


def test_the_indo_european_floor_has_branches_as_trees_and_cognates_as_confluences():
    assert IE._validate() == [] and "card_floor_indo_european" in chains.FLOORS
    g = _graph()
    m = chains.floor_map("card_floor_indo_european", get_card=g.get)
    assert {p["id"] for p in m["parts"]} == {IE._bid(s) for s, _, _ in IE.BRANCHES}
    conf_at = {c["at"] for c in m["confluences"]}
    assert IE._cid("father") in conf_at                    # Germanic and Italic meet at 'father'
    merged = {x["id"] for x in m["merges"]}
    assert {IE._cid("father"), IE._cid("hundred"), IE._cid("three")} <= merged
    # 'father' connects the branches that carry it
    pair = next(c for c in m["confluences"] if c["at"] == IE._cid("father"))
    assert pair["a"].startswith("card_ie_branch_") and pair["b"].startswith("card_ie_branch_")


def test_the_seed_merges_idempotently(monkeypatch):
    d = Path(tempfile.mkdtemp(prefix="nh-ie-seed-"))
    monkeypatch.setattr(IE, "DATA", d)
    monkeypatch.setattr(sys, "argv", ["seed"])
    assert IE.main() == 0
    before = (d / "chain_cards.jsonl").read_bytes()
    assert IE.main() == 0 and (d / "chain_cards.jsonl").read_bytes() == before
    ids = {json.loads(l)["id"] for l in before.decode().splitlines() if l.strip()}
    assert IE.FLOOR in ids and IE._cid("father") in ids
