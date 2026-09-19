"""THE ENGINE RUNS STDLIB-ONLY — and honestly.

The .com hero promises the engine "runs offline on your own box, stdlib-only." That is only true
if the engine does not CRASH when the optional `math` extra (sympy / numpy / scipy) is absent. This
simulates a stdlib-only box (blocks those imports) and asserts:

  1. every verifier module still IMPORTS (a top-level `import numpy` once crashed the whole registry);
  2. the stdlib-computable checks still produce real verdicts (all propositional logic, set algebra,
     the logic=circuits=sets bridge);
  3. the genuinely-symbolic checks (calculus, linear algebra) degrade to NOT_APPLICABLE with a clear
     reason — never a crash, never a false verdict.

Discovered 2026-09-19 while making the Atlas "attached and functioning": on a deps-absent box,
formal_logic crashed (its old except-clause re-imported sympy) and linear_algebra could not import.
This ratchet keeps the offline promise honest.
"""
from __future__ import annotations

import builtins
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

BLOCK = {"sympy", "numpy", "scipy"}


@pytest.fixture
def no_math_extra(monkeypatch):
    """Simulate a stdlib-only box: block sympy/numpy/scipy, and force the verifier modules to
    re-import under the block so their lazy loaders re-run. monkeypatch restores everything after."""
    for name in list(sys.modules):
        top = name.split(".")[0]
        if top in BLOCK or name == "concordance" or name.startswith("concordance.verifiers"):
            monkeypatch.delitem(sys.modules, name, raising=False)
    real_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name.split(".")[0] in BLOCK:
            raise ModuleNotFoundError(f"No module named '{name.split('.')[0]}' (simulated stdlib-only box)")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    yield


def _run(mod, key, spec):
    m = importlib.import_module(f"concordance.verifiers.{mod}")
    return m.run({key: spec})


def test_every_verifier_module_imports_without_the_math_extra(no_math_extra):
    import concordance.verifiers as pkg
    folder = Path(pkg.__file__).resolve().parent
    for f in sorted(folder.glob("*.py")):
        if f.name == "__init__.py":
            continue
        importlib.import_module(f"concordance.verifiers.{f.stem}")  # must not raise


def test_formal_logic_runs_stdlib_only(no_math_extra):
    # all five propositional checks are exact by truth table — no sympy needed
    assert _run("formal_logic", "LOGIC_VERIFY",
                {"variables": ["p"], "formula": "p | ~p", "claimed_tautology": True})[0].status == "CONFIRMED"
    assert _run("formal_logic", "LOGIC_VERIFY",
                {"variables": ["p", "q"], "premises": ["p", "p >> q"], "conclusion": "q",
                 "claimed_entailment": True})[0].status == "CONFIRMED"
    assert _run("formal_logic", "LOGIC_VERIFY",
                {"variables": ["p"], "formula": "p & ~p", "claimed_contradiction": True})[0].status == "CONFIRMED"


def test_the_boolean_bridge_runs_stdlib_only(no_math_extra):
    assert _run("computer_science", "CS_VERIFY",
                {"variables": ["a", "b"], "gate_a": "a & b", "gate_b": "~(~a | ~b)",
                 "claimed_equivalent": True})[0].status == "CONFIRMED"
    assert _run("mathematics", "MATH_VERIFY",
                {"variables": ["A", "B"], "set_a": "~(A | B)", "set_b": "~A & ~B",
                 "claimed_equal": True})[0].status == "CONFIRMED"


def test_symbolic_math_degrades_not_crashes(no_math_extra):
    r = _run("mathematics", "MATH_VERIFY", {"variables": ["x"], "expr_a": "x+x", "expr_b": "2*x"})
    assert r[0].status == "NOT_APPLICABLE"
    assert "math extra" in r[0].detail.lower() or "sympy" in r[0].detail.lower()


def test_linear_algebra_degrades_not_crashes(no_math_extra):
    r = _run("linear_algebra", "LIN_VERIFY",
             {"vec_a": [1, 2], "vec_b": [3, 4], "claimed_dot_product": 11})
    assert r[0].status == "NOT_APPLICABLE"
    assert "numpy" in r[0].detail.lower() or "math extra" in r[0].detail.lower()


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
