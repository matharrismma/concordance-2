#!/usr/bin/env python3
"""THE WATCHMAN — walk the live doors the way a person does, and say plainly what is wrong.

    python tools/watch.py                          # the live surfaces
    python tools/watch.py --host https://narrowhighway.org
    python tools/watch.py --json data/watch.json   # write the record (the timer does this)

WHY THIS EXISTS, and why it is not more tests. On 2026-08-01 six real defects were found in one
day. The gate was green through every one of them. The suite had 1,000+ passing tests, the moat
was 60/60, and the box was serving 500s to every caller of /verify.

    every /verify answering 500 for over an hour       (a file-handle leak)
    a 200-byte request buying 1.67 MB and 5.1s of CPU  (no ceiling on `limit`)
    "what is Mahavira" answering with Marcus Aurelius  (stopwords matched)
    /search deaf while /ask acquired the same thing    (two doors, one capability)
    an agent minting into the shared keeping unseen    (a hardcoded lifecycle_stage)
    3 cards held for review that no human could see    (a boundary with no door)

EVERY ONE was invisible to static inspection and obvious the moment the system was DRIVEN END TO
END. That is the whole thesis of this file: the tests prove the code does what it was told; this
asks whether the LIBRARY still behaves — over a real socket, as a reader and as an agent.

THREE STATES, NEVER TWO. A check that cannot run is not a check that passed:

    HOLDS         the invariant is true right now
    BROKEN        it is false — a defect, and the exit code says so
    CANNOT_CHECK  we could not tell (offline, timeout, no token). NOT a pass, NOT a failure.

EVERY CHECK NAMES THE DEFECT IT EXISTS FOR, with its date. A watchman that reports "check 7
failed" teaches nothing at 3am; one that says "reading knocked out proving — the 2026-08-01 handle
leak" points straight at the cause and the fix.

AND IT REFUSES TO REPORT OVER A SUBSET. If a check raises, the run says so and exits 2 rather than
printing a tidy table — because the assay that ran 1 probe of 1,000 and printed a confident verdict
did exactly that, and was believed.

Static/store drift (shards vs the file, receipts vs the CAS, sitemap vs the pages) is
`tools/divergence.py`, which runs where the data lives. This is the wire.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, List

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

HOLDS, BROKEN, CANNOT = "HOLDS", "BROKEN", "CANNOT_CHECK"
TIMEOUT = 60

# A term no archive holds and no card mentions — so a miss stays a miss. Deliberately nonsense:
# a real word would eventually be acquired and the check would rot into a false alarm.
NONSENSE = "zzqx-vorpal-thrimble"


def _get(host: str, path: str, timeout: int = TIMEOUT):
    try:
        with urllib.request.urlopen(host.rstrip("/") + path, timeout=timeout) as r:
            raw = r.read()
            return r.status, json.loads(raw.decode("utf-8", "replace")), len(raw)
    except urllib.error.HTTPError as e:
        return e.code, None, 0
    except Exception as e:  # noqa: BLE001
        return 0, {"__err__": f"{type(e).__name__}: {e}"}, 0


def _post(host: str, path: str, payload: dict, timeout: int = TIMEOUT):
    req = urllib.request.Request(host.rstrip("/") + path,
                                 data=json.dumps(payload).encode("utf-8"),
                                 headers={"content-type": "application/json",
                                          "accept": "application/json, text/event-stream"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
            body = raw.split("data: ")[-1] if "data: " in raw else raw
            return r.status, json.loads(body), len(raw)
    except urllib.error.HTTPError as e:
        return e.code, None, 0
    except Exception as e:  # noqa: BLE001
        return 0, {"__err__": f"{type(e).__name__}: {e}"}, 0


def _tool(host: str, name: str, args: dict):
    code, body, _ = _post(host, "/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                         "params": {"name": name, "arguments": args}})
    if code != 200 or not isinstance(body, dict):
        return code, None
    try:
        return code, json.loads(body["result"]["content"][0]["text"])
    except Exception:  # noqa: BLE001
        return code, None


# ── the checks. each one is a defect that actually happened. ────────────────────────────────────

def check_the_front_door_answers(host: str) -> dict:
    """The floor under every other check: if /health does not answer, nothing below means anything.

    Also the cheapest catch for a deploy that restarted into a broken state — the warm-up window
    after `tools/deploy.sh` is real, and a service that never finished warming has looked exactly
    like a healthy one from the outside more than once.
    """
    code, body, _ = _get(host, "/health")
    if code != 200 or not isinstance(body, dict):
        return {"state": BROKEN, "detail": f"/health answered {code}"}
    return {"state": HOLDS, "detail": f"version {body.get('version')}, surface {body.get('surface')}"}


def check_proving_still_works(host: str) -> dict:
    """2026-08-01: every POST /verify answered 500 for over an hour. Not because verification
    broke — because a handle leak meant Python could not open receipts.py to import it."""
    code, body, _ = _post(host, "/verify", {"mode": "equality", "params": {
        "expr_a": "1+1", "expr_b": "2", "variables": {}}})
    if code != 200 or not isinstance(body, dict):
        return {"state": BROKEN, "detail": f"/verify answered {code} — the engine cannot prove"}
    if body.get("verdict") != "HOLDS":
        return {"state": BROKEN, "detail": f"1+1=2 returned {body.get('verdict')!r}"}
    return {"state": HOLDS, "detail": "1+1=2 HOLDS"}


def check_handles_are_not_accumulating(host: str) -> dict:
    """THE LEAK ITSELF, not its symptom. Thread-per-connection x connection-per-thread-per-shard
    with nothing closing one: ~1020 handles per 81 minutes of ordinary traffic, then EMFILE."""
    code, body, _ = _get(host, "/health")
    if code != 200 or not isinstance(body, dict):
        return {"state": CANNOT, "detail": "/health did not answer"}
    sh = body.get("shards")
    if not isinstance(sh, dict) or "open" not in sh:
        return {"state": BROKEN, "detail": "/health no longer reports shard handles — the leak "
                                           "would be invisible again"}
    open_now, peak = int(sh.get("open", 0)), int(sh.get("peak", 0))
    if open_now > 200:
        return {"state": BROKEN, "detail": f"{open_now} shard handles open (peak {peak}) — "
                                           f"climbing toward the 2026-08-01 outage"}
    return {"state": HOLDS, "detail": f"open {open_now}, peak {peak}, "
                                      f"lifetime {sh.get('opened_total')}"}


def check_a_miss_stays_a_miss(host: str) -> dict:
    """2026-08-01: `what is Mahavira` returned Marcus Aurelius, because the matcher ORed every
    token including "what" and "is". A gap rendered as an answer, and the want never recorded."""
    code, body, _ = _get(host, "/search?q=what+is+" + NONSENSE)
    if code != 200 or not isinstance(body, dict):
        return {"state": CANNOT, "detail": f"/search answered {code}"}
    if body.get("count"):
        titles = [c.get("title") for c in (body.get("results") or [])[:2]]
        return {"state": BROKEN, "detail": f"a nonsense question returned {body['count']} "
                                           f"result(s): {titles} — junk is being served as an answer"}
    return {"state": HOLDS, "detail": "a question about nothing returns nothing"}


def check_the_ceiling_is_announced(host: str) -> dict:
    """2026-08-01: limit=10^9 returned 1.67 MB in 5.1s for a 200-byte request. Capped at 200 —
    and a cap that does not report itself reads as 'that was all of them'."""
    code, body, size = _get(host, "/search?q=grace&limit=1000000000")
    if code != 200 or not isinstance(body, dict):
        return {"state": CANNOT, "detail": f"/search answered {code}"}
    n = len(body.get("results") or [])
    if n > 200:
        return {"state": BROKEN, "detail": f"no ceiling: {n} results, {size:,} bytes"}
    if not body.get("limit_capped"):
        return {"state": BROKEN, "detail": "capped silently — the caller is not told"}
    return {"state": HOLDS, "detail": f"{n} results, capped and announced ({size:,} bytes)"}


def check_both_doors_expand(host: str) -> dict:
    """2026-08-01: /ask ran the tortoise and /search did not, so the same question got two
    different answers — and the deaf door was the one agents use."""
    code, body, _ = _get(host, "/search?q=" + NONSENSE, timeout=90)
    if code != 200 or not isinstance(body, dict):
        return {"state": CANNOT, "detail": f"/search answered {code}"}
    ex = body.get("expanded")
    if not isinstance(ex, dict):
        return {"state": BROKEN, "detail": "a miss on /search did not reach the slow lane at all "
                                           "— no `expanded` in the answer"}
    if ex.get("status") not in ("acquired", "nothing_found", "queued"):
        return {"state": BROKEN, "detail": f"unknown expansion status {ex.get('status')!r}"}
    return {"state": HOLDS, "detail": f"the slow lane ran and said {ex.get('status')!r}"}


def check_the_agent_plane_withholds(host: str) -> dict:
    """2026-08-01: lifecycle_stage was hardcoded "public", so an agent's acquisition entered the
    shared keeping with no human ever seeing it — against the covenant's "ask before writes".

    THE FIRST VERSION OF THIS CHECK PASSED VACUOUSLY, which is worth recording because it is the
    exact fault this whole file is against. It searched a nonsense term, got `nothing_found` (as it
    always would), never reached the branch that tests withholding, and reported `ok` anyway — a
    green light over a path it had not touched.

    So it now tests the invariant against what is ACTUALLY HELD: take a card the review desk says
    is waiting, and confirm the public surface does not serve it. If nothing is held there is
    nothing to prove, and that is CANNOT_CHECK — not a pass.
    """
    code, body, _ = _get(host, "/curate/queue")
    if code != 200 or not isinstance(body, dict):
        return {"state": CANNOT, "detail": "the review desk did not answer"}
    held = [i for i in (body.get("items") or []) if i.get("kind") == "acquisition"]
    if not held:
        return {"state": CANNOT, "detail": "nothing is held right now — the withholding cannot be "
                                           "observed, so this is not a pass"}
    cid = held[0].get("card_id")
    code, card, _ = _get(host, "/card?id=" + str(cid))
    if code == 200 and isinstance(card, dict):
        c = card.get("card") if isinstance(card.get("card"), dict) else card
        if (c or {}).get("id") == cid and (c or {}).get("lifecycle_stage") not in (
                "public_review", None):
            return {"state": BROKEN, "detail": f"{cid} is on the review desk but the public card "
                                               f"door serves it as {c.get('lifecycle_stage')!r}"}
        if (c or {}).get("id") == cid:
            return {"state": BROKEN, "detail": f"{cid} is awaiting review and the public card door "
                                               f"serves it anyway"}
    return {"state": HOLDS, "detail": f"{len(held)} held; {cid} is not served publicly"}


def check_the_review_desk_is_reachable(host: str) -> dict:
    """2026-08-01: three acquisitions sat in public_review and /curate/queue reported zero. A hold
    with no door is a grave, not a wait."""
    code, body, _ = _get(host, "/curate/queue")
    if code != 200 or not isinstance(body, dict) or "items" not in body:
        return {"state": BROKEN, "detail": f"/curate/queue answered {code} — nobody can see what "
                                           f"is waiting"}
    n = int(body.get("count") or 0)
    kinds = {}
    for i in body.get("items") or []:
        kinds[i.get("kind") or "?"] = kinds.get(i.get("kind") or "?", 0) + 1
    return {"state": HOLDS, "detail": f"{n} waiting {kinds or ''}".strip()}


def check_no_tool_advertises_a_private_key(host: str) -> dict:
    """The sovereignty promise, in the one place an agent LEARNS from: a tool schema is
    documentation agents imitate. Resolved 2026-07-28; this keeps it resolved."""
    code, body, _ = _post(host, "/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    if code != 200 or not isinstance(body, dict):
        return {"state": CANNOT, "detail": f"tools/list answered {code}"}
    tools = ((body.get("result") or {}).get("tools")) or []
    bad = [t.get("name") for t in tools if "private_key" in json.dumps(t)]
    if bad:
        return {"state": BROKEN, "detail": f"{len(bad)} tool schema(s) advertise a private key: {bad}"}
    return {"state": HOLDS, "detail": f"{len(tools)} tools, none asking for a key"}


def check_the_door_does_not_500_on_nonsense(host: str) -> dict:
    """Our fault must not surface as the caller's problem. Four malformed shapes, one request each."""
    shapes = [("not json", "this is not json"),
              ("no method", json.dumps({"jsonrpc": "2.0", "id": 1})),
              ("unknown tool", json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                           "params": {"name": "nope", "arguments": {}}})),
              ("bad arg type", json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                           "params": {"name": "search",
                                                      "arguments": {"query": "x", "limit": "many"}}}))]
    bad = []
    for label, raw in shapes:
        req = urllib.request.Request(host.rstrip("/") + "/mcp", data=raw.encode(),
                                     headers={"content-type": "application/json",
                                              "accept": "application/json, text/event-stream"},
                                     method="POST")
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                if r.status >= 500:
                    bad.append(f"{label}->{r.status}")
        except urllib.error.HTTPError as e:
            if e.code >= 500:
                bad.append(f"{label}->{e.code}")
        except Exception as e:  # noqa: BLE001
            bad.append(f"{label}->{type(e).__name__}")
    if bad:
        return {"state": BROKEN, "detail": "the door failed on malformed input: " + ", ".join(bad)}
    return {"state": HOLDS, "detail": f"{len(shapes)} malformed shapes, no 5xx"}


