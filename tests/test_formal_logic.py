"""Unit-pin the formal_logic verifier (A2, 2026-10-06). 'A or not A' is a tautology (law of excluded
middle). A false tautology claim is caught; a missing field is NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import formal_logic as FL


def test_tautology():
    assert FL.verify_tautology({"formula": "A or not A", "variables": ["A"], "claimed_tautology": True}).status == "CONFIRMED"
    assert FL.verify_tautology({"formula": "A or not A", "variables": ["A"], "claimed_tautology": False}).status == "MISMATCH"
    assert FL.verify_tautology({}).status == "NOT_APPLICABLE"


# ---- formal_logic.minimal_form (issue #12): minimality decided by Quine-McCluskey + exhaustive cover, exact <= 4 vars

_PQ = ["p", "q"]
_F = "(p&q)|(p&~q)"       # absorbs to p: one product term


def test_minimal_form_confirmed_with_one_term():
    r = FL.verify_minimal_form({"variables": _PQ, "formula": _F, "claimed_minimal": "p", "claimed_minimal_terms": 1})
    assert r.status == "CONFIRMED"
    assert r.data["minimum_terms"] == 1 and r.data["claimed_terms"] == 1 and r.data["minimum_cover"] == ["p"]
    # the keyword spelling is the same claim
    assert FL.verify_minimal_form({"variables": _PQ, "formula": "(p and q) or (p and not q)", "claimed_minimal": "p"}).status == "CONFIRMED"


def test_minimal_form_rejects_a_non_minimal_cover_and_names_the_minimum():
    r = FL.verify_minimal_form({"variables": _PQ, "formula": _F, "claimed_minimal": _F})
    assert r.status == "MISMATCH"
    assert r.data["minimum_terms"] == 1 and r.data["claimed_terms"] == 2 and "minimum is 1" in r.detail
    # the three-variable consensus term is redundant: (p&q)|(~p&r)|(q&r) minimizes to two terms
    r = FL.verify_minimal_form({"variables": ["p", "q", "r"], "formula": "(p&q)|(~p&r)|(q&r)", "claimed_minimal": "(p&q)|(~p&r)|(q&r)"})
    assert r.status == "MISMATCH" and r.data["minimum_terms"] == 2
    assert FL.verify_minimal_form({"variables": ["p", "q", "r"], "formula": "(p&q)|(~p&r)|(q&r)", "claimed_minimal": "(p&q)|(~p&r)"}).status == "CONFIRMED"
    # a stated term count that misdescribes the claim is a mismatch too
    assert FL.verify_minimal_form({"variables": _PQ, "formula": _F, "claimed_minimal": "p", "claimed_minimal_terms": 2}).status == "MISMATCH"


def test_minimal_form_rejects_a_non_equivalent_claim():
    r = FL.verify_minimal_form({"variables": _PQ, "formula": _F, "claimed_minimal": "q"})
    assert r.status == "MISMATCH" and r.data["equivalent"] is False and "not equivalent" in r.detail
    # XOR needs two terms; a claimed one-term form is simply not equivalent
    assert FL.verify_minimal_form({"variables": _PQ, "formula": "p ^ q", "claimed_minimal": "p"}).status == "MISMATCH"
    assert FL.verify_minimal_form({"variables": _PQ, "formula": "p ^ q", "claimed_minimal": "(p&~q)|(~p&q)"}).status == "CONFIRMED"


def test_minimal_form_is_bounded_at_four_variables():
    five = ["a", "b", "c", "d", "e"]
    r = FL.verify_minimal_form({"variables": five, "formula": "a&b&c&d&e", "claimed_minimal": "a&b&c&d&e"})
    assert r.status == "NOT_APPLICABLE" and "4 variables" in r.detail and "5 declared" in r.detail
    # four variables are decided exactly
    r = FL.verify_minimal_form({"variables": ["a", "b", "c", "d"], "formula": "(a&b)|(a&~b&c)|(a&~b&~c&d)", "claimed_minimal": "(a&b)|(a&c)|(a&d)"})
    assert r.status == "CONFIRMED" and r.data["minimum_terms"] == 3


def test_minimal_form_declines_a_claim_that_is_not_two_level():
    for bad in ("~(p&q)", "p >> q", "p ^ q", "(p|q)&(p|~q)", "~(~p|~q)|r"):
        r = FL.verify_minimal_form({"variables": ["p", "q", "r"], "formula": "p", "claimed_minimal": bad})
        assert r.status == "NOT_APPLICABLE", bad
    assert FL.verify_minimal_form({"variables": _PQ, "formula": _F, "claimed_minimal": "p&z"}).status == "NOT_APPLICABLE"   # undeclared
    assert FL.verify_minimal_form({"formula": _F}).status == "NOT_APPLICABLE"                                            # no claim
    # the degenerate forms: a tautology's minimum is the empty product, a contradiction's the empty sum
    assert FL.verify_minimal_form({"variables": _PQ, "formula": "p|~p", "claimed_minimal": "True"}).data["minimum_terms"] == 1
    assert FL.verify_minimal_form({"variables": _PQ, "formula": "p&~p", "claimed_minimal": "False"}).data["minimum_terms"] == 0


def test_minimal_form_is_wired_into_run():
    out = FL.run({"LOGIC_VERIFY": {"variables": _PQ, "formula": _F, "claimed_minimal": "p"}})
    assert [x.name for x in out] == ["formal_logic.minimal_form"] and out[0].status == "CONFIRMED"
