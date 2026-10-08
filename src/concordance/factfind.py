"""FACT FIND — what the CHECK door says when nothing in a claim is computable (R5 of
docs/PROJECT_REVIEW_2026-10-03.md; Matt, 2026-10-03: "go in order").

The auditor's extractors turn COMPUTABLE claims (sums, constants, definitional element facts) into verdicts
with receipts. A lookup claim — "the atomic mass of iron is 55.845", "iron melts at 1538 C" — is not computable,
and the door used to answer NOTHING_TO_CHECK and hand back three unrelated cards as "FOUND" (measured live:
a phase-theory card and two lexicon entries for the melting point of iron). This module makes that answer honest,
in three shapes, never blurred with a computed verdict and never minting a receipt:

  1. a FOUND FACT — the keeping's own sourced table holds the property — and whether it AGREES with the
     claimed number. Found, cited, not computed. Tables today: an element's standard atomic weight and
     atomic number (IUPAC); an isotope's half-life (ENSDF evaluations, 2026-10-07); a pure substance's
     normal boiling point at 101.325 kPa (CRC Handbook, 2026-10-07).
  2. FOUND CARDS — only cards whose TITLE names the subject (the same gap guard the front door uses), so a
     reader is never handed a lexicon entry for a metallurgy question.
  3. NOT HELD YET — plainly, with a WANT OFFERED (never opened on the engine's own: "nothing records a want on
     its own — bot noise must never write the acquisition queue"). The reader or agent opens it with one call,
     and the library goes to find a public-domain source. The keeping grows by its misses.

HOW A FOUND FACT AGREES (2026-10-07). A measured value carries its source's uncertainty; a claim carries the
precision the person STATED (verifiers.base.stated_precision — half a unit in the last written place, two or
more significant figures only). The two agree when the bands overlap: |claimed - value| <= uncertainty +
stated half-unit. Nothing else widens the window: the source's own uncertainty and the claim's own literal.
A claim stated to ONE figure ("8 days" for iodine-131, "100 C" for water) earns no window of its own — the
same rule the verifiers keep for "3e8" — and is compared at the source's uncertainty alone, with the exact
value and its band shown so the reader sees why. `agrees` is None only when no value was claimed at all.
The front-door benchmark (tools/frontdoor.py) reports these found facts in their own column, never as a
verifier's verdict.

Pure where it can be: find_fact() needs only the tables; verify_fallback() takes the search as an
argument so a test can stub it."""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from .verifiers.base import stated_precision, stated_tolerance_abs

# property words -> (lookup field, tolerance: ("abs", x) | ("rel", x) | ("exact", 0), source)
_HELD = {
    "standard atomic weight": ("atomic_mass", ("rel", 1e-3), "IUPAC standard atomic weights (verifiers/periodic_table)"),
    "atomic weight": ("atomic_mass", ("rel", 1e-3), "IUPAC standard atomic weights (verifiers/periodic_table)"),
    "atomic mass": ("atomic_mass", ("rel", 1e-3), "IUPAC standard atomic weights (verifiers/periodic_table)"),
    "atomic number": ("atomic_number", ("exact", 0), "IUPAC element identity (verifiers/periodic_table)"),
    "protons": ("atomic_number", ("exact", 0), "IUPAC element identity (verifiers/periodic_table)"),
}
# properties a reader asks about that the keeping does NOT hold as a sourced table for an ELEMENT (yet) — named
# honestly. "boiling point"/"half-life" stay here for the subjects their tables below do not list (gold's
# boiling point; an isotope not yet tabled): the table exists, the entry does not, and the note says which.
_NOT_HELD = ("melting point", "melts", "boiling point", "boils", "density", "electronegativity",
             "specific heat", "thermal conductivity", "electrical conductivity", "half-life", "half life",
             "ionization energy", "atomic radius", "hardness")
_NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?(?:\s*[eE]\s*[-+]?\d+)?")
_WORD = re.compile(r"[A-Za-z][A-Za-z-]*")


