"""Unit-pin the acoustics verifier (A2: verifier test-depth, 2026-10-06).
v = f*lambda (343 = 343*1); harmonic n*f0 (3*100 = 300). Wrong claim caught; missing field NOT_APPLICABLE.
"""
from __future__ import annotations

from concordance.verifiers import acoustics as A


def test_wave_relation():
    assert A.verify_wave_relation({"speed_of_wave": 343, "frequency_hz": 343, "wavelength_m": 1.0}).status == "CONFIRMED"
    assert A.verify_wave_relation({"speed_of_wave": 343, "frequency_hz": 343, "wavelength_m": 2.0}).status == "MISMATCH"
    assert A.verify_wave_relation({}).status == "NOT_APPLICABLE"


def test_harmonic_frequency():
    assert A.verify_harmonic_frequency({"fundamental_hz": 100, "harmonic_n": 3, "claimed_harmonic_hz": 300}).status == "CONFIRMED"
    assert A.verify_harmonic_frequency({"fundamental_hz": 100, "harmonic_n": 3, "claimed_harmonic_hz": 250}).status == "MISMATCH"
    assert A.verify_harmonic_frequency({}).status == "NOT_APPLICABLE"
