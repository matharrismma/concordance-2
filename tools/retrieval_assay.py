#!/usr/bin/env python3
"""THE FLEET TURNS INWARD — drive the live corpus through the retrieval verifier.

    PYTHONPATH=src python tools/retrieval_assay.py
    PYTHONPATH=src python tools/retrieval_assay.py --json      # machine-readable

verify_retrieval on its own is arithmetic. Arithmetic nobody points at the running library proves
nothing about the running library -- correct-looking code on a path nobody walked. This is the
walker: it takes a golden list of queries whose answers we can establish INDEPENDENTLY of the
search index, runs the real corpus.search(), and hands the outcome to the verifier for judgement.

HOW THE GROUND TRUTH IS ESTABLISHED, AND WHY IT IS NOT CIRCULAR. A golden set built by running
the search and blessing whatever came back would measure nothing at all -- it would score 1.000
forever and feel wonderful. So relevance here is decided by a SEPARATE READER: a direct scan of
every card's own title and body for the query's terms. That scan is slow and stupid and touches
the whole corpus, which is exactly why it is trustworthy -- it cannot miss what the index missed,
because it does not use the index. The search is then measured against it.

That inversion is the whole design. The dumb exhaustive reader is the judge; the fast clever
index is the defendant.

WHAT A BAD NUMBER MEANS. Low precision is noise: annoying, visible, arguable. Low recall is the
serious one -- documents the library HOLDS that the reader was never shown. And a false silence
(retrieval.no_false_silence MISMATCH) is the worst of all, because it is indistinguishable from
an honest gap and it poisons the want list with wants we could already have met.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
os.environ.setdefault("CONCORDANCE_DATA_DIR", os.path.join(ROOT, "data"))

if hasattr(sys.stdout, "reconfigure"):          # Windows console, non-ASCII in card titles
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from concordance import corpus                                    # noqa: E402
from concordance.verifiers import retrieval as R                  # noqa: E402


# Queries a real person actually arrives with. Deliberately NOT phrased to match card titles --
# a search that only works when you already know what the card is called is a search that only
# works for people who did not need it.
#
# RELEVANCE IS A CONJUNCTION OF DISJUNCTIONS. Each entry is a list of GROUPS; a card is relevant
# when EVERY group is satisfied by at least one of its alternatives. The first cut of this file
# OR-ed the terms together, so "purify water" scored every one of the 8,253 cards containing the
# word "water" as relevant and the library appeared to have 0.3% recall. That number was my
# measurement failing, not the search -- a truth set that loose measures nothing except how
# common a word is.
GOLDEN = [
    ("purify water",        [["purif", "distill", "filtrat", "chlorinat", "boil"], ["water"]]),
    ("solar power",         [["solar", "photovolta"], ["power", "panel", "electric", "energy"]]),
    ("food preservation",   [["preserv", "canning", "curing", "smok", "ferment"], ["food", "meat", "vegetable", "fruit"]]),
    ("antibiotic",          [["antibiotic", "penicillin"]]),
    ("germination",         [["germinat"], ["seed", "sprout", "plant"]]),
    ("splint a fracture",   [["splint"], ["fracture", "bone", "limb", "broken"]]),
    ("morse code",          [["morse"], ["code", "telegraph", "signal"]]),
    ("soap making",         [["soap"], ["lye", "saponif", "making", "make", "tallow"]]),
    ("well drilling",       [["well"], ["drill", "bore", "auger"]]),
    ("beekeeping",          [["beekeep", "apiar", "honey bee", "hive"]]),
    ("grain storage",       [["grain", "wheat", "corn"], ["storage", "storing", "granary", "silo"]]),
    ("navigation by stars", [["celestial", "sextant", "polaris", "star"], ["navigat"]]),
]

LIMIT = 25


def _text(card) -> str:
    if isinstance(card, dict):
        return f"{card.get('title', '')}\n{card.get('body', '')}".lower()
    return f"{getattr(card, 'title', '')}\n{getattr(card, 'body', '')}".lower()


def _cid(card) -> str:
    return str(card.get("id") if isinstance(card, dict) else getattr(card, "id", ""))


def _truth(cards, groups):
    """THE INDEPENDENT JUDGE. A direct scan of every card, using none of the search machinery.

    Relevant = every group satisfied by at least one alternative (AND of ORs).
    """
    out = []
    for c in cards:
        t = _text(c)
        if all(any(alt in t for alt in group) for group in groups):
            out.append(_cid(c))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="emit the measurement as JSON")
    ap.add_argument("--limit", type=int, default=LIMIT)
    args = ap.parse_args()

    cor = corpus.default_corpus()
    cards = list(cor.cards.values()) if hasattr(cor, "cards") else []
    if not cards:
        print("CANNOT_CHECK: the corpus is empty on this machine — nothing to measure")
        return 2

    rows, silences = [], []
    for query, terms in GOLDEN:
        relevant = _truth(cards, terms)
        try:
            hits = cor.search(query, limit=args.limit)
        except Exception as exc:                       # noqa: BLE001 — an engine failure is a
            rows.append({"query": query, "engine_error": str(exc)})   # THIRD state, not a zero
            continue
        returned = [_cid(h[0] if isinstance(h, tuple) else h) for h in hits]

        hit_set, rel_set = set(returned), set(relevant)
        prec = (len(hit_set & rel_set) / len(returned)) if returned else 0.0
        rec = (len(hit_set & rel_set) / len(relevant)) if relevant else float("nan")

        # RECALL@k HAS A CEILING AND THE CEILING MUST BE STATED. You cannot return more than k
        # documents, so recall@k can never exceed min(k, |relevant|)/|relevant|. Against a truth
        # set of 500 and k=25 the arithmetic maximum is 0.05, and printing a bare "recall 0.04"
        # reads as catastrophic when it is in fact 80% of everything achievable. The honest
        # figure is achieved/achievable — what fraction of the reachable ground we actually took.
        ceiling = (min(args.limit, len(relevant)) / len(relevant)) if relevant else float("nan")
        efficiency = (rec / ceiling) if (relevant and ceiling) else float("nan")

        # Reciprocal rank of the FIRST relevant result, the standard definition. The first cut
        # tracked an ARBITRARY member of the truth set instead, so a query with 4,000 equally
        # good answers scored 0 unless the search happened to pick the one the scan listed first.
        rank = 0
        for i, rid in enumerate(returned):
            if rid in rel_set:
                rank = i + 1
                break
        target = relevant[0] if relevant else None

        packet = {"RET_VERIFY": {
            "query": query,
            "returned_ids": returned,
            "relevant_ids": relevant,
            "claimed_precision": prec,
            "claimed_recall": rec if relevant else 0.0,
            "claimed_result_count": len(returned),
            "corpus_contains_match": bool(relevant),
        }}
        if target:
            packet["RET_VERIFY"]["target_id"] = target
            packet["RET_VERIFY"]["claimed_rank"] = rank

        verdicts = {v.name: v for v in R.run(packet)}
        false_silence = (verdicts.get("retrieval.no_false_silence") is not None
                         and verdicts["retrieval.no_false_silence"].status == "MISMATCH")
        if false_silence:
            silences.append(query)
        rows.append({"query": query, "held": len(relevant), "returned": len(returned),
                     "precision": prec, "recall": rec, "ceiling": ceiling,
                     "efficiency": efficiency, "rank_of_first_true": rank,
                     "false_silence": false_silence,
                     "verdicts": {k: v.status for k, v in verdicts.items()}})

    scored = [r for r in rows if "engine_error" not in r and r["held"]]
    n = len(scored)
    macro_p = sum(r["precision"] for r in scored) / n if n else 0.0
    macro_r = sum(r["recall"] for r in scored) / n if n else 0.0
    macro_e = sum(r["efficiency"] for r in scored) / n if n else 0.0
    mrr = sum((1.0 / r["rank_of_first_true"]) if r["rank_of_first_true"] else 0.0
              for r in scored) / n if n else 0.0

    report = {"corpus_cards": len(cards), "queries": len(GOLDEN), "scored": n,
              "limit": args.limit, "macro_precision": macro_p, "macro_recall": macro_r,
              "macro_recall_efficiency": macro_e, "mrr": mrr,
              "false_silences": silences, "rows": rows}

    if args.json:
        print(json.dumps(report, indent=2, default=str))
        return 0

    # COVERAGE FIRST — a measurement that does not say what it covered is not a measurement.
    print(f"RETRIEVAL ASSAY — {len(cards):,} cards, {len(GOLDEN)} golden queries, "
          f"top-{args.limit}, ground truth by exhaustive scan (not by the index)")
    print()
    print(f"  {'query':22s} {'held':>5s} {'ret':>4s} {'prec':>6s} {'rec':>6s} "
          f"{'max':>6s} {'of max':>7s} {'rank':>5s}")
    for r in rows:
        if "engine_error" in r:
            print(f"  {r['query']:22s}  ENGINE ERROR: {r['engine_error'][:40]}")
            continue
        if r["held"] == 0:
            print(f"  {r['query']:22s} {0:5d} {r['returned']:4d} "
                  f"{'  n/a ':>6s} {'  n/a ':>6s} {'  n/a ':>6s} {'   n/a ':>7s} "
                  f"{r['rank_of_first_true']:5d}   (corpus holds nothing — an honest gap)")
            continue
        flag = "  <-- FALSE SILENCE" if r["false_silence"] else ""
        print(f"  {r['query']:22s} {r['held']:5d} {r['returned']:4d} "
              f"{r['precision']:6.3f} {r['recall']:6.3f} {r['ceiling']:6.3f} "
              f"{r['efficiency']:7.3f} {r['rank_of_first_true']:5d}{flag}")
    print()
    print(f"  macro precision      : {macro_p:.3f}   of what we showed, how much belonged")
    print(f"  macro recall@{args.limit:<2d}      : {macro_r:.3f}   raw — bounded by the ceiling below")
    print(f"  macro recall ceiling : capped at min(k,|held|)/|held| — you cannot show more than k")
    print(f"  RECALL EFFICIENCY    : {macro_e:.3f}   <- the honest one: achieved / achievable")
    print(f"  MRR                  : {mrr:.3f}   how near the top the first true answer landed")
    print(f"  false silences       : {len(silences)}" + (f"  {silences}" if silences else ""))
    if silences:
        print()
        print("  A FALSE SILENCE IS OUR FAILURE, NOT A GAP IN THE WORLD. These queries must not")
        print("  reach the want list — the library already holds an answer and did not show it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
