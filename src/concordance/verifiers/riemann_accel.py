"""The Riemann-Siegel scan, accelerated — C, then numpy, then pure python (Matt, 2026-10-05: "Do C then numpy").

Counting the zeros of zeta up to a height T means evaluating Hardy's Z on a grid a fraction of the zero
spacing apart — tens of millions of points at T = 10^6. The arithmetic is the same at every point; only the
speed of the sweep differs. This module offers three backends for the bulk sweep and picks the fastest that
is actually present:

    C      _rs.c compiled on first use (cc -O3 -fopenmp), parallel across cores — ~2.4 us/point at T=1e6
    numpy  the main sum vectorised over grid points of equal m — portable, no compiler
    python the reference loop (verifiers.number_theory._rs_z), always available

All three compute the SAME first-order Riemann-Siegel formula. On one machine's libm the C path agrees with
python to the last bit; where it would differ (only within ~1e-15, never near a sign change that matters) the
caller's exact-mpmath recount decides, so the zero COUNT is identical whichever backend ran. The accelerator
is a speed, never a verdict. The compiled .so is a per-node artifact; it never travels with the keeping.
"""
from __future__ import annotations

import math
import os
import subprocess
import sys
import sysconfig
from pathlib import Path
from typing import List, Optional, Sequence

_TWO_PI = 2.0 * math.pi
_HERE = Path(__file__).resolve().parent
_C_SRC = _HERE / "_rs.c"

_np = None
_C = None                 # the loaded ctypes function, or False once a build has failed
_BUILD_NOTE = ""


def _numpy():
    global _np
    if _np is None:
        try:
            import numpy as np  # noqa
            _np = np
        except Exception:  # noqa: BLE001
            _np = False
    return _np


def _cache_dir() -> Path:
    """A writable place for the compiled .so: the data dir's cache, else a temp dir keyed to this user."""
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    d = (Path(base) / "cache") if base else (Path(sysconfig.get_path("data")) / "nh-cache")
    try:
        d.mkdir(parents=True, exist_ok=True)
        probe = d / ".w"
        probe.write_text("x", encoding="utf-8")
        probe.unlink()
        return d
    except OSError:
        import tempfile
        d = Path(tempfile.gettempdir()) / "nh-rs-cache"
        d.mkdir(parents=True, exist_ok=True)
        return d


def _so_path() -> Path:
    return _cache_dir() / ("_rs" + (sysconfig.get_config_var("EXT_SUFFIX") or ".so"))


def build(force: bool = False) -> Optional[Path]:
    """Compile _rs.c to a shared library, returning its path, or None when no compiler is available.
    Rebuilds when the source is newer than the .so. OpenMP is tried first, then plain -O3."""
    global _BUILD_NOTE
    if not _C_SRC.exists():
        _BUILD_NOTE = "no _rs.c"
        return None
    so = _so_path()
    if so.exists() and not force and so.stat().st_mtime >= _C_SRC.stat().st_mtime:
        return so
    cc = os.environ.get("CC", "").strip() or ("cc" if _which("cc") else ("gcc" if _which("gcc") else ""))
    if not cc:
        _BUILD_NOTE = "no C compiler (cc/gcc) on PATH"
        return None
    for extra in (["-fopenmp"], []):                 # OpenMP first (parallel), then plain if it is absent
        cmd = [cc, "-O3", "-fPIC", "-shared", *extra, "-o", str(so), str(_C_SRC), "-lm"]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
            _BUILD_NOTE = "compiled" + (" (openmp)" if extra else " (single-threaded)")
            return so
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
            continue
    _BUILD_NOTE = "compilation failed"
    return None


def _which(prog: str) -> Optional[str]:
    from shutil import which
    return which(prog)


def _load_c():
    """The ctypes function for nh_rs_z_array, or False if it cannot be built/loaded."""
    global _C
    if _C is not None:
        return _C
    try:
        import ctypes
        so = build()
        if so is None:
            _C = False
            return _C
        lib = ctypes.CDLL(str(so))
        fn = lib.nh_rs_z_array
        fn.argtypes = [ctypes.c_void_p, ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p,
                       ctypes.c_long, ctypes.c_void_p]
        fn.restype = None
        _C = fn
    except Exception:  # noqa: BLE001 — any failure falls through to numpy/python
        _C = False
    return _C


# ── the backends ────────────────────────────────────────────────────────────────────────────────
def _py_z(ts: Sequence[float]) -> List[float]:
    from . import number_theory as nt
    return [nt._rs_z(float(t)) for t in ts]


