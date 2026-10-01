"""Alpha-anchored domain checks — closing the gap.

The fine structure constant governs a family of domains (see physical_constants.alpha_governance),
but their verifiers did not compute THROUGH alpha. This suite pins the checks added to close that
gap: each is a real, exact quantity computed from the one constant source and anchored in alpha.

  * condensed_matter.quantum_hall — R_K = h/e^2 = mu_0 c / (2 alpha); K_J = 2e/h; R_H = R_K/nu

Runnable with pytest OR `python tests/test_alpha_anchored_checks.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.verifiers import condensed_matter as CM  # noqa: E402
from concordance.verifiers import atomic as AT  # noqa: E402
from concordance.verifiers import periodic_table as PT  # noqa: E402
from concordance.verifiers import optics as OP  # noqa: E402
from concordance.verifiers import photonics as PH  # noqa: E402
from concordance.verifiers import chemistry as CH  # noqa: E402
from concordance.verifiers import electrochemistry as EC  # noqa: E402
from concordance.verifiers import astronomy as AS  # noqa: E402 — the pattern generalized to G
from concordance.verifiers import grav_scale as GS  # noqa: E402
from concordance.verifiers import physics as PHY  # noqa: E402 — and to c
from concordance.verifiers import nuclear_physics as NUC  # noqa: E402
from concordance.verifiers import thermodynamics as TH  # noqa: E402 — and to k_B
from concordance.verifiers import meteorology as MET  # noqa: E402
from concordance.verifiers import materials_science as MAT  # noqa: E402
from concordance.verifiers import quantum_computing as QC  # noqa: E402 — and to h


def test_von_klitzing_from_h_e_and_the_alpha_identity():
    r = CM.verify_quantum_hall({"claimed_von_klitzing_ohm": 25812.807})
    assert r.status == "CONFIRMED", r
    # R_K = h/e^2 ~ 25812.807 ohm
    assert abs(r.data["von_klitzing_ohm"] - 25812.807) < 1.0
    # the alpha identity holds: h/e^2 == mu_0 c / (2 alpha) to the table's consistency
    rk, rka = r.data["von_klitzing_ohm"], r.data["R_K_from_alpha_ohm"]
    assert abs(rk - rka) / rk < 1e-6


def test_josephson_constant():
    r = CM.verify_quantum_hall({"claimed_josephson_ghz_per_v": 483597.8})
    assert r.status == "CONFIRMED", r
    assert abs(r.data["josephson_ghz_per_v"] - 483597.8) < 1.0


def test_hall_plateau_at_filling_two():
    r = CM.verify_quantum_hall({"filling_factor": 2, "claimed_hall_resistance_ohm": 12906.4})
    assert r.status == "CONFIRMED", r


def test_wrong_resistance_mismatches():
    assert CM.verify_quantum_hall({"claimed_von_klitzing_ohm": 26000.0}).status == "MISMATCH"


def test_routes_and_stays_quiet_when_absent():
    res = CM.run({"CONDMAT_VERIFY": {"claimed_von_klitzing_ohm": 25812.807}})
    assert any(x.name == "condensed_matter.quantum_hall" and x.status == "CONFIRMED" for x in res), res
    empty = CM.run({})
    assert empty and all(x.status == "NOT_APPLICABLE" for x in empty), empty
    unrel = CM.run({"TOTALLY_UNRELATED_XYZ": {"claimed_von_klitzing_ohm": 25812.807}})
    assert not any(x.status in ("CONFIRMED", "MISMATCH") for x in unrel), unrel


def test_atomic_energy_levels_and_lines():
    assert AT.verify_energy_level({"level_n": 1, "claimed_energy_level_eV": -13.6057}).status == "CONFIRMED"
    # He+ (Z=2) ground state = -54.42 eV
    assert AT.verify_energy_level({"level_n": 1, "level_Z": 2,
                                   "claimed_energy_level_eV": -54.42}).status == "CONFIRMED"
    # Balmer-alpha line (n=3 -> 2) at ~656.1 nm
    assert AT.verify_energy_level({"line_lower": 2, "line_upper": 3,
                                   "claimed_line_nm": 656.1}).status == "CONFIRMED"
    assert AT.verify_energy_level({"level_n": 1, "claimed_energy_level_eV": -10.0}).status == "MISMATCH"


def test_atomic_fine_structure_and_g2_anomaly():
    # a_e = alpha/2pi ~ 0.0011614; the measured 0.00115965 agrees to ~0.2% (leading QED)
    assert AT.verify_fine_structure({"claimed_g2_anomaly": 0.00115965}).status == "CONFIRMED"
    # the fine-structure energy scale alpha^2 Ry ~ 7.24e-4 eV
    assert AT.verify_fine_structure({"claimed_fine_structure_scale_ev": 7.24e-4}).status == "CONFIRMED"
    assert AT.verify_fine_structure({"claimed_g2_anomaly": 0.01}).status == "MISMATCH"


def test_moseley_k_alpha():
    # Cu K-alpha ~ 8048 eV (Moseley approximation, looser tolerance)
    assert PT.verify_moseley({"moseley_Z": 29, "claimed_k_alpha_ev": 8048}).status == "CONFIRMED"
    assert PT.verify_moseley({"moseley_Z": 29, "claimed_k_alpha_ev": 5000}).status == "MISMATCH"


def test_optics_light_matter_scale():
    assert OP.verify_light_matter_scale({"claimed_classical_electron_radius_m": 2.8179e-15}).status == "CONFIRMED"
    assert OP.verify_light_matter_scale({"claimed_thomson_cross_section_m2": 6.6524e-29}).status == "CONFIRMED"
    assert OP.verify_light_matter_scale({"claimed_classical_electron_radius_m": 3.0e-15}).status == "MISMATCH"


def test_photonics_compton():
    assert PH.verify_compton({"claimed_compton_wavelength_m": 2.4263e-12}).status == "CONFIRMED"
    # shift at 90 deg = lambda_C (1 - cos 90) = lambda_C
    assert PH.verify_compton({"compton_angle_deg": 90, "claimed_compton_shift_m": 2.4263e-12}).status == "CONFIRMED"


def test_chemistry_atomic_energy_scale():
    assert CH.verify_atomic_energy_scale({"claimed_hartree_ev": 27.2114}).status == "CONFIRMED"
    assert CH.verify_atomic_energy_scale({"claimed_rydberg_ev": 13.6057}).status == "CONFIRMED"


def test_electrochemistry_faraday_and_nernst():
    assert EC.verify_faraday_constant({"claimed_faraday_c_per_mol": 96485.33}).status == "CONFIRMED"
    assert EC.verify_faraday_constant({"nernst_temperature_k": 298.15,
                                       "claimed_thermal_voltage_v": 0.025693}).status == "CONFIRMED"


def test_every_governed_domain_routes_through_run_and_stays_quiet_when_absent():
    routed = {
        AT: ("ATOM_VERIFY", {"level_n": 1, "claimed_energy_level_eV": -13.6057}),
        PT: ("PT_VERIFY", {"moseley_Z": 29, "claimed_k_alpha_ev": 8048}),
        OP: ("OPT_VERIFY", {"claimed_thomson_cross_section_m2": 6.6524e-29}),
        PH: ("PHOT_VERIFY", {"claimed_compton_wavelength_m": 2.4263e-12}),
        CH: ("CHEM_VERIFY", {"claimed_hartree_ev": 27.2114}),
        EC: ("ECHEM_VERIFY", {"claimed_faraday_c_per_mol": 96485.33}),
        CM: ("CONDMAT_VERIFY", {"claimed_von_klitzing_ohm": 25812.807}),
    }
    for mod, (key, art) in routed.items():
        res = mod.run({key: art})
        assert any(x.status == "CONFIRMED" for x in res), (mod.__name__, res)
        empty = mod.run({})
        assert empty and all(x.status == "NOT_APPLICABLE" for x in empty), (mod.__name__, empty)


def test_G_remaining_domains_through_G():
    import concordance.verifiers.geology as GEO
    import concordance.verifiers.ephemeris as EPH
    # Newton's gravitation: Earth-Moon force ~ 1.98e20 N
    rp = PHY.run({"PHYS_VERIFY": {"grav_mass_1_kg": 5.972e24, "grav_mass_2_kg": 7.342e22,
                                  "grav_separation_m": 3.844e8, "claimed_gravitational_force_N": 1.98e20}})
    assert any(x.name == "physics.gravitation" and x.status == "CONFIRMED" for x in rp), rp
    # surface gravity of Earth ~ 9.82 m/s^2
    rg = GEO.run({"GEO_VERIFY": {"surface_gravity_mass_kg": 5.972e24, "surface_gravity_radius_m": 6.371e6,
                                 "claimed_surface_gravity_m_s2": 9.82}})
    assert any(x.name == "geology.surface_gravity" and x.status == "CONFIRMED" for x in rg), rg
    # Earth's orbital period ~ 3.156e7 s (1 year) via Kepler's third law
    re = EPH.run({"EPH_VERIFY": {"orbit_semi_major_m": 1.496e11, "orbit_central_mass_kg": 1.989e30,
                                 "claimed_orbital_period_s": 3.156e7}})
    assert any(x.name == "ephemeris.orbital_period" and x.status == "CONFIRMED" for x in re), re


def test_gravitational_scale_through_G_the_pattern_generalizes():
    # Earth escape velocity ~ 11.186 km/s, computed through G
    assert AS.verify_gravitational_scale({"escape_mass_kg": 5.972e24, "escape_radius_m": 6.371e6,
                                          "claimed_escape_velocity_m_s": 11186}).status == "CONFIRMED"
    # Sun Schwarzschild radius ~ 2954 m = 2 G M / c^2
    assert AS.verify_gravitational_scale({"schwarzschild_mass_kg": 1.989e30,
                                          "claimed_schwarzschild_radius_m": 2954}).status == "CONFIRMED"
    assert AS.verify_gravitational_scale({"escape_mass_kg": 5.972e24, "escape_radius_m": 6.371e6,
                                          "claimed_escape_velocity_m_s": 8000}).status == "MISMATCH"
    # routes through run, quiet when absent
    res = AS.run({"ASTRO_VERIFY": {"schwarzschild_mass_kg": 1.989e30,
                                   "claimed_schwarzschild_radius_m": 2954}})
    assert any(x.name == "astronomy.gravitational_scale" and x.status == "CONFIRMED" for x in res), res
    assert 2900 < GS.schwarzschild_radius_m(1.989e30) < 3000


def test_speed_of_light_domains_through_c():
    # E = m c^2: electron rest energy ~ 8.187e-14 J
    assert PHY.verify_mass_energy({"rest_mass_kg": 9.1093837015e-31,
                                   "claimed_rest_energy_J": 8.1871e-14}).status == "CONFIRMED"
    # Lorentz factor at 0.6c = 1.25
    assert PHY.verify_mass_energy({"lorentz_velocity_m_per_s": 1.798754748e8,
                                   "claimed_lorentz_factor": 1.25}).status == "CONFIRMED"
    assert PHY.verify_mass_energy({"rest_mass_kg": 9.1093837015e-31,
                                   "claimed_rest_energy_J": 1e-13}).status == "MISMATCH"
    # nuclear rest energy: 1 amu = 931.494 MeV (the mass-energy behind binding energies)
    rn = NUC.run({"NUCLEAR_VERIFY": {"rest_mass_amu": 1.0, "claimed_rest_energy_MeV": 931.494}})
    assert any(x.name == "nuclear_physics.rest_energy" and x.status == "CONFIRMED" for x in rn), rn
    # astronomy light-travel: 1 AU ~ 499 light-seconds
    ra = AS.run({"ASTRO_VERIFY": {"light_distance_m": 1.495978707e11, "claimed_light_time_s": 499.0}})
    assert any(x.name == "astronomy.light_travel" and x.status == "CONFIRMED" for x in ra), ra


def test_boltzmann_constant_domains_through_kB():
    # S = k_B ln 2 ~ 9.57e-24 J/K
    r = TH.run({"THERMO_VERIFY": {"microstates_W": 2, "claimed_entropy_J_per_K": 9.57e-24}})
    assert any(x.name == "thermodynamics.boltzmann_entropy" and x.status == "CONFIRMED" for x in r), r
    # Boltzmann factor exp(-1) = 0.3679 at E = k_B*300, T = 300
    rc = CH.run({"CHEM_VERIFY": {"boltzmann_energy_J": 4.141947e-21, "boltzmann_temperature_K": 300,
                                 "claimed_boltzmann_factor": 0.36788}})
    assert any(x.name == "chemistry.boltzmann_factor" and x.status == "CONFIRMED" for x in rc), rc
    # barometric scale height ~ 8425 m for air (28.97 amu) at 288 K
    rm = MET.run({"MET_VERIFY": {"scale_height_temp_K": 288, "molecular_mass_kg": 4.810582e-26,
                                 "gravity_m_s2": 9.81, "claimed_scale_height_m": 8425}})
    assert any(x.name == "meteorology.scale_height" and x.status == "CONFIRMED" for x in rm), rm
    # thermal energy k_B T = 0.02585 eV at 300 K
    rt = MAT.run({"MAT_VERIFY": {"thermal_temp_K": 300, "claimed_thermal_energy_ev": 0.025852}})
    assert any(x.name == "materials_science.thermal_energy" and x.status == "CONFIRMED" for x in rt), rt


def test_planck_constant_domains_through_h():
    # qubit energy E = h f at 5 GHz = 3.313e-24 J
    r = QC.run({"QCOMP_VERIFY": {"qubit_frequency_hz": 5e9, "claimed_qubit_energy_j": 3.313e-24}})
    assert any(x.name == "quantum_computing.qubit_energy" and x.status == "CONFIRMED" for x in r), r
    # photon energy at 500 nm ~ 2.48 eV, and at 5e14 Hz ~ 2.068 eV
    rp = PH.run({"PHOT_VERIFY": {"photon_wavelength_m": 500e-9, "claimed_photon_energy_ev": 2.48}})
    assert any(x.name == "photonics.photon_energy" and x.status == "CONFIRMED" for x in rp), rp
    rp2 = PH.run({"PHOT_VERIFY": {"photon_frequency_hz": 5e14, "claimed_photon_energy_ev": 2.0678}})
    assert any(x.name == "photonics.photon_energy" and x.status == "CONFIRMED" for x in rp2), rp2


def test_avogadro_constant_domains_through_NA():
    # N = 1 mol * N_A = 6.022e23
    rc = CH.run({"CHEM_VERIFY": {"amount_mol": 1.0, "claimed_particle_count": 6.02214076e23}})
    assert any(x.name == "chemistry.avogadro_count" and x.status == "CONFIRMED" for x in rc), rc
    # R = N_A k_B = 8.314462618 J/(mol K)
    rt = TH.run({"THERMO_VERIFY": {"claimed_gas_constant_j_per_mol_k": 8.314462618}})
    assert any(x.name == "thermodynamics.gas_constant" and x.status == "CONFIRMED" for x in rt), rt
    # electrochemistry's Faraday F = N_A e already computes through N_A
    re = EC.run({"ECHEM_VERIFY": {"claimed_faraday_c_per_mol": 96485.33}})
    assert any("faraday" in x.name and x.status == "CONFIRMED" for x in re), re


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} alpha-anchored checks passed.")
