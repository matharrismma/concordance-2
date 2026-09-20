#!/usr/bin/env python3
"""PLACE THE VERIFIERS — the engine's own deterministic computations, onto the map.

Matt, 2026-09-14: "place the remaining verifiers." The concordance ships ~331
verifier functions in src/concordance/verifiers/ — pure, deterministic checks,
each declaring its formula in its own source. This module places the COMPUTATIONAL
ones onto the calculation map by their canonical FORM (the formula is the evidence
for the same_form relation) and links each to its parent theory on THE FLOOR where
one is clean.

Discipline (found, not generated; every relation carries its evidence; a gap stays
a gap): a verifier is placed ONLY when its formula genuinely instantiates a form.
The many VALIDATION / CLASSIFICATION / LOOKUP / STRUCTURAL verifiers (isbn checks,
band classifiers, doctrinal and gate checks, lexicon lookups) are a DIFFERENT kind
— a check, not a calculation — and are honestly left off the Smith chart. `--check`
confirms every placed name is a real verifier in the engine source, so nothing here
is invented.

seed_calculations.py imports NEW_FORMS + verifier_calcs() + verifier_theory() and
merges them, so the existing store rebuild and both maps pick the verifiers up with
no other change.

    python tools/seed_verifiers.py --check    # validate names against engine source, forms, theories
    python tools/seed_verifiers.py --list     # print the placements grouped by form
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

VERIFIER_DIR = Path(__file__).resolve().parent.parent / "src" / "concordance" / "verifiers"

# --- the six new canonical forms the verifier corpus reveals -------------------
NEW_FORMS: dict[str, tuple[str, str]] = {
    "logarithmic":   ("y = k * log(x / x0)",        "a ratio compressed onto a log scale — decibels, pH, magnitude, entropy, half-life"),
    "trigonometric": ("a sin(theta) = b sin(phi)",  "relations among angles and lengths — planar and spherical (Snell, haversine, bearings)"),
    "combinatorial": ("C(n,k) = n! / (k!(n-k)!)",   "counting arrangements and selections — factorials, permutations, primes"),
    "boolean_logic": ("phi is SAT / valid / entailed", "truth-functional evaluation — satisfiability, entailment, validity"),
    "mensuration":   ("A = l*w ; V = (4/3) pi r^3", "closed-form measure of a shape — area, volume, perimeter"),
    "hypothesis_test": ("reject H0 if p <= alpha",  "compare a statistic to its null distribution — p-values, intervals, chi-squared"),
}

# --- the placements: (domain, verifier_name, form, theory_id_or_blank, formula) -
# domain = the verifier file stem; verifier_name = its canonical name (or function
# name where it has none). Only computational verifiers appear here.
PLACE: list[tuple[str, str, str, str, str]] = [
    # acoustics
    ("acoustics", "acoustics.wave_relation", "wave", "card_theory_acoustic_wave_theory", "c = f * lambda"),
    ("acoustics", "acoustics.decibel_ratio", "logarithmic", "card_theory_acoustic_wave_theory", "dB = 10 log10(I/I_ref)"),
    ("acoustics", "acoustics.doppler_shift", "ratio", "card_theory_acoustic_wave_theory", "f_obs = f (c+v_o)/(c+v_s)"),
    ("acoustics", "acoustics.harmonic_frequency", "fourier_spectral", "card_theory_music_theory", "f_n = n f_1"),
    # agriculture
    ("agriculture", "agriculture.stocking_density", "ratio", "card_theory_agricultural_science", "animals / area"),
    # architecture
    ("architecture", "architecture.floor_area_ratio", "ratio", "", "FAR = floor_area / lot_area"),
    ("architecture", "architecture.occupant_load", "ratio", "", "occupants = ceil(area / factor)"),
    ("architecture", "architecture.window_wall_ratio", "ratio", "", "WWR = window_area / wall_area"),
    ("architecture", "architecture.structural_load", "conservation", "card_theory_structural_statics", "total = dead + live + snow"),
    # astronomy
    ("astronomy", "astronomy.kepler_third_law", "power_law", "card_theory_heliocentrism_kepler_s_laws", "T^2 = a^3"),
    ("astronomy", "astronomy.gravitational_force", "inverse_square", "card_theory_newton_s_law_of_universal_gravitation", "F = G m1 m2 / r^2"),
    ("astronomy", "astronomy.parallax_distance", "trigonometric", "card_theory_celestial_mechanics_ephemeris_prediction", "d(pc) = 1 / p(arcsec)"),
    ("astronomy", "astronomy.apparent_magnitude_distance", "logarithmic", "", "m - M = 5 log10(d) - 5"),
    # atomic
    ("atomic", "atomic.shell_capacity", "combinatorial", "card_theory_pauli_exclusion_principle", "capacity = 2 n^2"),
    # calendar_time
    ("calendar_time", "calendar_time.leap_year", "modular", "card_theory_calendar_theory", "year mod 4, not 100, unless 400"),
    ("calendar_time", "calendar_time.day_of_week", "modular", "card_theory_calendar_theory", "weekday = (date) mod 7"),
    ("calendar_time", "calendar_time.utc_offset", "modular", "card_theory_calendar_theory", "local = UTC + offset (mod 24)"),
    # chemistry
    ("chemistry", "verify_equation", "conservation", "card_theory_law_of_conservation_of_mass", "atoms in = atoms out (balance)"),
    ("chemistry", "chemistry.thermodynamic_feasibility", "optimization", "card_theory_second_law_of_thermodynamics", "dG = dH - T dS (< 0 spontaneous)"),
    # combinatorics
    ("combinatorics", "combinatorics.permutations", "combinatorial", "card_theory_combinatorial_enumeration", "P(n,k) = n!/(n-k)!"),
    ("combinatorics", "combinatorics.combinations", "combinatorial", "card_theory_combinatorial_enumeration", "C(n,k) = n!/(k!(n-k)!)"),
    ("combinatorics", "combinatorics.derangements", "combinatorial", "card_theory_combinatorial_enumeration", "!n = n! sum (-1)^k/k!"),
    ("combinatorics", "combinatorics.multinomial", "combinatorial", "card_theory_combinatorial_enumeration", "n!/(k1! ... km!)"),
    # computer_science
    ("computer_science", "verify_runtime_complexity", "power_law", "card_theory_computational_complexity__p__np__reductions", "T(n) ~ n^k (log-log fit)"),
    ("computer_science", "verify_space_complexity", "power_law", "card_theory_computational_complexity__p__np__reductions", "S(n) ~ n^k"),
    # digital logic — Shannon 1937: a switching circuit IS a Boolean function. Same SAT engine as
    # formal_logic, realized in circuits — the bridge that ties the reasoning domains to the map.
    ("computer_science", "computer_science.logic_gate", "boolean_logic", "card_theory_boolean_algebra_propositional_logic", "gate_a == gate_b iff ~(a <-> b) unsat"),
    # construction (mensuration + ratios)
    ("construction", "construction.concrete_volume", "mensuration", "", "V = l * w * d"),
    ("construction", "construction.rectangular_area", "mensuration", "", "A = l * w"),
    ("construction", "construction.circular_area", "mensuration", "", "A = pi r^2"),
    ("construction", "construction.wall_area", "mensuration", "", "A = perimeter * h - openings"),
    ("construction", "construction.rebar_weight", "ratio", "", "W = length * unit_weight"),
    ("construction", "construction.paint_coverage", "ratio", "", "cans = ceil(area / coverage)"),
    ("construction", "construction.floor_tiles", "ratio", "", "tiles = ceil(area/tile)(1+waste)"),
    ("construction", "construction.beam_load", "ratio", "card_theory_structural_statics", "w = total_load / span"),
    # cybersecurity
    ("cybersecurity", "cybersecurity.password_entropy", "logarithmic", "card_theory_shannon_information_theory", "H = L log2(N)"),
    ("cybersecurity", "cybersecurity.subnet_hosts", "combinatorial", "", "hosts = 2^(32-prefix) - 2"),
    # document_validation (check digits = modular error-detecting codes)
    ("document_validation", "doc_validation.isbn10", "modular", "card_theory_error_correcting_codes", "sum(i*d_i) mod 11 = 0"),
    ("document_validation", "doc_validation.isbn13", "modular", "card_theory_error_correcting_codes", "weighted sum mod 10 = 0"),
    ("document_validation", "doc_validation.luhn", "modular", "card_theory_error_correcting_codes", "Luhn checksum mod 10 = 0"),
    ("document_validation", "doc_validation.ean_upc", "modular", "card_theory_error_correcting_codes", "weighted sum mod 10 = 0"),
    # ecology
    ("ecology", "ecology.logistic_growth", "logistic", "card_theory_population_ecology", "N = K/(1+((K-N0)/N0) e^-rt)"),
    ("ecology", "ecology.trophic_efficiency", "exponential", "card_theory_trophic_dynamics", "out = in * eff^levels"),
    ("ecology", "ecology.shannon_diversity", "logarithmic", "card_theory_shannon_information_theory", "H = -sum p ln p"),
    ("ecology", "ecology.carbon_footprint_transport", "ratio", "", "CO2 = distance * factor"),
    # economics
    ("economics", "economics.simple_interest", "ratio", "card_theory_time_value_of_money_discounting", "I = P r t"),
    ("economics", "economics.compound_interest", "exponential", "card_theory_time_value_of_money_discounting", "A = P (1+r/n)^(nt)"),
    ("economics", "economics.present_value", "exponential", "card_theory_time_value_of_money_discounting", "PV = FV/(1+r)^t"),
    ("economics", "economics.future_value", "exponential", "card_theory_time_value_of_money_discounting", "FV = PV(1+r)^t"),
    ("economics", "economics.rule_of_72", "logarithmic", "card_theory_time_value_of_money_discounting", "t_double ~ 72 / rate"),
    ("economics", "economics.inflation_adjusted", "exponential", "card_theory_time_value_of_money_discounting", "real = nominal/(1+i)^y"),
    ("economics", "economics.gdp_per_capita", "ratio", "", "GDP / population"),
    ("economics", "economics.price_elasticity", "ratio", "card_theory_supply_demand_market_equilibrium", "PED = %dQ / %dP"),
    # electrical
    ("electrical", "electrical.ohms_law", "linear_flux", "card_theory_ohm_s_law_circuit_theory", "V = I R"),
    ("electrical", "electrical.power", "ratio", "card_theory_ohm_s_law_circuit_theory", "P = V I"),
    ("electrical", "electrical.kirchhoff_voltage_loop", "conservation", "card_theory_ohm_s_law_circuit_theory", "sum V around a loop = 0"),
    ("electrical", "electrical.rc_time_constant", "exponential", "card_theory_ohm_s_law_circuit_theory", "v = V(1 - e^-t/RC)"),
    # energy
    ("energy", "energy.power_balance", "conservation", "card_theory_conservation_of_energy", "gen - consumed - loss = 0"),
    ("energy", "energy.wire_voltage_drop", "linear_flux", "card_theory_ohm_s_law_circuit_theory", "Vdrop = 2 I R_per_m L"),
    ("energy", "energy.efficiency", "ratio", "card_theory_conservation_of_energy", "eta = out / in (<= 1)"),
    ("energy", "energy.battery_sizing", "ratio", "", "Ah = kWh days 1000 / (V DoD)"),
    ("energy", "energy.solar_daily_yield", "ratio", "", "kWh = W * sun_hours * eta / 1000"),
    ("energy", "energy.runtime", "ratio", "", "hours = battery_Wh / load_W"),
    # ephemeris
    ("ephemeris", "ephemeris.julian_day", "accumulation", "card_theory_julian_day_number", "JD = running day count"),
    ("ephemeris", "ephemeris.moon_phase", "periodic", "card_theory_saros_eclipse_cycle", "phase = age mod 29.53 d"),
    ("ephemeris", "ephemeris.equinox_solstice", "periodic", "card_theory_celestial_mechanics_ephemeris_prediction", "solar longitude = 0,90,180,270"),
    ("ephemeris", "ephemeris.sunrise_sunset", "trigonometric", "card_theory_celestial_mechanics_ephemeris_prediction", "cos(H) = -tan(lat) tan(dec)"),
    # exercise_science
    ("exercise_science", "exercise_science.energy_expenditure", "ratio", "card_theory_exercise_physiology", "kcal = MET * kg * hours"),
    ("exercise_science", "exercise_science.max_heart_rate", "ratio", "card_theory_exercise_physiology", "HRmax = 208 - 0.7 age"),
    ("exercise_science", "exercise_science.target_heart_rate_zone", "ratio", "card_theory_exercise_physiology", "target = (HRmax-HRrest) I + HRrest"),
    # finance
    ("finance", "finance.accounting_identity", "conservation", "card_theory_double_entry_accounting_identity", "Assets = Liabilities + Equity"),
    ("finance", "finance.compound_interest", "exponential", "card_theory_time_value_of_money_discounting", "A = P(1+r/n)^(nt)"),
    ("finance", "finance.npv", "accumulation", "card_theory_time_value_of_money_discounting", "NPV = sum CF_t/(1+r)^t"),
    ("finance", "finance.present_value", "exponential", "card_theory_time_value_of_money_discounting", "PV = FV/(1+r)^t"),
    # formal_logic
    ("formal_logic", "formal_logic.satisfiability", "boolean_logic", "card_theory_boolean_algebra_propositional_logic", "exists an assignment making phi true"),
    ("formal_logic", "formal_logic.tautology", "boolean_logic", "card_theory_boolean_algebra_propositional_logic", "phi true under every assignment"),
    ("formal_logic", "formal_logic.contradiction", "boolean_logic", "card_theory_boolean_algebra_propositional_logic", "phi false under every assignment"),
    ("formal_logic", "formal_logic.entailment", "boolean_logic", "card_theory_boolean_algebra_propositional_logic", "A |= B (every model of A models B)"),
    ("formal_logic", "formal_logic.equivalence", "boolean_logic", "card_theory_boolean_algebra_propositional_logic", "A <=> B (same truth table)"),
    # geography (spherical trig + one area)
    ("geography", "geography.haversine_distance", "trigonometric", "card_theory_map_projections", "great-circle distance (haversine)"),
    ("geography", "geography.initial_bearing", "trigonometric", "card_theory_map_projections", "forward azimuth atan2(...)"),
    ("geography", "geography.geodesic_distance", "trigonometric", "card_theory_map_projections", "WGS84 ellipsoidal distance"),
    ("geography", "geography.destination_point", "trigonometric", "card_theory_map_projections", "dead reckoning from bearing+dist"),
    ("geography", "geography.projection_distortion", "trigonometric", "card_theory_map_projections", "scale distortion vs latitude"),
    ("geography", "geography.polygon_area", "mensuration", "card_theory_map_projections", "spherical-excess area"),
    # geology
    ("geology", "geology.radiometric_decay", "exponential", "card_theory_radiometric_dating_uniformitarianism", "N = N0 e^-lambda t"),
    ("geology", "geology.richter_amplitude", "logarithmic", "card_theory_seismology_earthquake_magnitude", "A2/A1 = 10^(M2-M1)"),
    # geometry
    ("geometry", "geometry.pythagorean", "trigonometric", "card_theory_pythagorean_theorem", "a^2 + b^2 = c^2"),
    ("geometry", "geometry.polygon_interior_angle_sum", "mensuration", "card_theory_euclidean_geometry_the_parallel_postulate", "sum = (n-2) 180"),
    ("geometry", "geometry.circle_properties", "mensuration", "card_theory_euclidean_geometry_the_parallel_postulate", "A = pi r^2 ; C = 2 pi r"),
    ("geometry", "geometry.rectangle", "mensuration", "card_theory_euclidean_geometry_the_parallel_postulate", "A = l w ; P = 2(l+w)"),
    ("geometry", "geometry.sphere", "mensuration", "card_theory_euclidean_geometry_the_parallel_postulate", "V = (4/3) pi r^3 ; A = 4 pi r^2"),
    ("geometry", "geometry.cylinder", "mensuration", "card_theory_euclidean_geometry_the_parallel_postulate", "V = pi r^2 h"),
    ("geometry", "geometry.cube", "mensuration", "card_theory_euclidean_geometry_the_parallel_postulate", "V = s^3 ; A = 6 s^2"),
    ("geometry", "geometry.coordination_angle", "trigonometric", "card_theory_vsepr_theory", "central bond angle of a geometry"),
    # hydrology
    ("hydrology", "hydrology.manning_velocity", "power_law", "card_theory_hydrologic_cycle_open_channel_flow", "v = (1/n) R^(2/3) S^(1/2)"),
    ("hydrology", "hydrology.darcy_velocity", "linear_flux", "card_theory_hydrologic_cycle_open_channel_flow", "q = -K dh/dl"),
    ("hydrology", "hydrology.rational_runoff", "ratio", "card_theory_hydrologic_cycle_open_channel_flow", "Q = C i A"),
    ("hydrology", "hydrology.bernoulli_head", "conservation", "card_theory_fluid_mechanics", "h = z + p/(rho g) + v^2/(2g)"),
    # information_theory
    ("information_theory", "info_theory.shannon_entropy", "logarithmic", "card_theory_shannon_information_theory", "H = -sum p log2 p"),
    ("information_theory", "info_theory.bsc_capacity", "logarithmic", "card_theory_shannon_information_theory", "C = 1 - H2(p)"),
    ("information_theory", "info_theory.hamming_distance", "combinatorial", "card_theory_error_correcting_codes", "count of differing positions"),
    # labor
    ("labor", "labor.gross_pay", "ratio", "card_theory_labor_economics", "pay = rate * hours"),
    ("labor", "labor.overtime_pay", "ratio", "card_theory_labor_economics", "reg*rate + OT*rate*1.5"),
    ("labor", "labor.annual_to_hourly", "ratio", "card_theory_labor_economics", "hourly = annual / 2080"),
    ("labor", "labor.take_home_pay", "ratio", "card_theory_labor_economics", "net = gross (1 - tax)"),
    ("law", "law.flsa_overtime", "ratio", "card_theory_labor_economics", "OT = max(0,h-40) rate 1.5"),
    # linear_algebra
    ("linear_algebra", "vector.dot_product", "linear_system", "card_theory_linear_algebra", "a . b = sum a_i b_i"),
    ("linear_algebra", "vector.cross_product", "linear_system", "card_theory_linear_algebra", "a x b (3D)"),
    ("linear_algebra", "vector.magnitude", "mensuration", "card_theory_linear_algebra", "|a| = sqrt(sum a_i^2)"),
    ("linear_algebra", "vector.angle", "trigonometric", "card_theory_linear_algebra", "cos t = a.b/(|a||b|)"),
    ("linear_algebra", "matrix.addition", "linear_system", "card_theory_linear_algebra", "(A+B)_ij = A_ij + B_ij"),
    ("linear_algebra", "matrix.multiplication", "linear_system", "card_theory_linear_algebra", "(AB)_ij = sum A_ik B_kj"),
    ("linear_algebra", "matrix.determinant", "linear_system", "card_theory_linear_algebra", "det A"),
    ("linear_algebra", "matrix.trace", "linear_system", "card_theory_linear_algebra", "tr A = sum A_ii"),
    ("linear_algebra", "matrix.eigenvalues", "eigenvalue", "card_theory_linear_algebra", "A v = lambda v"),
    ("linear_algebra", "matrix.inverse_check", "linear_system", "card_theory_linear_algebra", "A A^-1 = I"),
    ("linear_algebra", "system.solve_check", "linear_system", "card_theory_linear_algebra", "A x = b"),
    # manufacturing (Gaussian process statistics)
    ("manufacturing", "manufacturing.spc_control_limits", "gaussian", "card_theory_reliability_tolerance_stack_up", "UCL/LCL = mean +- k sigma"),
    ("manufacturing", "manufacturing.process_capability", "gaussian", "card_theory_reliability_tolerance_stack_up", "Cp, Cpk"),
    ("manufacturing", "manufacturing.tolerance_stack_rss", "gaussian", "card_theory_reliability_tolerance_stack_up", "total = sqrt(sum t_i^2)"),
    ("manufacturing", "manufacturing.sigma_level", "gaussian", "card_theory_reliability_tolerance_stack_up", "defect rate from sigma level"),
    # materials_science
    ("materials_science", "materials_science.stress_strain", "linear_flux", "card_theory_elasticity", "sigma = E epsilon (Hooke)"),
    ("materials_science", "materials_science.thermal_expansion", "ratio", "", "dL = alpha L0 dT"),
    ("materials_science", "materials_science.density", "ratio", "", "rho = m / V"),
    # mathematics — the algebra of sets IS a Boolean algebra (Boole; Stone's representation theorem).
    # Third face of the same kernel: a set identity holds iff the matching propositional formula is valid.
    ("mathematics", "mathematics.set_algebra", "boolean_logic", "card_theory_boolean_algebra_propositional_logic", "set identity iff Boolean formula is a tautology"),
    # medicine
    ("medicine", "medicine.bmi", "ratio", "", "BMI = kg / m^2"),
    ("medicine", "medicine.drug_dosage", "ratio", "card_theory_pharmacokinetics", "dose = weight * mg_per_kg"),
    ("medicine", "medicine.a1c_to_eag", "ratio", "", "eAG = 28.7 A1C - 46.7"),
    ("medicine", "medicine.egfr_cockcroft", "ratio", "", "eGFR = (140-age) wt f /(72 Cr)"),
    ("medicine", "medicine.map", "ratio", "", "MAP = DBP + (SBP-DBP)/3"),
    # meteorology
    ("meteorology", "meteorology.saturation_vapor_pressure", "exponential", "card_theory_atmospheric_thermodynamics", "e_s ~ exp(a T/(b+T))"),
    # music_theory
    ("music_theory", "music.interval_semitones", "modular", "card_theory_music_theory", "interval = note diff mod 12"),
    ("music_theory", "music.frequency_ratio", "ratio", "card_theory_music_theory", "f2/f1 = 2^(n/12)"),
    ("music_theory", "music.equal_temperament_freq", "exponential", "card_theory_tuning_systems_comma", "f = 440 * 2^((n-69)/12)"),
    ("music_theory", "music.scale_membership", "modular", "card_theory_music_theory", "note mod 12 in scale set"),
    # networking
    ("networking", "networking.subnet_host_count", "combinatorial", "", "hosts = 2^(32-N) - 2"),
    # nuclear_physics
    ("nuclear_physics", "nuclear_physics.radioactive_decay", "exponential", "card_theory_nuclear_decay_binding_energy", "N = N0 e^-lambda t"),
    ("nuclear_physics", "nuclear_physics.binding_energy_per_nucleon", "ratio", "card_theory_nuclear_decay_binding_energy", "BE/A = mass_defect 931.5 / A"),
    ("nuclear_physics", "nuclear_physics.half_life_from_activity", "logarithmic", "card_theory_nuclear_decay_binding_energy", "T = ln2 N / A"),
    ("nuclear_physics", "nuclear_physics.decay_constant", "logarithmic", "card_theory_nuclear_decay_binding_energy", "lambda = ln2 / T_half"),
    # number_theory
    ("number_theory", "number_theory.primality", "modular", "card_theory_fundamental_theorem_of_arithmetic", "no divisor in [2, sqrt n]"),
    ("number_theory", "number_theory.gcd", "modular", "card_theory_fundamental_theorem_of_arithmetic", "gcd(a,b)=gcd(b, a mod b)"),
    ("number_theory", "number_theory.factorial", "combinatorial", "card_theory_combinatorial_enumeration", "n! = n (n-1)!"),
    ("number_theory", "number_theory.modular_inverse", "modular", "card_theory_fundamental_theorem_of_arithmetic", "a x = 1 (mod m)"),
    ("number_theory", "number_theory.sequence", "recursion", "", "nth term of a sequence"),
    ("number_theory", "number_theory.perfect_number", "modular", "card_theory_fundamental_theorem_of_arithmetic", "sum of proper divisors = n"),
    # Prime Number Theorem — the bridge from the primes to the logarithm. Placed on the LOGARITHMIC
    # form deliberately: it is the one connection the Atlas's own topology needs to close its single
    # irreducible void (the analytic<->number-theory seam). Found, not forced (2026-09-19).
    ("number_theory", "number_theory.prime_counting", "logarithmic", "card_theory_fundamental_theorem_of_arithmetic", "pi(x) ~ x/ln(x)  (Prime Number Theorem)"),
    # nutrition
    ("nutrition", "nutrition.macronutrient_calories", "ratio", "card_theory_macronutrient_metabolism", "4c + 4p + 9f"),
    ("nutrition", "nutrition.energy_balance", "conservation", "card_theory_bioenergetics_energy_balance", "intake - expenditure"),
    # oceanography
    ("oceanography", "oceanography.pressure_at_depth", "ratio", "card_theory_physical_oceanography", "P = P_atm + rho g d"),
    ("oceanography", "oceanography.deep_water_wave_speed", "wave", "card_theory_physical_oceanography", "c = sqrt(g lambda / 2 pi)"),
    # operations_research
    ("operations_research", "operations_research.lp_feasibility", "optimization", "card_theory_linear_programming_duality", "A x <= b feasibility"),
    ("operations_research", "operations_research.critical_path", "optimization", "card_theory_graph_theory", "CPM makespan on a DAG"),
    ("operations_research", "operations_research.knapsack_01", "optimization", "card_theory_optimization", "0-1 knapsack (DP)"),
    ("operations_research", "operations_research.assignment_cost", "optimization", "card_theory_optimization", "min-cost assignment"),
    # optics
    ("optics", "optics.snell_law", "trigonometric", "card_theory_wave_optics", "n1 sin t1 = n2 sin t2"),
    ("optics", "optics.thin_lens", "ratio", "card_theory_wave_optics", "1/f = 1/do + 1/di"),
    ("optics", "optics.magnification", "ratio", "card_theory_wave_optics", "M = -di/do"),
    ("optics", "optics.rayleigh_diffraction", "wave", "card_theory_wave_optics", "theta ~ 1.22 lambda / D"),
    ("optics", "optics.double_slit", "wave", "card_theory_wave_optics", "dy = lambda L / d"),
    ("optics", "optics.photon_energy", "ratio", "card_theory_quantization", "E = h f"),
    ("optics", "optics.de_broglie", "ratio", "card_theory_quantization", "lambda = h / p"),
    ("optics", "optics.critical_angle", "trigonometric", "card_theory_wave_optics", "theta_c = arcsin(n2/n1)"),
    ("optics", "optics.numerical_aperture", "trigonometric", "card_theory_wave_optics", "NA = sqrt(n1^2 - n2^2)"),
    ("optics", "optics.fiber_attenuation", "logarithmic", "card_theory_wave_optics", "loss_dB = alpha * length"),
    # periodic_table
    ("periodic_table", "periodic_table.atomic_mass_weighted_average", "ratio", "card_theory_periodic_law", "sum(isotope * abundance)"),
    # philosophy
    ("philosophy", "philosophy.modal_logic_validity", "boolean_logic", "card_theory_formal_logic_epistemology", "box P -> diamond P (K axiom)"),
    ("philosophy", "philosophy.identity_principle", "boolean_logic", "card_theory_formal_logic_epistemology", "A = B iff same properties"),
    # photography
    ("photography", "photography.exposure_value", "logarithmic", "card_theory_photographic_exposure_theory", "EV = log2(N^2 / t)"),
    ("photography", "photography.reciprocity_equivalent", "logarithmic", "card_theory_photographic_exposure_theory", "equal EV settings equivalent"),
    ("photography", "photography.angle_of_view", "trigonometric", "card_theory_photographic_exposure_theory", "AOV = 2 atan(d / 2f)"),
    ("photography", "photography.hyperfocal_distance", "ratio", "card_theory_depth_of_field", "H = f^2/(N c) + f"),
    # photonics — light engineered as a signal/computing medium (guided, resonant, active, nonlinear).
    # A connective domain: each check instantiates a form already carried across many fields, so it
    # BRIDGES optics <-> electrical <-> quantum <-> materials. (Measured to heal the structure: closing
    # two of the topology's eight voids where noise adds holes — 2026-09-19.)
    ("photonics", "photonics.waveguide_v_number", "wave", "card_theory_wave_optics", "V = 2*pi*a*NA/lambda (single-mode iff V<=2.405)"),
    ("photonics", "photonics.ring_resonator_fsr", "periodic", "card_theory_wave_optics", "FSR = c/(n_g*L)"),
    ("photonics", "photonics.fiber_loss", "logarithmic", "card_theory_wave_optics", "P_out(dBm) = P_in - alpha*L"),
    ("photonics", "photonics.electro_optic_vpi", "linear_flux", "card_theory_maxwell_s_equations_classical_electromagnetism", "V_pi = lambda*d/(n^3*r*L)"),
    ("photonics", "photonics.second_harmonic", "power_law", "card_theory_quantization", "P_2w ~ P_w^2"),
    ("photonics", "photonics.laser_slope", "proportion", "card_theory_quantization", "P_out = eta*(I - I_th)"),
    ("photonics", "photonics.grating_angle", "trigonometric", "card_theory_wave_optics", "d*sin(theta) = m*lambda"),
    ("photonics", "photonics.beer_lambert", "decay", "card_theory_wave_optics", "I(z) = I0*exp(-alpha*z)"),
    # physics
    ("physics", "verify_conservation", "conservation", "card_theory_conservation_of_energy", "each named quantity conserved"),
    ("physics", "verify_named_conservation", "conservation", "card_theory_conservation_of_energy", "conservation + named-law profile"),
    ("physics", "physics.kinematic_motion", "accumulation", "card_theory_newton_s_three_laws_of_motion", "d = v0 t + 0.5 a t^2"),
    ("physics", "physics.newtons_second_law", "ratio", "card_theory_newton_s_three_laws_of_motion", "F = m a"),
    ("physics", "physics.kinetic_energy", "power_law", "card_theory_newton_s_three_laws_of_motion", "KE = 0.5 m v^2"),
    # probability
    ("probability", "probability.expected_value", "accumulation", "card_theory_kolmogorov_probability_axioms", "E[X] = sum x p(x)"),
    ("probability", "probability.variance", "accumulation", "card_theory_kolmogorov_probability_axioms", "Var = sum (x-mu)^2 p"),
    ("probability", "probability.binomial", "combinatorial", "card_theory_kolmogorov_probability_axioms", "C(n,k) p^k (1-p)^(n-k)"),
    ("probability", "probability.binomial_mean", "ratio", "card_theory_kolmogorov_probability_axioms", "mean = n p"),
    ("probability", "probability.normal_cdf", "gaussian", "card_theory_central_limit_theorem", "Phi(z)"),
    ("probability", "probability.normal_within_std", "gaussian", "card_theory_central_limit_theorem", "68-95-99.7 rule"),
    ("probability", "probability.poisson", "combinatorial", "card_theory_kolmogorov_probability_axioms", "P = lambda^k e^-lambda / k!"),
    ("probability", "probability.bayes", "ratio", "card_theory_bayes_theorem", "P(A|B) = P(B|A)P(A)/P(B)"),
    ("probability", "probability.conditional", "ratio", "card_theory_bayes_theorem", "P(A|B) = P(A and B)/P(B)"),
    ("probability", "probability.independence", "ratio", "card_theory_kolmogorov_probability_axioms", "P(A and B) = P(A) P(B)"),
    # quantum_computing
    ("quantum_computing", "quantum_computing.qubit_normalization", "conservation", "card_theory_quantum_information___entanglement__von_neumann_entr", "sum |amp|^2 = 1"),
    ("quantum_computing", "quantum_computing.grover_iterations", "power_law", "card_theory_quantum_information___entanglement__von_neumann_entr", "T = floor(pi sqrt(N)/4)"),
    ("quantum_computing", "quantum_computing.shor_period", "modular", "card_theory_cryptographic_security", "a^r = 1 (mod N)"),
    ("quantum_computing", "quantum_computing.von_neumann_entropy", "logarithmic", "card_theory_quantum_information___entanglement__von_neumann_entr", "S = -sum lambda log2 lambda"),
    ("quantum_computing", "quantum_computing.quantum_fidelity", "ratio", "card_theory_quantum_information___entanglement__von_neumann_entr", "F = |<psi|phi>|^2"),
    # real_estate
    ("real_estate", "real_estate.monthly_mortgage", "exponential", "card_theory_income_capitalization", "M = P r(1+r)^n/((1+r)^n-1)"),
    ("real_estate", "real_estate.cap_rate", "ratio", "card_theory_income_capitalization", "cap = NOI / value"),
    ("real_estate", "real_estate.gross_rent_mult", "ratio", "card_theory_income_capitalization", "GRM = price / annual_rent"),
    ("real_estate", "real_estate.loan_to_value", "ratio", "card_theory_real_estate_valuation", "LTV = loan / value"),
    ("real_estate", "real_estate.debt_service_cov", "ratio", "card_theory_income_capitalization", "DSCR = NOI / debt_service"),
    ("real_estate", "real_estate.rental_yield", "ratio", "card_theory_income_capitalization", "yield = annual_rent / value"),
    # retrieval (the engine measuring itself)
    ("retrieval", "retrieval.precision", "ratio", "card_theory_signal_detection", "precision = TP/(TP+FP)"),
    ("retrieval", "retrieval.recall_of_known", "ratio", "card_theory_signal_detection", "recall = TP/(TP+FN)"),
    # rhetoric
    ("rhetoric", "rhetoric.syllogism_validity", "boolean_logic", "card_theory_boolean_algebra_propositional_logic", "valid mood-figure of a syllogism"),
    # soil_science
    ("soil_science", "soil_science.npk_requirement", "ratio", "card_theory_nutrient_cycling_agronomy", "kg = rate * area"),
    ("soil_science", "soil_science.irrigation_req", "ratio", "card_theory_nutrient_cycling_agronomy", "ETc = ET0 * Kc"),
    ("soil_science", "soil_science.lime_requirement", "ratio", "card_theory_nutrient_cycling_agronomy", "t/ha = (target-current) rate"),
    # sports_analytics
    ("sports_analytics", "sports_analytics.pythagorean_expectation", "power_law", "card_theory_sabermetrics_sports_analytics", "W% = RS^2/(RS^2+RA^2)"),
    ("sports_analytics", "sports_analytics.elo_expected_score", "logistic", "card_theory_win_probability_models", "E = 1/(1+10^((Rb-Ra)/400))"),
    ("sports_analytics", "sports_analytics.elo_rating_update", "recursion", "card_theory_win_probability_models", "R' = R + K(S - E)"),
    ("sports_analytics", "sports_analytics.games_behind", "ratio", "card_theory_sabermetrics_sports_analytics", "GB = ((Wl-Wt)+(Lt-Ll))/2"),
    # statistics (hypothesis testing)
    ("statistics", "verify_pvalue_calibration", "hypothesis_test", "card_theory_null_hypothesis_significance_testing", "recompute p from inputs"),
    ("statistics", "verify_significance_consistency", "hypothesis_test", "card_theory_null_hypothesis_significance_testing", "significant iff p <= alpha"),
    ("statistics", "verify_multiple_comparisons", "hypothesis_test", "card_theory_null_hypothesis_significance_testing", "corrected p (Bonferroni/BH)"),
    ("statistics", "verify_confidence_interval", "hypothesis_test", "card_theory_null_hypothesis_significance_testing", "CI = estimate +- z SE"),
    ("biology", "verify_sample_size_powered", "hypothesis_test", "card_theory_null_hypothesis_significance_testing", "two-sample t-test power"),
    ("biology", "verify_hardy_weinberg", "hypothesis_test", "card_theory_hardy_weinberg_equilibrium", "chi^2 vs HWE p^2:2pq:q^2"),
    ("biology", "verify_mendelian", "hypothesis_test", "card_theory_mendelian_inheritance", "chi^2 vs Mendelian ratio"),
    ("biology", "verify_molarity", "ratio", "card_theory_stoichiometry_the_mole_concept", "M = moles / L"),
    # thermodynamics
    ("thermodynamics", "thermodynamics.carnot_efficiency", "ratio", "card_theory_carnot_efficiency", "eta = 1 - Tc/Th"),
    ("thermodynamics", "thermodynamics.ideal_gas_law", "ratio", "card_theory_ideal_gas_law", "P V = n R T"),
    ("thermodynamics", "thermodynamics.specific_heat", "ratio", "card_theory_heat_transfer", "Q = m c dT"),
    ("thermodynamics", "thermodynamics.entropy_change", "ratio", "card_theory_second_law_of_thermodynamics", "dS = Q / T"),
    ("thermodynamics", "thermodynamics.clausius_clapeyron", "exponential", "card_theory_phase_theory", "ln(P2/P1) = -L/R (1/T2 - 1/T1)"),
    # units
    ("units", "units.conversion", "ratio", "card_theory_dimensional_analysis", "x * (unit_b / unit_a)"),
]


def _harvest() -> set[tuple[str, str]]:
    """Every (domain, verifier_name) that actually exists in the engine source."""
    found = set()
    if not VERIFIER_DIR.exists():
        return found
    for f in sorted(VERIFIER_DIR.glob("*.py")):
        if f.name in ("__init__.py", "base.py"):
            continue
        domain = f.stem
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("verify_"):
                cname = ""
                for n in ast.walk(node):
                    if isinstance(n, ast.Assign) and any(
                        isinstance(t, ast.Name) and t.id == "name" for t in n.targets
                    ) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                        cname = n.value.value
                        break
                found.add((domain, cname or node.name))
    return found


def _slug(name: str) -> str:
    return "v_" + name.replace(".", "_")


def _title(name: str) -> str:
    seg = name.split(".")[-1]
    if seg.startswith("verify_"):
        seg = seg[len("verify_"):]
    return seg.replace("_", " ").strip().capitalize()


def verifier_calcs() -> list[tuple]:
    """(slug, title, formula, domain, form, note) for every placed verifier."""
    rows = []
    for domain, name, form, _theory, formula in PLACE:
        rows.append((_slug(name), _title(name), formula, domain, form,
                     f"engine verifier {name} — the deterministic check the concordance runs"))
    return rows


def verifier_theory() -> dict[str, str]:
    """slug -> parent theory id, for placed verifiers that have a clean one."""
    return {_slug(name): theory for _d, name, _f, theory, _fo in PLACE if theory}


def cmd_check(known_forms: set[str] | None = None, theory_ids: set[str] | None = None) -> int:
    found = _harvest()
    rc = 0
    # 1) every placed verifier is a real verifier in the engine source
    missing = [(d, n) for d, n, *_ in PLACE if (d, n) not in found]
    if missing:
        rc = 3
        print(f"NOT FOUND in engine source ({len(missing)}):")
        for d, n in missing:
            print(f"    {d} :: {n}")
    # 2) no duplicate slugs
    slugs = [_slug(n) for _d, n, *_ in PLACE]
    dupes = sorted({s for s in slugs if slugs.count(s) > 1})
    if dupes:
        rc = 3
        print("duplicate slugs:", dupes)
    # 3) forms known (base forms come from the caller; new forms are ours)
    forms_ok = set(NEW_FORMS)
    if known_forms:
        forms_ok |= known_forms
    bad_form = sorted({form for *_a, form, _t, _f in [(d, n, form, t, f) for d, n, form, t, f in PLACE] if form not in forms_ok}) if known_forms else []
    if bad_form:
        rc = 3
        print("unknown forms:", bad_form)
    # 4) theory targets resolve (only when the caller supplies the id set)
    if theory_ids is not None:
        bad_theory = sorted({t for _d, _n, _fm, t, _f in PLACE if t and t not in theory_ids})
        if bad_theory:
            rc = 3
            print("unresolved theory targets:")
            for t in bad_theory:
                print("   ", t)
    placed = len(PLACE)
    linked = sum(1 for *_r, t, _f in [(d, n, fm, t, f) for d, n, fm, t, f in PLACE] if t)
    print(f"placed {placed} verifiers of {len(found)} in source "
          f"({len(found)-placed} left as non-computational checks); "
          f"{linked}/{placed} linked to a parent theory; {len(NEW_FORMS)} new forms.")
    return rc


def cmd_list() -> int:
    from collections import defaultdict
    by = defaultdict(list)
    for _d, name, form, _t, formula in PLACE:
        by[form].append((name, formula))
    for form in sorted(by):
        print(f"== {form}  ({len(by[form])})")
        for name, formula in sorted(by[form]):
            print(f"     {name:44} {formula}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    if args.list:
        return cmd_list()
    # standalone --check: pull the base forms + theory ids so validation is real
    known_forms = None
    theory_ids = None
    try:
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).resolve().parent))
        from seed_calculations import FORMS as _BASE  # noqa: E402
        known_forms = set(_BASE)
    except Exception:  # noqa: BLE001
        pass
    import json as _json
    _tp = Path(__file__).resolve().parent.parent / "data" / "theory_cards.jsonl"
    if _tp.exists():
        theory_ids = set()
        for line in _tp.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    theory_ids.add(_json.loads(line)["id"])
                except (ValueError, KeyError):
                    pass
    return cmd_check(known_forms, theory_ids)


if __name__ == "__main__":
    raise SystemExit(main())
