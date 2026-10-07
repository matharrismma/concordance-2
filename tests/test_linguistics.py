"""Unit-pin the linguistics verifier (A2, 2026-10-06). Normalized transliteration match: two spellings
that normalize to the same form match; different words do not. Empty input NOT_APPLICABLE.
(Strong's-backed checks need the lexicon and are exercised with corpus data.)"""
from __future__ import annotations
from concordance.verifiers import linguistics as LN


def test_transliteration_normalized_match():
    assert LN.verify_transliteration_normalized_match("shalom", "shalom").status == "CONFIRMED"
    assert LN.verify_transliteration_normalized_match("shalom", "khesed").status == "MISMATCH"
    assert LN.verify_transliteration_normalized_match("", "").status == "NOT_APPLICABLE"
