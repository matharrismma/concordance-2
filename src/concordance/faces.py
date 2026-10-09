"""The expert faces — callable life-domain servants (Phase 3 of the specialist layer).

A FACE is not a model and holds no knowledge of its own. It is a deterministic COMPOSER: it assembles
the specialists we already have — the crisis gate, scoped search over the keeping, discern, and the
verifiers — into the answer a wise servant in that life-domain would give. It NEVER generates prose (the
`manner` is a fixed frame; the content is the keeping's), points to Christ and never to itself
(companion→Christ), defers to the crisis net first, and fails closed (an honest GAP over a bluff).

This keeps the sovereign core deterministic and no-LLM: a face only ARRANGES what already passed the
gates. See docs/EXPERT_FACES.md for the design. Scaffold — one face wired end-to-end + the registry;
NOT deployed until reviewed.
"""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional

from . import physiology

# A face is DATA (see docs/EXPERT_FACES.md): a servant role over existing components.
#   scope       — words that route a request to this face
#   shelves      — the keeping it draws on first (search is scoped here, then falls back)
#   verifiers    — domains whose deterministic checkers it runs on checkable claims
#   discernment  — whether the discern calibration applies (worldview/spiritual weight)
#   manner       — the FIXED frame for how the servant speaks (never generated)
_FACES: Dict[str, Dict[str, Any]] = {
    # TASK DETERMINES TITLE (Matt, 2026-10-08): this face's task is to count the cost, so it is the Bookkeeper.
    # "the Steward" is the one voice that meets the visitor and brings the right role (ask.respond → role);
    # the id stays — an id is an address, not a title.
    "face_steward": {
        "name": "the Bookkeeper",
        "scope": ["money", "budget", "debt", "provision", "save", "spend", "tithe", "steward",
                  "afford", "cost", "income", "expense", "loan", "rent", "mortgage"],
        "shelves": {"economics", "reference"},
        "verifiers": ["finance", "economics"],
        "discernment": True,
        # the steward COUNTS the cost and never EXECUTES a transaction (loss-leaders + stewardship)
        "manner": "the bookkeeper — count the cost plainly, never act for you; provision is under God, "
                  "who gives and is trusted (Matthew 6). We inform; the stewarding stays yours.",
    },
    "face_tutor": {
        "name": "the Tutor",
        "scope": ["learn", "teach", "explain", "study", "understand", "how does", "what is",
                  "help me learn", "lesson", "practice"],
        "shelves": {"mathematics", "physics", "chemistry", "biology", "reference", "countries"},
        "verifiers": ["mathematics", "physics", "chemistry", "biology"],
        "discernment": False,
        "manner": "the tutor — from first principles, one step at a time, showing the working so you own it.",
    },
    "face_social_worker": {
        "name": "the Social Worker",
        "scope": ["help", "need", "hungry", "homeless", "shelter", "water", "food", "power",
                  "first aid", "emergency", "cold", "no money", "evicted", "unemployed"],
        "shelves": {"survival", "firstaid", "water", "food", "power", "sanitation", "comms"},
        "verifiers": [],
        "discernment": True,
        # crisis-first is enforced by compose() regardless; this manner is for genuine hardship
        "manner": "the social worker — meet the need first and in dignity; the next small, doable step, "
                  "and the people and resources that can stand with you.",
    },
    "face_theorist": {
        "name": "the Theorist",
        "scope": ["theory", "why", "principle", "model", "prove", "derive", "equation", "law",
                  "mechanism", "how come", "explain why"],
        "shelves": {"mathematics", "physics", "chemistry", "forms", "calculations"},
        "verifiers": ["mathematics", "physics", "chemistry"],
        "discernment": False,
        "manner": "the theorist — the one form beneath the many cases; the same computation under a "
                  "change of variable, and the theory it rests on.",
    },
}

_WORD = re.compile(r"[a-z0-9]+")


def faces() -> Dict[str, Dict[str, Any]]:
    """The registry (read-only view): id -> {name, scope, shelves, verifiers, discernment, manner}."""
    return {fid: {k: v for k, v in f.items()} for fid, f in _FACES.items()}


def _scores(text: str) -> Dict[str, int]:
    """Each face's fitness for the request: how many of its scope phrases the request trips."""
    toks = set(_WORD.findall((text or "").lower()))
    low = " " + (text or "").lower() + " "
    scores: Dict[str, int] = {}
    for fid, f in _FACES.items():
        score = 0
        for s in f["scope"]:
            # multi-word phrases matched as substrings, single words as tokens
            score += (1 if s in low else 0) if " " in s else (1 if s in toks else 0)
        scores[fid] = score
    return scores


def route(text: str) -> Optional[str]:
    """Which face does this request call for? The face whose scope the request overlaps most; None if
    nothing overlaps (the caller then uses the ordinary front door — a face is never forced).

    When the allocation lever (physiology) is on, a TIE in fitness is broken toward the caste with
    capacity — division of labor + the homeostatic brake — and re-allocates to an available caste if the
    fittest is out. It only ever reorders WITHIN the top fitness tier; it never routes to a face the
    request does not fit, so the plain routing is unchanged whenever there is a single clear best."""
    if not _WORD.findall((text or "").lower()):
        return None
    scores = _scores(text)
    if physiology.enabled():
        return physiology.allocate(scores)
    best, best_score = None, 0
    for fid, score in scores.items():
        if score > best_score:
            best, best_score = fid, score
    return best if best_score > 0 else None


