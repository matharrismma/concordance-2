#!/usr/bin/env python3
"""The usefulness probe — measure real-life usefulness of the front door, on a battery of the
questions ordinary people actually ask. Re-runnable: this is the SOP instrument. Run it at regular
intervals, read the GAPS it prints, fix the biggest, gate, deploy, push, re-run. The score should
only ever go up.

Matt, 2026-07-25: "Look for the biggest gaps... still falling short in real life use... we should
continuously improve and refine our processes and methodology."

Grading is STRUCTURAL and conservative (no LLM): each case declares the kind of answer a useful reply
carries — a computed value, a verdict, a resolved verse, a fitting definition, or a clearly on-topic
top result. A reply that falls to bare web/keyword-search with an off-topic top card is a GAP. This
under-counts partial wins on purpose: we want the failures loud.

    PYTHONPATH=src python tools/probe_usefulness.py            # local (ask.respond), fast
    PYTHONPATH=src python tools/probe_usefulness.py --live     # against https://narrowhighway.com
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# (question, signal) — signal is what a USEFUL answer must carry:
#   compute  → a computed number in the message                (arithmetic, conversion, percentages)
#   verdict  → a verify verdict HOLDS/BROKEN                    (checkable claims)
#   verse    → a resolved Scripture verse                       (Bible)
#   define   → a fitting definition whose top hit names the term(word/term meaning)
#   fact     → a direct factual answer (message or on-topic top)(almanac / science / history facts)
#   pastoral → a gentle word + real people                      (first-person struggle)
BATTERY = [
    # — computation (pure, deterministic, high-frequency) —
    ("what is 15 percent of 240", "compute"),
    ("what is the square root of 144", "compute"),
    ("what is 8 times 7", "compute"),
    ("convert 10 miles to kilometers", "compute"),
    ("how many ounces in a pound", "compute"),
    ("what is 100 fahrenheit in celsius", "compute"),
    # — checkable claims —
    ("is 17 a prime number", "verdict"),
    ("is 91 prime", "verdict"),
    ("2+2=4", "verdict"),
    # — Scripture —
    ("John 3:16", "verse"),
    ("what does Psalm 23 say", "verse"),
    # — word / term meaning —
    ("what does agape mean", "define"),
    ("define grace", "define"),
    # — facts (almanac / science / history) —
    ("what is the boiling point of water", "fact"),
    ("how far away is the moon", "fact"),
    ("what is the speed of light", "fact"),
    ("what is the chemical formula for water", "fact"),
    ("who wrote the book of Romans", "fact"),
    ("how many books are in the bible", "fact"),
    ("when did World War 2 end", "fact"),
    # — pastoral —
    ("I feel like I have failed everyone", "pastoral"),
]


def _ask_local(q):
    from concordance import ask
    from concordance.config import EngineConfig
    # gate_open=True mirrors the real seeker experience (and the live .com, which flows Scripture);
    # usefulness is about the answer, not the gate.
    return ask.respond(q, EngineConfig(), gate_open=True)


def _ask_live(q):
    req = urllib.request.Request("https://narrowhighway.com/ask",
                                 data=json.dumps({"text": q}).encode(),
                                 headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


_NUM = re.compile(r"\d")


def _grade(q, sig, d):
    msg = (d.get("message") or "")
    results = d.get("results") or []
    top = (results[0].get("title", "") if results else "").lower()
    terms = [w for w in re.findall(r"[a-z]{4,}", q.lower())
             if w not in ("what", "does", "mean", "define", "many", "much", "book", "wrote", "when")]
    if sig == "compute":
        return "=" in msg and bool(_NUM.search(msg))
    if sig == "verdict":
        return bool((d.get("verify") or {}).get("verdict"))
    if sig == "verse":
        return bool(d.get("scripture"))
    if sig == "define":
        return d.get("kind") == "define" and bool(results) and any(t in top for t in terms[:1])
    if sig == "fact":
        # a direct message, OR an on-topic top result (a distinctive query word appears in the title)
        if msg and _NUM.search(msg):
            return True
        return bool(results) and any(t in top for t in terms)
    if sig == "pastoral":
        return d.get("kind") in ("comfort", "crisis") and bool(d.get("real_help") or d.get("scripture"))
    return False


def main() -> int:
    live = "--live" in sys.argv
    ask = _ask_live if live else _ask_local
    print(f"Usefulness probe — {'LIVE' if live else 'local'} · {len(BATTERY)} real questions\n")
    passed, gaps = 0, []
    by_sig = {}
    for q, sig in BATTERY:
        try:
            d = ask(q)
            ok = _grade(q, sig, d)
        except Exception as e:  # noqa: BLE001
            ok, d = False, {"kind": f"ERROR:{type(e).__name__}"}
        by_sig.setdefault(sig, [0, 0])
        by_sig[sig][1] += 1
        if ok:
            passed += 1
            by_sig[sig][0] += 1
        else:
            gaps.append((sig, q, d.get("kind")))
        print(f"  {'ok  ' if ok else 'GAP '}  [{sig:8}] {q}")
    n = len(BATTERY)
    print(f"\nSCORE: {passed}/{n}  ({100*passed//n}% useful)")
    print("by category: " + " · ".join(f"{k} {v[0]}/{v[1]}" for k, v in sorted(by_sig.items())))
    if gaps:
        print("\nBIGGEST GAPS (fix these next):")
        for sig, q, kind in gaps:
            print(f"  [{sig:8}] {q!r}  → routed to {kind!r}")
    return 0 if not gaps else 1


if __name__ == "__main__":
    sys.exit(main())
