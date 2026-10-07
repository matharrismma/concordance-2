"""Unit-pin the physics verifier (A2, 2026-10-06). Newton F=ma (2kg*3 = 6N); KE = 1/2 m v^2
(1/2 * 2 * 3^2 = 9 J)."""
from __future__ import annotations
from concordance.verifiers import physics as PH


def test_newtons_second_law():
    assert PH.verify_newtons_second_law({"mass_kg": 2, "acceleration_m_per_s2": 3, "claimed_force_N": 6}).status == "CONFIRMED"
    assert PH.verify_newtons_second_law({"mass_kg": 2, "acceleration_m_per_s2": 3, "claimed_force_N": 10}).status == "MISMATCH"
    assert PH.verify_newtons_second_law({}).status == "NOT_APPLICABLE"


def test_kinetic_energy_basic():
    assert PH.verify_kinetic_energy_basic({"mass_kg": 2, "velocity_m_per_s": 3, "claimed_kinetic_energy_J": 9}).status == "CONFIRMED"
    assert PH.verify_kinetic_energy_basic({"mass_kg": 2, "velocity_m_per_s": 3, "claimed_kinetic_energy_J": 12}).status == "MISMATCH"
