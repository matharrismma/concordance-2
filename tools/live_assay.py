#!/usr/bin/env python3
"""THE LIVE ASSAY WITH A RATCHET — ask the running engine the questions that found this week's bugs, every
night, and let recall only rise. (docs/PROJECT_REVIEW_2026-10-03.md R3; Matt, 2026-10-03: "go on those".)

CI runs 2,100 tests in fifty seconds and never touches the keeping. Five reach bugs in two days were found
only by asking the live box: a chart lifted as a bodiless brief, the alignment gate hiding a signpost, two
gap guards reading only titles, "lds" tripping inside "handhelds". This is the instrument that would have
caught every one of them the next morning.

    PYTHONPATH=src python tools/live_assay.py                       # against the box (127.0.0.1:8002 / 8001)
    ASSAY_BASE=https://narrowhighway.com python tools/live_assay.py # from anywhere
    python tools/live_assay.py --list                               # the probes, by id

The probes live in eval/live_probes.jsonl — each a request (face, method, path, query/body), a list of
expectations over the JSON answer (at / eq / ne / in / contains / startswith / has / len / absent / exists /
truthy / falsy), and optionally `known_miss: true` (the assay's want list: a thing the engine SHOULD do and
does not yet; it never counts as a regression, and the day it passes it joins the floor).

THE RATCHET: <ASSAY_DIR>/floor.json holds every probe id that has EVER passed. A probe in the floor that
fails tonight is a REGRESSION — the run exits 1, logs the ids, and posts to CONCORDANCE_ALERT_WEBHOOK if
set. A probe that passes for the first time joins the floor. Recall may only rise. Each run also writes
<ASSAY_DIR>/<date>.json with every probe's result, so a drift can be read, not guessed.
Stdlib only."""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent
PROBES = Path(os.environ.get("ASSAY_PROBES", "").strip() or (REPO / "eval" / "live_probes.jsonl"))
ASSAY_DIR = Path(os.environ.get("ASSAY_DIR", "").strip() or "/home/nh/backups/assay")
BASES = {
    "secular": os.environ.get("ASSAY_BASE", "http://127.0.0.1:8002").rstrip("/"),
    "witness": os.environ.get("ASSAY_WITNESS", "http://127.0.0.1:8001").rstrip("/"),
    "public": os.environ.get("ASSAY_PUBLIC", "https://narrowhighway.com").rstrip("/"),
}
TIMEOUT = int(os.environ.get("ASSAY_TIMEOUT", "150"))
_SEG = re.compile(r"([^.\[\]]+)|\[(\*|-?\d+)\]")


# ── pure: resolve a path into an answer, evaluate one expectation, the ratchet ───────────────────
def resolve(obj: Any, path: str) -> List[Any]:
    """Values at a dotted path with [n] / [*] steps — always a list (empty when the path is absent).
    '' names the whole object."""
    vals = [obj]
    for m in _SEG.finditer(path or ""):
        key, idx = m.group(1), m.group(2)
        nxt: List[Any] = []
        for v in vals:
            if key is not None:
                if isinstance(v, dict) and key in v:
                    nxt.append(v[key])
            elif idx == "*":
                if isinstance(v, list):
                    nxt.extend(v)
            else:
                i = int(idx)
                if isinstance(v, list) and -len(v) <= i < len(v):
                    nxt.append(v[i])
        vals = nxt
    return vals


