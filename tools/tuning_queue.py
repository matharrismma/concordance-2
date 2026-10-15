#!/usr/bin/env python3
"""Tuning queue — turn the Hodge curl's worst triangles into an actionable vocabulary queue, READ-ONLY.

hodge_probe names WHERE the routing preferences do not close (the intransitive triangles). The fixable
unit is one rung down: a PHRASE shared between two competing domains. This tool, for the worst curl
triangles, lists every shared phrase on their edges with:
  - its SOURCE (alias / curated synonym / verify_* function name / leaked docstring word), by raw weight;
  - its domain-frequency df (how many domains claim it at all);
  - a VERDICT HINT: a generic word leaked into several domains is SPURIOUS (remove it / add to _STOP); a
    phrase in two genuinely-related domains is LEGITIMATE (leave it — the idf decorr already down-weights
    it, and either verifier would see the same claim).
The operator curates (keeps what aligns, removes the leak); the tool only makes the queue visible. Nothing
is changed here. Run with CONCORDANCE_DECORR=off so the raw sources show.

    PYTHONPATH=src CONCORDANCE_DECORR=off python tools/tuning_queue.py [--tris N] [--all]
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))


def _sources():
    """Classify how each phrase entered the index, from the raw (pre-decorr) signals."""
    from concordance import domain_resolver as DR
    from concordance.verifiers import VERIFIERS
    DR._build()
    aliases = {k.replace("_", " ") for k in VERIFIERS}
    syn = {t for terms in DR._SYNONYMS.values() for t in terms}
    def src(phrase, weight):
        if phrase in aliases:
            return "alias"
        if phrase in syn:
            return "synonym"
        if weight >= 1.5:
            return "function"       # verify_* name or its words (weight 2.0 / 1.5)
        return "docstring"          # idf-weighted docstring word (<= ~1.05)
    return src


def run(n_tris=10, show_all=False):
    import hodge_probe as HP
    from concordance import domain_resolver as DR
    DR._build()
    idx = DR._INDEX
    ndom = len(DR._DOMAINS)
    src = _sources()

    pref_sum, pref_cnt, _ = HP.collect()
    H = HP.hodge(pref_sum, pref_cnt)
    worst = [t for t in H["worst_tri"] if abs(t[1]) > 1e-6][:n_tris]

    # gather the competing domain PAIRS from the worst triangles (each triangle = 3 edges)
    pairs = {}
    for (a, b, c), circ in worst:
        for x, y in ((a, b), (b, c), (a, c)):
            key = tuple(sorted((x, y)))
            pairs[key] = max(pairs.get(key, 0.0), abs(circ))

    print("=" * 78)
    print("TUNING QUEUE - shared vocabulary on the worst curl triangles' edges (read-only)")
    print("  from %d intransitive triangles -> %d competing domain pairs" % (len(worst), len(pairs)))
    print("=" * 78)

    rows = []
    for (a, b), impact in sorted(pairs.items(), key=lambda kv: -kv[1]):
        sa, sb = set(idx), set(idx)  # placeholder
        shared = [p for p, doms in idx.items() if a in doms and b in doms]
        for p in shared:
            doms = idx[p]
            df = len(doms)
            # classify on the stronger of the two raw weights (decorr off => raw)
            w = max(doms[a], doms[b])
            source = src(p, w)
            # verdict hint: generic/leaked if it reaches many domains or is a bare docstring word in >2
            if source == "docstring" and df >= 4:
                hint = "SPURIOUS (generic docstring leak -> _STOP)"
            elif source == "docstring" and df >= 3:
                hint = "review (docstring word in 3 domains)"
            elif source in ("synonym", "alias") and df >= 4:
                hint = "review (curated term claimed by %d domains)" % df
            else:
                hint = "legitimate (2 related domains; decorr handles)"
            rows.append((impact, a, b, p, df, source, hint))

    # print grouped by pair, worst pair first
    seen_pair = None
    shown = 0
    for impact, a, b, p, df, source, hint in sorted(rows, key=lambda r: (-r[0], r[1], r[2], -len(r[3]))):
        pair = (a, b)
        if pair != seen_pair:
            print("\n%-22s ~ %-22s  (curl impact %.2f)" % (a, b, impact))
            seen_pair = pair
        if ("SPURIOUS" in hint) or ("review" in hint) or show_all:
            print("   [df=%2d %-9s] %-28s %s" % (df, source, p[:28], hint))
            shown += 1
    if not shown:
        print("\n  (no shared phrases flagged — the competition is structural, not a vocabulary leak)")

    # summary: the spurious leaks across all pairs, deduped — the first thing to fix
    leaks = sorted({p for _, _, _, p, df, s, h in rows if "SPURIOUS" in h})
    print("\n" + "-" * 78)
    print("SPURIOUS LEAKS (generic docstring words in >=4 domains) — the queue's top of list:")
    if leaks:
        for p in leaks:
            doms = sorted(DR._INDEX[p].keys())
            print("   %-24s in %2d domains: %s" % (p, len(doms), ", ".join(doms)[:60]))
    else:
        print("   (none)")
    print("\nNext: remove the leaks (add to _STOP / tighten the docstring harvest), then re-run")
    print("hodge_probe + dispatch_probe + recall — curl and cross-talk down, recall unchanged.")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tris", type=int, default=10)
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args(argv)
    run(a.tris, a.all)


if __name__ == "__main__":
    raise SystemExit(main())
