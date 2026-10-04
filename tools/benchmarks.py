#!/usr/bin/env python3
"""THE ENGINE MEASURES ITSELF IN PUBLIC (Gen 3 · 7; docs/GEN3_CHARTER.md).

The standing benchmarks, run on the box, written to data/benchmarks.json, served at GET /benchmarks and shown on
/proof — never typed in. Three measures, each with a ratchet against the previous run:

  domains   every golden pair in data/domain_goldens.json (one true packet, one false, per domain) through the
            real router: did the domain SEAL its truth (a CONFIRMED and no MISMATCH) and REFUSE its falsehood
            (a MISMATCH or ERROR, never a lone CONFIRMED)? A falsehood confirmed is a FALSE POSITIVE.
  moat      tools/benchmark.py — the derivation-moat set (true and false claims, three modes); its own
            false-positive count must be 0.
  specs     every admitted spec proves its own goldens at load (verifiers/spec.py); refused specs are counted.

A REGRESSION is: a domain that was ok in the previous run and is not now, a moat false positive, or a spec that
was admitted before and is refused now. `--gate` exits 1 on regression so the deploy can refuse itself (tools/
deploy.sh reverts the files and restarts). The timer (nh-benchmarks.timer) runs it nightly after the assay.

    PYTHONPATH=src python tools/benchmarks.py            # run, write data/benchmarks.json, print the summary
    PYTHONPATH=src python tools/benchmarks.py --gate     # same; exit 1 on regression
    PYTHONPATH=src python tools/benchmarks.py --dry-run  # run, print, write nothing
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
os.environ.setdefault("CONCORDANCE_DATA_DIR", str(ROOT / "data"))


def _data_dir() -> Path:
    return Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or str(ROOT / "data"))


def bench_domains(goldens: Dict[str, Any]) -> Dict[str, Any]:
    from concordance import verifiers
    out: Dict[str, Any] = {}
    for domain in sorted(goldens):
        g = goldens[domain]
        key = g.get("packet_key")
        if not key or "true" not in g or "false" not in g:
            continue
        rec: Dict[str, Any] = {}
        for side in ("true", "false"):
            try:
                sts = [r.status for r in verifiers.run_for_domain(domain, {key: g[side]}, surface="witness")
                       if r.status != "NOT_APPLICABLE"]
            except Exception as e:  # noqa: BLE001 — a crash is a finding, never a silent pass
                sts = [f"CRASH:{type(e).__name__}"]
            rec[side] = sts
        confirmed_t = any("CONFIRM" in s for s in rec["true"]) and not any("MISMATCH" in s for s in rec["true"])
        refused_f = any(("MISMATCH" in s or "ERROR" in s or "CRASH" in s) for s in rec["false"])
        false_pos = any("CONFIRM" in s for s in rec["false"]) and not any("MISMATCH" in s for s in rec["false"])
        out[domain] = {"sealed_truth": bool(confirmed_t), "refused_falsehood": bool(refused_f),
                       "false_positive": bool(false_pos), "ok": bool(confirmed_t and refused_f and not false_pos),
                       "true": rec["true"], "false": rec["false"]}
    return out


def bench_moat() -> Dict[str, Any]:
    try:
        import benchmark as B  # tools/benchmark.py
    except Exception as e:  # noqa: BLE001
        return {"error": f"benchmark unavailable: {e}"}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = B.run(verbose=False, as_json=True)
    try:
        j = json.loads(buf.getvalue())
    except ValueError:
        return {"error": "benchmark emitted no JSON", "rc": rc}
    cases = j.get("cases") or []
    return {"version": j.get("benchmark_version"), "cases": len(cases),
            "correct": sum(1 for c in cases if c.get("correct")),
            "false_positives": len(j.get("false_positives") or []),
            "false_negatives": len(j.get("false_negatives") or []), "rc": rc}


def bench_specs() -> Dict[str, Any]:
    from concordance.verifiers import spec as S
    lo = S.load(force=True)
    return {"admitted": [s["id"] for s in lo["specs"]], "checks": sum(len(s.get("checks") or []) for s in lo["specs"]),
            "held": len(lo["held"]), "refused": [r["id"] for r in lo["refused"]]}


def latest_assay() -> Optional[Dict[str, Any]]:
    d = Path(os.environ.get("ASSAY_DIR", "").strip() or "/home/nh/backups/assay")
    try:
        files = sorted(d.glob("????-??-??.json"))
    except OSError:
        return None
    if not files:
        return None
    try:
        j = json.loads(files[-1].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return {k: j.get(k) for k in ("date", "at", "probes", "passed", "failed", "floor", "regressed", "newly_passing")}


def run(dry_run: bool = False) -> Dict[str, Any]:
    t0 = time.time()
    data = _data_dir()
    out_path = data / "benchmarks.json"
    prev: Dict[str, Any] = {}
    if out_path.exists():
        try:
            prev = json.loads(out_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            prev = {}
    try:
        goldens = json.loads((data / "domain_goldens.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        goldens = {}
    domains = bench_domains(goldens)
    moat = bench_moat()
    specs = bench_specs()
    # THE RATCHET (as the assay's): the floor is every domain that has EVER been ok and every spec ever
    # admitted. A regression is "in the floor, not ok tonight" — a refused deploy does not lower the floor,
    # so the same regression is named again tomorrow until it is fixed, never forgotten.
    floor_path = data / "benchmarks.floor.json"
    floor: Dict[str, Any] = {"domains": [], "specs": []}
    if floor_path.exists():
        try:
            floor = json.loads(floor_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
    floor_domains = set(floor.get("domains") or []) | {d for d, r in domains.items() if r["ok"]}
    floor_specs = set(floor.get("specs") or []) | set(specs["admitted"])
    regressions: List[str] = sorted(d for d in floor_domains if d in domains and not domains[d]["ok"])
    if moat.get("false_positives"):
        regressions.append(f"moat: {moat['false_positives']} false positive(s)")
    regressions += [f"spec refused: {s}" for s in specs["refused"] if s in floor_specs]
    try:
        from concordance import __version__ as ver
    except Exception:  # noqa: BLE001
        ver = None
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "host": socket.gethostname(), "version": ver, "seconds": round(time.time() - t0, 1),
        "domains": {"count": len(domains), "sealed_truths": sum(1 for r in domains.values() if r["sealed_truth"]),
                    "refused_falsehoods": sum(1 for r in domains.values() if r["refused_falsehood"]),
                    "false_positives": sum(1 for r in domains.values() if r["false_positive"]),
                    "ok": sum(1 for r in domains.values() if r["ok"]),
                    "not_ok": sorted(d for d, r in domains.items() if not r["ok"]),
                    "by_domain": domains},
        "moat": moat, "specs": specs, "assay": latest_assay(),
        "regressions": regressions, "regressed": bool(regressions),
        "previous": {"generated_at": prev.get("generated_at"), "domains_ok": (prev.get("domains") or {}).get("ok")},
        "note": ("Measured by tools/benchmarks.py on this node — every golden pair through the real router, the "
                 "derivation-moat set, every admitted spec's own goldens — and ratcheted against the previous run. "
                 "A regression refuses a deploy (tools/deploy.sh reverts). Never typed in."),
    }
    summary["floor"] = {"domains": len(floor_domains), "specs": len(floor_specs)}
    if not dry_run:
        if out_path.exists():
            try:
                os.replace(out_path, data / "benchmarks.prev.json")
            except OSError:
                pass
        tmp = out_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, out_path)
        floor_path.write_text(json.dumps({"domains": sorted(floor_domains), "specs": sorted(floor_specs),
                                          "updated": summary["generated_at"]}, indent=1), encoding="utf-8")
    return summary


def main(argv: Optional[List[str]] = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    s = run(dry_run="--dry-run" in a)
    d, m = s["domains"], s["moat"]
    print(f"{s['generated_at']} BENCHMARKS {'REGRESSED' if s['regressed'] else 'OK'}: domains {d['ok']}/{d['count']} ok "
          f"(sealed {d['sealed_truths']}, refused {d['refused_falsehoods']}, false positives {d['false_positives']}); "
          f"moat {m.get('correct')}/{m.get('cases')} correct, {m.get('false_positives')} false positives; "
          f"specs {s['specs']['checks']} checks admitted, {len(s['specs']['refused'])} refused; "
          f"regressions {s['regressions']}; {s['seconds']}s")
    if d["not_ok"]:
        print("  not ok:", ", ".join(d["not_ok"]))
    if "--gate" in a and s["regressed"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
