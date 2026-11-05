"""The one parser: what it reads, what it refuses, each limit at its edge, and how every caller reads a refusal.

mathematics.parse_expression walks Python's ast and builds sympy objects; nothing is evaluated. These tests hold the
parser's own contract. tests/test_parse_route.py proves the input classes through the real doors,
tests/test_parse_differential.py proves the readings unchanged, and tests/test_no_other_route.py proves no other way
in. Every input here is inert. Names the fix adds are read inside the tests, so the file collects at the step's base.
"""
from __future__ import annotations

import builtins
import json
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest
import sympy

from concordance.config import EngineConfig
from concordance.verifiers import mathematics as M
from concordance.verifiers import physics as P
from concordance.web import api

ROOT = Path(__file__).resolve().parents[1]
CONFIG = EngineConfig("secular")
NEWTON = {"F": "newton", "m": "kilogram", "a": "meter/second**2"}
PASSING_CHECK = {"mass_kg": 2.0, "acceleration_m_per_s2": 3.0, "claimed_force_N": 6.0}


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


def post(domain, spec):
    body = {"steps": [{"id": "r", "domain": domain, "spec": spec}]}
    status, out = api.dispatch("POST", "/verify", {"seal": "0"}, body, CONFIG)
    assert status == 200, out
    return out


def mode(name, params):
    return post("mathematics", {"mode": name, "params": params})


# ── ONE PARSER: what it reads ─────────────────────────────────────────────────────────────────────────────────
def test_a_refusal_is_a_parse_error_every_mode_already_catches():
    assert issubclass(M.ExpressionRefused, ValueError)
    assert issubclass(M.ExpressionRefused, M._PARSE_ERRORS)


@pytest.mark.parametrize("text, expected", [
    ("7", sympy.Integer(7)), ("1_000", sympy.Integer(1000)), ("0x10", sympy.Integer(16)),
    ("-x", -sympy.Symbol("x")), ("+x", sympy.Symbol("x")), ("x+1", sympy.Symbol("x") + 1), ("x-1", sympy.Symbol("x") - 1),
    ("2*x", 2 * sympy.Symbol("x")), ("1/3", sympy.Rational(1, 3)), ("x**2", sympy.Symbol("x") ** 2),
    ("x^2", sympy.Symbol("x") ** 2), ("16 % 9", sympy.Integer(7)),
    ("Mod(16,9)", sympy.Integer(7)), ("x<1", sympy.Symbol("x") < 1), ("x>=1", sympy.Symbol("x") >= 1),
    ("  x  ", sympy.Symbol("x")), ("(1 +\n2)", sympy.Integer(3)),
])
def test_the_listed_nodes_build_what_they_say(text, expected):
    got = read(text)
    assert got == expected and type(got) is type(expected)


@pytest.mark.parametrize("text", ["(1,2)", "x,y", "()", "(1,2)*3", "3*(1,2)", "(1,2)+(3,)", "-(1,2)", "sin((1,2)*3)",
                                  "Max(1,(2,3)*2)", "(1,2)<(3,)"])
def test_a_tuple_is_a_call_argument_and_nothing_else(text):
    refused(text)


@pytest.mark.parametrize("text", ["Sum(k,(k,1,3))", "Integral(x,(x,0,1))", "Matrix(((1,2),(3,4)))",
                                  "Matrix((((1),(2)),((3),(4))))", "Piecewise((x,x<1),(0,x>=1))"])
def test_a_tuple_is_read_as_a_call_argument_at_any_depth(text):
    read(text)


@pytest.mark.parametrize("text", [
    "lambda x: x", "x if y else z", "x and y", "x or y", "not x", "~x", "x.y", "x.y(1)", "sin(x)(1)", "(1).real",
    "Max(*x)", "Max(k for k in x)", "(y := 1)", "await x", "(yield x)", "f'a'", "x in y", "x not in y", "x is y",
    "x==1", "1<x<3", "7//2", "x<<1", "x>>1",
])
def test_every_other_node_and_operator_is_refused(text):
    refused(text)


@pytest.mark.parametrize("text", ["'a'", "b'a'", "None", "True", "False", "1j", "...", "Piecewise((1,x>0),(0,True))"])
def test_a_constant_is_an_int_or_a_float_and_nothing_else(text):
    refused(text)


@pytest.mark.parametrize("text", ["2 # + 1", "x @ y", "x ! y", "x $ y", "x & y", "x[1]", "{1}", "x \\\n+ y", "x | y", "`x`"])
def test_the_invalid_characters_are_refused_before_anything_parses(text):
    with pytest.raises(M.ExpressionRefused, match="invalid characters"):
        read(text)


def test_the_text_parsed_is_the_normalised_text_and_the_only_one(monkeypatch):
    seen = []
    real = M._ast.parse

    def spy(source, *args, **kw):
        seen.append(source)
        return real(source, *args, **kw)

    with monkeypatch.context() as patch:        # only around the read: pytest's own reports call ast.parse too
        patch.setattr(M._ast, "parse", spy)
        read("  2^3 mod 5 ", word_mod=True)
    assert seen == ["2**3 % 5"]


def test_the_word_form_of_mod_is_mathematics_own():
    """Physics never read the word. There mod is a name a symbol may have, and a claim in the word form never parsed."""
    assert M._parse("16 mod 9") == 7 and M._parse("x MOD 3") == sympy.Symbol("x") % 3
    assert M._parse("Mod(16,9)") == 7
    assert read("mod") == sympy.Symbol("mod") and read("MOD*a") == sympy.Symbol("MOD") * sympy.Symbol("a")
    refused("16 mod 9")


@pytest.mark.parametrize("text, names", [
    ("µ", None), ("µ**2", {"µ": sympy.Symbol("µ")}), ("x", {"µ": sympy.Symbol("µ")}),
    ("ｘ", None), ("x²", None), ("ﬁ", None),
])
def test_a_text_or_a_callers_name_nfkc_would_change_is_refused(text, names):
    with pytest.raises(M.ExpressionRefused):
        read(text, names)


