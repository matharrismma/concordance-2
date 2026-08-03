"""Retrieval verifier — the fleet turned inward, on the one claim we make most often.

Every other verifier in this fleet checks a claim about the world. This one checks a claim about
US: that when we say "here is what the library holds on X", the answer is true.

WHY THIS IS THE LOAD-BEARING ONE. The first rule of the covenant is RETRIEVE FIRST — find what
is held, cite it, never generate what could be looked up. That rule is only as good as the
finding. If retrieval silently drops a document the library actually holds, then everything
downstream stops being retrieval and becomes generation with a citation stapled on, and no
amount of care further down the pipe can recover it. So the honesty of the whole library reduces
to a number that, until now, nobody was measuring.

THE FAILURE THAT MATTERS MOST IS FALSE SILENCE. A wrong result is visible and a reader can argue
with it. "Nothing found" is invisible: it looks like an honest gap, it reads as humility, and it
is indistinguishable from a broken index. A false miss is therefore worse than a wrong hit, and
retrieval.no_false_silence exists to make it impossible to hide — if the corpus provably contains
a match and the search returned nothing, that is a MISMATCH against us, not a gap in the world.

Checks:
  * retrieval.precision         — of what came back, how much was actually relevant
  * retrieval.recall_of_known   — documents known to be held AND relevant: were they returned?
  * retrieval.rank_of_target    — did the right answer land where a reader would see it (MRR)
  * retrieval.no_false_silence  — "no results" is itself a claim, and it is checkable

All four are ordinary information-retrieval arithmetic with published definitions; nothing here
is a house metric tuned to make us look good. Precision, recall, F1 and reciprocal rank are the
same formulas an outside auditor would apply, which is the point — see [[gauge panel]] for why a
score whose formula we invented is not evidence.

RET_VERIFY shape:
    {
      "query": "how do I purify water",
      "returned_ids": ["c_a", "c_b", "c_c"],
      "relevant_ids": ["c_a", "c_c", "c_z"],      # ground truth for this query
      "claimed_precision": 0.667,
      "claimed_recall": 0.667,
      "claimed_f1": 0.667,

      "target_id": "c_c",
      "claimed_rank": 3,                          # 1-based; 0 = not returned

      "claimed_result_count": 0,                  # the "we found nothing" claim
      "corpus_contains_match": true,              # ...and whether that was true
    }
"""
from __future__ import annotations

from typing import Any, Dict, List

from .base import VerifierResult, na, confirm, mismatch, error, clamp_tol
from .base import dispatch


def _ids(v: Any) -> List[str]:
    if not isinstance(v, (list, tuple)):
        return []
    return [str(x) for x in v]


def _dedupe(seq: List[str]) -> List[str]:
    """Retrieval sets are SETS. A result list that repeats an id would otherwise inflate its own
    precision, which is exactly the kind of self-flattering arithmetic this module exists to
    refuse."""
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def verify_precision(spec: Dict[str, Any]) -> VerifierResult:
    """Of what we handed the reader, how much deserved to be there."""
    name = "retrieval.precision"
    returned = _dedupe(_ids(spec.get("returned_ids")))
    relevant = set(_ids(spec.get("relevant_ids")))
    claimed = spec.get("claimed_precision")
    if not returned or not relevant or claimed is None:
        return na(name)
    try:
        c = float(claimed)
    except (TypeError, ValueError):
        return error(name, "claimed_precision must be numeric")

    hits = [r for r in returned if r in relevant]
    actual = len(hits) / len(returned)
    tol = clamp_tol(spec, "tolerance", 0.005)
    data = {"query": spec.get("query"), "returned": len(returned), "relevant_returned": len(hits),
            "actual_precision": actual, "claimed_precision": c,
            "noise_ids": [r for r in returned if r not in relevant][:10],
            "formula": "precision = |returned ∩ relevant| / |returned|"}
    if abs(actual - c) <= tol:
        return confirm(name, f"precision {actual:.4f} over {len(returned)} results "
                             f"(matches claim {c})", data)
    return mismatch(name, f"precision is {actual:.4f}, claimed {c}", data)


