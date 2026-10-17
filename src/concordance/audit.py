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

import copy
import re
from functools import lru_cache
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
    from .verifiers.base import stated_window, hedged_before
    out = []
    pats = (r"(?:the\s+)?square\s+root\s+of\s+" + _NUM + r"\s*" + _EQ + r"\s*" + _HEDGE + _NUM,
            r"\bsqrt\s*\(\s*" + _NUM + r"\s*\)\s*(?:=|is|equals)\s*" + _HEDGE + _NUM,       # sqrt(144) = 12 (recall, 2026-10-08)
            r"√\s*" + _NUM + r"\s*(?:=|≈|~|is|equals)\s*" + _HEDGE + _NUM)                   # √2 ≈ 1.414
    for m in (mm for pat in pats for mm in re.finditer(pat, text, re.I)):
        n = _f(m.group(1))
        if n < 0:
            continue
        if n == int(n) and math.isqrt(int(n)) ** 2 == int(n):          # a perfect square: the exact path
            out.append((_q(text, m), "mathematics",
                        {"mode": "equality", "params": {"expr_a": f"sqrt({int(n)})", "expr_b": str(_f(m.group(2)))}}))
            continue
        lit = m.group(2).replace("$", "").strip()
        if stated_window(lit, hedged_before(text[:m.start(2)])) is None:   # one figure earns nothing unless hedged
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
                    {"GEOM_VERIFY": {"circle_radius": _f(m.group(1)), "claimed_circle_area": _f(m.group(2)),
                                     "claimed_circle_area_as_written": m.group(2)}}))
    for m in re.finditer(rad + r"circumference\s+(?:of\s+)?" + approx + _NUM, text, re.I):
        out.append((_q(text, m), "geometry",
                    {"GEOM_VERIFY": {"circle_radius": _f(m.group(1)), "claimed_circle_circumference": _f(m.group(2)),
                                     "claimed_circle_circumference_as_written": m.group(2)}}))
    # property first (recall, 2026-10-08): "the area of a circle with radius 3 is 28.27"
    for m in re.finditer(r"(?:the\s+)?(area|circumference)\s+of\s+(?:a|the)\s+circle\s+(?:of|with)\s+(?:an?\s+)?radius\s+(?:of\s+)?"
                         + _NUM + r"\s+(?:is|=|equals)\s+" + approx + _NUM, text, re.I):
        key = "claimed_circle_area" if m.group(1).lower() == "area" else "claimed_circle_circumference"
        out.append((_q(text, m), "geometry",
                    {"GEOM_VERIFY": {"circle_radius": _f(m.group(2)), key: _f(m.group(3)), key + "_as_written": m.group(3)}}))
    return out


def _x_physics_force(text: str):
    """"M kg at A m/s^2 exerts F N" — Newton's second law, F = m*a, routed to the physics verifier.
    The three units (kg, m/s^2, N) anchor it, so it is unambiguous; a wrong force breaks honestly."""
    n = r"(\d[\d,]*(?:\.\d+)?)"
    pat = (n + r"\s*kg\b[^.\n]{0,25}?\bat\s+" + n +
           r"\s*(?:m/s\^?2|m/s²|m/s/s|meters?\s+per\s+second\s+squared)\b[^.\n]{0,25}?"
           r"(?:exerts?|is|=|equals|produces?|gives?|has|needs?|requires?|takes?)\s*(?:a\s+)?(?:force\s+of\s+)?" + n +
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
    rev = (r"interior\s+angles?\s+of\s+(?:a|an|the)\s+(" + names + r")\b[^.\n]{0,20}?"
           r"(?:sum[a-z]*(?:\s+to)?|add\s+up\s+to|is|are|=|equals?|total[a-z]*)\s*" +
           r"(\d[\d,]*(?:\.\d+)?)\s*(?:°|degrees?|deg)\b")                       # reversed (recall, 2026-10-08)
    out = []
    for p in (pat, rev):
        for m in re.finditer(p, text, re.I):
            out.append((_q(text, m), "geometry",
                        {"GEOM_VERIFY": {"polygon_n": _POLY[m.group(1).lower()],
                                         "claimed_interior_angle_sum_deg": _f(m.group(2)),
                                         "claimed_interior_angle_sum_deg_as_written": m.group(2)}}))
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
                                     "claimed_rect_area": _f(m.group(3)),
                                     "claimed_rect_area_as_written": m.group(3)}}))
    unit = r"(?:\s*(?:m|cm|mm|km|ft|feet|foot|in|inches|yards?|yd|meters?|metres?))?"
    first = (r"\b" + n + unit + r"\s*(?:by|×|x)\s*" + n + unit + r"\s+rectangle\s+(?:has|is|=|with)\s+(?:an?\s+)?area\s+(?:of\s+)?" + approx + n)
    for m in re.finditer(first, text, re.I):                          # dims first (recall, 2026-10-08)
        out.append((_q(text, m), "geometry",
                    {"GEOM_VERIFY": {"rect_length": _f(m.group(1)), "rect_width": _f(m.group(2)),
                                     "claimed_rect_area": _f(m.group(3)), "claimed_rect_area_as_written": m.group(3)}}))
    with_units = (r"rectangle\s+" + n + unit + r"\s*(?:by|×|x)\s*" + n + unit + r"[^.\n]{0,25}?\b(?:has|is|=|with)\s+(?:an?\s+)?area\s+(?:of\s+)?" + approx + n)
    for m in re.finditer(with_units, text, re.I):                     # "a rectangle 5 m by 8 m has an area of 40 square meters"
        out.append((_q(text, m), "geometry",
                    {"GEOM_VERIFY": {"rect_length": _f(m.group(1)), "rect_width": _f(m.group(2)),
                                     "claimed_rect_area": _f(m.group(3)), "claimed_rect_area_as_written": m.group(3)}}))
    for m in re.finditer(dims + r"perimeter\s+(?:of\s+)?" + approx + n, text, re.I):
        out.append((_q(text, m), "geometry",
                    {"GEOM_VERIFY": {"rect_length": _f(m.group(1)), "rect_width": _f(m.group(2)),
                                     "claimed_rect_perimeter": _f(m.group(3)),
                                     "claimed_rect_perimeter_as_written": m.group(3)}}))
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
                                     "claimed_sphere_volume": _f(m.group(2)),
                                     "claimed_sphere_volume_as_written": m.group(2)}}))
    for m in re.finditer(rad + r"surface\s+area\s+(?:of\s+)?" + approx + n, text, re.I):
        out.append((_q(text, m), "geometry",
                    {"GEOM_VERIFY": {"sphere_radius": _f(m.group(1)),
                                     "claimed_sphere_surface_area": _f(m.group(2)),
                                     "claimed_sphere_surface_area_as_written": m.group(2)}}))
    # property first (recall, 2026-10-08): "the volume of a sphere with radius 3 is 113.1"
    for m in re.finditer(r"(?:the\s+)?(volume|surface\s+area)\s+of\s+(?:a|the)\s+sphere\s+(?:of|with)\s+(?:an?\s+)?radius\s+(?:of\s+)?"
                         + n + r"\s+(?:is|=|equals)\s+" + approx + n, text, re.I):
        key = "claimed_sphere_volume" if m.group(1).lower() == "volume" else "claimed_sphere_surface_area"
        out.append((_q(text, m), "geometry",
                    {"GEOM_VERIFY": {"sphere_radius": _f(m.group(2)), key: _f(m.group(3)), key + "_as_written": m.group(3)}}))
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
                                     "claimed_cube_volume": _f(m.group(2)),
                                     "claimed_cube_volume_as_written": m.group(2)}}))
    for m in re.finditer(side + r"surface\s+area\s+(?:of\s+)?" + approx + n, text, re.I):
        out.append((_q(text, m), "geometry",
                    {"GEOM_VERIFY": {"cube_side": _f(m.group(1)),
                                     "claimed_cube_surface_area": _f(m.group(2)),
                                     "claimed_cube_surface_area_as_written": m.group(2)}}))
    # property first (recall, 2026-10-08): "the volume of a cube of side 4 is 64"
    for m in re.finditer(r"(?:the\s+)?(volume|surface\s+area)\s+of\s+(?:a|the)\s+cube\s+(?:of|with)\s+(?:an?\s+)?(?:side|edge)\s+(?:lengths?\s+)?(?:of\s+)?"
                         + n + r"\s+(?:is|=|equals)\s+" + approx + n, text, re.I):
        key = "claimed_cube_volume" if m.group(1).lower() == "volume" else "claimed_cube_surface_area"
        out.append((_q(text, m), "geometry",
                    {"GEOM_VERIFY": {"cube_side": _f(m.group(2)), key: _f(m.group(3)), key + "_as_written": m.group(3)}}))
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
                                     "claimed_cyl_volume": _f(m.group(3)),
                                     "claimed_cyl_volume_as_written": m.group(3)}}))
    # property first (recall, 2026-10-08): "the volume of a cylinder with radius 2 and height 5 is 62.83"
    for m in re.finditer(r"(?:the\s+)?volume\s+of\s+(?:a|the)\s+cylinder\s+(?:of|with)\s+(?:an?\s+)?radius\s+(?:of\s+)?" + n +
                         r"\s+and\s+(?:an?\s+)?height\s+(?:of\s+)?" + n + r"\s+(?:is|=|equals)\s+" + approx + n, text, re.I):
        out.append((_q(text, m), "geometry",
                    {"GEOM_VERIFY": {"cyl_radius": _f(m.group(1)), "cyl_height": _f(m.group(2)),
                                     "claimed_cyl_volume": _f(m.group(3)),
                                     "claimed_cyl_volume_as_written": m.group(3)}}))
    return out


