"""THE HELM's fourth tier — DISCERNMENT: one verdict assembled from several probes.

An instrument says what is. A probe answers one bounded question. A discernment is the thing a row
of nine green lights can never do: it combines several answers into ONE verdict — and it is allowed
to say **I CANNOT TELL** and name the input it is missing.

That last part is the whole point, and it is why this file exists instead of a wider dashboard. A
readout that can only ever say green is decoration; the panel's job is to tell the operator
something he did not already assume. So every rule here has three outcomes, not two:

    ok=True,  tell=True    the combination holds, and says what agreed
    ok=False, tell=True    it does not hold, and says WHICH inputs disagree
              tell=False   it cannot be judged, and names the missing input

The middle one carries the weight. When two independent walks of the same record disagree, the
interesting fact is not which is right — it is that the method is in question. A discordance
indicts the method, not the constant.

COST: a discernment runs its probes SERIALLY through helm_probes.run, so it costs the sum of them,
and on a slow filesystem that is minutes. The catalog says how many probes each one fires so the
operator is never surprised by a button. Probes are serialized globally, so if one is already
running the first probe here is declined and the discernment correctly reports "I cannot tell".

Operator-gated by the caller, like the rest of the panel.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List

from . import helm_probes

_STALE_DAYS = 3.0          # a traffic rollup older than this is reported as stale, not quoted plainly


def _traffic() -> Dict[str, Any]:
    """The last rollup. Read inline rather than importing keep._read_traffic: that is a private
    name on a module being renamed piece by piece, and three lines here cannot drift."""
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    try:
        with open(os.path.join(base, "traffic.json"), "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except (OSError, ValueError):
        return {}


def _cannot(why: str, missing: List[str]) -> Dict[str, Any]:
    return {"ok": False, "tell": False, "verdict": "I cannot tell — " + why, "missing": missing,
            "next": "get that input, then ask again"}


# ── the rules ───────────────────────────────────────────────────────────────────────────────────

def _truth(res: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Is the engine telling the truth about its own record?

    Two independent walks: the chain probe recomputes every content_hash and link in process; the
    integrity tool does that AND sweeps every sealed CAS record. They overlap on purpose, because
    two methods that agree are evidence and two that disagree are a finding."""
    chain, integ = res.get("ledger_chain") or {}, res.get("integrity") or {}
    declined = [k for k, v in (("ledger_chain", chain), ("integrity", integ))
                if not v or v.get("verdict", "").startswith("declined")
                or v.get("verdict") == "no such probe"]
    if declined:
        return _cannot(
            "%s could not run (%s), and one walk alone cannot confirm the other"
            % (" and ".join(declined), "; ".join(
                (res.get(d) or {}).get("verdict", "no result") for d in declined)),
            declined)
    a, b = bool(chain.get("ok")), bool(integ.get("ok"))
    if a and b:
        return {"ok": True, "tell": True,
                "verdict": "the record stands — two independent walks agree (%s · %s)"
                           % (chain.get("verdict"), integ.get("verdict")),
                "next": "nothing"}
    if a != b:
        held, broke = ("the chain probe", "the integrity sweep") if a else ("the integrity sweep", "the chain probe")
        return {"ok": False, "tell": True,
                "verdict": "DISCORDANCE — %s says the record is sound and %s does not. "
                           "A disagreement between two methods indicts the METHOD, not the record: "
                           "do not act on either verdict until it is understood." % (held, broke),
                "next": "read both trails; the sweep covers sealed CAS records the chain walk does not"}
    return {"ok": False, "tell": True,
            "verdict": "THE RECORD IS BROKEN, and both walks agree it is (%s)" % chain.get("verdict"),
            "next": "stop writing; nothing should touch the ledger until this is understood"}


