"""The Auditor — find every checkable quantitative claim in a text, verify the lot, seal one report.

Paste anything (a paycheck stub, a receipt, a label, an article). Deterministic extractors —
plain regular expressions, no model anywhere — pull out the claims they can identify with
CERTAINTY, each one becomes a step in a single derivation, and the existing moat does the rest:
per-claim verdict + worked trail + one sealed receipt for the whole report.

The extraction inherits the moat's asymmetry, applied to reading: it would rather MISS a claim
than check the wrong one. Only unambiguous patterns extract; ambiguity is not extracted, never
guessed. The report names what it found — it never implies it checked the whole document.

Shapes (v1): explicit sums and products; "X% of Y is Z"; hourly pay (rate x hours = gross);
annual salary <-> hourly; compound interest (the word "compound" is REQUIRED — "at 5% for 10
years" alone is ambiguous between simple and compound, so it is skipped); rule of 72; elapsed
years between dates; day-of-week and leap-year claims; nutrition labels (the 4-9-4 kcal check).
"""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Tuple

MAX_TEXT = 20_000     # characters of input scanned (DoS bound; each claim is pool-bounded anyway)
MAX_CLAIMS = 40       # claims verified per report

_MONTHS = {"january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
           "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12}
_DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")

_NUM = r"\$?\s*(\d[\d,]*(?:\.\d+)?)"          # a money-or-plain number (commas ok, $ ok)
_EQ = r"(?:=|is|equals|comes to|totals?)"      # the claim verb


def _f(s: str) -> float:
    return float(s.replace(",", "").replace("$", "").strip())


def _q(text: str, m: re.Match) -> str:
    """The source quote for a match — the matched span, trimmed, capped."""
    return re.sub(r"\s+", " ", m.group(0)).strip()[:160]


# Each extractor: (name, fn(text) -> list[(quote, domain, spec)]). Pure and conservative.

def _x_sum(text: str):
    out = []
    for m in re.finditer(r"\$?\d[\d,]*(?:\.\d+)?(?:\s*\+\s*\$?\d[\d,]*(?:\.\d+)?)+\s*" + _EQ +
                         r"\s*" + _NUM, text, re.I):
        left = m.group(0).rsplit(m.group(1), 1)[0]   # everything left of the claimed total
        nums = [t.replace(",", "") for t in re.findall(r"\d[\d,]*(?:\.\d+)?", left)]
        if len(nums) < 2:
            continue
        expr_a = "+".join(nums)
        out.append((_q(text, m), "mathematics",
                    {"mode": "equality", "params": {"expr_a": expr_a, "expr_b": str(_f(m.group(1)))}}))
    return out


def _x_product(text: str):
    out = []
    for m in re.finditer(_NUM + r"\s*(?:x|×|\*)\s*" + _NUM + r"\s*" + _EQ + r"\s*" + _NUM,
                         text, re.I):
        a, b, c = _f(m.group(1)), _f(m.group(2)), _f(m.group(3))
        out.append((_q(text, m), "mathematics",
                    {"mode": "equality", "params": {"expr_a": f"{a}*{b}", "expr_b": str(c)}}))
    return out


_ARITH_WORDS = {"plus": "+", "minus": "-", "times": "*", "multiplied by": "*", "divided by": "/"}


def _x_arith_words(text: str):
    """"A plus/minus/times/divided by B is C" — arithmetic stated in WORDS (the symbol forms are
    _x_sum / _x_product). Unambiguous: two numbers joined by a NAMED operator, with the claim verb
    directly on the result. Because the operator must sit between two numbers and the verb must follow
    the second number immediately, prose like "2 plus a few more, is 4 enough?" cannot match — the
    same zero-false-positive discipline as every other extractor."""
    out = []
    for m in re.finditer(_NUM + r"\s*(plus|minus|times|multiplied by|divided by)\s*" + _NUM +
                         r"\s*" + _EQ + r"\s*" + _NUM, text, re.I):
        op = _ARITH_WORDS[m.group(2).lower()]
        out.append((_q(text, m), "mathematics",
                    {"mode": "equality", "params": {"expr_a": f"{_f(m.group(1))}{op}{_f(m.group(3))}",
                                                    "expr_b": str(_f(m.group(4)))}}))
    return out


def _x_each(text: str):
    """"N units at $X each = $Y" — quantity times unit price. Unambiguous: the words name the
    relationship (a count, a per-item price, a claimed total). A descriptor of up to a few words may
    sit between the count and "at"; the price MUST carry a per-item marker (each / apiece / per
    unit), so "50 brackets at $12.40 = $620" without "each" is left to the reader, not guessed."""
    out = []
    for m in re.finditer(
            r"(\d[\d,]*(?:\.\d+)?)\s+[a-z][a-z\- ]{0,24}?\s+at\s+\$?\s*(\d[\d,]*(?:\.\d+)?)"
            r"\s*(?:each|apiece|a piece|/ea\b|per (?:unit|piece|part|item|ea))\b"
            r"[^.\n]{0,20}?" + _EQ + r"\s*" + _NUM, text, re.I):
        qty, unit, total = _f(m.group(1)), _f(m.group(2)), _f(m.group(3))
        out.append((_q(text, m), "mathematics",
                    {"mode": "equality", "params": {"expr_a": f"{qty}*{unit}", "expr_b": str(total)}}))
    return out


def _x_percent(text: str):
    out = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:%|percent|pct)\s*(?:of|tip on|tax on|discount on|off(?: of)?|on)\s*"
                         + _NUM + r"\s*" + _EQ + r"\s*" + _NUM, text, re.I):
        pct, base, claimed = _f(m.group(1)), _f(m.group(2)), _f(m.group(3))
        out.append((_q(text, m), "mathematics",
                    {"mode": "equality", "params": {"expr_a": f"({pct}/100)*{base}",
                                                    "expr_b": str(claimed)}}))
    return out