# nPr / nCr notation — compact (5P3, 5C2) or functional (P(5,3), C(5,2)). ONE source of truth for "this
# is combinatorics, not plain arithmetic to sympify", used by the front door (ask._looks_math) and the
# candidate router (candidates._arithmetic_side) so the rule lives in exactly one place, not three.
COMBINATORICS_NOTATION_RE = re.compile(r"\b\d+\s*[PC]\s*\d+\b|[PC]\s*\(\s*\d+\s*,\s*\d+\s*\)")


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
        r"\b" + d + r"\s*C\s*" + d + eq + d,                                          # 5C2 = 10 (compact nCr)
        r"(?:number\s+of\s+)?combinations?\s+of\s+" + d +
        r"\s+(?:things?|items?|objects?|elements?)\s+taken\s+" + d + r"\s+at\s+a\s+time" + eq + d,
    )
    out = []
    for pat in pats:
        for m in re.finditer(pat, text, re.I):
            out.append((_q(text, m), "combinatorics",
                        {"COMB_VERIFY": {"comb_n": int(m.group(1)), "comb_k": int(m.group(2)),
                                         "claimed_combinations": int(m.group(3))}}))
    # "the number of ways to choose 3 from 10 is 120" (recall, 2026-10-08): k first, then n
    for m in re.finditer(r"(?:the\s+number\s+of\s+)?ways\s+to\s+(?:choose|pick|select)\s+" + d +
                         r"\s+(?:from|out\s+of)\s+" + d + eq + d, text, re.I):
        out.append((_q(text, m), "combinatorics",
                    {"COMB_VERIFY": {"comb_n": int(m.group(2)), "comb_k": int(m.group(1)),
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
        r"(?:number\s+of\s+)?permutations?\s+of\s+" + d + r"\s+taken\s+" + d + r"\s+at\s+a\s+time\s*(?:is|=|equals?|:)\s*" + d,
        r"\b" + d + r"\s*P\s*" + d + eq + d,                                         # 5P3 = 60 (recall, 2026-10-08)
    )
    out = []
    for pat in pats:
        for m in re.finditer(pat, text, re.I):
            out.append((_q(text, m), "combinatorics",
                        {"COMB_VERIFY": {"perm_n": int(m.group(1)), "perm_k": int(m.group(2)),
                                         "claimed_permutations": int(m.group(3))}}))
    # arranging ALL of them: n! (recall, 2026-10-08) - "the number of ways to arrange 5 books is 120",
    # "there are 720 ways to order 6 people"
    for m in re.finditer(r"(?:the\s+number\s+of\s+)?ways\s+to\s+(?:arrange|order)\s+" + d + r"\s+[a-z]+\s*(?:is|=|equals?)\s*" + d, text, re.I):
        out.append((_q(text, m), "combinatorics",
                    {"COMB_VERIFY": {"perm_n": int(m.group(1)), "perm_k": int(m.group(1)),
                                     "claimed_permutations": int(m.group(2))}}))
    for m in re.finditer(r"there\s+are\s+" + d + r"\s+ways\s+to\s+(?:arrange|order)\s+" + d + r"\s+[a-z]+", text, re.I):
        out.append((_q(text, m), "combinatorics",
                    {"COMB_VERIFY": {"perm_n": int(m.group(2)), "perm_k": int(m.group(2)),
                                     "claimed_permutations": int(m.group(1))}}))
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


# ── FORMAL LOGIC AS A STRENGTH (Matt, 2026-10-08) ─────────────────────────────────────────────────
# The one parser above (_parse_prop) was reached only through "is a tautology / contradiction / satisfiable".
# Here the rest of what people actually write about propositional logic: a RELATION between two clauses
# ("P implies Q is equivalent to not Q implies not P", "P and Q entails P"), an ARGUMENT judged valid or not
# ("If P then Q; P; therefore Q is valid" - entailment of the conclusion by the premises), a categorical
# SYLLOGISM ("All men are mortal; Socrates is a man; therefore Socrates is mortal is valid" - rhetoric's
# mood-and-figure table, the major premise chosen by the conclusion's predicate, singular terms read as
# universal), the COUNTS a truth table carries (2^n rows, 2^(2^n) functions) and the NAMED FORMS judged by their
# own schemas (modus ponens is valid; affirming the consequent is a fallacy). Same discipline: a clause that does
# not parse wholly is not extracted; a miss stays a miss.
_LOGIC_HEAD = re.compile(r"^\s*(?:(?:(?i:\b(?:and|or|not|implies|then)\b)|[B-HJ-Z]|[()])\s*)+")
_LOGIC_EQUIV = re.compile(r"\b(?:is|are)\s+(?P<neg>not\s+)?(?:logically\s+)?equivalent\s+to\b|(?P<sym>\s≡\s)", re.I)
_LOGIC_ENTAIL = re.compile(r"\b(?P<neg>does\s+not\s+|doesn't\s+|do\s+not\s+|don't\s+)?(?:entails?|logically\s+impl(?:y|ies))\b", re.I)
_LOGIC_VALID = re.compile(r"\b(?:is|are)\s+(?P<neg>not\s+)?(?:an?\s+)?(?P<kind>valid|invalid)(?:\s+(?:argument|inference|form|syllogism|reasoning))?\b", re.I)
_LOGIC_THEREFORE = re.compile(r"\b(?:therefore|hence|thus|so|ergo|it\s+follows\s+that|consequently)\b[,:]?\s*|∴\s*", re.I)
_LOGIC_FORMS = {
    "modus ponens": (["p >> q", "p"], "q"), "modus tollens": (["p >> q", "~q"], "~p"),
    "hypothetical syllogism": (["p >> q", "q >> r"], "p >> r"), "disjunctive syllogism": (["p | q", "~p"], "q"),
    "constructive dilemma": (["(p >> q) & (r >> s)", "p | r"], "q | s"),
    "affirming the consequent": (["p >> q", "q"], "p"), "denying the antecedent": (["p >> q", "~p"], "~q"),
    "affirming a disjunct": (["p | q", "p"], "~q"),
}
_LOGIC_FORM_RE = re.compile(
    r"\b(?P<form>" + "|".join(re.escape(k) for k in sorted(_LOGIC_FORMS, key=len, reverse=True)) + r")\b\s+(?:is|are)\s+"
    r"(?P<neg>not\s+)?(?:an?\s+)?(?:(?P<fal>(?:formal\s+)?fallac(?:y|ious)|invalid(?:\s+\w+)?)|(?P<val>valid(?:\s+\w+)?)|(?P<ok>a\s+valid\s+\w+))\b", re.I)
# The ORDERED number words (one->1 by position), distinct from _SMALL_WORDS (the dict at the divisor
# extractor above). They were BOTH named _SMALL_WORDS: this tuple silently shadowed the dict, so
# _x_divisor_count's `_SMALL_WORDS.get(...)` hit a tuple and raised inside audit.extract — turning every
# "N has K divisors" claim into a fall-through. Renamed so neither shadows the other.
_NUMBER_WORDS = ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve")


def _small(tok: str) -> int:
    """'five' -> 5; a digit string -> its int."""
    t = tok.strip().lower()
    return _NUMBER_WORDS.index(t) + 1 if t in _NUMBER_WORDS else int(t)


_SING = {"men": "man", "women": "woman", "people": "person", "children": "child", "mice": "mouse", "geese": "goose",
         "feet": "foot", "teeth": "tooth", "oxen": "ox", "humans": "human", "mortals": "mortal"}


def _sing(term: str) -> str:
    """One lower-case singular for a syllogism term, so 'men' and 'man' are the same middle term."""
    t = re.sub(r"\s+", " ", term.strip().lower())
    t = re.sub(r"^(?:a|an|the)\s+", "", t)
    if t in _SING:
        return _SING[t]
    if len(t) > 4 and t.endswith("ies"):
        return t[:-3] + "y"
    if len(t) > 4 and (t.endswith("ses") or t.endswith("xes") or t.endswith("ches") or t.endswith("shes")):
        return t[:-2]
    if len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
        return t[:-1]
    return t


def _categorical(clause: str):
    """'All men are mortal' / 'No fish are mammals' / 'Some S are (not) P' / 'Socrates is a man' -> a premise in
    rhetoric's grammar with singular terms, or None."""
    c = clause.strip().rstrip(".").strip()
    m = re.match(r"^(all|every|no|some)\s+(.+?)\s+(?:are|is)(\s+not)?\s+(?:an?\s+)?(.+)$", c, re.I)
    if m:
        q = m.group(1).lower()
        q = "all" if q == "every" else q
        return "%s %s are %s%s" % (q.capitalize(), _sing(m.group(2)), "not " if m.group(3) else "", _sing(m.group(4)))
    m = re.match(r"^([A-Z][\w-]*)\s+is\s+(not\s+)?(?:an?\s+)?([a-z][\w\s-]*)$", c)
    if m:                                                     # a singular term read as universal: Socrates is a man
        return "%s %s are %s%s" % ("No" if m.group(2) else "All", m.group(1).lower(), "", _sing(m.group(3))) \
            if not m.group(2) else "No %s are %s" % (m.group(1).lower(), _sing(m.group(3)))
    return None


def _x_logic_relations(text: str):
    """"P implies Q is equivalent to not Q implies not P" -> formal_logic.equivalence; "P and Q entails P" ->
    formal_logic.entailment. Both polarities. Both clauses must parse wholly."""
    out = []
    for m in _LOGIC_EQUIV.finditer(text):
        tm = _LOGIC_TRAIL.search(text[:m.start()])
        hm = _LOGIC_HEAD.match(text[m.end():])
        if not tm or not hm:
            continue
        pa, pb = _parse_prop(tm.group(0).strip()), _parse_prop(hm.group(0).strip())
        if not pa or not pb:
            continue
        quote = re.sub(r"\s+", " ", tm.group(0).strip() + " " + text[m.start():m.end()].strip() + " " + hm.group(0).strip())[:160]
        out.append((quote, "formal_logic",
                    {"LOGIC_VERIFY": {"variables": sorted(set(pa[1]) | set(pb[1])), "formula_a": pa[0], "formula_b": pb[0],
                                      "claimed_equivalent": not bool(m.group("neg"))}}))
    for m in _LOGIC_ENTAIL.finditer(text):
        tm = _LOGIC_TRAIL.search(text[:m.start()])
        hm = _LOGIC_HEAD.match(text[m.end():])
        if not tm or not hm:
            continue
        pa, pb = _parse_prop(tm.group(0).strip()), _parse_prop(hm.group(0).strip())
        if not pa or not pb:
            continue
        quote = re.sub(r"\s+", " ", tm.group(0).strip() + " " + text[m.start():m.end()].strip() + " " + hm.group(0).strip())[:160]
        out.append((quote, "formal_logic",
                    {"LOGIC_VERIFY": {"variables": sorted(set(pa[1]) | set(pb[1])), "premises": [pa[0]], "conclusion": pb[0],
                                      "claimed_entailment": not bool(m.group("neg"))}}))
    return out


def _x_argument_form(text: str):
    """"If P then Q; P; therefore Q is valid" -> formal_logic.entailment (premises |= conclusion); "If P then Q; Q;
    therefore P is a valid argument" breaks honestly (affirming the consequent). Premises split on ';' or ',';
    the conclusion follows 'therefore/hence/thus/so'; every clause must parse wholly."""
    out = []
    for vm in _LOGIC_VALID.finditer(text):
        before = text[:vm.start()]
        parts = list(_LOGIC_THEREFORE.finditer(before))
        if not parts:
            continue
        th = parts[-1]
        prem_text, conc_text = before[:th.start()], before[th.end():]
        # the argument starts after the last sentence break before the premises
        prem_text = re.split(r"[.!?\n]", prem_text)[-1]
        clauses = [c.strip().strip(",;") for c in re.split(r"[;,]", prem_text) if c.strip().strip(",;")]
        if not clauses:
            continue
        premises, variables = [], set()
        ok = True
        for c in clauses:
            c2 = re.sub(r"^(?:(?:if|and|given\s+that|suppose|assume|that)\s+)+", "", c.strip(), flags=re.I)
            p = _parse_prop(c2)
            if not p:
                ok = False; break
            premises.append(p[0]); variables |= set(p[1])
        pc = _parse_prop(re.sub(r"^(?:(?:then|if|that)\s+)+", "", conc_text.strip().strip(",;"), flags=re.I))
        if not ok or not pc:
            continue
        variables |= set(pc[1])
        claimed_valid = (vm.group("kind").lower() == "valid") != bool(vm.group("neg"))
        quote = re.sub(r"\s+", " ", (prem_text + " " + before[th.start():] + text[vm.start():vm.end()]).strip())[:160]
        out.append((quote, "formal_logic",
                    {"LOGIC_VERIFY": {"variables": sorted(variables), "premises": premises, "conclusion": pc[0],
                                      "claimed_entailment": claimed_valid}}))
    return out


def _x_syllogism(text: str):
    """"All men are mortal; Socrates is a man; therefore Socrates is mortal" -> rhetoric.syllogism_validity.
    Two categorical premises and a categorical conclusion; the MAJOR premise is the one carrying the conclusion's
    predicate (the verifier infers the figure from that order); singular terms are read as universal and plurals
    singularised so the middle term matches. The "therefore" ASSERTS the conclusion follows, so a BARE syllogism
    (no explicit "is valid") is checked with claimed_valid=True — a wrong one ("…; Socrates is mortal; therefore
    Socrates is a man") then breaks honestly. An explicit "is valid / is not valid" overrides that default. Every
    structural guard (two categorical premises, a categorical All/No/Some conclusion) is kept, so it stays 0-FP:
    "I think, therefore I am" and "it was raining therefore the ground was wet" do not parse and never fire."""
    out = []
    ths = list(_LOGIC_THEREFORE.finditer(text))
    if not ths:
        return out
    th = ths[-1]                                                       # the last 'therefore' leads the conclusion
    before, after = text[:th.start()], text[th.end():].strip()
    claimed_valid = True                                               # the bare 'therefore' claims the conclusion follows
    vm = _LOGIC_VALID.search(after)
    if vm:                                                             # an explicit claim overrides the default
        claimed_valid = (vm.group("kind").lower() == "valid") != bool(vm.group("neg"))
        after = after[:vm.start()].strip()
    prem_text = re.split(r"[.!?\n]", before)[-1]
    clauses = [c.strip().strip(",;") for c in re.split(r"[;]", prem_text) if c.strip().strip(",;")]
    if len(clauses) != 2:
        clauses = [c.strip().strip(",;") for c in re.split(r"[;,]", prem_text) if c.strip().strip(",;")]
    if len(clauses) == 1:                                              # "Every man is mortal and Socrates is a man"
        clauses = [c.strip() for c in re.split(r"\s+and\s+", clauses[0]) if c.strip()]
    if len(clauses) != 2:
        return out
    cats = [_categorical(c) for c in clauses]
    conc = _categorical(after.strip().strip(",;."))
    if not all(cats) or not conc:
        return out
    cm = re.match(r"^(All|No|Some) (.+?) are (?:not )?(.+)$", conc)
    if not cm:
        return out
    conc_pred = cm.group(3)
    major = next((c for c in cats if re.search(r"\b%s\b" % re.escape(conc_pred), c)), None)
    if major is None:
        return out
    minor = cats[0] if cats[1] == major else cats[1]
    quote = re.sub(r"\s+", " ", text.strip())[:160]
    out.append((quote, "rhetoric",
                {"RHET_VERIFY": {"major_premise": major, "minor_premise": minor, "conclusion": conc,
                                 "claimed_valid": claimed_valid}}))
    return out


def _x_logic_counts(text: str):
    """The arithmetic a truth table carries: "a truth table for 3 variables has 8 rows" (2^n), "there are 16 binary
    boolean functions" (2^(2^n)), "a formula with 4 variables has 16 possible assignments"."""
    out = []
    for m in re.finditer(r"(?:truth\s+table\s+(?:for|with|of|on)\s+|formula\s+(?:with|in|over)\s+|with\s+)(\d+|" + "|".join(_NUMBER_WORDS) + r")\s+(?:propositional\s+)?variables?\b[^.\n]{0,30}?"
                         r"\b(?:has|needs|contains|requires|gives)\s+(\d[\d,]*)\s+(?:rows?|lines?|possible\s+assignments?|assignments?|interpretations?|valuations?)\b", text, re.I):
        n, claimed = _small(m.group(1)), m.group(2)
        out.append((_q(text, m), "mathematics",
                    {"mode": "equality", "params": {"expr_a": f"2**{n}", "expr_b": claimed.replace(",", ""), "claimed_literal": claimed}}))
    for m in re.finditer(r"there\s+are\s+(\d[\d,]*)\s+(?:distinct\s+|possible\s+|different\s+)?(?:(binary|unary|ternary|two-input|one-input|three-input)|(\d+)-(?:ary|place|input))\s+(?:boolean|truth|logical)\s+(?:functions?|operators?|connectives?)\b", text, re.I):
        claimed = m.group(1)
        word = (m.group(2) or "").lower()
        arity = {"unary": 1, "one-input": 1, "binary": 2, "two-input": 2, "ternary": 3, "three-input": 3}.get(word) if word else int(m.group(3))
        if not arity:
            continue
        out.append((_q(text, m), "mathematics",
                    {"mode": "equality", "params": {"expr_a": f"2**{2 ** arity}", "expr_b": claimed.replace(",", ""), "claimed_literal": claimed}}))   # no nested tower: the evaluator refuses it
    return out


def _x_named_forms(text: str):
    """"modus ponens is valid" / "affirming the consequent is a fallacy" -> formal_logic.entailment on the form's
    own schema (the catalogue above): a named form is valid exactly when its premises entail its conclusion."""
    out = []
    for m in _LOGIC_FORM_RE.finditer(text):
        form = m.group("form").lower()
        prem, conc = _LOGIC_FORMS[form]
        neg = bool(m.group("neg"))
        says_valid = bool(m.group("val") or m.group("ok"))
        claimed_valid = (says_valid != neg) if (says_valid or m.group("fal")) else None
        if claimed_valid is None:
            continue
        if m.group("fal"):
            claimed_valid = neg                             # "is a fallacy" claims invalid; "is not a fallacy" claims valid
        variables = sorted({ch for f in prem + [conc] for ch in f if ch in "pqrs"})
        out.append((_q(text, m), "formal_logic",
                    {"LOGIC_VERIFY": {"variables": variables, "premises": list(prem), "conclusion": conc,
                                      "claimed_entailment": claimed_valid, "named_form": form}}))
    return out


def _x_fallacy_kind(text: str):
    """"ad hominem is an informal fallacy" / "affirming the consequent is a formal fallacy" -> rhetoric's catalogue."""
    from .verifiers import rhetoric as _rh
    names = sorted(_rh._FALLACIES, key=len, reverse=True)
    out = []
    for m in re.finditer(r"\b(" + "|".join(re.escape(n) for n in names) + r")\b\s+(?:is|are)\s+(?P<neg>not\s+)?(?:an?\s+)?(?P<kind>formal|informal)\s+fallac(?:y|ies)\b", text, re.I):
        claimed_formal = (m.group("kind").lower() == "formal") != bool(m.group("neg"))
        out.append((_q(text, m), "rhetoric",
                    {"RHET_VERIFY": {"fallacy_name": m.group(1).lower(), "claimed_is_formal_fallacy": claimed_formal}}))
    return out


# ── LINGUISTICS AS A STRENGTH (Matt, 2026-10-08): the computable claims about words ───────────────
# What a word's letters say is arithmetic: letters, vowels, consonants, syllables and phonemes (the pronunciation
# shelf), anagrams, palindromes, edit distance, an alphabet's size, a noun's plural, a letter's rank in English.
# Routed to verifiers/wordcraft.py, which names its convention in every detail. Meaning stays with the lexicon's
# doors (define, word_study); etymology is not in the keeping and is not pretended.
_W = r"[A-Za-z][A-Za-z'\-]*"
_WQ = r"[\"'\u2018\u2019\u201c\u201d]?"
_COUNT = r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|no)"


def _count(tok: str) -> int:
    t = tok.strip().lower()
    return 0 if t == "no" else _small(t)


def _x_word_letters(text: str):
    out = []
    for m in re.finditer(r"\b(?:the\s+)?word\s+" + _WQ + "(" + _W + ")" + _WQ + r"\s+(?:has|contains)\s+" + _COUNT +
                         r"\s+(letters?|vowels?|consonants?|syllables?|phonemes?|sounds?)\b", text, re.I):
        kind = m.group(3).lower().rstrip("s")
        kind = {"letter": "letters", "vowel": "vowels", "consonant": "consonants", "syllable": "syllables",
                "phoneme": "phonemes", "sound": "phonemes"}[kind]
        out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word": m.group(1), "claimed_" + kind: _count(m.group(2))}}))
    for m in re.finditer(_WQ + r"\b(" + _W + ")" + _WQ + r"\s+is\s+an?\s+(\d+)-(letter|syllable)\s+word\b", text, re.I):
        kind = "letters" if m.group(3).lower() == "letter" else "syllables"
        out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word": m.group(1), "claimed_" + kind: int(m.group(2))}}))
    return out


def _x_anagram(text: str):
    out = []
    for m in re.finditer(_WQ + r"\b(" + _W + ")" + _WQ + r"\s+is\s+(not\s+)?an\s+anagram\s+of\s+" + _WQ + "(" + _W + ")" + _WQ, text, re.I):
        out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word_a": m.group(1), "word_b": m.group(3),
                                                                "claimed_anagram": not bool(m.group(2))}}))
    return out


