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
    # culinary / canning volume (US) — the kitchen conversions a homestead family actually asks for
    # (live 2026-08-31: "how many teaspoons in a tablespoon" fell through to a dictionary card). tsp x3 = tbsp.
    "tablespoon": ("V", 0.01478676), "tablespoons": ("V", 0.01478676), "tbsp": ("V", 0.01478676),
    "teaspoon": ("V", 0.00492892), "teaspoons": ("V", 0.00492892), "tsp": ("V", 0.00492892),
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
                   r"what\s+does|what's the value of|whats the value of|work out|figure out)\s+", re.I)
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
        ast.USub: operator.neg, ast.UAdd: operator.pos}
_N = r"-?\d+(?:\.\d+)?"


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


def _denumber(t: str) -> str:
    """Normalize the ways people write numbers so phrasing does not change the answer: thousands
    commas, a leading currency sign, and the × ÷ symbols all fold to a canonical form."""
    t = t.replace("×", " x ").replace("÷", " / ").replace("·", "*")
    t = re.sub(r"(?<=\d),(?=\d{3}(?:\D|$))", "", t)   # 1,000 -> 1000 (only true thousands groups)
    t = re.sub(r"[$£€](?=\d)", "", t)                  # $50 -> 50
    return t


def _val(s: str) -> float:
    return float(s)


def _worded(body: str) -> Optional[str]:
    """Plain-English arithmetic → ONE canonical statement, so 'add 3 and 4', '3 plus 4' and '3 + 4'
    all read '3 + 4 = 7' (and therefore seal to the same receipt). Every case is exact or declines."""
    b = re.sub(r"\s+", " ", body.strip().rstrip("?.! ")).lower()
    N = _N
    m = re.match(rf"^(?:the\s+)?({N})\s*(?:percent|%)\s+of\s+({N})$", b)
    if m:
        return f"{m[1]}% of {m[2]} = {_fmt(_val(m[1]) / 100 * _val(m[2]))}"
    m = re.match(rf"^({N})\s*(?:percent|%)\s+off(?:\s+of)?\s+({N})$", b)
    if m:
        return f"{m[1]}% off {m[2]} = {_fmt(_val(m[2]) * (1 - _val(m[1]) / 100))}"
    m = re.match(rf"^(?:increase\s+)?({N})\s+(?:increased\s+)?by\s+({N})\s*(?:percent|%)$", b)
    if m and "increas" in b:      # require the keyword — never guess "increase" from a bare "N by M%"
        return f"{m[1]} increased by {m[2]}% = {_fmt(_val(m[1]) * (1 + _val(m[2]) / 100))}"
    m = re.match(rf"^(?:decrease|reduce)\s+({N})\s+by\s+({N})\s*(?:percent|%)$", b) \
        or re.match(rf"^({N})\s+(?:decreased|reduced)\s+by\s+({N})\s*(?:percent|%)$", b)
    if m:
        return f"{m[1]} decreased by {m[2]}% = {_fmt(_val(m[1]) * (1 - _val(m[2]) / 100))}"
    for word, div in (("a half", 2), ("half", 2), ("a third", 3), ("third", 3),
                      ("a quarter", 4), ("quarter", 4)):
        m = re.match(rf"^{word}\s+of\s+({N})$", b)
        if m:
            return f"{word} of {m[1]} = {_fmt(_val(m[1]) / div)}"
    m = re.match(rf"^(?:double|twice)\s+({N})$", b)
    if m:
        return f"double {m[1]} = {_fmt(_val(m[1]) * 2)}"
    m = re.match(rf"^triple\s+({N})$", b)
    if m:
        return f"triple {m[1]} = {_fmt(_val(m[1]) * 3)}"
    m = re.match(rf"^(?:add|sum of)\s+({N})\s+(?:and|to|\+)\s+({N})$", b)
    if m:
        return f"{m[1]} + {m[2]} = {_fmt(_val(m[1]) + _val(m[2]))}"
    m = re.match(rf"^(?:the\s+)?product of\s+({N})\s+and\s+({N})$", b) \
        or re.match(rf"^multiply\s+({N})\s+by\s+({N})$", b)
    if m:
        return f"{m[1]} × {m[2]} = {_fmt(_val(m[1]) * _val(m[2]))}"
    m = re.match(rf"^(?:the\s+)?difference (?:of|between)\s+({N})\s+and\s+({N})$", b)
    if m:
        return f"{m[1]} − {m[2]} = {_fmt(_val(m[1]) - _val(m[2]))}"
    m = re.match(rf"^subtract\s+({N})\s+from\s+({N})$", b)
    if m:
        return f"{m[2]} − {m[1]} = {_fmt(_val(m[2]) - _val(m[1]))}"
    m = re.match(rf"^divide\s+({N})\s+by\s+({N})$", b)
    if m and _val(m[2]) != 0:
        return f"{m[1]} ÷ {m[2]} = {_fmt(_val(m[1]) / _val(m[2]))}"
    m = re.match(r"^(?:the\s+)?(?:average|mean)\s+of\s+(.+)$", b)
    if m:
        nums = re.findall(N, m[1])
        if len(nums) >= 2:
            vals = [_val(x) for x in nums]
            return f"average of {', '.join(nums)} = {_fmt(sum(vals) / len(vals))}"
    return None


