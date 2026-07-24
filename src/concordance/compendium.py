"""The Works — a technical volume bound into the one book.

Matt: "show the depth of mathematics, science, and engineering we can achieve with the tools …
a technical document that is available and could be a part of the concordance which is the
entire book/project … all packaged into one product experience." And then: "cover all of
reality."

This is that volume. It is NOT prose that *claims* capability — it is a set of worked
demonstrations that are each run through the SAME engine that guards the moat, and each carries
a permanent, re-checkable seal (cite_url → /s/<hash>). Proof, not assertion (docs discipline):
the reader does not trust us; they open the seal and re-check the math themselves.

Conduit, not source: the engine verifies a PROVIDED derivation line by line; it never generates
the answer. Every demonstration here is a claim we hand it and it either confirms or breaks. The
numbers were not authored by hand — they were read back FROM the engine's own computation.

Five parts, reaching across reality:
    I   Mathematics & Logic
    II  Physical Science
    III Earth, Sky & Life
    IV  Engineering & Computation
    V   Society & the Human World

It grows: add a demonstration to DEMONSTRATIONS, rebuild, the book deepens. Only demonstrations
that actually HOLD are published; one the engine cannot confirm is dropped and logged — never
quietly shown as if it passed.

Build (run every demonstration through the engine + mint its seal + sign the volume):
    PYTHONPATH=src python -m concordance.compendium
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import EngineConfig
from .derivation import verify_derivation
from . import receipts

_log = logging.getLogger("concordance.compendium")


# ── spec helpers (mathematics moat) ──────────────────────────────────────────
def _eq(a: str, b: str) -> Dict[str, Any]:
    return {"mode": "equality", "params": {"expr_a": a, "expr_b": b, "variables": {}}}


def _dv(f: str, v: str, d: str) -> Dict[str, Any]:
    return {"mode": "derivative", "params": {"function": f, "variable": v, "claimed_derivative": d}}


# The parts of the volume, in order.
PARTS = [
    ("mathematics", "I · Mathematics & Logic"),
    ("physical", "II · Physical Science"),
    ("earth_life", "III · Earth, Sky & Life"),
    ("engineering", "IV · Engineering & Computation"),
    ("society", "V · Society & the Human World"),
]


# ── The demonstrations ───────────────────────────────────────────────────────
# Each: id, discipline (one of PARTS), field, title, narrative, steps.
# A step is a real verifier claim: {id, domain, spec, claim, uses?}. `spec` for math is
# {mode, params}; for every other domain it is that verifier's flat structured packet (wrapped
# into its typed artifact key at run time). EVERY value here was read back from the engine's own
# computation — the engine is what proves it, not this file.
def _M(cid, field, title, narrative, steps):
    return {"id": cid, "discipline": "mathematics", "field": field, "title": title,
            "narrative": narrative, "steps": steps}


def _demo(disc):
    def mk(cid, field, title, narrative, steps):
        return {"id": cid, "discipline": disc, "field": field, "title": title,
                "narrative": narrative, "steps": steps}
    return mk


_P, _E, _L, _S = _demo("physical"), _demo("engineering"), _demo("earth_life"), _demo("society")


DEMONSTRATIONS: List[Dict[str, Any]] = [
    # ══════════════ I · MATHEMATICS & LOGIC ══════════════
    _M("works_euler_identity", "Complex analysis",
       "Euler's identity, assembled from its parts",
       "Often called the most beautiful equation in mathematics: it binds e, i, π, 1 and 0 in a "
       "single line. We hand the engine each piece and the whole, and it confirms every one.",
       [{"id": "e1", "domain": "mathematics", "spec": _eq("cos(pi)", "-1"), "claim": "cos(π) = −1"},
        {"id": "e2", "domain": "mathematics", "spec": _eq("sin(pi)", "0"), "claim": "sin(π) = 0"},
        {"id": "e3", "domain": "mathematics", "spec": _eq("exp(I*pi)+1", "0"),
         "claim": "e^{iπ} + 1 = 0", "uses": ["e1", "e2"]}]),
    _M("works_calculus_chain", "Calculus",
       "Differentiate twice: position → velocity → acceleration",
       "A body's position goes as t³ in this toy law. Differentiate once for velocity, again for "
       "acceleration. Each differentiation is machine-checked; the second stands on the first.",
       [{"id": "c1", "domain": "mathematics", "spec": _dv("t**3", "t", "3*t**2"),
         "claim": "d/dt (t³) = 3t²  (position → velocity)"},
        {"id": "c2", "domain": "mathematics", "spec": _dv("3*t**2", "t", "6*t"),
         "claim": "d/dt (3t²) = 6t  (velocity → acceleration)", "uses": ["c1"]}]),
    _M("works_trig_identities", "Trigonometry",
       "From the unit circle to the double-angle law",
       "The Pythagorean identity is the unit circle written as algebra; the double-angle law for "
       "cosine follows in its train. Both are confirmed exactly (not sampled), for all x.",
       [{"id": "t1", "domain": "mathematics", "spec": _eq("sin(x)**2+cos(x)**2", "1"),
         "claim": "sin²x + cos²x = 1"},
        {"id": "t2", "domain": "mathematics", "spec": _eq("cos(2*x)", "1-2*sin(x)**2"),
         "claim": "cos 2x = 1 − 2 sin²x", "uses": ["t1"]}]),
    _M("works_number_theory", "Number theory",
       "The integers, examined: a prime, a divisor, a factorial",
       "Exact facts about whole numbers, decided by algorithm, not by eye: 97 is prime; 48 and 36 "
       "share a greatest common divisor of 12; and 6! counts the orderings of six things.",
       [{"id": "p1", "domain": "number_theory", "spec": {"n_prime": 97, "claimed_prime": True},
         "claim": "97 is prime"},
        {"id": "g1", "domain": "number_theory", "spec": {"gcd_a": 48, "gcd_b": 36, "claimed_gcd": 12},
         "claim": "gcd(48, 36) = 12", "uses": ["p1"]},
        {"id": "f1", "domain": "number_theory", "spec": {"factorial_n": 6, "claimed_factorial": 720},
         "claim": "6! = 720", "uses": ["g1"]}]),
    _M("works_counting", "Combinatorics",
       "Counting: how many ways to choose and to arrange",
       "From five things, there are 20 ordered pairs but only 10 unordered pairs — order is the "
       "whole difference between a permutation and a combination.",
       [{"id": "pm1", "domain": "combinatorics", "spec": {"perm_n": 5, "perm_k": 2, "claimed_permutations": 20},
         "claim": "P(5,2) = 5!/3! = 20"},
        {"id": "cm1", "domain": "combinatorics", "spec": {"comb_n": 5, "comb_k": 2, "claimed_combinations": 10},
         "claim": "C(5,2) = 10", "uses": ["pm1"]}]),
    _M("works_linear_algebra", "Linear algebra",
       "Vectors and matrices: a dot product and a determinant",
       "The dot product of two 3-vectors measures how they align; the determinant of a 2×2 matrix "
       "measures the signed area it scales. Both computed exactly.",
       [{"id": "dp1", "domain": "linear_algebra",
         "spec": {"vec_a": [1, 2, 3], "vec_b": [4, 5, 6], "claimed_dot_product": 32},
         "claim": "[1,2,3]·[4,5,6] = 4+10+18 = 32"},
        {"id": "dt1", "domain": "linear_algebra",
         "spec": {"matrix": [[1, 2], [3, 4]], "claimed_determinant": -2},
         "claim": "det [[1,2],[3,4]] = 1·4 − 2·3 = −2", "uses": ["dp1"]}]),
    _M("works_probability", "Probability",
       "Ten fair coins: the average and a particular outcome",
       "Flip a fair coin ten times. On average five come up heads; the chance of exactly two heads "
       "is C(10,2)/2¹⁰. The engine confirms both the expectation and the exact probability.",
       [{"id": "bm1", "domain": "probability",
         "spec": {"binomial_n": 10, "binomial_p": 0.5, "claimed_binomial_mean": 5},
         "claim": "E[Binom(10, ½)] = n·p = 5"},
        {"id": "bp1", "domain": "probability",
         "spec": {"binomial_n": 10, "binomial_p": 0.5, "binomial_k": 2,
                  "claimed_binomial_probability": 0.0439453125},
         "claim": "P(X=2) = C(10,2)·½¹⁰ = 45/1024 ≈ 0.04395", "uses": ["bm1"]}]),
    _M("works_logic", "Formal logic",
       "Two laws of thought, checked over every case",
       "The law of excluded middle (p or not-p is always true) and De Morgan's law are verified "
       "across the entire truth table — not argued, exhaustively decided.",
       [{"id": "lt1", "domain": "formal_logic",
         "spec": {"formula": "p | ~p", "claimed_tautology": True, "variables": ["p"]},
         "claim": "p ∨ ¬p is a tautology"},
        {"id": "le1", "domain": "formal_logic",
         "spec": {"formula_a": "~(p & q)", "formula_b": "~p | ~q", "claimed_equivalent": True,
                  "variables": ["p", "q"]},
         "claim": "¬(p ∧ q) ≡ ¬p ∨ ¬q  (De Morgan)", "uses": ["lt1"]}]),
    _M("works_information", "Information theory",
       "Measuring information: one bit, and a distance",
       "A single fair coin carries exactly one bit of Shannon entropy; the Hamming distance counts "
       "how many positions two codewords differ in — the ground of error correction.",
       [{"id": "sh1", "domain": "information_theory",
         "spec": {"probabilities": [0.5, 0.5], "claimed_entropy_bits": 1.0},
         "claim": "H(½,½) = 1 bit"},
        {"id": "hd1", "domain": "information_theory",
         "spec": {"string_a": "1011", "string_b": "1001", "claimed_hamming": 1},
         "claim": "Hamming(1011, 1001) = 1", "uses": ["sh1"]}]),
    _M("works_statistics", "Statistics",
       "A p-value against a threshold",
       "With significance set at 0.05, an observed p of 0.03 clears the bar — the result is "
       "statistically significant. The engine checks the decision is consistent with the numbers.",
       [{"id": "st1", "domain": "statistics",
         "spec": {"p_value": 0.03, "alpha": 0.05, "claimed_significance": "significant"},
         "claim": "p = 0.03 ≤ α = 0.05 → significant"}]),
    _M("works_bayes", "Probability / Bayes",
       "The base rate a doctor must not forget",
       "A disease affects 1 in 100. A test is 90% sensitive and has a 5% false-positive rate. A "
       "positive result feels alarming — yet Bayes' theorem shows the chance of actually being "
       "ill is only about 15%. The base rate rules.",
       [{"id": "by1", "domain": "probability",
         "spec": {"p_a": 0.01, "p_b_given_a": 0.9, "p_b_given_not_a": 0.05,
                  "claimed_p_a_given_b": 0.15384615384615385},
         "claim": "P(ill | +) = (.9·.01)/(.9·.01 + .05·.99) ≈ 0.154"}]),
    _M("works_polygon", "Plane geometry",
       "The angles inside a hexagon",
       "The interior angles of any n-sided polygon sum to (n−2)·180°. For a hexagon that is 720° — "
       "the reason six equilateral triangles, or a honeycomb, tile the plane.",
       [{"id": "pg1", "domain": "geometry",
         "spec": {"polygon_n": 6, "claimed_interior_angle_sum_deg": 720},
         "claim": "(6−2)·180° = 720°"}]),

    # ══════════════ II · PHYSICAL SCIENCE ══════════════
    _P("works_mechanics", "Classical mechanics",
       "A 2 kg mass: the force to move it, the energy it carries",
       "Newton's second law fixes the force to accelerate a mass; its kinetic energy fixes what "
       "the motion is worth. Same mass, two laws, both checked.",
       [{"id": "n1", "domain": "physics",
         "spec": {"mass_kg": 2, "acceleration_m_per_s2": 5, "claimed_force_N": 10},
         "claim": "F = m·a = 2·5 = 10 N"},
        {"id": "k1", "domain": "physics",
         "spec": {"mass_kg": 2, "velocity_m_per_s": 3, "claimed_kinetic_energy_J": 9},
         "claim": "KE = ½·m·v² = ½·2·3² = 9 J", "uses": ["n1"]}]),
    _P("works_free_fall", "Kinematics",
       "Free fall: how far in two seconds",
       "Drop something from rest near Earth. Constant g = 9.8 m/s² carries it 19.6 m in two "
       "seconds — s = ½·a·t².",
       [{"id": "d1", "domain": "physics",
         "spec": {"v0": 0, "a": 9.8, "t": 2, "claimed_displacement": 19.6},
         "claim": "s = ½·g·t² = ½·9.8·2² = 19.6 m"}]),
    _P("works_thermo_carnot", "Thermodynamics",
       "The Carnot ceiling no engine can beat",
       "Between a hot reservoir at 400 K and a cold one at 300 K, the second law caps efficiency at "
       "1 − T_cold/T_hot = 25%. Not a target — a law.",
       [{"id": "ca1", "domain": "thermodynamics",
         "spec": {"T_hot_K": 400, "T_cold_K": 300, "claimed_efficiency": 0.25},
         "claim": "η = 1 − 300/400 = 0.25"}]),
    _P("works_ideal_gas", "Thermodynamics",
       "The ideal gas law solves for temperature",
       "PV = nRT. Given a pressure, a volume and an amount, the temperature is fixed — one mole in "
       "22.4 litres at one atmosphere sits near the freezing point of water.",
       [{"id": "ig1", "domain": "thermodynamics",
         "spec": {"pressure_Pa": 101325, "volume_m3": 0.0224, "moles": 1,
                  "claimed_temperature_K": 272.9949482800096},
         "claim": "T = PV/(nR) ≈ 273 K"}]),
    _P("works_chemistry", "Chemistry",
       "Chemistry, two ways: will it run, and is it acid",
       "Gibbs free energy decides whether a reaction proceeds on its own (ΔG = ΔH − TΔS < 0); pH "
       "places a solution on the acid–base scale. Two questions, one deterministic answer each.",
       [{"id": "gi1", "domain": "chemistry",
         "spec": {"delta_H_kJ_mol": -100, "delta_S_J_mol_K": 50, "temperature_K": 298,
                  "claimed_spontaneous": True},
         "claim": "ΔG = −100 − 298·0.050 < 0 → spontaneous"},
        {"id": "ph1", "domain": "chemistry", "spec": {"pH": 3.0, "claimed_classification": "acidic"},
         "claim": "pH 3.0 → acidic", "uses": ["gi1"]}]),
    _P("works_snell", "Optics",
       "Light bends: Snell's law at a glass surface",
       "Passing from air into glass (n = 1.5) at 30°, a ray refracts to 19.47° — n₁ sin θ₁ = "
       "n₂ sin θ₂. The same law bends every lens and every rainbow.",
       [{"id": "sn1", "domain": "optics",
         "spec": {"n1": 1.0, "n2": 1.5, "theta1_deg": 30, "claimed_theta2_deg": 19.471220634490688},
         "claim": "sin θ₂ = (1·sin30)/1.5 → θ₂ ≈ 19.47°"}]),
    _P("works_photon", "Quantum / optics",
       "The energy in a single green photon",
       "A photon of 500 nm light carries E = hc/λ ≈ 3.97 × 10⁻¹⁹ joules — the quantum of energy "
       "that a leaf's chlorophyll is built to catch.",
       [{"id": "pe1", "domain": "optics",
         "spec": {"wavelength_m": 5e-7, "claimed_photon_energy_j": 3.972891714297857e-19},
         "claim": "E = hc/λ ≈ 3.97 × 10⁻¹⁹ J"}]),
    _P("works_acoustics", "Acoustics",
       "The wave equation for sound",
       "For any wave, speed = frequency × wavelength. A 343 Hz tone with a one-metre wavelength "
       "travels at 343 m/s — the speed of sound in air.",
       [{"id": "wv1", "domain": "acoustics",
         "spec": {"speed_of_wave": 343, "frequency_hz": 343, "wavelength_m": 1.0},
         "claim": "c = f·λ = 343·1 = 343 m/s"}]),
    _P("works_astronomy", "Astronomy",
       "Kepler's law, and the pull between Earth and Moon",
       "Kepler's third law binds a planet's period to its orbit (T² = a³); Newton's gravity gives "
       "the force holding the Moon — about 2 × 10²⁰ newtons.",
       [{"id": "kp1", "domain": "astronomy",
         "spec": {"orbital_period_years": 1, "semi_major_axis_au": 1, "claimed_kepler_consistent": True},
         "claim": "T² = a³ for Earth (1 yr, 1 AU)"},
        {"id": "gr1", "domain": "astronomy",
         "spec": {"mass_1_kg": 5.972e24, "mass_2_kg": 7.348e22, "separation_m": 3.844e8,
                  "claimed_gravitational_force_N": 1.982110729079252e20},
         "claim": "F = G·M·m/r² ≈ 1.98 × 10²⁰ N (Earth–Moon)", "uses": ["kp1"]}]),
    _P("works_nuclear", "Nuclear physics",
       "A radioactive clock's decay constant",
       "A nuclide with a ten-second half-life decays at λ = ln2 / T½ ≈ 0.0693 per second — the "
       "same relation that dates rock and bone.",
       [{"id": "dk1", "domain": "nuclear_physics",
         "spec": {"half_life_seconds": 10, "claimed_decay_constant": 0.06931471805599453},
         "claim": "λ = ln2 / 10 ≈ 0.0693 s⁻¹"}]),
    _P("works_vsepr", "Molecular geometry",
       "Why methane is a tetrahedron",
       "Four bonding pairs and no lone pairs around a central atom push apart into a tetrahedron "
       "with 109.47° angles — the shape of methane, and of carbon's whole architecture.",
       [{"id": "vs1", "domain": "molecular_geometry",
         "spec": {"bonding_domains": 4, "lone_pairs": 0, "claimed_geometry": "tetrahedral",
                  "claimed_bond_angle_deg": 109.47122063449069},
         "claim": "4 bonds, 0 lone pairs → tetrahedral, 109.47°"}]),
    _P("works_grover", "Quantum computing",
       "How many steps Grover's search needs",
       "To find one item among four with a quantum computer, Grover's algorithm needs just one "
       "iteration — ⌊π√N/4⌋ — where a classical search averages 2.5 look-ups.",
       [{"id": "gv1", "domain": "quantum_computing",
         "spec": {"n_items": 4, "claimed_grover_iterations": 1},
         "claim": "T = ⌊π√4 / 4⌋ = 1 iteration"}]),
    _P("works_constant_c", "Physical constants",
       "The speed of light is a defined exact number",
       "Since 1983 the metre is defined so that light travels 299,792,458 metres per second "
       "exactly — a constant of nature promoted to a fixed integer.",
       [{"id": "cc1", "domain": "physical_constants",
         "spec": {"constant": "speed_of_light", "claimed_value": 299792458.0, "claimed_unit": "m/s",
                  "exact": True},
         "claim": "c = 299,792,458 m/s (exact)"}]),
    _P("works_atom", "Atomic physics",
       "The electrons of sodium, shell by shell",
       "Sodium's eleven electrons fill the shells in a fixed order — 1s² 2s² 2p⁶ 3s¹ — and that "
       "one lonely outer electron is the whole reason sodium is so reactive.",
       [{"id": "at1", "domain": "atomic",
         "spec": {"atomic_number": 11, "claimed_configuration": "1s2 2s2 2p6 3s1"},
         "claim": "Z=11 ground state = 1s² 2s² 2p⁶ 3s¹"}]),
    _P("works_element", "Periodic table",
       "Carbon, by definition",
       "An element's identity is definitional, not measured: the element with six protons is "
       "carbon, symbol C. Identity, reduced to a proton count.",
       [{"id": "el1", "domain": "periodic_table",
         "spec": {"atomic_number": 6, "claimed_symbol": "C"},
         "claim": "Z = 6 ↔ carbon (C)"}]),
    _P("works_julian_day", "Positional astronomy",
       "The running day-count astronomers keep",
       "Astronomers count time in Julian days — an unbroken tally of days. Noon on 1 January 2000 "
       "is Julian day 2,451,545, the modern epoch J2000.",
       [{"id": "jd1", "domain": "ephemeris",
         "spec": {"iso_date": "2000-01-01", "claimed_julian_day": 2451545.0},
         "claim": "JD(2000-01-01) = 2,451,545"}]),

    # ══════════════ III · EARTH, SKY & LIFE ══════════════
    _L("works_radiometric", "Geochronology",
       "One half-life of a radioactive clock",
       "After one half-life — 5,730 years for carbon-14 — exactly half the original atoms remain. "
       "This is how charcoal, bone and shell are dated.",
       [{"id": "rd1", "domain": "geology",
         "spec": {"isotope_half_life_years": 5730, "elapsed_years": 5730, "initial_amount": 100,
                  "claimed_remaining_amount": 50},
         "claim": "N = 100·½¹ = 50 after one half-life"}]),
    _L("works_haversine", "Geodesy",
       "The great-circle distance from New York to London",
       "Across the curved Earth, the shortest path (the haversine great-circle distance) from New "
       "York to London is about 5,570 km — the number behind every flight plan and GPS fix.",
       [{"id": "hv1", "domain": "geography",
         "spec": {"lat1": 40.7128, "lon1": -74.0060, "lat2": 51.5074, "lon2": -0.1278,
                  "claimed_distance_km": 5570.222179737958},
         "claim": "haversine(NYC → London) ≈ 5,570 km"}]),
    _L("works_dew_point", "Meteorology",
       "When dew forms: the dew point",
       "Air at 20 °C and 50% humidity will bead with dew once it cools to about 9.26 °C — the "
       "Magnus formula the weather service uses.",
       [{"id": "dw1", "domain": "meteorology",
         "spec": {"temperature_c": 20, "relative_humidity_pct": 50,
                  "claimed_dew_point_c": 9.261106630534236},
         "claim": "dew point(20 °C, 50%) ≈ 9.26 °C"}]),
    _L("works_manning", "Hydrology",
       "How fast water runs in an open channel",
       "Manning's equation gives the velocity of water in a channel from its roughness, depth and "
       "slope — here 3.33 m/s. It sizes culverts, canals and storm drains.",
       [{"id": "mn1", "domain": "hydrology",
         "spec": {"manning_n": 0.03, "hydraulic_radius_m": 1, "slope": 0.01,
                  "claimed_velocity_m_s": 3.333333333333334},
         "claim": "V = (1/0.03)·1^⅔·0.01^½ = 3.33 m/s"}]),
    _L("works_wave_speed", "Oceanography",
       "How fast a 100-metre ocean swell travels",
       "In deep water a wave's speed grows with its wavelength: c = √(gλ/2π). A 100 m swell moves "
       "at about 12.5 m/s — long waves outrun short ones and arrive first.",
       [{"id": "ws1", "domain": "oceanography",
         "spec": {"wavelength_m": 100, "claimed_wave_speed_m_per_s": 12.495239060264087},
         "claim": "c = √(9.81·100 / 2π) ≈ 12.5 m/s"}]),
    _L("works_carbon", "Ecology",
       "The carbon cost of a hundred kilometres",
       "Emissions are distance times an emission factor: 100 km at 0.2 kg CO₂/km is 20 kg of "
       "carbon dioxide — the arithmetic under any honest footprint.",
       [{"id": "cf1", "domain": "ecology",
         "spec": {"distance_km": 100, "emission_factor_kg_per_km": 0.2, "claimed_co2_kg": 20},
         "claim": "CO₂ = 100·0.2 = 20 kg"}]),
    _L("works_soil", "Soil science",
       "Reading a soil by its texture",
       "40% sand, 40% silt, 20% clay lands squarely in loam on the USDA texture triangle — the "
       "balance a gardener hopes for.",
       [{"id": "sx1", "domain": "soil_science",
         "spec": {"sand_pct": 40, "silt_pct": 40, "clay_pct": 20, "claimed_texture_class": "loam"},
         "claim": "40/40/20 sand/silt/clay → loam"}]),
    _L("works_genetics", "Molecular biology",
       "Reading and mirroring a strand of DNA",
       "A strand's GC content and its reverse complement are fixed by the base-pairing rules — "
       "A with T, G with C. Here GGCC is all GC, and ATGC mirrors to GCAT.",
       [{"id": "gc1", "domain": "genetics", "spec": {"sequence": "GGCC", "claimed_gc_fraction": 1.0},
         "claim": "GC(GGCC) = 4/4 = 1.0"},
        {"id": "rc1", "domain": "genetics",
         "spec": {"sequence": "ATGC", "claimed_reverse_complement": "GCAT"},
         "claim": "revcomp(ATGC) = GCAT", "uses": ["gc1"]}]),
    _L("works_nutrition", "Nutrition",
       "Calories from macronutrients, and a BMI",
       "Carbohydrate and protein carry 4 kcal per gram; a body-mass index of 22.9 sits in the "
       "normal range. The bookkeeping of the body.",
       [{"id": "mc1", "domain": "nutrition",
         "spec": {"carb_g": 10, "protein_g": 10, "fat_g": 0, "calories_claimed": 80},
         "claim": "10 g carb + 10 g protein = 80 kcal"},
        {"id": "bm1", "domain": "nutrition",
         "spec": {"weight_kg": 70, "height_m": 1.75, "claimed_bmi_class": "normal"},
         "claim": "BMI = 70/1.75² = 22.9 → normal", "uses": ["mc1"]}]),
    _L("works_heart_rate", "Exercise physiology",
       "A thirty-year-old's maximum heart rate",
       "The Tanaka formula estimates maximum heart rate as 208 − 0.7·age — 187 bpm at thirty, the "
       "modern refinement of the old 220 − age rule.",
       [{"id": "hr1", "domain": "exercise_science",
         "spec": {"age_years": 30, "claimed_max_hr": 187.0},
         "claim": "HRmax = 208 − 0.7·30 = 187 bpm"}]),
    _L("works_medicine", "Clinical medicine",
       "The body's numbers: mean pressure and a safe dose",
       "Mean arterial pressure — what actually perfuses the organs — is DBP + (SBP−DBP)/3, about "
       "93 mmHg at 120/80. And a 10 mg/kg drug in a 70 kg adult is a 700 mg dose. The bedside "
       "arithmetic that must not be wrong.",
       [{"id": "mp1", "domain": "medicine",
         "spec": {"systolic": 120, "diastolic": 80, "claimed_map_mmhg": 93.33},
         "claim": "MAP = 80 + (120−80)/3 ≈ 93.3 mmHg"},
        {"id": "dd1", "domain": "medicine",
         "spec": {"dose_mg_per_kg": 10, "weight_kg": 70, "claimed_dose_mg": 700},
         "claim": "dose = 10 mg/kg · 70 kg = 700 mg", "uses": ["mp1"]}]),

    # ══════════════ IV · ENGINEERING & COMPUTATION ══════════════
    _E("works_ohms_law", "Electrical engineering",
       "A 12-volt circuit: the current it draws, the power it burns",
       "Ohm's law ties voltage, current and resistance; the power law says how much heat that "
       "makes. 12 V across 6 Ω draws 2 A and dissipates 24 W — the power line standing on Ohm's.",
       [{"id": "o1", "domain": "electrical",
         "spec": {"voltage_V": 12, "current_A": 2, "resistance_ohm": 6},
         "claim": "V = I·R → 12 = 2·6"},
        {"id": "pw1", "domain": "electrical",
         "spec": {"voltage_V": 12, "current_A": 2, "power_W_claim": 24},
         "claim": "P = V·I = 12·2 = 24 W", "uses": ["o1"]}]),
    _E("works_framing_square", "Structural / construction",
       "The 3-4-5 the builders use to square a corner",
       "A triangle with sides 3, 4, 5 is exactly right-angled — 3² + 4² = 5². It is why a knotted "
       "rope or a framing square gives a true corner without a protractor.",
       [{"id": "fs1", "domain": "geometry",
         "spec": {"pyth_a": 3, "pyth_b": 4, "pyth_c": 5, "claimed_right_triangle": True},
         "claim": "3² + 4² = 5² → a true right angle"}]),
    _E("works_spherical_tank", "Mechanical / geometry",
       "Sizing a spherical tank of radius 3",
       "For a sphere of radius 3, the volume is (4/3)πr³ and the surface area is 4πr² — both come "
       "to 36π here, decided to full precision.",
       [{"id": "sv1", "domain": "geometry",
         "spec": {"sphere_radius": 3, "claimed_sphere_volume": 113.09733552923255,
                  "claimed_sphere_surface_area": 113.09733552923255},
         "claim": "V = (4/3)π·3³ = 36π ≈ 113.097 ;  A = 4π·3² ≈ 113.097"}]),
    _E("works_concrete", "Civil / construction",
       "The concrete for a slab",
       "A slab 5 m by 4 m and 10 cm deep needs exactly 2 cubic metres of concrete — length × "
       "width × depth, the estimate every pour begins with.",
       [{"id": "cv1", "domain": "construction",
         "spec": {"length_m": 5, "width_m": 4, "depth_m": 0.1, "claimed_concrete_m3": 2},
         "claim": "V = 5·4·0.1 = 2 m³"}]),
    _E("works_far", "Architecture",
       "Floor-area ratio: how much building on a lot",
       "The floor-area ratio is total floor area over lot area. 2,000 m² of floor on a 1,000 m² "
       "lot is an FAR of 2 — the number a zoning code lives or dies by.",
       [{"id": "fa1", "domain": "architecture",
         "spec": {"total_floor_area_m2": 2000, "lot_area_m2": 1000, "claimed_far": 2},
         "claim": "FAR = 2000 / 1000 = 2"}]),
    _E("works_density", "Materials science",
       "Density from mass and volume",
       "Ten kilograms in five litres is a density of 2,000 kg/m³ — ρ = m/V, the property that "
       "tells iron from aluminium and floats a ship of steel.",
       [{"id": "de1", "domain": "materials_science",
         "spec": {"mass_kg": 10, "volume_m3": 0.005, "claimed_density_kg_per_m3": 2000},
         "claim": "ρ = 10 / 0.005 = 2000 kg/m³"}]),
    _E("works_six_sigma", "Manufacturing / quality",
       "What 'six sigma' actually means",
       "A process running at 3.4 defects per million opportunities is, by definition, at the "
       "six-sigma quality level — the target that named a whole discipline.",
       [{"id": "ss1", "domain": "manufacturing", "spec": {"dpmo": 3.4, "claimed_sigma": 6.0},
         "claim": "3.4 DPMO → 6.0 σ"}]),
    _E("works_battery", "Energy systems",
       "How long a battery runs a load",
       "A 100 Wh battery driving a 50 W load lasts two hours — energy divided by power. The "
       "arithmetic behind every off-grid design.",
       [{"id": "rt1", "domain": "energy",
         "spec": {"battery_wh": 100, "load_W": 50, "claimed_runtime_hours": 2},
         "claim": "runtime = 100 Wh / 50 W = 2 h"}]),
    _E("works_subnet", "Networking",
       "How many hosts fit in a /24",
       "A /24 subnet leaves 8 host bits — 2⁸ − 2 = 254 usable addresses, after reserving the "
       "network and broadcast. The daily arithmetic of every network.",
       [{"id": "sn1", "domain": "networking",
         "spec": {"subnet_prefix": 24, "claimed_usable_hosts": 254},
         "claim": "/24 → 2⁸ − 2 = 254 usable hosts"}]),
    _E("works_hash", "Cryptography",
       "Cryptographic strength: a fingerprint and a cipher",
       "SHA-256 of the three letters 'abc' is a fixed 256-bit fingerprint — change one bit and it "
       "changes utterly (the property this engine's seals rest on) — and a 256-bit AES key is, by "
       "the standard, strong.",
       [{"id": "hh1", "domain": "cryptography",
         "spec": {"hash_algorithm": "sha256", "data": "abc",
                  "claimed_hash_hex": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"},
         "claim": "SHA-256('abc') = ba7816bf…20015ad"},
        {"id": "ks1", "domain": "cryptography",
         "spec": {"cipher": "AES", "key_bits": 256, "claimed_key_strength": "strong"},
         "claim": "AES-256 → strong", "uses": ["hh1"]}]),
    _E("works_password", "Cybersecurity",
       "The strength of a password, in bits",
       "A 12-character password from a 95-symbol keyboard carries about 79 bits of entropy — "
       "H = L·log₂(N); and a CVSS score of 9.1 is, by the standard, a critical vulnerability.",
       [{"id": "pe1", "domain": "cybersecurity",
         "spec": {"password_length": 12, "charset_size": 95, "claimed_entropy_bits": 78.84},
         "claim": "H = 12·log₂(95) ≈ 78.84 bits"},
        {"id": "cv1", "domain": "cybersecurity",
         "spec": {"cvss_base_score": 9.1, "claimed_cvss_severity": "critical"},
         "claim": "CVSS 9.1 → critical", "uses": ["pe1"]}]),
    _E("works_knapsack", "Operations research",
       "The best a knapsack can carry",
       "Given items of weight and value and a fixed capacity, the 0-1 knapsack picks the most "
       "valuable subset that fits — here a total value of 7 within a weight of 5. The core of "
       "scheduling, budgeting and cargo-loading.",
       [{"id": "kn1", "domain": "operations_research",
         "spec": {"items": [{"weight": 2, "value": 3}, {"weight": 3, "value": 4},
                            {"weight": 4, "value": 5}, {"weight": 5, "value": 6}],
                  "capacity": 5, "claimed_optimal_value": 7},
         "claim": "0-1 knapsack (cap 5) → optimal value 7"}]),
    _E("works_luhn", "Computation / validation",
       "The check digit that catches a mistyped number",
       "The Luhn and ISBN algorithms embed a check digit so a single wrong digit is caught before "
       "it becomes a wrong order or a wrong book. Two standards, both verified.",
       [{"id": "lu1", "domain": "document_validation",
         "spec": {"luhn_number": "4532015112830366", "claimed_luhn_valid": True},
         "claim": "Luhn(4532 0151 1283 0366) is valid"},
        {"id": "ib1", "domain": "document_validation",
         "spec": {"isbn13": "9780306406157", "claimed_isbn13_valid": True},
         "claim": "ISBN-13 978-0-306-40615-7 is valid", "uses": ["lu1"]}]),
    _E("works_exposure", "Photography / optics",
       "The exposure value of a camera setting",
       "At f/8 and 1/250 s the exposure value is EV = log₂(N²/t) ≈ 13.97 — the single number that "
       "makes a bright beach and a dim room comparable.",
       [{"id": "ev1", "domain": "photography",
         "spec": {"f_number": 8, "shutter_seconds": 0.004,
                  "claimed_exposure_value": 13.965784284662087},
         "claim": "EV = log₂(8² / 0.004) ≈ 13.97"}]),

    # ══════════════ V · SOCIETY & THE HUMAN WORLD ══════════════
    _S("works_compound_interest", "Finance",
       "A thousand dollars, ten years, five percent",
       "Compound interest grows principal by (1+r)ⁿ: $1,000 at 5% for ten years becomes $1,628.89. "
       "The engine that both builds savings and buries debt.",
       [{"id": "ci1", "domain": "finance",
         "spec": {"principal": 1000, "rate": 0.05, "compounding_per_year": 1, "years": 10,
                  "claimed_future_value": 1628.894626777442},
         "claim": "A = 1000·1.05¹⁰ = $1,628.89"}]),
    _S("works_rule_72", "Economics",
       "The rule of 72",
       "Anything growing at 8% a year doubles in about 72/8 = 9 years — the back-of-envelope rule "
       "that turns a growth rate into a doubling time.",
       [{"id": "r72", "domain": "economics",
         "spec": {"rate_percent": 8, "claimed_doubling_years": 9},
         "claim": "doubling ≈ 72 / 8 = 9 years"}]),
    _S("works_cap_rate", "Real estate",
       "The capitalization rate of a property",
       "Net operating income over price is the cap rate: $50,000 on a $1,000,000 building is 5% — "
       "the first number any investor computes.",
       [{"id": "cr1", "domain": "real_estate",
         "spec": {"net_operating_income": 50000, "property_value": 1000000, "claimed_cap_rate": 0.05},
         "claim": "cap rate = 50,000 / 1,000,000 = 5%"}]),
    _S("works_gross_pay", "Labor",
       "A paycheck, plain and with overtime",
       "Forty hours at $20 is $800 gross; add ten hours of overtime at the FLSA time-and-a-half "
       "rate and the week totals $1,100. The arithmetic every paycheck must get right.",
       [{"id": "gp1", "domain": "labor",
         "spec": {"hourly_rate": 20, "hours_worked": 40, "claimed_gross_pay": 800},
         "claim": "gross = 20·40 = $800"},
        {"id": "ot1", "domain": "labor",
         "spec": {"hourly_rate": 20, "regular_hours": 40, "overtime_hours": 10,
                  "claimed_overtime_pay": 1100},
         "claim": "with 10 h OT: 800 + 20·1.5·10 = $1,100", "uses": ["gp1"]}]),
    _S("works_chronology", "History / chronology",
       "Counting the years and naming the century",
       "From 1900 to 2000 is 100 years; and 1969 falls in the 20th century (the hundred years "
       "ending in 2000). The arithmetic that keeps a timeline honest.",
       [{"id": "yr1", "domain": "history_chronology",
         "spec": {"from_year": 1900, "to_year": 2000, "claimed_elapsed_years": 100},
         "claim": "2000 − 1900 = 100 years"},
        {"id": "ct1", "domain": "history_chronology",
         "spec": {"year_CE": 1969, "claimed_century": 20},
         "claim": "1969 CE → 20th century", "uses": ["yr1"]}]),
    _S("works_leap_year", "Calendar",
       "The calendar's rules: a leap year and a weekday",
       "The Gregorian rule makes 2000 a leap year (divisible by 400) where 1900 was not; and the "
       "same calendar fixes that 1 January 2000 fell on a Saturday. Rules, not lore.",
       [{"id": "ly1", "domain": "calendar_time", "spec": {"year": 2000, "claimed_leap": True},
         "claim": "2000 is a leap year (÷400)"},
        {"id": "dw1", "domain": "calendar_time",
         "spec": {"date_iso": "2000-01-01", "claimed_day_of_week": "saturday"},
         "claim": "2000-01-01 was a Saturday", "uses": ["ly1"]}]),
    _S("works_music", "Music theory",
       "The perfect fifth and the pitch of A",
       "From C to G is seven semitones — the perfect fifth; and MIDI note 69 is concert A at "
       "exactly 440 Hz. Where mathematics becomes music.",
       [{"id": "iv1", "domain": "music_theory",
         "spec": {"note_a": "C", "note_b": "G", "claimed_semitones": 7},
         "claim": "C → G = 7 semitones (a perfect fifth)"},
        {"id": "et1", "domain": "music_theory",
         "spec": {"midi_note": 69, "claimed_frequency_hz": 440.0},
         "claim": "MIDI 69 = A4 = 440 Hz", "uses": ["iv1"]}]),
    _S("works_fallacy", "Rhetoric / logic",
       "Naming a formal fallacy",
       "'Affirming the consequent' — from P→Q and Q, wrongly concluding P — is a formal fallacy, "
       "invalid by its shape alone. The engine classifies the error, not the topic.",
       [{"id": "fl1", "domain": "rhetoric",
         "spec": {"fallacy_name": "affirming the consequent", "claimed_is_formal_fallacy": True},
         "claim": "affirming the consequent is a formal fallacy"}]),
    _S("works_pythag_expectation", "Sports analytics",
       "How many games a team should have won",
       "Bill James's Pythagorean expectation predicts winning percentage from runs scored and "
       "allowed: 800 to 700 forecasts a .566 season — closer to truth than the actual record.",
       [{"id": "px1", "domain": "sports_analytics",
         "spec": {"runs_scored": 800, "runs_allowed": 700, "pythag_exponent": 2,
                  "claimed_winning_pct": 0.5663716814159292},
         "claim": "W% = 800² / (800² + 700²) ≈ .566"}]),
    _S("works_money_over_time", "Economics",
       "Money over time: interest earned, value eroded",
       "Simple interest on $1,000 at 5% for three years is $150; meanwhile a jump in the price "
       "index from 100 to 110 is 10% inflation. What money earns, and what it quietly loses.",
       [{"id": "si1", "domain": "economics",
         "spec": {"principal": 1000, "rate": 0.05, "time_years": 3, "claimed_simple_interest": 150},
         "claim": "I = P·r·t = 1000·0.05·3 = $150"},
        {"id": "if1", "domain": "economics",
         "spec": {"cpi_current": 110, "cpi_previous": 100, "claimed_inflation_rate": 0.10},
         "claim": "inflation = (110−100)/100 = 10%", "uses": ["si1"]}]),
    _S("works_law_age", "Constitutional law",
       "The age the Constitution sets for the presidency",
       "Article II sets a minimum age of 35 for the President; a candidate of 40 meets it. A rule "
       "read straight from the public-domain text of the Constitution.",
       [{"id": "la1", "domain": "law",
         "spec": {"office": "president", "age": 40, "claimed_meets_age_requirement": True},
         "claim": "age 40 ≥ 35 (Art. II §1) → eligible"}]),
    _S("works_ethics", "Philosophy",
       "What an ethical framework weighs",
       "Deontology locates the moral worth of an act in duties and rules, not in its consequences "
       "— the opposite of a consequentialist's ledger of outcomes. The engine classifies the "
       "framework, it does not adjudicate the ethics.",
       [{"id": "et1", "domain": "philosophy",
         "spec": {"framework_name": "deontological", "claimed_focuses_on_outcomes": False},
         "claim": "deontology judges by duty, not outcomes"}]),
]


# ── build + seal ─────────────────────────────────────────────────────────────
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _data_dir() -> Path:
    d = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    return (Path(d) if d else Path("data"))


def _compiled_path() -> Path:
    return _data_dir() / "compendium" / "compiled" / "compendium_latest.json"


def _identity_path() -> Path:
    return _data_dir() / "compendium" / "compiled" / "compendium_identity.json"


def _config() -> EngineConfig:
    # secular surface → seals cite narrowhighway.com (the world-facing book).
    return EngineConfig(surface="secular")


# Each non-math verifier reads its claim from ONE typed artifact key. We keep the demonstrations
# above written as flat, readable specs and wrap them into the verifier's packet here — one place,
# so a new demonstration stays a plain dict of numbers.
_ARTIFACT_KEY = {
    "number_theory": "NUM_VERIFY", "physics": "PHYS_VERIFY", "electrical": "ELEC_VERIFY",
    "thermodynamics": "THERMO_VERIFY", "chemistry": "CHEM_VERIFY", "geometry": "GEOM_VERIFY",
    "combinatorics": "COMB_VERIFY", "linear_algebra": "LIN_VERIFY", "probability": "PROB_VERIFY",
    "statistics": "STAT_VERIFY", "formal_logic": "LOGIC_VERIFY", "information_theory": "INFO_VERIFY",
    "optics": "OPT_VERIFY", "acoustics": "ACOUS_VERIFY", "nuclear_physics": "NUCLEAR_VERIFY",
    "physical_constants": "CONST_VERIFY", "astronomy": "ASTRO_VERIFY",
    "molecular_geometry": "VSEPR_VERIFY", "quantum_computing": "QCOMP_VERIFY",
    "geology": "GEO_VERIFY", "geography": "GEO_LOC_VERIFY", "meteorology": "MET_VERIFY",
    "hydrology": "HYD_VERIFY", "oceanography": "OCEAN_VERIFY", "ecology": "ECO_VERIFY",
    "soil_science": "SOIL_VERIFY", "genetics": "GENETICS_VERIFY", "nutrition": "NUT_VERIFY",
    "exercise_science": "EX_VERIFY", "construction": "CONSTR_VERIFY", "architecture": "ARCH_VERIFY",
    "materials_science": "MAT_VERIFY", "manufacturing": "MFG_VERIFY", "energy": "ENERGY_VERIFY",
    "networking": "NET_VERIFY", "cryptography": "CRYPTO_VERIFY", "cybersecurity": "CYBER_VERIFY",
    "photography": "PHOTO_VERIFY", "document_validation": "DOC_VERIFY", "finance": "FIN_VERIFY",
    "economics": "ECON_VERIFY", "real_estate": "RE_VERIFY", "labor": "LABOR_VERIFY",
    "history_chronology": "HIST_VERIFY", "calendar_time": "CAL_VERIFY", "music_theory": "MUS_VERIFY",
    "rhetoric": "RHET_VERIFY", "sports_analytics": "SPORT_VERIFY",
    "medicine": "MED_VERIFY", "law": "LAW_VERIFY", "ephemeris": "EPH_VERIFY",
    "operations_research": "OR_VERIFY", "atomic": "ATOM_VERIFY", "periodic_table": "PT_VERIFY",
    "philosophy": "PHIL_VERIFY",
}


def _packet_for(domain: str, spec: Dict[str, Any]) -> Dict[str, Any]:
    """Math specs ({mode, params}) pass through; a flat domain spec is wrapped under its
    verifier's artifact key (unless already wrapped)."""
    d = (domain or "").strip().lower()
    if d in ("mathematics", "math"):
        return spec
    key = _ARTIFACT_KEY.get(d)
    if not key:
        return spec
    if isinstance(spec, dict) and len(spec) == 1 and key in spec:
        return spec
    return {key: spec}


