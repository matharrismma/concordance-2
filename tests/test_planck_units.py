"""The Planck units — the one place h, G and c (and k_B) make a number together (2026-10-02, Matt:
"can we build a planck-length verifier?"). Pinned to CODATA 2018: every value is computed from the
constant table, never a literal, so a drift in the table would show here first.
"""
import math

from concordance.verifiers import run_for_domain, physics, planck_scale as P

# CODATA 2018 (the uncertainty comes from G at 2.2e-5; everything else is exact)
L_P, T_P, M_P = 1.616255e-35, 5.391247e-44, 2.176434e-8
E_P_J, E_P_GEV, TEMP_P = 1.956081e9, 1.220890e19, 1.416784e32


def test_planck_length_from_the_constant_table():
    assert abs(P.planck_length_m() - L_P) / L_P < 2e-6
    r = physics.verify_planck_units({"claimed_planck_length_m": L_P})
    assert r.status == "CONFIRMED", r
    assert physics.verify_planck_units({"claimed_planck_length_m": 1.616255e-34}).status == "MISMATCH"  # 10x off


def test_all_five_units_confirm_codata():
    r = physics.verify_planck_units({
        "claimed_planck_length_m": L_P, "claimed_planck_time_s": T_P, "claimed_planck_mass_kg": M_P,
        "claimed_planck_energy_J": E_P_J, "claimed_planck_energy_gev": E_P_GEV,
        "claimed_planck_temperature_k": TEMP_P})
    assert r.status == "CONFIRMED", r
    assert r.data["h"] == 6.62607015e-34 and r.data["G"] == 6.67430e-11 and r.data["c"] == 299792458.0


def test_the_identities_hold_exactly():
    c = 299792458.0
    assert math.isclose(P.planck_length_m(), c * P.planck_time_s(), rel_tol=1e-12)          # l_P = c t_P
    assert math.isclose(P.planck_energy_J(), P.planck_mass_kg() * c * c, rel_tol=1e-12)     # E_P = m_P c^2
    assert math.isclose(P.planck_temperature_K() * 1.380649e-23, P.planck_energy_J(), rel_tol=1e-12)


def test_one_wrong_value_among_right_ones_is_a_mismatch():
    r = physics.verify_planck_units({"claimed_planck_length_m": L_P, "claimed_planck_mass_kg": 2.176434e-7})
    assert r.status == "MISMATCH" and "m_P" in r.detail and "l_P" not in r.detail, r


def test_tolerance_can_only_tighten():
    # a 1% claim with a requested 10% window: the clamp keeps the 1e-3 default, so it must not confirm
    assert physics.verify_planck_units({"claimed_planck_length_m": 1.60e-35,
                                        "tolerance_relative": 0.1}).status == "MISMATCH"
    # and a caller may tighten: a 7-digit claim fails a 1e-9 window honestly
    assert physics.verify_planck_units({"claimed_planck_length_m": L_P,
                                        "tolerance_relative": 1e-9}).status == "MISMATCH"


def test_dispatch_from_the_physics_packet():
    rs = run_for_domain("physics", {"PHYS_VERIFY": {"claimed_planck_length_m": L_P}})
    assert any(r.name == "physics.planck_units" and r.status == "CONFIRMED" for r in rs), rs
    assert physics.verify_planck_units({}).status == "NOT_APPLICABLE"
    assert physics.verify_planck_units({"claimed_planck_length_m": "tiny"}).status == "ERROR"
