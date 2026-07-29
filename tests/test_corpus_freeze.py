"""The freeze (D4) — heavy shelves ride the shards; the reader never gets a lighter answer.

Matt, 2026-07-27: the two server processes held ~2.8 GB RSS each with every shelf resident, and
the shard layer sat UNWIRED — built, measured, and never consulted. Profiled per-structure
(2026-07-28): dictionary/gutenberg/geography/taxonomy carry 258.7 MB serialized and ~70% of it
is body/bands/extra/source — none of which the GRAPH needs.

Pinned here, as behavior:
  * a frozen-shelf card loads as a STUB — body shed, but id/title/connections/lifecycle intact,
    so the nesting stays whole (zero orphans) and is_public judges it exactly as before;
  * get_card REHYDRATES the full card from the shard — body and provenance return, and the
    LIVE resident graph (bridges, minted edges) wins over the stored copy's connections;
  * search over body text still finds frozen cards (shard FTS fills what title-only stubs
    cannot match) and returns them FULL — the guarantee reaches the reader;
  * no shards on disk -> nothing freezes (bodies are never shed without a way back);
  * a shard that cannot answer returns the stub itself — never a silent hole, never a crash.

Opt-in and reversible: unset CONCORDANCE_FREEZE_SHELVES and everything loads resident as before.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402

_DDL = ("pragma journal_mode=off; pragma synchronous=off;"
        "create table cards (id text primary key, shelf text, surface text, title text, json text);"
        "create virtual table fts using fts5(id unindexed, text, tokenize='porter unicode61');")

FULL_DICT_CARD = {
    "id": "card_dict_zymurgy", "kind": "reference", "title": "Zymurgy",
    "body": "Zymurgy: the branch of applied chemistry dealing with fermentation of barley and "
            "other grains in brewing. The last word in many dictionaries.",
    "bands": ["fermentation", "chemistry", "brewing"],
    "source": {"label": "Webster 1913 (PD)", "ref": "zymurgy", "authority_tier": "reference"},
    "shelf": "dictionary", "surface": "secular", "lifecycle_stage": "public", "generated": False,
    "connections": [{"to_card_id": "card_core_home", "relationship": "member_of",
                     "evidence": "a member of the dictionary shelf"}],
}
CORE_CARD = {
    "id": "card_core_home", "kind": "note", "title": "The home card",
    "body": "A resident core card the frozen one hangs from.",
    "shelf": "codex", "surface": "secular", "lifecycle_stage": "public", "generated": False,
    "connections": [{"to_card_id": "card_dict_zymurgy", "relationship": "has_member",
                     "evidence": "the reciprocal"}],
}


def _build_world(tmp: Path, with_shards: bool = True) -> None:
    """A tiny keeping: one core card + one dictionary card, and (optionally) the dictionary
    card's shard exactly as tools/build_corpus_db.py would write it."""
    with open(tmp / "cards.jsonl", "w", encoding="utf-8") as f:
        f.write(json.dumps(CORE_CARD) + "\n")
        f.write(json.dumps(FULL_DICT_CARD) + "\n")
    if with_shards:
        sh = tmp / "shards"
        sh.mkdir()
        db = sqlite3.connect(str(sh / "dictionary.db"))
        db.executescript(_DDL)
        # the STORED copy carries no connections — the live resident graph must win on rehydrate
        stored = dict(FULL_DICT_CARD, connections=[])
        db.execute("insert into cards values (?,?,?,?,?)",
                   (stored["id"], stored["shelf"], stored["surface"], stored["title"],
                    json.dumps(stored, ensure_ascii=False)))
        db.execute("insert into fts values (?,?)",
                   (stored["id"], f"{stored['title']} {stored['body']}"))
        db.commit()
        db.close()
        (sh / "manifest.json").write_text(
            json.dumps({"shards": {"dictionary": {"file": "dictionary.db", "cards": 1}}}),
            encoding="utf-8")


@pytest.fixture()
def frozen_world():
    """Fresh temp keeping + shard, freeze env on, all module state isolated and restored."""
    from concordance import corpus, corpus_db
    tmp = Path(tempfile.mkdtemp())
    _build_world(tmp)
    prior_env = {k: os.environ.get(k) for k in
                 ("CONCORDANCE_DATA_DIR", "CONCORDANCE_CORPUS_SHARDS", "CONCORDANCE_FREEZE_SHELVES",
                  "CONCORDANCE_CARDS_JSONL", "CONCORDANCE_CORPUS_DB")}
    os.environ["CONCORDANCE_DATA_DIR"] = str(tmp)
    os.environ["CONCORDANCE_CORPUS_SHARDS"] = str(tmp / "shards")
    os.environ["CONCORDANCE_FREEZE_SHELVES"] = "dictionary,gutenberg,geography,taxonomy"
    os.environ.pop("CONCORDANCE_CARDS_JSONL", None)
    os.environ.pop("CONCORDANCE_CORPUS_DB", None)
    prior_default = corpus._DEFAULT
    corpus._DEFAULT = None
    _reset_corpus_db(corpus_db)
    yield tmp
    corpus._DEFAULT = prior_default
    _reset_corpus_db(corpus_db)
    for k, v in prior_env.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _reset_corpus_db(corpus_db):
    for c in list(corpus_db._OPEN.values()):
        try:
            c.close()
        except Exception:  # noqa: BLE001
            pass
    corpus_db._OPEN.clear()
    corpus_db._MANIFEST = None
    corpus_db._USE.clear()