def _run_one(demo: Dict[str, Any], config: EngineConfig) -> Optional[Dict[str, Any]]:
    """Run one demonstration through the engine and seal it. Returns the published record,
    or None if it does not HOLD (dropped + logged — never shown as if it passed)."""
    steps = demo["steps"]
    runsteps = [dict(s, spec=_packet_for(s.get("domain", ""), s.get("spec") or {})) for s in steps]
    result = verify_derivation(runsteps)
    if result.get("verdict") != "HOLDS":
        _log.warning("compendium: DROPPED %s — verdict=%s broken_at=%s gap_at=%s",
                     demo["id"], result.get("verdict"), result.get("broken_at"), result.get("gap_at"))
        return None
    seal_domain = str(steps[0].get("domain") or "mathematics")
    sealed = receipts.attach(result, config=config, domain=seal_domain, enabled=True)
    seal = sealed.get("seal") or {}
    return {
        "id": demo["id"], "discipline": demo["discipline"], "field": demo["field"],
        "title": demo["title"], "narrative": demo["narrative"],
        "verdict": result["verdict"], "steps": result["steps"],
        "confirmed_steps": result["confirmed_steps"],
        "trail": result["trail"],
        "seal": {"content_hash": seal.get("content_hash"), "cite_url": seal.get("cite_url"),
                 "ledgered": seal.get("ledgered")} if seal else None,
    }