def compose(face_id: str, text: str, config: Any = None, *,
            crisis_fn: Optional[Callable[[str], bool]] = None,
            search_fn: Optional[Callable[..., List[dict]]] = None,
            discern_fn: Optional[Callable[..., Dict[str, Any]]] = None,
            verify_fn: Optional[Callable[[List[Dict[str, Any]]], Dict[str, Any]]] = None,
            ) -> Dict[str, Any]:
    """Assemble a face's answer, deterministically. NEVER generates: returns a structured result the
    caller renders. The dependencies are injectable for tests; they default to the live specialists.

    Order (docs/EXPERT_FACES.md): crisis gate → gather (scoped) → discern → verify → render-frame.
    """
    face = _FACES.get(face_id)
    if face is None:
        return {"error": "unknown face", "face": face_id}

    _is_crisis = crisis_fn or (lambda t: __import__("concordance.ask", fromlist=["is_crisis"]).is_crisis(t))
    # 1. CRISIS FIRST — a face never speaks over a cry (help-first, never overridden).
    if _is_crisis(text):
        return {"face": face_id, "name": face["name"], "kind": "crisis",
                "handoff": "crisis", "gathered": [], "verify": None, "discern": None,
                "manner": face["manner"],
                "means": "a cry outranks the servant — this is handed to the crisis response, real people first"}

    # This servant is now doing the work — record a unit of recent load (aggregate, content-free) so the
    # allocation lever can balance the castes and regulate the rate. No-op unless the lever is on.
    if physiology.enabled():
        physiology.note(face_id)

    # 2. GATHER — scoped to the face's shelves first (the servant's own substance), then the keeping.
    if search_fn is None:
        from . import corpus as _corpus
        def search_fn(q, shelves=None, limit=6):  # noqa: E306
            return _corpus.search(q, limit=limit, shelves=shelves)
    hits = search_fn(text, shelves=set(face["shelves"]), limit=6) or []
    if not hits:
        hits = search_fn(text, shelves=None, limit=6) or []   # fall back to the whole keeping
    gathered = [_brief(h) for h in hits[:6]]

    # 3. DISCERN — the front-door proposal. It does two jobs: it names the checkable CLAIM (which the
    # verify step needs) AND, where the face carries worldview weight, the calibration. So it ALWAYS
    # runs (crisis was already handled above); the `discernment` flag only governs whether the
    # calibration is SHOWN, not whether the claim is proposed.
    if discern_fn is None:
        from . import discern as _discern
        discern_fn = _discern.served
    try:
        proposal = discern_fn(text)
    except Exception:  # noqa: BLE001 — discern must never crash the servant
        proposal = None
    discern = proposal if face["discernment"] else None

    # 4. VERIFY — run the face's verifiers on a checkable claim IF the proposal named structured steps.
    verify = None
    steps = _steps_from_discern(proposal, face["verifiers"])
    if steps:
        if verify_fn is None:
            from .derivation import verify_derivation as verify_fn  # noqa: E501
        try:
            verify = verify_fn(steps)
        except Exception:  # noqa: BLE001 — our failure is not their falsehood; report GAP, never crash
            verify = {"verdict": "SYSTEM_ERROR", "detail": "verifier raised", "trail": []}

    # 5. RENDER FRAME — DATA the caller renders; the manner is fixed, the content is the keeping's.
    return {
        "face": face_id, "name": face["name"], "kind": "served",
        "manner": face["manner"],
        "gathered": gathered,               # cards from the keeping (the substance)
        "discern": discern,                 # the calibration proposal (or None)
        "verify": verify,                   # a worked, sealed verdict (or None = GAP: nothing checkable)
        "shelves": sorted(face["shelves"]),
        "means": ("this servant ARRANGES what the keeping holds and the gates passed — it does not "
                  "author; where it cannot check, it says so. The eye is turned upward, not to itself."),
    }


def _brief(c: dict) -> Dict[str, Any]:
    from . import corpus as _corpus
    try:
        return _corpus._brief(c)
    except Exception:  # noqa: BLE001
        return {"id": c.get("id"), "title": c.get("title"), "shelf": c.get("shelf")}


def _steps_from_discern(discern: Optional[Dict[str, Any]], verifiers: List[str]) -> List[Dict[str, Any]]:
    """If discern proposed one or more STRUCTURED checkable claims in a domain this face verifies,
    shape them into verify_derivation steps. Conservative: no structured claim → no steps → honest GAP."""
    if not discern or not verifiers:
        return []
    claim = discern.get("claim")
    if not isinstance(claim, dict):
        return []
    dom = str(claim.get("domain") or "").lower()
    if dom and dom not in {v.lower() for v in verifiers}:
        return []
    spec = claim.get("spec") or {"mode": claim.get("mode"), "params": claim.get("params", {})}
    if not spec.get("mode"):
        return []
    return [{"id": "s", "domain": dom or verifiers[0], "spec": spec}]
