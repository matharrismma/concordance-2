"""Pure-stdlib propositional equivalence — no sympy, so it runs on the sovereign stdlib-only box.

Two Boolean formulas are equivalent exactly when they share a truth table. For the handful of
variables a logic-gate or set-algebra identity carries, enumerating all 2^n assignments is exact
and instant — and needs nothing but the standard library, unlike the SAT path in formal_logic
(which imports sympy and is therefore inert where sympy is not installed).

The evaluator is a strict AST allowlist: only Boolean structure is permitted — the operators
& (AND) | (OR) ~ (NOT) ^ (XOR) >> (IMPLIES), the `and`/`or`/`not` keywords, declared variable
names, and the constants True/False. Anything else (a call, an attribute, an unknown name, a
number) is refused. There is no eval and no sympify, so a formula can never carry code — the same
guarantee the math/logic verifiers reach through a separate guard, here structural by construction.
"""
from __future__ import annotations

import ast
import itertools
from typing import Dict, List

# Cap the enumeration so a pathological input cannot hang the box. Gate and set identities carry a
# few variables; 2^20 (~1M rows) is already far past anything real, and the caller treats an
# over-cap formula as NOT_APPLICABLE rather than pretending to have checked it.
MAX_VARS = 20


class BooleanParseError(ValueError):
    """The string is not a well-formed Boolean formula over the declared variables."""


_BINOPS = {
    ast.BitAnd: lambda a, b: a and b,
    ast.BitOr: lambda a, b: a or b,
    ast.BitXor: lambda a, b: a != b,
    ast.RShift: lambda a, b: (not a) or b,   # p >> q  ==  p implies q
}


def _eval(node: ast.AST, env: Dict[str, bool]) -> bool:
    if isinstance(node, ast.Expression):
        return _eval(node.body, env)
    if isinstance(node, ast.BoolOp):
        vals = [_eval(v, env) for v in node.values]
        return all(vals) if isinstance(node.op, ast.And) else any(vals)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.Not, ast.Invert)):
        return not _eval(node.operand, env)
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        return bool(_BINOPS[type(node.op)](_eval(node.left, env), _eval(node.right, env)))
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise BooleanParseError(f"unknown symbol {node.id!r}")
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return node.value
    raise BooleanParseError(f"unsupported expression element: {type(node).__name__}")


def _tree(formula: str) -> ast.Expression:
    try:
        return ast.parse(formula, mode="eval")
    except SyntaxError as e:
        raise BooleanParseError(f"cannot parse {formula!r}: {e}") from e


def _assignments(variables: List[str]):
    vars_ = list(variables or [])
    if len(vars_) > MAX_VARS:
        raise BooleanParseError(f"{len(vars_)} variables exceeds the {MAX_VARS}-variable enumeration cap")
    for combo in itertools.product((False, True), repeat=len(vars_)):
        yield dict(zip(vars_, combo))


def truth_rows(exprs: List[str], variables: List[str]):
    """Yield, for every assignment of `variables`, the tuple of the exprs' truth values.

    One engine for every Boolean check — equivalence, satisfiability, tautology, entailment all
    read these rows. Raises BooleanParseError on a malformed expr, an undeclared symbol, or a
    variable count over MAX_VARS. Pure standard library.
    """
    trees = [_tree(e) for e in exprs]
    for env in _assignments(variables):
        yield tuple(_eval(t, env) for t in trees)


def satisfiable(expr: str, variables: List[str]) -> bool:
    """True iff some assignment of `variables` makes `expr` true (exact enumeration)."""
    tree = _tree(expr)
    return any(_eval(tree, env) for env in _assignments(variables))


def boolean_equivalent(expr_a: str, expr_b: str, variables: List[str]) -> bool:
    """True iff expr_a and expr_b have identical truth tables over `variables`.

    Raises BooleanParseError if either string is malformed, references an undeclared symbol, or the
    variable count exceeds MAX_VARS. Exact — enumerates every assignment; pure standard library.
    """
    return all(a == b for a, b in truth_rows([expr_a, expr_b], variables))