def _x_palindrome(text: str):
    out = []
    for m in re.finditer(_WQ + r"\b(" + _W + ")" + _WQ + r"\s+is\s+(not\s+)?a\s+palindrome\b", text, re.I):
        if m.group(1).lower() in ("it", "this", "that", "which", "word", "name"):
            continue
        out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word": m.group(1), "claimed_palindrome": not bool(m.group(2))}}))
    return out


def _x_edit_distance(text: str):
    out = []
    for m in re.finditer(_WQ + r"\b(" + _W + ")" + _WQ + r"\s+and\s+" + _WQ + "(" + _W + ")" + _WQ +
                         r"\s+are\s+" + _COUNT + r"\s+(?:edits?|letters?|changes?|steps?)\s+apart\b", text, re.I):
        out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word_a": m.group(1), "word_b": m.group(2),
                                                                "claimed_edit_distance": _count(m.group(3))}}))
    for m in re.finditer(r"\b(?:the\s+)?(?:edit|levenshtein)\s+distance\s+(?:between|from)\s+" + _WQ + "(" + _W + ")" + _WQ +
                         r"\s+(?:and|to)\s+" + _WQ + "(" + _W + ")" + _WQ + r"\s+(?:is|=|equals)\s+" + _COUNT + r"\b", text, re.I):
        out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word_a": m.group(1), "word_b": m.group(2),
                                                                "claimed_edit_distance": _count(m.group(3))}}))
    return out


def _x_alphabet(text: str):
    from .verifiers import wordcraft as _wc
    names = "|".join(re.escape(k) for k in sorted(_wc.ALPHABETS, key=len, reverse=True))
    out = []
    for m in re.finditer(r"\b(?:the\s+)?(" + names + r")\s+alphabet\s+(?:has|contains|consists\s+of)\s+" + _COUNT + r"\s+letters?\b", text, re.I):
        out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"alphabet": m.group(1).lower(), "claimed_alphabet_letters": _count(m.group(2))}}))
    for m in re.finditer(r"\b(" + names + r")\s+has\s+" + _COUNT + r"\s+letters?\b(?:\s+in\s+(?:its|the)\s+alphabet)?", text, re.I):
        out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"alphabet": m.group(1).lower(), "claimed_alphabet_letters": _count(m.group(2))}}))
    return out


def _x_plural(text: str):
    out = []
    for m in re.finditer(r"\bthe\s+plural\s+(?:form\s+)?of\s+" + _WQ + "(" + _W + ")" + _WQ + r"\s+is\s+" + _WQ + "(" + _W + ")" + _WQ, text, re.I):
        out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"singular": m.group(1), "claimed_plural": m.group(2)}}))
    return out


_RANK_WORDS = {"most": 1, "second most": 2, "third most": 3, "fourth most": 4, "fifth most": 5, "least": 26, "second least": 25}


def _x_letter_rank(text: str):
    out = []
    ranks = "|".join(re.escape(k) for k in sorted(_RANK_WORDS, key=len, reverse=True))
    for m in re.finditer(r"\b(?:the\s+letter\s+)?" + _WQ + r"\b([A-Za-z])\b" + _WQ + r"\s+is\s+the\s+(" + ranks + r")\s+(?:common|frequent)\s+letter\s+in\s+(?:written\s+)?English\b", text, re.I):
        out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"letter": m.group(1).lower(), "claimed_rank": _RANK_WORDS[m.group(2).lower()]}}))
    for m in re.finditer(r"\bthe\s+(" + ranks + r")\s+(?:common|frequent)\s+letter\s+in\s+(?:written\s+)?English\s+is\s+" + _WQ + r"([A-Za-z])\b", text, re.I):
        out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"letter": m.group(2).lower(), "claimed_rank": _RANK_WORDS[m.group(1).lower()]}}))
    return out


# ── PHONICS + ETYMOLOGY (Matt, 2026-10-08: "Etymology and phonics") ─────────────────────────────────
# Sound, read off the keeping's pronunciation shelf (CMU, ARPABET): rhymes, homophones, the stressed syllable,
# silent letters, the long/short vowel names of phonics, the first and last sounds. Origin, read off the
# etymology shelf (Webster 1913, public domain): "X comes from Latin", "the Latin word salarium", "the Latin
# word for little mouse", "of Greek origin". Routed to verifiers/wordcraft.py, which names its convention and
# declines what the shelf cannot tell (a word not held, a vowel letter's silence, a comparison that is not a
# derivation) rather than guessing.
_TW = r"(?:the\s+)?(?:words?\s+|names?\s+|terms?\s+)?"
_PRON_STOP = frozenset({"it", "this", "that", "which", "word", "name", "term", "he", "she", "they", "we", "you", "i",
                        "one", "who", "what", "each", "either", "neither", "both", "all", "something", "nothing", "everything"})
_ORD = {"first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3, "fourth": 4, "4th": 4, "fifth": 5, "5th": 5,
        "sixth": 6, "6th": 6, "last": -1, "final": -1, "penultimate": -2, "second-to-last": -2, "second to last": -2,
        "next-to-last": -2, "next to last": -2}
_ORD_RE = "|".join(re.escape(k) for k in sorted(_ORD, key=len, reverse=True))
_NEG_DOES = r"(?:(?P<neg>does\s+not|doesn't|did\s+not|didn't|cannot|can't)\s+)?"


def _wd(m, key="w"):
    """The word a pattern named, or None when it is a stop word (a pronoun, 'word', 'it')."""
    w = m.group(key)
    return None if (not w or w.lower() in _PRON_STOP) else w


def _x_rhyme(text: str):
    out = []
    for m in re.finditer(_TW + _WQ + r"\b(?P<a>" + _W + r")" + _WQ + r"\s+" + _NEG_DOES + r"rhymes?\s+with\s+" + _WQ + r"(?P<b>" + _W + r")" + _WQ, text, re.I):
        a = _wd(m, "a")
        if a:
            out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word_a": a, "word_b": m.group("b"), "claimed_rhyme": not bool(m.group("neg"))}}))
    for m in re.finditer(_TW + _WQ + r"\b(?P<a>" + _W + r")" + _WQ + r"\s+and\s+" + _WQ + r"(?P<b>" + _W + r")" + _WQ + r"\s+(?:(?P<neg>do\s+not|don't)\s+)?rhyme\b", text, re.I):
        a = _wd(m, "a")
        if a:
            out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word_a": a, "word_b": m.group("b"), "claimed_rhyme": not bool(m.group("neg"))}}))
    for m in re.finditer(_TW + _WQ + r"\b(?P<a>" + _W + r")" + _WQ + r"\s+is\s+(?P<neg>not\s+)?a\s+(?:perfect\s+|true\s+|full\s+)?rhyme\s+(?:for|with|of)\s+" + _WQ + r"(?P<b>" + _W + r")" + _WQ, text, re.I):
        a = _wd(m, "a")
        if a:
            out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word_a": a, "word_b": m.group("b"), "claimed_rhyme": not bool(m.group("neg"))}}))
    return out


def _x_homophone(text: str):
    out = []
    pair = _TW + _WQ + r"\b(?P<a>" + _W + r")" + _WQ + r"\s+and\s+" + _WQ + r"(?P<b>" + _W + r")" + _WQ
    for m in re.finditer(pair + r"\s+are\s+(?P<neg>not\s+)?homophones\b", text, re.I):
        a = _wd(m, "a")
        if a:
            out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word_a": a, "word_b": m.group("b"), "claimed_homophone": not bool(m.group("neg"))}}))
    for m in re.finditer(_TW + _WQ + r"\b(?P<a>" + _W + r")" + _WQ + r"\s+is\s+(?P<neg>not\s+)?a\s+homophone\s+(?:of|for|with)\s+" + _WQ + r"(?P<b>" + _W + r")" + _WQ, text, re.I):
        a = _wd(m, "a")
        if a:
            out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word_a": a, "word_b": m.group("b"), "claimed_homophone": not bool(m.group("neg"))}}))
    for m in re.finditer(pair + r"\s+(?:(?P<neg>do\s+not|don't)\s+)?(?:sound|are\s+pronounced|are\s+said)\s+(?P<how>the\s+same|alike|identically|differently)\b", text, re.I):
        a = _wd(m, "a")
        if a:
            same = m.group("how").lower() != "differently"
            out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word_a": a, "word_b": m.group("b"), "claimed_homophone": same != bool(m.group("neg"))}}))
    for m in re.finditer(_TW + _WQ + r"\b(?P<a>" + _W + r")" + _WQ + r"\s+(?:is\s+pronounced|sounds)\s+(?:the\s+same\s+as|exactly\s+like|identically\s+to|identical\s+to)\s+" + _WQ + r"(?P<b>" + _W + r")" + _WQ, text, re.I):
        a = _wd(m, "a")
        if a:
            out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word_a": a, "word_b": m.group("b"), "claimed_homophone": True}}))
    return out


def _x_stress(text: str):
    out = []
    syl = r"(?:the\s+|its\s+)?(?P<ord>" + _ORD_RE + r")\s+syllable\b"
    pats = [
        _TW + _WQ + r"\b(?P<w>" + _W + r")" + _WQ + r"\s+(?:is|gets|was)\s+(?:stressed|accented|emphasized)\s+on\s+" + syl,
        r"\b(?:the\s+)?(?:stress|accent|emphasis|primary\s+stress)\s+(?:in|of|on)\s+" + _TW + _WQ + r"(?P<w>" + _W + r")" + _WQ + r"\s+(?:falls|is|lies|goes|comes)\s+on\s+" + syl,
        _TW + _WQ + r"\b(?P<w>" + _W + r")" + _WQ + r"\s+(?:has|carries|takes|puts)\s+(?:its\s+|the\s+)?(?:primary\s+|main\s+)?(?:stress|accent|emphasis)\s+on\s+" + syl,
        r"\bin\s+" + _TW + _WQ + r"(?P<w>" + _W + r")" + _WQ + r",?\s+the\s+(?:stress|accent|emphasis)\s+(?:is|falls|lies)\s+on\s+" + syl,
        r"\bthe\s+(?P<ord>" + _ORD_RE + r")\s+syllable\s+of\s+" + _TW + _WQ + r"(?P<w>" + _W + r")" + _WQ + r"\s+(?:is|gets|carries\s+the)\s+(?:stressed|accented|stress|emphasized)\b",
    ]
    for pat in pats:
        for m in re.finditer(pat, text, re.I):
            w = _wd(m)
            if w:
                out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word": w, "claimed_stress_syllable": _ORD[m.group("ord").lower()]}}))
    return out


def _x_silent_letter(text: str):
    out = []
    L = _WQ + r"(?P<l>[A-Za-z])" + _WQ
    for m in re.finditer(r"\bthe\s+(?:letter\s+)?" + L + r"\s+in\s+" + _TW + _WQ + r"(?P<w>" + _W + r")" + _WQ + r"\s+(?:is|stays|remains)\s+(?P<neg>not\s+)?(?P<how>silent|pronounced|sounded|voiced|unpronounced|unsounded)\b", text, re.I):
        w = _wd(m)
        if w:
            silent = m.group("how").lower() in ("silent", "unpronounced", "unsounded")
            out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word": w, "letter": m.group("l").lower(), "claimed_silent": silent != bool(m.group("neg"))}}))
    for m in re.finditer(_TW + _WQ + r"\b(?P<w>" + _W + r")" + _WQ + r"\s+(?:has|contains|is\s+spelled\s+with|is\s+written\s+with|begins\s+with|starts\s+with|ends\s+with)\s+a\s+silent\s+" + L + r"(?![A-Za-z])", text, re.I):
        w = _wd(m)
        if w:
            out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word": w, "letter": m.group("l").lower(), "claimed_silent": True}}))
    for m in re.finditer(r"\bthe\s+(?:letter\s+)?" + L + r"\s+(?:is|stays)\s+(?P<neg>not\s+)?(?P<how>silent|pronounced|sounded)\s+in\s+" + _TW + _WQ + r"(?P<w>" + _W + r")" + _WQ, text, re.I):
        w = _wd(m)
        if w:
            silent = m.group("how").lower() == "silent"
            out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word": w, "letter": m.group("l").lower(), "claimed_silent": silent != bool(m.group("neg"))}}))
    return out


