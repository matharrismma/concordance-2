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

# a money-or-plain number (commas ok, $ ok), with an optional scale WORD kept inside the group so _f can read
# it ("$29.3 million" -> 29.3e6; the failure report H5 found "million" dropped and 29.3 compared to 29,320,113)
_NUM = r"\$?\s*(\d[\d,]*(?:\.\d+)?(?:\s*(?:thousand|million|billion|trillion)\b)?)"
_EQ = r"(?:=|is|equals|comes to|totals?)"      # the claim verb
# an optional hedge before a claimed number — kept INSIDE the quote so extract() can read it (the one rule, H6)
_HEDGE = r"(?:about|approximately|approx\.?|roughly|around|nearly|almost|close\s+to|circa|~|≈)?\s*"


def _f(s: str) -> float:
    from .verifiers.base import literal_scale
    lit, factor = literal_scale(s)
    return float(lit.replace(",", "").replace("$", "").strip()) * factor


def _q(text: str, m: re.Match) -> str:
    """The source quote for a match — the matched span, trimmed, capped."""
    return re.sub(r"\s+", " ", m.group(0)).strip()[:160]


# Each extractor: (name, fn(text) -> list[(quote, domain, spec)]). Pure and conservative.

# ── THE CLAIM GRAMMAR (Gen 3 · 3, 2026-10-04) — one deterministic parser for arithmetic claims ─────
# Until today sum, product, quotient and word-arithmetic were four pair/chain regexes; the cardinal bug of
# 2026-10-03 ("2 * 2 * 3 = 12" judged BROKEN) was a pair taken out of a chain, and a mixed expression
# ("2 + 3 * 4 = 14") was a miss by design. The grammar tokenizes a sentence (numbers, operators, parens,
# the claim verb, everything else as junk) and takes the MAXIMAL expression that ends at the claim verb:
#   expr := term (op term)*     term := NUM | '(' expr ')' | '-' term     op := + | - | * | / | % | words
# with the same zero-false-positive discipline as before, now in one place:
#   * tokens must be adjacent (only whitespace between), so "3 times and 4 people" is not a claim;
#   * an expression must contain at least one binary operator;
#   * a symbolic minus is binary only with whitespace on both sides ("3-5" is a range, "3 - 5" is a sum);
#   * "/" and "x" are operators only between numbers ("$18.50/hr" is a rate, "3 x $4.50" a product);
#   * "^" and "%" end an expression (the power and percent extractors own them);
#   * division by a literal zero is left unextracted — a gap, never a verdict.
# The whole expression goes to the mathematics equality verifier, which honours precedence; the label
# keeps the names the pins know — sum / product / quotient / arith_words — and "expression" for a mix.
_T_NUM = r"\$?\s?\d[\d,]*(?:\.\d+)?"
_T_WORD_OP = r"(?i:plus|minus|times|multiplied\s+by|divided\s+by|modulo|mod)(?![A-Za-z])"
_T_EQ = r"(?:=|(?i:equals|comes\s+to|totals?|is)(?![A-Za-z]))"
_TOKEN = re.compile(
    r"(?P<num>" + _T_NUM + r")"
    r"|(?P<wop>" + _T_WORD_OP + r")"
    r"|(?P<eq>" + _T_EQ + r")"
    r"|(?P<x>(?<=[\d\s])[xX×*](?=\s*\$?\d|\s*\())"
    r"|(?P<bminus>(?<=\s)-(?=\s))"
    r"|(?P<uminus>-(?=\s*\$?\d|\s*\())"
    r"|(?P<op>[+/÷])"
    r"|(?P<lp>\()|(?P<rp>\))"
    r"|(?P<junk>[^\s])"
)
_WORD_TO_OP = {"plus": "+", "minus": "-", "times": "*", "multipliedby": "*", "dividedby": "/", "mod": "%", "modulo": "%"}
_SYM_TO_OP = {"+": "+", "-": "-", "*": "*", "x": "*", "X": "*", "×": "*", "/": "/", "÷": "/"}


def _tokens(text: str):
    """[(kind, value, start, end)] — numbers, operators, parens, the claim verb; everything else is junk."""
    out = []
    for m in _TOKEN.finditer(text):
        kind = m.lastgroup
        v = m.group(0)
        if kind == "num":
            out.append(("num", v.replace("$", "").replace(",", "").strip(), m.start(), m.end()))
        elif kind == "wop":
            out.append(("op", _WORD_TO_OP[re.sub(r"\s+", "", v.lower())], m.start(), m.end(), "word"))
        elif kind in ("x", "op", "bminus"):
            out.append(("op", _SYM_TO_OP[v], m.start(), m.end(), "sym"))
        elif kind == "uminus":
            out.append(("neg", "-", m.start(), m.end()))
        elif kind == "eq":
            out.append(("eq", v, m.start(), m.end()))
        elif kind == "lp":
            out.append(("lp", "(", m.start(), m.end()))
        elif kind == "rp":
            out.append(("rp", ")", m.start(), m.end()))
        else:
            out.append(("junk", v, m.start(), m.end()))
    return out


def _adjacent(text: str, a_end: int, b_start: int) -> bool:
    return text[a_end:b_start].strip() == ""


def _parse_expr(toks, i, text):
    """Greedy expr starting at toks[i]; returns (next_index, parts, n_ops, kinds) or None."""
    r = _parse_term(toks, i, text)
    if r is None:
        return None
    j, parts, n_ops, kinds = r
    while j < len(toks) and toks[j][0] == "op" and _adjacent(text, toks[j - 1][3], toks[j][2]):
        t = _parse_term(toks, j + 1, text) if j + 1 < len(toks) and _adjacent(text, toks[j][3], toks[j + 1][2]) else None
        if t is None:
            break
        k, tparts, tn, tk = t
        parts = parts + [toks[j][1]] + tparts
        n_ops += 1 + tn
        kinds |= {toks[j][4]} | tk
        j = k
    return j, parts, n_ops, kinds


def _parse_term(toks, i, text):
    if i >= len(toks):
        return None
    k, v = toks[i][0], toks[i][1]
    if k == "num":
        return i + 1, [v], 0, set()
    if k == "neg" and i + 1 < len(toks) and _adjacent(text, toks[i][3], toks[i + 1][2]):
        r = _parse_term(toks, i + 1, text)
        if r is None:
            return None
        j, parts, n, kinds = r
        return j, ["-"] + parts, n, kinds
    if k == "lp" and i + 1 < len(toks) and _adjacent(text, toks[i][3], toks[i + 1][2]):
        r = _parse_expr(toks, i + 1, text)
        if r is None:
            return None
        j, parts, n, kinds = r
        if j < len(toks) and toks[j][0] == "rp" and _adjacent(text, toks[j - 1][3], toks[j][2]):
            return j + 1, ["("] + parts + [")"], n, kinds
    return None