def _x_gross_pay(text: str):
    out = []
    # A single descriptor word may sit between the count and "hours" — a real quote says
    # "22 machine hours at $95/hr = $2,090", not "22 hours ...". One optional word only, to stay
    # unambiguous (it cannot swallow another number or cross a claim).
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:[a-z]+\s+)?hours?\s*(?:at|@)\s*\$\s*(\d+(?:\.\d+)?)"
                         r"\s*(?:/hr|/hour|per hour|an hour|hourly)?\s*" + _EQ + r"\s*" + _NUM,
                         text, re.I):
        out.append((_q(text, m), "labor",
                    {"LABOR_VERIFY": {"hours_worked": _f(m.group(1)), "hourly_rate": _f(m.group(2)),
                                      "claimed_gross_pay": _f(m.group(3))}}))
    return out


def _x_annual_hourly(text: str):
    out = []
    for m in re.finditer(_NUM + r"\s*(?:a year|per year|/year|annually|annual(?: salary)?)"
                         r"[^.\n]{0,40}?" + _EQ + r"\s*" + _NUM +
                         r"\s*(?:/hr|/hour|per hour|an hour|hourly)", text, re.I):
        out.append((_q(text, m), "labor",
                    {"LABOR_VERIFY": {"annual_salary": _f(m.group(1)),
                                      "claimed_hourly_equivalent": _f(m.group(2))}}))
    return out


def _x_compound(text: str):
    """The word 'compound' is REQUIRED in the matched span — 'at 5% for 10 years' alone is
    ambiguous between simple and compound interest, so it is honestly skipped."""
    out = []
    for m in re.finditer(_NUM + r"[^.\n]{0,30}?\bat\s*(\d+(?:\.\d+)?)\s*%[^.\n]{0,40}?"
                         r"\bcompound\w*\b[^.\n]{0,40}?(\d+(?:\.\d+)?)\s*years?"
                         r"[^.\n]{0,30}?(?:=|is|grows to|becomes|yields|worth)\s*" + _NUM,
                         text, re.I):
        out.append((_q(text, m), "finance",
                    {"FIN_VERIFY": {"principal": _f(m.group(1)), "rate": _f(m.group(2)) / 100.0,
                                    "years": _f(m.group(3)), "claimed_future_value": _f(m.group(4))}}))
    # the other common ordering: "... for N years compounded ... = X"
    for m in re.finditer(_NUM + r"[^.\n]{0,30}?\bat\s*(\d+(?:\.\d+)?)\s*%[^.\n]{0,30}?"
                         r"for\s*(\d+(?:\.\d+)?)\s*years?[^.\n]{0,30}?\bcompound\w*\b"
                         r"[^.\n]{0,30}?(?:=|is|grows to|becomes|yields|worth)\s*" + _NUM,
                         text, re.I):
        out.append((_q(text, m), "finance",
                    {"FIN_VERIFY": {"principal": _f(m.group(1)), "rate": _f(m.group(2)) / 100.0,
                                    "years": _f(m.group(3)), "claimed_future_value": _f(m.group(4))}}))
    return out


def _x_rule72(text: str):
    out = []
    for m in re.finditer(r"(?:at\s*)?(\d+(?:\.\d+)?)\s*%[^.\n]{0,50}?doubl\w+[^.\n]{0,30}?"
                         r"(\d+(?:\.\d+)?)\s*years?", text, re.I):
        out.append((_q(text, m), "economics",
                    {"ECON_VERIFY": {"rate_percent": _f(m.group(1)),
                                     "claimed_doubling_years": _f(m.group(2))}}))
    return out


def _x_elapsed_years(text: str):
    out = []
    #  "... 4 years ... (1914-1918)" — the claim adjacent to a parenthesised range
    for m in re.finditer(r"(\d{1,4})\s*years?[^.\n]{0,40}?\((\d{3,4})\s*(?:-|–|—|to)\s*(\d{3,4})\)",
                         text, re.I):
        out.append((_q(text, m), "history_chronology",
                    {"HIST_VERIFY": {"from_year": int(m.group(2)), "to_year": int(m.group(3)),
                                     "claimed_elapsed_years": int(m.group(1))}}))
    #  "between 1500 and 2000 ... 500 years"  /  "from 1500 to 2000 is 500 years"
    for m in re.finditer(r"(?:between|from)\s*(\d{3,4})\s*(?:and|to)\s*(\d{3,4})"
                         r"[^.\n]{0,40}?(\d{1,4})\s*years?", text, re.I):
        out.append((_q(text, m), "history_chronology",
                    {"HIST_VERIFY": {"from_year": int(m.group(1)), "to_year": int(m.group(2)),
                                     "claimed_elapsed_years": int(m.group(3))}}))
    return out


def _x_day_of_week(text: str):
    out = []
    month_alt = "|".join(m.capitalize() for m in _MONTHS)
    day_alt = "|".join(d.capitalize() for d in _DAYS)
    for m in re.finditer(rf"\b({month_alt})\s+(\d{{1,2}}),?\s*(\d{{3,4}})\s*"
                         rf"(?:was|is|falls?(?: on)?|fell on)\s*(?:a|an)?\s*({day_alt})\b",
                         text, re.I):
        mo = _MONTHS[m.group(1).lower()]
        iso = f"{int(m.group(3)):04d}-{mo:02d}-{int(m.group(2)):02d}"
        out.append((_q(text, m), "calendar_time",
                    {"CAL_VERIFY": {"date_iso": iso, "claimed_day_of_week": m.group(4).lower()}}))
    return out


def _x_leap_year(text: str):
    out = []
    for m in re.finditer(r"\b(\d{3,4})\s*(?:was|is|will be)\s*(not\s+)?a\s+leap\s+year", text, re.I):
        out.append((_q(text, m), "calendar_time",
                    {"CAL_VERIFY": {"year": int(m.group(1)), "claimed_leap": not m.group(2)}}))
    return out


def _x_nutrition(text: str):
    """A label: calories + all three macros within one tight window (~250 chars). All four
    or nothing — partial labels are ambiguous and skipped."""
    out = []
    for m in re.finditer(r"calories[:\s]*(\d+)", text, re.I):
        window = text[m.start():m.start() + 250]
        fat = re.search(r"(?:total\s*)?fat[:\s]*(\d+(?:\.\d+)?)\s*g", window, re.I)
        carb = re.search(r"(?:total\s*)?carb(?:ohydrate)?s?[:\s]*(\d+(?:\.\d+)?)\s*g", window, re.I)
        prot = re.search(r"protein[:\s]*(\d+(?:\.\d+)?)\s*g", window, re.I)
        if not (fat and carb and prot):
            continue
        quote = re.sub(r"\s+", " ", window[:max(fat.end(), carb.end(), prot.end())]).strip()[:160]
        out.append((quote, "nutrition",
                    {"NUT_VERIFY": {"calories_claimed": int(m.group(1)), "fat_g": _f(fat.group(1)),
                                    "carb_g": _f(carb.group(1)), "protein_g": _f(prot.group(1))}}))
    return out


