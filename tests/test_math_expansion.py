"""Math expansion — the four new MATH_VERIFY modes (2026-09-30).

(1) calc_chain  — grade a worked arithmetic solution step by step (incl. GSM8K <<expr=result>> text)
(2) numeric     — evaluate an arithmetic expression and check a claimed value (verifier-behind-solver)
(3) number_theory — gcd / lcm / primality / factorial / binomial / modulo, exact
(3) system      — a claimed solution to a system of equations, verified by substitution

Every mode must CONFIRM a truth and REFUSE a falsehood (the engine's one unforgivable failure is a
false positive). Runnable with pytest OR `python tests/test_math_expansion.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.verifiers import mathematics as M  # noqa: E402


def _run(spec):
    return M.run({"MATH_VERIFY": spec})


def test_calc_chain_steps_and_final_answer():
    assert M.verify_calc_chain({"calc_steps": ["16-3-4=9", "9*2=18"], "claimed_answer": 18}).status == "CONFIRMED"
    # a wrong step is caught
    assert M.verify_calc_chain({"calc_steps": ["16-3-4=9", "9*2=20"], "claimed_answer": 20}).status == "MISMATCH"
    # the final answer not matching the last step is caught
    assert M.verify_calc_chain({"calc_steps": ["16-3-4=9", "9*2=18"], "claimed_answer": 19}).status == "MISMATCH"


def test_calc_chain_parses_gsm8k_text():
    sol = ("She has 16 - 3 - 4 = <<16-3-4=9>>9 eggs left. "
           "She makes 9 * 2 = $<<9*2=18>>18 at market.\n#### 18")
    assert M.verify_calc_chain({"solution_text": sol}).status == "CONFIRMED"
    # inject an arithmetic error into the worked chain
    assert M.verify_calc_chain({"solution_text": "two plus two is <<2+2=5>>5\n#### 5"}).status == "MISMATCH"


def test_numeric_evaluation():
    assert M.verify_numeric({"numeric_expr": "sqrt(2)+1", "claimed_value": 2.41421356}).status == "CONFIRMED"
    assert M.verify_numeric({"numeric_expr": "2**10", "claimed_value": 1024}).status == "CONFIRMED"
    assert M.verify_numeric({"numeric_expr": "2**10", "claimed_value": 1000}).status == "MISMATCH"


def test_number_theory():
    ok = [
        {"gcd": [12, 18], "claimed_gcd": 6},
        {"lcm": [4, 6], "claimed_lcm": 12},
        {"is_prime": 17, "claimed_prime": True},
        {"factorial": 5, "claimed_factorial": 120},
        {"binomial": [5, 2], "claimed_binomial": 10},
        {"modulo": [17, 5], "claimed_modulo": 2},
    ]
    for s in ok:
        assert M.verify_number_theory(s).status == "CONFIRMED", s
    bad = [
        {"gcd": [12, 18], "claimed_gcd": 5},
        {"is_prime": 18, "claimed_prime": True},
        {"factorial": 5, "claimed_factorial": 100},
    ]
    for s in bad:
        assert M.verify_number_theory(s).status == "MISMATCH", s


def test_system_of_equations():
    sys_spec = {"equations": ["x + y = 3", "x - y = 1"], "variables": ["x", "y"]}
    assert M.verify_system({**sys_spec, "claimed_solution": {"x": 2, "y": 1}}).status == "CONFIRMED"
    assert M.verify_system({**sys_spec, "claimed_solution": {"x": 1, "y": 2}}).status == "MISMATCH"


def test_all_four_route_through_run():
    assert any(x.status == "CONFIRMED" for x in _run({"calc_steps": ["2+2=4"], "claimed_answer": 4}))
    assert any(x.status == "CONFIRMED" for x in _run({"numeric_expr": "7*6", "claimed_value": 42}))
    assert any(x.status == "CONFIRMED" for x in _run({"gcd": [8, 12], "claimed_gcd": 4}))
    assert any(x.status == "CONFIRMED" for x in _run(
        {"equations": ["2*x = 10"], "variables": ["x"], "claimed_solution": {"x": 5}}))
    # absent -> NOT_APPLICABLE, never a stray confirm
    empty = M.run({})
    assert empty and all(x.status == "NOT_APPLICABLE" for x in empty), empty


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} math-expansion tests passed.")
