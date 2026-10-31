#!/usr/bin/env python3
"""THE WINNING TICKET — measure, propose, apply, gate, rewind (docs/SOP/PRUNING.md; src/concordance/ticket.py).

Pruning as a MASK over the keeping, by the lottery-ticket procedure carried over to a deterministic engine: a unit's
IMPORTANCE = magnitude × activation in a dated window; the DEAD (never exercised by the gates or real traffic in the
window) are masked p at a time; the 0-FP gates must hold with the mask on; a regression rewinds. Nothing is deleted.

First unit kind instrumented: the faces' routing vocabulary (scope words — the keyword bag the Fable review called
brittle; "dead synonyms = tokenization" is the lesson it enforces). Synonyms, roads and cards follow the same path.

    PYTHONPATH=src python tools/winning_ticket.py measure [--window-days 90] [--extra queries.txt]...
    PYTHONPATH=src python tools/winning_ticket.py propose --p 0.2        # print the proposal, write nothing
    PYTHONPATH=src python tools/winning_ticket.py apply --p 0.2          # write the next mask version (then GATE it)
    PYTHONPATH=src python tools/winning_ticket.py run --p 0.2 --gate-cmd "<cmd>" [--gate-cmd ...]   # the full IMP loop
    PYTHONPATH=src python tools/winning_ticket.py status | rewind

The exercise corpora (ACTIVATION) are the gates' own inputs plus real traffic: data/recall_phrasings.json,
data/frontdoor_claims.json, tools/probe_usefulness.BATTERY, eval/live_probes.jsonl, data/activity.jsonl (events in the
window), and any --extra file (one query per line). Runs on the box (CONCORDANCE_DATA_DIR); `measure`/`propose` are
read-only.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

# NH_ROOT lets the tool run from outside the checkout (a shipped copy under /tmp on the box) against that checkout's
# data/, eval/ and tools/ — appending its src so a package already on PYTHONPATH (the shipped one) wins.
_ROOT_ENV = os.environ.get("NH_ROOT", "").strip()
ROOT = Path(_ROOT_ENV) if _ROOT_ENV else Path(__file__).resolve().parent.parent
if _ROOT_ENV:
    sys.path.append(str(ROOT / "src"))
    sys.path.append(str(ROOT / "tools"))
else:
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT / "tools"))

_TEXT_KEYS = ("text", "q", "query", "claim", "question", "prompt", "input")


def _data_dir() -> Path:
    return Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or str(ROOT / "data"))


def _strings(obj: Any) -> List[str]:
    """Every query-like string in a record: the known keys, else nothing (we never guess at a body)."""
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        out: List[str] = []
        for k in _TEXT_KEYS:
            v = obj.get(k)
            if isinstance(v, str) and v.strip():
                out.append(v)
        body = obj.get("body")                       # a POST probe carries its text in the body (eval/live_probes.jsonl)
        if isinstance(body, dict):
            out.extend(_strings(body))
        return out
    return []


def collect(window_days: int, extra: List[str]) -> Tuple[List[str], Dict[str, int]]:
    """The exercise corpora, with a count per source — so the report says what the activation was measured ON."""
    data = _data_dir()
    texts: List[str] = []
    counts: Dict[str, int] = {}

    def add(name: str, items: List[str]) -> None:
        counts[name] = len(items)
        texts.extend(items)

    p = data / "recall_phrasings.json"
    if p.exists():
        rp = json.loads(p.read_text(encoding="utf-8"))
        fams = rp.get("families") if isinstance(rp.get("families"), dict) else rp      # {about, families: {family: [...]}}
        add("recall_phrasings", [s for k, fam in fams.items() if isinstance(fam, list) for it in fam for s in _strings(it)])
    p = data / "frontdoor_claims.json"
    if p.exists():
        fc = json.loads(p.read_text(encoding="utf-8"))
        add("frontdoor_claims", [s for it in (fc.get("claims") if isinstance(fc, dict) else fc) or [] for s in _strings(it)])
    try:
        from probe_usefulness import BATTERY  # type: ignore
        add("probe_usefulness", [q for q, _sig in BATTERY if isinstance(q, str)])
    except Exception:
        counts["probe_usefulness"] = 0
    p = ROOT / "eval" / "face_routes.json"             # the village's own questions, labeled (SOP-14)
    if p.exists():
        fr = json.loads(p.read_text(encoding="utf-8"))
        add("face_routes", [s for it in (fr.get("routes") if isinstance(fr, dict) else fr) or [] for s in _strings(it)])
    p = ROOT / "eval" / "live_probes.jsonl"
    if p.exists():
        items: List[str] = []
        for ln in p.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln.startswith("{"):
                try:
                    items.extend(_strings(json.loads(ln)))
                except Exception:
                    continue
        add("live_probes", items)
    p = data / "activity.jsonl"
    if p.exists():
        since = time.time() - window_days * 86400
        items = []
        for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                ev = json.loads(ln)
            except Exception:
                continue
            if isinstance(ev, dict) and int(ev.get("t") or 0) >= since:
                items.extend(_strings(ev))
        add(f"activity_{window_days}d", items)
    for path in extra:
        q = Path(path)
        if q.exists():
            add(q.name, [ln.strip() for ln in q.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")])
    return texts, counts


def measure(window_days: int, extra: List[str]) -> Dict[str, Any]:
    from concordance import faces
    texts, counts = collect(window_days, extra)
    fires = faces.scope_fires(texts)
    units = {uid: (row["magnitude"], row["fires"]) for uid, row in fires.items()}
    by_face: Dict[str, Dict[str, Any]] = {}
    for uid, row in fires.items():
        b = by_face.setdefault(row["face"], {"alive": 0, "dead": [], "top": []})
        if row["fires"] > 0:
            b["alive"] += 1
            b["top"].append((row["fires"], uid.split("|", 1)[1]))
        else:
            b["dead"].append(uid.split("|", 1)[1])
    for b in by_face.values():
        b["top"] = sorted(b["top"], reverse=True)[:5]
    return {"texts": len(texts), "sources": counts, "units": {"scope": units}, "by_face": by_face,
            "window": {"days": window_days, "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}}


def print_measure(m: Dict[str, Any]) -> None:
    print(f"activation measured on {m['texts']} texts: {m['sources']}")
    total = len(m["units"]["scope"])
    dead = sum(len(b["dead"]) for b in m["by_face"].values())
    print(f"scope units {total}  alive {total - dead}  dead {dead} ({100 * dead / max(total, 1):.0f}%)")
    for fid, b in sorted(m["by_face"].items()):
        print(f"  {fid:<22} alive {b['alive']:>3}  dead {len(b['dead']):>3}   top {[w for _, w in b['top']]}")
        if b["dead"]:
            print(f"  {'':<22} dead: {', '.join(b['dead'][:18])}{' …' if len(b['dead']) > 18 else ''}")


def gate(cmds: List[str]) -> Tuple[bool, Dict[str, Any]]:
    """Run every gate command; the mask in force is read by each process from CONCORDANCE_DATA_DIR. Pass = all exit 0."""
    detail: Dict[str, Any] = {}
    ok = True
    for c in cmds:
        t0 = time.time()
        r = subprocess.run(c, shell=True, capture_output=True, text=True)
        tail = (r.stdout.strip().splitlines() or [""])[-1][:160]
        detail[c] = {"rc": r.returncode, "tail": tail, "s": round(time.time() - t0, 1)}
        ok = ok and r.returncode == 0
    return ok, detail


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("measure", "propose", "apply", "run", "status", "rewind"))
    ap.add_argument("--p", type=float, default=0.2)
    ap.add_argument("--p-min", type=float, default=0.05)
    ap.add_argument("--rounds", type=int, default=6)
    ap.add_argument("--window-days", type=int, default=90)
    ap.add_argument("--extra", action="append", default=[])
    ap.add_argument("--gate-cmd", action="append", default=[])
    a = ap.parse_args(argv)
    from concordance import ticket

    if a.cmd == "status":
        cur = ticket.current()
        print(json.dumps({k: cur.get(k) for k in ("version", "measured_at", "window", "sparsity", "gates", "receipt", "parent")}, indent=1))
        print("masked:", {k: len(v) for k, v in (cur.get("masked") or {}).items()}, " versions on disk:", ticket.versions())
        return 0
    if a.cmd == "rewind":
        body = ticket.rewind()
        print("rewound to version", body.get("version"))
        return 0

    m = measure(a.window_days, a.extra)
    print_measure(m)
    units = m["units"]["scope"]
    if a.cmd == "measure":
        return 0
    cur = ticket.current()
    already = set((cur.get("masked") or {}).get("scope") or [])
    pick = ticket.propose(units, a.p, protect=already)
    print(f"\nproposal (p={a.p}): mask {len(pick)} dead scope units (already masked {len(already)}):")
    for uid in pick[:60]:
        print("  -", uid)
    if len(pick) > 60:
        print(f"  … {len(pick) - 60} more")
    if a.cmd == "propose":
        return 0
    if a.cmd == "apply":
        mask = ticket.save({"scope": sorted(already | set(pick))}, window=m["window"], totals={"scope": len(units)})
        print(f"\nwrote mask version {mask['version']} receipt {mask['receipt'][:16]}… — now GATE it (SOP) or `rewind`")
        return 0
    if not a.gate_cmd:
        print("run needs at least one --gate-cmd", file=sys.stderr)
        return 2
    history = ticket.imp(
        lambda: {"scope": measure(a.window_days, a.extra)["units"]["scope"]},
        lambda cumulative: ticket.save(cumulative, window=m["window"], totals={"scope": len(units)}),
        lambda: gate(a.gate_cmd),
        p0=a.p, p_min=a.p_min, rounds=a.rounds, protect=already)
    for row in history:
        print(json.dumps(row, default=str))
    final = ticket.current()
    print(f"\nticket in force: version {final.get('version')} masked {len((final.get('masked') or {}).get('scope') or [])} scope units")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
