"""NO OTHER ROUTE, default deny: no text reaches a parser or an evaluator by any path but the one parser.

The static half walks the AST of every module under src/concordance and refuses, unless ALLOWED lists it by file and
function with a reason: any import, attribute or alias of sympify, parse_expr, parse_latex, eval, exec, compile or
__import__, whether called or passed as a value; any import of sympy outside mathematics.py and physics.py, including a
dynamic one; and, in this repo, any import of subprocess, which V3's walk does not watch and which this repo has. The re
module's compile is exempt by its receiver. Planted cases prove the walk can fail. The list is this repo's own: the walk
covers src/concordance, so tools/gauge_panel.py's eval, which reads default values from this repo's own source, is
outside it.

The runtime half is the tripwire in tests/fixtures/parse_tripwire.py: it catches any str reaching sympy's string
parser, which covers simplify, S, sin and every other sympy function that parses a string, by what they do and not by
their names. It sees only the branches the tests exercise, and says nothing of a branch no test reaches: that is why
the static half exists, and why neither half is the whole proof. It runs here over one golden per domain, one claim per
mathematics mode and every allowlisted function, in tests/test_parse_differential.py over the differential table and
the sources it records at runtime, and in tests/test_parse_route.py over the route tests.
"""
from __future__ import annotations

import ast
import builtins
import json
import sys
from pathlib import Path
from typing import Dict, Set, Tuple

import pytest
import sympy

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "concordance"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests" / "fixtures"))

import benchmark  # noqa: E402
from concordance.derivation import verify, verify_derivation  # noqa: E402
from concordance.verifiers import mathematics as M  # noqa: E402
from concordance.verifiers import physics as P  # noqa: E402
from parse_tripwire import tripwire  # noqa: E402

WATCHED = frozenset({"sympify", "parse_expr", "parse_latex", "eval", "exec", "compile", "__import__"})
SYMPY_HOMES = frozenset({"src/concordance/verifiers/mathematics.py", "src/concordance/verifiers/physics.py"})
IMPORT_SYMPY = "import sympy"
IMPORT_SUBPROCESS = "import subprocess"

# (file, function, what) -> why it is safe. A new site fails until someone classifies it here; a stale one fails too.
ALLOWED: Dict[Tuple[str, str, str], str] = {
    ("src/concordance/verifiers/computer_science.py", "_exec_function", "exec"):
        "runs caller code only behind CONCORDANCE_ALLOW_CODE_EXEC, default off: tests/test_code_exec_flag.py",
    ("src/concordance/verifiers/computer_science.py", "_exec_function", "compile"):
        "the same line, behind the same flag",
    ("src/concordance/derivation.py", "<module>", IMPORT_SYMPY):
        "_HEAVY_LIBS names sympy so warm() can pre-import it at boot; no text reaches it",
    ("src/concordance/byom.py", "run_byom", "__import__"):
        "two lazy imports of this package's own airlock and discern, by literal names; no text reaches them",
    ("src/concordance/faces.py", "compose", "__import__"):
        "a lazy import of this package's own ask, by a literal name; no text reaches it",
    ("src/concordance/four_gates.py", "run", "__import__"):
        "a lazy import of this package's own ask, by a literal name; no text reaches it",
    ("src/concordance/verifiers/riemann_accel.py", "<module>", IMPORT_SUBPROCESS):
        "build compiles this repo's own _rs.c with a fixed argument list; the compiler comes from the environment and "
        "the paths from this module, and no text from a request reaches the command",
}


