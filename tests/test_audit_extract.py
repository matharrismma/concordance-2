"""Auditor extraction — natural quote phrasing (2026-08-24).

The front door promises "every number in your quote." The v1 extractor only recognized clean
arithmetic, so a real quote ("50 brackets at $12.40 each", "22 machine hours at $95/hr") extracted
nothing. These tests lock the two new/loosened patterns AND the zero-false-positive discipline that
governs all extraction: ambiguous text extracts NOTHING — better to miss a claim than check the
wrong one.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance.audit import extract, audit  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402

CFG = EngineConfig(skip_schema_validation=True)


def _extractors(text):
    return [s["extractor"] for s in extract(text)]


# ---- the new "N units at $X each = $Y" pattern ----

def test_units_at_each_extracts_and_confirms():
    text = "50 brackets at $12.40 each = $620"
    assert _extractors(text) == ["units_each"]
    res = audit(text, CFG, seal=False)
    assert res["held"] == 1 and res["broken"] == 0


def test_units_at_each_catches_a_wrong_total():
    res = audit("50 widgets at $12.40 each = $700", CFG, seal=False)  # 620, not 700
    assert res["broken"] == 1
    assert res["results"][0]["status"] == "MISMATCH"


def test_units_each_with_multiword_descriptor():
    assert _extractors("120 stainless steel washers at $0.35 each = $42") == ["units_each"]


# ---- loosened hours: a descriptor may sit before "hours" ----

def test_hours_with_descriptor_extracts_and_confirms():
    text = "22 machine hours at $95/hr = $2,090"
    assert "gross_pay" in _extractors(text)
    assert audit(text, CFG, seal=False)["held"] == 1


def test_plain_hours_still_extracts():   # regression — the original phrasing must not break
    assert "gross_pay" in _extractors("22 hours at $95/hr = $2,090")


# ---- a real four-line quote, one number wrong ----

def test_full_quote_three_hold_one_broken():
    text = ("50 brackets at $12.40 each = $620\n"
            "22 machine hours at $95/hr = $2,090\n"
            "$620 + $2,090 = $2,710\n"
            "10% of $2,710 = $300")   # should be $271
    res = audit(text, CFG, seal=False)
    assert res["claims_found"] == 4
    assert res["held"] == 3 and res["broken"] == 1


# ---- zero false positives: ambiguity extracts NOTHING ----

def test_ambiguous_text_extracts_nothing():
    for t in [
        "We made 50 brackets for the customer.",              # no relationship asserted
        "50 brackets, $12.40, $620",                          # columnar, no 'at/each/='
        "50 brackets at $12.40 = $620",                       # no per-item marker -> not guessed
        "call me at 5 for the $12 part",                      # 'at' + numbers but no claim
    ]:
        assert extract(t) == [], t


# ---- named physical constants (dogfood 2026-09-06): a COMPUTABLE claim, so a verdict + receipt ----

def test_a_named_constant_confirms_against_codata():
    text = "the speed of light is 299792458 m/s"
    assert _extractors(text) == ["physical_constant"]
    res = audit(text, CFG, seal=False)
    assert res["held"] == 1 and res["broken"] == 0
    assert res["results"][0]["domain"] == "physical_constants"


def test_a_wrong_constant_value_is_broken():
    res = audit("the speed of light is 300000000 m/s", CFG, seal=False)  # rounded, outside 1e-4
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_a_true_constant_is_never_broken_by_unit_formatting():
    """The gas constant IS 8.314 J/(mol·K); written "J/K/mol" the stored form differs, but the value
    is right. The unit is passed to the verifier ONLY when it will confirm, so a true claim is checked
    on its value and never falsely BROKEN over unit spelling — the auditor's asymmetry, applied here."""
    res = audit("the ideal gas constant is 8.314 J/K/mol", CFG, seal=False)
    assert res["held"] == 1 and res["broken"] == 0


def test_scientific_notation_and_apostrophe_names_extract():
    assert _extractors("avogadro's number is 6.022e23") == ["physical_constant"]
    res = audit("the boltzmann constant is 1.380649e-23 J/K", CFG, seal=False)
    assert res["held"] == 1


def test_a_bare_symbol_or_common_word_is_not_a_constant_claim():
    """Conservative: a lone symbol/greek letter or a common word is far too ambiguous in prose, so it
    is NOT matched as a constant. The required numeric value guards the rest — better to miss than to
    tell someone their unrelated number is a wrong physical constant."""
    for t in ["alpha is 0.5", "c is 4", "the total is 36", "e is 2.718", "our margin is 0.1"]:
        assert "physical_constant" not in _extractors(t), t


if __name__ == "__main__":
    import pytest
    sys.exit(int(pytest.main([__file__, "-q"])))
