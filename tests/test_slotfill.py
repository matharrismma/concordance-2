"""The slot-fillers (2026-10-07): unit-anchored extraction, any word order, zero false positives.

Pins the three things the front-door fix must keep true: (1) a natural phrasing the regexes miss now
reaches the verifier and the verdict is right; (2) the false twin is MISMATCHED, never confirmed; (3) the
existing extractor's pins stand — a mass-first sentence still reports the ORIGINAL extractor (dedup keeps
the first), and a lowercase word is still never parsed as a formula (the name is looked up, under its own
extractor name). Ambiguous sentences (two of a slot) extract nothing — a miss stays a miss.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance.audit import extract, audit  # noqa: E402
from concordance import slotfill as S  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402

CFG = EngineConfig(skip_schema_validation=True)


def _names(text):
    return [s["extractor"] for s in extract(text)]


# ---- Ohm's law: any order ----

def test_ohms_law_any_order_confirms():
    for t in ["a 10 ohm resistor with 2 amps drops 20 volts",
              "20 volts across 10 ohms gives 2 amps",
              "with 2 A through 10 Ω the drop is 20 V"]:
        assert "ohms_law" in _names(t), t
        r = audit(t, CFG, seal=False)
        assert r["held"] == 1 and r["broken"] == 0, (t, r["results"])


def test_ohms_law_catches_a_wrong_claim():
    r = audit("a 10 ohm resistor with 2 amps drops 30 volts", CFG, seal=False)   # 20, not 30
    assert r["broken"] == 1 and r["results"][0]["status"] == "MISMATCH"


def test_ohms_law_zero_false_positives():
    for t in ["a 10 ohm and a 20 ohm resistor in series with 2 amps at 60 volts",   # two ohms -> ambiguous
              "the battery is 12 volts and the fuse is 2 amps",                       # no ohms at all
              "I drove 20 miles in 2 hours"]:
        assert "ohms_law" not in _names(t), t


# ---- kinetic energy: energy-first phrasing ----

def test_kinetic_energy_energy_first_confirms():
    t = "the kinetic energy of a 2 kg mass at 3 m/s is 9 J"
    assert "kinetic_energy_units" in _names(t)
    r = audit(t, CFG, seal=False)
    assert r["held"] == 1 and r["broken"] == 0


def test_kinetic_energy_energy_first_catches_a_wrong_claim():
    r = audit("the kinetic energy of a 2 kg mass at 3 m/s is 12 J", CFG, seal=False)   # 9, not 12
    assert r["broken"] == 1 and r["results"][0]["status"] == "MISMATCH"


def test_kinetic_energy_mass_first_still_reports_the_original_extractor():
    """Dedup keeps the first (domain, spec): the pinned regex, not the filler."""
    names = _names("a 2 kg object at 3 m/s has kinetic energy 9 J")
    assert "kinetic_energy" in names and "kinetic_energy_units" not in names


def test_kinetic_energy_filler_zero_false_positives():
    for t in ["a 2 kg bag of flour on the shelf", "I ran at 3 m/s and felt full of energy",
              "the kinetic energy is 9 J"]:                                # no mass, no speed
        assert "kinetic_energy_units" not in _names(t), t


# ---- molar mass by NAME (a found table, never a parsed word) ----

def test_molar_mass_named_confirms():
    t = "the molar mass of water is 18.015 g/mol"
    names = _names(t)
    assert "molar_mass_named" in names and "molar_mass" not in names     # the old pin stands
    r = audit(t, CFG, seal=False)
    assert r["held"] == 1 and r["broken"] == 0


def test_molar_mass_named_catches_a_wrong_claim():
    r = audit("the molar mass of water is 20 g/mol", CFG, seal=False)      # 18.015, not 20
    assert r["broken"] == 1 and r["results"][0]["status"] == "MISMATCH"


def test_molar_mass_unknown_name_is_not_extracted():
    assert "molar_mass_named" not in _names("the molar mass of unobtainium is 500 g/mol")


# ---- escape velocity by named world ----

def test_escape_velocity_earth_confirms_at_stated_precision():
    t = "the escape velocity of earth is 11.2 km/s"      # exact 11186 m/s; 11.2 is right to 3 s.f.
    assert "escape_velocity" in _names(t)
    r = audit(t, CFG, seal=False)
    assert r["held"] == 1 and r["broken"] == 0, r["results"]


def test_escape_velocity_catches_a_wrong_claim():
    r = audit("the escape velocity of earth is 15 km/s", CFG, seal=False)
    assert r["broken"] == 1 and r["results"][0]["status"] == "MISMATCH"


def test_escape_velocity_unknown_body_is_not_extracted():
    assert "escape_velocity" not in _names("the escape velocity of krypton is 11.2 km/s")


def test_fillers_are_registered_after_the_originals():
    from concordance.audit import _EXTRACTORS
    names = [n for n, _ in _EXTRACTORS]
    assert names.index("unit_fact") < names.index("ohms_law")
    assert set(n for n, _ in S.FILLERS) <= set(names)
