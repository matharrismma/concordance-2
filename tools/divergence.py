#!/usr/bin/env python3
"""THE DIVERGENCE SWEEP — find the defect where the copy left its source.

    PYTHONPATH=src python tools/divergence.py            # every check, with its coverage
    PYTHONPATH=src python tools/divergence.py --json     # for the Keep

Matt, 2026-08-01, asked how to find the source of a defect and answered it in the same breath:
*"It would be areas we diverge from source."*

That is not a metaphor — it is the diagnostic that would have caught every failure of the last
two days, each of which was a COPY that had drifted from what it was derived from:

  * the SQLite shards drifted from cards.jsonl — 4,039 citations repaired in the file still
    served the old text, and the check that "proved" the repair only ever read the file;
  * the box drifted from the repo — three modules deleted here lived on there for days;
  * a RUNNING PROCESS drifted from its own file on disk — /wants answered 500 while the
    identical code served 200 in a fresh interpreter, and a restart healed it;
  * the traffic rollup drifted from the logs it claimed to summarize (one readable file of three);
  * cards' source.url drifted from what actually resolves (the encyclopedia/canon shims).

Every check here names its COVERAGE before its verdict — what it read, how many rows — because a
check that silently examines a subset is the very failure it is meant to catch.

Verdicts are three-state, never two: AGREES · DIVERGED · CANNOT_CHECK. "We could not look" is a
fact about us and is never reported as agreement.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

AGREES, DIVERGED, CANNOT = "AGREES", "DIVERGED", "CANNOT_CHECK"


def _data_dir() -> Path:
    return Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or (ROOT / "data"))


def check_shards_against_the_file(sample: int = 400) -> dict:
    """THE SHARDS vs cards.jsonl — the drift that cost 4,039 citations.

    A frozen shelf serves its body from SQLite; the file is the source. Sampling is honest here
    and the sample size is reported: a full compare would read 550k cards.
    """
    import sqlite3
    d = _data_dir() / "shards"
    src = _data_dir() / "cards.jsonl"
    if not d.exists() or not src.exists():
        return {"check": "shards ↔ cards.jsonl", "verdict": CANNOT,
                "coverage": f"shards dir {'present' if d.exists() else 'MISSING'}, "
                            f"cards.jsonl {'present' if src.exists() else 'MISSING'}"}
    shard_cards: dict = {}
    dbs = sorted(d.glob("*.db"))
    for db in dbs:
        try:
            conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        except sqlite3.Error:
            continue
        try:
            for cid, js in conn.execute("select id, json from cards limit ?", (sample,)):
                shard_cards.setdefault(cid, js)
        except sqlite3.Error:
            pass
        finally:
            conn.close()
    if not shard_cards:
        return {"check": "shards ↔ cards.jsonl", "verdict": CANNOT,
                "coverage": f"{len(dbs)} shard file(s), no rows read"}
    diffs, compared = [], 0
    with open(src, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                c = json.loads(line)
            except ValueError:
                continue
            js = shard_cards.get(c.get("id"))
            if js is None:
                continue
            compared += 1
            try:
                sc = json.loads(js)
            except ValueError:
                diffs.append((c.get("id"), "shard row is not JSON"))
                continue
            for field in ("title", "body"):
                if str(sc.get(field) or "") != str(c.get(field) or ""):
                    diffs.append((c.get("id"), f"{field} differs"))
                    break
            else:
                if str((sc.get("source") or {}).get("url") or "") != \
                   str((c.get("source") or {}).get("url") or ""):
                    diffs.append((c.get("id"), "source.url differs"))
    return {"check": "shards ↔ cards.jsonl",
            "verdict": DIVERGED if diffs else (AGREES if compared else CANNOT),
            "coverage": f"{len(dbs)} shard file(s), {len(shard_cards):,} rows sampled, "
                        f"{compared:,} matched against the file",
            "diverged": len(diffs), "examples": diffs[:5]}


def check_receipt_cards_against_the_cas() -> dict:
    """RECEIPT CARDS vs the CAS — the card carries the record; the hash must still recompute."""
    from concordance import cas, corpus
    cards = [c for c in corpus.default_corpus().cards.values() if c.get("shelf") == "seals"]
    if not cards:
        return {"check": "receipt cards ↔ CAS", "verdict": CANNOT,
                "coverage": "no receipt cards in the keeping yet"}
    bad = []
    for c in cards:
        h = str((c.get("extra") or {}).get("seal_hash") or "")
        if cas.card_to_record(c) is None:
            bad.append((c.get("id"), "carried record does not recompute to its address"))
        elif cas.exists(h):
            obj = cas.fetch(h) or {}
            rec = cas.card_to_record(c) or {}
            if {k: v for k, v in obj.items() if k != "content_hash"} != \
               {k: v for k, v in rec.items() if k != "content_hash"}:
                bad.append((c.get("id"), "card and CAS object differ"))
    return {"check": "receipt cards ↔ CAS",
            "verdict": DIVERGED if bad else AGREES,
            "coverage": f"{len(cards):,} receipt card(s) checked, hash-recomputed",
            "diverged": len(bad), "examples": bad[:5]}


def check_citations_resolve() -> dict:
    """CARDS' source.url vs what this build can actually answer — the shim drift."""
    from concordance import corpus
    from concordance.web import api
    routes = {r["path"] for r in api.ROUTES}
    retired_paths = set(api._RETIRED) | {r["path"] for r in api.ROUTES if r.get("retired")}
    pages = {p.name for p in (ROOT / "site").glob("*.html")}
    cards = list(corpus.default_corpus().cards.values())
    dead: dict = {}
    checked = 0
    for c in cards:
        u = str((c.get("source") or {}).get("url") or "")
        if not u.startswith("/"):
            continue                       # external or absent — not ours to resolve
        checked += 1
        # CHECK THE INSTRUMENT FIRST. The first run of this sweep reported 352 divergences, and
        # two of its top five were the checker's own fault: it kept the "#fragment" (so a retired
        # page with an anchor looked unserved) and it only knew the _RETIRED dict, missing
        # /daily.html — which is served by its own handler and marked `retired` in the registry.
        base = u.split("?")[0].split("#")[0]
        if base in retired_paths:
            continue                       # a retired path IS served: it redirects, by design
        if base.endswith(".html"):
            if base.lstrip("/") not in pages:
                dead[base] = dead.get(base, 0) + 1
        elif not (base in routes or base.startswith("/card/") or base.startswith("/s/")):
            dead[base] = dead.get(base, 0) + 1
    return {"check": "card citations ↔ what this build serves",
            "verdict": DIVERGED if dead else AGREES,
            "coverage": f"{len(cards):,} cards, {checked:,} carrying an internal citation",
            "diverged": sum(dead.values()),
            "examples": sorted(dead.items(), key=lambda x: -x[1])[:5]}


