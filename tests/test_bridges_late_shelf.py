"""A bridge to a card on a late-loaded, FROZEN shelf renders on both cards (2026-10-31).

Seen live on 2026-10-31: tools/seed_computer_science.py had written the row
    {"a": "card_cs_logic_gates", "b": "card_src_book_15114", "relationship": "connects_at", ...}
into the box's chain_bridges.jsonl, yet GET /card?id=card_cs_logic_gates listed no edge to the book, and the
book (shelf gutenberg, a catalogue card) listed only its spine. The sibling row to a resident theory card had
applied, so the seed was sound: the mechanism was the load. corpus._apply_bridges already ran after every source
file (file order was never the gap), but a card on a FROZEN shelf never enters the resident dict — lazy stubs
leave only a (call, title) index entry — so `cards.get(b)` was None and the row was dropped by a silent
`continue`.

Pinned here, as behavior:
  * the bridge resolves against the FULL keeping (resident OR the frozen index): the resident card carries the
    edge inline; the frozen card carries it on read (get_card, which /card serves), beside the shard's own edges,
    with the declared reverse label;
  * the frozen card stays frozen — the fix adds no resident stub;
  * the edges survive the corpus cache (the box boots from it), so a HIT renders what the MISS built;
  * a row whose endpoint exists nowhere attaches NOTHING on either card (0-FP) and is counted and warned —
    never silent (LOAD_PHASES carries the tally; a WARNING names the overlay, the count and the pair);
  * _apply_bridges' own contract: a frozen endpoint counts only when a receiver for its edge is given, so a row
    is applied on both cards or on neither.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402

from concordance import corpus, corpus_db  # noqa: E402

_DDL = ("pragma journal_mode=off; pragma synchronous=off;"
        "create table cards (id text primary key, shelf text, surface text, title text, json text);"
        "create virtual table fts using fts5(id unindexed, text, tokenize='porter unicode61');")

GATES = "card_cs_logic_gates"
BOOK = "card_src_book_15114"
SPINE = "card_spine_gutenberg"
NOWHERE = "card_src_book_nowhere"


def _public(**kw) -> dict:
    c = {"surface": "secular", "lifecycle_stage": "public", "generated": False, "connections": []}
    c.update(kw)
    return c


GATES_CARD = _public(id=GATES, kind="note", title="Logic gates — the 16 functions of two inputs",
                     body="The sixteen Boolean functions of two inputs; AND, OR and NOT suffice to build them all.",
                     shelf="codex", box="computer_science")
SPINE_CARD = _public(id=SPINE, kind="spine", title="Project Gutenberg", body="The Great Books, catalogued.",
                     shelf="spines")
BOOK_CARD = _public(id=BOOK, kind="reference", title="An Investigation of the Laws of Thought (Boole, 1854)",
                    body="Boole's calculus of logic: the laws of thought written as algebra. A Project Gutenberg "
                         "catalogue card; the full text ships on demand.",
                    shelf="gutenberg",
                    source={"label": "Project Gutenberg (PD)", "ref": "15114", "authority_tier": "reference"},
                    connections=[{"to_card_id": SPINE, "relationship": "member_of", "evidence": "catalogued"}])

ROW_SYM = {"a": GATES, "b": BOOK, "relationship": "connects_at", "evidence": "Boole's laws name the gates"}
ROW_DIR = {"a": GATES, "b": BOOK, "relationship": "rests_on", "evidence": "the gates rest on Boole's algebra"}


def _rows(p: Path, rows) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def _build_world(tmp: Path, bridge_rows) -> None:
    """A tiny keeping laid out like the real one: the resident chain card in chain_cards.jsonl; the Gutenberg
    catalogue card in gutenberg_cards.jsonl (an EXTRA source listed after chain_cards, on a shelf the box
    freezes); the overlay in chain_bridges.jsonl; and the book's shard as tools/build_corpus_db.py writes it."""
    _rows(tmp / "cards.jsonl", [SPINE_CARD])
    _rows(tmp / "chain_cards.jsonl", [GATES_CARD])
    _rows(tmp / "gutenberg_cards.jsonl", [BOOK_CARD])
    _rows(tmp / "chain_bridges.jsonl", bridge_rows)
    sh = tmp / "shards"
    sh.mkdir()
    shard = corpus_db.shard_of("gutenberg")
    db = sqlite3.connect(str(sh / f"{shard}.db"))
    db.executescript(_DDL)
    db.execute("insert into cards values (?,?,?,?,?)",
               (BOOK, BOOK_CARD["shelf"], BOOK_CARD["surface"], BOOK_CARD["title"],
                json.dumps(BOOK_CARD, ensure_ascii=False)))
    db.execute("insert into fts values (?,?)", (BOOK, f"{BOOK_CARD['title']} {BOOK_CARD['body']}"))
    db.commit()
    db.close()
    (sh / "manifest.json").write_text(json.dumps({"shards": {shard: {"file": f"{shard}.db", "cards": 1}}}),
                                      encoding="utf-8")


