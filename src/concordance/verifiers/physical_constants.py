"""Physical constants verifier.

CODATA 2018 recommended values for fundamental physical constants.
All values are public domain (US government via NIST). Where a value
is exact by SI definition (post-2019 redefinition), the constant is
marked accordingly.

Checks:
  * physical_constant.value — claim of a named constant's value matches
    CODATA within a stated tolerance

CONST_VERIFY shape:
    {
      "constant": "speed_of_light",   # see _CONSTANTS below for the keys
      "claimed_value": 299792458,
      "claimed_unit": "m/s",           # optional, must match if given
      "rel_tol": 1e-4,                 # optional, default 1e-4
    }
"""
from __future__ import annotations

import math
from typing import Any, Dict, List

from .base import VerifierResult, na, confirm, mismatch, error, clamp_tol


# Each entry: (canonical_value, unit, is_exact, source_note)
# Aliases for common synonyms come below in _ALIASES.
_CONSTANTS: Dict[str, Dict[str, Any]] = {
    "speed_of_light":             {"value": 299_792_458.0,            "unit": "m/s",          "exact": True,  "note": "exact since 1983 SI"},
    "planck_constant":            {"value": 6.626_070_15e-34,         "unit": "J*s",          "exact": True,  "note": "exact since 2019 SI redefinition"},
    "reduced_planck_constant":    {"value": 1.054_571_817e-34,        "unit": "J*s",          "exact": False, "note": "derived"},
    "elementary_charge":          {"value": 1.602_176_634e-19,        "unit": "C",            "exact": True,  "note": "exact since 2019 SI"},
    "boltzmann_constant":         {"value": 1.380_649e-23,            "unit": "J/K",          "exact": True,  "note": "exact since 2019 SI"},
    "avogadro_constant":          {"value": 6.022_140_76e23,          "unit": "1/mol",        "exact": True,  "note": "exact since 2019 SI"},
    "gas_constant":               {"value": 8.314_462_618,            "unit": "J/(mol*K)",    "exact": True,  "note": "exact (N_A * k_B)"},
    "electron_mass":              {"value": 9.109_383_7015e-31,       "unit": "kg",           "exact": False},
    "proton_mass":                {"value": 1.672_621_923_69e-27,     "unit": "kg",           "exact": False},
    "neutron_mass":               {"value": 1.674_927_498_04e-27,     "unit": "kg",           "exact": False},
    "atomic_mass_unit":           {"value": 1.660_539_066_60e-27,     "unit": "kg",           "exact": False},
    "gravitational_constant":     {"value": 6.674_30e-11,             "unit": "m^3/(kg*s^2)", "exact": False, "note": "G; weakest-measured fundamental"},
    "vacuum_permittivity":        {"value": 8.854_187_8128e-12,       "unit": "F/m",          "exact": False, "note": "epsilon_0"},
    "vacuum_permeability":        {"value": 1.256_637_062_12e-6,      "unit": "N/A^2",        "exact": False, "note": "mu_0"},
    "fine_structure_constant":    {"value": 7.297_352_5693e-3,        "unit": "dimensionless","exact": False, "note": "alpha"},
    "rydberg_constant":           {"value": 1.097_373_156_8160e7,     "unit": "1/m",          "exact": False},
    "bohr_radius":                {"value": 5.291_772_109_03e-11,     "unit": "m",            "exact": False, "note": "a_0"},
    "stefan_boltzmann_constant":  {"value": 5.670_374_419e-8,         "unit": "W/(m^2*K^4)",  "exact": False, "note": "sigma"},
    "standard_gravity":           {"value": 9.806_65,                 "unit": "m/s^2",        "exact": True,  "note": "exact by definition"},
    "atmosphere":                 {"value": 101_325.0,                "unit": "Pa",           "exact": True,  "note": "1 atm; exact by definition"},
    "molar_volume_stp":           {"value": 0.022_413_969_54,         "unit": "m^3/mol",      "exact": False, "note": "ideal gas at 0°C, 100 kPa"},
    "wien_displacement_constant": {"value": 2.897_771_955e-3,         "unit": "m*K",          "exact": False},
    "faraday_constant":           {"value": 96_485.332_12,            "unit": "C/mol",        "exact": True,  "note": "exact (N_A * e)"},
}

