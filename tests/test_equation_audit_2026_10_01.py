"""Pins from the Fable equation audit (2026-10-01): every verify_* law in the physics core was
read against its textbook form and CODATA 2018. Two were WRONG (a false verdict was reachable),
six were sloppy. Each pin below is the exact packet that exposed the hole, kept so the hole
stays closed. No test anywhere referenced v_source_mps or claimed_drop_pct before this file —
the two WRONG findings lived in unpinned branches.
"""
import math

from concordance.verifiers import acoustics, photonics, energy, thermodynamics, nuclear_physics
from concordance.verifiers import physics, astronomy


# ── WRONG 1: acoustics.doppler_shift — source sign contradicted its own convention ────────
# Docstring: "positive velocities are toward the other party (closing)". The shipped formula
# (c + v_obs)/(c + v_src) is the textbook form for v_src > 0 = RECEDING, so an approaching
# source's true pitch was rejected and the receding pitch confirmed. Fixed to (c − v_src).

def _dop(v_obs, v_src, claim):
    return acoustics.verify_doppler_shift({
        "f_source_hz": 440, "v_observer_mps": v_obs, "v_source_mps": v_src,
        "speed_medium_mps": 343, "claimed_f_observed_hz": claim})


def test_doppler_approaching_source_is_heard_higher():
    r = _dop(0, +10, 440 * 343 / 333)  # 453.21 Hz
    assert r.status == "CONFIRMED", r
    assert _dop(0, +10, 440 * 343 / 353).status == "MISMATCH"  # 427.54 was the old false CONFIRM


def test_doppler_receding_source_is_heard_lower():
    assert _dop(0, -10, 440 * 343 / 353).status == "CONFIRMED"


def test_doppler_observer_term_unchanged_and_mach_one_source_is_an_error():
    assert _dop(+10, 0, 440 * 353 / 343).status == "CONFIRMED"  # the module docstring example
    assert _dop(0, 343, 1.0).status == "ERROR"  # source closing at the wave speed: no finite pitch


# ── WRONG 2: energy.wire_voltage_drop — a %-only claim fell through to CONFIRM ───────────
# With claimed_drop_pct but no system_V_for_drop, actual_pct was None, the pct branch was
# skipped, and the function reached the trailing confirm having compared nothing.

_WIRE = {"wire_resistance_ohm_per_m": 0.0033, "distance_m": 10, "current_A": 30}


def test_wire_drop_pct_claim_without_system_voltage_is_not_confirmed():
    r = energy.verify_wire_voltage_drop({**_WIRE, "claimed_drop_pct": 0.1})
    assert r.status == "NOT_APPLICABLE", r


def test_wire_drop_pct_claim_with_system_voltage_is_actually_checked():
    # Vdrop = 2·30·0.0033·10 = 1.98 V = 16.5 % of 12 V
    ok = energy.verify_wire_voltage_drop({**_WIRE, "system_V_for_drop": 12, "claimed_drop_pct": 16.5})
    bad = energy.verify_wire_voltage_drop({**_WIRE, "system_V_for_drop": 12, "claimed_drop_pct": 0.1})
    assert ok.status == "CONFIRMED", ok
    assert bad.status == "MISMATCH", bad


# ── SLOPPY: photonics.fiber_loss tolerance was relative to the dBm figure ─────────────────
# dBm is a log scale; the window must be an absolute dB width (0.1 dB, as decibel_ratio does).

def test_fiber_loss_uses_an_absolute_db_window():
    base = {"input_power_dbm": -70, "attenuation_db_per_km": 0.2, "length_km": 50}  # → −80 dBm
    assert photonics.verify_fiber_loss({**base, "claimed_output_dbm": -80.05}).status == "CONFIRMED"
    assert photonics.verify_fiber_loss({**base, "claimed_output_dbm": -80.5}).status == "MISMATCH"  # was CONFIRMED


# ── SLOPPY: zero-valued true results could not be confirmed (compare() refuses actual == 0) ──

def test_compton_zero_angle_has_zero_shift():
    assert photonics.verify_compton({"compton_angle_deg": 0, "claimed_compton_shift_m": 0}).status == "CONFIRMED"
    assert photonics.verify_compton({"compton_angle_deg": 0, "claimed_compton_shift_m": 2.4e-12}).status == "MISMATCH"
    r = photonics.verify_compton({"compton_angle_deg": 90, "claimed_compton_shift_m": 2.4263e-12})
    assert r.status == "CONFIRMED", r


