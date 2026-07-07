"""Inequality verifier — the 0-false-positive guarantee for the sampling path.

Regression for the confirmed false-positive: a finite sample grid returned CONFIRMED for
inequalities that are false only between/at unsampled points. The fix decides symbolically
and uses sampling ONLY to disprove — never to confirm. Hermetic; sympy required.
Runnable with pytest OR `python tests/test_inequality.py` (sovereign — no pytest needed).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.verifiers import mathematics as m  # noqa: E402


def _status(lhs, rhs, op, **extra):
    spec = {"lhs": lhs, "rhs": rhs, "op": op}
    spec.update(extra)
    return m.verify_inequality(spec).status


def test_false_inequalities_are_never_confirmed():
    # These are the exact traps that used to seal as HOLDS.
    assert _status("(x-3)**2", "0", ">") != "CONFIRMED"     # false at x=3
    assert _status("sin(x)", "0.9999", "<=") != "CONFIRMED"  # false near pi/2
    assert _status("x**2", "1", ">=") != "CONFIRMED"         # false on (-1,1)


def test_genuine_universals_still_confirm():
    assert _status("x**2", "0", ">=") == "CONFIRMED"         # true for all real x
    assert _status("x**2 + 1", "0", ">") == "CONFIRMED"      # strictly positive


def test_constant_comparisons_decide_correctly():
    assert _status("pi", "3", ">") == "CONFIRMED"
    assert _status("8*sqrt(3)", "16", "<") == "CONFIRMED"
    assert _status("pi", "3", "<") == "MISMATCH"
    assert _status("1", "2", ">") == "MISMATCH"


def test_counterexample_disproves():
    # a real violation must be caught (sound disproof), not swallowed
    assert _status("x**2", "0", "<") == "MISMATCH"           # x**2 < 0 is false everywhere


def test_parse_guards_apply_to_inequality():
    # the DoS/injection guards that equality uses must also cover inequality
    assert _status("9**9**9", "0", ">") == "ERROR"           # power tower rejected
    assert _status("x #comment", "0", ">") == "ERROR"        # '#'-truncation rejected


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} inequality tests passed — no false-positive survives the sampling path.")
