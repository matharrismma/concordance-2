"""Chapter:verse re-citer — cite-fair by construction, proven on a synthetic corpus.

tools/recite.py restores GENUINE 'cites' edges: only a card whose own text carries a
"Book chapter:verse" reference gets one. This test locks that gate hermetically:
  * a card that merely NAMES a book (no ch:v) gains NO cites edge — and its demoted
    'references' co-mention edge is NOT upgraded;
  * a card with a real ref gets its existing edge UPGRADED in place (id preserved) with the
    exact ref(s) recorded;
  * a ref-bearing card with no prior edge gets a NEW deterministic-id cites edge
    (same inputs -> same id, so re-runs never duplicate);
  * the whole run is idempotent (second run changes nothing).

Runnable with pytest OR `python tests/test_recite.py` (sovereign — no pytest needed).
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

_spec = importlib.util.spec_from_file_location("recite", ROOT / "tools" / "recite.py")
recite = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(recite)


def _note(cid, title, body):
    return {"id": cid, "kind": "note", "title": title, "body": body,
            "visibility": "public", "lifecycle_stage": "public"}


def _conn(cid, left, right, kind):
    return {"id": cid, "kind": "connection", "title": f"{left} references John",
            "body": "co-mention", "visibility": "public", "lifecycle_stage": "public",
            "source": {"label": "Auto-detected reference"}, "bands": ["references"],
            "extra": {"left_card_id": left, "right_card_id": right, "relationship_kind": kind}}


def _fixture(tmp: Path) -> Path:
    cards = [
        _note("card_john", "John", "The gospel."),                          # the book target
        _note("card_ref", "Easton: Erastus", "See Acts 19:22 and John 3:16."),  # genuine refs
        _note("card_mention", "Easton: Jude", "Not to be confused with John."),  # bare mention
        _note("card_acts", "Acts", "The book of Acts."),
        _conn("card_c_up", "card_ref", "card_john", "references"),      # should UPGRADE
        _conn("card_c_stay", "card_mention", "card_john", "references"),  # must NOT upgrade
    ]
    p = tmp / "cards.jsonl"
    p.write_text("\n".join(json.dumps(c) for c in cards) + "\n", encoding="utf-8")
    return p


def _load(p: Path):
    return {c["id"]: c for c in (json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip())}


def test_recite_gates_upgrades_and_creates():
    with tempfile.TemporaryDirectory() as td:
        p = _fixture(Path(td))
        assert recite.main([str(p)]) == 0
        cards = _load(p)

        # UPGRADED in place: id preserved, kind flipped, exact ref recorded
        up = cards["card_c_up"]["extra"]
        assert up["relationship_kind"] == "cites"
        assert "John 3:16" in up["refs"] and up["ref"].startswith("John")

        # the bare co-mention must NOT be upgraded — no ch:v ref, no cites
        assert cards["card_c_stay"]["extra"]["relationship_kind"] == "references"

        # CREATED: card_ref cites Acts (no prior edge) with a deterministic id
        eid = recite._edge_id("card_ref", "card_acts")
        assert eid in cards, "expected a new cites edge for the Acts 19:22 ref"
        ex = cards[eid]["extra"]
        assert ex["relationship_kind"] == "cites" and ex["refs"] == ["Acts 19:22"]

        # the gate, globally: EVERY cites edge points from a card whose text carries a ref
        for c in cards.values():
            if c.get("kind") == "connection" and c["extra"].get("relationship_kind") == "cites":
                left = cards[c["extra"]["left_card_id"]]
                assert recite.REF_RE.search(f"{left.get('title','')} {left.get('body','')}"), \
                    f"cites edge {c['id']} without a genuine ch:v ref in the source card"

        # the mention-only card gained nothing new
        for c in cards.values():
            if c.get("kind") == "connection" and c["extra"].get("left_card_id") == "card_mention":
                assert c["extra"]["relationship_kind"] == "references"


def test_recite_is_idempotent():
    with tempfile.TemporaryDirectory() as td:
        p = _fixture(Path(td))
        recite.main([str(p)])
        first = p.read_text(encoding="utf-8")
        recite.main([str(p)])  # second run: "(no change …)" path — nothing rewritten
        assert p.read_text(encoding="utf-8") == first, "second run must change nothing"


def test_edge_id_deterministic():
    a = recite._edge_id("card_x", "card_y")
    assert a == recite._edge_id("card_x", "card_y")
    assert a != recite._edge_id("card_y", "card_x")
    assert a.startswith("card_c_") and len(a) == len("card_c_") + 12


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} recite tests passed — no cites without a chapter:verse; idempotent; deterministic.")
