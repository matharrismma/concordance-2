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


__all__ = ["strip", "reattach", "round_trips", "spans"]