CHECKS: List[Callable[[str], dict]] = [
    check_the_front_door_answers,
    check_proving_still_works,
    check_handles_are_not_accumulating,
    check_a_miss_stays_a_miss,
    check_the_ceiling_is_announced,
    check_both_doors_expand,
    check_the_agent_plane_withholds,
    check_the_review_desk_is_reachable,
    check_no_tool_advertises_a_private_key,
    check_the_door_does_not_500_on_nonsense,
]


def watch(host: str) -> Dict[str, Any]:
    results, crashed = [], []
    for fn in CHECKS:
        t0 = time.time()
        try:
            r = fn(host)
        except Exception as e:  # noqa: BLE001 — a crashed check is a hole in the coverage
            crashed.append(f"{fn.__name__}: {type(e).__name__}: {e}")
            continue
        r["check"] = fn.__name__.removeprefix("check_").replace("_", " ")
        r["secs"] = round(time.time() - t0, 2)
        results.append(r)
    counts = {s: sum(1 for r in results if r["state"] == s) for s in (HOLDS, BROKEN, CANNOT)}
    return {"host": host, "at": int(time.time()), "ran": len(results), "planned": len(CHECKS),
            "crashed": crashed, "counts": counts, "checks": results}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="https://narrowhighway.com")
    ap.add_argument("--json", default="", help="write the record here (and append to history)")
    args = ap.parse_args()

    print(f"THE WATCHMAN — {args.host}")
    print(f"  {len(CHECKS)} live checks, each one a defect that actually happened\n")
    rep = watch(args.host)

    # THE COVERAGE GATE, on the watchman itself. A tidy table over a subset is worse than nothing.
    if rep["crashed"]:
        print(f"REFUSING TO REPORT — {rep['ran']} of {rep['planned']} checks ran, "
              f"{len(rep['crashed'])} crashed:")
        for c in rep["crashed"]:
            print(f"    {c}")
        return 2

    width = max(len(r["check"]) for r in rep["checks"])
    for r in rep["checks"]:
        mark = {HOLDS: "  ok  ", BROKEN: " BROKEN", CANNOT: "  ??  "}[r["state"]]
        print(f"  {mark}  {r['check']:<{width}}  {r['detail']}")

    c = rep["counts"]
    print(f"\n  {c[HOLDS]} hold · {c[BROKEN]} broken · {c[CANNOT]} could not be checked "
          f"({rep['ran']}/{rep['planned']} ran)")

    if args.json:
        p = args.json
        os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, ensure_ascii=False, indent=1)
        # One line per run, so DRIFT is visible over time rather than only the latest snapshot.
        with open(os.path.join(os.path.dirname(p) or ".", "watch_history.jsonl"), "a",
                  encoding="utf-8") as fh:
            fh.write(json.dumps({"at": rep["at"], "host": rep["host"], **rep["counts"],
                                 "broken": [r["check"] for r in rep["checks"]
                                            if r["state"] == BROKEN]}, ensure_ascii=False) + "\n")
        print(f"  record -> {p}")

    # CANNOT_CHECK is not a failure. Only a broken invariant is.
    return 1 if c[BROKEN] else 0


if __name__ == "__main__":
    sys.exit(main())
