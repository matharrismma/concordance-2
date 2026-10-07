"""Unit-pin the photonics verifier (A2, 2026-10-06). Photon energy E = hc/lambda; 500 nm -> ~2.48 eV.
Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import photonics as PN


def test_photon_energy():
    assert PN.verify_photon_energy({"photon_wavelength_m": 500e-9, "claimed_photon_energy_ev": 2.48}).status == "CONFIRMED"
    assert PN.verify_photon_energy({"photon_wavelength_m": 500e-9, "claimed_photon_energy_ev": 5.0}).status == "MISMATCH"
    assert PN.verify_photon_energy({}).status == "NOT_APPLICABLE"
