#!/usr/bin/env python3
"""CALIBRATION — measure the engine against a known standard, and report the OFFSET in both
directions. Never a grade.

    python tools/calibrate.py                       # against the live secular surface
    python tools/calibrate.py --host https://narrowhighway.org
    python tools/calibrate.py --json data/calibration.json

WHAT CALIBRATION IS, AS DISTINCT FROM THE OTHER THREE INSTRUMENTS. We already ask three questions
and this is the fourth, which none of them answer:

    tools/check.py       does the code do what it was told?          (the gate)
    tools/divergence.py  do the stores still agree with each other?  (drift, at rest)
    tools/watch.py       is the library still behaving on the wire?  (liveness)
    tools/calibrate.py   is it still TRUE, and by how much is it off?

`tools/benchmark.py` has always been calibration — 60 ground-truth math claims, false positives
must be zero — but it calibrates ONLY the derivation verifiers. Everything else the engine asserts
(what it holds, where a verse is, what a word means, what authority a card carries) had no standard
to be measured against. That is precisely why 2026-08-01's defects passed a green gate: search
returning junk for "what is Mahavira" is not a code failure, it is a CALIBRATION failure, and
nothing was measuring it.

THE NULL TEST IS WHAT MAKES IT HONEST (Matt, on the tune as a heuristic: "consonance says where to
look; the null test makes it honest"). An instrument that only ever confirms is not measuring — it
is agreeing. So half of this standard is DECOYS: claims that must NOT be confirmed, references that
must NOT resolve, queries that must NOT return. A false positive here is the critical number, the
same as in the moat: it means we asserted something untrue, and a library that does that has failed
at the one thing it is for.

FOUR OUTCOMES, and the two failures are not the same failure:

    TRUE_POSITIVE   we hold it / it is so, and we said so
    TRUE_NEGATIVE   it is not so, and we declined       <- the null test
    FALSE_POSITIVE  WE ASSERTED SOMETHING UNTRUE        <- critical; must be 0
    FALSE_NEGATIVE  it is so and we missed it           <- honest, recorded, not hidden

A false negative is a gap in the keeping and is allowed to exist. A false positive is a lie and is
not. Reporting one number over both would hide exactly the distinction that matters.

COVERAGE BEFORE VERDICT: how many reference points, in which dimensions, and how many actually
reached the engine. A rate over an unknown denominator is not a measurement.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from typing import Any, Dict, List

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

TP, TN, FP, FN, CANNOT = "TRUE_POS", "TRUE_NEG", "FALSE_POS", "FALSE_NEG", "CANNOT_CHECK"
TIMEOUT = 45

# ── THE STANDARD ────────────────────────────────────────────────────────────────────────────────
# Every reference point is objectively checkable by someone with a Bible, a lexicon, or arithmetic.
# `truth` is what must be so. Decoys carry truth=False and are the null test.

SCRIPTURE = [
    # (query, must_resolve_to or None for a decoy)
    ("John 3:16", "John 3:16"),
    ("1 John 3:16", "1 John 3:16"),          # the classic collision — must NOT fold into John
    ("Philemon 6", "Philemon 1:6"),          # single-chapter book: bare verse is chapter 1
    ("Jude 9", "Jude 1:9"),
    ("Obadiah 1", "Obadiah 1:1"),
    ("Psalm 119:176", "Psalms 119:176"),     # the longest chapter's last verse
    ("Genesis 1:1", "Genesis 1:1"),
    ("Revelation 22:21", "Revelation 22:21"),
    ("2 Kings 25:30", "2 Kings 25:30"),
    ("Song of Solomon 1:1", "Song of Solomon 1:1"),
    # THE NULL TEST — these are not references, and must not become one.
    ("Hezekiah 3:16", None),                 # no such book
    ("John 99:1", None),                     # no such chapter
    ("Genesis 1:99", None),                  # no such verse
    ("Second Opinions 4:4", None),
]

# A card we KNOW the keeping holds must be findable by its own title. This is the dimension that
# 2026-08-01's search regressions actually broke, and nothing was measuring it.
RETRIEVAL_SEEDS = ["grace", "Gilgamesh", "Zoroaster", "Baal", "Confucius"]

# Deliberate nonsense: a library that "finds" something for these is agreeing, not retrieving.
RETRIEVAL_DECOYS = ["zzqx vorpal thrimble", "flarn quibbet zolmish", "xyzzy plugh frobnitz"]

MATH = [
    ("1+1", "2", True), ("2*3", "6", True), ("(x+1)**2", "x**2+2*x+1", True),
    ("1+1", "3", False), ("2*3", "7", False), ("(x+1)**2", "x**2+1", False),
]


def _get(host: str, path: str):
    try:
        with urllib.request.urlopen(host.rstrip("/") + path, timeout=TIMEOUT) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:  # noqa: BLE001
        return 0, None


def _post(host: str, path: str, payload: dict):
    req = urllib.request.Request(host.rstrip("/") + path, data=json.dumps(payload).encode(),
                                 headers={"content-type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:  # noqa: BLE001
        return 0, None


def _norm(s: Any) -> str:
    return " ".join(str(s or "").lower().replace(".", "").split())


# ── the dimensions ──────────────────────────────────────────────────────────────────────────────

def calibrate_scripture(host: str) -> List[dict]:
    """A reference resolves where it actually is, or not at all. Objectively checkable."""
    out = []
    for query, expect in SCRIPTURE:
        code, body = _get(host, "/resolve?ref=" + urllib.parse.quote(query))
        rec = {"dimension": "scripture", "probe": query, "expected": expect}
        if code == 0 or not isinstance(body, dict):
            rec["outcome"] = CANNOT
            out.append(rec)
            continue

        # READ THE VERDICT, NOT THE ECHO. `ref` is the caller's own string handed back; the
        # answer is `status` ("ok" | "not_found") with `detail` saying why. The first version of
        # this check read `ref`, found the input reflected in it, and reported SEVEN false
        # positives — four of which were the engine correctly refusing "Hezekiah 3:16" and
        # friends with a precise reason. An instrument that mistakes an echo for an answer
        # accuses the thing it is measuring. Verify the instrument before reporting the defect.
        status = str(body.get("status") or "")
        resolved = status == "ok"
        text = str(body.get("text") or "")
        detail = str(body.get("detail") or "")

        if expect is None:                       # NULL TEST: it must DECLINE, and say why
            rec["got"] = f"{status} — {detail}" if detail else status
            if resolved:
                rec["outcome"] = FP
            elif not detail:
                # Declining is right, but a refusal that names nothing teaches nothing.
                rec["outcome"] = TN
                rec["got"] = "declined, but gave no reason"
            else:
                rec["outcome"] = TN
        elif not resolved:
            rec["got"] = f"{status} — {detail}"
            rec["outcome"] = FN                  # a real reference we cannot reach
        elif not text.strip():
            rec["got"] = "status ok but no text"
            rec["outcome"] = FP                  # claiming to resolve while handing over nothing
        else:
            rec["got"] = f"ok — {text[:48]}…"
            rec["outcome"] = TP
        out.append(rec)
    return out


def calibrate_retrieval(host: str) -> List[dict]:
    """What the keeping holds must be findable BY ITS OWN TITLE; nonsense must return nothing.

    The second half is the null test, and it is the half that would have caught the 2026-08-01
    stopword bug on the day it shipped: "what is <nonsense>" returning Marcus Aurelius is a false
    positive against a standard, not a crash anyone could have seen in a log.
    """
    out = []
    for seed in RETRIEVAL_SEEDS:
        code, body = _get(host, "/search?q=" + urllib.parse.quote(seed) + "&limit=3")
        rec = {"dimension": "retrieval", "probe": seed, "expected": "a card whose text says so"}
        if code != 200 or not isinstance(body, dict):
            rec["outcome"] = CANNOT
            out.append(rec)
            continue
        results = body.get("results") or []
        hay = " ".join(f"{c.get('title','')} {c.get('snippet','')}" for c in results).lower()
        rec["got"] = f"{len(results)} result(s)"
        if not results:
            rec["outcome"] = FN                  # we may genuinely not hold it — a gap, not a lie
        elif seed.split()[0].lower() in hay:
            rec["outcome"] = TP
        else:
            rec["outcome"] = FP                  # answered with something that never mentions it
            rec["got"] = "results mention none of it: " + \
                         ", ".join(str(c.get("title"))[:34] for c in results[:2])
        out.append(rec)

    for decoy in RETRIEVAL_DECOYS:               # THE NULL TEST
        code, body = _get(host, "/search?q=" + urllib.parse.quote(decoy) + "&limit=3")
        rec = {"dimension": "retrieval-null", "probe": decoy, "expected": "nothing"}
        if code != 200 or not isinstance(body, dict):
            rec["outcome"] = CANNOT
            out.append(rec)
            continue
        n = len(body.get("results") or [])
        rec["got"] = f"{n} result(s)"
        rec["outcome"] = TN if n == 0 else FP
        out.append(rec)
    return out


def calibrate_math(host: str) -> List[dict]:
    """The moat's discipline, over the wire: a false claim must never come back HOLDS."""
    out = []
    for a, b, truth in MATH:
        code, body = _post(host, "/verify", {"mode": "equality", "params": {
            "expr_a": a, "expr_b": b, "variables": {}}})
        rec = {"dimension": "math", "probe": f"{a} == {b}", "expected": "HOLDS" if truth else "not HOLDS"}
        if code != 200 or not isinstance(body, dict):
            rec["outcome"] = CANNOT
            out.append(rec)
            continue
        verdict = body.get("verdict")
        rec["got"] = verdict
        if truth:
            rec["outcome"] = TP if verdict == "HOLDS" else FN
        else:
            rec["outcome"] = FP if verdict == "HOLDS" else TN
        out.append(rec)
    return out