def _x_vowel_sound(text: str):
    from .verifiers import wordcraft as _wc
    snd = r"(?P<snd>" + "|".join(re.escape(k) for k in sorted(_wc.VOWEL_SOUNDS, key=len, reverse=True)) + r")"
    out = []
    for m in re.finditer(_TW + _WQ + r"\b(?P<w>" + _W + r")" + _WQ + r"\s+(?:has|contains|uses|makes|carries)\s+(?:(?P<neg>no|not\s+a|not\s+the)\s+|(?:a|an|the)\s+)?" + snd + r"(?:\s+(?:vowel\s+sound|vowel|sound))?\b", text, re.I):
        w = _wd(m)
        if w:
            out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word": w, "claimed_vowel_sound": m.group("snd").lower(), "claimed": not bool(m.group("neg"))}}))
    for m in re.finditer(_TW + _WQ + r"\b(?P<w>" + _W + r")" + _WQ + r"\s+(?:does\s+not|doesn't)\s+(?:have|contain|use|make)\s+(?:a|an|the)\s+" + snd + r"(?:\s+(?:vowel\s+sound|vowel|sound))?\b", text, re.I):
        w = _wd(m)
        if w:
            out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word": w, "claimed_vowel_sound": m.group("snd").lower(), "claimed": False}}))
    for m in re.finditer(r"\bthe\s+(?:letter\s+)?" + _WQ + r"(?P<v>[aeiou])" + _WQ + r"\s+in\s+" + _TW + _WQ + r"(?P<w>" + _W + r")" + _WQ + r"\s+(?:is|sounds|makes|says|has|takes)\s+(?:a\s+|the\s+|its\s+)?(?P<neg>not\s+)?(?P<ls>long|short)(?:\s+(?:sound|vowel|vowel\s+sound))?\b", text, re.I):
        w = _wd(m)
        if w:
            out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word": w, "claimed_vowel_sound": f"{m.group('ls').lower()} {m.group('v').lower()}", "claimed": not bool(m.group("neg"))}}))
    for m in re.finditer(r"\bthe\s+vowel(?:\s+sound)?\s+in\s+" + _TW + _WQ + r"(?P<w>" + _W + r")" + _WQ + r"\s+is\s+(?:a\s+|an\s+|the\s+)?" + snd + r"\b", text, re.I):
        w = _wd(m)
        if w:
            out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word": w, "claimed_vowel_sound": m.group("snd").lower(), "claimed": True}}))
    return out


def _x_edge_sound(text: str):
    from .verifiers import wordcraft as _wc
    snd = r"/?(?P<snd>" + "|".join(re.escape(k) for k in sorted(_wc.SOUND_NAMES, key=len, reverse=True)) + r")/?"
    first = {"starts", "begins", "opens", "first", "initial", "opening"}
    out = []
    for m in re.finditer(_TW + _WQ + r"\b(?P<w>" + _W + r")" + _WQ + r"\s+" + _NEG_DOES + r"(?P<pos>starts?|begins?|opens?|ends?|finish(?:es)?|closes?)\s+with\s+(?:a|an|the)\s+" + snd + r"\s+sound\b", text, re.I):
        w = _wd(m)
        if w:
            pos = "first" if m.group("pos").lower().rstrip("s") in {p.rstrip("s") for p in first} or m.group("pos").lower() in first else "last"
            out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word": w, "claimed_edge_sound": m.group("snd").lower(), "position": pos, "claimed": not bool(m.group("neg"))}}))
    for m in re.finditer(r"\bthe\s+(?P<pos>first|initial|opening|last|final|closing)\s+sound\s+(?:in|of)\s+" + _TW + _WQ + r"(?P<w>" + _W + r")" + _WQ + r"\s+is\s+(?P<neg>not\s+)?(?:a\s+|an\s+|the\s+)?" + snd + r"(?:\s+sound)?\b", text, re.I):
        w = _wd(m)
        if w:
            pos = "first" if m.group("pos").lower() in first else "last"
            out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word": w, "claimed_edge_sound": m.group("snd").lower(), "position": pos, "claimed": not bool(m.group("neg"))}}))
    for m in re.finditer(_TW + _WQ + r"\b(?P<w>" + _W + r")" + _WQ + r"\s+(?P<pos>starts|begins|ends)\s+with\s+the\s+sound\s+" + snd + r"\b", text, re.I):
        w = _wd(m)
        if w:
            pos = "first" if m.group("pos").lower() in first else "last"
            out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": {"word": w, "claimed_edge_sound": m.group("snd").lower(), "position": pos, "claimed": True}}))
    return out


_SRC_STOP = frozenset({"and", "or", "in", "the", "a", "an", "which", "meaning", "that", "where", "via", "through", "by",
                       "into", "as", "with", "during", "around", "about", "but", "so", "because", "while", "when", "it",
                       "its", "not", "also", "originally", "literally", "itself", "to", "from", "then", "ultimately",
                       "rather", "language", "speakers", "times", "roots", "root", "word", "words", "form", "forms"})


def _x_etymology(text: str):
    from .verifiers import wordcraft as _wc
    langs = r"(?P<lang>" + "|".join(re.escape(k) for k in sorted(_wc.LANG_ABBR, key=len, reverse=True)) + r")"
    head = _TW + _WQ + r"\b(?P<w>" + _W + r")" + _WQ + r"\s+"
    src = r"(?:\s+(?:word|noun|verb|root|term|name|form|adjective))?(?:\s+for\s+(?P<gloss>[A-Za-z][A-Za-z' \-]{1,40}?)(?=[.,;:!?)]|\s+(?:and|or|which|that|because|via|through|by|in|meaning|but)\b|$)|\s+" + _WQ + r"(?P<src>[A-Za-z][A-Za-z\-]{2,})" + _WQ + r")?"
    neg = r"(?:(?P<neg>does\s+not|doesn't|did\s+not|didn't|is\s+not|isn't|was\s+not|wasn't)\s+)?"
    verbs = (r"(?:comes?|came|derives?|derived|descends?|descended|originates?|originated|stems?|stemmed|hails|is\s+derived|was\s+derived|"
             r"is\s+borrowed|was\s+borrowed|is\s+taken|was\s+taken|was\s+adopted|is\s+adopted|entered\s+english|came\s+into\s+english)")
    frm = r"\s+(?:(?:to\s+us\s+|into\s+english\s+|ultimately\s+|originally\s+|directly\s+)?from|out\s+of|via|through)\s+(?:the\s+|an?\s+)?"
    pats = [
        head + neg + verbs + frm + langs + src,
        head + r"(?:is|was)\s+(?P<neg>not\s+)?(?:of|from)\s+(?:(?:ultimately|originally|partly|purely)\s+)?" + langs + r"\s+(?:origin|derivation|extraction|descent|stock|provenance)\b",
        head + r"(?:is|was)\s+(?P<neg>not\s+)?" + langs + r"\s+in\s+origin\b",
        head + r"(?:is|was)\s+(?P<neg>not\s+)?(?:a|an)\s+" + langs + r"\s+(?:word|loanword|loan-word|borrowing|loan|term)\b",
        head + r"(?:is|was)\s+(?P<neg>not\s+)?(?:a\s+)?loan(?:word|-word)?\s+from\s+(?:the\s+)?" + langs + r"\b",
        head + r"has\s+(?:a\s+|an\s+|its\s+)?(?P<neg>no\s+)?" + langs + r"\s+(?:origin|root|roots|etymology|ancestry)\b",
        head + r"(?:traces|goes|dates)\s+back\s+to\s+(?:the\s+|an?\s+)?" + langs + src,
        r"\b(?:the\s+)?(?:origin|etymology|root|source)\s+of\s+" + _TW + _WQ + r"(?P<w>" + _W + r")" + _WQ + r"\s+(?:is|was|lies\s+in)\s+(?:the\s+)?" + langs + src,
        r"\b(?:the\s+)?" + langs + r"\s+(?:word\s+|root\s+|noun\s+|verb\s+)?" + _WQ + r"(?P<src>[A-Za-z][A-Za-z\-]{2,})" + _WQ + r"\s+(?:gives|gave|yields|yielded|produced|became)\s+(?:us\s+)?(?:the\s+)?(?:english\s+)?(?:word\s+)?" + _WQ + r"(?P<w>" + _W + r")" + _WQ,
    ]
    out = []
    for pat in pats:
        for m in re.finditer(pat, text, re.I):
            w = _wd(m)
            if not w or w.lower() in _wc.LANG_ABBR:
                continue
            spec = {"word": w, "claimed_language": re.sub(r"\s+", " ", m.group("lang").lower()),
                    "claimed_origin": not bool(m.groupdict().get("neg"))}
            sw = m.groupdict().get("src")
            if sw and sw.lower() not in _SRC_STOP and sw.lower() not in _wc.LANG_ABBR:
                spec["claimed_source_word"] = sw
            gl = m.groupdict().get("gloss")
            if gl and gl.strip():
                spec["claimed_gloss"] = gl.strip()
            out.append((_q(text, m), "wordcraft", {"WORD_VERIFY": spec}))
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


def _parse_int_poly(s: str):
    """A univariate integer polynomial in x -> coefficients highest-degree-first, or None. Accepts
    "x^2 - 5x + 6", "2x^3 - x - 3", "-x^2 + 4". Conservative: integer coefficients only, the one
    variable x, no division, no other letters — anything else returns None (held, never a wrong parse)."""
    t = (s or "").strip().lower().replace(" ", "").replace("**", "^").replace("*", "")
    if not t or "x" not in t or "/" in t or re.search(r"[a-wyz]", t):   # only 'x' may appear as a letter
        return None
    powmap: Dict[int, int] = {}
    for term in re.findall(r"[+-]?[^+-]+", t):
        if term in ("+", "-", ""):
            continue
        m = re.fullmatch(r"([+-]?)(\d*)x(?:\^(\d+))?", term)
        if m:
            coef = (int(m.group(2)) if m.group(2) else 1) * (-1 if m.group(1) == "-" else 1)
            power = int(m.group(3)) if m.group(3) else 1
            powmap[power] = powmap.get(power, 0) + coef
            continue
        m = re.fullmatch(r"([+-]?\d+)", term)                           # a constant term
        if m:
            powmap[0] = powmap.get(0, 0) + int(m.group(1))
            continue
        return None                                                     # an unparseable term -> not a clean poly
    if not powmap or max(powmap) < 1:
        return None
    deg = max(powmap)
    return [powmap.get(p, 0) for p in range(deg, -1, -1)]


_RR_NUM = re.compile(r"-?\d+(?:/\d+)?")
_RR_SET = re.compile(r"\b(?:the\s+)?rational\s+roots?\s+of\s+(.+?)\s+(?:are|is|=|:)\s+(.+?)[.?!]?\s*$", re.I)
_RR_ONE = re.compile(r"\b(-?\d+(?:/\d+)?)\s+is\s+(?:an?\s+)?roots?\s+of\s+(.+?)[.?!]?\s*$", re.I)


def _x_rational_roots(text: str):
    """"the rational roots of x^2 - 5x + 6 are 2 and 3" -> polynomial.rational_roots (the COMPLETE set,
    by the Rational Root Theorem); "3/2 is a root of 2x^2 - x - 3" -> polynomial.root. The polynomial
    must parse as a clean integer polynomial in x, or nothing extracts (0-FP)."""
    out = []
    for m in _RR_SET.finditer(text):
        coeffs = _parse_int_poly(m.group(1))
        if not coeffs:
            continue
        roots = _RR_NUM.findall(m.group(2))
        if not roots and not re.search(r"\bnone\b|\bno\s+rational", m.group(2), re.I):
            continue                                                    # "are 2 and 3" needs numbers; "are none" is the empty set
        out.append((_q(text, m), "polynomial",
                    {"POLY_VERIFY": {"coeffs": coeffs, "claimed_rational_roots": roots}}))
    for m in _RR_ONE.finditer(text):
        coeffs = _parse_int_poly(m.group(2))
        if coeffs:
            out.append((_q(text, m), "polynomial",
                        {"POLY_VERIFY": {"coeffs": coeffs, "claimed_root": m.group(1)}}))
    return out


_SUB_PHASE = re.compile(
    r"\bthe\s+(?P<prop>boiling|melting|freezing)\s+point\s+of\s+(?P<sub>[a-z][a-z ]{1,28}?)\s+"
    r"(?:is|are|=|equals?)\s+(?P<num>-?\d+(?:\.\d+)?)\s*(?:°|º|deg(?:rees?)?)?\s*(?:c\b|celsius|centigrade)\b", re.I)
_SUB_FORMULA_EXPLICIT = re.compile(
    r"\bthe\s+(?:chemical\s+)?formula\s+(?:for|of)\s+(?P<sub>[a-z][a-z ]{1,28}?)\s+(?:is|=)\s+(?P<f>(?:[A-Z][a-z]?\d*)+)\b")
_SUB_FORMULA_BARE = re.compile(
    r"\b(?P<sub>[a-z][a-z ]{1,28}?)\s+(?:is|=|has\s+the\s+formula)\s+(?P<f>(?:[A-Z][a-z]?\d*)+)\b")


