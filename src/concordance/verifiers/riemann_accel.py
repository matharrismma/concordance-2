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


def _np_z(ts):
    np = _numpy()
    ts = np.ascontiguousarray(ts, dtype=float)
    a = np.sqrt(ts / _TWO_PI)
    m = np.floor(a).astype(np.int64)
    th = ts / 2 * np.log(ts / _TWO_PI) - ts / 2 - math.pi / 8 + 1.0 / (48 * ts) + 7.0 / (5760 * ts ** 3)
    p = a - m
    c0 = np.cos(_TWO_PI * (p * p - p - 1.0 / 16.0)) / np.cos(_TWO_PI * p)
    corr = np.where(m % 2 == 1, 1.0, -1.0) * a ** -0.5 * c0
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
    return {"backend": backend(), "build_note": _BUILD_NOTE or "(not built)", "source": str(_C_SRC.name),
            "note": ("the Riemann-Siegel sweep is accelerated when a C compiler or numpy is present; all backends "
                     "compute the same formula and the scan defers to exact mpmath near every zero, so the count "
                     "is identical whichever ran. The compiled library is a per-node artifact, never synced.")}