def test_a_name_is_the_callers_or_a_constant_or_a_symbol():
    mine = sympy.Symbol("beta")
    assert read("beta", {"beta": mine}) is mine              # a caller's name wins over a function's name
    assert read("pi", {"pi": mine}) is mine                  # and over a constant
    assert read("pi") is sympy.pi and read("E") is sympy.E and read("I") is sympy.I and read("oo") is sympy.oo
    assert read("true") is sympy.true and read("false") is sympy.false
    for name in ("foo", "theta", "int", "plotting", "sieve"):   # sympy itself reads these as symbols
        assert read(name) == sympy.Symbol(name)


@pytest.mark.parametrize("name", ["_v", "__x", "__import__", "__builtins__", "_"])
def test_a_name_beginning_with_an_underscore_is_refused(name):
    with pytest.raises(M.ExpressionRefused, match="underscore"):
        read(name, {name: sympy.Symbol("x")})


@pytest.mark.parametrize("name", ["sin", "gamma", "beta", "Matrix", "simplify", "abs", "round"])
def test_an_allowlisted_function_used_as_a_value_is_refused(name):
    refused(name)
    refused(f"Matrix(1,1,{name})")


@pytest.mark.parametrize("name", ["print", "bin", "len", "eval", "exec", "open", "getattr", "compile", "N", "S", "Q", "O",
                                  "ZZ", "Reals", "EmptySet", "Id", "Function", "Lambda", "sympify", "Rel"])
def test_any_other_name_sympy_reads_as_an_object_is_refused(name):
    refused(name)
    refused(f"Matrix(1,1,{name})")


def test_a_callers_name_used_as_a_function_is_refused():
    refused("sin(x)", {"sin": sympy.Symbol("sin")})
    refused("m(x)", {"m": sympy.Symbol("m")})


@pytest.mark.parametrize("text", ["f(x)", "log10(x)", "print(1)", "eval(x)", "Function(x)", "max(1,2)"])
def test_a_call_off_the_allowlist_is_refused(text):
    refused(text)


@pytest.mark.parametrize("text", ["sin(x,evaluate=x)", "Max(1,**x)", "simplify(x,measure=x)", "Pow(2,3,evaluate=true)"])
def test_a_call_takes_no_keywords(text):
    refused(text)


def test_nsimplify_is_off_the_list_and_refused():
    assert "nsimplify" not in M._ALLOWED_FUNCS
    refused("nsimplify(0.5)")
    refused("nsimplify(2)")


@pytest.mark.parametrize("text, value", [
    ("igcd(4,6)", sympy.Integer(2)), ("ilcm(4,6)", sympy.Integer(12)), ("nextprime(7)", sympy.Integer(11)),
    ("prevprime(7)", sympy.Integer(5)), ("isprime(7)", sympy.true), ("isprime(8)", sympy.false),
])
def test_a_plain_result_becomes_a_sympy_value(text, value):
    got = read(text)
    assert got is value or (got == value and type(got) is type(value))


def test_a_plain_result_can_be_computed_with():
    assert read("igcd(4,6)+1") == 3 and read("nextprime(7)*2") == 22


@pytest.mark.parametrize("text", ["primerange(1,10)", "factorint(12)", "roots(x**2-1,x)"])
def test_an_iterator_or_a_container_of_plain_values_is_refused(text):
    with pytest.raises(M.ExpressionRefused, match="a call returned"):
        read(text)


@pytest.mark.parametrize("returned", ["text", iter(()), (i for i in ()), 1.5, 7, None, object(), print, sympy.sin,
                                      ["text"], (["text"],), {"a": sympy.Integer(1)}, {sympy.Integer(1): "a"},
                                      [{sympy.Integer(1): [iter(())]}]])
def test_the_second_line_refuses_what_a_call_returns_at_every_depth(monkeypatch, returned):
    monkeypatch.setitem(M._FUNCTIONS, "sin", lambda *a: returned)
    with pytest.raises(M.ExpressionRefused, match="a call returned"):
        read("sin(1)")


def test_a_list_tuple_or_dict_of_sympy_values_is_returned():
    x = sympy.Symbol("x")
    assert read("solve(x-1,x)") == [sympy.Integer(1)]
    assert read("solve((x+y-3,x-y-1),(x,y))") == {x: 2, sympy.Symbol("y"): 1}


def test_arithmetic_is_on_sympy_values_including_a_mutable_matrix():
    m = sympy.Matrix(((1, 2), (3, 4)))
    assert read("Matrix(((1,2),(3,4)))*2") == m * 2
    assert read("2*Matrix(((1,2),(3,4)))") == 2 * m
    assert read("Matrix(((1,2),(3,4)))+Matrix(((1,2),(3,4)))") == m + m
    assert read("Matrix(((1,2),(3,4)))**2") == m ** 2
    assert read("-Matrix(((1,2),(3,4)))") == -m


@pytest.mark.parametrize("text", ["Tuple(1,2)*3", "3*Tuple(1,2)", "Tuple(1,2)+Tuple(3)", "-Tuple(1,2)", "Tuple(1,2)<Tuple(3)",
                                  "solve(x-1,x)*3", "3*solve(x-1,x)", "solve(x-1,x)+solve(x-2,x)", "-solve(x-1,x)"])
def test_arithmetic_is_never_on_a_tuple_or_a_list(text):
    with pytest.raises(M.ExpressionRefused, match="sympy values only"):
        read(text)


def test_numbers_are_read_as_written():
    long = "0.1234567890123456789012345"
    assert read(long) == sympy.Float(long) and read(long)._prec == sympy.Float(long)._prec
    assert read(long, rational=True) == sympy.Rational(long)
    assert read("0.1") == sympy.Float("0.1") and read("0.1", rational=True) == sympy.Rational(1, 10)
    assert read("1e400") == sympy.Float("1e400")             # past a Python float: the digits, never the float
    assert read("2.5e3", rational=True) == 2500
    assert read("Float(0.5)", rational=True) == sympy.Rational(1, 2)   # sympy's rational read rewrites the name too