# ── SOURCED TABLES (2026-10-07) ────────────────────────────────────────────────────────────────────────
# HALF-LIVES: (value, uncertainty, unit) exactly as the ENSDF evaluation states them (NNDC NuDat; the IAEA
# Live Chart of Nuclides publishes the same evaluations). The unit is the source's: a claim in another unit is
# converted to it. A value is never recomputed here — there is nothing to compute; it is FOUND and cited.
_HL_SOURCE = "ENSDF evaluated half-lives (NNDC NuDat / IAEA Live Chart of Nuclides)"
_HALF_LIVES: Dict[str, Tuple[float, float, str]] = {
    "hydrogen-3": (12.32, 0.02, "y"),            # tritium
    "beryllium-7": (53.22, 0.06, "d"),
    "carbon-11": (20.364, 0.014, "min"),
    "carbon-14": (5700.0, 30.0, "y"),            # radiocarbon (the Cambridge half-life 5730 +/- 40 y lies within this band)
    "nitrogen-13": (9.965, 0.004, "min"),
    "oxygen-15": (122.24, 0.16, "s"),
    "fluorine-18": (109.77, 0.05, "min"),
    "sodium-22": (2.6018, 0.0022, "y"),
    "sodium-24": (14.997, 0.012, "h"),
    "phosphorus-32": (14.268, 0.005, "d"),
    "chlorine-36": (3.013e5, 0.015e5, "y"),
    "argon-39": (269.0, 3.0, "y"),
    "potassium-40": (1.248e9, 0.003e9, "y"),
    "cobalt-60": (1925.28, 0.14, "d"),
    "krypton-85": (10.739, 0.014, "y"),
    "technetium-99": (2.111e5, 0.012e5, "y"),
    "iodine-123": (13.2235, 0.0019, "h"),
    "iodine-129": (1.57e7, 0.04e7, "y"),
    "iodine-131": (8.0252, 0.0006, "d"),
    "xenon-133": (5.2475, 0.0005, "d"),
    "cesium-134": (2.0652, 0.0004, "y"),
    "cesium-137": (30.08, 0.09, "y"),
    "iridium-192": (73.829, 0.011, "d"),
    "lead-210": (22.20, 0.22, "y"),
    "bismuth-209": (2.01e19, 0.08e19, "y"),
    "polonium-210": (138.376, 0.002, "d"),
    "radon-220": (55.6, 0.1, "s"),
    "radon-222": (3.8235, 0.0003, "d"),
    "radium-226": (1600.0, 7.0, "y"),
    "actinium-227": (21.772, 0.003, "y"),
    "thorium-230": (7.54e4, 0.03e4, "y"),
    "thorium-232": (1.40e10, 0.01e10, "y"),
    "protactinium-231": (3.276e4, 0.011e4, "y"),
    "uranium-233": (1.592e5, 0.002e5, "y"),
    "uranium-234": (2.455e5, 0.006e5, "y"),
    "uranium-235": (7.04e8, 0.01e8, "y"),
    "uranium-238": (4.468e9, 0.006e9, "y"),
    "neptunium-237": (2.144e6, 0.007e6, "y"),
    "plutonium-238": (87.7, 0.1, "y"),
    "plutonium-239": (24110.0, 30.0, "y"),
    "plutonium-240": (6561.0, 7.0, "y"),
    "americium-241": (432.6, 0.6, "y"),
    "californium-252": (2.645, 0.008, "y"),
}
_ISOTOPE_ALIASES = {"tritium": "hydrogen-3", "radiocarbon": "carbon-14"}
# seconds per unit; the year is the ENSDF convention (365.2422 d)
_TIME_S = {"s": 1.0, "sec": 1.0, "secs": 1.0, "second": 1.0, "seconds": 1.0, "ms": 1e-3, "millisecond": 1e-3,
           "milliseconds": 1e-3, "min": 60.0, "minute": 60.0, "minutes": 60.0, "h": 3600.0, "hr": 3600.0,
           "hrs": 3600.0, "hour": 3600.0, "hours": 3600.0, "d": 86400.0, "day": 86400.0, "days": 86400.0,
           "y": 365.2422 * 86400.0, "yr": 365.2422 * 86400.0, "yrs": 365.2422 * 86400.0,
           "year": 365.2422 * 86400.0, "years": 365.2422 * 86400.0}
