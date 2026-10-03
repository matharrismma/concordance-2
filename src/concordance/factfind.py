"""FACT FIND — what the CHECK door says when nothing in a claim is computable (R5 of
docs/PROJECT_REVIEW_2026-10-03.md; Matt, 2026-10-03: "go in order").

The auditor's extractors turn COMPUTABLE claims (sums, constants, definitional element facts) into verdicts
with receipts. A lookup claim — "the atomic mass of iron is 55.845", "iron melts at 1538 C" — is not computable,
and the door used to answer NOTHING_TO_CHECK and hand back three unrelated cards as "FOUND" (measured live:
a phase-theory card and two lexicon entries for the melting point of iron). This module makes that answer honest,
in three shapes, never blurred with a computed verdict and never minting a receipt:

  1. a FOUND FACT — the keeping's own sourced table holds the property (today: an element's standard atomic
     weight, IUPAC) — and whether it AGREES with the claimed number. Found, cited, not computed.
  2. FOUND CARDS — only cards whose TITLE names the subject (the same gap guard the front door uses), so a
     reader is never handed a lexicon entry for a metallurgy question.
  3. NOT HELD YET — plainly, with a WANT OFFERED (never opened on the engine's own: "nothing records a want on
     its own — bot noise must never write the acquisition queue"). The reader or agent opens it with one call,
     and the library goes to find a public-domain source. The keeping grows by its misses.

Pure where it can be: find_fact() needs only the element table; verify_fallback() takes the search as an
argument so a test can stub it."""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional

# property words -> (lookup field, tolerance: ("abs", x) | ("rel", x) | ("exact", 0), source)
_HELD = {
    "standard atomic weight": ("atomic_mass", ("rel", 1e-3), "IUPAC standard atomic weights (verifiers/periodic_table)"),
    "atomic weight": ("atomic_mass", ("rel", 1e-3), "IUPAC standard atomic weights (verifiers/periodic_table)"),
    "atomic mass": ("atomic_mass", ("rel", 1e-3), "IUPAC standard atomic weights (verifiers/periodic_table)"),
    "atomic number": ("atomic_number", ("exact", 0), "IUPAC element identity (verifiers/periodic_table)"),
    "protons": ("atomic_number", ("exact", 0), "IUPAC element identity (verifiers/periodic_table)"),
}
# properties a reader asks about that the keeping does NOT hold as a sourced table (yet) — named honestly
_NOT_HELD = ("melting point", "melts", "boiling point", "boils", "density", "electronegativity",
             "specific heat", "thermal conductivity", "electrical conductivity", "half-life", "half life",
             "ionization energy", "atomic radius", "hardness")
_NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?(?:\s*[eE]\s*[-+]?\d+)?")
_WORD = re.compile(r"[A-Za-z][A-Za-z-]*")


def element_in(text: str) -> Optional[Dict[str, Any]]:
    """The element the claim names — by name ("iron", any case) or by symbol as its own token ("Fe", "Au")."""
    from .verifiers import periodic_table as _pt
    from . import lookup as _lookup
    names = getattr(_pt, "_BY_NAME", {}) or {}
    for w in _WORD.findall(text or ""):
        low = w.lower()
        if low in names:
            got = _lookup.lookup("element", {"name": low})
            if got.get("found"):
                return got["value"]
    for w in _WORD.findall(text or ""):
        if 1 <= len(w) <= 2 and w[0].isupper() and w not in ("A", "I", "C", "K", "N", "O", "S", "F", "H", "P", "V", "W", "U"):
            got = _lookup.lookup("element", {"symbol": w})
            if got.get("found"):
                return got["value"]
    return None


def number_in(text: str) -> Optional[float]:
    """The claimed number: the LAST number in the claim (claims put their value last)."""
    nums = _NUM.findall(text or "")
    if not nums:
        return None
    try:
        return float(nums[-1].replace(",", "").replace(" ", ""))
    except ValueError:
        return None


