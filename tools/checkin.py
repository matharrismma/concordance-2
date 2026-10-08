#!/usr/bin/env python3
"""THE ISOLATED CHECK-IN — what each piece costs ALONE (Matt, 2026-10-08: "we need to see speed and memory of
each piece. We optimize each and the connections between them to get full capability.")

systems.checkin() runs at boot and measures what the server loads beyond its own imports. That is the honest
roll-call, but a module the server had already pulled in reads 0 there. This tool answers the other question:
each subsystem imported in a FRESH interpreter, by itself — cold wall time and peak resident memory with
nothing else loaded, minus a bare-interpreter baseline (python + `import concordance`). Also the heavy
singletons (the corpus, the graph, the verify deps) by themselves, because they dominate the box.

The number per piece is the optimizable one: shrink a piece, or cut an edge that pulls a heavy piece into a
light path, and this table moves. Writes data/checkin_isolated.json (untracked, box-generated) and prints the
table sorted by cost. Stdlib only; each child is time-boxed.

    PYTHONPATH=src python tools/checkin.py             # all subsystems + singletons
    PYTHONPATH=src python tools/checkin.py --no-singletons
    PYTHONPATH=src python tools/checkin.py --only ask,verify
    PYTHONPATH=src python tools/checkin.py --json       # the table as JSON only
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
os.environ.setdefault("CONCORDANCE_DATA_DIR", str(ROOT / "data"))

# Runs in the child. Reads a JSON job on argv[1]: {"modules": [...], "singleton": null | "corpus"|"graph"|"verify"}.
# Prints one JSON line: ms, rss_kb (current), peak_kb, loaded (count of concordance.* modules now resident).
_CHILD = r'''
import json, sys, time, os
job = json.loads(sys.argv[1])
def rss():
    try:
        from concordance.systems import rss_kb
        return rss_kb()
    except Exception:
        return None
def peak():
    try:
        if os.name == "posix":
            import resource
            v = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            return int(v if sys.platform != "darwin" else v // 1024)
        if os.name == "nt":
            import ctypes, ctypes.wintypes as w
            class PMC(ctypes.Structure):
                _fields_ = [("cb", w.DWORD), ("PageFaultCount", w.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                            ("WorkingSetSize", ctypes.c_size_t), ("a", ctypes.c_size_t), ("b", ctypes.c_size_t),
                            ("c", ctypes.c_size_t), ("d", ctypes.c_size_t), ("e", ctypes.c_size_t), ("f", ctypes.c_size_t)]
            k32 = ctypes.windll.kernel32; k32.GetCurrentProcess.restype = w.HANDLE
            f = ctypes.windll.psapi.GetProcessMemoryInfo
            f.argtypes = [w.HANDLE, ctypes.POINTER(PMC), w.DWORD]; f.restype = w.BOOL
            p = PMC(); p.cb = ctypes.sizeof(PMC)
            if f(k32.GetCurrentProcess(), ctypes.byref(p), p.cb):
                return int(p.PeakWorkingSetSize // 1024)
    except Exception:
        pass
    return None
t0 = time.perf_counter()
import concordance  # the baseline every piece shares
base_ms = (time.perf_counter() - t0) * 1000.0
r0 = rss()
t1 = time.perf_counter()
err = None
try:
    import importlib
    for m in job.get("modules") or []:
        importlib.import_module("concordance." + m)
    s = job.get("singleton")
    if s == "corpus":
        from concordance import corpus; corpus.default_corpus()
    elif s == "graph":
        from concordance import graph; graph._graph()
    elif s == "verify":
        from concordance.derivation import warm; warm()
except Exception as e:
    err = type(e).__name__ + ": " + str(e)[:140]
ms = (time.perf_counter() - t1) * 1000.0
r1 = rss()
print(json.dumps({"base_ms": round(base_ms, 1), "ms": round(ms, 1), "rss_before_kb": r0, "rss_after_kb": r1,
                  "rss_kb": (r1 - r0) if (r0 is not None and r1 is not None) else None, "peak_kb": peak(),
                  "loaded": sum(1 for k in sys.modules if k.startswith("concordance.")), "error": err}))
'''


def _child(job: Dict[str, Any], timeout: float) -> Dict[str, Any]:
    env = {**os.environ, "PYTHONPATH": str(SRC), "CONCORDANCE_SEAL_INDEX": os.environ.get("CONCORDANCE_SEAL_INDEX", "0")}
    t0 = time.perf_counter()
    try:
        p = subprocess.run([sys.executable, "-c", _CHILD, json.dumps(job)], capture_output=True, text=True,
                           timeout=timeout, env=env, cwd=str(ROOT))
    except subprocess.TimeoutExpired:
        return {"error": f"timed out after {timeout:.0f}s", "wall_ms": round((time.perf_counter() - t0) * 1000, 1)}
    wall = round((time.perf_counter() - t0) * 1000.0, 1)
    line = (p.stdout or "").strip().splitlines()
    if not line:
        return {"error": ("no output; rc=%s; %s" % (p.returncode, (p.stderr or "")[-200:])).strip(), "wall_ms": wall}
    try:
        out = json.loads(line[-1])
    except ValueError:
        return {"error": "unparseable child output: " + line[-1][:200], "wall_ms": wall}
    out["wall_ms"] = wall
    return out


def run(only: Optional[List[str]] = None, singletons: bool = True, timeout: float = 240.0,
        write: bool = True, data_dir: Optional[Path] = None) -> Dict[str, Any]:
    from concordance import systems as S
    base = _child({"modules": []}, timeout=60)
    rows: List[Dict[str, Any]] = []
    for s in S.SUBSYSTEMS:
        if only and s["slug"] not in only:
            continue
        r = _child({"modules": s["modules"]}, timeout=timeout)
        rows.append({"kind": "subsystem", "slug": s["slug"], "name": s["name"], "modules": s["modules"], **r})
    if singletons:
        for key, label in (("corpus", "corpus (default_corpus)"), ("graph", "graph (_graph)"),
                           ("verify", "verify deps (derivation.warm)")):
            r = _child({"modules": [], "singleton": key}, timeout=timeout)
            rows.append({"kind": "singleton", "slug": key, "name": label, "modules": [], **r})
    # the piece's own cost: its resident delta already excludes the baseline (measured after `import concordance`);
    # its peak minus the baseline's peak is the high-water mark it alone adds
    bpeak = base.get("peak_kb")
    for r in rows:
        r["peak_over_base_kb"] = (r["peak_kb"] - bpeak) if (r.get("peak_kb") is not None and bpeak is not None) else None
    rows.sort(key=lambda r: -(float(r.get("ms") or 0)))
    out = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "python": sys.version.split()[0],
           "platform": sys.platform, "baseline": base, "rows": rows,
           "about": ("each subsystem imported alone in a fresh interpreter: ms (import wall time after the shared "
                     "`import concordance` baseline), rss_kb (resident delta), peak_over_base_kb (high-water mark it "
                     "alone adds). The optimizable number per piece; connections are priced in systems.checkin().")}
    if write:
        d = Path(data_dir) if data_dir else Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or str(ROOT / "data"))
        try:
            d.mkdir(parents=True, exist_ok=True)
            p = d / "checkin_isolated.json"
            tmp = p.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(out, indent=1), encoding="utf-8")
            os.replace(tmp, p)
        except OSError:
            pass
    return out


def _fmt_kb(v: Any) -> str:
    if v is None:
        return "    ?"
    try:
        return f"{float(v) / 1024:7.1f}"
    except (TypeError, ValueError):
        return "    ?"


def table(out: Dict[str, Any]) -> str:
    b = out.get("baseline") or {}
    lines = [f"baseline (python + import concordance): {b.get('base_ms', '?')} ms, RSS {_fmt_kb(b.get('rss_after_kb'))} MB, "
             f"peak {_fmt_kb(b.get('peak_kb'))} MB   [{out.get('platform')}, py {out.get('python')}]",
             f"{'piece':<32} {'kind':<10} {'ms':>9} {'rss MB':>8} {'peak+ MB':>9}  note"]
    for r in out.get("rows") or []:
        note = r.get("error") or ""
        lines.append(f"{r['name'][:32]:<32} {r['kind']:<10} {float(r.get('ms') or 0):9.1f} {_fmt_kb(r.get('rss_kb')):>8} "
                     f"{_fmt_kb(r.get('peak_over_base_kb')):>9}  {note[:70]}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    only = None
    if "--only" in a:
        only = [x.strip() for x in a[a.index("--only") + 1].split(",") if x.strip()]
    out = run(only=only, singletons="--no-singletons" not in a, write="--dry-run" not in a)
    if "--json" in a:
        print(json.dumps(out, indent=1))
    else:
        print(table(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
