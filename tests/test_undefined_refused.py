"""A value with no meaning the parser builds never leaves the node that built it.

sympy answers a division by zero and some function poles with zoo, nan, AccumBounds or an oo of its own and carries on,
and a later node can collapse that into an ordinary number: the reciprocal of zoo is 0. So a claim through such a step
read HOLDS. mathematics._refuse_no_meaning tests each built value at its own node, so a refusal can never be collapsed.

Every form below reads a refusal: that is what these tests prove, and each is a false claim only if it is read. What the
rule does not close is named by the run's goal and filed as wants: a deferred object sympy has not yet evaluated, a pole
at a claimed variable value, indeterminate forms sympy settles by convention, an evaluator's divergent answer under a
written bound, and float absorption. A deferred object is pinned at the parser here and in no mode, so a later fix moves
it on purpose. Names the fix adds are read inside the tests, so the file collects at the step's base.
"""
from __future__ import annotations

import json
import math
import random
from fractions import Fraction

import pytest
import sympy

from concordance.config import EngineConfig
from concordance.derivation import verify_derivation, verify_domain
from concordance.mcp.http import handle_http
from concordance.verifiers import mathematics as M
from concordance.verifiers import physics as P
from concordance.web import api

CONFIG = EngineConfig("secular")
pytestmark = pytest.mark.filterwarnings("ignore")


