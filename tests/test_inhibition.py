"""INHIBITION — the honeybee STOP signal (cross-inhibition). Pins: OFF by default (absent); names the
strongest COMPETING answer on a different subject the lead was committed over; a same-subject hit is a
corroborating witness, not a rival; never changes which card leads."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402
from concordance import inhibition  # noqa: E402


def _c(cid, subject):
    return {"id": cid, "subject": subject, "title": subject}


def test_off_by_default_is_absent(monkeypatch):
    monkeypatch.delenv("CONCORDANCE_INHIBITION", raising=False)
    assert inhibition.enabled() is False
    assert inhibition.assess([_c("a", "grafting")]) is None


def test_names_the_competing_answer(monkeypatch):
    monkeypatch.setenv("CONCORDANCE_INHIBITION", "1")
    hits = [_c("a", "the fear of the Lord"),
            _c("b", "grafting fruit trees"),          # a different subject — a rival answer
            _c("c", "the fear of the Lord reverence")]
    r = inhibition.assess(hits)
    assert r["inhibited"] == "grafting fruit trees"   # the top competing, not the same-subject witness
    assert "cross-inhibition" in r["means"]


def test_all_same_subject_is_uncontested(monkeypatch):
    monkeypatch.setenv("CONCORDANCE_INHIBITION", "1")
    hits = [_c("a", "the fear of the Lord"),
            _c("b", "the fear of the Lord reverence"),
            _c("c", "fear of the Lord wisdom")]
    r = inhibition.assess(hits)
    assert r["inhibited"] is None and "uncontested" in r["means"]


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
