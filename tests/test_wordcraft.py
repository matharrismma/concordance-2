"""WORDCRAFT (linguistics as a strength, Matt, 2026-10-08): the computable claims about words, letters and
alphabets, through the verifier and through the front door. No corpus: the syllable check with no corpus declines."""
from __future__ import annotations

import os
import tempfile

TMP = tempfile.mkdtemp(prefix="nh-words-")
os.environ.setdefault("CONCORDANCE_DATA_DIR", TMP)

from concordance.audit import audit, extract  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.verifiers import wordcraft as W  # noqa: E402

CFG = EngineConfig("secular")


def _v(text: str) -> str:
    return audit(text, CFG, seal=False, index=False, card=False)["verdict"]


def test_the_verifier_counts_and_compares():
    assert W.verify_letters({"word": "strengths", "claimed_letters": 9, "claimed_vowels": 1}).status == "CONFIRMED"
    assert W.verify_letters({"word": "strengths", "claimed_vowels": 2}).status == "MISMATCH"
    assert W.verify_letters({"word": "rhythm", "claimed_vowels": 0}).status == "CONFIRMED"      # y is a consonant letter here, said so
    assert W.verify_anagram({"word_a": "listen", "word_b": "silent", "claimed_anagram": True}).status == "CONFIRMED"
    assert W.verify_anagram({"word_a": "listen", "word_b": "silver", "claimed_anagram": True}).status == "MISMATCH"
    assert W.verify_palindrome({"word": "Racecar", "claimed_palindrome": True}).status == "CONFIRMED"
    assert W.verify_palindrome({"word": "engine", "claimed_palindrome": True}).status == "MISMATCH"
    assert W.levenshtein("kitten", "sitting") == 3
    assert W.verify_edit_distance({"word_a": "kitten", "word_b": "sitting", "claimed_edit_distance": 3}).status == "CONFIRMED"
    assert W.verify_edit_distance({"word_a": "kitten", "word_b": "sitting", "claimed_edit_distance": 2}).status == "MISMATCH"
    assert W.arpabet_counts("EH2 N S AY2 K L OW0 P IY1 D IY0 AH0") == (6, 12)
    # the card body as the keeping writes it: the FIRST pronunciation, a variant after "; also" ignored
    body = "strength: pronounced (ARPABET) S T R EH1 NG K TH; also S T R EH1 NG TH. From the CMU Pronouncing Dictionary."
    assert W.arpabet_from_body(body) == "S T R EH1 NG K TH" and W.arpabet_counts(W.arpabet_from_body(body)) == (1, 7)
    assert W.arpabet_from_body("level: pronounced (ARPABET) L EH1 V AH0 L. From the CMU") == "L EH1 V AH0 L"
    r = W.verify_syllables({"word": "encyclopedia", "claimed_syllables": 6, "pronunciation": "EH2 N S AY2 K L OW0 P IY1 D IY0 AH0"})
    assert r.status == "CONFIRMED"
    assert W.verify_syllables({"word": "encyclopedia", "claimed_syllables": 6}).status == "NOT_APPLICABLE"   # no corpus here: declined
    assert W.verify_alphabet({"alphabet": "Hebrew", "claimed_alphabet_letters": 22}).status == "CONFIRMED"
    assert W.verify_alphabet({"alphabet": "greek", "claimed_alphabet_letters": 26}).status == "MISMATCH"
    assert W.verify_alphabet({"alphabet": "klingon", "claimed_alphabet_letters": 26}).status == "NOT_APPLICABLE"
    assert W.verify_plural({"singular": "child", "claimed_plural": "children"}).status == "CONFIRMED"
    assert W.verify_plural({"singular": "child", "claimed_plural": "childs"}).status == "MISMATCH"
    assert W.verify_plural({"singular": "city", "claimed_plural": "cities"}).status == "CONFIRMED"
    assert W.verify_plural({"singular": "box", "claimed_plural": "boxes"}).status == "CONFIRMED"
    assert W.verify_plural({"singular": "octopus", "claimed_plural": "octopodes"}).status == "NOT_APPLICABLE"   # not held: declined, never wrong
    assert W.verify_letter_rank({"letter": "e", "claimed_rank": 1}).status == "CONFIRMED"
    assert W.verify_letter_rank({"letter": "z", "claimed_rank": 26}).status == "CONFIRMED"
    assert W.verify_letter_rank({"letter": "z", "claimed_rank": 1}).status == "MISMATCH"


def test_the_front_door_reaches_the_ways_people_write_it():
    assert _v("the word strengths has 9 letters") == "HOLDS"
    assert _v("the word strengths has 10 letters") == "BROKEN"
    assert _v("the word strengths has one vowel") == "HOLDS"
    assert _v("strengths is a 9-letter word") == "HOLDS"
    assert _v("the word rhythm has no vowels") == "HOLDS"
    assert _v("the word queue has 4 vowels") == "HOLDS"
    assert _v("listen is an anagram of silent") == "HOLDS"
    assert _v("listen is an anagram of silver") == "BROKEN"
    assert _v("listen is not an anagram of silver") == "HOLDS"
    assert _v("racecar is a palindrome") == "HOLDS"
    assert _v("engine is a palindrome") == "BROKEN"
    assert _v("kitten and sitting are 3 edits apart") == "HOLDS"
    assert _v("the edit distance between kitten and sitting is 2") == "BROKEN"
    assert _v("the Levenshtein distance from flaw to lawn is 2") == "HOLDS"
    assert _v("the Hebrew alphabet has 22 letters") == "HOLDS"
    assert _v("English has 26 letters") == "HOLDS"
    assert _v("the Greek alphabet has 26 letters") == "BROKEN"
    assert _v("the plural of child is children") == "HOLDS"
    assert _v("the plural of child is childs") == "BROKEN"
    assert _v("the plural of city is cities") == "HOLDS"
    assert _v("E is the most common letter in English") == "HOLDS"
    assert _v("the most common letter in English is T") == "BROKEN"
    assert _v("T is the second most common letter in English") == "HOLDS"
    assert _v("Z is the least common letter in English") == "HOLDS"
    # a syllable claim is reached, and with no corpus it is declined rather than judged
    r = audit("the word encyclopedia has 6 syllables", CFG, seal=False, index=False, card=False)
    assert r["claims_found"] == 1 and r["verdict"] == "INCOMPLETE"


def test_the_extractors_name_themselves():
    names = {s["extractor"] for s in extract("listen is an anagram of silent. racecar is a palindrome. "
                                             "the plural of child is children. the Hebrew alphabet has 22 letters.")}
    assert {"anagram", "palindrome", "plural", "alphabet"} <= names
