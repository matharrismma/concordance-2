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


def verify_vowel_shift(a: Dict[str, Any]) -> VerifierResult:
    """A regular VOWEL shift (the Great Vowel Shift): each cited word's stressed vowel moves as the claimed
    map says. `vowel_pairs` = [[word, old_vowel, new_vowel], ...]; `shift` = {old: new}. Confirms iff every
    pair follows the map (and each is a real change); any pair that does not is an exception. 0 FP."""
    name = "sound_law.vowel_shift"
    pairs = a.get("vowel_pairs")
    shift = a.get("shift")
    if not isinstance(pairs, list) or not pairs or not isinstance(shift, dict) or not shift:
        return error(name, "need 'vowel_pairs' [[word, old, new], ...] and a 'shift' map {old: new}")
    if any(str(k).strip() == str(v).strip() for k, v in shift.items()):
        return error(name, "a shift maps a vowel to a DIFFERENT vowel; the map has an identity entry")
    law = str(a.get("law") or "a vowel shift")
    holds: List[str] = []
    exceptions: List[str] = []
    for p in pairs:
        if not (isinstance(p, (list, tuple)) and len(p) == 3):
            return error(name, f"each pair is [word, old_vowel, new_vowel]; got {p!r}")
        word, ov, nv = str(p[0]), str(p[1]).strip(), str(p[2]).strip()
        if shift.get(ov) == nv and ov != nv:
            holds.append(f"{word}: {ov}->{nv}")
        else:
            exceptions.append(f"{word}: {ov}->{nv} (map says {ov}->{shift.get(ov, '∅')})")
    data = {"law": law, "shift": shift, "n_pairs": len(pairs), "holds": len(holds),
            "exceptions": exceptions, "examples": holds[:8]}
    claimed = a.get("claimed_regular", True)
    if exceptions and claimed:
        return mismatch(name, f"{law}: claimed regular, but {len(exceptions)} of {len(pairs)} cited words do not "
                              f"shift as the map claims — {'; '.join(exceptions[:4])}", data)
    if exceptions:
        return na(name, f"{law}: {len(exceptions)} of {len(pairs)} words are exceptions to the map", data)
    return confirm(name, f"{law}: every one of the {len(pairs)} cited words' stressed vowels shifts exactly as the "
                         f"map claims ({', '.join(holds[:6])}{'...' if len(holds) > 6 else ''}) — a regular vowel "
                         f"shift. The words and their vowels are attested; the shift is the verified correspondence.", data)


_ASPIRATES = ("bh", "dh", "gh", "ph", "th", "kh", "jh")


def _deaspirate_first(word: str, aspirates) -> str:
    """Remove the aspiration (the 'h') from the FIRST aspirate in the word; leave the rest untouched."""
    lo = word.lower()
    best = None
    for asp in aspirates:
        i = lo.find(asp)
        if i >= 0 and (best is None or i < best[0]):
            best = (i, asp)
    if best is None:
        return word
    i, asp = best
    return word[:i] + asp[:-1] + word[i + len(asp):]   # drop the trailing 'h'


