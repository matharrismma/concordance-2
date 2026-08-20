"""Context — the middle process of the loop: strip → hold locally → reattach.

Matt's build plan ("Closing the Context Loop"): content (verify) and the gate run; the CONTEXT process
never closed. This module lays its FLOOR — Step 1, the no-op round-trip — and nothing is built on top
until this holds.

    The context process is fundamentally strip → (hold) → reattach. If strip and reattach are not exact
    inverses, no amount of smart context-classification will ever close the loop.

So before any discernment, prove reversibility in isolation. `strip` removes nothing semantic — it only
assigns every span a stable HANDLE. `reattach` restores every handle by pure lookup. The invariant is
byte-identical round-trip on arbitrary messy text:

    reattach(*strip(text)) == text        # exactly, forever (see tests/test_context.py)

Why a handle SUBSTRATE and not just the PII redactor: `redact` reattaches only the few classes it
strips (email/SSN/card/IP/URL); it passes everything else through. That is enough for privacy but it is
NOT the reversibility floor — it never proves that the strip/reattach MACHINERY can reproduce the input
from handles alone. This module proves exactly that, on every span, so the later increments can trust it.

Design that makes the floor unbreakable:
  * The segmentation TILES the text — every character belongs to exactly one span (a run of non-space
    or a run of space), so the spans concatenate back to the input with no gaps and no overlaps.
  * The skeleton is a LIST of handles, never a string with handles embedded — so a hold value that
    happens to look like a handle can never be mis-parsed on reattach (the redactor's one theoretical
    hazard is absent here by construction).
  * Handles are STABLE: the same span value always gets the same handle, so structure and repetition
    survive the strip (what Step 2's discriminator will read).

The reattach is pure lookup — never reconstruction. If a round-trip ever fails, the bug is in the
handle/mapping substrate here, not in any discernment above it. That is the whole point of laying the
floor first.

Step 2 (not built here) adds a discriminator that PROJECTS this handle sequence into the skeleton that
travels to the verifier — truth-bearing spans kept, private spans typed-placeheld, noise dropped — while
this same (skeleton, holds) still reattaches the local result exactly. The floor does not change; the
projection is layered on top and each increment must keep this round-trip green.

Stdlib only, fully offline. The holds stay with the user; nothing here reaches a network.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

# A span is a maximal run of non-space OR a maximal run of space. Every character is one or the other
# (\S and \s are complementary), so the spans TILE the text: "".join(spans) == text, always — including
# newlines, CRLF, tabs, unicode, and empty input.
_SPAN_RE = re.compile(r"\S+|\s+")

# Handle brackets chosen to be visually distinct and rare; but note reattach never parses these out of a
# string (the skeleton is a list), so even a hold value containing "⟦0⟧" is safe.
_OPEN, _CLOSE = "⟦", "⟧"  # ⟦ ⟧


def strip(text: str) -> Tuple[List[str], Dict[str, str]]:
    """The no-op identity strip (the context floor): assign every span a stable handle, remove nothing.

    Returns (skeleton, holds):
      * skeleton — the ordered list of handles that reattaches to EXACTLY the input by pure lookup.
      * holds    — {handle: original span}. The user's side keeps this; it never travels.

    Same span value → same handle (stable), so repetition and structure are preserved. Raises TypeError
    on non-str input rather than guessing — the floor defends its own contract.
    """
    if not isinstance(text, str):
        raise TypeError("context.strip expects str, got %s" % type(text).__name__)
    holds: Dict[str, str] = {}
    value_to_handle: Dict[str, str] = {}
    skeleton: List[str] = []
    for span in _SPAN_RE.findall(text):
        handle = value_to_handle.get(span)
        if handle is None:
            handle = f"{_OPEN}{len(value_to_handle)}{_CLOSE}"
            value_to_handle[span] = handle
            holds[handle] = span
        skeleton.append(handle)
    return skeleton, holds


def reattach(skeleton: List[str], holds: Dict[str, str]) -> str:
    """Restore every handle by pure lookup — the exact inverse of strip. `reattach(*strip(t)) == t`.

    Pure lookup, never reconstruction: a missing handle is a substrate bug and must fail loudly, not be
    papered over — so a handle absent from `holds` raises KeyError rather than silently vanishing.
    """
    return "".join(holds[h] for h in skeleton)


def round_trips(text: str) -> bool:
    """True iff the no-op strip→reattach reproduces `text` byte-for-byte. The floor's self-check."""
    skeleton, holds = strip(text)
    return reattach(skeleton, holds) == text