def _pretty(expr: str) -> str:
    """Canonical arithmetic, prettified for reading: '8 * 7' → '8 × 7', 'sqrt(144)' → '√144'."""
    e = re.sub(r"\bsqrt\(([^()]*)\)", r"√\1", expr)
    e = re.sub(r"\bcbrt\(([^()]*)\)", r"∛\1", e)
    e = e.replace("**", " ^ ").replace("*", " × ").replace("/", " ÷ ").replace("%", " mod ")
    return re.sub(r"\s+", " ", e).strip()


def _arith(t: str) -> Optional[str]:
    body = _LEAD.sub("", t.strip().rstrip("?.! ")).strip()
    worded = _worded(body)                        # plain-English forms → one canonical statement
    if worded:
        return worded
    s = body.lower()
    # phrase → operator FIRST ("to the power of" needs its 'the'); strip leftover articles AFTER
    s = re.sub(r"square\s+root\s+of\s+(-?\d+(?:\.\d+)?)", r"sqrt(\1)", s)
    s = re.sub(r"cube\s+root\s+of\s+(-?\d+(?:\.\d+)?)", r"cbrt(\1)", s)
    s = re.sub(r"(\d)\s*squared\b", r"\1**2", s)
    s = re.sub(r"(\d)\s*cubed\b", r"\1**3", s)
    s = (s.replace("to the power of", "**").replace("multiplied by", "*").replace("times", "*")
         .replace("divided by", "/").replace("plus", "+").replace("minus", "-").replace("^", "**"))
    s = re.sub(r"(?<=\d)\s*x\s*(?=\d)", "*", s)     # 8x7 → 8*7, but never touch letters in words
    s = re.sub(r"\s+", " ", re.sub(r"\bthe\b", " ", s)).strip()   # collapse ws — ast.parse(eval) rejects leading indent
    # a numeric expression only — digits, operators, parens, dot, and the two root functions
    if not re.search(r"\d", s) or not re.fullmatch(r"[0-9+\-*/%(). sqrtcb]*", s):
        return None
    if not re.search(r"[+\-*/%]|sqrt|cbrt", s):     # must be an actual computation, not a lone number
        return None
    # Decline BEFORE computing an absurd exponent — "2 ** 99999999" is a valid expression but its
    # result has no exact, displayable answer (and computing/formatting it wastes CPU for nothing).
    # A bound here also protects the process: without it, a large-enough exponent raises later during
    # formatting (see below) — caught, but only after paying for the giant intermediate integer.
    if any(abs(float(e)) > 1000 for e in re.findall(r"\*\*\s*(-?\d+(?:\.\d+)?)", s)):
        return None
    try:
        tree = ast.parse(s, mode="eval")
        val = _safe_eval(tree.body)
    except Exception:  # noqa: BLE001 — anything unparseable: decline, never guess
        return None
    if not isinstance(val, (int, float)) or val != val or val in (float("inf"), float("-inf")):
        return None
    try:
        canon = ast.unparse(tree.body)             # canonical form — spacing/phrasing no longer matters
    except Exception:  # noqa: BLE001 — ast.unparse is 3.9+; fall back to the normalized expression
        canon = s
    try:
        # a result too large to represent as a float (or to format) is not an EXACT answer either —
        # decline rather than crash (OverflowError on huge ints; ValueError on Python's int-str digit
        # limit for enormous values reached through other operators, e.g. repeated multiplication).
        shown = _fmt(float(val))
    except (OverflowError, ValueError):
        return None
    return f"{_pretty(canon)} = {shown}"


def answer(text: str) -> Optional[str]:
    """A direct, exact answer to a computational question, or None to fall through to search."""
    raw = _denumber((text or "").strip())
    t = raw.rstrip("?.! ").lower()
    if not t:
        return None
    try:
        return _convert(t) or _arith(raw)
    except (OverflowError, ValueError):
        # found: _worded() ("double X", "multiply X by Y", ...), _temperature(), and _do_convert()
        # each call _fmt() straight on a caller-supplied number with no finiteness check — unlike
        # _arith()'s own ast-expression path, which already declines on inf/nan before formatting.
        # A large-enough literal (e.g. a 300+ digit number) overflows float() to inf, and _fmt()'s
        # round(x) (single-arg -> int) then raises OverflowError. Confirmed live via POST /ask
        # ("double " + "9"*320). Decline rather than crash, matching this module's own philosophy.
        return None