# A named fundamental physical constant asserted to a value — "the speed of light is 299792458 m/s".
# This is a COMPUTABLE claim (the wedge's differentiator: AI models emit constants often), so it earns
# a verdict + receipt, not just a find. The name alternation is built ONCE from the verifier's own
# CODATA table + its curated aliases — so the extractor can only name a constant the verifier actually
# knows, and stays in lock-step with it. Conservative, per the auditor's asymmetry:
#   * a bare symbol ("c", "e", "g", "alpha") is NOT matched — far too ambiguous in prose; only the
#     full constant names, multi-word alias phrases, and a few unmistakable proper names (planck,
#     boltzmann, avogadro, faraday) are candidates. The required numeric value guards the rest.
#   * the unit is passed to the verifier ONLY when it normalize-MATCHES the constant's own unit — i.e.
#     only when it will CONFIRM. A true claim can then never be falsely BROKEN over unit formatting
#     ("8.314 J/K/mol" for the gas constant is correct, but its stored form differs, so we check the
#     value alone rather than break it); any other unit is dropped and only the value is checked. The
#     residual — the exact numeric value stated under a wrong unit label — is left to the structured
#     door, which checks units deliberately. Scientific "e" notation is read; "x 10^n" is left to miss.
_PC_SAFE_SINGLE = frozenset({"planck", "boltzmann", "avogadro", "faraday"})
_PC_PAT: Optional[re.Pattern] = None


def _pc_pattern() -> re.Pattern:
    global _PC_PAT
    if _PC_PAT is None:
        from .verifiers import physical_constants as _pc
        names = {k.replace("_", " ") for k in _pc._CONSTANTS}
        for k in _pc._ALIASES:
            phrase = k.replace("_", " ")
            if " " in phrase or phrase in _PC_SAFE_SINGLE:
                names.add(phrase)
        alt = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
        _PC_PAT = re.compile(
            r"\b(?:the\s+)?(" + alt + r")\s+" + _EQ +
            r"\s*(?:about|approximately|roughly|around|~|≈)?\s*"
            r"(\d[\d,]*(?:\.\d+)?(?:\s*[eE]\s*[-+]?\d+)?)"
            r"\s*([^\s.,;:!?]{1,14})?", re.I)
    return _PC_PAT


def _x_physical_constant(text: str):
    from .verifiers import physical_constants as _pc
    out = []
    for m in _pc_pattern().finditer(text):
        canon = _pc._canonical(m.group(1))
        if canon not in _pc._CONSTANTS:            # the name must resolve to a constant it truly knows
            continue
        try:
            value = float(m.group(2).replace(",", "").replace(" ", ""))
        except ValueError:
            continue
        cv: Dict[str, Any] = {"constant": canon, "claimed_value": value}
        unit = (m.group(3) or "").strip()
        if unit:                                    # pass the unit ONLY when it will confirm (see above)
            stored = _pc._CONSTANTS[canon]["unit"]
            if unit.lower() == stored.lower() or _pc._normalize_unit(unit) == _pc._normalize_unit(stored):
                cv["claimed_unit"] = unit
        out.append((_q(text, m), "physical_constants", {"CONST_VERIFY": cv}))
    return out


# A claimed unit conversion — "1 mile is 1.609 kilometers", "500 mg is 0.5 grams", "100 degrees
# fahrenheit is 37.78 celsius". A COMPUTABLE claim (conversions are the most common computable claim
# in AI output), so it earns a verdict + receipt. The unit vocabulary is the verifier's own table
# (compute._UNITS + _TEMP), so the extractor and verifier can never drift. Conservative: BOTH sides
# must carry a known unit AND share a dimension (or both be temperatures) — a cross-dimension pair is
# NOT extracted (units like "ounce" are ambiguous mass-vs-fluid; we decline rather than risk a false
# BROKEN), and a bare "5 apples = 5 fruit" never matches (not units). The second value must be present,
# so "convert 1 mile to km" (a question, no claimed answer) is left to the compute door.
_UC_PAT: Optional[re.Pattern] = None


def _uc_pattern() -> re.Pattern:
    global _UC_PAT
    if _UC_PAT is None:
        from .compute import _UNITS, _TEMP
        units = sorted(set(_UNITS) | set(_TEMP), key=len, reverse=True)
        alt = "|".join(re.escape(u) for u in units)
        n = r"(-?\d[\d,]*(?:\.\d+)?)"
        _UC_PAT = re.compile(
            n + r"\s*(?:degrees?\s+)?(" + alt + r")\b\s+" + _EQ +
            r"\s*(?:about|approximately|roughly|around|~|≈)?\s*" +
            n + r"\s*(?:degrees?\s+)?(" + alt + r")\b", re.I)
    return _UC_PAT


def _x_unit_conversion(text: str):
    from .compute import _UNITS, _TEMP
    out = []
    for m in _uc_pattern().finditer(text):
        u1, u2 = m.group(2).lower(), m.group(4).lower()
        both_temp = u1 in _TEMP and u2 in _TEMP
        same_dim = (u1 in _UNITS and u2 in _UNITS and _UNITS[u1][0] == _UNITS[u2][0])
        if not (both_temp or same_dim):        # cross-dimension / mixed / unknown — not extracted
            continue
        out.append((_q(text, m), "unit_conversion",
                    {"CONV_VERIFY": {"from_value": _f(m.group(1)), "from_unit": u1,
                                     "to_value": _f(m.group(3)), "to_unit": u2}}))
    return out


_UF_PAT: Optional[re.Pattern] = None


def _uf_pattern() -> re.Pattern:
    """there are N unit1 in a unit2 — cached like _uc_pattern."""
    global _UF_PAT
    if _UF_PAT is None:
        from .compute import _UNITS, _TEMP
        alt = "|".join(re.escape(u) for u in sorted(set(_UNITS) | set(_TEMP), key=len, reverse=True))
        _UF_PAT = re.compile(r"there\s+(?:are|is)\s+(-?\d[\d,]*(?:\.\d+)?)\s*(" + alt +
                             r")\b\s+in\s+(?:a|an|one|1)\s+(" + alt + r")\b", re.I)
    return _UF_PAT


