"""VERIFIERS AS DATA, NOT DEPLOYS (Gen 3 · 2; docs/GEN3_CHARTER.md).

A verifier is a LAW applied to a claim: inputs, a relation, a tolerance, a source. Until now every one of
them was Python — a new domain was a deploy. This module runs a declarative SPEC through ONE generic
evaluator so a verified law can be contributed through the gate, held in the keeping as data
(data/verifier_specs.jsonl), carried to every node by capability 1, and run without a restart.

A spec (one JSON object per line):
    {"id": "spec_electrical", "domain": "electrical", "packet_key": "ELEC_VERIFY", "status": "admitted",
     "sources": [{"label": "Ohm, Die galvanische Kette (1827)", "pd": true}],
     "checks": [
        {"check": "ohms_law", "law": "V = I · R",
         "inputs": {"I": "current_A", "R": "resistance_ohm"}, "claimed": "voltage_V",
         "compute": "I * R", "tolerance": {"rel": 1e-3, "abs": 1e-6},
         "guards": [{"when": "R < 0", "error": "resistance must be non-negative"}],
         "goldens": {"true": {...packet...}, "false": {...packet...}}}
     ]}

Rules of the evaluator:
  * The expression language is an AST WHITELIST (stdlib `ast`): numbers, the bound input names, + - * / ** %,
    unary sign, list literals and indexing, and a fixed set of math functions. No attributes, no names
    outside the inputs, no calls outside the set. An expression that steps outside is an ERROR, never run.
  * A check fires when every input key and the claimed key are present in the artifact (a `compute` LIST
    is a set of equivalent forms: it fires when at least one form's inputs are present, and every form
    that can be computed must match — the cross-check `electrical.power` does in code).
  * Tolerance: the spec sets `rel`/`abs`; a caller may TIGHTEN through `tolerance_relative` /
    `tolerance_absolute` in the artifact but never loosen (base.clamp_tol).
  * A spec carries its own goldens and is refused at load if they do not hold. A spec that cannot prove
    itself does not run.
  * SHADOW: when a Python module already produced a result of the same name, the spec's result is not
    added — a spec extends a domain, it never contradicts code. A domain with no module is served by its
    specs alone: a new domain without a deploy.
  * Only `status: "admitted"` specs run on the public faces; anything else is listed as held.

Sovereign: stdlib only. Found, never generated: the evaluator computes what the law says and compares.
"""
from __future__ import annotations

import ast
import json
import math
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

from .base import VerifierResult, clamp_tol, confirm, error, mismatch, na

SPEC_FILE = "verifier_specs.jsonl"
MAX_EXPR = 400

_FUNCS: Dict[str, Callable[..., Any]] = {
    "sqrt": math.sqrt, "exp": math.exp, "log": math.log, "log10": math.log10, "log2": math.log2,
    "sin": math.sin, "cos": math.cos, "tan": math.tan, "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "atan2": math.atan2, "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh, "hypot": math.hypot,
    "floor": math.floor, "ceil": math.ceil, "abs": abs, "min": min, "max": max, "sum": sum, "len": len,
    "pow": pow, "round": round,
}
_CONSTS: Dict[str, float] = {"pi": math.pi, "e": math.e, "tau": math.tau, "inf": math.inf}
_BIN = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b, ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b, ast.Pow: lambda a, b: a ** b, ast.Mod: lambda a, b: a % b,
        ast.FloorDiv: lambda a, b: a // b}
_CMP = {ast.Lt: lambda a, b: a < b, ast.LtE: lambda a, b: a <= b, ast.Gt: lambda a, b: a > b,
        ast.GtE: lambda a, b: a >= b, ast.Eq: lambda a, b: a == b, ast.NotEq: lambda a, b: a != b}


class SpecError(ValueError):
    pass


