"""PHONICS + ETYMOLOGY (Matt, 2026-10-08: "Etymology and phonics"): sound from the pronunciation shelf (rhyme,
homophone, stress, silent letters, the long/short vowel names, first and last sounds) and origin from the
etymology shelf (Webster 1913). No corpus here: every check runs on a pronunciation / etymology given in the spec,
and the front door with no corpus DECLINES rather than judges. The Webster parser is pinned on a fixture."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="nh-phon-")
os.environ.setdefault("CONCORDANCE_DATA_DIR", TMP)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from concordance.audit import audit, extract  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.verifiers import wordcraft as W  # noqa: E402

CFG = EngineConfig("secular")


def _v(text: str) -> str:
    return audit(text, CFG, seal=False, index=False, card=False)["verdict"]


def _specs(text: str):
    out = []
    for s in extract(text):
        for v in s.values():
            if isinstance(v, dict) and "WORD_VERIFY" in v:
                out.append((s["extractor"], v["WORD_VERIFY"]))
    return out


# ── the pronunciation shelf, read whole ──────────────────────────────────────────────────────────────────────
def test_variants_tails_and_stress():
    body = "strength: pronounced (ARPABET) S T R EH1 NG K TH; also S T R EH1 NG TH. From the CMU Pronouncing Dictionary."
    assert W.arpabet_variants_from_body(body) == ["S T R EH1 NG K TH", "S T R EH1 NG TH"]
    assert W.arpabet_variants_from_body("level: pronounced (ARPABET) L EH1 V AH0 L. From the CMU") == ["L EH1 V AH0 L"]
    assert W.rhyme_tail("K AE1 T") == ["AE", "T"] and W.rhyme_tail("B AH0 N AE1 N AH0") == ["AE", "N", "AH"]
    assert W.stressed_syllable("B AH0 N AE1 N AH0") == 2 and W.stressed_syllable("F OW1 T AH0 G R AE2 F") == 1
    assert W.strip_stress("DH EH1 R") == ["DH", "EH", "R"]


def test_rhyme_and_homophone():
    r = W.verify_rhyme({"word_a": "cat", "word_b": "hat", "claimed_rhyme": True, "pronunciation_a": "K AE1 T", "pronunciation_b": "HH AE1 T"})
    assert r.status == "CONFIRMED"
    assert W.verify_rhyme({"word_a": "orange", "word_b": "door", "claimed_rhyme": True, "pronunciation_a": "AO1 R AH0 N JH", "pronunciation_b": "D AO1 R"}).status == "MISMATCH"
    assert W.verify_rhyme({"word_a": "cat", "word_b": "dog", "claimed_rhyme": False, "pronunciation_a": "K AE1 T", "pronunciation_b": "D AO1 G"}).status == "CONFIRMED"
    # a variant pronunciation counts: either/neither
    assert W.verify_rhyme({"word_a": "either", "word_b": "neither", "claimed_rhyme": True, "pronunciation_a": "IY1 DH ER0; AY1 DH ER0", "pronunciation_b": "N IY1 DH ER0; N AY1 DH ER0"}).status == "CONFIRMED"
    r = W.verify_rhyme({"word_a": "there", "word_b": "their", "claimed_rhyme": True, "pronunciation_a": "DH EH1 R", "pronunciation_b": "DH EH1 R"})
    assert r.status == "CONFIRMED" and "identical" in r.detail
    assert W.verify_homophone({"word_a": "there", "word_b": "their", "claimed_homophone": True, "pronunciation_a": "DH EH1 R", "pronunciation_b": "DH EH1 R"}).status == "CONFIRMED"
    assert W.verify_homophone({"word_a": "night", "word_b": "knight", "claimed_homophone": True, "pronunciation_a": "N AY1 T", "pronunciation_b": "N AY1 T"}).status == "CONFIRMED"
    assert W.verify_homophone({"word_a": "bear", "word_b": "beer", "claimed_homophone": True, "pronunciation_a": "B EH1 R", "pronunciation_b": "B IH1 R"}).status == "MISMATCH"
    # no corpus: a word with no pronunciation given is declined, never judged
    assert W.verify_rhyme({"word_a": "cat", "word_b": "hat", "claimed_rhyme": True}).status == "NOT_APPLICABLE"


def test_stress():
    assert W.verify_stress({"word": "banana", "claimed_stress_syllable": 2, "pronunciation": "B AH0 N AE1 N AH0"}).status == "CONFIRMED"
    assert W.verify_stress({"word": "banana", "claimed_stress_syllable": 1, "pronunciation": "B AH0 N AE1 N AH0"}).status == "MISMATCH"
    assert W.verify_stress({"word": "hotel", "claimed_stress_syllable": -1, "pronunciation": "HH OW0 T EH1 L"}).status == "CONFIRMED"     # last
    assert W.verify_stress({"word": "banana", "claimed_stress_syllable": -2, "pronunciation": "B AH0 N AE1 N AH0"}).status == "CONFIRMED"  # penultimate


def test_silent_letters_judge_only_what_the_convention_can_tell():
    S = W.verify_silent_letter
    assert S({"word": "knife", "letter": "k", "claimed_silent": True, "pronunciation": "N AY1 F"}).status == "CONFIRMED"
    assert S({"word": "kite", "letter": "k", "claimed_silent": True, "pronunciation": "K AY1 T"}).status == "MISMATCH"
    assert S({"word": "kite", "letter": "k", "claimed_silent": False, "pronunciation": "K AY1 T"}).status == "CONFIRMED"
    assert S({"word": "climb", "letter": "b", "claimed_silent": True, "pronunciation": "K L AY1 M"}).status == "CONFIRMED"
    assert S({"word": "castle", "letter": "t", "claimed_silent": True, "pronunciation": "K AE1 S AH0 L"}).status == "CONFIRMED"
    assert S({"word": "Wednesday", "letter": "d", "claimed_silent": True, "pronunciation": "W EH1 N Z D EY2"}).status == "CONFIRMED"   # two d's, one D
    assert S({"word": "bomb", "letter": "b", "claimed_silent": True, "pronunciation": "B AA1 M"}).status == "CONFIRMED"
    assert S({"word": "iron", "letter": "r", "claimed_silent": True, "pronunciation": "AY1 ER0 N"}).status == "MISMATCH"              # ER carries the r
    # the final e after a consonant
    assert S({"word": "cake", "letter": "e", "claimed_silent": True, "pronunciation": "K EY1 K"}).status == "CONFIRMED"
    assert S({"word": "recipe", "letter": "e", "claimed_silent": True, "pronunciation": "R EH1 S AH0 P IY0"}).status == "MISMATCH"
    # declined, never guessed: a digraph, a vowel letter inside the word, a vowel team, a shared sound, a word with no such letter
    assert S({"word": "ship", "letter": "h", "claimed_silent": True, "pronunciation": "SH IH1 P"}).status == "NOT_APPLICABLE"
    assert S({"word": "build", "letter": "u", "claimed_silent": True, "pronunciation": "B IH1 L D"}).status == "NOT_APPLICABLE"
    assert S({"word": "shoe", "letter": "e", "claimed_silent": True, "pronunciation": "SH UW1"}).status == "NOT_APPLICABLE"
    assert S({"word": "science", "letter": "c", "claimed_silent": True, "pronunciation": "S AY1 AH0 N S"}).status == "NOT_APPLICABLE"
    assert S({"word": "day", "letter": "y", "claimed_silent": True, "pronunciation": "D EY1"}).status == "NOT_APPLICABLE"
    assert S({"word": "cow", "letter": "w", "claimed_silent": True, "pronunciation": "K AW1"}).status == "NOT_APPLICABLE"
    assert S({"word": "cat", "letter": "k", "claimed_silent": True, "pronunciation": "K AE1 T"}).status == "NOT_APPLICABLE"
    # a variant that sounds the letter satisfies a 'sounded' claim; the primary that drops it satisfies 'silent'
    assert S({"word": "often", "letter": "t", "claimed_silent": True, "pronunciation": "AO1 F AH0 N; AO1 F T AH0 N"}).status == "CONFIRMED"
    assert S({"word": "often", "letter": "t", "claimed_silent": False, "pronunciation": "AO1 F AH0 N; AO1 F T AH0 N"}).status == "CONFIRMED"


def test_vowel_and_edge_sounds():
    V, E = W.verify_vowel_sound, W.verify_edge_sound
    assert V({"word": "cake", "claimed_vowel_sound": "long a", "pronunciation": "K EY1 K"}).status == "CONFIRMED"
    assert V({"word": "cat", "claimed_vowel_sound": "short a", "pronunciation": "K AE1 T"}).status == "CONFIRMED"
    assert V({"word": "cat", "claimed_vowel_sound": "long a", "pronunciation": "K AE1 T"}).status == "MISMATCH"
    assert V({"word": "dog", "claimed_vowel_sound": "short o", "pronunciation": "D AO1 G"}).status == "CONFIRMED"          # AO counts as short o
    assert V({"word": "cup", "claimed_vowel_sound": "short u", "pronunciation": "K AH1 P"}).status == "CONFIRMED"
    assert V({"word": "banana", "claimed_vowel_sound": "short u", "pronunciation": "B AH0 N AE1 N AH0"}).status == "MISMATCH"  # AH0 is a schwa, not a short u
    assert V({"word": "banana", "claimed_vowel_sound": "schwa", "pronunciation": "B AH0 N AE1 N AH0"}).status == "CONFIRMED"
    assert V({"word": "cake", "claimed_vowel_sound": "long a", "claimed": False, "pronunciation": "K EY1 K"}).status == "MISMATCH"
    assert E({"word": "phone", "claimed_edge_sound": "f", "position": "first", "pronunciation": "F OW1 N"}).status == "CONFIRMED"
    assert E({"word": "city", "claimed_edge_sound": "s", "position": "first", "pronunciation": "S IH1 T IY0"}).status == "CONFIRMED"
    assert E({"word": "gem", "claimed_edge_sound": "j", "position": "first", "pronunciation": "JH EH1 M"}).status == "CONFIRMED"
    assert E({"word": "dogs", "claimed_edge_sound": "z", "position": "last", "pronunciation": "D AA1 G Z"}).status == "CONFIRMED"
    assert E({"word": "cats", "claimed_edge_sound": "z", "position": "last", "pronunciation": "K AE1 T S"}).status == "MISMATCH"
    assert E({"word": "knife", "claimed_edge_sound": "k", "position": "first", "pronunciation": "N AY1 F"}).status == "MISMATCH"
    assert E({"word": "think", "claimed_edge_sound": "th", "position": "first", "pronunciation": "TH IH1 NG K"}).status == "CONFIRMED"


# ── etymology: Webster 1913's chains, judged by its own abbreviations ────────────────────────────────────────
SALARY = ["L. salarius.", "F. salarie, L. salarium, originally, salt money, the money given to the Roman soldiers for salt, "
          "which was a part of thir pay, fr. salarius belonging to salt, fr. sal salt. See Salt."]
STRENGTH = "OE. strengthe, AS. streng, fr. strang strong. See Strong."
WINDOW = "OE. windowe, windoge, Icel. vindauga window, properly, wind eye; akin to Dan. vindue. Wind, n., and Eye."
ALGEBRA = ("LL. algebra, fr. Ar. al-jebr reduction of parts to a whole, or fractions to whole numbers, fr. jabara to bind "
           "together, consolidate; al-jebr w'almuqabalah reduction and comparison (by equations): cf. F. algèbre, It. & Sp. algebra.")
MUSCLE = "F., fr. L. musculus a muscle, a little mouse, dim. of mus a mouse. See Mouse, and cf. sense 3 (below)."
CANDIDATE = ("L. Candidatus, n. (because candidates for office in Rome were clothed in a white toga.) fr. candidatus clothed "
             "in white, fr. candiduslittering, white: cf. F. candidat.")
BUNGALOW = "Bengalee bangla"
PHILOSOPHY = "OE. philosophie, F. philosophie, L. philosophia, from Gr. Philosopher."


def test_origin_holds_breaks_and_declines_by_the_chain():
    O = W.verify_origin
    assert O({"word": "salary", "claimed_language": "latin", "etymology": SALARY}).status == "CONFIRMED"
    assert O({"word": "salary", "claimed_language": "french", "etymology": SALARY}).status == "CONFIRMED"           # it came through French
    assert O({"word": "salary", "claimed_language": "latin", "claimed_source_word": "salarium", "etymology": SALARY}).status == "CONFIRMED"
    assert O({"word": "salary", "claimed_language": "latin", "claimed_source_word": "solarium", "etymology": SALARY}).status == "NOT_APPLICABLE"  # the form is not in the chain: declined, never wrong
    assert O({"word": "salary", "claimed_language": "greek", "etymology": SALARY}).status == "MISMATCH"             # Italic only, no Hellenic
    assert O({"word": "strength", "claimed_language": "latin", "etymology": STRENGTH}).status == "MISMATCH"         # wholly Germanic
    assert O({"word": "strength", "claimed_language": "old english", "etymology": STRENGTH}).status == "CONFIRMED"
    assert O({"word": "strength", "claimed_language": "latin", "claimed_origin": False, "etymology": STRENGTH}).status == "CONFIRMED"
    assert O({"word": "window", "claimed_language": "old norse", "etymology": WINDOW}).status == "CONFIRMED"
    assert O({"word": "window", "claimed_language": "danish", "etymology": WINDOW}).status == "NOT_APPLICABLE"      # Dan. only after 'akin to': compared, not derived
    assert O({"word": "algebra", "claimed_language": "arabic", "etymology": ALGEBRA}).status == "CONFIRMED"
    assert O({"word": "algebra", "claimed_language": "french", "etymology": ALGEBRA}).status == "NOT_APPLICABLE"    # 'cf. F.' compares
    assert O({"word": "algebra", "claimed_language": "greek", "etymology": ALGEBRA}).status == "MISMATCH"
    assert O({"word": "muscle", "claimed_language": "latin", "claimed_gloss": "little mouse", "etymology": MUSCLE}).status == "CONFIRMED"
    assert O({"word": "muscle", "claimed_language": "latin", "claimed_gloss": "little house", "etymology": MUSCLE}).status == "NOT_APPLICABLE"
    assert O({"word": "candidate", "claimed_language": "latin", "claimed_source_word": "candidatus", "etymology": CANDIDATE}).status == "CONFIRMED"
    assert O({"word": "candidate", "claimed_language": "french", "etymology": CANDIDATE}).status == "NOT_APPLICABLE"   # compared, not derived
    assert O({"word": "bungalow", "claimed_language": "bengali", "etymology": BUNGALOW}).status == "CONFIRMED"
    assert O({"word": "bungalow", "claimed_language": "hindi", "etymology": BUNGALOW}).status == "NOT_APPLICABLE"    # same family, the language not named: declined
    assert O({"word": "philosophy", "claimed_language": "greek", "etymology": PHILOSOPHY}).status == "CONFIRMED"
    assert O({"word": "philosophy", "claimed_language": "greek", "claimed_origin": False, "etymology": PHILOSOPHY}).status == "MISMATCH"
    assert O({"word": "philosophy", "claimed_language": "arabic", "etymology": PHILOSOPHY}).status == "MISMATCH"
    assert O({"word": "philosophy", "claimed_language": "klingon", "etymology": PHILOSOPHY}).status == "NOT_APPLICABLE"
    assert O({"word": "salary", "claimed_language": "latin"}).status == "NOT_APPLICABLE"                            # no corpus: declined
    body = "salary: etymology (Webster 1913) — a.: [L. salarius.]; n.: [F. salarie, L. salarium (salt money)]. From Webster's."
    assert W.etymologies_from_body(body) == ["L. salarius.", "F. salarie, L. salarium (salt money)"]


# ── the front door: the ways people write it; with no corpus the verdict is a decline, not a judgement ──────
def test_the_front_door_reaches_phonics_and_etymology():
    rows = {
        "cat rhymes with hat": ("rhyme", {"word_a": "cat", "word_b": "hat", "claimed_rhyme": True}),
        "the words moon and spoon rhyme": ("rhyme", {"word_a": "moon", "word_b": "spoon", "claimed_rhyme": True}),
        "cat does not rhyme with dog": ("rhyme", {"word_a": "cat", "word_b": "dog", "claimed_rhyme": False}),
        "banana is a perfect rhyme for bandana": ("rhyme", {"word_a": "banana", "word_b": "bandana", "claimed_rhyme": True}),
        "there and their are homophones": ("homophone", {"word_a": "there", "word_b": "their", "claimed_homophone": True}),
        "night is a homophone of knight": ("homophone", {"word_a": "night", "word_b": "knight", "claimed_homophone": True}),
        "flower and flour sound the same": ("homophone", {"word_a": "flower", "word_b": "flour", "claimed_homophone": True}),
        "bear and beer are pronounced differently": ("homophone", {"word_a": "bear", "word_b": "beer", "claimed_homophone": False}),
        "banana is stressed on the second syllable": ("stress", {"word": "banana", "claimed_stress_syllable": 2}),
        "the stress in photograph falls on the first syllable": ("stress", {"word": "photograph", "claimed_stress_syllable": 1}),
        "the word photography has its stress on the second syllable": ("stress", {"word": "photography", "claimed_stress_syllable": 2}),
        "in the word hotel the stress is on the last syllable": ("stress", {"word": "hotel", "claimed_stress_syllable": -1}),
        "the k in knife is silent": ("silent_letter", {"word": "knife", "letter": "k", "claimed_silent": True}),
        "the word climb has a silent b": ("silent_letter", {"word": "climb", "letter": "b", "claimed_silent": True}),
        "the t in castle is not pronounced": ("silent_letter", {"word": "castle", "letter": "t", "claimed_silent": True}),
        "the k in kite is pronounced": ("silent_letter", {"word": "kite", "letter": "k", "claimed_silent": False}),
        "the word cake has a long a sound": ("vowel_sound", {"word": "cake", "claimed_vowel_sound": "long a", "claimed": True}),
        "cat has a short a sound": ("vowel_sound", {"word": "cat", "claimed_vowel_sound": "short a", "claimed": True}),
        "the a in cat is long": ("vowel_sound", {"word": "cat", "claimed_vowel_sound": "long a", "claimed": True}),
        "the vowel sound in bike is long i": ("vowel_sound", {"word": "bike", "claimed_vowel_sound": "long i", "claimed": True}),
        "phone starts with the f sound": ("edge_sound", {"word": "phone", "claimed_edge_sound": "f", "position": "first", "claimed": True}),
        "the word city begins with the s sound": ("edge_sound", {"word": "city", "claimed_edge_sound": "s", "position": "first", "claimed": True}),
        "dogs ends with the z sound": ("edge_sound", {"word": "dogs", "claimed_edge_sound": "z", "position": "last", "claimed": True}),
        "the first sound in gem is j": ("edge_sound", {"word": "gem", "claimed_edge_sound": "j", "position": "first", "claimed": True}),
        "salary comes from Latin": ("etymology", {"word": "salary", "claimed_language": "latin", "claimed_origin": True}),
        "the word salary comes from the Latin word salarium": ("etymology", {"word": "salary", "claimed_language": "latin", "claimed_origin": True, "claimed_source_word": "salarium"}),
        "philosophy is of Greek origin": ("etymology", {"word": "philosophy", "claimed_language": "greek", "claimed_origin": True}),
        "the word algebra comes from Arabic": ("etymology", {"word": "algebra", "claimed_language": "arabic", "claimed_origin": True}),
        "window is of Old Norse origin": ("etymology", {"word": "window", "claimed_language": "old norse", "claimed_origin": True}),
        "muscle comes from the Latin word for little mouse": ("etymology", {"word": "muscle", "claimed_language": "latin", "claimed_origin": True, "claimed_gloss": "little mouse"}),
        "the word candidate derives from the Latin candidatus": ("etymology", {"word": "candidate", "claimed_language": "latin", "claimed_origin": True, "claimed_source_word": "candidatus"}),
        "philosophy is not of Greek origin": ("etymology", {"word": "philosophy", "claimed_language": "greek", "claimed_origin": False}),
        "bungalow derives from Hindi": ("etymology", {"word": "bungalow", "claimed_language": "hindi", "claimed_origin": True}),
        "strength is a Latin word": ("etymology", {"word": "strength", "claimed_language": "latin", "claimed_origin": True}),
        "the Latin word salarium gave us salary": ("etymology", {"word": "salary", "claimed_language": "latin", "claimed_origin": True, "claimed_source_word": "salarium"}),
    }
    for text, (name, want) in rows.items():
        got = _specs(text)
        assert got, f"nothing extracted from {text!r}"
        names = {n for n, _s in got}
        assert name in names, f"{text!r}: fired {names}, wanted {name}"
        spec = [s for n, s in got if n == name][0]
        assert spec == want, f"{text!r}: {spec} != {want}"
        r = audit(text, CFG, seal=False, index=False, card=False)
        assert r["claims_found"] >= 1 and r["verdict"] == "INCOMPLETE", (text, r["verdict"])   # no corpus: declined
    # not phonics: a pronoun, a comparison that is not a rhyme claim, 'starts with c' (a letter, not a sound)
    assert not _specs("it rhymes with everything he says")
    assert not _specs("cat starts with c")
    assert not _specs("Paul comes from Tarsus")


# ── the Webster parser (tools/card_etymology.py), pinned on a fixture in the Gutenberg text's own shape ──────
FIXTURE = """The Project Gutenberg eBook of Webster's Unabridged Dictionary
SALARY
Sal"a*ry, a. Etym: [L. salarius.]