def verify_recall_of_known(spec: Dict[str, Any]) -> VerifierResult:
    """Documents we KNOW are held and relevant. Anything missing here we dropped on the floor."""
    name = "retrieval.recall_of_known"
    returned = set(_dedupe(_ids(spec.get("returned_ids"))))
    relevant = _dedupe(_ids(spec.get("relevant_ids")))
    claimed = spec.get("claimed_recall")
    if not relevant or claimed is None:
        return na(name)
    try:
        c = float(claimed)
    except (TypeError, ValueError):
        return error(name, "claimed_recall must be numeric")

    found = [r for r in relevant if r in returned]
    missed = [r for r in relevant if r not in returned]
    actual = len(found) / len(relevant)
    tol = clamp_tol(spec, "tolerance", 0.005)
    data = {"query": spec.get("query"), "known_relevant": len(relevant), "found": len(found),
            "actual_recall": actual, "claimed_recall": c,
            # naming what was dropped is the whole value: a recall number without the missing
            # ids tells you that you failed but not what you failed to find
            "missed_ids": missed[:20],
            "formula": "recall = |returned ∩ relevant| / |relevant|"}
    if spec.get("claimed_f1") is not None:
        try:
            p_ret = _dedupe(_ids(spec.get("returned_ids")))
            prec = (len([r for r in p_ret if r in set(relevant)]) / len(p_ret)) if p_ret else 0.0
            f1 = (2 * prec * actual / (prec + actual)) if (prec + actual) else 0.0
            data["actual_f1"] = f1
            data["claimed_f1"] = float(spec["claimed_f1"])
        except (TypeError, ValueError):
            pass
    if abs(actual - c) <= tol:
        return confirm(name, f"recall {actual:.4f} — found {len(found)} of {len(relevant)} known "
                             f"(matches claim {c})", data)
    return mismatch(name, f"recall is {actual:.4f}, claimed {c}; missed {len(missed)} "
                          f"document(s) the library holds", data)


def verify_rank_of_target(spec: Dict[str, Any]) -> VerifierResult:
    """Where the right answer landed. Rank 40 and rank 0 are the same to a reader."""
    name = "retrieval.rank_of_target"
    returned = _dedupe(_ids(spec.get("returned_ids")))
    target = spec.get("target_id")
    claimed = spec.get("claimed_rank")
    if not returned or target is None or claimed is None:
        return na(name)
    try:
        c = int(claimed)
    except (TypeError, ValueError):
        return error(name, "claimed_rank must be an integer (1-based; 0 = absent)")

    t = str(target)
    actual = returned.index(t) + 1 if t in returned else 0
    rr = (1.0 / actual) if actual else 0.0
    data = {"query": spec.get("query"), "target_id": t, "actual_rank": actual,
            "claimed_rank": c, "reciprocal_rank": rr, "results_considered": len(returned),
            "formula": "rank is 1-based position in the returned list; RR = 1/rank, 0 if absent"}
    if actual == c:
        where = f"rank {actual}" if actual else "NOT RETURNED AT ALL"
        return confirm(name, f"'{t}' came back at {where} (matches claim)", data)
    return mismatch(name, f"'{t}' is at rank {actual}, claimed {c}", data)


def verify_no_false_silence(spec: Dict[str, Any]) -> VerifierResult:
    """'We found nothing' is a claim about the library, and it is checkable.

    A true miss is honest and belongs on the want list. A FALSE miss is the library lying by
    omission, and it is invisible from outside — it looks exactly like humility. This check is
    the only place that difference gets caught, so it treats a false silence as a MISMATCH
    against us rather than a gap in the world.
    """
    name = "retrieval.no_false_silence"
    claimed_n = spec.get("claimed_result_count")
    contains = spec.get("corpus_contains_match")
    if claimed_n is None or contains is None:
        return na(name)
    try:
        n = int(claimed_n)
    except (TypeError, ValueError):
        return error(name, "claimed_result_count must be an integer")

    held = bool(contains)
    silent = (n == 0)
    data = {"query": spec.get("query"), "claimed_result_count": n,
            "corpus_contains_match": held, "silent": silent,
            "witness_ids": _ids(spec.get("relevant_ids"))[:10],
            "rule": "returning zero results is only honest when the corpus truly holds no match"}
    if silent and held:
        return mismatch(name,
                        f"FALSE SILENCE: search returned nothing for '{spec.get('query')}' while "
                        f"the corpus does hold a match — this is our failure, not a gap in the "
                        f"world, and it must not be recorded as a want", data)
    if silent:
        return confirm(name, f"'{spec.get('query')}' returned nothing and the corpus genuinely "
                             f"holds nothing — an honest miss", data)
    return confirm(name, f"'{spec.get('query')}' returned {n} result(s); not a silence", data)


_RULES = [
    (("returned_ids", "relevant_ids", "claimed_precision"), verify_precision),
    (("relevant_ids", "claimed_recall"), verify_recall_of_known),
    (("returned_ids", "target_id", "claimed_rank"), verify_rank_of_target),
    (("claimed_result_count", "corpus_contains_match"), verify_no_false_silence),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, 'RET_VERIFY', _RULES, domain='retrieval',
                    none_reason='no RET_VERIFY artifacts present')