def _label(parts, kinds) -> str:
    ops = {p for p in parts if p in ("+", "-", "*", "/", "%")}
    if kinds == {"word"}:
        return "arith_words"
    if ops == {"+"}:
        return "sum"
    if ops == {"*"}:
        return "product"
    if ops == {"/"}:
        return "quotient"
    return "expression"


def _x_grammar(text: str, want: str):
    """Every arithmetic claim "<expr> <verb> <number>" in the text whose label is `want`."""
    out = []
    toks = _tokens(text or "")
    i = 0
    while i < len(toks):
        if toks[i][0] not in ("num", "lp", "neg"):
            i += 1
            continue
        r = _parse_expr(toks, i, text)
        if r is None:
            i += 1
            continue
        j, parts, n_ops, kinds = r
        if n_ops == 0 or j >= len(toks) or toks[j][0] != "eq" or not _adjacent(text, toks[j - 1][3], toks[j][2]):
            i += 1
            continue
        # the claimed value: an optional sign and a number, adjacent to the verb
        k = j + 1
        sign = ""
        if k < len(toks) and toks[k][0] == "neg" and _adjacent(text, toks[j][3], toks[k][2]):
            sign, k = "-", k + 1
        if not (k < len(toks) and toks[k][0] == "num" and _adjacent(text, toks[k - 1][3], toks[k][2])):
            i += 1
            continue
        claimed = sign + toks[k][1]
        if any(parts[q] == "/" and q + 1 < len(parts) and _f(parts[q + 1]) == 0 for q in range(len(parts)) if parts[q] == "/"):
            i = k + 1
            continue                                                  # division by zero: a gap, never a verdict
        label = _label(parts, kinds)
        if label == want:
            span = text[toks[i][2]:toks[k][3]]
            quote = re.sub(r"\s+", " ", span).strip()[:160]
            out.append((quote, "mathematics",
                        {"mode": "equality", "params": {"expr_a": " ".join(parts), "expr_b": claimed,
                                                        "claimed_literal": claimed}}))
        i = k + 1
    return out


def _x_sum(text: str):
    return _x_grammar(text, "sum")


def _x_product(text: str):
    return _x_grammar(text, "product")


def _x_quotient(text: str):
    return _x_grammar(text, "quotient")


def _x_arith_words(text: str):
    return _x_grammar(text, "arith_words")


def _x_expression(text: str):
    """A mixed or parenthesised expression — "2 + 3 * 4 = 14", "(2 + 3) * 4 = 20", "10 - 2 * 3 = 4"."""
    return _x_grammar(text, "expression")


def _x_divisor_count(text: str):
    """"the number of divisors of 12 is 6", "12 has 6 divisors", "60 has twelve divisors" -> number_theory τ(n)."""
    out = []
    pats = (r"(?:the\s+)?number\s+of\s+(?:positive\s+)?divisors\s+of\s+(\d{1,12})\s+" + _EQ + r"\s*(\d{1,4})\b",
            r"\b(\d{1,12})\s+has\s+(?:exactly\s+)?(\d{1,4}|[a-z]+)\s+(?:positive\s+)?divisors\b")
    for pat in pats:
        for m in re.finditer(pat, text, re.I):
            n = int(m.group(1))
            k_raw = m.group(2).lower()
            k = int(k_raw) if k_raw.isdigit() else _SMALL_WORDS.get(k_raw)
            if k is None:
                continue
            out.append((_q(text, m), "number_theory",
                        {"NUM_VERIFY": {"divisors_of": n, "claimed_divisor_count": k}}))
    return out


_SMALL_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
                "ten": 10, "eleven": 11, "twelve": 12, "sixteen": 16, "twenty": 20, "twenty-four": 24}

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
                         + _NUM + r"\s*" + _EQ + r"\s*" + _HEDGE + _NUM, text, re.I):
        pct, base, claimed = _f(m.group(1)), _f(m.group(2)), _f(m.group(3))
        out.append((_q(text, m), "mathematics",
                    {"mode": "equality", "params": {"expr_a": f"({pct}/100)*{base}",
                                                    "expr_b": str(claimed), "claimed_literal": m.group(3)}}))
    # the reversed form (2026-10-08, the failure report H1): "27 is 71% of 42", "$27 million is 71% of $42 million"
    for m in re.finditer(_NUM + r"\s+" + _EQ + r"\s+(\d+(?:\.\d+)?)\s*(?:%|percent|pct)\s+of\s+" + _NUM, text, re.I):
        claimed, pct, base = _f(m.group(1)), _f(m.group(2)), _f(m.group(3))
        out.append((_q(text, m), "mathematics",
                    {"mode": "equality", "params": {"expr_a": f"({pct}/100)*{base}",
                                                    "expr_b": str(claimed), "claimed_literal": m.group(1)}}))
    return out


def _x_gross_pay(text: str):
    out = []
    # A single descriptor word may sit between the count and "hours" — a real quote says
    # "22 machine hours at $95/hr = $2,090", not "22 hours ...". One optional word only, to stay
    # unambiguous (it cannot swallow another number or cross a claim).
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:[a-z]+\s+)?hours?\s*(?:at|@)\s*\$\s*(\d+(?:\.\d+)?)"
                         r"\s*(?:/hr|/hour|per hour|an hour|hourly)?\s*" + _EQ + r"\s*" + _HEDGE + _NUM,
                         text, re.I):
        out.append((_q(text, m), "labor",
                    {"LABOR_VERIFY": {"hours_worked": _f(m.group(1)), "hourly_rate": _f(m.group(2)),
                                      "claimed_gross_pay": _f(m.group(3))}}))
    return out


def _x_annual_hourly(text: str):
    out = []
    for m in re.finditer(_NUM + r"\s*(?:a year|per year|/year|annually|annual(?: salary)?)"
                         r"[^.\n]{0,40}?" + _EQ + r"\s*" + _HEDGE + _NUM +
                         r"\s*(?:/hr|/hour|per hour|an hour|hourly)", text, re.I):
        out.append((_q(text, m), "labor",
                    {"LABOR_VERIFY": {"annual_salary": _f(m.group(1)),
                                      "claimed_hourly_equivalent": _f(m.group(2)),
                                      "claimed_hourly_as_written": m.group(2)}}))
    return out


def _x_hourly_annual(text: str):
    """"$20 per hour is $41,600 per year" (2026-10-08, the failure report H1) — the mirror of _x_annual_hourly."""
    out = []
    for m in re.finditer(_NUM + r"\s*(?:/hr|/hour|per hour|an hour|hourly)[^.\n]{0,30}?" + _EQ + r"\s*" + _HEDGE + _NUM +
                         r"\s*(?:a year|per year|/year|/yr|annually|per annum)", text, re.I):
        out.append((_q(text, m), "labor",
                    {"LABOR_VERIFY": {"hourly_rate": _f(m.group(1)), "claimed_annual_salary": _f(m.group(2)),
                                      "claimed_annual_as_written": m.group(2)}}))
    return out


