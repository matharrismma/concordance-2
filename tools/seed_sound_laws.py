#!/usr/bin/env python3
"""Three more sound laws, verified and sealed: the Great Vowel Shift, Grassmann's law, Verner's law.

Matt, 2026-10-11: "cognate confluences + sealed sound-laws (Verner's, Grassmann's, the Great Vowel
Shift)." Grimm's law is already a sealed stick (tools/tick.py grimm_law); these three are the other
famous regular correspondences of Indo-European historical linguistics. Each is CHECKABLE and sealed
through the extended sound_law verifier (src/concordance/verifiers/sound_law.py), 0 false positives:

  - the GREAT VOWEL SHIFT  - English long vowels raised/diphthongized regularly (vowel_shift check)
  - GRASSMANN'S LAW        - the first of two aspirates dissimilates (dissimilation check)
  - VERNER'S LAW           - Grimm's fricatives voice unless the accent preceded (voicing check)

What is sealed: the correspondence holds on every cited datum. What is cited (a postulate, never
sealed): the reconstructed inputs - the Middle English vowel values, the two-aspirate underlying
forms, the Proto-Indo-European accent positions - inferred from the comparative record. The engine
seals only what it checked. Each stick is placed on card_floor_indo_european (it inherits the IE
floor's Babel root). Seals use index=False (a light cold mint; searchable on the next reload).

    PYTHONPATH=src python tools/seed_sound_laws.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))

IE_FLOOR = "card_floor_indo_european"


def _seal(packet: dict):
    """Verify the packet through sound_law and attach a light seal; return the 64-hex content hash or None."""
    from concordance import receipts
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    res = verify_derivation([{"id": "law", "domain": "sound_law", "spec": {"SOUNDLAW_VERIFY": packet}}])
    if res.get("verdict") != "HOLDS":
        print("  !! did not hold:", packet.get("law"), res.get("verdict"))
        return None
    res = receipts.attach(res, config=EngineConfig(), domain="sound_law", index=False)
    return (res.get("seal") or {}).get("content_hash")


def _stick(question, statement, marks, by):
    from concordance import roots, tickstick as TS
    import tick
    sid = TS.create(question, statement, "linguistics")["id"]
    tick._mint_marks(sid, marks, by=by)
    roots.place("stick:" + sid, IE_FLOOR, by="proposed",
                why="a sound law on the Indo-European floor (inherits the Babel root)", data_dir=DATA)
    print(f"  minted {sid} + placed on {IE_FLOOR}")
    return sid


def great_vowel_shift() -> int:
    shift = {"iː": "aɪ", "eː": "iː", "aː": "eɪ", "oː": "uː", "uː": "aʊ"}
    pairs = [["bite", "iː", "aɪ"], ["meet", "eː", "iː"], ["name", "aː", "eɪ"],
             ["boot", "oː", "uː"], ["mouse", "uː", "aʊ"], ["geese", "eː", "iː"]]
    seal = _seal({"law": "the Great Vowel Shift", "shift": shift, "vowel_pairs": pairs, "claimed_regular": True})
    if not seal:
        return 1
    marks = [
        ("instance",
         "[the Great Vowel Shift, verified] Between c. 1400 and 1700 the Middle English long vowels raised and the "
         "highest diphthongized, regularly across the vocabulary: bite iː→aɪ, meet eː→iː, "
         "name aː→eɪ, boot oː→uː, mouse uː→aʊ - every cited word's stressed "
         "vowel shifts exactly as the map claims (sealed through sound_law). A chain shift, not word-by-word change; "
         "it is why English spelling and pronunciation parted ways.", seal),
        ("postulate",
         "[cited, not proven] The Middle English vowel VALUES are reconstructed from spelling, rhyme, loanwords and the "
         "orthoepists - a postulate; the shift is verified on them. The engine seals only the correspondence.",
         {"source": "O. Jespersen, A Modern English Grammar (1909); the standard histories of English; the comparative method"}),
        ("note",
         "[on the one map] The counterpart of Grimm's law for VOWELS, on the Germanic branch (English) of "
         "card_floor_indo_european. A sound law is math on the vocabulary - exactly checkable, sealable, refutable.",
         {"source": "src/concordance/verifiers/sound_law.py vowel_shift; card_floor_indo_european"}),
    ]
    _stick("The Great Vowel Shift - a regular vowel correspondence, verified",
           "English long vowels raised and diphthongized regularly (c. 1400-1700).", marks,
           by="tools/seed_sound_laws.py great_vowel_shift")
    return 0


def grassmann() -> int:
    asp = ["th", "ph", "kh", "bh", "dh", "gh"]
    forms = [["thithemi", "tithemi"], ["phepheuga", "pepheuga"], ["bhabhuva", "babhuva"]]
    seal = _seal({"law": "Grassmann's law", "aspirates": asp, "dissimilation": forms, "claimed_regular": True})
    if not seal:
        return 1
    marks = [
        ("instance",
         "[Grassmann's law, verified] In Greek and Sanskrit, when two aspirated stops began successive syllables the "
         "FIRST lost its aspiration: *thi-the-mi → titheemi ('I place'), *phe-pheug-a → pepheuga ('have fled'), "
         "Sanskrit *bha-bhuuva → babhuuva ('has become') - the first of two aspirates is made plain, the rest "
         "unchanged, on every cited form (sealed through sound_law). A regular dissimilation.", seal),
        ("postulate",
         "[cited, not proven] The two-aspirate UNDERLYING forms are reconstructed (the reduplication, the root shape) - "
         "a postulate; the dissimilation is verified on them.",
         {"source": "H. Grassmann, 'Ueber die aspiraten...' (1863); the comparative method"}),
        ("note",
         "[why it matters] Grassmann's law is why Grimm's law appeared to have exceptions in Greek - the two regular "
         "laws interact. An apparent exception that a deeper regularity explained, not a fudge.",
         {"source": "src/concordance/verifiers/sound_law.py dissimilation; card_floor_indo_european (Hellenic, Indo-Iranian)"}),
    ]
    _stick("Grassmann's law - aspirate dissimilation, verified",
           "The first of two successive aspirates loses its aspiration (Greek, Sanskrit).", marks,
           by="tools/seed_sound_laws.py grassmann")
    return 0


def verner() -> int:
    rows = [
        ["brother (*bhraater-, accent on the root)", True, "þ", "ð", "þ"],
        ["father (*ph2teer-, accent on the suffix)", False, "þ", "ð", "ð"],
        ["was (*wes-, accent on the root)", True, "s", "z", "s"],
        ["were (*wes-, accent shifted off the root)", False, "s", "z", "z"],
    ]
    seal = _seal({"law": "Verner's law", "voicing": rows, "claimed_regular": True})
    if not seal:
        return 1
    marks = [
        ("instance",
         "[Verner's law, verified] A voiceless fricative from Grimm's law became VOICED unless the Proto-Indo-European "
         "accent fell on the immediately preceding syllable: *bhráater → brother (þ, accent on the root) but "
         "*ph2téer → father (ð, accent on the suffix); *wés- → was (s) but *wes- with the accent "
         "shifted → were (z, later r) - voiced exactly when the accent did NOT precede, on every cited word (sealed "
         "through sound_law). This is the Germanic Grammatischer Wechsel.", seal),
        ("postulate",
         "[cited, not proven] The Proto-Indo-European ACCENT positions are reconstructed (chiefly from Vedic Sanskrit "
         "and Greek accent) - a postulate; the conditioning is verified on them.",
         {"source": "K. Verner, 'Eine Ausnahme der ersten Lautverschiebung' (1877); the comparative method"}),
        ("note",
         "[the famous residue] Verner's law is the residue of Grimm's law - the apparent exceptions a deeper regularity "
         "(the accent) explained. The exception became a want, then a law; the method narrows, it does not fudge. "
         "[[feedback_let_the_math_determine_truth_2026-10-06]]",
         {"source": "src/concordance/verifiers/sound_law.py voicing; card_floor_indo_european (Germanic branch)"}),
    ]
    _stick("Verner's law - accent-conditioned voicing, verified",
           "Grimm's fricatives voice unless the PIE accent preceded (the Germanic Grammatischer Wechsel).", marks,
           by="tools/seed_sound_laws.py verner")
    return 0


def main() -> int:
    rc = 0
    rc |= great_vowel_shift()
    rc |= grassmann()
    rc |= verner()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
