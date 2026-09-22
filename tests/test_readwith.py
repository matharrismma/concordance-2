"""READ WITH THE COACH — the chosen text becomes the cube's decodable surface, and stays HONEST.

Matt, 2026-09-22: "choose the text." The cube is the frame; the learner's chosen public-domain work
supplies the words. What must hold:

  * every sentence returned is VERBATIM from the work and carries one of the cube's anchors — found by
    the lens, never composed to fit
  * shortest first (short = most decodable)
  * OCR debris (index rows, tables of figures) is not offered as a sentence
  * a line the scanner wrapped ("impor- tant") is rejoined to the word it really is — restored, not
    rewritten — while real compounds (home-grown) are left alone
  * honest when a book holds few anchors, and when the work cannot be read at all

No test here touches the network: tortoise.open_work is stubbed.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from concordance import readwith  # noqa: E402


def _stub(monkeypatch, text, **head):
    base = {"status": "read", "text": text, "title": "A Manual", "detail_url": "https://archive.org/details/x",
            "language": "english", "discipline": "carpentry"}
    base.update(head)
    monkeypatch.setattr(readwith.tortoise, "open_work", lambda card, **k: base)


CARD = {"id": "card_arch_x", "title": "A Manual", "language": "english"}


def test_it_finds_real_anchor_sentences_verbatim_shortest_first(monkeypatch):
    _stub(monkeypatch,
          "This is very important. There are no medullary rays visible. It is chiefly home-grown. "
          "The joiner selected a long board of well-seasoned oak for the frame.")
    r = readwith.decodable(CARD, "en", limit=5)
    assert r["status"] == "read"
    texts = [f["text"] for f in r["found"]]
    assert "This is very important." in texts
    assert "It is chiefly home-grown." in texts          # the compound is preserved
    # the sentence with no anchor is not invented into the set
    assert all(f["anchor"] for f in r["found"])
    # shortest first
    words = [f["words"] for f in r["found"]]
    assert words == sorted(words)


def test_a_wrapped_word_is_rejoined_not_rewritten(monkeypatch):
    _stub(monkeypatch, "This is very impor- tant work.")
    r = readwith.decodable(CARD, "en", limit=3)
    assert r["found"], "the sentence should be found"
    assert "important" in r["found"][0]["text"]
    assert "impor- tant" not in r["found"][0]["text"]


def test_ocr_debris_is_not_offered_as_a_sentence(monkeypatch):
    # a row of figures with an anchor-looking fragment: mostly non-letters -> rejected
    _stub(monkeypatch, "12 3/4 in. 5 6 7 8 9 10 11 12 13 14 15 16 17 18 there is 3 4 5 6 7 8 9 0.")
    r = readwith.decodable(CARD, "en", limit=5)
    assert r["found"] == [], "a table of figures is not a readable sentence"


def test_honest_when_a_book_holds_no_anchors(monkeypatch):
    _stub(monkeypatch, "The joiner selected oak. He planed the board with care. The grain ran true.")
    r = readwith.decodable(CARD, "en", limit=5)
    assert r["status"] == "read"
    assert r["count"] == 0
    assert "few" in r["note"].lower() or "another" in r["note"].lower()


def test_a_work_that_cannot_be_read_passes_the_miss_through(monkeypatch):
    monkeypatch.setattr(readwith.tortoise, "open_work",
                        lambda card, **k: {"status": "not_available", "reason": "no plain-text edition",
                                           "title": "A Scan", "detail_url": "https://archive.org/details/y"})
    r = readwith.decodable(CARD, "en")
    assert r["status"] == "not_available"
    assert r["found"] == [] and r["count"] == 0
    assert r["reason"]


def test_non_latin_markers_match_their_own_script(monkeypatch):
    """A Greek work read with the Greek cube matches the Greek anchors as substrings."""
    _stub(monkeypatch, "οὗτός ἐστιν ὁ ἄρτος. ἔστι τράπεζα ἐν τῷ οἴκῳ. πολλοὶ ἄνθρωποι ἦλθον.",
          language="greek")
    r = readwith.decodable(CARD, "grc", limit=5)
    assert r["count"] >= 1
    assert any("ἄρτος" in f["text"] or "τράπεζα" in f["text"] for f in r["found"])


def test_language_maps_to_the_right_cube():
    assert readwith.subjects_for_language("German") == "de"
    assert readwith.subjects_for_language("latin") == "la"
    assert readwith.subjects_for_language("") == "en"
    assert readwith.subjects_for_language("Klingon") == "en"     # unknown -> the anchor cube


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