# ── the expression language ─────────────────────────────────────────────────────────────────────
def _ev(node: ast.AST, env: Dict[str, Any]) -> Any:
    if isinstance(node, ast.Expression):
        return _ev(node.body, env)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise SpecError(f"only numbers are constants, not {node.value!r}")
        return node.value
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        if node.id in _CONSTS:
            return _CONSTS[node.id]
        raise SpecError(f"unknown name {node.id!r} (not an input)")
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
        return _BIN[type(node.op)](_ev(node.left, env), _ev(node.right, env))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        v = _ev(node.operand, env)
        return v if isinstance(node.op, ast.UAdd) else -v
    if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
        vals = [_ev(v, env) for v in node.values]
        return all(vals) if isinstance(node.op, ast.And) else any(vals)
    if isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in _CMP:
        return _CMP[type(node.ops[0])](_ev(node.left, env), _ev(node.comparators[0], env))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCS and not node.keywords:
        return _FUNCS[node.func.id](*[_ev(a, env) for a in node.args])
    if isinstance(node, ast.List):
        return [_ev(e, env) for e in node.elts]
    if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, int):
        seq = _ev(node.value, env)
        return seq[node.slice.value]
    raise SpecError(f"{type(node).__name__} is outside the expression language")


def safe_eval(expr: str, env: Dict[str, Any]) -> Any:
    """Evaluate a spec expression over the bound inputs; anything outside the whitelist raises SpecError."""
    if not isinstance(expr, str) or not expr.strip():
        raise SpecError("empty expression")
    if len(expr) > MAX_EXPR:
        raise SpecError(f"expression longer than {MAX_EXPR} characters")
    try:
        tree = ast.parse(expr.strip(), mode="eval")
    except SyntaxError as e:
        raise SpecError(f"cannot parse: {e.msg}") from None
    return _ev(tree, env)


def expr_names(expr: str) -> Set[str]:
    try:
        tree = ast.parse(expr.strip(), mode="eval")
    except SyntaxError:
        return set()
    return {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id not in _FUNCS and n.id not in _CONSTS}


# ── one check ───────────────────────────────────────────────────────────────────────────────────
def _num(v: Any) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float, str)):
        raise ValueError
    return float(v)


def run_check(domain: str, chk: Dict[str, Any], art: Dict[str, Any]) -> Optional[VerifierResult]:
    """Apply one spec check to one artifact. None when the check does not fire (inputs absent)."""
    name = f"{domain}.{chk.get('check')}"
    inputs: Dict[str, str] = dict(chk.get("inputs") or {})
    claimed_key = str(chk.get("claimed") or "")
    forms = chk.get("compute")
    forms = [forms] if isinstance(forms, str) else list(forms or [])
    if not claimed_key or claimed_key not in art or art.get(claimed_key) is None or not forms:
        return None
    # bind what is present
    env: Dict[str, Any] = {}
    for var, key in inputs.items():
        if key in art and art.get(key) is not None:
            env[var] = art[key]
    computable = [f for f in forms if expr_names(f) <= set(env)]
    if not computable:
        return None
    if len(forms) == 1 and set(inputs) - set(env):
        return None                                                  # a single form needs every input
    for extra in chk.get("requires") or []:
        if extra not in art:
            return None
    # numeric binding (lists stay lists)
    try:
        for k, v in list(env.items()):
            env[k] = [_num(x) for x in v] if isinstance(v, (list, tuple)) else _num(v)
        claimed = _num(art[claimed_key])
    except (TypeError, ValueError):
        return error(name, "all inputs and the claim must be numeric")
    for g in chk.get("guards") or []:
        try:
            if safe_eval(str(g.get("when") or "False"), env):
                return error(name, str(g.get("error") or f"guard failed: {g.get('when')}"))
        except (SpecError, ArithmeticError, ValueError, TypeError, IndexError) as e:
            return error(name, f"guard could not be evaluated: {e}")
    rel = clamp_tol(art, "tolerance_relative", float((chk.get("tolerance") or {}).get("rel", 1e-3)))
    ab = clamp_tol(art, "tolerance_absolute", float((chk.get("tolerance") or {}).get("abs", 1e-6)))
    values = []
    for f in computable:
        try:
            v = float(safe_eval(f, env))
        except SpecError as e:
            return error(name, f"the spec's expression is outside the language: {e}")
        except (ArithmeticError, ValueError, TypeError, IndexError) as e:
            return error(name, f"{f}: {type(e).__name__}: {e}")
        if not math.isfinite(v):
            return error(name, f"{f} is not finite")
        values.append((f, v))
    bad = []
    for f, v in values:
        if abs(v - claimed) > max(ab, rel * abs(v)):
            bad.append(f"{f} = {v:.6g}, claimed {claimed:.6g}")
    data = {"law": chk.get("law"), "inputs": {k: env[k] for k in env}, "claimed": claimed,
            "computed": {f: v for f, v in values}, "tolerance": {"rel": rel, "abs": ab}, "spec": True}
    if bad:
        return mismatch(name, "; ".join(bad), data)
    shown = ", ".join(f"{f} = {v:.6g}" for f, v in values)
    return confirm(name, f"{chk.get('law') or name}: {shown} (matches claim {claimed:.6g})", data)