def _x_unit_fact(text: str):
    """"there are N unit1 in a unit2" — a unit-equivalence FACT ("there are 5280 feet in a mile",
    "there are 12 inches in a foot"). The "there are/is" marker makes it unambiguously a count claim
    (unlike "5 minutes in an hour" = within), so it verifies as N unit1 == 1 unit2 against the same
    factor table (with tolerance). Same-dimension only; cross-dimension / unknown units extract
    nothing. A FALSE fact ("there are 5000 feet in a mile") breaks honestly."""
    from .compute import _UNITS
    out = []
    for m in _uf_pattern().finditer(text):
        u1, u2 = m.group(2).lower(), m.group(3).lower()
        if not (u1 in _UNITS and u2 in _UNITS and _UNITS[u1][0] == _UNITS[u2][0]):
            continue
        out.append((_q(text, m), "unit_conversion",
                    {"CONV_VERIFY": {"from_value": _f(m.group(1)), "from_unit": u1,
                                     "to_value": 1.0, "to_unit": u2}}))
    return out


def _x_power(text: str):
    """"A to the power of B is C" and "A^B = C" — exponentiation with an INTEGER exponent, so the
    result is exact (the equality verifier is exact-symbolic). A DECIMAL exponent (a root) is skipped
    because its result is usually an approximation that would break honestly-but-harshly. The exponent
    is capped at 1000 so a claim can never become an expression bomb."""
    out = []

    def add(a, b, c, m):
        try:
            e = int(b.replace(",", ""))
        except ValueError:
            return
        if e > 1000:            # a miss stays a miss — don't emit an astronomically large expression
            return
        out.append((_q(text, m), "mathematics",
                    {"mode": "equality", "params": {"expr_a": f"{_f(a)}**{e}", "expr_b": str(_f(c))}}))
    for m in re.finditer(_NUM + r"\s*to\s+the\s+power\s+of\s+(\d[\d,]*)\s*" + _EQ + r"\s*" + _NUM, text, re.I):
        add(m.group(1), m.group(2), m.group(3), m)
    for m in re.finditer(_NUM + r"\s*\^\s*(\d[\d,]*)\s*" + _EQ + r"\s*" + _NUM, text, re.I):
        add(m.group(1), m.group(2), m.group(3), m)
    return out


def _x_factorial(text: str):
    """"N factorial is M" / "N! is M" — factorial, exact. Capped at 200 so it cannot become an
    expression bomb; a bare "5!" without the claim verb and a number extracts nothing."""
    out = []
    for m in re.finditer(r"(\d[\d,]*)\s*(?:!|\bfactorial\b)\s*" + _EQ + r"\s*" + _NUM, text, re.I):
        try:
            n = int(m.group(1).replace(",", ""))
        except ValueError:
            continue
        if n > 200:
            continue
        out.append((_q(text, m), "mathematics",
                    {"mode": "equality", "params": {"expr_a": f"factorial({n})", "expr_b": str(_f(m.group(2)))}}))
    return out


def _x_sqrt(text: str):
    """"the square root of N is M" — ONLY when N is a PERFECT SQUARE, so the result is exact and the
    exact-symbolic equality verifier is the right tool. sqrt of a non-perfect-square is an irrational
    approximation that would break harshly, so it is skipped (a miss stays a miss)."""
    import math
    out = []
    for m in re.finditer(r"(?:the\s+)?square\s+root\s+of\s+" + _NUM + r"\s*" + _EQ + r"\s*" + _NUM, text, re.I):
        n = _f(m.group(1))
        if n < 0 or n != int(n):
            continue
        root = math.isqrt(int(n))
        if root * root != int(n):            # not a perfect square -> skip
            continue
        out.append((_q(text, m), "mathematics",
                    {"mode": "equality", "params": {"expr_a": f"sqrt({int(n)})", "expr_b": str(_f(m.group(2)))}}))
    return out


def _x_circle(text: str):
    """"a circle of radius R has area A" / "... has circumference C" — routes to the geometry verifier
    (area = pi r^2, circumference = 2 pi r; tolerance 1e-3, so a user-rounded value like 28.27 for
    pi*3^2 holds). Radius phrasing only (diameter is left to the reader). A wrong value breaks honestly
    with the true one shown."""
    out = []
    rad = r"circle\s+(?:of|with)\s+(?:an?\s+)?radius\s+(?:of\s+)?" + _NUM + r"\s+has\s+(?:an?\s+)?"
    approx = r"(?:about|approximately|roughly|around|~|≈)?\s*"
    for m in re.finditer(rad + r"area\s+(?:of\s+)?" + approx + _NUM, text, re.I):
        out.append((_q(text, m), "geometry",
                    {"GEOM_VERIFY": {"circle_radius": _f(m.group(1)), "claimed_circle_area": _f(m.group(2))}}))
    for m in re.finditer(rad + r"circumference\s+(?:of\s+)?" + approx + _NUM, text, re.I):
        out.append((_q(text, m), "geometry",
                    {"GEOM_VERIFY": {"circle_radius": _f(m.group(1)), "claimed_circle_circumference": _f(m.group(2))}}))
    return out


def _x_physics_force(text: str):
    """"M kg at A m/s^2 exerts F N" — Newton's second law, F = m*a, routed to the physics verifier.
    The three units (kg, m/s^2, N) anchor it, so it is unambiguous; a wrong force breaks honestly."""
    n = r"(\d[\d,]*(?:\.\d+)?)"
    pat = (n + r"\s*kg\b[^.\n]{0,25}?\bat\s+" + n +
           r"\s*(?:m/s\^?2|m/s²|m/s/s|meters?\s+per\s+second\s+squared)\b[^.\n]{0,25}?"
           r"(?:exerts?|is|=|equals|produces?|gives?|has)\s*(?:a\s+)?(?:force\s+of\s+)?" + n +
           r"\s*(?:N|newtons?)\b")
    out = []
    for m in re.finditer(pat, text, re.I):
        out.append((_q(text, m), "physics",
                    {"PHYS_VERIFY": {"mass_kg": _f(m.group(1)), "acceleration_m_per_s2": _f(m.group(2)),
                                     "claimed_force_N": _f(m.group(3))}}))
    return out


