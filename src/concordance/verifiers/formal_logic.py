"""Formal Logic verifier.

Deterministic checks of propositional-logic claims by exact truth-table enumeration
(pure standard library — no sympy), so the verifier runs on the sovereign stdlib-only
box, not only where the optional `math` extra is installed. The five canonical
propositional questions are decidable mechanically; this verifier wraps that decision
into the engine's CONFIRMED / MISMATCH / NA / ERROR shape.

Why truth tables and not a SAT solver: the V1 spec is purely propositional (declared
Boolean symbols, no quantifiers), and enumerating the 2^n assignments over the few
variables a claim carries is exact and complete — it gives the identical answer sympy's
SAT would, with nothing to install. (sympy would only add first-order / SMT, which the
spec does not expose.) The shared engine lives in `_boolean.py` and also backs the
computer_science.logic_gate and mathematics.set_algebra bridge verifiers — one Boolean
core, three faces (logic / circuits / sets).

Checks performed:

  * formal_logic.satisfiability
      formula has a satisfying assignment (or doesn't), matches claim.
  * formal_logic.tautology
      formula is true under every assignment.
  * formal_logic.contradiction
      formula is false under every assignment.
  * formal_logic.entailment
      premises |= conclusion  <=>  no assignment makes every premise true and the conclusion false.
  * formal_logic.equivalence
      formula_a === formula_b  <=>  identical truth tables.

Formula syntax (Python-flavored Boolean operators):
  &   = AND        |   = OR         ~   = NOT
  ^   = XOR        >>  = implies (p >> q)
The `and`/`or`/`not` keywords and the constants True/False are also accepted. The parser is a
strict AST allowlist (see _boolean.py): a call, attribute, number, or undeclared name is refused
(-> NOT_APPLICABLE), so a formula can never carry code — structural safety, no sympify.

LOGIC_VERIFY packet shape (any subset of fields):
    {
      "variables": ["p", "q", "r"],          # propositional symbol names
      "formula": "p & q",                    # satisfiability/tautology/contradiction
      "claimed_satisfiable": true,
      "claimed_tautology": false,
      "claimed_contradiction": false,
      "premises": ["p", "p >> q"],           # entailment
      "conclusion": "q",
      "claimed_entailment": true,
      "formula_a": "p | q",                  # equivalence
      "formula_b": "~(~p & ~q)",
      "claimed_equivalent": true,
    }
"""
from __future__ import annotations
from typing import Any, Dict, List

from .base import VerifierResult, na, confirm, mismatch, error
from ._boolean import boolean_equivalent, satisfiable, truth_rows, BooleanParseError


def verify_satisfiability(spec: Dict[str, Any]) -> VerifierResult:
    name = "formal_logic.satisfiability"
    formula = spec.get("formula")
    claimed = spec.get("claimed_satisfiable")
    if formula is None or claimed is None:
        return na(name)
    var_names = spec.get("variables") or []
    try:
        actual = satisfiable(formula, var_names)
    except BooleanParseError as e:
        return na(name, f"cannot parse formula: {e}")
    except Exception as e:  # noqa: BLE001
        return error(name, f"computation failure: {type(e).__name__}: {e}")
    claimed_b = bool(claimed)
    if actual == claimed_b:
        return confirm(name,
                       f"formula {formula!r} satisfiable={actual}, matches claim",
                       {"formula": formula, "actual": actual, "claimed": claimed_b})
    return mismatch(name,
                    f"formula {formula!r} satisfiable={actual}, claimed {claimed_b}",
                    {"formula": formula, "actual": actual, "claimed": claimed_b})


def verify_tautology(spec: Dict[str, Any]) -> VerifierResult:
    name = "formal_logic.tautology"
    formula = spec.get("formula")
    claimed = spec.get("claimed_tautology")
    if formula is None or claimed is None:
        return na(name)
    var_names = spec.get("variables") or []
    try:
        # tautology iff every assignment makes the formula true
        is_taut = all(row[0] for row in truth_rows([formula], var_names))
    except BooleanParseError as e:
        return na(name, f"cannot parse formula: {e}")
    except Exception as e:  # noqa: BLE001
        return error(name, f"computation failure: {type(e).__name__}: {e}")
    claimed_b = bool(claimed)
    if is_taut == claimed_b:
        return confirm(name,
                       f"formula {formula!r} tautology={is_taut}, matches claim",
                       {"formula": formula, "actual": is_taut, "claimed": claimed_b})
    return mismatch(name,
                    f"formula {formula!r} tautology={is_taut}, claimed {claimed_b}",
                    {"formula": formula, "actual": is_taut, "claimed": claimed_b})