def check(vals: List[Any], spec: Dict[str, Any]) -> Tuple[bool, str]:
    """One expectation against the resolved values. Returns (ok, why)."""
    at = spec.get("at", "")
    if "absent" in spec:
        ok = (len(vals) == 0) == bool(spec["absent"])
        return ok, f"{at}: {'absent' if vals == [] else 'present'}"
    if "exists" in spec:
        ok = (len(vals) > 0) == bool(spec["exists"])
        return ok, f"{at}: {'present' if vals else 'absent'}"
    if not vals:
        return False, f"{at}: absent"
    v = vals[0]
    s = "" if v is None else (v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))
    if "eq" in spec:
        return v == spec["eq"], f"{at} = {s[:80]!r}"
    if "ne" in spec:
        return v != spec["ne"], f"{at} = {s[:80]!r}"
    if "in" in spec:
        return v in spec["in"], f"{at} = {s[:80]!r}"
    if "contains" in spec:
        return str(spec["contains"]).lower() in s.lower(), f"{at} = {s[:80]!r}"
    if "startswith" in spec:
        return s.lower().startswith(str(spec["startswith"]).lower()), f"{at} = {s[:80]!r}"
    if "has" in spec:
        return spec["has"] in vals, f"{at} has {len(vals)} values"
    if "len" in spec:
        n = len(v) if isinstance(v, (list, dict, str)) else len(vals)
        return n == spec["len"], f"{at} len {n}"
    if "min_len" in spec:
        n = len(v) if isinstance(v, (list, dict, str)) else len(vals)
        return n >= spec["min_len"], f"{at} len {n}"
    if "truthy" in spec:
        return bool(v) == bool(spec["truthy"]), f"{at} = {s[:40]!r}"
    return False, f"{at}: unknown expectation {sorted(spec)}"


def evaluate(probe: Dict[str, Any], answer: Any, status: int) -> Tuple[bool, List[str]]:
    """Every expectation must hold, and the status must be the one expected (200 unless said)."""
    fails: List[str] = []
    want = int(probe.get("status", 200))
    if status != want:
        fails.append(f"status {status} != {want}")
    for spec in probe.get("expect") or []:
        ok, why = check(resolve(answer, spec.get("at", "")), spec)
        if not ok:
            fails.append(why)
    return (not fails), fails


def ratchet(floor: Dict[str, Any], passed: List[str], failed: List[str], known_miss: List[str]) -> Dict[str, Any]:
    """The floor only rises. regressed = in the floor, failed tonight, not a known miss."""
    ids = set(floor.get("ids") or [])
    regressed = sorted(i for i in failed if i in ids and i not in known_miss)
    newly = sorted(i for i in passed if i not in ids)
    ids |= set(passed)
    return {"ids": sorted(ids), "regressed": regressed, "newly_passing": newly,
            "since": floor.get("since") or date.today().isoformat()}


