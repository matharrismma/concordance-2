"""FACT FIND (R5): when nothing in a claim is computable, the CHECK door answers with a found fact that agrees
or disagrees, with on-subject cards only, or with 'not held yet' and a want offered — never unrelated cards,
never a computed verdict, never a receipt."""
import os
import tempfile

os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp(prefix="nh-ff-"))

from concordance import factfind  # noqa: E402


def test_an_elements_standard_atomic_weight_is_a_found_fact_that_agrees_or_not():
    ff = factfind.find_fact("the atomic mass of iron is 55.845")
    assert ff["subject"] == "iron" and ff["symbol"] == "Fe" and ff["field"] == "atomic_mass"
    assert ff["value"] == 55.845 and ff["claimed"] == 55.845 and ff["agrees"] is True
    assert "IUPAC" in ff["source"]
    assert factfind.find_fact("iron's atomic weight is 60")["agrees"] is False
    assert factfind.find_fact("Au has 79 protons")["agrees"] is True                       # by symbol, exact
    assert factfind.find_fact("gold has 80 protons")["agrees"] is False


def test_a_property_the_keeping_lacks_is_named_as_not_held():
    ff = factfind.find_fact("iron melts at 1538 C")
    assert ff == {"kind": "element", "subject": "iron", "symbol": "Fe", "property": "melts", "held": False, "source": None}
    assert factfind.find_fact("the boiling point of gold is 2970 C")["held"] is False
    assert factfind.find_fact("the capital of France is Paris") is None                    # no element
    assert factfind.find_fact("iron is a metal") is None                                     # no property
    assert factfind.number_in("the atomic mass of iron is 55.845") == 55.845 and factfind.number_in("none") is None


def test_the_fallback_hands_back_only_on_subject_cards():
    cards = [{"id": "c_iron", "title": "Iron and steel in the forge", "body": "x", "shelf": "trades"},
             {"id": "c_phase", "title": "Phase theory", "body": "melting", "shelf": "theories"},
             {"id": "c_lex", "title": "h4127", "body": "iron", "shelf": "lexicon"}]
    out = factfind.verify_fallback("iron melts at 1538 C", search=lambda q, limit=3: cards)
    assert "found_fact" not in out and [c["id"] for c in out["found"]] == ["c_iron"]
    assert "FOUND and cited" in out["note"] and "want" not in out


def test_the_fallback_says_not_held_and_offers_a_want_when_nothing_names_the_subject():
    cards = [{"id": "c_phase", "title": "Phase theory", "body": "melting", "shelf": "theories"},
             {"id": "c_lex", "title": "h4127", "body": "iron", "shelf": "lexicon"}]
    out = factfind.verify_fallback("iron melts at 1538 C", search=lambda q, limit=3: cards)
    assert out["found"] == [] and out["want"]["query"] == "iron melts"
    assert "does not yet hold a sourced table for the melts of iron" in out["note"] and "nothing is invented" in out["note"]
    assert "want_open" in out["want"]["how"]
    out = factfind.verify_fallback("the capital of Ruritania is Strelsau", search=lambda q, limit=3: [])
    assert out["found"] == [] and out["want"]["query"].startswith("the capital of Ruritania")
    out = factfind.verify_fallback("the atomic mass of iron is 55.845", search=lambda q, limit=3: [])
    assert out["found_fact"]["agrees"] is True and "not a computed verdict" in out["note"]
    out = factfind.verify_fallback("x", search=lambda q, limit=3: (_ for _ in ()).throw(RuntimeError("down")))
    assert out["found"] == [] and "want" in out                                                # a failing search never breaks it


# ---- the sourced tables of 2026-10-07: half-lives (ENSDF) and normal boiling points (CRC) ----

