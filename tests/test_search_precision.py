"""A miss must stay a miss — asking a question must not manufacture an answer.

FOUND BY THE 1,000-PROBE ANCIENT ASSAY, 2026-08-01, live on narrowhighway.com:

    q="Mahavira"          -> 0 results, and want_hint offers to record the miss.   CORRECT.
    q="what is Mahavira"  -> 3 results: Aurelius Meditations 8.51, 8.10, Boethius §boe_03_10.

`corpus_db._match` joined EVERY token with OR, stopwords included, so any natural-language question
matched any card containing "what" or "is". Three classics cards surfaced across roughly 250
unrelated probes — Sumerian cities, Chinese philosophers, Vedic texts — purely because they contain
common English words.

WHY THIS IS A DOCTRINAL BUG AND NOT A RANKING PREFERENCE. The library answered "here is what I have"
when the truth was "I do not have that." And because results came back, `want_hint` never fired, so
the miss was never recorded and the shepherd loop was never fed. The whole design says the library
grows by its misses; this silently ate them. A gap is a third state and must be permitted to say so
— the same rule that forbids sealing our own failure as a verdict.

It also inflated the assay's own numbers: what looked like 251 damaged cards was three classics
cards seen over and over.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

SHARD = "core"


@pytest.fixture(scope="module")
def shards():
    d = Path(tempfile.mkdtemp())
    conn = sqlite3.connect(str(d / f"{SHARD}.db"))
    try:
        conn.executescript(
            "create table cards (id text primary key, shelf text, surface text, title text, json text);"
            "create virtual table fts using fts5(id unindexed, text, tokenize='porter unicode61');")
        # A card full of ordinary English words — the shape that hijacked every "what is X" query.
        rows = [
            ("card_meditations", "classics", "Meditations 8.51",
             "He that knoweth not what the world is, knoweth not where he is"),
            ("card_zoroaster", "persia", "Zoroaster",
             "Zoroaster taught of Ahura Mazda and the ordering of asha"),
        ]
        for cid, shelf, title, body in rows:
            card = {"id": cid, "title": title, "shelf": shelf, "surface": "secular",
                    "lifecycle_stage": "public", "body": body}
            conn.execute("insert into cards values (?,?,?,?,?)",
                         (cid, shelf, "secular", title, json.dumps(card)))
            conn.execute("insert into fts (id, text) values (?,?)", (cid, f"{title} {body}"))
        conn.commit()
    finally:
        conn.close()
    (d / "manifest.json").write_text(
        json.dumps({"mode": "shards", "shards": {SHARD: {"file": f"{SHARD}.db"}}}), encoding="utf-8")

    os.environ["CONCORDANCE_CORPUS_SHARDS"] = str(d)
    from concordance import corpus_db
    corpus_db._MANIFEST = None
    corpus_db._OPEN.clear()
    corpus_db.unfreeze(SHARD)
    yield corpus_db
    corpus_db.close_this_thread()
    os.environ.pop("CONCORDANCE_CORPUS_SHARDS", None)


def test_a_question_about_something_absent_returns_nothing(shards):
    """THE BUG, pinned. 'what is Mahavira' must not return Marcus Aurelius."""
    hits = shards.search("what is Mahavira", limit=5)
    titles = [h.get("title") for h in hits]
    assert hits == [], (
        f"a question about a term we do not hold returned {titles}. The stopwords 'what' and 'is' "
        f"matched an unrelated card, so the miss was hidden and no want was ever recorded.")


def test_the_bare_term_behaves_the_same_as_the_question(shards):
    """The two spellings of one question must agree — otherwise phrasing decides truth."""
    assert shards.search("Mahavira", limit=5) == []
    assert shards.search("what is Mahavira", limit=5) == []


def test_a_question_about_something_present_still_answers(shards):
    """Precision must not cost recall on real holdings — we refuse abuse, not use."""
    hits = shards.search("what is Zoroaster", limit=5)
    assert hits, "a natural-language question about a card we DO hold must still find it"
    assert hits[0]["id"] == "card_zoroaster"


def test_all_words_beat_any_word(shards):
    """Both terms present outranks a loose single-term match."""
    hits = shards.search("Zoroaster Ahura Mazda", limit=5)
    assert hits and hits[0]["id"] == "card_zoroaster"


def test_a_query_of_only_stopwords_is_not_a_query(shards):
    """'what is it' asks about nothing; matching everything is not an answer."""
    assert shards._match("what is it") == ""
    assert shards.search("what is it", limit=5) == []


def test_stopwords_never_reach_the_match_expression(shards):
    expr = shards._match("what is the Rigveda")
    assert "what" not in expr and '"is"' not in expr and '"the"' not in expr
    assert "rigveda" in expr


def test_both_doors_share_one_stopword_list():
    """THE RESIDENT CORPUS HAD THE SAME BUG, and fixing only the shard side did not fix the site.

    After the shard matcher was corrected and deployed, `what is Mahavira` STILL returned Marcus
    Aurelius live, because there are two searchers: the shard FTS and the resident in-memory index.
    The resident one scores with IDF, which dampens common words but never excludes them —
    log(478k / 20k) is about 3.2, small beside a rare term and nowhere near zero. With the
    distinctive word matching nothing, "what" and "is" were the only contributors and carried
    unrelated cards to the reader.

    Fixing one instance of a defect and calling the path repaired is exactly the failure this
    project keeps meeting. One list, imported by both, so they cannot drift.
    """
    from concordance import corpus, corpus_db
    assert corpus_db._STOP, "the stopword list must not be empty"
    for w in ("what", "is", "the", "of", "how"):
        assert w in corpus_db._STOP
    # The resident door must reach for the same list, not keep a copy of its own.
    src = Path(corpus.__file__).read_text(encoding="utf-8")
    assert "_STOP" in src, "corpus.py must filter stopwords too — IDF alone does not"


def test_a_shard_reregistered_at_a_new_path_is_actually_reopened(shards):
    """A cache keyed by NAME serves the old file forever after the shard moves.

    Found 2026-08-01: two test modules each registered a shard called `core` at different temp
    paths, and the second was served the first one's cards — passing alone, failing in the suite.
    That is not a test artifact. On a live box the same shape is a rebuilt or relocated shard whose
    readers keep getting the previous corpus, with no error raised anywhere: the library confidently
    hands over the wrong thing, which is the one failure this module exists to prevent.
    """
    other = Path(tempfile.mkdtemp())
    conn = sqlite3.connect(str(other / f"{SHARD}.db"))
    try:
        conn.executescript(
            "create table cards (id text primary key, shelf text, surface text, title text, json text);"
            "create virtual table fts using fts5(id unindexed, text, tokenize='porter unicode61');")
        card = {"id": "card_relocated", "title": "Relocated", "shelf": "moved",
                "surface": "secular", "lifecycle_stage": "public",
                "body": "Zoroaster appears only in the relocated shard"}
        conn.execute("insert into cards values (?,?,?,?,?)",
                     ("card_relocated", "moved", "secular", "Relocated", json.dumps(card)))
        conn.execute("insert into fts (id, text) values (?,?)",
                     ("card_relocated", "Relocated Zoroaster appears only in the relocated shard"))
        conn.commit()
    finally:
        conn.close()

    shards.search("Zoroaster", limit=3)                    # warm this thread's handle on the OLD file
    shards._OPEN[SHARD] = str(other / f"{SHARD}.db")       # the shard now lives somewhere else
    hits = shards.search("Zoroaster", limit=3)

    assert hits, "after relocation the shard answered nothing"
    assert hits[0]["id"] == "card_relocated", (
        f"served {hits[0]['id']} from the OLD file after the shard moved — a stale corpus with no "
        f"error raised is the worst way for a library to fail.")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
