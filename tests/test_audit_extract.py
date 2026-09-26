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


# ---- unit conversions (dogfood 2026-09-06): the most common computable claim in AI output ----

def test_a_conversion_confirms_against_the_factor_table():
    text = "1 mile is 1.609 kilometers"
    assert _extractors(text) == ["unit_conversion"]
    res = audit(text, CFG, seal=False)
    assert res["held"] == 1 and res["broken"] == 0
    assert res["results"][0]["domain"] == "unit_conversion"


def test_a_wrong_conversion_is_broken():
    res = audit("1 mile is 2 kilometers", CFG, seal=False)
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_milligrams_and_temperature_convert():
    assert audit("500 mg is 0.5 grams", CFG, seal=False)["held"] == 1
    assert audit("100 degrees fahrenheit is 37.78 celsius", CFG, seal=False)["held"] == 1
    # 100 F is 37.78 C, not 50 — a false temperature claim must break
    assert audit("100 degrees fahrenheit is 50 degrees celsius", CFG, seal=False)["broken"] == 1


def test_cross_dimension_and_non_unit_pairs_are_not_extracted():
    """Conservative: a cross-dimension pair (the table's 'ounce' is mass; a cup is volume) is NOT
    extracted — 'ounce' is ambiguous mass-vs-fluid, so we decline rather than risk a false BROKEN on a
    true fluid-ounce claim. A non-unit pair ('5 apples is 5 fruit') never matches at all."""
    for t in ["2 cups is 16 ounces", "5 apples is 5 fruit", "the team is 5 people"]:
        assert "unit_conversion" not in _extractors(t), t


# ---- percent stated in WORDS (2026-09-15): the box is live; people type "percent", not "%" ----

def test_percent_in_words_extracts_and_confirms():
    text = "12 percent of 500 is 60"
    assert _extractors(text) == ["percent"]
    res = audit(text, CFG, seal=False)
    assert res["held"] == 1 and res["broken"] == 0


def test_percent_in_words_catches_a_wrong_claim():
    res = audit("15 percent of 200 is 45", CFG, seal=False)   # 30, not 45
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_percent_symbol_still_extracts():   # regression — the original % phrasing must not break
    assert "percent" in _extractors("10% of $2,710 = $271")


# ---- arithmetic stated in WORDS (2026-09-15): "2 plus 2 equals 4", not just "2 + 2 = 4" ----

def test_word_arithmetic_extracts_and_confirms():
    for t in ["2 plus 2 equals 4", "3 times 4 is 12", "10 divided by 2 is 5",
              "9 minus 4 is 5", "6 multiplied by 7 is 42"]:
        assert "arith_words" in _extractors(t), t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_word_arithmetic_catches_a_wrong_claim():
    res = audit("2 plus 2 equals 5", CFG, seal=False)
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_word_arithmetic_zero_false_positives():
    """The named operator must sit between two numbers with the verb directly on the result;
    ambiguous prose extracts NOTHING — better to miss than check the wrong thing."""
    for t in [
        "2 plus a few more, is 4 enough?",           # no second number adjacent to 'plus'
        "I called 3 times and 4 people answered",    # 'times' but no claim verb on a result
        "5 minus the discount, roughly 2 left",      # no number after 'minus'
    ]:
        assert "arith_words" not in _extractors(t), t


# ---- unit-equivalence FACTS (2026-09-15): "there are 5280 feet in a mile" ----

def test_unit_fact_extracts_and_confirms():
    for t in ["there are 5280 feet in a mile", "there are 12 inches in a foot",
              "there are 100 centimeters in a meter"]:
        assert _extractors(t) == ["unit_fact"], t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_unit_fact_catches_a_wrong_fact():
    res = audit("there are 5000 feet in a mile", CFG, seal=False)   # 5280, not 5000
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_unit_fact_zero_false_positives():
    """The 'there are' marker is required so a count-claim ("there are N X in a Y") is not confused
    with mere containment ("5 minutes in an hour" = within); and unknown/non-unit words never match."""
    for t in [
        "I spent 5 minutes in an hour-long call",   # 'in an hour' but no 'there are' -> within, not a fact
        "there are 5 apples in a basket",           # apples/basket are not units
        "there are 3 people in a room",             # not units
    ]:
        assert "unit_fact" not in _extractors(t), t