def _x_substance(text: str):
    """"the boiling point of water is 100 C" -> chemistry.phase_point; "water is H2O" / "the formula for
    water is H2O" -> chemistry.formula. The bare "X is <formula>" fires ONLY when X is a known substance
    (so "it is OK" is never a formula claim); the explicit "formula of X" and the phase anchor are strong
    enough to fire regardless, and the verifier declines any substance it does not hold (0-FP)."""
    from .verifiers import chemistry as _chem
    out, seen = [], set()
    for m in _SUB_PHASE.finditer(text):
        sub = m.group("sub").strip()
        out.append((_q(text, m), "chemistry",
                    {"CHEM_VERIFY": {"substance": sub, "property": m.group("prop").lower(),
                                     "claimed_c": float(m.group("num")), "claimed_literal": m.group("num")}}))
    for m in _SUB_FORMULA_EXPLICIT.finditer(text):
        sub = m.group("sub").strip()
        out.append((_q(text, m), "chemistry", {"CHEM_VERIFY": {"name": sub, "claimed_formula": m.group("f")}}))
        seen.add(sub.lower())
    for m in _SUB_FORMULA_BARE.finditer(text):
        sub = m.group("sub").strip()
        if sub.lower() in seen:
            continue
        _, rec = _chem.substance(sub)                      # bare "X is <formula>" only for a KNOWN substance
        if rec is not None:
            out.append((_q(text, m), "chemistry", {"CHEM_VERIFY": {"name": sub, "claimed_formula": m.group("f")}}))
    return out


# ── THE REACH (issue #11, 2026-10-16): verifiers no sentence could reach ─────────────────────────
# Thirteen domain verifiers were built, registered and pinned by their own tests, and no extractor ever
# handed one of them a plain claim — a person's sentence stopped at the door. Below, the same discipline
# as the logic front door: a strict regex anchored to a WHOLE clause, every number parsed (never guessed),
# units carried into the verifier's own key, and nothing extracted when any required part is missing.
# Two domains are left unreached on purpose: pressure_fighting takes a 14-field closed-set observation
# and retrieval takes id lists — neither is a sentence, and a miss stays a miss.
import json as _json

_RN = r"-?\d[\d,]*(?:\.\d+)?"                        # a signed plain number, commas allowed
_IS = r"(?:is|equals|=|comes\s+to)"


def _fl(s: str) -> float:
    return float(str(s).replace(",", "").strip())


def _cnt(tok: str) -> int:
    """'four' / '4' / 'no' / 'zero' -> an int."""
    t = tok.strip().lower()
    if t in ("no", "zero", "none"):
        return 0
    return _NUMBER_WORDS.index(t) + 1 if t in _NUMBER_WORDS else int(t)


# ── linear algebra: a bracketed literal parsed WHOLE ───────────────────────────────────────────────
_LA_N = r"-?\d+(?:\.\d+)?"
_LA_ROW = r"\[\s*" + _LA_N + r"(?:\s*,\s*" + _LA_N + r")*\s*\]"
_LA_MAT = r"\[\s*" + _LA_ROW + r"(?:\s*,\s*" + _LA_ROW + r")*\s*\]"
_LA_DEG = r"\s*(?:°|degrees?|deg)\b"
_LA_DET = re.compile(r"(?:the\s+)?(?:determinant\s+of\s+(?:the\s+)?(?:matrix\s+)?|det\s*\(?\s*)(?P<m>" + _LA_MAT +
                     r")\s*\)?\s*" + _IS + r"\s*" + _HEDGE + r"(?P<c>" + _RN + r")", re.I)
_LA_TR = re.compile(r"(?:the\s+)?(?:trace\s+of\s+(?:the\s+)?(?:matrix\s+)?|tr\s*\(?\s*)(?P<m>" + _LA_MAT +
                    r")\s*\)?\s*" + _IS + r"\s*" + _HEDGE + r"(?P<c>" + _RN + r")", re.I)
_LA_DOT = re.compile(r"(?:(?:the\s+)?dot\s+product\s+of\s+(?P<a>" + _LA_ROW + r")\s+and\s+(?P<b>" + _LA_ROW +
                     r")|(?P<a2>" + _LA_ROW + r")\s*[·⋅]\s*(?P<b2>" + _LA_ROW + r"))\s*" + _IS + r"\s*" + _HEDGE +
                     r"(?P<c>" + _RN + r")", re.I)
_LA_MAG = re.compile(r"(?:(?:the\s+)?(?:magnitude|norm|length)\s+of\s+(?:the\s+)?(?:vector\s+)?(?P<v>" + _LA_ROW +
                     r")|\|\s*(?P<v2>" + _LA_ROW + r")\s*\|)\s*" + _IS + r"\s*" + _HEDGE + r"(?P<c>" + _RN + r")", re.I)
_LA_ANG = re.compile(r"(?:the\s+)?angle\s+between\s+(?:the\s+)?(?:vectors?\s+)?(?P<a>" + _LA_ROW + r")\s+and\s+(?P<b>" +
                     _LA_ROW + r")\s+" + _IS + r"\s*" + _HEDGE + r"(?P<c>" + _RN + r")" + _LA_DEG, re.I)
_LA_ID = re.compile(r"(?:the\s+)?(?:(?P<n>\d{1,2})\s*[x×]\s*(?P<n2>\d{1,2})\s+identity\s+matrix\s+has\s+(?:a\s+)?"
                    r"(?P<k>trace|determinant)\s+(?:of\s+)?|(?P<k2>trace|determinant)\s+of\s+(?:the\s+)?(?P<n3>\d{1,2})"
                    r"\s*[x×]\s*(?P<n4>\d{1,2})\s+identity\s+matrix\s+" + _IS + r"\s+)" + _HEDGE + r"(?P<c>" + _RN + r")", re.I)


def _la_load(span: str):
    try:
        return _json.loads(re.sub(r"\s+", "", span))
    except ValueError:
        return None


def _la_square(m) -> bool:
    return bool(isinstance(m, list) and m and all(isinstance(r, list) and len(r) == len(m) for r in m))


def _x_linear_algebra(text: str):
    """"the determinant of [[1,2],[3,4]] is -2" / "the trace of [[1,2],[3,4]] is 5" / "the dot product of [1,2,3]
    and [4,5,6] is 32" / "the magnitude of [3,4] is 5" / "the angle between [1,0] and [0,1] is 90 degrees" /
    "the 3x3 identity matrix has trace 3" -> linear_algebra (LIN_VERIFY). A matrix or vector is a bracketed
    literal parsed whole; a ragged or non-square matrix, or two vectors of different length, is not extracted."""
    out = []
    for m in _LA_DET.finditer(text):
        mat = _la_load(m.group("m"))
        if _la_square(mat):
            out.append((_q(text, m), "linear_algebra",
                        {"LIN_VERIFY": {"matrix": mat, "claimed_determinant": _fl(m.group("c")), "claimed_literal": m.group("c")}}))
    for m in _LA_TR.finditer(text):
        mat = _la_load(m.group("m"))
        if _la_square(mat):
            out.append((_q(text, m), "linear_algebra",
                        {"LIN_VERIFY": {"matrix": mat, "claimed_trace": _fl(m.group("c")), "claimed_literal": m.group("c")}}))
    for m in _LA_DOT.finditer(text):
        a, b = _la_load(m.group("a") or m.group("a2")), _la_load(m.group("b") or m.group("b2"))
        if isinstance(a, list) and isinstance(b, list) and len(a) == len(b) and a:
            out.append((_q(text, m), "linear_algebra",
                        {"LIN_VERIFY": {"vec_a": a, "vec_b": b, "claimed_dot_product": _fl(m.group("c")), "claimed_literal": m.group("c")}}))
    for m in _LA_MAG.finditer(text):
        v = _la_load(m.group("v") or m.group("v2"))
        if isinstance(v, list) and v:
            out.append((_q(text, m), "linear_algebra",
                        {"LIN_VERIFY": {"vec": v, "claimed_magnitude": _fl(m.group("c")), "claimed_literal": m.group("c")}}))
    for m in _LA_ANG.finditer(text):
        a, b = _la_load(m.group("a")), _la_load(m.group("b"))
        if isinstance(a, list) and isinstance(b, list) and len(a) == len(b) and a:
            out.append((_q(text, m), "linear_algebra",
                        {"LIN_VERIFY": {"vec_a": a, "vec_b": b, "claimed_angle_deg": _fl(m.group("c")), "claimed_literal": m.group("c")}}))
    for m in _LA_ID.finditer(text):
        n, n2 = int(m.group("n") or m.group("n3")), int(m.group("n2") or m.group("n4"))
        if n != n2 or not 1 <= n <= 12:
            continue
        ident = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
        key = "claimed_" + (m.group("k") or m.group("k2")).lower()
        out.append((_q(text, m), "linear_algebra",
                    {"LIN_VERIFY": {"matrix": ident, key: _fl(m.group("c")), "claimed_literal": m.group("c")}}))
    return out


# ── chess: a FEN is unmistakable, a move is coordinate notation ────────────────────────────────────
_CH_FEN = r"(?P<fen>(?-i:(?:[rnbqkpRNBQKP1-8]{1,8}/){7}[rnbqkpRNBQKP1-8]{1,8}\s+[wb]\s+(?:-|K?Q?k?q?)\s+(?:-|[a-h][36])\s+\d+\s+\d+))"
_CH_MOVE = r"(?P<move>[a-h][1-8][a-h][1-8][qrbn]?)"
_CH_START = r"(?:the\s+)?(?:starting|initial|opening|start)\s+position"
_CH_LEG = r"is\s+(?P<neg>not\s+)?(?:an?\s+)?(?P<leg>legal|illegal)(?:\s+move)?\b"
_CH_LEGAL_A = re.compile(r"(?:in|from)\s+" + _CH_START + r",?\s+(?:the\s+move\s+)?" + _CH_MOVE + r"\s+" + _CH_LEG, re.I)
_CH_LEGAL_B = re.compile(r"(?:the\s+move\s+)?" + _CH_MOVE + r"\s+" + _CH_LEG + r"\s+(?:in|from)\s+" + _CH_START + r"\b", re.I)
_CH_LEGAL_FEN = re.compile(r"(?:in\s+)?(?:the\s+)?position\s+" + _CH_FEN + r",?\s+(?:the\s+move\s+)?" + _CH_MOVE + r"\s+" + _CH_LEG, re.I)
_CH_STATE = re.compile(r"(?:(?:in\s+)?(?:the\s+)?position\s+)?" + _CH_FEN +
                       r"\s+is\s+(?P<neg>not\s+)?(?:(?:a|in)\s+)?(?P<kind>checkmate|stalemate|check|mate)\b", re.I)


def _x_chess(text: str):
    """"in the starting position, e2e4 is a legal move" / "e2e5 is not a legal move from the starting position" /
    "in the position <FEN>, g1f3 is legal" / "the position <FEN> is checkmate" -> chess (CHESS_VERIFY, the
    PERFT-proven rules engine). A move is coordinate notation only; a FEN must carry all six fields."""
    from .chess import START_FEN                     # the engine itself runs inside the verifier
    out = []
    for rx, fen_from in ((_CH_LEGAL_A, None), (_CH_LEGAL_B, None), (_CH_LEGAL_FEN, "fen")):
        for m in rx.finditer(text):
            claimed = (m.group("leg").lower() == "legal") != bool(m.group("neg"))
            fen = m.group("fen") if fen_from else START_FEN
            out.append((_q(text, m), "chess",
                        {"CHESS_VERIFY": {"fen": re.sub(r"\s+", " ", fen), "claim": "legal_move",
                                          "move": m.group("move").lower(), "claimed": claimed}}))
    for m in _CH_STATE.finditer(text):
        kind = m.group("kind").lower()
        kind = "checkmate" if kind == "mate" else kind
        out.append((_q(text, m), "chess",
                    {"CHESS_VERIFY": {"fen": re.sub(r"\s+", " ", m.group("fen")), "claim": kind,
                                      "claimed": not bool(m.group("neg"))}}))
    return out


# ── condensed matter: the named solid-state constants and the quantum Hall plateau ─────────────────
_CM_OHM = r"\s*(?P<u>k(?:ilo-?)?ohms?|kΩ|ohms?|Ω)\b"
_CM_VK = re.compile(r"(?:the\s+)?(?:von\s+klitzing\s+constant|resistance\s+quantum|quantum\s+of\s+resistance)"
                    r"(?:\s*,?\s*(?:R_?K|h\s*/\s*e[²^2]*)\s*,?)?\s+" + _IS + r"\s*" + _HEDGE + r"(?P<c>" + _RN + r")" + _CM_OHM, re.I)
_CM_KJ = re.compile(r"(?:the\s+)?josephson\s+constant(?:\s*,?\s*(?:K_?J|2\s*e\s*/\s*h)\s*,?)?\s+" + _IS + r"\s*" + _HEDGE +
                    r"(?P<c>" + _RN + r")\s*(?P<u>(?-i:[kMGT]?Hz))\s*(?:/|per)\s*(?:V|volt)\b", re.I)
_CM_JMOLK = r"\s*(?:J|joules?)\s*(?:/|per)?\s*\(?\s*mol(?:e)?\s*(?:[·\*\s]|/|per)?\s*K(?:elvin)?\s*\)?(?![A-Za-z])"
_CM_DP = re.compile(r"(?:by\s+|under\s+|from\s+)?(?:the\s+)?dulong[\s\-–]petit\b[^.;\n]{0,70}?\b(?:is|equals|=|approaches|of)\s+"
                    r"(?:3\s*R\s*[=≈]\s*)?" + _HEDGE + r"(?P<c>" + _RN + r")" + _CM_JMOLK, re.I)
_CM_HALL_A = re.compile(r"(?:at\s+)?(?:a\s+)?filling\s+factor\s+(?:of\s+)?(?:(?:ν|nu)\s*=\s*)?(?P<nu>\d+(?:\.\d+)?),?\s+(?:the\s+)?"
                        r"(?:quantum\s+)?hall\s+(?:resistance|plateau)(?:\s+plateau)?\s+" + _IS + r"\s*(?:at\s+)?" + _HEDGE +
                        r"(?P<c>" + _RN + r")" + _CM_OHM, re.I)
_CM_HALL_B = re.compile(r"(?:the\s+)?(?:ν|nu)\s*=\s*(?P<nu>\d+(?:\.\d+)?)\s+(?:quantum\s+)?hall\s+(?:resistance|plateau)(?:\s+plateau)?\s+" +
                        _IS + r"\s*(?:at\s+)?" + _HEDGE + r"(?P<c>" + _RN + r")" + _CM_OHM, re.I)
_HZ = {"Hz": 1e-9, "kHz": 1e-6, "MHz": 1e-3, "GHz": 1.0, "THz": 1e3}


def _ohm(u: str) -> float:
    return 1000.0 if u.lower().startswith("k") else 1.0


