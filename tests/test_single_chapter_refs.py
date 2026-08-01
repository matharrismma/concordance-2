"""In a one-chapter book, a bare number is the VERSE — `Jude 9` is Jude 1:9.

FOUND BY tools/calibrate.py ON ITS FIRST RUN, 2026-08-01. `Philemon 6`, `Jude 9` and `Obadiah 1`
all answered "could not parse reference". These are not exotic forms — they are how these books
are ALWAYS cited; nobody writes "Jude 1:9". Three of the five one-chapter books in the canon were
unreachable by their ordinary name, with 1,100+ tests green.

That is the point of a calibration standard: it is not a code failure, so no test would have
caught it. Only measuring the engine against known-true reference points could.

WHICH BOOKS HAVE ONE CHAPTER IS ASKED OF THE CORPUS, never hardcoded — a literal list would be a
second source of truth about the canon, free to drift from the text we actually hold.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from concordance.verifiers import scripture  # noqa: E402

ONE_CHAPTER = [("Jude 9", "Jude 1:9"), ("Philemon 6", "Philemon 1:6"),
               ("Obadiah 1", "Obadiah 1:1"), ("2 John 4", "2 John 1:4"),
               ("3 John 2", "3 John 1:2")]


def _skip_if_unprovisioned():
    if scripture.resolve_ref("John 3:16").get("status") == "source_missing":
        pytest.skip("bible_en.jsonl not provisioned here")


@pytest.mark.parametrize("ref,expect", ONE_CHAPTER)
def test_a_bare_verse_in_a_one_chapter_book_resolves(ref, expect):
    _skip_if_unprovisioned()
    d = scripture.resolve_ref(ref)
    assert d["status"] == "ok", f"{ref} -> {d.get(chr(39) + 'detail' + chr(39))}"
    assert d["ref"] == expect
    assert d["text"].strip(), "resolved with no text is a claim with nothing behind it"


@pytest.mark.parametrize("ref", ["John 3", "Genesis 1", "Romans 8"])
def test_a_bare_number_in_a_MULTI_chapter_book_is_still_a_chapter(ref):
    """The guard that keeps the fix from over-reaching: `John 3` means chapter 3, and resolving it
    to John 1:3 would be a confident wrong answer — worse than declining."""
    _skip_if_unprovisioned()
    assert scripture.resolve_ref(ref)["status"] != "ok"


def test_a_verse_past_the_end_of_a_one_chapter_book_declines_precisely():
    _skip_if_unprovisioned()
    d = scripture.resolve_ref("Jude 99")
    assert d["status"] == "not_found"
    assert "1:99" in d["detail"], "the refusal must name what it looked for"


def test_an_unknown_book_with_a_bare_number_still_declines():
    _skip_if_unprovisioned()
    assert scripture.resolve_ref("Hezekiah 3")["status"] != "ok"


def test_the_one_chapter_set_is_read_from_the_corpus_not_a_list():
    """A hardcoded canon would be a second source of truth, free to drift from the text we hold."""
    src = Path(scripture.__file__).read_text(encoding="utf-8")
    assert "_is_single_chapter" in src
    for name in ("Jude", "Philemon", "Obadiah"):
        assert f'"{name}"' not in src.split("_COMMON_ABBREV")[-1].split("class Bible")[0],             f"{name} looks hardcoded as a one-chapter book — ask the corpus instead"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
