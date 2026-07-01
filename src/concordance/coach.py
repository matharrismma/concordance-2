"""Coach — the Shepherd as a K-3 reading tutor that grows with the student.

The door in (the Apple model): a child learns to read here, and the same engine grows with them.
Coach FINDS and PRESENTS the curriculum — it never generates a lesson and never renders a verdict
on a child. The units are the operator's authored, verbatim teaching (data/curriculum/read_en.json,
ported by tools/migrate_school.py from the offline Read school); this module loads them, orders
them deterministically, and hands them out one continuing lesson at a time.

HARD BOUNDARY (load-bearing): Coach will NOT grade, rank, label, or judge a child — no "grade
level," no "is my kid behind," no verdict on a person. Those questions get pointed to the adult in
the room and to real help (a teacher, a doctor, a librarian). What Coach CAN seal is one honest,
re-checkable fact: the INTEGER count of units a learner has actually completed — the moat's math
applied to progress, never to the person. A window to reading, not a wall; success is the day they
need the tool LESS (John 3:30).

Mirrors steward.py: pure stdlib, deterministic, find-and-present. A lesson RIDES a thread (threads.py)
so it is one continuing chain that never starts over. Every response carries generated:false.

Sovereign: stdlib only; loads read_en.json; seals ONLY via the public receipts helper (never imports
verifiers/derivation). Conduit, not source.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── curriculum load (verbatim data, cached) ─────────────────────────────────────────────────

_CURRICULUM: Optional[List[Dict[str, Any]]] = None


def _file() -> Path:
    """The curriculum path. CONCORDANCE_CURRICULUM_DIR / CONCORDANCE_DATA_DIR override the default."""
    env = os.environ.get("CONCORDANCE_CURRICULUM_DIR", "").strip()
    if env:
        return Path(env) / "read_en.json"
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    if data:
        return Path(data) / "curriculum" / "read_en.json"
    return Path("data") / "curriculum" / "read_en.json"


def _load() -> List[Dict[str, Any]]:
    """Load the units verbatim from read_en.json (cached). Missing/unreadable -> empty (never raises)."""
    global _CURRICULUM
    if _CURRICULUM is not None:
        return _CURRICULUM
    p = _file()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        units = data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        units = []
    _CURRICULUM = [u for u in units if isinstance(u, dict) and u.get("id")]
    return _CURRICULUM


def reload() -> int:
    """Drop the cache and re-read from disk (for the migrator/tests). Returns the unit count."""
    global _CURRICULUM
    _CURRICULUM = None
    return len(_load())


def _ordered() -> List[Dict[str, Any]]:
    """Units in a STABLE, deterministic teaching order: by unit_seq, then id (unit_seq repeats
    across tracks, so id is the tiebreak — the same order on every box, every time)."""
    def _seq(u: Dict[str, Any]) -> int:
        try:
            return int(u.get("unit_seq", 10 ** 9))
        except (TypeError, ValueError):
            return 10 ** 9
    return sorted(_load(), key=lambda u: (_seq(u), str(u.get("id", ""))))


# ── find + present (never generate) ─────────────────────────────────────────────────────────

_NOTE = "Coach finds and presents the lesson; it never generates it, and never grades a child."


def overview() -> Dict[str, Any]:
    """The map of the whole path: how many units, the tracks, and the ordered list of unit briefs.
    Found and cited, never generated."""
    units = _ordered()
    tracks: List[str] = []
    for u in units:
        t = str(u.get("track") or "")
        if t and t not in tracks:
            tracks.append(t)
    briefs = [{"id": u.get("id"), "title": u.get("title"), "unit_seq": u.get("unit_seq"),
               "track": u.get("track")} for u in units]
    return {
        "kind": "coach_overview",
        "count": len(units),
        "tracks": tracks,
        "units": briefs,
        "source": "Read school curriculum (offline), ported verbatim.",
        "note": _NOTE,
        "generated": False,
    }


def unit(unit_id: str) -> Dict[str, Any]:
    """One unit, VERBATIM as authored — the rule, examples, decodable sentence, checks, next.
    Returns kind:coach_unit_not_found (never a guess) when the id is unknown."""
    uid = str(unit_id or "")
    for u in _load():
        if u.get("id") == uid:
            out = dict(u)  # the operator's teaching, unaltered
            out["kind"] = "coach_unit"
            out["note"] = _NOTE
            out["generated"] = False
            return out
    return {"kind": "coach_unit_not_found", "id": uid,
            "message": "No unit by that id. See /coach/overview for the path.",
            "note": _NOTE, "generated": False}


def next_unit(after: Optional[str] = None) -> Dict[str, Any]:
    """The next lesson to teach, deterministically. after=None -> the first unit; after=<id> ->
    the unit that follows it in the stable teaching order. Past the end -> kind:coach_complete.
    A lesson is a continuing chain (ride threads.py for continuity); this only decides WHICH unit."""
    units = _ordered()
    if not units:
        return {"kind": "coach_empty", "message": "No curriculum is loaded yet.",
                "note": _NOTE, "generated": False}
    if after is None or str(after) == "":
        first = units[0]
        return {"kind": "coach_next", "after": None, "unit": unit(str(first.get("id"))),
                "position": 1, "of": len(units), "note": _NOTE, "generated": False}
    ids = [str(u.get("id")) for u in units]
    aid = str(after)
    if aid not in ids:
        # Unknown anchor — do not guess. Point back to the map.
        return {"kind": "coach_next_unknown_anchor", "after": aid,
                "message": "That unit id isn't in the path. See /coach/overview.",
                "note": _NOTE, "generated": False}
    idx = ids.index(aid)
    if idx + 1 >= len(units):
        return {"kind": "coach_complete", "after": aid,
                "message": "That was the last unit in this path. Well done — keep reading.",
                "position": len(units), "of": len(units), "note": _NOTE, "generated": False}
    nxt = units[idx + 1]
    return {"kind": "coach_next", "after": aid, "unit": unit(str(nxt.get("id"))),
            "position": idx + 2, "of": len(units), "note": _NOTE, "generated": False}


# ── mastery: seal an HONEST INTEGER count (the moat applied to progress, never to the person) ──

def mastery_result(completed_ids: List[str]) -> Dict[str, Any]:
    """Build the derivation-shaped result for the HONEST count of completed units, ready to seal.

    We count only ids that ACTUALLY exist in the loaded curriculum (no inflation) and de-duplicate.
    The sealed fact is the tautology `n == n` where n is that true count — the engine's exact
    arithmetic applied to PROGRESS, never a verdict on the learner. The endpoint seals this the SAME
    way steward.py's budget does: hand this result to receipts.attach (which reads verdict + trail;
    it re-runs NO verifier), so this module imports NOTHING from verifiers/derivation.

    Returns {result, count, completed} — result is the receipts-ready dict; count is the honest int.
    """
    valid = {str(u.get("id")) for u in _load()}
    seen: List[str] = []
    for cid in (completed_ids or []):
        c = str(cid)
        if c in valid and c not in seen:
            seen.append(c)
    n = len(seen)
    total = len(valid)
    # A derivation-result shape receipts.record_from_derivation understands: a single HOLDS step
    # asserting the true integer count equals itself. Honest by construction — n is what was counted.
    trail = [{
        "id": "mastery_count",
        "domain": "mathematics",
        "status": "PASS",
        "claim": f"completed units == {n}",
        "detail": f"{n} of {total} curriculum units completed (counted, de-duplicated, existence-checked)",
        "uses": [],
        "link_ok": True,
    }]
    result = {
        "verdict": "HOLDS",
        "steps": 1,
        "confirmed_steps": 1,
        "broken_at": None,
        "gap_at": None,
        "trail": trail,
        "count": n,
        "of": total,
        "completed": seen,
        "note": "The seal is the honest integer count of completed units — never a grade on the child.",
    }
    return {"result": result, "count": n, "of": total, "completed": seen}


def mastery(completed_ids: List[str]) -> Dict[str, Any]:
    """The learner-facing mastery summary (UN-sealed here; the endpoint attaches the receipt via
    receipts.attach on mastery_result()['result'], exactly like steward.budget). Honest count only."""
    m = mastery_result(completed_ids)
    return {
        "kind": "coach_mastery",
        "completed_count": m["count"],
        "of": m["of"],
        "completed": m["completed"],
        "note": "An honest count of units completed — a receipt for progress, never a grade on the child.",
        "generated": False,
    }


# ── the guardrail: NEVER grade or judge a child ─────────────────────────────────────────────

# Phrasings that ask the engine to RANK/JUDGE a child. Coach declines and points to the adult +
# real help — it will not render a model verdict on a person.
_JUDGE_PATTERNS = (
    "is my kid behind", "is my child behind", "is my son behind", "is my daughter behind",
    "what grade level", "grade level", "reading level", "what level is my", "what level is she",
    "what level is he", "how far behind", "is he behind", "is she behind", "are they behind",
    "behind for his age", "behind for her age", "behind for their age", "behind for his grade",
    "behind for her grade", "is my kid slow", "is my child slow", "is my kid smart",
    "is my child smart", "how smart is", "iq of my", "diagnose", "does my kid have", "dyslexi",
    "is my kid normal", "is my child normal", "should i be worried about my", "compare my kid",
    "compare my child", "rank my", "how does my kid compare", "how does my child compare",
    "is my kid failing", "is my child failing", "grade my kid", "grade my child",
)

_JUDGE_MSG = ("I won't grade, rank, or label a child — that's not something a tool should decide, and "
              "no verdict from me could love them the way you do. Reading grows at its own pace. What "
              "I can do is show the next lesson and keep the path steady, one unit at a time.")


def coach_guardrail(text: str) -> Optional[Dict[str, Any]]:
    """Return a refusal+pointer if the request asks Coach to grade/rank/judge a child; None otherwise.
    The boundary, enforced — Coach teaches; it never renders a verdict on a person."""
    t = " " + (text or "").lower() + " "
    if any(p in t for p in _JUDGE_PATTERNS):
        return {
            "kind": "grade_declined",
            "message": _JUDGE_MSG,
            "point_to": [
                "Talk with the child's teacher — they see the whole picture and can help.",
                "A pediatrician or a reading specialist can assess a real concern.",
                "Your local library often has free literacy help and reading buddies.",
            ],
            "do_instead": "Ask me for the next lesson and we'll keep going, at the child's pace.",
            "note": _NOTE,
            "generated": False,
        }
    return None


def guidance() -> Dict[str, Any]:
    """What Coach does, and the boundary it will not cross."""
    return {
        "identity": "Coach — a K-3 reading tutor that grows with the student.",
        "does": [
            "present the curriculum — the map, any unit, and the next lesson (verbatim, deterministic)",
            "keep a lesson continuous — it rides a thread so it never starts over",
            "seal an honest count of units completed — a receipt for progress",
        ],
        "will_not": [
            "grade, rank, label, or judge a child (that stays with the adult + real help)",
            "generate a lesson — it finds and presents the operator's authored teaching",
        ],
        "note": "A window to reading, not a wall. Success is the day they need the tool less (John 3:30).",
        "generated": False,
    }


__all__ = ["overview", "unit", "next_unit", "mastery", "mastery_result", "coach_guardrail",
           "guidance", "reload", "_file"]
