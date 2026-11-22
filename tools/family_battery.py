#!/usr/bin/env python3
"""THE FAMILY BATTERY, RUN — grade eval/family_questions.json against a live face.

    python tools/family_battery.py                         # the .com face
    python tools/family_battery.py --base https://narrowhighway.org
    python tools/family_battery.py --limit 10 --out eval/RESULTS_FAMILY.md

WHAT IT REPORTS, AND WHY THREE NUMBERS AND NOT ONE. A floor can always trade one outcome for another,
so a single score hides the thing we are hunting:

    PASS          the leading source sits on a shelf the battery named
    MISRETRIEVAL  a leader on a shelf nobody named — a confident irrelevant hit, the real defect
    GAP           nothing served. NOT a defect: a want. Several shelves a family needs are nearly
                  empty (survival 24 cards, sanitation 24, practical 3,058 against dictionary 149,490),
                  so a large GAP count is a statement about the KEEPING, not about retrieval.

★ THE KNOWN WEAKNESS OF A SHELF LABEL, STATED UP FRONT. A shelf is coarse. Live 2026-11-21: "the
woodstove is smoking back into the room" was led by a MEAT-CURING card whose shelf is `practical` —
and `practical` is one of that row's named shelves, so the shelf test scores it PASS. A shelf label
catches a reference-shelf collision (a pronunciation card answering a wound) and CANNOT catch a
within-shelf one. So this runner prints the LEAD TITLE on every row and marks PASS rows with
`?` for a human read. Treat PASS as an upper bound, never as proof the answer was right.

A probe never writes: GET/POST to a read door only, no seals, nothing minted.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BATTERY = os.path.join(HERE, "eval", "family_questions.json")


def ask(base, q, timeout=90):
    req = urllib.request.Request(
        base.rstrip("/") + "/ask", data=json.dumps({"text": q}).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def ask_retry(base, q):
    """Only a TIMEOUT may be re-run; any other red stays red."""
    try:
        return ask(base, q), None
    except (urllib.error.URLError, TimeoutError) as e:
        reason = getattr(e, "reason", e)
        if isinstance(reason, TimeoutError) or "timed out" in str(reason).lower():
            try:
                return ask(base, q), "retried after timeout"
            except Exception as e2:  # noqa: BLE001
                return None, "timeout twice: %s" % e2
        return None, "error: %s" % reason
    except Exception as e:  # noqa: BLE001
        return None, "error: %s" % e


def served_shelf(d):
    """The shelf of the LEADING source, wherever this lane puts it. /ask has several shapes:
    a card lead (`lead`), a face answer carrying scripture refs (`scripture_refs`), a crisis
    response (no source at all), and a `web` punt (nothing from the keeping)."""
    lead = d.get("lead")
    if isinstance(lead, dict) and lead.get("shelf"):
        return str(lead["shelf"]), str(lead.get("title") or "")
    for key in ("scripture_refs", "results"):
        v = d.get(key)
        if isinstance(v, list) and v and isinstance(v[0], dict) and v[0].get("shelf"):
            return str(v[0]["shelf"]), str(v[0].get("title") or "")
    return None, ""


def classify(row, d):
    """-> (outcome, shelf, title, detail). Outcomes: PASS / MISRETRIEVAL / GAP / FAIL."""
    kind = str(d.get("kind") or "")
    shelf, title = served_shelf(d)
    expect = row["expect"]

    if expect == "crisis":
        ok = (kind == "crisis") and not shelf
        return ("PASS" if ok else "FAIL"), shelf, title, (
            "help first, nothing retrieved" if ok else "kind=%s shelf=%s — a card served to a cry for help" % (kind, shelf))

    if expect == "miss":
        if kind == "crisis":
            return "FAIL", shelf, title, "crisis on a non-crisis row"
        ok = not shelf
        return ("PASS" if ok else "FAIL"), shelf, title, (
            "honest miss (kind=%s)" % kind if ok else "served a source for something it cannot know")

    # expect == shelf_in
    if kind == "crisis":
        return "FAIL", shelf, title, "crisis false positive on an ordinary question"
    if not shelf:
        return "GAP", None, "", "nothing served (kind=%s) — a want, not a defect" % (kind or "?")
    if shelf in (row.get("shelf_in") or []):
        return "PASS", shelf, title, "on a named shelf — CHECK THE TITLE, a shelf is coarse"
    return "MISRETRIEVAL", shelf, title, "shelf %r is not among %s" % (shelf, row.get("shelf_in"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://narrowhighway.com")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="")
    ap.add_argument("--json", default="")
    a = ap.parse_args()

    with open(BATTERY, encoding="utf-8") as f:
        bat = json.load(f)
    rows = bat["questions"]
    if a.limit:
        rows = rows[:a.limit]

    print("THE FAMILY BATTERY — %d questions against %s" % (len(rows), a.base))
    print("(PASS is an UPPER BOUND: a shelf is coarse and cannot catch a within-shelf collision)\n")
    out = []
    t0 = time.time()
    for i, row in enumerate(rows, 1):
        d, err = ask_retry(a.base, row["q"])
        if d is None:
            outcome, shelf, title, detail = "FAIL", None, "", err
            kind = "?"
        else:
            outcome, shelf, title, detail = classify(row, d)
            kind = str(d.get("kind") or "")
            if err:
                detail += " (%s)" % err
        out.append({"q": row["q"], "kind_asked": row["kind"], "expect": row["expect"],
                    "shelf_in": row.get("shelf_in") or [], "served_kind": kind,
                    "served_shelf": shelf, "lead_title": title[:120],
                    "outcome": outcome, "detail": detail})
        print("%3d %-13s %-13s %-16s %s" % (
            i, outcome, row["kind"], (shelf or "-"), row["q"][:46]))
        if title:
            print("      lead: %s" % title[:96])
    secs = time.time() - t0

    tally = {}
    for r in out:
        tally[r["outcome"]] = tally.get(r["outcome"], 0) + 1
    print("\n%s" % ("-" * 74))
    print("%d questions in %.0fs against %s" % (len(out), secs, a.base))
    for k in ("PASS", "MISRETRIEVAL", "GAP", "FAIL"):
        if k in tally:
            print("  %-13s %3d  (%.0f%%)" % (k, tally[k], 100.0 * tally[k] / len(out)))
    # the three that matter, split by what was asked
    print("\nby kind asked:")
    kinds = sorted({r["kind_asked"] for r in out})
    print("  %-14s %6s %6s %6s %6s" % ("kind", "PASS", "MISRET", "GAP", "FAIL"))
    for k in kinds:
        sub = [r for r in out if r["kind_asked"] == k]
        c = lambda n: sum(1 for r in sub if r["outcome"] == n)  # noqa: E731
        print("  %-14s %6d %6d %6d %6d" % (k, c("PASS"), c("MISRETRIEVAL"), c("GAP"), c("FAIL")))
    print("\nMISRETRIEVALS — the defect this battery exists to count:")
    for r in out:
        if r["outcome"] == "MISRETRIEVAL":
            print("  %s\n      -> [%s] %s" % (r["q"], r["served_shelf"], r["lead_title"][:80]))
    print("\nFAILS — crisis or fabrication:")
    for r in out:
        if r["outcome"] == "FAIL":
            print("  %s\n      -> %s" % (r["q"], r["detail"]))

    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({"base": a.base, "secs": secs, "tally": tally, "rows": out}, f,
                      ensure_ascii=False, indent=1)
        print("\nwrote %s" % a.json)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write("# The family battery — %d questions against %s\n\n" % (len(out), a.base))
            f.write("PASS is an **upper bound**: a shelf is coarse and cannot catch a within-shelf\n"
                    "collision (live: a meat-curing card, shelf `practical`, led a woodstove question).\n"
                    "Read the lead titles.\n\n")
            for k in ("PASS", "MISRETRIEVAL", "GAP", "FAIL"):
                if k in tally:
                    f.write("- **%s** %d\n" % (k, tally[k]))
            f.write("\n| # | outcome | asked | served shelf | question | lead |\n|---|---|---|---|---|---|\n")
            for i, r in enumerate(out, 1):
                f.write("| %d | **%s** | %s | %s | %s | %s |\n" % (
                    i, r["outcome"], r["kind_asked"], r["served_shelf"] or "—",
                    r["q"].replace("|", "/"), r["lead_title"].replace("|", "/")[:70]))
        print("wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
