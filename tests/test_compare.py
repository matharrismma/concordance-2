"""A comparison names what is missing — it never sets two things side by side when one is absent.

Matt, 2026-08-01, having asked the library to compare and contrast Nazarene vs Wesleyan:
*"Nothing worth reading. We don't want to set our rules so tight we can provide no value."*

Both halves of that are load-bearing. The old behaviour put two subjects in one bag of words,
returned six Wesleyan cards, and said nothing about the missing side — half a question answered as
though it were whole. But the cure is not more refusal: COMPOSITION IS NOT GENERATION. Arranging
two voice cards on shared axes, every cell attributable, is the concordance doing its work.

HAVING THE WORD IS NOT HAVING THE THING — the trap this feature exists to avoid. "Nazarene"
matches five cards about Jesus of Nazareth. A naive count would report the subject held and
cheerfully compare a denomination against a biblical epithet. The `churches` shelf is the registry
of traditions we actually cover, so that is the test.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from concordance import compare  # noqa: E402

VOICE = {"id": "c_wes", "title": "Methodist / Wesleyan", "shelf": "churches",
         "body": "Confession: the Articles of Religion (Wesley).",
         "connections": [{"to_card_id": "c_root"}, {"to_card_id": "c_x"}]}
VOICE2 = {"id": "c_bap", "title": "Baptist", "shelf": "churches", "body": "Baptist tradition.",
          "connections": [{"to_card_id": "c_root"}]}
# The word, not the thing: cards that MENTION "Nazarene" but are about Jesus of Nazareth.
WORD_ONLY = [{"id": "c_naz1", "title": "Easton: Nazarene", "shelf": "dictionary", "body": "of Nazareth"},
             {"id": "c_naz2", "title": "ISBE: Nazarene", "shelf": "encyclopedia", "body": "Nazarene"}]


def _fake(mapping):
    return lambda q, limit=8, **k: mapping.get(q.lower(), [])


# ── reading the question ──────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("q,expect", [
    ("compare and contrast Nazarene vs Wesleyan", ["Nazarene", "Wesleyan"]),
    ("Baptist vs Presbyterian", ["Baptist", "Presbyterian"]),
    ("difference between Anglican and Methodist", ["Anglican", "Methodist"]),
    ("contrast Lutheran with Reformed", ["Lutheran", "Reformed"]),
])
def test_a_comparison_is_read_as_two_subjects(q, expect):
    assert compare.subjects_of(q) == expect


@pytest.mark.parametrize("q", ["what is grace", "Wesleyan Church", "", "   ", "compare"])
def test_an_ordinary_question_is_not_a_comparison(q):
    """The parse must not hijack normal questions — a comparison path for everything is worse."""
    assert compare.subjects_of(q) is None


def test_the_same_subject_twice_is_not_a_comparison():
    assert compare.subjects_of("Baptist vs Baptist") is None


# ── the honesty that was missing ──────────────────────────────────────────────────────────────
def test_a_missing_side_is_named_and_never_filled():
    r = compare.compare("compare and contrast Nazarene vs Wesleyan",
                        search=_fake({"nazarene": WORD_ONLY, "wesleyan": [VOICE]}))
    assert r["missing"] == ["Nazarene"]
    assert "no tradition card for Nazarene" in r["message"]
    assert "will not set two things side by side" in r["message"]


def test_holding_the_WORD_is_not_holding_the_THING():
    """Five cards about Jesus of Nazareth must not count as holding the denomination."""
    r = compare.compare("Nazarene vs Wesleyan",
                        search=_fake({"nazarene": WORD_ONLY, "wesleyan": [VOICE]}))
    naz = [s for s in r["sides"] if s["subject"] == "Nazarene"][0]
    assert naz["mentions"] == len(WORD_ONLY), "the mentions are real and are reported"
    assert naz["held_as_tradition"] is False, (
        "a card that merely contains the word must never count as the tradition")
    assert "dictionary" in naz["shelves"], "and we say WHAT we hold instead"


def test_a_missing_side_offers_the_want_but_does_not_open_it():
    """A person asks, a person chooses — the same rule as the want desk."""
    r = compare.compare("Nazarene vs Wesleyan",
                        search=_fake({"nazarene": [], "wesleyan": [VOICE]}))
    assert r["want"] and r["want"]["queries"] == ["Nazarene"]


def test_both_held_composes_without_asserting():
    r = compare.compare("Baptist vs Wesleyan",
                        search=_fake({"baptist": [VOICE2], "wesleyan": [VOICE]}))
    assert r["missing"] == []
    assert all(s["held_as_tradition"] for s in r["sides"])
    assert [s["voice"]["title"] for s in r["sides"]] == ["Baptist", "Methodist / Wesleyan"]


def test_shared_ground_is_read_from_the_cards_never_claimed():
    """The common root is evidence — an edge both voice cards actually carry."""
    r = compare.compare("Baptist vs Wesleyan",
                        search=_fake({"baptist": [VOICE2], "wesleyan": [VOICE]}))
    assert r["shared_ground"] == ["c_root"], "only the edge BOTH hold"
    assert "c_x" not in r["shared_ground"], "an edge only one side has is not shared ground"


def test_shared_ground_is_not_computed_when_a_side_is_missing():
    """Nothing is shared with something that is not here."""
    r = compare.compare("Nazarene vs Wesleyan",
                        search=_fake({"nazarene": WORD_ONLY, "wesleyan": [VOICE]}))
    assert r["shared_ground"] == []


def test_nothing_in_the_answer_is_authored():
    """Every cell must be a card. The module may name absence; it may not write substance."""
    r = compare.compare("Baptist vs Wesleyan",
                        search=_fake({"baptist": [VOICE2], "wesleyan": [VOICE]}))
    for s in r["sides"]:
        for c in s["cards"]:
            assert c.get("id"), "a cell with no card behind it is authored content"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
