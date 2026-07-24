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

# ── curriculum load (verbatim data, cached, MULTI-SUBJECT) ──────────────────────────────────
# Each subject is one <subject>_en.json in the curriculum dir, ported verbatim by migrate_school.
# 'read' (phonics) is the default door in; the others (mcguffey, aesop, founding, pilgrims, es, …)
# grow with the student. Subjects are DISCOVERED from the files present — drop in a new *_en.json
# and it appears, no code change. Conduit: found content, never generated.

DEFAULT_SUBJECT = "read"
_LABELS = {
    "read": "Learn to Read (phonics)", "mcguffey": "McGuffey Readers", "aesop": "Aesop's Fables",
    "founding": "Founding Documents", "pilgrims": "Pilgrim's Progress", "es": "Español (Spanish)",
    "bible": "Bible Study",
}
_CACHE: Dict[str, List[Dict[str, Any]]] = {}
_SUBJECTS: Optional[List[str]] = None


def _curr_dir() -> Path:
    """The curriculum directory. CONCORDANCE_CURRICULUM_DIR / CONCORDANCE_DATA_DIR override the default."""
    env = os.environ.get("CONCORDANCE_CURRICULUM_DIR", "").strip()
    if env:
        return Path(env)
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    return (Path(data) / "curriculum") if data else (Path("data") / "curriculum")


def _file(subject: str = DEFAULT_SUBJECT) -> Path:
    """The path for one subject's curriculum (<subject>_en.json)."""
    return _curr_dir() / (str(subject or DEFAULT_SUBJECT) + "_en.json")


def _discover() -> List[str]:
    """The subjects present, as <subject> stems of the *_en.json files. 'read' first if present."""
    global _SUBJECTS
    if _SUBJECTS is not None:
        return _SUBJECTS
    found: List[str] = []
    try:
        for p in sorted(_curr_dir().glob("*_en.json")):
            found.append(p.name[:-len("_en.json")])
    except OSError:
        found = []
    if DEFAULT_SUBJECT in found:
        found = [DEFAULT_SUBJECT] + [s for s in found if s != DEFAULT_SUBJECT]
    _SUBJECTS = found
    return _SUBJECTS


def _load(subject: str = DEFAULT_SUBJECT) -> List[Dict[str, Any]]:
    """Load one subject's units verbatim (cached). Missing/unreadable -> empty (never raises)."""
    subject = str(subject or DEFAULT_SUBJECT)
    if subject in _CACHE:
        return _CACHE[subject]
    try:
        data = json.loads(_file(subject).read_text(encoding="utf-8"))
        units = data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        units = []
    _CACHE[subject] = [u for u in units if isinstance(u, dict) and u.get("id")]
    return _CACHE[subject]


def reload() -> int:
    """Drop all caches and re-read from disk (for the migrator/tests). Returns the default subject's count."""
    global _CACHE, _SUBJECTS
    _CACHE = {}
    _SUBJECTS = None
    return len(_load(DEFAULT_SUBJECT))


def subjects() -> Dict[str, Any]:
    """The subjects a learner can study — the door in ('read') plus whatever else is present."""
    out = [{"id": s, "title": _LABELS.get(s, s.replace("_", " ").title()), "count": len(_load(s))}
           for s in _discover()]
    return {"kind": "coach_subjects", "subjects": out, "default": DEFAULT_SUBJECT,
            "note": _NOTE, "generated": False}


def _all_unit_ids() -> set:
    """Every unit id across every subject — so a completed count is honest across the whole school."""
    return {str(u.get("id")) for s in _discover() for u in _load(s)}


def _ordered(subject: str = DEFAULT_SUBJECT) -> List[Dict[str, Any]]:
    """One subject's units in a STABLE, deterministic teaching order: by unit_seq, then id."""
    def _seq(u: Dict[str, Any]) -> int:
        try:
            return int(u.get("unit_seq", 10 ** 9))
        except (TypeError, ValueError):
            return 10 ** 9
    return sorted(_load(subject), key=lambda u: (_seq(u), str(u.get("id", ""))))


# ── find + present (never generate) ─────────────────────────────────────────────────────────

_NOTE = "Coach finds and presents the lesson; it never generates it, and never grades a child."


