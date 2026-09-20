"""The five verifiers built from Atlas's own formulas: neuroscience, electrochemistry,
condensed_matter, game_theory, archaeology. Each must CONFIRM a correct claim, catch a
wrong one (MISMATCH), and return NOT_APPLICABLE on an empty packet."""
import math

from concordance.verifiers import run_for_domain, VERIFIERS


def _find(results, name):
    for r in results:
        if r.name == name:
            return r
    return None


def test_all_five_domains_are_registered():
    for d in ("neuroscience", "electrochemistry", "condensed_matter", "game_theory", "archaeology"):
        assert d in VERIFIERS, f"{d} not registered"


def test_photonics_is_registered_and_computes():
    """Photonics — added 2026-09-19 because the Atlas's own topology asked for it (it closes two of
    the eight voids where random additions add holes). A connective domain: guided/resonant/active/
    nonlinear light, each check a real closed-form relation, pure stdlib (runs on the offline box)."""
    assert "photonics" in VERIFIERS
    # V = 2*pi*a*NA/lambda = 2.686 for a=4um, NA=0.14, lambda=1.31um
    ok = run_for_domain("photonics", {"PHOT_VERIFY": {
        "core_radius_m": 4e-6, "numerical_aperture": 0.14, "wavelength_m": 1.31e-6, "claimed_v_number": 2.686}})
    assert _find(ok, "photonics.waveguide_v_number").status == "CONFIRMED"
    bad = run_for_domain("photonics", {"PHOT_VERIFY": {
        "core_radius_m": 4e-6, "numerical_aperture": 0.14, "wavelength_m": 1.31e-6, "claimed_v_number": 9.9}})
    assert _find(bad, "photonics.waveguide_v_number").status == "MISMATCH"
    # FSR = c/(n_g*L); ring resonator
    fsr = run_for_domain("photonics", {"PHOT_VERIFY": {
        "group_index": 4.2, "ring_length_m": 6.28e-5, "claimed_fsr_hz": 1.137e12}})
    assert _find(fsr, "photonics.ring_resonator_fsr").status == "CONFIRMED"
    # d*sin(theta) = m*lambda -> 30 deg for d=1.5um, lambda=0.75um, m=1
    g = run_for_domain("photonics", {"PHOT_VERIFY": {
        "grating_period_m": 1.5e-6, "order": 1, "wavelength_m": 0.75e-6, "claimed_angle_deg": 30.0}})
    assert _find(g, "photonics.grating_angle").status == "CONFIRMED"
    assert run_for_domain("photonics", {})[0].status == "NOT_APPLICABLE"


def test_neuroscience_nernst_and_weber():
    # E = (RT/zF) ln(145/12) at 310K = 66.56 mV
    ok = run_for_domain("neuroscience", {"NEURO_VERIFY": {
        "ion_z": 1, "c_out_mM": 145, "c_in_mM": 12, "temp_K": 310, "claimed_mV": 66.56}})
    assert _find(ok, "neuroscience.nernst_potential").status == "CONFIRMED"
    bad = run_for_domain("neuroscience", {"NEURO_VERIFY": {
        "ion_z": 1, "c_out_mM": 145, "c_in_mM": 12, "temp_K": 310, "claimed_mV": 50.0}})
    assert _find(bad, "neuroscience.nernst_potential").status == "MISMATCH"
    wf = run_for_domain("neuroscience", {"NEURO_VERIFY": {
        "stimulus": 100, "reference": 10, "weber_k": 1.0, "claimed_sensation": math.log(10)}})
    assert _find(wf, "neuroscience.weber_fechner").status == "CONFIRMED"
    assert run_for_domain("neuroscience", {})[0].status == "NOT_APPLICABLE"