# ── the specs on disk ───────────────────────────────────────────────────────────────────────────
_CACHE: Dict[str, Any] = {"path": None, "mtime": None, "specs": [], "refused": []}


def _data_dir() -> Path:
    d = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    return Path(d) if d else Path("data")


def spec_path(data_dir: Optional[Path] = None) -> Path:
    return (Path(data_dir) if data_dir else _data_dir()) / SPEC_FILE


_REQUIRED = ("id", "domain", "packet_key", "checks")


def validate(spec: Dict[str, Any]) -> List[str]:
    """Why a spec is malformed — [] when it is well-formed. Shape only; the goldens are judged by prove()."""
    why = []
    for k in _REQUIRED:
        if not spec.get(k):
            why.append(f"missing {k}")
    if not isinstance(spec.get("checks"), list) or not spec.get("checks"):
        return why or ["checks must be a non-empty list"]
    seen = set()
    for i, chk in enumerate(spec["checks"]):
        tag = f"checks[{i}]"
        if not isinstance(chk, dict):
            why.append(f"{tag} is not an object"); continue
        if not chk.get("check") or not str(chk["check"]).replace("_", "").isalnum():
            why.append(f"{tag}: check must be a plain name")
        if chk.get("check") in seen:
            why.append(f"{tag}: duplicate check {chk.get('check')!r}")
        seen.add(chk.get("check"))
        if not isinstance(chk.get("inputs"), dict) or not chk.get("inputs"):
            why.append(f"{tag}: inputs must map names to artifact keys")
        if not chk.get("claimed"):
            why.append(f"{tag}: claimed key missing")
        forms = chk.get("compute")
        forms = [forms] if isinstance(forms, str) else forms
        if not forms or not all(isinstance(f, str) for f in forms):
            why.append(f"{tag}: compute must be an expression or a list of them")
        else:
            names = set(chk.get("inputs") or {})
            for f in forms:
                try:
                    ast.parse(f, mode="eval")
                except SyntaxError:
                    why.append(f"{tag}: cannot parse {f!r}"); continue
                stray = expr_names(f) - names
                if stray:
                    why.append(f"{tag}: {f!r} uses names that are not inputs: {sorted(stray)}")
        g = chk.get("goldens") or {}
        if not isinstance(g, dict) or "true" not in g or "false" not in g:
            why.append(f"{tag}: goldens must carry a 'true' and a 'false' packet")
    return why


def prove(spec: Dict[str, Any]) -> List[str]:
    """Run every check's own goldens: the true packet must CONFIRM, the false must MISMATCH or ERROR.
    Returns the failures — [] when the spec proves itself."""
    fails = []
    for chk in spec.get("checks") or []:
        g = chk.get("goldens") or {}
        name = f"{spec.get('domain')}.{chk.get('check')}"
        r_true = run_check(str(spec.get("domain")), chk, dict(g.get("true") or {}))
        r_false = run_check(str(spec.get("domain")), chk, dict(g.get("false") or {}))
        if r_true is None or r_true.status != "CONFIRMED":
            fails.append(f"{name}: the true golden did not CONFIRM ({r_true.status + ': ' + r_true.detail if r_true else 'did not fire'})")
        if r_false is None or r_false.status not in ("MISMATCH", "ERROR"):
            fails.append(f"{name}: the false golden was not refused ({r_false.status if r_false else 'did not fire'})")
    return fails


