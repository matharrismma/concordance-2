"""Compute — the deterministic calculator behind the front door.

Matt, 2026-07-25: "still falling short in real life use." A verification engine that answers
"what is 15 percent of 240" with a keyword-matched card, or "convert 10 miles to km" with a
"kilometers per hour" card, is not useful. This turns the plainest computational questions —
arithmetic, percentages, roots, unit conversions, temperature — into a DIRECT, exact answer,
computed (never generated, never guessed). Purely numeric: it declines anything it cannot compute
exactly, so the front door falls through to search rather than risk a wrong number.

    compute.answer("what is 15 percent of 240")   -> "15% of 240 = 36"
    compute.answer("convert 10 miles to kilometers") -> "10 miles = 16.0934 kilometers"
    compute.answer("100 fahrenheit in celsius")    -> "100 °F = 37.78 °C"
"""
from __future__ import annotations

import ast
import operator
import re
from typing import Optional

# ── unit conversion — factor to a base unit per dimension (L=meter, M=gram, V=liter, T=second) ──
_UNITS = {
    "meter": ("L", 1.0), "meters": ("L", 1.0), "metre": ("L", 1.0), "m": ("L", 1.0),
    "kilometer": ("L", 1000.0), "kilometers": ("L", 1000.0), "km": ("L", 1000.0),
    "mile": ("L", 1609.344), "miles": ("L", 1609.344), "mi": ("L", 1609.344),
    "foot": ("L", 0.3048), "feet": ("L", 0.3048), "ft": ("L", 0.3048),
    "inch": ("L", 0.0254), "inches": ("L", 0.0254),
    "yard": ("L", 0.9144), "yards": ("L", 0.9144), "yd": ("L", 0.9144),
    "centimeter": ("L", 0.01), "centimeters": ("L", 0.01), "cm": ("L", 0.01),
    "millimeter": ("L", 0.001), "millimeters": ("L", 0.001), "mm": ("L", 0.001),
    "gram": ("M", 1.0), "grams": ("M", 1.0), "g": ("M", 1.0),
    "kilogram": ("M", 1000.0), "kilograms": ("M", 1000.0), "kg": ("M", 1000.0),
    "pound": ("M", 453.59237), "pounds": ("M", 453.59237), "lb": ("M", 453.59237), "lbs": ("M", 453.59237),
    "ounce": ("M", 28.349523), "ounces": ("M", 28.349523), "oz": ("M", 28.349523),
    "ton": ("M", 907184.74), "tons": ("M", 907184.74),
    "liter": ("V", 1.0), "liters": ("V", 1.0), "litre": ("V", 1.0), "l": ("V", 1.0),
    "milliliter": ("V", 0.001), "milliliters": ("V", 0.001), "ml": ("V", 0.001),
    "gallon": ("V", 3.785411), "gallons": ("V", 3.785411),
    "quart": ("V", 0.946353), "quarts": ("V", 0.946353),
    "pint": ("V", 0.473176), "pints": ("V", 0.473176),
    "cup": ("V", 0.236588), "cups": ("V", 0.236588),
    "second": ("T", 1.0), "seconds": ("T", 1.0), "sec": ("T", 1.0),
    "minute": ("T", 60.0), "minutes": ("T", 60.0), "min": ("T", 60.0),
    "hour": ("T", 3600.0), "hours": ("T", 3600.0), "hr": ("T", 3600.0),
    "day": ("T", 86400.0), "days": ("T", 86400.0), "week": ("T", 604800.0), "weeks": ("T", 604800.0),
}
_TEMP = {"fahrenheit": "f", "celsius": "c", "centigrade": "c", "kelvin": "k"}


def _fmt(x: float) -> str:
    """A clean number: integers as integers, else up to 6 significant decimals, no trailing zeros."""
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return f"{round(x, 6):g}"


def _to_celsius(v: float, u: str) -> float:
    return (v - 32) * 5 / 9 if u == "f" else (v - 273.15 if u == "k" else v)


def _from_celsius(c: float, u: str) -> float:
    return c * 9 / 5 + 32 if u == "f" else (c + 273.15 if u == "k" else c)