def test_electrochemistry_nernst_and_cell():
    # E = 1.10 - (RT/2F) ln(0.01) at 298.15K = 1.159 V
    ok = run_for_domain("electrochemistry", {"ECHEM_VERIFY": {
        "e0_V": 1.10, "n_electrons": 2, "reaction_quotient": 0.01, "claimed_E_V": 1.159}})
    assert _find(ok, "electrochemistry.nernst").status == "CONFIRMED"
    bad = run_for_domain("electrochemistry", {"ECHEM_VERIFY": {
        "e0_V": 1.10, "n_electrons": 2, "reaction_quotient": 0.01, "claimed_E_V": 1.0}})
    assert _find(bad, "electrochemistry.nernst").status == "MISMATCH"
    cell = run_for_domain("electrochemistry", {"ECHEM_VERIFY": {
        "e_cathode_V": 0.34, "e_anode_V": -0.76, "claimed_cell_V": 1.10}})
    assert _find(cell, "electrochemistry.cell_potential").status == "CONFIRMED"
    assert run_for_domain("electrochemistry", {})[0].status == "NOT_APPLICABLE"


def test_condensed_matter_phonon():
    # omega = 2 sqrt(K/m) |sin(ka/2)| with K=m=1, k=pi, a=1 -> 2
    ok = run_for_domain("condensed_matter", {"CONDMAT_VERIFY": {
        "spring_const": 1.0, "atom_mass": 1.0, "wavevector": math.pi, "lattice_a": 1.0, "claimed_omega": 2.0}})
    assert _find(ok, "condensed_matter.phonon_dispersion").status == "CONFIRMED"
    bad = run_for_domain("condensed_matter", {"CONDMAT_VERIFY": {
        "spring_const": 1.0, "atom_mass": 1.0, "wavevector": math.pi, "lattice_a": 1.0, "claimed_omega": 5.0}})
    assert _find(bad, "condensed_matter.phonon_dispersion").status == "MISMATCH"
    assert run_for_domain("condensed_matter", {})[0].status == "NOT_APPLICABLE"


def test_game_theory_payoff_and_nash():
    # prisoner's dilemma: expected payoff of (0.5,0.5) vs (0.5,0.5) = 2.25
    ok = run_for_domain("game_theory", {"GAME_VERIFY": {
        "row_payoff": [[3, 0], [5, 1]], "p": [0.5, 0.5], "q": [0.5, 0.5], "claimed_payoff": 2.25}})
    assert _find(ok, "game_theory.expected_payoff").status == "CONFIRMED"
    # (defect, defect) is the Nash equilibrium of the PD; (cooperate, cooperate) is not
    nash = run_for_domain("game_theory", {"GAME_VERIFY": {
        "row_payoff_A": [[3, 0], [5, 1]], "col_payoff_B": [[3, 5], [0, 1]],
        "profile": [1, 1], "claimed_is_nash": True}})
    assert _find(nash, "game_theory.nash_pure").status == "CONFIRMED"
    notnash = run_for_domain("game_theory", {"GAME_VERIFY": {
        "row_payoff_A": [[3, 0], [5, 1]], "col_payoff_B": [[3, 5], [0, 1]],
        "profile": [0, 0], "claimed_is_nash": True}})
    assert _find(notnash, "game_theory.nash_pure").status == "MISMATCH"
    assert run_for_domain("game_theory", {})[0].status == "NOT_APPLICABLE"


def test_archaeology_radiocarbon():
    # a quarter of the C-14 remains -> two half-lives -> ~11460 years
    ok = run_for_domain("archaeology", {"ARCH_VERIFY": {
        "fraction_remaining": 0.25, "claimed_age_years": 11460}})
    assert _find(ok, "archaeology.radiocarbon").status == "CONFIRMED"
    bad = run_for_domain("archaeology", {"ARCH_VERIFY": {
        "fraction_remaining": 0.25, "claimed_age_years": 5000}})
    assert _find(bad, "archaeology.radiocarbon").status == "MISMATCH"
    hl = run_for_domain("archaeology", {"ARCH_VERIFY": {
        "fraction_for_halflives": 0.125, "claimed_half_lives": 3}})
    assert _find(hl, "archaeology.half_lives_elapsed").status == "CONFIRMED"
    assert run_for_domain("archaeology", {})[0].status == "NOT_APPLICABLE"