# ── BOUNDS: each limit at its edge, on the tree ───────────────────────────────────────────────────────────────
def test_the_text_limit_at_its_edge():
    assert read("a" * 4000) == sympy.Symbol("a" * 4000)
    assert read("1" * 4000) == int("1" * 4000)
    with pytest.raises(M.ExpressionRefused, match="too long"):
        read("a" * 4001)


def test_the_text_limit_holds_for_the_text_parsed_not_the_text_written():
    written = "Max(" + ",".join(["2^2"] * 900) + ")"
    assert len(written) <= 4000 < len(written.replace("^", "**"))
    with pytest.raises(M.ExpressionRefused, match="too long"):
        read(written)


def test_the_node_limit_at_its_edge():
    assert read("Max(" + ",".join(["1"] * 1996) + ")") == 1          # exactly 2,000 nodes
    with pytest.raises(M.ExpressionRefused, match="too large"):
        read("Max(" + ",".join(["1"] * 1997) + ")")


def test_the_depth_limit_at_its_edge():
    x = sympy.Symbol("x")
    assert read("-" * 56 + "x") == x
    assert read("-" * 57 + "x") == -x                                # exactly 60 deep
    with pytest.raises(M.ExpressionRefused, match="too deeply nested"):
        read("-" * 58 + "x")


@pytest.mark.parametrize("edge, past", [
    ("x**10000", "x**10001"), ("x^10000", "x^10001"), ("2**10000", "2**10001"), ("2^10000", "2^10001"),
    ("Pow(2,10000)", "Pow(2,10001)"), ("Pow(x,10000)", "Pow(x,10001)"), ("x**-10000", "x**-10001"),
    ("Pow(x,-10000)", "Pow(x,-10001)"), ("x**10000.0", "x**10000.5"), ("x**(5000*2)", "x**(5000*2+1)"),
    ("Integer(2)**10000", "Integer(2)**10001"), ("2**Pow(10,4)", "2**(Pow(10,4)+1)"),
])
def test_the_exponent_limit_at_its_edge(edge, past):
    read(edge)
    with pytest.raises(M.ExpressionRefused, match="exponent too large"):
        read(past)


def test_the_exponent_limit_reads_the_third_argument_of_the_function_form_too():
    with pytest.raises(M.ExpressionRefused, match="exponent too large"):
        read("Pow(2,10001,x)")


@pytest.mark.parametrize("text", ["2**oo", "x**oo", "2**-oo"])
def test_an_infinite_exponent_is_no_number_to_limit(text):
    read(text)


@pytest.mark.parametrize("text", ["x**y**2", "x**(y**2)", "2**(3**2)", "2^3^2", "x**sin(y**2)"])
def test_a_power_in_the_exponent_is_refused(text):
    with pytest.raises(M.ExpressionRefused, match="tower"):
        read(text)


@pytest.mark.parametrize("edge, past", [
    ("(2**1000)**1047", "(2**1000)**1048"),                      # 1,001 bits a side: 1,047 of them fit in 2**20
    ("(2^1000)^1047", "(2^1000)^1048"),
    ("Pow(Pow(2,1000),1047)", "Pow(Pow(2,1000),1048)"),
    ("Pow(2**1000,1047)", "Pow(2**1000,1048)"),
    ("(2**1000)**-1047", "(2**1000)**-1048"),
    ("(1/2**1000)**1047", "(1/2**1000)**1048"),                  # a rational base
    ("(3/2**1000)**1047", "(3/2**1000)**1048"),
    ("Pow(1/2**1000,1047)", "Pow(1/2**1000,1048)"),
    ("Rational(1,2**1000)**1047", "Rational(1,2**1000)**1048"),
    ("(2**1000*x)**1047", "(2**1000*x)**1048"),                  # a coefficient multiplies out under the exponent
    ("(2**1000*sqrt(3))**1046", "(2**1000*sqrt(3))**1047"),      # every factor counts: the root takes its share
    ("Integer(2**1000)**1047", "Integer(2**1000)**1048"),
])
def test_the_bits_cap_at_its_edge(edge, past):
    read(edge)
    with pytest.raises(M.ExpressionRefused, match="power too large"):
        read(past)


