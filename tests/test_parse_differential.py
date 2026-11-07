"""SAME READINGS: the parser reads what sympify read, and sympify runs here, in this test, and nowhere else.

Every expression these sources carry is read through the parser and through sympy's sympify, and the two are structurally
equal, with rational=True too; the unevaluated build is compared by its pole sets:

    tools/benchmark.py            CLAIMS, read from the packets
    data/domain_goldens.json      every true and false packet, read from the packets
    src/concordance/compendium.py every step of every demonstration, read from the packets
    eval/live_probes.jsonl        every packet a probe's body holds, and each plain sentence, run through audit
    src/concordance/audit.py      the forms extract builds from the front door's, recall's and the probes' sentences
    tests/test_frontdoor.py       the real run over data/frontdoor_claims.json, recorded at the parser
    tests/test_recall.py          the real run over data/recall_phrasings.json, recorded at the parser
    tools/tick.py                 every stick in the catalog, recorded at the parser, since its texts are f-strings

tests/fixtures/parse_recorder.py does the running and the recording, in a process of its own. A fixed table of forms the
sources may not show is read the same way. A form the parser refuses and sympify read is listed here by name with its
reason, and a form this list does not name fails. The parser side of each read runs under the tripwire, armed around it
alone, because the oracle parses text on purpose.

The table also holds false claims the sources cannot show, read through every mode they reach, and none reads HOLDS.
Every input here is inert: the oracle evaluates only these sources and the literal table below.
"""
from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterator, List, Tuple

import pytest
import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests" / "fixtures"))

import benchmark  # noqa: E402
from concordance import compendium  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.verifiers import mathematics as M  # noqa: E402
from concordance.verifiers import physics as P  # noqa: E402
from concordance.web import api  # noqa: E402
from parse_tripwire import tripwire  # noqa: E402

CONFIG = EngineConfig("secular")
pytestmark = pytest.mark.filterwarnings("ignore")

# Fields a mathematics mode reads whole, in any packet that carries them.
MATH_FIELDS = ("expr_a", "expr_b", "function", "claimed_derivative", "integrand", "claimed_antiderivative", "point",
               "claimed_limit", "lhs", "rhs", "numeric_expr")

# Each text in these sources that the parser refuses and sympify takes, with its reason. None does, measured 2026-11-04.
SOURCES_REFUSED: Dict[str, str] = {}

# The least each source may give, in distinct reads, set just under what each gave on 2026-11-04. A source that gives
# none, or a run that read a test's fixture in place of the shipped data, stops here. The counts print when the test runs.
LEAST = {"tools/benchmark.py": 60, "data/domain_goldens.json": 3, "src/concordance/compendium.py": 10,
         "eval/live_probes.jsonl": 10, "src/concordance/audit.py": 60, "tests/test_frontdoor.py": 6,
         "tests/test_recall.py": 50, "tools/tick.py": 500}


# ── gathering the sources ─────────────────────────────────────────────────────────────────────────────────────
def _packets() -> Iterator[Tuple[str, dict]]:
    """(source, spec) for each packet a static read can see."""
    for _label, spec, _desc in benchmark.CLAIMS:
        yield "tools/benchmark.py", spec
    goldens = json.loads((ROOT / "data" / "domain_goldens.json").read_text(encoding="utf-8"))
    for pair in goldens.values():
        key = pair.get("packet_key")
        for label in ("true", "false"):
            yield "data/domain_goldens.json", ({key: pair[label]} if key else pair[label])
    for demonstration in compendium.DEMONSTRATIONS:
        for step in demonstration["steps"]:
            yield "src/concordance/compendium.py", compendium._packet_for(step.get("domain", ""), step.get("spec") or {})


def _sides(equation) -> List[str]:
    """An equation as the modes split it: at its first '=', unless it holds '=='."""
    text = str(equation)
    return text.split("=", 1) if "=" in text and "==" not in text else [text]


def _math_texts(p: dict) -> Iterator[str]:
    for field in MATH_FIELDS:
        if p.get(field) is not None:
            yield str(p[field])
    if p.get("equation") is not None:
        yield from _sides(p["equation"])
    for equation in p.get("equations") or []:
        yield from _sides(equation)
    claimed = p.get("claimed_solutions")
    for value in claimed if isinstance(claimed, list) else []:
        yield str(value)
    claimed = p.get("claimed_solution")
    for value in claimed.values() if isinstance(claimed, dict) else []:
        yield str(value)
    for step in p.get("calc_steps") or []:
        if isinstance(step, dict):
            yield from (str(step[k]) for k in ("lhs", "rhs", "expr", "result") if step.get(k) is not None)
        elif isinstance(step, str) and "=" in step:
            yield from step.split("=", 1)
    if p.get("claimed_answer") is not None:
        yield str(p["claimed_answer"])
    text = p.get("solution_text")
    if isinstance(text, str):
        for match in M._CALC_ANNOTATION.finditer(text):
            yield from match.groups()
        for match in M._INLINE_EQ.finditer(text):
            yield from (M._norm_inline(g) for g in match.groups())
        for match in M._FINAL_ANSWER.finditer(text):
            yield match.group(1).replace(",", "")


