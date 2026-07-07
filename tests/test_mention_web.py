"""Mention web — curated, guarded, honest. Proven on a synthetic corpus.

tools/mention_web.py links a card to an Easton person/place entry ONLY when the name is
(1) classified person|place by Easton's own category field, (2) not a Bible book name,
(3) found MID-SENTENCE in the card's text, and (4) not already connected. This test locks
all four gates hermetically, plus idempotence and deterministic ids.

Runnable with pytest OR `python tests/test_mention_web.py` (sovereign — no pytest needed).
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

_spec = importlib.util.spec_from_file_location("mention_web", ROOT / "tools" / "mention_web.py")
mw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mw)


def _note(cid, title, body):
    return {"id": cid, "kind": "note", "title": title, "body": body,
            "visibility": "public", "lifecycle_stage": "public"}


def _fixture(tmp: Path):
    easton = tmp / "entries.jsonl"
    easton.write_text("\n".join(json.dumps(e) for e in [
        {"name": "Erastus", "category": "person"},
        {"name": "Damascus", "category": "place"},
        {"name": "On", "category": "place"},
        {"name": "Baptism", "category": "concept"},   # concept: must NEVER link
        {"name": "John", "category": "person"},       # book name: must NEVER link here
    ]) + "\n", encoding="utf-8")

    cards = [
        _note("card_erastus", "Easton: Erastus", "A Corinthian."),
        _note("card_damascus", "Easton: Damascus", "A city of Syria."),
        _note("card_on", "Easton: On", "A city of Egypt."),
        _note("card_baptism", "Easton: Baptism", "An ordinance."),
        _note("card_john_e", "Easton: John", "The apostle."),
        # mid-sentence mention of Erastus + Damascus -> two edges
        _note("card_a", "Classic A", "He sent Erastus toward Damascus with a letter."),
        # 'On' ONLY at sentence starts -> no edge; 'Baptism' mid-sentence -> concept, no edge;
        # 'John' mid-sentence -> book name, no edge
        _note("card_b", "Classic B", "On the first day he taught. On the second, Baptism was "
                                     "discussed, and John wrote it down."),
        # mid-sentence 'On' (the city) -> edge
        _note("card_c", "Classic C", "They came to the city of On before dawn."),
        # already connected to Erastus -> skip (no double edge)
        _note("card_d", "Classic D", "He greeted Erastus warmly."),
        {"id": "card_c_existing", "kind": "connection", "title": "Classic D cites Acts",
         "visibility": "public", "lifecycle_stage": "public",
         "extra": {"left_card_id": "card_d", "right_card_id": "card_erastus",
                   "relationship_kind": "cites"}},
    ]
    cj = tmp / "cards.jsonl"
    cj.write_text("\n".join(json.dumps(c) for c in cards) + "\n", encoding="utf-8")
    return cj, easton


def _load(p: Path):
    return {c["id"]: c for c in (json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip())}


def _mentions(cards):
    return [c for c in cards.values()
            if c.get("kind") == "connection" and (c.get("extra") or {}).get("mention")]


def test_gates_hold():
    with tempfile.TemporaryDirectory() as td:
        cj, easton = _fixture(Path(td))
        assert mw.main([str(cj), "--easton", str(easton)]) == 0
        cards = _load(cj)
        edges = {(e["extra"]["left_card_id"], e["extra"]["right_card_id"]): e for e in _mentions(cards)}

        # genuine mid-sentence mentions link
        assert ("card_a", "card_erastus") in edges
        assert ("card_a", "card_damascus") in edges
        # mid-sentence 'On' (the city) links; sentence-start 'On' does not
        assert ("card_c", "card_on") in edges
        assert ("card_b", "card_on") not in edges
        # concept + book-name subjects never link
        assert not any(r == "card_baptism" for (_l, r) in edges)
        assert not any(r == "card_john_e" for (_l, r) in edges)
        # an existing pair is never double-edged
        assert ("card_d", "card_erastus") not in edges

        # every mention edge is honest: kind 'references', name + category recorded
        for e in _mentions(cards):
            ex = e["extra"]
            assert ex["relationship_kind"] == "references"
            assert ex["mention"] and ex["easton_category"] in ("person", "place")
            left = cards[ex["left_card_id"]]
            assert ex["mention"] in f"{left.get('title','')} {left.get('body','')}"


def test_idempotent_and_deterministic():
    with tempfile.TemporaryDirectory() as td:
        cj, easton = _fixture(Path(td))
        mw.main([str(cj), "--easton", str(easton)])
        first = cj.read_text(encoding="utf-8")
        mw.main([str(cj), "--easton", str(easton)])   # second run: nothing to add
        assert cj.read_text(encoding="utf-8") == first
        a = mw._edge_id("x", "y")
        assert a == mw._edge_id("x", "y") and a != mw._edge_id("y", "x")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} mention-web tests passed — curated, guarded, idempotent.")