# Common synonyms → canonical key. The classifier will hand us whatever
# Claude returned; this absorbs the variants without complaining.
_ALIASES: Dict[str, str] = {
    "c": "speed_of_light",
    "light_speed": "speed_of_light",
    "speed_of_light_in_vacuum": "speed_of_light",
    "h": "planck_constant",
    "planck": "planck_constant",
    "h_bar": "reduced_planck_constant",
    "hbar": "reduced_planck_constant",
    "e": "elementary_charge",
    "electron_charge": "elementary_charge",
    "k_b": "boltzmann_constant",
    "kb": "boltzmann_constant",
    "boltzmann": "boltzmann_constant",
    "n_a": "avogadro_constant",
    "na": "avogadro_constant",
    "avogadro": "avogadro_constant",
    "avogadro's_number": "avogadro_constant",
    "avogadros_number": "avogadro_constant",
    "avogadro_number": "avogadro_constant",
    "avogadro's_constant": "avogadro_constant",
    "avogadros_constant": "avogadro_constant",
    "r": "gas_constant",
    "universal_gas_constant": "gas_constant",
    "ideal_gas_constant": "gas_constant",
    "m_e": "electron_mass",
    "me": "electron_mass",
    "m_p": "proton_mass",
    "mp": "proton_mass",
    "m_n": "neutron_mass",
    "mn": "neutron_mass",
    "u": "atomic_mass_unit",
    "amu": "atomic_mass_unit",
    "dalton": "atomic_mass_unit",
    "g_newton": "gravitational_constant",
    "newton_constant": "gravitational_constant",
    "epsilon_0": "vacuum_permittivity",
    "permittivity": "vacuum_permittivity",
    "mu_0": "vacuum_permeability",
    "permeability": "vacuum_permeability",
    "alpha": "fine_structure_constant",
    "a_0": "bohr_radius",
    "sigma": "stefan_boltzmann_constant",
    "g": "standard_gravity",          # surface gravity, not G!
    "earth_gravity": "standard_gravity",
    "atm": "atmosphere",
    "1_atm": "atmosphere",
    "f": "faraday_constant",
    "faraday": "faraday_constant",
}


def _canonical(name: str) -> str:
    key = (name or "").strip().lower().replace(" ", "_").replace("-", "_")
    if key in _CONSTANTS:
        return key
    return _ALIASES.get(key, key)


# Unit-string normalizer: accept the common synonyms Claude is likely
# to produce ("meter/second" for "m/s", "J·s" for "J*s", etc.) so the
# verifier doesn't fail on cosmetic format differences.
_UNIT_ALIASES = {
    "meter/second": "m/s", "meters/second": "m/s", "metre/second": "m/s",
    "meters_per_second": "m/s", "meter_per_second": "m/s", "m_per_s": "m/s",
    "meter/second^2": "m/s^2", "meters/second^2": "m/s^2",
    "m/s2": "m/s^2", "m*s^-2": "m/s^2", "m·s^-2": "m/s^2",
    "j·s": "J*s", "j*s": "J*s", "joule·second": "J*s", "joule_second": "J*s",
    "joule/kelvin": "J/K", "j/k": "J/K", "j·k^-1": "J/K",
    "1/mol": "1/mol", "mol^-1": "1/mol", "per_mole": "1/mol",
    "permole": "1/mol",            # space-squashed "per mole"
    "permol": "1/mol",
    "permolecule": "1/mol",
    "particles/mole": "1/mol", "particles/mol": "1/mol",
    "atoms/mole": "1/mol", "atoms/mol": "1/mol",
    "entities/mole": "1/mol", "molecules/mole": "1/mol",
    "j/(mol·k)": "J/(mol*K)", "j/(mol*k)": "J/(mol*K)",
    "joule/(mole·kelvin)": "J/(mol*K)",
    "kilogram": "kg", "kilograms": "kg",
    "coulomb": "C", "coulombs": "C",
    "pascal": "Pa", "pascals": "Pa",
    "farad/meter": "F/m", "f/m": "F/m",
    "newton/ampere^2": "N/A^2", "n/a^2": "N/A^2", "n·a^-2": "N/A^2",
    "1/m": "1/m", "m^-1": "1/m", "per_meter": "1/m",
    "watt/(meter^2*kelvin^4)": "W/(m^2*K^4)", "w/(m^2*k^4)": "W/(m^2*K^4)",
    "coulomb/mol": "C/mol", "c/mol": "C/mol",
    "meter·kelvin": "m*K", "m*k": "m*K",
    "meter^3/(kilogram*second^2)": "m^3/(kg*s^2)",
    "m^3/(kg·s^2)": "m^3/(kg*s^2)",
    "dimensionless": "dimensionless", "unitless": "dimensionless", "": "dimensionless",
}


