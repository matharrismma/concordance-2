"""The Smith chart in its literal domain — the handoff's first-journey fixture (2026-10-02): Z0 = 50 Ω,
Z = 50 + j50 Ω → z = 1 + j → Γ = 0.2 + 0.4j; the inverse returns the load; a series −j50 Ω reaches the
centre. The map is a Möbius transform the Atlas already names (mobius_conformal / smith_reflection)."""
import math

from concordance.verifiers import run_for_domain, electrical as E

FIX = {"z0_ohm": 50, "z_real_ohm": 50, "z_imag_ohm": 50}


def test_the_handoff_fixture_maps_and_inverts():
    r = E.verify_reflection_coefficient({**FIX, "claimed_gamma_real": 0.2, "claimed_gamma_imag": 0.4,
                                         "claimed_gamma_mag": math.sqrt(0.2), "claimed_vswr": (1 + math.sqrt(0.2)) / (1 - math.sqrt(0.2)),
                                         "claimed_return_loss_db": -20 * math.log10(math.sqrt(0.2))})
    assert r.status == "CONFIRMED", r
    assert r.data["inverse_holds"] and r.data["to_centre_series_reactance_ohm"] == -50   # the one permitted move to the centre
    assert r.data["z_normalized"] == [1.0, 1.0]


def test_the_centre_is_a_match_and_the_edge_is_total_reflection():
    centre = E.verify_reflection_coefficient({"z0_ohm": 50, "z_real_ohm": 50, "z_imag_ohm": 0, "claimed_gamma_mag": 0.0})
    assert centre.status == "CONFIRMED" and centre.data["vswr"] == 1.0, centre
    short = E.verify_reflection_coefficient({"z0_ohm": 50, "z_real_ohm": 0, "z_imag_ohm": 0, "claimed_gamma_real": -1})
    assert short.status == "CONFIRMED" and short.data["gamma_mag"] == 1.0, short          # a short: Γ = −1, VSWR unbounded
    pure_x = E.verify_reflection_coefficient({"z0_ohm": 50, "z_real_ohm": 0, "z_imag_ohm": 75, "claimed_gamma_mag": 1.0})
    assert pure_x.status == "CONFIRMED", pure_x                                            # any pure reactance sits on the rim


def test_wrong_claims_mismatch_and_bad_loads_error():
    assert E.verify_reflection_coefficient({**FIX, "claimed_gamma_real": 0.4, "claimed_gamma_imag": 0.2}).status == "MISMATCH"  # swapped
    assert E.verify_reflection_coefficient({**FIX, "claimed_vswr": 1.0}).status == "MISMATCH"
    assert E.verify_reflection_coefficient({"z0_ohm": 0, "z_real_ohm": 50, "claimed_gamma_mag": 0}).status == "ERROR"      # no reference
    assert E.verify_reflection_coefficient({"z0_ohm": 50, "z_real_ohm": -10, "claimed_gamma_mag": 0}).status == "ERROR"    # active load: outside the disk
    assert E.verify_reflection_coefficient({"z0_ohm": 50, "z_real_ohm": "fifty", "claimed_gamma_mag": 0}).status == "ERROR"
    assert E.verify_reflection_coefficient({"z0_ohm": 50, "z_real_ohm": 50}).status == "NOT_APPLICABLE"                  # no claim


def test_tolerance_tightens_only_and_dispatch():
    assert E.verify_reflection_coefficient({**FIX, "claimed_gamma_real": 0.21, "tolerance_relative": 0.5}).status == "MISMATCH"
    rs = run_for_domain("electrical", {"ELEC_VERIFY": {**FIX, "claimed_gamma_real": 0.2, "claimed_gamma_imag": 0.4}})
    assert any(r.name == "electrical.reflection_coefficient" and r.status == "CONFIRMED" for r in rs), rs