_MULT = {"thousand": 1e3, "million": 1e6, "billion": 1e9, "trillion": 1e12}
_HL_WORDS = re.compile(r"\bhalf[-\s]?li(?:fe|ves)\b", re.I)
_HL_Q = re.compile(r"(?<![\w-])(\d[\d,]*(?:\.\d+)?(?:[eE][-+]?\d+)?)\s*(thousand|million|billion|trillion)?\s*"
                   r"(years?|yrs?|y|days?|d|hours?|hrs?|h|minutes?|min|seconds?|secs?|s|ms|milliseconds?)\b", re.I)
_ISO = re.compile(r"\b([A-Za-z]+)[-\s](\d{1,3})\b")           # carbon-14, carbon 14, C-14
_ISO_TIGHT = re.compile(r"\b(\d{1,3})([A-Z][a-z]?)\b")        # 14C

# NORMAL BOILING POINTS, degrees Celsius at 101.325 kPa: (value, uncertainty). CRC Handbook of Chemistry and
# Physics (Physical Constants of Organic/Inorganic Compounds; Properties of the Elements). The uncertainty is
# the spread a careful reader meets across editions, not a measurement figure; metals carry more of it.
# Deliberately absent: substances with no normal boiling point (carbon dioxide sublimes at 1 atm) and metals
# whose tabulated boiling points differ by more than a few percent between standard sources (gold, tungsten,
# platinum) — the keeping does not hold what the sources do not agree on.
_BP_SOURCE = "CRC Handbook of Chemistry and Physics, normal boiling point at 101.325 kPa"
_BOILING_POINTS: Dict[str, Tuple[float, float]] = {
    "water": (99.97, 0.05),
    "methanol": (64.6, 0.2), "methyl alcohol": (64.6, 0.2),
    "ethanol": (78.3, 0.2), "ethyl alcohol": (78.3, 0.2),
    "isopropanol": (82.3, 0.2), "isopropyl alcohol": (82.3, 0.2), "2-propanol": (82.3, 0.2),
    "acetone": (56.08, 0.1), "benzene": (80.09, 0.1), "toluene": (110.6, 0.1), "hexane": (68.73, 0.1),
    "octane": (125.67, 0.1), "diethyl ether": (34.5, 0.1), "chloroform": (61.17, 0.1),
    "acetic acid": (117.9, 0.1), "glycerol": (290.0, 5.0), "formaldehyde": (-19.1, 0.2),
    "methane": (-161.5, 0.1), "ethane": (-88.6, 0.1), "propane": (-42.1, 0.1), "butane": (-0.5, 0.1),
    "ammonia": (-33.33, 0.1), "hydrogen sulfide": (-59.55, 0.1), "sulfur dioxide": (-10.05, 0.1),
    "nitrogen dioxide": (21.15, 0.1), "nitrous oxide": (-88.48, 0.1), "carbon monoxide": (-191.5, 0.1),
    "hydrogen chloride": (-85.0, 0.1), "hydrogen fluoride": (19.5, 0.1),
    "hydrogen": (-252.879, 0.01), "helium": (-268.928, 0.01), "neon": (-246.046, 0.01),
    "nitrogen": (-195.795, 0.01), "oxygen": (-182.962, 0.01), "fluorine": (-188.11, 0.05),
    "argon": (-185.848, 0.01), "krypton": (-153.415, 0.01), "xenon": (-108.099, 0.01),
    "chlorine": (-34.04, 0.05), "bromine": (58.8, 0.1), "iodine": (184.4, 0.1), "sulfur": (444.61, 0.1),
    "mercury": (356.62, 0.05), "sodium": (882.94, 0.5), "potassium": (759.0, 1.0), "lithium": (1342.0, 2.0),
    "magnesium": (1090.0, 2.0), "calcium": (1484.0, 2.0), "zinc": (907.0, 2.0), "lead": (1749.0, 5.0),
    "aluminum": (2519.0, 5.0), "aluminium": (2519.0, 5.0), "silver": (2162.0, 5.0), "copper": (2562.0, 5.0),
    "iron": (2861.0, 5.0), "nickel": (2913.0, 5.0), "tin": (2602.0, 5.0),
}
_NOT_PURE = ("heavy water", "sea water", "seawater", "salt water", "saltwater", "sugar water", "tap water")
_BOIL_WORDS = re.compile(r"\bboil(?:s|ing|ed)?\b", re.I)
_TEMP_Q = re.compile(r"(-?\d[\d,]*(?:\.\d+)?)\s*(?:°|º|deg(?:rees?)?\.?\s*)?(C|celsius|centigrade|F|fahrenheit|K|kelvins?)\b", re.I)
_PRESS = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(atm|atmospheres?|kPa|hPa|mbar|millibars?|bar|mm\s*Hg|torr|psi|Pa|pascals?)\b", re.I)
_NORMAL_P = {"atm": 1.0, "atmosphere": 1.0, "atmospheres": 1.0, "kpa": 101.325, "hpa": 1013.25, "mbar": 1013.25,
             "millibar": 1013.25, "millibars": 1013.25, "bar": 1.01325, "mmhg": 760.0, "torr": 760.0,
             "psi": 14.696, "pa": 101325.0, "pascal": 101325.0, "pascals": 101325.0}