def _x_compound(text: str):
    """The word 'compound' is REQUIRED in the matched span — 'at 5% for 10 years' alone is
    ambiguous between simple and compound interest, so it is honestly skipped."""
    out = []
    for m in re.finditer(_NUM + r"[^.\n]{0,30}?\bat\s*(\d+(?:\.\d+)?)\s*%[^.\n]{0,40}?"
                         r"\bcompound\w*\b[^.\n]{0,40}?(\d+(?:\.\d+)?)\s*years?"
                         r"[^.\n]{0,30}?(?:=|is|grows to|becomes|yields|worth)\s*" + _HEDGE + _NUM,
                         text, re.I):
        out.append((_q(text, m), "finance",
                    {"FIN_VERIFY": {"principal": _f(m.group(1)), "rate": _f(m.group(2)) / 100.0,
                                    "years": _f(m.group(3)), "claimed_future_value": _f(m.group(4)),
                                    "claimed_future_value_as_written": m.group(4)}}))
    # the other common ordering: "... for N years compounded ... = X"
    for m in re.finditer(_NUM + r"[^.\n]{0,30}?\bat\s*(\d+(?:\.\d+)?)\s*%[^.\n]{0,30}?"
                         r"for\s*(\d+(?:\.\d+)?)\s*years?[^.\n]{0,30}?\bcompound\w*\b"
                         r"[^.\n]{0,30}?(?:=|is|grows to|becomes|yields|worth)\s*" + _HEDGE + _NUM,
                         text, re.I):
        out.append((_q(text, m), "finance",
                    {"FIN_VERIFY": {"principal": _f(m.group(1)), "rate": _f(m.group(2)) / 100.0,
                                    "years": _f(m.group(3)), "claimed_future_value": _f(m.group(4)),
                                    "claimed_future_value_as_written": m.group(4)}}))
    # the third ordering (2026-10-08, the failure report H2): "... compounded annually grows to X over/in/after N years"
    for m in re.finditer(_NUM + r"[^.\n]{0,30}?\bat\s*(\d+(?:\.\d+)?)\s*%[^.\n]{0,40}?\bcompound\w*\b[^.\n]{0,30}?"
                         r"(?:=|is|grows to|becomes|yields|worth)\s*" + _HEDGE + _NUM +
                         r"[^.\n]{0,20}?\b(?:over|in|after|within)\s*(\d+(?:\.\d+)?)\s*years?", text, re.I):
        out.append((_q(text, m), "finance",
                    {"FIN_VERIFY": {"principal": _f(m.group(1)), "rate": _f(m.group(2)) / 100.0,
                                    "years": _f(m.group(4)), "claimed_future_value": _f(m.group(3)),
                                    "claimed_future_value_as_written": m.group(3)}}))
    return out


def _x_rule72(text: str):
    out = []
    for m in re.finditer(r"(?:at\s*)?(\d+(?:\.\d+)?)\s*%[^.\n]{0,50}?doubl\w+[^.\n]{0,30}?"
                         r"(\d+(?:\.\d+)?)\s*years?", text, re.I):
        out.append((_q(text, m), "economics",
                    {"ECON_VERIFY": {"rate_percent": _f(m.group(1)),
                                     "claimed_doubling_years": _f(m.group(2)),
                                     "claimed_doubling_years_as_written": m.group(2)}}))
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
#   * a STATED unit must normalize-MATCH the constant's own unit, or the claim is DECLINED — left
#     unchecked, never silently confirmed on the value alone. Until 2026-10-01 a non-matching unit was
#     DROPPED and the bare value checked, so "the speed of light is 299792458 km/s" (false — 1000x c)
#     and "... 299792458 mph" each earned a sealed HOLDS: the cardinal failure, found by the Fable
#     review. The old rationale — avoid a false BROKEN on an equivalent-but-oddly-formatted unit such
#     as "8.314 J/K/mol" — is served just as well by declining: neither a false HOLDS nor a false
#     BROKEN, because _normalize_unit cannot yet tell "wrong unit" from "same unit, other format"
#     (refinement: a real unit normalizer would let formatting variants confirm and wrong units
#     MISMATCH honestly). A claim with NO unit stated still checks the value; the structured door
#     checks units deliberately. Scientific "e" notation is read; "x 10^n" is left to miss.
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
            r"[ \t]*((?:[^\s.,;:!?()]{1,14}(?:[ \t]+|(?=[.,;:!?)]|$))){0,4})", re.I)
    return _PC_PAT


# Prose that follows a number and is not a unit — "299792458 in a vacuum" must not read "in" as inches
# (a true claim turned BROKEN by a preposition). A unit run that STARTS with one of these is no unit.
_PC_PROSE = frozenset({"in", "a", "an", "at", "to", "as", "is", "on", "of", "or", "by", "it", "if", "so",
                       "no", "and", "the", "for", "that", "which", "when", "with", "from", "was", "are"})


def _pc_spec(name: str, num_text: str, unit_text: str) -> Optional[Dict[str, Any]]:
    """The CONST_VERIFY packet for a named constant, a number as written and the unit tokens after it — or
    None when the name is not a constant the engine knows, the number does not parse, or the unit run is not a
    unit it knows (declined, never confirmed on the bare value)."""
    from .verifiers import physical_constants as _pc
    canon = _pc._canonical(name)
    if canon not in _pc._CONSTANTS:            # the name must resolve to a constant it truly knows
        return None
    try:
        value = float(num_text.replace(",", "").replace(" ", ""))
    except ValueError:
        return None
    # The literal AS WRITTEN rides along (2026-10-07): the verifier reads the stated precision off it,
    # so "9.81" — right to the three figures the person gave — is not refused by a flat tolerance.
    cv: Dict[str, Any] = {"constant": canon, "claimed_value": value, "claimed_literal": num_text}
    tokens = (unit_text or "").split()
    if tokens and tokens[0].lower() not in _PC_PROSE:
        stored = _pc._CONSTANTS[canon]["unit"]
        first = tokens[0]
        if first.lower() == stored.lower() or _pc._normalize_unit(first) == _pc._normalize_unit(stored):
            cv["claimed_unit"] = first
        else:
            # THE UNIT NORMALIZER (2026-10-03, R4): the longest run of tokens that is a unit of the
            # constant's own dimension ("m s^-1 in vacuum" -> "m s^-1"), else the longest run that is a
            # unit at all (a wrong dimension is a claim to answer); the verifier converts, mismatches,
            # or declines. A run no part of which is a unit the engine knows -> DECLINE (unchecked),
            # never confirm on the bare value: that path minted a false HOLDS for "299792458 km/s".
            from .verifiers import si_units as _si
            best = _si.longest_unit_prefix(tokens, stored)
            if best is None:
                return None
            cv["claimed_unit"] = best[0]
    return cv


_PC_REV_PAT: Optional[re.Pattern] = None


