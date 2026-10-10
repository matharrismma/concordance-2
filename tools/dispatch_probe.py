#!/usr/bin/env python3
"""Dispatch probe — measure the engine's answer routing on three axes, READ-ONLY.

Matt, 2026-10-10. Four witnesses from reality name one efficiency doctrine, and this tool
measures how far today's dispatch is from it, before a single line of the core changes:

  1. COST  (the cosmic distance ladder) — climb only as far as the query forces you.
     Here: what fraction of queries ROUTE at the cheap address rung (resolve_domain decides a
     domain) vs FALL THROUGH to the expensive ~6 GB corpus-search rung (ask / no-vocabulary)?
     The fall-through fraction is the cost headroom.

  2. PLACEMENT  (opposing sorts: radix vs comparison) — compute the destination from the key's
     structure instead of comparing against the whole corpus. Routing IS radix; search IS
     comparison. Same number as the fall-through rate, read as a placement failure.

  3. REPRESENTATION  (co/contravariant tensors, and sine/cosine):
     (a) INVARIANCE — a true answer is a scalar, invariant under a change of basis (rephrasing).
         data/recall_phrasings.json groups phrasings by FAMILY: each family is a paraphrase
         equivalence-class. Do all phrasings of one family route to ONE domain? Scatter = a
         coordinate artifact (the answer depends on wording), not truth.
     (b) ORTHOGONALITY — sin/cos are the canonical orthonormal pair; an orthogonal domain basis
         makes routing a clean projection with no cross-talk. Cross-talk = second_score/top_score
         over routed queries. 0 = orthogonal/unambiguous; →1 = a tangled, non-orthogonal basis.

Touches nothing: imports resolve_domain + is_crisis, reads data/recall_phrasings.json, writes
no engine state. Prints a report; with --json <path> also writes the raw numbers.

    PYTHONPATH=src python tools/dispatch_probe.py [--json out.json] [--worst N]
"""
from __future__ import annotations
import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

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
        if not isinstance(rows, list):
            continue
        texts = [r.get("text", "") for r in rows if isinstance(r, dict) and r.get("text")]
        if texts:
            out[fam] = texts
    return out


def _classify(text: str, resolve, is_crisis):
    """One query -> its rung and the numbers for the three axes."""
    if is_crisis(text):
        return {"rung": "crisis", "domain": None, "top": 0.0, "second": 0.0, "crosstalk": 0.0}
    r = resolve(text)
    if r.get("crisis"):
        return {"rung": "crisis", "domain": None, "top": 0.0, "second": 0.0, "crosstalk": 0.0}
    cands = r.get("candidates") or []
    top = float(cands[0]["score"]) if cands else 0.0
    second = float(cands[1]["score"]) if len(cands) > 1 else 0.0
    crosstalk = (second / top) if top > 0 else 0.0
    if r.get("decision"):
        rung = "route"          # cheap address rung reached (radix hit)
    elif cands:
        rung = "ask_tie"        # vocabulary matched but ambiguous -> would ask / fall to search
    else:
        rung = "search"         # no vocabulary -> straight to the ~6 GB comparison rung
    return {"rung": rung, "domain": r.get("decision") or (cands[0]["domain"] if cands else None),
            "top": top, "second": second, "crosstalk": crosstalk}


def run(worst_n: int = 10):
    from concordance.domain_resolver import resolve_domain
    from concordance.ask import is_crisis
    import os
    data_dir = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))
    fams = _phrasings(data_dir)

    per_family = {}
    all_crosstalk = []
    totals = Counter()
    n_total = 0
    for fam, texts in fams.items():
        rungs = Counter()
        domains_routed = Counter()
        cts = []
        for t in texts:
            c = _classify(t, resolve_domain, is_crisis)
            rungs[c["rung"]] += 1
            totals[c["rung"]] += 1
            n_total += 1
            if c["rung"] == "route":
                domains_routed[c["domain"]] += 1
                cts.append(c["crosstalk"])
                all_crosstalk.append(c["crosstalk"])
        n = sum(rungs.values())
        routed = rungs["route"]
        # invariance: of the phrasings that routed, how many agree with the family's modal domain
        mode_dom, mode_ct = (domains_routed.most_common(1)[0] if domains_routed else (None, 0))
        invariance = (mode_ct / routed) if routed else None
        per_family[fam] = {
            "n": n,
            "routed": routed,
            "ask_tie": rungs["ask_tie"],
            "search": rungs["search"],
            "crisis": rungs["crisis"],
            "route_rate": routed / n if n else 0.0,
            "fallthrough_rate": (rungs["ask_tie"] + rungs["search"]) / n if n else 0.0,
            "modal_domain": mode_dom,
            "n_distinct_domains": len(domains_routed),
            "invariance": invariance,
            "mean_crosstalk": (statistics.fmean(cts) if cts else 0.0),
        }

    routed = totals["route"]
    fallthrough = totals["ask_tie"] + totals["search"]
    inv_rates = [f["invariance"] for f in per_family.values() if f["invariance"] is not None]
    summary = {
        "families": len(fams),
        "phrasings": n_total,
        "cost_placement": {
            "routed": routed,
            "route_rate": routed / n_total if n_total else 0.0,
            "fallthrough": fallthrough,
            "fallthrough_rate": fallthrough / n_total if n_total else 0.0,
            "ask_tie": totals["ask_tie"],
            "search": totals["search"],
            "crisis": totals["crisis"],
        },
        "representation": {
            "mean_family_invariance": (statistics.fmean(inv_rates) if inv_rates else 0.0),
            "families_fully_invariant": sum(1 for r in inv_rates if r >= 0.999),
            "families_measured": len(inv_rates),
            "mean_crosstalk": (statistics.fmean(all_crosstalk) if all_crosstalk else 0.0),
        },
    }
    return summary, per_family, worst_n