def _theta_and_correction(ts):
    """theta(t), m = floor(sqrt(t/2pi)), and the first Riemann-Siegel correction, for a grid of t.
    ONE definition, shared by every backend: the numpy path and the FFT path must not drift apart."""
    np = _numpy()
    a = np.sqrt(ts / _TWO_PI)
    m = np.floor(a).astype(np.int64)
    th = ts / 2 * np.log(ts / _TWO_PI) - ts / 2 - math.pi / 8 + 1.0 / (48 * ts) + 7.0 / (5760 * ts ** 3)
    p = a - m
    c0 = np.cos(_TWO_PI * (p * p - p - 1.0 / 16.0)) / np.cos(_TWO_PI * p)
    return th, m, np.where(m % 2 == 1, 1.0, -1.0) * a ** -0.5 * c0


def _np_z(ts):
    np = _numpy()
    ts = np.ascontiguousarray(ts, dtype=float)
    th, m, corr = _theta_and_correction(ts)
    out = np.empty_like(ts)
    mmax = int(m.max()) if ts.size else 0
    logn = np.log(np.arange(1, mmax + 1, dtype=float)) if mmax else np.empty(0)
    invsq = 1.0 / np.sqrt(np.arange(1, mmax + 1, dtype=float)) if mmax else np.empty(0)
    for mv in np.unique(m):                       # m changes slowly: a handful of groups per block
        idx = np.where(m == mv)[0]
        tt = ts[idx][:, None]
        thh = th[idx][:, None]
        terms = np.cos(thh - tt * logn[None, :mv]) * invsq[None, :mv]
        out[idx] = 2.0 * terms.sum(axis=1) + corr[idx]
    return out


_C_TABLES = {"mmax": 0, "logk": None, "invsqrtk": None}


def _tables(mmax: int):
    """Precomputed log(k) and 1/sqrt(k) for k=1..mmax, grown as needed and reused across blocks."""
    np = _numpy()
    if mmax > _C_TABLES["mmax"]:
        ks = np.arange(1, mmax + 1, dtype=float)
        _C_TABLES.update({"mmax": mmax, "logk": np.ascontiguousarray(np.log(ks)),
                          "invsqrtk": np.ascontiguousarray(1.0 / np.sqrt(ks))})
    return _C_TABLES["logk"], _C_TABLES["invsqrtk"], _C_TABLES["mmax"]


def _c_z(ts):
    import ctypes
    np = _numpy()
    fn = _load_c()
    ts = np.ascontiguousarray(ts, dtype=float)
    out = np.empty_like(ts)
    tmax = float(ts.max()) if ts.size else 20.0
    mmax = max(1, int((tmax / _TWO_PI) ** 0.5) + 1)
    logk, invsqrtk, mm = _tables(mmax)
    fn(ts.ctypes.data_as(ctypes.c_void_p), ts.size,
       logk.ctypes.data_as(ctypes.c_void_p), invsqrtk.ctypes.data_as(ctypes.c_void_p),
       mm, out.ctypes.data_as(ctypes.c_void_p))
    return out


def z_array(ts):
    """Z(t) for every t in ts (each t > ~300, where the first-order formula is accurate), as a numpy array
    when numpy is present, else a list. Uses C, then numpy, then pure python — the fastest that is available."""
    np = _numpy()
    if np is not False and _load_c() is not False:
        return _c_z(ts)
    if np is not False:
        return _np_z(ts)
    return _py_z(ts)


def backend() -> str:
    """Which bulk-sweep backend is live on this node — for the capability statement's honesty."""
    if _numpy() is not False and _load_c() is not False:
        return "c"
    if _numpy() is not False:
        return "numpy"
    return "python"


def describe() -> dict:
    return {"backend": backend(), "main_sum": bulk_path(), "build_note": _BUILD_NOTE or "(not built)",
            "main_sum_note": ("'fft' when the blocked main sum is live for a long uniform block: the same "
                              "first-order formula, summed by a type-1 NUFFT instead of point by point. It is "
                              "as close to exact mpmath as the point-by-point path at every height measured, "
                              "and the scan still recounts exactly near every zero. A speed, never a verdict."),
            "source": str(_C_SRC.name),
            "note": ("the Riemann-Siegel sweep is accelerated when a C compiler or numpy is present; all backends "
                     "compute the same formula and the scan defers to exact mpmath near every zero, so the count "
                     "is identical whichever ran. The compiled library is a per-node artifact, never synced.")}