def _x_molar_mass(text: str):
    """"the molar mass of H2O is 18.015 g/mol" — FORMULA notation only (a simple element+count formula
    sitting immediately before the claim verb), routed to the periodic_table molar-mass verifier. A
    plain word ("water"), a parenthesised formula (Ca(OH)2), or a lowercase token is NOT extracted —
    case is significant (Co vs CO) and a miss stays a miss. The formula group is case-sensitive
    (?-i:) even though the surrounding words are not."""
    out = []
    for m in re.finditer(r"molar\s+mass\s+of\s+(?-i:([A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*)*))\s+"
                         + _EQ + r"\s*" + _NUM + r"\s*(?:g\s*/\s*mol|grams?\s+per\s+mole?)?", text, re.I):
        out.append((_q(text, m), "periodic_table",
                    {"PT_VERIFY": {"formula": m.group(1), "claimed_molar_mass": _f(m.group(2))}}))
    return out


def _x_pythagorean(text: str):
    """"a right triangle with legs A and B has hypotenuse C" — routes to geometry.pythagorean
    (a² + b² = c²). Legs-and-hypotenuse phrasing only, so it is unambiguous; a false hypotenuse
    breaks honestly with the true right-triangle relation shown."""
    n = r"(\d[\d,]*(?:\.\d+)?)"
    pat = (r"right\s+triangle\s+with\s+legs?\s+(?:of\s+)?" + n + r"\s+and\s+" + n +
           r"\s+(?:has|is|=|with)\s+(?:an?\s+)?hypotenuse\s+(?:of\s+)?" + n)
    out = []
    for m in re.finditer(pat, text, re.I):
        out.append((_q(text, m), "geometry",
                    {"GEOM_VERIFY": {"pyth_a": _f(m.group(1)), "pyth_b": _f(m.group(2)),
                                     "pyth_c": _f(m.group(3)), "claimed_right_triangle": True}}))
    return out


_POLY = {"triangle": 3, "quadrilateral": 4, "pentagon": 5, "hexagon": 6, "heptagon": 7,
         "octagon": 8, "nonagon": 9, "decagon": 10, "hendecagon": 11, "dodecagon": 12}


def _x_polygon_angles(text: str):
    """"a hexagon's interior angles sum to 720 degrees" — routes to geometry (interior-angle sum
    (n-2)·180). Named polygons only; a false total breaks honestly."""
    names = "|".join(_POLY)
    pat = (r"\b(" + names + r")\b[^.\n]{0,40}?interior\s+angles?\b[^.\n]{0,20}?"
           r"(?:sum[a-z]*(?:\s+to)?|add\s+up\s+to|is|are|=|equals?|total[a-z]*)\s*" +
           r"(\d[\d,]*(?:\.\d+)?)\s*(?:°|degrees?|deg)\b")
    out = []
    for m in re.finditer(pat, text, re.I):
        out.append((_q(text, m), "geometry",
                    {"GEOM_VERIFY": {"polygon_n": _POLY[m.group(1).lower()],
                                     "claimed_interior_angle_sum_deg": _f(m.group(2))}}))
    return out


def _x_kinetic_energy(text: str):
    """"a M kg object at V m/s has kinetic energy E J" — routes to physics.kinetic_energy (½mv²).
    Anchored by kg, m/s and joules, so it is unambiguous; a wrong value breaks honestly."""
    n = r"(\d[\d,]*(?:\.\d+)?)"
    pat = (n + r"\s*kg\b[^.\n]{0,30}?\bat\s+" + n + r"\s*(?:m/s|meters?\s+per\s+second)\b[^.\n]{0,30}?"
           r"kinetic\s+energy\s+(?:of\s+|is\s+|=\s*|equals?\s+)?(?:about\s+|approximately\s+|~|≈)?" + n +
           r"\s*(?:J\b|joules?\b)")
    out = []
    for m in re.finditer(pat, text, re.I):
        out.append((_q(text, m), "physics",
                    {"PHYS_VERIFY": {"mass_kg": _f(m.group(1)), "velocity_m_per_s": _f(m.group(2)),
                                     "claimed_kinetic_energy_J": _f(m.group(3))}}))
    return out


def _x_rectangle(text: str):
    """"a rectangle 4 by 6 has area 24" / "... has perimeter 20" — routes to geometry.rectangle
    (A = l·w, P = 2·(l+w); a square is the l=w case). Two dimensions right after the word "rectangle",
    joined by by/×/x, so it is unambiguous; a wrong area or perimeter breaks honestly with the true
    value shown. No dimensions, or no area/perimeter claim, means nothing is extracted (a miss stays
    a miss)."""
    n = r"(\d[\d,]*(?:\.\d+)?)"
    approx = r"(?:about|approximately|roughly|around|~|≈)?\s*"
    dims = (r"rectangle\s+(?:(?:that\s+is|measuring|of|with\s+(?:sides?|dimensions?)\s+of?)\s*)?" +
            n + r"\s*(?:by|×|x)\s*" + n + r"[^.\n]{0,25}?\b(?:has|is|=|with)\s+(?:an?\s+)?")
    out = []
    for m in re.finditer(dims + r"area\s+(?:of\s+)?" + approx + n, text, re.I):
        out.append((_q(text, m), "geometry",
                    {"GEOM_VERIFY": {"rect_length": _f(m.group(1)), "rect_width": _f(m.group(2)),
                                     "claimed_rect_area": _f(m.group(3))}}))
    for m in re.finditer(dims + r"perimeter\s+(?:of\s+)?" + approx + n, text, re.I):
        out.append((_q(text, m), "geometry",
                    {"GEOM_VERIFY": {"rect_length": _f(m.group(1)), "rect_width": _f(m.group(2)),
                                     "claimed_rect_perimeter": _f(m.group(3))}}))
    return out


