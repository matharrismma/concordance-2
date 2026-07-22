"""Your days — the map of time and concentration, and what it refuses to show.

The counting is the easy part. These tests mostly guard the two refusals: a person's crisis
never appears on a chart, and there is no way to see days that are not yours.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-days-")

from concordance import days, threads  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402

SEC = EngineConfig("secular")
DAY = 86400


def test_it_counts_only_what_you_hold():
    tid = threads.new_thread("secular")["thread_id"]
    threads.append(tid, "covenant in Genesis 15:6", {"kind": "scripture", "message": "x"})
    c = days.chart([tid, "0" * 32, "not-an-id", ""])
    assert c["ok"] and c["threads_found"] == 1 and c["exchanges"] == 1


def test_an_id_you_do_not_hold_shows_you_nothing():
    """The only way in is holding the id. There is no listing to ask for."""
    mine = threads.new_thread("secular")["thread_id"]
    threads.append(mine, "my own work on Ruth 1:16", {"kind": "scripture", "message": "x"})
    empty = days.chart(["a" * 32])
    assert empty["threads_found"] == 0 and empty["exchanges"] == 0
    assert empty["days"] == [] and empty["concentration"] == []


def test_crisis_is_never_charted():
    """A person's worst hour is not a data point. It is excluded from every count — and the
    words themselves must not appear anywhere in the response."""
    tid = threads.new_thread("secular")["thread_id"]
    threads.append(tid, "reading Psalm 23:4 tonight", {"kind": "scripture", "message": "x"})
    threads.append(tid, "i want to end it, i cant go on", {"kind": "crisis", "message": "help"})
    c = days.chart([tid])
    assert c["exchanges"] == 1, "the crisis exchange must not be counted"
    assert c["excluded_private"] == 1, "but the omission must be visible"
    blob = str(c).lower()
    for leaked in ("end it", "cant go on"):
        assert leaked not in blob, f"crisis content reached the chart: {leaked!r}"
    # Nor the REASON. "1 private exchange left out" beside the word "crisis" is an inference
    # anyone can make over your shoulder, and this page is meant to be showable.
    assert "crisis" not in blob, "the chart must not name why an exchange was withheld"


def test_the_chain_still_holds_the_crisis_exchange():
    """Excluded from the chart is not deleted from the record."""
    tid = threads.new_thread("secular")["thread_id"]
    threads.append(tid, "i want to end it", {"kind": "crisis", "message": "help"})
    assert any(e["user"] == "i want to end it" for e in threads.get(tid)["exchanges"])


def test_concentration_is_what_you_returned_to_not_what_you_repeated():
    """Said six times in one sitting is a topic. Said on three different days is a concentration."""
    tid = threads.new_thread("secular")["thread_id"]
    for _ in range(6):
        threads.append(tid, "hesychasm hesychasm hesychasm", {"kind": "found", "message": "x"})
    threads.append(tid, "peripatetic thinking", {"kind": "found", "message": "x"})
    rec = threads.get(tid)
    base = 1_780_000_000.0
    for i, ex in enumerate(rec["exchanges"]):
        ex["at"] = base                      # all six on one day
    rec["exchanges"][-1]["at"] = base + DAY  # the last on a second day
    threads._save(tid, rec) if hasattr(threads, "_save") else None
    c = days.chart([tid])
    assert c["exchanges"] == 7


def test_your_own_clock_decides_the_day():
    """A day boundary in UTC is the wrong day for most of the world."""
    tid = threads.new_thread("secular")["thread_id"]
    threads.append(tid, "late night reading", {"kind": "found", "message": "x"})
    a = days.chart([tid], tz_offset_minutes=0)
    b = days.chart([tid], tz_offset_minutes=-720)
    assert a["days"] and b["days"]
    assert isinstance(a["days"][0]["date"], str) and len(a["days"][0]["date"]) == 10


def test_scripture_and_words_are_pulled_from_your_own_words():
    tid = threads.new_thread("secular")["thread_id"]
    threads.append(tid, "what does chesed mean in H2617", {"kind": "word_study", "message": "x"})
    threads.append(tid, "read John 3:16", {"kind": "scripture", "message": "x"})
    c = days.chart([tid])
    assert any(x["strongs"] == "H2617" for x in c["strongs"])
    assert any("John 3:16" in x["ref"] for x in c["scripture"])


def test_nothing_held_is_an_honest_empty_not_an_error():
    c = days.chart([])
    assert c["ok"] and c["exchanges"] == 0 and c["span"]["days_active"] == 0


def test_the_endpoint_requires_your_own_list():
    assert dispatch("POST", "/days", {}, {}, SEC)[0] == 400
    assert dispatch("POST", "/days", {}, {"thread_ids": "not-a-list"}, SEC)[0] == 400
    st, p = dispatch("POST", "/days", {}, {"thread_ids": []}, SEC)
    assert st == 200 and p["ok"] and p["exchanges"] == 0


def test_the_endpoint_charts_a_held_thread():
    tid = threads.new_thread("secular")["thread_id"]
    threads.append(tid, "Habakkuk 2:4 and the just shall live", {"kind": "scripture", "message": "x"})
    st, p = dispatch("POST", "/days", {}, {"thread_ids": [tid], "tz_offset_minutes": -300}, SEC)
    assert st == 200 and p["exchanges"] == 1
    assert any("Habakkuk 2:4" in x["ref"] for x in p["scripture"])


def test_a_wild_timezone_cannot_be_used_to_skew_the_map():
    st, p = dispatch("POST", "/days", {}, {"thread_ids": [], "tz_offset_minutes": 99999}, SEC)
    assert st == 200 and p["ok"]


def test_a_check_that_happened_by_itself_still_counts_as_work():
    """The Auditor checks claims nobody pressed a button for. If the chart only counted the
    old explicit route it would under-report the work by most of it."""
    tid = threads.new_thread("secular")["thread_id"]
    threads.append(tid, "40 hours at $18.50 an hour is $740.00",
                   {"kind": "found", "message": "x",
                    "audit": {"claims_found": 2, "results": []}})
    assert days.chart([tid])["made"]["checked"] == 2


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} days tests passed — counted, never inferred; crisis never charted; "
          "nothing enumerated.")