def build_all() -> Dict[str, Any]:
    """Run every demonstration through the engine, mint each seal, sign the volume, persist it."""
    config = _config()
    published: List[Dict[str, Any]] = []
    dropped: List[str] = []
    for demo in DEMONSTRATIONS:
        rec = _run_one(demo, config)
        if rec is None:
            dropped.append(demo["id"])
        else:
            published.append(rec)

    by_discipline: Dict[str, int] = {}
    for r in published:
        by_discipline[r["discipline"]] = by_discipline.get(r["discipline"], 0) + 1

    manifest = {
        "work": "The Works — mathematics, science and engineering, worked and sealed",
        "part_of": "The Concordance (narrowhighway) — the whole book/project",
        "generated": _now(),
        "published": len(published), "dropped": dropped,
        "by_discipline": by_discipline,
        "seals": [r["seal"]["content_hash"] for r in published if r.get("seal")],
        "discipline_order": [k for k, _label in PARTS],
        "part_labels": {k: label for k, label in PARTS},
    }
    manifest_hash = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    payload: Dict[str, Any] = {
        "manifest": manifest, "manifest_sha256": manifest_hash,
        "demonstrations": published,
    }
    _sign(payload)
    p = _compiled_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)
    _emit_cards(published)  # every demonstration becomes a seed in the keeping — cards as we build
    _log.info("compendium: published %d, dropped %d -> %s", len(published), len(dropped), p)
    return payload