# Neither is a perfect power, so a root of one stays a root, shows no integer, and sympy multiplies the exponents out into
# one integer power as the outer power is built. 1,001 bits to a step: 1,047 steps fit in 2**20, and 1,048 do not.
B, C = "(2**1000+1)", "(2**999+1)"
MATRIX = f"Matrix((({B},0),(0,1)))"
ROOT_EDGES = {
    "operator": (f"({B}**(1/2))**{{}}", 2094),
    "caret": ("((2^1000+1)^(1/2))^{}", 2094),
    "Pow on a Pow": (f"Pow(Pow({B},1/2),{{}})", 2094),
    "Pow on an operator": (f"Pow({B}**(1/2),{{}})", 2094),
    "sqrt": (f"sqrt({B})**{{}}", 2094),
    "Pow on sqrt": (f"Pow(sqrt({B}),{{}})", 2094),
    "cbrt": (f"cbrt({B})**{{}}", 3141),
    "root": (f"root({B},2)**{{}}", 2094),
    "negative exponent": (f"({B}**(1/2))**-{{}}", 2094),
    "near one": (f"({B}**(9999/10000))**{{}}", 1047),
    "a root of a root": (f"(({B}**(1/2))**(1/2))**{{}}", 4188),
    "a rational under the root": (f"((3/{B})**(1/2))**{{}}", 698),
    "a product of roots": (f"(sqrt({B})*sqrt({C}))**{{}}", 1048),
    "a symbol beside the root": (f"((x*sqrt({B}))**(1/2))**{{}}", 4188),
    "a negative base": (f"(-sqrt({B}))**{{}}", 2090),
    "an imaginary base": (f"(I*sqrt({B}))**{{}}", 2094),
    "a piece of a Piecewise": (f"Piecewise(({B},x<1),(1,true))**{{}}", 1047),
    "a root in a Piecewise": (f"Piecewise((sqrt({B}),x<1),(1,true))**{{}}", 2094),
    "an entry of a Matrix": (f"Matrix((({B},0),(0,1)))**{{}}", 1045),
    "an entry of a diag": (f"diag({B},1)**{{}}", 1045),
    # Default-deny: a base the walk does not read counts every Rational inside it, so each carrier has this edge.
    "a constant Poly": (f"Poly({B},x)**{{}}", 1047),
    "a Poly term": (f"Poly({B}*x,x)**{{}}", 1047),
    "a Transpose": (f"Transpose({MATRIX})**{{}}", 1045),
    "an Inverse": (f"Inverse({MATRIX})**{{}}", 1044),
    "a root of a matrix": (f"({MATRIX}**(1/2))**{{}}", 2086),
    "a root of a Transpose": (f"(Transpose({MATRIX})**(1/2))**{{}}", 2086),
    "a function it does not know": (f"sin({B})**{{}}", 1047),
    "a sum": (f"(x+{B})**{{}}", 1047),
    "a root in a sum": (f"(1+sqrt({B}))**{{}}", 2090),
    "a set": (f"Interval(0,{B})**{{}}", 1046),
    "a symbolic power": (f"({B}**x)**{{}}", 1047),
}


@pytest.mark.parametrize("spelling", sorted(ROOT_EDGES))
def test_the_bits_cap_at_its_edge_on_what_a_base_hides(spelling):
    text, edge = ROOT_EDGES[spelling]
    read(text.format(edge))
    with pytest.raises(M.ExpressionRefused, match="power too large"):
        read(text.format(edge + 1))
    with pytest.raises(M.ExpressionRefused, match="power too large"):
        read(text.format(9999))


def test_the_bits_cap_at_its_edge_on_a_poly_of_two_terms():
    """Both sides by the bound alone. Each coefficient fits the cap and there are n of them, so building it at this edge
    ran past 18 s: the cap binds an integer, not how many there are."""
    base = read(f"Poly({B}*x+1,x)")
    assert M._power_bits(base, sympy.Integer(1046)) <= M._MAX_POW_BITS < M._power_bits(base, sympy.Integer(1047))
    with pytest.raises(M.ExpressionRefused, match="power too large"):
        read(f"Poly({B}*x+1,x)**1047")


def largest_integer(value) -> int:
    if isinstance(value, sympy.MatrixBase):
        return max(largest_integer(entry) for entry in value)
    return max([max(int(a.p).bit_length(), int(a.q).bit_length()) for a in value.atoms(sympy.Rational)] or [0])


@pytest.mark.parametrize("base, exponent", [
    ("2**1000", 1000), (f"sqrt({B})", 2000), (f"cbrt({B})", 3000), (f"{B}**(9999/10000)", 1000), (f"sqrt({B})*sqrt({C})", 1000),
    (f"(3/{B})**(1/2)", 600), (f"(x*sqrt({B}))**(1/2)", 4000), (f"Piecewise(({B},x<1),(1,true))", 1000),
    (f"Matrix((({B},1),(1,1)))", 500), ("Matrix(((1,1),(1,0)))", 9999), ("(1+sqrt(2))", 100), ("x", 10000), ("sin(2**100)", 3),
    (f"Poly({B},x)", 1000), (f"Poly({B}*x+1,x)", 8), (f"Transpose(Matrix((({B},1),(1,1))))", 500), (f"{MATRIX}**(1/2)", 1000),
])
def test_the_bound_is_an_upper_bound_on_what_the_power_holds(base, exponent):
    value = read(base)
    assert largest_integer(value ** exponent) <= M._power_bits(value, sympy.Integer(exponent)) + largest_integer(value) + 32


@pytest.mark.parametrize("text", ["((2**1000)**1000)**2", "(((2**100)**100)**100)**100", "factorial(1000)**10000",
                                  "(3**4999*sqrt(3))**9999", "sqrt(3**9999)**9999", "(2**1000)**(3000/2)",
                                  f"({B}**(1/2))**10000", f"sqrt({B})**10000", f"Pow(sqrt({B}),10000)", f"cbrt({B})**9999",
                                  f"({B}**(9999/10000))**10000", f"({B}**(1/2))**-10000", f"(sqrt({B})*sqrt({C}))**10000"])
def test_the_bits_cap_holds_however_the_base_was_built(text):
    with pytest.raises(M.ExpressionRefused, match="power too large"):
        read(text)


@pytest.mark.parametrize("exponent, fits", [("999/1000", True), ("1", True), ("1001/1000", False), ("3/2", False), ("1999/1000", False)])
def test_a_fractional_exponent_rounds_the_bound_up_and_never_down(exponent, fits):
    text = f"((2**10000)**104)**({exponent})"       # 1,040,001 bits, so one step fits and two do not
    if fits:
        read(text)
    else:
        with pytest.raises(M.ExpressionRefused, match="power too large"):
            read(text)


