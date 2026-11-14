"""THE MEANING TEST of data/sticks/jacobian_conjecture.json (run 2026-11-13-ai-era-marks, step marks).

A golden pins what an entry mints, by content hash, and not what its seals mean. This file holds the entry's four sealed
expressions to their source: the counterexample to the Jacobian conjecture in dimension three as printed in S. Gao,
arXiv:2608.00222v2, Section 3.4, Theorem 3.3 ('Written out in full'), transcribed here once. With sympy it checks that
the Jacobian determinant of that F is -2 and that F sends the three points, which are distinct, to (-1/4, 0, 0). It
checks that the entry's det seal is exactly the cofactor template applied to that F, and each point seal exactly the
image template applied to that F and that point. Each of the four seals holds through verify_derivation with the
math-mode shape, while a changed claim (-3 for -2, a moved point) does not."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
ENTRY = ROOT / "data" / "sticks" / "jacobian_conjecture.json"

# Gao, arXiv:2608.00222v2, Section 3.4: f1, f2, f3, in sympy's syntax, stated once.
F = ("(1+x*y)**3*z + y**2*(1+x*y)*(4+3*x*y)",
     "y + 3*x*(1+x*y)**2*z + 3*x*y**2*(4+3*x*y)",
     "2*x - 3*x**2*y - x**3*z")
VARIABLES = ("x", "y", "z")
IMAGE = ("-1/4", "0", "0")                          # F(0,0,-1/4) = F(1,-3/2,13/2) = F(-1,3/2,13/2) = (-1/4,0,0)
POINTS = {"p1": ("0", "0", "-1/4"), "p2": ("1", "-3/2", "13/2"), "p3": ("-1", "3/2", "13/2")}


def cofactor(f=F) -> str:
    """The determinant of the 3x3 matrix whose (i, j) entry is diff(f_i, x_j), expanded by cofactors along row one."""
    def a(i, j):
        return f"diff({f[i]}, {VARIABLES[j]})"
    return (f"{a(0, 0)}*({a(1, 1)}*{a(2, 2)} - {a(1, 2)}*{a(2, 1)})"
            f" - {a(0, 1)}*({a(1, 0)}*{a(2, 2)} - {a(1, 2)}*{a(2, 0)})"
            f" + {a(0, 2)}*({a(1, 0)}*{a(2, 1)} - {a(1, 1)}*{a(2, 0)})")


def image(point, f=F) -> str:
    """The sum of the squared differences between each component of f at the point and that of (-1/4, 0, 0)."""
    def at(component):
        return "".join(f"({point[VARIABLES.index(c)]})" if c in VARIABLES else c for c in component)
    return " + ".join(f"({at(f[i])} - ({IMAGE[i]}))**2" for i in range(3))


def entry() -> dict:
    return json.loads(ENTRY.read_text(encoding="utf-8"))


def seals() -> dict:
    return {s["key"]: s for s in entry()["seals"]}


def holds(params: dict, key: str) -> dict:
    from concordance.derivation import verify_derivation
    return verify_derivation([{"id": key, "domain": "mathematics", "spec": {"mode": "equality", "params": params}}])


X, Y, Z = sympy.symbols("x y z")
F_SYMPY = [sympy.sympify(f) for f in F]


def test_sympy_finds_the_jacobian_determinant_of_gaos_f_is_minus_2():
    jacobian = sympy.Matrix(F_SYMPY).jacobian([X, Y, Z])
    assert sympy.expand(jacobian.det()) == -2


def test_the_three_points_are_distinct_and_f_sends_each_to_the_common_image():
    points = [tuple(sympy.Rational(c) for c in p) for p in POINTS.values()]
    assert len(set(points)) == 3
    for p in points:
        assert tuple(sympy.expand(f.subs({X: p[0], Y: p[1], Z: p[2]})) for f in F_SYMPY) == tuple(
            sympy.Rational(c) for c in IMAGE), p


def test_the_entry_holds_exactly_four_math_mode_seals_det_p1_p2_p3():
    assert list(seals()) == ["det", "p1", "p2", "p3"]
    for s in seals().values():
        assert (s["domain"], s["mode"]) == ("mathematics", "equality") and "expr" not in s and "artifact" not in s


def test_the_det_seal_is_exactly_the_cofactor_template_applied_to_gaos_f():
    assert seals()["det"]["params"] == {"expr_a": "-2", "expr_b": cofactor(), "variables": list(VARIABLES)}
    assert sympy.expand(sympy.sympify(cofactor())) == -2                # the template itself evaluates to -2


@pytest.mark.parametrize("key", sorted(POINTS))
def test_each_point_seal_is_exactly_the_image_template_applied_to_gaos_f_and_its_point(key):
    assert seals()[key]["params"] == {"expr_a": image(POINTS[key]), "expr_b": "0"}
    assert sympy.sympify(image(POINTS[key])) == 0                       # exact rational arithmetic


@pytest.mark.parametrize("key", ["det", "p1", "p2", "p3"])
def test_each_seal_holds_through_verify_derivation_with_the_math_mode_shape(key):
    r = holds(seals()[key]["params"], key)
    assert r["verdict"] == "HOLDS", r
    if key == "det":
        assert r["trail"][0]["detail"].startswith("-2 = ")              # the claim first, so the receipt opens on it


@pytest.mark.parametrize("key,changed", [
    ("det", {"expr_a": "-3", "expr_b": cofactor(), "variables": list(VARIABLES)}),
    ("p2", {"expr_a": image(("1", "-3/2", "6")), "expr_b": "0"}),
    ("p3", {"expr_a": image(("-1", "3/2", "13/2 + 1/10**10")), "expr_b": "0"}),
])
def test_a_changed_claim_does_not_hold(key, changed):
    assert holds(changed, key)["verdict"] == "BROKEN"


def test_the_six_marks_are_four_sealed_witnesses_and_two_notes_and_none_closes_the_question():
    from concordance import tickstick
    st = entry()["sticks"]
    assert len(st) == 1 and st[0]["question"] == "The Jacobian conjecture" and st[0]["field"] == "mathematics"
    marks = st[0]["marks"]
    assert [(m["kind"], m.get("seal")) for m in marks] == [("witness", "det"), ("witness", "p1"), ("witness", "p2"),
                                                           ("witness", "p3"), ("note", None), ("note", None)]
    assert all(len(m["claim"]) <= tickstick.CLAIM_CAP for m in marks)