def _pc_rev_pattern() -> re.Pattern:
    """Value first (2026-10-08, H6): "approximately 300,000 km/s is the speed of light"."""
    global _PC_REV_PAT
    if _PC_REV_PAT is None:
        from .verifiers import physical_constants as _pc
        names = {k.replace("_", " ") for k in _pc._CONSTANTS}
        for k in _pc._ALIASES:
            phrase = k.replace("_", " ")
            if " " in phrase or phrase in _PC_SAFE_SINGLE:
                names.add(phrase)
        alt = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
        _PC_REV_PAT = re.compile(
            r"(?:about|approximately|roughly|around|~|≈)?\s*"
            r"(\d[\d,]*(?:\.\d+)?(?:\s*[eE]\s*[-+]?\d+)?)"
            r"[ \t]*((?:(?!(?:is|equals)\b)[^\s.,;:!?()]{1,14}[ \t]+){0,3})"
            r"(?:is|equals)\s+(?:the\s+)?(" + alt + r")\b", re.I)
    return _PC_REV_PAT


def _x_physical_constant(text: str):
    out = []
    for m in _pc_pattern().finditer(text):
        cv = _pc_spec(m.group(1), m.group(2), m.group(3) or "")
        if cv is not None:
            out.append((_q(text, m), "physical_constants", {"CONST_VERIFY": cv}))
    for m in _pc_rev_pattern().finditer(text):
        cv = _pc_spec(m.group(3), m.group(1), m.group(2) or "")
        if cv is not None:
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
                                     "to_value": _f(m.group(3)), "to_unit": u2,
                                     "claimed_literal": m.group(3)}}))
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
    """"the square root of N is M". A PERFECT SQUARE goes to the exact-symbolic equality verifier (the result
    is exact, so equality is the right tool — unchanged since 2026-09-15). Any other N (2026-10-07) is an
    irrational approximation the exact verifier would break harshly, so it goes to the NUMERIC verifier and
    is judged at the precision the person STATED (verifiers.base.stated_tolerance_abs: half a unit in the
    last written place) — and only when they stated two or more significant figures: "1.41421" is checked,
    "1" is not extracted at all (a one-figure approximation of an irrational is too coarse to judge either
    way; a miss stays a miss)."""
    import math
    from .verifiers.base import stated_tolerance_abs
    out = []
    for m in re.finditer(r"(?:the\s+)?square\s+root\s+of\s+" + _NUM + r"\s*" + _EQ + r"\s*" + _NUM, text, re.I):
        n = _f(m.group(1))
        if n < 0:
            continue
        if n == int(n) and math.isqrt(int(n)) ** 2 == int(n):          # a perfect square: the exact path
            out.append((_q(text, m), "mathematics",
                        {"mode": "equality", "params": {"expr_a": f"sqrt({int(n)})", "expr_b": str(_f(m.group(2)))}}))
            continue
        lit = m.group(2).replace("$", "").strip()
        if stated_tolerance_abs(lit) is None:                            # one significant figure earns nothing
            continue
        expr_n = str(int(n)) if n == int(n) else repr(n)
        out.append((_q(text, m), "mathematics",
                    {"mode": "numeric", "params": {"numeric_expr": f"sqrt({expr_n})",
                                                   "claimed_value": _f(m.group(2)), "claimed_literal": lit}}))
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
                         + _EQ + r"\s*" + _HEDGE + _NUM + r"\s*(?:g\s*/\s*mol|grams?\s+per\s+mole?)?", text, re.I):
        out.append((_q(text, m), "periodic_table",
                    {"PT_VERIFY": {"formula": m.group(1), "claimed_molar_mass": _f(m.group(2)),
                                   "claimed_literal": m.group(2)}}))
    # formula first, the unit REQUIRED (2026-10-08, the failure report H3): "aspirin C9H8O4 is 180.16 g/mol".
    # Two or more element groups, so a lone capitalised word never reads as a formula.
    for m in re.finditer(r"(?-i:\b([A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*)+))\s+(?:is|=|equals|has\s+a\s+molar\s+mass\s+of|"
                         r"has\s+molar\s+mass)\s*(?:about|approximately|roughly|~|≈)?\s*" + _NUM +
                         r"\s*(?:g\s*/\s*mol|grams?\s+per\s+mole?)\b", text, re.I):
        out.append((_q(text, m), "periodic_table",
                    {"PT_VERIFY": {"formula": m.group(1), "claimed_molar_mass": _f(m.group(2)),
                                   "claimed_literal": m.group(2)}}))
    return out


_MATH_CONSTS = (
    (r"(?:the\s+)?(?:number\s+)?pi|π", "pi"),
    (r"euler'?s\s+number(?:\s+e)?|the\s+constant\s+e", "E"),
    (r"(?:the\s+)?golden\s+ratio|phi|φ", "GoldenRatio"),
)
_MATH_CONST_RE = re.compile(
    r"\b(?P<name>" + "|".join(p for p, _ in _MATH_CONSTS) + r")\s+(?:is|=|equals|≈|~)\s*"
    r"(?:about|approximately|roughly|around|~|≈)?\s*(?P<val>\d+(?:\.\d+)?)(?![\d.]*\s*(?:%|percent))", re.I)


def _x_math_constant(text: str):
    """"pi is 3.14" (2026-10-08, the failure report H4): the mathematical constants, judged at the precision
    stated — "3.14" is right to three figures; "pi is 3" is one figure and earns no window."""
    out = []
    for m in _MATH_CONST_RE.finditer(text):
        name = m.group("name").lower()
        sym = next(s for p, s in _MATH_CONSTS if re.fullmatch(p, name, re.I))
        out.append((_q(text, m), "mathematics",
                    {"mode": "numeric", "params": {"numeric_expr": sym, "claimed_value": float(m.group("val")),
                                                   "claimed_literal": m.group("val")}}))
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
                                     "claimed_kinetic_energy_J": _f(m.group(3)),
                                     "claimed_kinetic_energy_as_written": m.group(3)}}))
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


# ── propositional logic (3a, 2026-09-25): a bounded parser over prose → formal_logic ────────────────
# The structured "next layer": a claim like "P or not P is a tautology" is a determinate structure once
# the prose around it is stripped. A small recursive-descent parser turns the clause into a formula in
# the verifier's syntax; if it does not parse WHOLLY and cleanly, nothing is extracted (a miss stays a
# miss). Variables are single uppercase letters EXCEPT A (article) and I (pronoun), so English prose is
# never mistaken for a proposition.
_LOGIC_TOK = re.compile(r"\(|\)|(?i:\b(?:and|or|not|implies|then)\b)|\b[B-HJ-Z]\b")
_LOGIC_TRAIL = re.compile(r"(?:(?:(?i:\b(?:and|or|not|implies|then)\b)|[B-HJ-Z]|[()])\s*)+$")
_LOGIC_VERDICT = re.compile(
    r"\bis\s+(?P<neg>not\s+)?(?:an?\s+)?"
    r"(?P<kind>tautolog(?:y|ical)|contradiction|contradictory|(?P<un>un)?satisfiable)\b", re.I)