@pytest.fixture(autouse=True)
def _tables(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CONCORDANCE_CAS_DIR", str(tmp_path / "cas"))
    M._ensure_sympy()
    P._ensure_sympy()


def read(text, names=None, **kw):
    return M.parse_expression(text, names, **kw)


def refused(text, names=None, **kw):
    with pytest.raises(M.ExpressionRefused):
        read(text, names, **kw)


STATUS_TO_VERDICT = {"CONFIRMED": "HOLDS", "MISMATCH": "BROKEN", "ERROR": "SYSTEM_ERROR", "NOT_APPLICABLE": "INCOMPLETE"}


def route(spec, domain="mathematics"):
    """Through the door, with sealing off. derivation.py here has no MATH_VERIFY branch, so /verify does not reach
    mathematics.run: a MATH_VERIFY packet reads through verify_domain, the call V3's branch makes, and its status is put
    in the words of a verdict. One core keeps the sibling rule there, though no door here reaches it."""
    if "MATH_VERIFY" in spec:
        return {"verdict": STATUS_TO_VERDICT[verify_domain("mathematics", spec)["status"]]}
    steps = [{"id": "r", "domain": domain, "spec": spec}]
    status, out = api.dispatch("POST", "/verify", {"seal": "0"}, {"steps": steps}, CONFIG)
    assert status == 200, out
    return out


def post(mode, params):
    return route({"mode": mode, "params": params})


# Each mode that reads a text: the params that would read HOLDS if the form collapsed to 0, and that mode's reading of a
# refusal, which the rule keeps: a refusal is a member of _PARSE_ERRORS.
MODES = {
    "equality": (lambda t: {"expr_a": t, "expr_b": "0"}, "INCOMPLETE"),
    "solve": (lambda t: {"equation": f"y + ({t}) = 3", "variable": "y", "claimed_solutions": ["3"]}, "INCOMPLETE"),
    "derivative": (lambda t: {"function": f"x + ({t})", "variable": "x", "claimed_derivative": "1"}, "INCOMPLETE"),
    "integral": (lambda t: {"integrand": f"1 + ({t})", "variable": "x", "claimed_antiderivative": "x"}, "INCOMPLETE"),
    "limit": (lambda t: {"function": f"x + ({t})", "variable": "x", "point": "1", "claimed_limit": "1"}, "INCOMPLETE"),
    "numeric": (lambda t: {"numeric_expr": t, "claimed_value": 0}, "SYSTEM_ERROR"),
    "inequality": (lambda t: {"lhs": t, "rhs": "0", "op": "<="}, "SYSTEM_ERROR"),
    "system": (lambda t: {"equations": [f"y + ({t}) = 3"], "variables": ["y"], "claimed_solution": {"y": 3}}, "SYSTEM_ERROR"),
    "calc_chain": (lambda t: {"calc_steps": [f"{t}=0"]}, "BROKEN"),
}

FORMS = [
    "1/(1/0)",                                  # a reciprocal of a reciprocal of zero, spelled literally
    "1/(1/(1-1))",                              # of a difference that is zero
    "igcd(1,1)/(igcd(1,1)/igcd(0,0))",          # through an integer-returning call
    "ilcm(1,1)/(ilcm(1,1)/ilcm(0,0))",          # through another
    "1/Abs(1/0)",                               # an absolute value of such a form
    "1/Abs(igcd(1,1)/igcd(0,0))",               # and through an integer-returning call
    "1/log(0)", "1/gamma(0)",                   # a function pole sympy answers with zoo, under a reciprocal
    "1/atanh(1)", "1/acoth(1)", "1/loggamma(0)", "1/Ei(0)", "1/li(1)",   # and one it answers with oo or -oo
    "1/(1/0 + 1)",                              # the operator + through an undefined step
    "1/(2*(1/0))",                              # the operator * through one
    "0*sin(oo)", "0*cos(oo)",                   # a trigonometric function of oo
    "1/atanh(1+1/oo)", "1/atanh(1+1/inf)", "1/atanh(igcd(1,1)+1/oo)", "1/acoth(1+1/oo)",   # a written oo gone by the pole
    "1/atanh(1) + 1/oo", "1/oo + 1/atanh(1)",   # a written oo beside a pole
]


def test_each_form_is_distinct():
    assert len(FORMS) == len(set(FORMS)) == 23


@pytest.mark.parametrize("text", FORMS)
@pytest.mark.parametrize("mode", sorted(MODES))
def test_a_form_with_no_meaning_reads_each_modes_refusal(mode, text):
    params, verdict = MODES[mode]
    r = post(mode, params(text))
    assert r["verdict"] == verdict and r["verdict"] != "HOLDS", r
    assert not r.get("seal")


@pytest.mark.parametrize("text", ["1/atanh(1+0*oo)", "1/Ei(0*oo)", "1/atanh(oo/oo)", "1/atanh(1+0*inf)", "1/atanh(1) + 0*oo"])
@pytest.mark.parametrize("mode", ["equality", "numeric", "calc_chain"])
def test_a_variable_merely_named_oo_earns_nothing(mode, text):
    """The rule reads the value, never a name: here oo is a symbol, so no infinity was written and none is carried."""
    params, verdict = MODES[mode]
    r = post(mode, dict(params(text), variables=["oo", "inf"]))
    assert r["verdict"] == verdict and r["verdict"] != "HOLDS", r


def test_a_symbol_called_oo_is_a_symbol_and_never_an_infinity():
    names = {"oo": sympy.Symbol("oo")}
    assert read("oo", names) == sympy.Symbol("oo")
    assert read("oo/oo", names) == 1
    refused("atanh(oo/oo)", names)              # by a test of the name, this would pass
    refused("atanh(1+0*oo)", names)


@pytest.mark.parametrize("text", ["atanh(1+1/oo)", "atanh(1+1/inf)", "atanh(2-exp(-oo)-1)", "Ei(1/oo)", "li(1+1/oo)", "acoth(1+1/oo)"])
def test_a_written_oo_that_reduces_to_a_finite_number_licenses_nothing(text):
    """The infinity is gone by the time the pole is built, so nothing carries it in."""
    names = {"inf": sympy.oo}
    refused(text, names)


def test_the_rule_tests_built_values_through_every_container():
    x = sympy.Symbol("x")
    for bad in (sympy.zoo, sympy.nan, sympy.AccumBounds(-1, 1), x + sympy.zoo, x * sympy.nan, sympy.Tuple(1, sympy.zoo), [1, sympy.zoo],
                (1, (2, sympy.nan)), {sympy.Integer(1): sympy.zoo}, {sympy.zoo: sympy.Integer(1)}, [{sympy.Integer(1): [sympy.nan]}],
                sympy.ImmutableMatrix(((sympy.zoo, 1),)), sympy.FiniteSet(1, sympy.zoo)):
        for written, carried in ((False, False), (True, False), (False, True), (True, True)):
            with pytest.raises(M.ExpressionRefused):
                M._refuse_no_meaning(bad, written, carried)


def test_an_infinity_stands_only_written_or_carried():
    x = sympy.Symbol("x")
    for value in (sympy.oo, -sympy.oo, x + sympy.oo, sympy.Tuple(1, sympy.oo), [sympy.oo], (1, (2, -sympy.oo)), {sympy.Integer(1): sympy.oo},
                  sympy.Interval(0, sympy.oo), sympy.ImmutableMatrix(((sympy.oo, 1),))):
        with pytest.raises(M.ExpressionRefused):
            M._refuse_no_meaning(value, False, False)
        assert M._refuse_no_meaning(value, True, False) is True
        assert M._refuse_no_meaning(value, False, True) is True
    assert M._refuse_no_meaning(sympy.Integer(1), False, False) is False
    assert M._refuse_no_meaning(x, True, True) is False


def test_a_refusal_is_a_parse_error_every_mode_catches():
    with pytest.raises(M._PARSE_ERRORS):
        read("1/0")


@pytest.mark.parametrize("text", [
    "1/0", "0/0", "0*(1/0)", "(1/0)**0", "sign(1/0)", "Abs(1/0)", "Max(1/0,1)", "Min(1/0,1)", "simplify(1/(1/0))", "expand(0*(1/0))", "floor(1/0)",
    "Matrix(((1/0,1),(1,1)))", "Tuple(1/0,2)", "FiniteSet(1/0)", "Piecewise((1/0,x<1),(0,true))", "solve(x-1/0,x)", "Rational(1,0)", "Integer(1)/0",
    "oo-oo", "oo/oo", "0*oo", "1**oo", "oo%2", "sin(oo)", "cos(-oo)", "zoo", "nan", "x**nan", "x+zoo", "x*nan",
])
@pytest.mark.parametrize("rational", [False, True], ids=["plain", "rational"])
def test_no_later_node_can_collapse_a_refusal(text, rational):
    refused(text, rational=rational)


@pytest.mark.parametrize("text, value", [
    ("oo", sympy.oo), ("-oo", -sympy.oo), ("+oo", sympy.oo), ("oo+1", sympy.oo), ("2*oo", sympy.oo), ("oo*oo", sympy.oo), ("2**oo", sympy.oo),
    ("exp(oo)", sympy.oo), ("Abs(-oo)", sympy.oo), ("Max(1,oo)", sympy.oo), ("1/oo", sympy.Integer(0)), ("exp(-oo)", sympy.Integer(0)),
    ("atan(oo)", sympy.pi / 2), ("tanh(oo)", sympy.Integer(1)), ("Interval(0,oo)", sympy.Interval(0, sympy.oo)),
])
def test_a_written_oo_stays_legal(text, value):
    assert read(text) == value


def test_inf_is_written_in_mathematics_alone():
    assert M._parse("inf") is sympy.oo and M._parse("1/inf") == 0
    assert read("inf") == sympy.Symbol("inf")               # physics reads it as a symbol, as it always did


@pytest.mark.parametrize("text", ["Sum(1/k**2,(k,1,oo))", "Integral(exp(-x),(x,0,oo))", "Limit(1/x,x,oo)", "Product(1+1/k**2,(k,1,oo))"])
def test_a_written_oo_in_a_bound_stays_legal(text):
    read(text)


def test_an_answer_built_from_a_written_bound_stays_legal():
    assert read("limit(1/x,x,oo)") == 0 and read("integrate(exp(-x),(x,0,oo))") == 1


@pytest.mark.parametrize("text", ["limit(1/x,x,0)", "solve(x>0,x)"])
def test_an_answer_holding_an_oo_nobody_wrote_is_refused(text):
    with pytest.raises(M.ExpressionRefused, match="nobody wrote"):
        read(text)


def test_only_a_read_that_evaluates_is_tested():
    """The unevaluated read looks for poles, and holds only what the evaluated read of the same text passed. A refusal there
    would read as no pole. What it does evaluate, under a %, is tested."""
    assert isinstance(read("1/x", evaluate=False), sympy.Mul)
    read("1/0", evaluate=False)
    refused("(1/0)%3", evaluate=False)


@pytest.mark.parametrize("mode, params, verdict", [
    ("equality", {"expr_a": "1/oo", "expr_b": "0"}, "HOLDS"),
    ("numeric", {"numeric_expr": "1/oo", "claimed_value": 0}, "HOLDS"),
    ("calc_chain", {"calc_steps": ["1/oo=0"]}, "HOLDS"),
    ("numeric", {"numeric_expr": "Sum(1/k**2,(k,1,oo))", "claimed_value": 1.6449340668482264}, "HOLDS"),
    ("limit", {"function": "1/x", "variable": "x", "point": "oo", "claimed_limit": "0"}, "HOLDS"),
    ("limit", {"function": "exp(-x)", "variable": "x", "point": "oo", "claimed_limit": "0"}, "HOLDS"),
    ("limit", {"function": "exp(x)", "variable": "x", "point": "-oo", "claimed_limit": "0"}, "HOLDS"),
    ("limit", {"function": "1/x", "variable": "x", "point": "inf", "claimed_limit": "0"}, "HOLDS"),
    ("equality", {"expr_a": "igcd(12,18)", "expr_b": "6"}, "HOLDS"),
    ("equality", {"expr_a": "ilcm(4,6)", "expr_b": "12"}, "HOLDS"),
    ("equality", {"expr_a": "nextprime(7)", "expr_b": "11"}, "HOLDS"),
    ("equality", {"expr_a": "prevprime(7)", "expr_b": "5"}, "HOLDS"),
    ("equality", {"expr_a": "igcd(12,18)/igcd(4,6)", "expr_b": "3"}, "HOLDS"),
    ("numeric", {"numeric_expr": "igcd(12,18)/igcd(4,6)", "claimed_value": 3}, "HOLDS"),
    ("equality", {"expr_a": "igcd(0,0)", "expr_b": "0"}, "HOLDS"),
    ("equality", {"expr_a": "2+2", "expr_b": "4"}, "HOLDS"),
    ("equality", {"expr_a": "2+2", "expr_b": "5"}, "BROKEN"),
    ("equality", {"expr_a": "sin(pi/6)", "expr_b": "1/2"}, "HOLDS"),
    ("equality", {"expr_a": "(x-1)*(x+1)", "expr_b": "x**2-1"}, "HOLDS"),
    ("equality", {"expr_a": "(x-1)*(x+1)", "expr_b": "x**2+1"}, "BROKEN"),
    ("equality", {"expr_a": "x/x", "expr_b": "1"}, "BROKEN"),
])
def test_the_checks_that_must_not_move(mode, params, verdict):
    assert post(mode, params)["verdict"] == verdict


# ── a computed value that is not finite as a float passes no numeric comparison ─────────────────────────────────
INFINITE = float("inf")


# Each of these read HOLDS at the step's base: an infinite float sits inside any window, and inf <= inf is true.
@pytest.mark.parametrize("mode, params, verdict", [
    ("numeric", {"numeric_expr": "oo", "claimed_value": INFINITE, "claimed_literal": "1.0"}, "SYSTEM_ERROR"),
    ("numeric", {"numeric_expr": "10**400*1.0", "claimed_value": INFINITE, "claimed_literal": "5.0"}, "SYSTEM_ERROR"),
    ("numeric", {"numeric_expr": "1e400", "claimed_value": INFINITE, "claimed_literal": "5.0"}, "SYSTEM_ERROR"),
    ("equality", {"expr_a": "oo", "expr_b": "10**400*1.0", "claimed_literal": "5.0"}, "BROKEN"),
    ("calc_chain", {"calc_steps": ["oo=5"], "step_rel_tol": 1e-3}, "BROKEN"),
    ("calc_chain", {"calc_steps": ["1e400=5"], "step_rel_tol": 1e-3}, "BROKEN"),
])
def test_a_value_not_finite_as_a_float_passes_no_comparison(mode, params, verdict):
    """Equality and calc_chain fall through to their exact reading, which is what proves those false."""
    assert post(mode, params)["verdict"] == verdict


@pytest.mark.parametrize("params", [
    {"numeric_expr": "10**400", "claimed_value": INFINITE, "claimed_literal": "1.0e400"},
    {"numeric_expr": "10**400", "claimed_value": "1e400", "claimed_literal": "1.0e400"},
    {"numeric_expr": "10**400/3", "claimed_value": "3.33e399", "claimed_literal": "3.33e399"},
])
def test_a_true_claim_past_a_float_is_not_checkable_and_never_false(params):
    """BROKEN mints a receipt that a claim is false. Two values past a float cannot be compared, so nothing proves that."""
    assert post("numeric", params)["verdict"] == "SYSTEM_ERROR"


@pytest.mark.parametrize("mode, params", [
    ("numeric", {"numeric_expr": "10**400", "claimed_value": 5}),
    ("numeric", {"numeric_expr": "oo", "claimed_value": 5}),
    ("numeric", {"numeric_expr": "10**400", "claimed_value": 5, "claimed_literal": "5.0"}),
    ("calc_chain", {"calc_steps": ["10**400=5"]}),
    ("calc_chain", {"calc_steps": ["5=1e400"], "step_rel_tol": 1e-3}),
])
def test_a_finite_claim_against_a_value_past_a_float_is_false(mode, params):
    """No finite float equals a value past a float, so this does prove the claim false."""
    assert post(mode, params)["verdict"] == "BROKEN"


TOP = "1.7976931348623157e308"     # the largest float: a window around it reaches past a float, so its edge is infinite


@pytest.mark.parametrize("expr, claimed", [
    (TOP, "1e400"), (TOP, INFINITE), (TOP, "inf"), (TOP, "Infinity"), (TOP, "nan"), (TOP, -INFINITE),
    (f"-{TOP}", "-1e400"), (f"-{TOP}", -INFINITE), (f"-{TOP}", "nan"),
    ("5", "1e400"), ("5", INFINITE), ("5", -INFINITE), ("5", "nan"), ("0", INFINITE),
])
@pytest.mark.parametrize("literal", [None, "1.0", "5.0", "1e400", "inf"])
def test_a_finite_value_against_a_claim_not_finite_is_false(expr, claimed, literal):
    """Read before any window, the flat default or a stated one: no finite value equals what is not finite."""
    params = {"numeric_expr": expr, "claimed_value": claimed}
    if literal is not None:
        params["claimed_literal"] = literal
    assert post("numeric", params)["verdict"] == "BROKEN"


def test_a_value_inside_a_float_still_compares():
    assert post("numeric", {"numeric_expr": "10**300", "claimed_value": 1e300})["verdict"] == "HOLDS"
    assert post("numeric", {"numeric_expr": "10**300", "claimed_value": 5})["verdict"] == "BROKEN"
    assert post("numeric", {"numeric_expr": TOP, "claimed_value": float(TOP)})["verdict"] == "HOLDS"
    assert post("numeric", {"numeric_expr": TOP, "claimed_value": 1e308})["verdict"] == "BROKEN"


# ── the routes the mode table does not reach: a refusal must not be lost on the way to a verdict ───────────────
UNDEFINED_STEPS = ["1/0 = 5", "3/0 = 9", "0/0 = 1", "1/0*2 = 5", "1/0+1 = 5", "2*3/0 = 5", "5-1/0 = 2", "1/0 x 2 = 3", "$1/0 = $5"]
CHAIN_SHAPES = ["{}", "First 2+3 = 5. Then {}.", "{}. Then 2+3 = 5.", "<<2+3=5>> and then {}", "2+3 = 5. Next {}. #### 5",
                "2+3 = 5, 4+4 = 8, {}, and 9-1 = 8. #### 8"]


@pytest.mark.parametrize("step", UNDEFINED_STEPS)
@pytest.mark.parametrize("shape", CHAIN_SHAPES)
def test_a_chain_never_certifies_over_a_step_with_no_meaning(shape, step):
    """A refusal by the rule is not prose. Dropping the step would leave the true steps beside it to certify the chain."""
    r = post("calc_chain", {"solution_text": shape.format(step)})
    assert r["verdict"] == "BROKEN", r


@pytest.mark.parametrize("text, verdict", [
    ("2+3 = 5. Next 7/2 = 9. #### 5", "BROKEN"),                # a false step, graded
    ("2+3 = 5. Next 8/2 = 4. #### 4", "HOLDS"),                 # a true one
    ("First 2+3 = 5. Then 4+4 = 8. #### 8", "HOLDS"),
    ("2+3 = 5 and version 1.2.3+4 = 5", "HOLDS"),               # refused text that is prose still skips
])
def test_prose_still_skips_and_arithmetic_is_still_graded(text, verdict):
    assert post("calc_chain", {"solution_text": text})["verdict"] == verdict


def test_only_a_refusal_by_the_rule_is_kept_as_arithmetic():
    assert M._inline_is_prose("1/0", "5", []) is False          # no meaning: kept, and read as unparseable
    assert M._inline_is_prose("5", "0/0", []) is False
    assert M._inline_is_prose("1.2.3+4", "5", []) is True       # not a computation: prose
    assert M._inline_is_prose("x+1", "5", []) is True           # holds a variable: prose
    assert M._inline_is_prose("2+3", "5", []) is False


TRUE_CHECK = {"numeric_expr": "2+2", "claimed_value": 4}
REFUSED_SET = {"set_a": "A &", "set_b": "A", "claimed_equal": True, "variables": ["A"]}
SET_ASIDE = {       # the modes whose refusal is NOT_APPLICABLE, which a step's status drops
    "equality": lambda t: {"expr_a": t, "expr_b": "0"},
    "derivative": lambda t: {"function": f"x + ({t})", "variable": "x", "claimed_derivative": "1"},
    "integral": lambda t: {"integrand": f"1 + ({t})", "variable": "x", "claimed_antiderivative": "x"},
    "limit": lambda t: {"function": f"x + ({t})", "variable": "x", "point": "1", "claimed_limit": "1"},
    "solve": lambda t: {"equation": f"y + ({t}) = 3", "variable": "y", "claimed_solutions": ["3"]},
}


@pytest.mark.parametrize("text", FORMS + ["1/0", "1#0", "x.y", "1 +"])
@pytest.mark.parametrize("mode", sorted(SET_ASIDE))
def test_a_passing_check_never_lifts_a_refused_text(mode, text):
    """A true check beside it goes, so it cannot lift the packet: whether the rule refused the text or it never parsed."""
    packet = dict(TRUE_CHECK, **SET_ASIDE[mode](text))
    results = M.run({"MATH_VERIFY": packet})
    assert [r.status for r in results] == ["NOT_APPLICABLE"]
    r = route({"MATH_VERIFY": packet})
    assert r["verdict"] == "INCOMPLETE", r
    assert not r.get("seal")


# Every text-reading mode's refusal in a packet, and a sibling of each kind on either side of it. dispatch fires _RULES in
# order: calc_chain first, then numeric, and inequality last, so these three put a sibling before and after every mode.
REFUSALS = {mode: (build("1/(1/0)"), reading) for mode, (build, reading) in MODES.items()}
REFUSALS["set_algebra"] = (REFUSED_SET, "INCOMPLETE")
SIBLINGS = {
    "calc_chain": {"true": {"calc_steps": ["2+3=5"]}, "false": {"calc_steps": ["2+3=6"]}},
    "numeric": {"true": TRUE_CHECK, "false": {"numeric_expr": "2+2", "claimed_value": 5},
                "erroring": {"numeric_expr": "1 +", "claimed_value": 4}},
    "inequality": {"true": {"lhs": "1", "rhs": "2", "op": "<"}, "false": {"lhs": "2", "rhs": "1", "op": "<"},
                   "erroring": {"lhs": "1 +", "rhs": "2", "op": "<"}},
}
BESIDE = [(mode, side, kind) for mode in sorted(REFUSALS) for side in sorted(SIBLINGS) for kind in sorted(SIBLINGS[side])
          if side != mode]


def _reading_beside(refusal, kind):
    """BROKEN over SYSTEM_ERROR over INCOMPLETE, as every step reads; a passing sibling adds nothing to a refusal."""
    words = {refusal, {"false": "BROKEN", "erroring": "SYSTEM_ERROR", "true": refusal}[kind]}
    return next(w for w in ("BROKEN", "SYSTEM_ERROR", "INCOMPLETE") if w in words)


def test_a_sibling_stands_on_each_side_of_every_mode():
    order = [fn.__name__ for _, fn in M._RULES]
    assert order[0] == "verify_calc_chain" and order[1] == "verify_numeric" and order[-1] == "verify_inequality"
    for mode in REFUSALS:
        sides = {side for m, side, _ in BESIDE if m == mode}
        assert sides == set(SIBLINGS) - {mode}


@pytest.mark.parametrize("side, kind", [(side, kind) for side in sorted(SIBLINGS) for kind in sorted(SIBLINGS[side])])
def test_each_sibling_reads_what_it_is_called(side, kind):
    verdict = {"true": "HOLDS", "false": "BROKEN", "erroring": "SYSTEM_ERROR"}[kind]
    assert route({"MATH_VERIFY": SIBLINGS[side][kind]})["verdict"] == verdict


@pytest.mark.parametrize("mode, side, kind", BESIDE)
def test_a_refused_text_hides_no_sibling_and_is_lifted_by_none(mode, side, kind):
    """A refused text cannot dodge a genuine BROKEN, and a passing check cannot lift it: only the passing result goes."""
    params, refusal = REFUSALS[mode]
    packet = dict(SIBLINGS[side][kind], **params)
    assert route({"MATH_VERIFY": packet})["verdict"] == _reading_beside(refusal, kind)
    statuses = [r.status for r in M.run({"MATH_VERIFY": packet})]
    if refusal == "INCOMPLETE":
        assert "NOT_APPLICABLE" in statuses and "CONFIRMED" not in statuses
        assert ("MISMATCH" in statuses) == (kind == "false") and ("ERROR" in statuses) == (kind == "erroring")


@pytest.mark.parametrize("mode", sorted(set(SET_ASIDE) | {"set_algebra"}))
def test_a_false_check_stands_beside_a_refused_text_and_a_true_one(mode):
    packet = dict(SIBLINGS["inequality"]["false"], **TRUE_CHECK, **REFUSALS[mode][0])
    assert sorted(r.status for r in M.run({"MATH_VERIFY": packet})) == ["MISMATCH", "NOT_APPLICABLE"]
    assert route({"MATH_VERIFY": packet})["verdict"] == "BROKEN"


def test_every_refusal_counts_whatever_its_text():
    """Set text has its own words. They stay, and it counts as a refusal all the same."""
    (result,) = M.run({"MATH_VERIFY": dict(TRUE_CHECK, **REFUSED_SET)})
    assert result.status == "NOT_APPLICABLE" and result.detail.startswith("cannot parse set expression: ")
    assert route({"MATH_VERIFY": dict(TRUE_CHECK, **REFUSED_SET)})["verdict"] == "INCOMPLETE"


def test_two_refused_texts_read_as_one():
    packet = dict(REFUSED_SET, **SET_ASIDE["equality"]("1 +"), **TRUE_CHECK)
    assert [r.status for r in M.run({"MATH_VERIFY": packet})] == ["NOT_APPLICABLE", "NOT_APPLICABLE"]
    assert route({"MATH_VERIFY": packet})["verdict"] == "INCOMPLETE"


# physics: each kind of refusal, and a true, a false and an erroring check on each side of the equation in run's order.
FORCE_UNITS = {"F": "newton", "m": "kg", "a": "meter/second**2"}
PHYSICS_REFUSALS = {
    "undefined text": {"equation": "F = m*a + 1/(1/0)", "symbols": FORCE_UNITS},
    "syntax": {"equation": "F = m*a +", "symbols": FORCE_UNITS},
    "unit": {"equation": "F = m*a", "symbols": dict(FORCE_UNITS, m="kg#")},
    "symbols table": {"equation": "F = m*a", "symbols": ["F"]},
    "symbols key": {"equation": "F = m*a", "symbols": dict(FORCE_UNITS, _m="kg")},
    "not a text": {"equation": 5, "symbols": FORCE_UNITS},
}
LIGHT_SQUARED = 299792458.0 ** 2
PHYSICS_SIBLINGS = {    # true, false, erroring
    "before: mass and energy": ({"rest_mass_kg": 1.0, "claimed_rest_energy_J": LIGHT_SQUARED},
                                {"rest_mass_kg": 1.0, "claimed_rest_energy_J": 5.0},
                                {"rest_mass_kg": "x", "claimed_rest_energy_J": 5.0}),
    "before: gravitation": ({"grav_mass_1_kg": 1.0, "grav_mass_2_kg": 1.0, "grav_separation_m": 1.0,
                             "claimed_gravitational_force_N": 6.6743e-11},
                            {"grav_mass_1_kg": 1.0, "grav_mass_2_kg": 1.0, "grav_separation_m": 1.0,
                             "claimed_gravitational_force_N": 5.0},
                            {"grav_mass_1_kg": "x", "grav_mass_2_kg": 1.0, "grav_separation_m": 1.0,
                             "claimed_gravitational_force_N": 5.0}),
    "after: conservation": ({"before": {"E": 1.0}, "after": {"E": 1.0}}, {"before": {"E": 1.0}, "after": {"E": 2.0}},
                            {"before": 1, "after": 2}),      # this one raises inside run: it reads an error, not a crash
    "after: kinematics": ({"v0": 0, "a": 2, "t": 3, "claimed_displacement": 9},
                          {"v0": 0, "a": 2, "t": 3, "claimed_displacement": 50},
                          {"v0": "x", "a": 2, "t": 3, "claimed_displacement": 9}),
    "after: speed limit": ({"speed_m_per_s": 10.0}, {"speed_m_per_s": 4e8}, {"speed_m_per_s": "x"}),
    "after: force": ({"mass_kg": 2.0, "acceleration_m_per_s2": 3.0, "claimed_force_N": 6.0},
                     {"mass_kg": 2.0, "acceleration_m_per_s2": 3.0, "claimed_force_N": 7.0},
                     {"mass_kg": "x", "acceleration_m_per_s2": 3.0, "claimed_force_N": 7.0}),
    "after: kinetic energy": ({"mass_kg": 2.0, "velocity_m_per_s": 3.0, "claimed_kinetic_energy_J": 9.0},
                              {"mass_kg": 2.0, "velocity_m_per_s": 3.0, "claimed_kinetic_energy_J": 7.0},
                              {"mass_kg": "x", "velocity_m_per_s": 3.0, "claimed_kinetic_energy_J": 7.0}),
}


def physics(packet):
    return route({"PHYS_VERIFY": packet}, "physics")["verdict"]


@pytest.mark.parametrize("sibling", sorted(PHYSICS_SIBLINGS))
def test_each_physics_sibling_reads_what_it_is_called(sibling):
    assert [physics(p) for p in PHYSICS_SIBLINGS[sibling]] == ["HOLDS", "BROKEN", "SYSTEM_ERROR"]


@pytest.mark.parametrize("sibling", sorted(PHYSICS_SIBLINGS))
@pytest.mark.parametrize("refusal", sorted(PHYSICS_REFUSALS))
def test_physics_runs_every_check_and_a_refusal_removes_only_a_pass(refusal, sibling):
    """A sibling listed after the equation runs as one listed before it does, so neither side can hide behind a refusal."""
    true, false, erroring = (dict(p, **PHYSICS_REFUSALS[refusal]) for p in PHYSICS_SIBLINGS[sibling])
    assert physics(true) == "INCOMPLETE"
    assert physics(false) == "BROKEN"
    assert physics(erroring) == "SYSTEM_ERROR"


def test_a_physics_refusal_keeps_what_stands_and_only_that():
    packet = dict(PHYSICS_REFUSALS["syntax"], speed_m_per_s=4e8, v0=0, a=2, t=3, claimed_displacement=9,
                  rest_mass_kg=1.0, claimed_rest_energy_J=5.0)
    results = {r.name: r.status for r in P.run({"PHYS_VERIFY": packet})}
    assert "CONFIRMED" not in results.values() and "physics.dimensional" in results
    assert sorted(results.values()) == ["MISMATCH", "MISMATCH", "NOT_APPLICABLE"]


@pytest.mark.parametrize("equation, sibling, verdict", [
    ("F = m*a", 0, "HOLDS"), ("F = m*a", 1, "BROKEN"), ("F = m*a", 2, "SYSTEM_ERROR"),   # read, it speaks with the rest
    ("F = m", 0, "BROKEN"),                                                              # a false equation stands
    ("F", 0, "SYSTEM_ERROR"),                                                            # no '=' is an error, as it was
])
def test_a_physics_packet_with_no_refused_text_reads_as_it_did(equation, sibling, verdict):
    packet = dict(PHYSICS_SIBLINGS["after: kinematics"][sibling], equation=equation, symbols=FORCE_UNITS)
    assert physics(packet) == verdict


@pytest.mark.parametrize("packet, verdict", [
    (dict(TRUE_CHECK), "HOLDS"),
    (dict(TRUE_CHECK, expr_a="2+2", expr_b="4"), "HOLDS"),
    (dict(TRUE_CHECK, expr_a="2+2", expr_b="5"), "BROKEN"),
    (dict(TRUE_CHECK, expr_a=None, expr_b="4"), "HOLDS"),                    # nothing to read: no text was refused
    (dict(TRUE_CHECK, solution_text="the answer is five"), "HOLDS"),          # a framing question: no text was refused
    (dict(TRUE_CHECK, set_a="A & A", set_b="A", claimed_equal=True, variables=["A"]), "HOLDS"),
    (dict(TRUE_CHECK, set_a="A & A", set_b="A", claimed_equal=False, variables=["A"]), "BROKEN"),
])
def test_a_packet_with_no_refused_text_reads_as_it_did(packet, verdict):
    assert route({"MATH_VERIFY": packet})["verdict"] == verdict


def test_a_step_refused_in_a_derivation_is_not_lost():
    steps = [{"id": "a", "domain": "mathematics", "spec": {"mode": "equality", "params": {"expr_a": "1/(1/0)", "expr_b": "0"}}},
             {"id": "b", "domain": "mathematics", "spec": {"mode": "equality", "params": {"expr_a": "2+2", "expr_b": "4"}}}]
    assert verify_derivation(steps)["verdict"] == "INCOMPLETE"
    assert verify_derivation(steps[::-1])["verdict"] == "INCOMPLETE"


def test_a_stated_window_never_certifies_what_exact_arithmetic_refuses():
    """As a float this denominator is not quite zero, so the float read passes and lands inside the stated window. Read
    exactly it is zero, and the exact re-read comes first."""
    params = {"expr_a": "1/(0.1+0.2-0.3)", "expr_b": "1.8e16", "claimed_literal": "1.8e16"}
    assert post("equality", params)["verdict"] == "INCOMPLETE"


# ── a deferred object: named by the goal, filed as a want, pinned here at the parser and in no mode ──────────────
@pytest.mark.parametrize("text, kind", [
    ("Sum(1/k,(k,0,3))", sympy.Sum), ("Product(1/k,(k,0,3))", sympy.Product), ("Integral(1/x,(x,0,1))", sympy.Integral),
    ("Limit(1/x,x,0)", sympy.Limit), ("Subs(1/x,x,0)", sympy.Subs),
])
def test_a_deferred_object_is_read_and_left_unevaluated(text, kind):
    """Its undefined step is not built yet, and reading it costs an unbounded evaluation. A later fix moves this on purpose."""
    value = read(text)
    assert isinstance(value, kind) and not value.has(sympy.zoo, sympy.nan)


# ── a sweep against an exact oracle: Fractions and plain Python, no sympy ───────────────────────────────────────
class _Undefined(Exception):
    pass


class _Skip(Exception):
    pass


def _is_prime(n):
    return n > 1 and all(n % d for d in range(2, int(n ** 0.5) + 1))


def _next_prime(n):
    n += 1
    while not _is_prime(n):
        n += 1
    return n


def _previous_prime(n):
    n -= 1
    while not _is_prime(n):
        n -= 1
    return n


def _atom(r):
    k = r.random()
    if k < .30:
        a, b = r.randint(0, 12), r.randint(0, 12)
        return f"igcd({a},{b})", Fraction(math.gcd(a, b))
    if k < .50:
        a, b = r.randint(0, 9), r.randint(0, 9)
        return f"ilcm({a},{b})", Fraction(math.lcm(a, b))
    if k < .62:
        a = r.randint(0, 20)
        return f"nextprime({a})", Fraction(_next_prime(a))
    if k < .74:
        a = r.randint(3, 20)
        return f"prevprime({a})", Fraction(_previous_prime(a))
    if k < .90:
        return "igcd(0,0)", Fraction(0)
    a = r.randint(1, 7)
    return str(a), Fraction(a)


def _apply(op, x, y):
    if op == "+":
        return x + y
    if op == "-":
        return x - y
    if op == "*":
        return x * y
    if op in "/%" and y == 0:
        raise _Undefined
    if op == "/":
        return x / y
    if op == "%":
        return x - y * math.floor(x / y)
    if y.denominator != 1 or abs(y) > 6 or (x == 0 and y == 0):
        raise _Skip                                      # a convention, or a form the oracle does not hold
    if x == 0 and y < 0:
        raise _Undefined
    return x ** int(y)


def _build(r, depth):
    if depth == 0 or r.random() < .25:
        text, value = _atom(r)
        return text, (lambda: value)
    k = r.random()
    if k < .16:
        name = r.choice(("Abs", "floor", "ceiling", "sign"))
        text, inner = _build(r, depth - 1)
        rule = {"Abs": abs, "floor": lambda v: Fraction(math.floor(v)), "ceiling": lambda v: Fraction(math.ceil(v)),
                "sign": lambda v: Fraction((v > 0) - (v < 0))}[name]
        return f"{name}({text})", (lambda: rule(inner()))
    if k < .24:
        text, inner = _build(r, depth - 1)
        return f"(-({text}))", (lambda: -inner())
    op = r.choice(["+", "-", "*", "/", "/", "/", "**", "%"])
    a, left = _build(r, depth - 1)
    b, right = _build(r, depth - 1)
    return f"({a}){op}({b})", (lambda: _apply(op, left(), right()))


def _written(value):
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _sweep(count, seed):
    """(truth, mode, params) for count expressions, each read through five modes."""
    r = random.Random(seed)
    rows, seen = [], set()
    while len(seen) < count:
        text, value = _build(r, r.choice((2, 2, 3)))
        if text in seen or len(text) > 200:
            continue
        try:
            v = value()
        except _Skip:
            continue
        except _Undefined:
            seen.add(text)
            for c in ("0", "1"):
                rows += [("UNDEFINED", "equality", {"expr_a": text, "expr_b": c}),
                         ("UNDEFINED", "numeric", {"numeric_expr": text, "claimed_value": int(c)}),
                         ("UNDEFINED", "calc_chain", {"calc_steps": [f"{text}={c}"]}),
                         ("UNDEFINED", "system", {"equations": [f"x + ({text}) = 3"], "variables": ["x"], "claimed_solution": {"x": 3 - int(c)}})]
            rows += [("UNDEFINED", "inequality", {"lhs": text, "rhs": "0", "op": "<="}), ("UNDEFINED", "inequality", {"lhs": text, "rhs": "0", "op": ">="})]
            continue
        if abs(v) > 10 ** 5 or v.denominator > 10 ** 4:
            continue
        seen.add(text)
        w = v + 1 + abs(v)
        rows += [("TRUE", "equality", {"expr_a": text, "expr_b": _written(v)}), ("FALSE", "equality", {"expr_a": text, "expr_b": _written(w)}),
                 ("TRUE", "numeric", {"numeric_expr": text, "claimed_value": float(v)}), ("FALSE", "numeric", {"numeric_expr": text, "claimed_value": float(w)}),
                 ("TRUE", "inequality", {"lhs": text, "rhs": _written(v), "op": "<="}), ("FALSE", "inequality", {"lhs": text, "rhs": _written(v), "op": "<"}),
                 ("FALSE", "inequality", {"lhs": text, "rhs": _written(v), "op": ">"}),
                 ("TRUE", "system", {"equations": [f"x + ({text}) = {_written(v + 2)}"], "variables": ["x"], "claimed_solution": {"x": 2}}),
                 ("FALSE", "system", {"equations": [f"x + ({text}) = {_written(v + 2)}"], "variables": ["x"], "claimed_solution": {"x": 3}}),
                 ("TRUE", "calc_chain", {"calc_steps": [f"{text}={_written(v)}"]}), ("FALSE", "calc_chain", {"calc_steps": [f"{text}={_written(w)}"]})]
    return rows


def _read_sweep(count, seed):
    rows = _sweep(count, seed)
    assert {truth for truth, _m, _p in rows} == {"TRUE", "FALSE", "UNDEFINED"}
    wrong = []
    for truth, mode, params in rows:
        verdict = verify_derivation([{"id": "s", "domain": "mathematics", "spec": {"mode": mode, "params": params}}]).get("verdict")
        if (truth == "TRUE") != (verdict == "HOLDS"):
            wrong.append((truth, mode, verdict, params))
    assert wrong == []
    return len(rows)


def test_a_small_sweep_against_the_exact_oracle():
    assert _read_sweep(12, 20261104) > 60


def test_the_full_sweep_against_the_exact_oracle():
    assert _read_sweep(400, 20261105) > 2000


# ── this repo's own rows, beside V3's ─────────────────────────────────────────────────────────────────────────
def dimensional(equation, symbols):
    return physics({"equation": equation, "symbols": symbols})


@pytest.mark.parametrize("text", [t for t in FORMS if "inf" not in t])
def test_a_form_with_no_meaning_is_refused_on_a_physics_side_and_in_a_unit(text):
    """inf is a constant in mathematics alone: physics reads it as a symbol, as it always has."""
    assert dimensional(f"x = {text}", {"x": "1"}) == "INCOMPLETE"
    assert dimensional("x = x", {"x": text}) == "INCOMPLETE"


@pytest.mark.parametrize("mode, params, verdict", [
    ("equality", {"expr_a": "0", "expr_b": "1/(1/0)"}, "INCOMPLETE"),
    ("inequality", {"lhs": "0", "rhs": "1/(1/0)", "op": "<="}, "SYSTEM_ERROR"),
    ("system", {"equations": ["x = 0"], "claimed_solution": {"x": "1/(1/0)"}}, "SYSTEM_ERROR"),
    ("solve", {"equation": "x = 0", "variable": "x", "claimed_solutions": ["1/(1/0)"]}, "INCOMPLETE"),
    ("derivative", {"function": "x", "variable": "x", "claimed_derivative": "1 + 1/(1/0)"}, "INCOMPLETE"),
    ("integral", {"integrand": "1", "variable": "x", "claimed_antiderivative": "x + 1/(1/0)"}, "INCOMPLETE"),
    ("limit", {"function": "x", "variable": "x", "point": "1/(1/0)", "claimed_limit": "0"}, "INCOMPLETE"),
    ("limit", {"function": "x", "variable": "x", "point": "0", "claimed_limit": "1/(1/0)"}, "INCOMPLETE"),
    ("calc_chain", {"calc_steps": ["0 = 1/(1/0)"]}, "BROKEN"),
])
def test_the_rule_holds_in_the_other_field_each_mode_reads(mode, params, verdict):
    assert post(mode, params)["verdict"] == verdict


@pytest.mark.parametrize("returned", [sympy.zoo, sympy.nan, sympy.oo, -sympy.oo, sympy.AccumBounds(-1, 1), [sympy.zoo], (sympy.nan,),
                                      [[sympy.oo]], {sympy.Integer(1): sympy.zoo}, {sympy.oo: sympy.Integer(1)},
                                      [{sympy.Integer(1): [sympy.nan]}], sympy.Matrix(((1, sympy.oo),)), sympy.Tuple(1, sympy.zoo),
                                      sympy.Symbol("x") + sympy.oo],
                         ids=lambda v: type(v).__name__)
def test_the_rule_reaches_what_a_call_returns_through_every_container(monkeypatch, returned):
    monkeypatch.setitem(M._FUNCTIONS, "sin", lambda *a: returned)
    refused("sin(1)")


# verify_numeric keeps its plain comparison here, where V3's goes through its band: past float range the window is as infinite
# as the value, so the comparison alone would pass any claim. This is the plan's one exception to keeping non-parser lines.
@pytest.mark.parametrize("claimed", [5, 0, 1e308])
@pytest.mark.parametrize("text", ["10**400", "-(10**400)", "igcd(10,10)**400", "10.0**400", "exp(1000)", "oo", "-oo"])
def test_a_computed_value_past_float_range_reads_broken_whatever_is_claimed(text, claimed):
    assert post("numeric", {"numeric_expr": text, "claimed_value": claimed})["verdict"] == "BROKEN"


@pytest.mark.parametrize("text, claimed, verdict", [("igcd(10,10)**300", 1e300, "HOLDS"), ("igcd(10,10)**300", 5, "BROKEN"),
                                                    ("2**10", 1024, "HOLDS"), ("2**10", 1000, "BROKEN")])
def test_the_same_arithmetic_below_float_range_reads_as_it_did(text, claimed, verdict):
    assert post("numeric", {"numeric_expr": text, "claimed_value": claimed})["verdict"] == verdict


# calc_chain's opt-in tolerance takes V3's finite guard, the plan's other exception to keeping non-parser lines. A side past
# float range built only from integer-returning calls was a plain int at the step's base, so float() raised and the step read
# SYSTEM_ERROR. The parser makes it an Integer, float() gives inf, and inf <= tol*inf passes: with no guard the port itself
# would move this false step to HOLDS, sealed. So each row here is held with the tolerance on, through both doors.
def through_mcp(spec, domain="mathematics"):
    arguments = {"steps": [{"id": "r", "domain": domain, "spec": spec}], "seal": False}
    call = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "verify", "arguments": arguments}}
    status, _headers, raw = handle_http("POST", {}, json.dumps(call).encode("utf-8"), CONFIG)
    assert status == 200, raw
    result = json.loads(raw)["result"]
    assert result["isError"] is False, result
    return json.loads(result["content"][0]["text"])


