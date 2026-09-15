#!/usr/bin/env python3
"""Seed the LONE domains of THE FLOOR — grow each field that holds only one theory.

theory_map.py names the fields we have barely entered: a domain with a single theory card is a
beam resting on almost nothing. This ADDS real theories to those domains, each one gathered (a
seed of wisdom, not a fabrication) and joined to the floor by relations that carry their evidence.

NON-DESTRUCTIVE BY CONSTRUCTION. It APPENDS to data/theory_cards.jsonl and never rewrites it, so
the 178 enriched bodies and 285 connections already there are untouched. Idempotent: a card whose
id is already present is skipped. Run card_theories.py NEVER after this — it regenerates the store
from the catalogue as stubs and would clobber every enrichment (this file included).

    python tools/seed_lone_domains.py --domain exercise_science
    python tools/seed_lone_domains.py --all
    python tools/seed_lone_domains.py --check      # validate connection targets, write nothing
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

STORE = Path("data/theory_cards.jsonl")

_CLASS = {
    "seals": "a deterministic verifier can CONFIRM or BREAK checkable claims drawn from it, and seal them",
    "partial": "specific relations verify; the theory as a whole is not a sealable computation",
    "map-only": "out of scope for sealing — foundational, empirical or interpretive (RESONANCE)",
}
_SECTION_BANDS = {
    "Life sciences": ["life", "sciences"],
    "Physics & energy": ["physics", "energy"],
    "Applied & human systems": ["applied", "human", "systems"],
    "Earth & space": ["earth", "space"],
    "Humanities & witness": ["humanities", "witness"],
    "Mathematics & formal reasoning": ["mathematics", "formal", "reasoning"],
    "Chemistry & materials": ["chemistry", "materials"],
}

# domain -> [ {id, title, subject, calib, section, body, conns:[(rel, target_id, evidence)]} ]
# rel in: rests_on | limits | same_form.  member_of card_spine_theories is added automatically.
DOMAINS: dict[str, list[dict]] = {
    "exercise_science": [
        {
            "id": "card_theory_biomechanics_human_movement",
            "title": "Biomechanics of human movement (levers, torque, ground reaction)",
            "subject": "Biomechanics",
            "calib": "seals",
            "section": "Life sciences",
            "body": (
                "The body is a system of levers. Every joint is a fulcrum, every muscle a force applied "
                "at a moment arm, and the useful output is TORQUE = force x moment arm. Change the moment "
                "arm and you change the force required for the same effect — which is why leverage, not "
                "raw strength, decides a grappling exchange or a safe lift. Three lever classes appear "
                "throughout the skeleton (the forearm is third-class: speed bought at the cost of force). "
                "Ground reaction is Newton's third law made visible — push the earth, the earth pushes "
                "back, and every stride and takedown is powered by that returned force. Because the "
                "quantities are torque, force and angle, the checkable claims here SEAL."
            ),
            "conns": [
                ("rests_on", "card_theory_newton_s_three_laws_of_motion",
                 "torque and ground reaction are Newton's laws applied to the skeleton; force x moment arm and action-reaction"),
                ("same_form", "card_theory_structural_statics",
                 "the body's levers obey the SAME statics as a loaded beam — moment = force x distance, equilibrium of moments; a cross-domain isomorphism between architecture and anatomy"),
                ("rests_on", "card_theory_neuromuscular_size_principle",
                 "the force that turns the levers is supplied by recruited motor units — biomechanics rests on the neural force source"),
            ],
        },
        {
            "id": "card_theory_neuromuscular_size_principle",
            "title": "Neuromuscular recruitment & the size principle (Henneman)",
            "subject": "Size principle",
            "calib": "partial",
            "section": "Life sciences",
            "body": (
                "Muscle force is graded, not switched. As demand rises the nervous system recruits motor "
                "units in a fixed order — small, slow, fatigue-resistant units first, then progressively "
                "larger, faster ones (Henneman's SIZE PRINCIPLE), and adds RATE CODING on top. The "
                "recruitment ORDER is a checkable, testable claim; the theory as a whole is a physiological "
                "framework, so it calibrates PARTIAL. It explains why early strength gains are largely "
                "NEURAL — the trainee learns to recruit and synchronise motor units — before any muscle "
                "grows, and why maximal and explosive work must reach the high-threshold units that "
                "ordinary effort never calls."
            ),
            "conns": [
                ("rests_on", "card_theory_homeostasis_physiological_regulation",
                 "graded, ordered recruitment is homeostatic control applied to force output — the set point defended is the demanded tension"),
            ],
        },
        {
            "id": "card_theory_motor_learning_skill_acquisition",
            "title": "Motor learning & the stages of skill acquisition (Fitts & Posner)",
            "subject": "Motor learning",
            "calib": "partial",
            "section": "Life sciences",
            "body": (
                "Skill is acquired in stages: COGNITIVE (understanding the task, many errors), ASSOCIATIVE "
                "(refining, fewer errors), and AUTONOMOUS (the movement runs without conscious attention). "
                "Improvement follows the POWER LAW OF PRACTICE — performance time falls as a power function "
                "of repetitions, a straight line on a log-log plot — which is a checkable relation, so the "
                "theory calibrates PARTIAL while the stage taxonomy stays descriptive. Feedback and "
                "distributed (spaced) practice govern how fast the stages are climbed. This is the science "
                "under coaching itself: the autonomous stage is what a drilled technique becomes, freeing "
                "attention for the opponent instead of the mechanics."
            ),
            "conns": [
                ("rests_on", "card_theory_neuromuscular_size_principle",
                 "a learned skill is, physically, a learned recruitment pattern — motor learning rests on the neuromuscular substrate it organises"),
            ],
        },
    ],
    # --- Frontier concepts hunted from the wild (2026-09-13): real, deep theories gathered from a
    #     speculative text, given their due and bounded. These enrich populated domains, not lone ones. ---
    "mathematics": [
        {
            "id": "card_theory_noncommutative_geometry",
            "title": "Noncommutative geometry & the spectral triple (Connes)",
            "subject": "Noncommutative geometry",
            "calib": "map-only",
            "section": "Mathematics & formal reasoning",
            "body": (
                "Alain Connes' spectral triple (A, H, D) — an algebra A, a Hilbert space H, and a Dirac "
                "operator D whose spectrum carries the metric — encodes a geometry algebraically. A "
                "commutative A gives ordinary Riemannian geometry; a noncommutative A describes spaces with "
                "no points, the natural language for quantum spacetime and for the internal symmetries of "
                "particle physics. The Connes-Chamseddine SPECTRAL ACTION even recovers the Standard Model's "
                "gauge content and the Einstein-Hilbert term from a single spectral principle. Calibrates "
                "MAP-ONLY: a foundational framework, resonant, not one sealable computation."
            ),
            "conns": [
                ("rests_on", "card_theory_linear_algebra",
                 "a spectral triple is operators on a Hilbert space; the geometry is read off their eigenvalues"),
                ("same_form", "card_theory_general_relativity",
                 "both encode geometry — GR as manifold curvature, NCG as the spectrum of the Dirac operator; the spectral action reproduces the Einstein-Hilbert term"),
            ],
        },
        {
            "id": "card_theory_spectral_geometry",
            "title": "Spectral geometry (can one hear the shape of a drum?)",
            "subject": "Spectral geometry",
            "calib": "partial",
            "section": "Mathematics & formal reasoning",
            "body": (
                "How far does the eigenvalue spectrum of the Laplacian determine a shape? Mark Kac (1966): "
                "'Can one hear the shape of a drum?' The spectrum fixes real invariants — area, perimeter, "
                "total curvature (Weyl's law) — so much CAN be heard. But the full answer is NO: "
                "Gordon-Webb-Wolpert (1992) built isospectral, non-isometric drums, identical spectra and "
                "different shapes. That LIMIT is exactly why reconstructing an exact structure from its "
                "eigenvalues alone is under-determined. Calibrates PARTIAL: the isospectral results are "
                "theorems; the reconstruction question is open."
            ),
            "conns": [
                ("rests_on", "card_theory_linear_algebra",
                 "eigenvalues of the Laplacian and Dirac operator are the whole subject"),
                ("same_form", "card_theory_noncommutative_geometry",
                 "both read geometry from a spectrum; NCG makes the spectrum the very definition of the space"),
            ],
        },
        {"id": "card_theory_category_theory", "title": "Category theory (objects, morphisms, composition)",
         "subject": "Category theory", "calib": "map-only", "section": "Mathematics & formal reasoning",
         "body": "Category theory studies structure through OBJECTS and the MORPHISMS (arrows) between them, with composition as the only primitive; functors map between categories, natural transformations between functors. It is the mathematics of mathematics — the same universal constructions (products, limits, adjunctions) recur across algebra, topology and logic. MAP-ONLY: a unifying framework, not one computation.",
         "conns": [("same_form", "card_theory_graph_theory", "a category is a graph with composition and identities — both are objects joined by arrows")]},
        {"id": "card_theory_golden_ratio_phyllotaxis", "title": "The golden ratio & phyllotaxis",
         "subject": "Golden ratio", "calib": "seals", "section": "Mathematics & formal reasoning",
         "body": "phi = (1+sqrt5)/2 is the most irrational number, worst approximated by any fraction, so the golden angle (~137.5 deg) places successive elements with no repeating gap — which is why sunflowers, pinecones, and this very theory-map's layout use it. Fibonacci ratios converge to phi. SEALS: the ratio and angle compute exactly.",
         "conns": [("rests_on", "card_theory_euclidean_geometry_the_parallel_postulate", "phi is Euclid's division of a line in extreme and mean ratio (Elements VI) — a compass-and-straightedge construction")]},
        {"id": "card_theory_information_geometry", "title": "Information geometry (statistics as curved space)",
         "subject": "Information geometry", "calib": "partial", "section": "Mathematics & formal reasoning",
         "body": "Probability distributions form a curved manifold whose metric is the Fisher information; estimation, testing and learning become GEOMETRY — distances, geodesics and curvature on the space of models. PARTIAL: the Fisher metric computes; the program is broad.",
         "conns": [("rests_on", "card_theory_kolmogorov_probability_axioms", "the manifold is the space of probability measures the axioms define"),
                   ("same_form", "card_theory_general_relativity", "inference on a curved manifold with a metric — statistics wearing GR's geometry")]},
        {"id": "card_theory_stochastic_processes", "title": "Stochastic processes & Ito calculus",
         "subject": "Stochastic processes", "calib": "seals", "section": "Mathematics & formal reasoning",
         "body": "The mathematics of random evolution in continuous time. Its canonical object is the WIENER PROCESS (Brownian motion) — a path that is continuous everywhere yet differentiable nowhere, with independent Gaussian increments. Ito's calculus integrates against it and supplies a chain rule (Ito's lemma) that corrects ordinary calculus for the path's quadratic variation, turning 'drift plus noise' into stochastic differential equations dX = mu dt + sigma dW. It is the frame under a whole form on the calculation map — Black-Scholes, the Langevin equation, genetic drift, and mean-reverting (Ornstein-Uhlenbeck) processes are all SDEs. SEALS: a rigorous theory; Ito's lemma and the Wiener measure are proven.",
         "conns": [("rests_on", "card_theory_kolmogorov_probability_axioms", "a stochastic process is a probability measure on the space of paths — built directly on the measure-theoretic axioms of probability"),
                   ("rests_on", "card_theory_central_limit_theorem", "Donsker's theorem: the Wiener process is the scaling limit of a random walk — the functional CLT — so its increments are Gaussian"),
                   ("same_form", "card_theory_fundamental_theorem_of_calculus", "Ito calculus is the fundamental theorem of calculus adapted to a nowhere-differentiable path — an integral and a chain rule corrected for quadratic variation")]},
    ],
    "physics": [
        {
            "id": "card_theory_casimir_effect",
            "title": "The Casimir effect (structured energy of the quantum vacuum)",
            "subject": "Casimir effect",
            "calib": "seals",
            "section": "Physics & energy",
            "body": (
                "Two uncharged conducting plates in vacuum attract: the boundary excludes some vacuum field "
                "modes, so the zero-point energy between them is lower than outside. Casimir (1948) computed "
                "the force per area, F/A = -pi^2 h-bar c / (240 d^4), confirmed experimentally (Lamoreaux, "
                "1997). Direct evidence that the quantum vacuum carries real, structured energy. Calibrates "
                "SEALS: the force law is a checkable computation."
            ),
            "conns": [
                ("rests_on", "card_theory_standard_model_quantum_field_theory",
                 "the Casimir force is zero-point vacuum energy — a direct consequence of quantizing the field"),
            ],
        },
        {
            "id": "card_theory_superfluid_vacuum_theory",
            "title": "Superfluid vacuum theory (the vacuum as a quantum liquid)",
            "subject": "Superfluid vacuum",
            "calib": "map-only",
            "section": "Physics & energy",
            "body": (
                "A minority research program (Volovik and others) models the physical vacuum as a superfluid "
                "or Bose-Einstein condensate: elementary particles are collective excitations of the liquid, "
                "and Lorentz symmetry and even gravity EMERGE as long-wavelength effective phenomena rather "
                "than fundamentals. Suggestive — it reproduces relativistic dispersion at low energy and "
                "offers an emergent-gravity picture — but unconfirmed and empirically thin. Calibrates "
                "MAP-ONLY: a real but speculative foundational program, resonant, not sealed."
            ),
            "conns": [
                ("rests_on", "card_theory_standard_model_quantum_field_theory",
                 "the excitations of the vacuum liquid play the role of the fields' quanta"),
                ("same_form", "card_theory_general_relativity",
                 "both give gravity a geometric face — GR fundamentally, SVT as an emergent effective metric in a flowing condensate"),
            ],
        },
        {"id": "card_theory_renormalization_group", "title": "The renormalization group (physics across scales)",
         "subject": "Renormalization group", "calib": "partial", "section": "Physics & energy",
         "body": "Physics looks different at different SCALES. Coarse-grain the small-scale detail, rescale, and watch the couplings run (the beta function); the flow settles onto scale-invariant fixed points. Its crown is UNIVERSALITY: utterly different microscopic systems flow to the same fixed point and obey the same macroscopic laws. PARTIAL: beta functions and exponents compute; the framework is broad.",
         "conns": [("rests_on", "card_theory_standard_model_quantum_field_theory", "renormalization tames the field theory's infinities and runs its couplings"),
                   ("same_form", "card_theory_phase_theory", "the RG was built to explain critical phenomena at phase transitions — different substances, one set of exponents")]},
        # NOTE: Noether's theorem is already carded canonically as
        # card_theory_noether_s_theorem__symmetry_and_conservation (referenced by the two
        # conservation-law cards). The duplicate that once lived here was removed to keep
        # one theorem = one card on THE FLOOR.
        {"id": "card_theory_holographic_principle", "title": "The holographic principle & black-hole entropy",
         "subject": "Holographic principle", "calib": "map-only", "section": "Physics & energy",
         "body": "The information in a region is bounded by its boundary AREA, not its volume: Bekenstein-Hawking black-hole entropy S = A/4 is the archetype, and 't Hooft and Susskind raised it to a principle — a volume may be fully described by data on its surface, so spacetime could be emergent. MAP-ONLY: foundational and unconfirmed.",
         "conns": [("rests_on", "card_theory_general_relativity", "black-hole entropy joins gravity to thermodynamics at the horizon"),
                   ("same_form", "card_theory_second_law_of_thermodynamics", "the holographic bound is the second law enforced on a horizon")]},
    ],
    "quantum_computing": [
        {
            "id": "card_theory_topological_quantum_computation",
            "title": "Topological quantum computation (non-Abelian / Fibonacci anyons)",
            "subject": "Topological quantum computation",
            "calib": "partial",
            "section": "Mathematics & formal reasoning",
            "body": (
                "Information stored in the BRAIDING of non-Abelian anyons — quasiparticles whose worldlines, "
                "when swapped, apply quantum gates that depend only on the TOPOLOGY of the braid, not its "
                "details. Because local noise cannot change a knot's topology, the computation is "
                "intrinsically protected from decoherence. Fibonacci anyons are computationally UNIVERSAL: "
                "their braids alone approximate any quantum gate. Calibrates PARTIAL: the anyon fusion rules "
                "and braid-group relations are checkable; a fault-tolerant machine is engineering not yet realized."
            ),
            "conns": [
                ("rests_on", "card_theory_quantum_mechanics",
                 "anyonic qubits are quantum states and braiding is their unitary evolution"),
            ],
        },
        {
            "id": "card_theory_quantum_error_correction",
            "title": "Quantum error correction & the threshold theorem",
            "subject": "Quantum error correction",
            "calib": "partial",
            "section": "Mathematics & formal reasoning",
            "body": (
                "Quantum information is protected by encoding one logical qubit across many physical qubits "
                "(stabilizer codes, the surface code) and correcting errors WITHOUT measuring the data. The "
                "threshold theorem: below a critical physical error rate, arbitrarily long computation becomes "
                "possible. Calibrates PARTIAL: code distances and thresholds compute; a scalable machine is engineering."
            ),
            "conns": [
                ("rests_on", "card_theory_quantum_mechanics",
                 "QEC protects quantum states against decoherence"),
                ("same_form", "card_theory_topological_quantum_computation",
                 "topological codes ARE a form of error correction — protection by redundancy vs by topology"),
            ],
        },
    ],
    # --- BULK lone-domain fill (2026-09-13): one real second theory per field, to un-lone it. ---
    "acoustics": [
        {"id": "card_theory_room_acoustics_sabine", "title": "Room acoustics & reverberation (Sabine)",
         "subject": "Room acoustics", "calib": "seals", "section": "Physics & energy",
         "body": "Sabine's law: reverberation time RT60 = 0.161 V/A (room volume over total absorption) — the time for sound to decay 60 dB. It put architectural acoustics on a quantitative footing (Wallace Sabine, 1890s) and still governs hall and studio design. SEALS: the RT60 relation computes directly.",
         "conns": [("rests_on", "card_theory_acoustic_wave_theory", "reverberation is the room's superposition of reflected acoustic waves")]},
    ],
    "calendar_time": [
        {"id": "card_theory_julian_day_number", "title": "Julian Day Number (continuous astronomical time)",
         "subject": "Julian Day", "calib": "seals", "section": "Humanities & witness",
         "body": "The Julian Day Number counts days continuously from a fixed epoch (noon, 1 Jan 4713 BCE), giving astronomy one linear clock free of calendar reform. Any date converts to a JDN and back; intervals become subtraction. SEALS: the conversion is exact arithmetic.",
         "conns": [("rests_on", "card_theory_calendar_theory", "JDN is the continuous substrate under the Gregorian calendar's civil rules"),
                   ("same_form", "card_theory_celestial_mechanics_ephemeris_prediction", "astronomical time is read from orbital motion — the same clock the ephemeris keeps")]},
    ],
    "cybersecurity": [
        {"id": "card_theory_diffie_hellman_key_exchange", "title": "Diffie-Hellman key exchange",
         "subject": "Diffie-Hellman", "calib": "partial", "section": "Applied & human systems",
         "body": "Two parties agree a shared secret over a public channel by exchanging g^a and g^b mod p; each computes g^(ab), while an eavesdropper faces the discrete-logarithm problem. Diffie-Hellman (1976) founded public-key cryptography. PARTIAL: the modular arithmetic computes; the security rests on a hardness assumption.",
         "conns": [("rests_on", "card_theory_cryptographic_security", "DH is a pillar of the PKI the cryptographic-security theory describes")]},
    ],
    "ecology": [
        {"id": "card_theory_trophic_dynamics", "title": "Trophic dynamics & ecological efficiency (Lindeman)",
         "subject": "Trophic dynamics", "calib": "partial", "section": "Life sciences",
         "body": "Energy flows up trophic levels with heavy loss at each step — Lindeman's ~10% ecological efficiency — so food chains are short and apex predators few. An ecosystem is an energy cascade obeying the second law. PARTIAL: transfer-efficiency relations compute; the whole is empirical.",
         "conns": [("rests_on", "card_theory_population_ecology", "trophic structure organizes the populations the ecology models"),
                   ("same_form", "card_theory_conservation_of_energy", "a food web is an energy-conservation ledger with loss at each transfer")]},
    ],
    "governance": [
        {"id": "card_theory_arrow_impossibility_theorem", "title": "Arrow's impossibility theorem",
         "subject": "Arrow's theorem", "calib": "map-only", "section": "Applied & human systems",
         "body": "No ranked voting rule can satisfy a short list of fairness conditions at once (unrestricted domain, Pareto, independence of irrelevant alternatives, non-dictatorship) — Arrow (1951). Collective preference cannot always be rational the way individual preference is. MAP-ONLY: a proven impossibility result the engine maps as a hard limit; it seals no computational run of its own (the governance verifier returns NOT_APPLICABLE), so it claims no seal.",
         "conns": [("limits", "card_theory_public_choice_decision_theory", "Arrow is a hard LIMIT on what any social-choice procedure can achieve")]},
    ],
    "law": [
        {"id": "card_theory_coase_theorem", "title": "The Coase theorem (law & economics)",
         "subject": "Coase theorem", "calib": "partial", "section": "Applied & human systems",
         "body": "With clear property rights and zero transaction costs, parties bargain to an efficient allocation regardless of who holds the right (Coase, 1960). Its real force is the converse: costs are never zero, so the assignment of legal rights matters for efficiency — founding law-and-economics. PARTIAL.",
         "conns": [("rests_on", "card_theory_contract_theory_rule_of_law", "Coase concerns how legal rights and contracts allocate resources"),
                   ("same_form", "card_theory_supply_demand_market_equilibrium", "bargaining drives allocation to the efficient market outcome — law meeting economics")]},
    ],
    "linear_algebra": [
        {"id": "card_theory_singular_value_decomposition", "title": "Singular value decomposition (SVD)",
         "subject": "SVD", "calib": "seals", "section": "Mathematics & formal reasoning",
         "body": "Every matrix factors as A = U Sigma V^T — orthogonal rotations and a diagonal of singular values. It reveals rank, the best low-rank approximation (Eckart-Young), and underlies PCA, latent semantic analysis, and recommender systems. SEALS: the factorization is a direct computation.",
         "conns": [("rests_on", "card_theory_linear_algebra", "SVD is the deepest factorization of a linear map")]},
    ],
    "meteorology": [
        {"id": "card_theory_geostrophic_balance", "title": "Geostrophic balance & Coriolis dynamics",
         "subject": "Geostrophic balance", "calib": "partial", "section": "Earth & space",
         "body": "In large-scale flow the pressure-gradient force balances the Coriolis force, so winds blow ALONG isobars, not across them. It is why weather systems rotate and why the same equations govern ocean gyres. PARTIAL: the balance relation computes; full dynamics are numerical.",
         "conns": [("rests_on", "card_theory_atmospheric_thermodynamics", "geostrophic flow organizes the atmosphere the thermodynamics describes"),
                   ("same_form", "card_theory_physical_oceanography", "the same Coriolis balance drives ocean gyres — one fluid dynamics across air and sea")]},
    ],
    "music_theory": [
        {"id": "card_theory_tuning_systems_comma", "title": "Tuning systems & the Pythagorean comma",
         "subject": "Tuning systems", "calib": "seals", "section": "Humanities & witness",
         "body": "Stacking pure fifths (3:2) never closes the octave (2:1): twelve fifths overshoot seven octaves by the Pythagorean comma (~23.5 cents). Every tuning is a compromise — just intonation keeps pure ratios locally, equal temperament spreads the error across twelve semitones. SEALS: the frequency ratios compute exactly.",
         "conns": [("rests_on", "card_theory_music_theory", "tuning refines the harmonic-series and temperament theory of pitch"),
                   ("same_form", "card_theory_fundamental_theorem_of_arithmetic", "pitch ratios are integer factorizations; the comma is 3^12 against 2^19 — number theory heard as sound")]},
    ],
    "periodic_table": [
        {"id": "card_theory_aufbau_configuration", "title": "Aufbau principle & electron configuration",
         "subject": "Electron configuration", "calib": "seals", "section": "Chemistry & materials",
         "body": "Electrons fill orbitals from lowest energy upward (Aufbau), under Pauli exclusion and Hund's rule, which reproduces the periodic table's shape and each element's chemistry from its configuration. SEALS: 2n^2 shell capacities and configurations compute directly.",
         "conns": [("rests_on", "card_theory_periodic_law", "configuration explains WHY the periodic law holds"),
                   ("rests_on", "card_theory_pauli_exclusion_principle", "the filling order is exclusion plus energy ordering")]},
    ],
    "oceanography": [
        {"id": "card_theory_thermohaline_circulation", "title": "Thermohaline circulation (the ocean conveyor)",
         "subject": "Thermohaline circulation", "calib": "partial", "section": "Earth & space",
         "body": "Density differences from temperature and salinity drive a global overturning conveyor: cold, salty water sinks in the North Atlantic and upwells elsewhere over ~1000-year cycles, redistributing heat and regulating climate. PARTIAL: density/stratification relations compute; the circulation is modeled.",
         "conns": [("rests_on", "card_theory_physical_oceanography", "the conveyor is hydrostatics and density stratification at planetary scale"),
                   ("same_form", "card_theory_atmospheric_thermodynamics", "ocean and atmosphere are one coupled heat engine moving energy poleward")]},
    ],
    "real_estate": [
        {"id": "card_theory_income_capitalization", "title": "Income capitalization (V = NOI / cap rate)",
         "subject": "Income capitalization", "calib": "seals", "section": "Applied & human systems",
         "body": "An income property's value is its net operating income divided by a capitalization rate (V = NOI / cap-rate) — perpetuity/Gordon-growth logic applied to real estate, tying value to yield and, through the cap rate, to interest rates. SEALS: the capitalization computes directly.",
         "conns": [("rests_on", "card_theory_real_estate_valuation", "income capitalization is the core of the valuation theory"),
                   ("same_form", "card_theory_time_value_of_money_discounting", "a cap rate is discounting a perpetuity — the time value of money, in property")]},
    ],
    # --- BULK lone-domain fill, batch 2 (2026-09-13): clear the last nine. ---
    "ephemeris": [
        {"id": "card_theory_saros_eclipse_cycle", "title": "The Saros cycle (eclipse prediction)",
         "subject": "Saros cycle", "calib": "seals", "section": "Earth & space",
         "body": "Eclipses recur in a Saros cycle of ~6585.32 days (18 years 11 days), when Sun, Moon and nodes return to nearly the same geometry. It let ancient astronomers predict eclipses without dynamics and still organizes eclipse catalogs. SEALS: the periodicity computes directly.",
         "conns": [("rests_on", "card_theory_celestial_mechanics_ephemeris_prediction", "the Saros is a beat frequency of the lunar month, year and nodal cycle the ephemeris tracks")]},
    ],
    "geography": [
        {"id": "card_theory_central_place_theory", "title": "Central place theory (Christaller)",
         "subject": "Central place theory", "calib": "partial", "section": "Applied & human systems",
         "body": "Settlements arrange in a nested hexagonal hierarchy of market, transport and administrative areas, set by the range and threshold of the goods they offer (Christaller, 1933). It is the geometry of why towns sit where they do. PARTIAL: the hierarchy relations compute; real landscapes deviate.",
         "conns": [("rests_on", "card_theory_supply_demand_market_equilibrium", "the range and threshold of a good are its supply-demand geography — settlement follows the market")]},
    ],
    "history_chronology": [
        {"id": "card_theory_astronomical_dating", "title": "Astronomical dating (anchoring history to the sky)",
         "subject": "Astronomical dating", "calib": "partial", "section": "Humanities & witness",
         "body": "Dated eclipses, planetary conjunctions and heliacal risings recorded in ancient texts fix absolute calendar dates for otherwise floating chronologies — an eclipse over Nineveh anchors Assyrian regnal lists. PARTIAL: the astronomy computes exactly; matching it to a record is interpretive.",
         "conns": [("rests_on", "card_theory_historical_chronology", "astronomical anchors convert relative regnal chronology into absolute dates"),
                   ("same_form", "card_theory_celestial_mechanics_ephemeris_prediction", "history is dated by running the ephemeris backward to a recorded sky")]},
    ],
    "labor": [
        {"id": "card_theory_human_capital", "title": "Human capital theory (Becker, Mincer)",
         "subject": "Human capital", "calib": "partial", "section": "Applied & human systems",
         "body": "Education and training are investments that raise a worker's productivity and future earnings; the Mincer equation relates wages to schooling and experience (Becker, Mincer). It reframed skill as capital with a rate of return. PARTIAL: the earnings relations estimate; causation is contested.",
         "conns": [("rests_on", "card_theory_labor_economics", "human capital sets the wage the labor market pays"),
                   ("same_form", "card_theory_time_value_of_money_discounting", "schooling is an investment with a discounted stream of returns — finance applied to a life")]},
    ],
    "molecular_geometry": [
        {"id": "card_theory_molecular_symmetry_point_groups", "title": "Molecular symmetry & point groups",
         "subject": "Molecular symmetry", "calib": "seals", "section": "Chemistry & materials",
         "body": "A molecule's symmetry operations form a point group, and that group predicts its polarity, chirality, allowed spectroscopic transitions and orbital combinations. Group theory turns shape into chemistry. SEALS: symmetry classification is exact.",
         "conns": [("rests_on", "card_theory_vsepr_theory", "point-group symmetry is read off the VSEPR-predicted geometry")]},
    ],
    "nutrition": [
        {"id": "card_theory_macronutrient_metabolism", "title": "Macronutrient metabolism & glycemic response",
         "subject": "Macronutrient metabolism", "calib": "partial", "section": "Life sciences",
         "body": "Carbohydrate, fat and protein follow distinct metabolic paths and yield energy at 4-9-4 kcal/g; the glycemic index ranks how fast a carbohydrate raises blood glucose, shaping insulin response. PARTIAL: energy and index values compute; individual response varies.",
         "conns": [("rests_on", "card_theory_bioenergetics_energy_balance", "metabolism is the bioenergetics of specific fuels"),
                   ("same_form", "card_theory_exercise_physiology", "intake and expenditure are two sides of one energy ledger")]},
    ],
    "photography": [
        {"id": "card_theory_depth_of_field", "title": "Depth of field & hyperfocal distance",
         "subject": "Depth of field", "calib": "seals", "section": "Applied & human systems",
         "body": "The zone of acceptable sharpness is set by aperture, focal length, subject distance and the circle of confusion; focusing at the hyperfocal distance maximizes it. It is geometric optics applied to the sensor plane. SEALS: the DoF and hyperfocal relations compute directly.",
         "conns": [("rests_on", "card_theory_photographic_exposure_theory", "depth of field is governed by the aperture the exposure theory sets"),
                   ("same_form", "card_theory_wave_optics", "focus and the circle of confusion are optics — the lens equation on a sensor")]},
    ],
    "rhetoric": [
        {"id": "card_theory_toulmin_argument", "title": "The Toulmin model of argumentation",
         "subject": "Toulmin model", "calib": "partial", "section": "Humanities & witness",
         "body": "An argument decomposes into claim, grounds (data), warrant (the bridge), backing, qualifier and rebuttal (Toulmin, 1958). It maps how real, non-deductive arguments actually persuade, beyond bare formal validity. PARTIAL: the structure classifies; soundness is judgment.",
         "conns": [("rests_on", "card_theory_aristotelian_rhetoric_fallacy_taxonomy", "Toulmin refines the classical account of how arguments are built and where they fail"),
                   ("same_form", "card_theory_formal_logic_epistemology", "the warrant is the informal cousin of a logical inference rule — argument meeting logic")]},
    ],
    "sports_analytics": [
        {"id": "card_theory_win_probability_models", "title": "Win-probability & expected-value models",
         "subject": "Win-probability models", "calib": "partial", "section": "Applied & human systems",
         "body": "Every game state maps to a probability of winning, updated play by play; expected-value metrics (expected goals, win probability added, WAR) credit each action by how much it shifts that probability. PARTIAL: the models compute from data; their assumptions are testable.",
         "conns": [("rests_on", "card_theory_sabermetrics_sports_analytics", "win-probability models generalize sabermetrics from tallies to state-dependent value"),
                   ("same_form", "card_theory_bayes_theorem", "each play is a Bayesian update of the probability of winning")]},
    ],
    "computer_science": [
        {"id": "card_theory_kolmogorov_complexity", "title": "Algorithmic information (Kolmogorov complexity)",
         "subject": "Kolmogorov complexity", "calib": "map-only", "section": "Mathematics & formal reasoning",
         "body": "The complexity of a string is the length of the shortest program that outputs it (Kolmogorov, Chaitin, Solomonoff). It formalizes randomness (incompressible = random) and Occam's razor (prefer the shortest explanation) — but is provably UNCOMPUTABLE in general. MAP-ONLY: profound and uncomputable.",
         "conns": [("rests_on", "card_theory_shannon_information_theory", "algorithmic information is the individual-string counterpart of Shannon's ensemble entropy"),
                   ("same_form", "card_theory_church_turing_thesis_computability", "its uncomputability is a Turing-halting result in disguise")]},
        {"id": "card_theory_network_science", "title": "Network science (scale-free & small-world graphs)",
         "subject": "Network science", "calib": "partial", "section": "Applied & human systems",
         "body": "Real networks — social, biological, technological — are rarely random: scale-free (a few high-degree hubs), small-world (short paths between any two nodes), robust to random failure yet fragile to hub attack. PARTIAL: degree distributions and path lengths compute; models idealize.",
         "conns": [("rests_on", "card_theory_graph_theory", "network science is graph theory on large, evolving, real graphs"),
                   ("same_form", "card_theory_network_theory", "both study connectivity — one the internet's routing, one the science of connection itself")]},
    ],
    "geometry": [
        {"id": "card_theory_platonic_solids", "title": "The five Platonic solids",
         "subject": "Platonic solids", "calib": "seals", "section": "Mathematics & formal reasoning",
         "body": "There are EXACTLY five convex regular polyhedra — tetrahedron, cube, octahedron, dodecahedron, icosahedron — provable from Euler's formula V - E + F = 2 and the geometry of regular faces meeting at a vertex. Kepler once tried to nest them as the planetary orbits. SEALS: the enumeration is a proof — exactly five.",
         "conns": [("rests_on", "card_theory_euclidean_geometry_the_parallel_postulate", "the regular solids are Euclidean; that there are five is a theorem of that geometry"),
                   ("same_form", "card_theory_graph_theory", "the proof runs through Euler's polyhedron formula — the solids are planar graphs")]},
        {"id": "card_theory_projective_geometry", "title": "Projective geometry (perspective & the cross-ratio)",
         "subject": "Projective geometry", "calib": "seals", "section": "Mathematics & formal reasoning",
         "body": "The geometry of projection and perspective. Add a 'line at infinity' so that ANY two lines meet — parallels included — and drop distance and angle, keeping only incidence (which points lie on which lines). What survives is the CROSS-RATIO of four collinear points, the one number every projection preserves. Points and lines become interchangeable (duality), and Klein's Erlangen program recasts the whole subject as the invariant theory of the projective group. It is the frame behind perspective drawing, the pinhole camera, and homogeneous coordinates in graphics. SEALS: a rigorous classical geometry; the cross-ratio's invariance is a theorem.",
         "conns": [("same_form", "card_theory_group_theory", "Erlangen program: projective geometry IS the invariant theory of the projective group PGL — the cross-ratio is exactly what that group of transformations preserves"),
                   ("limits", "card_theory_euclidean_geometry_the_parallel_postulate", "Euclidean geometry is the restricted case: single out a line at infinity and restore a metric, and parallels and distance reappear — projective geometry is the wider frame where the parallel postulate's exception dissolves"),
                   ("same_form", "card_theory_map_projections", "central (perspective) projection from a single point — the draftsman's and the camera's map — is itself a projective transformation")]},
    ],
    "medicine": [
        {"id": "card_theory_free_energy_principle", "title": "The free-energy principle (Friston)",
         "subject": "Free-energy principle", "calib": "map-only", "section": "Life sciences",
         "body": "Living systems resist entropy by minimizing variational free energy — a bound on surprise, i.e. prediction error — over their sensory states. Perception updates the model, action changes the world to fit it, and both reduce the same quantity: life as a thing that MODELS its world to persist (Friston). MAP-ONLY: an ambitious unifying framework, contested.",
         "conns": [("rests_on", "card_theory_bayes_theorem", "free-energy minimization is approximate Bayesian inference"),
                   ("same_form", "card_theory_second_law_of_thermodynamics", "resisting entropy by modeling the world — the thermodynamics of being alive")]},
    ],
}

SPINE_CONN = {"to_card_id": "card_spine_theories", "relationship": "member_of",
              "evidence": "a theory the sciences and math run on, calibrated"}


def _existing_ids() -> set[str]:
    ids = set()
    if STORE.exists():
        for line in STORE.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                ids.add(json.loads(line)["id"])
            except (ValueError, KeyError):
                pass
    return ids


def build_card(domain: str, d: dict) -> dict:
    calib = d["calib"]
    section = d["section"]
    body = (f"{d['title']} — an engine domain that can touch it: {domain}. "
            f"Calibration: {calib} — {_CLASS[calib]}. {d['body']}")
    conns = [dict(SPINE_CONN)]
    for rel, target, ev in d["conns"]:
        conns.append({"to_card_id": target, "relationship": rel, "evidence": ev})
    return {
        "id": d["id"], "kind": "reference", "title": d["title"][:180], "body": body,
        "source": {"label": "The Theory Assay — calibrated, not judged (lone-domain seeding)",
                   "url": "", "domain": domain, "authority_tier": "reference"},
        "shelf": "theories", "box": "theory",
        "bands": ["theory", domain, calib, "calibration"] + _SECTION_BANDS.get(section, []),
        "subject": d["subject"],
        "connections": conns,
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
        "generated": False,
        "extra": {"calibration": calib, "engine_domain": domain, "section": section},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", help="seed one lone domain")
    ap.add_argument("--all", action="store_true", help="seed every defined domain")
    ap.add_argument("--check", action="store_true", help="validate connection targets; write nothing")
    args = ap.parse_args()

    existing = _existing_ids()
    targets = set(DOMAINS)
    if args.domain:
        targets = {args.domain} if args.domain in DOMAINS else set()
        if not targets:
            print(f"no definitions for domain '{args.domain}'")
            return 1
    elif not (args.all or args.check):
        print("give --domain <name>, --all, or --check")
        return 2

    planned = []
    for dom in sorted(targets):
        for d in DOMAINS[dom]:
            planned.append((dom, d))

    # every connection target must resolve to an existing card or one we are about to add
    will_exist = existing | {d["id"] for _dom, d in planned}
    unresolved = []
    for dom, d in planned:
        for _rel, target, _ev in d["conns"]:
            if target not in will_exist:
                unresolved.append((d["id"], target))
    if unresolved:
        print("UNRESOLVED connection targets (fix before seeding):")
        for src, tgt in unresolved:
            print(f"   {src}  ->  {tgt}")
        return 3

    new = [(dom, d) for dom, d in planned if d["id"] not in existing]
    if args.check:
        print(f"OK: {len(planned)} cards planned, {len(new)} new, all connection targets resolve.")
        return 0
    if not new:
        print("nothing to add — all planned cards already present (idempotent).")
        return 0

    with STORE.open("a", encoding="utf-8") as fh:
        for _dom, d in new:
            fh.write(json.dumps(build_card(_dom, d), ensure_ascii=False) + "\n")
    print(f"appended {len(new)} theory cards -> {STORE}")
    for dom, d in new:
        print(f"   + [{dom}] {d['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
