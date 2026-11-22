"""THE HELM's action side — the PROBES: allow-listed, bounded, operator-only.

The instruments (`keep.py:dashboard`) say what IS. A probe is the other half the panel never had:
one button, one bounded job, a receipt. Until 2026-11-22 the operator's panel returned thirteen
keys and every one of them was a readout — the only available action was reloading the page.

OPERATOR DECISION 2026-11-22 (Matt): the gated handler MAY run the tools directly, rather than
writing a request to a queue the desk drains. So this file is where that power is fenced.

THE LINE A PROBE MAY NOT CROSS — the rule this registry exists to enforce:

    A probe NEVER writes to the keeping, the ledger, the CAS, or any sealed artifact. It MAY
    refresh its own derived cache (integrity_status.json, traffic.json) — that is the entire point
    of two of them. Anything that mutates the record is a LEVER: it needs a second confirmation
    stating what changes and whether it can be undone, it produces a receipt, and it does NOT
    live in this file.

SHELL SAFETY, now that a web handler may spawn:
  - the request chooses an ID from PROBES and nothing else. No value from a request ever reaches
    an argv. There is no probe that takes free text.
  - argv is an explicit list built from sys.executable + a path resolved from THIS file, run with
    -I (isolated). Never a string, never shell=True, never cwd on sys.path.
  - every probe carries a timeout, and captured output is truncated.
  - a probe whose tool is missing, or whose INPUTS are missing, refuses instead of running. That
    guard is load-bearing for `traffic`: tools/traffic_rollup.py defaults to
    /var/log/caddy/*.access.log and, finding nothing, would happily write a file full of zeros
    OVER a good traffic.json. A probe that can destroy the thing it exists to refresh is not a
    probe. So we check the logs are there first, and decline on the desk.

DECLARED CONSEQUENCE: tools/integrity_check.py POSTs a short JSON alert to
CONCORDANCE_ALERT_WEBHOOK when a check FAILS (its own behaviour, inert unless that env is set).
Firing the `integrity` probe can therefore send one outbound request. No email, ever.

This module runs nothing on import and holds no state. It must only ever be called from behind
the operator gate (`keep.request_is_operator`); it does not check that itself, because the caller
owns the gate and a second half-gate here would be a place for the two to disagree.
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# ONE PROBE AT A TIME, measured 2026-11-22. The server is a ThreadingHTTPServer, so a slow probe
# does not block the panel outright -- but it does starve it: /helm.json answers in ~1s idle and
# took 47.8s while a 36s chain walk was running, because the walk is thousands of small reads. Two
# probes at once would be worse, and the page polls every 15s, so a pile-up is easy to cause by
# clicking twice. A second probe is therefore DECLINED immediately rather than queued: an operator
# who asked twice gets an answer, not a longer wait.
_RUNNING = threading.Lock()

# repo root: .../src/concordance/web/helm_probes.py -> parents[3]
_ROOT = Path(__file__).resolve().parents[3]
_OUT_CAP = 4000          # bytes of captured output we keep
_DEFAULT_TIMEOUT = 120   # seconds


def _data_dir() -> Path:
    return Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or (_ROOT / "data"))


def _ledger_chain() -> Dict[str, Any]:
    """In-process, read-only: walk the ledger hash-chain. This one can genuinely fail, which is
    the only reason it is worth a button — and when it does, the verdict must NAME what broke.
    The report's own keys are `tampered`, `broken_links`, `missing_records` and `unsigned`; an
    earlier draft of this probe filtered for keys verify_chain never emits, so a broken chain
    would have come back as a bare count with no cause."""
    from .. import ledger
    rep = ledger.verify_chain()
    total, ok_n = rep.get("total"), rep.get("verified")
    parts = []
    for key, noun in (("tampered", "tampered"), ("broken_links", "broken link"),
                      ("missing_records", "missing sealed record")):
        n = len(rep.get(key) or [])
        if n:
            parts.append("%d %s%s" % (n, noun, "" if n == 1 or noun == "tampered" else "s"))
    good = bool(rep.get("ok"))
    return {
        "ok": good,
        "verdict": ("chain holds — %s/%s verified" % (ok_n, total)) if good else
                   ("CHAIN BROKEN — %s (%s/%s verified)"
                    % (", ".join(parts) or "cause unnamed", ok_n, total)),
        "detail": {"total": total, "verified": ok_n,
                   "tampered": (rep.get("tampered") or [])[:10],
                   "broken_links": (rep.get("broken_links") or [])[:10],
                   "missing_records": (rep.get("missing_records") or [])[:10],
                   "unsigned": (rep.get("unsigned") or [])[:10]},
        "next": ("nothing — the record stands" if good else
                 "stop writing, run the integrity probe, and read the detail before anything "
                 "else touches the ledger"),
    }


# id -> spec. "inproc" calls a function here; "tool" spawns a script with an explicit argv.
PROBES: Dict[str, Dict[str, Any]] = {
    "ledger_chain": {
        "label": "Re-verify the chain",
        "what": "walks the ledger hash-chain in process: recomputes every content_hash, confirms "
                "every prev_hash link, re-verifies each bound CAS record",
        "kind": "inproc",
        "fn": _ledger_chain,
        "refreshes": None,
        # NO TIMEOUT KEY, deliberately: a timeout is only enforced for "tool" probes, where the
        # subprocess can be killed. An in-process walk cannot be interrupted without threads or
        # signals, so declaring a number here would be decoration. MEASURED 2026-11-22 on the desk:
        # 28-36s for 1,823 precedents, on a OneDrive-backed filesystem — thousands of small reads,
        # so the box's local disk should be much quicker. This is the known limit of the tier: an
        # in-process probe is bounded by what it reads, not by a clock.
    },
    "integrity": {
        "label": "Re-run integrity",
        "what": "the full watchdog: the chain plus a sweep of every sealed CAS record. Writes "
                "integrity_status.json, which the panel's integrity tile reads",
        "kind": "tool",
        "script": "tools/integrity_check.py",
        "args": [],
        "refreshes": "integrity_status.json",
        "timeout": 300,
        "note": "POSTs to CONCORDANCE_ALERT_WEBHOOK on failure, if that env is set",
    },
    "traffic": {
        "label": "Refresh traffic",
        "what": "rolls up the Caddy access logs into traffic.json — the fix for the stale traffic "
                "tile (own-2). Seven days, because the rollup cannot read rotated .gz logs and a "
                "longer window would silently under-report",
        "kind": "tool",
        "script": "tools/traffic_rollup.py",
        "args": ["--days", "7"],
        "refreshes": "traffic.json",
        "timeout": 300,
        "requires_glob": "/var/log/caddy/*.access.log",
    },
}


def catalog() -> List[Dict[str, Any]]:
    """What the panel renders. Executes nothing."""
    out = []
    for pid, spec in PROBES.items():
        out.append({
            "probe": pid,
            "label": spec["label"],
            "what": spec["what"],
            "tier": "probe",
            "refreshes": spec.get("refreshes"),
            "note": spec.get("note"),
            "available": _availability(spec)[0],
            "unavailable_because": _availability(spec)[1],
        })
    return out


def _availability(spec: Dict[str, Any]) -> tuple:
    """A probe that cannot run says so BEFORE it is fired, so the panel can grey the button
    instead of handing back a failure that looks like a defect in the engine."""
    if spec["kind"] == "tool":
        if not (_ROOT / spec["script"]).is_file():
            return False, "%s is not present in this tree" % spec["script"]
        pat = spec.get("requires_glob")
        if pat and not glob.glob(pat):
            return False, "no files match %s on this host — nothing to read" % pat
    return True, None


def _run_tool(spec: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    script = _ROOT / spec["script"]
    argv = [sys.executable, "-I", str(script)] + list(spec.get("args") or [])
    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                           cwd=str(_ROOT), env=env, shell=False)
    except subprocess.TimeoutExpired:
        return {"ok": False, "verdict": "timed out after %ds" % timeout, "detail": {"argv": argv[2:]},
                "next": "run it on the box by hand — a probe that cannot finish in %ds is a lever" % timeout}
    out = (p.stdout or "")[-_OUT_CAP:]
    err = (p.stderr or "")[-_OUT_CAP:]
    ok = p.returncode == 0
    first = next((ln for ln in reversed(out.splitlines()) if ln.strip()), "") or \
            next((ln for ln in reversed(err.splitlines()) if ln.strip()), "")
    return {
        "ok": ok,
        "verdict": first.strip() or ("exit 0" if ok else "exit %d" % p.returncode),
        "detail": {"exit": p.returncode, "stdout": out, "stderr": err},
        "next": "nothing" if ok else "read the output above before anything else writes",
    }


def run(probe_id: str, *, timeout: Optional[int] = None) -> Dict[str, Any]:
    """Fire one probe by ID. Returns the same four things every time — verdict, ok, cost in ms,
    and the one next step — plus what it refreshed, so the panel can mark that tile fresh.

    CALL ONLY FROM BEHIND THE OPERATOR GATE."""
    spec = PROBES.get(str(probe_id or "").strip())
    if spec is None:
        return {"probe": probe_id, "ok": False, "verdict": "no such probe",
                "ms": 0, "next": "choose one of: " + ", ".join(sorted(PROBES)),
                "detail": None, "refreshed": None, "at": int(time.time())}
    available, because = _availability(spec)
    if not available:
        return {"probe": probe_id, "label": spec["label"], "ok": False,
                "verdict": "declined — " + because, "ms": 0, "detail": None, "refreshed": None,
                "next": "run it where the inputs are (the box), not here", "at": int(time.time())}
    if not _RUNNING.acquire(blocking=False):
        return {"probe": probe_id, "label": spec["label"], "ok": False, "ms": 0, "detail": None,
                "refreshed": None, "at": int(time.time()),
                "verdict": "declined — a probe is already running",
                "next": "wait for it; probes run one at a time so one cannot starve the panel"}
    t0 = time.time()
    try:
        if spec["kind"] == "inproc":
            res = spec["fn"]()
        else:
            res = _run_tool(spec, int(timeout or spec.get("timeout") or _DEFAULT_TIMEOUT))
    except Exception as e:                                   # a probe never takes the panel down
        res = {"ok": False, "verdict": "%s: %s" % (type(e).__name__, e), "detail": None,
               "next": "this is a defect in the probe, not necessarily in the engine"}
    finally:
        _RUNNING.release()
    ms = int(1000 * (time.time() - t0))
    refreshed = spec.get("refreshes")
    if refreshed:
        f = _data_dir() / refreshed
        refreshed = {"file": refreshed,
                     "mtime": int(f.stat().st_mtime) if f.exists() else None}
    return {"probe": probe_id, "label": spec["label"], "ms": ms, "at": int(time.time()),
            "refreshed": refreshed, **res}