def _normalize_unit(u: str) -> str:
    if not u:
        return ""
    k = u.strip().lower().replace("·", "*").replace(" ", "")
    # Try exact alias hit on the normalized form
    if k in _UNIT_ALIASES:
        return _UNIT_ALIASES[k]
    # Best-effort: also strip case-folding from the canonical forms
    canonicals = {v.lower(): v for v in _UNIT_ALIASES.values()}
    if k in canonicals:
        return canonicals[k]
    # Fall through — caller compares strings as a last resort
    return u.strip()


def verify_physical_constant(spec: Dict[str, Any]) -> VerifierResult:
    """Check a claim about a named fundamental physical constant."""
    name = "physical_constants.value"
    raw_name = spec.get("constant", "")
    claimed = spec.get("claimed_value")
    if not raw_name or claimed is None:
        return na(name)
    canonical = _canonical(raw_name)
    record = _CONSTANTS.get(canonical)
    if not record:
        return na(name)
    try:
        claim = float(claimed)
    except (TypeError, ValueError):
        return na(name)
    actual = record["value"]
    rel_tol = clamp_tol(spec, "rel_tol", 1e-4)
    if actual == 0:
        threshold = 1e-12
    else:
        threshold = abs(actual) * rel_tol
    diff = abs(actual - claim)
    data = {
        "constant": canonical,
        "actual_value": actual,
        "unit": record["unit"],
        "claimed_value": claim,
        "claimed_unit": spec.get("claimed_unit"),
        "diff": diff,
        "rel_tol": rel_tol,
        "exact": record.get("exact", False),
        "note": record.get("note", ""),
        "source": "CODATA 2018 / NIST",
    }
    # If a unit was provided and doesn't match after normalization, surface
    # that distinctly. We normalize common synonyms ("meter/second" → "m/s")
    # so the verifier doesn't fail on cosmetic format differences.
    claimed_unit_raw = (spec.get("claimed_unit") or "").strip()
    if claimed_unit_raw:
        claimed_norm = _normalize_unit(claimed_unit_raw)
        actual_norm = _normalize_unit(record["unit"])
        data["claimed_unit_normalized"] = claimed_norm
        if claimed_norm != actual_norm and claimed_unit_raw.lower() != record["unit"].lower():
            return mismatch(
                name,
                f"{canonical} unit mismatch: actual {record['unit']}, claimed {claimed_unit_raw}",
                data,
            )
    if diff <= threshold:
        return confirm(
            name,
            f"{canonical} = {actual} {record['unit']} (claim {claim} within {rel_tol:.0e})",
            data,
        )
    return mismatch(
        name,
        f"{canonical} actual {actual} {record['unit']}, claimed {claim}",
        data,
    )


