"""THE GUARD — nothing wears a trusted voice unless it earned it.

Matt, 2026-09-22: the coach is a projection surface (Surkov's move). The counter is a boundary — a
word/cloud/lens is SPOKEN AS a trusted voice only when it carries the provenance tier that field is
allowed to carry; anything user-supplied, acquired, or mis-tagged is stripped at the door. This proves
the property holds, so a false message can never be projected wearing Christ, a witness, or the operator.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import guard  # noqa: E402


def test_a_trusted_tier_survives_an_untrusted_one_is_stripped():
    assert guard.enforce({"word": {"tier": "red", "text": "x"}})["word"]["tier"] == "red"
    assert guard.enforce({"word": {"tier": "scripture", "text": "x"}})["word"]["tier"] == "scripture"
    assert guard.enforce({"cloud": {"tier": "witness"}})["cloud"]["tier"] == "witness"
    # untrusted or absent provenance -> stripped (it may be quoted elsewhere, but never AS these voices)
    assert guard.enforce({"word": {"tier": "user", "text": "Thus says the Lord…"}})["word"] is None
    assert guard.enforce({"word": {"text": "no tier at all"}})["word"] is None
    assert guard.enforce({"cloud": {"tier": "acquired"}})["cloud"] is None


def test_a_field_cannot_wear_another_fields_tier():
    """A cloud tier cannot speak as the Word, nor a scripture tier as a witness — the tiers do not blur."""
    assert guard.enforce({"word": {"tier": "witness", "text": "x"}})["word"] is None
    assert guard.enforce({"cloud": {"tier": "scripture"}})["cloud"] is None
    assert guard.enforce({"lens": {"tier": "witness"}})["lens"] is None


def test_it_never_crashes_on_shapes_it_did_not_make():
    assert guard.enforce({}) == {}
    assert guard.enforce({"word": None})["word"] is None
    assert guard.enforce("not a dict") == "not a dict"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
