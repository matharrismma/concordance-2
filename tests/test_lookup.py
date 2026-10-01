"""The Lookup — the found-value twin of verify, consolidated like verify (one tool, one kind at a
time). Every value is computed from the SAME offline PD data the verifiers hold, so a lookup and a
verify agree by construction. found=False is an honest miss, never a guess."""
from concordance import lookup as L


def test_molar_mass_matches_what_the_verifier_computes():
    r = L.lookup("molar_mass", {"formula": "H2O"})
    assert r["found"] and abs(r["value"] - 18.015) < 0.01 and r["unit"] == "g/mol"
    # the lookup and the verifier agree, by construction (one compute)
    from concordance.verifiers import periodic_table as pt
    assert pt.verify_molar_mass({"formula": "H2O", "claimed_molar_mass": r["value"]}).status == "CONFIRMED"


def test_element_lookup_by_symbol_name_number():
    assert L.lookup("element", {"symbol": "Fe"})["value"]["name"] == "iron"
    assert L.lookup("element", {"name": "gold"})["value"]["symbol"] == "Au"
    assert L.lookup("element", {"atomic_number": 1})["value"]["symbol"] == "H"


def test_unit_conversion():
    r = L.lookup("convert", {"value": 5, "from": "km", "to": "mi"})
    assert r["found"] and "mi" in r["value"]
    rt = L.lookup("convert", {"value": 350, "from": "fahrenheit", "to": "celsius"})
    assert rt["found"] and ("176" in rt["value"])


def test_unknown_kind_and_bad_input_are_honest_misses_not_guesses():
    bad = L.lookup("teleport", {})
    assert bad["found"] is False and "kinds" in bad          # lists the real kinds
    assert L.lookup("element", {"symbol": "Xx"})["found"] is False
    assert L.lookup("molar_mass", {"formula": "Ca(OH)2"})["found"] is False  # parentheses unsupported -> miss, not guess


def test_points_to_verify_as_its_twin():
    assert "verify" in L.lookup("molar_mass", {"formula": "H2O"})["see_also"]


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]:
        fn()
        print("  ok ", fn.__name__)
    print("lookup tests passed.")
