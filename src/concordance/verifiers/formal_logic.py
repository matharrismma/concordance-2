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
  * formal_logic.minimal_form
      claimed_minimal is a two-level sum-of-products equivalent to formula (truth table), AND no
      equivalent sum-of-products has fewer product terms: Quine-McCluskey Quine-McCluskey implicants plus an
      exhaustive minimum cover over the minterms, decided EXACTLY for <= 4 variables (16 minterms).
      Five or more variables -> NOT_APPLICABLE with the reason (bounded, never a guess); a claim that
      is not two-level (a negated group, >>, ^) -> NOT_APPLICABLE. MISMATCH names the true minimum.

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
      "claimed_minimal": "p",                # minimal_form: a two-level sum-of-products over `variables`,
      "claimed_minimal_terms": 1,            #   checked against `formula`; the term count is optional
    }
"""
from __future__ import annotations

import ast
import itertools
from typing import Any, Dict, List, Tuple

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


# ---- minimal two-level form: Quine-McCluskey, exact up to MINIMAL_FORM_MAX_VARS variables ----

# 2^4 = 16 minterms. A four-variable function has at most 13 prime implicants, so the exhaustive
# minimum-cover search below is a few thousand subset checks at worst — instant and exact. At five
# variables the prime-implicant count can reach 32 and the cover search is no longer bounded, so the
# verifier declines (NOT_APPLICABLE with the reason) rather than guess.
MINIMAL_FORM_MAX_VARS = 4

# An implicant is (value, mask) over the declared variables: variable j is bit j; a mask bit set
# means that variable is free (don't-care); a fixed variable takes the bit of `value`. Free bits of
# `value` are kept 0 so equal implicants compare equal.
Implicant = Tuple[int, int]


def _sop_terms(formula: str, variables: List[str]) -> List[frozenset]:
    """The product terms of a two-level sum-of-products, each a frozenset of (name, polarity).

    Parsed with `ast` as _boolean does: a BitOr (or `or`) of BitAnd (or `and`) groups whose leaves are
    a declared Name or its Invert / `not`. A bare product or a bare literal is a one-term sum. The two
    degenerate forms are the constants: True is the empty product (one term, no literals), False the
    empty sum (zero terms). Anything else — a negated group, >>, ^, a call, a number, an undeclared
    name — raises BooleanParseError: the claim is not two-level, so minimality is not even the question.
    """
    try:
        tree = ast.parse(formula, mode="eval")
    except SyntaxError as e:
        raise BooleanParseError(f"cannot parse {formula!r}: {e}") from e
    declared = set(variables)

    def literal(node: ast.AST) -> Tuple[str, bool]:
        if (isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.Invert, ast.Not))
                and isinstance(node.operand, ast.Name)):
            name, polarity = node.operand.id, False
        elif isinstance(node, ast.Name):
            name, polarity = node.id, True
        else:
            raise BooleanParseError(f"not two-level: {type(node).__name__} inside a product term")
        if name not in declared:
            raise BooleanParseError(f"unknown symbol {name!r}")
        return name, polarity

    def product(node: ast.AST) -> frozenset:
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitAnd):
            return product(node.left) | product(node.right)
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
            return frozenset().union(*(product(v) for v in node.values))
        return frozenset([literal(node)])

    def total(node: ast.AST) -> List[frozenset]:
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return total(node.left) + total(node.right)
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            return [t for v in node.values for t in total(v)]
        return [product(node)]

    body = tree.body
    if isinstance(body, ast.Constant) and isinstance(body.value, bool):
        return [frozenset()] if body.value else []
    return total(body)


def _minterms(formula: str, variables: List[str]) -> List[int]:
    """The on-set of `formula`: every assignment (as an int, variable j at bit j) that makes it true."""
    n = len(variables)
    out: List[int] = []
    for i, (val,) in enumerate(truth_rows([formula], variables)):
        if val:
            # truth_rows enumerates itertools.product order: the FIRST variable is the most significant
            out.append(sum(1 << j for j in range(n) if (i >> (n - 1 - j)) & 1))
    return out


def _prime_implicants(minterms: List[int], n: int) -> List[Implicant]:
    """Quine-McCluskey: every prime implicant of the function whose on-set is `minterms`.

    Two implicants with the same free-mask that differ in exactly one fixed bit combine into one with
    that bit freed; an implicant that combines with nothing at its level is prime. Exact.
    """
    current = {(m, 0) for m in minterms}
    primes: set = set()
    while current:
        nxt: set = set()
        combined: set = set()
        by_mask: Dict[int, set] = {}
        for v, m in current:
            by_mask.setdefault(m, set()).add(v)
        for m, vals in by_mask.items():
            for v in vals:
                for bit in range(n):
                    b = 1 << bit
                    if (m & b) or (v & b):          # bit already free, or pair seen from its 0 side
                        continue
                    if (v | b) in vals:
                        nxt.add((v, m | b))
                        combined.add((v, m))
                        combined.add((v | b, m))
        primes.update(imp for imp in current if imp not in combined)
        current = nxt
    return sorted(primes)


def _covers(imp: Implicant, minterm: int) -> bool:
    v, m = imp
    return (minterm & ~m) == (v & ~m)


def _minimum_cover(primes: List[Implicant], minterms: List[int]) -> List[Implicant]:
    """The fewest prime implicants covering every minterm — exhaustive by increasing size, so exact.

    A minimum-term sum-of-products can always be taken from the prime implicants (any implicant
    widens to a prime one without adding a term), so this minimum is the minimum over ALL SOPs.
    """
    need = set(minterms)
    if not need:
        return []
    cov = {imp: {mt for mt in need if _covers(imp, mt)} for imp in primes}
    for k in range(1, len(primes) + 1):
        for combo in itertools.combinations(primes, k):
            if set().union(*(cov[i] for i in combo)) >= need:
                return list(combo)
    return list(primes)      # unreachable: the primes together cover the whole on-set


def _implicant_str(imp: Implicant, variables: List[str]) -> str:
    v, m = imp
    lits = [(name if (v >> j) & 1 else "~" + name) for j, name in enumerate(variables) if not (m >> j) & 1]
    return " & ".join(lits) if lits else "True"


def verify_minimal_form(spec: Dict[str, Any]) -> VerifierResult:
    """CONFIRMED iff claimed_minimal === formula (truth table) AND no equivalent two-level
    sum-of-products has fewer product terms (Quine-McCluskey + exhaustive minimum cover, exact for
    <= MINIMAL_FORM_MAX_VARS variables). MISMATCH when not equivalent, or when a smaller cover exists
    (the minimum is named). NOT_APPLICABLE when the claim is not two-level, or when the variable
    count is past the bound — bounded, never a guess."""
    name = "formal_logic.minimal_form"
    formula = spec.get("formula")
    claimed = spec.get("claimed_minimal")
    if formula is None or claimed is None:
        return na(name)
    formula, claimed = str(formula), str(claimed)
    var_names = [str(v) for v in (spec.get("variables") or [])]
    try:
        terms = _sop_terms(claimed, var_names)
    except BooleanParseError as e:
        return na(name, f"claimed_minimal is not a two-level sum-of-products over the declared variables: {e}")
    stated = spec.get("claimed_minimal_terms")
    if stated is not None:
        try:
            stated = int(stated)
        except (TypeError, ValueError):
            return na(name, "claimed_minimal_terms must be an integer")
    try:
        equiv = boolean_equivalent(claimed, formula, var_names)
    except BooleanParseError as e:
        return na(name, f"cannot parse formula: {e}")
    except Exception as e:  # noqa: BLE001
        return error(name, f"computation failure: {type(e).__name__}: {e}")
    claimed_terms = len(terms)
    data: Dict[str, Any] = {"formula": formula, "claimed_minimal": claimed, "claimed_terms": claimed_terms,
                            "variables": var_names, "equivalent": equiv}
    if not equiv:
        return mismatch(name, f"{claimed!r} is not equivalent to {formula!r}: the truth tables differ", data)
    if stated is not None and stated != claimed_terms:
        data["claimed_minimal_terms"] = stated
        return mismatch(name, f"claimed_minimal_terms={stated} but {claimed!r} has {claimed_terms} product term(s)", data)
    n = len(var_names)
    if n > MINIMAL_FORM_MAX_VARS:
        return na(name, f"equivalent, but minimality is decided exactly only up to {MINIMAL_FORM_MAX_VARS} variables "
                        f"({n} declared): whether a smaller cover exists is not decided here — bounded, never guessed",
                  data)
    try:
        minterms = _minterms(formula, var_names)
        primes = _prime_implicants(minterms, n)
        cover = _minimum_cover(primes, minterms)
    except Exception as e:  # noqa: BLE001
        return error(name, f"computation failure: {type(e).__name__}: {e}")
    minimum = len(cover)
    data.update({"minimum_terms": minimum, "minterms": minterms,
                 "prime_implicants": [_implicant_str(p, var_names) for p in primes],
                 "minimum_cover": [_implicant_str(p, var_names) for p in cover]})
    if claimed_terms == minimum:
        return confirm(name, f"{claimed!r} === {formula!r} and no equivalent sum-of-products has fewer than "
                             f"{minimum} product term(s) (Quine-McCluskey over {n} variable(s))", data)
    smaller = " | ".join(f"({t})" for t in data["minimum_cover"]) or "False"
    return mismatch(name, f"{claimed!r} === {formula!r} but a smaller cover exists: the minimum is {minimum} "
                          f"product term(s), e.g. {smaller}; claimed {claimed_terms}", data)


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
    if has_formula and "claimed_minimal" in lv:
        results.append(verify_minimal_form(lv))
    if "premises" in lv and "conclusion" in lv and "claimed_entailment" in lv:
        results.append(verify_entailment(lv))
    if "formula_a" in lv and "formula_b" in lv and "claimed_equivalent" in lv:
        results.append(verify_equivalence(lv))

    if not results:
        results.append(na("formal_logic", "no LOGIC_VERIFY artifacts present"))
    return results
