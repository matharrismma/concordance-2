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


# "hodge" is rare (one chain); "conjecture" is common (every Millennium node). The Hodge-test bug:
# a lead sharing only the rarest token ("hodge") was NOT suppressed, so Bochner's Hodge-THEORY card led.
_HODGE = _FakeCorpus({"hodge": ["h1"], "conjecture": ["m1", "m2", "m3", "m4"],
                      "harmonic": ["h1", "b1"], "cycles": ["h1"]})


def test_floor_nulls_a_lead_sharing_only_the_rarest_token():
    # Bochner (Hodge THEORY): has "hodge", lacks "conjecture" -> only ONE of two -> suppress
    bochner = {"title": "S. Bochner 1946 - Vector fields and Ricci curvature",
               "body": "harmonic forms and the Hodge decomposition of a Riemannian manifold"}
    assert ask._covers_the_asking(bochner, "the Hodge conjecture", _HODGE) is False


def test_floor_passes_a_lead_that_covers_the_name_via_bands():
    # the Hodge-conjecture node carries the distinctive name in its BANDS, not its prose
    floor = {"title": "The Hodge chain - from periods to the classes that are not cycles",
             "body": "Riemann's periods, Lefschetz's (1,1) theorem, Hodge's harmonic integrals",
             "bands": ["hodge", "Hodge conjecture", "algebraic cycles"]}
    assert ask._covers_the_asking(floor, "the Hodge conjecture", _HODGE) is True


# The gate refused the first deploy of the floor (2026-11-01): four discernment charts the question
# plainly named ("what did the stoics believe", "is mormonism christian", ...) were nulled, because a
# chart's subject lives in its discerns_terms ("the stoics"), not its prose ("Stoicism"). A chart leads
# on purpose (_pair_discernment) — the floor must never second-guess the one the asking names.
_STOA = _FakeCorpus({"stoics": ["s1"], "believe": ["b1", "b2", "b3"], "capital": ["c1", "c2"],
                     "france": ["c6"]})
_STOICISM = {"id": "card_foreshadow_stoicism", "shelf": "foreshadows", "title": "Stoicism",
             "body": "Zeno's porch: live according to nature; the Logos; Paul on the Areopagus (Acts 17).",
             "bands": ["foreshadow", "religion", "stoic", "natural law"],
             "extra": {"discerns_terms": ["stoicism", "stoic philosophy", "the stoics"]}}


def test_floor_never_nulls_the_chart_the_asking_names():
    # "stoics" is in no prose/band token, only in the chart's own terms ("the stoics") -> still leads
    assert ask._covers_the_asking(_STOICISM, "what did the stoics believe", _STOA) is True


def test_floor_still_judges_a_chart_the_asking_did_not_name():
    # the same chart on an unrelated asking is judged by coverage like any card -> suppressed
    assert ask._covers_the_asking(_STOICISM, "what is the capital of France", _STOA) is False


def test_floor_counts_a_charts_terms_toward_its_coverage():
    # no whole term is tripped ("ching" is not "tao te ching"), but the TERM's tokens cover the asking's
    # rarest word and the body covers a second -> covered, like _shares_a_word reads a chart
    chart = {"shelf": "foreshadows", "title": "Chinese traditions", "body": "the Way, virtue, the sage",
             "bands": ["daoism", "the way"], "extra": {"discerns_terms": ["tao te ching", "lao tzu"]}}
    keeping = _FakeCorpus({"ching": ["t1"], "virtue": ["v1", "v2", "v3"], "teaching": ["x1", "x2"]})
    assert ask._covers_the_asking(chart, "ching virtue teaching", keeping) is True