class _Walk(ast.NodeVisitor):
    """What one module's tree refers to, each finding as (function, what)."""

    def __init__(self, path: str, re_names: Set[str]):
        self.path, self.re_names = path, re_names
        self.stack, self.found = [], set()

    def _hit(self, what: str) -> None:
        self.found.add((".".join(self.stack) or "<module>", what))

    def _scope(self, node) -> None:
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    visit_FunctionDef = visit_AsyncFunctionDef = visit_ClassDef = _scope

    def _import_of_sympy(self, module: str) -> None:
        root = module.split(".")[0]
        if root == "sympy" and self.path not in SYMPY_HOMES:
            self._hit(IMPORT_SYMPY)
        elif root == "subprocess":
            self._hit(IMPORT_SUBPROCESS)

    def visit_Import(self, node) -> None:
        for alias in node.names:
            self._import_of_sympy(alias.name)

    def visit_ImportFrom(self, node) -> None:
        module = node.module or ""
        self._import_of_sympy(module)
        for alias in node.names:
            if alias.name in WATCHED and not (module == "re" and alias.name == "compile"):
                self._hit(alias.name)

    def visit_Name(self, node) -> None:
        if node.id in WATCHED:
            self._hit(node.id)

    def visit_Attribute(self, node) -> None:
        receiver = node.value.id if isinstance(node.value, ast.Name) else None
        if node.attr in WATCHED and not (node.attr == "compile" and receiver in self.re_names):
            self._hit(node.attr)
        self.generic_visit(node)

    def visit_Call(self, node) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == "getattr" and len(node.args) >= 2 \
                and isinstance(node.args[1], ast.Constant) and node.args[1].value in WATCHED:
            self._hit(node.args[1].value)
        self.generic_visit(node)

    def visit_Constant(self, node) -> None:     # a dynamic import names its module in a literal
        if isinstance(node.value, str) and node.value.split(".")[0] in ("sympy", "subprocess"):
            self._import_of_sympy(node.value)


def scan(source: str, path: str) -> Set[Tuple[str, str]]:
    tree = ast.parse(source)
    re_names = {alias.asname or alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
                for alias in node.names if alias.name == "re"}
    walk = _Walk(path, re_names)
    walk.visit(tree)
    return walk.found


def test_no_module_refers_to_an_evaluator_or_sympy_outside_the_list():
    found: Set[Tuple[str, str, str]] = set()
    modules = sorted(SRC.rglob("*.py"))
    assert len(modules) > 100
    for path in modules:
        rel = path.relative_to(ROOT).as_posix()
        found |= {(rel, function, what) for function, what in scan(path.read_text(encoding="utf-8"), rel)}
    assert found - set(ALLOWED) == set(), "a new site: read it, then list it here with its reason"
    assert set(ALLOWED) - found == set(), "a listed site is gone: take it off the list"
    assert all(ALLOWED.values())


PLANTED = {
    "a direct call": ("def f(t):\n    return sympify(t)\n", ("f", "sympify")),
    "a direct call of eval": ("def f(t):\n    return eval(t)\n", ("f", "eval")),
    "a direct call of exec": ("def f(t):\n    exec(t)\n", ("f", "exec")),
    "a direct call of compile": ("def f(t):\n    return compile(t, 'x', 'eval')\n", ("f", "compile")),
    "a direct call of __import__": ("def f(t):\n    return __import__(t)\n", ("f", "__import__")),
    "a method": ("class C:\n    def f(self, t):\n        return sympify(t)\n", ("C.f", "sympify")),
    "an import alias": ("from sympy import sympify as harmless\n", ("<module>", "sympify")),
    "an import alias of parse_expr": ("from sympy.parsing.sympy_parser import parse_expr as p\n", ("<module>", "parse_expr")),
    "an import alias of parse_latex": ("from sympy.parsing.latex import parse_latex as p\n", ("<module>", "parse_latex")),
    "an import alias of a builtin": ("from builtins import eval as e\n", ("<module>", "eval")),
    "a module attribute": ("import sympy\ndef f(t):\n    return sympy.sympify(t)\n", ("f", "sympify")),
    "an aliased module attribute": ("import sympy as sp\ndef f(t):\n    return sp.parse_expr(t)\n", ("f", "parse_expr")),
    "a builtins attribute": ("import builtins\ndef f(t):\n    return builtins.eval(t)\n", ("f", "eval")),
    "getattr by name": ("import builtins\ndef f(t):\n    return getattr(builtins, 'exec')(t)\n", ("f", "exec")),
    "a function passed as a value": ("def f(ts):\n    return list(map(eval, ts))\n", ("f", "eval")),
    "an attribute passed as a value": ("import sympy\ndef f(ts):\n    return map(sympy.sympify, ts)\n", ("f", "sympify")),
    "a function kept in a name": ("parse = sympify\n", ("<module>", "sympify")),
    "compile off another receiver": ("import regex\ndef f(t):\n    return regex.compile(t)\n", ("f", "compile")),
    "compile off a value": ("def f(p, t):\n    return p.compile(t)\n", ("f", "compile")),
    "import sympy": ("import sympy\n", ("<module>", IMPORT_SYMPY)),
    "import sympy in a function": ("def f():\n    import sympy\n", ("f", IMPORT_SYMPY)),
    "from sympy": ("from sympy.core import Symbol\n", ("<module>", IMPORT_SYMPY)),
    "a dynamic import": ("import importlib\ndef f():\n    importlib.import_module('sympy')\n", ("f", IMPORT_SYMPY)),
    "a dynamic import of a part": ("import importlib\nimportlib.import_module('sympy.parsing')\n", ("<module>", IMPORT_SYMPY)),
    "import subprocess": ("import subprocess\n", ("<module>", IMPORT_SUBPROCESS)),
    "from subprocess": ("from subprocess import run\n", ("<module>", IMPORT_SUBPROCESS)),
    "import subprocess in a function": ("def f():\n    import subprocess as s\n", ("f", IMPORT_SUBPROCESS)),
    "a dynamic import of subprocess": ("import importlib\nimportlib.import_module('subprocess')\n", ("<module>", IMPORT_SUBPROCESS)),
}


