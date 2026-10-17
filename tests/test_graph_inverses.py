"""ONE CONNECTION MODEL, step 1 (GitHub issue #25, 2026-10-16): the reverse label of a bridge is
DECLARED, a pair keeps every relationship it carries, and an exact duplicate edge exists once.

The audit of the card graph found that `corpus._apply_bridges` wrote the SAME label on both cards
for every directional relationship outside the 10-pair `_INVERSE_REL` table — 302 bridge rows
locally (element Z+1 also "preceded" Z), 125 on the tracked seeds — kept only the FIRST edge per
(source, target) so a second relationship on a bridged pair was silently dropped (16 locally, 2 on
the seeds), and that 3,079 exact-duplicate inline edges rode along unnoticed. Pinned here:

  * `_INVERSE_REL` is involutive — reverse(reverse(x)) == x for every label in it, no label is its
    own inverse, no label is both a key and a value of different pairs; and it is disjoint from the
    declared symmetric set `_SYMMETRIC_REL`;
  * the ten pairs that were already there stay exactly as they were;
  * a bridge `precedes` yields `follows` on the reverse card; a symmetric bridge keeps its label;
    a label in neither table is mirrored with its own label and logged ONCE (a visible gap, never
    a silent mirror);
  * a (source, target) pair bridged with two relationships keeps BOTH edges; an exact duplicate
    bridge row adds nothing; a missing relationship becomes the explicit, logged fallback — not
    "names_the_created_thing";
  * exact-duplicate inline connections are dropped at load, deterministically, the first kept;
  * every relationship in the tracked bridge overlays is classified (data-dependent; skips when
    the overlays are absent).

Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import logging
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from concordance import corpus  # noqa: E402

# the table as it stood before issue #25 — these pairs must never drift
_ORIGINAL_PAIRS = {
    "member_of": "has_member", "part_of": "has_part", "nested_in": "contains",
    "figure_of": "has_figure", "pre_registered_validation_of": "validated_by",
    "leads_to": "reached_from", "points_beyond_itself": "pointed_to_by",
    "builds_on": "enables", "open_end_of": "has_open_end", "charts": "charted_by",
}
_DIRECTIONAL_FROM_THE_AUDIT = ("precedes", "demonstrates", "paves", "cites", "modulates", "embodies",
                               "verified_by", "culminates_in", "feeds_back", "demonstrated_by",
                               "instance_of_one_floor")
_SYMMETRIC_FROM_THE_AUDIT = ("connects_at", "same_family", "adjacent", "names_the_created_thing",
                             "kindred", "concords_with")


def _edges(card: dict, to: str):
    return sorted(e["relationship"] for e in card.get("connections", []) if e.get("to_card_id") == to)


def _apply(rows, ids=("A", "B")) -> dict:
    """Stub cards + a temp overlay of `rows`, folded through the real corpus._apply_bridges."""
    d = Path(tempfile.mkdtemp(prefix="nh-graph-inv-"))
    overlay = d / "x_bridges.jsonl"
    overlay.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    cards = {i: {"id": i, "title": i, "connections": []} for i in ids}
    corpus._apply_bridges(cards, overlay)
    return cards


# ---- the tables -----------------------------------------------------------------------------------

def test_inverse_table_is_involutive_and_never_self_inverse():
    inv = corpus._INVERSE_REL
    for k, v in inv.items():
        assert k != v, f"{k!r} declared as its own inverse — that is symmetric, declare it so"
        assert corpus._reverse_rel(k) == v and corpus._reverse_rel(v) == k
        assert corpus._reverse_rel(corpus._reverse_rel(k)) == k
        assert corpus._reverse_rel(corpus._reverse_rel(v)) == v
    # no label is both a key and a value (of different pairs): every label appears in exactly one pair
    labels = list(inv.keys()) + list(inv.values())
    assert len(labels) == len(set(labels)), "a label appears in two inverse pairs"
    assert len(corpus._REVERSE_REL) == 2 * len(inv)


def test_inverse_table_is_disjoint_from_the_symmetric_set():
    assert corpus._SYMMETRIC_REL.isdisjoint(corpus._REVERSE_REL), (
        corpus._SYMMETRIC_REL & set(corpus._REVERSE_REL))
    for rel in corpus._SYMMETRIC_REL:
        assert corpus._reverse_rel(rel) == rel


def test_the_original_ten_pairs_are_unchanged_and_the_audit_list_is_covered():
    for k, v in _ORIGINAL_PAIRS.items():
        assert corpus._INVERSE_REL.get(k) == v, (k, corpus._INVERSE_REL.get(k))
    for rel in _DIRECTIONAL_FROM_THE_AUDIT:
        assert rel in corpus._REVERSE_REL, f"{rel!r} still has no declared inverse"
        assert corpus._reverse_rel(rel) != rel
    for rel in _SYMMETRIC_FROM_THE_AUDIT:
        assert rel in corpus._SYMMETRIC_REL, f"{rel!r} is not declared symmetric"
    # the named pairs the issue asked for
    assert corpus._reverse_rel("precedes") == "follows"
    assert corpus._reverse_rel("follows") == "precedes"
    assert corpus._reverse_rel("demonstrated_by") == "demonstrates"
    assert corpus._reverse_rel("verified_by") == "verifies"
    assert corpus._reverse_rel("cites") == "cited_by"


def test_an_unclassified_relationship_is_mirrored_and_logged_once(caplog):
    rel = "frobnicates_for_this_test_only"
    corpus._REL_GAPS_LOGGED.discard(rel)
    try:
        with caplog.at_level(logging.WARNING, logger="concordance.corpus"):
            assert corpus._reverse_rel(rel) == rel          # the old behavior, kept
            assert corpus._reverse_rel(rel) == rel          # a second call ...
        hits = [r for r in caplog.records if rel in r.getMessage()]
        assert len(hits) == 1, [r.getMessage() for r in caplog.records]   # ... logs nothing new
        assert hits[0].levelno == logging.WARNING
    finally:
        corpus._REL_GAPS_LOGGED.discard(rel)


# ---- _apply_bridges --------------------------------------------------------------------------------

def test_a_precedes_bridge_yields_follows_on_the_reverse_card():
    cards = _apply([{"a": "A", "b": "B", "relationship": "precedes", "evidence": "Z then Z+1"}])
    assert _edges(cards["A"], "B") == ["precedes"]
    assert _edges(cards["B"], "A") == ["follows"], cards["B"]["connections"]
    # the evidence rides on both edges
    assert cards["B"]["connections"][0]["evidence"] == "Z then Z+1"


def test_a_symmetric_bridge_keeps_its_label_both_ways():
    cards = _apply([{"a": "A", "b": "B", "relationship": "connects_at", "evidence": "a joint"}])
    assert _edges(cards["A"], "B") == ["connects_at"]
    assert _edges(cards["B"], "A") == ["connects_at"]


def test_a_pair_with_two_relationships_keeps_both():
    cards = _apply([{"a": "A", "b": "B", "relationship": "part_of", "evidence": "one"},
                    {"a": "A", "b": "B", "relationship": "member_of", "evidence": "two"}])
    assert _edges(cards["A"], "B") == ["member_of", "part_of"]
    assert _edges(cards["B"], "A") == ["has_member", "has_part"]


def test_an_exact_duplicate_bridge_row_is_dropped_once():
    row = {"a": "A", "b": "B", "relationship": "part_of", "evidence": "the same row twice"}
    cards = _apply([row, dict(row)])
    assert _edges(cards["A"], "B") == ["part_of"]
    assert _edges(cards["B"], "A") == ["has_part"]
    assert len(cards["A"]["connections"]) == 1 and len(cards["B"]["connections"]) == 1


def test_a_bridge_never_duplicates_an_inline_edge_already_on_the_card():
    d = Path(tempfile.mkdtemp(prefix="nh-graph-inv-"))
    overlay = d / "x_bridges.jsonl"
    overlay.write_text(json.dumps({"a": "A", "b": "B", "relationship": "part_of", "evidence": "x"}) + "\n",
                       encoding="utf-8")
    cards = {"A": {"id": "A", "connections": [{"to_card_id": "B", "relationship": "part_of", "evidence": "seed"}]},
             "B": {"id": "B", "connections": []}}
    corpus._apply_bridges(cards, overlay)
    assert _edges(cards["A"], "B") == ["part_of"]
    assert cards["A"]["connections"][0]["evidence"] == "seed"      # the first stays, untouched
    assert _edges(cards["B"], "A") == ["has_part"]


def test_a_missing_relationship_is_the_explicit_fallback_and_is_logged(caplog):
    with caplog.at_level(logging.WARNING, logger="concordance.corpus"):
        cards = _apply([{"a": "A", "b": "B", "evidence": "no relationship on this row"}])
    assert corpus._BRIDGE_REL_FALLBACK != "names_the_created_thing"
    assert _edges(cards["A"], "B") == [corpus._BRIDGE_REL_FALLBACK]
    assert _edges(cards["B"], "A") == [corpus._BRIDGE_REL_FALLBACK]
    msgs = [r.getMessage() for r in caplog.records if "x_bridges.jsonl" in r.getMessage()]
    assert len(msgs) == 1 and "1 bridge row" in msgs[0], msgs


def test_a_bridge_to_a_card_not_present_is_skipped():
    cards = _apply([{"a": "A", "b": "NOWHERE", "relationship": "precedes", "evidence": "x"}])
    assert cards["A"]["connections"] == []


# ---- dedupe at load ---------------------------------------------------------------------------------

def test_dedupe_connections_drops_exact_duplicates_and_keeps_the_first_in_place():
    card = {"id": "A", "connections": [
        {"to_card_id": "B", "relationship": "cites", "evidence": "first"},
        {"to_card_id": "C", "relationship": "member_of", "evidence": "spine"},
        {"to_card_id": "B", "relationship": "cites", "evidence": "second copy"},
        {"to_card_id": "B", "relationship": "part_of", "evidence": "a different relationship — stays"},
        {"to_card_id": "B", "relationship": "cites", "evidence": "third copy"},
        "not-a-dict-entry-stays",
    ]}
    assert corpus._dedupe_connections(card) == 2
    assert [(e.get("to_card_id"), e.get("relationship")) if isinstance(e, dict) else e
            for e in card["connections"]] == [("B", "cites"), ("C", "member_of"), ("B", "part_of"),
                                              "not-a-dict-entry-stays"]
    assert card["connections"][0]["evidence"] == "first"
    assert corpus._dedupe_connections(card) == 0          # idempotent
    assert corpus._dedupe_connections({"id": "X"}) == 0    # no connections at all
    assert corpus._dedupe_connections({"id": "X", "connections": "junk"}) == 0


def test_load_cards_drops_exact_duplicate_inline_edges_once():
    d = Path(tempfile.mkdtemp(prefix="nh-graph-inv-"))
    p = d / "cards.jsonl"
    dup = {"to_card_id": "card_spine_x", "relationship": "member_of", "evidence": "the shelf"}
    p.write_text(json.dumps({"id": "card_dup_test", "kind": "note", "title": "dup", "body": "b",
                             "shelf": "codex", "connections": [dup, dict(dup),
                                                               {"to_card_id": "card_spine_x",
                                                                "relationship": "cites", "evidence": "e"}]})
                 + "\n" + json.dumps({"id": "card_clean_test", "kind": "note", "title": "clean", "body": "b",
                                      "shelf": "codex", "connections": [dict(dup)]}) + "\n",
                 encoding="utf-8")
    cards = corpus.load_cards(p)
    assert _edges(cards["card_dup_test"], "card_spine_x") == ["cites", "member_of"]
    assert len(cards["card_clean_test"]["connections"]) == 1
    assert corpus.LOAD_PHASES.get("dup_edges_dropped") == 1


# ---- the tracked seeds -------------------------------------------------------------------------------

def _tracked_bridge_rows():
    rows = []
    for fp in sorted((ROOT / "data").glob("*_bridges.jsonl")):
        for ln in fp.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln:
                try:
                    rows.append(json.loads(ln))
                except json.JSONDecodeError:
                    pass
    return rows


def test_every_relationship_in_the_tracked_bridge_overlays_is_declared():
    rows = _tracked_bridge_rows()
    if not rows:
        pytest.skip("no tracked bridge overlays in data/")
    rels = {r.get("relationship") for r in rows if isinstance(r, dict)}
    gaps = {r for r in rels if r and r not in corpus._REVERSE_REL and r not in corpus._SYMMETRIC_REL}
    assert not gaps, f"bridge relationships in neither table: {sorted(gaps)}"
    assert None not in rels, "a tracked bridge row carries no relationship"


def test_elements_follow_in_order_on_the_tracked_seeds():
    """Z `precedes` Z+1 on the periodic table — and Z+1 `follows` Z, never `precedes` it too."""
    rows = [r for r in _tracked_bridge_rows() if r.get("relationship") == "precedes"]
    if not rows:
        pytest.skip("no `precedes` bridge rows in the tracked overlays")
    ids = {r["a"] for r in rows} | {r["b"] for r in rows}
    d = Path(tempfile.mkdtemp(prefix="nh-graph-inv-"))
    overlay = d / "p_bridges.jsonl"
    overlay.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    cards = {i: {"id": i, "connections": []} for i in ids}
    corpus._apply_bridges(cards, overlay)
    both_ways = [(r["a"], r["b"]) for r in rows if "precedes" in _edges(cards[r["b"]], r["a"])]
    assert not both_ways, both_ways[:5]
    assert all(_edges(cards[r["b"]], r["a"]) == ["follows"] for r in rows)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q", "-p", "no:cacheprovider"]))
