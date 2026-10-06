"""Phonons — the quantized lattice vibrations, verified deterministically (Matt, 2026-10-06: "Phonon").

alpha built the atom; phonons are the atom LATTICE in motion. Each relation is canonical solid-state
physics, computed from the attested constants: the energy quantum E=hbar*omega, the Debye cutoff
temperature, the Bose-Einstein occupation, the acoustic sound speed, and the Dulong-Petit ceiling 3R.
CONFIRMED for the right number, MISMATCH for the wrong one — never a guess."""
from concordance.verifiers import condensed_matter as CM
from concordance import verifiers as V


def test_phonon_is_a_registered_domain_routing_to_condensed_matter():
    assert V.VERIFIERS["phonon"] == V.VERIFIERS["condensed_matter"]
    assert V.VERIFIERS["phonons"] == V.VERIFIERS["condensed_matter"]


def test_phonon_energy_quantum():
    r = CM.verify_phonon_energy({"phonon_omega": 1e13, "claimed_phonon_energy_J": 1.054571817e-21})
    assert r.status == "CONFIRMED"
    assert CM.verify_phonon_energy({"phonon_omega": 1e13, "claimed_phonon_energy_J": 2e-21}).status == "MISMATCH"


def test_debye_temperature():
    # theta_D = hbar*omega_D/k_B ; omega_D=1e13 -> ~76.38 K
    r = CM.verify_debye_temperature({"debye_frequency": 1e13, "claimed_debye_temp_K": 76.38})
    assert r.status == "CONFIRMED"
    assert CM.verify_debye_temperature({"debye_frequency": 1e13, "claimed_debye_temp_K": 300.0}).status == "MISMATCH"


def test_phonon_occupation_is_bose_einstein():
    # n = 1/(exp(hbar*omega/k_B T)-1); omega=1e13, T=300 -> ~3.4488
    r = CM.verify_phonon_occupation({"phonon_omega": 1e13, "temperature_K": 300.0, "claimed_occupation": 3.4488})
    assert r.status == "CONFIRMED"
    bad = CM.verify_phonon_occupation({"phonon_omega": 1e13, "temperature_K": 300.0, "claimed_occupation": 1.0})
    assert bad.status == "MISMATCH"


def test_acoustic_sound_velocity():
    # v_s = a*sqrt(K/m); a=3e-10, K=10, m=1e-26 -> ~9486.8 m/s
    r = CM.verify_sound_velocity({"spring_const": 10.0, "atom_mass": 1e-26, "lattice_a": 3e-10,
                                  "claimed_sound_velocity": 9486.8})
    assert r.status == "CONFIRMED"


def test_dulong_petit_ceiling_is_3R():
    r = CM.verify_dulong_petit({"claimed_molar_heat_capacity": 24.94})
    assert r.status == "CONFIRMED"
    assert CM.verify_dulong_petit({"claimed_molar_heat_capacity": 12.0}).status == "MISMATCH"


def test_a_phonon_claim_dispatches_through_the_registry():
    # the whole-packet path: the condensed_matter run() picks the right rule by the keys present
    out = CM.run({"CONDMAT_VERIFY": {"phonon_omega": 1e13, "claimed_phonon_energy_J": 1.054571817e-21}})
    assert out and out[0].status == "CONFIRMED" and "phonon_energy" in out[0].name
