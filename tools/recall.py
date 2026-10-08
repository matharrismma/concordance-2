#!/usr/bin/env python3
"""THE RECALL SET — per-extractor phrasing recall, ratcheted (the failure report H1, Matt, 2026-10-08).

The report: "Listed extractors miss ordinary phrasing. Hourly-to-annual pay failed in 3 phrasings... Percent-of failed
as '27 is 71% of 42' but worked as '15% of 200 is 40'. Fix: build a phrasing test set per extractor from real
documents and report recall."

data/recall_phrasings.json holds, per extractor FAMILY, the ways a claim of that kind is actually written — in the
registers of real documents (an invoice line, a news sentence, a textbook sentence, a forum post, a report bullet, a
spreadsheet note), each with its truth worked by hand, true and false side by side. Authored in those registers, not
scraped: every row is a claim whose truth is known exactly, which a scraped sentence is not.

Each phrasing goes through the real front door (audit.audit, sealing off, no corpus) and is judged exactly as the
front-door benchmark judges (tools/frontdoor.judge): reached = some extractor fired; correct = reached and the verdict
matches the truth; a false positive is a false claim confirmed. RECALL per family = reached / phrasings; the number
the report asked for. The ratchet is frontdoor's: the floor is every phrasing that has EVER been reached-and-correct;
a regression is a floor phrasing not correct tonight, or any false positive; `--gate` exits 1 on regression so the
deploy refuses itself. A phrasing reached by a DIFFERENT family than the one it was written for still counts as
reached (the engine reached it); the row records which extractor fired.

    PYTHONPATH=src python tools/recall.py              # run, write data/recall.json + the floor, print one line
    PYTHONPATH=src python tools/recall.py --gate       # same; exit 1 on regression
    PYTHONPATH=src python tools/recall.py --dry-run    # run, print, write nothing
    PYTHONPATH=src python tools/recall.py --verbose    # one line per family, then every miss
"""
from __future__ import annotations

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


def _data_dir() -> Path:
    return Path(os.environ.get("CONCORDANCE_DATA_DIR") or (ROOT / "data"))