def list_constants() -> List[Dict[str, Any]]:
    """Public listing — useful for /agents and for documentation pages."""
    out = []
    for key, rec in _CONSTANTS.items():
        out.append({
            "constant": key,
            "value": rec["value"],
            "unit": rec["unit"],
            "exact": rec.get("exact", False),
            "note": rec.get("note", ""),
        })
    return sorted(out, key=lambda x: x["constant"])


# Derived-constant RELATIONS — each is an exact physical identity computed from the constants
# above. The engine can seal the RELATION (does the formula reproduce the target constant?)
# without ever judging a measured value: the inputs and the target are both CODATA table
# values and the check is pure arithmetic. The web of constants as edges, not islands.
_RELATIONS: Dict[str, Dict[str, Any]] = {
    "fine_structure_constant": {
        "target": "fine_structure_constant",
        "formula": "alpha = e^2 / (2 * epsilon_0 * h * c)",
        "inputs": ["elementary_charge", "vacuum_permittivity", "planck_constant", "speed_of_light"],
        "compute": lambda C: C["elementary_charge"] ** 2
        / (2 * C["vacuum_permittivity"] * C["planck_constant"] * C["speed_of_light"]),
    },
    "reduced_planck_constant": {
        "target": "reduced_planck_constant",
        "formula": "hbar = h / (2*pi)",
        "inputs": ["planck_constant"],
        "compute": lambda C: C["planck_constant"] / (2 * math.pi),
    },
    "gas_constant": {
        "target": "gas_constant",
        "formula": "R = N_A * k_B",
        "inputs": ["avogadro_constant", "boltzmann_constant"],
        "compute": lambda C: C["avogadro_constant"] * C["boltzmann_constant"],
    },
    "faraday_constant": {
        "target": "faraday_constant",
        "formula": "F = N_A * e",
        "inputs": ["avogadro_constant", "elementary_charge"],
        "compute": lambda C: C["avogadro_constant"] * C["elementary_charge"],
    },
    "vacuum_permittivity": {
        "target": "vacuum_permittivity",
        "formula": "epsilon_0 = 1 / (mu_0 * c^2)",
        "inputs": ["vacuum_permeability", "speed_of_light"],
        "compute": lambda C: 1.0 / (C["vacuum_permeability"] * C["speed_of_light"] ** 2),
    },
    "bohr_radius": {
        "target": "bohr_radius",
        "formula": "a_0 = epsilon_0 * h^2 / (pi * m_e * e^2)",
        "inputs": ["vacuum_permittivity", "planck_constant", "electron_mass", "elementary_charge"],
        "compute": lambda C: C["vacuum_permittivity"] * C["planck_constant"] ** 2
        / (math.pi * C["electron_mass"] * C["elementary_charge"] ** 2),
    },
}


def verify_constant_relation(spec: Dict[str, Any]) -> VerifierResult:
    """Check that a named DERIVED relation reproduces its target constant.

    Computes a fundamental constant from OTHER constants via an exact physical identity
    (e.g. alpha = e^2 / (2 epsilon_0 h c)) using the CODATA table, and confirms it matches the
    table's own value for that constant within a relative tolerance. This seals the RELATION
    between constants -- an edge in the web -- never a measured value: both the inputs and the
    target are reference values, and the check is pure arithmetic.

    Spec (artifact key CONST_RELATION):
        {"relation": "fine_structure_constant" | "alpha" | "gas_constant" | ...,
         "rel_tol": 1e-6}    # optional, clamped (tighten-only)
    """
    name = "physical_constants.relation"
    rel = _canonical(spec.get("relation", ""))
    record = _RELATIONS.get(rel)
    if not record:
        return na(name)
    consts = {k: v["value"] for k, v in _CONSTANTS.items()}
    try:
        computed = float(record["compute"](consts))
    except Exception as e:  # noqa: BLE001 — a malformed relation is an ERROR, not a crash
        return error(name, f"relation {rel} failed to compute: {e}")
    target_key = record["target"]
    actual = _CONSTANTS[target_key]["value"]
    rel_tol = clamp_tol(spec, "rel_tol", 1e-6)
    diff = abs(computed - actual)
    rel_diff = diff / abs(actual) if actual else float("inf")
    data = {
        "relation": rel,
        "formula": record["formula"],
        "inputs": record["inputs"],
        "target": target_key,
        "computed_value": computed,
        "table_value": actual,
        "unit": _CONSTANTS[target_key]["unit"],
        "diff": diff,
        "rel_diff": rel_diff,
        "rel_tol": rel_tol,
        "source": "CODATA 2018 / NIST",
    }
    if rel_diff <= rel_tol:
        return confirm(
            name,
            f"{record['formula']}: computed {computed:.10g} matches {target_key} "
            f"{actual:.10g} (rel {rel_diff:.1e} <= {rel_tol:.0e})",
            data,
        )
    return mismatch(
        name,
        f"{record['formula']}: computed {computed:.10g} != {target_key} {actual:.10g} "
        f"(rel {rel_diff:.1e} > {rel_tol:.0e})",
        data,
    )


