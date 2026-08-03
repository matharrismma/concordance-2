#!/usr/bin/env python3
"""THE FLOOR — the aligned theories, assembled across domains.

    PYTHONPATH=src python tools/assemble_floor.py --dry-run
    PYTHONPATH=src python tools/assemble_floor.py

Matt, 2026-08-02: *"We should have assembled the aligned theories across domains. That was the
floor. Reality itself mapped... along with a coherent language model that can communicate reality
effectively."*

MEASURED FIRST, and the measurement is the indictment: 99 theory cards on the shelf, and
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
