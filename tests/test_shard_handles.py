"""A thread returns the file handles it borrowed — or reading knocks out proving.

THE FAILURE THIS PINS, found by pressure test 2026-08-01 and the worst defect this project has had:

    250 rapid GET /search  ->  1023 of 1024 file descriptors held
    then every POST /verify -> 500
    because Python could no longer open `receipts.py` to import it.

Nothing was wrong with verification. A burst of ordinary READING exhausted the process, and the
first thing to die was the ability to PROVE — the one thing the whole project is for. The engine
reported "internal error" to every caller and could not have explained itself.

The arithmetic was the whole bug: ThreadingHTTPServer opens a thread per connection, corpus_db
opens a connection per thread per shard, and nothing closed one. 255 handles each on dictionary.db
and books.db, 254 each on world.db and word.db. Raising LimitNOFILE would only have set a later
date; a leak refills.

WHY THIS TEST RUNS OVER A REAL SOCKET: the close lives in `Handler.handle`'s `finally`. A test that
called `corpus_db._conn()` and then `close_this_thread()` directly would pass on a server that never
calls it — it would test the function while the wire kept leaking. Check the check.

WHY IT PROVES ITS OWN COVERAGE FIRST: this suite normally runs with no shards configured, so `_OPEN`
is empty and NO connection is ever opened. Every assertion about returning to zero would then pass
without touching the code under test — a green light over an unexercised path, which is the same
blindness as a log glob that silently reads one file. So the test builds a real shard, and refuses
to render a verdict until it can show it opened something.

That guard has now caught three separate ways of measuring nothing, which is a better record than
the code it protects: (1) no `CONCORDANCE_FREEZE_SHELVES`, so the search was answered from resident
memory and no file was ever touched; (2) an ABSOLUTE handle count, which read the whole suite's
threads rather than this burst's; (3) `peak`, a process-wide high-water mark another test had
already driven past anything this burst could reach. Each time the guard was right and the signal
was wrong. What it asks now is the only question that survives a shared process: did the LIFETIME
open counter move, and did THIS burst give back what it took.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

SHARD = "core"          # always thawed, so a plain /search reaches it
CARD_ID = "card_handle_probe"
# A token no resident card carries. The shard is consulted only when the resident corpus has not
# already filled the limit, so a common word would be answered from memory and never touch a file.
PROBE_WORD = "zzhandleprobe"


def _build_shard(dirname: Path) -> None:
    """A real shard, in the shape tools/build_corpus_db.py ships."""
    db = dirname / f"{SHARD}.db"
    conn = sqlite3.connect(str(db))
    try:
        conn.executescript(
            "create table cards (id text primary key, shelf text, surface text, title text, json text);"
            "create virtual table fts using fts5(id unindexed, text, tokenize='porter unicode61');")
        card = {"id": CARD_ID, "title": "handle probe", "shelf": "core", "surface": "secular",
                "kind": "note", "lifecycle_stage": "public",
                "body": f"{PROBE_WORD}: borrowed handles must be returned"}
        conn.execute("insert into cards values (?,?,?,?,?)",
                     (CARD_ID, "core", "secular", "handle probe",
                      json.dumps(card, ensure_ascii=False)))
        conn.execute("insert into fts (id, text) values (?,?)",
                     (CARD_ID, f"{PROBE_WORD} handle probe borrowed handles must be returned"))
        conn.commit()
    finally:
        conn.close()
    (dirname / "manifest.json").write_text(
        json.dumps({"mode": "shards", "shards": {SHARD: {"file": f"{SHARD}.db"}}}),
        encoding="utf-8")


@pytest.fixture(scope="module")
def server():
    shards = Path(tempfile.mkdtemp())
    _build_shard(shards)
    os.environ["CONCORDANCE_CORPUS_SHARDS"] = str(shards)
    # The shard is consulted only for shelves declared FROZEN — without this the whole search is
    # answered from resident memory and no file is ever opened. This is the switch the live boxes
    # run with (24 shelves frozen); the test must run with it too or it measures nothing.
    os.environ["CONCORDANCE_FREEZE_SHELVES"] = SHARD
    os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp())

    from concordance import corpus_db
    from concordance.web import api
    corpus_db._MANIFEST = None                 # pick up the shard dir we just wrote
    corpus_db.unfreeze(SHARD)

    httpd = api.build_server(host="127.0.0.1", port=0, surface="secular",
                             site_dir=str(ROOT / "site"), warm=False)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    os.environ.pop("CONCORDANCE_CORPUS_SHARDS", None)
    os.environ.pop("CONCORDANCE_FREEZE_SHELVES", None)


def _get(base: str, path: str) -> dict:
    # No keep-alive: urlopen closes each connection, so each request is its own thread — exactly
    # the shape that leaked.
    with urllib.request.urlopen(base + path, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def test_a_burst_of_reads_does_not_hoard_file_handles(server):
    from concordance import corpus_db

    before = corpus_db.open_connections()
    for i in range(60):
        _get(server, f"/search?q={PROBE_WORD}&limit=5&n={i}")
    after = corpus_db.open_connections()

    # COVERAGE FIRST: prove the burst actually opened shard connections. Without this the test
    # passes on a build with no shards, having exercised nothing.
    #
    # It must be the MONOTONIC TOTAL, not `peak`. Using `peak` failed a gate run: peak is a
    # process-wide high-water mark, other tests had already driven it to 16, and a burst that
    # honestly opened 5 connections could never exceed it. The guard was right to refuse — the
    # signal was wrong. "Did MY burst do work?" is a question only a running total can answer.
    assert after["opened_total"] > before["opened_total"], (
        "the burst never opened a shard connection — this test proved nothing. "
        f"before={before} after={after}")

    # THE INVARIANT IS A DELTA, NOT AN ABSOLUTE — and that correction was earned too. The first
    # version asserted `open <= 4`, passed alone, and FAILED in the full suite at 16, because the
    # count is process-wide and other tests' threads had touched shards. An absolute reading of a
    # shared process measures the suite, not the code under test. What must be true is narrower and
    # actually the thing claimed: THIS burst releases what THIS burst opened.
    grew = after["open"] - before["open"]
    assert grew <= 4, (
        f"shard handles are accumulating: +{grew} across 60 reads (before={before['open']}, "
        f"after={after['open']}, peak={after['peak']}). This is the 2026-08-01 leak — at 1024 the "
        f"engine stops being able to open its own source files and every /verify answers 500.")


def test_health_reports_the_handle_count(server):
    """A leak nobody can watch is a leak that comes back."""
    h = _get(server, "/health")
    assert "shards" in h, "/health must report shard handles — this leak was invisible for months"
    assert set(h["shards"]) >= {"open", "peak"}
    assert isinstance(h["shards"]["open"], int)


def test_a_thread_releases_what_it_opened(server):
    """The unit contract underneath the wire test: close_this_thread is exact and idempotent."""
    from concordance import corpus_db

    before = corpus_db.open_connections()["open"]
    done = []

    def worker():
        corpus_db._conn(SHARD)
        done.append(corpus_db.close_this_thread())
        done.append(corpus_db.close_this_thread())   # twice is safe

    ts = [threading.Thread(target=worker) for _ in range(12)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()

    assert done.count(1) == 12, f"each thread should close exactly one handle: {done}"
    assert done.count(0) == 12, "a second close must be a no-op, not a double-count"
    after = corpus_db.open_connections()["open"]
    assert after <= before + 2, (
        f"12 threads opened and closed one handle each; the live count went {before} -> {after}. "
        f"A close must actually release, and must not be undone by a second call.")


def test_a_thread_that_reads_again_after_closing_is_still_watched(server):
    """Closing must not make a thread invisible — that is the original leak in a new hat.

    `_conn` registers a thread only when it CREATES its cache. The first version of the fix cleared
    the cache's contents but left the (now empty) cache in place, so a thread that closed and then
    read again rebuilt an unregistered cache: its handles counted nowhere and the reaper could never
    reclaim them.
    """
    from concordance import corpus_db

    seen = {}

    def worker():
        corpus_db._conn(SHARD)
        corpus_db.close_this_thread()
        corpus_db._conn(SHARD)                       # read again on the same thread
        seen["registered"] = threading.get_ident() in corpus_db._CACHES
        seen["counted"] = corpus_db.open_connections()["open"]
        corpus_db.close_this_thread()

    t = threading.Thread(target=worker)
    t.start()
    t.join()

    assert seen["registered"], "a thread that read again after closing was not re-registered"
    assert seen["counted"] >= 1, "its reopened handle was not counted"


def test_dead_threads_have_their_handles_reaped(server):
    """The backstop: the HTTP handler closes its own, but nothing else does — so something must."""
    from concordance import corpus_db

    def worker():
        corpus_db._conn(SHARD)                       # opens, then exits WITHOUT closing

    ts = [threading.Thread(target=worker) for _ in range(8)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()

    after = corpus_db.open_connections()             # reaps as it measures
    assert after["reaped"] >= 8, (
        f"8 threads died holding a shard handle each and only {after['reaped']} were reclaimed. "
        f"Every thread that touches a shard must be covered, not just the HTTP handler.")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