def calibrate_authority(host: str) -> List[dict]:
    """AUTHORITY IS NEVER SILENTLY UPGRADED — the kernel's fifth clause, measured.

    A card found on the open web is `primary_pd` at best; a member's word stays `member` however
    popular it becomes; only our own sealed work may claim to be verified. A card that reports a
    tier its source cannot support is a false positive of the most damaging kind, because the whole
    promise of this library is that you can tell what a thing IS before you lean on it.
    """
    out = []
    code, body = _get(host, "/search?q=grace&limit=8")
    if code != 200 or not isinstance(body, dict):
        return [{"dimension": "authority", "probe": "tiers on a live result set",
                 "expected": "every card declares an honest tier", "outcome": CANNOT}]
    allowed = {"", "reference", "primary_pd", "member", "external_aligned", "sealed", "verified",
               "primary", "scripture", "lexicon"}
    for c in (body.get("results") or []):
        tier = str(c.get("authority_tier") or "")
        rec = {"dimension": "authority", "probe": str(c.get("id"))[:40],
               "expected": "a declared, known tier", "got": tier or "(none)"}
        if tier and tier not in allowed:
            rec["outcome"] = FP
            rec["got"] = f"undeclared tier {tier!r}"
        elif c.get("generated") and tier in ("sealed", "verified"):
            rec["outcome"] = FP
            rec["got"] = f"generated content claiming {tier!r}"
        else:
            rec["outcome"] = TP
        out.append(rec)
    return out