def overview(subject: str = DEFAULT_SUBJECT) -> Dict[str, Any]:
    """The map of one subject's path: how many units, the tracks, and the ordered unit briefs.
    Found and cited, never generated. subject defaults to the reading path ('read')."""
    subject = str(subject or DEFAULT_SUBJECT)
    units = _ordered(subject)
    tracks: List[str] = []
    for u in units:
        t = str(u.get("track") or "")
        if t and t not in tracks:
            tracks.append(t)
    briefs = [{"id": u.get("id"), "title": u.get("title"), "unit_seq": u.get("unit_seq"),
               "track": u.get("track"), "prerequisites": list(u.get("prerequisites") or []),
               "next": u.get("next")} for u in units]
    return {
        "kind": "coach_overview",
        "subject": subject,
        "subject_title": _LABELS.get(subject, subject.replace("_", " ").title()),
        "count": len(units),
        "tracks": tracks,
        "units": briefs,
        "source": "Read-school curriculum (offline), ported verbatim.",
        "note": _NOTE,
        "generated": False,
    }


# ── the one lifelong journey ─────────────────────────────────────────────────────────────────
# Coach is for ANY AGE. It starts at the very youngest (the first letter) and STAYS WITH YOU —
# the separate subjects are one arc that climbs from letters, through the readers and the great
# works, and opens into the whole keeping: the Word, and the floor of all discovery. You can enter
# at the beginning or wherever you already are; it never graduates you out. Success is the day you
# no longer need it (John 3:30) — and the path still points on, to Christ.
_JOURNEY = [
    ("read", "subject", "Learn to read",
     "the very first letters and their sounds — for the youngest, and for anyone beginning"),
    ("mcguffey", "subject", "First readers", "words into sentences, and sentences into stories"),
    ("aesop", "subject", "Fables", "short stories that carry wisdom"),
    ("pilgrims", "subject", "Pilgrim's Progress", "the great allegory of the journey home"),
    ("founding", "subject", "Founding documents", "the words a free people stand on"),
    ("/bible.html", "keeping", "The Word",
     "Scripture itself — where the whole path has been leading"),
    ("/floor.html", "keeping", "The whole floor",
     "the sciences, history, the created order — all of it, connected, and how it points to the Maker"),
]
_OPENING = ("For any age. A child at their first letter, someone learning to read late, or anyone "
            "climbing higher — start at the very beginning, or wherever you already are. I will "
            "stay with you, as far as you want to go.")


