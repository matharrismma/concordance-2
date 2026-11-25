#!/usr/bin/env python3
"""THE STICK RE-CHECK (2026-11-25, Matt: "build the status door and then start on the list of suggested").

The sticks hold about 900 sealed marks (bound, instance, witness), each a pointer to a HOLDS verification in the
keeping. Nothing re-read them after they were minted. This does, three ways, for every sealed mark:

  1. PRESENT AND UNALTERED - its record is in the keeping (cas.fetch_anywhere: the CAS object, or the card that
     carries it) and the record's canonical bytes still hash to the seal (cas.content_hash_of, the canonical form
     tools/verify_seal.py checks with no engine code). States: MATCHES, MISSING, TAMPERED.
  2. HOLDS - the record's own verdict is PASS / HOLDS. State: NOT_HOLDS otherwise.
  3. SAME AS NOW - when a catalog entry mints this very mark (the same stick, kind and claim in the golden fixtures,
     which tools/tick_golden.py keeps equal to what the current code mints), the seal on the box is the seal the code
     mints today. A golden holds a seal only where today's check HOLDS, so DRIFTED means: re-minted today this claim
     still HOLDS, but the record's bytes differ. Measured 2026-11-25 on one such pair, the only difference was the
     numeric verifier's detail line ("= 90 (claim 90.0, within 1e-12)" became "= 90 - the claim 90.0 is exact.",
     commit 3244c52, 2026-10-09). So drift is REPORTED, with the dates its marks were minted, and does not fail the
     run; what it does mean is that re-running an old entry would mint a second mark with a new seal beside the old
     one. A mark no catalog entry mints today is counted as not_in_catalog and is not a failure.

READ-ONLY: it writes nothing to the keeping. The report goes to stdout and, with --json, to that path. Exit 0 when
every record is present, unaltered and HOLDS; 1 when any mark is MISSING, TAMPERED or NOT_HOLDS (drift alone never
fails it). No alert is sent anywhere.

    PYTHONPATH=src python tools/recheck_sticks.py                          # the keeping CONCORDANCE_DATA_DIR names
    PYTHONPATH=src python tools/recheck_sticks.py --json /path/report.json
    PYTHONPATH=src python tools/recheck_sticks.py --data DIR --golden DIR  # another keeping / golden set
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

from concordance.stick_recheck import GOLDEN, golden_seals, holds, recheck  # noqa: E402,F401

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", type=Path, default=None, help="the keeping (default: CONCORDANCE_DATA_DIR)")
    ap.add_argument("--golden", type=Path, default=GOLDEN)
    ap.add_argument("--json", type=Path, default=None, help="also write the report here")
    a = ap.parse_args(argv)
    r = recheck(a.data, a.golden)
    d = r["drift"]
    line = (f"{r['at']} RECHECK {'OK' if r['ok'] else 'FAILING'}: {r['sealed_marks']} sealed marks on {r['sticks']} "
            f"sticks; integrity {r['integrity']}; against today's catalog {r['now']} (drifted marks minted "
            f"{d['minted_from']} to {d['minted_to']}); {r['failing']} failing; {r['seconds']}s")
    print(line)
    for p in r["problems"][:20]:
        print(f"  {p['integrity']:9s} {p['now']:14s} {p['stick']} [{p['kind']}] {p['seal'][:12]} {p['claim'][:70]}")
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
