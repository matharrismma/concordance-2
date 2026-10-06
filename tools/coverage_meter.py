#!/usr/bin/env python3
"""THE VERIFY-COVERAGE METER — measure the Moat's real breadth and depth, write data/coverage.json, so the
Bridge shows a real needle for verify coverage instead of a curated estimate (Matt, 2026-10-06).

    PYTHONPATH=src python tools/coverage_meter.py          # writes data/coverage.json

Three honest numbers, none guessed:
  * DOMAINS   — distinct verifier modules (the subject breadth), excluding the *_scale support libs.
  * BENCHMARKED — domains with a standing golden, re-run at every deploy (the regression guard).
  * UNIT-TESTED — domains with a tests/test_<module>.py pinning their logic (the depth of coverage).
The breadth is wide; the unit-test depth is the real gap. A meter, not a verdict.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

_ROOT = Path(__file__).resolve().parent.parent
# support libraries + internals, not subject domains
_SUPPORT = {"alpha_scale", "grav_scale", "molar_scale", "planck_scale", "rela_scale", "thermal_scale",
            "si_units", "scale_base", "bridges", "_boolean", "riemann_accel", "base", "spec", "retrieval"}


def _data_dir() -> Path:
    return Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data")


def measure() -> dict:
    from concordance import verifiers as V
    sec = set(V.VERIFIERS.values())
    wit = set(V.WITNESS_VERIFIERS.values())
    modules = sorted({p.split(".")[-1] for p in (sec | wit)})
    domains = [m for m in modules if m not in _SUPPORT]
    tested = sorted(m for m in domains if (_ROOT / "tests" / ("test_%s.py" % m)).exists())
    untested = sorted(set(domains) - set(tested))
    # benchmarked domains — from the standing benchmark file the gate writes
    benchmarked = None
    try:
        b = json.loads((_data_dir() / "benchmarks.json").read_text(encoding="utf-8"))
        dom = b.get("domains") or {}
        benchmarked = dom.get("ok") if isinstance(dom.get("ok"), int) else None
    except (OSError, ValueError):
        benchmarked = None
    nd = len(domains)
    return {
        "measured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "domains": nd,
        "aliases_accepted": len(V.VERIFIERS) + len(V.WITNESS_VERIFIERS),
        "benchmarked": benchmarked,
        "unit_tested": len(tested),
        "unit_tested_ratio": round(len(tested) / nd, 4) if nd else 0.0,
        "untested": untested,
        "note": ("domains = distinct verifier modules (subject breadth, excl. *_scale libs); benchmarked = "
                 "domains with a standing golden re-run at every deploy (the regression guard); unit_tested = "
                 "domains with a tests/test_<module>.py. Breadth is wide; unit-test depth is the real gap."),
    }


def main() -> int:
    out = _data_dir() / "coverage.json"
    data = measure()
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, out)
    print("domains %d · benchmarked %s · unit-tested %d (%.0f%%) -> %s"
          % (data["domains"], data["benchmarked"], data["unit_tested"],
             100 * data["unit_tested_ratio"], out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