def _served(res: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Is anybody being served — and through which door?

    The rollup counts every watched door with the operator's own addresses excluded, so this is
    adoption rather than our own testing. It is the inversion on demand instead of once by hand."""
    t = _traffic()
    probe = res.get("traffic") or {}
    if not t:
        return _cannot("there is no traffic rollup to read (%s)"
                       % (probe.get("verdict") or "traffic.json absent"), ["traffic.json"])
    doors = ((t.get("fruit") or {}).get("doors") or {})
    if not doors:
        return _cannot("the rollup carries no per-door counts", ["fruit.doors"])
    age_days = max(0.0, (time.time() - float(t.get("generated_at") or 0)) / 86400.0)
    tally = {p: sum(int(v) for v in (counts or {}).values()) for p, counts in doors.items()}
    ask, mcp = tally.get("/ask", 0), tally.get("/mcp", 0)
    busiest = max(tally.items(), key=lambda kv: kv[1], default=("(none)", 0))
    window = t.get("window_days")
    stale = age_days > _STALE_DAYS
    lead = ("the rollup is %.1f days old, so this describes the past, not now — " % age_days) if stale else ""
    if not any(tally.values()):
        return _cannot("the rollup is present but every watched door reads zero over %s days"
                       % window, ["a non-empty window"])
    verdict = ("%sthe busiest door is %s with %d, against /ask's %d over %s days"
               % (lead, busiest[0], busiest[1], ask, window))
    if mcp and ask * 20 < mcp:
        verdict += " — the agent door carries %.0fx what the human door does" % (mcp / max(1, ask))
    return {"ok": not stale, "tell": True, "verdict": verdict,
            "detail": {"doors": tally, "window_days": window, "rollup_age_days": round(age_days, 2)},
            "next": ("refresh traffic, then ask again" if stale
                     else "put the next build where the traffic is")}


DISCERNMENTS: Dict[str, Dict[str, Any]] = {
    "truth": {
        "label": "Is the engine telling the truth?",
        "question": "two independent walks of the same record — do they agree?",
        "probes": ["ledger_chain", "integrity"],
        "rule": _truth,
    },
    "served": {
        "label": "Is anybody being served?",
        "question": "which door is actually carrying people, with our own addresses excluded",
        "probes": ["traffic"],
        "rule": _served,
    },
}


def catalog() -> List[Dict[str, Any]]:
    """Executes nothing. Says how many probes each one fires, so a slow button is never a surprise."""
    out = []
    for did, spec in DISCERNMENTS.items():
        out.append({"discernment": did, "label": spec["label"], "question": spec["question"],
                    "tier": "discernment", "probes": list(spec["probes"]),
                    "fires": len(spec["probes"])})
    return out


def run(discernment_id: str) -> Dict[str, Any]:
    """Fire one discernment: run its probes serially, then combine them into ONE verdict.

    CALL ONLY FROM BEHIND THE OPERATOR GATE."""
    spec = DISCERNMENTS.get(str(discernment_id or "").strip())
    if spec is None:
        return {"discernment": discernment_id, "ok": False, "tell": False, "ms": 0,
                "verdict": "no such discernment",
                "next": "choose one of: " + ", ".join(sorted(DISCERNMENTS)),
                "at": int(time.time())}
    t0 = time.time()
    results: Dict[str, Dict[str, Any]] = {}
    for pid in spec["probes"]:
        results[pid] = helm_probes.run(pid)
    try:
        combined = spec["rule"](results)
    except Exception as e:                                   # a rule never takes the panel down
        combined = {"ok": False, "tell": False,
                    "verdict": "I cannot tell — the rule itself failed (%s: %s)" % (type(e).__name__, e),
                    "missing": [], "next": "this is a defect in the discernment, not in the engine"}
    return {"discernment": discernment_id, "label": spec["label"],
            "ms": int(1000 * (time.time() - t0)), "at": int(time.time()),
            # the trail: every probe that fed the verdict, so a verdict is never unexaminable
            "trail": [{"probe": p, "ok": r.get("ok"), "verdict": r.get("verdict"), "ms": r.get("ms")}
                      for p, r in results.items()],
            **combined}


__all__ = ["catalog", "run", "DISCERNMENTS"]