def _prop_tokens(clause: str):
    """Tokenize a propositional clause; None if any non-propositional text sits between tokens."""
    toks: List[str] = []
    last = 0
    for m in _LOGIC_TOK.finditer(clause):
        if clause[last:m.start()].strip():
            return None
        toks.append(m.group(0))
        last = m.end()
    if clause[last:].strip() or not toks:
        return None
    return toks


def _parse_prop(clause: str):
    """Bounded recursive-descent parse → (formula, sorted vars) in the verifier's syntax (& | ~ >>), or
    None if it does not parse wholly and cleanly. Precedence: not > and > or > implies; parens group."""
    toks = _prop_tokens(clause)
    if not toks:
        return None
    variables = set()
    pos = 0

    def peek():
        return toks[pos] if pos < len(toks) else None

    def eat():
        nonlocal pos
        t = toks[pos]
        pos += 1
        return t

    def atom():
        t = peek()
        if t == "(":
            eat()
            e = imp()
            if e is None or peek() != ")":
                return None
            eat()
            return e
        if t is not None and re.fullmatch(r"[B-HJ-Z]", t):
            eat()
            variables.add(t.lower())
            return t.lower()
        return None

    def neg():
        if peek() is not None and peek().lower() == "not":
            eat()
            e = neg()
            return None if e is None else "~" + e
        return atom()

    def conj():
        left = neg()
        if left is None:
            return None
        while peek() is not None and peek().lower() == "and":
            eat()
            right = neg()
            if right is None:
                return None
            left = "(%s & %s)" % (left, right)
        return left

    def disj():
        left = conj()
        if left is None:
            return None
        while peek() is not None and peek().lower() == "or":
            eat()
            right = conj()
            if right is None:
                return None
            left = "(%s | %s)" % (left, right)
        return left

    def imp():
        left = disj()
        if left is None:
            return None
        while peek() is not None and peek().lower() in ("implies", "then"):
            eat()
            right = disj()
            if right is None:
                return None
            left = "(%s >> %s)" % (left, right)
        return left

    formula = imp()
    if formula is None or pos != len(toks) or not variables:
        return None
    return formula, sorted(variables)


def _x_propositional_logic(text: str):
    """"P or not P is a tautology" / "P and not P is a contradiction" / "P and Q is satisfiable" — the
    clause is parsed (single-letter vars excl. A/I, joined by and/or/not/implies/then, with parens) and
    routed to formal_logic's truth-table decision. No clean parse -> nothing extracted. Both polarities:
    "is not a tautology" / "is unsatisfiable" break honestly."""
    out = []
    for vm in _LOGIC_VERDICT.finditer(text):
        tm = _LOGIC_TRAIL.search(text[:vm.start()])
        if not tm:
            continue
        parsed = _parse_prop(tm.group(0).strip())
        if not parsed:
            continue
        formula, variables = parsed
        negated = bool(vm.group("neg"))
        kind = vm.group("kind").lower()
        spec: Dict[str, Any] = {"variables": variables, "formula": formula}
        if kind.startswith("tautolog"):
            spec["claimed_tautology"] = not negated
        elif kind.startswith("contradict"):
            spec["claimed_contradiction"] = not negated
        else:  # (un)satisfiable
            spec["claimed_satisfiable"] = not (negated or bool(vm.group("un")))
        quote = re.sub(r"\s+", " ", tm.group(0).strip() + " " + text[vm.start():vm.end()]).strip()[:160]
        out.append((quote, "formal_logic", {"LOGIC_VERIFY": spec}))
    return out


# ── element FACTS (fact-verifier, 2026-09-25): a lookup claim becomes a VERDICT ──────────────────────
# The gap Matt named: a lookup like "the atomic number of carbon is 6" returned NOTHING_TO_CHECK + FOUND,
# never a verdict. The periodic_table verifier + IUPAC data already exist (definitional identity, zero
# ambiguity); this extractor routes the prose to it, so a chemistry lookup HOLDS or BREAKS honestly. The
# element name is validated against the real table, so a non-element ("the atomic number of the meeting")
# is never extracted — and a miss stays a miss.
def _x_element_fact(text: str):
    """"the atomic number of carbon is 6" / "oxygen has atomic number 8" / "the symbol for gold is Au" —
    routes to periodic_table.element (IUPAC identity). The element must be a real element name; a wrong
    atomic number or symbol breaks honestly with the true one shown."""
    from .verifiers import periodic_table as _pt
    names = _pt._BY_NAME
    out = []
    for m in re.finditer(r"(?:the\s+)?atomic\s+number\s+of\s+([A-Za-z]+)\s+(?:is|=|equals?)\s+(\d{1,3})\b",
                         text, re.I):
        el = m.group(1).lower()
        if el in names:
            out.append((_q(text, m), "periodic_table",
                        {"PT_VERIFY": {"name": el, "claimed_atomic_number": int(m.group(2))}}))
    for m in re.finditer(r"\b([A-Za-z]+)\s+has\s+(?:an?\s+)?atomic\s+number\s+(?:of\s+)?(\d{1,3})\b",
                         text, re.I):
        el = m.group(1).lower()
        if el in names:
            out.append((_q(text, m), "periodic_table",
                        {"PT_VERIFY": {"name": el, "claimed_atomic_number": int(m.group(2))}}))
    for m in re.finditer(r"(?:the\s+)?(?:chemical\s+)?symbol\s+for\s+([A-Za-z]+)\s+(?:is|=)\s+"
                         r"([A-Za-z][a-z]{0,2})\b", text, re.I):
        el = m.group(1).lower()
        if el in names:
            out.append((_q(text, m), "periodic_table",
                        {"PT_VERIFY": {"name": el, "claimed_symbol": m.group(2)}}))
    return out


# ── primality (2026-10-03): "137 is a prime number" / "138 is not prime" — the same declarative shape the
# front door already verifies (ask._PRIME_D); the CHECK door answered NOTHING_TO_CHECK for it. A QUESTION
# ("is 137 prime?") is not a claim and is left to /ask.
_PRIME_DECL = re.compile(r"\b(\d{1,12})\s+is\s+(not\s+)?(?:an?\s+)?(prime|composite)(?:\s+number)?\b", re.I)


def _x_primality(text: str):
    out = []
    for m in _PRIME_DECL.finditer(text or ""):
        n = int(m.group(1))
        claimed = (m.group(3).lower() == "prime")
        if m.group(2):
            claimed = not claimed
        out.append((_q(text, m), "number_theory", {"NUM_VERIFY": {"n_prime": n, "claimed_prime": claimed}}))
    return out


# ── sequence FACTS (fact-verifier, 2026-09-25): "the Nth prime/Fibonacci/triangular number is X" ─────
# Reuses the number_theory verifier's computed sequences (deterministic, OEIS-keyed) — a lookup like
# "the 5th prime is 11" becomes a VERDICT, not a FOUND card. Ordinal-anchored ("Nth <sequence>"), so
# ordinary prose is never mistaken for it; a wrong term breaks honestly with the true one shown.
_SEQ_ORD = r"(?:the\s+)?(\d+)\s*(?:st|nd|rd|th)\s+"
_SEQ_EQ = r"\s+(?:is|=|equals?)\s+(\d+)\b"


