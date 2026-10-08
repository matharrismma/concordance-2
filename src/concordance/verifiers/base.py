"""Verifier framework — the deterministic computational checks.

A verifier is a PURE function: it takes a spec and returns a VerifierResult.
No I/O, no LLM, no network. It either confirms the artifact's math/logic,
finds a mismatch, errors on malformed input, or declares itself not-applicable.

    CONFIRMED      — the artifact ran and agreed with the claim
    MISMATCH       — the artifact ran and contradicted the claim
    NOT_APPLICABLE — the relevant artifact was absent (verifier could not run)
    ERROR          — the artifact was present but malformed

Ported as-is from 1.0 — domain-neutral.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Literal, Optional, Sequence, Tuple, Union

VerifierStatus = Literal["CONFIRMED", "MISMATCH", "NOT_APPLICABLE", "ERROR"]


@dataclass(frozen=True)
class VerifierResult:
    name: str
    status: VerifierStatus
    detail: str = ""
    data: Optional[Dict[str, Any]] = None

    @property
    def passed(self) -> bool:
        return self.status == "CONFIRMED"

    @property
    def failed(self) -> bool:
        return self.status in ("MISMATCH", "ERROR")

    @property
    def applicable(self) -> bool:
        return self.status != "NOT_APPLICABLE"


def na(name: str, reason: str = "no artifact provided",
       data: Optional[Dict[str, Any]] = None) -> VerifierResult:
    return VerifierResult(name=name, status="NOT_APPLICABLE", detail=reason, data=data)


def confirm(name: str, detail: str = "", data: Optional[Dict[str, Any]] = None) -> VerifierResult:
    return VerifierResult(name=name, status="CONFIRMED", detail=detail, data=data)


def mismatch(name: str, detail: str, data: Optional[Dict[str, Any]] = None) -> VerifierResult:
    return VerifierResult(name=name, status="MISMATCH", detail=detail, data=data)


def error(name: str, detail: str, data: Optional[Dict[str, Any]] = None) -> VerifierResult:
    return VerifierResult(name=name, status="ERROR", detail=detail, data=data)


def clamp_tol(spec: Dict[str, Any], key: str, default: float) -> float:
    """Caller-supplied tolerance, clamped: a caller may TIGHTEN a tolerance but never LOOSEN
    it past the verifier's default — otherwise an adversarial caller could widen the window to
    force a CONFIRMED on a value that is actually wrong. Missing/malformed -> the default."""
    try:
        v = spec.get(key)
        if v is None:
            return default
        return min(abs(float(v)), abs(default))
    except (TypeError, ValueError):
        return default


_LITERAL = re.compile(r"[-+]?(\d*)(?:\.(\d*))?(?:[eE]([-+]?\d+))?")


_SCALE_WORDS = {"thousand": 1e3, "million": 1e6, "billion": 1e9, "trillion": 1e12,
                "k": 1e3, "m": 1e6, "mn": 1e6, "b": 1e9, "bn": 1e9}


def literal_scale(literal: Any) -> Tuple[str, float]:
    """The number AS WRITTEN and its scale: "$29.3 million" -> ("29.3", 1e6); "$5k" -> ("5", 1e3);
    "41,600" -> ("41,600", 1.0). The literal keeps its own digits so stated_precision reads the figures the
    person gave, and the scale word becomes a factor (the failure report's H5: "$29.3 million" was read as 29.3).
    A one-letter scale (k, M, B, bn) counts only when attached to a $-number ("$29.3M"); a spaced "m" is metres."""
    import re
    s = str(literal or "").strip()
    m = re.match(r"^\$?\s*(-?\d[\d,]*(?:\.\d+)?)\s*(thousand|million|billion|trillion)\b", s, re.I)
    if m:
        return m.group(1), _SCALE_WORDS[m.group(2).lower()]
    m = re.match(r"^\$\s*(-?\d[\d,]*(?:\.\d+)?)(k|m|mn|b|bn)\b", s, re.I)
    if m:
        return m.group(1), _SCALE_WORDS[m.group(2).lower()]
    m = re.match(r"^\$?\s*(-?\d[\d,]*(?:\.\d+)?)", s)
    return (m.group(1) if m else s), 1.0


def stated_precision(literal: Any) -> Optional[Tuple[int, float]]:
    """(significant figures, half a unit in the last stated place) of a number AS THE PERSON WROTE IT.

    "9.81" -> (3, 0.005)   "5730" -> (3, 5.0)   "3.0e8" -> (2, 5e6)   "3e8" -> (1, 5e7)   "0.0025" -> (2, 5e-5)
    A bare integer's trailing zeros are NOT counted significant ("300000000" is one figure) — the
    conservative reading, so a round number never claims more precision than it shows. None when the
    literal is not a number. Pure."""
    s = str(literal if literal is not None else "").strip().replace(",", "").replace(" ", "").replace("$", "")
    m = _LITERAL.fullmatch(s)
    if not m or not (m.group(1) or m.group(2)):
        return None
    ip, fp, ex = m.group(1) or "", m.group(2), int(m.group(3) or 0)
    if fp is not None:                       # a decimal point was written: every written decimal counts
        digits = (ip + fp).lstrip("0")
        return (len(digits) if digits else 1, 0.5 * 10.0 ** (ex - len(fp)))
    core = ip.lstrip("0")
    if not core:
        return (1, 0.5 * 10.0 ** ex)
    stripped = core.rstrip("0")
    trailing = len(core) - len(stripped)
    return (len(stripped), 0.5 * 10.0 ** (ex + trailing))


def stated_tolerance_abs(literal: Any, unit_factor: float = 1.0) -> Optional[float]:
    """The absolute tolerance a claim EARNS from its own stated precision — half a unit in its last stated
    place, scaled to the verifier's unit by `unit_factor` (a claim in km/s judged in m/s: 1000) — or None
    when it earns none: an unreadable literal, or a single significant figure, so "3e8" or "300000000"
    never passes as the exact value. The claim's own literal is the ONLY thing that can widen a window;
    a caller never hands in a tolerance (cf. clamp_tol, which only ever tightens). (2026-10-07: "earth
    gravity is 9.81 m/s^2" was refused by a flat 1e-4 — right to every figure stated, called false.)"""
    sp = stated_precision(literal)
    if sp is None or sp[0] < 2:
        return None
    try:
        f = abs(float(unit_factor)) or 1.0
    except (TypeError, ValueError):
        f = 1.0
    return sp[1] * f


# A rule is (requirement, verify_fn). requirement is EITHER a sequence of keys that must ALL
# be present in the artifact, OR a callable(artifact)->bool for irregular conditions (or/
# is-not-None/non-empty). verify_fn is callable(artifact)->VerifierResult.
Requirement = Union[Sequence[str], Callable[[Dict[str, Any]], bool]]
Rule = Tuple[Requirement, Callable[[Dict[str, Any]], "VerifierResult"]]


def dispatch(packet: Dict[str, Any], artifact_key: str, rules: Iterable[Rule], *,
             domain: str, none_reason: str = "") -> List["VerifierResult"]:
    """Declarative run() driver — read ONE artifact, fire each matching rule, and apply
    UNIFORM present-vs-null handling: an absent artifact OR no rule firing yields exactly one
    na(domain, ...). This is behaviour-identical to the hand-written pattern

        art = packet.get(KEY) or {}
        if <keys present>: results.append(fn(art))   # for each rule
        if not results: results.append(na(domain, ...))

    but declarative and consistent, so every verifier reports "nothing applicable" the same
    way and a new check is one line in a rules table. A requirement is a tuple of required
    keys (ALL must be present) or a callable(artifact)->bool for or/is-not-None conditions."""
    art = packet.get(artifact_key) or {}
    out: List["VerifierResult"] = []
    for req, fn in rules:
        fires = req(art) if callable(req) else all(k in art for k in req)
        if fires:
            out.append(fn(art))
    if not out:
        out.append(na(domain, none_reason or f"no {artifact_key} artifacts present"))
    return out