# The evaluated read takes each of these: the base collapses to 1. In the unevaluated read it stands whole, and a call there
# still multiplies: the Pow function evaluates, and so do simplify and Integer around the operator.
LARGE = "(2**1000)"
COLLAPSED = [
    f"Pow({LARGE}/{LARGE},10000)", f"Pow({LARGE}-{LARGE}+1,10000)", f"Pow({LARGE}*0+1,10000)", f"({LARGE}/{LARGE})**10000",
    f"simplify(({LARGE}/{LARGE})**10000)", f"Integer(({LARGE}/{LARGE})**10000)", f"expand(({LARGE}/{LARGE})**10000)",
    f"Max(({LARGE}/{LARGE})**10000,0)", f"sqrt(({LARGE}/{LARGE})**10000)", f"Mod(({LARGE}/{LARGE})**10000,7)",
    f"Pow({LARGE}/{LARGE},5000*2)", f"simplify(({LARGE}/{LARGE})**(5000*2))",     # an exponent left written out
    "Pow(((2**10)**(10*10))/((2**10)**(10*10)),10000)",                         # and one inside the base
]


@pytest.mark.parametrize("text", COLLAPSED)
def test_the_power_limits_bind_the_unevaluated_read_too(text):
    assert read(text) == 1
    with pytest.raises(M.PowerRefused):
        read(text, evaluate=False)


@pytest.mark.parametrize("text", COLLAPSED)
def test_a_refusal_in_the_unevaluated_read_is_not_checkable_and_never_no_mismatch(text):
    """A pole that could not be looked for is no answer. It was HOLDS at the step's base, after the power was multiplied out."""
    with pytest.raises(M.PowerRefused):
        M._domain_mismatch(text, "1", [])
    r = mode("equality", {"expr_a": text, "expr_b": "1"})
    assert r["verdict"] == "INCOMPLETE", r
    assert not r.get("seal")


@pytest.mark.parametrize("a, b", [
    (f"x/x + Pow({LARGE}/{LARGE},10000)", "2"),                     # a pole beside the refused power: reading it as no
    (f"x/x + ({LARGE}/{LARGE})**10000", "2"),                       # mismatch would read HOLDS
    ("x/x + (2**1000)**1047", "1 + (2**1000)**1047"),               # the unevaluated measure runs high on a small base,
    ("x/x + Pow(2**1000,1047)", "1 + Pow(2**1000,1047)"),           # and that too must fail closed
])
def test_a_pole_beside_a_refused_power_never_reads_holds(a, b):
    assert mode("equality", {"expr_a": a, "expr_b": b})["verdict"] == "INCOMPLETE"


@pytest.mark.parametrize("name", ["ValueError", "TypeError", "ZeroDivisionError", "RecursionError", "ExpressionRefused"])
def test_every_other_failed_unevaluated_read_stays_no_mismatch(monkeypatch, name):
    """Only the power limits fail closed: the wider case is a want, and SAME READINGS binds this step."""
    failure = getattr(M, name, None) or getattr(builtins, name)

    def fails(*_args, **_kwargs):
        raise failure("x")
    monkeypatch.setattr(M, "_parse", fails)
    assert M._domain_mismatch("x/x", "1", []) is None


@pytest.mark.parametrize("text", ["Pow(2/2,10000)", "(2/2)**10000", "Pow(x/x,3)", "x**10000", "(2**10)**1000"])
def test_a_power_inside_the_limits_reads_in_both_reads(text):
    read(text)
    read(text, evaluate=False)


def test_an_exponent_is_bound_by_its_value_in_the_unevaluated_read():
    read("x**(5000*2)", evaluate=False)
    with pytest.raises(M.PowerRefused, match="exponent too large"):
        read("x**(5000*2+1)", evaluate=False)


def test_an_exponent_that_will_not_rebuild_never_fails_a_read():
    """It is no number to bound. A failure here would be an ordinary failed read, which an unevaluated read takes as no pole."""
    held = "Matrix(((x,0),(0,y)))"
    read(f"2**((0.5/{held})/(1-{held}))", evaluate=False)


def test_bounding_a_power_runs_nothing_in_its_exponent():
    written = sympy.Sum(sympy.Symbol("k"), (sympy.Symbol("k"), 1, 10))
    assert M._settled(written) is written


@pytest.mark.parametrize("text, count", [
    ("x+(y+z)", 3), ("(x+y)+z", 3), ("(x+y)+(z+w)", 4), ("x+(y-z)", 3), ("x-y-z", 3), ("x*(y*z)", 3), ("(x*y)*z", 3),
    ("(x*y)*(z*w)", 4), ("x*(y/z)", 3), ("x/y/z", 3), ("x-(y+z)", 2), ("x/(y*z)", 2), ("-(x+y)+z", 2), ("expand(x+y)+z", 2),
    ("z+expand(x+y)", 2), ("expand(x*y)*z", 2), ("x+sin(y+z)", 2),
])
def test_the_unevaluated_build_flattens_what_the_text_wrote_and_nothing_else(text, count):
    assert len(read(text, evaluate=False).args) == count


def test_the_unevaluated_build_flattens_the_tree_not_the_value():
    """A product holding a matrix is a matrix once built, so it can only be flattened before it is built."""
    assert M._domain_mismatch("(z*Matrix(((1,2),(3,4))))/z", "Matrix(((1,2),(3,4)))", []) == "z"


def test_the_bits_cap_is_two_to_the_twenty():
    assert M._MAX_POW_BITS == 2 ** 20
    assert 1001 * 1047 <= 2 ** 20 < 1001 * 1048


@pytest.mark.parametrize("rational", [False, True])
def test_a_written_decimal_exponent_is_held_to_the_exponent_limit(rational):
    read("1e10000", rational=rational)
    read("1e-10000", rational=rational)
    for text in ("1e10001", "1e-10001", "1E10001", "2.5e10001", "1e10_001", "1e999999999", "1e-999999999"):
        with pytest.raises(M.ExpressionRefused, match="exponent too large"):
            read(text, rational=rational)


@pytest.mark.parametrize("text", ["x" + "+x" * 1999, "x" + "*x" * 1999, "-" * 3999 + "x", "(" * 1999 + "x" + ")" * 1999,
                                  "sin(" * 500 + "x" + ")" * 500],
                         ids=["sums", "products", "signs", "parentheses", "calls"])