def test_frozen_shelf_loads_as_stub_and_the_graph_stays_whole(frozen_world):
    from concordance import corpus
    cards = corpus.default_corpus().cards
    stub = cards["card_dict_zymurgy"]
    assert stub.get("frozen") is True and "body" not in stub and "bands" not in stub, \
        "the weight is shed"
    assert stub["title"] == "Zymurgy" and stub["shelf"] == "dictionary"
    assert stub["connections"] and stub["connections"][0]["to_card_id"] == "card_core_home", \
        "the nesting stays whole — a stub is never an orphan"
    assert corpus.is_public(stub), "the public boundary judges a stub exactly as the full card"
    core = cards["card_core_home"]
    assert core.get("frozen") is None and core.get("body"), "resident shelves load untouched"


def test_get_card_rehydrates_full_and_the_live_graph_wins(frozen_world):
    from concordance import corpus
    c = corpus.get_card("card_dict_zymurgy")
    assert c and c.get("body", "").startswith("Zymurgy:"), "the reader gets the FULL card back"
    assert c.get("source", {}).get("label") == "Webster 1913 (PD)", "provenance rides home too"
    assert c["connections"] and c["connections"][0]["to_card_id"] == "card_core_home", \
        "the LIVE resident graph wins over the stored copy (which had none)"
    # and the resident stub was never mutated by the read
    assert "body" not in corpus.default_corpus().cards["card_dict_zymurgy"]


def test_search_on_body_text_still_finds_the_frozen_card_full(frozen_world):
    from concordance import corpus
    hits = corpus.search("fermentation of barley in brewing", limit=5)
    ids = [h.get("id") for h in hits]
    assert "card_dict_zymurgy" in ids, \
        "body-text search must still find frozen freight (shard FTS fills the gap)"
    hit = next(h for h in hits if h.get("id") == "card_dict_zymurgy")
    assert hit.get("body"), "and it comes back FULL — the guarantee reaches the reader"


def test_without_shards_nothing_freezes(frozen_world):
    from concordance import corpus, corpus_db
    tmp2 = Path(tempfile.mkdtemp())
    _build_world(tmp2, with_shards=False)
    os.environ["CONCORDANCE_DATA_DIR"] = str(tmp2)
    os.environ["CONCORDANCE_CORPUS_SHARDS"] = str(tmp2 / "no_such_dir")
    corpus._DEFAULT = None
    _reset_corpus_db(corpus_db)
    assert corpus.frozen_shelves() == frozenset(), "no way back -> nothing is shed"
    c = corpus.default_corpus().cards["card_dict_zymurgy"]
    assert c.get("frozen") is None and c.get("body"), "everything loads resident as before"


def test_freezing_never_shifts_the_corpus_idf_statistics(frozen_world):
    """The probe battery caught title-only indexing re-ranking two RESIDENT cards on an
    unrelated query: shedding bodies shrank document frequencies corpus-wide. Pinned: a
    body-only token's IDF is IDENTICAL whether its shelf is frozen or resident."""
    from concordance import corpus
    frozen_c = corpus.default_corpus()
    prior = os.environ.pop("CONCORDANCE_FREEZE_SHELVES")
    try:
        resident_c = corpus.Corpus(corpus.load_cards())
    finally:
        os.environ["CONCORDANCE_FREEZE_SHELVES"] = prior
    q = {"fermentation", "zymurgy", "home"}          # body-only, title, and resident tokens
    assert frozen_c._idf(q) == resident_c._idf(q), \
        "freezing a shelf must not move the corpus-wide IDF statistics"


def test_the_shard_builder_disarms_the_freeze(frozen_world):
    """Shards rebuilt from stubs would destroy the bodies they exist to keep. The builder
    strips the freeze env before loading — pinned by reading its source, since running the
    full builder here would be a build, not a test."""
    src = (Path(__file__).resolve().parent.parent / "tools" / "build_corpus_db.py").read_text(
        encoding="utf-8")
    assert 'os.environ.pop("CONCORDANCE_FREEZE_SHELVES"' in src, \
        "tools/build_corpus_db.py must disarm CONCORDANCE_FREEZE_SHELVES before loading"


def test_rehydrate_falls_back_to_the_stub_never_a_hole(frozen_world):
    from concordance import corpus
    ghost = {"id": "card_dict_not_in_shard", "title": "Ghost", "shelf": "dictionary",
             "frozen": True, "connections": [{"to_card_id": "card_core_home",
                                              "relationship": "member_of", "evidence": "e"}]}
    back = corpus.rehydrate(ghost)
    assert back is ghost, "a shard that cannot answer returns the stub itself — never None"
    assert corpus.rehydrate(None) is None and corpus.rehydrate(CORE_CARD) is CORE_CARD, \
        "non-frozen cards pass through untouched"


if __name__ == "__main__":
    rc = pytest.main([__file__, "-q"])
    sys.exit(int(rc))