def _math_names(p: dict) -> Tuple[str, ...]:
    names = list(p.get("variables") or [])
    if isinstance(p.get("variable"), str):
        names.append(p["variable"])
    if isinstance(p.get("claimed_solution"), dict):
        names.extend(p["claimed_solution"])
    return tuple(sorted(set(names)))


def _reads(spec: dict) -> Iterator[Tuple[str, str, Tuple[str, ...]]]:
    """(kind, text, names) for each expression a spec carries, as the verifier reads it."""
    math = spec.get("MATH_VERIFY") if "MATH_VERIFY" in spec else spec.get("params") if "mode" in spec else None
    if isinstance(math, dict):
        names = _math_names(math)
        for text in _math_texts(math):
            yield "math", text, names
    phys = spec.get("PHYS_VERIFY")
    if isinstance(phys, dict) and "equation" in phys and "symbols" in phys:
        symbols = phys["symbols"] or {}
        names = tuple(sorted(symbols))
        for text in str(phys["equation"]).split("=", 1):
            yield "equation", text, names
        for unit in symbols.values():
            yield "unit", str(unit), ()


@pytest.fixture(scope="module")
def recorded(tmp_path_factory) -> dict:
    """What tests/fixtures/parse_recorder.py saw, run once and alone. Under coverage in CI this process is not traced."""
    out = tmp_path_factory.mktemp("parse_recorder") / "recorded.json"
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(ROOT / "src"), str(ROOT / "tools")]))
    run = subprocess.run([sys.executable, str(ROOT / "tests" / "fixtures" / "parse_recorder.py"), str(out)], cwd=str(ROOT),
                         env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, encoding="utf-8", errors="replace",
                         timeout=900)
    assert run.returncode == 0, run.stderr[-3000:]
    return json.loads(out.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def corpus(recorded) -> Dict[Tuple[str, str, Tuple[str, ...]], List[str]]:
    """Each distinct read, with the sources that carry it."""
    M._ensure_sympy()
    P._ensure_sympy()
    out: Dict[Tuple[str, str, Tuple[str, ...]], List[str]] = {}

    def add(source: str, read: Tuple[str, str, Tuple[str, ...]]) -> None:
        sources = out.setdefault(read, [])
        if source not in sources:
            sources.append(source)

    for source, spec in _packets():
        for read in _reads(spec):
            add(source, read)
    for source, specs in recorded["forms"].items():
        for spec in specs:
            for read in _reads(spec):
                add(source, read)
    for source, kind, text, names in recorded["reads"]:
        add(source, (kind, text, tuple(names)))
    return out


def _names(kind: str, names: Tuple[str, ...]) -> dict:
    if kind == "unit":
        return dict(P._UNIT_TABLE)
    table = {n: sympy.Symbol(n) for n in names}
    if kind == "math":                         # what mathematics._parse adds; physics never had these
        table.setdefault("oo", sympy.oo)
        table.setdefault("inf", sympy.oo)
    return table


def _parser(text, names, **kw):
    try:
        return M.parse_expression(text, names, **kw), None
    except M.ExpressionRefused as e:
        return None, str(e) or "refused"


@contextlib.contextmanager
def _sympys_own_powers():
    """The power floor lifted for one read and put back, whether that read finished or not."""
    M._ensure_sympy()
    kinds = (sympy.Integer, sympy.Rational)
    floored = [kind._eval_power for kind in kinds]
    for kind, power in zip(kinds, floored):
        kind._eval_power = power.unfloored
    try:
        yield
    finally:
        for kind, power in zip(kinds, floored):
            kind._eval_power = power


def _oracle(text, names, word_mod=False, **kw):
    """sympify, as each caller handed it a text: no surrounding space, and in mathematics the word form of mod. It reads
    raw sympy: this is the record of what sympify reads with no guard of ours, and the parser is measured against that
    record. The power floor is the engine's guard and no part of sympify, so it does not belong here. Under it a row the
    parser refuses and sympify read could no longer say so, and the record would be measuring the engine against itself."""
    with _sympys_own_powers():
        try:
            return sympy.sympify((M._MOD_WORD_RE.sub("%", text) if word_mod else text).strip(), locals=dict(names), **kw), None
        except Exception as e:  # noqa: BLE001 — the oracle's own failure is a reading: it refused
            return None, type(e).__name__


def _same(a, b) -> bool:
    return type(a) is type(b) and bool(a == b) and sympy.srepr(a) == sympy.srepr(b)


def _compare(rows):
    """Read each (label, text, names, kw) through the parser under the tripwire, then through sympify unarmed.
    Returns (differences, refused): each difference named, each form the parser refused and sympify read named."""
    with tripwire() as hits:
        parsed = [_parser(text, names, **kw) for _label, text, names, kw in rows]
    assert hits == [], f"text reached sympy's string parser: {hits[:5]!r}"
    differences, refused = [], []
    for (label, text, names, kw), (got, why) in zip(rows, parsed):
        want, oracle_refused = _oracle(text, names, **kw)
        if why and oracle_refused:
            continue
        if why:
            refused.append(text)
        elif oracle_refused:
            differences.append(f"{label}: the parser read what sympify refused ({oracle_refused}): {text!r}")
        elif kw.get("evaluate", True) is False:
            if M._pole_bases(got) != M._pole_bases(want):
                differences.append(f"{label}: poles differ for {text!r}")
            elif got != want:
                differences.append(f"{label}: the unevaluated build differs for {text!r}")
        elif not _same(got, want):
            differences.append(f"{label}: {text!r} reads {got!r}, sympify {want!r}")
    return differences, refused


# ── the corpus ────────────────────────────────────────────────────────────────────────────────────────────────
def test_each_source_states_how_many_texts_it_gave(corpus, recorded, capsys):
    given = {source: sum(1 for found in corpus.values() if source in found) for source in LEAST}
    with capsys.disabled():
        print(f"\ntexts each source gave: {given}")
        print(f"parser calls at runtime: {recorded['calls']}, over sentences: {recorded['sentences']}")
    short = {source: count for source, count in given.items() if count < LEAST[source]}
    assert short == {}, f"a source gave less than it holds: {given}"
    assert set(LEAST) >= {source for found in corpus.values() for source in found}


def test_the_runtime_sources_read_the_shipped_data_and_not_a_tests_fixture(recorded):
    """The two tests' own fixtures hold two sentences. A count near two is a run that never reached the shipped files."""
    assert recorded["sentences"]["tests/test_frontdoor.py"] > 39 and recorded["calls"]["tests/test_frontdoor.py"] > 20
    assert recorded["sentences"]["tests/test_recall.py"] >= 300 and recorded["calls"]["tests/test_recall.py"] > 200
    assert sum(recorded["calls"].get(s, 0) for s in ("tests/test_frontdoor.py", "tests/test_recall.py")) > 230


def test_every_stick_ran_and_each_that_reached_the_parser_held(recorded):
    """A stick that reached the parser and did not finish would hide what it had yet to read. The ones that never reach it
    finish as they do in a clean clone, some on a table only the box holds. Of those, sources_crosscheck alone builds a
    numeric text, behind that table, so its two forms are written out in FORMS below."""
    entries = recorded["entries"]
    assert len(entries) == sum(1 for _p in (ROOT / "data" / "sticks").glob("*.json"))
    assert {name: rc for name, (rc, calls) in entries.items() if calls and rc} == {}
    assert sum(calls for _rc, calls in entries.values()) == recorded["calls"]["tools/tick.py"] > 500
    assert entries["sources_crosscheck"] == [2, 0]


def test_no_source_reached_the_string_parser_at_runtime(recorded):
    assert recorded["hits"] == [], f"text reached sympy's string parser: {recorded['hits'][:5]!r}"


@pytest.mark.parametrize("kw", [{}, {"rational": True}, {"evaluate": False}], ids=["plain", "rational", "unevaluated"])
def test_every_source_text_reads_the_same(corpus, kw):
    rows = [(f"{kind} {sources[0]}", text, _names(kind, names), dict(kw, word_mod=True) if kind == "math" else kw)
            for (kind, text, names), sources in corpus.items()]
    differences, refused = _compare(rows)
    assert differences == []
    assert set(refused) == set(SOURCES_REFUSED), sorted(set(refused) ^ set(SOURCES_REFUSED))


# ── the fixed table ───────────────────────────────────────────────────────────────────────────────────────────
FORMS = [
    # rationals and decimals, long decimals, every written number
    "1/3", "2/4", "-1/3", "1/3+1/6", "Rational(1,3)", "Rational(0.5)", "Rational(1,3)+0.5", "0.1", "1.5", "2.5e3", "1e-3",
    "1E5", ".5", "5.", "0.1234567890123456789012345", "3.14159265358979323846264338327950288", "1e400", "1_000", "0x10",
    "0b11", "0o7", "1_000.5", "0.1+0.2", "520/1.04", "6*0.1", "100000000000000000000000000",
    # tuples for Sum limits, integrals, products, matrices
    "Sum(k,(k,1,3))", "Sum(1/k**2,(k,1,oo))", "Product(k,(k,1,3))", "Integral(x,(x,0,1))", "summation(k,(k,1,3))",
    "integrate(x,(x,0,1))", "Matrix(((1,2),(3,4)))", "Piecewise((x,x<1),(0,x>=1))", "Piecewise((1,x>0),(0,true))",
    "Matrix(((1,2),(3,4)))*2", "2*Matrix(((1,2),(3,4)))", "Matrix(((1,2),(3,4)))+Matrix(((1,0),(0,1)))", "-Matrix(((1,2),(3,4)))",
    "Matrix(((1,2),(3,4)))**2", "det(Matrix(((1,2),(3,4))))",
    # every operator the parser reads
    "x+y", "x-y", "x*y", "x/y", "x**y", "x^y", "x%3", "16%9", "16 mod 9", "-x", "+x", "--x", "2**-1", "(-1)**(1/2)", "2**0.5",
    "2**10000", "(x**2)**3", "Pow(x,y**2)", "(x+y)**2", "1<2", "x<1", "x<=1", "x>1", "x>=1", "1>2", "  x  ", "(1 +\n2)",
    # sums and products nested every way, for the unevaluated build
    "x+(y+z)", "(x+y)+z", "(x+y)+(z+w)", "x+(y-z)", "x-(y+z)", "x-(y-z)", "x-y-z", "x-y+z", "x*(y*z)", "(x*y)*z", "(x*y)*(z*w)",
    "x*(y/z)", "x/(y*z)", "x/(y/z)", "x/y/z", "-x/y", "-(x+y)", "-(x*y)", "-(x+y)+z", "1/(x+(y+z))", "1/(x*(y*z))", "x/(x*(y*z))",
    "1/(x-(y-z))", "1/(x*(y/z))", "(a+(b+c))**-1", "(x/x)%3", "Mod(x/x,3)", "expand(x+y)+z", "z+expand(x+y)", "expand(x*y)*z",
    "1/(expand(x+y)+z)", "sin(x+(y+z))", "sin(x*(y*z))", "(x+(y+z))*(x*(y*z))", "x<(y+(z+w))", "(z*Matrix(((1,2),(3,4))))/z",
    "x*Matrix(((1,2),(3,4)))*y", "Matrix(((1,2),(3,4)))/z", "(Matrix(((1,2),(3,4)))*x)*(y*z)",
    # names sympy reads as symbols, and arithmetic with a function's result
    "foo", "theta", "alpha", "lamda", "int", "float", "list", "plotting", "sieve", "igcd(4,6)+1", "nextprime(7)*2",
    "2**oo", "x**oo", "x**nan", "S(1)/2", "Float(0.5,3)", "N(pi,5)", "Max(1,x)", "Min(1,x)",
    # the forms tools/tick.py builds in sources_crosscheck, behind a table a clean clone does not hold: the shapes, by hand
    "(74920.827498994/(2*pi))*(log(74920.827498994/(2*pi)) - 1) + 7/8", "1.26920930427955*5*1/5**2",
    "5.98691729246392*1*1/1**2*0.0511114082399688",
]

# Every constant in the parser's fixed table, and what _parse adds to it.
CONSTANTS = ["pi", "E", "I", "oo", "inf", "zoo", "nan", "EulerGamma", "GoldenRatio", "Catalan", "TribonacciConstant",
             "true", "false"]

# Every allowlisted function with a typical argument; a name not here is called on 1.
TYPICAL = {
    "atan2": "atan2(1,1)", "root": "root(8,3)", "Pow": "Pow(2,3)", "Mod": "Mod(7,3)", "gcd": "gcd(4,6)", "lcm": "lcm(4,6)",
    "igcd": "igcd(4,6)", "ilcm": "ilcm(4,6)", "binomial": "binomial(5,2)", "factorint": "factorint(12)",
    "primerange": "primerange(1,10)", "isprime": "isprime(7)", "nextprime": "nextprime(7)", "prevprime": "prevprime(7)",
    "polygamma": "polygamma(0,1)", "beta": "beta(1,2)", "Min": "Min(1,2)", "Max": "Max(1,2)", "Rational": "Rational(1,3)",
    "Integer": "Integer(3)", "Float": "Float(0.5)", "Number": "Number(2)", "Symbol": "Symbol(x)", "symbols": "symbols(x)",
    "Dummy": "Dummy()", "Eq": "Eq(x,1)", "Ne": "Ne(x,1)", "Lt": "Lt(x,1)", "Le": "Le(x,1)", "Gt": "Gt(x,1)", "Ge": "Ge(x,1)",
    "Equality": "Equality(x,1)", "Unequality": "Unequality(x,1)", "StrictLessThan": "StrictLessThan(x,1)",
    "LessThan": "LessThan(x,1)", "StrictGreaterThan": "StrictGreaterThan(x,1)", "GreaterThan": "GreaterThan(x,1)",
    "Relational": "Relational(x,1)", "And": "And(x<1,x>0)", "Or": "Or(x<1,x>0)", "Not": "Not(x<1)", "Xor": "Xor(x<1,x>0)",
    "Nand": "Nand(x<1,x>0)", "Nor": "Nor(x<1,x>0)", "Implies": "Implies(x<1,x>0)", "Equivalent": "Equivalent(x<1,x>0)",
    "ITE": "ITE(x<1,x,0)", "Piecewise": "Piecewise((x,x<1),(0,x>=1))", "diff": "diff(x**2,x)", "Derivative": "Derivative(x**2,x)",
    "integrate": "integrate(x,x)", "Integral": "Integral(x,x)", "limit": "limit(x,x,0)", "Limit": "Limit(x,x,0)",
    "Sum": "Sum(k,(k,1,3))", "summation": "summation(k,(k,1,3))", "Product": "Product(k,(k,1,3))",
    "product": "product(k,(k,1,3))", "Subs": "Subs(x,x,1)", "simplify": "simplify(x+x)", "expand": "expand((x+1)**2)",
    "factor": "factor(x**2-1)", "cancel": "cancel(x/x)", "together": "together(1/x+1)", "apart": "apart(1/(x*(x+1)))",
    "collect": "collect(x+x*y,x)", "trigsimp": "trigsimp(sin(x)**2+cos(x)**2)", "radsimp": "radsimp(1/sqrt(2))", "N": "N(pi)",
    "evalf": "evalf(1)", "Poly": "Poly(x**2,x)", "degree": "degree(x**2,x)", "solve": "solve(x-1,x)",
    "solveset": "solveset(x-1,x)", "roots": "roots(x**2-1,x)", "Matrix": "Matrix(((1,2),(3,4)))",
    "ImmutableMatrix": "ImmutableMatrix(((1,2),(3,4)))", "eye": "eye(2)", "zeros": "zeros(2)", "ones": "ones(2)",
    "diag": "diag(1,2)", "Transpose": "Transpose(Matrix(((1,2),(3,4))))", "det": "det(Matrix(((1,2),(3,4))))",
    "trace": "trace(Matrix(((1,2),(3,4))))", "Determinant": "Determinant(Matrix(((1,2),(3,4))))",
    "Trace": "Trace(Matrix(((1,2),(3,4))))", "Inverse": "Inverse(Matrix(((1,2),(3,4))))",
    "transpose": "transpose(Matrix(((1,2),(3,4))))", "Tuple": "Tuple(1,2)", "Interval": "Interval(0,1)",
    "FiniteSet": "FiniteSet(1,2)", "S": "S(1)", "round": "round(2.5)", "abs": "abs(-2)", "Abs": "Abs(-2)",
    "atanh": "atanh(1/2)", "acoth": "acoth(2)", "li": "li(2)", "zeta": "zeta(2)",     # 1 is a pole of each: see REFUSED
}

# The five whose plain int or bool the parser converts: equal in value to what sympify returned, not in type.
CONVERTED = ("igcd(4,6)", "ilcm(4,6)", "nextprime(7)", "prevprime(7)", "isprime(7)", "isprime(8)")

# Two reads of Dummy() are two Dummies by design: a Dummy equals only itself.
SAME_KIND_ONLY = ("Dummy()",)

# Each form the parser refuses and sympify read, with its reason.
REFUSED = {
    # allowlisted names with no function behind them or no mathematical value out of them
    "Relational(x,1)": "sympy does not export the name: sympify read an undefined function, not a relation",
    "evalf(1)": "the name is a module in sympy: sympify read an undefined function, not a call",
    "factorint(12)": "returns a dict of plain ints, which is not a mathematical value",
    "roots(x**2-1,x)": "returns a dict with plain int multiplicities, which is not a mathematical value",
    "primerange(1,10)": "returns a generator",
    "nsimplify(0.5)": "off the list: it builds a text inside the call and parses it",
    "nsimplify(2)": "off the list: it builds a text inside the call and parses it",
    # function forms the list never held
    "f(x)": "a call off the allowlist; no corpus text uses one",
    "log10(x)": "a call off the allowlist; no corpus text uses one",
    "max(1,2)": "a call off the allowlist",
    "min(1,2)": "a call off the allowlist",
    # constants that are not numbers
    "True": "a bool literal; write true",
    "False": "a bool literal; write false",
    "None": "not a number",
    "1j": "a complex literal; write I",
    "...": "not a number",
    "'a'": "a string can reach a second parse",
    "b'a'": "a string can reach a second parse",
    "Piecewise((1,x>0),(0,True))": "a bool literal; write true",
    # names that are not values
    "_v": "an underscore name",
    "__x": "an underscore name",
    "sin": "an allowlisted function used as a value",
    "beta": "an allowlisted function used as a value",
    "gamma": "an allowlisted function used as a value",
    "N": "an allowlisted function used as a value",
    "S": "an allowlisted function used as a value",
    "Q": "sympy reads it as an object",
    "O": "sympy reads it as a class",
    "ZZ": "sympy reads it as an object",
    "QQ": "sympy reads it as an object",
    "Reals": "a set, off the fixed table of constants",
    "Integers": "a set, off the fixed table of constants",
    "EmptySet": "a set, off the fixed table of constants",
    "Id": "a callable, off the fixed table of constants",
    "print": "a real builtin function used as a value",
    "len": "a real builtin function used as a value",
    "bin": "a real builtin function used as a value",
    # operators and nodes off the list
    "x==1": "sympify read a Python comparison of objects, not a relation; write Eq(x,1)",
    "not x": "sympify read Python truth; write Not(x)",
    "x and y": "sympify read Python truth; write And(x,y)",
    "x or y": "sympify read Python truth; write Or(x,y)",
    "x if y else z": "sympify read Python truth",
    "7//2": "floor division is off the list",
    "~x": "bitwise inversion is off the list; write Not(x)",
    "lambda x: x": "a callable",
    # tuples and containers
    "(1,2)": "a tuple is a call argument and nothing else",
    "x,y": "a tuple is a call argument and nothing else",
    "()": "a tuple is a call argument and nothing else",
    "(1,2)*3": "repeats without bound",
    "Tuple(1,2)*3": "repeats without bound",
    "3*Tuple(1,2)": "repeats without bound",
    "Tuple(1,2)+Tuple(3)": "arithmetic on a tuple",
    "solve(x-1,x)*3": "arithmetic on a list",
    "solve(x-1,x)+solve(x-2,x)": "arithmetic on a list",
    "[1,2]": "the invalid characters",
    "{1,2}": "the invalid characters",
    "x&y": "the invalid characters",
    "x|y": "the invalid characters",
    # the limits: today's, and those today's guard let by
    "x**y**2": "a power in the exponent",
    "x**(y**2)": "a power in the exponent",
    "2**(3**2)": "a power in the exponent",
    "x**20000.5": "past the exponent limit",
    "x**10001": "past the exponent limit",
    "x**-10001": "past the exponent limit",
    "x**(5000*3)": "past the exponent limit, however it was written",
    "2^20000": "past the exponent limit: the caret spelling never reached it",
    "Pow(2,20000)": "past the exponent limit: the function spelling never reached it",
    "(2**1000)**2000": "past the bits cap",
    "((2**1000+1)**(1/2))**10000": "past the bits cap: the base shows no integer, and sympy multiplies the exponents out",
    "Pow(sqrt(2**1000+1),10000)": "past the bits cap, by the function spelling",
    "((2**10000)**104)**(1999/1000)": "past the bits cap: a fractional exponent rounds up",
    "x^(y^2)": "a power in the exponent: the caret spelling never reached the limit",
    "2^3^2": "a power in the exponent: the caret spelling never reached the limit",
    "1e20000": "past the exponent limit: a written decimal exponent is a power of ten",
    # a value with no meaning: sympy answers it with zoo, nan, AccumBounds or an oo of its own, and a later node can collapse
    # that into an ordinary number. The first seven are forms this table held as readings before the rule.
    "zoo": "no meaning: the constant is refused by its value, like any built zoo",
    "nan": "no meaning: the constant is refused by its value, like any built nan",
    "x**nan": "no meaning: sympy builds nan itself",
    "zeta(1)": "a pole, answered with zoo",
    "atanh(1)": "a pole, answered with an oo nobody wrote",
    "acoth(1)": "a pole, answered with an oo nobody wrote",
    "li(1)": "a pole, answered with a -oo nobody wrote",
    "1/0": "no meaning: answered with zoo",
    "0/0": "no meaning: answered with nan",
    "log(0)": "a pole, answered with zoo",
    "gamma(0)": "a pole, answered with zoo",
    "loggamma(0)": "a pole, answered with an oo nobody wrote",
    "Ei(0)": "a pole, answered with a -oo nobody wrote",
    "sin(oo)": "answered with AccumBounds, which a later node can collapse",
    "oo-oo": "no meaning: answered with nan, from a written oo",
    "0*oo": "no meaning: answered with nan, from a written oo",
    "limit(1/x,x,0)": "a divergent answer: an oo nobody wrote",
    "solve(x>0,x)": "an answer holding an oo nobody wrote",
    "Float((1,2))": "a Float made from a raw tuple: sympy cannot test what such a value holds, so it fails the rule's test",
}

# Two sides that differ only in how a sum or a product nests, and the claims around them: each read by pole sets against
# sympy's evaluate=False, and by the verdict it read at the step's base. A sum a call returned stays whole, so
# 1/(expand(x+y)+z) keeps its own pole base: flattening by value would move it from BROKEN to HOLDS.
POLE_PAIRS = [
    ("1/(x+(y+z))", "1/(x+y+z)", "HOLDS"),
    ("1/(x+y+z)", "1/(x+(y+z))", "HOLDS"),
    ("1/((x+y)+z)", "1/(x+(y+z))", "HOLDS"),
    ("1/(a+(b+c))", "1/(a+b+c)", "HOLDS"),
    ("1/(x+(y+1))", "1/(x+y+1)", "HOLDS"),
    ("1/(x+(y-z))", "1/(x+y-z)", "HOLDS"),
    ("1/(x-(y-z))", "1/(x-y+z)", "BROKEN"),
    ("(a+(b+c))**-1", "(a+b+c)**-1", "HOLDS"),
    ("1/(x+(y+z))+1", "1+1/(x+y+z)", "HOLDS"),
    ("(x+(y+z))/(x+(y+z))", "1", "BROKEN"),
    ("1/(x*(y*z))", "1/(x*y*z)", "HOLDS"),
    ("1/(x*y*z)", "1/(x*(y*z))", "HOLDS"),
    ("1/((x*y)*z)", "1/(x*(y*z))", "HOLDS"),
    ("1/(a*(b*c))", "1/(a*b*c)", "HOLDS"),
    ("x/(x*(y*z))", "x/(x*y*z)", "HOLDS"),
    ("1/(2*(x*y))", "1/(2*x*y)", "HOLDS"),
    ("1/(x*(y/z))", "1/(x*y/z)", "HOLDS"),
    ("(x*(y*z))/(x*(y*z))", "1", "BROKEN"),
    ("1/(x*(y*z))", "1/(x*(y*z))", "HOLDS"),
    ("1/(x+y+z)", "1/(x+y+z)", "HOLDS"),
    ("x/x", "1", "BROKEN"),
    ("(x**2-1)/(x-1)", "x+1", "BROKEN"),
    ("1/(x-1)", "1/(x-1)", "HOLDS"),
    ("(z*Matrix(((1,2),(3,4))))/z", "Matrix(((1,2),(3,4)))", "BROKEN"),
    ("1/(expand(x+y)+z)", "1/(x+y+z)", "BROKEN"),
    ("1/(x+expand(y+z))", "1/(x+y+z)", "BROKEN"),
    ("1/(sin(x)*(y*z))", "1/(sin(x)*y*z)", "HOLDS"),
    ("(x/x) % 3", "1", "HOLDS"),
]


@pytest.fixture(autouse=True)
def _keeping(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CONCORDANCE_CAS_DIR", str(tmp_path / "cas"))


def _table_rows(kw: dict) -> List[Tuple[str, str, dict, dict]]:
    names = _names("math", ())
    functions = [TYPICAL.get(n, f"{n}(1)") for n in sorted(M._ALLOWED_FUNCS)]
    texts = [t for t in FORMS + CONSTANTS + functions
             if t not in CONVERTED and t not in SAME_KIND_ONLY and t not in REFUSED]
    return [("form", t, names, dict(kw, word_mod=True)) for t in texts]


def test_every_allowlisted_function_has_a_row():
    M._ensure_sympy()
    P._ensure_sympy()
    assert set(TYPICAL) <= M._ALLOWED_FUNCS
    functions = {TYPICAL.get(n, f"{n}(1)"): n for n in M._ALLOWED_FUNCS}
    assert len(functions) == len(M._ALLOWED_FUNCS)
    read = [t for t in functions if t not in REFUSED and t not in CONVERTED and t not in SAME_KIND_ONLY]
    assert len(read) > 120


def test_every_constant_in_the_table_has_a_row():
    M._ensure_sympy()
    assert set(M._CONSTANT_NAMES) | {"inf"} == set(CONSTANTS)


@pytest.mark.parametrize("kw", [{}, {"rational": True}, {"evaluate": False}], ids=["plain", "rational", "unevaluated"])
def test_the_fixed_table_reads_the_same(kw):
    differences, refused = _compare(_table_rows(kw))
    assert differences == []
    assert refused == [], f"refused and listed nowhere: {refused!r}"


# This repo's sources hold no dimensional claim: every read above is mathematics, so physics' two readers are this table's to
# prove. Every name in the unit table, the compound units a packet writes, and each equation with its symbols.
UNITS = ["meter/second**2", "m/s^2", "m/s**2", "kg*m/s**2", "kg*m**2/s**2", "newton*meter", "joule/second", "1", "2", "m**2",
         "m**-1", "1/s", "  newton  ", "\tmeter/second**2", "kilogram*meter/second**2", "volt*ampere", "watt*second"]
EQUATIONS = {"F = m*a": ("F", "a", "m"), "F = m": ("F", "a", "m"), "  F  =  m * a  ": ("F", "a", "m"),
             "E = m*c^2": ("E", "c", "m"), "E = m*c**2": ("E", "c", "m"), "v = sqrt(2*g*h)": ("g", "h", "v"),
             "T = 2*pi*sqrt(L/g)": ("L", "T", "g"), "z = inf": ("z",), "gamma = m": ("gamma", "m"),
             "F = mod*a": ("F", "a", "mod"), "F = MOD*a": ("F", "MOD", "a"), "p = m*v": ("m", "p", "v"),
             "x = x*2^10/2^10": ("x",), "W = F*d*cos(theta)": ("F", "W", "d", "theta")}


def _physics_rows(kw: dict) -> List[Tuple[str, str, dict, dict]]:
    rows = [("unit", text, _names("unit", ()), kw) for text in sorted(P._UNIT_TABLE) + UNITS]
    return rows + [("equation", side, _names("equation", names), kw)
                   for equation, names in EQUATIONS.items() for side in equation.split("=", 1)]


@pytest.mark.parametrize("kw", [{}, {"rational": True}, {"evaluate": False}], ids=["plain", "rational", "unevaluated"])
def test_the_physics_table_reads_the_same(kw):
    P._ensure_sympy()
    M._ensure_sympy()
    rows = _physics_rows(kw)
    assert len(rows) > 60
    differences, refused = _compare(rows)
    assert differences == []
    assert refused == [], f"refused and listed nowhere: {refused!r}"


@pytest.mark.parametrize("text", CONVERTED)
def test_the_five_converted_functions_are_equal_in_value(text):
    names = _names("math", ())
    got, why = _parser(text, names)
    want, _ = _oracle(text, names)
    assert why is None and isinstance(got, (sympy.Basic,)) and not isinstance(want, sympy.Basic)
    assert got == want if isinstance(want, int) and not isinstance(want, bool) else bool(got) is want


def test_a_dummy_is_the_same_kind_on_both_sides():
    names = _names("math", ())
    assert type(_parser("Dummy()", names)[0]) is type(_oracle("Dummy()", names)[0]) is sympy.Dummy


@pytest.mark.parametrize("text", sorted(REFUSED))
def test_each_listed_form_is_refused_and_sympify_read_it(text):
    """A row that stops being refused, or that sympify stops reading, goes stale here and comes off the list."""
    names = _names("math", ())
    with tripwire() as hits:
        got, why = _parser(text, names, word_mod=True)
    assert hits == []
    assert why is not None, f"{text!r} is listed as refused and read as {got!r}"
    _value, oracle_refused = _oracle(text, names, word_mod=True)
    assert oracle_refused is None, f"{text!r} is listed, and sympify refused it too ({oracle_refused})"
    assert REFUSED[text]


def test_the_oracle_reads_raw_sympy_and_puts_the_floor_back():
    """Lifted for the oracle's read and nothing else, whether sympify read the text or refused it."""
    names = _names("math", ())
    value, oracle_refused = _oracle("(2**1000)**2000", names)
    assert oracle_refused is None and value == 2 ** 2000000
    assert _oracle("1+", names)[1] is not None
    assert all(hasattr(kind._eval_power, "unfloored") for kind in (sympy.Integer, sympy.Rational))
    with pytest.raises(M.PowerFloorRefused):
        sympy.Integer(2 ** 1000) ** sympy.Integer(2001)


def _sympy_mismatch(a: str, b: str):
    """_domain_mismatch's answer, on sympify's own evaluate=False."""
    names = _names("math", ())
    left, right = (sympy.sympify(t, locals=dict(names), evaluate=False) for t in (a, b))
    different = M._pole_bases(left).symmetric_difference(M._pole_bases(right))
    return ", ".join(sorted(str(p) for p in different)) if different else None


@pytest.mark.parametrize("a, b, verdict", POLE_PAIRS)
def test_a_pair_reads_as_sympy_read_it_by_pole_sets_and_by_verdict(a, b, verdict):
    assert M._domain_mismatch(a, b, []) == _sympy_mismatch(a, b)
    assert _post("mathematics", {"mode": "equality", "params": {"expr_a": a, "expr_b": b}})["verdict"] == verdict


# ── false claims the corpus cannot show ───────────────────────────────────────────────────────────────────────
MICRO = "µ"    # NFKC gives a different letter, and ast would too: one name would become two symbols
FALSE_CLAIMS = [
    ("name", "derivative", {"function": MICRO + "**2", "variable": MICRO, "claimed_derivative": "0"}),
    ("name", "integral", {"integrand": "0", "variable": MICRO, "claimed_antiderivative": MICRO + "**2"}),
    ("name", "limit", {"function": MICRO + "**2", "variable": MICRO, "point": "3", "claimed_limit": MICRO + "**2"}),
    ("name", "solve", {"equation": MICRO + " = 1", "variable": MICRO, "claimed_solutions": ["2"]}),
    ("name", "inequality", {"lhs": MICRO, "rhs": MICRO + "-1", "op": "<=", "variable": MICRO}),
    ("name", "equality", {"expr_a": MICRO, "expr_b": "1", "variables": [MICRO]}),
    ("name", "numeric", {"numeric_expr": MICRO, "claimed_value": 1, "variables": [MICRO]}),
    ("name", "system", {"equations": [MICRO + " = 1"], "claimed_solution": {MICRO: 2}}),
    ("name", "calc_chain", {"calc_steps": [MICRO + " = 2"], "variables": [MICRO]}),
    ("comment", "equality", {"expr_a": "2 # + 1", "expr_b": "2"}),
    ("comment", "numeric", {"numeric_expr": "2 # + 1", "claimed_value": 2}),
    ("comment", "calc_chain", {"calc_steps": ["2 # + 1 = 2"]}),
    ("comment", "derivative", {"function": "x**2 # + x", "variable": "x", "claimed_derivative": "2*x"}),
    ("comment", "integral", {"integrand": "2*x # + 1", "variable": "x", "claimed_antiderivative": "x**2"}),
    ("comment", "limit", {"function": "x # + 1", "variable": "x", "point": "2", "claimed_limit": "2"}),
    ("comment", "solve", {"equation": "x = 1 # + 1", "variable": "x", "claimed_solutions": ["1"]}),
    ("comment", "inequality", {"lhs": "1 # + 5", "rhs": "2", "op": "<="}),
    ("comment", "system", {"equations": ["x = 1 # + 1"], "claimed_solution": {"x": 1}}),
]
FALSE_PHYSICS = [
    ("name", {"equation": "F = " + MICRO + "*m", "symbols": {"F": "newton", MICRO: "1", "m": "newton"}}),
    ("comment", {"equation": "F = m*a # + 1", "symbols": {"F": "newton", "m": "kilogram", "a": "meter/second**2"}}),
    # Claims a length is a bare number. Physics never read the word: reading it here would make this one read HOLDS.
    ("word-mod", {"equation": "x = y mod z", "symbols": {"x": "1", "y": "m", "z": "m"}}),
]


def _post(domain: str, spec: dict) -> dict:
    body = {"steps": [{"id": "r", "domain": domain, "spec": spec}]}
    with tripwire() as hits:
        status, out = api.dispatch("POST", "/verify", {"seal": "0"}, body, CONFIG)
    assert status == 200, out
    assert hits == [], f"text reached sympy's string parser: {hits!r}"
    return out


@pytest.mark.parametrize("kind, mode, params", FALSE_CLAIMS, ids=[f"{k}-{m}" for k, m, _p in FALSE_CLAIMS])
def test_a_false_claim_the_corpus_cannot_show_never_reads_holds(kind, mode, params):
    r = _post("mathematics", {"mode": mode, "params": params})
    assert r["verdict"] != "HOLDS", r
    assert not r.get("seal")


@pytest.mark.parametrize("kind, packet", FALSE_PHYSICS, ids=[k for k, _p in FALSE_PHYSICS])
def test_a_false_physics_claim_the_corpus_cannot_show_reads_incomplete(kind, packet):
    r = _post("physics", {"PHYS_VERIFY": packet})
    assert r["verdict"] == "INCOMPLETE", r
    assert not r.get("seal")