def _agrees(value: float, claimed: float, tol) -> bool:
    kind, x = tol
    if kind == "exact":
        return float(value) == float(claimed)
    if kind == "abs":
        return abs(value - claimed) <= x
    return abs(value - claimed) <= abs(value) * x


def find_fact(claim: str) -> Optional[Dict[str, Any]]:
    """A found fact about an element, or 'not held' for a property the keeping lacks, or None when the claim
    names no element or no property."""
    el = element_in(claim)
    if not el:
        return None
    low = (claim or "").lower()
    for words in sorted(_HELD, key=len, reverse=True):
        if words in low:
            field, tol, source = _HELD[words]
            value = el.get(field)
            claimed = number_in(claim)
            out = {"kind": "element", "subject": el["name"], "symbol": el["symbol"], "property": words,
                   "field": field, "value": value, "source": source, "claimed": claimed}
            out["agrees"] = (claimed is not None and value is not None and _agrees(float(value), float(claimed), tol))
            return out
    for words in _NOT_HELD:
        if re.search(r"\b" + re.escape(words) + r"\b", low):
            return {"kind": "element", "subject": el["name"], "symbol": el["symbol"], "property": words,
                    "held": False, "source": None}
    return None


def verify_fallback(claim: str, checked: Optional[str] = None,
                    search: Optional[Callable[..., List[Dict[str, Any]]]] = None) -> Dict[str, Any]:
    """The honest answer when claims_found is 0: {found_fact} | {found: on-subject briefs} | {found: [], want}.
    `search(query, limit=3)` defaults to the keeping's question search; `checked` is the airlocked text."""
    from . import ask as _ask, corpus as _corpus
    search = search or (lambda q, limit=3: _corpus.search_question(q, limit=limit))
    out: Dict[str, Any] = {}
    ff = find_fact(claim)
    if ff and ff.get("field"):
        out["found_fact"] = ff
        verb = "agrees with" if ff.get("agrees") else "does NOT agree with"
        out["note"] = (f"No computable claim to prove here — but the keeping's own sourced table holds this: "
                       f"{ff['subject']} ({ff['symbol']}) {ff['property']} = {ff['value']} ({ff['source']}), which "
                       f"{verb} the claimed {ff.get('claimed')}. FOUND and cited, not a computed verdict; no receipt.")
        return out
    subject = ff["subject"] if ff else None
    try:
        hits = search(checked or claim, limit=3) or []
    except Exception:  # noqa: BLE001 — the find is a bonus; never break the verify answer
        hits = []
    probe = subject or (claim or "")
    on_subject = [c for c in hits if isinstance(c, dict) and _ask._title_names_subject(probe, c)]
    if on_subject:
        out["found"] = [_corpus._brief(c) for c in on_subject]
        out["note"] = ("No computable claim to prove here — the engine proves numbers, formulas and constants "
                       "with a receipt. The keeping does hold this subject, FOUND and cited below (not a computed "
                       "verdict, no receipt): read the source and decide. For a question rather than a claim, use /ask.")
        return out
    want_q = f"{subject} {ff['property']}" if ff and ff.get("property") else (claim or "").strip()[:200]
    out["found"] = []
    out["want"] = {"query": want_q,
                   "offer": "The keeping holds nothing on this yet. Open a want and the library goes to find a "
                            "public-domain source for it; the keeping grows by its misses.",
                   "how": "POST /want {query, kind: 'missing'} — or the want_open tool on the agent door"}
    if ff and ff.get("held") is False:
        out["note"] = (f"No computable claim to prove here, and the keeping does not yet hold a sourced table for "
                       f"the {ff['property']} of {ff['subject']} — said plainly, not papered over with unrelated cards. "
                       f"A want is offered; nothing is invented.")
    else:
        out["note"] = ("No computable claim to prove here, and no card in the keeping names this subject — said "
                       "plainly. A want is offered; nothing is invented.")
    return out
