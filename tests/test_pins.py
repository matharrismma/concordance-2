"""Pins — the page remembers what you were carrying.

Guarded here: the discernment (list vs reminder vs note vs question), the when-parser's
determinism, the privacy law (nothing enumerable — unheld ids return nothing), and that
crossing off leaves the record intact while leaving the page.
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-pins-")

from concordance import pins, threads  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402

SEC = EngineConfig("secular")

# a fixed Tuesday 10:00 local — the when-parser must answer the same forever
_TUE = time.mktime((2026, 7, 21, 10, 0, 0, 0, 0, -1))


def _tid():
    return threads.new_thread("secular")["thread_id"]


def test_a_list_looks_like_a_list_and_a_letter_does_not():
    assert pins.looks_like_list("milk\neggs\nbread")
    assert pins.looks_like_list("- call the vet\n- fix the gate latch")
    assert not pins.looks_like_list("Dear brother, I have been thinking about the farm all week.")
    assert not pins.looks_like_list("milk")


def test_a_question_is_never_kept_as_a_note():
    assert not pins.looks_like_note("what should I do about the barn roof?")
    assert pins.looks_like_note(
        "I keep circling the same thought about the barn and I want to get it down before it goes")


def test_the_when_parser_is_deterministic():
    assert pins.parse_when("remind me in 2 hours", now=_TUE) == _TUE + 7200
    assert pins.parse_when("remind me tomorrow", now=_TUE) == _TUE - 10 * 3600 + 86400 + 9 * 3600
    thu = pins.parse_when("remind me Thursday", now=_TUE)
    assert time.localtime(thu).tm_wday == 3 and thu > _TUE
    # a weekday named on that same weekday means the NEXT one, not right now
    tue2 = pins.parse_when("remind me Tuesday", now=_TUE)
    assert tue2 - _TUE > 6 * 86400
    assert pins.parse_when("remind me to call the bank", now=_TUE) is None


def test_pins_greet_the_pages_you_hold_and_nobody_else():
    tid = _tid()
    pins.add(tid, "list", "milk\neggs")
    pins.add(tid, "reminder", "call the bank", due=None)
    got = pins.collect([tid])
    assert len(got["pins"]) == 2
    assert pins.collect(["a" * 32])["pins"] == []          # an unheld id shows nothing
    assert pins.collect([])["pins"] == []


def test_a_future_reminder_waits_and_a_due_one_comes_forward():
    tid = _tid()
    pins.add(tid, "reminder", "sharpen the mower", due=time.time() + 86400 * 3)
    pins.add(tid, "reminder", "water the seedlings", due=time.time() - 60)
    got = pins.collect([tid])["pins"]
    waiting = {p["text"]: p["waiting"] for p in got}
    assert waiting["sharpen the mower"] is True
    assert waiting["water the seedlings"] is False
    assert got[0]["text"] == "water the seedlings"          # due first


def test_crossing_off_leaves_the_page_but_not_the_record():
    tid = _tid()
    pin = pins.add(tid, "list", "one thing")["pin"]
    assert pins.done(tid, pin["id"])["ok"]
    assert pins.collect([tid])["pins"] == []
    raw = pins._load(tid)
    assert raw and raw[0]["done"] is True and "one thing" in raw[0]["text"]


def test_the_endpoints_hold_the_same_law():
    tid = _tid()
    pins.add(tid, "list", "nails\ntwine")
    st, p = dispatch("POST", "/pins", {}, {"thread_ids": [tid]}, SEC)
    assert st == 200 and len(p["pins"]) == 1
    st, d = dispatch("POST", "/pins/done", {},
                     {"thread_id": tid, "id": p["pins"][0]["id"]}, SEC)
    assert st == 200
    assert dispatch("POST", "/pins", {}, {}, SEC)[0] == 400
    assert dispatch("POST", "/pins/done", {}, {"thread_id": tid}, SEC)[0] == 400
    assert dispatch("POST", "/pins/done", {}, {"thread_id": tid, "id": "nope"}, SEC)[0] == 404


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} pins tests passed — carried, crossed off, never enumerable.")