def spans(text: str) -> List[str]:
    """The tiling segmentation itself — exposed so callers (and Step 2's discriminator) can see the
    exact spans the handles stand for. `"".join(spans(text)) == text` for any text."""
    if not isinstance(text, str):
        raise TypeError("context.spans expects str, got %s" % type(text).__name__)
    return _SPAN_RE.findall(text)


# ── Step 2 — the discriminator: keep only what is NECESSARY to check the claim ──────────────────────
# Matt's rule (2026-08-19): "we would need only the thing that is necessary." The verifier gets the bare
# checkable claim plus any condition that BEARS ON ITS TRUTH — "water boils at 100C", and "in Dayton" if
# the claim ties the boiling point to Dayton — and nothing else: who said it, whose mother, the greeting
# are all irrelevant to whether water boils at 100C, so they stay home. Necessity is judged by the
# verdict: a span travels iff dropping it could change the check. Framing never can; a condition can.
#
# The plan builds this ONE KIND AT A TIME, proving closure after each. Increment 1 (here) is the
# highest-confidence, unambiguous drop — ATTRIBUTION FRAMING: "my mom said …", "she told me …",
# "according to Dr X, …". Strip the leading frame, keep the claim (INCLUDING any location or number
# inside it). Conservative by construction: it removes only a leading frame it matches with high
# confidence and keeps EVERYTHING else, so a truth-bearing condition is never dropped — the safe error
# direction for a verifier. More kinds (politeness, then finer classes) accrete here, each proven to
# keep the round-trip green. The discriminator PROPOSES; the round-trip test and the verifier confirm.
#
# This is a projection over the Step-1 FLOOR, not a second reattach path: every span still lands in
# `holds`, so reattach() reproduces the input exactly; the discriminator only decides, per span, whether
# it travels (keep), travels as a typed placeholder (private/PII), or is held home (local).

_PERSON = (r"(?:my|her|his|their|our|the|a)?\s*(?:mom|mother|dad|father|parents?|friends?|neighbou?rs?|"
           r"doctors?|dr\.?|pastors?|teachers?|professors?|wife|husband|spouse|sons?|daughters?|"
           r"sisters?|brothers?|aunts?|uncles?|cousins?|boss(?:es)?|colleagues?|co-?workers?|kids?|"
           r"child(?:ren)?|grand(?:ma|mother|pa|father)|nurses?|coach(?:es)?|guy|lady|woman|man|"
           r"people|someone|somebody)")
_PRONOUN = r"(?:he|she|they|i)"
_SPEECH = (r"(?:said|says|say|told\s+me|tells\s+me|telling\s+me|asked|asks|wondered|wonders|claimed|"
           r"claims|claim|thinks?|thought|believes?|believed|figured|wrote|writes|mentioned|mentions|"
           r"noted|notes|reported|reports|insists?|insisted|heard|read|reckons?|reckoned)")
# A LEADING attribution frame only: subject (a person reference or a pronoun) + a speech verb + optional
# "that", or "according to X,". High-confidence and bounded — a claim's own conditions can't match it.
_ATTR = re.compile(
    r"^\s*(?:according\s+to\s+[^,]{1,40},\s*"
    r"|(?:%s|%s)\s+%s\s+(?:that\s+)?)" % (_PERSON, _PRONOUN, _SPEECH),
    re.IGNORECASE)


def _framing_end(text: str) -> int:
    """End offset of a leading attribution frame ('my mom said (that) ', 'according to X, '), else 0.
    Only a leading, high-confidence frame — conservative, so a claim's own conditions are never taken
    for framing."""
    m = _ATTR.match(text or "")
    return m.end() if m else 0