# ── the wire ─────────────────────────────────────────────────────────────────────────────────
def fetch(probe: Dict[str, Any]) -> Tuple[int, Any]:
    base = BASES.get(probe.get("face") or "secular", BASES["secular"])
    url = base + probe["path"]
    if probe.get("query"):
        url += "?" + urllib.parse.urlencode(probe["query"])
    data = None
    headers = {"accept": "application/json", "user-agent": "nh-live-assay/1"}
    headers.update(probe.get("headers") or {})
    if probe.get("body") is not None:
        data = json.dumps(probe["body"]).encode("utf-8")
        headers["content-type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=probe.get("method") or ("POST" if data else "GET"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            raw = r.read()
            status = r.status
    except urllib.error.HTTPError as e:
        raw, status = e.read(), e.code
    except Exception as e:  # noqa: BLE001 — a dead door is a failed probe, not a crash
        return 0, {"error": f"{type(e).__name__}: {e}"}
    try:
        return status, json.loads(raw.decode("utf-8", errors="replace"))
    except Exception:
        return status, {"_text": raw.decode("utf-8", errors="replace")[:4000]}


def seal_clean(probe: Dict[str, Any], answer: Any) -> List[str]:
    """For a verify probe with `seal_clean`: fetch the receipt it minted and assert the strings are absent."""
    words = probe.get("seal_clean") or []
    if not words or not isinstance(answer, dict):
        return []
    receipt = answer.get("receipt") or ((answer.get("seal") or {}).get("cite_url") if isinstance(answer.get("seal"), dict) else None)
    if not receipt:
        return ["seal_clean: no receipt on the answer"]
    path = urllib.parse.urlparse(str(receipt)).path or "/"
    status, body = fetch({"face": probe.get("face") or "secular", "path": path, "method": "GET"})
    text = json.dumps(body, ensure_ascii=False) if not isinstance(body, dict) or "_text" not in body else body["_text"]
    leaked = [w for w in words if w.lower() in text.lower()]
    return [f"seal carries {w!r}" for w in leaked] + ([] if status == 200 else [f"receipt {path} -> {status}"])


def load_probes(path: Path = PROBES) -> List[Dict[str, Any]]:
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln and not ln.startswith("#"):
            out.append(json.loads(ln))
    return out


def alert(text: str) -> None:
    hook = os.environ.get("CONCORDANCE_ALERT_WEBHOOK", "").strip()
    if not hook:
        return
    try:
        req = urllib.request.Request(hook, data=json.dumps({"text": text}).encode("utf-8"), method="POST",
                                     headers={"content-type": "application/json"})
        urllib.request.urlopen(req, timeout=20).read()
    except Exception:  # noqa: BLE001 — the alert is best-effort
        pass


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    probes = load_probes()
    if "--list" in argv:
        for p in probes:
            print(f"{p['id']:40} {p.get('face','secular'):8} {p.get('method','GET'):4} {p['path']}  {'(known miss)' if p.get('known_miss') else ''}")
        return 0
    only = [a for a in argv if not a.startswith("--")]
    if only:
        probes = [p for p in probes if p["id"] in only]
    ASSAY_DIR.mkdir(parents=True, exist_ok=True)
    floor_path = ASSAY_DIR / "floor.json"
    floor = json.loads(floor_path.read_text(encoding="utf-8")) if floor_path.exists() else {"ids": [], "since": date.today().isoformat()}
    started = time.time()
    results: List[Dict[str, Any]] = []
    passed, failed, known = [], [], []
    for p in probes:
        t0 = time.time()
        status, answer = fetch(p)
        ok, fails = evaluate(p, answer, status)
        fails += seal_clean(p, answer)
        ok = ok and not fails
        rec = {"id": p["id"], "ok": ok, "status": status, "ms": int((time.time() - t0) * 1000),
               "known_miss": bool(p.get("known_miss")), "fails": fails}
        results.append(rec)
        (passed if ok else failed).append(p["id"])
        if p.get("known_miss"):
            known.append(p["id"])
        print(("PASS " if ok else ("miss " if p.get("known_miss") else "FAIL ")) + f"{p['id']:40} {rec['ms']:5d}ms" + ("" if ok else "  " + "; ".join(fails)[:160]))
    r = ratchet(floor, passed, failed, known)
    today = date.today().isoformat()
    summary = {"date": today, "at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "bases": BASES,
               "probes": len(probes), "passed": len(passed), "failed": len(failed),
               "known_misses": len(known), "known_misses_now_passing": sorted(i for i in known if i in passed),
               "regressed": r["regressed"], "newly_passing": r["newly_passing"], "floor": len(r["ids"]),
               "seconds": round(time.time() - started, 1), "results": results}
    (ASSAY_DIR / f"{today}.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    floor_path.write_text(json.dumps({"ids": r["ids"], "since": r["since"], "updated": today}, indent=1), encoding="utf-8")
    line = (f"{summary['at']} ASSAY {'REGRESSED' if r['regressed'] else 'OK'}: {len(passed)}/{len(probes)} passed, "
            f"floor {len(r['ids'])}, newly passing {r['newly_passing']}, regressed {r['regressed']}, "
            f"known misses now passing {summary['known_misses_now_passing']}, {summary['seconds']}s")
    with open(ASSAY_DIR / "assay.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)
    if r["regressed"]:
        alert("Narrow Highway live assay REGRESSED: " + ", ".join(r["regressed"]))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
