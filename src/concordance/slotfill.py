"""SLOT-FILLERS — the second stage of the front-door funnel (2026-10-07).

The auditor's extractors (audit._EXTRACTORS) are word-order regexes: "a 2 kg object at 3 m/s has kinetic
energy 9 J" is caught, "the kinetic energy of a 2 kg mass at 3 m/s is 9 J" is not — same engine, same
numbers, inverted phrasing. And 67 of the 80 verified domains had no extractor at all: Ohm's law, escape
velocity, a molar mass by its NAME. Measured live 2026-10-07: 3 of 10 reasonable claims reached a verifier.

A slot-filler is anchored on UNITS, not word order. Volts, amps and ohms in one sentence are Ohm's law
whatever order they come in; kg, m/s and joules beside the words "kinetic energy" are ½mv². The packet keys
are filled from the unit each number carries, so the claim verb's position does not matter. Each filler
keeps the auditor's asymmetry: every slot must be present exactly once, or NOTHING is extracted — a miss
stays a miss, never a guess.

Two FOUND tables feed computed verifiers (receipts, never lookups): COMPOUNDS names a formula for a common
substance ("water" -> H2O; the periodic_table verifier then COMPUTES the molar mass), BODIES names a mass
and radius for a world ("earth"; the astronomy verifier then COMPUTES the escape velocity through G). A name
not in a table is not extracted. Nothing here parses a word as a formula — the pinned discipline of
_x_molar_mass stands; this is a lookup beside it, under its own extractor name.

Each filler returns [(quote, domain, spec)] exactly as an audit extractor does; audit registers them AFTER
its own, so a sentence both catch is deduped to the original (same domain + spec). Pure; no corpus, no IO.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

_N = r"(\d[\d,]*(?:\.\d+)?(?:[eE][-+]?\d+)?)"
_SENT = re.compile(r"[.;\n]+")


def _f(s: str) -> float:
    return float(s.replace(",", "").replace(" ", ""))


def _quote(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()[:160]


def _one(pattern: str, sent: str) -> Optional[re.Match]:
    """The single match of a unit-anchored number in a sentence, or None if there are 0 or 2+."""
    ms = list(re.finditer(pattern, sent, re.I))
    return ms[0] if len(ms) == 1 else None


# ── FOUND tables ───────────────────────────────────────────────────────────────────────────────────────
# Common substances by their everyday name -> molecular formula (IUPAC / standard chemistry). The formula
# is what the periodic_table verifier computes from; the name is only the key.
COMPOUNDS: Dict[str, str] = {
    "water": "H2O", "carbon dioxide": "CO2", "carbon monoxide": "CO", "methane": "CH4", "ammonia": "NH3",
    "glucose": "C6H12O6", "sucrose": "C12H22O11", "table salt": "NaCl", "sodium chloride": "NaCl",
    "ethanol": "C2H6O", "ethyl alcohol": "C2H6O", "methanol": "CH4O", "acetic acid": "C2H4O2",
    "sulfuric acid": "H2SO4", "sulphuric acid": "H2SO4", "hydrochloric acid": "HCl", "nitric acid": "HNO3",
    "sodium hydroxide": "NaOH", "potassium hydroxide": "KOH", "sodium bicarbonate": "NaHCO3",
    "baking soda": "NaHCO3", "hydrogen peroxide": "H2O2", "ozone": "O3", "oxygen": "O2", "nitrogen": "N2",
    "hydrogen": "H2", "chlorine": "Cl2", "propane": "C3H8", "butane": "C4H10", "benzene": "C6H6",
    "urea": "CH4N2O", "caffeine": "C8H10N4O2", "aspirin": "C9H8O4", "nitrous oxide": "N2O",
    "sulfur dioxide": "SO2", "nitrogen dioxide": "NO2", "hydrogen sulfide": "H2S", "silica": "SiO2",
    "quartz": "SiO2", "lime": "CaO", "quicklime": "CaO", "limestone": "CaCO3", "calcium carbonate": "CaCO3",
    "magnesium oxide": "MgO", "iron oxide": "Fe2O3", "rust": "Fe2O3", "potassium nitrate": "KNO3",
}

# Worlds by name -> (mass kg, mean radius m). NASA planetary fact sheets (nssdc.gsfc.nasa.gov); the
# astronomy verifier computes v = sqrt(2 G M / r) from these through the one constant source.
BODIES: Dict[str, Tuple[float, float]] = {
    "earth": (5.9722e24, 6.371e6), "moon": (7.346e22, 1.7374e6), "mars": (6.4171e23, 3.3895e6),
    "venus": (4.8675e24, 6.0518e6), "mercury": (3.3011e23, 2.4397e6), "jupiter": (1.8982e27, 6.9911e7),
    "saturn": (5.6834e26, 5.8232e7), "sun": (1.9885e30, 6.957e8), "uranus": (8.6810e25, 2.5362e7),
    "neptune": (1.02413e26, 2.4622e7),
}

_SPEED_UNIT = {"km/s": 1000.0, "kilometers per second": 1000.0, "kilometres per second": 1000.0,
               "m/s": 1.0, "meters per second": 1.0, "metres per second": 1.0}


# ── fillers ────────────────────────────────────────────────────────────────────────────────────────────
def x_ohms_law(text: str) -> List[Tuple[str, str, Dict[str, Any]]]:
    """Volts, amps and ohms in ONE sentence, any order, each exactly once -> electrical Ohm's law
    (V = I R). The spelled unit "ohm(s)"/Ω is required, which marks the sentence electrical, so the bare
    V/A after a number is unambiguous there. Two of a kind (a divider: 10 ohm and 20 ohm) -> nothing."""
    out = []
    for sent in _SENT.split(text or ""):
        if not re.search(r"\bohms?\b|Ω", sent, re.I):
            continue
        v = _one(_N + r"\s*(?:volts?|V)\b", sent)
        i = _one(_N + r"\s*(?:amps?|amperes?|A)\b", sent)
        r = _one(_N + r"\s*(?:ohms?|Ω)\b", sent)
        if not (v and i and r):
            continue
        out.append((_quote(sent), "electrical",
                    {"ELEC_VERIFY": {"voltage_V": _f(v.group(1)), "current_A": _f(i.group(1)),
                                     "resistance_ohm": _f(r.group(1))}}))
    return out


def x_kinetic_energy_units(text: str) -> List[Tuple[str, str, Dict[str, Any]]]:
    """kg, m/s and J/joules in ONE sentence that says "kinetic energy", any order -> physics ½mv²."""
    out = []
    for sent in _SENT.split(text or ""):
        if not re.search(r"\bkinetic\s+energy\b", sent, re.I):
            continue
        m = _one(_N + r"\s*(?:kg|kilograms?)\b", sent)
        v = _one(_N + r"\s*(?:m/s|meters?\s+per\s+second|metres?\s+per\s+second)\b", sent)
        e = _one(_N + r"\s*(?:J|joules?)\b", sent)
        if not (m and v and e):
            continue
        out.append((_quote(sent), "physics",
                    {"PHYS_VERIFY": {"mass_kg": _f(m.group(1)), "velocity_m_per_s": _f(v.group(1)),
                                     "claimed_kinetic_energy_J": _f(e.group(1))}}))
    return out


_MM_NAMED = re.compile(r"\bmolar\s+mass\s+of\s+(?:the\s+)?([a-z][a-z \-]{1,30}?)\s+(?:is|=|equals)\s*(?:about|approximately|roughly|~|≈)?\s*"
                       + _N + r"\s*(?:g\s*/\s*mol|grams?\s+per\s+mole?)?", re.I)


def x_molar_mass_named(text: str) -> List[Tuple[str, str, Dict[str, Any]]]:
    """"the molar mass of water is 18.015 g/mol" — a NAME found in COMPOUNDS -> its formula -> the
    periodic_table molar-mass verifier computes it. A name not in the table is not extracted."""
    out = []
    for m in _MM_NAMED.finditer(text or ""):
        name = re.sub(r"\s+", " ", m.group(1).strip().lower())
        formula = COMPOUNDS.get(name)
        if not formula:
            continue
        out.append((_quote(m.group(0)), "periodic_table",
                    {"PT_VERIFY": {"formula": formula, "claimed_molar_mass": _f(m.group(2)), "named": name}}))
    return out


_EV = re.compile(r"\bescape\s+velocity\s+(?:of|from|for|on)\s+(?:the\s+)?([a-z]+)\b[^.;\n]{0,40}?"
                 r"(?:is|=|equals|about|approximately|roughly|~|≈)\s*(?:about|approximately|roughly|~|≈)?\s*"
                 + _N + r"\s*(km/s|kilomet(?:er|re)s\s+per\s+second|m/s|met(?:er|re)s\s+per\s+second)\b", re.I)


def x_escape_velocity(text: str) -> List[Tuple[str, str, Dict[str, Any]]]:
    """"the escape velocity of earth is 11.2 km/s" — a world found in BODIES -> astronomy computes
    v = sqrt(2 G M / r). The claim is handed over AS WRITTEN ("11.2 km/s") so the verifier can judge it at
    the precision the person stated (see verifiers.base.stated_tolerance)."""
    out = []
    for m in _EV.finditer(text or ""):
        body = m.group(1).lower()
        if body not in BODIES:
            continue
        unit = re.sub(r"\s+", " ", m.group(3).lower())
        factor = _SPEED_UNIT.get(unit) or (1000.0 if unit.startswith("kilo") else 1.0)
        mass, radius = BODIES[body]
        out.append((_quote(m.group(0)), "astronomy",
                    {"ASTRO_VERIFY": {"escape_mass_kg": mass, "escape_radius_m": radius,
                                      "claimed_escape_velocity_m_s": _f(m.group(2)) * factor,
                                      "claimed_escape_velocity_as_written": f"{m.group(2)} {unit}",
                                      "body": body}}))
    return out


# (name, fn) — registered by audit after its own extractors; names are what the report shows.
FILLERS = (
    ("ohms_law", x_ohms_law),
    ("kinetic_energy_units", x_kinetic_energy_units),
    ("molar_mass_named", x_molar_mass_named),
    ("escape_velocity", x_escape_velocity),
)