def _num(s: str) -> float:
    return float(s.replace(",", "").replace(" ", ""))


def element_in(text: str) -> Optional[Dict[str, Any]]:
    """The element the claim names — by name ("iron", any case) or by symbol as its own token ("Fe", "Au")."""
    from .verifiers import periodic_table as _pt
    from . import lookup as _lookup
    names = getattr(_pt, "_BY_NAME", {}) or {}
    for w in _WORD.findall(text or ""):
        low = w.lower()
        if low in names:
            got = _lookup.lookup("element", {"name": low})
            if got.get("found"):
                return got["value"]
    for w in _WORD.findall(text or ""):
        if 1 <= len(w) <= 2 and w[0].isupper() and w not in ("A", "I", "C", "K", "N", "O", "S", "F", "H", "P", "V", "W", "U"):
            got = _lookup.lookup("element", {"symbol": w})
            if got.get("found"):
                return got["value"]
    return None


def isotope_in(text: str) -> Optional[str]:
    """The ONE isotope a text names, canonical ("carbon-14"), or None: "carbon-14" / "carbon 14" / "C-14" /
    "14C" / "tritium". Two different isotopes -> None (ambiguous; a miss stays a miss)."""
    from .verifiers import periodic_table as _pt
    names = getattr(_pt, "_BY_NAME", {}) or {}
    symbols = getattr(_pt, "_BY_SYMBOL", {}) or {}
    t = text or ""
    found = set()
    for m in _ISO.finditer(t):
        w, a = m.group(1), int(m.group(2))
        if w.lower() in names:
            found.add(f"{w.lower()}-{a}")
        elif w in symbols:
            found.add(f"{symbols[w]['name'].lower()}-{a}")
    for m in _ISO_TIGHT.finditer(t):
        a, sym = int(m.group(1)), m.group(2)
        if sym in symbols:
            found.add(f"{symbols[sym]['name'].lower()}-{a}")
    low = t.lower()
    for alias, canon in _ISOTOPE_ALIASES.items():
        if re.search(r"\b" + alias + r"\b", low):
            found.add(canon)
    if low.strip() in _HALF_LIVES:                      # the canonical key itself, as lookup() may pass it
        found.add(low.strip())
    return found.pop() if len(found) == 1 else None


