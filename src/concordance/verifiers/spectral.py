"""Change of domain: put the problem in the space where it diagonalizes, solve it there, map back.

Matt, 2026-10-09: "We can use the domain with the best aspect to solve a particular problem. putting the problem in a
Hilbert Space" -> "build it". This is the EXACT flip (the structured sibling of the get-close approximation): a linear
operator is hard to iterate in the standard basis and trivial in its eigenbasis, where it is diagonal and the coupled
system becomes independent scalars. The method is three steps - transform, solve as scalars, transform back - and the
engine CHECKS the transform is valid before it trusts the answer.

Two canonical flips, each verified end to end:

  * DIAGONALIZE (the eigenbasis). Given a matrix A, the engine finds its eigenvalues and eigenvectors and VERIFIES
    each pair: A v = lambda v (the flip is real, not asserted). If asked for a power A^k, it computes it two ways -
    through the eigenbasis (P diag(lambda^k) P^-1, independent scalar powers) AND directly - and confirms they agree.
    This is Binet's formula for Fibonacci, a Markov chain's steady state (the lambda = 1 eigenvector), any linear
    recurrence: coupled in the standard basis, independent in the eigenbasis.

  * FOURIER (the frequency basis). Convolution is O(n^2) in the standard basis and pointwise multiplication in the
    frequency basis: DFT(a * b) = DFT(a) . DFT(b). The engine computes the convolution directly AND through the
    Fourier flip (ifft(fft a . fft b)) and confirms they agree - the convolution theorem, checked. This is fast
    polynomial and integer multiplication.

0 false positives: a claimed eigenvalue that does not satisfy A v = lambda v, a claimed power/convolution that does
not match, is a MISMATCH. The flip is never trusted until the engine has confirmed it holds. Numpy absent -> the
honest gap NOT_APPLICABLE, never a false result.

Artifact: SPECTRAL_VERIFY = {
  "matrix": [[...], ...],                 # DIAGONALIZE: the operator A
  "power": k, "apply_to": [x...],         #   optional: compute A^k (or A^k x) and check the eigenbasis route = direct
  "claimed_eigenvalues": [...],           #   optional: confirm the spectrum
  "claimed_result": ... ,                 #   optional: confirm A^k (or A^k x)
  "a": [...], "b": [...],                 # FOURIER: convolve via the frequency flip
  "claimed_convolution": [...],           #   optional: confirm a * b
}
"""
from __future__ import annotations

from typing import Any, Dict, List

from .base import VerifierResult, confirm, dispatch, error, mismatch, na

_TOL = 1e-7


def _np():
    try:
        import numpy as np  # noqa: F401
        return np
    except Exception:  # noqa: BLE001 — sovereign minimal install: no numpy -> honest gap
        return None


