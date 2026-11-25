"""THE STATUS DOOR (2026-11-25, Matt: "build the status door").

A claim like "The Riemann hypothesis has been proved" holds nothing an extractor can compute, so /verify answered
NOTHING_TO_CHECK - while the keeping already charts that very question on a tick stick, whose fit says exactly what is
sealed, cited, closed and open. This door reads the stick and says so: CITED, the stick's own reading, never a
computed verdict and never a receipt.

It answers only for a question named plainly. The names below are curated, most specific first (the generalized and
the finite-field Riemann hypotheses before the Riemann hypothesis), and none is a bare acronym: "RH" is also relative
humidity and "BSD" a licence, and a door that seats the wrong stick is worse than silence (the router held on
2026-11-19 for exactly that). A question no stick charts gets no status.

Served by GET /status?q=..., and by the verify fallback (factfind.verify_fallback) on both the web and the agent
doors, so a status claim sent to verify is answered by the stick instead of by silence.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

# (stick id, the names the question goes by) - FIRST MATCH WINS, so the more specific questions come first.
NAMED: List[Tuple[str, List[str]]] = [
    ("stick_generalized_riemann_hypothesis",
     [r"generali[sz]ed riemann hypothesis", r"extended riemann hypothesis", r"grand riemann hypothesis"]),
    ("stick_finite_field_the_weil_riemann_hypothesis",
     [r"weil conjectures?", r"riemann hypothesis (?:over|for) (?:a |the )?finite fields?"]),
    ("stick_the_de_bruijn_newman_constant", [r"de bruijn[\s\-–]+newman"]),
    ("stick_the_hilbert_polya_conjecture", [r"hilbert[\s\-–]+p[oó]lya"]),
    ("stick_riemann_hypothesis", [r"riemann(?:'s)? hypothesis", r"riemann conjecture"]),
    ("stick_poincare_conjecture", [r"poincar[eé](?:'s)? conjecture"]),
    ("stick_p_versus_np", [r"\bp\s*(?:versus|vs\.?|=|!=|≠|=/=)\s*np\b"]),
    ("stick_navier_stokes_existence_and_smoothness", [r"navier[\s\-–]+stokes"]),
    ("stick_3d_euler_equations_finite_time_singularity",
     [r"\beuler equations?\b[^.]{0,60}\b(?:blow|singular|smooth)", r"\b(?:blow[\s\-]?up|singularit\w*)\b[^.]{0,60}\beuler equations?\b"]),
    ("stick_yang_mills_existence_and_mass_gap", [r"yang[\s\-–]+mills", r"\bmass gap\b"]),
    ("stick_hodge_conjecture", [r"hodge conjecture"]),
    ("stick_birch_and_swinnerton_dyer_conjecture",
     [r"birch(?:\s+and\s+|[\s\-–]+)swinnerton[\s\-–]+dyer", r"\bbsd conjecture\b"]),
    ("stick_the_jacobian_conjecture", [r"jacobian conjecture"]),
    ("stick_the_langlands_program", [r"\blanglands\b"]),
]
_COMPILED = [(sid, [re.compile(p, re.IGNORECASE) for p in pats]) for sid, pats in NAMED]


def match(text: str) -> Optional[str]:
    """The stick a plainly named question points at, or None."""
    t = (text or "")[:2000]
    for sid, pats in _COMPILED:
        if any(p.search(t) for p in pats):
            return sid
    return None


def status_of(text: str, data_dir=None) -> Optional[Dict[str, Any]]:
    """The stick's own reading for the question these words name: CLOSED (with the closed mark, its source) or OPEN
    (with what is held). None when no named question matches or the stick is not on this node."""
    sid = match(text)
    if not sid:
        return None
    from . import tickstick as TS
    r = TS.read(sid, data_dir)
    if not r.get("ok"):
        return None
    f = r.get("fit") or {}
    closed = next((t for t in r.get("ticks") or [] if t.get("kind") == "closed"), None)
    best = f.get("verified_up_to") or None
    out: Dict[str, Any] = {
        "stick": sid,
        "question": r.get("question"),
        "statement": r.get("statement"),
        "status": "CLOSED" if closed else "OPEN",
        "reads": f.get("open"),
        "held": {
            "verified_up_to": ({"up_to": best.get("up_to"), "unit": best.get("unit")} if isinstance(best, dict) else None),
            "verified_instances": f.get("verified_instances", 0),
            "witnesses": f.get("witnesses", 0),
            "equivalent_statements": len(f.get("equivalent_statements") or []),
            "excluded_approaches": len(f.get("excluded_approaches") or []),
            "postulates": len(f.get("postulates") or []),
            "notes": len(f.get("record") or []),
        },
        "kind": "CITED",
        "means": ("the tick stick's own reading of what the keeping holds on this question - cited, not a computed "
                  "verdict, and no receipt. It does not judge the words it was given; read the stick for what is "
                  "sealed, cited and open."),
        "link": f"/stick?id={sid}",
    }
    if closed:
        out["closed_by"] = {"claim": closed.get("claim"), "source": closed.get("source")}
    return out


def sentence(st: Dict[str, Any]) -> str:
    """One line for a note: what the stick reads, cut where the fit cuts."""
    head = f"the keeping charts this question on a tick stick ({st.get('question')}), and it reads {st.get('status')}"
    if st.get("status") == "CLOSED" and st.get("closed_by"):
        return head + ": " + str(st["closed_by"].get("claim") or "")[:200]
    return head + ": " + str(st.get("reads") or "")[:200]
