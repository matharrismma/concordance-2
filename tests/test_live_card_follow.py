"""THE FOLLOWER (run 2026-11-15-live-card-count, step count-follower) — a card another process appends to the
keeping's append-only card logs is counted within one poll, without a restart.

Before this step a process that did not make a card never read it until it restarted: a cold mint
(cas._mint_receipt_card, index=False) appends to receipt_cards.jsonl, shepherd_rounds --choose to
acquired_cards.jsonl, and nh-engine and nh-mcp never read each other's warm receipts (run ledger line 3, (b)).
The follower reads exactly receipt_cards.jsonl, acquired_cards.jsonl and verified_cards.jsonl beside the main cards
file, from where the build's own reading stopped, and hands each new complete line to add_cards (step one's rule).

Every pin runs over a scratch keeping (CONCORDANCE_DATA_DIR and CONCORDANCE_CORPUS_CACHE_DIR in a temporary
directory) and calls the poll directly, with no thread and no sleep — except (7), which starts and stops the one
thread and leaves none behind."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

import pytest  # noqa: E402

from concordance import capabilities, cas, corpus, corpus_cache, ops  # noqa: E402

BODY = "the river runs over the stone and the rope holds fast through the long night " * 2


def _card(cid: str, title: str, shelf: str = "alpha", body: str = BODY, **kw) -> dict:
    c = {"id": cid, "kind": "note", "title": title, "shelf": shelf, "surface": "secular", "body": body}
    c.update(kw)
    return c


def _line(c: dict) -> bytes:
    return json.dumps(c, ensure_ascii=False).encode("utf-8") + b"\n"


def _rows(p: Path, rows) -> None:
    p.write_bytes(b"".join(_line(r) for r in rows))


def _append(p: Path, *cards) -> None:
    with open(p, "ab") as fh:
        fh.write(b"".join(_line(c) for c in cards))


def _receipt(claim: str) -> dict:
    rec = {"kind": "verification", "verdict": "HOLDS", "claim": claim}
    h = cas.content_hash_of(rec)
    return {"id": cas.receipt_card_id(h), "kind": "receipt", "shelf": "seals", "surface": "secular",
            "title": "Receipt " + h[:12] + " HOLDS: " + claim, "body": json.dumps(rec),
            "connections": [{"to_card_id": cas._RECEIPT_SPINE, "relationship": "part_of", "evidence": "x"}]}


SEEDED_PUBLIC = 7      # c_a, c_m, the receipt spine and one receipt, v_1, v_2, w_1 (c_held is withheld)


def _seed(d: Path) -> None:
    _rows(d / "cards.jsonl", [_card("c_m", "Mid"), _card("c_a", "Alpha"),
                              _card("c_held", "Held", lifecycle_stage="public_review")])
    _rows(d / "receipt_cards.jsonl", [cas._receipt_spine(), _receipt("1 + 1 = 2")])
    _rows(d / "verified_cards.jsonl", [_card("v_1", "Verified one", "verified"),
                                       _card("v_2", "Verified two", "verified")])
    _rows(d / "web_cache.jsonl", [_card("w_1", "Cached one", "sources")])


@pytest.fixture
def keeping(tmp_path, monkeypatch):
    d = tmp_path / "keeping"
    d.mkdir()
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(d))
    monkeypatch.setenv("CONCORDANCE_CORPUS_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("CONCORDANCE_CORPUS_CACHE", "0")
    for k in ("CONCORDANCE_CARDS_JSONL", "CONCORDANCE_PROPHECY_DIR", "CONCORDANCE_FREEZE_SHELVES",
              "CONCORDANCE_CORPUS_SHARDS", "CONCORDANCE_CORPUS_DB", "CONCORDANCE_CAS_DIR"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(corpus, "_DEFAULT", None)
    monkeypatch.setattr(ops, "_SUBSTANCE_CACHE", None)
    monkeypatch.setattr(ops, "_SUBSTANCE_PENDING", None, raising=False)
    yield d
    stop = getattr(corpus, "stop_follower", None)
    if stop is not None:
        assert stop(timeout=10)                  # no follower outlives its test


def _boot(monkeypatch, restored: bool) -> corpus.Corpus:
    """The default corpus, built — or restored from the corpus cache, a hit asserted."""
    if restored:
        monkeypatch.setenv("CONCORDANCE_CORPUS_CACHE", "1")
        corpus._DEFAULT = None
        corpus.default_corpus()
        assert corpus.LOAD_PHASES["corpus_cache"] == "miss" and corpus.LOAD_PHASES["corpus_cache_saved"] is True
        corpus._DEFAULT = None
    cp = corpus.default_corpus()
    assert corpus.LOAD_PHASES["corpus_cache"] == ("hit" if restored else "off"), corpus.LOAD_PHASES
    return cp


def _cards_entry() -> dict:
    return capabilities._substrate()["cards"]


# ── (1) a child's cold mint, counted after one poll ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("restored", [False, True], ids=["built", "restored"])
def test_a_childs_mint_is_counted_after_one_poll(keeping, monkeypatch, restored):
    _seed(keeping)
    cp = _boot(monkeypatch, restored)
    count = corpus.card_count()
    assert count == SEEDED_PUBLIC and capabilities.statement()["substrate"]["cards"]["count"] == count
    rec = {"kind": "verification", "verdict": "HOLDS", "claim": "2 + 2 = 4"}
    h = cas.content_hash_of(rec)
    rid = cas.receipt_card_id(h)
    rc = keeping / "receipt_cards.jsonl"
    size0 = rc.stat().st_size
    child = ("import sys; sys.path.insert(0, %r); from concordance import cas; "
             "cas._mint_receipt_card(%r, %r, index=False)" % (str(SRC), h, rec))
    r = subprocess.run([sys.executable, "-I", "-B", "-c", child], env=dict(os.environ), capture_output=True,
                       text=True, timeout=300)
    assert r.returncode == 0, r.stderr
    appended = [json.loads(x)["id"] for x in rc.read_bytes()[size0:].decode("utf-8").splitlines() if x.strip()]
    assert appended == [cas._RECEIPT_SPINE, rid]            # the cold path writes the spine again
    new_ids = set(appended) - set(cp.cards) - set(cp._frozen)
    assert new_ids == {rid} and corpus.get_card(rid) is None
    corpus.poll_followed()
    assert corpus.card_count() == count + len(new_ids)
    assert capabilities.statement()["substrate"]["cards"]["count"] == count + len(new_ids)
    assert all(corpus.get_card(i) is not None for i in new_ids)
    assert corpus.default_corpus() is cp


# ── (2) a torn last line ────────────────────────────────────────────────────────────────────────────────────────

def test_a_torn_last_line_is_taken_only_once_its_newline_arrives(keeping, monkeypatch):
    _seed(keeping)
    _boot(monkeypatch, False)
    count = corpus.card_count()
    vc = keeping / "verified_cards.jsonl"
    line = _line(_card("v_torn", "Torn", "verified"))
    for part in (line[:20], line[20:-1]):                   # the line, still without its newline
        with open(vc, "ab") as fh:
            fh.write(part)
        assert corpus.poll_followed() == 0
        assert corpus.card_count() == count and corpus.get_card("v_torn") is None
    with open(vc, "ab") as fh:
        fh.write(b"\n")
    assert corpus.poll_followed() == 1
    assert corpus.card_count() == count + 1 and corpus.get_card("v_torn") is not None
    assert corpus.poll_followed() == 0 and corpus.card_count() == count + 1


# ── (3) the start: each line counted once, wherever it falls against the load ──────────────────────────────────

@pytest.mark.parametrize("when", ["appended_before_the_load", "appended_after_the_load",
                                  "appended_after_the_key_on_a_hit"])
def test_the_start_counts_each_line_once(keeping, monkeypatch, when):
    _seed(keeping)
    rc = keeping / "receipt_cards.jsonl"
    late = _receipt("3 + 3 = 6")
    if when == "appended_after_the_key_on_a_hit":
        monkeypatch.setenv("CONCORDANCE_CORPUS_CACHE", "1")
        corpus.default_corpus()                              # a miss, saved for the hit below
        assert corpus.LOAD_PHASES["corpus_cache"] == "miss" and corpus.LOAD_PHASES["corpus_cache_saved"] is True
        corpus._DEFAULT = None
        real_load = corpus_cache.load

        def load(path, key):                                 # runs after the key is made
            _append(rc, late)
            return real_load(path, key)

        monkeypatch.setattr(corpus_cache, "load", load)
    else:
        real_load_cards = corpus.load_cards

        def load_cards(*a, **k):
            if when == "appended_before_the_load":
                _append(rc, late)
            out = real_load_cards(*a, **k)
            if when == "appended_after_the_load":
                _append(rc, late)
            return out

        monkeypatch.setattr(corpus, "load_cards", load_cards)
    cp = corpus.default_corpus()
    if when == "appended_after_the_key_on_a_hit":
        assert corpus.LOAD_PHASES["corpus_cache"] == "hit"
    taken_by_the_load = late["id"] in cp.cards
    assert taken_by_the_load == (when == "appended_before_the_load")
    assert corpus.card_count() == SEEDED_PUBLIC + (1 if taken_by_the_load else 0)
    assert corpus.poll_followed() == 1                       # the line is past the start offset every time
    assert corpus.card_count() == SEEDED_PUBLIC + 1          # ... and counts once
    assert corpus.get_card(late["id"]) is not None
    assert corpus.poll_followed() == 0 and corpus.card_count() == SEEDED_PUBLIC + 1


# ── (4) a rewritten file is left to the next restart, and said so ──────────────────────────────────────────────

def _same_size_in_place(p: Path) -> None:
    """Change an early line in place, keeping the file's size, and put its size and mtime_ns back as they were,
    so only the hash can see it."""
    st = p.stat()
    data = p.read_bytes()
    i = data.index(b"Verified one")
    with open(p, "r+b") as fh:
        fh.seek(i)
        fh.write(b"Verified ONE")
    os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns))
    after = p.stat()
    assert (after.st_size, after.st_mtime_ns) == (st.st_size, st.st_mtime_ns)


@pytest.mark.parametrize("how", ["replaced", "truncated", "same_size_in_place", "during_the_load",
                                 "grew_past_the_cap"])
def test_a_rewritten_file_is_left_to_the_restart_with_a_note(keeping, monkeypatch, how):
    _seed(keeping)
    vc = keeping / "verified_cards.jsonl"
    if how == "during_the_load":                             # between the start reading and the end of the load
        real_load_cards = corpus.load_cards

        def load_cards(*a, **k):
            _same_size_in_place(vc)
            return real_load_cards(*a, **k)

        monkeypatch.setattr(corpus, "load_cards", load_cards)
    _boot(monkeypatch, False)
    assert set(_cards_entry()) == {"count", "means"}         # nothing left: exactly the base's keys
    count = corpus.card_count()
    if how == "replaced":
        tmp = vc.with_name(vc.name + ".tmp")
        _rows(tmp, [_card("v_9", "Verified nine", "verified"), _card("v_8", "Verified eight", "verified"),
                    _card("v_7", "Verified seven", "verified")])
        os.replace(tmp, vc)
    elif how == "truncated":
        with open(vc, "r+b") as fh:
            fh.truncate(10)
    elif how == "same_size_in_place":
        _same_size_in_place(vc)
    elif how == "grew_past_the_cap":
        monkeypatch.setattr(corpus, "FOLLOW_MAX_GROWTH", 64)  # a stand-in for 16 MiB: this line is longer
        _append(vc, _card("v_big", "Verified big", "verified"))
    assert corpus.poll_followed() == 0                       # nothing taken from it
    assert corpus.card_count() == count
    monkeypatch.setattr(corpus, "FOLLOW_MAX_GROWTH", 16 * 1024 * 1024)   # the real cap again, for the rest
    entry = _cards_entry()
    assert set(entry) == {"count", "means", "note"}
    assert "verified_cards.jsonl" in entry["note"] and "counted at the next restart" in entry["note"]
    _append(vc, _card("v_after", "Verified after", "verified"))   # never followed again in this process
    assert corpus.poll_followed() == 0 and corpus.card_count() == count
    _append(keeping / "receipt_cards.jsonl", _receipt("4 + 4 = 8"))   # the other files still are
    assert corpus.poll_followed() == 1 and corpus.card_count() == count + 1
    assert "verified_cards.jsonl" in _cards_entry()["note"]


def test_a_replacement_that_keeps_every_read_byte_is_followed_as_an_append(keeping, monkeypatch):
    _seed(keeping)
    _boot(monkeypatch, False)
    count = corpus.card_count()
    vc = keeping / "verified_cards.jsonl"
    tmp = vc.with_name(vc.name + ".tmp")
    tmp.write_bytes(vc.read_bytes() + _line(_card("v_3", "Verified three", "verified")))
    os.replace(tmp, vc)
    assert corpus.poll_followed() == 1
    assert corpus.card_count() == count + 1 and corpus.get_card("v_3") is not None
    assert set(_cards_entry()) == {"count", "means"}


# ── (5) a file absent at the start ──────────────────────────────────────────────────────────────────────────────

def test_a_file_absent_at_the_start_is_followed_from_offset_zero(keeping, monkeypatch):
    _seed(keeping)
    acq = keeping / "acquired_cards.jsonl"
    assert not acq.exists()
    _boot(monkeypatch, False)
    count = corpus.card_count()
    assert corpus.poll_followed() == 0
    _append(acq, _card("a_1", "Acquired one", "sources"), _card("a_2", "Acquired two", "sources"))
    assert corpus.poll_followed() == 2
    assert corpus.card_count() == count + 2 and corpus.get_card("a_1") is not None
    assert set(_cards_entry()) == {"count", "means"}


# ── (6) no corpus, no build; no cell ────────────────────────────────────────────────────────────────────────────

def test_a_poll_with_no_corpus_loaded_builds_none_and_adds_nothing(keeping, monkeypatch):
    _seed(keeping)
    rc = keeping / "receipt_cards.jsonl"
    _append(rc, _receipt("5 + 5 = 10"))
    assert corpus._DEFAULT is None
    assert corpus.poll_followed() == 0
    assert corpus._DEFAULT is None                           # no build
    _boot(monkeypatch, False)                                # the load takes that line
    count = corpus.card_count()
    _append(rc, _receipt("6 + 6 = 12"))
    with monkeypatch.context() as m:
        m.setattr(corpus._cells, "in_a_cell", lambda: True)
        assert corpus.poll_followed() == 0                   # never in a cell
    assert corpus.card_count() == count
    assert corpus.poll_followed() == 1 and corpus.card_count() == count + 1


# ── (7) one thread, and a stop ──────────────────────────────────────────────────────────────────────────────────

def test_two_starts_give_one_thread_and_the_stop_ends_it(keeping, monkeypatch):
    def followers():
        return [t for t in threading.enumerate() if t.name == "nh-follow-cards" and t.is_alive()]

    assert not followers()
    try:
        assert corpus.start_follower() is True
        assert corpus.start_follower() is False              # a second start is a no-op
        assert len(followers()) == 1
    finally:
        assert corpus.stop_follower(timeout=10) is True       # ends within one poll
    assert not followers()


# ── (8) web_cache.jsonl is not followed ─────────────────────────────────────────────────────────────────────────

def test_a_line_in_web_cache_is_not_followed(keeping, monkeypatch):
    _seed(keeping)
    cp = _boot(monkeypatch, False)
    assert "w_1" in cp.cards                                 # the load reads it
    count = corpus.card_count()
    _append(keeping / "web_cache.jsonl", _card("w_2", "Cached two", "sources"))
    assert corpus.poll_followed() == 0
    assert corpus.card_count() == count and corpus.get_card("w_2") is None