# ── the blocked main sum ────────────────────────────────────────────────────────────────────────
# The scan grid is UNIFORM (t_j = t0 + j*h) and m = floor(sqrt(t/2pi)) is constant across a block, so
# the block origin pulls straight out of the k-sum:
#
#     Z(t_j) = 2*Re[ e^{i theta_j} F_j ] + corr_j,   F_j = sum_k a_k e^{-i j w_k}
#     a_k = k^{-1/2} e^{-i t_mid log k},             w_k = h log k
#
# which is a type-1 NUFFT: m nonuniform frequencies, n uniform outputs. O(n*m) becomes O(M log M + m*q).
# The grid is already ~24x oversampled against the highest frequency present (h*log m ~ 0.13 rad/sample
# at T=1e7), so the transform introduces no aliasing of its own.
#
# EXPAND ABOUT THE BLOCK MIDPOINT, NOT ITS EDGE. The deconvolution multiplies by exp(tau*(2*pi*j/M)^2);
# about the edge, j runs to the band limit and the result overflows (measured: ~1e34). About the midpoint
# the exponent is capped at tau*(pi/sigma)^2.
#
# This path is a SPEED, never a verdict: it computes the same first-order formula, it is as close to exact
# mpmath as the point-by-point path at every height measured, and the caller still recounts exactly near
# every candidate zero while Backlund's strip count remains the independent authority.
_FFT_MIN_N = 1 << 12          # below this the transform's fixed cost is not repaid
_FFT_MIN_M = 64               # below this the direct sum is already cheap
_FFT_Q = 24                   # gridding width, in grid points
_FFT_SIGMA = 2                # FFT oversampling
_FFT_TAU = 1.25               # Gaussian width; (q, tau) calibrated against the direct sum, not asserted


def uniform_grid(t0: float, h: float, n: int):
    """The one construction of a uniform scan grid. A caller that wants the blocked main sum builds its t
    values HERE, so the grid the sum models and the grid the span logic reads are the same bits."""
    np = _numpy()
    return float(t0) + float(h) * np.arange(int(n), dtype=float)


def m_run(t0: float, h: float, nmax: int) -> int:
    """How many uniform steps from t0 keep m constant, capped at nmax. m is constant on
    [2pi*m^2, 2pi*(m+1)^2) — a run ~12.57*m wide in t, wider than a block at the heights that matter but
    not always, so the caller asks. The FFT path needs m BEFORE it starts; the others group by m after."""
    m0 = int(math.floor(math.sqrt(max(float(t0), 1.0) / _TWO_PI)))
    span = _TWO_PI * (m0 + 1) ** 2 - float(t0)
    return max(1, min(int(nmax), int(span / float(h))))


def _fft_z(ts, h: float):
    """Z on one m-group of a uniform grid, main sum by NUFFT. `ts` is the caller's own array."""
    np = _numpy()
    n = int(ts.size)
    th, m, corr = _theta_and_correction(ts)
    mv = int(m[0])
    M = _FFT_SIGMA * (1 << max(1, int(math.ceil(math.log2(max(n, 2))))))
    ks = np.arange(1, mv + 1, dtype=float)
    logk = np.log(ks)
    a = (1.0 / np.sqrt(ks)) * np.exp(-1j * (float(ts[n // 2]) * logk))   # phase origin: the block's middle
    x = (float(h) * logk) * M / _TWO_PI                                 # source positions, grid units
    half = _FFT_Q // 2
    G = np.zeros(M, dtype=complex)
    base = np.floor(x).astype(np.int64)
    for d in range(-half + 1, half + 1):
        nn = base + d
        np.add.at(G, np.mod(nn, M), a * np.exp(-((nn - x) ** 2) / (4.0 * _FFT_TAU)))
    jp = np.arange(-(n // 2), n - (n // 2))                             # centred modes, increasing t order
    F = np.fft.fft(G)[np.mod(jp, M)] * np.exp(_FFT_TAU * (_TWO_PI * jp / M) ** 2)
    return 2.0 * np.real(np.exp(1j * th) * (F / math.sqrt(4.0 * math.pi * _FFT_TAU))) + corr


def z_uniform(t0: float, h: float, n: int):
    """Z on the uniform grid t0 + j*h, j = 0..n-1 — the blocked main sum where it pays, else z_array.
    Splits at m boundaries, which only the FFT path requires."""
    np = _numpy()
    n = int(n)
    if np is False:
        return _py_z([float(t0) + i * float(h) for i in range(n)])
    ts = uniform_grid(t0, h, n)
    if float(h) <= 0.0 or n < _FFT_MIN_N:
        return np.asarray(z_array(ts), float)
    out = np.empty(n, dtype=float)
    done = 0
    while done < n:
        seg = m_run(float(ts[done]), h, n - done)
        hi = done + seg
        sub = ts[done:hi]
        mv = int(math.floor(math.sqrt(max(float(sub[0]), 1.0) / _TWO_PI)))
        if seg >= _FFT_MIN_N and mv >= _FFT_MIN_M:
            out[done:hi] = _fft_z(sub, h)
        else:
            out[done:hi] = np.asarray(z_array(sub), float)
        done = hi
    return out


def bulk_path() -> str:
    """'fft' when the blocked main sum is available on this node, else the point-by-point backend.
    Reported BESIDE backend(), never instead of it: backend() keeps its old meaning."""
    return "fft" if _numpy() is not False else backend()
