"""The resonance floor (ask._covers_the_asking) — the fix for the "human capital theory" bug.

A found answer must cover the asking's rarest (most identifying) token, not just a common one.
These test the pure logic with a tiny fake corpus (its `_by_token` sets the token frequencies), so
they run on a clean clone with no full corpus. The floor's threshold is the corpus's own token
frequencies, so there is nothing to tune — only to validate against the box's full keeping.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import ask  # noqa: E402


class _FakeCorpus:
    def __init__(self, by_token):
        self._by_token = by_token


# "capital" is common in the keeping (human capital, capital markets, …); "france" is rarer.
_KEEPING = _FakeCorpus({"capital": ["c1", "c2", "c3", "c4", "c5"], "france": ["c6"],
                        "paris": ["c6"], "theory": ["c1", "c7"], "human": ["c1", "c8"]})


def test_floor_nulls_a_lead_that_misses_the_rarest_token():
    lead = {"title": "Human capital theory (Becker, Mincer)",
            "body": "schooling is an investment with a discounted stream of returns"}
    assert ask._covers_the_asking(lead, "what is the capital of France", _KEEPING) is False


def test_floor_passes_a_lead_that_covers_the_rarest_token():
    lead = {"title": "France", "body": "The capital of France is Paris, on the Seine."}
    assert ask._covers_the_asking(lead, "what is the capital of France", _KEEPING) is True


def test_floor_does_not_suppress_a_thin_asking():
    # a single content token can't discriminate — never suppress on it
    assert ask._covers_the_asking({"title": "x", "body": "y"}, "paris", _KEEPING) is True


def test_floor_does_not_suppress_when_the_keeping_holds_too_little():
    # neither token is in the keeping -> cannot discriminate -> don't suppress
    empty = _FakeCorpus({})
    assert ask._covers_the_asking({"title": "z", "body": ""}, "quokka numbat population", empty) is True