def verify_contradiction(spec: Dict[str, Any]) -> VerifierResult:
    name = "formal_logic.contradiction"
    formula = spec.get("formula")
    claimed = spec.get("claimed_contradiction")
    if formula is None or claimed is None:
        return na(name)
    var_names = spec.get("variables") or []
    try:
        # contradiction iff no assignment satisfies it
        is_contradiction = not satisfiable(formula, var_names)
    except BooleanParseError as e:
        return na(name, f"cannot parse formula: {e}")
    except Exception as e:  # noqa: BLE001
        return error(name, f"computation failure: {type(e).__name__}: {e}")
    claimed_b = bool(claimed)
    if is_contradiction == claimed_b:
        return confirm(name,
                       f"formula {formula!r} contradiction={is_contradiction}, matches claim",
                       {"formula": formula, "actual": is_contradiction, "claimed": claimed_b})
    return mismatch(name,
                    f"formula {formula!r} contradiction={is_contradiction}, claimed {claimed_b}",
                    {"formula": formula, "actual": is_contradiction, "claimed": claimed_b})


def verify_entailment(spec: Dict[str, Any]) -> VerifierResult:
    name = "formal_logic.entailment"
    premises = spec.get("premises")
    conclusion = spec.get("conclusion")
    claimed = spec.get("claimed_entailment")
    if not premises or conclusion is None or claimed is None:
        return na(name)
    var_names = spec.get("variables") or []
    try:
        # premises |= conclusion iff no row has every premise true but the conclusion false
        exprs = [str(p) for p in premises] + [str(conclusion)]
        entails = all(row[-1] or not all(row[:-1]) for row in truth_rows(exprs, var_names))
    except BooleanParseError as e:
        return na(name, f"cannot parse formula: {e}")
    except Exception as e:  # noqa: BLE001
        return error(name, f"computation failure: {type(e).__name__}: {e}")
    claimed_b = bool(claimed)
    if entails == claimed_b:
        return confirm(name,
                       f"premises |= conclusion = {entails}, matches claim",
                       {"premises": list(premises), "conclusion": conclusion,
                        "actual": entails, "claimed": claimed_b})
    return mismatch(name,
                    f"premises |= conclusion = {entails}, claimed {claimed_b}",
                    {"premises": list(premises), "conclusion": conclusion,
                     "actual": entails, "claimed": claimed_b})


def verify_equivalence(spec: Dict[str, Any]) -> VerifierResult:
    name = "formal_logic.equivalence"
    a = spec.get("formula_a")
    b = spec.get("formula_b")
    claimed = spec.get("claimed_equivalent")
    if a is None or b is None or claimed is None:
        return na(name)
    var_names = spec.get("variables") or []
    try:
        is_equiv = boolean_equivalent(a, b, var_names)
    except BooleanParseError as e:
        return na(name, f"cannot parse formula: {e}")
    except Exception as e:  # noqa: BLE001
        return error(name, f"computation failure: {type(e).__name__}: {e}")
    claimed_b = bool(claimed)
    if is_equiv == claimed_b:
        return confirm(name,
                       f"{a!r} === {b!r} = {is_equiv}, matches claim",
                       {"a": a, "b": b, "actual": is_equiv, "claimed": claimed_b})
    return mismatch(name,
                    f"{a!r} === {b!r} = {is_equiv}, claimed {claimed_b}",
                    {"a": a, "b": b, "actual": is_equiv, "claimed": claimed_b})


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    """Dispatch every applicable formal-logic check for the LOGIC_VERIFY block."""
    results: List[VerifierResult] = []
    lv = packet.get("LOGIC_VERIFY") or {}

    has_formula = "formula" in lv
    if has_formula and "claimed_satisfiable" in lv:
        results.append(verify_satisfiability(lv))
    if has_formula and "claimed_tautology" in lv:
        results.append(verify_tautology(lv))
    if has_formula and "claimed_contradiction" in lv:
        results.append(verify_contradiction(lv))
    if "premises" in lv and "conclusion" in lv and "claimed_entailment" in lv:
        results.append(verify_entailment(lv))
    if "formula_a" in lv and "formula_b" in lv and "claimed_equivalent" in lv:
        results.append(verify_equivalence(lv))

    if not results:
        results.append(na("formal_logic", "no LOGIC_VERIFY artifacts present"))
    return results