# ---- powers / exponents (2026-09-15): "2 to the power of 10 is 1024", "2^10 = 1024" ----

def test_power_extracts_and_confirms():
    for t in ["2 to the power of 10 is 1024", "2^10 = 1024", "10 to the power of 3 is 1000"]:
        assert "power" in _extractors(t), t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_power_catches_a_wrong_claim():
    res = audit("10 to the power of 3 is 999", CFG, seal=False)   # 1000, not 999
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_power_zero_false_positives():
    for t in [
        "2 to the power of 0.5 is 1.414",   # decimal exponent -> approximation, skipped
        "I scored 5! It was great",         # bare ! with no claim verb + number
    ]:
        assert "power" not in _extractors(t) and "factorial" not in _extractors(t), t


# ---- factorial (2026-09-15): "5 factorial is 120", "5! is 120" ----

def test_factorial_extracts_and_confirms():
    for t in ["5 factorial is 120", "5! is 120", "6 factorial is 720"]:
        assert "factorial" in _extractors(t), t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_factorial_catches_a_wrong_claim():
    res = audit("4 factorial is 30", CFG, seal=False)   # 24, not 30
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


# ---- square roots of PERFECT SQUARES only (2026-09-15): exact so equality is right ----

def test_sqrt_of_perfect_square_extracts_and_confirms():
    for t in ["the square root of 144 is 12", "square root of 64 is 8", "the square root of 400 is 20"]:
        assert "sqrt" in _extractors(t), t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_sqrt_catches_a_wrong_perfect_square_claim():
    res = audit("the square root of 16 is 5", CFG, seal=False)   # 4, not 5
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_sqrt_of_non_perfect_square_extracts_nothing():
    """sqrt(2) = 1.41421... is irrational; the exact-symbolic verifier would break a correct
    approximation harshly, so a non-perfect-square root is skipped (a miss stays a miss)."""
    for t in ["the square root of 2 is 1.414", "square root of 10 is 3.16", "square root of 2.5 is 1.58"]:
        assert "sqrt" not in _extractors(t), t


# ---- circle geometry (2026-09-15): verifier tolerance loosened to 1e-3 so user rounding holds ----

def test_circle_area_extracts_and_confirms():
    for t in ["a circle of radius 3 has area 28.27", "a circle with radius 5 has circumference 31.42"]:
        assert "circle" in _extractors(t), t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_circle_catches_a_wrong_area():
    res = audit("a circle of radius 3 has area 50", CFG, seal=False)   # ~28.27, not 50
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_circle_zero_false_positives():
    for t in ["a circle of radius 3 has area to spare", "the circle of life has no radius"]:
        assert "circle" not in _extractors(t), t


# ---- Newton's second law F = m*a (2026-09-15): "10 kg at 9.8 m/s^2 exerts 98 N" ----

def test_force_extracts_and_confirms():
    for t in ["a 10 kg mass at 9.8 m/s^2 exerts 98 N of force", "10 kg at 9.8 m/s² exerts 98 N"]:
        assert "physics_force" in _extractors(t), t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_force_catches_a_wrong_claim():
    res = audit("10 kg at 9.8 m/s^2 is 50 N", CFG, seal=False)   # 98, not 50
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_force_zero_false_positives():
    """The three units (kg, m/s^2, N) anchor it; a bare mass with no acceleration/force is skipped."""
    for t in ["the 10 kg box sat at the dock", "she ran 10 km at 9 minutes per mile"]:
        assert "physics_force" not in _extractors(t), t


# ---- molar mass from a chemical formula (2026-09-15): new periodic_table.molar_mass verifier ----

def test_molar_mass_extracts_and_confirms():
    for t in ["the molar mass of H2O is 18.015 g/mol", "the molar mass of CO2 is 44.01 g/mol",
              "the molar mass of C6H12O6 is 180.16 g/mol"]:
        assert "molar_mass" in _extractors(t), t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_molar_mass_catches_a_wrong_claim():
    res = audit("the molar mass of H2O is 20 g/mol", CFG, seal=False)   # 18.015, not 20
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_molar_mass_zero_false_positives():
    """Formula notation only, case-significant; a plain word or a parenthesised/complex formula is
    skipped rather than mis-parsed (a miss stays a miss)."""
    for t in [
        "the molar mass of water is 18",       # lowercase word, not a formula token
        "the molar mass of Ca(OH)2 is 74.09",  # parentheses unsupported -> not extracted
    ]:
        assert "molar_mass" not in _extractors(t), t


