"""A shard must answer many readers at once — the bug our own telemetry caught.

`data/activity.jsonl`, 2026-07-29 16:55:
    {"action": "mcp_error", "tool": "cards_browse",
     "detail": "OperationalError: database is locked"}

One connection per shard is shared across every thread of a ThreadingHTTPServer, and during the
30k-request days at the end of July concurrent readers collided on SQLite's file locks. An agent
asked and got an error instead of the library.

The fix is `immutable=1`, which states something TRUE about a shard — built offline, shipped, never
written while serving — so SQLite skips locking altogether. This test drives real threads at a real
file, because a lock bug does not reproduce in a single-threaded assertion and the previous code
passed every test in the suite while failing live.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from concordance import corpus_db  # noqa: E402

READERS = 12
ROUNDS = 40


@pytest.fixture(scope="module")
def shard(tmp_path_factory):
    """A real shard file, shaped like the ones tools/build_corpus_db.py ships."""
    p = tmp_path_factory.mktemp("shards") / "probe.db"
    con = sqlite3.connect(str(p))
    con.execute("create table cards (id text primary key, title text, body text, shelf text)")
    con.executemany("insert into cards values (?,?,?,?)",
                    [(f"card_{i}", f"Title {i}", f"Body of card {i}", "probe") for i in range(500)])
    con.commit()
    con.close()
    return str(p)


def test_a_shard_is_opened_lock_free(shard):
    """The flag itself, on the connection the module actually builds."""
    c = corpus_db._open_db(shard)
    try:
        assert c.execute("select count(*) from cards").fetchone()[0] == 500
        # read-only is still enforced — immutable must not be mistaken for "unguarded"
        with pytest.raises(sqlite3.OperationalError):
            c.execute("insert into cards values ('x','x','x','x')")
    finally:
        c.close()


def test_many_threads_read_one_shard_without_locking(shard):
    """THE REGRESSION. One shared connection, many concurrent readers — exactly the live shape.

    Before `immutable=1` this is the arrangement that raised `database is locked`."""
    # Drive it exactly the way the server does: register the shard as thawed, then let each thread
    # ask the module for a connection — which is where the per-thread fix lives.
    corpus_db._OPEN["probe"] = shard
    errors: list = []
    barrier = threading.Barrier(READERS)

    def reader(n: int) -> None:
        try:
            barrier.wait(timeout=30)          # make them collide, not queue politely
            for i in range(ROUNDS):
                conn = corpus_db._conn("probe")
                assert conn is not None
                cur = conn.execute(
                    "select id, title from cards where id = ?", (f"card_{(n * 7 + i) % 500}",))
                row = cur.fetchone()
                assert row is not None, (
                    f"card_{(n * 7 + i) % 500} exists in the file but the shard said it does not — "
                    f"a wrong answer, which is worse than an error")
                conn.execute("select count(*) from cards").fetchone()
        except Exception as exc:  # noqa: BLE001 — the whole point is to collect what went wrong
            errors.append(f"{type(exc).__name__}: {exc}")

    threads = [threading.Thread(target=reader, args=(n,)) for n in range(READERS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    assert not errors, (f"{len(errors)} of {READERS} concurrent readers failed — "
                        f"this is the live bug: {errors[:3]}")
    corpus_db._OPEN.pop("probe", None)


def test_the_immutable_promise_is_stated_where_it_binds():
    """`immutable=1` tells SQLite the bytes cannot change, so a rebuild REQUIRES a restart. That
    obligation must be written next to the flag, or the next person who rebuilds a shard by hand
    reads stale pages and has no idea why."""
    src = (ROOT / "src" / "concordance" / "corpus_db.py").read_text(encoding="utf-8")
    assert "immutable=1" in src
    # The obligation belongs with the CONNECT CALL, not merely somewhere in the file — so read the
    # body of _open_db itself rather than the first mention anywhere.
    start = src.index("def _open_db(")
    body = src[start:src.index("\ndef ", start + 1)].lower()
    assert "immutable=1" in body, "the flag is not on the connection this module opens"
    assert "restart" in body, "the rebuild-then-restart obligation is not stated beside the flag"


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