def substance_in(text: str) -> Optional[str]:
    """The ONE boiling-point-table substance a text names (longest key first, so "ethyl alcohol" is read
    before any shorter key inside it), or None when it names none, two with different values, or a mixture
    ("sea water" is not water)."""
    low = (text or "").lower()
    if any(re.search(r"\b" + re.escape(x) + r"\b", low) for x in _NOT_PURE):
        return None
    hits: List[str] = []
    covered = low
    for key in sorted(_BOILING_POINTS, key=len, reverse=True):
        pat = r"(?<![a-z-])" + re.escape(key) + r"(?![a-z])"
        if re.search(pat, covered):
            hits.append(key)
            covered = re.sub(pat, " ", covered)
    values = {_BOILING_POINTS[h] for h in hits}
    return hits[0] if hits and len(values) == 1 else None


def number_in(text: str) -> Optional[float]:
    """The claimed number: the LAST number in the claim (claims put their value last)."""
    nums = _NUM.findall(text or "")
    if not nums:
        return None
    try:
        return float(nums[-1].replace(",", "").replace(" ", ""))
    except ValueError:
        return None


def _agrees(value: float, claimed: float, tol) -> bool:
    kind, x = tol
    if kind == "exact":
        return float(value) == float(claimed)
    if kind == "abs":
        return abs(value - claimed) <= x
    return abs(value - claimed) <= abs(value) * x


def _bands_overlap(value: float, unc: float, claimed: float, half: Optional[float]) -> bool:
    """A measured value (+/- unc) agrees with a stated one when the bands overlap. `half` is the claim's
    stated half-unit — None when it stated one figure, which earns no window: the source's band alone decides."""
    return abs(float(value) - float(claimed)) <= float(unc) + float(half or 0.0)


def _find_half_life(claim: str) -> Optional[Dict[str, Any]]:
    if not _HL_WORDS.search(claim or ""):
        return None
    iso = isotope_in(claim)
    if not iso:
        return None
    if iso not in _HALF_LIVES:
        return {"kind": "isotope", "subject": iso, "property": "half-life", "held": False, "source": None,
                "table": "half_life"}
    value, unc, unit = _HALF_LIVES[iso]
    out: Dict[str, Any] = {"kind": "isotope", "subject": iso, "property": "half-life", "field": "half_life",
                           "value": value, "unit": unit, "uncertainty": unc, "source": _HL_SOURCE,
                           "lookup": {"kind": "half_life", "params": {"isotope": iso}},
                           "claimed": None, "claimed_unit": None, "agrees": None}
    qs = list(_HL_Q.finditer(claim))
    if len(qs) != 1:                                      # no quantity, or two: found, not compared
        return out
    m = qs[0]
    lit, mult, cunit = m.group(1), (m.group(2) or "").lower(), m.group(3).lower()
    if cunit not in _TIME_S:
        return out
    factor = _MULT.get(mult, 1.0) * _TIME_S[cunit] / _TIME_S[unit]     # claimed unit -> the table's unit
    claimed = _num(lit) * factor
    sp = stated_precision(lit)
    out.update({"claimed": _num(lit) * _MULT.get(mult, 1.0), "claimed_unit": cunit,
                "claimed_in_table_unit": claimed, "stated_sigfigs": sp[0] if sp else None,
                "agrees": _bands_overlap(value, unc, claimed, stated_tolerance_abs(lit, unit_factor=factor))})
    return out


def _normal_pressure(claim: str) -> bool:
    """True unless the claim states a pressure that is NOT the standard atmosphere (then the normal boiling
    point is the wrong table, and nothing is found). 101.3 kPa, 760 mmHg, 14.7 psi, 1013 mbar pass; 1 bar
    and 100 kPa do not (water boils at 99.6 C there, and that difference must not be papered over)."""
    for m in _PRESS.finditer(claim or ""):
        unit = re.sub(r"\s+", "", m.group(2).lower())
        normal = _NORMAL_P.get(unit)
        if normal is None:
            return False
        if abs(_num(m.group(1)) - normal) > 0.005 * normal:
            return False
    return True


