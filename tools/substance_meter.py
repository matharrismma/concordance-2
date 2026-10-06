#!/usr/bin/env python3
"""THE SUBSTANCE METER — measure the keeping's substance-vs-stub ratio over the WHOLE corpus and write
data/substance.json, so The Bridge shows a real needle instead of an estimate (Matt, 2026-10-06).

    PYTHONPATH=src CONCORDANCE_DATA_DIR=<dir> python tools/substance_meter.py        # writes <dir>/substance.json

Substance = a card whose body is >= ops.STUB_BODY_CHARS (it answers something); a stub is a pointer.
Connection edges are excluded. The resident cards are judged by ops.substance; the frozen shelves are
judged from the shard bodies (cards.json), which the resident walk cannot see (an in-memory frozen card is
a stripped stub). This is a COMPOSITION count, not a judgment of brief-by-nature reference (a taxon, a
headword) — those are relationally complete and the count says nothing against them.
"""
from __future__ import annotations

import glob
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def _data_dir() -> Path:
    return Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data")


def measure() -> dict:
    from concordance import corpus, ops
    thr = ops.STUB_BODY_CHARS
    res = ops.substance(corpus.default_corpus().cards)      # resident (non-frozen), the engine's own walk
    by_shard: dict = {}
    fsub = fstub = frows = 0
    for db in sorted(glob.glob(str(_data_dir() / "shards" / "*.db"))):
        con = sqlite3.connect(db)
        sub = stub = rows = 0
        try:
            cur = con.execute("SELECT json FROM cards")
            while True:
                batch = cur.fetchmany(5000)
                if not batch:
                    break
                for (js,) in batch:
                    try:
                        d = json.loads(js)
                    except Exception:  # noqa: BLE001
                        continue
                    if d.get("kind") == "connection":
                        continue
                    rows += 1
                    if len(str(d.get("body") or "")) >= thr:
                        sub += 1
                    else:
                        stub += 1
        finally:
            con.close()
        fsub += sub; fstub += stub; frows += rows
        by_shard[os.path.basename(db)] = {"cards": rows, "substance": sub, "stub": stub,
                                          "stub_ratio": round(stub / rows, 4) if rows else 0.0}
    holdings = res["measured_cards"] + frows
    substance = res["substance_cards"] + fsub
    stub = res["stub_cards"] + fstub
    return {
        "measured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "holdings": holdings, "substance": substance, "stub": stub,
        "substance_ratio": round(substance / holdings, 4) if holdings else 0.0,
        "stub_ratio": round(stub / holdings, 4) if holdings else 0.0,
        "threshold_chars": thr,
        "resident": {"measured": res["measured_cards"], "substance": res["substance_cards"],
                     "stub": res["stub_cards"]},
        "by_shard": by_shard,
        "note": ("substance = body >= %d chars (answers something); connection edges excluded; frozen "
                 "shelves measured from the shard bodies. A composition count, never a verdict against "
                 "brief-by-nature reference." % thr),
    }


def main() -> int:
    out = _data_dir() / "substance.json"
    data = measure()
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, out)
    print("substance %.1f%% (%d/%d holdings) -> %s"
          % (100 * data["substance_ratio"], data["substance"], data["holdings"], out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