@pytest.mark.parametrize("case", sorted(PLANTED))
def test_the_walk_fails_on_a_planted_case(case):
    source, finding = PLANTED[case]
    assert finding in scan(source, "src/concordance/verifiers/planted.py")


@pytest.mark.parametrize("source", [
    "import re\nP = re.compile('x')\n",
    "import re as _re\nP = _re.compile('x')\n",
    "from re import compile as c\nP = c('x')\n",
    "def f(p):\n    return p.search('x')\n",
])
def test_the_re_modules_compile_is_exempt_by_its_receiver(source):
    assert scan(source, "src/concordance/verifiers/planted.py") == set()


@pytest.mark.parametrize("path", sorted(SYMPY_HOMES))
def test_sympy_may_be_imported_in_its_two_homes_and_a_parse_still_may_not(path):
    assert scan("import sympy\nfrom sympy import Symbol\n", path) == set()
    assert ("f", "sympify") in scan("from sympy import Symbol\ndef f(t):\n    return sympify(t)\n", path)


# ── the runtime tripwire ──────────────────────────────────────────────────────────────────────────────────────
def planted_verifier(spec: dict):
    """A verifier as it must never be: it hands a request's text to a sympy function that is no parser by name."""
    return sympy.simplify(spec["expression"])


def test_the_tripwire_fails_on_a_planted_verifier_that_passes_text_to_simplify():
    with tripwire() as hits:
        assert planted_verifier({"expression": "1+1"}) == 2
    assert hits == ["1+1"]


@pytest.mark.parametrize("planted", [lambda: sympy.sympify("1+1"), lambda: sympy.S("1+1"), lambda: sympy.sin("1"),
                                     lambda: sympy.Symbol("x").subs("x", "1"), lambda: sympy.Symbol("x").diff("x")],
                         ids=["sympify", "S", "sin", "subs", "diff"])
def test_the_tripwire_sees_a_parse_by_what_it_does_not_by_its_name(planted):
    with tripwire() as hits:
        planted()
    assert hits


def test_the_tripwire_wraps_parse_expr_and_no_builtin_and_lets_go():
    import sympy.parsing.sympy_parser as parser
    before, real = dict(vars(builtins)), parser.parse_expr
    with tripwire():
        assert parser.parse_expr is not real
        assert vars(builtins) == before
    assert parser.parse_expr is real and vars(builtins) == before


# The modes the moat's claims do not reach, each with a true claim, and physics' dimensional check, which no golden holds.
MORE_MODES = {
    "integral": {"integrand": "2*x", "variable": "x", "claimed_antiderivative": "x**2"},
    "limit": {"function": "sin(x)/x", "variable": "x", "point": "0", "claimed_limit": "1"},
    "solve": {"equation": "x**2 = 4", "variable": "x", "claimed_solutions": ["2", "-2"]},
    "numeric": {"numeric_expr": "2**10", "claimed_value": 1024},
    "calc_chain": {"calc_steps": ["2+2 = 4", "4*3 = 12"]},
    "system": {"equations": ["x + y = 3", "x - y = 1"], "claimed_solution": {"x": 2, "y": 1}},
}
DIMENSIONAL = {"PHYS_VERIFY": {"equation": "F = m*a", "symbols": {"F": "newton", "m": "kilogram", "a": "meter/second**2"}}}