def _find_boiling_point(claim: str) -> Optional[Dict[str, Any]]:
    if not _BOIL_WORDS.search(claim or ""):
        return None
    sub = substance_in(claim)
    if not sub or not _normal_pressure(claim):
        return None
    value, unc = _BOILING_POINTS[sub]
    out: Dict[str, Any] = {"kind": "substance", "subject": sub, "property": "boiling point", "field": "boiling_point_C",
                           "value": value, "unit": "degC", "uncertainty": unc, "source": _BP_SOURCE,
                           "lookup": {"kind": "boiling_point", "params": {"substance": sub}},
                           "claimed": None, "claimed_unit": None, "agrees": None}
    qs = list(_TEMP_Q.finditer(claim))
    if len(qs) != 1:
        return out
    m = qs[0]
    lit, u = m.group(1), m.group(2).lower()
    x = _num(lit)
    if u in ("c", "celsius", "centigrade"):
        claimed, scale, cunit = x, 1.0, "degC"
    elif u in ("f", "fahrenheit"):
        claimed, scale, cunit = (x - 32.0) * 5.0 / 9.0, 5.0 / 9.0, "degF"
    else:
        claimed, scale, cunit = x - 273.15, 1.0, "K"
    sp = stated_precision(lit)
    out.update({"claimed": x, "claimed_unit": cunit, "claimed_in_table_unit": round(claimed, 6),
                "stated_sigfigs": sp[0] if sp else None,
                "agrees": _bands_overlap(value, unc, claimed, stated_tolerance_abs(lit, unit_factor=scale))})
    return out


def find_fact(claim: str) -> Optional[Dict[str, Any]]:
    """A found fact (an isotope's half-life, a substance's normal boiling point, an element's atomic weight or
    number), or 'not held' for a property the keeping lacks, or None when the claim names no subject or no
    property the tables know."""
    ff = _find_half_life(claim) or _find_boiling_point(claim)
    if ff:
        return ff
    el = element_in(claim)
    if not el:
        return None
    low = (claim or "").lower()
    for words in sorted(_HELD, key=len, reverse=True):
        if words in low:
            field, tol, source = _HELD[words]
            value = el.get(field)
            claimed = number_in(claim)
            out = {"kind": "element", "subject": el["name"], "symbol": el["symbol"], "property": words,
                   "field": field, "value": value, "source": source, "claimed": claimed,
                   "lookup": {"kind": "element", "params": {"name": str(el["name"])}}}
            out["agrees"] = (claimed is not None and value is not None and _agrees(float(value), float(claimed), tol))
            return out
    for words in _NOT_HELD:
        if re.search(r"\b" + re.escape(words) + r"\b", low):
            return {"kind": "element", "subject": el["name"], "symbol": el["symbol"], "property": words,
                    "held": False, "source": None}
    return None


def fact_sentence(ff: Dict[str, Any]) -> str:
    """One plain sentence for a found fact: the value, its unit and uncertainty, the source, the comparison."""
    unit = f" {ff['unit']}" if ff.get("unit") else ""
    unc = f" +/- {ff['uncertainty']}" if ff.get("uncertainty") is not None else ""
    who = f"{ff['subject']} ({ff['symbol']})" if ff.get("symbol") else ff["subject"]
    head = f"{who} {ff['property']} = {ff['value']}{unit}{unc} ({ff['source']})"
    if ff.get("claimed") is None:
        return head + "; no claimed value to compare"
    cunit = f" {ff['claimed_unit']}" if ff.get("claimed_unit") else ""
    verb = "agrees with" if ff.get("agrees") else "does NOT agree with"
    sf = ff.get("stated_sigfigs")
    if sf is not None and sf < 2:
        how = " (compared at the source's uncertainty alone — a claim stated to one figure earns no window of its own)"
    elif ff.get("agrees") and sf:
        how = f" (within the source's uncertainty and the {sf} significant figure(s) stated)"
    else:
        how = ""
    return head + f", which {verb} the claimed {ff['claimed']}{cunit}{how}"