def _x_sequence_fact(text: str):
    """"the 5th prime is 11" / "the 7th Fibonacci number is 13" / "the 4th triangular number is 10" —
    routes to number_theory.sequence (1-indexed for these three). A wrong term breaks honestly."""
    out = []
    for seq, word in (("prime", "primes?"), ("fibonacci", "fibonacci"), ("triangular", "triangular")):
        pat = _SEQ_ORD + word + r"(?:\s+number)?" + _SEQ_EQ
        for m in re.finditer(pat, text, re.I):
            out.append((_q(text, m), "number_theory",
                        {"NUM_VERIFY": {"sequence": seq, "sequence_index": int(m.group(1)),
                                        "claimed_term": int(m.group(2))}}))
    return out


_EXTRACTORS: Tuple[Tuple[str, Callable], ...] = (
    ("sum", _x_sum), ("product", _x_product), ("quotient", _x_quotient), ("arith_words", _x_arith_words),
    ("expression", _x_expression),      # THE CLAIM GRAMMAR (Gen 3 · 3): a mixed/parenthesised expression
    ("power", _x_power), ("factorial", _x_factorial), ("sqrt", _x_sqrt),
    ("combinations", _x_combinations), ("permutations", _x_permutations),
    ("propositional_logic", _x_propositional_logic),
    ("circle", _x_circle), ("pythagorean", _x_pythagorean), ("polygon_angles", _x_polygon_angles),
    ("rectangle", _x_rectangle), ("triangle_inequality", _x_triangle_inequality),
    ("sphere", _x_sphere), ("cube", _x_cube), ("cylinder", _x_cylinder),
    ("physics_force", _x_physics_force), ("kinetic_energy", _x_kinetic_energy),
    ("kinematics", _x_kinematics),
    ("molar_mass", _x_molar_mass), ("element_fact", _x_element_fact),
    ("sequence_fact", _x_sequence_fact), ("primality", _x_primality), ("divisor_count", _x_divisor_count),
    ("units_each", _x_each), ("percent", _x_percent),
    ("gross_pay", _x_gross_pay), ("annual_hourly", _x_annual_hourly),
    ("compound_interest", _x_compound), ("rule_of_72", _x_rule72),
    ("hourly_annual", _x_hourly_annual), ("math_constant", _x_math_constant),
    ("elapsed_years", _x_elapsed_years), ("day_of_week", _x_day_of_week),
    ("leap_year", _x_leap_year), ("nutrition_label", _x_nutrition),
    ("physical_constant", _x_physical_constant), ("unit_conversion", _x_unit_conversion),
    ("unit_fact", _x_unit_fact),
)

# THE SECOND STAGE (2026-10-07): unit-anchored slot-fillers, registered AFTER the regexes so a sentence
# both catch dedups to the original. The regexes are word-order bound ("a 2 kg object at 3 m/s has kinetic
# energy 9 J" caught; "the kinetic energy of a 2 kg mass at 3 m/s is 9 J" missed) and reached 13 of the 80
# verified domains; a filler reads the packet keys off the units each number carries, whatever the order.
from .slotfill import FILLERS as _SLOT_FILLERS  # noqa: E402 — no cycle: slotfill imports nothing of ours
_EXTRACTORS = _EXTRACTORS + _SLOT_FILLERS


def _literal_holder(spec: Dict[str, Any]):
    """(the dict that carries the claimed literal, its key) — the math {mode, params} shape or the single
    {WRAPPER: {...}} shape — or (None, None)."""
    holder = spec.get("params") if isinstance(spec.get("params"), dict) else None
    if holder is None:
        inner = [v for v in spec.values() if isinstance(v, dict)]
        holder = inner[0] if len(inner) == 1 else None
    if not holder:
        return None, None
    key = next((k for k in holder if k == "claimed_literal" or k.endswith("_as_written")), None)
    return (holder, key) if key else (None, None)


def _mark_hedge(quote: str, spec: Dict[str, Any]) -> None:
    """THE ONE RULE's hedge (2026-10-08, H6), read ONCE for every extractor: when a hedge word (about,
    approximately, roughly, ~) precedes the claimed number inside the quote, `hedged: True` is set beside the
    literal, and the verifier's window follows base.stated_window. Nothing else widens a prose claim."""
    holder, key = _literal_holder(spec)
    if holder is None:
        return
    lit = str(holder[key])
    i = quote.rfind(lit)
    if i < 0:
        mnum = re.match(r"\$?\s*(-?\d[\d,]*(?:\.\d+)?)", lit)
        i = quote.rfind(mnum.group(1)) if mnum else -1
    if i < 0:
        return
    from .verifiers.base import hedged_before
    if hedged_before(quote[:i]):
        holder["hedged"] = True


def extract(text: str) -> List[Dict[str, Any]]:
    """All certain claims in the text, as verify_derivation steps (id, domain, spec, claim).
    Deduped on (domain, spec); order = extractor order, then position."""
    text = (text or "")[:MAX_TEXT]
    steps: List[Dict[str, Any]] = []
    seen = set()
    for xname, fn in _EXTRACTORS:
        for quote, domain, spec in fn(text):
            _mark_hedge(quote, spec)
            key = (domain, repr(sorted(spec.items())))
            if key in seen:
                continue
            seen.add(key)
            steps.append({"id": f"a{len(steps) + 1}", "domain": domain, "spec": spec,
                          "claim": quote, "extractor": xname})
            if len(steps) >= MAX_CLAIMS:
                return steps
    return steps


# ── THE STRUCTURED HINT (2026-10-08, the failure report H7) ──────────────────────────────────────
# A numeric claim no extractor recognized used to be routed to "open a want" — a dead end, since a want is for
# a missing SOURCE and arithmetic needs none. Now the door hands back a TEMPLATE for the structured form, built
# from the words (never evaluated here): the person edits it and sends it, or asks find_verifier for the
# domain's packet. Offered, never run — the engine does not pick the claim's own path.
_HINT_VERB = re.compile(r"\s(?:=|is|equals|comes\s+to|totals?|makes|gives|yields|comes\s+out\s+to)\s", re.I)
_HINT_NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
_HINT_OPS = re.compile(r"[-+*/^()%]|\b(?:plus|minus|times|multiplied\s+by|divided\s+by|x|×|÷|mod)\b", re.I)