def _x_kinematics(text: str):
    """"starting at 5 m/s, accelerating at 2 m/s² for 3 s, it travels 24 m" — routes to
    physics.kinematic_motion (d = v0·t + ½·a·t²). Anchored by four SI units (m/s, m/s², s, m) in
    order, so it is unambiguous; a wrong displacement breaks honestly with the true value shown. A
    bare velocity or acceleration with no full v0-a-t-distance chain extracts nothing."""
    n = r"(\d[\d,]*(?:\.\d+)?)"
    approx = r"(?:about|approximately|roughly|around|~|≈)?\s*"
    mps = r"(?:m/s|meters?\s+per\s+second|metres?\s+per\s+second)"
    mps2 = (r"(?:m/s\^?2|m/s²|m/s/s|meters?\s+per\s+second\s+squared|"
            r"metres?\s+per\s+second\s+squared)")
    pat = (r"start(?:ing|s|ed)?\s+(?:from|at)\s+" + n + r"\s*" + mps +
           r"[^.\n]{0,30}?accelerat\w*\s+(?:at\s+)?" + n + r"\s*" + mps2 +
           r"[^.\n]{0,30}?\bfor\s+" + n + r"\s*(?:s\b|sec\b|seconds?\b)" +
           r"[^.\n]{0,35}?(?:travels?|covers?|moves?|displac\w*|goes?)\s+"
           r"(?:a\s+distance\s+of\s+|through\s+|of\s+)?" + approx + n + r"\s*(?:m\b|meters?\b|metres?\b)")
    out = []
    for m in re.finditer(pat, text, re.I):
        out.append((_q(text, m), "physics",
                    {"PHYS_VERIFY": {"v0": _f(m.group(1)), "a": _f(m.group(2)), "t": _f(m.group(3)),
                                     "claimed_displacement": _f(m.group(4))}}))
    return out


_TRI_D = r"(\d+(?:\.\d+)?)"
_TRI_L = _TRI_D + r"\s*,\s*" + _TRI_D + r"\s*,?\s+and\s+" + _TRI_D


def _x_triangle_inequality(text: str):
    """"sides 3, 4, and 5 form a valid triangle" (True) / "sides 1, 2, and 10 cannot form a triangle"
    (False) — routes to geometry.triangle_inequality (a triangle iff each pair of sides sums to more
    than the third). A BOOLEAN claim, so both polarities are read explicitly: only valid/forms phrasing
    is True, only cannot/do-not/invalid phrasing is False. A bare "sides 3, 4, and 5" or a "triangle"
    with no verdict extracts nothing — a miss stays a miss. A stated validity that is wrong for those
    side lengths breaks honestly. The three sides must be a clean comma list ending in "and"."""
    L = _TRI_L
    out = []
    true_pats = (
        r"triangle\s+with\s+sides?\s+(?:of\s+)?" + L + r"\s+(?:is|are)\s+valid\b",
        r"sides?\s+(?:of\s+)?" + L + r"\s+(?:forms?|makes?)\s+(?:a\s+)?(?:valid\s+)?triangle\b",
    )
    false_pats = (
        r"triangle\s+with\s+sides?\s+(?:of\s+)?" + L + r"\s+is\s+(?:not\s+valid|invalid)\b",
        r"sides?\s+(?:of\s+)?" + L +
        r"\s+(?:cannot|can\s?not|can't|could\s+not|couldn't|do\s+not|don't|does\s+not|doesn't|"
        r"will\s+not|won't)\s+(?:form|make)\s+(?:a\s+)?(?:valid\s+)?triangle\b",
    )
    for claimed, pats in ((True, true_pats), (False, false_pats)):
        for pat in pats:
            for m in re.finditer(pat, text, re.I):
                out.append((_q(text, m), "geometry",
                            {"GEOM_VERIFY": {"tri_a": _f(m.group(1)), "tri_b": _f(m.group(2)),
                                             "tri_c": _f(m.group(3)),
                                             "claimed_valid_triangle": claimed}}))
    return out


def _x_sphere(text: str):
    """"a sphere of radius 3 has volume 113.1" / "... has surface area 314.16" — routes to
    geometry.sphere (V = 4/3·πr³, A = 4πr²; rel tol 1e-4, so ordinary rounding holds). Radius phrasing
    only; a wrong value breaks honestly with the true one shown."""
    n = r"(\d[\d,]*(?:\.\d+)?)"
    approx = r"(?:about|approximately|roughly|around|~|≈)?\s*"
    rad = r"sphere\s+(?:of|with)\s+(?:an?\s+)?radius\s+(?:of\s+)?" + n + r"\s+has\s+(?:an?\s+)?"
    out = []
    for m in re.finditer(rad + r"volume\s+(?:of\s+)?" + approx + n, text, re.I):
        out.append((_q(text, m), "geometry",
                    {"GEOM_VERIFY": {"sphere_radius": _f(m.group(1)),
                                     "claimed_sphere_volume": _f(m.group(2))}}))
    for m in re.finditer(rad + r"surface\s+area\s+(?:of\s+)?" + approx + n, text, re.I):
        out.append((_q(text, m), "geometry",
                    {"GEOM_VERIFY": {"sphere_radius": _f(m.group(1)),
                                     "claimed_sphere_surface_area": _f(m.group(2))}}))
    return out


def _x_cube(text: str):
    """"a cube with side 3 has volume 27" / "... has surface area 54" — routes to geometry.cube
    (V = s³, A = 6s²). Side/edge phrasing only, so the cube ROOT of a number ("the cube root of 27 is
    3") is never mistaken for it; a wrong value breaks honestly."""
    n = r"(\d[\d,]*(?:\.\d+)?)"
    approx = r"(?:about|approximately|roughly|around|~|≈)?\s*"
    side = (r"cube\s+(?:of|with)\s+(?:an?\s+)?(?:side|edge)\s+(?:lengths?\s+)?(?:of\s+)?" + n +
            r"\s+has\s+(?:an?\s+)?")
    out = []
    for m in re.finditer(side + r"volume\s+(?:of\s+)?" + approx + n, text, re.I):
        out.append((_q(text, m), "geometry",
                    {"GEOM_VERIFY": {"cube_side": _f(m.group(1)),
                                     "claimed_cube_volume": _f(m.group(2))}}))
    for m in re.finditer(side + r"surface\s+area\s+(?:of\s+)?" + approx + n, text, re.I):
        out.append((_q(text, m), "geometry",
                    {"GEOM_VERIFY": {"cube_side": _f(m.group(1)),
                                     "claimed_cube_surface_area": _f(m.group(2))}}))
    return out