def test_boltzmann_entropy_of_one_microstate_is_zero():
    assert thermodynamics.verify_boltzmann_entropy({"microstates_W": 1, "claimed_entropy_J_per_K": 0}).status == "CONFIRMED"
    assert thermodynamics.verify_boltzmann_entropy({"microstates_W": 1, "claimed_entropy_J_per_K": 1e-23}).status == "MISMATCH"


# ── SLOPPY: constants — R and u→MeV were rounded while the same files confirm the exact ones ──

def test_thermodynamics_uses_the_exact_gas_constant():
    assert abs(thermodynamics._R - 8.314462618) < 1e-8
    r = thermodynamics.verify_ideal_gas_law({
        "pressure_Pa": 101325, "volume_m3": 0.0224, "moles": 1.0, "temperature_K": 273.15,
        "claimed_pressure_Pa": 8.314462618 * 273.15 / 0.0224, "tolerance_relative": 1e-6})
    assert r.status == "CONFIRMED", r  # a caller tightening below 5.6e-5 used to reject the exact value


def test_binding_energy_uses_codata_u_to_mev():
    assert abs(nuclear_physics._AMU_TO_MEV - 931.49410242) < 1e-6
    r = nuclear_physics.verify_binding_energy_per_nucleon({
        "mass_defect_amu": 0.5284, "nucleon_count": 56, "claimed_binding_energy_MeV_per_nucleon": 8.79})
    assert r.status == "CONFIRMED", r  # Fe-56, the real mass defect (the old docstring example had 0.0988 u)


# ── SLOPPY: v = c raised instead of returning a verdict ───────────────────────────────────

def test_lorentz_factor_at_c_is_an_error_verdict_not_a_crash():
    r = physics.verify_mass_energy({"lorentz_velocity_m_per_s": 299792458.0, "claimed_lorentz_factor": 1e9})
    assert r.status == "ERROR", r
    assert physics.verify_mass_energy({"lorentz_velocity_m_per_s": 0.6 * 299792458.0,
                                       "claimed_lorentz_factor": 1.25}).status == "CONFIRMED"


# ── SLOPPY: distance-modulus 0.5 pc absolute floor was a 38 % window at Proxima ──────────

def test_distance_modulus_floor_no_longer_swallows_nearby_stars():
    prox = {"apparent_magnitude": 11.13, "absolute_magnitude": 15.6}  # d = 1.28 pc
    assert astronomy.verify_distance_modulus({**prox, "claimed_distance_parsec": 1.30}).status == "CONFIRMED"
    assert astronomy.verify_distance_modulus({**prox, "claimed_distance_parsec": 1.75}).status == "MISMATCH"  # was CONFIRMED


# ── docstring examples must pass their own verifier ───────────────────────────────────────

def test_corrected_docstring_examples_pass():
    assert photonics.verify_electro_optic_vpi({"wavelength_m": 1.55e-6, "gap_m": 1e-5, "index": 2.2,
                                               "eo_coefficient_m_per_v": 3.1e-11, "length_m": 0.02,
                                               "claimed_vpi_v": 2.35}).status == "CONFIRMED"
    assert photonics.verify_grating_angle({"wavelength_m": 1.55e-6, "grating_period_m": 3.0e-6, "order": 1,
                                           "claimed_angle_deg": 31.1}).status == "CONFIRMED"
    assert photonics.verify_beer_lambert({"input_intensity": 1.0, "coefficient_per_m": 200.0,
                                          "path_length_m": 0.001, "claimed_output_intensity": 0.8187}).status == "CONFIRMED"
    assert photonics.verify_beer_lambert({"input_intensity": 1.0, "coefficient_per_m": 200.0,
                                          "length_m2": 0.001, "claimed_output_intensity": 0.8187}).status == "CONFIRMED"  # legacy key
    assert astronomy.verify_gravitational_force({"mass_1_kg": 5.972e24, "mass_2_kg": 7.342e22, "separation_m": 3.84e8,
                                                 "claimed_gravitational_force_N": 1.985e20}).status == "CONFIRMED"
