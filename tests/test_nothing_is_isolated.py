"""Nothing in the keeping is isolated — every card carries at least its nesting.

The standing rule is that there are no orphans: every card is at least `member_of` its shelf spine,
so any card can be walked back to the Floor. On 2026-07-28 an audit found 15 that were not — and
they all came from ONE path. `find._mint_doc` (the tortoise, which fetches public-domain sources
when the corpus cannot answer) wrote a literal `"connections": []`, so every source it kept was born
an orphan. Not a historical backlog: an ongoing leak, one more each time it ran.

Two things are pinned here, and the second is the one that matters:

  1. no card in the corpus lacks a connection;
  2. **the tortoise's own mint path produces a nested card** — because fixing the 15 without fixing
     the path would have left the leak open and the count would have crept back up.

Also pinned: the spines live in CODE, not in a data file. `data/web_cache.jsonl` is untracked, so a
spine defined only there would be missing on a fresh box and the graft would dangle.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402


def test_no_card_in_the_keeping_is_isolated():
    # NOT corpus.default_corpus(): which corpus that singleton holds is decided by a race between
    # module imports (53 files point CONCORDANCE_DATA_DIR at a scratch temp dir). Measured
    # 2026-08-03: under the full gate it does hold the real keeping, but in any subset run it is
    # empty and this assertion iterates zero cards and passes. conftest.real_cards() loads the
    # actual keeping either way, and the count below refuses a vacuous one.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from conftest import real_cards
    cards = real_cards()
    assert len(cards) > 100_000, f"only {len(cards):,} cards — this must measure the REAL keeping"
    stranded = [(cid, c.get("shelf"), str(c.get("title"))[:40])
                for cid, c in cards.items()
                if c.get("kind") != "connection" and not (c.get("connections") or [])]
    assert not stranded, (
        f"{len(stranded)} card(s) carry no connection at all — they cannot be walked back to the "
        f"Floor: {stranded[:5]}. Run `python tools/graft_orphans.py --dry-run` to see them, and fix "
        f"the PATH that created them, not just the cards.")


def test_the_tortoise_nests_what_it_brings_back():
    """The class fix. If this fails, the 15 will come back one fetch at a time."""
    from concordance import find
    for shelf, practical in (("practical", True), ("sources", False)):
        conns = find._member_of(shelf)
        assert conns, f"a card kept on the {shelf} shelf would be born with no nesting"
        assert conns[0]["relationship"] == "member_of"
        spine = find._spine_card(shelf)
        assert spine and spine["id"] == conns[0]["to_card_id"], "the graft must not dangle"
        assert spine["connections"][0]["to_card_id"] == find.FLOOR, "the spine must root in the Floor"


def test_a_freshly_minted_source_is_nested_and_its_spine_written():
    """End to end through the real mint path, in a temp store — the fix has to hold where it runs,
    not only where it is declared."""
    from concordance import find
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    try:
        doc = {"title": "A tried and true handbook", "url": "https://example.invalid/x",
               "source": "Library of Congress", "license": "Public domain", "year": "1911"}
        card = find._mint_doc("how to bank a fire", doc, practical=True)
        assert card is not None
        assert card["connections"], "the tortoise minted an orphan again"
        assert card["connections"][0]["to_card_id"] == "card_spine_practical"

        written = (Path(os.environ["CONCORDANCE_DATA_DIR"]) / "web_cache.jsonl").read_text(encoding="utf-8")
        assert "card_spine_practical" in written, "the spine must be written BEFORE the card needing it"
        assert written.index("card_spine_practical") < written.index(card["id"]), (
            "spine must precede its member in the store, or a reader hits a dangling graft")
    finally:
        if prior is None:
            os.environ.pop("CONCORDANCE_DATA_DIR", None)
        else:
            os.environ["CONCORDANCE_DATA_DIR"] = prior


def test_the_graft_is_found_never_guessed():
    """`member_of` here restates a fact the card already carries (its shelf). The tool must REFUSE
    an unknown shelf rather than invent a home — a guessed spine is the authored edge the
    53-false-edge cleanup exists to prevent."""
    from concordance import find
    assert find._member_of("some-shelf-nobody-defined") == []
    assert find._spine_card("some-shelf-nobody-defined") is None


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed — nothing in the keeping is isolated.")
