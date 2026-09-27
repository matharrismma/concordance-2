"""QUORUM — the 'two or three witnesses' (Deut 19:15) / honeybee-quorum confidence signal. Pins: OFF by
default (absent), counts DISTINCT INDEPENDENT sources on the LEAD's subject (two cards from one source =
one witness), established at the threshold, and never touches which card leads."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402
from concordance import quorum  # noqa: E402


def _c(cid, subject, source_label):
    return {"id": cid, "subject": subject, "title": subject, "source": {"label": source_label}}


def test_off_by_default_is_absent(monkeypatch):
    monkeypatch.delenv("CONCORDANCE_QUORUM", raising=False)
    assert quorum.enabled() is False
    assert quorum.assess([_c("a", "grafting", "Webster")]) is None


def test_two_independent_witnesses_establish(monkeypatch):
    monkeypatch.setenv("CONCORDANCE_QUORUM", "1")
    hits = [_c("a", "the fear of the Lord", "Matthew Henry"),
            _c("b", "the fear of the Lord", "Spurgeon"),
            _c("c", "the fear of the Lord reverence", "Easton")]
    q = quorum.assess(hits)
    assert q["witnesses"] == 3 and q["established"] is True and "established" in q["means"]


def test_one_source_many_cards_is_a_single_witness(monkeypatch):
    monkeypatch.setenv("CONCORDANCE_QUORUM", "1")
    hits = [_c("a", "zymurgy", "Webster 1913 (PD)"),
            _c("b", "zymurgy fermentation", "Webster 1913 (PD)")]   # same source, two cards
    q = quorum.assess(hits)
    assert q["witnesses"] == 1 and q["established"] is False and "single witness" in q["means"]


def test_off_subject_hits_do_not_count_as_witnesses(monkeypatch):
    monkeypatch.setenv("CONCORDANCE_QUORUM", "1")
    hits = [_c("a", "photosynthesis", "OpenStax"),
            _c("b", "the roman aqueducts", "Britannica")]   # unrelated subject — not a witness to the lead
    q = quorum.assess(hits)
    assert q["witnesses"] == 1 and q["established"] is False


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
