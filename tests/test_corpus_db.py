"""The small sharded corpus — freeze/unfreeze/rebalance retrieval, on tiny temp shards.

Proves the load-management the device relies on: core thaws automatically; other shards stay FROZEN
(and invisible to search) until unfrozen; a query's domain can be thawed on demand; rebalance freezes
the least-used but never core. All from disk, stdlib sqlite3, no in-RAM card list.
"""
from __future__ import annotations

import json
import sqlite3
import tempfile

import pytest

from concordance import corpus_db


def _mkshard(path, rows):
    c = sqlite3.connect(path)
    c.executescript("create table cards (id text primary key, shelf text, surface text, title text, json text);"
                    "create virtual table fts using fts5(id unindexed, text, tokenize='porter unicode61');")
    for cid, shelf, surface, title, text, obj in rows:
        c.execute("insert into cards values (?,?,?,?,?)", (cid, shelf, surface, title, json.dumps(obj)))
        c.execute("insert into fts values (?,?)", (cid, text))
    c.commit(); c.close()


def _reset():
    for conn in list(corpus_db._OPEN.values()):
        try:
            conn.close()
        except Exception:  # noqa: BLE001
            pass
    corpus_db._OPEN.clear()
    corpus_db._MANIFEST = None
    corpus_db._USE.clear()


@pytest.fixture()
def shards(monkeypatch):
    d = tempfile.mkdtemp(prefix="shards_")
    _mkshard(f"{d}/core.db", [("card_a", "spine", "secular", "The Floor",
                               "floor design created order the word", {"id": "card_a", "title": "The Floor", "shelf": "spine"})])
    _mkshard(f"{d}/books.db", [("card_b", "gutenberg", "secular", "Pride and Prejudice",
                               "pride and prejudice jane austen novel", {"id": "card_b", "title": "Pride and Prejudice", "shelf": "gutenberg"})])
    open(f"{d}/manifest.json", "w").write(json.dumps({"mode": "shards", "shards": {
        "core": {"file": "core.db", "cards": 1, "core": True},
        "books": {"file": "books.db", "cards": 1, "core": False}}}))
    monkeypatch.setenv("CONCORDANCE_CORPUS_SHARDS", d)
    monkeypatch.delenv("CONCORDANCE_CORPUS_DB", raising=False)
    _reset()
    yield d
    _reset()


def test_shards_dir_defaults_to_data_dir_so_freezing_cannot_be_silently_disarmed(monkeypatch):
    """2026-09-05: on the live box `CONCORDANCE_FREEZE_SHELVES` was set but `CONCORDANCE_CORPUS_SHARDS`
    was NOT, so `available()` was False and the whole corpus loaded resident — freezing silently off,
    one env var disarming the other. The shards live beside the data at `<DATA_DIR>/shards`, so
    `available()` must find them from `CONCORDANCE_DATA_DIR` alone. Explicit override still wins; and
    where no built shards exist, it stays False (no behaviour change)."""
    import os
    data = tempfile.mkdtemp(prefix="datadir_")
    monkeypatch.delenv("CONCORDANCE_CORPUS_SHARDS", raising=False)
    monkeypatch.delenv("CONCORDANCE_CORPUS_DB", raising=False)
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", data)
    _reset()
    assert corpus_db.available() is False           # DATA_DIR set, but no shards built yet
    os.mkdir(f"{data}/shards")
    _mkshard(f"{data}/shards/core.db", [("card_a", "spine", "secular", "The Floor", "floor", {"id": "card_a"})])
    open(f"{data}/shards/manifest.json", "w").write(json.dumps({"mode": "shards", "shards": {
        "core": {"file": "core.db", "cards": 1, "core": True}}}))
    _reset()
    assert corpus_db.available() is True            # found beside the data, no second env var needed
    _reset()


def test_core_thaws_automatically_and_searches(shards):
    r = corpus_db.search("floor design")
    assert r and r[0]["id"] == "card_a"
    assert "core" in corpus_db.thawed()


def test_frozen_shard_is_invisible_until_unfrozen(shards):
    assert not any(h["id"] == "card_b" for h in corpus_db.search("pride prejudice austen"))  # books frozen
    corpus_db.thaw_for("gutenberg")                       # route the query's domain to its freight
    assert any(h["id"] == "card_b" for h in corpus_db.search("pride prejudice austen"))


def test_rebalance_freezes_the_extra_but_never_core(shards):
    corpus_db.unfreeze("books")
    corpus_db.rebalance(keep=0)                            # trim all non-core off the yard
    thawed = corpus_db.thawed()
    assert "core" in thawed and "books" not in thawed


def test_airlock_search_pulls_from_frozen_shard_and_leaves_nothing_open(shards):
    r = corpus_db.airlock_search("pride prejudice austen")     # books is frozen
    assert any(h["id"] == "card_b" for h in r)                 # found via the airlock (thaw→pull→reseal)
    assert corpus_db.thawed() == ["core"]                      # nothing lingers but core


def test_get_card_across_thawed_shards(shards):
    corpus_db.thaw_for("gutenberg")
    assert corpus_db.get_card("card_b")["title"] == "Pride and Prejudice"
    assert corpus_db.get_card("nope") is None