def test_a_long_chain_is_a_refusal_never_an_unhandled_error(text):
    assert len(text) <= 4000
    refused(text)


@pytest.mark.parametrize("failure", [RuntimeError("inside the call"), RecursionError(), MemoryError(), KeyError("k"),
                                     ZeroDivisionError(), AttributeError("a")])
def test_any_failure_inside_the_walk_is_a_refusal(monkeypatch, failure):
    def fails(*_args):
        raise failure
    monkeypatch.setitem(M._FUNCTIONS, "sin", fails)
    refused("sin(1)")


@pytest.mark.parametrize("text", ["1\x00", "\ud800", "", "   ", "1 +", "x y", "(", "Mod(1,0)", "1\n2"],
                         ids=["null", "surrogate", "empty", "blank", "open", "two-names", "paren", "modulo-zero", "two-lines"])
def test_text_that_cannot_be_read_is_a_refusal(text):
    refused(text)


# ── EVERY CALLER ──────────────────────────────────────────────────────────────────────────────────────────────
def test_domain_mismatch_reads_the_text_parse_read():
    """Word mod and caret spellings once hid a pole from the unevaluated read, which took the raw text."""
    assert M._domain_mismatch("x/x + (5 mod 3)", "3", []) == "x"
    assert M._domain_mismatch("  x/x  ", "1", []) == "x"
    assert M._domain_mismatch("x^2/x", "x", []) == "x"
    assert mode("equality", {"expr_a": "x/x + (5 mod 3)", "expr_b": "3"})["verdict"] == "BROKEN"


def test_domain_mismatch_keeps_each_pole_it_saw_and_reports_none_when_they_match():
    assert M._domain_mismatch("x/x", "1", []) == "x"
    assert M._domain_mismatch("1/(x-1)", "1/(x-1)", []) is None
    assert M._domain_mismatch("(x**2-1)/(x-1)", "x+1", []) == "x - 1*1"    # sympy's own unevaluated form
    assert M._domain_mismatch("1 +", "1", []) is None             # a refused text never raises here


FRESH_PHYSICS_FIRST = """
import json
from concordance.verifiers import physics
out = [physics.verify_dimensional_consistency('F = m.a', {'F': 'newton', 'm': 'kilogram', 'a': 'meter'}).status,
       physics.verify_dimensional_consistency('F = m*a', {'F': 'x.y', 'm': 'kilogram', 'a': 'meter'}).status,
       physics.verify_dimensional_consistency('F = m*a', {'F': 'newton', 'm': 'kilogram', 'a': 'meter/second**2'}).status]
from concordance.verifiers import mathematics
out.append(mathematics.verify_equality({'expr_a': 'x.y', 'expr_b': '1'}).status)
print(json.dumps(out))
"""
FRESH_MATHEMATICS_FIRST = """
import json
from concordance.verifiers import mathematics
out = [mathematics.verify_equality({'expr_a': 'x.y', 'expr_b': '1'}).status,
       mathematics.verify_equality({'expr_a': '2+2', 'expr_b': '4'}).status]
from concordance.verifiers import physics
out.append(physics.verify_dimensional_consistency('F = m.a', {'F': 'newton', 'm': 'kilogram', 'a': 'meter'}).status)
print(json.dumps(out))
"""
FRESH_PARSER_ALONE = """
import json
from concordance.verifiers import mathematics
assert mathematics._SympifyError is None                     # nothing has loaded sympy yet
try:
    mathematics.parse_expression('x.y')
    out = 'read'
except mathematics._PARSE_ERRORS as e:
    out = type(e).__name__
print(json.dumps(out))
"""


def test_the_parser_works_in_a_fresh_interpreter_whichever_verifier_is_imported_first():
    """A refusal must be clean before anything has loaded sympy: _SympifyError is None until then."""
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    runs = [subprocess.Popen([sys.executable, "-c", code], cwd=str(ROOT), env=env, text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for code in (FRESH_PHYSICS_FIRST, FRESH_MATHEMATICS_FIRST, FRESH_PARSER_ALONE)]
    got = []
    for run in runs:
        out, err = run.communicate(timeout=120)
        assert run.returncode == 0, err
        got.append(json.loads(out.strip().splitlines()[-1]))
    assert got[0] == ["NOT_APPLICABLE", "NOT_APPLICABLE", "CONFIRMED", "NOT_APPLICABLE"]
    assert got[1] == ["NOT_APPLICABLE", "CONFIRMED", "NOT_APPLICABLE"]
    assert got[2] == "ExpressionRefused"


@pytest.mark.parametrize("equation, symbols, verdict", [
    ("F = m*a", NEWTON, "HOLDS"),
    ("F = m*a", {"F": "newton", "m": "kg", "a": "m/s^2"}, "HOLDS"),
    ("F = m*a", {"F": "newton", "m": "kg", "a": "m/s**2"}, "HOLDS"),
    ("F = m*a", {"F": "  newton", "m": " kilogram ", "a": "\tmeter/second**2"}, "HOLDS"),
    ("  F  =  m * a  ", NEWTON, "HOLDS"),
    ("E = m*c^2", {"E": "joule", "m": "kilogram", "c": "meter/second"}, "HOLDS"),
    ("F = m", NEWTON, "BROKEN"),
    ("v = sqrt(2*g*h)", {"v": "meter/second", "g": "meter/second**2", "h": "meter"}, "HOLDS"),
    ("T = 2*pi*sqrt(L/g)", {"T": "second", "L": "meter", "g": "meter/second**2"}, "HOLDS"),
    ("z = inf", {"z": "1"}, "BROKEN"),            # undeclared in physics, inf stays a symbol: it is no constant here
    ("gamma = m", {"gamma": "kilogram", "m": "kg"}, "HOLDS"),   # a caller's name wins over a function's name
    ("F = mod*a", {"F": "newton", "mod": "kilogram", "a": "meter/second**2"}, "HOLDS"),   # mod is a name in physics
    ("F = MOD*a", {"F": "newton", "MOD": "kilogram", "a": "meter/second**2"}, "HOLDS"),
])
def test_physics_reads_a_claim_as_it_did(equation, symbols, verdict):
    assert post("physics", {"PHYS_VERIFY": {"equation": equation, "symbols": symbols}})["verdict"] == verdict


def test_physics_here_never_read_a_dimensions_key_and_still_does_not():
    """V3's run() reads this key beside symbols; this repo's never did, so the parser's caller is gated on symbols alone.
    Reading it now would move a packet from INCOMPLETE to HOLDS, and no reading moves that way in this port."""
    assert post("physics", {"PHYS_VERIFY": {"equation": "F = m*a", "dimensions": NEWTON}})["verdict"] == "INCOMPLETE"
    assert post("physics", {"PHYS_VERIFY": {"equation": "F = m.a", "dimensions": NEWTON}})["verdict"] == "INCOMPLETE"
    assert [r.name for r in P.run({"PHYS_VERIFY": {"equation": "F = m.a", "dimensions": {}}})] == ["physics"]


@pytest.mark.parametrize("key", ["a b", "1x", "x.y", "x-y", "_v", "__x", "lambda", "", "µ", 7])
def test_a_symbols_key_must_be_a_plain_identifier(key):
    symbols = {"F": "newton", key: "kilogram"}
    results = P.run({"PHYS_VERIFY": {"equation": "F = F", "symbols": symbols}})
    assert [r.status for r in results] == ["NOT_APPLICABLE"]


# ── A REFUSAL NEVER PASSES ────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("refused_text", ["1 +", "x.y", "print", "2^20000", "x**10001", f"({B}**(1/2))**10000",
                                          f"Pow(sqrt({B}),10000)"])