# The Floor of Discovery keystone (data/keystone_seeds.jsonl) — every worked, sealed demonstration
# is a paving-stone of the one floor of reality, so each Works card grafts to it.
_FLOOR_KEYSTONE = "card_k_floor_of_discovery"


def _emit_cards(published: List[Dict[str, Any]]) -> None:
    """Card each published demonstration into the keeping (data/works_cards.jsonl) and WEAVE it into
    the one graph (data/works_bridges.jsonl). "Cards are created as we build … no more orphans — one
    tool, all integrated." So each demonstration is not a lonely spoke: it grafts to the Floor of
    Discovery (its root) AND to the existing cards of the SAME domain (the weave) AND to its sibling
    demonstrations. Conduit, not source: generated=False — it is FOUND and verified, never generated.

    Every edge is TRUE by construction (same verifier domain), so the 0-false-positive discipline
    holds; token overlap only RANKS which same-domain cards are the closest, it never invents a link."""
    from . import corpus as _corpus  # existing keeping, to find true same-domain neighbours

    def _doms(r):
        return sorted({str(t.get("domain", "")) for t in (r.get("trail") or []) if t.get("domain")})

    # index the existing keeping by verifier domain (source.domain), and the works cards by domain
    try:
        existing = _corpus.load_cards()
    except Exception:  # a fresh box with no cards.jsonl — the Floor edge alone still integrates
        existing = {}
    by_domain: Dict[str, List[str]] = {}
    text_of: Dict[str, set] = {}
    for cid_e, c in existing.items():
        if c.get("shelf") == "the-works":  # prior works cards are handled as siblings, not "existing"
            continue
        dm = str((c.get("source") or {}).get("domain") or "")
        if dm:
            by_domain.setdefault(dm, []).append(cid_e)
            text_of[cid_e] = set(_corpus._tokens(_corpus._card_text(c)))
    works_by_domain: Dict[str, List[str]] = {}
    for r in published:
        for dm in _doms(r):
            works_by_domain.setdefault(dm, []).append(r["id"])

    cards: List[Dict[str, Any]] = []
    bridges: List[Dict[str, Any]] = []
    seen_edge: set = set()
    wtoks: Dict[str, set] = {}        # each works card's tokens (for the part weave)
    wtitle: Dict[str, str] = {}
    by_part: Dict[str, List[str]] = {}

    def _edge(a, b, rel, ev, a_title):
        key = tuple(sorted((a, b))) + (rel,)
        if a == b or key in seen_edge:
            return
        seen_edge.add(key)
        bridges.append({"a": a, "b": b, "relationship": rel, "evidence": ev, "a_title": a_title})

    for r in published:
        cid = "card_" + str(r["id"])
        doms = _doms(r)
        field = str(r.get("field", ""))
        claims = " · ".join(t.get("claim", "") for t in (r.get("trail") or []) if t.get("claim"))
        seal = r.get("seal") or {}
        body = (str(r.get("narrative", "")) + "  Worked & sealed by the engine — " + claims +
                (".  [HOLDS; open the seal to re-check.]" if seal.get("cite_url") else "."))
        bands = ["the-works", str(r["discipline"])] + doms + field.lower().split()
        cards.append({
            "id": cid, "kind": "verified", "title": r["title"], "body": body,
            "source": {"label": "The Works — worked & sealed", "url": seal.get("cite_url") or "",
                       "domain": (doms[0] if doms else ""), "authority_tier": "verified"},
            "shelf": "the-works", "box": str(r["discipline"]),
            "bands": bands, "connections": [], "author": "engine",
            "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
            "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
            "generated": False, "subject": field,
            "extra": {"seal_hash": seal.get("content_hash"), "cite_url": seal.get("cite_url"),
                      "demonstration_id": r["id"], "verdict": r.get("verdict")},
        })
        # (1) root: every stone paves the one floor of reality
        _edge(cid, _FLOOR_KEYSTONE, "paves",
              "A worked, engine-sealed demonstration — a paving-stone of the floor of reality.", r["title"])
        my_toks = set(_corpus._tokens((r["title"] + " " + field + " " + body)))
        wtoks[cid] = my_toks
        wtitle[cid] = r["title"]
        by_part.setdefault(str(r["discipline"]), []).append(cid)
        for dm in doms:
            # (2) the weave: connect to the closest existing cards of the SAME domain (true edge)
            cands = [c for c in by_domain.get(dm, []) if c != cid]
            cands.sort(key=lambda c: len(my_toks & text_of.get(c, set())), reverse=True)
            for target in cands[:3]:
                _edge(cid, target, "demonstrates",
                      f"A worked demonstration in the same field ({dm}).", r["title"])
            # (3) kindred: sibling demonstrations of the same domain
            for other in works_by_domain.get(dm, []):
                if other != r["id"]:
                    _edge(cid, "card_" + other, "kindred",
                          f"A sibling worked demonstration in {dm}.", r["title"])

    # (4) the part weave: within each part of the volume, connect every demonstration to its two
    # closest part-mates (by token overlap) — so each part is a woven cluster, not a fan of spokes,
    # and even a lone-domain demonstration (no reference card, no sibling) is integrated, never an
    # orphan hanging off the hub. Same part = the same broad discipline, so the edge is true.
    for part, members in by_part.items():
        for cid in members:
            mates = sorted((m for m in members if m != cid),
                           key=lambda m: len(wtoks[cid] & wtoks[m]), reverse=True)
            for mate in mates[:2]:
                _edge(cid, mate, "adjacent",
                      f"Neighbouring worked demonstrations in the same part of the volume.", wtitle[cid])

    d = _data_dir()
    d.mkdir(parents=True, exist_ok=True)
    for name, rows in (("works_cards.jsonl", cards), ("works_bridges.jsonl", bridges)):
        fp = d / name
        tmp = fp.with_suffix(fp.suffix + ".tmp")
        tmp.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n", encoding="utf-8")
        os.replace(tmp, fp)
    _log.info("compendium: emitted %d works cards + %d bridges (floor + same-domain weave + siblings)",
              len(cards), len(bridges))


