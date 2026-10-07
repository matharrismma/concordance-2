"""Unit-pin the optics verifier (A2: verifier test-depth, 2026-10-06).
Snell's law (n1 sin th1 = n2 sin th2; 1*sin30 = 1.5*sin(19.47)); photon energy E = h*f (f=5e14 ->
~3.313e-19 J). Wrong claim caught; missing field NOT_APPLICABLE.
"""
from __future__ import annotations

from concordance.verifiers import optics as O


def test_snell_law():
    assert O.verify_snell_law({"n1": 1.0, "n2": 1.5, "theta1_deg": 30, "claimed_theta2_deg": 19.47}).status == "CONFIRMED"
    assert O.verify_snell_law({"n1": 1.0, "n2": 1.5, "theta1_deg": 30, "claimed_theta2_deg": 25.0}).status == "MISMATCH"
    assert O.verify_snell_law({}).status == "NOT_APPLICABLE"


def test_photon_energy():
    assert O.verify_photon_energy({"frequency_hz": 5e14, "claimed_photon_energy_j": 3.313e-19}).status == "CONFIRMED"
    assert O.verify_photon_energy({"frequency_hz": 5e14, "claimed_photon_energy_j": 1.0e-19}).status == "MISMATCH"
    assert O.verify_photon_energy({}).status == "NOT_APPLICABLE"
