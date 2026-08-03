#!/usr/bin/env python3
"""THE GAUGE PANEL — every constant that turns a measurement into a verdict, and what it costs.

    PYTHONPATH=src python tools/gauge_panel.py
    PYTHONPATH=src python tools/gauge_panel.py --json
    PYTHONPATH=src python tools/gauge_panel.py --max-relative 0.05   # gate on the loosest gauge

A verifier does two things: it computes a true value, and then it decides whether the caller's
claim is close enough. The first half is physics and is checkable. The SECOND half is a number
someone typed, and it is the half nobody looks at -- yet it is the half that decides.

A tolerance is not a formatting preference. It is the width of the door a falsehood can walk
through. At tolerance_relative = 1e-3 a claim must be right to a tenth of a percent; at 0.02 it
can be off by 2%, which on a 400 mg dose is 8 mg and on a 5,000 km flight is 100 km. Both are
CONFIRMED, both get a seal, and the seal does not say which door it came through.

So this instrument does not print a list of constants. It converts each one into the sentence
that actually matters:

    in <verifier>, a claim can be wrong by <this much> and still be sealed CONFIRMED.

WHY AST AND NOT GREP. The defaults are the last argument of clamp_tol(spec, key, default) and
they appear as literals, negated literals, and small arithmetic expressions. A regex reads some
of those wrong and silently skips the rest, and a survey that silently skips is worse than no
survey -- it reports a clean panel it never actually looked at. The parser reads what Python
reads.

THE KINDS. Not every loose gauge is a defect, and a panel that cries wolf gets ignored, which
costs more than never building it:
  * SCALED       -- the default is an EXPRESSION over the value being checked, e.g.
                    max(0.001, actual * 0.005). This is the target pattern and the whole point of
                    the exercise: the gauge is a formula on the measured curve, so it stays right
                    as the quantity changes instead of being right at one magnitude and absurd at
                    another. These are held up, not flagged.
  * FLOAT-NOISE  -- <= 1e-6, guarding IEEE754 comparison rather than judgement. Invisible, correct.
  * CONVENTIONAL -- a tolerance the field itself publishes (0.5 degC instrument spec, 5 kcal
                    food-label rounding). Loose on purpose and defensible.
  * FIXED        -- a constant absolute tolerance. Not wrong, but right only at the magnitude the
                    author had in mind; the candidates for promotion to SCALED live here.
  * WIDE         -- a RELATIVE gauge above a tenth of a percent: a door whose width was chosen.

A NOTE ON NOT KNOWING. The default's key does not always say whether it is relative or absolute
-- a bare "tolerance" could be either, and the first run of this panel guessed "relative" and
reported economics.rule_of_72 as letting a claim be wrong by 50%. It is 0.5 YEARS on a doubling
time, which is fine. That was this instrument failing, not the verifier, and the fix is to report
UNKNOWN-UNIT rather than guess. Our failure is never their falsehood.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLEET = os.path.join(ROOT, "src", "concordance", "verifiers")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FLOAT_NOISE = 1e-6          # at or below this, the gauge is guarding arithmetic, not truth

# Keys whose name genuinely does not settle their unit. Listed rather than inferred, because a
# suffix rule mis-files them with confidence: "tolerance_pct" LOOKS like it declares a unit, and
# in soil_science it means ten percentage points while in sports_analytics it is an absolute
# 0.005 on a 0-1 fraction. Reading it either way libels one of the two.
AMBIGUOUS_KEYS = {"tolerance", "tolerance_pct", "tolerance_percent"}

# Gauges that are loose because the FIELD is loose, each with the reason it is defensible.
# Anything not named here and above the float-noise floor is reported as WIDE -- the burden of
# proof sits on the constant, not on the reader.
CONVENTIONAL = {
    ("nutrition", "tolerance_kcal"): "food labels are rounded to the nearest 5 kcal by regulation",
    ("meteorology", "tolerance_c"): "0.5 degC is the stated accuracy of ordinary field thermometers",
    ("atomic", "tolerance_ev"): "0.1 eV is the spread across published ionisation tables",
    ("periodic_table", "tolerance_ev"): "0.1 eV is the spread across published ionisation tables",
    ("geography", "tolerance_deg"): "1 deg of bearing is finer than a hand compass can be read",
    ("medicine", "tolerance_absolute"): "clinical reference ranges are themselves interval-valued",
}


def _literal(node):
    """Evaluate a default that is a literal, a negation, or simple constant arithmetic."""
    try:
        return float(ast.literal_eval(node))
    except (ValueError, TypeError, SyntaxError):
        pass
    try:                                    # 1/298.257... and friends
        return float(eval(compile(ast.Expression(node), "<gauge>", "eval"), {"__builtins__": {}}))
    except Exception:                        # noqa: BLE001 — a gauge we cannot read is REPORTED
        return None


def collect():
    gauges, unreadable = [], []
    for fn in sorted(os.listdir(FLEET)):
        if not fn.endswith(".py") or fn.startswith("_"):
            continue
        domain = fn[:-3]
        path = os.path.join(FLEET, fn)
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        try:
            tree = ast.parse(src, filename=path)
        except SyntaxError as exc:
            unreadable.append((domain, f"unparseable: {exc}"))
            continue
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and getattr(node.func, "id", "") == "clamp_tol"):
                continue
            if len(node.args) < 3:
                unreadable.append((domain, f"line {node.lineno}: clamp_tol with <3 args"))
                continue
            key = (node.args[1].value if isinstance(node.args[1], ast.Constant) else None)
            val = _literal(node.args[2])
            expr = ast.unparse(node.args[2])
            gauges.append({"domain": domain, "key": str(key), "value": val,
                           "expr": expr, "line": node.lineno})
    return gauges, unreadable


def _is_relative(key: str):
    """True / False / None(=cannot tell). Never guess — see the note in the module docstring.

    tolerance_pct is deliberately NOT treated as relative. The fleet uses that one key for two
    different things: soil_science passes 10.0 meaning ten percentage points, sports_analytics
    passes 0.005 as an absolute tolerance on a 0-1 fraction. Reading it either way libels one of
    them, so the panel says it cannot tell and reports the collision instead.
    """
    if key in AMBIGUOUS_KEYS:
        return None               # named ambiguous BEFORE any suffix rule can claim it
    if "relative" in key or key == "rel_tol":
        return True
    if key.startswith("tolerance_") and key != "tolerance_relative":
        return False              # tolerance_km, tolerance_deg, tolerance_kcal ... carry a unit
    if key in ("tolerance_absolute",):
        return False
    return None                   # a bare "tolerance" says nothing about its own unit


def classify(g):
    if g["value"] is None:
        return "SCALED", f"a formula on the measured value: {g['expr']}"
    if abs(g["value"]) <= FLOAT_NOISE:
        return "FLOAT-NOISE", "guards IEEE754 comparison, not judgement"
    why = CONVENTIONAL.get((g["domain"], g["key"]))
    if why:
        return "CONVENTIONAL", why
    rel = _is_relative(g["key"])
    if rel is True and abs(g["value"]) > 1e-3:
        return "WIDE", "a relative door wider than a tenth of a percent, chosen not derived"
    if rel is None:
        return "UNKNOWN-UNIT", "the key does not say whether this is relative or absolute"
    if rel is True:
        return "FLOAT-NOISE", "relative and tight"
    return "FIXED", "a constant absolute tolerance — right at one magnitude, a candidate for SCALED"


def door_width(g):
    """The sentence that matters: how wrong may a claim be and still seal?"""
    k, v = g["key"], g["value"]
    if v is None:
        return f"scales: {g['expr'][:40]}"
    rel = _is_relative(k)
    if rel is True:
        return f"{v * 100:.4g}% of the true value"
    unit = k.replace("tolerance_", "").replace("tolerance", "").strip("_")
    if rel is None:
        return f"{v:g} (unit undeclared)"
    return f"{v:g} {unit or 'absolute'}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max-relative", type=float, default=None,
                    help="fail if any non-conventional relative gauge exceeds this")
    args = ap.parse_args()

    gauges, unreadable = collect()
    for g in gauges:
        g["kind"], g["reason"] = classify(g)
        g["door"] = door_width(g)

    kinds = {}
    for g in gauges:
        kinds[g["kind"]] = kinds.get(g["kind"], 0) + 1
    flagged = sorted([g for g in gauges if g["kind"] in ("WIDE", "UNKNOWN-UNIT")],
                     key=lambda g: (g["kind"] != "WIDE", -abs(g["value"] or 0.0)))

    if args.json:
        print(json.dumps({"gauges": gauges, "unreadable": unreadable, "counts": kinds}, indent=2))
        return 0

    # COVERAGE FIRST.
    files = len({g["domain"] for g in gauges})
    print(f"GAUGE PANEL — {len(gauges)} verdict-deciding constants across {files} verifiers, "
          f"read by AST")
    if unreadable:
        print(f"  !! {len(unreadable)} NOT READ — a survey that skips silently is not a survey:")
        for d, why in unreadable[:10]:
            print(f"     {d}: {why}")
    print()
    labels = {"SCALED": "already a formula on the measured value — the target pattern",
              "FLOAT-NOISE": "guarding arithmetic, not judgement",
              "CONVENTIONAL": "the field itself publishes this width",
              "FIXED": "constant absolute — candidates for promotion to SCALED",
              "WIDE": "relative door wider than 0.1% — chosen, not derived",
              "UNKNOWN-UNIT": "the key does not declare relative or absolute"}
    for k in ("SCALED", "FLOAT-NOISE", "CONVENTIONAL", "FIXED", "WIDE", "UNKNOWN-UNIT"):
        print(f"  {k:14s} {kinds.get(k, 0):4d}   {labels[k]}")
    # AMBIGUOUS KEYS, AND WHAT THEY ACTUALLY RISK. clamp_tol takes min(|caller|, |default|), so a
    # caller can only ever TIGHTEN a gauge, never loosen it. That means a collision cannot open a
    # door and cannot manufacture a false CONFIRMED — the first draft of this panel said it could,
    # which was an overstatement in exactly the direction this project must never overstate.
    #
    # The real cost runs the other way. One packet is offered to many verifiers, so a caller who
    # sets tolerance_absolute=1e-9 to sharpen a chemistry check also sharpens every other verifier
    # reading that key in the same packet — including ones whose honest working width is 0.5. The
    # result is FALSE NEGATIVES: true claims returned as MISMATCH. That is less dangerous than a
    # false seal and still a defect, because a library that rejects true things teaches its
    # readers to ignore it. Spread across orders of magnitude is the signal.
    by_key = {}
    for g in gauges:
        if g["value"]:
            by_key.setdefault(g["key"], []).append(g)
    collisions = []
    for key, gs in by_key.items():
        vals = [abs(x["value"]) for x in gs]
        if len(gs) > 1 and max(vals) / min(vals) >= 100:
            collisions.append((key, min(vals), max(vals),
                               sorted({x["domain"] for x in gs})))
    if collisions:
        print()
        print("  AMBIGUOUS GAUGE KEYS — one name, incompatible meanings. clamp_tol means these")
        print("  cannot open a door (a caller may only tighten); the risk is the mirror image —")
        print("  tightening one verifier over-tightens its neighbours in the same packet, and")
        print("  true claims come back MISMATCH:")
        for key, lo, hi, doms in sorted(collisions, key=lambda c: -(c[2] / c[1])):
            print(f"    {key:22s} {lo:<12g} .. {hi:<12g} ({hi / lo:,.0f}x)  {', '.join(doms[:6])}")

    print()
    print("  NEEDING A MEASURED CURVE — how wrong a claim may be and still be sealed CONFIRMED:")
    print(f"  {'verifier':22s} {'gauge':22s} {'a claim may be off by':28s} {'kind':13s} line")
    for g in flagged[:18]:
        print(f"  {g['domain']:22s} {g['key']:22s} {g['door']:28s} {g['kind']:13s} {g['line']}")
    if len(flagged) > 18:
        print(f"  ... and {len(flagged) - 18} more (--json for all) — NOT truncated silently")

    if args.max_relative is not None:
        over = [g for g in gauges
                if g["kind"] == "WIDE" and abs(g["value"] or 0.0) > args.max_relative]
        print()
        if over:
            print(f"  GAUGE GATE FAIL: {len(over)} relative gauge(s) wider than "
                  f"{args.max_relative:g}")
            for g in over:
                print(f"     {g['domain']}.{g['key']} = {g['value']:g} (line {g['line']})")
            return 1
        print(f"  GAUGE GATE PASS: no non-conventional relative gauge exceeds "
              f"{args.max_relative:g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