def _x_condensed_matter(text: str):
    """"the von Klitzing constant is 25812.807 ohms" / "the Josephson constant is 483597.8 GHz/V" / "by the
    Dulong-Petit law the molar heat capacity of a solid is 24.94 J/(mol K)" / "at filling factor 2 the Hall
    resistance is 12906.4 ohms" -> condensed_matter (CONDMAT_VERIFY), computed through h, e and alpha."""
    out = []
    for m in _CM_VK.finditer(text):
        out.append((_q(text, m), "condensed_matter",
                    {"CONDMAT_VERIFY": {"claimed_von_klitzing_ohm": _fl(m.group("c")) * _ohm(m.group("u")), "claimed_literal": m.group("c")}}))
    for m in _CM_KJ.finditer(text):
        out.append((_q(text, m), "condensed_matter",
                    {"CONDMAT_VERIFY": {"claimed_josephson_ghz_per_v": _fl(m.group("c")) * _HZ[m.group("u")], "claimed_literal": m.group("c")}}))
    for m in _CM_DP.finditer(text):
        out.append((_q(text, m), "condensed_matter",
                    {"CONDMAT_VERIFY": {"claimed_molar_heat_capacity": _fl(m.group("c")), "claimed_literal": m.group("c")}}))
    for rx in (_CM_HALL_A, _CM_HALL_B):
        for m in rx.finditer(text):
            out.append((_q(text, m), "condensed_matter",
                        {"CONDMAT_VERIFY": {"filling_factor": float(m.group("nu")),
                                            "claimed_hall_resistance_ohm": _fl(m.group("c")) * _ohm(m.group("u")),
                                            "claimed_literal": m.group("c")}}))
    return out


# ── cybersecurity: the standards' own tables (IANA, FIRST, IETF) and the entropy formula ───────────
_CY_SUBNET = re.compile(r"(?:an?\s+)?/(?P<p>\d{1,2})\s+(?:(?:ipv4\s+)?(?:subnet|network|block|prefix|cidr\s+block)\s+)?"
                        r"(?:has|gives|provides|allows|supports|contains|offers|yields)\s+(?P<c>\d[\d,]*)\s+"
                        r"(?:usable\s+(?:hosts?|addresses|host\s+addresses|ips?)|hosts?|host\s+addresses)\b", re.I)
_CY_PORT = re.compile(r"\b(?:(?:tcp|udp)\s+)?port\s+(?P<p>\d{1,5})\s+is\s+(?:an?\s+)?(?P<k>well[\s-]?known|registered|dynamic|ephemeral|private)"
                      r"(?:\s+(?:tcp|udp))?\s+port\b", re.I)
_CY_CVSS = re.compile(r"(?:an?\s+)?cvss\s*(?:v?3(?:\.\d)?\s*)?(?:base\s+)?(?:score\s+)?(?:of\s+)?(?P<s>\d{1,2}(?:\.\d)?)\s+"
                      r"(?:is|rates\s+as|is\s+rated|maps\s+to|means|counts\s+as)\s+(?:an?\s+|as\s+)?(?P<k>none|low|medium|high|critical)"
                      r"(?:\s+severity)?\b", re.I)
_CY_TLS = re.compile(r"\b(?:(?P<tls>TLS)\s*v?(?P<v>1\.[0-3])|(?P<ssl>SSL)\s*v?(?P<sv>[23])(?:\.0)?)\s+is\s+"
                     r"(?:(?:now|considered|officially)\s+)?(?P<k>deprecated|current|recommended|insecure)\b", re.I)
_CY_ENTROPY = re.compile(r"(?:an?\s+)?(?P<L>\d{1,4})[-\s]character\s+(?:(?P<named>lowercase|uppercase|alphanumeric|hex(?:adecimal)?|base64|numeric|digits?)\s+)?"
                         r"password\s+(?:(?:drawn|chosen|picked|taken)\s+)?(?:(?:from|over|using)\s+(?:an?\s+)?(?P<N>\d{1,4})[-\s](?:character|symbol)\s+"
                         r"(?:set|alphabet|charset|pool|space)\s+)?has\s+(?:" + _HEDGE + r"(?P<c>" + _RN + r")\s+bits\s+of\s+entropy|an?\s+entropy\s+of\s+" +
                         _HEDGE + r"(?P<c2>" + _RN + r")\s+bits)\b", re.I)
_CY_NAMED = {"lowercase": "lowercase", "uppercase": "uppercase", "alphanumeric": "alphanumeric", "hex": "hex", "hexadecimal": "hex",
             "base64": "base64", "numeric": "digits", "digit": "digits", "digits": "digits"}


def _x_cybersecurity(text: str):
    """"a /24 subnet has 254 usable hosts" / "port 443 is a well-known port" / "a CVSS score of 9.1 is critical" /
    "TLS 1.0 is deprecated" / "a 16-character password from a 94-character set has 104.9 bits of entropy" ->
    cybersecurity (CYBER_VERIFY). Usable hosts only: a bare "256 addresses" (the total) is not the verifier's
    quantity and is left alone."""
    out = []
    for m in _CY_SUBNET.finditer(text):
        out.append((_q(text, m), "cybersecurity",
                    {"CYBER_VERIFY": {"cidr_prefix": int(m.group("p")), "claimed_host_count": int(m.group("c").replace(",", "")),
                                      "claimed_literal": m.group("c")}}))
    for m in _CY_PORT.finditer(text):
        k = re.sub(r"[\s-]+", "_", m.group("k").lower())
        k = "dynamic" if k in ("ephemeral", "private") else k
        out.append((_q(text, m), "cybersecurity", {"CYBER_VERIFY": {"port_number": int(m.group("p")), "claimed_port_class": k}}))
    for m in _CY_CVSS.finditer(text):
        out.append((_q(text, m), "cybersecurity",
                    {"CYBER_VERIFY": {"cvss_base_score": float(m.group("s")), "claimed_cvss_severity": m.group("k").lower()}}))
    for m in _CY_TLS.finditer(text):
        v = m.group("v") if m.group("tls") else "ssl" + m.group("sv")
        out.append((_q(text, m), "cybersecurity", {"CYBER_VERIFY": {"tls_version": v, "claimed_tls_status": m.group("k").lower()}}))
    for m in _CY_ENTROPY.finditer(text):
        charset = m.group("N") and int(m.group("N"))
        if charset is None and m.group("named"):
            charset = _CY_NAMED[m.group("named").lower()]
        if charset is None:
            continue
        lit = m.group("c") or m.group("c2")
        out.append((_q(text, m), "cybersecurity",
                    {"CYBER_VERIFY": {"password_length": int(m.group("L")), "charset_size": charset,
                                      "claimed_entropy_bits": _fl(lit), "claimed_literal": lit}}))
    return out


# ── document validation: a checksum is a yes/no the digits themselves decide ───────────────────────
_DV_VALID = r"is\s+(?:an?\s+)?(?P<neg>not\s+)?(?P<v>valid|invalid)"
_DV_ISBN = re.compile(r"\bISBN(?:[-\s]?(?P<kind>1[03]))?\s*:?\s*(?P<n>\d[\d\-\s]{7,18}[\dXx])\s+" + _DV_VALID + r"(?:\s+ISBN)?\b", re.I)
_DV_CARD = re.compile(r"(?:the\s+)?(?:credit[-\s]card|card|account|imei|debit[-\s]card)\s+number\s+(?P<n>\d[\d\-\s]{9,22}\d)\s+" + _DV_VALID + r"\b", re.I)
_DV_LUHN = re.compile(r"(?:(?:the\s+)?(?:(?:credit[-\s]card|card|account|imei)\s+)?number\s+)?(?P<n>\d[\d\-\s]{9,22}\d)\s+(?P<pf>passes|fails)\s+"
                      r"(?:the\s+)?luhn(?:\s+(?:check|test|algorithm|checksum))?\b", re.I)
_DV_EAN = re.compile(r"\b(?:the\s+)?(?:UPC(?:-A)?|EAN(?:-13)?|barcode|bar\s+code)\s*(?:number\s+|code\s+)?:?\s*(?P<n>\d[\d\-\s]{10,15}\d)\s+" +
                     _DV_VALID + r"\b", re.I)


def _dv_digits(s: str) -> str:
    return re.sub(r"[^0-9Xx]", "", s)


def _x_document_validation(text: str):
    """"ISBN 0-306-40615-2 is valid" / "ISBN 978-0-306-40615-7 is valid" / "79927398713 passes the Luhn check" /
    "the card number 4532 0151 1283 0366 is valid" / "UPC 036000291452 is valid" -> document_validation
    (DOC_VERIFY). ISBN length decides 10 vs 13; an explicit "ISBN-13" on ten digits is a contradiction and is
    not extracted; a UPC/EAN must be 12 or 13 digits."""
    out = []
    for m in _DV_ISBN.finditer(text):
        d = _dv_digits(m.group("n"))
        claimed = (m.group("v").lower() == "valid") != bool(m.group("neg"))
        if len(d) == 10 and m.group("kind") in (None, "10"):
            out.append((_q(text, m), "document_validation", {"DOC_VERIFY": {"isbn10": d, "claimed_isbn10_valid": claimed}}))
        elif len(d) == 13 and d.isdigit() and m.group("kind") in (None, "13"):
            out.append((_q(text, m), "document_validation", {"DOC_VERIFY": {"isbn13": d, "claimed_isbn13_valid": claimed}}))
    for m in _DV_CARD.finditer(text):
        d = _dv_digits(m.group("n"))
        if d.isdigit() and len(d) >= 10:
            claimed = (m.group("v").lower() == "valid") != bool(m.group("neg"))
            out.append((_q(text, m), "document_validation", {"DOC_VERIFY": {"luhn_number": d, "claimed_luhn_valid": claimed}}))
    for m in _DV_LUHN.finditer(text):
        d = _dv_digits(m.group("n"))
        if d.isdigit() and len(d) >= 10:
            out.append((_q(text, m), "document_validation",
                        {"DOC_VERIFY": {"luhn_number": d, "claimed_luhn_valid": m.group("pf").lower() == "passes"}}))
    for m in _DV_EAN.finditer(text):
        d = _dv_digits(m.group("n"))
        if d.isdigit() and len(d) in (12, 13):
            claimed = (m.group("v").lower() == "valid") != bool(m.group("neg"))
            out.append((_q(text, m), "document_validation", {"DOC_VERIFY": {"ean_or_upc": d, "claimed_ean_valid": claimed}}))
    return out


# ── manufacturing: Six Sigma's table, the 3-sigma chart, the RSS stack ─────────────────────────────
_MF_SIG = r"(?P<s>\d(?:\.\d)?|one|two|three|four|five|six|seven)[\s-]*(?:sigma|σ)"
_MF_DPMO_WORD = r"(?:DPMO|defects?\s+per\s+million(?:\s+opportunities)?)"
_MF_DPMO_A = re.compile(r"(?:(?:a\s+)?DPMO\s+of\s+(?P<d1>" + _RN + r")|(?:a\s+)?(?:defect\s+rate\s+of\s+)?(?P<d2>" + _RN + r")\s+" + _MF_DPMO_WORD +
                        r")\s+(?:is|corresponds\s+to|equals|means|=|maps\s+to)\s+(?:about\s+|roughly\s+|approximately\s+)?(?:a\s+)?" + _MF_SIG +
                        r"(?:\s+(?:level|process|quality))?\b", re.I)
_MF_DPMO_B = re.compile(r"(?:a\s+)?" + _MF_SIG + r"(?:\s+(?:level|process|quality))?\s+(?:is|means|corresponds\s+to|equals|=|allows|has)\s+"
                        r"(?:about\s+|roughly\s+|approximately\s+|only\s+)?(?P<d>" + _RN + r")\s+" + _MF_DPMO_WORD + r"\b", re.I)
_MF_SPC = re.compile(r"(?:(?:a|the)\s+)?(?:process\s+|chart\s+)?with\s+(?:a\s+)?(?:process\s+)?mean\s+(?:of\s+)?(?P<m>" + _RN + r")\s+and\s+(?:a\s+)?"
                     r"(?:standard\s+deviation|sigma|σ|std\.?\s*dev\.?)\s+(?:of\s+)?(?P<s>" + _RN + r"),?\s+(?:the\s+|has\s+|gives\s+)?"
                     r"(?:(?P<k>[1-3]|one|two|three)[\s-]*(?:sigma|σ)\s+)?(?:x-?bar\s+)?control\s+limits\s+(?:are|of|at|=|is)\s+"
                     r"(?:UCL\s*(?:=|of)?\s*)?(?P<a>" + _RN + r")\s+and\s+(?:LCL\s*(?:=|of)?\s*)?(?P<b>" + _RN + r")\b", re.I)
_MF_LIST = r"(?P<list>" + _RN + r"(?:\s*,\s*" + _RN + r")*(?:,?\s*(?:and|&)\s+" + _RN + r")?)"
_MF_RSS_WORD = r"(?:RSS|root[-\s]sum[-\s](?:of[-\s])?squares?|statistical)"
_MF_RSS_A = re.compile(r"(?:the\s+)?" + _MF_RSS_WORD + r"\s+(?:tolerance\s+)?stack(?:[-\s]?up)?\s+(?:of|for)\s+(?:(?:the\s+)?tolerances\s+(?:of\s+)?)?" +
                       _MF_LIST + r"\s+" + _IS + r"\s*" + _HEDGE + r"(?P<c>" + _RN + r")\b", re.I)
_MF_RSS_B = re.compile(r"tolerances\s+(?:of\s+)?" + _MF_LIST + r"\s+stack\s+(?:up\s+)?(?:statistically\s+)?to\s+(?:an?\s+)?" + _MF_RSS_WORD +
                       r"\s+(?:total\s+|stack(?:[-\s]?up)?\s+)?(?:of\s+)?" + _HEDGE + r"(?P<c>" + _RN + r")\b", re.I)


def _sigf(tok: str) -> float:
    """'5' / '5.0' / 'six' -> a sigma level."""
    return float(tok) if re.match(r"\d", tok) else float(_cnt(tok))