# ---- Pythagorean theorem (2026-09-24): "a right triangle with legs 3 and 4 has hypotenuse 5" ----

def test_pythagorean_extracts_and_confirms():
    for t in ["a right triangle with legs 3 and 4 has hypotenuse 5",
              "a right triangle with legs of 5 and 12 has a hypotenuse of 13"]:
        assert "pythagorean" in _extractors(t), t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_pythagorean_catches_a_wrong_claim():
    res = audit("a right triangle with legs 3 and 4 has hypotenuse 6", CFG, seal=False)  # 5, not 6
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_pythagorean_zero_false_positives():
    for t in ["the triangle restaurant has great legs of lamb", "legs 3 and 4 of the trip were long"]:
        assert "pythagorean" not in _extractors(t), t


# ---- polygon interior-angle sum (2026-09-24): "a hexagon interior angles sum to 720 degrees" ----

def test_polygon_angles_extracts_and_confirms():
    for t in ["a hexagon interior angles sum to 720 degrees",
              "a pentagon interior angles add up to 540 degrees"]:
        assert "polygon_angles" in _extractors(t), t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_polygon_angles_catches_a_wrong_claim():
    res = audit("a hexagon interior angles sum to 700 degrees", CFG, seal=False)  # 720, not 700
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_polygon_angles_zero_false_positives():
    for t in ["the octagon table seats eight", "a hexagon has real interior beauty"]:
        assert "polygon_angles" not in _extractors(t), t


# ---- kinetic energy (2026-09-24): "a 2 kg object at 3 m/s has kinetic energy 9 J" ----

def test_kinetic_energy_extracts_and_confirms():
    for t in ["a 2 kg object at 3 m/s has kinetic energy 9 J",
              "a 10 kg mass at 2 m/s has kinetic energy of 20 joules"]:
        assert "kinetic_energy" in _extractors(t), t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_kinetic_energy_catches_a_wrong_claim():
    res = audit("a 2 kg object at 3 m/s has kinetic energy 10 J", CFG, seal=False)  # 9, not 10
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_kinetic_energy_zero_false_positives():
    for t in ["a 2 kg bag of flour on the shelf", "I ran at 3 m/s and felt full of energy"]:
        assert "kinetic_energy" not in _extractors(t), t


# ---- rectangle area / perimeter (2026-09-24): "a rectangle 4 by 6 has area 24" ----

def test_rectangle_extracts_and_confirms():
    for t in ["a rectangle 4 by 6 has area 24", "a rectangle 4 by 6 has perimeter 20",
              "a rectangle measuring 5 by 5 has an area of 25"]:
        assert "rectangle" in _extractors(t), t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_rectangle_catches_a_wrong_claim():
    res = audit("a rectangle 4 by 6 has area 30", CFG, seal=False)   # 24, not 30
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_rectangle_zero_false_positives():
    """Two dimensions AND an area/perimeter claim are required; dimensions alone, or none, extract
    nothing (a miss stays a miss)."""
    for t in ["a rectangle 4 by 6 is in the corner of the room",   # dims but no area/perimeter claim
              "the golden rectangle has a pleasing shape"]:        # no numbers at all
        assert "rectangle" not in _extractors(t), t


# ---- 1D kinematics (2026-09-24): "starting at 5 m/s, accelerating at 2 m/s^2 for 3 s, travels 24 m" ----

