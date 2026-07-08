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


def _x_percent(text: str):
    out = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*%\s*(?:of|tip on|tax on|discount on|off(?: of)?|on)\s*"
                         + _NUM + r"\s*" + _EQ + r"\s*" + _NUM, text, re.I):
        pct, base, claimed = _f(m.group(1)), _f(m.group(2)), _f(m.group(3))
        out.append((_q(text, m), "mathematics",
                    {"mode": "equality", "params": {"expr_a": f"({pct}/100)*{base}",
                                                    "expr_b": str(claimed)}}))
    return out


def _x_gross_pay(text: str):
    out = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*hours?\s*(?:at|@)\s*\$\s*(\d+(?:\.\d+)?)"
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


_EXTRACTORS: Tuple[Tuple[str, Callable], ...] = (
    ("sum", _x_sum), ("product", _x_product), ("percent", _x_percent),
    ("gross_pay", _x_gross_pay), ("annual_hourly", _x_annual_hourly),
    ("compound_interest", _x_compound), ("rule_of_72", _x_rule72),
    ("elapsed_years", _x_elapsed_years), ("day_of_week", _x_day_of_week),
    ("leap_year", _x_leap_year), ("nutrition_label", _x_nutrition),
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


def audit(text: str, config, seal: bool = True) -> Dict[str, Any]:
    """Extract -> verify the lot as one derivation -> attach one seal. The coverage report."""
    steps = extract(text)
    if not steps:
        return {"claims_found": 0, "results": [], "verdict": "NOTHING_TO_CHECK",
                "note": ("No unambiguously checkable claim was found. The auditor extracts only "
                         "certain patterns (sums, percentages, pay, interest, dates, labels) — "
                         "it would rather miss a claim than check the wrong one.")}
    from .derivation import verify_derivation
    dres = verify_derivation([{k: s[k] for k in ("id", "domain", "spec", "claim")} for s in steps])
    results = []
    held = broken = 0
    for s, t in zip(steps, dres["trail"]):
        ok = t["status"] == "CONFIRMED"
        held += 1 if ok else 0
        broken += 0 if ok else 1
        results.append({"claim": s["claim"], "extractor": s["extractor"], "domain": s["domain"],
                        "status": t["status"], "detail": t["detail"]})
    out: Dict[str, Any] = {
        "claims_found": len(steps), "held": held, "broken_or_unchecked": broken,
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