def _reset_corpus_db() -> None:
    for c in list(corpus_db._OPEN.values()):
        try:
            c.close()
        except Exception:  # noqa: BLE001
            pass
    corpus_db._OPEN.clear()
    corpus_db._MANIFEST = None
    corpus_db._USE.clear()


@pytest.fixture()
def world(monkeypatch):
    """A fresh temp keeping with the gutenberg shelf FROZEN, the corpus cache off (one test turns it on), and
    all module state isolated and restored."""
    tmp = Path(tempfile.mkdtemp(prefix="nh-bridge-late-"))
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp))
    monkeypatch.setenv("CONCORDANCE_CORPUS_SHARDS", str(tmp / "shards"))
    monkeypatch.setenv("CONCORDANCE_FREEZE_SHELVES", "gutenberg")
    monkeypatch.setenv("CONCORDANCE_CORPUS_CACHE", "0")
    monkeypatch.setenv("CONCORDANCE_CORPUS_CACHE_DIR", str(tmp / "cache"))
    for k in ("CONCORDANCE_CARDS_JSONL", "CONCORDANCE_CORPUS_DB", "CONCORDANCE_PROPHECY_DIR"):
        monkeypatch.delenv(k, raising=False)
    prior = corpus._DEFAULT
    corpus._DEFAULT = None
    _reset_corpus_db()
    yield tmp
    corpus._DEFAULT = prior
    _reset_corpus_db()


def _boot():
    corpus._DEFAULT = None
    _reset_corpus_db()
    return corpus.default_corpus(), dict(corpus.LOAD_PHASES)


def _edges(card, to):
    return sorted(e["relationship"] for e in (card or {}).get("connections", []) if e.get("to_card_id") == to)


def test_a_bridge_to_a_frozen_shelf_card_renders_on_both_cards(world):
    _build_world(world, [ROW_SYM, ROW_DIR])
    cp, ph = _boot()
    assert BOOK not in cp.cards and BOOK in cp._frozen, "the book is FROZEN — the path that dropped the edge live"
    assert GATES in cp.cards
    gates = corpus.get_card(GATES)
    assert _edges(gates, BOOK) == ["connects_at", "rests_on"], gates["connections"]
    book = corpus.get_card(BOOK)
    assert book and book.get("body", "").startswith("Boole's calculus"), "the full card, rehydrated from the shard"
    assert _edges(book, GATES) == ["connects_at", "supports"], \
        "the reverse edges on the frozen card: the symmetric label kept, the declared inverse for rests_on"
    assert _edges(book, SPINE) == ["member_of"], "the shard's own graph stays beside the grafted edges"
    assert BOOK not in corpus.default_corpus().cards, "still not resident after the read — no stub was added"
    links = corpus.connections(BOOK)["links"]
    assert any(e["to_card_id"] == GATES and e["relationship"] == "connects_at" for e in links)
    assert _edges(corpus.get_card(BOOK), GATES) == ["connects_at", "supports"], "a second read never doubles it"
    assert ph["bridge_rows"] == 2 and ph["bridge_rows_applied"] == 2 and ph["bridge_rows_unresolved"] == 0, ph
    assert ph["bridge_edges_frozen_side"] == 2 and ph["bridge_unresolved_by_overlay"] == {}, ph


def test_the_same_bridge_resolves_when_the_shelf_loads_resident(world, monkeypatch):
    """With nothing frozen the gutenberg card is resident — still an EXTRA source listed after chain_cards.jsonl,
    and the overlay applies after every source file is read, so the same edges render on both cards."""
    _build_world(world, [ROW_SYM])
    monkeypatch.setenv("CONCORDANCE_FREEZE_SHELVES", "")
    cp, ph = _boot()
    assert BOOK in cp.cards and not cp._frozen
    assert _edges(corpus.get_card(GATES), BOOK) == ["connects_at"]
    assert _edges(corpus.get_card(BOOK), GATES) == ["connects_at"]
    assert ph["bridge_rows_applied"] == 1 and ph["bridge_edges_frozen_side"] == 0, ph
    assert ph["bridge_rows_unresolved"] == 0, ph