def list_relations() -> List[Dict[str, Any]]:
    """Public listing of the sealed relations — for /agents and documentation."""
    return [
        {"relation": k, "target": r["target"], "formula": r["formula"], "inputs": r["inputs"]}
        for k, r in sorted(_RELATIONS.items())
    ]


# ── Constant governance: which DOMAINS a fundamental constant governs ────────────────────────
# A domain "falls under" a constant when its characteristic quantities are FUNCTIONS OF that
# constant (or of the quantities the constant defines). This is a PHYSICS fact, curated and
# auditable here -- deliberately NOT a keyword match, so lexical collisions are named and rejected
# (the same discernment the crisis-net and the alignment gate rest on: substance, not the word).
# The same process serves every constant; alpha was the first graph, the rest follow the pattern.
#
# Each entry: sets (one line), defines (the quantities it scales), governed {domain: why},
# descendant {domain: why} (governed only THROUGH a governed domain), rejected {domain: why}
# (a surface-token or spurious association, no real dependence), and code_grounded (the domains
# whose verifier actually computes a quantity THROUGH the constant today; the rest are the gap).
_GOVERNANCE: Dict[str, Dict[str, Any]] = {
    "fine_structure_constant": {
        "sets": "the electromagnetic coupling and the scale of atomic structure",
        "defines": ["elementary_charge (e)", "vacuum_permittivity (epsilon_0)",
                    "rydberg_constant (R_inf = alpha^2 m_e c / 2h)",
                    "bohr_radius (a_0 = hbar / (m_e c alpha))",
                    "electron g-2 anomaly (a_e ~ alpha/2pi)", "fine-structure splitting (~ alpha^2 Ry)"],
        "governed": {
            "atomic": "energy levels E_n = -R_inf h c / n^2; fine-structure ~ alpha^2; a_e ~ alpha/2pi",
            "periodic_table": "shell structure and ionization energies scale with R_inf; Moseley K-alpha",
            "optics": "refractive index / dispersion from atomic polarizability; Thomson (r_e = alpha^2 a_0)",
            "photonics": "light-matter coupling and transition rates scale with alpha; the Compton scale",
            "chemistry": "bond and ionization energies set by the atomic Coulomb scale (Rydberg/Hartree)",
            "electrochemistry": "electrode potentials carried by the elementary charge e (F = N_A e)",
            "condensed_matter": "screened Coulomb interaction; von Klitzing R_K = h/e^2 = mu_0 c/2alpha",
        },
        "descendant": {
            "materials_science": "properties inherited from condensed_matter and chemistry",
            "biology": "molecular biology inherits the chemical (atomic) scale",
            "medicine": "pharmacology inherits molecular chemistry",
            "nuclear_physics": "the Coulomb barrier involves e, but the strong force dominates",
        },
        "rejected": {
            "statistics": "'alpha' here is the significance level, not the coupling",
            "linguistics": "'alphabet' is an unrelated word",
            "finance": "no electromagnetic dependence; a token match only",
        },
        "code_grounded": frozenset({"atomic", "periodic_table", "optics", "photonics",
                                    "chemistry", "electrochemistry", "condensed_matter"}),
    },
    "gravitational_constant": {
        "sets": "the strength of gravitation and the dynamics of orbits and masses",
        "defines": ["orbital period (Kepler T^2 = 4 pi^2 a^3 / G M)",
                    "escape velocity (v = sqrt(2 G M / r))",
                    "Schwarzschild radius (r_s = 2 G M / c^2)", "surface gravity (g = G M / r^2)"],
        "governed": {
            "astronomy": "orbits, Kepler's third law, stellar and galactic dynamics scale with G M",
            "ephemeris": "planetary positions integrate the gravitational N-body problem",
            "physics": "Newtonian gravitation F = G m M / r^2 and its potential energy",
            "geology": "surface gravity, isostasy and the Earth's internal mass distribution",
        },
        "descendant": {
            "oceanography": "tides are the gravitational pull of Moon and Sun",
            "meteorology": "hydrostatic balance uses g, itself set by G",
        },
        "rejected": {
            "economics": "'gravity models' of trade are an analogy, not gravitation",
            "finance": "no gravitational dependence",
        },
        # all four compute through G: astronomy (Newtonian force, Kepler, escape velocity,
        # Schwarzschild), physics (F = G m1 m2 / r^2), geology (surface gravity g = G M / r^2),
        # ephemeris (orbital period T = 2 pi sqrt(a^3 / G M)).
        "code_grounded": frozenset({"astronomy", "physics", "geology", "ephemeris"}),
    },
    "boltzmann_constant": {
        "sets": "the thermal energy scale, linking temperature to energy",
        "defines": ["thermal energy (k_B T)", "Boltzmann factor (exp(-E/k_B T))",
                    "entropy (S = k_B ln W)", "gas constant (R = N_A k_B)"],
        "governed": {
            "thermodynamics": "k_B T is the thermal energy quantum; entropy S = k_B ln W",
            "chemistry": "reaction equilibria and Arrhenius rates go as exp(-E/k_B T)",
            "meteorology": "the barometric scale height H = k_B T / m g",
            "materials_science": "Fermi-Dirac / Bose-Einstein occupancy and thermal transport",
        },
        "descendant": {
            "biology": "molecular processes run on thermal (k_B T) energy",
            "ecology": "metabolic rates inherit the thermal scale",
        },
        "rejected": {
            "finance": "no thermal dependence",
            "law": "no thermal dependence",
        },
        # thermodynamics (S=k_B ln W), chemistry (Boltzmann factor), meteorology (scale height)
        # and materials_science (thermal energy k_B T) all compute through k_B.
        "code_grounded": frozenset({"thermodynamics", "chemistry", "meteorology", "materials_science"}),
    },
    "speed_of_light": {
        "sets": "the speed of causal propagation and the mass-energy relation",
        "defines": ["mass-energy (E = m c^2)", "relativistic energy and momentum",
                    "light-travel time and distance", "impedance of free space (Z_0 = mu_0 c)"],
        "governed": {
            "physics": "special relativity: E = m c^2, time dilation, the Lorentz factor",
            "nuclear_physics": "binding energies and Q-values via E = m c^2",
            "optics": "the phase velocity c/n and all electromagnetic wave propagation",
            "astronomy": "light-travel time, redshift and cosmological distance",
        },
        "descendant": {
            "photonics": "propagation delay and phase inherit c",
            "networking": "signal latency is bounded by c",
        },
        "rejected": {
            "finance": "no dependence on the speed of light",
        },
        # physics (E=mc^2, Lorentz), nuclear (rest energy), optics (photon energy E=hc/lambda) and
        # astronomy (light-travel) all compute through c.
        "code_grounded": frozenset({"physics", "nuclear_physics", "optics", "astronomy"}),
    },
    "planck_constant": {
        "sets": "the quantum of action -- the scale at which quantization matters",
        "defines": ["photon energy (E = h nu)", "de Broglie wavelength (lambda = h/p)",
                    "the uncertainty bound (dx dp >= hbar/2)", "quantized angular momentum"],
        "governed": {
            "quantum_computing": "qubit energies and gate dynamics are set by h",
            "atomic": "quantized energy levels and angular momentum",
            "photonics": "photon energy E = h nu",
            "condensed_matter": "band quantization and the flux quantum",
        },
        "descendant": {
            "chemistry": "orbital quantization inherits h through atomic structure",
        },
        "rejected": {
            "finance": "no dependence on the quantum of action",
        },
        # quantum_computing (E=hf), photonics (E=h nu) compute through h directly; atomic (Rydberg
        # energy R_inf h c) and condensed_matter (von Klitzing R_K=h/e^2) compute through it too.
        "code_grounded": frozenset({"quantum_computing", "atomic", "photonics", "condensed_matter"}),
    },
    "avogadro_constant": {
        "sets": "the number of entities per mole -- the bridge from atoms to laboratory amounts",
        "defines": ["molar mass and molar quantities", "gas constant (R = N_A k_B)",
                    "Faraday constant (F = N_A e)"],
        "governed": {
            "chemistry": "stoichiometry, molar mass and the mole itself",
            "thermodynamics": "the gas constant R = N_A k_B",
            "electrochemistry": "the Faraday constant F = N_A e",
        },
        "descendant": {
            "nutrition": "amounts per serving convert through moles",
            "medicine": "dosing converts mass to moles",
        },
        "rejected": {
            "finance": "no dependence on the mole",
        },
        # chemistry (N = n N_A), thermodynamics (R = N_A k_B) and electrochemistry (F = N_A e)
        # all compute through N_A.
        "code_grounded": frozenset({"chemistry", "thermodynamics", "electrochemistry"}),
    },
}


