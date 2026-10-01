"""The free-text constants door must never confirm a value under a WRONG unit — the cardinal pin.

2026-10-01, the Fable review: "the speed of light is 299792458 km/s" (false — 1000x c) and
"... 299792458 mph" each earned a sealed HOLDS through POST /verify's free-text door, because the
extractor DROPPED a non-matching stated unit and checked the bare value, which is correct. That is
the one failure the engine must never make. Now a stated unit that does not normalize-match the
constant's own unit is DECLINED (unchecked) — never confirmed on the value alone, and never falsely
BROKEN either (the structured door checks units deliberately). Run alone or with the suite."""
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


def test_an_unmatched_unit_is_declined_not_broken():
    # the decline is the honest middle: neither a false HOLDS nor a false BROKEN
    r = audit("The speed of light is 299792458 km/s.", CFG, seal=False)
    assert r["verdict"] not in ("HOLDS", "BROKEN")
    assert r.get("held", 0) == 0 and r.get("broken", 0) == 0


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]:
        fn()
        print("  ok ", fn.__name__)
    print("constant-unit cardinal pins passed.")
