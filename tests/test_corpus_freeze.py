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
        # the shard holds the FULL card — body, connections, provenance (with lazy stubs, the graph
        # of a frozen card rides the shard, not a resident stub).
        stored = dict(FULL_DICT_CARD)
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


def test_frozen_shelf_is_lazy_not_resident(frozen_world):
    """LAZY STUBS (increment 2): a frozen card is NOT held resident — it leaves only a compact
    index entry (call, title, surface) for browse / the call-tree, and the full card rehydrates
    from the shard on read. Resident RAM scales with the core, not the whole keeping."""
    from concordance import corpus
    cp = corpus.default_corpus()
    assert "card_dict_zymurgy" not in cp.cards, "a frozen card is no longer a resident dict"
    assert "card_dict_zymurgy" in cp._frozen, "it lives in the compact frozen index"
    call, title, surface = cp._frozen["card_dict_zymurgy"]
    assert title == "Zymurgy" and surface == "secular" and call.startswith("dictionary")
    assert cp.has("card_dict_zymurgy"), "the corpus still knows it"
    assert cp.cards["card_core_home"].get("body"), "resident shelves load full, untouched"
    # browse / the call-tree still reach it (walkable via its Dewey call, which heads with its shelf)
    assert "card_dict_zymurgy" in cp.cids_for_call("dictionary"), \
        "the frozen card is walkable via the call-tree, without a resident stub"


def test_a_share_alike_card_on_a_frozen_shelf_is_never_served(frozen_world):
    """A CC-BY-SA card on a frozen shelf is withheld. With lazy stubs it is DROPPED entirely — not
    resident, not in the browse index — so neither browse, get_card, nor search can leak it (its DF
    still counts so IDF is unshifted). Guards the divergence found LIVE 2026-08-06 for HYG cards."""
    from concordance import corpus
    sa = {"id": "card_dict_sa", "kind": "reference", "title": "ShareAlikeWord",
          "body": "a term drawn from a CC-BY-SA source", "shelf": "dictionary", "surface": "secular",
          "lifecycle_stage": "public", "generated": False,
          "source": {"label": "Some DB (CC-BY-SA 4.0)", "authority_tier": "reference"},
          "connections": [{"to_card_id": "card_core_home", "relationship": "member_of",
                           "evidence": "member"}]}
    with open(frozen_world / "cards.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(sa) + "\n")
    cp = corpus.default_corpus()
    assert "card_dict_sa" not in cp.cards and "card_dict_sa" not in cp._frozen, \
        "a withheld frozen card is dropped — not resident, not in the browse index"
    assert corpus.get_card("card_dict_sa") is None, "get_card never serves it"


def test_get_card_rehydrates_full_from_the_shard(frozen_world):
    from concordance import corpus
    c = corpus.get_card("card_dict_zymurgy")
    assert c and c.get("body", "").startswith("Zymurgy:"), "the reader gets the FULL card back"
    assert c.get("source", {}).get("label") == "Webster 1913 (PD)", "provenance rides home too"
    assert c["connections"] and c["connections"][0]["to_card_id"] == "card_core_home", \
        "connections come from the shard's stored copy — the graph rides the shard now"
    assert "card_dict_zymurgy" not in corpus.default_corpus().cards, "still not resident after the read"


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
