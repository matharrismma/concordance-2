"""THE HIVE — one turn of the standing cycle, run by a timer so nobody has to run it.

Matt, 2026-08-02: *"It should continuously improve and refine. It should not require me to keep
building. It should use the inputs from requests, but it should also have a hive acting as worker
bees filling up the corpus. We want some of the hive working to improve the corpus and find the
connections as well."*

WHAT THE MEASUREMENT FOUND (live box, 2026-08-02) -- the reason this file exists:

    nh-gather.timer        -> tools/gather_cycle.py       WorkingDirectory=/home/nh/Lighthouse  (V1)
    nh-daily-reading.timer -> tools/render_daily_reading.py                    /home/nh/Lighthouse
    nh-watch.timer         -> tools/watch.py                            /home/nh/concordance-2
    shepherd_rounds.py     -> scheduled ZERO times
    grow.py                -> scheduled ZERO times
    propose_edges.py       -> scheduled ZERO times

So the corpus WAS growing on its own -- out of the V1 checkout, with code that does not exist in
this repo, is not covered by the gate, and would stop silently if that directory were ever
cleaned. Meanwhile the three workers 2.0 built for exactly this job had never once been run by a
machine. The supply side ran on borrowed code; the demand and refinement sides did not run at all.

THIS FILE ADDS NO WORKER. Every step below is a tool that already existed in this repo and was
simply never wired to a clock. It replaces V1's gather_cycle.py rather than joining it, and it
deliberately does NOT port V1's `suggest_connections.py` or `skill_capacity.py`, because
`propose_edges.py` and `shepherd_rounds.py` already do those jobs here. Consolidate; never stack a
second tool beside a working one.

THE THREE PARTS OF THE HIVE, which is Matt's own division:

  DEMAND   what people actually asked for -- the want list, dug by shepherd_rounds
  SUPPLY   worker bees filling the corpus
  REFINE   improving what is held and FINDING THE CONNECTIONS -- propose_edges, theory_map

Ordered cheapest-and-safest first, so a cycle that dies halfway has still done the free work.

EVERY STEP IS SPEND-GUARDED. tools/spend_guard.py (ported from V1 the same day) holds a hard
monthly ceiling. A step declares a conservative MAXIMUM cost; if that estimate does not fit in
what is left this month, the step is SKIPPED and the reason is printed. Deterministic steps
declare 0.0 and therefore always run -- they cost nothing but CPU.

NOTHING HERE SEALS ANYTHING. propose_edges proposes; a named steward accepts. The hive gathers
and arranges attributed material and stops at the point where judgement begins.

Usage:
    PYTHONPATH=src python tools/hive_cycle.py              # dry run -- print the plan, touch nothing
    PYTHONPATH=src python tools/hive_cycle.py --apply      # do the work
    PYTHONPATH=src python tools/hive_cycle.py --only refine
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "src"))

import spend_guard  # noqa: E402  (tools/ is on the path above)

PYTHON = sys.executable

# key       the --only selector and the ledger source name
# part      DEMAND / SUPPLY / REFINE -- Matt's own division of the hive
# estimate  CONSERVATIVE MAXIMUM dollars. 0.0 means deterministic: no API, always runs.
# argv      a tool THAT ALREADY EXISTS in this repo. Adding a new worker here is a mistake.
STEPS = [
    {
        "key": "watch",
        "part": "REFINE",
        "estimate": 0.0,
        "argv": [PYTHON, "tools/watch.py"],
        "note": "walk the live doors; a broken door outranks any new work",
    },
    {
        "key": "shepherd",
        "part": "DEMAND",
        "estimate": 0.0,
        "argv": [PYTHON, "tools/shepherd_rounds.py"],
        "note": "dig the want list -- what people actually asked for and we did not have",
    },
    {
        "key": "connections",
        "part": "REFINE",
        "estimate": 0.0,
        "argv": [PYTHON, "tools/propose_edges.py"],
        "note": "find connections nobody has drawn yet -> proposals, never sealed edges",
    },
    {
        "key": "theorymap",
        "part": "REFINE",
        "estimate": 0.0,
        "argv": [PYTHON, "tools/theory_map.py"],
        "note": "redraw the floor and re-stamp the catalogue count so it cannot rot",
    },
    {
        "key": "grow",
        "part": "SUPPLY",
        "estimate": 0.0,
        "argv": [PYTHON, "tools/grow.py"],
        "note": "one turn of the standing growth cycle: measure, safe edges, record",
    },
]

VALID_PARTS = ("DEMAND", "SUPPLY", "REFINE")


def _env():
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.join(ROOT, "src") + os.pathsep + env.get("PYTHONPATH", "")
    env.setdefault("NH_REPO_ROOT", ROOT)
    return env


def run_step(step, apply_it):
    """Run one worker if the month's remaining budget covers its declared maximum."""
    key, est = step["key"], float(step["estimate"])
    flag = "NH_HIVE_" + key.upper()
    if os.environ.get(flag, "1").strip() in ("0", "off", "no"):
        print("[hive] %-12s SKIP  disabled by %s" % (key, flag))
        return {"key": key, "status": "disabled"}

    if est > 0 and not spend_guard.can_spend(est):
        print("[hive] %-12s SKIP  est $%.2f exceeds remaining $%.2f this month"
              % (key, est, spend_guard.remaining()))
        return {"key": key, "status": "over_budget", "estimate": est}

    if not apply_it:
        print("[hive] %-12s PLAN  %-9s est $%.2f  %s" % (key, step["part"], est, step["note"]))
        return {"key": key, "status": "planned", "estimate": est}

    started = time.time()
    try:
        proc = subprocess.run(step["argv"], cwd=ROOT, env=_env(),
                              capture_output=True, text=True, timeout=1800)
        rc = proc.returncode
        tail = (proc.stdout or proc.stderr or "").strip().splitlines()
        detail = tail[-1][:110] if tail else ""
    except subprocess.TimeoutExpired:
        rc, detail = 124, "timed out after 1800s"
    except Exception as exc:                                  # noqa: BLE001
        rc, detail = 1, str(exc)[:110]

    took = time.time() - started
    # A FAILING WORKER IS REPORTED, NOT SWALLOWED. The cycle continues so one broken step cannot
    # stop the rest, but the non-zero code travels back to the caller and into the log.
    print("[hive] %-12s %s  %5.1fs  %s"
          % (key, "OK  " if rc == 0 else "FAIL", took, detail))
    if est > 0 and rc == 0:
        spend_guard.record("hive:" + key, est)
    return {"key": key, "status": "ok" if rc == 0 else "failed", "rc": rc, "seconds": round(took, 1)}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true",
                    help="actually run the workers (default is a dry plan)")
    ap.add_argument("--only", default="", help="one part: demand | supply | refine")
    ap.add_argument("--json", action="store_true", help="machine-readable summary")
    args = ap.parse_args()

    want = args.only.strip().upper()
    if want and want not in VALID_PARTS:
        print("--only must be one of: " + ", ".join(p.lower() for p in VALID_PARTS))
        return 2

    steps = [s for s in STEPS if not want or s["part"] == want]
    st = spend_guard._status_dict()
    print("[hive] month %s  spent $%.2f / $%.2f  steps=%d  mode=%s"
          % (st["month"], st["spent_usd"], st["cap_usd"], len(steps),
             "APPLY" if args.apply else "dry-run"))

    results = [run_step(s, args.apply) for s in steps]

    failed = [r for r in results if r.get("status") == "failed"]
    st2 = spend_guard._status_dict()
    print("[hive] done. %d ok, %d failed, %d skipped. month-to-date $%.2f / $%.2f"
          % (sum(1 for r in results if r.get("status") == "ok"), len(failed),
             sum(1 for r in results if r.get("status") in ("over_budget", "disabled")),
             st2["spent_usd"], st2["cap_usd"]))
    if args.json:
        print(json.dumps({"steps": results, "spend": st2}, indent=1))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
