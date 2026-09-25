"""Question retrieval — strip the frame, keep the subject (2026-09-25, lever #1).

The airlock applied to a query: `corpus.query_subject` drops a leading question/request FRAME so the
full-text engine matches the SUBJECT, not the scaffold. Deterministic, conservative, fail-safe — a bare
query is unchanged and an all-frame query is never stripped to nothing (a miss stays a miss). Recall is
protected downstream by search_question, which merges the subject search with the raw one.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance.corpus import query_subject  # noqa: E402


def test_strips_stacked_request_and_bible_frame_to_subject():
    # the live failure case: framing matched "The Great Schism"; the subject matches the right teaching.
    assert query_subject("Can you tell me what the Bible says about being anxious and worried?") \
        == "being anxious and worried"


def test_strips_what_does_the_bible_say_about():
    assert query_subject("what does the Bible say about worry") == "worry"


def test_bare_subject_is_unchanged():
    for q in ["fear of the Lord", "anxiety worry", "the Great Schism of 1054", "photosynthesis"]:
        assert query_subject(q) == q


def test_wh_question_reduces_to_subject():
    assert query_subject("why is the sky blue") == "sky blue"
    assert query_subject("what is the fear of the Lord") == "fear of the Lord"


def test_never_over_strips_to_empty():
    # an all-frame query must still return something real, never empty/whitespace.
    for q in ["what is", "how do", "please", ""]:
        s = query_subject(q)
        assert s == "" if q == "" else (s and s.strip())


def test_idempotent_on_its_own_output():
    once = query_subject("Can you tell me what the Bible says about honey bees?")
    assert query_subject(once) == once      # a stripped subject re-strips to itself


if __name__ == "__main__":
    import pytest
    raise SystemExit(int(pytest.main([__file__, "-q"])))