def _sign(payload: Dict[str, Any]) -> None:
    """Ed25519-sign the volume (degraded-but-honest if `cryptography` is absent), mirroring
    the codex artifact so the whole book is signed the same way."""
    try:
        from . import identity as _id
        idp = _identity_path()
        if idp.exists():
            ident = json.loads(idp.read_text(encoding="utf-8"))
        else:
            ident = _id.create_identity()
            idp.parent.mkdir(parents=True, exist_ok=True)
            idp.write_text(json.dumps(ident, indent=2), encoding="utf-8")
        payload["signature"] = _id.sign(ident["private_key"], payload["manifest_sha256"])
        payload["public_key"] = ident["public_key"]
        payload["fingerprint"] = _id.fingerprint(ident["public_key"])
        payload["signed"] = bool(_id.signing_available())
    except Exception as e:  # never crash the volume over signing
        payload["signature"] = None
        payload["signed"] = False
        payload["sign_error"] = str(e)[:120]


# ── serve ────────────────────────────────────────────────────────────────────
_CACHE: Optional[Dict[str, Any]] = None


def load(force: bool = False) -> Dict[str, Any]:
    """The compiled volume. Reads the sealed file; builds it lazily if absent. Cached in-process."""
    global _CACHE
    if _CACHE is not None and not force:
        return _CACHE
    p = _compiled_path()
    if p.exists() and not force:
        try:
            _CACHE = json.loads(p.read_text(encoding="utf-8"))
            return _CACHE
        except Exception:  # corrupt file — rebuild
            pass
    _CACHE = build_all()
    return _CACHE