def test_the_corpus_cache_hit_renders_the_same_edges(world, monkeypatch):
    """The box boots from the corpus cache; the frozen side must ride it, or the fix lasts exactly one boot."""
    _build_world(world, [ROW_SYM, ROW_DIR])
    monkeypatch.setenv("CONCORDANCE_CORPUS_CACHE", "1")
    cp1, ph1 = _boot()
    assert ph1["corpus_cache"] == "miss" and ph1["corpus_cache_saved"] is True, ph1
    want_gates, want_book = _edges(corpus.get_card(GATES), BOOK), _edges(corpus.get_card(BOOK), GATES)
    assert want_gates == ["connects_at", "rests_on"] and want_book == ["connects_at", "supports"]
    cp2, ph2 = _boot()
    assert ph2["corpus_cache"] == "hit" and ph2["load_cards_ms"] == 0.0, ph2
    assert cp2 is not cp1 and cp2._frozen_edges == cp1._frozen_edges and set(cp2._frozen_edges) == {BOOK}
    assert ph2["frozen_edges"] == 1, ph2
    assert _edges(corpus.get_card(GATES), BOOK) == want_gates
    assert _edges(corpus.get_card(BOOK), GATES) == want_book


def test_a_row_to_a_card_nowhere_attaches_nothing_and_is_counted_and_warned(world, caplog):
    """0-FP: an endpoint in neither the resident keeping nor the frozen index gets no edge on either card.
    Never silent: the count rides LOAD_PHASES and a WARNING names the overlay, the count and the pair."""
    gone_b = {"a": GATES, "b": NOWHERE, "relationship": "connects_at", "evidence": "a book that is not here"}
    gone_a = {"a": "card_cs_not_seeded", "b": BOOK, "relationship": "cites", "evidence": "a card that is not here"}
    _build_world(world, [ROW_SYM, gone_b, gone_a])
    with caplog.at_level(logging.WARNING, logger="concordance.corpus"):
        cp, ph = _boot()
    gates, book = corpus.get_card(GATES), corpus.get_card(BOOK)
    assert _edges(gates, BOOK) == ["connects_at"] and _edges(gates, NOWHERE) == []
    assert _edges(book, GATES) == ["connects_at"] and _edges(book, "card_cs_not_seeded") == []
    assert set(cp._frozen_edges) <= set(cp._frozen), "the side table never names a card the keeping lacks"
    assert ph["bridge_rows"] == 3 and ph["bridge_rows_applied"] == 1 and ph["bridge_rows_unresolved"] == 2, ph
    assert ph["bridge_unresolved_by_overlay"] == {"chain_bridges.jsonl": 2}, ph
    msgs = [r.getMessage() for r in caplog.records if "chain_bridges.jsonl" in r.getMessage()]
    assert any("2 of 3" in m and NOWHERE in m and "card_cs_not_seeded" in m for m in msgs), msgs
    assert any("still unresolved at the end of the load" in m for m in msgs), msgs


def test_a_frozen_endpoint_without_a_receiver_is_unresolved_not_half_applied(tmp_path):
    """_apply_bridges' own contract: `frozen` counts only when `frozen_edges` is given to receive the frozen
    side, so a row is applied on both cards or on neither; and the two-argument call every stub-world test
    makes still works."""
    overlay = tmp_path / "x_bridges.jsonl"
    _rows(overlay, [{"a": "A", "b": "B", "relationship": "part_of", "evidence": "e"}])
    frozen = {"B": ("gutenberg.b", "B", "secular")}
    cards = {"A": {"id": "A", "connections": []}}
    st = corpus._apply_bridges(cards, overlay, frozen=frozen)                       # no receiver
    assert cards["A"]["connections"] == [] and st["unresolved"] == 1 and st["applied"] == 0
    side: dict = {}
    st = corpus._apply_bridges(cards, overlay, frozen=frozen, frozen_edges=side)
    assert _edges(cards["A"], "B") == ["part_of"] and st["applied"] == 1 and st["frozen_side"] == 1
    assert side == {"B": [{"to_card_id": "A", "relationship": "has_part", "evidence": "e"}]}
    st = corpus._apply_bridges(cards, overlay, frozen=frozen, frozen_edges=side)   # idempotent
    assert len(cards["A"]["connections"]) == 1 and len(side["B"]) == 1 and st["frozen_side"] == 0
    st = corpus._apply_bridges(cards, overlay)                                      # the old call shape
    assert st["applied"] == 0 and st["unresolved"] == 1 and len(cards["A"]["connections"]) == 1


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