def verify_diagonalize(a: Dict[str, Any]) -> VerifierResult:
    name = "spectral.diagonalize"
    np = _np()
    if np is None:
        return na(name, "numpy not available — the eigenbasis flip needs it")
    try:
        A = np.array(a["matrix"], dtype=float)
    except Exception as e:  # noqa: BLE001
        return error(name, f"'matrix' must be a numeric square matrix: {e}")
    if A.ndim != 2 or A.shape[0] != A.shape[1] or A.shape[0] == 0:
        return error(name, f"'matrix' must be square and non-empty; got shape {A.shape}")
    n = A.shape[0]
    try:
        vals, vecs = np.linalg.eig(A)
    except Exception as e:  # noqa: BLE001
        return error(name, f"eigendecomposition failed: {e}")
    # THE FLIP IS REAL: every eigenpair satisfies A v = lambda v
    max_resid = 0.0
    for i in range(n):
        v = vecs[:, i]
        resid = float(np.linalg.norm(A @ v - vals[i] * v))
        max_resid = max(max_resid, resid)
    if max_resid > _TOL * (1.0 + float(np.linalg.norm(A))):
        return error(name, f"the eigenpairs do not satisfy A v = lambda v (residual {max_resid:.2e})")
    # THE EIGENBASIS MUST EXIST: a defective matrix (a Jordan block) returns a repeated eigenvector that still
    # satisfies A v = lambda v, so the residual check alone would falsely confirm. Require n INDEPENDENT eigenvectors
    # - the eigenvector matrix well-conditioned - or there is no basis to flip into, and the honest answer is ERROR.
    try:
        cond = float(np.linalg.cond(vecs))
    except Exception:  # noqa: BLE001
        cond = float("inf")
    if not np.isfinite(cond) or cond > 1e12:
        return error(name, f"defective matrix: fewer than {n} independent eigenvectors (condition {cond:.1e}) — "
                           "no eigenbasis exists, the flip does not apply here")
    data: Dict[str, Any] = {"eigenvalues": [complex(x).real if abs(complex(x).imag) < _TOL else complex(x)
                                            for x in vals],
                            "spectral_radius": float(max(abs(vals))), "max_eigenpair_residual": max_resid}
    # confirm a claimed spectrum
    if "claimed_eigenvalues" in a:
        claimed = sorted((complex(x) for x in a["claimed_eigenvalues"]), key=lambda z: (z.real, z.imag))
        got = sorted((complex(x) for x in vals), key=lambda z: (z.real, z.imag))
        if len(claimed) != len(got) or any(abs(c - g) > _TOL * (1 + abs(g)) for c, g in zip(claimed, got)):
            return mismatch(name, f"claimed eigenvalues {[round(c.real, 6) for c in claimed]} != computed "
                                  f"{[round(g.real, 6) for g in got]}", data)
    # the solve: A^k (or A^k x) through the eigenbasis vs directly
    if "power" in a:
        try:
            k = int(a["power"])
        except (TypeError, ValueError):
            return error(name, "'power' must be an integer")
        P = vecs
        try:
            Pinv = np.linalg.inv(P)
        except Exception as e:  # noqa: BLE001
            return error(name, f"eigenvectors not independent (inverse failed): {e}")
        via_eigen = (P @ np.diag(vals ** k) @ Pinv)
        direct = np.linalg.matrix_power(A, k) if k >= 0 else np.linalg.matrix_power(np.linalg.inv(A), -k)
        gap = float(np.linalg.norm(via_eigen - direct))
        if gap > _TOL * (1.0 + float(np.linalg.norm(direct))):
            return mismatch(name, f"the eigenbasis route and the direct route disagree for A^{k} (gap {gap:.2e})", data)
        result = via_eigen
        if "apply_to" in a:
            x = np.array(a["apply_to"], dtype=float)
            result = via_eigen @ x
        res_real = np.real_if_close(result, tol=1000)
        data["result"] = res_real.tolist()
        data["eigenbasis_vs_direct_gap"] = gap
        if "claimed_result" in a:
            claimed = np.array(a["claimed_result"], dtype=float)
            if claimed.shape != np.array(res_real).shape or float(np.linalg.norm(claimed - res_real)) > 1e-6 * (1 + float(np.linalg.norm(res_real))):
                return mismatch(name, f"claimed result != A^{k} computed through the eigenbasis", data)
        return confirm(name, f"change of domain confirmed: A diagonalizes (max residual {max_resid:.1e}), and A^{k} "
                             f"through the eigenbasis (independent scalar powers of the eigenvalues) equals the direct "
                             f"computation to {gap:.1e}. The flip is valid.", data)
    return confirm(name, f"A diagonalizes: {n} eigenpairs satisfy A v = lambda v (max residual {max_resid:.1e}); "
                         f"spectral radius {data['spectral_radius']:.6g}. In this basis the operator is diagonal — "
                         f"the coupled system becomes independent scalars.", data)


def verify_fourier_convolution(a: Dict[str, Any]) -> VerifierResult:
    name = "spectral.fourier_convolution"
    np = _np()
    if np is None:
        return na(name, "numpy not available — the Fourier flip needs it")
    try:
        x = np.array(a["a"], dtype=float); y = np.array(a["b"], dtype=float)
    except Exception as e:  # noqa: BLE001
        return error(name, f"'a' and 'b' must be numeric sequences: {e}")
    if x.ndim != 1 or y.ndim != 1 or x.size == 0 or y.size == 0:
        return error(name, "'a' and 'b' must be non-empty 1-D sequences")
    direct = np.convolve(x, y)
    N = x.size + y.size - 1
    via_fft = np.real(np.fft.ifft(np.fft.fft(x, N) * np.fft.fft(y, N)))
    gap = float(np.linalg.norm(direct - via_fft))
    if gap > 1e-6 * (1.0 + float(np.linalg.norm(direct))):
        return mismatch(name, f"the convolution theorem check failed (gap {gap:.2e})", {"gap": gap})
    data: Dict[str, Any] = {"convolution": [round(float(v), 10) for v in direct], "length": int(N),
                            "theorem_gap": gap}
    if "claimed_convolution" in a:
        claimed = np.array(a["claimed_convolution"], dtype=float)
        if claimed.shape != direct.shape or float(np.linalg.norm(claimed - direct)) > 1e-6 * (1 + float(np.linalg.norm(direct))):
            return mismatch(name, "claimed convolution != a * b", data)
    return confirm(name, f"Fourier flip confirmed: a * b computed in the frequency basis (ifft of fft·fft) equals the "
                         f"direct convolution to {gap:.1e} — the convolution theorem. Convolution is multiplication "
                         f"in the frequency domain.", data)


_RULES = [
    (lambda a: "matrix" in a, verify_diagonalize),
    (lambda a: ("a" in a and "b" in a), verify_fourier_convolution),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, "SPECTRAL_VERIFY", _RULES, domain="spectral",
                    none_reason="no SPECTRAL_VERIFY artifacts present")
