#!/usr/bin/env python3
"""Hodge probe — the discrete Hodge/Helmholtz decomposition of the engine's routing, READ-ONLY.

DESIGN_FROM_THE_DOTS, the last of the "next measurements". The four-witnesses doctrine names the
assembled path's calculus: CURL = route-dependence of the verdict (verifiers should commute, so a true
answer is route-independent); GRADIENT = a consistent narrowing (a single potential explains every
preference); DIVERGENCE = unsourced content (every step cites a source, or records a miss). This tool
MEASURES those on the live router, with no model and nothing changed.

The router gives, for each query, domains with scores — a set of PAIRWISE PREFERENCES (domain a scored
above b). That is exactly the input to HodgeRank (Jiang, Lim, Ye, Guibas, "Statistical ranking and
combinatorial Hodge theory", Math. Programming 127 (2011) 203-244), the discrete Hodge decomposition of
a pairwise comparison flow on a graph:

    Y  =  grad(s)        +  curl(Phi)        +  harmonic
          a global rank      local 3-cycles      global cycles
          (route-independent) (a>b>c>a)          (not bounded by triangles)

grad is the part a single consistent domain ranking explains; curl + harmonic are the inconsistency —
route-dependence, the preference that NO global ranking can account for. curl = d1 (edges->triangles),
grad = d0 (nodes->edges); d1 d0 = 0 (curl of a gradient is zero) makes the three parts orthogonal, so
||Y||^2 = ||grad||^2 + ||curl||^2 + ||harmonic||^2 splits the preference energy exactly.

WHAT CARRIES OVER (named, per the bra-ket rule): the finite graph, d0/d1, the orthogonal split, the
Laplacian least-squares for the potential — all exact on a finite complex. WHAT DOES NOT: no continuum,
no smoothness, no metric beyond the comparison counts; "curl" lives on the triangles of co-occurring
domains, not on a surface. A verdict path is not a fluid.

    PYTHONPATH=src python tools/hodge_probe.py [--worst N]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _phrasings(data_dir: Path):
    p = data_dir / "recall_phrasings.json"
    if not p.exists():
        p = ROOT / "data" / "recall_phrasings.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    fams = d.get("families", d)
    out = {}
    for fam, rows in fams.items():
        if isinstance(rows, list):
            texts = [r.get("text", "") for r in rows if isinstance(r, dict) and r.get("text")]
            if texts:
                out[fam] = texts
    return out


def collect():
    """Run the live router over every phrasing; gather pairwise domain preferences and a sourcing read."""
    from concordance.domain_resolver import resolve_domain
    from concordance.ask import is_crisis
    data_dir = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))
    fams = _phrasings(data_dir)

    pref_sum = defaultdict(float)     # (a,b) a<b -> sum of (score_a - score_b)
    pref_cnt = defaultdict(int)       # (a,b) a<b -> count
    routed = sourced = total = 0
    for texts in fams.values():
        for t in texts:
            if is_crisis(t):
                continue
            r = resolve_domain(t)
            if r.get("crisis"):
                continue
            total += 1
            cands = r.get("candidates") or []
            if r.get("decision"):
                routed += 1
                # DIVERGENCE / sourcing: a routed decision must carry its source — the literal terms it
                # matched (why). An empty why would be an unsourced assertion (a divergence at the node).
                if (cands and cands[0].get("why")):
                    sourced += 1
            # every ordered pair in this query's ranking is one pairwise comparison
            scored = [(c["domain"], float(c["score"])) for c in cands if c.get("score") is not None]
            for (da, sa), (db, sb) in combinations(scored, 2):
                a, b = (da, db) if da < db else (db, da)
                diff = (sa - sb) if da < db else (sb - sa)   # preference of a over b, a<b
                pref_sum[(a, b)] += diff
                pref_cnt[(a, b)] += 1
    return pref_sum, pref_cnt, {"routed": routed, "sourced": sourced, "total": total}


def hodge(pref_sum, pref_cnt):
    """The discrete Hodge decomposition of the mean-preference flow Y on the domain graph."""
    edges = sorted(pref_sum.keys())
    nodes = sorted({n for e in edges for n in e})
    ni = {n: i for i, n in enumerate(nodes)}
    E, V = len(edges), len(nodes)
    y = np.array([pref_sum[e] / pref_cnt[e] for e in edges])   # mean preference per edge (a<b)
    w = np.array([pref_cnt[e] for e in edges], dtype=float)

    # d0: nodes -> edges (gradient). row e=(a,b): +1 at a, -1 at b, so (d0 s)_e = s_a - s_b.
    B = np.zeros((E, V))
    for e, (a, b) in enumerate(edges):
        B[e, ni[a]] = 1.0
        B[e, ni[b]] = -1.0
    # global ranking s: ordinary least squares on the mean-preference flow. grad = B s is then the exact
    # orthogonal projection of Y onto the gradient space (im d0), so the three energies sum to ||Y||^2.
    s, *_ = np.linalg.lstsq(B, y, rcond=None)
    s = s - s.mean()                                           # gauge: potentials sum to zero
    grad = B @ s
    R = y - grad                                               # the inconsistent (divergence-free) part

    # d1: edges -> triangles (curl). triangle (a<b<c): circ = Y(a,b) + Y(b,c) - Y(a,c).
    eidx = {e: i for i, e in enumerate(edges)}
    tris = []
    C_rows = []
    for a, b, c in combinations(nodes, 3):
        if (a, b) in eidx and (b, c) in eidx and (a, c) in eidx:
            row = np.zeros(E)
            row[eidx[(a, b)]] = 1.0
            row[eidx[(b, c)]] = 1.0
            row[eidx[(a, c)]] = -1.0
            C_rows.append(row)
            tris.append((a, b, c))
    if C_rows:
        C = np.vstack(C_rows)
        phi, *_ = np.linalg.lstsq(C.T, R, rcond=None)          # project R onto im(C^T) = curl space
        curl = C.T @ phi
    else:
        C = np.zeros((0, E))
        curl = np.zeros(E)
    harmonic = R - curl
    circ = (C @ y) if len(tris) else np.zeros(0)               # per-triangle circulation (C@grad = 0)

    ny = float(y @ y) or 1.0
    frac = {"gradient": float(grad @ grad) / ny, "curl": float(curl @ curl) / ny,
            "harmonic": float(harmonic @ harmonic) / ny}
    ranking = sorted(zip(nodes, s), key=lambda kv: -kv[1])
    worst_tri = sorted(zip(tris, circ), key=lambda kv: -abs(kv[1]))
    return {"E": E, "V": V, "T": len(tris), "frac": frac, "ranking": ranking,
            "worst_tri": worst_tri, "edges": edges, "y": y, "cnt": w}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--worst", type=int, default=10)
    a = ap.parse_args(argv)
    pref_sum, pref_cnt, src = collect()
    H = hodge(pref_sum, pref_cnt)
    f = H["frac"]
    incon = f["curl"] + f["harmonic"]

    print("=" * 74)
    print("HODGE PROBE - the routing preference flow, decomposed (read-only)")
    print("  %d domains, %d comparison edges, %d triangles" % (H["V"], H["E"], H["T"]))
    print("=" * 74)
    print("\nHELMHOLTZ-HODGE of the pairwise preference flow Y  (||Y||^2 = grad + curl + harmonic):")
    print("  GRADIENT  (a consistent global ranking explains)  : %6.2f%%" % (100 * f["gradient"]))
    print("  CURL      (local A>B>C>A cycles = route-dependence): %6.2f%%" % (100 * f["curl"]))
    print("  HARMONIC  (global cycles, not bounded by triangles): %6.2f%%" % (100 * f["harmonic"]))
    print("  -> consistency (gradient) %.2f%%   inconsistency (curl+harmonic) %.2f%%" %
          (100 * f["gradient"], 100 * incon))
    print("  -> CURL is the design doctrine's number: route-dependence of the verdict. 0 = verifiers")
    print("     commute, a true answer is a scalar invariant under the path taken to reach it.")

    print("\nDIVERGENCE (sourcing) - every routed step must cite its source, or it is unsourced content:")
    r, s0, t = src["routed"], src["sourced"], src["total"]
    print("  routed decisions sourced (carry the matched terms): %d / %d  (%.1f%%)" %
          (s0, r, 100 * s0 / r if r else 0.0))
    print("  -> div = 0 at a node means nothing is asserted there that is not sourced or a recorded miss.")

    print("\nGRADIENT - the consistent global ranking the router induces (top and bottom potentials):")
    rk = H["ranking"]
    for n, v in rk[:6]:
        print("  %+7.3f  %s" % (v, n))
    print("  ...")
    for n, v in rk[-4:]:
        print("  %+7.3f  %s" % (v, n))

    print("\nWORST ROUTE-DEPENDENCE - triangles whose preferences do not close (largest |circulation|):")
    print("  the engine prefers A>B, B>C, yet C>A on these - a cycle no ranking can hold.")
    shown = 0
    for (x, y_, z), circ in H["worst_tri"][:max(1, a.worst)]:
        if abs(circ) < 1e-6:
            break
        print("  |circ|=%.3f   %s  >  %s  >  %s  (>%s)" % (abs(circ), x, y_, z, x))
        shown += 1
    if not shown:
        print("  (none - the preference flow is a pure gradient on the triangles: routing closes)")
    print()


if __name__ == "__main__":
    raise SystemExit(main())
