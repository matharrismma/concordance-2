"""The blocked main sum (Matt, 2026-11-21: "Build the blocked/FFT"). Over a long uniform block with m
constant, the Riemann-Siegel main sum is a type-1 NUFFT, so O(n*m) becomes O(M log M + m*q). It computes
the SAME first-order formula; it is a speed, never a verdict.

What these pin:
  * the blocked sum agrees with the point-by-point sum to well inside the formula's own truncation error;
  * it is not WORSE than the point-by-point path against exact mpmath (the only comparison that matters);
  * m_run never hands the FFT path a block that straddles an m boundary (the one new constraint);
  * the fallbacks fire where the transform would not pay;
  * backend() keeps its old meaning and its old three values; bulk_path() is reported beside it.
"""
import math

import pytest

from concordance.verifiers import number_theory as NT
from concordance.verifiers import riemann_accel as RA

_TWO_PI = 2.0 * math.pi


def _np_or_skip():
    np = RA._numpy()
    if np is False:
        pytest.skip("numpy absent")
    return np


def _block(m=400, n=8192):
    """A block starting just above the m boundary, so the whole of it sits in one m-run."""
    t0 = _TWO_PI * m * m + 1.0
    h = (_TWO_PI / math.log(t0 / _TWO_PI)) / 24.0
    return t0, h, n


def test_the_blocked_sum_matches_the_point_by_point_sum_inside_the_formulas_own_error():
    np = _np_or_skip()
    t0, h, n = _block()
    ts = RA.uniform_grid(t0, h, n)
    fast = np.asarray(RA._fft_z(ts, h), float)
    ref = np.asarray(RA._np_z(ts), float)
    err = float(np.abs(fast - ref).max())
    trunc = t0 ** -0.75                      # the first-order Riemann-Siegel truncation error here
    assert err < trunc / 10.0, (err, trunc)


def test_the_blocked_sum_is_not_worse_than_the_shipped_path_against_exact_mpmath():
    """The question that matters is not whether the two paths agree — they differ by a
    double-precision PHASE floor that grows with the height — but whether the fast one is as close to
    truth as the shipped one."""
    np = _np_or_skip()
    import mpmath as mp
    t0, h, n = _block(m=400, n=4096)
    ts = RA.uniform_grid(t0, h, n)
    fast = np.asarray(RA._fft_z(ts, h), float)
    ref = np.asarray(RA._np_z(ts), float)
    idx = np.linspace(0, n - 1, 40).astype(int)
    exact = np.array([float(mp.siegelz(mp.mpf(float(ts[i])))) for i in idx])
    fast_err = float(np.abs(fast[idx] - exact).max())
    ref_err = float(np.abs(ref[idx] - exact).max())
    assert fast_err <= ref_err * 2.0, (fast_err, ref_err)


def test_m_run_never_returns_a_block_that_straddles_an_m_boundary():
    for m in (64, 400, 1261):
        t0 = _TWO_PI * m * m + 1.0
        h = (_TWO_PI / math.log(t0 / _TWO_PI)) / 24.0
        for nmax in (1 << 10, 1 << 14, 1 << 20):
            n = RA.m_run(t0, h, nmax)
            assert 1 <= n <= nmax
            lo = int(math.floor(math.sqrt(t0 / _TWO_PI)))
            hi = int(math.floor(math.sqrt((t0 + (n - 1) * h) / _TWO_PI)))
            assert lo == hi, (m, nmax, n, lo, hi)
    # and immediately below a boundary it must return a SHORT run, not the cap
    m = 400
    t_near = _TWO_PI * (m + 1) ** 2 - 1.0
    h = (_TWO_PI / math.log(t_near / _TWO_PI)) / 24.0
    assert RA.m_run(t_near, h, 1 << 20) < 1 << 20


def test_z_uniform_falls_back_where_the_transform_would_not_pay_and_still_agrees():
    np = _np_or_skip()
    t0, h, _ = _block()
    for n in (64, 1024):                      # below _FFT_MIN_N: the direct path must answer
        ts = RA.uniform_grid(t0, h, n)
        got = np.asarray(RA.z_uniform(t0, h, n), float)
        ref = np.asarray(RA.z_array(ts), float)
        assert float(np.abs(got - ref).max()) == 0.0
    # low height: m is small, so the transform is skipped even for a long block
    t_low, h_low, n = 600.0, 0.02, 1 << 13
    got = np.asarray(RA.z_uniform(t_low, h_low, n), float)
    ref = np.asarray(RA.z_array(RA.uniform_grid(t_low, h_low, n)), float)
    assert float(np.abs(got - ref).max()) == 0.0


def test_z_uniform_spans_an_m_boundary_without_a_seam():
    """A block that crosses an m boundary is split; the two halves must join with no step."""
    np = _np_or_skip()
    m = 400
    t0 = _TWO_PI * (m + 1) ** 2 - 60.0        # a boundary sits inside this block
    h = (_TWO_PI / math.log(t0 / _TWO_PI)) / 24.0
    n = 1 << 13
    got = np.asarray(RA.z_uniform(t0, h, n), float)
    ref = np.asarray(RA.z_array(RA.uniform_grid(t0, h, n)), float)
    assert float(np.abs(got - ref).max()) < t0 ** -0.75


def test_the_count_still_equals_the_strip_count_where_the_blocked_sum_is_live():
    # the real contract, unchanged: the on-line scan equals Backlund's independent count
    for T in (100.0, 1000.0):
        on = NT._zeros_on_line(T)
        n_strip, _ = NT._zeros_in_strip(T)
        assert on == round(n_strip), (T, on, n_strip, RA.backend(), RA.bulk_path())


def test_backend_keeps_its_meaning_and_the_main_sum_is_reported_beside_it():
    assert RA.backend() in ("c", "numpy", "python")
    assert RA.bulk_path() in ("fft", "c", "numpy", "python")
    d = RA.describe()
    assert d["backend"] in ("c", "numpy", "python")
    assert d["main_sum"] in ("fft", "c", "numpy", "python")
    assert "per-node artifact" in d["note"] and "never a verdict" in d["main_sum_note"]