def load(data_dir: Optional[Path] = None, force: bool = False) -> Dict[str, Any]:
    """Every spec on disk, proven: {"specs": [admitted + proven], "held": [...], "refused": [{id, why}]}.
    Re-read when the file changes — a new spec runs without a restart (that is the point)."""
    p = spec_path(data_dir)
    try:
        mtime = p.stat().st_mtime_ns
    except OSError:
        mtime = None
    if not force and _CACHE["path"] == str(p) and _CACHE["mtime"] == mtime:
        return {"specs": _CACHE["specs"], "held": _CACHE["held"], "refused": _CACHE["refused"]}
    specs: List[Dict[str, Any]] = []
    held: List[Dict[str, Any]] = []
    refused: List[Dict[str, Any]] = []
    if mtime is not None:
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except OSError:
            lines = []
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                spec = json.loads(line)
            except ValueError:
                refused.append({"id": f"line {i + 1}", "why": "not JSON"}); continue
            why = validate(spec) if isinstance(spec, dict) else ["not an object"]
            if why:
                refused.append({"id": spec.get("id") if isinstance(spec, dict) else f"line {i + 1}", "why": "; ".join(why)}); continue
            fails = prove(spec)
            if fails:
                refused.append({"id": spec["id"], "why": "; ".join(fails)}); continue
            (specs if spec.get("status") == "admitted" else held).append(spec)
    _CACHE.update({"path": str(p), "mtime": mtime, "specs": specs, "held": held, "refused": refused})
    return {"specs": specs, "held": held, "refused": refused}


def run_for_domain(domain: str, packet: Dict[str, Any], have: Iterable[str] = (),
                   data_dir: Optional[Path] = None) -> List[VerifierResult]:
    """The admitted specs of a domain applied to a packet; results whose name a module already produced
    are shadowed (dropped), so a spec extends and never contradicts code."""
    d = (domain or "").lower()
    taken = set(have)
    out: List[VerifierResult] = []
    for spec in load(data_dir)["specs"]:
        if str(spec.get("domain", "")).lower() != d:
            continue
        art = packet.get(str(spec.get("packet_key"))) or {}
        if not isinstance(art, dict):
            continue
        for chk in spec.get("checks") or []:
            r = run_check(d, chk, art)
            if r is None or r.name in taken:
                continue
            taken.add(r.name)
            out.append(r)
    return out


def domains(data_dir: Optional[Path] = None) -> List[str]:
    return sorted({str(s.get("domain")).lower() for s in load(data_dir)["specs"]})


def catalog(data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """What the node holds as data: every admitted check with its law and sources, the held, the refused."""
    lo = load(data_dir)
    checks = []
    for s in lo["specs"]:
        for c in s.get("checks") or []:
            checks.append({"domain": s.get("domain"), "check": c.get("check"), "law": c.get("law"),
                           "inputs": c.get("inputs"), "claimed": c.get("claimed"), "spec": s.get("id"),
                           "sources": s.get("sources"), "seal": s.get("seal"), "packet_key": s.get("packet_key")})
    return {"checks": checks, "count": len(checks), "domains": domains(data_dir),
            "held": [{"id": s.get("id"), "status": s.get("status")} for s in lo["held"]],
            "refused": lo["refused"], "file": SPEC_FILE,
            "note": ("A spec is a law applied to a claim, held as data and run by one generic evaluator. Each carries "
                     "its own goldens and is refused at load if they fail. A spec never contradicts code: a result a "
                     "Python verifier already produced shadows the spec's. New checks ship without a deploy.")}


def admit(spec: Dict[str, Any], data_dir: Optional[Path] = None, *, seal: bool = True) -> Dict[str, Any]:
    """The operator path (Gen 3 · 2 v1; the agent path with standing is capability 6): validate, prove,
    seal the spec as a CAS record, append it admitted. Replaces an earlier spec of the same id."""
    why = validate(spec)
    if why:
        return {"ok": False, "why": why}
    fails = prove(spec)
    if fails:
        return {"ok": False, "why": fails}
    rec = dict(spec)
    rec["status"] = "admitted"
    rec["admitted_at"] = int(time.time())
    if seal:
        from .. import cas
        body = {k: v for k, v in rec.items() if k not in ("seal", "admitted_at")}
        rec["seal"] = cas.store({"kind": "verifier_spec", "spec": body})
    p = spec_path(data_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    kept = []
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                old = json.loads(line)
            except ValueError:
                continue
            if isinstance(old, dict) and old.get("id") != rec["id"]:
                kept.append(json.dumps(old, ensure_ascii=False))
    kept.append(json.dumps(rec, ensure_ascii=False))
    tmp = p.with_suffix(".tmp")
    tmp.write_text("\n".join(kept) + "\n", encoding="utf-8")
    os.replace(tmp, p)
    load(data_dir, force=True)
    return {"ok": True, "id": rec["id"], "checks": len(rec["checks"]), "seal": rec.get("seal"), "file": str(p)}