def test_kinematics_extracts_and_confirms():
    for t in ["starting at 5 m/s and accelerating at 2 m/s^2 for 3 s covers 24 m",
              "starting at 10 m/s and accelerating at 4 m/s^2 for 2 s travels 28 m"]:
        assert "kinematics" in _extractors(t), t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_kinematics_catches_a_wrong_claim():
    res = audit("starting at 5 m/s and accelerating at 2 m/s^2 for 3 s covers 25 m",
                CFG, seal=False)   # d = 5*3 + 0.5*2*9 = 24, not 25
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_kinematics_zero_false_positives():
    """The full v0-a-t-distance chain (four SI units in order) is required; a bare velocity or
    acceleration mention extracts nothing."""
    for t in ["starting at 5 m/s we talked for a while",         # v0 only, no accel/time/distance
              "accelerating at 2 m/s^2 down the hill was fun"]:  # no start velocity or distance
        assert "kinematics" not in _extractors(t), t


# ---- sphere volume / surface area (2026-09-25): "a sphere of radius 3 has volume 113.1" ----

def test_sphere_extracts_and_confirms():
    for t in ["a sphere of radius 3 has volume 113.1",
              "a sphere of radius 5 has surface area 314.16"]:
        assert "sphere" in _extractors(t), t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_sphere_catches_a_wrong_claim():
    res = audit("a sphere of radius 3 has volume 120", CFG, seal=False)   # ~113.1, not 120
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_sphere_zero_false_positives():
    for t in ["the sphere of influence had no radius", "a sphere of radius 3 has real beauty"]:
        assert "sphere" not in _extractors(t), t


# ---- cube volume / surface area (2026-09-25): "a cube with side 3 has volume 27" ----

def test_cube_extracts_and_confirms():
    for t in ["a cube with side 3 has volume 27", "a cube of edge 4 has surface area 96"]:
        assert "cube" in _extractors(t), t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_cube_catches_a_wrong_claim():
    res = audit("a cube with side 3 has volume 30", CFG, seal=False)   # 27, not 30
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_cube_zero_false_positives():
    """Side/edge phrasing only, so the cube ROOT of a number is never mistaken for a cube solid."""
    for t in ["the cube root of 27 is 3", "a cube of sugar sweetened the coffee"]:
        assert "cube" not in _extractors(t), t


# ---- cylinder volume (2026-09-25): "a cylinder of radius 3 and height 5 has volume 141.37" ----

def test_cylinder_extracts_and_confirms():
    for t in ["a cylinder of radius 3 and height 5 has volume 141.37",
              "a cylinder with radius 2 and height 10 has volume 125.66"]:
        assert "cylinder" in _extractors(t), t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_cylinder_catches_a_wrong_claim():
    res = audit("a cylinder of radius 3 and height 5 has volume 150", CFG, seal=False)  # ~141.37
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_cylinder_zero_false_positives():
    for t in ["the engine has six cylinders", "a cylinder of compressed air stood in the corner"]:
        assert "cylinder" not in _extractors(t), t


# ---- triangle inequality (2026-09-25): a BOOLEAN claim, both polarities read explicitly ----

def test_triangle_inequality_extracts_and_confirms():
    for t in ["sides 3, 4, and 5 form a valid triangle",       # valid, claimed valid
              "sides 1, 2, and 10 cannot form a triangle",      # invalid, claimed invalid
              "a triangle with sides 6, 8, and 10 is valid"]:   # valid, claimed valid
        assert "triangle_inequality" in _extractors(t), t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_triangle_inequality_catches_a_wrong_claim():
    res = audit("sides 1, 2, and 10 form a valid triangle", CFG, seal=False)  # 1+2 < 10, not valid
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_triangle_inequality_catches_a_wrong_negative():
    res = audit("sides 3, 4, and 5 cannot form a triangle", CFG, seal=False)  # 3,4,5 IS valid
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_triangle_inequality_zero_false_positives():
    """A boolean claim needs an explicit validity verdict; sides with no verdict, or 'triangle' used
    figuratively, extract nothing (a miss stays a miss)."""
    for t in ["a triangle with sides 3, 4, and 5",              # no verdict
              "the love triangle had three sides to it",         # figurative, no number list
              "sides 3, 4, and 5 of the argument were weak"]:    # no triangle/valid/form verdict
        assert "triangle_inequality" not in _extractors(t), t


# ---- combinations / permutations (2026-09-25): "5 choose 2 is 10", "P(5,2) = 20" ----