def _x_cylinder(text: str):
    """"a cylinder of radius 3 and height 5 has volume 141.37" — routes to geometry.cylinder
    (V = πr²h; rel tol 1e-4). Radius-and-height phrasing only, so it is unambiguous; a wrong volume
    breaks honestly."""
    n = r"(\d[\d,]*(?:\.\d+)?)"
    approx = r"(?:about|approximately|roughly|around|~|≈)?\s*"
    dims = (r"cylinder\s+(?:of|with)\s+(?:an?\s+)?radius\s+(?:of\s+)?" + n +
            r"\s+and\s+(?:an?\s+)?height\s+(?:of\s+)?" + n + r"\s+has\s+(?:an?\s+)?"
            r"volume\s+(?:of\s+)?" + approx + n)
    out = []
    for m in re.finditer(dims, text, re.I):
        out.append((_q(text, m), "geometry",
                    {"GEOM_VERIFY": {"cyl_radius": _f(m.group(1)), "cyl_height": _f(m.group(2)),
                                     "claimed_cyl_volume": _f(m.group(3))}}))
    return out


def _x_combinations(text: str):
    """"5 choose 2 is 10" / "C(5,2) = 10" / "combinations of 5 things taken 2 at a time is 10" — routes
    to combinatorics.combinations (C(n,k) = n!/(k!·(n-k)!)). Strongly anchored (the word "choose", the
    C(n,k) notation, or the full "combinations of … taken … at a time" phrase); a wrong count breaks
    honestly. Whole numbers only, so "choose between 2 and 5" is never mistaken for it."""
    d = r"(\d+)"
    eq = r"\s*(?:is|=|equals?)\s*"
    pats = (
        d + r"\s+choose\s+" + d + eq + d,
        r"\bC\s*\(\s*" + d + r"\s*,\s*" + d + r"\s*\)" + eq + d,
        r"(?:number\s+of\s+)?combinations?\s+of\s+" + d +
        r"\s+(?:things?|items?|objects?|elements?)\s+taken\s+" + d + r"\s+at\s+a\s+time" + eq + d,
    )
    out = []
    for pat in pats:
        for m in re.finditer(pat, text, re.I):
            out.append((_q(text, m), "combinatorics",
                        {"COMB_VERIFY": {"comb_n": int(m.group(1)), "comb_k": int(m.group(2)),
                                         "claimed_combinations": int(m.group(3))}}))
    return out


def _x_permutations(text: str):
    """"P(5,2) = 20" / "5 permute 2 is 20" / "permutations of 5 things taken 2 at a time is 20" — routes
    to combinatorics.permutations (P(n,k) = n!/(n-k)!). Notation/verb anchored; a wrong count breaks
    honestly. Whole numbers only."""
    d = r"(\d+)"
    eq = r"\s*(?:is|=|equals?)\s*"
    pats = (
        r"\bP\s*\(\s*" + d + r"\s*,\s*" + d + r"\s*\)" + eq + d,
        d + r"\s+permute\s+" + d + eq + d,
        r"(?:number\s+of\s+)?permutations?\s+of\s+" + d +
        r"\s+(?:things?|items?|objects?|elements?)\s+taken\s+" + d + r"\s+at\s+a\s+time" + eq + d,
    )
    out = []
    for pat in pats:
        for m in re.finditer(pat, text, re.I):
            out.append((_q(text, m), "combinatorics",
                        {"COMB_VERIFY": {"perm_n": int(m.group(1)), "perm_k": int(m.group(2)),
                                         "claimed_permutations": int(m.group(3))}}))
    return out


_EXTRACTORS: Tuple[Tuple[str, Callable], ...] = (
    ("sum", _x_sum), ("product", _x_product), ("arith_words", _x_arith_words),
    ("power", _x_power), ("factorial", _x_factorial), ("sqrt", _x_sqrt),
    ("combinations", _x_combinations), ("permutations", _x_permutations),
    ("circle", _x_circle), ("pythagorean", _x_pythagorean), ("polygon_angles", _x_polygon_angles),
    ("rectangle", _x_rectangle), ("triangle_inequality", _x_triangle_inequality),
    ("sphere", _x_sphere), ("cube", _x_cube), ("cylinder", _x_cylinder),
    ("physics_force", _x_physics_force), ("kinetic_energy", _x_kinetic_energy),
    ("kinematics", _x_kinematics),
    ("molar_mass", _x_molar_mass),
    ("units_each", _x_each), ("percent", _x_percent),
    ("gross_pay", _x_gross_pay), ("annual_hourly", _x_annual_hourly),
    ("compound_interest", _x_compound), ("rule_of_72", _x_rule72),
    ("elapsed_years", _x_elapsed_years), ("day_of_week", _x_day_of_week),
    ("leap_year", _x_leap_year), ("nutrition_label", _x_nutrition),
    ("physical_constant", _x_physical_constant), ("unit_conversion", _x_unit_conversion),
    ("unit_fact", _x_unit_fact),
)


def extract(text: str) -> List[Dict[str, Any]]:
    """All certain claims in the text, as verify_derivation steps (id, domain, spec, claim).
    Deduped on (domain, spec); order = extractor order, then position."""
    text = (text or "")[:MAX_TEXT]
    steps: List[Dict[str, Any]] = []
    seen = set()
    for xname, fn in _EXTRACTORS:
        for quote, domain, spec in fn(text):
            key = (domain, repr(sorted(spec.items())))
            if key in seen:
                continue
            seen.add(key)
            steps.append({"id": f"a{len(steps) + 1}", "domain": domain, "spec": spec,
                          "claim": quote, "extractor": xname})
            if len(steps) >= MAX_CLAIMS:
                return steps
    return steps


_CHAIN_CONNECTIVE = re.compile(
    r"\b(?:so|therefore|thus|hence|consequently|meaning|which\s+means|so\s+that|"
    r"and\s+so|as\s+a\s+result|it\s+follows(?:\s+that)?)\b", re.I)