def overview() -> Dict[str, Any]:
    """The volume's front matter: what it is, how many demonstrations stand, by discipline."""
    v = load()
    man = v.get("manifest") or {}
    return {
        "work": man.get("work"), "part_of": man.get("part_of"),
        "generated": man.get("generated"),
        "published": man.get("published", 0), "by_discipline": man.get("by_discipline", {}),
        "part_labels": man.get("part_labels", {}), "discipline_order": man.get("discipline_order", []),
        "signed": v.get("signed", False), "fingerprint": v.get("fingerprint"),
        "manifest_sha256": v.get("manifest_sha256"),
        "note": ("Every demonstration below was run through the same engine that guards the moat "
                 "and carries a permanent, re-checkable seal. Proof, not assertion — open a seal "
                 "and re-check the math yourself. The engine verifies a provided derivation; it "
                 "does not generate the answer."),
    }


def demonstrations() -> List[Dict[str, Any]]:
    """Every published demonstration, in part order (I → V)."""
    v = load()
    order = {d: i for i, d in enumerate((v.get("manifest") or {}).get("discipline_order", []))}
    demos = list(v.get("demonstrations") or [])
    demos.sort(key=lambda r: (order.get(r.get("discipline"), 99), r.get("id", "")))
    return demos


def demonstration(demo_id: str) -> Optional[Dict[str, Any]]:
    for r in (load().get("demonstrations") or []):
        if r.get("id") == demo_id:
            return r
    return None