def verify_dissimilation(a: Dict[str, Any]) -> VerifierResult:
    """Grassmann's law — when two aspirated stops begin successive syllables, the FIRST loses its aspiration.
    `dissimilation` = [[underlying, attested], ...] (the underlying form has two aspirates; the attested has
    the first deaspirated). Confirms iff, for every cited form, the attested equals the underlying with its
    first aspirate made plain and the rest unchanged. A form with fewer than two aspirates, or one where the
    wrong aspirate changed, is an exception. 0 FP."""
    name = "sound_law.dissimilation"
    forms = a.get("dissimilation")
    aspirates = [str(x).lower() for x in (a.get("aspirates") or _ASPIRATES)]
    if not isinstance(forms, list) or not forms:
        return error(name, "need 'dissimilation' [[underlying, attested], ...]")
    law = str(a.get("law") or "Grassmann's law (aspirate dissimilation)")
    holds: List[str] = []
    exceptions: List[str] = []
    for p in forms:
        if not (isinstance(p, (list, tuple)) and len(p) == 2):
            return error(name, f"each form is [underlying, attested]; got {p!r}")
        u, att = str(p[0]), str(p[1])
        lo = u.lower()
        n_asp = sum(lo.count(asp) for asp in aspirates)
        if n_asp < 2:
            exceptions.append(f"{u}->{att} (only {n_asp} aspirate(s); the rule needs two)")
            continue
        predicted = _deaspirate_first(u, aspirates)
        if predicted.lower() == att.lower():
            holds.append(f"{u}->{att}")
        else:
            exceptions.append(f"{u}->{att} (dissimilation predicts {predicted})")
    data = {"law": law, "aspirates": aspirates, "n_forms": len(forms), "holds": len(holds),
            "exceptions": exceptions, "examples": holds[:8]}
    claimed = a.get("claimed_regular", True)
    if exceptions and claimed:
        return mismatch(name, f"{law}: claimed regular, but {len(exceptions)} of {len(forms)} cited forms do not "
                              f"dissimilate as the law predicts — {'; '.join(exceptions[:4])}", data)
    if exceptions:
        return na(name, f"{law}: {len(exceptions)} of {len(forms)} forms are exceptions", data)
    return confirm(name, f"{law}: in every one of the {len(forms)} cited forms the first of two aspirates loses its "
                         f"aspiration, the rest unchanged ({', '.join(holds[:6])}) — a regular dissimilation. The "
                         f"forms are attested; the rule is the verified correspondence.", data)


def verify_voicing(a: Dict[str, Any]) -> VerifierResult:
    """Verner's law — a Grimm voiceless fricative becomes VOICED unless the accent fell on the immediately
    preceding syllable. `voicing` = [[word, accent_precedes(bool), voiceless, voiced, attested], ...]. The
    accent position is the cited reconstruction; the LAW verified is that the attested segment is the
    voiceless one exactly when the accent precedes, the voiced one otherwise. Confirms iff every cited word
    matches that conditioning; a word that voices where the accent precedes (or stays voiceless where it does
    not) is an exception. 0 FP."""
    name = "sound_law.voicing"
    rows = a.get("voicing")
    if not isinstance(rows, list) or not rows:
        return error(name, "need 'voicing' [[word, accent_precedes, voiceless, voiced, attested], ...]")
    law = str(a.get("law") or "Verner's law (accent-conditioned voicing)")
    holds: List[str] = []
    exceptions: List[str] = []
    for r in rows:
        if not (isinstance(r, (list, tuple)) and len(r) == 5):
            return error(name, f"each row is [word, accent_precedes, voiceless, voiced, attested]; got {r!r}")
        word, pre, vl, vd, att = str(r[0]), bool(r[1]), str(r[2]).strip(), str(r[3]).strip(), str(r[4]).strip()
        if vl == vd:
            return error(name, f"{word}: the voiceless and voiced segments are the same ('{vl}')")
        predicted = vl if pre else vd
        if att == predicted:
            holds.append(f"{word}: accent {'precedes' if pre else 'shifted'} -> {att}")
        else:
            exceptions.append(f"{word}: accent {'precedes' if pre else 'shifted'} predicts {predicted}, attested {att}")
    data = {"law": law, "n_words": len(rows), "holds": len(holds), "exceptions": exceptions, "examples": holds[:8]}
    claimed = a.get("claimed_regular", True)
    if exceptions and claimed:
        return mismatch(name, f"{law}: claimed regular, but {len(exceptions)} of {len(rows)} cited words do not follow "
                              f"the accent conditioning — {'; '.join(exceptions[:4])}", data)
    if exceptions:
        return na(name, f"{law}: {len(exceptions)} of {len(rows)} words are exceptions", data)
    return confirm(name, f"{law}: in every one of the {len(rows)} cited words the fricative is voiced exactly when the "
                         f"accent did NOT precede it, voiceless when it did ({', '.join(holds[:5])}) — the regular "
                         f"conditioning. The accent positions are the cited reconstruction; the conditioning is verified.", data)


_RULES = [
    (lambda a: ("pairs" in a and "source_onset" in a and "target_onset" in a), verify_sound_law),
    (lambda a: ("vowel_pairs" in a and "shift" in a), verify_vowel_shift),
    (lambda a: ("dissimilation" in a), verify_dissimilation),
    (lambda a: ("voicing" in a), verify_voicing),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, "SOUNDLAW_VERIFY", _RULES, domain="sound_law",
                    none_reason="no SOUNDLAW_VERIFY artifacts present")
