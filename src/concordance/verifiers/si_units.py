"""SI UNITS — a small, honest unit normalizer: parse a unit expression into a dimension vector and a factor,
convert between expressions of the same dimension, and say NOTHING when it cannot parse.

Why (R4 of docs/PROJECT_REVIEW_2026-10-03.md; Matt, 2026-10-03: "go in order"): since the Fable review a stated
unit that did not string-match the constant's own unit was DECLINED — never a false HOLDS ("299792458 km/s" had
earned one), never a false BROKEN — but the commonest phrasing of a wrong constant, "the speed of light is 150000
km/s", got no verdict at all. With a real normalizer a wrong unit MISMATCHes honestly, a formatting variant
("m s^-1", "J K^-1 mol^-1", "N m^2/kg^2") confirms, and an unknown unit still declines.

Distinct from verifiers/units.py (the CONV_VERIFY door: a claimed conversion equality over compute._UNITS). This
module is the dimensional algebra the constants verifier and the auditor's constant extractor use.

Pure, stdlib only. Dimensions are a vector over the SI base (m, kg, s, A, K, mol, cd); the factor converts the
expression to the coherent SI unit of that dimension. Temperatures with offsets (°C, °F) are not units of this
kind and are not parsed here.

    parse("km/s")            -> ({"m": 1, "s": -1}, 1000.0)
    parse("J/(mol*K)")       -> ({"kg": 1, "m": 2, "s": -2, "mol": -1, "K": -1}, 1.0)
    convert(150000, "km/s", "m/s") -> 150000000.0
    same_dimension("N m^2/kg^2", "m^3/(kg*s^2)") -> True
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

Dims = Dict[str, int]
Parsed = Tuple[Dims, float]

_BASE = ("m", "kg", "s", "A", "K", "mol", "cd")

# symbol -> (dims, factor to coherent SI). Symbols are case-sensitive; names (below) are not.
_SYMBOLS: Dict[str, Parsed] = {
    "1": ({}, 1.0), "dimensionless": ({}, 1.0),
    "m": ({"m": 1}, 1.0), "g": ({"kg": 1}, 1e-3), "s": ({"s": 1}, 1.0), "A": ({"A": 1}, 1.0),
    "K": ({"K": 1}, 1.0), "mol": ({"mol": 1}, 1.0), "cd": ({"cd": 1}, 1.0),
    "N": ({"kg": 1, "m": 1, "s": -2}, 1.0), "J": ({"kg": 1, "m": 2, "s": -2}, 1.0),
    "W": ({"kg": 1, "m": 2, "s": -3}, 1.0), "Pa": ({"kg": 1, "m": -1, "s": -2}, 1.0),
    "C": ({"A": 1, "s": 1}, 1.0), "V": ({"kg": 1, "m": 2, "s": -3, "A": -1}, 1.0),
    "F": ({"kg": -1, "m": -2, "s": 4, "A": 2}, 1.0), "Hz": ({"s": -1}, 1.0),
    "T": ({"kg": 1, "s": -2, "A": -1}, 1.0), "Wb": ({"kg": 1, "m": 2, "s": -2, "A": -1}, 1.0),
    "H": ({"kg": 1, "m": 2, "s": -2, "A": -2}, 1.0), "Ω": ({"kg": 1, "m": 2, "s": -3, "A": -2}, 1.0),
    "ohm": ({"kg": 1, "m": 2, "s": -3, "A": -2}, 1.0),
    "eV": ({"kg": 1, "m": 2, "s": -2}, 1.602176634e-19), "cal": ({"kg": 1, "m": 2, "s": -2}, 4.184),
    "min": ({"s": 1}, 60.0), "h": ({"s": 1}, 3600.0), "hr": ({"s": 1}, 3600.0), "d": ({"s": 1}, 86400.0),
    "mi": ({"m": 1}, 1609.344), "ft": ({"m": 1}, 0.3048), "in": ({"m": 1}, 0.0254), "yd": ({"m": 1}, 0.9144),
    "nmi": ({"m": 1}, 1852.0), "Å": ({"m": 1}, 1e-10), "AU": ({"m": 1}, 1.495978707e11), "ly": ({"m": 1}, 9.4607304725808e15),
    "lb": ({"kg": 1}, 0.45359237), "oz": ({"kg": 1}, 0.028349523125), "t": ({"kg": 1}, 1000.0),
    "L": ({"m": 3}, 1e-3), "l": ({"m": 3}, 1e-3), "ha": ({"m": 2}, 1e4),
    "mph": ({"m": 1, "s": -1}, 0.44704), "kph": ({"m": 1, "s": -1}, 1000.0 / 3600.0), "kn": ({"m": 1, "s": -1}, 1852.0 / 3600.0),
    "bar": ({"kg": 1, "m": -1, "s": -2}, 1e5), "atm": ({"kg": 1, "m": -1, "s": -2}, 101325.0), "psi": ({"kg": 1, "m": -1, "s": -2}, 6894.757293168),
}
# words (any case, singular or plural) -> symbol
_NAMES: Dict[str, str] = {
    "meter": "m", "metre": "m", "second": "s", "sec": "s", "gram": "g", "gramme": "g", "kilogram": "kg", "kilogramme": "kg",
    "ampere": "A", "amp": "A", "kelvin": "K", "mole": "mol", "candela": "cd", "newton": "N", "joule": "J", "watt": "W",
    "pascal": "Pa", "coulomb": "C", "volt": "V", "farad": "F", "hertz": "Hz", "tesla": "T", "weber": "Wb", "henry": "H",
    "henries": "H", "ohm": "ohm", "electronvolt": "eV", "electron-volt": "eV", "calorie": "cal", "minute": "min",
    "hour": "h", "day": "d", "mile": "mi", "foot": "ft", "feet": "ft", "inch": "in", "inches": "in", "yard": "yd",
    "angstrom": "Å", "pound": "lb", "ounce": "oz", "tonne": "t", "liter": "L", "litre": "L", "hectare": "ha",
    "kilometer": "km", "kilometre": "km", "centimeter": "cm", "centimetre": "cm", "millimeter": "mm", "millimetre": "mm",
    "micrometer": "µm", "micrometre": "µm", "nanometer": "nm", "nanometre": "nm", "millisecond": "ms", "microsecond": "µs",
    "nanosecond": "ns", "milligram": "mg", "microgram": "µg", "kilojoule": "kJ", "megajoule": "MJ", "kilowatt": "kW",
    "megawatt": "MW", "kilopascal": "kPa", "megapascal": "MPa", "millivolt": "mV", "kilovolt": "kV", "milliampere": "mA",
    "milliamp": "mA", "kilohertz": "kHz", "megahertz": "MHz", "gigahertz": "GHz", "knot": "kn",
}
_PREFIX: Dict[str, float] = {
    "Y": 1e24, "Z": 1e21, "E": 1e18, "P": 1e15, "T": 1e12, "G": 1e9, "M": 1e6, "k": 1e3, "h": 1e2, "da": 1e1,
    "d": 1e-1, "c": 1e-2, "m": 1e-3, "µ": 1e-6, "u": 1e-6, "μ": 1e-6, "n": 1e-9, "p": 1e-12, "f": 1e-15, "a": 1e-18,
    "z": 1e-21, "y": 1e-24,
}
# symbols that take an SI prefix (never the imperial / time words, never "mph")
_PREFIXABLE = {"m", "g", "s", "A", "K", "mol", "cd", "N", "J", "W", "Pa", "C", "V", "F", "Hz", "T", "Wb", "H", "Ω", "ohm", "eV", "cal", "L", "l", "t", "bar"}
_SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")
# a symbol is letters (plus the few symbol characters); the exponent may follow as ^n, ^(n), or glued n / -n
_TOKEN = re.compile(r"^([A-Za-zµμΩÅ-]+?)(?:\^?\(?(-?\d+)\)?)?$")


def _lookup(sym: str) -> Optional[Parsed]:
    if sym in _SYMBOLS:
        return _SYMBOLS[sym]
    low = sym.lower()
    if low in ("ohm", "dimensionless", "l"):
        return _SYMBOLS[low]
    name = low[:-1] if low.endswith("s") and low[:-1] in _NAMES else low
    if name in _NAMES:
        return _lookup(_NAMES[name])
    for plen in (2, 1):                                    # 'da' then single-character prefixes
        p, rest = sym[:plen], sym[plen:]
        if p in _PREFIX and rest in _PREFIXABLE and rest in _SYMBOLS:
            dims, factor = _SYMBOLS[rest]
            return (dims, factor * _PREFIX[p])
    return None


def _atom(tok: str) -> Optional[Parsed]:
    """One unit atom with an optional exponent: 'km', 'm^3', 's-2', 'mol⁻¹', 'meters', 'kg2', '1'."""
    tok = tok.strip().translate(_SUP)
    if not tok:
        return None
    if tok == "1":
        return ({}, 1.0)
    m = _TOKEN.match(tok)
    if not m:
        return None
    sym, exp = m.group(1), int(m.group(2) or 1)
    base = _lookup(sym)
    if base is None:
        return None
    dims, factor = base
    return ({k: v * exp for k, v in dims.items()}, factor ** exp)


def _mul(a: Parsed, b: Parsed, sign: int = 1) -> Parsed:
    dims = dict(a[0])
    for k, v in b[0].items():
        dims[k] = dims.get(k, 0) + sign * v
    dims = {k: v for k, v in dims.items() if v}
    return dims, a[1] * (b[1] ** sign)


def parse(expr: str) -> Optional[Parsed]:
    """A unit expression -> (dims, factor to SI), or None when any part is not a unit it knows.
    Accepts '*', '·', '×' and whitespace as products; '/' and 'per' as division (left-associative, so
    'J/K/mol' = J·K⁻¹·mol⁻¹); one level of parentheses after '/'; exponents as ^n, superscripts, or glued n."""
    s = (expr or "").strip()
    if not s:
        return None
    s = re.sub(r"\bper\b", "/", s, flags=re.I).replace("×", "*").replace("·", "*").replace("**", "^")
    parts = s.split("/")
    result: Parsed = ({}, 1.0)
    for i, part in enumerate(parts):
        part = part.strip().strip("()").strip()
        if not part:
            if i == 0:
                continue                                   # a leading '/' : '/mol' = 1/mol
            return None
        group: Parsed = ({}, 1.0)
        for tok in re.split(r"[\s*]+", part):
            if not tok:
                continue
            a = _atom(tok)
            if a is None:
                return None
            group = _mul(group, a)
        result = _mul(result, group, 1 if i == 0 else -1)
    return result


def same_dimension(a: str, b: str) -> Optional[bool]:
    pa, pb = parse(a), parse(b)
    if pa is None or pb is None:
        return None
    return pa[0] == pb[0]


def convert(value: float, from_unit: str, to_unit: str) -> Optional[float]:
    """value in from_unit expressed in to_unit, or None when either is unknown or the dimensions differ."""
    pa, pb = parse(from_unit), parse(to_unit)
    if pa is None or pb is None or pa[0] != pb[0]:
        return None
    return float(value) * pa[1] / pb[1]


def describe(dims: Dims) -> str:
    """A readable dimension, e.g. 'm·s^-1' — for a MISMATCH detail a person can check."""
    if not dims:
        return "dimensionless"
    order = lambda kv: _BASE.index(kv[0]) if kv[0] in _BASE else 99
    return "·".join(f"{k}^{v}" if v != 1 else k for k, v in sorted(dims.items(), key=order))


def longest_unit_prefix(tokens: List[str], want: str) -> Optional[Tuple[str, int]]:
    """From a run of prose tokens after a number, the longest leading run that parses as a unit of the SAME
    dimension as `want` (so 'm s^-1 in vacuum' yields 'm s^-1', not 'm s^-1 in'); else the longest run that
    parses at all (a wrong dimension is a claim to answer, not to drop); else None. Returns (expr, n_tokens)."""
    pw = parse(want)
    best_any: Optional[Tuple[str, int]] = None
    for n in range(min(4, len(tokens)), 0, -1):
        expr = " ".join(tokens[:n])
        p = parse(expr)
        if p is None:
            continue
        if pw is not None and p[0] == pw[0]:
            return expr, n
        if best_any is None:
            best_any = (expr, n)
    return best_any