def _as_expression(words: str) -> str:
    """The arithmetic left in a run of words: numbers, operators and parentheses, word-operators mapped; when
    no operator survives, the words themselves inside angle brackets — a slot to fill, never a guess."""
    s = words.strip()
    for w, op in sorted(_WORD_TO_OP.items(), key=lambda kv: -len(kv[0])):
        s = re.sub(r"\b" + w.replace("by", r"\s*by") + r"\b", " " + op + " ", s, flags=re.I)
    s = s.replace("×", "*").replace("÷", "/").replace("$", "").replace(",", "")
    s = re.sub(r"(?<=\d)\s*x\s*(?=\d)", " * ", s, flags=re.I)
    kept = re.findall(r"\d+(?:\.\d+)?|[-+*/^()%]", s)
    if len(kept) == 1 and re.match(r"\d", kept[0]):
        return kept[0]                                         # a lone number is already an expression
    # valid only when numbers and binary operators alternate (parentheses aside): "40 18.50 /" is not arithmetic
    core = [t for t in kept if t not in "()"]
    alternates = (len(core) >= 3 and all(bool(re.match(r"\d", t)) == (i % 2 == 0) for i, t in enumerate(core))
                  and re.match(r"\d", core[-1]) is not None)
    if alternates and kept.count("(") == kept.count(")"):
        return " ".join(kept)
    return "<" + re.sub(r"\s+", " ", words.strip()) + ">"


def looks_arithmetic(text: str) -> bool:
    """Two or more numbers, or a number beside an operator: words that carry arithmetic to check."""
    t = text or ""
    nums = _HINT_NUM.findall(t)
    return len(nums) >= 2 or (len(nums) == 1 and bool(_HINT_OPS.search(t)))


def structured_hint(text: str) -> Optional[Dict[str, Any]]:
    """The template for the structured door, built from the words — or None when they carry no number."""
    t = re.sub(r"\s+", " ", (text or "")).strip()
    nums = _HINT_NUM.findall(t)
    if not nums:
        return None
    out: Dict[str, Any] = {
        "why": ("no extractor recognized these words as a checkable claim; the structured form checks the "
                "arithmetic directly — edit the template, then send it"),
        "send": {"http": "POST /verify with the template as the JSON body", "mcp": "verify {mode, params}"},
        "edit": "expr_a and expr_b must be arithmetic (numbers and + - * / ^ ( )); replace any <words> with the expression they stand for",
        "domain_packet": ("for a physical or financial claim, find_verifier {claim} names the domain and its packet; "
                          "then POST /verify {steps: [{id, domain, spec}]}"),
    }
    verbs = list(_HINT_VERB.finditer(t))
    if verbs:
        v = verbs[-1]
        lhs, rhs = t[:v.start()], t[v.end():]
        if _HINT_NUM.search(lhs) and _HINT_NUM.search(rhs):
            out["template"] = {"mode": "equality", "params": {"expr_a": _as_expression(lhs), "expr_b": _as_expression(rhs)}}
            return out
    try:
        claimed = float(nums[-1].replace(",", ""))
    except ValueError:
        claimed = nums[-1]
    out["template"] = {"mode": "numeric", "params": {"numeric_expr": "<the expression>", "claimed_value": claimed}}
    return out


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


# ── GOVERNED CLAIMS + COVERAGE (2026-10-08, the failure report C2 and C4) ─────────────────────────
# C2: "It is false that 2 + 2 = 4" HELD, because the extractor lifted "2 + 2 = 4" out of its sentence and the
# negation never reached the verifier. A claim the text does not assert plainly — a negation, a reported belief
# (nobody believes, denies, doubts) or a hypothetical (suppose, assume, unless) governs it in the same sentence,
# or the sentence calls it false right after it — is DECLINED, never checked as if asserted. The engine verifies
# what the text says, not a fragment. ("if"/"whether" are left out on purpose: "check if 2 + 2 = 4" is a request.)
# C4: "2 + 2 = 4, therefore vaccines cause autism" HELD at the top level after checking one clause. The headline
# is what gets quoted, so the top-level verdict is HOLDS only when the checked claims COVER the text: material
# text outside every checked span — a number, a governed claim, or three or more content words in a row — makes
# it PARTIAL. BROKEN stays BROKEN (a false claim is false whatever surrounds it).
_GOV_BEFORE = re.compile(
    r"\b(?:not|no|never|false|untrue|wrong|incorrect|isn't|aren't|wasn't|weren't|don't|doesn't|didn't|cannot|"
    r"can't|couldn't|nobody|no\s+one|no-one|none|nothing|den(?:y|ies|ied)|doubt(?:s|ed|ful)?|disput(?:e|es|ed)|"
    r"believ(?:e|es|ed|ing)|belief|think(?:s)?|thought|alleg(?:ed|es|edly)|suppos(?:e|ed|edly|ing)|"
    r"assum(?:e|es|ed|ing)|imagine|pretend(?:s|ed)?|hypothetically|unless|myth|lie|lies|hoax|mistaken(?:ly)?|"
    r"wrongly|erroneous(?:ly)?|falsely|contrary\s+to)\b", re.I)
_GOV_AFTER = re.compile(
    r"^\W{0,3}(?:(?:is|was|'s|that's|which\s+is|that\s+is)\s+(?:not\s+(?:true|right|correct|so)|false|wrong|"
    r"incorrect|untrue|a\s+lie|a\s+myth|nonsense|mistaken|bogus|disputed|doubtful)|isn't|is\s+not|wasn't)\b", re.I)
_SENT_BREAK = re.compile(r"[.!?;\n]")
_STOP = frozenset("""a an the and or but so then also is are was were be been being am it its it's this that these
those which who whom whose what there here of to in on at by for from with as about around approximately roughly
nearly almost exactly just only very really indeed true truly correct correctly right yes ok okay note check please
see i we you they he she them us my our your their me him her fact facts clearly obviously course certainly sure
dollars dollar usd cents percent per each every total totals totalling totaling overall meanwhile too either neither
both all any some such more less than equal equals therefore thus hence because since while when where after before
during between among within without into onto over under up down out off again further once still yet now today
currently well simply plainly actually basically namely etc""".split())


def _governor(norm: str, start: int, end: int) -> Optional[str]:
    """The phrase that governs the claim at norm[start:end] in its own sentence, or None."""
    sent_start = max((m.end() for m in _SENT_BREAK.finditer(norm, 0, start)), default=0)
    m_end = _SENT_BREAK.search(norm, end)
    sent_end = m_end.start() if m_end else len(norm)
    before, after = norm[sent_start:start], norm[end:sent_end]
    hits = list(_GOV_BEFORE.finditer(before))
    if hits:
        return hits[-1].group(0)
    m = _GOV_AFTER.search(after)
    return m.group(0).strip(" ,") if m else None


def _material(frag: str) -> bool:
    toks = re.findall(r"[A-Za-z][A-Za-z'’\-]*|\d[\d,.]*", frag)
    if any(ch.isdigit() for t in toks for ch in t):
        return True
    run = best = 0
    for t in toks:
        if t.lower().strip("'’-") in _STOP:
            run = 0
        else:
            run += 1
            best = max(best, run)
    return best >= 3


