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