def _temperature(t: str) -> Optional[str]:
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:degrees?\s*)?(fahrenheit|celsius|centigrade|kelvin)\b"
                  r".*?\b(?:to|in|into|as)\b\s*(?:degrees?\s*)?(fahrenheit|celsius|centigrade|kelvin)\b", t)
    if not m:
        return None
    val = float(m.group(1)); frm = _TEMP[m.group(2)]; to = _TEMP[m.group(3)]
    out = _from_celsius(_to_celsius(val, frm), to)
    sym = {"f": "°F", "c": "°C", "k": "K"}
    return f"{_fmt(val)} {sym[frm]} = {_fmt(round(out, 2))} {sym[to]}"


def _do_convert(val: float, u1: str, u2: str) -> Optional[str]:
    a, b = _UNITS.get(u1), _UNITS.get(u2)
    if not a or not b or a[0] != b[0]:
        return None
    return f"{_fmt(val)} {u1} = {_fmt(val * a[1] / b[1])} {u2}"


def _convert(t: str) -> Optional[str]:
    r = _temperature(t)
    if r:
        return r
    m = re.search(r"how many ([a-z]+)\s+(?:are\s+)?in\s+(?:(?:an?|one|1)\s+)?([a-z]+)", t)
    if m:
        return _do_convert(1.0, m.group(2), m.group(1))
    m = re.search(r"(?:convert\s+)?(-?\d+(?:\.\d+)?)\s*([a-z]+)\s+(?:to|in|into)\s+([a-z]+)\b", t)
    if m:
        return _do_convert(float(m.group(1)), m.group(2), m.group(3))
    return None


# ── arithmetic — a SAFE evaluator (ast, numeric only; never eval()) ──
_LEAD = re.compile(r"^\s*(?:what\s+is|what's|whats|calculate|compute|evaluate|solve|how much is|"
                   r"what\s+does|what's the value of)\s+", re.I)
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
        ast.USub: operator.neg, ast.UAdd: operator.pos}


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("non-numeric")
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("sqrt", "cbrt"):
        v = _safe_eval(node.args[0])
        return v ** 0.5 if node.func.id == "sqrt" else v ** (1.0 / 3.0)
    raise ValueError("unsupported")


def _arith(t: str) -> Optional[str]:
    body = _LEAD.sub("", t.strip().rstrip("?.! ")).strip()
    mp = re.match(r"^(?:the\s+)?(-?\d+(?:\.\d+)?)\s*(?:percent|%)\s+of\s+(-?\d+(?:\.\d+)?)$", body, re.I)
    if mp:
        return f"{mp.group(1)}% of {mp.group(2)} = {_fmt(float(mp.group(1)) / 100 * float(mp.group(2)))}"
    s = body.lower()
    # phrase → operator FIRST ("to the power of" needs its 'the'); strip leftover articles AFTER
    s = re.sub(r"square\s+root\s+of\s+(-?\d+(?:\.\d+)?)", r"sqrt(\1)", s)
    s = re.sub(r"cube\s+root\s+of\s+(-?\d+(?:\.\d+)?)", r"cbrt(\1)", s)
    s = re.sub(r"(\d)\s*squared\b", r"\1**2", s)
    s = re.sub(r"(\d)\s*cubed\b", r"\1**3", s)
    s = (s.replace("to the power of", "**").replace("multiplied by", "*").replace("times", "*")
         .replace("divided by", "/").replace("plus", "+").replace("minus", "-")
         .replace("^", "**").replace("x", "*"))
    s = re.sub(r"\s+", " ", re.sub(r"\bthe\b", " ", s)).strip()   # collapse ws — ast.parse(eval) rejects leading indent
    body = re.sub(r"\s+", " ", re.sub(r"\bthe\b", " ", body)).strip()   # clean display too
    # a numeric expression only — digits, operators, parens, dot, and the two root functions
    if not re.search(r"\d", s) or not re.fullmatch(r"[0-9+\-*/%(). sqrtcb]*", s):
        return None
    if not re.search(r"[+\-*/%]|sqrt|cbrt", s):     # must be an actual computation, not a lone number
        return None
    try:
        val = _safe_eval(ast.parse(s, mode="eval").body)
    except Exception:  # noqa: BLE001 — anything unparseable: decline, never guess
        return None
    if not isinstance(val, (int, float)) or val != val or val in (float("inf"), float("-inf")):
        return None
    return f"{body} = {_fmt(float(val))}"


def answer(text: str) -> Optional[str]:
    """A direct, exact answer to a computational question, or None to fall through to search."""
    t = (text or "").strip().rstrip("?.! ").lower()
    if not t:
        return None
    return _convert(t) or _arith(text or "")