def bench(families: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Every phrasing through the front door, judged as the front-door benchmark judges. Pure but for the engine."""
    from concordance import audit as _audit
    from concordance.config import EngineConfig
    from frontdoor import judge
    cfg = EngineConfig("secular")
    rows: List[Dict[str, Any]] = []
    for fam, items in families.items():
        for i, it in enumerate(items, 1):
            claim = {"id": it.get("id") or f"{fam}_{i}", "truth": bool(it.get("truth"))}
            try:
                rep = _audit.audit(it["text"], cfg, seal=False, index=False, card=False)
            except Exception as e:  # noqa: BLE001 — a crash is a miss, recorded, never a verdict
                rep = {"claims_found": 0, "results": [], "verdict": "ERROR", "note": str(e)[:200]}
            row = judge(claim, rep)
            row.update({"family": fam, "register": it.get("register"), "text": it["text"], "verdict": rep.get("verdict")})
            rows.append(row)
    return rows


def run(dry_run: bool = False, data_dir: Optional[Path] = None, phrasings_path: Optional[Path] = None,
        verbose: bool = False) -> Dict[str, Any]:
    t0 = time.time()
    data = Path(data_dir) if data_dir else _data_dir()
    ppath = Path(phrasings_path) if phrasings_path else data / "recall_phrasings.json"
    if not ppath.exists() and not phrasings_path:
        ppath = ROOT / "data" / "recall_phrasings.json"          # the set ships with the repo; the data dir may be elsewhere
    out_path = data / "recall.json"
    floor_path = data / "recall.floor.json"
    families: Dict[str, List[Dict[str, Any]]] = {}
    if ppath.exists():
        families = json.loads(ppath.read_text(encoding="utf-8")).get("families") or {}
    # WARM THE KEEPING FIRST (2026-10-08). The shelf-reading checks (syllables, rhyme, origin ...) read the
    # corpus but never build it inside a verify budget (corpus.loaded()); so the gate builds it here, once,
    # before the clock starts - on the box that is the frozen-cache boot (~18 s), in a test's empty data dir
    # it is nothing. Without this every shelf-reading phrasing was shed as SYSTEM_ERROR and never judged.
    t_warm = time.time()
    corpus_state = "none"
    if (data / "cards.jsonl").exists():
        try:
            from concordance import corpus as _corpus
            _corpus.default_corpus()
            corpus_state = "warm"
        except Exception as e:  # noqa: BLE001 - a keeping that will not load is reported, never hidden
            corpus_state = f"failed: {str(e)[:120]}"
    warm_s = round(time.time() - t_warm, 1)
    rows = bench(families)
    floor: List[str] = []
    if floor_path.exists():
        try:
            floor = list(json.loads(floor_path.read_text(encoding="utf-8")).get("claims") or [])
        except (OSError, ValueError):
            floor = []
    correct_now = {r["id"] for r in rows if r["correct"]}
    floor_set = set(floor) | correct_now
    by_id = {r["id"]: r for r in rows}
    regressions = sorted(i for i in floor_set if i in by_id and not by_id[i]["correct"])
    regressions += [f"false positive: {r['id']}" for r in rows if r["false_positive"]]
    per: Dict[str, Dict[str, Any]] = {}
    for fam in families:
        fr = [r for r in rows if r["family"] == fam]
        n = len(fr)
        per[fam] = {"phrasings": n, "reached": sum(1 for r in fr if r["reached"]),
                    "correct": sum(1 for r in fr if r["correct"]),
                    "false_positives": sum(1 for r in fr if r["false_positive"]),
                    "false_negatives": sum(1 for r in fr if r["false_negative"]),
                    "recall": round(sum(1 for r in fr if r["reached"]) / n, 3) if n else None,
                    "missed": [r["text"] for r in fr if not r["reached"]]}
    n = len(rows)
    reached = sum(1 for r in rows if r["reached"])
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "host": socket.gethostname(), "seconds": round(time.time() - t0, 1),
        "corpus": corpus_state, "corpus_warm_seconds": warm_s,
        "families": len(families), "phrasings": n, "reached": reached, "correct": len(correct_now),
        "recall": round(reached / n, 3) if n else None,
        "false_positives": sum(1 for r in rows if r["false_positive"]),
        "false_negatives": sorted(r["id"] for r in rows if r["false_negative"]),
        "fully_reached_families": sorted(f for f, p in per.items() if p["phrasings"] and p["reached"] == p["phrasings"]),
        "weakest_families": [f for f, _ in sorted(per.items(), key=lambda kv: (kv[1]["recall"] or 0, kv[0]))[:8]],
        "newly_correct": sorted(correct_now - set(floor)),
        "regressions": regressions, "regressed": bool(regressions),
        "floor": len(floor_set),
        "per_family": per, "rows": rows,
        "about": ("Per-extractor phrasing recall (the failure report H1, 2026-10-08): the ways a claim of each kind is "
                  "actually written, in the registers of real documents, each truth worked by hand, through the real "
                  "front door and judged as the front-door benchmark judges. Recall = reached / phrasings; false "
                  "positives must be 0; ratcheted against every phrasing ever reached-and-correct. Authored in those "
                  "registers, not scraped, so every truth is exact."),
    }
    if verbose:
        for fam, p in sorted(per.items(), key=lambda kv: (kv[1]["recall"] or 0, kv[0])):
            print(f"  {fam:<22} recall {p['reached']}/{p['phrasings']}  correct {p['correct']}  "
                  f"fp {p['false_positives']}  fn {p['false_negatives']}")
        for r in rows:
            if r["false_positive"] or r["false_negative"]:
                print(f"  !! {'FP' if r['false_positive'] else 'FN'} {r['id']}: {r['text']}  [{r['verdict']}] {r['detail'][:100]}")
        for r in rows:
            if not r["reached"]:
                print(f"  -- miss {r['id']:<22} [{r['register']}] {r['text']}")
    if not dry_run:
        data.mkdir(parents=True, exist_ok=True)
        tmp = out_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, out_path)
        floor_path.write_text(json.dumps({"claims": sorted(floor_set), "updated_at": summary["generated_at"]},
                                         indent=1), encoding="utf-8")
    return summary


def main(argv: Optional[List[str]] = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    s = run(dry_run="--dry-run" in a, verbose="--verbose" in a)
    print(f"{s['generated_at']} RECALL {'REGRESSED' if s['regressed'] else 'OK'}: reached {s['reached']}/{s['phrasings']} "
          f"({(s['recall'] or 0) * 100:.0f}%) over {s['families']} families, correct {s['correct']}/{s['phrasings']}, "
          f"false positives {s['false_positives']}, false negatives {s['false_negatives']}, fully reached "
          f"{len(s['fully_reached_families'])}, weakest {s['weakest_families'][:4]}, newly correct {len(s['newly_correct'])}, "
          f"regressions {s['regressions']}; {s['seconds']}s")
    if "--gate" in a and s["regressed"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