@pytest.mark.parametrize("name, params, verdict", [
    ("equality", {"expr_a": "{t}", "expr_b": "1"}, "INCOMPLETE"),
    ("equality", {"expr_a": "1", "expr_b": "{t}"}, "INCOMPLETE"),
    ("solve", {"equation": "x = {t}", "claimed_solutions": ["1"]}, "INCOMPLETE"),
    ("solve", {"equation": "x = 1", "claimed_solutions": ["{t}"]}, "INCOMPLETE"),
    ("derivative", {"function": "{t}", "variable": "x", "claimed_derivative": "1"}, "INCOMPLETE"),
    ("integral", {"integrand": "{t}", "variable": "x", "claimed_antiderivative": "1"}, "INCOMPLETE"),
    ("limit", {"function": "{t}", "variable": "x", "point": "0", "claimed_limit": "1"}, "INCOMPLETE"),
    ("numeric", {"numeric_expr": "{t}", "claimed_value": 2}, "SYSTEM_ERROR"),
    ("inequality", {"lhs": "{t}", "rhs": "1", "op": "<="}, "SYSTEM_ERROR"),
    ("system", {"equations": ["x = {t}"], "claimed_solution": {"x": 1}}, "SYSTEM_ERROR"),
    ("system", {"equations": ["x = 1"], "claimed_solution": {"x": "{t}"}}, "SYSTEM_ERROR"),
    ("calc_chain", {"calc_steps": ["{t} = 2"]}, "BROKEN"),
])
def test_each_mode_keeps_its_reading_of_a_refused_text(name, params, verdict, refused_text):
    filled = json.loads(json.dumps(params).replace("{t}", refused_text))
    r = mode(name, filled)
    assert r["verdict"] == verdict and r["verdict"] != "HOLDS", r
    assert not r.get("seal")


REFUSED_PACKETS = {
    "refused equation": {"equation": "F = m.a", "symbols": NEWTON},
    "refused left side": {"equation": "F.x = m*a", "symbols": NEWTON},
    "syntax error": {"equation": "F = 1 +", "symbols": NEWTON},
    "second equals": {"equation": "F == m*a", "symbols": NEWTON},
    "refused unit": {"equation": "F = m*a", "symbols": {"F": "newton", "m": "kilogram.x", "a": "meter/second**2"}},
    "unit too large": {"equation": "F = m*a", "symbols": {"F": "2^20000", "m": "kilogram", "a": "meter/second**2"}},
    "non-text unit": {"equation": "F = m*a", "symbols": {"F": 5, "m": "kilogram", "a": "meter/second**2"}},
    "non-text equation": {"equation": 5, "symbols": NEWTON},
    "symbols a list": {"equation": "F = m*a", "symbols": ["F", "m", "a"]},
    "symbols a text": {"equation": "F = m*a", "symbols": "F"},
    "symbols a number": {"equation": "F = m*a", "symbols": 5},
    "symbols empty": {"equation": "F = m*a", "symbols": {}},
    "symbols null": {"equation": "F = m*a", "symbols": None},
    "key not plain": {"equation": "F = m*a", "symbols": {"F": "newton", "m a": "kilogram"}},
    "key underscored": {"equation": "F = F", "symbols": {"F": "newton", "_v": "kilogram"}},
    "name nfkc changes": {"equation": "F = F", "symbols": {"F": "newton", "µ": "kilogram"}},
}


@pytest.mark.parametrize("case", sorted(REFUSED_PACKETS))
def test_a_refused_packet_is_one_not_applicable_and_nothing_else(case):
    results = P.run({"PHYS_VERIFY": dict(REFUSED_PACKETS[case], **PASSING_CHECK)})
    assert [r.status for r in results] == ["NOT_APPLICABLE"]


@pytest.mark.parametrize("case", sorted(REFUSED_PACKETS))
def test_a_passing_check_beside_a_refused_packet_cannot_lift_it(case):
    r = post("physics", {"PHYS_VERIFY": dict(REFUSED_PACKETS[case], **PASSING_CHECK)})
    assert r["verdict"] == "INCOMPLETE", r
    assert not r.get("seal")