@dataclass(frozen=True)
class Stripped:
    """One strip of a claim over the unified substrate. `holds` stays LOCAL (it reattaches the input
    exactly); `travels()` is the skeleton that may go to the verifier — only the necessary spans."""
    text: str
    handles: Tuple[str, ...]        # local skeleton: one handle per span, in order
    roles: Tuple[str, ...]          # per-span: "keep" (travels) | "private" (travels placeheld) | "local" (home)
    holds: Dict[str, str]           # handle -> original span value (LOCAL — reattaches to text exactly)
    labels: Dict[str, str]          # handle -> typed placeholder, PRIVATE spans only

    def reattach(self) -> str:
        """The local result: restore every handle by pure lookup — exactly the input (the floor)."""
        return "".join(self.holds[h] for h in self.handles)

    def travels(self) -> str:
        """The skeleton that may reach the verifier: necessary spans travel literally, PII as typed
        placeholders, and framing/local context is held home (omitted). With no discriminator active
        (minimal=False) every span is necessary, so this equals redact()'s clean text by construction."""
        parts: List[str] = []
        for handle, role in zip(self.handles, self.roles):
            if role == "keep":
                parts.append(self.holds[handle])
            elif role == "private":
                parts.append(self.labels[handle])
            # role == "local" -> held home, does not travel
        return "".join(parts)

    @property
    def pii_map(self) -> Dict[str, str]:
        """{placeholder: original value} — held LOCAL, for reattaching a verdict later (Step 3)."""
        return {ph: self.holds[h] for h, ph in self.labels.items()}

    def framing(self) -> str:
        """The local context held home (attribution etc.) — what did NOT travel, kept on the user's
        machine and woven back into the response. Empty when nothing was held local."""
        return "".join(self.holds[h] for h, role in zip(self.handles, self.roles) if role == "local")

    def reveal(self, verdict: str) -> str:
        """Reattach a verdict (or any returned text) by putting the private values back — pure lookup,
        via the one restore path (redact.restore). Never reconstruction."""
        from . import redact
        return redact.restore(verdict, self.pii_map)


def decontextualize(text: str, *, minimal: bool = False) -> Stripped:
    """Strip a claim over the floor substrate. Always: PII -> typed placeholders (Step 2a). With
    minimal=True: also hold ATTRIBUTION FRAMING home so only what is necessary to check travels
    (Step 2b). The returned Stripped reattaches the input exactly AND yields a de-identified,
    necessity-only skeleton."""
    if not isinstance(text, str):
        raise TypeError("context.decontextualize expects str, got %s" % type(text).__name__)
    from . import redact
    private = redact.pii_spans(text)                       # (start, end, label, value), ascending
    frame_end = _framing_end(text) if minimal else 0

    # Tile the WHOLE text into typed spans: public whitespace-runs + private PII atoms, each with its
    # start offset. Concatenation of the values is the input, so reattach stays exact.
    typed: List[Tuple[str, int, str, "str | None"]] = []   # (value, start, kind, label|None)
    cursor = 0
    for start, end, label, value in private:
        for m in _SPAN_RE.finditer(text[cursor:start]):
            typed.append((m.group(0), cursor + m.start(), "public", None))
        typed.append((value, start, "private", label))
        cursor = end
    for m in _SPAN_RE.finditer(text[cursor:]):
        typed.append((m.group(0), cursor + m.start(), "public", None))

    handles: List[str] = []
    roles: List[str] = []
    holds: Dict[str, str] = {}
    labels: Dict[str, str] = {}
    value_to_handle: Dict[Tuple[str, str, "str | None"], str] = {}
    label_value_to_token: Dict[Tuple[str, str], str] = {}
    label_counters: Dict[str, int] = {}
    for value, start, kind, label in typed:
        key = (value, kind, label)
        handle = value_to_handle.get(key)
        if handle is None:
            handle = f"{_OPEN}{len(value_to_handle)}{_CLOSE}"
            value_to_handle[key] = handle
            holds[handle] = value
            if kind == "private":
                token = label_value_to_token.get((label, value))
                if token is None:                          # first-appearance numbering, matching redact()
                    label_counters[label] = label_counters.get(label, 0) + 1
                    token = f"[{label}_{label_counters[label]}]"
                    label_value_to_token[(label, value)] = token
                labels[handle] = token
        handles.append(handle)
        if start < frame_end:
            roles.append("local")                          # inside the attribution frame — held home
        elif kind == "private":
            roles.append("private")                        # PII — travels only as a typed placeholder
        else:
            roles.append("keep")                           # necessary to the check — travels literally
    return Stripped(text=text, handles=tuple(handles), roles=tuple(roles), holds=holds, labels=labels)


def claim(text: str) -> str:
    """The necessity-only skeleton: attribution framing dropped, PII placeheld, the claim and its
    conditions kept. Convenience for decontextualize(text, minimal=True).travels()."""
    return decontextualize(text, minimal=True).travels()


def leaks(travels_text: str) -> bool:
    """True if any PII survives in what would travel — the leak check. A skeleton that leaks must never
    reach the verifier; the loop quarantines instead."""
    from . import redact
    return redact.has_pii(travels_text)


