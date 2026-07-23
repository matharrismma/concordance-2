"""Growth — the standing engine that improves the keeping without ever regressing it.

The load-bearing guard is 0-FP: the growth gate must NEVER propose a connection between two
cards that do not demonstrably share a scripture reference. Everything else (normalization,
rarity, idempotency, the ledger) serves that.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-growth-")

from concordance import growth  # noqa: E402


def _card(cid, ref="", bands=None, links=None, vis="public", shelf="codex", title=""):
    return {"id": cid, "title": title or cid, "shelf": shelf, "visibility": vis,
            "source": {"ref": ref}, "bands": bands or [],
            "connections": [{"to_card_id": t} for t in (links or [])]}


def test_the_gate_only_joins_cards_that_share_a_verse():
    cards = [_card("a", ref="John 3:16"), _card("b", ref="John 3:16"),
             _card("c", ref="Romans 8:28")]
    edges = growth.safe_edges(cards)
    pairs = {frozenset((e["a"], e["b"])) for e in edges}
    assert frozenset(("a", "b")) in pairs           # a & b share John 3:16
    assert not any("c" in p for p in pairs)         # c shares with no one — never proposed


def test_normalization_makes_the_same_verse_the_same_verse():
    """A leading space, an abbreviation, and a full name are ONE verse — else true bridges
    are missed and hub counts split (the bug the survey caught)."""
    assert growth.norm_ref(" Matt", "28", "19") == growth.norm_ref("Matthew", "28", "19")
    cards = [_card("a", ref=" Matt 28:19"), _card("b", bands=["Matt. 28:19"]),
             _card("c", title="on Matthew 28:19")]
    edges = growth.safe_edges(cards)
    assert len({frozenset((e["a"], e["b"])) for e in edges}) == 3   # all three pairwise


def test_a_hub_verse_everyone_cites_is_not_drawn():
    """A verse named by many cards is low signal; densifying it over-connects. Only rare
    (specific) shared verses pass — a real bridge, not a crowd."""
    cards = [_card(str(i), ref="Matthew 28:19") for i in range(10)]
    assert growth.safe_edges(cards, max_share=6) == []
    two = [_card("x", ref="Habakkuk 2:4"), _card("y", ref="Habakkuk 2:4")]
    assert growth.safe_edges(two, max_share=6)      # a rare shared verse does pass


def test_an_already_linked_pair_is_never_reproposed():
    cards = [_card("a", ref="John 1:1", links=["b"]), _card("b", ref="John 1:1", links=["a"])]
    assert growth.safe_edges(cards) == []


def test_a_private_card_is_never_grown():
    cards = [_card("a", ref="Psalm 23:1"), _card("b", ref="Psalm 23:1", vis="private")]
    assert growth.safe_edges(cards) == []


def test_edges_carry_their_evidence():
    cards = [_card("a", ref="Micah 5:2"), _card("b", ref="Micah 5:2")]
    e = growth.safe_edges(cards)[0]
    assert e["relationship"] == "shares_scripture" and e["evidence"] == "Micah 5:2"


def test_measure_is_a_deterministic_steering_report():
    cards = [_card("a", ref="John 3:16"), _card("b", ref="John 3:16"),
             _card("c", ref=""), _card("d", ref="", links=["a"])]
    m = growth.measure(cards)
    assert m["cards"] == 4
    assert m["orphans"] == 3                          # a, b, c have no links; d does
    assert m["safe_edges_available"] == 1             # only a-b
    assert growth.measure(cards) == m                 # same corpus, same report


def test_the_ledger_records_and_reads_back():
    growth.ledger_append("draw_safe_edges", {"drawn": 7, "gate": "shares_scripture"}, at=1.0)
    growth.ledger_append("draw_safe_edges", {"drawn": 3, "gate": "shares_scripture"}, at=2.0)
    rows = growth.ledger_read()
    assert rows[-1]["drawn"] == 3 and rows[-2]["drawn"] == 7
    assert all(r["action"] == "draw_safe_edges" for r in rows)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} growth tests passed — 0-FP: it only draws what the data already holds.")
