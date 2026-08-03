#!/usr/bin/env python3
"""THE FLOOR — the aligned theories, assembled across domains.

    PYTHONPATH=src python tools/assemble_floor.py --dry-run
    PYTHONPATH=src python tools/assemble_floor.py

Matt, 2026-08-02: *"We should have assembled the aligned theories across domains. That was the
floor. Reality itself mapped... along with a coherent language model that can communicate reality
effectively."*

MEASURED FIRST, and the measurement is the indictment (2026-08-02, at the start: 99 cards on
the shelf, now 110 —
**zero theory→theory edges — zero of them crossing a domain.** The catalogue was built, the assay
was run, the cards were minted, and then each one was left standing alone on its own tile. A
hundred true statements side by side is a *pile*; the floor is what you get when you can walk
from any one of them to the ones it rests on. Cell theory and the central dogma had no path
between them. Bayes did not know it stood on Kolmogorov.

WHAT AN EDGE MAY BE HERE. Only relations that are FOUND — readable off the theories themselves,
checkable by anyone who knows the field — never a resemblance I liked the sound of:

  rests_on   B is not statable without A. Bayes' theorem rests on the Kolmogorov axioms; the
             central dogma rests on cell theory. Directional, and the direction is the argument.
  limits     A bounds what B can claim about itself. Gödel limits Peano and ZFC and the
             Church–Turing thesis — the honest edge that keeps the floor from becoming an idol.
  same_form  the SAME mathematics under different boundary conditions — and this one is only
             admitted with COMPUTED RECEIPTS on both sides, from the verifier fleet. That is the
             rule that separates a concordance from numerology: the octave's 2:1 and the orbital
             resonance's 3:2 are the same integer-ratio lattice, and both sides are sealed.

Every edge carries its `evidence` line. An edge without one is a claim wearing a relation's
clothes, and this tool will not write it.

Idempotent, atomic, and it never touches a card it did not come to edit.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass


def _key(text: str) -> str:
    """A title reduced to its identifying words — the join key.

    THE FIRST RUN REFUSED ALL 27 EDGES because it addressed cards by a slug I had guessed
    ("godel_s_..." where the shelf says "g_del_s_...", "bayes_theorem" where the id is truncated
    differently). The refusal was correct and the addressing was wrong: an id is an internal
    accident, a TITLE is the thing the theory is actually called. Matching on the title's
    significant words survives transliteration, truncation, and punctuation — and when it cannot
    find one end, the tool still refuses rather than inventing."""
    t = (text or "").lower()
    t = t.replace("&", " and ").replace("–", "-").replace("—", "-")
    words = re.findall(r"[a-z0-9]+", t)
    drop = {"the", "of", "a", "an", "and", "or", "in", "to", "s"}
    return " ".join(w for w in words if w not in drop)


# ── THE EDGE SET ──────────────────────────────────────────────────────────────────────────────
# (from, relation, to, evidence). Written as TITLES — what the theory is actually called —
# resolved against the shelf; an edge whose either end is missing is REFUSED and named, never
# invented. A dangling edge is worse than no edge.
EDGES = [
    # — mathematics is the floor under the sciences —
    ("Bayes' theorem", "rests_on", "Kolmogorov probability axioms",
     "Bayes' theorem is derived from the axioms of probability: P(A|B) = P(A∩B)/P(B) is the "
     "conditional defined on a Kolmogorov measure space"),
    ("Central limit theorem", "rests_on", "Kolmogorov probability axioms",
     "the CLT is a statement about distributions of sums, defined on a probability measure"),
    ("Null-hypothesis significance testing", "rests_on", "Central limit theorem",
     "the sampling distributions that make p-values computable are CLT results"),
    ("Gödel's incompleteness theorems", "limits", "Peano arithmetic axioms",
     "Gödel's first theorem is proved FOR any consistent formal system that includes Peano "
     "arithmetic: it exhibits a true sentence that system cannot prove"),
    ("Gödel's incompleteness theorems", "limits", "Zermelo–Fraenkel set theory (ZFC)",
     "ZFC, being strong enough to encode arithmetic, falls under the incompleteness result — "
     "no consistent axiomatization proves its own consistency"),
    ("Gödel's incompleteness theorems", "limits", "Church–Turing thesis / computability",
     "incompleteness and undecidability are the same boundary from two sides: the halting "
     "problem is the computational face of the unprovable sentence"),
    ("Fundamental theorem of arithmetic", "rests_on",
     "Peano arithmetic axioms",
     "unique factorization is a theorem ABOUT the natural numbers Peano's axioms define"),
    ("Cryptographic security", "rests_on",
     "Fundamental theorem of arithmetic",
     "RSA's hardness is the difficulty of recovering the unique prime factorization of a large "
     "semiprime — the theorem guarantees the factorization exists and is unique"),
    ("Graph theory", "rests_on", "Combinatorial enumeration",
     "path and subgraph counting are enumeration on a constrained structure"),

    # — physics: what rests on conservation, and what limits the classical picture —
    ("Ideal gas law", "rests_on", "Kinetic theory of gases",
     "PV = nRT is derived by averaging molecular momentum transfer over a container wall — the "
     "gas law is the macroscopic shadow of the kinetic account"),
    ("Kinetic theory of gases", "rests_on", "Conservation of linear & angular momentum",
     "the derivation is momentum bookkeeping over elastic collisions"),
    ("Conservation of energy", "rests_on",
     "Conservation of linear & angular momentum",
     "Noether's theorem: energy conservation is time-translation symmetry as momentum "
     "conservation is space-translation symmetry — one principle, two coordinates"),
    ("General relativity", "limits", "Heliocentrism & Kepler's laws",
     "Kepler's ellipses are the weak-field limit; GR corrects them measurably — Mercury's "
     "perihelion advances 43 arcseconds per century beyond the Newtonian prediction"),
    ("Heisenberg uncertainty principle", "limits", "Bohr / quantum model of the atom",
     "the uncertainty relation forbids the definite electron ORBIT the Bohr model draws; the "
     "orbital is a probability amplitude, not a path"),
    ("Bohr / quantum model of the atom", "rests_on", "Acoustic wave theory",
     "the quantization condition is a standing-wave condition: an integer number of de Broglie "
     "wavelengths around the orbit, the same integer-mode rule that fixes a string's harmonics"),

    # — chemistry stands on atoms and energy —
    ("Chemical bonding", "rests_on",
     "Bohr / quantum model of the atom",
     "bonding is described in terms of atomic orbitals and their overlap — the quantum atom is "
     "the object the bond is made of"),
    ("Dalton's atomic theory", "limits", "Chemical bonding",
     "Dalton's indivisible atom cannot express bonding, isotopes, or spectra; the quantum "
     "account supersedes it while keeping its conserved-mass arithmetic"),
    ("Hess's law", "rests_on", "Conservation of energy",
     "Hess's law is the first law applied to reaction paths: enthalpy change is path-independent "
     "because energy is conserved"),
    ("Brønsted–Lowry acid–base theory", "rests_on",
     "Chemical kinetics",
     "pH is an equilibrium statement — the position of the water autoionization equilibrium"),

    # — life rests on chemistry, and inheritance on life —
    ("Central dogma of molecular biology", "rests_on", "Cell theory",
     "transcription and translation are described as processes WITHIN the cell — the cell is the "
     "compartment the dogma is stated about"),
    ("Central dogma of molecular biology", "rests_on",
     "Chemical bonding",
     "base pairing is hydrogen bonding with a specific geometry; the code is chemistry"),
    ("Hardy-Weinberg equilibrium", "rests_on",
     "Combinatorial enumeration",
     "p² + 2pq + q² is the binomial expansion of allele draws — the genotype frequencies ARE a "
     "combinatorial identity"),
    ("Hardy-Weinberg equilibrium", "rests_on", "Darwinian evolution by natural selection",
     "the equilibrium is defined as the NULL case — what allele frequencies do when selection, "
     "drift, mutation and migration are absent; it is selection's own control condition"),
    ("Germ theory of disease", "rests_on", "Cell theory",
     "the pathogen is a cell (or an agent acting on cells); germ theory is cell theory applied "
     "to sickness"),

    # — the SAME FORM, both sides computed (the resonance deck's sealed edges) —
    ("Acoustic wave theory", "same_form", "Celestial mechanics",
     "small-integer ratio resonance: the octave is exactly 2:1 (440→880 Hz, sealed) and orbital "
     "resonances lock at the same simple ratios — one integer-mode lattice, two boundary "
     "conditions"),
    ("Euclidean geometry & the parallel postulate", "same_form", "Cell theory",
     "the honeycomb theorem (Hales 1999): the hexagonal grid minimizes total perimeter per area, "
     "and the interior angle is exactly 120° so three close a full turn (720/6 = 120, 360/120 = "
     "3, both sealed) — the bee's comb is the proven optimum, geometry realized in tissue"),
]


# -- THE REST OF THE FLOOR (2026-08-02) --------------------------------------------------------
# Matt: "Look in every science domain, Cryptography, engineering. They all are aligned." -- then:
# "Connect them as well as the 66 islands."
#
# The alignment is not a mood; it is structural, and it shows up as three recurring facts:
#   * ENGINEERING IS APPLIED CONSERVATION. Statics is Newton's laws with the accelerations set to
#     zero; a tolerance stack-up is the central limit theorem in a machinist's units.
#   * CRYPTOGRAPHY IS NUMBER THEORY MADE ADVERSARIAL -- unique factorization, plus Shannon's
#     account of what a secret costs to keep.
#   * ENTROPY IS ONE QUANTITY WEARING TWO COATS. Clausius's and Shannon's differ by the base of
#     the logarithm; Boltzmann's S = k log W is Shannon's H with k in front. Not a metaphor --
#     Landauer's principle makes it physical.
# Every edge below is a relation a practitioner of the field would recognize on sight.
EDGES += [
    # -- mathematics: the ground under everything --
    ("Pythagorean theorem", "rests_on", "Euclidean geometry & the parallel postulate",
     "the theorem is proved from the Euclidean axioms; it FAILS on a sphere, which is how the "
     "parallel postulate shows itself"),
    ("Non-Euclidean (hyperbolic / elliptic) geometry", "limits",
     "Euclidean geometry & the parallel postulate",
     "consistent geometries denying the parallel postulate prove it INDEPENDENT of the others -- "
     "Euclid's fifth is a choice, not a necessity"),
    ("Linear algebra (vector spaces, eigenvalues)", "rests_on", "Fundamental theorem of algebra",
     "eigenvalues are roots of the characteristic polynomial; every square complex matrix has one "
     "precisely because every non-constant polynomial has a root"),
    ("Maxwell's equations / classical electromagnetism", "rests_on",
     "Fundamental theorem of calculus",
     "the divergence and curl theorems are the fundamental theorem in higher dimensions -- "
     "Maxwell's integral and differential forms are that identity applied to fields"),
    ("Boolean algebra / propositional logic", "same_form",
     "Formal logic & epistemology (validity, inference)",
     "Boole's algebra IS propositional inference in arithmetic dress: AND/OR/NOT over {0,1} "
     "reproduce conjunction, disjunction and negation, and validity becomes tautology"),
    ("Church-Turing thesis / computability", "rests_on", "Boolean algebra / propositional logic",
     "every computation is realizable as a circuit of boolean gates; the thesis is stated over "
     "models built from them"),
    ("Law of large numbers", "rests_on", "Kolmogorov probability axioms",
     "convergence of sample means is a theorem about a probability measure"),
    ("Queueing theory (Little's law)", "rests_on", "Kolmogorov probability axioms",
     "L = lambda*W is derived over arrival and service processes on a probability space"),
    ("Linear programming & duality", "rests_on", "Linear algebra (vector spaces, eigenvalues)",
     "the simplex method walks vertices of a polytope defined by a linear system; duality is a "
     "statement about that system's transpose"),
    ("Game theory (Nash equilibrium)", "same_form", "Linear programming & duality",
     "von Neumann's minimax theorem for zero-sum games and LP strong duality are equivalent -- "
     "each is provable from the other"),
    ("Public choice / decision theory", "rests_on", "Game theory (Nash equilibrium)",
     "voting rules and institutional design are analyzed as games with strategic voters"),
    ("Sabermetrics / sports analytics (Pythagorean expectation, Elo)", "rests_on",
     "Kolmogorov probability axioms",
     "Elo is a logistic probability model and Pythagorean expectation an estimator -- both are "
     "statements about probabilities of outcomes"),

    # -- physics: Newton at the base, relativity and quanta at the bounds --
    ("Conservation of linear & angular momentum", "rests_on", "Newton's three laws of motion",
     "the third law makes internal forces cancel pairwise, so an isolated system's total momentum "
     "cannot change -- conservation is the third law summed"),
    ("Newton's law of universal gravitation", "rests_on", "Newton's three laws of motion",
     "the inverse-square force is stated as a force law acting within the three laws' framework"),
    ("Heliocentrism & Kepler's laws", "rests_on", "Newton's law of universal gravitation",
     "all three of Kepler's laws are derivable from the inverse-square attraction -- ellipses, "
     "equal areas, and the period-radius relation fall out of one force law"),
    ("Special relativity", "limits", "Newton's three laws of motion",
     "Newtonian mechanics is the v << c limit; at high speed momentum and time dilate measurably "
     "(muon lifetimes, particle accelerators)"),
    ("Special relativity", "rests_on", "Maxwell's equations / classical electromagnetism",
     "the constancy of c is Maxwell's own result; special relativity is what remains when that "
     "constancy is taken seriously for every observer"),
    ("General relativity", "rests_on", "Special relativity",
     "GR generalizes special relativity to accelerated frames and curved spacetime; SR is its "
     "flat-space, local limit"),
    ("General relativity", "limits", "Newton's law of universal gravitation",
     "gravitation as curvature corrects the inverse-square law where fields are strong -- "
     "Mercury's perihelion, light deflection and GPS clock rates all measure the difference"),
    ("Quantum mechanics (Schrodinger equation)", "limits", "Bohr / quantum model of the atom",
     "the Schrodinger solution replaces Bohr's postulated orbits with orbitals, and gets the "
     "hydrogen spectrum right where Bohr's model fails for every larger atom"),
    ("Heisenberg uncertainty principle", "rests_on", "Quantum mechanics (Schrodinger equation)",
     "the uncertainty relation is a theorem about non-commuting operators in the quantum "
     "formalism, not an additional postulate"),
    ("Pauli exclusion principle", "rests_on", "Quantum mechanics (Schrodinger equation)",
     "exclusion is antisymmetry of the many-fermion wavefunction -- a property of the quantum "
     "state, stated in that formalism"),
    ("Periodic law (Mendeleev)", "rests_on", "Pauli exclusion principle",
     "the period lengths 2, 8, 8, 18 ARE the shell capacities exclusion forces; Mendeleev's "
     "empirical table is explained by which orbitals may be occupied"),
    ("Standard Model / quantum field theory", "rests_on",
     "Quantum mechanics (Schrodinger equation)",
     "QFT is quantum mechanics made relativistic and many-bodied; the Standard Model is a "
     "specific field content within it"),
    ("Nuclear decay & binding energy", "rests_on", "Special relativity",
     "binding energy IS the mass defect: E = mc^2 converts the missing mass of a bound nucleus "
     "into the energy that binds it"),
    ("Stellar nucleosynthesis & the HR diagram", "rests_on", "Nuclear decay & binding energy",
     "which fusion chains run, and what a star can become, is set by the binding-energy curve -- "
     "iron's peak is why fusion stops there"),
    ("Big Bang cosmology & expansion (Hubble's law)", "rests_on", "General relativity",
     "the expanding metric is a solution of the Einstein field equations; Hubble's law is that "
     "solution read off redshifts"),
    ("Wave optics (Huygens, Snell's law, diffraction)", "rests_on",
     "Maxwell's equations / classical electromagnetism",
     "light is an electromagnetic wave; refraction, diffraction and polarization are Maxwell's "
     "equations at a boundary"),
    ("Acoustic wave theory (harmonics, Doppler)", "same_form",
     "Wave optics (Huygens, Snell's law, diffraction)",
     "both are the wave equation in different media: Huygens' construction, Snell's law, "
     "interference and the Doppler shift hold for sound and light alike"),
    ("Ohm's law & circuit theory (Kirchhoff)", "rests_on",
     "Maxwell's equations / classical electromagnetism",
     "Kirchhoff's current and voltage laws are charge conservation and the curl-free "
     "electrostatic field -- the lumped-element limit of Maxwell"),
    ("Physical oceanography (hydrostatics, tides)", "rests_on",
     "Newton's law of universal gravitation",
     "tides are the differential gravitational pull of moon and sun across the earth's diameter"),

    # -- thermodynamics and its information twin --
    ("Second law of thermodynamics (entropy)", "rests_on", "Kinetic theory of gases",
     "Boltzmann derived entropy statistically from molecular microstates: S = k log W makes the "
     "second law a counting argument about overwhelming likelihood"),
    ("Third law of thermodynamics", "rests_on", "Second law of thermodynamics (entropy)",
     "the third law fixes the entropy scale the second law defines only up to a constant"),
    ("Phase theory (phase diagrams, Clausius-Clapeyron)", "rests_on",
     "Second law of thermodynamics (entropy)",
     "the Clausius-Clapeyron relation is derived from equality of chemical potentials, itself a "
     "second-law equilibrium condition"),
    ("Shannon information theory (entropy, channel capacity)", "same_form",
     "Second law of thermodynamics (entropy)",
     "Shannon's H = -sum p log p and Boltzmann's S = k log W are the same functional, differing "
     "by the base of the logarithm and the constant k. Landauer's principle makes the identity "
     "physical: erasing one bit dissipates at least kT ln 2 of heat"),
    ("Shannon information theory (entropy, channel capacity)", "rests_on",
     "Kolmogorov probability axioms",
     "entropy and channel capacity are defined over probability distributions on a message set"),
    ("Atmospheric thermodynamics (dew point, lapse rate)", "rests_on", "Ideal gas law (PV = nRT)",
     "the dry adiabatic lapse rate is derived from the gas law plus hydrostatic balance"),
    ("Bioenergetics / energy balance (calorimetry, 4-9-4)", "rests_on",
     "Conservation of energy (1st law of thermodynamics)",
     "calorimetry is the first law applied to a body: intake minus expenditure is storage"),
    ("Exercise physiology (VO2max, HR zones)", "rests_on",
     "Bioenergetics / energy balance (calorimetry, 4-9-4)",
     "VO2max measures the ceiling of aerobic energy conversion -- bioenergetics under load"),

    # -- chemistry completed --
    ("Stoichiometry & the mole concept", "rests_on", "Law of conservation of mass (Lavoisier)",
     "balancing an equation IS asserting mass conservation atom by atom"),
    ("Stoichiometry & the mole concept", "rests_on", "Dalton's atomic theory",
     "the mole counts discrete atoms in fixed proportions -- Dalton's law of definite proportions "
     "is what makes the arithmetic possible"),
    ("VSEPR theory (molecular geometry)", "rests_on",
     "Chemical bonding (valence-bond / molecular-orbital)",
     "VSEPR predicts shape from electron-pair repulsion among the bonds and lone pairs the "
     "bonding account supplies"),

    # -- life, medicine, ecology --
    ("Mendelian inheritance", "rests_on", "Cell theory",
     "the segregation Mendel inferred is chromosome behaviour in meiosis -- a cellular process"),
    ("Hardy-Weinberg equilibrium", "rests_on", "Mendelian inheritance",
     "the equilibrium is the population-level consequence of Mendelian segregation"),
    ("Homeostasis & physiological regulation", "rests_on", "Cell theory",
     "regulation is stated over cellular and organ set points; the cell is the regulated unit"),
    ("Pharmacokinetics (dosing, clearance, half-life)", "same_form",
     "Chemical kinetics & equilibrium (Arrhenius, Le Chatelier)",
     "first-order clearance and chemical first-order decay are the same differential equation; "
     "half-life is t-half = ln2/k in both"),
    ("Population ecology (Lotka-Volterra, carrying capacity)", "same_form",
     "Chemical kinetics & equilibrium (Arrhenius, Le Chatelier)",
     "Lotka-Volterra is mass-action kinetics with organisms as reactants -- Lotka wrote it as "
     "chemical kinetics first and then applied it to populations"),

    # -- earth --
    ("Seismology & earthquake magnitude (Richter / moment)", "rests_on", "Plate tectonics",
     "earthquakes are stress released at plate boundaries; magnitude measures that release"),
    ("Radiometric dating & uniformitarianism", "rests_on", "Nuclear decay & binding energy",
     "a date is read off an exponential decay with a measured half-life"),
    ("Plate tectonics", "rests_on", "Conservation of energy (1st law of thermodynamics)",
     "mantle convection is a heat engine: the interior's thermal energy drives the motion"),
    ("Hydrologic cycle & open-channel flow (Manning, Darcy)", "rests_on",
     "Atmospheric thermodynamics (dew point, lapse rate)",
     "evaporation, saturation and precipitation are phase changes governed by the atmospheric "
     "thermodynamic state"),
    ("Nutrient cycling & agronomy (NPK, evapotranspiration)", "rests_on",
     "Hydrologic cycle & open-channel flow (Manning, Darcy)",
     "evapotranspiration and leaching are the water cycle moving nutrients through soil"),
    ("Agricultural science (yield, soil-pH suitability)", "rests_on",
     "Nutrient cycling & agronomy (NPK, evapotranspiration)",
     "yield models are stated over nutrient availability and pH, which the soil cycle sets"),

    # -- ENGINEERING: applied conservation, and statistics in a machinist's units --
    ("Structural statics (load, moment, floor-area ratio)", "rests_on",
     "Newton's three laws of motion",
     "statics IS Newton's second law with acceleration zero: sum F = 0 and sum M = 0 are the "
     "equilibrium conditions a standing structure must satisfy"),
    ("Elasticity (Hooke's law, stress-strain)", "same_form",
     "Acoustic wave theory (harmonics, Doppler)",
     "Hooke's linear restoring force gives the harmonic oscillator, and a continuum of coupled "
     "oscillators gives the wave equation -- the speed of sound in a solid is sqrt(E/rho), "
     "elasticity over density"),
    ("Structural statics (load, moment, floor-area ratio)", "rests_on",
     "Elasticity (Hooke's law, stress-strain)",
     "member sizing needs stress-strain response; statics gives the forces, elasticity says "
     "whether the material survives them"),
    ("Reliability & tolerance stack-up (RSS)", "same_form", "Central limit theorem",
     "root-sum-square stacking IS the CLT in the shop: independent variances add, so an "
     "assembly's tolerance is sqrt(sum of squares) and its error distribution tends to normal"),

    # -- CRYPTOGRAPHY and the networks it protects --
    ("Cryptographic security (hashing, checksums, PKI)", "rests_on",
     "Shannon information theory (entropy, channel capacity)",
     "key strength is measured in bits of entropy, and Shannon's perfect-secrecy theorem sets "
     "what a cipher can and cannot promise"),
    ("Network theory (routing, addressing / CIDR)", "rests_on",
     "Graph theory (Euler, connectivity)",
     "routing is shortest-path and connectivity on a graph of nodes and links"),
    ("Network theory (routing, addressing / CIDR)", "rests_on",
     "Shannon information theory (entropy, channel capacity)",
     "channel capacity bounds what any link can carry, whatever the protocol"),

    # -- money, law, and the invariants they keep --
    ("Double-entry accounting identity (A = L + E)", "same_form",
     "Law of conservation of mass (Lavoisier)",
     "both are closed-system conservation checked by balancing two columns: nothing is created or "
     "destroyed, only transferred, and a failure to balance PROVES an error was made"),
    ("Time value of money & discounting", "same_form", "Nuclear decay & binding energy",
     "discounting is exponential decay: a present value falls as e^(-rt) exactly as an isotope's "
     "population does, and 'half-life' and 'halving time of value' are one computation"),
    ("Modern portfolio theory (Markowitz)", "rests_on", "Kolmogorov probability axioms",
     "risk is variance and diversification is covariance arithmetic -- statements about a "
     "probability distribution of returns"),
    ("Real-estate valuation (cap rate, DCF)", "rests_on", "Time value of money & discounting",
     "a DCF valuation is discounting applied to a property's cash flows"),
    ("Supply & demand / market equilibrium", "same_form",
     "Chemical kinetics & equilibrium (Arrhenius, Le Chatelier)",
     "Le Chatelier's principle and market response are one form: perturb a system at equilibrium "
     "and it shifts to oppose the change -- Samuelson took the analogy from chemistry deliberately"),
    ("Comparative advantage", "rests_on", "Linear programming & duality",
     "the gains-from-trade argument is an optimization over opportunity costs; its shadow prices "
     "are LP duals"),
    ("Labor economics (minimum wage, overtime law)", "rests_on",
     "Supply & demand / market equilibrium",
     "wage floors and overtime rules are analyzed as interventions in a labour market"),
    ("Contract theory & rule of law", "rests_on", "Game theory (Nash equilibrium)",
     "enforceable contracts are commitment devices that change a game's equilibria -- the law's "
     "function here is to make promises credible"),

    # -- language, reasoning, and the making of images --
    ("Structural & generative linguistics (Saussure, Chomsky)", "same_form",
     "Church-Turing thesis / computability",
     "the Chomsky hierarchy IS a computability hierarchy: regular, context-free, "
     "context-sensitive and recursively enumerable grammars correspond exactly to finite "
     "automata, pushdown automata, linear-bounded automata and Turing machines"),
    ("Aristotelian rhetoric & fallacy taxonomy", "rests_on",
     "Formal logic & epistemology (validity, inference)",
     "a fallacy is named by the inference rule it violates; the taxonomy presupposes validity"),
    ("Normative ethics (consequentialism / deontology / virtue)", "rests_on",
     "Formal logic & epistemology (validity, inference)",
     "each normative theory is argued as an inference from premises about the good; the "
     "disagreement is over premises, and the arguing is logic"),
    ("Music theory (harmonic series, equal temperament)", "rests_on",
     "Acoustic wave theory (harmonics, Doppler)",
     "the harmonic series is the standing-wave mode set of a string or air column; equal "
     "temperament is the compromise the 12th root of 2 makes with those integer ratios"),
    ("Photographic exposure theory (exposure value, reciprocity)", "rests_on",
     "Wave optics (Huygens, Snell's law, diffraction)",
     "aperture, focal length and the diffraction limit are wave optics; exposure value is a "
     "log-base-2 accounting of the light those optics deliver"),

    # -- time itself --
    ("Calendar theory (Gregorian reform, leap rules)", "rests_on",
     "Celestial mechanics / ephemeris prediction",
     "the leap rules approximate the tropical year, a quantity celestial mechanics measures"),
    ("Historical chronology (era reckoning, elapsed years)", "rests_on",
     "Calendar theory (Gregorian reform, leap rules)",
     "converting between eras requires the calendar's own leap structure"),
]


# -- THE LAST THREE BRIDGES (2026-08-02) -------------------------------------------------------
# After 101 edges the floor still stood in three pieces: 86 theories in one body, an
# optimization/law cluster of 7 around game theory and LP duality, and a rate-equation cluster of
# 6 around chemical kinetics. Matt: "Link them all." These are the three joins that close it --
# and none is a stitch of convenience; each is the relation a practitioner would give first.
EDGES += [
    ("Quantum mechanics (Schrodinger equation)", "rests_on",
     "Linear algebra (vector spaces, eigenvalues)",
     "quantum mechanics IS linear algebra on Hilbert space: states are vectors, observables are "
     "Hermitian operators, and the values a measurement can return are that operator's "
     "eigenvalues -- the spectrum of an atom is an eigenvalue problem"),
    ("Game theory (Nash equilibrium)", "rests_on", "Kolmogorov probability axioms",
     "a mixed strategy IS a probability distribution over actions, and Nash's existence proof is "
     "a fixed-point argument over the simplex of those distributions"),
    ("Chemical kinetics & equilibrium (Arrhenius, Le Chatelier)", "rests_on",
     "Kinetic theory of gases",
     "the Arrhenius factor exp(-Ea/RT) IS the Boltzmann fraction of molecules carrying more than "
     "the activation energy -- reaction rate is collision statistics counted"),
]


# -- FROM THE FINDER (2026-08-02) --------------------------------------------------------------
# The first edges this project did not write by hand: tools/propose_edges.py proposed them from
# co-retrieval over the keeping, and the witnesses it printed are named in the evidence below.
# 18 proposals -> 3 accepted, 6 redundant, 9 spurious word-collisions.
EDGES += [
    ("Second law of thermodynamics (entropy)", "limits",
     "Conservation of energy (1st law of thermodynamics)",
     "energy conservation permits a process in EITHER direction -- it would allow heat to flow "
     "from cold to hot -- and the second law says which way it actually runs. The first law "
     "cannot answer 'will this reaction go?'; free energy, which is the second law's bookkeeping, "
     "can. Proposed by the finder; witness: 'Gibbs free energy -- will a reaction go?'"),
    ("Newton's law of universal gravitation", "rests_on", "Fundamental theorem of calculus",
     "Newton built the calculus in order to state this law and derive its consequences: an orbit "
     "is obtained by integrating the inverse-square force, and Kepler's equal-area rule is a "
     "statement about the integral of angular momentum. Proposed by the finder; witness: the "
     "keeping's own 'Isaac Newton' card, which both retrievals pulled"),
    ("Maxwell's equations / classical electromagnetism", "same_form",
     "Newton's law of universal gravitation",
     "Coulomb's law and universal gravitation are the SAME inverse-square field: both fall off as "
     "1/r^2 from a point source, so the same mathematics solves both -- Gauss's flux law, the "
     "shell theorem (a uniform sphere attracts as though its mass were at the centre), and the "
     "1/r potential. The sign differs, and the constant, and nothing else. Proposed by the finder"),
]


# -- BATCH 3: THE MISSING FRAMEWORKS AND THE GAME-THEORY / QUANTUM BRIDGE (2026-08-02) ---------
# Matt: "Game theory and Quantum physics... game theory has been a big component from the
# beginning." Measured: 16 of 16 probed frameworks absent -- including NOETHER, whose theorem the
# floor already cited as evidence while holding no card for it. A floor that names a beam it does
# not contain is lying about itself.
EDGES += [
    # -- the bridge, and it is mathematical rather than biographical --
    ("Game theory (Nash equilibrium)", "rests_on", "Fixed-point theorems (Brouwer, Kakutani)",
     "Nash's existence proof IS a fixed-point argument (Kakutani), and von Neumann's minimax rests "
     "on Brouwer: an equilibrium exists because a continuous map of a convex compact set into "
     "itself must fix a point. The economics is topology wearing a payoff matrix"),
    ("Quantum mechanics (Schrodinger equation)", "same_form", "Game theory (Nash equilibrium)",
     "a MIXED STRATEGY and a QUANTUM MIXED STATE are the same object: a probability distribution "
     "over pure alternatives, non-negative and summing to one, living on a simplex. Density "
     "matrices and mixed strategies share the convex geometry, and both existence theorems are "
     "fixed-point arguments over it. Von Neumann proved the minimax theorem in 1928, wrote the "
     "Mathematical Foundations of Quantum Mechanics in 1932, and Theory of Games in 1944 -- one "
     "mathematics, applied twice"),
    ("Quantum information & entanglement (von Neumann entropy)", "rests_on",
     "Quantum mechanics (Schrodinger equation)",
     "the density matrix, entanglement and decoherence are all statements in the quantum "
     "formalism"),
    ("Quantum information & entanglement (von Neumann entropy)", "same_form",
     "Shannon information theory (entropy, channel capacity)",
     "von Neumann entropy S = -Tr(rho log rho) reduces EXACTLY to Shannon's H = -sum p log p in "
     "the density matrix's eigenbasis -- the same functional, one door further in. Quantum "
     "channel capacity generalizes Shannon's, and reduces to it for classical channels"),
    ("Quantum information & entanglement (von Neumann entropy)", "limits",
     "Cryptographic security (hashing, checksums, PKI)",
     "Shor's algorithm factors in polynomial time on a quantum computer, so RSA's hardness -- "
     "unique factorization being hard to reverse -- is a claim about CLASSICAL computers only. "
     "The honest card says which assumption the security rests on"),

    # -- game theory outward: into biology, into institutions --
    ("Evolutionary game theory (evolutionarily stable strategies)", "rests_on",
     "Game theory (Nash equilibrium)",
     "an ESS is a Nash equilibrium with a stability condition added: no rare mutant strategy can "
     "invade a population playing it"),
    ("Evolutionary game theory (evolutionarily stable strategies)", "rests_on",
     "Darwinian evolution by natural selection",
     "reproduction does the choosing -- payoffs are fitness, and the equilibrium is reached by "
     "differential survival rather than by reasoning"),
    ("Mechanism design & auction theory", "rests_on", "Game theory (Nash equilibrium)",
     "mechanism design is game theory run backwards: fix the outcome you want, then design rules "
     "whose equilibrium produces it"),
    ("Contract theory & rule of law", "rests_on", "Mechanism design & auction theory",
     "a contract is a mechanism: it changes the payoffs so that keeping the promise is the "
     "equilibrium play"),

    # -- Noether, the beam the floor was already leaning on --
    ("Conservation of energy (1st law of thermodynamics)", "rests_on",
     "Noether's theorem (symmetry and conservation)",
     "energy conservation is time-translation symmetry; the theorem is the reason the conservation "
     "laws are not a coincidence but a consequence of the action's symmetries"),
    ("Conservation of linear & angular momentum", "rests_on",
     "Noether's theorem (symmetry and conservation)",
     "space-translation symmetry gives linear momentum, rotational symmetry gives angular "
     "momentum -- the same theorem, two symmetries"),
    ("Noether's theorem (symmetry and conservation)", "rests_on",
     "Standard Model / quantum field theory",
     "gauge symmetries generate the conserved charges of the Standard Model: electric charge, "
     "colour, weak isospin -- Noether's argument is how the field content is organized"),

    # -- the mathematical floor under probability, learning and control --
    ("Kolmogorov probability axioms", "rests_on", "Measure theory (Lebesgue integration)",
     "a probability IS a measure of total mass one; Kolmogorov's axioms are the measure axioms "
     "with that normalization"),
    ("Statistical learning theory (bias-variance, generalization)", "rests_on",
     "Kolmogorov probability axioms",
     "generalization bounds are probability statements about unseen samples"),
    ("Statistical learning theory (bias-variance, generalization)", "rests_on",
     "Linear programming & duality",
     "fitting is optimization under constraint; the dual view (support vectors, regularization "
     "paths) is the same duality"),
    ("Control theory & cybernetics (feedback, stability)", "rests_on",
     "Linear algebra (vector spaces, eigenvalues)",
     "stability of a linear system is decided by where the eigenvalues of its state matrix sit -- "
     "the loop is stable exactly when they lie in the left half-plane"),
    ("Homeostasis & physiological regulation", "same_form",
     "Control theory & cybernetics (feedback, stability)",
     "a physiological set point with negative feedback IS a control loop: thermoregulation, "
     "glucose regulation and baroreflex are described with the same block diagram an engineer "
     "draws for a governor"),
    ("Dynamical systems & deterministic chaos", "rests_on", "Newton's three laws of motion",
     "the systems whose sensitivity to initial conditions defines chaos are Newtonian ones -- "
     "the three-body problem is the original case"),
    ("Dynamical systems & deterministic chaos", "limits",
     "Celestial mechanics / ephemeris prediction",
     "deterministic does not mean predictable: the solar system is chaotic on ~5 million-year "
     "timescales, so ephemeris accuracy has a horizon no computing power removes"),
    ("Computational complexity (P, NP, reductions)", "rests_on",
     "Church-Turing thesis / computability",
     "complexity classes are defined over the machine model the thesis identifies; computability "
     "asks whether, complexity asks how expensively"),
    ("Computational complexity (P, NP, reductions)", "limits",
     "Cryptographic security (hashing, checksums, PKI)",
     "every public-key scheme rests on a problem BELIEVED hard; P vs NP is open, so the security "
     "is conditional and the honest card says which conjecture it is standing on"),
    ("Fourier analysis & signal processing", "same_form",
     "Acoustic wave theory (harmonics, Doppler)",
     "the harmonic series IS the Fourier decomposition of a standing wave; the transform is the "
     "general statement of what a vibrating string does"),
    ("Fourier analysis & signal processing", "rests_on", "Fundamental theorem of calculus",
     "the transform pair is a pair of integrals, and inversion is the fundamental theorem doing "
     "its work in the frequency domain"),
    ("Heisenberg uncertainty principle", "same_form", "Fourier analysis & signal processing",
     "uncertainty is the Fourier bandwidth theorem: a signal narrow in time is broad in frequency, "
     "and position/momentum are a transform pair. The physical constant hbar sets the scale; the "
     "inequality itself is mathematics about any conjugate pair, which is why the same limit "
     "governs radar resolution and note onset in music"),
]


# -- HERMENEUTICS AND ITS NEIGHBOURS (2026-08-02) -----------------------------------------------
# Matt: "Hermeneutics" -- and the measurement was that a shelf of 110 held ZERO theories of
# interpretation, inside a project whose every working rule is a hermeneutical commitment. Not a
# field we forgot; the one we were standing on.
EDGES += [
    ("Hermeneutics (the theory of interpretation)", "rests_on",
     "Semiotics (sign, signified, interpretant)",
     "interpretation presupposes signs that mean at all; Peirce's interpretant -- the effect in a "
     "mind that takes something AS a sign -- puts interpretation inside the sign's own structure, "
     "which is where hermeneutics begins"),
    ("Hermeneutics (the theory of interpretation)", "rests_on",
     "Formal logic & epistemology (validity, inference)",
     "a reading is argued: it draws inferences from the text and from context, and the standards "
     "for a good inference are logic's"),
    ("Hermeneutics (the theory of interpretation)", "limits",
     "Structural & generative linguistics (Saussure, Chomsky)",
     "grammar does not determine meaning. The same well-formed sentence means differently in "
     "different mouths and moments -- irony, genre, and the speaker's situation decide what "
     "syntax leaves open -- so a complete account of competence still cannot deliver the sense of "
     "an utterance. This is the honest boundary between the two, and it runs in this direction"),
    ("Hermeneutics (the theory of interpretation)", "same_form", "Bayes' theorem",
     "the hermeneutical circle IS iterative conditioning: pre-understanding is a prior, the text "
     "is evidence, the revised understanding is a posterior, and you read again with it as the "
     "new prior. Gadamer's fusion of horizons and Bayesian updating are the same shape -- which "
     "is also why neither can start from nowhere: a flat prior is still a prior, and a reading "
     "with no pre-understanding is not a purer reading but an unexamined one"),
    ("Textual criticism (establishing what the text says)", "rests_on",
     "Hermeneutics (the theory of interpretation)",
     "the canons are interpretive judgements -- 'prefer the harder reading' is a claim about what "
     "a copyist would do, argued from the habits of scribes"),
    ("Hermeneutics (the theory of interpretation)", "rests_on",
     "Textual criticism (establishing what the text says)",
     "you cannot interpret what you have not first established: for any ancient work the reading "
     "itself is reconstructed from disagreeing copies, so exegesis stands on the apparatus"),
    ("Translation theory (formal vs dynamic equivalence)", "rests_on",
     "Hermeneutics (the theory of interpretation)",
     "every translation decides meanings the source left open; choosing between formal and "
     "dynamic equivalence IS choosing a hermeneutic and then writing it down"),
    ("Translation theory (formal vs dynamic equivalence)", "rests_on",
     "Semiotics (sign, signified, interpretant)",
     "if the sign-signified link is arbitrary and system-internal, no two languages carve the "
     "world identically -- which is why untranslatables exist and why equivalence is a trade "
     "rather than a lookup"),
    ("Semiotics (sign, signified, interpretant)", "rests_on",
     "Structural & generative linguistics (Saussure, Chomsky)",
     "Saussure's arbitrariness of the sign and the system-of-differences account are the "
     "structural half of semiotics"),
    ("Aristotelian rhetoric & fallacy taxonomy", "same_form",
     "Hermeneutics (the theory of interpretation)",
     "one art faces each way across the same act: rhetoric is the making of a text that will be "
     "understood as intended, hermeneutics the recovering of that intent from the text. Aristotle "
     "treats audience, occasion and genre as constraints on composition; the interpreter reads "
     "the same three backwards as evidence of what was meant"),
]

# -- BATCH 6: HOW YOU COVER A PLANE (2026-08-03) ------------------------------------------------
# Matt: "The tiling pattern found in Math and also in archeology has two types of tiles." And an
# hour before that: "Think of the corpus as a honeycomb filled with honey. The structure matters."
# Two halves of one question, and the corpus held NEITHER — a probe for penrose / aperiodic /
# quasicrystal / girih / tiling / tessellation / monotile across all 22,152 cards returned 0.
#
# This is the cross-domain case in its strongest form: the SAME structure was reached three times
# independently — by craftsmen at Isfahan in 1453, by a mathematician in 1974, and by matter itself
# in an alloy in 1982 — and each time the others were unknown.
EDGES += [
    ("Aperiodic tiling (Penrose, and the 2023 monotile)", "rests_on",
     "Euclidean geometry & the parallel postulate",
     "the tiles are Euclidean polygons and the matching rules are constraints on their edges and "
     "angles; aperiodicity is a theorem about the flat plane, and the five-fold symmetry it "
     "permits is exactly what the crystallographic restriction forbids to a periodic lattice"),

    ("Aperiodic tiling (Penrose, and the 2023 monotile)", "same_form",
     "Fourier analysis & signal processing",
     "the deep result is spectral: the Fourier transform of a Penrose tiling is a PURE POINT "
     "spectrum — genuinely sharp peaks — from a structure with no repeating unit cell. Sharp peaks "
     "had been taken to prove periodicity; they prove long-range ORDER, which is the weaker and "
     "correct claim. The tiling and its diffraction pattern are one object seen in two domains"),

    ("Quasicrystals (forbidden symmetry in real matter)", "same_form",
     "Aperiodic tiling (Penrose, and the 2023 monotile)",
     "a quasicrystal IS an aperiodic tiling realised in matter: Shechtman's 1982 electron "
     "diffraction of Al-Mn showed sharp Bragg peaks with ten-fold symmetry, which is precisely "
     "what the Fourier transform of a Penrose-like structure predicts. Mathematics described the "
     "object eight years before anyone found it in a crucible, and neither party was looking for "
     "the other"),

    ("Quasicrystals (forbidden symmetry in real matter)", "rests_on",
     "Wave optics (Huygens, Snell's law, diffraction)",
     "the entire evidence for a quasicrystal is a diffraction pattern, so the claim rests on "
     "diffraction theory: sharpness of the peaks measures the coherence length of the order, and "
     "their angular arrangement measures its symmetry. Change the optics and the finding "
     "evaporates"),

    ("Girih tiles — quasi-periodic design in medieval Islamic architecture", "same_form",
     "Aperiodic tiling (Penrose, and the 2023 monotile)",
     "Lu and Steinhardt (Science, 2007) showed the Darb-i Imam shrine at Isfahan (1453) carries a "
     "nearly perfect decagonal quasi-periodic tiling with the self-similar subdivision that "
     "generates it — the same structure Penrose described in 1974, reached by craft roughly five "
     "centuries earlier. Held at RESONANCE, not proof of possessing the theory: the tilings "
     "contain defects and the interpretation is contested"),

    ("Girih tiles — quasi-periodic design in medieval Islamic architecture", "rests_on",
     "Euclidean geometry & the parallel postulate",
     "girih are constructed polygons — decagon, pentagon, hexagon, bowtie, rhombus — set out with "
     "compass-and-straightedge methods recorded in the Topkapı Scroll"),

    ("Optimal packing & the honeycomb conjecture (Hales)", "rests_on",
     "Euclidean geometry & the parallel postulate",
     "the statement is a plane-geometry optimisation: among partitions of the plane into equal "
     "areas, the regular hexagonal grid minimises total perimeter. Conjectured by Pappus c. 300 "
     "AD, proved by Hales in 1999"),

    ("Optimal packing & the honeycomb conjecture (Hales)", "limits",
     "Aperiodic tiling (Penrose, and the 2023 monotile)",
     "the honeycomb theorem fixes the CEILING that any aperiodic tiling must pay to get away from: "
     "if minimum wall per unit area were the only objective, the answer is settled and it is the "
     "hexagon. An aperiodic tiling is therefore never the efficient choice — it buys something "
     "else, an arrangement that is itself information, since in a periodic comb every cell is "
     "interchangeable and the arrangement says nothing"),
]

# -- BATCH 7: ASTRONOMY AND SPACE (2026-08-03) --------------------------------------------------
# Matt: "Astronomy and space." Measured first: 7 cards in the section, ALL SEVEN template-only
# (207-285 chars against a ~200-char template), and 16 of 19 probed concepts absent. The thinnest
# section on the floor -- and the one where verify_astronomy and verify_ephemeris can actually
# seal, which is the worst combination we had.
#
# Four cells were DEEPENED rather than duplicated. One card was added: SPECTROSCOPY, because it is
# not a topic among topics but the instrument that made astronomy a physical science, and nearly
# every other astronomy claim here silently rests on it. Its absence was the real gap.
EDGES += [
    ("Spectroscopy (how we know what a distant thing is made of)", "rests_on",
     "Wave optics (Huygens, Snell's law, diffraction)",
     "a spectrum is made by dispersing light with a prism or grating, so the instrument IS "
     "diffraction and refraction; the resolving power of a grating sets what the astronomer can "
     "distinguish, and Fraunhofer, who mapped the solar dark lines, invented the diffraction "
     "grating to do it"),

    ("Spectroscopy (how we know what a distant thing is made of)", "rests_on",
     "Bohr / quantum model of the atom",
     "the lines are quantised: an electron falling between allowed levels emits a photon of "
     "exactly that energy difference, which is why each element's fingerprint is FIXED and "
     "identical everywhere. Bohr's model gave the first quantitative account of the hydrogen "
     "series, so the astronomical reading of a star's composition rests on atomic structure"),

    ("Spectroscopy (how we know what a distant thing is made of)", "same_form",
     "Periodic law (Mendeleev)",
     "two independent fingerprints of the same underlying fact. Mendeleev sorted elements by "
     "chemical periodicity; spectroscopy sorts them by line pattern -- and they agree, because "
     "both are consequences of electron shell structure. Helium was found in the Sun's spectrum "
     "in 1868 before it was isolated on Earth, and the periodic table had a place waiting"),

    ("Big Bang cosmology & expansion (Hubble's law)", "rests_on",
     "Spectroscopy (how we know what a distant thing is made of)",
     "Hubble's law is a spectroscopic measurement before it is a cosmological claim: redshift is "
     "the Doppler displacement of the whole line pattern, and without identifiable lines there is "
     "no velocity, no v = H0*d, and no expansion. The evidence for the largest claim in the "
     "section is a shifted fingerprint"),

    ("Stellar nucleosynthesis & the HR diagram", "rests_on",
     "Spectroscopy (how we know what a distant thing is made of)",
     "stellar composition and temperature are both read off the spectrum -- lines give what the "
     "star is made of, the continuum shape gives how hot it is by Wien's law -- and those two "
     "axes are exactly what the HR diagram plots"),

    ("Stellar nucleosynthesis & the HR diagram", "rests_on",
     "Nuclear decay & binding energy",
     "IRON IS THE HINGE, and it is a binding-energy fact rather than an astronomical one: iron-56 "
     "sits at the peak of binding energy per nucleon, so fusion pays up to iron and costs beyond "
     "it. That single curve decides which elements a star can make, and that a star with an iron "
     "core must collapse"),

    ("Heliocentrism & Kepler's laws", "rests_on",
     "Newton's law of universal gravitation",
     "Kepler DESCRIBED the three laws from Brahe's positions (1609-1619); Newton later DERIVED all "
     "three from the inverse-square law. The order is the lesson: an accurate description that "
     "cannot yet say why is still knowledge, and waiting for the explanation would have cost "
     "eighty years"),

    ("Celestial mechanics / ephemeris prediction", "rests_on",
     "Heliocentrism & Kepler's laws",
     "an ephemeris is Kepler's elements advanced in time and then perturbed; the two-body solution "
     "is the analytic backbone every numerical integration corrects from"),
]

# -- BATCH 8: THE FREQUENCY AXIS (2026-08-03) ---------------------------------------------------
# Matt, across four messages in one night: "Look at the mechanisms for Radio broadcast. Especially
# AM." ... "Astronomy and space." ... "frequency as well." ... "Light spectrum."
#
# Those are ONE question. Measured: Maxwell, wave optics, acoustics, Fourier and spectroscopy were
# all on the floor -- and the ELECTROMAGNETIC SPECTRUM itself was absent, as was modulation. Every
# layer present, the axis running through them missing. This is exactly what Matt described as
# "the exciting parts... the axes that only show when the layers are aligned."
EDGES += [
    ("The electromagnetic spectrum & modulation (radio to gamma, one axis)", "rests_on",
     "Maxwell's equations / classical electromagnetism",
     "the spectrum IS Maxwell's wave solution indexed by frequency: the equations give a "
     "self-propagating field travelling at c = 1/sqrt(mu0*eps0), and c = f*lambda then sorts radio "
     "through gamma onto one axis. Maxwell's identification of light as an electromagnetic wave is "
     "what makes them one phenomenon rather than seven"),

    ("Spectroscopy (how we know what a distant thing is made of)", "rests_on",
     "The electromagnetic spectrum & modulation (radio to gamma, one axis)",
     "a spectrum is a measurement ALONG this axis: dispersing light sorts photons by frequency, "
     "and an absorption line is a frequency at which the sample removed energy. Without the axis "
     "there is no coordinate for the line to sit on"),

    ("Wave optics (Huygens, Snell's law, diffraction)", "rests_on",
     "The electromagnetic spectrum & modulation (radio to gamma, one axis)",
     "optics is the roughly one octave of the spectrum the eye happens to detect; refraction, "
     "diffraction and interference are frequency-dependent behaviours of the same wave, which is "
     "why a radio dish and a telescope mirror are governed by the same diffraction limit"),

    ("The electromagnetic spectrum & modulation (radio to gamma, one axis)", "same_form",
     "Fourier analysis & signal processing",
     "modulation and Fourier are one statement. Multiplying a carrier by a message shifts the "
     "message's spectrum up to the carrier, producing sidebands at f_c +/- f_m -- so an AM "
     "signal's bandwidth is twice the highest message frequency, which is the transform theorem "
     "and not a rule of thumb. The same algebra sets the Doppler broadening of a spectral line: "
     "AM sidebands and a broadened absorption line are the same mathematics"),

    # -- BATCH 9: WHERE PHYSICS ENDS (2026-08-03) ----------------------------------------------
    # Matt: "Quantum and Space time." The card was minted and its edges were NOT declared, so
    # tests/test_floor_connected.py::test_the_floor_is_one_body failed gate 82 with exactly one
    # island: the quantum-gravity card itself. The ratchet did its job -- a theory nobody can walk
    # to is not on the floor, it is beside it. These are the edges that were missing.
    ("Spacetime & the quantum-gravity problem (where physics ends)", "limits",
     "General relativity",
     "general relativity predicts its own breakdown: the field equations output SINGULARITIES -- "
     "infinite curvature at the centre of a black hole and at the start of the expansion -- and "
     "Penrose and Hawking proved these are generic rather than artefacts of assumed symmetry. A "
     "theory that returns infinities is naming the boundary of its own validity"),

    ("Spacetime & the quantum-gravity problem (where physics ends)", "limits",
     "Quantum mechanics (Schrödinger equation)",
     "quantum theory assumes a FIXED background spacetime for its fields to live on, which fails "
     "exactly where gravity is strong enough to make geometry dynamical. Quantising gravity by the "
     "method that worked for the other forces gives a NON-RENORMALIZABLE theory: the infinities "
     "cannot be absorbed into finitely many measured constants"),

    ("Spacetime & the quantum-gravity problem (where physics ends)", "rests_on",
     "Special relativity",
     "spacetime as a single four-dimensional structure with an invariant interval is Minkowski's "
     "1908 reading of special relativity, and it is the object both candidate theories are trying "
     "to quantise. Without the interval there is no 'spacetime' to be the subject"),

    ("General relativity", "rests_on", "Special relativity",
     "general relativity reduces to special relativity locally: the equivalence principle says a "
     "freely falling frame is indistinguishable from an inertial one, so special relativity holds "
     "in every sufficiently small patch and the general theory is what happens when those patches "
     "cannot be combined into one flat frame"),

    # -- BATCH 10: THE PRACTICAL FLOOR (2026-08-03) --------------------------------------------
    # Matt: "Agriculture and any other space that is practical for use should be included as
    # well." Measured: 40 of 75 major figures absent, and the cluster that matters most to someone
    # with no other option was entirely missing -- Liebig, Haber, Bosch, Borlaug, Jenner,
    # Semmelweis, Lister, Fleming, Snow. How food is grown and how disease is stopped.
    ("Haber–Bosch nitrogen fixation (bread from air)", "rests_on",
     "Chemical kinetics & equilibrium (Arrhenius, Le Chatelier)",
     "the whole design is a fight with an equilibrium: the reaction is exothermic, so heat speeds "
     "the kinetics and shifts the equilibrium BACKWARD by Le Chatelier. Haber-Bosch runs at a "
     "deliberately compromised temperature and buys the loss back with 150-300 atmospheres and an "
     "iron catalyst. It is the textbook case of engineering against an equilibrium"),

    ("Haber–Bosch nitrogen fixation (bread from air)", "rests_on",
     "Stoichiometry & the mole concept",
     "N2 + 3H2 -> 2NH3 is a mole-ratio statement before it is an industry; yield, feed rates and "
     "recycle are all stoichiometry"),

    ("The Green Revolution (Borlaug, semi-dwarf breeding)", "rests_on",
     "Haber–Bosch nitrogen fixation (bread from air)",
     "the two are one package and neither works alone. Fertilising a traditional TALL wheat makes "
     "it lodge -- fall over under its own grain weight -- so the nitrogen is wasted. A semi-dwarf "
     "stalk converts that nitrogen into grain instead of straw. Dwarfing is what made industrial "
     "nitrogen worth applying"),

    ("The Green Revolution (Borlaug, semi-dwarf breeding)", "rests_on",
     "Mendelian inheritance",
     "Borlaug's method is selective breeding at scale: crossing for disease resistance, "
     "photoperiod insensitivity and short stature, then selecting the segregants that carry all "
     "three. Mendelian ratios are what make that search finite rather than hopeful"),

    ("Crop rotation & biological nitrogen fixation (the low-input path)", "limits",
     "Haber–Bosch nitrogen fixation (bread from air)",
     "root nodules do at soil temperature and one atmosphere, by the nitrogenase enzyme, what "
     "Haber-Bosch needs 400C and 200 atm to do -- so the industrial route is not the only way to "
     "break the triple bond, only the fastest. This bounds the DEPENDENCY: rotation and "
     "intercropping buy fertility with knowledge and labour rather than with purchased inputs, "
     "which is the difference between a farmer who can act and one who cannot"),

    ("Crop rotation & biological nitrogen fixation (the low-input path)", "rests_on",
     "Nutrient cycling & agronomy (NPK, evapotranspiration)",
     "rotation is a nutrient-budget strategy: legumes deposit nitrogen, deep-rooted crops lift "
     "leached minerals, and the sequence is chosen so each course returns what the last removed"),

    ("Liebig's law of the minimum (what actually limits growth)", "rests_on",
     "Nutrient cycling & agronomy (NPK, evapotranspiration)",
     "the law is the reason a nutrient BUDGET rather than a nutrient total is the useful object: "
     "the scarcest element sets the yield, so the budget must be read element by element"),

    ("Agricultural science (yield, soil-pH suitability)", "rests_on",
     "Liebig's law of the minimum (what actually limits growth)",
     "yield responds to the binding constraint and to nothing else, so a soil test precedes any "
     "purchase -- adding nitrogen to a phosphorus-limited field buys nothing"),

    ("Vaccination & immune memory (Jenner to eradication)", "rests_on",
     "Germ theory of disease",
     "a vaccine only makes sense if disease is caused by a specific transmissible agent that the "
     "body can learn to recognise. Jenner acted 60 years before germ theory explained why it "
     "worked, which is the same order as Kepler before Newton: a reliable effect first, the "
     "mechanism after"),

    ("Antisepsis & handwashing (Semmelweis, Lister)", "rests_on",
     "Germ theory of disease",
     "Lister built antisepsis directly on Pasteur. Semmelweis had the decisive MEASUREMENT twenty "
     "years earlier -- mortality from ~18% to ~2% on chlorinated-lime handwashing -- and was "
     "rejected for having no mechanism. A measured effect without a mechanism is still evidence, "
     "and demanding the mechanism first cost thousands of lives"),

    ("Antibiotics & antimicrobial resistance (Fleming's own warning)", "rests_on",
     "Darwinian evolution by natural selection",
     "resistance is not a misuse of the theory, it IS the theory: an antibiotic is a selection "
     "pressure, the susceptible die, any resistant variant reproduces, and the population shifts "
     "within days. Fleming warned of exactly this in his 1945 Nobel lecture"),

    ("Antibiotics & antimicrobial resistance (Fleming's own warning)", "rests_on",
     "Pharmacokinetics (dosing, clearance, half-life)",
     "the practical rule -- finish the course, and dose adequately -- is pharmacokinetic: "
     "sub-therapeutic concentrations kill the weakest bacteria and select the rest"),

    ("Sanitation, clean water & oral rehydration (Snow's pump handle)", "rests_on",
     "Germ theory of disease",
     "Snow demonstrated waterborne transmission in 1854 from a map and a death count, before the "
     "organism was seen -- a spatial pattern in data identifying a cause no microscope had yet "
     "resolved. Germ theory later supplied the agent"),

    ("Sanitation, clean water & oral rehydration (Snow's pump handle)", "rests_on",
     "Homeostasis & physiological regulation",
     "cholera kills by dehydration and electrolyte loss rather than by the organism, so the "
     "treatment is a homeostasis problem. Oral rehydration works because glucose drives sodium "
     "co-transport across the gut wall EVEN while it is inflamed -- which is why salt, sugar and "
     "clean water can replace an intravenous drip"),

    # -- BATCH 11: POWER, FLUIDS, HEAT, AND TWO BEAMS WE WERE ALREADY LEANING ON (2026-08-03) ---
    # Matt: "Tesla first, but there is a deep list." / "Mathematics should cover all known forms."
    #
    # GROUP THEORY and TOPOLOGY are the Noether mistake repeated at scale: both were cited as
    # EVIDENCE on existing edges while no card held them. Noether's theorem is about symmetries;
    # the crystallographic restriction behind quasicrystals is group theory; the fixed-point
    # theorems under Nash equilibrium are topological. A floor that names a beam it does not
    # contain is telling the truth about the world and lying about itself.
    ("Group theory & symmetry (the mathematics of what stays the same)", "rests_on",
     "Zermelo–Fraenkel set theory (ZFC)",
     "a group is a SET with an operation satisfying four axioms; the whole of abstract algebra is "
     "built on the set-theoretic foundation"),

    ("Noether's theorem (symmetry and conservation)", "rests_on",
     "Group theory & symmetry (the mathematics of what stays the same)",
     "THE BEAM, NOW HELD. Noether's theorem says every differentiable SYMMETRY of the action "
     "yields a conserved quantity -- and symmetries form groups, specifically continuous Lie "
     "groups here. Time-translation gives energy, space-translation momentum, rotation angular "
     "momentum. Group theory is why the conservation laws are consequences rather than a list of "
     "coincidences, and the floor cited this relationship for a day before holding a card for it"),

    ("Quasicrystals (forbidden symmetry in real matter)", "rests_on",
     "Group theory & symmetry (the mathematics of what stays the same)",
     "the CRYSTALLOGRAPHIC RESTRICTION THEOREM -- that a periodic lattice admits only 2-, 3-, 4- "
     "and 6-fold rotational symmetry, never 5-fold -- is a group-theoretic result about which "
     "rotations can generate a lattice. That theorem is exactly why Shechtman's ten-fold "
     "diffraction pattern was held to be impossible, and why the resolution had to be that the "
     "structure is not periodic"),

    ("Fixed-point theorems (Brouwer, Kakutani)", "rests_on",
     "Topology (what survives stretching)",
     "THE SECOND BEAM. Brouwer's theorem is topological, not algebraic: it holds for any convex "
     "compact set because of the SHAPE of that set, and no formula is produced. That is precisely "
     "why Nash can prove an equilibrium exists while giving no method to find it -- the "
     "non-constructiveness is inherited from the topology"),

    ("Graph theory (Euler, connectivity)", "same_form",
     "Topology (what survives stretching)",
     "graph theory is topology with the geometry discarded: Euler solved the Königsberg bridges by "
     "keeping only what touches what, and his V - E + F = 2 for convex polyhedra is a property of "
     "the SPHERE they are drawn on rather than of any solid. This is why one theory serves road "
     "networks, molecules and a corpus of linked cards alike"),

    ("Electromagnetic induction (Faraday's law — how all electricity is made)", "rests_on",
     "Maxwell's equations / classical electromagnetism",
     "Faraday's law is one of Maxwell's four equations; Faraday found it experimentally in 1831 "
     "and Maxwell gave it its mathematical form thirty years later. The minus sign (Lenz) is "
     "conservation of energy appearing as a sign: were it positive, cranking a generator would "
     "yield free energy"),

    ("AC & the polyphase system (Tesla, and why the grid is alternating)", "rests_on",
     "Electromagnetic induction (Faraday's law — how all electricity is made)",
     "a transformer needs a CHANGING flux, which is why only alternating current can be stepped "
     "up and down efficiently -- and since transmission loss is I^2*R, raising voltage tenfold "
     "cuts loss a hundredfold. That single fact settled the war of currents on engineering rather "
     "than personality. The rotating magnetic field from three phases 120 degrees apart is "
     "induction applied again, and it gives a motor with no brushes to wear out"),

    ("AC & the polyphase system (Tesla, and why the grid is alternating)", "same_form",
     "The electromagnetic spectrum & modulation (radio to gamma, one axis)",
     "the Tesla coil is a resonant air-core transformer -- two LC circuits tuned to the same "
     "frequency so energy transfers between them -- which is the SAME resonant selection a radio "
     "receiver uses to pick one station out of the spectrum. Power engineering and radio "
     "reception are one principle at different scales"),

    ("Fluid mechanics (Bernoulli, Reynolds, Navier–Stokes)", "rests_on",
     "Conservation of energy (1st law of thermodynamics)",
     "Bernoulli's principle IS energy conservation along a streamline: pressure plus kinetic plus "
     "potential is constant, so where a fluid speeds up its pressure must drop. Not a special "
     "force -- a bookkeeping identity"),

    ("Fluid mechanics (Bernoulli, Reynolds, Navier–Stokes)", "limits",
     "Dynamical systems & deterministic chaos",
     "turbulence is the practical face of chaos: above a Reynolds number of roughly 4,000 the flow "
     "becomes chaotic and mixing, and whether the Navier-Stokes equations even admit smooth "
     "solutions in three dimensions is an open Clay Millennium Problem. We design aircraft and "
     "heart valves with equations whose basic mathematical behaviour is unproven"),

    ("Heat transfer (conduction, convection, radiation)", "rests_on",
     "Second law of thermodynamics (entropy)",
     "all three modes run only hot-to-cold unaided, and that direction is the second law. It is "
     "also why insulation slows heat and never blocks it: you can lengthen the path, not reverse "
     "the arrow"),

    ("Heat transfer (conduction, convection, radiation)", "same_form",
     "The electromagnetic spectrum & modulation (radio to gamma, one axis)",
     "thermal radiation is not a fourth kind of heat but the spectrum again: every body emits "
     "electromagnetic radiation whose total rises as the FOURTH power of absolute temperature "
     "(Stefan-Boltzmann) and whose peak wavelength shifts with temperature (Wien). That is the "
     "same law spectroscopy reads a star's temperature from"),

    ("The Carnot limit (the ceiling on every engine ever built)", "rests_on",
     "Second law of thermodynamics (entropy)",
     "the bound eta = 1 - Tc/Th follows from reversibility, and it is why an engine MUST dump heat "
     "to a cold sink to run at all. Waste heat is a requirement, not a design flaw. Carnot "
     "published it in 1824, before thermodynamics existed and while heat was still thought to be a "
     "fluid -- the result outlived the theory it was derived in"),

    # -- BATCH 12: THE CHEMISTRY OF LIFE AND THE BRIDGES BETWEEN FLOORS (2026-08-03) ------------
    # Filling measured gaps: organic chemistry, biochemistry, immunology, neuroscience,
    # statistical mechanics, differential equations, electrochemistry -- plus the double helix,
    # which the floor referenced through the central dogma while holding no card for the molecule.
    ("Organic chemistry & functional groups (why life is built on carbon)", "rests_on",
     "Chemical bonding (valence-bond / molecular-orbital)",
     "carbon's four near-equal bonds and its unique ability to bond indefinitely to ITSELF "
     "(catenation) are consequences of its electron configuration. Silicon sits directly below it "
     "and cannot manage it -- weaker bonds, and an oxide that is a solid rather than a gas -- which "
     "is why life is carbon"),

    ("Biochemistry & enzymes (catalysis at body temperature)", "rests_on",
     "Chemical kinetics & equilibrium (Arrhenius, Le Chatelier)",
     "an enzyme lowers ACTIVATION ENERGY without shifting the equilibrium or supplying energy -- "
     "it changes how fast the system reaches where it was already going. Rate enhancements of "
     "10^10 and beyond are routine, which is how a body runs industrial chemistry at 37C and "
     "neutral pH"),

    ("Crop rotation & biological nitrogen fixation (the low-input path)", "rests_on",
     "Biochemistry & enzymes (catalysis at body temperature)",
     "the nitrogenase enzyme in a root nodule breaks the nitrogen triple bond at soil temperature "
     "and one atmosphere. That is the same bond Haber-Bosch needs 400C and 200 atm to break, and "
     "the difference is catalysis -- the clearest case on the floor of biology outperforming "
     "industry on conditions while losing on rate"),

    ("The double helix (structure that explains its own copying)", "rests_on",
     "Chemical bonding (valence-bond / molecular-orbital)",
     "base pairing is hydrogen bonding with exact geometry: adenine-thymine by two bonds, "
     "guanine-cytosine by three, and the pairing is EXCLUSIVE because only those shapes fit. "
     "Chargaff had measured A=T and G=C before the structure was proposed, which made the pairing "
     "forced rather than chosen"),

    ("Central dogma of molecular biology (DNA→RNA→protein)", "rests_on",
     "The double helix (structure that explains its own copying)",
     "the structure contains its own mechanism: because pairing is exclusive, each strand carries "
     "the information to rebuild the other, so separating them gives two templates. Watson and "
     "Crick's closing line noted the structure 'immediately suggests a possible copying mechanism' "
     "-- heredity explained by geometry"),

    ("The immune system (innate and adaptive, and self versus not-self)", "same_form",
     "Darwinian evolution by natural selection",
     "clonal selection is Darwinian machinery running inside one body on a timescale of days: "
     "lymphocyte receptors are generated at RANDOM, and the ones that happen to match an invader "
     "are selected and amplified. The body does not design an antibody to fit a pathogen; it makes "
     "millions of shapes in advance and multiplies whichever fits"),

    ("Vaccination & immune memory (Jenner to eradication)", "rests_on",
     "The immune system (innate and adaptive, and self versus not-self)",
     "a vaccine works by exploiting the memory cells left behind after clonal selection, so its "
     "mechanism is the adaptive system's and nothing else"),

    ("Neurons & the action potential (how a nerve carries a signal)", "same_form",
     "The electromagnetic spectrum & modulation (radio to gamma, one axis)",
     "the action potential is ALL-OR-NOTHING, so a nerve encodes intensity as FREQUENCY rather "
     "than amplitude -- more spikes, not bigger ones. That is the same engineering choice as "
     "frequency modulation over amplitude modulation, made for the same reason: a frequency code "
     "survives attenuation that would corrupt an amplitude code. Biology and radio reached it "
     "independently"),

    ("Statistical mechanics (Boltzmann — why the second law is a counting argument)", "rests_on",
     "Kolmogorov probability axioms",
     "S = k log W counts MICROSTATES consistent with an observed macrostate, so the second law "
     "becomes a probability statement rather than a commandment: heat spreads because "
     "overwhelmingly more arrangements are spread out than concentrated. At 10^23 particles, "
     "'overwhelmingly unlikely' becomes 'never observed'"),

    ("Statistical mechanics (Boltzmann — why the second law is a counting argument)", "same_form",
     "Shannon information theory (entropy, channel capacity)",
     "Boltzmann's log W and Shannon's -sum p log p are one functional. Both count how much you do "
     "NOT know about which microstate you are in, which is why thermodynamic and informational "
     "entropy are the same measure rather than a shared metaphor -- and why erasing a bit has a "
     "minimum thermodynamic cost"),

    ("Second law of thermodynamics (entropy)", "rests_on",
     "Statistical mechanics (Boltzmann — why the second law is a counting argument)",
     "the macroscopic law is derived from the microscopic counting: irreversibility is not a "
     "separate principle but what probability looks like at Avogadro scale"),

    ("Differential equations (the language every physical law is written in)", "rests_on",
     "Fundamental theorem of calculus",
     "solving a differential equation is integration under constraint, and the local-to-global "
     "move -- a rate specified at every instant determining a whole trajectory -- is the "
     "fundamental theorem doing its work"),

    ("Newton's three laws of motion", "rests_on",
     "Differential equations (the language every physical law is written in)",
     "F = ma is a second-order differential equation in position, and it determines nothing "
     "without INITIAL CONDITIONS. The law says how things change; the conditions say what is "
     "actually happening. Chaos is exactly the case where those conditions can never be known "
     "well enough"),

    ("Electrochemistry & the battery (Volta, Faraday, and stored charge)", "rests_on",
     "Brønsted–Lowry acid–base theory & pH",
     "cells run on redox in an electrolyte, and electrode potentials shift with concentration and "
     "pH by the Nernst equation -- which is why a battery weakens in the cold and why corrosion "
     "accelerates in salt water"),

    ("Electrochemistry & the battery (Volta, Faraday, and stored charge)", "rests_on",
     "Ohm's law & circuit theory (Kirchhoff)",
     "voltage is set by CHEMISTRY and capacity by QUANTITY, which is why cells series for voltage "
     "and parallel for capacity; internal resistance is why a battery's terminal voltage sags "
     "under load. Volta's pile (1800) was the first steady current source, and every "
     "electromagnetic experiment afterwards depended on having one"),

    # -- BATCH 13: THICKEN THE COMB (2026-08-03) -----------------------------------------------
    # Matt: "Think of the corpus as a honeycomb filled with honey. The structure matters."
    # Measured after the depth work finished: every one of 144 cards carries real content, and 32
    # of them still had ONE relation or none. A hexagonal comb has six neighbours per cell and a
    # median of 2 is a chain, not a comb. These are the joins the starved cells were missing --
    # each one a relation that was already TRUE and simply never written down.
    ("Pythagorean theorem", "rests_on", "Euclidean geometry & the parallel postulate",
     "the theorem is logically EQUIVALENT to the parallel postulate -- it holds exactly when the "
     "space is flat and fails measurably on a sphere or a saddle. So it is not merely derived from "
     "Euclid's fifth, it is another way of stating it"),

    ("Non-Euclidean (hyperbolic / elliptic) geometry", "limits",
     "Euclidean geometry & the parallel postulate",
     "two thousand years of failed attempts to PROVE the fifth postulate ended when Lobachevsky, "
     "Bolyai and Riemann denied it without contradiction. Euclidean geometry is therefore one "
     "choice among consistent alternatives rather than the necessary geometry of space -- and "
     "which one describes the world became an empirical question"),

    ("General relativity", "rests_on", "Non-Euclidean (hyperbolic / elliptic) geometry",
     "gravity as CURVATURE requires a geometry in which curvature is meaningful, and the angle sum "
     "of a triangle reveals it from INSIDE the space with no outside vantage point. A pure "
     "mathematical rebellion against one axiom became the language of gravity ninety years later"),

    ("Physical oceanography (hydrostatics, tides)", "rests_on",
     "Newton's law of universal gravitation",
     "tides are a GRADIENT effect, not a pull: what raises them is the DIFFERENCE in gravitational "
     "attraction across the Earth's diameter, which is why there are two bulges and two high tides "
     "a day rather than one. The inverse-square law differentiated is the tide"),

    ("Radiometric dating & uniformitarianism", "rests_on", "Nuclear decay & binding energy",
     "the entire method rests on decay being a fixed PROBABILITY per unit time, unaffected by "
     "temperature, pressure or chemistry. That indifference is what makes a nucleus a clock -- and "
     "it is a nuclear fact, not a geological one"),

    ("Neurons & the action potential (how a nerve carries a signal)", "rests_on",
     "Electrochemistry & the battery (Volta, Faraday, and stored charge)",
     "a neuron IS an electrochemical cell: it holds about -70 mV across its membrane by pumping "
     "ions against their gradients, and the Nernst equation gives that potential from the "
     "concentration ratio. The action potential is that stored charge discharging through gated "
     "channels, so the nerve and the battery are the same physics"),

    ("Music theory (harmonic series, equal temperament)", "rests_on",
     "Acoustic wave theory (harmonics, Doppler)",
     "the harmonic series is a physical fact about standing waves before it is a musical one: a "
     "string sounds a fundamental plus integer multiples, and consonant intervals are the simple "
     "ratios whose overtones coincide rather than beat"),

    ("Music theory (harmonic series, equal temperament)", "same_form",
     "Fourier analysis & signal processing",
     "timbre IS a spectrum -- what distinguishes a violin from a flute at the same pitch is the "
     "relative strength of the harmonics, which is the Fourier decomposition of the waveform heard "
     "rather than plotted"),

    ("Hess's law / thermochemistry", "rests_on",
     "Conservation of energy (1st law of thermodynamics)",
     "path-independence IS energy conservation: if the enthalpy change depended on the route, a "
     "cycle could be run to create energy from nothing. Enthalpy being a STATE FUNCTION is the "
     "first law expressed as a bookkeeping property"),

    ("Phase theory (phase diagrams, Clausius–Clapeyron)", "rests_on",
     "Differential equations (the language every physical law is written in)",
     "the Clausius-Clapeyron relation is a differential equation for the slope of a phase boundary "
     "(dP/dT), and integrating it is what predicts a boiling point at altitude"),

    ("Population ecology (Lotka–Volterra, carrying capacity)", "rests_on",
     "Differential equations (the language every physical law is written in)",
     "the logistic and predator-prey models ARE coupled differential equations, and their cycles "
     "and equilibria are properties of the solutions rather than observations added on top"),

    ("Population ecology (Lotka–Volterra, carrying capacity)", "same_form",
     "Control theory & cybernetics (feedback, stability)",
     "carrying capacity is negative feedback with a set point, and OVERSHOOT-and-crash is what a "
     "control loop does when its response lags -- the same delay pathology that makes a shower "
     "oscillate and a supply chain whipsaw"),

    ("Queueing theory (Little's law)", "rests_on", "Kolmogorov probability axioms",
     "arrivals and service times are random variables, and every queueing result is a statement "
     "about their distributions; Little's law holds for ANY stable queue precisely because it does "
     "not depend on which distributions they are"),

    ("Law of large numbers", "same_form",
     "Statistical mechanics (Boltzmann — why the second law is a counting argument)",
     "both say the same thing at different scales: averages over many independent draws converge, "
     "so at 10^23 particles a thermodynamic quantity has no observable fluctuation. "
     "Irreversibility IS the law of large numbers with Avogadro's number of trials"),

    ("Bayes' theorem", "limits",
     "Null-hypothesis significance testing (Fisher / Neyman–Pearson)",
     "a p-value is P(data|null) and is routinely read as P(null|data). Bayes gives the correct "
     "inversion and shows it requires a PRIOR that NHST never supplies -- which is why a "
     "significant result on a rare hypothesis is usually still a false positive. The commonest "
     "error in published science is this one missing term"),

    ("Modern portfolio theory (Markowitz)", "limits", "Central limit theorem",
     "the model treats returns as approximately normal, which requires finite variance and "
     "independence. Market returns are fat-tailed and their correlations converge toward one "
     "during a crash, so the diversification computed in calm conditions evaporates exactly when "
     "it is needed. The theorem's CONDITIONS, not the theorem, are what fail"),

    ("Real-estate valuation (cap rate, DCF)", "rests_on", "Time value of money & discounting",
     "a DCF is discounting applied to rents, and the cap rate is its shorthand -- which is why "
     "comparing the cap rate to the prevailing interest rate is the test that matters: when "
     "borrowing costs more than the property yields, the arithmetic only works if prices keep "
     "rising"),

    ("Labor economics (minimum wage, overtime law)", "rests_on",
     "Supply & demand / market equilibrium",
     "the textbook prediction that a wage floor cuts employment is the supply-and-demand diagram "
     "applied to labour -- and MONOPSONY is what that diagram omits, which is why the empirical "
     "record refused to match the confident theory"),

    ("Comparative advantage", "same_form", "Linear programming & duality",
     "opportunity cost IS a shadow price: what you give up to produce a thing is exactly the dual "
     "variable on your own binding constraint. Ricardo's argument and LP duality are one piece of "
     "mathematics, which is why comparative advantage scales unchanged from one person's day to "
     "national trade"),

    ("Public choice / decision theory", "rests_on", "Game theory (Nash equilibrium)",
     "concentrated benefits with diffuse costs is a game whose equilibrium favours the organised "
     "minority, and rational ignorance is an equilibrium too -- neither requires conspiracy, only "
     "each player acting on their own payoffs"),

    ("Double-entry accounting identity (A = L + E)", "same_form",
     "Cryptographic security (hashing, checksums, PKI)",
     "the identity is a CHECKSUM: single-entry has no internal test and carries an error silently, "
     "while double-entry makes most mistakes announce themselves as an imbalance. Error detection "
     "built into the notation, which is what a parity bit does for a byte -- and neither stops a "
     "deliberate forgery that alters both sides consistently"),

    ("Exercise physiology (VO₂max, HR zones)", "rests_on",
     "Bioenergetics / energy balance (calorimetry, 4-9-4)",
     "VO2max is a measurement of the rate at which oxygen can be delivered to burn fuel, so the "
     "ceiling on sustained work is a bioenergetic ceiling; the three energy systems are three "
     "routes to ATP with different rates and capacities"),

    ("Exercise physiology (VO₂max, HR zones)", "rests_on",
     "Homeostasis & physiological regulation",
     "progressive overload is homeostasis exploited deliberately: a stress slightly beyond the "
     "accustomed shifts the set point during RECOVERY. Training without recovery is stress without "
     "adaptation, which is how overtraining and injury arrive"),

    ("Antisepsis & handwashing (Semmelweis, Lister)", "rests_on", "Cell theory",
     "sterilisation only works if life comes from life. Pasteur's swan-neck flask showed broth "
     "stays sterile while air reaches it but dust cannot, disposing of spontaneous generation -- "
     "and without that clause, boiling instruments would be pointless because organisms would "
     "simply reappear"),

    ("Biochemistry & enzymes (catalysis at body temperature)", "rests_on",
     "Organic chemistry & functional groups (why life is built on carbon)",
     "an enzyme's active site is functional groups arranged in space, and its specificity comes "
     "from shape and chirality -- the modular behaviour of functional groups is what makes a "
     "protein's chemistry predictable at all"),

    ("Fundamental theorem of algebra", "rests_on", "Topology (what survives stretching)",
     "the name is a mild lie: every proof is ultimately analytic or topological, resting on "
     "continuity or on a WINDING NUMBER argument rather than on algebra alone. A statement about "
     "polynomial roots turns out to be a statement about the shape of the plane"),

    ("Measure theory (Lebesgue integration)", "rests_on", "Zermelo–Fraenkel set theory (ZFC)",
     "measure theory is built on sets, and it finds its own edge there: assuming the axiom of "
     "choice, NON-MEASURABLE sets exist (Vitali) -- objects to which no consistent size can be "
     "assigned. Not everything can be measured, and the theory is precise about which"),

    ("Historical chronology (era reckoning, elapsed years)", "rests_on",
     "Calendar theory (Gregorian reform, leap rules)",
     "elapsed-time arithmetic depends on which calendar the source used, and the Gregorian "
     "changeover means one day carries two dates depending on the country. A date is a DERIVED "
     "quantity carrying assumptions, not a raw fact"),

    ("Normative ethics (consequentialism / deontology / virtue)", "rests_on",
     "Formal logic & epistemology (validity, inference)",
     "an ethical argument can be perfectly VALID and rest on premises no logic can establish, "
     "which is exactly why this pair sits together: the engine can check the chain and cannot "
     "supply the premises, and pretending otherwise would be the failure"),

    ("Photographic exposure theory (exposure value, reciprocity)", "rests_on",
     "Wave optics (Huygens, Snell's law, diffraction)",
     "aperture is a diffraction-limited opening, so stopping down past a point costs sharpness "
     "rather than gaining it -- resolution is bounded by roughly wavelength over aperture, the "
     "same limit that sets a telescope's"),

    # -- BATCH 14: CLOSE THE NAMED GAPS (2026-08-03) -------------------------------------------
    # Matt: "All of the still open should be completed." Every branch the coverage audits flagged
    # and had not yet been filled, plus Archimedes and Harvey -- two figures whose work is
    # load-bearing and was absent.
    ("Simple machines & buoyancy (Archimedes)", "rests_on",
     "Conservation of energy (1st law of thermodynamics)",
     "a machine trades DISTANCE for FORCE and creates nothing: halve the force and you must double "
     "the distance, because the work is conserved. Mechanical advantage is that identity read as a "
     "ratio, and it is why no arrangement of levers and pulleys has ever been a perpetual motion "
     "machine"),

    ("Simple machines & buoyancy (Archimedes)", "rests_on",
     "Physical oceanography (hydrostatics, tides)",
     "buoyancy is hydrostatics: the upward force equals the WEIGHT OF FLUID DISPLACED, which "
     "follows from pressure increasing with depth so the bottom of a submerged body is pushed "
     "harder than the top"),

    ("Structural statics (load, moment, floor-area ratio)", "rests_on",
     "Simple machines & buoyancy (Archimedes)",
     "moment is force times distance, which is the law of the lever -- and Archimedes gave it a "
     "PROOF rather than a rule of thumb. Every statics calculation about a beam is that law summed "
     "around a point"),

    ("Circulation of the blood (Harvey's quantitative argument)", "rests_on",
     "Homeostasis & physiological regulation",
     "a closed circulatory loop is what makes regulated internal conditions possible at all: "
     "delivery of oxygen and nutrients and removal of waste at a controlled rate is the transport "
     "layer every set point depends on"),

    ("Circulation of the blood (Harvey's quantitative argument)", "same_form",
     "Fluid mechanics (Bernoulli, Reynolds, Navier–Stokes)",
     "Harvey's argument was ARITHMETIC -- ejected volume times pulse rate gives several times the "
     "body's weight in blood per hour, which no organ could manufacture and no tissue consume, so "
     "the same blood must return. Continuity of flow proved circulation before any capillary was "
     "seen, and Malpighi confirmed the predicted connection four years after Harvey died"),

    ("Plasma physics (the fourth state, and most of the universe)", "rests_on",
     "Maxwell's equations / classical electromagnetism",
     "a plasma's defining property is that its charges are FREE, so it responds to electric and "
     "magnetic fields as a neutral gas cannot. Magnetohydrodynamics couples fluid flow to Maxwell, "
     "and the counter-intuitive result -- field lines effectively frozen into a good conductor and "
     "dragged with the flow -- is how stellar fields wind up and flares store energy"),

    ("Plasma physics (the fourth state, and most of the universe)", "rests_on",
     "Kinetic theory of gases",
     "a plasma is a gas whose particles have been ionised, so the kinetic picture still applies "
     "-- temperature is still average kinetic energy -- with long-range Coulomb forces added to "
     "the short-range collisions"),

    ("Stellar nucleosynthesis & the HR diagram", "rests_on",
     "Plasma physics (the fourth state, and most of the universe)",
     "a star IS a self-gravitating plasma, and its structure, energy transport and confinement are "
     "plasma physics before they are astronomy"),

    ("Condensed matter & semiconductors (band theory and the transistor)", "rests_on",
     "Pauli exclusion principle",
     "bands exist because electrons cannot share states: atomic levels smear into bands as atoms "
     "approach, and the FILLING of those bands under exclusion is what decides conductor, "
     "insulator or semiconductor. The transistor is the Pauli principle turned into a switch"),

    ("Condensed matter & semiconductors (band theory and the transistor)", "limits",
     "Standard Model / quantum field theory",
     "EMERGENCE bounds reductionism: superconductivity, magnetism and band structure are "
     "properties of the COLLECTIVE that no individual particle has, so knowing the fundamental "
     "constituents perfectly does not yield the behaviour of the whole. Anderson's 'more is "
     "different' is a claim about physics, not about our ignorance"),

    ("Chemical engineering (unit operations, balances, and scale-up)", "rests_on",
     "Law of conservation of mass (Lavoisier)",
     "a mass balance around a chosen boundary IS conservation of mass turned into an accounting "
     "sheet, and it is the working tool of the whole discipline"),

    ("Chemical engineering (unit operations, balances, and scale-up)", "limits",
     "Heat transfer (conduction, convection, radiation)",
     "SCALE-UP fails geometrically: multiply linear size by ten and volume rises 1,000-fold while "
     "surface area rises 100-fold, so heat transfer PER UNIT VOLUME falls tenfold. A reaction "
     "easily cooled in a flask runs away in a tank. The square-cube law is why the pilot plant "
     "exists and why 'it worked in the lab' proves nothing about scale"),

    ("Systems engineering (requirements, interfaces, and emergent failure)", "rests_on",
     "Reliability & tolerance stack-up (RSS)",
     "series reliability multiplies, so a system of many good parts can be a bad system -- which "
     "is the quantitative case for simplicity and for hunting COMMON-MODE failure, since two pumps "
     "on one power supply are not redundant"),

    ("Systems engineering (requirements, interfaces, and emergent failure)", "same_form",
     "Control theory & cybernetics (feedback, stability)",
     "both are disciplines of the WHOLE rather than the parts: stability is a property of the loop, "
     "and emergent behaviour is a property of the system, so testing every component is not testing "
     "either one. The Mars Climate Orbiter was lost with both subsystems correct and the interface "
     "unstated"),

    ("Differential geometry (curvature measured from inside)", "rests_on",
     "Non-Euclidean (hyperbolic / elliptic) geometry",
     "differential geometry is the general machinery for which hyperbolic and elliptic geometry are "
     "constant-curvature special cases; Riemann's 1854 lecture generalised them to manifolds of "
     "arbitrary varying curvature"),

    ("General relativity", "rests_on", "Differential geometry (curvature measured from inside)",
     "GAUSS'S THEOREMA EGREGIUM is what makes the theory possible: curvature is INTRINSIC and "
     "measurable from within a surface, with no surrounding space required. So spacetime need not "
     "curve 'inside' anything, and observers stuck in it can measure its shape. Riemann built the "
     "mathematics sixty years before Einstein needed it"),

    ("Algebraic geometry (solution sets as shapes)", "same_form",
     "Euclidean geometry & the parallel postulate",
     "Descartes put coordinates on the plane in 1637 and made equation and shape one object seen "
     "two ways -- x^2 + y^2 = 1 is both a formula and a circle. It is the original case of the "
     "pattern this floor keeps finding: two descriptions of one structure, each doing work the "
     "other cannot"),

    ("Cryptographic security (hashing, checksums, PKI)", "rests_on",
     "Algebraic geometry (solution sets as shapes)",
     "points on an elliptic curve can be ADDED by a geometric rule, forming a group, and the "
     "difficulty of reversing that addition is what elliptic-curve cryptography rests on -- which "
     "secures most modern connections and signatures, including this project's seals"),

    ("Category theory (the mathematics of structure-preserving maps)", "rests_on",
     "Zermelo–Fraenkel set theory (ZFC)",
     "categories are defined over collections of objects and arrows, and the size questions that "
     "raises (small versus large categories) are set-theoretic ones the framework has to answer"),

    ("Category theory (the mathematics of structure-preserving maps)", "same_form",
     "Group theory & symmetry (the mathematics of what stays the same)",
     "a group IS a category with one object whose every arrow is invertible -- so group theory is "
     "a special case, and the generalisation is what lets 'same structure' be stated precisely. "
     "This is the formal theory of what this floor's own `same_form` relation gestures at: when "
     "Shannon entropy and Boltzmann entropy, or a mixed strategy and a density matrix, turn out to "
     "share a form, an isomorphism is what would make that checkable rather than merely observed"),

    ("Numerical analysis (why the computer's answer is not the answer)", "limits",
     "Differential equations (the language every physical law is written in)",
     "most differential equations of practical interest have no closed-form solution and are "
     "integrated numerically, so the answer carries discretisation and rounding error. An "
     "ill-CONDITIONED problem amplifies input error and no algorithm repairs it; an UNSTABLE "
     "algorithm amplifies rounding error and a better method does. Confusing the two is how bad "
     "numerics get blamed on the wrong thing"),

    ("Numerical analysis (why the computer's answer is not the answer)", "limits",
     "Church–Turing thesis / computability",
     "computability says what a machine could compute given unlimited exact arithmetic; numerical "
     "analysis says what it actually returns with 64 bits and finite time. 0.1 + 0.2 is not 0.3 in "
     "binary floating point, and the Patriot failure at Dhahran in 1991 killed 28 people because a "
     "clock accumulated rounding error over 100 hours. This is the gap between computable and "
     "computed"),

    ("Acoustic wave theory (harmonics, Doppler)", "same_form",
     "The electromagnetic spectrum & modulation (radio to gamma, one axis)",
     "identical wave mathematics on a different carrier: frequency, wavelength, superposition, "
     "harmonics and Doppler shift all transfer unchanged, which is why the same Fourier tools "
     "serve music and radio. THE DISANALOGY IS LOAD-BEARING AND IS KEPT: sound is a pressure wave "
     "requiring a medium and travels at ~343 m/s in air, while an electromagnetic wave needs none "
     "and travels at c. Same form, different substance -- the resemblance is real and it is not an "
     "identity"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--path", default=os.path.join(ROOT, "data", "theory_cards.jsonl"))
    args = ap.parse_args()

    if os.path.exists(os.path.join(ROOT, ".gate.lock")):
        print("the gate holds the floor — run this after it finishes")
        return 2

    rows, index, by_title = [], {}, {}
    with open(args.path, encoding="utf-8") as fh:
        for line in fh:
            s = line.strip()
            if not s:
                rows.append(line)
                continue
            try:
                card = json.loads(s)
            except ValueError:
                rows.append(line)
                continue
            rows.append(card)
            index[card.get("id")] = card
            if card.get("shelf") == "theories":
                by_title.setdefault(_key(card.get("title")), card)

    # RESOLVE FIRST, WRITE NOTHING YET. A dangling edge is worse than no edge, so every end is
    # checked against the real shelf before a single card is touched.
    def _find(title):
        k = _key(title)
        if k in by_title:
            return by_title[k]
        kw = set(k.split())
        best, score = None, 0
        for other_k, card in by_title.items():
            ow = set(other_k.split())
            overlap = len(kw & ow)
            # a confident partial: most of the shorter name's words present in the other
            if overlap >= max(2, min(len(kw), len(ow)) - 1) and overlap > score:
                best, score = card, overlap
        return best

    planned, missing = [], []
    for a, rel, b, why in EDGES:
        ca, cb = _find(a), _find(b)
        if ca is None or cb is None:
            missing.append(((a if ca is None else b), f"{a} -{rel}-> {b}"))
            continue
        planned.append((ca["id"], rel, cb["id"], why))

    added = 0
    for ida, rel, idb, why in planned:
        card = index[ida]
        conns = card.setdefault("connections", [])
        if any(str(e.get("to_card_id")) == idb and e.get("relationship") == rel for e in conns):
            continue
        conns.append({"to_card_id": idb, "relationship": rel, "evidence": why})
        added += 1

    doms = {}
    for ida, rel, idb, _w in planned:
        da = ((index[ida].get("source") or {}).get("domain") or "?")
        db = ((index[idb].get("source") or {}).get("domain") or "?")
        if da != db:
            doms[(da, db)] = doms.get((da, db), 0) + 1

    print(f"{'PROPOSED' if args.dry_run else 'APPLIED'} — {added} new edge(s) of "
          f"{len(planned)} declared; {len(missing)} refused for a missing end\n")
    by_rel = {}
    for _a, rel, _b, _w in planned:
        by_rel[rel] = by_rel.get(rel, 0) + 1
    for rel, n in sorted(by_rel.items(), key=lambda x: -x[1]):
        print(f"  {n:>3}  {rel}")
    print(f"\n  cross-domain pairs joined: {len(doms)}")
    for (da, db), n in sorted(doms.items(), key=lambda x: -x[1])[:12]:
        print(f"      {da} -> {db}  ({n})")
    if missing:
        print("\n  REFUSED (a named theory is not on the shelf — say so, never invent it):")
        for mid, edge in missing:
            print(f"      {mid}   in   {edge}")

    if args.dry_run:
        print("\nNothing written.")
        return 0
    if not added:
        print("\nNothing to add — already assembled.")
        return 0

    tmp = args.path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        for r in rows:
            fh.write(r if isinstance(r, str) else json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, args.path)
    print(f"\nwrote {args.path} — {added} edge(s); every other line byte for byte")
    return 0


if __name__ == "__main__":
    sys.exit(main())