def check_sitemap_against_the_pages() -> dict:
    """THE SITEMAP vs site/ — a sitemap naming a page that is gone teaches crawlers a lie."""
    from concordance.web import api
    pages = {p.name for p in (ROOT / "site").glob("*.html")}
    listed = [p for p in api._SITEMAP_PAGES if p.endswith(".html")]
    missing = [p for p in listed if p.lstrip("/") not in pages]
    return {"check": "sitemap ↔ site/*.html",
            "verdict": DIVERGED if missing else AGREES,
            "coverage": f"{len(listed)} page(s) listed, {len(pages)} on disk",
            "diverged": len(missing), "examples": missing[:5]}


def check_manifest_against_the_tests() -> dict:
    """THE SUITE vs its manifest — the gate's own guard, run here too so the sweep is whole."""
    man = ROOT / "tests" / "MANIFEST.txt"
    if not man.exists():
        return {"check": "tests ↔ MANIFEST.txt", "verdict": CANNOT, "coverage": "no manifest"}
    want = {ln.strip() for ln in man.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.startswith("#")}
    have = {p.name for p in (ROOT / "tests").glob("test_*.py")}
    diff = sorted((want - have) | (have - want))
    return {"check": "tests ↔ MANIFEST.txt",
            "verdict": DIVERGED if diff else AGREES,
            "coverage": f"{len(want)} listed, {len(have)} on disk",
            "diverged": len(diff), "examples": diff[:5]}


CHECKS = (check_shards_against_the_file, check_receipt_cards_against_the_cas,
          check_citations_resolve, check_sitemap_against_the_pages,
          check_manifest_against_the_tests)


def main() -> int:
    # The gate runs alone (tools/check.py holds .gate.lock): a heavy job beside it has produced
    # three false failures by starving a wire test. Step aside rather than corrupt a verdict.
    if os.path.exists(os.path.join(ROOT, ".gate.lock")):
        print("the gate holds the floor — run this after it finishes")
        return 2
    results = []
    for fn in CHECKS:
        try:
            results.append(fn())
        except Exception as exc:  # noqa: BLE001 — a check that dies says so; it never says AGREES
            results.append({"check": fn.__name__, "verdict": CANNOT,
                            "coverage": f"the check itself failed: {type(exc).__name__}: {exc}"})
    if "--json" in sys.argv:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=1))
        return 1 if any(r["verdict"] == DIVERGED for r in results) else 0

    print("THE DIVERGENCE SWEEP — where has a copy left its source?\n")
    for r in results:
        mark = {AGREES: "  ok  ", DIVERGED: " DIFF ", CANNOT: " ??   "}[r["verdict"]]
        print(f"{mark} {r['check']}")
        print(f"        coverage: {r['coverage']}")
        if r.get("diverged"):
            print(f"        DIVERGED: {r['diverged']:,}")
            for e in r.get("examples") or []:
                print(f"           {e}")
    n_diff = sum(1 for r in results if r["verdict"] == DIVERGED)
    n_cant = sum(1 for r in results if r["verdict"] == CANNOT)
    print(f"\n{len(results)} check(s): {len(results) - n_diff - n_cant} agree, {n_diff} diverged, "
          f"{n_cant} could not be checked.")
    if n_cant:
        print("A check that could not run is NOT a pass — it is a hole in the instrument.")
    return 1 if n_diff else 0


if __name__ == "__main__":
    sys.exit(main())