DOORS = {"dispatch": route, "mcp": through_mcp}
PAST_A_FLOAT = ["igcd(10,10)**400", "ilcm(10,10)**400", "nextprime(7)**400", "igcd(10,10)**400*ilcm(1,3)",
                "igcd(10,10)**400+igcd(4,6)", "-igcd(10,10)**400"]


def chain(params):
    return {"mode": "calc_chain", "params": params}


@pytest.mark.parametrize("door", sorted(DOORS))
@pytest.mark.parametrize("tolerance", [1e-2, 1e-3, 1e-9])
@pytest.mark.parametrize("text", PAST_A_FLOAT)
def test_a_false_step_past_a_float_reads_broken_with_the_tolerance_on(door, tolerance, text):
    r = DOORS[door](chain({"calc_steps": [f"{text} = 5"], "step_rel_tol": tolerance}))
    assert r["verdict"] == "BROKEN", r
    assert not r.get("seal")


@pytest.mark.parametrize("door", sorted(DOORS))
@pytest.mark.parametrize("text", PAST_A_FLOAT)
def test_a_false_final_answer_past_a_float_reads_broken_with_the_tolerance_on(door, text):
    r = DOORS[door](chain({"calc_steps": ["2+3 = 5"], "claimed_answer": text, "step_rel_tol": 1e-3}))
    assert r["verdict"] == "BROKEN", r
    assert not r.get("seal")