DIMENSIONS = (calibrate_scripture, calibrate_retrieval, calibrate_math, calibrate_authority)


def run(host: str) -> Dict[str, Any]:
    points, crashed = [], []
    for fn in DIMENSIONS:
        try:
            points.extend(fn(host))
        except Exception as e:  # noqa: BLE001
            crashed.append(f"{fn.__name__}: {type(e).__name__}: {e}")
    counts = defaultdict(int)
    for p in points:
        counts[p["outcome"]] += 1
    return {"host": host, "at": int(time.time()), "points": points,
            "counts": dict(counts), "crashed": crashed}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="https://narrowhighway.com")
    ap.add_argument("--json", default="")
    ap.add_argument("--show", type=int, default=12, help="how many misses to name")
    args = ap.parse_args()

    planned = len(SCRIPTURE) + len(RETRIEVAL_SEEDS) + len(RETRIEVAL_DECOYS) + len(MATH)
    print(f"CALIBRATION — {args.host}")
    print(f"  measuring the engine against a known standard; the null test is "
          f"{len(RETRIEVAL_DECOYS) + sum(1 for _, e in SCRIPTURE if e is None) + 3} of the points\n")

    rep = run(args.host)
    if rep["crashed"]:
        print(f"REFUSING TO REPORT — {len(rep['crashed'])} dimension(s) crashed:")
        for c in rep["crashed"]:
            print(f"    {c}")
        return 2

    n = len(rep["points"])
    c = rep["counts"]
    reached = n - c.get(CANNOT, 0)
    print(f"  coverage: {n} reference points (~{planned} planned), {reached} reached the engine\n")

    by_dim = defaultdict(lambda: defaultdict(int))
    for p in rep["points"]:
        by_dim[p["dimension"]][p["outcome"]] += 1
    print(f"  {'dimension':<18} {'true+':>6} {'true-':>6} {'FALSE+':>7} {'false-':>7} {'??':>4}")
    for dim, d in by_dim.items():
        print(f"  {dim:<18} {d[TP]:>6} {d[TN]:>6} {d[FP]:>7} {d[FN]:>7} {d[CANNOT]:>4}")

    fps = [p for p in rep["points"] if p["outcome"] == FP]
    fns = [p for p in rep["points"] if p["outcome"] == FN]

    print(f"\n  FALSE POSITIVES — we asserted something untrue: {len(fps)}   (this must be 0)")
    for p in fps[:args.show]:
        print(f"     [{p['dimension']}] {p['probe']}")
        print(f"        expected {p['expected']!r}, got {p.get('got')!r}")

    print(f"\n  false negatives — true, and we missed it: {len(fns)}   (a gap, honestly recorded)")
    for p in fns[:args.show]:
        print(f"     [{p['dimension']}] {p['probe']} -> {p.get('got')}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, ensure_ascii=False, indent=1)
        print(f"\n  record -> {args.json}")

    # THE OFFSET, stated as a direction rather than a grade.
    print(f"\n  OFFSET: {len(fps)} toward asserting what is not so, "
          f"{len(fns)} toward missing what is.")
    return 1 if fps else 0


if __name__ == "__main__":
    sys.exit(main())