def test_the_passing_check_alone_does_hold():
    assert post("physics", {"PHYS_VERIFY": dict(PASSING_CHECK)})["verdict"] == "HOLDS"


def test_a_passing_check_beside_a_claim_that_reads_keeps_both():
    packet = dict(PASSING_CHECK, equation="F = m*a", symbols=NEWTON)
    assert [r.status for r in P.run({"PHYS_VERIFY": packet})] == ["CONFIRMED", "CONFIRMED"]
    assert post("physics", {"PHYS_VERIFY": packet})["verdict"] == "HOLDS"
    packet = dict(PASSING_CHECK, equation="F = m", symbols=NEWTON)
    assert post("physics", {"PHYS_VERIFY": packet})["verdict"] == "BROKEN"


def test_an_equation_with_no_equals_still_reads_an_error():
    r = P.run({"PHYS_VERIFY": {"equation": "F", "symbols": NEWTON}})
    assert [x.status for x in r] == ["ERROR"]


# ── THE INTEGER-CALL CLASS, THE ONE MOVE TOWARD HOLDS THE PLAN NAMES ──────────────────────────────────────────
# A call to an integer-returning allowlisted function, or arithmetic on such calls, reads as a sympy value, as V3 reads it.
# A plain int crashed several modes at the step's base, and divided in floats in others, so a true claim moves from
# SYSTEM_ERROR or BROKEN to HOLDS. Each mode holds a true claim reading HOLDS and its false sibling reading BROKEN, so the
# move is a reading and no blanket pass.
INTEGER_CALLS = [("igcd(4,6)", 2), ("igcd(4,6)*ilcm(1,3)", 6), ("igcd(4,6)+ilcm(2,3)", 8), ("nextprime(7)", 11),
                 ("prevprime(7)", 5), ("-igcd(4,6)", -2), ("igcd(12,18)/igcd(4,6)", 3), ("igcd(1,1)/igcd(3,3)", Fraction(1, 3)),
                 ("igcd(4,6)/ilcm(2,3)", Fraction(1, 3))]


def integer_claim(name, text, value):
    return {
        "equality": {"expr_a": text, "expr_b": str(value)},
        "inequality": {"lhs": text, "rhs": str(value), "op": "<="},
        "system": {"equations": [f"x = {text}"], "claimed_solution": {"x": str(value)}},
        "solve": {"equation": f"x = {text}", "variable": "x", "claimed_solutions": [str(value)]},
        "derivative": {"function": f"({text})*x", "variable": "x", "claimed_derivative": str(value)},
        "integral": {"integrand": text, "variable": "x", "claimed_antiderivative": f"({value})*x"},
        "limit": {"function": f"({text})*x", "variable": "x", "point": "1", "claimed_limit": str(value)},
        "numeric": {"numeric_expr": text, "claimed_value": float(value)},
        "calc_chain": {"calc_steps": [f"{text} = {value}"]},
    }[name]


@pytest.mark.parametrize("text, value", INTEGER_CALLS)
@pytest.mark.parametrize("name", ["equality", "inequality", "system", "solve", "derivative", "integral", "limit", "numeric",
                                  "calc_chain"])
def test_an_integer_call_reads_a_true_claim_holds_and_its_false_sibling_broken(name, text, value):
    assert mode(name, integer_claim(name, text, value))["verdict"] == "HOLDS"
    assert mode(name, integer_claim(name, text, value - 1))["verdict"] == "BROKEN"


@pytest.mark.parametrize("text, _value", INTEGER_CALLS)
def test_an_integer_call_on_a_physics_side_reads_true_and_false_by_its_units(text, _value):
    assert post("physics", {"PHYS_VERIFY": {"equation": f"x = {text}", "symbols": {"x": "1"}}})["verdict"] == "HOLDS"
    assert post("physics", {"PHYS_VERIFY": {"equation": f"x = {text}", "symbols": {"x": "meter"}}})["verdict"] == "BROKEN"


# ── THE OBSERVER THE ROUTE TESTS STAND ON ─────────────────────────────────────────────────────────────────────
SEALS_MOVE = """
import json
from concordance.config import EngineConfig
from concordance.web import api
config = EngineConfig("secular")
def count():
    seals = api.dispatch("GET", "/seals", {}, None, config)[1]["seals"]
    chain = api.dispatch("GET", "/sync/ledger", {"hashes_only": "1"}, None, config)[1]
    return [seals["minted"], chain["count"], chain["head"]]
body = {"mode": "equality", "params": {"expr_a": "2+2", "expr_b": "4"}}
empty = count()
off = api.dispatch("POST", "/verify", {"seal": "0"}, body, config)[1]["verdict"]
unmoved = count()
sealed = api.dispatch("POST", "/verify", {}, body, config)[1]
print(json.dumps([empty, off, unmoved, sealed["seal"]["ledgered"], count()]))
"""


def test_the_seal_count_moves_when_a_seal_is_written_and_stays_when_sealing_is_off(tmp_path):
    """tests/test_parse_route.py reads no-seal from this count, since this repo has no /ledger/verify. It lives here because
    every test in that file must be red at the step's base, and this control is green there by design. It runs in a process
    of its own because a real seal folds its cards into the process's corpus, which every later test would then read."""
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), CONCORDANCE_DATA_DIR=str(tmp_path),
               CONCORDANCE_CAS_DIR=str(tmp_path / "cas"))
    run = subprocess.run([sys.executable, "-c", SEALS_MOVE], cwd=str(ROOT), env=env, capture_output=True, encoding="utf-8",
                         errors="replace", timeout=120)
    assert run.returncode == 0, run.stderr
    empty, off, unmoved, ledgered, after = json.loads(run.stdout.strip().splitlines()[-1])
    assert off == "HOLDS" and unmoved == empty
    assert ledgered is True
    assert after[0] == empty[0] + 1 and after[1] == empty[1] + 1 and after[2] != empty[2]
