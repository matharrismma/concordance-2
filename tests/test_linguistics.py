"""Unit-pin the linguistics verifier (A2, 2026-10-06). Normalized transliteration match: two spellings
that normalize to the same form match; different words do not. Empty input NOT_APPLICABLE.
(Strong's-backed checks need the lexicon and are exercised with corpus data.)"""
from __future__ import annotations
from concordance.verifiers import linguistics as LN


def test_transliteration_normalized_match():
    assert LN.verify_transliteration_normalized_match("shalom", "shalom").status == "CONFIRMED"
    assert LN.verify_transliteration_normalized_match("shalom", "khesed").status == "MISMATCH"
    assert LN.verify_transliteration_normalized_match("", "").status == "NOT_APPLICABLE"


def test_romanization_is_greek_only_and_zero_false_positive():
    """General transliteration (Matt, 2026-10-10: "expand linguistics to be comprehensive"). Greek
    romanizes by a fixed scheme and a claim is confirmed only on an exact (folded) match; a wrong
    romanization never confirms; Hebrew and other scripts decline rather than guess."""
    assert LN.verify_romanization("λόγος", "logos").status == "CONFIRMED"
    assert LN.verify_romanization("θεός", "theos").status == "CONFIRMED"
    assert LN.verify_romanization("ἀγάπη", "agape").status == "CONFIRMED"  # breathing stripped
    assert LN.verify_romanization("λόγος", "logy").status == "MISMATCH"
    assert LN.verify_romanization("שלום", "shalom").status == "NOT_APPLICABLE"  # Hebrew declines
    assert LN.verify_romanization("cat", "kat").status == "NOT_APPLICABLE"


def test_semantic_relations_report_wordnet_cited():
    """Semantic relations (Matt, 2026-10-10: comprehensive linguistics, step 3). Synonymy and IS-A
    come from the held WordNet thesaurus, cited; antonymy is not held and declines; an unheld
    relation is a MISMATCH, never a false confirm."""
    import pytest
    from concordance import thesaurus as TH
    if not TH.available():
        pytest.skip("thesaurus.db not present")
    assert LN.verify_semantic_relation("car", "automobile", "synonym").status == "CONFIRMED"
    assert LN.verify_semantic_relation("dog", "happy", "synonym").status == "MISMATCH"
    assert LN.verify_semantic_relation("dog", "canine", "is_a").status == "CONFIRMED"
    assert LN.verify_semantic_relation("dog", "carnivore", "is_a").status == "CONFIRMED"   # transitive
    assert LN.verify_semantic_relation("dog", "mineral", "is_a").status == "MISMATCH"
    assert LN.verify_semantic_relation("hot", "cold", "antonym").status == "NOT_APPLICABLE"  # not held