def _bar(x, width=20):
    n = int(round(x * width))
    return "#" * n + "." * (width - n)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="")
    ap.add_argument("--worst", type=int, default=10)
    a = ap.parse_args(argv)
    summary, per_family, worst_n = run(a.worst)

    cp = summary["cost_placement"]
    rep = summary["representation"]
    print("=" * 74)
    print("DISPATCH PROBE - routing measured on three axes (read-only)")
    print("  %d phrasings across %d families (data/recall_phrasings.json)" % (summary["phrasings"], summary["families"]))
    print("=" * 74)
    print("\nAXIS 1 - COST (distance ladder) + AXIS 2 - PLACEMENT (radix vs comparison)")
    print("  routed at the cheap address rung : %4d  %5.1f%%  %s" % (cp["routed"], 100 * cp["route_rate"], _bar(cp["route_rate"])))
    print("  fell through to the search rung  : %4d  %5.1f%%  %s" % (cp["fallthrough"], 100 * cp["fallthrough_rate"], _bar(cp["fallthrough_rate"])))
    print("      of which ambiguous (ask/tie) : %4d" % cp["ask_tie"])
    print("      of which no vocabulary       : %4d" % cp["search"])
    print("  crisis (rung 0, always first)    : %4d" % cp["crisis"])
    print("  --> the fall-through rate is the cost/placement headroom: every one of these")
    print("      climbs to the ~6 GB comparison rung a stronger address hit would have spared.")

    print("\nAXIS 3a - REPRESENTATION - invariance (co/contravariant: a true answer is a scalar)")
    print("  mean family invariance           : %5.1f%%  %s" % (100 * rep["mean_family_invariance"], _bar(rep["mean_family_invariance"])))
    print("  families routing to ONE domain   : %d / %d measured" % (rep["families_fully_invariant"], rep["families_measured"]))
    print("  --> below 100% means phrasings of the SAME claim route to different domains:")
    print("      the answer depends on wording - a coordinate artifact, not an invariant.")

    print("\nAXIS 3b - REPRESENTATION - orthogonality (sine/cosine: an orthonormal basis)")
    print("  mean cross-talk (2nd/top score)  : %5.3f   %s" % (rep["mean_crosstalk"], _bar(rep["mean_crosstalk"])))
    print("  --> 0 = orthogonal/unambiguous basis; higher = domains overlap and the runner-up")
    print("      crowds the leader. This is the 'orthogonalize the domain basis' lever, measured.")

    # worst families, by fall-through then by scatter
    rows = [(f, d) for f, d in per_family.items()]
    worst_fall = sorted(rows, key=lambda kv: (-kv[1]["fallthrough_rate"], kv[0]))[:worst_n]
    print("\nWORST FAMILIES by fall-through (would hit the expensive rung most):")
    print("  %-26s %5s %6s %6s %6s" % ("family", "n", "route%", "inv%", "xtalk"))
    for f, d in worst_fall:
        inv = ("%5.0f" % (100 * d["invariance"])) if d["invariance"] is not None else "   - "
        print("  %-26s %5d %5.0f%% %5s%% %6.3f" % (f[:26], d["n"], 100 * d["route_rate"], inv, d["mean_crosstalk"]))

    scattered = sorted([r for r in rows if r[1]["invariance"] is not None and r[1]["invariance"] < 0.999],
                       key=lambda kv: (kv[1]["invariance"], -kv[1]["n_distinct_domains"]))[:worst_n]
    if scattered:
        print("\nWORST FAMILIES by scatter (one claim, many domains — invariance broken):")
        print("  %-26s %5s %6s %8s" % ("family", "n", "inv%", "domains"))
        for f, d in scattered:
            print("  %-26s %5d %5.0f%% %8d" % (f[:26], d["routed"], 100 * d["invariance"], d["n_distinct_domains"]))

    if a.json:
        Path(a.json).write_text(json.dumps({"summary": summary, "per_family": per_family}, indent=1), encoding="utf-8")
        print("\nwrote", a.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