def _material_fragments(norm: str, quotes: List[str], locate) -> List[str]:
    """The pieces of the (whitespace-normalised) text that no checked quote covers and that still say something:
    a number, or three or more content words in a row. Connectives, articles, units and filler do not count."""
    mask = bytearray(len(norm))
    for q in quotes:
        qn = re.sub(r"\s+", " ", q or "").strip()
        p = locate(q)
        if p >= 0 and qn:
            mask[p:p + len(qn)] = b"\x01" * len(qn)
    frags, cur = [], []
    for i, ch in enumerate(norm):
        if mask[i]:
            if cur:
                frags.append("".join(cur)); cur = []
        else:
            cur.append(ch)
    if cur:
        frags.append("".join(cur))
    out = []
    for f in frags:
        if _material(f):
            out.append(re.sub(r"^\W+|\W+$", "", f.strip())[:140])
    return out


def audit(text: str, config, seal: bool = True, index: bool = True, card: bool = True) -> Dict[str, Any]:
    """Extract -> compose the stated chain -> decline what the text does not assert -> verify the rest as one
    derivation -> attach one seal to that fragment -> say what was NOT checked.

    Composition (2026-09-25): after extraction, `compose_uses` sets a `uses` edge wherever the author
    chained two claims ("A, so B" reusing A's number). The moat then checks the LINK as well as each
    step, so a conclusion that rests on a false premise no longer stands on its own — the reasoning is
    verified, not just the isolated facts. The derivation runs in TEXT order so a `uses` ref (always an
    earlier claim) is processed first; the report keeps extraction order.

    Governed claims and coverage (2026-10-08, the failure report): see _GOV_BEFORE / _material_fragments above.
    Verdicts: HOLDS (every checked claim held AND the checked claims cover the text), PARTIAL (the checked
    fragment held; material text was not checked — named in `coverage.unchecked_text`), BROKEN, INCOMPLETE
    (nothing could be checked, or every claim found is governed and was declined), NOTHING_TO_CHECK."""
    text = (text or "")[:MAX_TEXT]
    steps = extract(text)
    if not steps:
        return {"claims_found": 0, "results": [], "verdict": "NOTHING_TO_CHECK",
                "note": ("No unambiguously checkable claim was found. The auditor extracts only "
                         "certain patterns (sums, percentages, pay, interest, dates, labels) — "
                         "it would rather miss a claim than check the wrong one.")}
    compose_uses(steps, text)
    norm, locate = _norm_pos(text)
    governed = []
    for s_ in steps:
        p = locate(s_.get("claim") or "")
        if p < 0:
            continue
        g = _governor(norm, p, p + len(re.sub(r"\s+", " ", s_["claim"]).strip()))
        if g:
            s_["governed"] = g
            governed.append(s_)
    checked = [s_ for s_ in steps if not s_.get("governed")]
    gov_ids = {s_["id"] for s_ in governed}
    from .derivation import verify_derivation
    # The derivation must process a used step before the step that uses it. `uses` edges always point
    # from a later claim back to an earlier one, so text order satisfies that; an unlocatable claim
    # sorts to the end (stable). The report below still comes back in extraction order.
    order = sorted(range(len(checked)),
                   key=lambda i: (locate(checked[i].get("claim") or "") if locate(checked[i].get("claim") or "") >= 0
                                  else 10 ** 9, i))
    dsteps = []
    for i in order:
        s_ = checked[i]
        d = {"id": s_["id"], "domain": s_["domain"], "spec": s_["spec"], "claim": s_["claim"]}
        uses = [u for u in (s_.get("uses") or []) if u not in gov_ids]
        if uses:
            d["uses"] = uses
        dsteps.append(d)
    dres = verify_derivation(dsteps) if dsteps else {"verdict": "INCOMPLETE", "trail": []}
    trail_by_id = {t["id"]: t for t in dres["trail"]}
    results = []
    held = broken = unchecked = 0
    for s_ in steps:
        if s_.get("governed"):
            unchecked += 1
            results.append({"claim": s_["claim"], "extractor": s_["extractor"], "domain": s_["domain"],
                            "status": "DECLINED", "governed_by": s_["governed"],
                            "detail": (f"governed by '{s_['governed']}': the text does not assert this claim plainly "
                                       "(a negation, a reported belief or a condition governs it), so it was not "
                                       "checked — state the bare claim to check it")})
            continue
        t = trail_by_id.get(s_["id"], {"status": "ERROR", "detail": ""})
        st = t["status"]
        if st == "CONFIRMED":
            held += 1
        elif st == "MISMATCH":
            broken += 1
        else:  # NOT_APPLICABLE / ERROR — we did not get a result, which is not a finding
            unchecked += 1
        r = {"claim": s_["claim"], "extractor": s_["extractor"], "domain": s_["domain"],
             "status": st, "detail": t.get("detail", "")}
        if t.get("uses"):
            # this claim was read as building on the named earlier claim(s) — the prose said "so"/"therefore"
            r["uses"] = t["uses"]
        if t.get("builds_on_unconfirmed"):
            # raw-checked here, but it rests on a premise that did NOT hold — so it does not stand alone
            r["builds_on_unconfirmed"] = t["builds_on_unconfirmed"]
        results.append(r)
    leftover = _material_fragments(norm, [s_["claim"] for s_ in steps], locate)
    complete = not leftover and not governed
    verdict = dres["verdict"]
    if governed and not checked:
        verdict = "INCOMPLETE"
    elif verdict == "HOLDS" and not complete:
        verdict = "PARTIAL"
    note = f"{len(checked)} claim(s) checked — the rest of the text was NOT. "
    if leftover:
        note += "Not checked: " + "; ".join(f"'{x}'" for x in leftover[:4]) + ". "
    if governed:
        note += "Declined (governed, not asserted plainly): " + "; ".join(f"'{s_['claim']}'" for s_ in governed[:4]) + ". "
    note += "Every claim shows its source quote; nothing was generated."
    out: Dict[str, Any] = {
        "claims_found": len(steps), "held": held,
        # `broken` is a finding about the CLAIM; `unchecked` is a fact about US. The old single
        # `broken_or_unchecked` counter merged the two and the page then labelled every one of
        # them "BROKEN" — telling people their true claim was false whenever we simply failed.
        # Kept as the sum for callers that already read it; read the split instead.
        "broken": broken, "unchecked": unchecked,
        "broken_or_unchecked": broken + unchecked,
        "results": results, "verdict": verdict,
        "coverage": {"complete": complete, "checked": [s_["claim"] for s_ in checked],
                     "unchecked_text": leftover,
                     "governed": [{"claim": s_["claim"], "by": s_["governed"]} for s_ in governed]},
        "note": note,
    }
    if seal and dsteps:
        from . import receipts
        dom = checked[0]["domain"]
        # `index` carries the bounded-seal choice: the explicit /verify door indexes the receipt card into
        # the live corpus (True); the high-frequency ambient /ask audit seals durably but does NOT (False),
        # so a visible re-checkable seal on every checked turn never bloats the corpus (Jevons governor).
        # The seal covers the checked fragment only — never the text around it.
        sealed = receipts.attach(dres, config=config, domain=dom, enabled=True, index=index, card=card)
        if sealed.get("seal"):
            out["seal"] = sealed["seal"]
    return out