def _spec_numbers(spec: Any) -> set:
    """Every number anywhere in a step's spec — works for the {mode, params} math shape (numbers live
    inside the expr strings) and the {WRAPPER: {...}} shape (numbers are values). Booleans excluded."""
    nums: set = set()

    def add(v: Any) -> None:
        if isinstance(v, bool):
            return
        try:
            nums.add(round(float(v), 9))
        except (TypeError, ValueError):
            return

    def walk(o: Any) -> None:
        if isinstance(o, dict):
            for k, val in o.items():
                if k == "mode":            # a routing label, not a quantity
                    continue
                walk(val)
        elif isinstance(o, (list, tuple)):
            for x in o:
                walk(x)
        elif isinstance(o, (int, float)):
            add(o)
        elif isinstance(o, str):
            for tok in re.findall(r"-?\d+(?:\.\d+)?", o):
                add(tok)

    walk(spec)
    return nums


def _norm_pos(text: str):
    """Whitespace-normalized text plus a locator — quotes are stored whitespace-normalized (see _q),
    so a chain has to be read in that same space or the connective search misses."""
    norm = re.sub(r"\s+", " ", text or "")

    def locate(claim: str) -> int:
        q = re.sub(r"\s+", " ", claim or "").strip()
        return norm.find(q) if q else -1

    return norm, locate


def compose_uses(steps: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
    """Set `uses` edges between claims the author explicitly CHAINED: a later claim that reuses an
    earlier claim's number AND sits just after a chaining connective ("so", "therefore", …) depends on
    it. Nothing is invented — both claims are the author's own; the edge only records the dependency the
    prose asserts, so the gate can check the LINK as well as each step (a conclusion resting on a false
    premise no longer stands). Conservative by design: no connective between them, no shared number, or
    too far apart → no edge, and a miss stays a miss."""
    norm, locate = _norm_pos(text)
    pos = {s["id"]: locate(s.get("claim") or "") for s in steps}
    length = {s["id"]: len(re.sub(r"\s+", " ", s.get("claim") or "").strip()) for s in steps}
    nums = {s["id"]: _spec_numbers(s.get("spec") or {}) for s in steps}
    for b in steps:
        pb = pos[b["id"]]
        if pb < 0:
            continue
        for a in steps:
            if a["id"] == b["id"]:
                continue
            pa = pos[a["id"]]
            if pa < 0 or pa >= pb:                       # a must strictly precede b in the text
                continue
            a_end = pa + length[a["id"]]
            if a_end > pb:                               # overlapping quotes — not a chain
                continue
            gap = norm[a_end:pb]
            if len(gap) > 140 or not _CHAIN_CONNECTIVE.search(gap):
                continue
            if not (nums[a["id"]] & nums[b["id"]]):       # b must reuse one of a's numbers
                continue
            b.setdefault("uses", [])
            if a["id"] not in b["uses"]:
                b["uses"].append(a["id"])
    return steps


def audit(text: str, config, seal: bool = True) -> Dict[str, Any]:
    """Extract -> compose the stated chain -> verify the lot as one derivation -> attach one seal.

    Composition (2026-09-25): after extraction, `compose_uses` sets a `uses` edge wherever the author
    chained two claims ("A, so B" reusing A's number). The moat then checks the LINK as well as each
    step, so a conclusion that rests on a false premise no longer stands on its own — the reasoning is
    verified, not just the isolated facts. The derivation runs in TEXT order so a `uses` ref (always an
    earlier claim) is processed first; the report keeps extraction order."""
    steps = extract(text)
    if not steps:
        return {"claims_found": 0, "results": [], "verdict": "NOTHING_TO_CHECK",
                "note": ("No unambiguously checkable claim was found. The auditor extracts only "
                         "certain patterns (sums, percentages, pay, interest, dates, labels) — "
                         "it would rather miss a claim than check the wrong one.")}
    compose_uses(steps, text)
    from .derivation import verify_derivation
    _, locate = _norm_pos(text)
    # The derivation must process a used step before the step that uses it. `uses` edges always point
    # from a later claim back to an earlier one, so text order satisfies that; an unlocatable claim
    # sorts to the end (stable). The report below still comes back in extraction order.
    order = sorted(range(len(steps)),
                   key=lambda i: (locate(steps[i].get("claim") or "") if locate(steps[i].get("claim") or "") >= 0
                                  else 10 ** 9, i))
    dsteps = []
    for i in order:
        s = steps[i]
        d = {"id": s["id"], "domain": s["domain"], "spec": s["spec"], "claim": s["claim"]}
        if s.get("uses"):
            d["uses"] = s["uses"]
        dsteps.append(d)
    dres = verify_derivation(dsteps)
    trail_by_id = {t["id"]: t for t in dres["trail"]}
    results = []
    held = broken = unchecked = 0
    for s in steps:
        t = trail_by_id.get(s["id"], {"status": "ERROR", "detail": ""})
        st = t["status"]
        if st == "CONFIRMED":
            held += 1
        elif st == "MISMATCH":
            broken += 1
        else:  # NOT_APPLICABLE / ERROR — we did not get a result, which is not a finding
            unchecked += 1
        r = {"claim": s["claim"], "extractor": s["extractor"], "domain": s["domain"],
             "status": st, "detail": t.get("detail", "")}
        if t.get("uses"):
            # this claim was read as building on the named earlier claim(s) — the prose said "so"/"therefore"
            r["uses"] = t["uses"]
        if t.get("builds_on_unconfirmed"):
            # raw-checked here, but it rests on a premise that did NOT hold — so it does not stand alone
            r["builds_on_unconfirmed"] = t["builds_on_unconfirmed"]
        results.append(r)
    out: Dict[str, Any] = {
        "claims_found": len(steps), "held": held,
        # `broken` is a finding about the CLAIM; `unchecked` is a fact about US. The old single
        # `broken_or_unchecked` counter merged the two and the page then labelled every one of
        # them "BROKEN" — telling people their true claim was false whenever we simply failed.
        # Kept as the sum for callers that already read it; read the split instead.
        "broken": broken, "unchecked": unchecked,
        "broken_or_unchecked": broken + unchecked,
        "results": results, "verdict": dres["verdict"],
        "note": (f"{len(steps)} claim(s) checked — the rest of the text was NOT. "
                 "Every claim shows its source quote; nothing was generated."),
    }
    if seal:
        from . import receipts
        dom = steps[0]["domain"]
        sealed = receipts.attach(dres, config=config, domain=dom, enabled=True)
        if sealed.get("seal"):
            out["seal"] = sealed["seal"]
    return out