def _x_manufacturing(text: str):
    """"a DPMO of 233 is a 5 sigma level" / "six sigma is 3.4 defects per million opportunities" / "with a mean of
    100 and a standard deviation of 2, the 3-sigma control limits are 94 and 106" / "the RSS stack-up of
    tolerances 0.1, 0.2 and 0.2 is 0.3" -> manufacturing (MFG_VERIFY). Control limits are an unordered pair:
    the lower one is the LCL whichever is written first."""
    out = []
    for m in _MF_DPMO_A.finditer(text):
        out.append((_q(text, m), "manufacturing",
                    {"MFG_VERIFY": {"dpmo": _fl(m.group("d1") or m.group("d2")), "claimed_sigma": _sigf(m.group("s"))}}))
    for m in _MF_DPMO_B.finditer(text):
        out.append((_q(text, m), "manufacturing",
                    {"MFG_VERIFY": {"dpmo": _fl(m.group("d")), "claimed_sigma": _sigf(m.group("s"))}}))
    for m in _MF_SPC.finditer(text):
        a, b = _fl(m.group("a")), _fl(m.group("b"))
        spec = {"mean": _fl(m.group("m")), "sigma": _fl(m.group("s")), "claimed_ucl": max(a, b), "claimed_lcl": min(a, b)}
        if m.group("k"):
            spec["k"] = _cnt(m.group("k"))
        out.append((_q(text, m), "manufacturing", {"MFG_VERIFY": spec}))
    for rx in (_MF_RSS_A, _MF_RSS_B):
        for m in rx.finditer(text):
            tols = [_fl(t) for t in re.findall(_RN, m.group("list"))]
            if len(tols) < 2 or any(t < 0 for t in tols):
                continue
            out.append((_q(text, m), "manufacturing",
                        {"MFG_VERIFY": {"tolerances": tols, "claimed_rss": _fl(m.group("c")), "claimed_literal": m.group("c")}}))
    return out


# ── molecular geometry: VSEPR from the domain count, in AXE notation or in words ───────────────────
_MG_GEO = r"(?P<geo>linear|trigonal[\s_-]planar|bent|tetrahedral|trigonal[\s_-]pyramidal|trigonal[\s_-]bipyramidal|see-?saw|t[\s_-]shaped|octahedral|square[\s_-]pyramidal|square[\s_-]planar)"
_MG_DEGU = r"\s*(?:°|degrees?|deg)\b"
_MG_ANG_A = r"(?:ideal\s+)?(?:bond\s+)?angles?\s+(?:of\s+)?" + _HEDGE + r"(?P<angA>\d{2,3}(?:\.\d+)?)" + _MG_DEGU
_MG_ANG_B = _HEDGE + r"(?P<angB>\d{2,3}(?:\.\d+)?)\s*(?:°|degrees?|deg)\s+(?:bond\s+)?angles?\b"
_MG_ANG_C = r"(?:ideal\s+)?(?:bond\s+)?angles?\s+(?:of\s+)?" + _HEDGE + r"(?P<angC>\d{2,3}(?:\.\d+)?)" + _MG_DEGU
_MG_ANG_D = _HEDGE + r"(?P<angD>\d{2,3}(?:\.\d+)?)\s*(?:°|degrees?|deg)\s+(?:bond\s+)?angles?\b"
_MG_TAIL = (r"(?:(?:is|are|has|have|adopts?|gives?|forms?|yields?|makes?)\s+(?:an?\s+)?(?:(?:molecular\s+)?(?:geometry|shape)\s+(?:of|that\s+is)\s+(?:an?\s+)?)?" +
            _MG_GEO + r"(?:\s+(?:geometry|shape|molecule))?(?:\s+(?:with|and)\s+(?:an?\s+)?(?:" + _MG_ANG_A + r"|" + _MG_ANG_B + r"))?" +
            r"|(?:has|have|with)\s+(?:an?\s+)?(?:" + _MG_ANG_C + r"|" + _MG_ANG_D + r"))")
_MG_AXE = re.compile(r"\b(?:an?\s+)?AX(?P<n>[1-6])(?P<E>E(?P<e>[1-3])?)?\b\s*(?:(?:molecule|species|system|geometry)\s+)?" + _MG_TAIL, re.I)
_MG_CNT = r"(?:\d|one|two|three|four|five|six|no|zero)"
_MG_DOM = re.compile(r"(?:(?:(?:a|an|the)\s+)?(?:(?:central\s+)?atom|molecule|species)\s+)?(?:(?:with|having|that\s+has)\s+)?(?P<n>" + _MG_CNT +
                     r")\s+(?:bonding\s+(?:domains?|pairs?|groups?|regions?)|bond(?:ed)?\s+(?:pairs?|atoms?)|bonds)\s+and\s+(?P<e>" + _MG_CNT +
                     r")\s+lone\s+pairs?\s+" + _MG_TAIL, re.I)


def _x_molecular_geometry(text: str):
    """"an AX4 molecule is tetrahedral with 109.5° bond angles" / "AX2E2 is bent" / "a molecule with 4 bonding
    pairs and no lone pairs is tetrahedral" -> molecular_geometry (VSEPR_VERIFY). The domain count is read from
    AXE notation or the words; a geometry the verifier's table gives more than one angle for is not extracted
    with an angle (the verifier cannot decide a single value), and an untabulated count is not extracted."""
    from .verifiers.molecular_geometry import _VSEPR
    out = []
    for rx in (_MG_AXE, _MG_DOM):
        for m in rx.finditer(text):
            n = _cnt(m.group("n"))
            if rx is _MG_AXE:
                e = (int(m.group("e") or 1)) if m.group("E") else 0
            else:
                e = _cnt(m.group("e"))
            entry = _VSEPR.get((n + e, e))
            if entry is None or n < 1:
                continue
            geo = m.group("geo")
            ang = m.group("angA") or m.group("angB") or m.group("angC") or m.group("angD")
            if ang is not None and entry[1] is None:
                continue
            spec: Dict[str, Any] = {"bonding_domains": n, "lone_pairs": e}
            if geo:
                g = re.sub(r"[\s_-]+", "_", geo.lower())
                spec["claimed_geometry"] = "seesaw" if g in ("see_saw", "seesaw") else g
            if ang is not None:
                spec["claimed_bond_angle_deg"] = float(ang)
                spec["claimed_literal"] = ang
            out.append((_q(text, m), "molecular_geometry", {"VSEPR_VERIFY": spec}))
    return out


# ── philosophy: which named framework judges by outcomes (the verifier's own four) ─────────────────
_PH_FW = r"(?P<fw>consequentialism|consequentialist\s+ethics|consequentialists?|deontology|deontological\s+ethics|deontologists?|virtue\s+ethics|virtue\s+ethicists?|contractarianism|contractarian\s+ethics|contractarians?)"
_PH_OUT = r"(?:outcomes?|consequences?|results)"
_PH_PRED = (r"(?:(?:(?P<n1>does\s+not|doesn't|do\s+not|don't)\s+)?(?:judges?|evaluates?|assesses?|measures?|grades?|determines?)\s+(?:the\s+)?(?:moral\s+)?"
            r"(?:worth\s+of\s+|rightness\s+of\s+)?(?:an\s+)?(?:actions?|acts?|conduct|behaviou?r)\s+(?:solely\s+|primarily\s+|only\s+|entirely\s+)?by\s+(?:their\s+|its\s+)?" + _PH_OUT +
            r"|(?:is|are)\s+(?P<n2>not\s+)?(?:(?:solely|primarily|chiefly|mainly)\s+)?(?:focused\s+on|concerned\s+with|about|based\s+on|grounded\s+in|a\s+matter\s+of)\s+" + _PH_OUT +
            r"|(?:(?P<n3>does\s+not|doesn't|do\s+not|don't)\s+)?focus(?:es)?\s+(?:solely\s+|primarily\s+)?on\s+" + _PH_OUT + r")")
_PH_RE = re.compile(r"\b" + _PH_FW + r"\s+" + _PH_PRED + r"\b", re.I)


def _x_philosophy(text: str):
    """"consequentialism judges actions by their outcomes" / "virtue ethics is not about outcomes" / "deontology
    does not judge actions by their consequences" -> philosophy (PHIL_VERIFY, the ethical-framework catalogue).
    Only the verifier's own four frameworks are named; no school is mapped onto another."""
    out = []
    for m in _PH_RE.finditer(text):
        fw = m.group("fw").lower()
        key = ("consequentialist" if fw.startswith("consequential") else "deontological" if fw.startswith("deontolog")
               else "virtue_ethics" if fw.startswith("virtue") else "contractarian")
        neg = bool(m.group("n1") or m.group("n2") or m.group("n3"))
        out.append((_q(text, m), "philosophy", {"PHIL_VERIFY": {"framework_name": key, "claimed_focuses_on_outcomes": not neg}}))
    return out


# ── photonics: a photon's energy from its wavelength or frequency, through h ───────────────────────
_PN_WL = r"(?P<wu>nm|nanomet(?:er|re)s?|µm|μm|um|microns?|micromet(?:er|re)s?|Å|angstroms?|pm|picomet(?:er|re)s?|mm|millimet(?:er|re)s?|met(?:er|re)s?|m)"
_PN_FQ = r"(?P<fu>(?-i:[kMGTP]?Hz)|hertz|kilohertz|megahertz|gigahertz|terahertz|petahertz)"
_PN_UNIT = r"(?:" + _PN_WL + r"|" + _PN_FQ + r")\b"
_PN_EV = r"(?P<eu>(?-i:[mk]?eV)|electron[-\s]?volts?|electronvolts?)\b"
_PN_A = re.compile(r"(?:a|an|the)\s+(?P<x>" + _RN + r")\s*" + _PN_UNIT + r"\s+(?:photon|light|laser)\s+(?:has|carries)\s+(?:an?\s+)?(?:photon\s+)?energy\s+(?:of\s+)?" +
                   _HEDGE + r"(?P<c>" + _RN + r")\s*" + _PN_EV, re.I)
_PN_B = re.compile(r"(?:the\s+)?(?:photon\s+)?energy\s+of\s+(?:a|an)\s+(?P<x>" + _RN + r")\s*" + _PN_UNIT + r"\s+(?:photon|light)\s+" + _IS + r"\s*" +
                   _HEDGE + r"(?P<c>" + _RN + r")\s*" + _PN_EV, re.I)
_PN_C = re.compile(r"(?:a|an)\s+photon\s+(?:of|with|at)\s+(?:a\s+)?(?:wavelength|frequency)?\s*(?:of\s+)?(?P<x>" + _RN + r")\s*" + _PN_UNIT +
                   r"\s+(?:has|carries)\s+(?:an?\s+)?energy\s+(?:of\s+)?" + _HEDGE + r"(?P<c>" + _RN + r")\s*" + _PN_EV, re.I)
_PN_D = re.compile(r"(?:light|photons?)\s+at\s+(?P<x>" + _RN + r")\s*" + _PN_UNIT + r"\s+(?:has|have|carries|carry)\s+(?:an?\s+)?(?:photon\s+)?energy\s+(?:of\s+)?" +
                   _HEDGE + r"(?P<c>" + _RN + r")\s*" + _PN_EV, re.I)
_PN_WLF = {"nm": 1e-9, "nanomet": 1e-9, "µm": 1e-6, "μm": 1e-6, "um": 1e-6, "micron": 1e-6, "micromet": 1e-6, "å": 1e-10, "angstrom": 1e-10,
           "pm": 1e-12, "picomet": 1e-12, "mm": 1e-3, "millimet": 1e-3, "met": 1.0, "m": 1.0}
_PN_FQF = {"hz": 1.0, "khz": 1e3, "mhz": 1e6, "ghz": 1e9, "thz": 1e12, "phz": 1e15, "hertz": 1.0, "kilohertz": 1e3, "megahertz": 1e6,
           "gigahertz": 1e9, "terahertz": 1e12, "petahertz": 1e15}
_PN_EVF = {"ev": 1.0, "mev": 1e-3, "kev": 1e3}


def _pn_factor(table: Dict[str, float], unit: str) -> Optional[float]:
    u = unit.lower()
    for k in sorted(table, key=len, reverse=True):
        if u == k or u.startswith(k):
            return table[k]
    return None


def _x_photonics(text: str):
    """"a 500 nm photon has energy 2.48 eV" / "the energy of a 1550 nm photon is 0.8 eV" / "a 600 THz photon has
    energy 2.48 eV" -> photonics (PHOT_VERIFY, E = h c / lambda or E = h nu). Wavelength and frequency units
    are converted into the verifier's metres and hertz; the energy into eV."""
    out = []
    for rx in (_PN_A, _PN_B, _PN_C, _PN_D):
        for m in rx.finditer(text):
            x = _fl(m.group("x"))
            eu = m.group("eu").lower()
            ef = 1.0 if eu.startswith("electron") else _PN_EVF.get(eu)
            if x <= 0 or ef is None:
                continue
            spec: Dict[str, Any] = {"claimed_photon_energy_ev": _fl(m.group("c")) * ef, "claimed_literal": m.group("c")}
            if m.group("wu"):
                f = _pn_factor(_PN_WLF, m.group("wu"))
                if f is None:
                    continue
                spec["photon_wavelength_m"] = x * f
            else:
                f = _pn_factor(_PN_FQF, m.group("fu"))
                if f is None:
                    continue
                spec["photon_frequency_hz"] = x * f
            out.append((_q(text, m), "photonics", {"PHOT_VERIFY": spec}))
    return out


# ── sports analytics: games behind, the Elo expectation, the Pythagorean record ────────────────────
_SP_LEADER = r"(?:leader|first[-\s]place\s+team|team|club)"
_SP_GB = re.compile(r"(?:(?:a|the)\s+)?(?:team\s+)?(?:(?:at|with\s+a\s+record\s+of|with\s+a|standing\s+at)\s+)?(?P<tw>\d{1,3})\s*[-–]\s*(?P<tl>\d{1,3})"
                    r"(?:\s+(?:team|record|club))?\s+(?:is|are|sits|stands)\s+(?P<gb>" + _RN + r")\s+games?\s+(?:back|behind)(?:\s+of)?\s+(?:(?:a|the)\s+)?"
                    r"(?:(?P<lw>\d{1,3})\s*[-–]\s*(?P<ll>\d{1,3})\s+" + _SP_LEADER + r"|" + _SP_LEADER + r"\s+(?:at|with\s+a\s+record\s+of|with\s+a)\s+"
                    r"(?P<lw2>\d{1,3})\s*[-–]\s*(?P<ll2>\d{1,3}))\b", re.I)