def governance(constant: str) -> Dict[str, Any]:
    """The reach of a fundamental constant across the domains, curated from the physics.

    Returns the tiers -- governed / descendant / rejected -- with the governing reason for each,
    plus the gap: the governed domains whose verifier does not yet compute THROUGH the constant.
    A physical-governance graph rooted in the constant web, NOT a lexical scan, so it is stable,
    auditable, and free of surface-token false positives. The one repeatable process for every
    constant; alpha was the first. Pass a canonical name ('fine_structure_constant',
    'gravitational_constant', ...) or an alias the constant table knows.
    """
    key = _canonical(constant)
    g = _GOVERNANCE.get(key)
    if not g:
        return {"constant": key, "error": "no governance graph",
                "available": sorted(_GOVERNANCE)}
    cg = g["code_grounded"]
    governed = {d: {"why": w, "code_grounded": d in cg} for d, w in g["governed"].items()}
    return {
        "constant": key,
        "sets": g["sets"],
        "defines": g["defines"],
        "governed": governed,
        "descendant": g["descendant"],
        "rejected": g["rejected"],
        "gap": sorted(d for d in g["governed"] if d not in cg),
        "method": "curated physical-governance graph rooted in the constant web; "
                  "surface-token matches rejected",
    }


def list_governed_constants() -> List[str]:
    """The fundamental constants that carry a governance graph."""
    return sorted(_GOVERNANCE)


def alpha_governance() -> Dict[str, Any]:
    """Back-compat alias: the governance graph for the fine structure constant."""
    return governance("fine_structure_constant")


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    results: List[VerifierResult] = []
    cv = packet.get("CONST_VERIFY") or {}
    if cv.get("constant") and cv.get("claimed_value") is not None:
        results.append(verify_physical_constant(cv))
    cr = packet.get("CONST_RELATION") or {}
    if cr.get("relation"):
        results.append(verify_constant_relation(cr))
    if not results:
        results.append(na("physical_constants", "no artifact provided"))
    return results