@pytest.mark.parametrize("door", sorted(DOORS))
@pytest.mark.parametrize("text", PAST_A_FLOAT)
def test_a_false_step_inside_a_true_chain_reads_broken_with_the_tolerance_on(door, text):
    r = DOORS[door](chain({"calc_steps": ["2+3 = 5", f"{text} = 5", "4+4 = 8"], "step_rel_tol": 1e-3}))
    assert r["verdict"] == "BROKEN", r


@pytest.mark.parametrize("door", sorted(DOORS))
@pytest.mark.parametrize("text", PAST_A_FLOAT)
def test_the_same_false_step_reads_broken_with_the_tolerance_off(door, text):
    assert DOORS[door](chain({"calc_steps": [f"{text} = 5"]}))["verdict"] == "BROKEN"


@pytest.mark.parametrize("door", sorted(DOORS))
@pytest.mark.parametrize("text", PAST_A_FLOAT)
def test_an_exact_step_past_a_float_still_holds_with_the_tolerance_on(door, text):
    """The guard binds the float comparison alone: a step exact arithmetic proves never reaches it."""
    assert DOORS[door](chain({"calc_steps": [f"{text} = {text}"], "step_rel_tol": 1e-3}))["verdict"] == "HOLDS"


@pytest.mark.parametrize("door", sorted(DOORS))
def test_the_tolerance_still_does_its_work_inside_a_float(door):
    within = chain({"calc_steps": ["10.0 = 10.00001"], "step_rel_tol": 1e-3})
    outside = chain({"calc_steps": ["10.0 = 11.0"], "step_rel_tol": 1e-3})
    assert DOORS[door](within)["verdict"] == "HOLDS"
    assert DOORS[door](outside)["verdict"] == "BROKEN"