def journey(done_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """The one lifelong arc — the stages a learner climbs, at any age, from the first letter up into
    the whole keeping. If `done_ids` is given, also names WHERE the learner is and the next step, so
    the path stays with them across the whole journey. Progress is caller-held (no personal data)."""
    present = set(_discover())
    stages: List[Dict[str, Any]] = []
    for ident, kind, title, note in _JOURNEY:
        if kind == "subject" and ident not in present:
            continue
        st = {"kind": kind, "title": title, "note": note}
        if kind == "subject":
            st["subject"] = ident
            st["count"] = len(_load(ident))
        else:
            st["ref"] = ident
        stages.append(st)
    out = {"kind": "coach_journey", "for_any_age": True, "opening": _OPENING,
           "stages": stages, "note": _NOTE, "generated": False}
    if done_ids is not None:
        out["where_next"] = where_next(done_ids)
    return out


def where_next(done_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """The single next step across the WHOLE journey. Walks the arc; inside a subject returns the
    next un-done unit; when a subject is finished it advances; when all the school is done it opens
    the keeping — which never ends. Never a grade, never a coin flip — just the next step."""
    done = {str(x) for x in (done_ids or []) if x}
    present = set(_discover())
    for ident, kind, title, note in _JOURNEY:
        if kind == "keeping":
            return {"kind": "coach_journey_next", "stage": "keeping", "title": title, "note": note,
                    "ref": ident, "generated": False}
        if ident not in present:
            continue
        remaining = [u for u in _ordered(ident) if str(u.get("id")) not in done]
        if remaining:
            u = remaining[0]
            return {"kind": "coach_journey_next", "stage": ident, "subject": ident,
                    "stage_title": title, "note": note,
                    "next_unit": {"id": u.get("id"), "title": u.get("title")}, "generated": False}
    return {"kind": "coach_journey_next", "stage": "keeping", "title": "The whole floor",
            "ref": "/floor.html", "note": "The school is walked; the keeping is open, and it stays "
            "with you.", "generated": False}


def unit(unit_id: str, subject: str = DEFAULT_SUBJECT) -> Dict[str, Any]:
    """One unit, VERBATIM as authored — the rule, examples, decodable sentence, checks, next.
    Searches the given subject first, then any subject (ids are subject-unique), so a caller need not
    know the subject. Returns kind:coach_unit_not_found (never a guess) when the id is unknown."""
    uid = str(unit_id or "")
    order = [str(subject or DEFAULT_SUBJECT)] + [s for s in _discover() if s != subject]
    for subj in order:
        for u in _load(subj):
            if u.get("id") == uid:
                out = dict(u)  # the operator's teaching, unaltered
                out["kind"] = "coach_unit"
                out["subject"] = subj
                out["note"] = _NOTE
                out["generated"] = False
                return out
    return {"kind": "coach_unit_not_found", "id": uid,
            "message": "No unit by that id. See /coach/overview for the path.",
            "note": _NOTE, "generated": False}


def next_unit(after: Optional[str] = None, subject: str = DEFAULT_SUBJECT) -> Dict[str, Any]:
    """The next lesson to teach, deterministically, within a subject. after=None -> the first unit;
    after=<id> -> the unit that follows it in the stable teaching order. Past the end -> coach_complete.
    A lesson is a continuing chain (ride threads.py for continuity); this only decides WHICH unit."""
    subject = str(subject or DEFAULT_SUBJECT)
    units = _ordered(subject)
    if not units:
        return {"kind": "coach_empty", "message": "No curriculum is loaded yet.",
                "note": _NOTE, "generated": False}
    if after is None or str(after) == "":
        first = units[0]
        return {"kind": "coach_next", "after": None, "subject": subject,
                "unit": unit(str(first.get("id")), subject),
                "position": 1, "of": len(units), "note": _NOTE, "generated": False}
    ids = [str(u.get("id")) for u in units]
    aid = str(after)
    if aid not in ids:
        # Unknown anchor — do not guess. Point back to the map.
        return {"kind": "coach_next_unknown_anchor", "after": aid, "subject": subject,
                "message": "That unit id isn't in the path. See /coach/overview.",
                "note": _NOTE, "generated": False}
    idx = ids.index(aid)
    if idx + 1 >= len(units):
        return {"kind": "coach_complete", "after": aid, "subject": subject,
                "message": "That was the last unit in this path. Well done — keep reading.",
                "position": len(units), "of": len(units), "note": _NOTE, "generated": False}
    nxt = units[idx + 1]
    return {"kind": "coach_next", "after": aid, "subject": subject,
            "unit": unit(str(nxt.get("id")), subject),
            "position": idx + 2, "of": len(units), "note": _NOTE, "generated": False}


def recommend(completed_ids: Optional[List[str]] = None, subject: str = DEFAULT_SUBJECT) -> Dict[str, Any]:
    """Adaptive 'where you are / what's next' within a subject: given the units already completed,
    point to the next lesson whose prerequisites are all met — grows with the student. Deterministic
    and FOUND: it only chooses WHICH authored unit comes next; never generates or judges the child.
    The caller holds progress (no personal data server-side). All done -> kind:coach_complete."""
    subject = str(subject or DEFAULT_SUBJECT)
    done = {str(x) for x in (completed_ids or [])}
    units = _ordered(subject)
    if not units:
        return {"kind": "coach_empty", "subject": subject, "message": "No curriculum is loaded yet.",
                "note": _NOTE, "generated": False}
    total = len(units)
    here = done & {str(u.get("id")) for u in units}   # completed within THIS subject
    # First un-done unit whose prerequisites are satisfied (the natural next step).
    for i, u in enumerate(units):
        uid = str(u.get("id"))
        if uid in done:
            continue
        prereqs = [str(p) for p in (u.get("prerequisites") or [])]
        if all(p in done for p in prereqs):
            return {"kind": "coach_recommend", "subject": subject, "unit": unit(uid, subject),
                    "completed": len(here), "position": i + 1, "of": total, "note": _NOTE, "generated": False}
    # None with met prerequisites: either everything is done, or a gap. Never guess past the end.
    if len(here) >= total:
        return {"kind": "coach_complete", "subject": subject, "completed": total, "of": total,
                "message": "Every unit in this path is complete. Well done — keep reading.",
                "note": _NOTE, "generated": False}
    for i, u in enumerate(units):  # fall back to the first un-done unit in order (prereqs unmet upstream)
        if str(u.get("id")) not in done:
            return {"kind": "coach_recommend", "subject": subject, "unit": unit(str(u.get("id")), subject),
                    "completed": len(here),
                    "position": i + 1, "of": total, "note": _NOTE, "generated": False}
    return {"kind": "coach_complete", "completed": total, "of": total, "note": _NOTE, "generated": False}


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
    valid = _all_unit_ids()   # honest across every subject present (read, mcguffey, aesop, …)
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