def test_combinations_extracts_and_confirms():
    for t in ["5 choose 2 is 10", "C(6,2) = 15",
              "the number of combinations of 5 things taken 2 at a time is 10"]:
        assert "combinations" in _extractors(t), t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_combinations_catches_a_wrong_claim():
    res = audit("5 choose 2 is 12", CFG, seal=False)   # C(5,2)=10, not 12
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_combinations_zero_false_positives():
    for t in ["choose 2 of the 5 boxes on the shelf", "I had to choose between 2 and 5 options"]:
        assert "combinations" not in _extractors(t), t


def test_permutations_extracts_and_confirms():
    for t in ["P(5,2) = 20", "5 permute 2 is 20",
              "the number of permutations of 5 things taken 2 at a time is 20"]:
        assert "permutations" in _extractors(t), t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_permutations_catches_a_wrong_claim():
    res = audit("P(5,2) = 25", CFG, seal=False)   # P(5,2)=20, not 25
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_permutations_zero_false_positives():
    for t in ["the permutations of the schedule were endless", "P was 5, 2 short of the goal"]:
        assert "permutations" not in _extractors(t), t


# ---- propositional logic (2026-09-25, 3a): a bounded parser → formal_logic (structured layer) ----

def test_propositional_logic_extracts_and_confirms():
    for t in ["P or not P is a tautology",           # excluded middle
              "P and not P is a contradiction",        # non-contradiction
              "P and Q is satisfiable"]:               # a model exists
        assert "propositional_logic" in _extractors(t), t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_propositional_logic_catches_a_wrong_claim():
    res = audit("P and not P is a tautology", CFG, seal=False)   # it is a contradiction, not a tautology
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_propositional_logic_catches_a_wrong_negative():
    res = audit("P or not P is not a tautology", CFG, seal=False)  # it IS a tautology
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_propositional_logic_zero_false_positives():
    """The clause must parse wholly as a proposition; ordinary prose (and the English words A/I) never
    becomes a formula — a miss stays a miss."""
    for t in ["the plan is a contradiction of everything we stand for",   # 'plan' is not a variable
              "the requirement is satisfiable by any vendor",              # 'requirement' is not a var
              "I is a tautology of the self"]:                             # 'I' is excluded (pronoun)
        assert "propositional_logic" not in _extractors(t), t


# ---- element FACTS (2026-09-25, fact-verifier): a lookup claim becomes a verdict ----

def test_element_fact_extracts_and_confirms():
    for t in ["the atomic number of carbon is 6",
              "oxygen has an atomic number of 8",
              "the chemical symbol for gold is Au"]:
        assert "element_fact" in _extractors(t), t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_element_fact_catches_a_wrong_atomic_number():
    res = audit("the atomic number of carbon is 7", CFG, seal=False)   # carbon is 6
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_element_fact_catches_a_wrong_symbol():
    res = audit("the symbol for gold is Ag", CFG, seal=False)          # Ag is silver, Au is gold
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_element_fact_zero_false_positives():
    """The name must be a real element; ordinary prose in the same shape extracts nothing."""
    for t in ["the atomic number of the meeting is 5",
              "the symbol for freedom is a flag",
              "the atomic number of attendees is 12"]:
        assert "element_fact" not in _extractors(t), t


# ---- sequence FACTS (2026-09-25, fact-verifier): "the Nth prime/Fibonacci/triangular is X" ----

def test_sequence_fact_extracts_and_confirms():
    for t in ["the 5th prime is 11",
              "the 7th Fibonacci number is 13",
              "the 4th triangular number is 10"]:
        assert "sequence_fact" in _extractors(t), t
        assert audit(t, CFG, seal=False)["held"] == 1, t


def test_sequence_fact_catches_a_wrong_term():
    res = audit("the 5th prime is 13", CFG, seal=False)   # 5th prime is 11, not 13
    assert res["broken"] == 1 and res["results"][0]["status"] == "MISMATCH"


def test_sequence_fact_zero_false_positives():
    """The ordinal must name one of the supported sequences; ordinary "Nth X" prose extracts nothing."""
    for t in ["the 5th person is 11", "the 3rd time is the charm", "the 2nd item is 10"]:
        assert "sequence_fact" not in _extractors(t), t


if __name__ == "__main__":
    import pytest
    sys.exit(int(pytest.main([__file__, "-q"])))
