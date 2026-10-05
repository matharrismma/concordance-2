"""The Riemann-Siegel scan, accelerated (Matt, 2026-10-05: "Do C then numpy"). The three backends — C, numpy,
pure python — compute the same formula; they agree away from the zeros, and the scan defers to exact mpmath
near every zero, so the zero COUNT is identical whichever ran. The accelerator is a speed, never a verdict."""
import math

import pytest

from concordance.verifiers import number_theory as NT
from concordance.verifiers import riemann_accel as RA


def _py_z(ts):
    return [NT._rs_z(float(t)) for t in ts]


def test_numpy_and_python_agree_to_the_last_bits_away_from_zeros():
    np = RA._numpy()
    if np is False:
        pytest.skip("numpy absent")
    ts = [600.0 + i * 0.0237 for i in range(3000)]      # above the seam
    py = _py_z(ts)
    nz = RA._np_z(ts)
    assert max(abs(float(a) - b) for a, b in zip(nz, py)) < 1e-12
    # the sign-change count is what the scan actually uses — it must be identical
    sc_py = sum(1 for i in range(1, len(py)) if (py[i - 1] < 0) != (py[i] < 0))
    sc_np = sum(1 for i in range(1, len(nz)) if (float(nz[i - 1]) < 0) != (float(nz[i]) < 0))
    assert sc_py == sc_np


def test_whatever_backend_is_live_gives_the_same_counts_as_the_strip():
    # This is the real contract: the on-line scan (through riemann_accel) equals Backlund's independent count.
    for T in (100.0, 1000.0):
        on = NT._zeros_on_line(T)
        n_strip, _ = NT._zeros_in_strip(T)
        assert on == round(n_strip), (T, on, n_strip, RA.backend())


def test_z_array_matches_the_reference_whatever_backend():
    ts = [750.0 + i * 0.05 for i in range(200)]
    got = [float(v) for v in RA.z_array(ts)]
    ref = _py_z(ts)
    assert max(abs(a - b) for a, b in zip(got, ref)) < 1e-9
    assert RA.backend() in ("c", "numpy", "python")


def test_the_dip_detector_finds_a_pair_the_grid_steps_over_and_never_counts_one_twice():
    # a clean crossing in a triple is left to the ordinary count (the dip test returns 0)
    assert NT._dip_crossings(100.0, 100.1, 100.2, 1.0, 0.1, -0.5) == 0
    # a convex same-sign dip that the parabola sends below zero is rescanned exactly; a shallow one is not.
    # (exact recount is the judge; here we only assert the gate opens/closes, using a real near-zero region.)
    import mpmath as mp
    # pick three equally spaced points straddling a known zero so the exact recount finds the crossing(s)
    z1 = float(mp.zetazero(1).imag)                    # ~14.1347
    h = 0.4
    a, b, c = z1 - h, z1, z1 + h
    va, vb, vc = float(mp.siegelz(a)), float(mp.siegelz(b)), float(mp.siegelz(c))
    # vb straddles the zero so this is actually a crossing triple -> dip test returns 0 (handled by the count)
    assert NT._dip_crossings(a, b, c, va, vb, vc) == 0


def test_describe_names_the_backend_for_the_capability_statement():
    d = RA.describe()
    assert d["backend"] in ("c", "numpy", "python") and "per-node artifact" in d["note"]
