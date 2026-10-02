"""The Lookup — the one door for "what IS this value", the found-value twin of `verify`.

concordance-2 could always CHECK a claimed value ("is 18 g/mol the molar mass of H2O?"); this is the
other half a reader needs first — RETURN the value ("what is the molar mass of H2O?"). It is
consolidated exactly like `verify`: ONE tool, one `kind` at a time, structured params — never a
per-domain tool explosion (that was the 1.0 design we retired). Every answer is computed
deterministically from the SAME offline, public-domain data the verifiers already hold — no model,
no network, attributed to its source — so you can look a value up and then verify it through two
parallel doors over one body of data.

found=False is an honest miss (unknown kind, bad input, or the value is not in the data), never a
guess. New kinds are one function in _KINDS; the tool surface never grows.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

_SEE_ALSO = {"verify": "check a claimed value against this same data", "search": "find it in the keeping"}


def _result(kind: str, found: bool, value: Any, detail: str, source: str,
            extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    out: Dict[str, Any] = {"kind": kind, "found": bool(found), "value": value,
                           "detail": detail, "source": source, "see_also": _SEE_ALSO}
    if extra:
        out.update(extra)
    return out


def _molar_mass(params: Dict[str, Any]) -> Dict[str, Any]:
    from .verifiers import periodic_table as pt
    formula = str(params.get("formula") or "").strip()
    mass, comp = pt.molar_mass(formula)
    if mass is None:
        return _result("molar_mass", False, None, comp, "periodic_table")   # comp is the reason string
    return _result("molar_mass", True, mass,
                   f"{formula} = {mass} g/mol  (M = Σ count × atomic_mass)",
                   "periodic_table (IUPAC standard atomic weights)",
                   {"unit": "g/mol", "composition": comp})


def _element(params: Dict[str, Any]) -> Dict[str, Any]:
    from .verifiers import periodic_table as pt
    el = pt.element(symbol=params.get("symbol"), name=params.get("name"),
                    atomic_number=params.get("atomic_number"))
    if not el:
        return _result("element", False, None,
                       "no element matched symbol / name / atomic_number", "periodic_table")
    return _result("element", True, el,
                   f"{el.get('name')} ({el.get('symbol')}), Z={el.get('atomic_number')}, "
                   f"{el.get('atomic_mass')} u", "periodic_table (IUPAC)")


def _convert(params: Dict[str, Any]) -> Dict[str, Any]:
    from . import compute
    try:
        val = float(params.get("value"))
    except (TypeError, ValueError):
        return _result("convert", False, None, "value must be numeric", "compute")
    frm = str(params.get("from") or params.get("from_unit") or "").strip()
    to = str(params.get("to") or params.get("to_unit") or "").strip()
    if not frm or not to:
        return _result("convert", False, None, "from and to units required", "compute")
    s = compute.answer(f"convert {val:g} {frm} to {to}")
    if not s:
        return _result("convert", False, None, f"cannot convert {frm!r} to {to!r}", "compute")
    return _result("convert", True, s, s, "compute (offline unit-factor table)")


# kind -> handler. One excellent tool for the "look it up" situation; a new kind is one line here,
# the agent-facing tool surface never grows (the consolidated lesson from `verify`).
def _principles(params: Dict[str, Any]) -> Dict[str, Any]:
    """The principles of those who repeatedly won, applied to a present situation: the Strategy
    Concordance patterns the situation names, each with its proof count (distinct figures x arenas x
    dated cases) and the figures' own public-domain words, attributed. found=False when no pattern
    is named (never a guess)."""
    from . import principles as pr
    situation = str(params.get("situation") or params.get("text") or "").strip()
    if not situation:
        return _result("principles", False, None, "situation (text) required", "principles")
    r = pr.apply(situation, limit=int(params.get("limit") or 3), per_pattern=int(params.get("per_pattern") or 4))
    return _result("principles", r["found"], r["patterns"], r["detail"],
                   "principles (public-domain works, verbatim) + the Strategy Concordance", {"note": r.get("note")})


_KINDS = {"molar_mass": _molar_mass, "element": _element, "convert": _convert, "principles": _principles}


def kinds() -> list:
    return sorted(_KINDS)


def lookup(kind: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return a found value from the engine's offline data. `kind` is one of lookup.kinds(); `params`
    are that kind's structured inputs. Deterministic, model-free, attributed. found=False (never a
    guess) for an unknown kind or a value absent from the data."""
    k = str(kind or "").strip().lower()
    fn = _KINDS.get(k)
    if fn is None:
        return {"kind": k, "found": False, "value": None,
                "detail": f"unknown lookup kind {k!r}", "kinds": kinds(), "see_also": _SEE_ALSO}
    return fn(params or {})
