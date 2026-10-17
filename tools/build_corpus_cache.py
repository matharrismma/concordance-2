#!/usr/bin/env python3
"""Build, time, or PROVE the corpus cache for the keeping (issue #10, concordance/corpus_cache.py).

A cold `corpus.default_corpus()` rebuilds the whole index from the JSONL on every boot (measured 2026-10-16:
1337 s / 5.9 GB peak for 932k cards). With the cache, the first boot builds + saves and every later boot loads.
This tool does that boot on purpose, reports where the time and memory went, and — with --verify — proves
that a cache-loaded corpus and a fresh build are the SAME corpus.

    PYTHONPATH=src python tools/build_corpus_cache.py              # boot once (miss: build + save; hit: load); report
    PYTHONPATH=src python tools/build_corpus_cache.py --rebuild    # ignore an existing cache file, write afresh
    PYTHONPATH=src python tools/build_corpus_cache.py --verify     # THE PARITY PROOF: a fresh build (saving the
                                                                   # cache) and then a cache load, each in its OWN
                                                                   # subprocess (never two corpora in one process —
                                                                   # the box is memory-bound), compared check by check
    PYTHONPATH=src python tools/build_corpus_cache.py --snapshot out.json   # (what --verify runs) boot + write the battery

Env: CONCORDANCE_DATA_DIR (the keeping), CONCORDANCE_CORPUS_CACHE_DIR (where the cache lives; default
<data>/.cache), CONCORDANCE_CORPUS_CACHE (1 / 0 / rebuild), CONCORDANCE_FREEZE_SHELVES (part of the key).
Exit status: 0 when every check agrees (or on a plain build), 1 on any difference or a load that did not hit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# twenty fixed queries across the shelves: verse lookups, how-to, science, tradition, a plural, a typo-free rare word
QUERIES = ["Philippians 4:13", "photosynthesis", "southern baptists", "how to purify water",
           "fine structure constant", "Wesleyan church", "zymurgy", "Riemann hypothesis", "Genesis 1:1",
           "the LORD is my shepherd", "speed of light", "hydrogen", "Augustine confessions", "navier stokes",
           "sodium chloride", "trinity", "grimm's law", "pythagorean theorem", "mitochondria", "covenant of grace"]


def _peak_rss_mb() -> float | None:
    """Peak resident set of THIS process, in MB — Windows via psapi, POSIX via getrusage."""
    try:
        if os.name == "nt":
            import ctypes
            import ctypes.wintypes as w

            class _PMC(ctypes.Structure):
                _fields_ = [("cb", w.DWORD), ("PageFaultCount", w.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
            k32 = ctypes.windll.kernel32
            k32.GetCurrentProcess.restype = w.HANDLE
            f = ctypes.windll.psapi.GetProcessMemoryInfo
            f.argtypes = [w.HANDLE, ctypes.POINTER(_PMC), w.DWORD]
            f.restype = w.BOOL
            pmc = _PMC()
            pmc.cb = ctypes.sizeof(_PMC)
            if not f(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
                return None
            # the larger of the two peaks: the working set can be trimmed under memory pressure while the
            # committed (pagefile-backed) footprint cannot, so PeakPagefileUsage is the honest ceiling there
            return round(max(pmc.PeakWorkingSetSize, pmc.PeakPagefileUsage) / 1048576, 1)
        import resource
        ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return round((ru / 1024) if sys.platform != "darwin" else (ru / 1048576), 1)
    except Exception:  # noqa: BLE001
        return None


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


def battery(cp) -> dict:
    """The parity battery over a loaded corpus: counts, the public order's ends, 20 searches' top-10, 20 cards'
    connections(), stats(), and content hashes over the raw structures (every card in sample, every posting in
    sample, the whole public order, the whole call tree)."""
    from concordance import corpus
    ps = cp._public_sorted
    n = len(ps)
    fixed = [ps[i * n // 20] for i in range(20)] if n >= 20 else list(ps)
    toks = list(cp._by_token)
    calls = list(cp._cids_by_call)
    cards_order = list(cp.cards)
    return {
        "counts": {"resident": len(cp.cards), "frozen": len(cp._frozen), "public": n, "n": cp._n,
                   "tokens": len(toks), "postings": sum(len(v) for v in cp._by_token.values()),
                   "calls": len(calls), "df_extra": len(cp._df_extra), "min_idf": cp.min_idf, "froze": cp._froze},
        "public_first_50": ps[:50], "public_last_50": ps[-50:],
        "cards_first_50": cards_order[:50], "cards_last_50": cards_order[-50:],
        "search_top10": {q: [h.get("id") for h in corpus.search(q, limit=10)] for q in QUERIES},
        "connections": {cid: corpus.connections(cid, limit=10) for cid in fixed},
        "stats": corpus.stats(),
        "hash": {
            "cards_every_500th": _sha([cp.cards[c] for c in cards_order[::500]]),
            "cards_all_ids_titles": _sha([(c, (cp.cards[c].get("title") or "")) for c in cards_order]),
            "postings_every_1000th_token": _sha([(t, cp._by_token[t]) for t in toks[::1000]]),
            "postings_df_all": _sha([len(cp._by_token[t]) for t in toks]),
            "cids_by_call_every_100th": _sha([(c, cp._cids_by_call[c]) for c in calls[::100]]),
            "public_sorted_all": hashlib.sha256("\n".join(ps).encode("utf-8")).hexdigest(),
            "call_tree": _sha(cp._call_tree),
            "frozen_every_1000th": _sha(list(cp._frozen.items())[::1000]),
            "df_extra_every_1000th": _sha(sorted(cp._df_extra.items())[::1000]),
        },
    }


def boot() -> tuple:
    """default_corpus() once, timed; returns (corpus, phases, seconds)."""
    from concordance import corpus
    corpus._DEFAULT = None
    t0 = time.perf_counter()
    cp = corpus.default_corpus()
    return cp, dict(corpus.LOAD_PHASES), time.perf_counter() - t0


def report(ph: dict, secs: float) -> dict:
    state = ph.get("corpus_cache")
    out = {"corpus_cache": state, "boot_s": round(secs, 1), "peak_rss_mb": _peak_rss_mb(),
           "resident_cards": ph.get("resident_cards"), "frozen_index": ph.get("frozen_index"),
           "file": ph.get("corpus_cache_file")}
    if state == "hit":
        out["cache_load_s"] = round((ph.get("corpus_cache_load_ms") or 0.0) / 1000.0, 1)
    else:
        out["load_cards_s"] = round((ph.get("load_cards_ms") or 0.0) / 1000.0, 1)
        out["index_build_s"] = round((ph.get("index_build_ms") or 0.0) / 1000.0, 1)
        out["cold_build_s"] = round((ph.get("total_ms") or 0.0) / 1000.0, 1)
        out["cache_write_s"] = round((ph.get("corpus_cache_save_ms") or 0.0) / 1000.0, 1)
        out["cache_saved"] = ph.get("corpus_cache_saved")
        try:
            f = ph.get("corpus_cache_file")
            out["cache_file_mb"] = round(Path(f).stat().st_size / 1048576, 1) if f and Path(f).exists() else None
        except OSError:
            out["cache_file_mb"] = None
    return out


def _snapshot(out: Path) -> int:
    cp, ph, secs = boot()
    rep = report(ph, secs)
    print(json.dumps(rep, indent=1), flush=True)
    t0 = time.perf_counter()
    bat = battery(cp)
    rep["battery_s"] = round(time.perf_counter() - t0, 1)
    rep["peak_rss_mb"] = _peak_rss_mb()
    out.write_text(json.dumps({"report": rep, "battery": bat}, ensure_ascii=False, default=str), encoding="utf-8")
    return 0


def _run(mode: str, out: Path) -> dict:
    env = dict(os.environ, CONCORDANCE_CORPUS_CACHE=mode, PYTHONIOENCODING="utf-8",
               PYTHONPATH=os.pathsep.join(x for x in (str(ROOT / "src"), os.environ.get("PYTHONPATH", "")) if x))
    cmd = [sys.executable, str(Path(__file__).resolve()), "--snapshot", str(out)]
    print(f"$ CONCORDANCE_CORPUS_CACHE={mode} {' '.join(cmd[1:])}", flush=True)
    rc = subprocess.call(cmd, env=env)
    if rc != 0 or not out.exists():
        raise SystemExit(f"snapshot failed (rc={rc})")
    return json.loads(out.read_text(encoding="utf-8"))


def _diff(a, b, path="", out=None) -> list:
    out = [] if out is None else out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            _diff(a.get(k), b.get(k), f"{path}.{k}" if path else str(k), out)
    elif a != b:
        out.append(path)
    return out


def _verify(workdir: Path) -> int:
    workdir.mkdir(parents=True, exist_ok=True)
    fresh = _run("rebuild", workdir / "fresh.json")        # a cold build that SAVES the cache
    loaded = _run("1", workdir / "loaded.json")            # a boot that must LOAD it
    ra, rb = fresh["report"], loaded["report"]
    print("\n== THE FOUR NUMBERS ==")
    print(f"cold build   {ra.get('cold_build_s')} s  (load_cards {ra.get('load_cards_s')} s + index {ra.get('index_build_s')} s)"
          f"   peak {ra.get('peak_rss_mb')} MB")
    print(f"cache write  {ra.get('cache_write_s')} s   file {ra.get('cache_file_mb')} MB   saved={ra.get('cache_saved')}")
    print(f"cache load   {rb.get('cache_load_s')} s   (boot {rb.get('boot_s')} s)   peak {rb.get('peak_rss_mb')} MB"
          f"   state={rb.get('corpus_cache')}")
    print(f"cards        {ra.get('resident_cards')} resident + {ra.get('frozen_index')} frozen")
    print("\n== PARITY (fresh build vs cache load) ==")
    diffs = _diff(fresh["battery"], loaded["battery"])
    for k in ("counts", "public_first_50", "public_last_50", "cards_first_50", "cards_last_50",
              "search_top10", "connections", "stats", "hash"):
        bad = [d for d in diffs if d == k or d.startswith(k + ".")]
        print(f"  {k:18s} {'SAME' if not bad else 'DIFFERS: ' + ', '.join(bad[:6])}")
    ok = not diffs and rb.get("corpus_cache") == "hit"
    print("\nVERDICT:", "IDENTICAL — the cache-loaded corpus is the fresh build" if ok
          else ("DIFFERS" if diffs else "NOT A HIT — the second boot did not load the cache"))
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--rebuild", action="store_true", help="ignore an existing cache file; build and write afresh")
    ap.add_argument("--verify", action="store_true", help="fresh build vs cache load in two subprocesses, compared")
    ap.add_argument("--snapshot", metavar="OUT.json", help="(internal) boot and write the parity battery")
    ap.add_argument("--workdir", default=None, help="--verify: where the two snapshots go (default: the cache dir)")
    a = ap.parse_args(argv)
    if a.snapshot:
        return _snapshot(Path(a.snapshot))
    if a.verify:
        from concordance import corpus, corpus_cache
        wd = Path(a.workdir) if a.workdir else corpus_cache.cache_dir(corpus._cards_path().parent) / "verify"
        return _verify(wd)
    if a.rebuild:
        os.environ["CONCORDANCE_CORPUS_CACHE"] = "rebuild"
    cp, ph, secs = boot()
    print(json.dumps(report(ph, secs), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
