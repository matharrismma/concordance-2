"""The free-text constants door must never confirm a value under a WRONG unit — the cardinal pin.

2026-10-01, the Fable review: "the speed of light is 299792458 km/s" (false — 1000x c) and
"... 299792458 mph" each earned a sealed HOLDS through POST /verify's free-text door, because the
extractor DROPPED a non-matching stated unit and checked the bare value, which is correct. That is
the one failure the engine must never make. Now a stated unit that does not normalize-match the
constant's own unit was DECLINED (unchecked). Since 2026-10-03 (R4) the SI normalizer CONVERTS a known unit of
the right dimension and judges the value, MISMATCHES a wrong dimension, and still DECLINES an unknown unit —
never a false HOLDS, never a false BROKEN. Run alone or with the suite."""
from concordance.audit import audit
from concordance.config import EngineConfig

CFG = EngineConfig("secular")


def _verdict(text: str) -> str:
    return audit(text, CFG, seal=False)["verdict"]


def test_a_right_value_under_a_wrong_unit_never_holds():
    # CARDINAL: these are false claims; a HOLDS here is a sealed falsehood.
    assert _verdict("The speed of light is 299792458 km/s.") != "HOLDS"
    assert _verdict("The speed of light is 299792458 mph.") != "HOLDS"
    assert _verdict("The speed of light is 299792458 furlongs per fortnight.") != "HOLDS"


def test_the_right_unit_and_a_bare_value_still_hold():
    assert _verdict("The speed of light is 299792458 m/s.") == "HOLDS"
    assert _verdict("The speed of light is 299792458.") == "HOLDS"      # no unit stated -> value checked


def test_a_wrong_value_is_still_broken():
    assert _verdict("The speed of light is 300000000 m/s.") == "BROKEN"


def test_a_wrong_value_under_a_known_unit_is_now_broken():
    """R4 (2026-10-03): with the SI normalizer a known unit of the right dimension is CONVERTED and the value
    judged — the commonest phrasing of a wrong constant finally gets its verdict."""
    assert _verdict("The speed of light is 299792458 km/s.") == "BROKEN"      # 1000x c
    assert _verdict("The speed of light is 150000 km/s.") == "BROKEN"
    assert _verdict("The speed of light is 299792458 mph.") == "BROKEN"


def test_a_right_value_in_another_spelling_or_unit_holds():
    assert _verdict("The speed of light is 299792.458 km/s.") == "HOLDS"
    assert _verdict("The speed of light is 299792458 m s^-1 in vacuum.") == "HOLDS"
    assert _verdict("The speed of light is 299792458 m/s in a vacuum.") == "HOLDS"
    assert _verdict("The speed of light is 299792458 meters per second.") == "HOLDS"
    assert _verdict("The gas constant is 8.314 J K^-1 mol^-1.") == "HOLDS"
    assert _verdict("The gravitational constant is 6.674e-11 N m^2/kg^2.") == "HOLDS"


def test_a_preposition_after_the_number_is_not_a_unit():
    # "in" is inches to a parser and a preposition to a person; the bare value is what is checked
    assert _verdict("The speed of light is 299792458 in a vacuum.") == "HOLDS"


def test_a_wrong_dimension_is_broken_and_an_unknown_unit_is_declined():
    assert _verdict("The speed of light is 300000000 kg.") == "BROKEN"        # c is not a mass
    r = audit("The speed of light is 299792458 furlongs per fortnight.", CFG, seal=False)
    assert r["verdict"] not in ("HOLDS", "BROKEN")                             # unknown: declined, not judged
    assert r.get("held", 0) == 0 and r.get("broken", 0) == 0


def test_the_exact_codata_value_is_never_eaten_by_the_airlock():
    """2026-10-03, the 137 slide: "the fine structure constant is 0.0072973525693" came back BROKEN through
    POST /verify — the airlock's card rule took the 13 digits after the point (they pass Luhn) for an
    account number and the claim became "… is 0". The decimal is a number, not an account."""
    from concordance import redact
    clean, held = redact.redact("the fine structure constant is 0.0072973525693")
    assert clean == "the fine structure constant is 0.0072973525693" and held == {}
    clean, held = redact.redact("card 4532015112830366 on file")               # a real card still goes
    assert "[CARD_1]" in clean and held
    assert _verdict("The fine structure constant is 0.0072973525693.") == "HOLDS"
    assert _verdict("The fine structure constant is 0.00729927.") == "BROKEN"   # 1/137 is a rounding, not the value


def test_a_declarative_primality_claim_is_checkable():
    assert _verdict("137 is a prime number.") == "HOLDS"
    assert _verdict("138 is prime.") == "BROKEN"
    assert _verdict("137 is not prime.") == "BROKEN"
    assert _verdict("91 is composite.") == "HOLDS"


def test_division_and_divisor_counts_are_checkable():
    """2026-10-03: "72 / 2 = 36" was NOTHING_TO_CHECK while "72 * 2 = 144" held; "the number of divisors of 12 is 6"
    had no verifier. Twelve is the smallest number with six divisors; sixty has twelve — the reason they organize
    wholes, and the honest answer to "is the universe base 12": a base is notation; the divisor count is arithmetic."""
    assert _verdict("72 / 2 = 36.") == "HOLDS" and _verdict("72 / 2 = 35.") == "BROKEN"
    assert _verdict("144 ÷ 12 = 12.") == "HOLDS" and _verdict("72 divided by 2 is 36.") == "HOLDS"
    assert _verdict("the number of divisors of 12 is 6.") == "HOLDS"
    assert _verdict("12 has 6 divisors.") == "HOLDS" and _verdict("60 has twelve divisors.") == "HOLDS"
    assert _verdict("the number of divisors of 12 is 5.") == "BROKEN"
    assert _verdict("10 has 6 divisors.") == "BROKEN"                        # 1, 2, 5, 10
    r = audit("1 / 0 = 0.", CFG, seal=False)
    assert r["verdict"] not in ("HOLDS", "BROKEN")                          # division by zero: a gap, never a verdict


def test_a_chain_is_taken_whole_never_from_the_middle():
    """2026-10-03, cardinal: "2 * 2 * 3 = 12" was BROKEN — the pair extractor took "2 * 3 = 12" out of the
    middle and judged a true claim false. A chain is taken whole; a chain that starts mid-expression is
    left alone (a miss, never a verdict)."""
    assert _verdict("2 * 2 * 3 = 12.") == "HOLDS" and _verdict("12 * 12 * 1000 = 144,000.") == "HOLDS"
    assert _verdict("2 x 3 x 4 = 24.") == "HOLDS" and _verdict("2 * 3 * 4 = 25.") == "BROKEN"
    assert _verdict("100 / 5 / 2 = 10.") == "HOLDS" and _verdict("100 / 5 / 2 = 40.") == "BROKEN"
    assert _verdict("1 + 2 + 3 = 6.") == "HOLDS"
    for mixed in ("2 + 3 * 4 = 14.", "10 - 2 * 3 = 4.", "2 * 3 + 4 = 10.", "100 / 5 + 2 = 22."):
        assert audit(mixed, CFG, seal=False)["verdict"] != "BROKEN", mixed  # true claims; never judged false
    assert _verdict("64 mod 9 is 1.") == "HOLDS" and _verdict("64 mod 9 is 2.") == "BROKEN"


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]:
        fn()
        print("  ok ", fn.__name__)
    print("constant-unit cardinal pins passed.")