def test_a_half_life_is_a_found_fact_from_the_sourced_table():
    ff = factfind.find_fact("the half life of carbon-14 is 5730 years")
    assert ff["subject"] == "carbon-14" and ff["field"] == "half_life" and ff["unit"] == "y"
    assert ff["value"] == 5700.0 and ff["uncertainty"] == 30.0 and "ENSDF" in ff["source"]
    assert ff["claimed"] == 5730.0 and ff["stated_sigfigs"] == 3 and ff["agrees"] is True   # bands overlap: 30 <= 30 + 5
    assert ff["lookup"] == {"kind": "half_life", "params": {"isotope": "carbon-14"}}
    assert factfind.find_fact("the half life of carbon-14 is 7730 years")["agrees"] is False
    assert factfind.find_fact("the half-life of tritium is 12.32 years")["subject"] == "hydrogen-3"
    co = factfind.find_fact("cobalt-60 has a half-life of 5.27 years")           # the table is in days; the claim in years
    assert co["unit"] == "d" and co["agrees"] is True
    u = factfind.find_fact("uranium-238 has a half-life of 4.468 billion years")
    assert u["claimed"] == 4.468e9 and u["agrees"] is True
    assert factfind.find_fact("14C has a half-life of 5,700 y")["agrees"] is True
    # one figure earns no window of its own: compared at the source's band alone (the verifiers' "3e8" rule)
    one = factfind.find_fact("the half-life of iodine-131 is 8 days")
    assert one["stated_sigfigs"] == 1 and one["agrees"] is False
    # found, nothing claimed -> nothing compared
    q = factfind.find_fact("what is the half-life of C-14")
    assert q["value"] == 5700.0 and q["claimed"] is None and q["agrees"] is None
    # an isotope the table lacks is named as not held — the isotope, and the table
    sr = factfind.find_fact("the half-life of strontium-90 is 28.8 years")
    assert sr["held"] is False and sr["subject"] == "strontium-90" and sr["table"] == "half_life"
    out = factfind.verify_fallback("the half-life of strontium-90 is 28.8 years", search=lambda q, limit=3: [])
    assert "half-life table holds no entry for strontium-90" in out["note"] and out["want"]["query"] == "strontium-90 half-life"
    out = factfind.verify_fallback("the half life of carbon-14 is 5730 years", search=lambda q, limit=3: [])
    assert out["found_fact"]["agrees"] is True and "agrees with the claimed 5730.0 years" in out["note"] and "no receipt" in out["note"]


def test_a_normal_boiling_point_is_a_found_fact_from_the_sourced_table():
    ff = factfind.find_fact("water boils at 100 C at sea level")
    assert ff["subject"] == "water" and ff["field"] == "boiling_point_C" and ff["value"] == 99.97 and "CRC" in ff["source"]
    assert ff["stated_sigfigs"] == 1 and ff["agrees"] is True        # 100 lies inside 99.97 +/- 0.05; one figure adds nothing
    assert factfind.find_fact("water boils at 90 C at sea level")["agrees"] is False
    assert factfind.find_fact("water boils at 212 F")["agrees"] is True                # Fahrenheit, converted
    assert factfind.find_fact("water boils at 373.15 K")["agrees"] is True             # Kelvin, converted
    assert factfind.find_fact("the boiling point of ethanol is 78.3 C")["agrees"] is True
    assert factfind.find_fact("ethanol boils at 88 C")["agrees"] is False
    assert factfind.find_fact("the boiling point of mercury is 356.6 C")["agrees"] is True   # an element: the table first
    assert factfind.find_fact("ethyl alcohol boils at 78 degrees C")["subject"] == "ethyl alcohol"
    # not the NORMAL boiling point, or not a pure substance, or two substances -> not this table: nothing found
    assert factfind.find_fact("water boils at 99.6 C at 1 bar") is None
    assert factfind.find_fact("sea water boils at 100 C") is None
    assert factfind.find_fact("water boils at 100 C and ethanol at 78 C") is None
    # a substance the table lacks falls through to the old honest answer (gold is deliberately not tabled)
    assert factfind.find_fact("the boiling point of gold is 2970 C")["held"] is False
    out = factfind.verify_fallback("water boils at 100 C at sea level", search=lambda q, limit=3: [])
    assert out["found_fact"]["agrees"] is True and "agrees with the claimed 100.0 degC" in out["note"]
    assert "one figure earns no window" in out["note"] and "no receipt" in out["note"]


def test_lookup_kinds_open_the_same_tables():
    from concordance import lookup
    assert {"half_life", "boiling_point"} <= set(lookup.kinds())
    hl = lookup.lookup("half_life", {"isotope": "C-14"})
    assert hl["found"] and hl["value"] == 5700.0 and hl["unit"] == "y" and hl["isotope"] == "carbon-14"
    assert lookup.lookup("half_life", {"isotope": "strontium-90"})["found"] is False
    bp = lookup.lookup("boiling_point", {"substance": "water"})
    assert bp["found"] and bp["value"] == 99.97 and bp["unit"] == "degC"
    assert lookup.lookup("boiling_point", {"substance": "gold"})["found"] is False