Defn: Saline [Obs.]

SALARY
Sal"a*ry, n.; pl. Salaries. Etym: [F. salarie, L. salarium,
originally, salt money, the money given to the Roman soldiers for
salt, fr. sal salt. See Salt.]

Defn: The recompense or consideration paid.

STRENGTH
Strength, n. Etym: [OE. strengthe, AS. streng, fr. strang strong. See
Strong.]

1. The quality or state of being strong.

SALT
Salt, n. Etym: [AS. sealt; akin to D. zout, G. salz, L. sal, Gr.
[Gr. hals].]

Defn: The chloride of sodium.
"""


def test_the_webster_parser_keeps_every_bracket_as_written():
    import card_etymology as CE
    entries = CE.parse_entries(FIXTURE)
    assert set(entries) == {"SALARY", "STRENGTH", "SALT"}
    assert entries["SALARY"] == [("a.", "L. salarius."),
                                 ("n.", "F. salarie, L. salarium, originally, salt money, the money given to the Roman soldiers for salt, fr. sal salt. See Salt.")]
    assert entries["STRENGTH"][0][1] == "OE. strengthe, AS. streng, fr. strang strong. See Strong."
    assert entries["SALT"][0][1] == "AS. sealt; akin to D. zout, G. salz, L. sal, Gr. [Gr. hals]."   # nested bracket balanced
    c = CE.card("SALARY", entries["SALARY"])
    assert c["id"] == "card_src_etym_salary" and c["shelf"] == "etymology" and c["generated"] is False
    assert W.etymologies_from_body(c["body"])[0] == "L. salarius."
    assert "(Gr. hals)" in CE.card("SALT", entries["SALT"])["body"]      # inner brackets become parentheses in the body
    # the card body feeds the verifier exactly as the shelf would
    etyms = W.etymologies_from_body(c["body"])
    assert W.verify_origin({"word": "salary", "claimed_language": "latin", "claimed_source_word": "salarium", "etymology": etyms}).status == "CONFIRMED"