def _one_case_per_domain() -> Dict[str, list]:
    """The true golden of each domain, the first true claim of each mathematics mode, and physics' dimensional check. The
    mathematics golden is a MATH_VERIFY packet, which derivation.py here has no branch for, so that domain reads the moat."""
    picked: Dict[str, list] = {}
    goldens = json.loads((ROOT / "data" / "domain_goldens.json").read_text(encoding="utf-8"))
    for domain, pair in goldens.items():
        if pair["packet_key"] != "MATH_VERIFY":
            picked[domain] = [{"id": "g", "domain": domain, "spec": {pair["packet_key"]: pair["true"]}}]
    for label, spec, _desc in benchmark.CLAIMS:
        if label:
            steps = [{"id": "b", "domain": "mathematics", "spec": spec}]
            picked.setdefault("mathematics", steps)
            picked.setdefault("mathematics " + spec["mode"], steps)
    for mode, params in MORE_MODES.items():
        picked["mathematics " + mode] = [{"id": "m", "domain": "mathematics", "spec": {"mode": mode, "params": params}}]
    picked["physics dimensional"] = [{"id": "d", "domain": "physics", "spec": DIMENSIONAL}]
    return picked


@pytest.mark.filterwarnings("ignore")
def test_no_text_reaches_the_string_parser_on_one_case_per_domain(monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(ROOT / "data"))      # other tests move it
    P._ensure_sympy()
    picked = _one_case_per_domain()
    assert len(picked) > 60 and {"mathematics", "physics", "physics dimensional"} <= set(picked)
    assert {"mathematics " + mode for mode in ("equality", "inequality", "derivative", *MORE_MODES)} <= set(picked)
    verdicts = {}
    with tripwire() as hits:
        for domain, steps in picked.items():
            verdicts[domain] = verify_derivation(steps).get("verdict")
        verdicts["moat"] = verify(benchmark.CLAIMS[0][1]).get("verdict")
    assert hits == [], f"text reached sympy's string parser: {hits[:5]!r}"
    assert verdicts["mathematics"] == verdicts["physics dimensional"] == verdicts["moat"] == "HOLDS"
    assert {verdicts["mathematics " + mode] for mode in MORE_MODES} == {"HOLDS"}


SHAPES = ("{f}()", "{f}(x)", "{f}(1)", "{f}(0.5)", "{f}(x,y)", "{f}(1,2)", "{f}(x,1)", "{f}(1,x)", "{f}(x,y,z)", "{f}(1,2,3)",
          "{f}(x,1,y)", "{f}(x,x,x,x)", "{f}(((1,2),(3,4)))", "{f}((((x,),),))", "{f}(x,((1,2),(3,4)))", "{f}(((x,1),(x,2)),x)",
          "{f}(((x-1,x<2),(0,x>=2)))", "{f}(1,((2,),))", "{f}(x<1)", "{f}(x<1,x)", "{f}(pi)", "{f}(oo)", "{f}(foo,bar)",
          "{f}(1,1,foo)", "{f}(1,1,x)", "{f}(1.5,foo)", "{f}(foo,1.5)")


@pytest.mark.filterwarnings("ignore")
def test_no_allowlisted_function_parses_a_text_on_these_shapes():
    """Each function on each shape here, and on nothing else: a tripwire sees the branches a test exercises. A decimal in
    solve does reach sympy's string parser, with numeric text sympy builds from that number, as it did before this parser;
    that is a want of its own, so no shape here holds one."""
    P._ensure_sympy()
    M._ensure_sympy()
    read = 0
    with tripwire() as hits:
        for name in sorted(M._ALLOWED_FUNCS):
            for shape in SHAPES:
                try:
                    M.parse_expression(shape.format(f=name))
                    read += 1
                except M.ExpressionRefused:
                    pass
    assert hits == [], f"text reached sympy's string parser: {hits[:5]!r}"
    assert read > 800
