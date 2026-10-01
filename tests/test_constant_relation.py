"""Physical-constant RELATION verifier — does a formula reproduce its target constant?

The value verifier already checks a single named constant against the CODATA table. This checks
the EDGES: a derived constant computed from others via an exact physical identity (e.g.
alpha = e^2 / (2 epsilon_0 h c)) must reproduce the table's own value for that constant. It
seals the relation between constants, never a measured value -- both sides are reference values
and the check is pure arithmetic.

Runnable with pytest OR `python tests/test_constant_relation.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.verifiers import physical_constants as P  # noqa: E402


def test_alpha_relation_confirms_from_e_epsilon0_h_c():
    r = P.verify_constant_relation({"relation": "fine_structure_constant"})
    assert r.status == "CONFIRMED", r
    assert r.data["rel_diff"] < 1e-9  # reproduces alpha to ~3e-12
    assert r.data["target"] == "fine_structure_constant"


def test_alpha_alias_resolves():
    assert P.verify_constant_relation({"relation": "alpha"}).status == "CONFIRMED"


def test_every_registered_relation_reproduces_its_target():
    for rel in P.list_relations():
        r = P.verify_constant_relation({"relation": rel["relation"]})
        assert r.status == "CONFIRMED", (rel["relation"], r)
        assert r.data["rel_diff"] < 1e-6


def test_a_tolerance_tighter_than_the_residual_mismatches():
    # It is a REAL check, not an always-pass: demand more precision than the table carries.
    r = P.verify_constant_relation({"relation": "fine_structure_constant", "rel_tol": 1e-13})
    assert r.status == "MISMATCH", r


def test_caller_cannot_loosen_the_tolerance():
    r = P.verify_constant_relation({"relation": "fine_structure_constant", "rel_tol": 10.0})
    assert r.data["rel_tol"] <= 1e-6  # clamped to the verifier's default


def test_unknown_relation_is_not_applicable():
    assert P.verify_constant_relation({"relation": "not_a_real_relation"}).status == "NOT_APPLICABLE"


def test_run_handles_value_and_relation_and_stays_quiet_when_absent():
    # the existing value check still works
    v = P.run({"CONST_VERIFY": {"constant": "speed_of_light", "claimed_value": 299792458}})
    assert any(x.status == "CONFIRMED" for x in v), v
    # the new relation check routes
    rel = P.run({"CONST_RELATION": {"relation": "alpha"}})
    assert any(x.name == "physical_constants.relation" and x.status == "CONFIRMED" for x in rel), rel
    # both together
    both = P.run({
        "CONST_VERIFY": {"constant": "alpha", "claimed_value": 7.2973525693e-3},
        "CONST_RELATION": {"relation": "alpha"},
    })
    assert sum(1 for x in both if x.status == "CONFIRMED") == 2, both
    # absent -> non-empty all-NA (present-vs-null invariant)
    empty = P.run({})
    assert empty and all(x.status == "NOT_APPLICABLE" for x in empty), empty
    # unrelated -> never CONFIRMED/MISMATCH
    unrel = P.run({"TOTALLY_UNRELATED_XYZ": {"relation": "alpha"}})
    assert not any(x.status in ("CONFIRMED", "MISMATCH") for x in unrel), unrel


def test_governance_graphs_are_physics_not_keywords():
    from concordance.verifiers import VERIFIERS
    consts = P.list_governed_constants()
    # the pattern generalized: several fundamental constants now carry a governance graph
    for c in ("fine_structure_constant", "gravitational_constant", "boltzmann_constant",
              "speed_of_light", "planck_constant", "avogadro_constant"):
        assert c in consts, c
    for cst in consts:
        g = P.governance(cst)
        assert "error" not in g, (cst, g)
        assert g["governed"], cst
        # every gap is now CLOSED — each governed domain computes through the constant
        assert g["gap"] == [], (cst, g["gap"])
        # no ghosts: every named domain across every tier is a real registered verifier
        for tier in ("governed", "descendant", "rejected"):
            for d in g[tier]:
                assert d in VERIFIERS, (cst, tier, d)
    # alpha's gap is CLOSED and its lexical collisions are rejected, not governed
    a = P.alpha_governance()
    assert a["gap"] == [], a["gap"]
    assert "statistics" in a["rejected"] and "linguistics" in a["rejected"]
    assert "statistics" not in a["governed"]
    # an unknown constant returns an honest error, not a guess
    assert "error" in P.governance("not_a_constant")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} constant-relation tests passed.")