_SP_RATED = r"(?:[-\s](?:elo[-\s])?rated|[-\s]elo)?"
_SP_SCORE = r"(?:(?P<s>0?\.\d+|1\.0+|0|1)|(?P<pc>\d{1,3}(?:\.\d+)?)\s*%)(?!\d)"
_SP_EXPECT = r"(?:is\s+expected\s+to\s+score|has\s+an?\s+expected\s+score\s+of|expects\s+to\s+score|should\s+score)"
_SP_ELO_A = re.compile(r"(?:a|an)\s+(?P<a>\d{3,4})" + _SP_RATED + r"\s+(?:player|team)\s+" + _SP_EXPECT + r"\s+" + _HEDGE + _SP_SCORE +
                       r"\s+(?:against|versus|vs\.?)\s+(?:a|an)\s+(?P<b>\d{3,4})" + _SP_RATED + r"\s+(?:player|team|opponent)\b", re.I)
_SP_ELO_B = re.compile(r"(?:a|an)\s+(?P<a>\d{3,4})" + _SP_RATED + r"\s+(?:player|team)\s+(?:against|versus|vs\.?|facing|playing)\s+(?:a|an)\s+(?P<b>\d{3,4})" +
                       _SP_RATED + r"\s+(?:player|team|opponent)\s+" + _SP_EXPECT + r"\s+" + _HEDGE + _SP_SCORE, re.I)
_SP_PCT = r"(?:(?P<p>\.\d+|0\.\d+|1\.0+)|(?P<ppc>\d{1,3}(?:\.\d+)?)\s*%)(?!\d)"
_SP_PYWORD = r"pythagorean\s+(?:win(?:ning)?\s+(?:percentage|pct\.?|expectation|%)|expectation|record|win\s+%)"
_SP_PY_A = re.compile(r"(?:(?:a|the)\s+)?(?:team\s+)?(?:that\s+|which\s+|who\s+)?(?:scored|scoring|with|having\s+scored)\s+(?P<rs>\d[\d,]*)\s+runs?(?:\s+scored)?\s+and\s+"
                      r"(?:allowed|allowing|gave\s+up|giving\s+up|conceded|conceding)\s+(?P<ra>\d[\d,]*)(?:\s+runs?)?\s+(?:has|have|had|gets|earns)\s+(?:an?\s+)?(?:expected\s+)?" +
                      _SP_PYWORD + r"\s+(?:of\s+)?" + _HEDGE + _SP_PCT, re.I)
_SP_PY_B = re.compile(r"(?:the\s+)?" + _SP_PYWORD + r"\s+(?:for|of)\s+(?:a\s+team\s+(?:with|that\s+scored)\s+)?(?P<rs>\d[\d,]*)\s+runs?\s+(?:scored\s+)?and\s+(?P<ra>\d[\d,]*)\s+"
                      r"(?:runs\s+)?allowed\s+" + _IS + r"\s*" + _HEDGE + _SP_PCT, re.I)


def _x_sports_analytics(text: str):
    """"a team at 45-35 is 5 games behind a leader at 50-30" / "a 1600-rated player is expected to score 0.64 against
    a 1500-rated player" / "a team that scored 750 runs and allowed 600 has a Pythagorean winning percentage of
    .610" -> sports_analytics (SPORT_VERIFY). The word "Pythagorean" is REQUIRED (it names the exponent-2 formula);
    a bare win percentage is not this claim."""
    out = []
    for m in _SP_GB.finditer(text):
        lw, ll = m.group("lw") or m.group("lw2"), m.group("ll") or m.group("ll2")
        out.append((_q(text, m), "sports_analytics",
                    {"SPORT_VERIFY": {"leader_wins": int(lw), "leader_losses": int(ll), "team_wins": int(m.group("tw")),
                                      "team_losses": int(m.group("tl")), "claimed_games_behind": _fl(m.group("gb")), "claimed_literal": m.group("gb")}}))
    for rx in (_SP_ELO_A, _SP_ELO_B):
        for m in rx.finditer(text):
            lit = m.group("s") or m.group("pc")
            score = float(m.group("s")) if m.group("s") else float(m.group("pc")) / 100.0
            out.append((_q(text, m), "sports_analytics",
                        {"SPORT_VERIFY": {"elo_a": float(m.group("a")), "elo_b": float(m.group("b")), "claimed_expected_score_a": score,
                                          "claimed_literal": lit}}))
    for rx in (_SP_PY_A, _SP_PY_B):
        for m in rx.finditer(text):
            lit = m.group("p") or m.group("ppc")
            pct = float(m.group("p")) if m.group("p") else float(m.group("ppc")) / 100.0
            out.append((_q(text, m), "sports_analytics",
                        {"SPORT_VERIFY": {"runs_scored": int(m.group("rs").replace(",", "")), "runs_allowed": int(m.group("ra").replace(",", "")),
                                          "claimed_winning_pct": pct, "claimed_literal": lit}}))
    return out


# ── archaeology: the decay clock, from the surviving fraction ──────────────────────────────────────
_AR_FRAC = (r"(?:(?P<pct>\d+(?:\.\d+)?)\s*(?:%|percent)|(?P<dec>0?\.\d+)|(?P<word>half|one[-\s]half|a\s+half|(?:a|one)[-\s]quarter|(?:a|one)[-\s]fourth|"
            r"three[-\s]quarters|(?:an|one)[-\s]eighth|(?:a|one)[-\s]sixteenth))")
_AR_WORDS = {"half": 0.5, "one half": 0.5, "a half": 0.5, "a quarter": 0.25, "one quarter": 0.25, "a fourth": 0.25, "one fourth": 0.25,
             "three quarters": 0.75, "an eighth": 0.125, "one eighth": 0.125, "a sixteenth": 0.0625, "one sixteenth": 0.0625}
_AR_C14 = r"(?:carbon[-\s]?14|carbon[-\s]?fourteen|C[-\s]?14|14[-\s]?C|¹⁴C|radiocarbon)"
_AR_SCALE = r"(?P<ys>thousand|million|billion)?"
_AR_YEARS = r"(?P<age>" + _RN + r")\s*" + _AR_SCALE + r"\s*years?(?:\s+old)?\b"
_AR_HALFN = r"(?P<n>" + _RN + r"|one|two|three|four|five|six|seven|eight|nine|ten)\s+half[-\s]li(?:fe|ves)\b"
_AR_A = re.compile(r"(?:(?:a|the)\s+)?(?:sample|bone|charcoal|wood|artifact|artefact|specimen|object|fossil|shell|seed)\s+(?:with|retaining|that\s+retains|that\s+has|having|containing)\s+"
                   r"(?:only\s+|just\s+)?" + _AR_FRAC + r"\s+of\s+(?:its|the)\s+(?:original\s+)?" + _AR_C14 + r"(?:\s+(?:remaining|left|intact))?\s+"
                   r"(?:is|dates\s+to|would\s+be|must\s+be|has\s+an\s+age\s+of|is\s+dated\s+(?:at|to))\s+" + _HEDGE + _AR_YEARS, re.I)
_AR_B = re.compile(r"(?:if\s+|when\s+)?(?:only\s+)?" + _AR_FRAC + r"\s+of\s+(?:the|its|a\s+sample's)\s+(?:original\s+)?" + _AR_C14 +
                   r"\s+(?:remains|is\s+left|survives|is\s+remaining),?\s+(?:the\s+)?(?:sample|object|bone|specimen|age)\s+(?:is|would\s+be|dates\s+to|must\s+be)\s+" +
                   _HEDGE + _AR_YEARS, re.I)
_AR_C = re.compile(_AR_FRAC + r"\s+(?:remaining|surviving|left|residual)\s+" + _AR_C14 +
                   r"\s+(?:is|means|gives|corresponds\s+to|=|indicates|implies|dates\s+to)\s+(?:an\s+age\s+of\s+)?" + _HEDGE + _AR_YEARS, re.I)
_AR_HL_A = re.compile(_AR_FRAC + r"\s+(?:remaining|left|surviving)(?:\s+of\s+(?:a|the|an)\s+(?:original\s+)?(?:sample|isotope|parent|nuclide|amount))?\s+"
                      r"(?:is|means|represents|corresponds\s+to|=|equals|takes|after)\s+" + _AR_HALFN, re.I)
_AR_HL_B = re.compile(r"after\s+" + _AR_HALFN + r",?\s+(?:only\s+)?" + _AR_FRAC +
                      r"(?:\s+of\s+(?:the|a|an)\s+(?:original\s+)?(?:sample|isotope|parent|nuclide|amount))?\s+(?:remains|is\s+left|survives|will\s+remain)\b", re.I)
_AR_ISO = re.compile(r"(?:with\s+)?(?:a\s+)?half[-\s]life\s+of\s+(?P<hl>" + _RN + r")\s*(?P<hls>thousand|million|billion)?\s*years,?\s+(?:a\s+sample\s+with\s+)?" + _AR_FRAC +
                     r"\s+(?:remaining|left)\s+(?:is|means|gives|corresponds\s+to|dates\s+to|implies)\s+(?:an\s+age\s+of\s+)?" + _HEDGE + _AR_YEARS, re.I)
_SCALE = {None: 1.0, "thousand": 1e3, "million": 1e6, "billion": 1e9}


def _ar_frac(m: re.Match) -> Optional[float]:
    if m.group("pct"):
        f = float(m.group("pct")) / 100.0
    elif m.group("dec"):
        f = float(m.group("dec"))
    else:
        f = _AR_WORDS.get(re.sub(r"[-\s]+", " ", m.group("word").lower()))
    return f if f is not None and 0.0 < f <= 1.0 else None


def _x_archaeology(text: str):
    """"a sample with 25% of its carbon-14 remaining is about 11,460 years old" / "25% remaining carbon-14 is about
    11460 years" / "if 50% of the carbon-14 remains, the sample is 5730 years old" / "12.5% remaining is 3
    half-lives" / "with a half-life of 1.25 billion years, 50% remaining is 1.25 billion years old" ->
    archaeology (ARCH_VERIFY, t = -(T/ln 2) ln f). The fraction is a percent, a decimal or a plain word."""
    out = []
    for rx in (_AR_A, _AR_B, _AR_C):
        for m in rx.finditer(text):
            f = _ar_frac(m)
            if f is None:
                continue
            age = _fl(m.group("age")) * _SCALE[(m.group("ys") or "").lower() or None]
            out.append((_q(text, m), "archaeology",
                        {"ARCH_VERIFY": {"fraction_remaining": f, "claimed_age_years": age, "claimed_literal": m.group("age")}}))
    for rx in (_AR_HL_A, _AR_HL_B):
        for m in rx.finditer(text):
            f = _ar_frac(m)
            if f is None:
                continue
            n = m.group("n")
            out.append((_q(text, m), "archaeology",
                        {"ARCH_VERIFY": {"fraction_for_halflives": f, "claimed_half_lives": float(_cnt(n)) if not re.match(r"-?\d", n) else _fl(n),
                                         "claimed_literal": n}}))
    for m in _AR_ISO.finditer(text):
        f = _ar_frac(m)
        if f is None:
            continue
        hl = _fl(m.group("hl")) * _SCALE[(m.group("hls") or "").lower() or None]
        age = _fl(m.group("age")) * _SCALE[(m.group("ys") or "").lower() or None]
        if hl <= 0:
            continue
        out.append((_q(text, m), "archaeology",
                    {"ARCH_VERIFY": {"fraction_remaining_iso": f, "half_life_years": hl, "claimed_age_years_iso": age, "claimed_literal": m.group("age")}}))
    return out


_EXTRACTORS: Tuple[Tuple[str, Callable], ...] = (
    ("sum", _x_sum), ("product", _x_product), ("quotient", _x_quotient), ("arith_words", _x_arith_words),
    ("rational_roots", _x_rational_roots), ("substance", _x_substance),
    ("expression", _x_expression),      # THE CLAIM GRAMMAR (Gen 3 · 3): a mixed/parenthesised expression
    ("power", _x_power), ("factorial", _x_factorial), ("sqrt", _x_sqrt),
    ("combinations", _x_combinations), ("permutations", _x_permutations),
    ("propositional_logic", _x_propositional_logic), ("logic_relations", _x_logic_relations), ("argument_form", _x_argument_form),
    ("syllogism", _x_syllogism), ("logic_counts", _x_logic_counts), ("named_forms", _x_named_forms),
    ("fallacy_kind", _x_fallacy_kind),
    # THE REACH (issue #11): the eleven domains a sentence could not reach until 2026-10-16
    ("linear_algebra", _x_linear_algebra), ("chess", _x_chess), ("condensed_matter", _x_condensed_matter),
    ("cybersecurity", _x_cybersecurity), ("document_validation", _x_document_validation),
    ("manufacturing", _x_manufacturing), ("molecular_geometry", _x_molecular_geometry), ("philosophy", _x_philosophy),
    ("photonics", _x_photonics), ("sports_analytics", _x_sports_analytics), ("archaeology", _x_archaeology),
    ("word_letters", _x_word_letters), ("anagram", _x_anagram), ("palindrome", _x_palindrome),
    ("edit_distance", _x_edit_distance), ("alphabet", _x_alphabet), ("plural", _x_plural), ("letter_rank", _x_letter_rank),
    ("rhyme", _x_rhyme), ("homophone", _x_homophone), ("stress", _x_stress), ("silent_letter", _x_silent_letter),
    ("vowel_sound", _x_vowel_sound), ("edge_sound", _x_edge_sound), ("etymology", _x_etymology),
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


def _extract_run(text: str) -> List[Dict[str, Any]]:
    """The actual recognition pass — run every extractor over the text. Pure and deterministic
    (plain regex, no model), so its result is memoized by extract() below."""
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


@lru_cache(maxsize=256)
def _extract_memo(text: str) -> Tuple[Dict[str, Any], ...]:
    return tuple(_extract_run(text))


def extract(text: str) -> List[Dict[str, Any]]:
    """All certain claims in the text, as verify_derivation steps (id, domain, spec, claim).
    Deduped on (domain, spec); order = extractor order, then position.

    RECOGNIZE ONCE (2026-10-12): the ~N-extractor pass is deterministic, so it is MEMOIZED per text —
    a request extracts a claim once in from_prose and again in the blind route() (which reads only
    raw_text, by design), and both now share the one computed recognition. Callers get fresh deep copies
    so the cache is read-only and can never be corrupted; the key is bounded by MAX_TEXT."""
    return [copy.deepcopy(s) for s in _extract_memo((text or "")[:MAX_TEXT])]


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
