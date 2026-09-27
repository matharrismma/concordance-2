"""ELDERSHIP — the orca matriarch's weight on the cloud of witnesses. Pins: OFF by default (absent);
canon and enduring (PD-by-age) sources are elders, recent ones are not; groups witnesses like quorum."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402
from concordance import eldership  # noqa: E402


def _c(cid, subject, source_label):
    return {"id": cid, "subject": subject, "title": subject, "source": {"label": source_label}}


def test_off_by_default_is_absent(monkeypatch):
    monkeypatch.delenv("CONCORDANCE_ELDERSHIP", raising=False)
    assert eldership.enabled() is False
    assert eldership.assess([_c("a", "grace", "KJV Bible")]) is None


def test_canon_and_pd_age_are_elders_recent_is_not():
    assert eldership.standing(_c("a", "grace", "KJV Bible"))["elder"] is True
    assert eldership.standing(_c("b", "grace", "Matthew Henry 1710"))["elder"] is True
    assert eldership.standing(_c("c", "grace", "Modern Devotional Blog 2024"))["elder"] is False


def test_assess_counts_elders_among_witnesses(monkeypatch):
    monkeypatch.setenv("CONCORDANCE_ELDERSHIP", "1")
    hits = [_c("a", "the fear of the Lord", "KJV Bible"),
            _c("b", "the fear of the Lord reverence", "Matthew Henry 1710"),
            _c("c", "the fear of the Lord", "Modern Devotional Blog 2024")]
    e = eldership.assess(hits)
    assert e["elders"] == 2 and e["witnesses"] == 3 and "elders concur" in e["means"]


def test_no_elder_says_recent(monkeypatch):
    monkeypatch.setenv("CONCORDANCE_ELDERSHIP", "1")
    hits = [_c("a", "quantum widgets", "Modern Blog 2024"),
            _c("b", "quantum widgets", "Another Site 2023")]
    e = eldership.assess(hits)
    assert e["elders"] == 0 and "recent testimony" in e["means"]


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
