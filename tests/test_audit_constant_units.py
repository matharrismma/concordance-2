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


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]:
        fn()
        print("  ok ", fn.__name__)
    print("constant-unit cardinal pins passed.")