def verify_fallback(claim: str, checked: Optional[str] = None,
                    search: Optional[Callable[..., List[Dict[str, Any]]]] = None) -> Dict[str, Any]:
    """The honest answer when claims_found is 0: {found_fact} | {found: on-subject briefs} | {found: [], want}.
    `search(query, limit=3)` defaults to the keeping's question search; `checked` is the airlocked text."""
    from . import ask as _ask, corpus as _corpus
    search = search or (lambda q, limit=3: _corpus.search_question(q, limit=limit))
    out: Dict[str, Any] = {}
    ff = find_fact(claim)
    if ff and ff.get("field"):
        out["found_fact"] = ff
        out["note"] = (f"No computable claim to prove here — but the keeping's own sourced table holds this: "
                       f"{fact_sentence(ff)}. FOUND and cited, not a computed verdict; no receipt.")
        return out
    subject = ff["subject"] if ff else None
    try:
        hits = search(checked or claim, limit=3) or []
    except Exception:  # noqa: BLE001 — the find is a bonus; never break the verify answer
        hits = []
    probe = subject or (claim or "")
    on_subject = [c for c in hits if isinstance(c, dict) and _ask._title_names_subject(probe, c)]
    if on_subject:
        out["found"] = [_corpus._brief(c) for c in on_subject]
        out["note"] = ("No computable claim to prove here — the engine proves numbers, formulas and constants "
                       "with a receipt. The keeping does hold this subject, FOUND and cited below (not a computed "
                       "verdict, no receipt): read the source and decide. For a question rather than a claim, use /ask.")
        return out
    # H7 (2026-10-08): words that carry arithmetic go to the STRUCTURED form with a template — a want is for a
    # missing source, and arithmetic needs none. A numeric lookup-shaped claim keeps the want and gets the
    # template too, so neither door is a dead end.
    from . import audit as _audit
    hint = _audit.structured_hint(claim or "")
    if hint:
        out["structured"] = hint
    if hint and _audit.looks_arithmetic(claim or ""):
        out["found"] = []
        out["note"] = ("No extractor recognized these words as a checkable claim, but they carry arithmetic: the "
                       "structured form checks it directly — edit the template in `structured` and send it, or ask "
                       "find_verifier for the domain's packet. (A want is for a missing source; arithmetic needs none.)")
        return out
    want_q = f"{subject} {ff['property']}" if ff and ff.get("property") else (claim or "").strip()[:200]
    out["found"] = []
    out["want"] = {"query": want_q,
                   "offer": "The keeping holds nothing on this yet. Open a want and the library goes to find a "
                            "public-domain source for it; the keeping grows by its misses.",
                   "how": "POST /want {query, kind: 'missing'} — or the want_open tool on the agent door"}
    if ff and ff.get("held") is False and ff.get("table"):
        out["note"] = (f"No computable claim to prove here, and the keeping's {ff['property']} table holds no entry "
                       f"for {ff['subject']} yet — said plainly, not papered over with unrelated cards. A want is "
                       f"offered; nothing is invented.")
    elif ff and ff.get("held") is False:
        out["note"] = (f"No computable claim to prove here, and the keeping does not yet hold a sourced table for "
                       f"the {ff['property']} of {ff['subject']} — said plainly, not papered over with unrelated cards. "
                       f"A want is offered; nothing is invented.")
    else:
        out["note"] = ("No computable claim to prove here, and no card in the keeping names this subject — said "
                       "plainly. A want is offered; nothing is invented.")
    return out
