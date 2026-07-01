"""#21/#22 — the Journal + the superposition stack model.

Proves: a card lives ONCE and is referenced into many stacks (no duplication); the Journal keeps by
date + topics; the Deck's exchanges surface in the day's journal (superposition); tiering marks
seldom-used cards cold; the endpoints. Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-stacks-")

from concordance import stacks, threads  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402

SEC = EngineConfig("secular")


def test_card_lives_once_and_touch_makes_it_hot():
    c = stacks.put_card("a thought", kind="idea")
    assert c["use_count"] == 0 and c["tier"] == "hot"
    got = stacks.get_card(c["id"])
    assert got["use_count"] == 1  # touching bumps use


def test_one_card_many_stacks_no_duplication():
    c = stacks.put_card("grace and truth", kind="note")
    stacks.add_to_stack("date", "2026-07-01", c["id"])
    stacks.add_to_stack("topic", "grace", c["id"])
    d = stacks.get_stack("date", "2026-07-01")
    t = stacks.get_stack("topic", "grace")
    assert any(x["id"] == c["id"] for x in d["cards"])
    assert any(x["id"] == c["id"] for x in t["cards"])   # SAME card id in two stacks — one card


def test_journal_add_and_day_and_dates():
    r = stacks.journal_add("a line I don't want to lose", kind="writing", topics=["prayer", "hope"])
    day = r["date"]
    jd = stacks.journal_day(day)
    assert any("don't want to lose" in e["text"] for e in jd["entries"])
    # superposition: the same entry is also in each topic stack
    assert any(e["id"] == r["card"]["id"] for e in stacks.get_stack("topic", "prayer")["cards"])
    assert day in [x["date"] for x in stacks.journal_dates()]


def test_deck_exchanges_surface_in_the_day():
    tid = threads.new_thread("secular")["thread_id"]
    threads.append(tid, "what is mercy", {"kind": "found", "note": "n"})
    today = stacks._today()
    jd = stacks.journal_day(today)
    assert any(e.get("source") == "deck" for e in jd["entries"])   # the Deck's cards appear by date


def test_tier_sweep_marks_seldom_used_cold():
    c = stacks.put_card("old idea", kind="idea")
    p = stacks._card_path(c["id"])
    obj = json.loads(p.read_text(encoding="utf-8"))
    obj["last_touched"] = time.time() - 100 * 86400  # 100 days ago
    p.write_bytes(json.dumps(obj).encode("utf-8"))
    moved = stacks.tier_sweep(cold_after_days=30)
    assert moved >= 1 and stacks.get_card(c["id"], bump=False)["tier"] == "cold"


def test_journal_endpoints():
    st, p = dispatch("POST", "/journal", {}, {"text": "kept via api", "topics": ["api"]}, SEC)
    assert st == 200 and "card" in p and p["date"]
    assert dispatch("POST", "/journal", {}, {"text": "  "}, SEC)[0] == 400
    st2, day = dispatch("GET", "/journal", {"date": p["date"]}, None, SEC)
    assert st2 == 200 and any("kept via api" in e["text"] for e in day["entries"])
    st3, dts = dispatch("GET", "/journal/dates", {}, None, SEC)
    assert st3 == 200 and any(x["date"] == p["date"] for x in dts["dates"])


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} stacks/journal tests passed — one card, many stacks; nothing good falls through.")
