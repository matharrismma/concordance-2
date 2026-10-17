#!/usr/bin/env python3
"""THE TICK GOLDEN — prove a stick's sealed content is byte-identical across a refactor (issue #13).

    PYTHONPATH=src python tools/tick_golden.py snapshot [DIR]    # run every entry in an isolated keeping; write DIR/<name>.json
    PYTHONPATH=src python tools/tick_golden.py check [DIR]       # re-run every entry and diff against DIR; exit 1 on ANY difference
    PYTHONPATH=src python tools/tick_golden.py check DIR name... # only these entries
    PYTHONPATH=src python tools/tick_golden.py list              # the entries and how they are run

DIR defaults to tests/fixtures/tick_golden. Every entry runs in a FRESH temp CONCORDANCE_DATA_DIR (never a real
keeping, exactly as tools/mc_paths.py does) with the cold seal path (CONCORDANCE_SEAL_INDEX=0). What is kept per
entry is the canonical JSON of what the run SEALED and MARKED:

  * sticks — id, question, statement, field, references, and every tick in order: kind, claim, seal, source,
    up_to, unit, by (the fields the keeping stores; `at` is a timestamp and is not compared);
  * seals  — every CAS content hash the run minted (the hash IS the record: same nid/expr/value/tol/spec ->
    same hash), with the verifier names it carries for the reader;
  * rc     — the entry's return code.

Nothing printed is compared. A handler that takes a CLI argument runs at the argument pinned in GOLDEN_ARGS
(the CLI defaults); the pin is part of the golden.

Entries come from tick.py's catalog (tick.catalog_entries) when it has one — the data-driven dispatch —
and otherwise from the if-chain of tick.main() read by tools/tick_record.parse_dispatch (the pre-refactor
form), so the SAME harness snapshots the old functions and checks the new loader against them.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
os.environ["CONCORDANCE_SEAL_INDEX"] = "0"
os.environ.setdefault("CONCORDANCE_VERIFY_TIMEOUT_S", "1800")
os.environ.setdefault("CONCORDANCE_RIEMANN_MAX", "1e9")
os.environ.setdefault("WEB_FIND_DISABLED", "1")

DEFAULT_DIR = ROOT / "tests" / "fixtures" / "tick_golden"

# A handler with a CLI argument runs at the argument tick.main() defaults to (each is seconds, measured
# 2026-10-17). The pinned value is what the golden holds; the handler stays Python either way.
GOLDEN_ARGS = {
    "riemann": (100.0,),
    "riemann_li": (10,),          # the CLI default (30) is past the verifier's practical cap of 25 and refuses
    "robin": (1000000,),
    "schoenfeld": (2000000,),
    "lagarias": (1000000,),
    "nicolas": (1000000,),
    "count": (1000000000.0,),
    "bsd": ("11a1",),
}

TICK_FIELDS = ("kind", "claim", "seal", "source", "up_to", "unit", "by")


def entry_name(func_name: str) -> str:
    """The golden key for a tick.py function: its name without the stick_ prefix / _stick suffix."""
    n = func_name
    if n.startswith("stick_"):
        n = n[len("stick_"):]
    if n.endswith("_stick"):
        n = n[: -len("_stick")]
    return n


def _entries():
    """[(name, callable)] — every stick entry, each callable running it to completion and returning rc."""
    import tick as T
    if hasattr(T, "catalog_entries"):
        out = []
        for name, run in T.catalog_entries():
            out.append((name, (lambda run=run, name=name: run(*GOLDEN_ARGS.get(name, ())))))
        return out
    from tick_record import parse_dispatch
    out = []
    for fn_name, _aliases in parse_dispatch((ROOT / "tools" / "tick.py").read_text(encoding="utf-8")):
        fn = getattr(T, fn_name)
        name = entry_name(fn_name)
        out.append((name, (lambda fn=fn, name=name: fn(*GOLDEN_ARGS.get(name, ())))))
    return out


def _reset_cold_caches() -> None:
    """The cold seal path dedups cards within the process; a fresh keeping must start fresh."""
    try:
        from concordance import cas, science_cards
        cas._COLD_CARDS_WRITTEN.clear()
        cas._COLD_SPINE_WRITTEN = False
        science_cards._MINTED = None
    except Exception:  # noqa: BLE001
        pass


def dump_state(tmp: Path) -> dict:
    from concordance import tickstick
    sticks = {}
    for sid, st in sorted(tickstick.fold(tmp).items()):
        sticks[sid] = {"question": st.get("question"), "statement": st.get("statement") or "",
                       "field": st.get("field") or "", "references": list(st.get("references") or []),
                       "ticks": [{k: t[k] for k in TICK_FIELDS if k in t} for t in st["ticks"]]}
    seals = {}
    cas_dir = tmp / "cas"
    if cas_dir.exists():
        for p in sorted(cas_dir.rglob("*.json")):
            h = p.parent.name + p.stem
            try:
                rec = json.loads(p.read_text(encoding="utf-8"))
            except ValueError:
                rec = {}
            seals[h] = {"overall": rec.get("overall"),
                        "axis": (rec.get("axis_coords") or {}).get("axis"),
                        "verifiers": [v.get("name") for v in rec.get("verifier_results") or []]}
    return {"sticks": sticks, "seals": seals}


def run_entry(name: str, run) -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="nh_golden_"))
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = str(tmp)
    _reset_cold_caches()
    t0 = time.time()
    try:
        try:
            rc = run()
        except SystemExit as exc:  # noqa: PERF203
            rc = int(exc.code or 0)
        state = dump_state(tmp)
    finally:
        if prior is None:
            os.environ.pop("CONCORDANCE_DATA_DIR", None)
        else:
            os.environ["CONCORDANCE_DATA_DIR"] = prior
        shutil.rmtree(tmp, ignore_errors=True)
    return {"entry": name, "rc": rc, "seconds": round(time.time() - t0, 2), **state}


def _canon(d: dict) -> str:
    return json.dumps({k: v for k, v in d.items() if k != "seconds"}, sort_keys=True, ensure_ascii=False, indent=1)


def _diff(name: str, old: dict, new: dict) -> list:
    out = []
    if old.get("rc") != new.get("rc"):
        out.append(f"{name}: rc {old.get('rc')} -> {new.get('rc')}")
    os_, ns = old.get("sticks", {}), new.get("sticks", {})
    for sid in sorted(set(os_) | set(ns)):
        if sid not in os_:
            out.append(f"{name}: stick {sid} is NEW"); continue
        if sid not in ns:
            out.append(f"{name}: stick {sid} is MISSING"); continue
        a, b = os_[sid], ns[sid]
        for k in ("question", "statement", "field", "references"):
            if a.get(k) != b.get(k):
                out.append(f"{name}: {sid}.{k} differs")
        ta, tb = a.get("ticks", []), b.get("ticks", [])
        if len(ta) != len(tb):
            out.append(f"{name}: {sid} has {len(ta)} ticks in the golden, {len(tb)} now")
        for i, (x, y) in enumerate(zip(ta, tb)):
            if x != y:
                keys = sorted(k for k in set(x) | set(y) if x.get(k) != y.get(k))
                out.append(f"{name}: {sid} tick[{i}] ({x.get('kind')}) differs in {keys}")
    oh, nh = set(old.get("seals", {})), set(new.get("seals", {}))
    for h in sorted(oh - nh):
        out.append(f"{name}: seal {h[:16]} ({old['seals'][h].get('verifiers')}) is MISSING")
    for h in sorted(nh - oh):
        out.append(f"{name}: seal {h[:16]} ({new['seals'][h].get('verifiers')}) is NEW")
    return out


def main() -> int:
    a = sys.argv[1:]
    if not a or a[0] not in ("snapshot", "check", "list"):
        print(__doc__); return 2
    cmd = a[0]
    gdir = Path(a[1]) if len(a) > 1 else DEFAULT_DIR
    only = set(a[2:])
    entries = _entries()
    if cmd == "list":
        for name, _ in entries:
            print(f"{name:32s} args={GOLDEN_ARGS.get(name, ())}")
        print(len(entries), "entries"); return 0
    if only:
        entries = [(n, r) for n, r in entries if n in only]
        missing = only - {n for n, _ in entries}
        if missing:
            print("no such entry:", ", ".join(sorted(missing))); return 2
    gdir.mkdir(parents=True, exist_ok=True)
    diffs: list = []
    t0 = time.time()
    for i, (name, run) in enumerate(entries, 1):
        got = run_entry(name, run)
        p = gdir / f"{name}.json"
        if cmd == "snapshot":
            p.write_text(_canon(got) + "\n", encoding="utf-8")
            print(f"[{i}/{len(entries)}] {name}: rc={got['rc']} sticks={len(got['sticks'])} seals={len(got['seals'])} "
                  f"{got['seconds']}s", flush=True)
        else:
            if not p.exists():
                diffs.append(f"{name}: no golden at {p}")
                print(f"[{i}/{len(entries)}] {name}: NO GOLDEN", flush=True); continue
            want = json.loads(p.read_text(encoding="utf-8"))
            d = _diff(name, want, got)
            diffs.extend(d)
            print(f"[{i}/{len(entries)}] {name}: {'ok' if not d else 'DIFF x%d' % len(d)} "
                  f"(rc={got['rc']} sticks={len(got['sticks'])} seals={len(got['seals'])} {got['seconds']}s)", flush=True)
    print(f"\n{len(entries)} entries in {time.time() - t0:.0f}s")
    if cmd == "check":
        if diffs:
            print("\n".join(diffs))
            print(f"\nGOLDEN DIFF: {len(diffs)} difference(s)")
            return 1
        print("GOLDEN DIFF: zero differences")
    return 0


if __name__ == "__main__":
    sys.exit(main())
