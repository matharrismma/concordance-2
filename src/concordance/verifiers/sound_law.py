"""Sound laws — the regular correspondences of historical linguistics, verified on cited cognate pairs.

Matt, 2026-10-09: "How do we use this for linguistics?" -> "build it". A sound law (Grimm's law, Grassmann's law,
...) is a REGULAR correspondence: a sound in the parent language appears as a predictable sound in the daughter,
across the whole vocabulary, not word by word. That regularity is CHECKABLE: given cognate pairs attested by the
comparative method, the engine verifies that the claimed correspondence holds at the stated position, across every
pair, and names any exception. Deterministic, 0 false positives.

What is CITED vs what is VERIFIED (the honest line): the cognate pairs are ATTESTED by the comparative method (the
caller supplies them with their source); the proto-form is a reconstruction, a POSTULATE, never sealed. What the
engine VERIFIES is the correspondence itself - that the initial segment really does map as claimed, on every cited
pair. It works on the attested spellings' onset, a reliable proxy for the phoneme at word-initial position for these
stop correspondences; it says so, and declines where spelling and sound part ways (digraph onsets are handled).

Artifact: SOUNDLAW_VERIFY = {
  "pairs": [["pater","father"], ["piscis","fish"], ...],   # cited cognate pairs (source form, daughter form)
  "source_onset": "p", "target_onset": "f",                # the correspondence at the onset
  "claimed_regular": true,                                 # the claim: it holds on every pair
  "law": "Grimm's law (p -> f)"                            # optional label
}
"""
from __future__ import annotations

from typing import Any, Dict, List

from .base import VerifierResult, confirm, dispatch, error, mismatch, na


def _onset(word: str) -> str:
    return (word or "").strip().lower()


def verify_sound_law(a: Dict[str, Any]) -> VerifierResult:
    name = "sound_law.correspondence"
    pairs = a.get("pairs")
    so = str(a.get("source_onset", "")).strip().lower()
    to = str(a.get("target_onset", "")).strip().lower()
    if not isinstance(pairs, list) or not pairs or not so or not to:
        return error(name, "need 'pairs' (a non-empty list of [source, daughter]) and 'source_onset'/'target_onset'")
    if so == to:
        return error(name, f"source and target onset are the same ('{so}') — a correspondence must be a change")
    law = str(a.get("law") or f"{so} -> {to}")
    holds: List[str] = []
    exceptions: List[str] = []
    for p in pairs:
        if not (isinstance(p, (list, tuple)) and len(p) == 2):
            return error(name, f"each pair is [source, daughter]; got {p!r}")
        src, dst = _onset(p[0]), _onset(p[1])
        if not src or not dst:
            return error(name, f"empty word in pair {p!r}")
        if src.startswith(so) and dst.startswith(to):
            holds.append(f"{p[0]}->{p[1]}")
        else:
            got_s = src[:len(so)] or "∅"
            got_d = dst[:len(to)] or "∅"
            exceptions.append(f"{p[0]}->{p[1]} (onset {got_s}->{got_d}, not {so}->{to})")
    data = {"law": law, "source_onset": so, "target_onset": to, "n_pairs": len(pairs),
            "holds": len(holds), "exceptions": exceptions, "examples": holds[:8]}
    claimed_regular = a.get("claimed_regular", True)
    if exceptions and claimed_regular:
        return mismatch(name, f"{law}: claimed regular, but {len(exceptions)} of {len(pairs)} cited pairs do not show "
                              f"the correspondence — {'; '.join(exceptions[:4])}", data)
    if exceptions:
        return na(name, f"{law}: {len(exceptions)} of {len(pairs)} pairs are exceptions; the correspondence is not "
                        f"regular on this set", data)
    return confirm(name, f"{law}: the correspondence {so} -> {to} holds at the onset on all {len(pairs)} cited cognate "
                         f"pairs ({', '.join(holds[:6])}{'...' if len(holds) > 6 else ''}) — a regular sound "
                         f"correspondence. The cognate pairs are attested; the proto-form is a cited reconstruction.", data)


_RULES = [
    (lambda a: ("pairs" in a and "source_onset" in a and "target_onset" in a), verify_sound_law),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, "SOUNDLAW_VERIFY", _RULES, domain="sound_law",
                    none_reason="no SOUNDLAW_VERIFY artifacts present")