# ── Step 3 — application: close the triad (reception → integration → expression) ────────────────────
# The plan: "reattach the verdict to local context by handle… present with the boundary declared: what
# was checked, what was not, the seal for re-checking. Never present a verdict as broader than what the
# gate actually confirmed." Matt: "we would add it back in our response." run() is that circuit:
#   integration  — decontextualize(minimal): hold local framing + PII, produce the necessity-only skeleton
#   reception    — verify(skeleton): the content process checks ONLY the de-identified skeleton
#   expression   — reveal the verdict locally, weave the held context back, declare the boundary
# verify is injected (a fake in tests; the real gate/check as a follow-on) so the loop is provable with
# no engine. Fail-safe: a skeleton that would leak is QUARANTINED (never sent); a verifier that errors
# yields INCOMPLETE, never a false pass.

def _normalize_verdict(raw: "object") -> Dict[str, "object"]:
    """Accept a verifier's return in a few honest shapes and normalize to {status, statement, seal}.
    A bare string has no declared status, so it is UNKNOWN — never silently a PASS."""
    if isinstance(raw, str):
        return {"status": "UNKNOWN", "statement": raw, "seal": None}
    if isinstance(raw, dict):
        status = raw.get("status") or raw.get("verdict") or "UNKNOWN"
        statement = raw.get("statement") or raw.get("text") or raw.get("answer") or ""
        seal = raw.get("seal") or raw.get("cite_url") or raw.get("content_hash")
        return {"status": str(status), "statement": str(statement), "seal": seal}
    return {"status": "UNKNOWN", "statement": str(raw), "seal": None}


def _compose(revealed: str, checked: str, framing: str, verdict: Dict[str, "object"]) -> str:
    """Deterministic assembly (NOT generation): the verifier's own statement (PII revealed locally),
    then the boundary — what was checked, what stayed home, the status, and the re-check seal."""
    lines = [revealed.strip() or "(no statement returned)"]
    boundary = "— checked: %r" % checked
    if framing.strip():
        boundary += "  · kept on your machine (not sent): %r" % framing.strip()
    lines.append(boundary)
    tail = "[%s]" % verdict["status"]
    if verdict.get("seal"):
        tail += "  re-check: %s" % verdict["seal"]
    lines.append(tail)
    return "\n".join(lines)


def run(text: str, verify: "callable", *, minimal: bool = True) -> Dict[str, "object"]:
    """Close the context loop on one real input. `verify` is a callable skeleton:str -> (str | dict)
    that checks ONLY the de-identified, necessity-only skeleton. Returns the structured result and a
    ready-to-show `response` with the boundary declared. Private context never leaves this function."""
    if not isinstance(text, str):
        raise TypeError("context.run expects str, got %s" % type(text).__name__)
    if not callable(verify):
        raise TypeError("context.run needs a verify callable")

    s = decontextualize(text, minimal=minimal)          # integration: hold local, de-identify
    skeleton = s.travels()

    if leaks(skeleton):                                  # fail-safe: never send private context
        return {"ok": False, "status": "QUARANTINE", "checked": None,
                "held_local": {"framing": s.framing(), "pii": list(s.pii_map.values())},
                "verdict": None,
                "response": "Held back: the claim could not be de-identified safely, so nothing was sent.",
                "boundary": {"checked": None, "not_checked": s.reattach(), "reason": "would leak PII"}}

    try:                                                 # reception: the content process checks the skeleton
        raw = verify(skeleton)
    except Exception as e:  # noqa: BLE001 — a verifier error is INCOMPLETE, never a false pass
        return {"ok": False, "status": "INCOMPLETE", "checked": skeleton,
                "held_local": {"framing": s.framing(), "pii": list(s.pii_map.values())},
                "verdict": None,
                "response": "Could not complete the check (%s). Nothing is confirmed." % type(e).__name__,
                "boundary": {"checked": skeleton, "error": type(e).__name__}}

    v = _normalize_verdict(raw)
    revealed = s.reveal(str(v["statement"]))            # expression: put the user's PII back, locally
    framing = s.framing()
    return {
        "ok": True, "status": v["status"], "checked": skeleton,
        "held_local": {"framing": framing, "pii": list(s.pii_map.values())},
        "verdict": v,
        "response": _compose(revealed, skeleton, framing, v),
        "boundary": {"checked": skeleton, "not_checked": (framing.strip() or None),
                     "pii_masked": len(s.pii_map), "seal": v.get("seal")},
    }


__all__ = ["strip", "reattach", "round_trips", "spans",
           "Stripped", "decontextualize", "claim", "leaks", "run"]
