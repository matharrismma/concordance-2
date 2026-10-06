"""THE LEAD — one body that discerns the needed solution, tools, technique, and strategy, then applies.

Matt, 2026-10-06: *"Make sure this leads. We should be one thing that discerns the needed tools, technique
and strategy. Then apply those tools correctly."* And: *"look back at archetypes … the types identified in
the Bible. Use them to find a more applicable solution."*

This composes what the engine already holds into one leading motion — it authors nothing, invents no
tactic, renders no verdict of its own. Crisis outranks all. The verifiers remain the only authority on
truth, and Christ is where every road here leads.

  1. SOLUTION (most applicable, leads)  archetypes.match — the biblical TYPE this situation is an instance
     of, and the canonical Word that met that hour (David before Goliath; the prodigal on the road home).
  2. TOOL                               router.route — which member of the body should handle it.
  3. TECHNIQUE                          the refined-system witness (the games) whose craft bears on it.
  4. STRATEGY                           principles.apply — the patterns, the figures' own words, and
                                        where the same move has FAILED (read the boundary before applying).
  5. APPLY                              the gate, on whatever in the situation is computably checkable —
                                        a verdict and a re-checkable receipt; nothing forced, nothing faked.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

# The refined-system TECHNIQUE witnesses the engine holds, and the cues that call each. Only witnesses
# that exist as verifier domains are named; a situation that calls none is told so (never a forced fit).
_TECHNIQUE = {
    "pressure_fighting": ("fight fought fighting clinch cage wrestl grappl grapple takedown pressure spar "
                          "bout mma box boxing punch strike opponent jab submission mount guard"),
    "chess": "chess position tempo gambit endgame checkmate pawn opening zugzwang board",
    "game_theory": "payoff equilibrium nash dominant bluff cooperate defect incentive negotiat zero-sum bargain",
    "sports_analytics": "season team win loss record elo rating standings baseball pythagorean",
}


def _technique_for(situation: str) -> List[Dict[str, Any]]:
    s = " " + (situation or "").lower() + " "
    out = []
    for name, cues in _TECHNIQUE.items():
        hits = [c for c in cues.split() if (" " + c) in s or (c + " ") in s]
        if hits:
            out.append({"witness": name, "cues": hits[:4]})
    return out


def lead(situation: str, *, apply_fn: Optional[Callable[[str], Dict[str, Any]]] = None) -> Dict[str, Any]:
    """A situation in; the discerned solution + tool + technique + strategy out, with what is checkable
    applied. Composes archetypes, router, principles, the game witnesses, and the gate — never generating.
    `apply_fn(situation) -> audit result` is injected so the seed stays pure; the door binds the real gate."""
    from . import ask, archetypes, router, principles

    t = (str(situation) if situation else "").strip()
    if not t:
        return {"situation": situation, "kind": "empty",
                "why": "nothing was brought", "next": "name the situation in your own words"}

    # 1. CRISIS outranks everything — real people, never the tools, never a verdict.
    if ask.is_crisis(t):
        return {"situation": t, "kind": "crisis", "route": {"member": "crisis"},
                "resources": list(ask._CRISIS_RESOURCES),
                "why": "discerned as a cry for help — routed to real people first, not the engine",
                "next": "real_help"}

    # 2. THE MORE APPLICABLE SOLUTION — the biblical type this situation is an instance of (it leads).
    types = archetypes.match(t, k=2)
    solution = None
    if types:
        best = types[0]
        solution = {"biblical_type": f"{best['character']} — {best['moment']}", "meets": best["meets"],
                    "word": best["scripture"], "frame": best.get("frame"),
                    "also": [f"{x['character']} — {x['moment']}" for x in types[1:]],
                    "note": "the most applicable solution is the Word that met this hour; it is offered, "
                            "not stamped on anyone, and every road here leads to Christ."}

    # 3. TOOL — which member should handle it.
    route = router.route(t)
    # 4. TECHNIQUE — the refined-system witness whose craft bears on it.
    technique = _technique_for(t)
    # 5. STRATEGY — the patterns, the figures' verbatim principles, and where the move has failed.
    strat = principles.apply(t)

    # 6. APPLY — the gate, on whatever is computably checkable in the situation.
    applied = None
    if apply_fn is not None:
        try:
            ar = apply_fn(t)
            if isinstance(ar, dict):
                applied = {"verdict": ar.get("verdict"), "claims_found": ar.get("claims_found"),
                           "checks": ar.get("checks") or [c for c in (ar.get("results") or [])],
                           "receipt": ar.get("receipt") or ((ar.get("seal") or {}).get("cite_url"))}
        except Exception:  # noqa: BLE001 — apply is a beat of the proposal; it must not sink it
            applied = None

    return {
        "situation": t, "kind": "situation",
        "solution": solution or {"found": False,
                                 "note": "no biblical type clearly matched — said rather than forced"},
        "discerned": {
            "tool": {"member": route.get("member"), "why": route.get("why"),
                     "alternatives": route.get("alternatives")},
            "technique": technique or "no refined-system witness clearly bears — none proposed",
            "strategy": ({"patterns": [{"title": p["title"], "gist": p["gist"],
                                        "proof": (p.get("proof") or {}).get("figures"),
                                        "principles": p["principles"][:2],
                                        "where_it_failed": p["where_it_failed"][:1]}
                                       for p in strat["patterns"]]}
                         if strat.get("found") else {"found": False, "detail": strat.get("detail")}),
        },
        "applied": applied or {"note": "nothing in this situation was computably checkable; the solution "
                                        "is the Word and the technique to live out, not a verdict to compute"},
        "guard": ("Composes what the engine holds — the biblical type, the tool, the technique, the "
                  "strategy — and applies only what is checkable. It authors nothing and renders no verdict "
                  "of its own; the verifiers are the authority, and Christ is where every road leads."),
        "next": ("apply the tool to a checkable claim (POST /verify), read the strategy's where-it-failed "
                 "before using the pattern, and sit with the Word that met this hour"),
    }