def artifact() -> Dict[str, Any]:
    """The signed volume: manifest + signature + public key (the book as of a date, Ed25519-sealed)."""
    v = load()
    return {"manifest": v.get("manifest"), "manifest_sha256": v.get("manifest_sha256"),
            "signature": v.get("signature"), "public_key": v.get("public_key"),
            "fingerprint": v.get("fingerprint"), "signed": v.get("signed", False)}


def verify_artifact() -> Dict[str, Any]:
    """Re-check the volume's signature and manifest hash."""
    v = load()
    man = v.get("manifest")
    if not man:
        return {"ok": False, "reason": "no volume compiled yet"}
    recomputed = hashlib.sha256(
        json.dumps(man, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    hash_ok = recomputed == v.get("manifest_sha256")
    sig_ok = None
    if v.get("signature") and v.get("public_key"):
        try:
            from . import identity as _id
            sig_ok = _id.verify(v["public_key"], v["manifest_sha256"], v["signature"])
        except Exception:
            sig_ok = None
    return {"ok": bool(hash_ok and (sig_ok is not False)),
            "manifest_hash_ok": hash_ok, "signature_ok": sig_ok,
            "published": man.get("published"), "generated": man.get("generated")}


if __name__ == "__main__":  # sovereign self-run (droplet gate has no pytest)
    logging.basicConfig(level=logging.INFO)
    out = build_all()
    m = out["manifest"]
    print(f"The Works: published {m['published']} demonstrations "
          f"({m['by_discipline']}), dropped {len(m['dropped'])}: {m['dropped']}")
    print(f"signed={out.get('signed')} fingerprint={out.get('fingerprint')}")
    print(f"verify: {verify_artifact()}")
