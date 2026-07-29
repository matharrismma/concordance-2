"""The commentaries as cards — the father's own words, in the keeping, reaching the reader.

GAPS.md G1: the million must be counted in SUBSTANCE, not stubs. The deepest substance already
on our disk was three public-domain commentaries that lived only behind `/commentary` — not
searchable, not walkable in the graph, invisible to a reader who did not know to ask. Now
44,371 verse cards carry the exposition itself (avg ~1,460 chars).

Pinned here:
  * every card carries REAL TEXT, not a pointer — this seam exists to add substance;
  * every card is nested (member_of its source spine), and every spine roots in the Floor;
  * `comments_on` edges point at verse cards that EXIST — a found edge, never invented;
  * attribution and the PD licence travel with every card (cite-fair), and nothing is
    `generated` — these are the commentator's own recorded words, played back;
  * the shelf is `commentary`, which is frozen freight: the body must therefore be present in
    the SHARD, or the reader gets a title where a paragraph belongs. That is checked here,
    because "correct in the jsonl and empty on the page" is this project's oldest failure.

Skips honestly if the data is absent (it is data, not tracked in git).

Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

CARDS = ROOT / "data" / "commentary_verse_cards.jsonl"


def _cards(limit=None):
    if not CARDS.exists():
        pytest.skip("data/commentary_verse_cards.jsonl absent (mint with tools/card_commentary_verses.py)")
    out = []
    with open(CARDS, encoding="utf-8") as f:
        for i, ln in enumerate(f):
            if limit and i >= limit:
                break
            if ln.strip():
                out.append(json.loads(ln))
    return out


def test_every_card_carries_the_exposition_itself():
    """A commentator's note is as long as he made it. Clarke on 1 Chronicles 1:12 is *"Caphthorim
    — 'The Cappadocians.' — T."* — 37 characters and the whole of what he wrote. So the test is
    not "every body ≥ 120 chars" (my first draft, which failed 330 real cards and would have
    pushed us to DROP genuine exposition to satisfy an instrument). It is: nothing is EMPTY, the
    corpus-wide average is deep, and short notes stay a small minority — which would catch a
    regression that truncated bodies while leaving these honest brief ones alone."""
    cards = _cards(6000)
    verses = [c for c in cards if c.get("box")]
    assert len(verses) > 100
    empty = [c["id"] for c in verses if len((c.get("body") or "").strip()) < 20]
    assert not empty, f"{len(empty)} commentary cards carry no exposition at all: {empty[:3]}"
    avg = sum(len(c["body"]) for c in verses) // len(verses)
    assert avg > 400, f"average body {avg} chars — this seam exists to add substance"
    brief = sum(1 for c in verses if len(c["body"]) < 120)
    assert brief <= len(verses) // 10, (
        f"{brief} of {len(verses)} bodies are under 120 chars — that is no longer a tail of "
        f"genuine short notes, it is truncation")


def test_attribution_and_licence_travel_and_nothing_is_generated():
    for c in _cards(2000):
        src = c.get("source") or {}
        assert "Public Domain" in src.get("label", ""), f"{c['id']}: the licence must travel"
        assert c.get("generated") is False, f"{c['id']}: found words, never generated"
        assert c.get("author") == "engine" and c.get("kind") == "reference"


def test_nesting_holds_and_comments_on_points_at_a_real_verse():
    cards = _cards()
    ids = {c["id"] for c in cards}
    spines = {c["id"] for c in cards if c.get("shelf") == "spine"}
    assert spines, "each commentary needs its spine"
    from concordance import corpus
    keeping = corpus.default_corpus().cards
    stray, dangling = [], []
    for c in cards:
        if c["id"] in spines:
            assert any(e["relationship"] == "part_of" for e in c["connections"]), \
                f"{c['id']}: a spine roots in the Floor"
            continue
        rels = {e["relationship"]: e["to_card_id"] for e in c.get("connections") or []}
        if rels.get("member_of") not in spines:
            stray.append(c["id"])
        target = rels.get("comments_on")
        if target and target not in ids and target not in keeping:
            dangling.append((c["id"], target))
    assert not stray, f"{len(stray)} commentary cards are not nested: {stray[:3]}"
    assert not dangling, f"{len(dangling)} comments_on edges point nowhere: {dangling[:3]}"


def test_the_body_reaches_the_reader_through_the_shard():
    """The `commentary` shelf is frozen freight. If the shard does not hold these bodies, the
    reader gets a title — correct in the jsonl, empty on the page. Checked, not assumed."""
    shards = ROOT / "data" / "shards"
    if not (shards / "manifest.json").exists():
        pytest.skip("no shards built on this machine")
    prior = {k: os.environ.get(k) for k in ("CONCORDANCE_CORPUS_SHARDS", "CONCORDANCE_FREEZE_SHELVES")}
    os.environ["CONCORDANCE_CORPUS_SHARDS"] = str(shards)
    os.environ["CONCORDANCE_FREEZE_SHELVES"] = "commentary"
    try:
        from concordance import corpus_db
        corpus_db._MANIFEST = None
        sample = [c for c in _cards(600) if c.get("box")][:5]
        corpus_db.thaw_for("commentary")
        # The real question is not "is it long enough" (a genuine 37-char Clarke note is the
        # whole of what he wrote) but "does the shard serve EXACTLY what we minted".
        missing = []
        for c in sample:
            full = corpus_db.get_card(c["id"])
            if not full or (full.get("body") or "") != c["body"]:
                missing.append(c["id"])
        assert not missing, ("the shard does not serve what was minted — rebuild with "
                            f"tools/build_corpus_db.py: {missing[:3]}")
    finally:
        for k, v in prior.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
