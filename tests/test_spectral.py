"""CHANGE OF DOMAIN - solve in the eigenbasis, map back (Matt, 2026-10-09: "putting the problem in a Hilbert Space" -
"build it"). The spectral verifier: diagonalize and the Fourier flip. Pinned: a diagonalizable operator's power
through the eigenbasis equals the direct computation (Fibonacci -> Binet), a Markov steady state is the lambda=1
eigenvector, the Fourier flip equals the direct convolution; a defective (non-diagonalizable) matrix is an honest
ERROR, never a false confirm; a wrong spectrum / power / convolution is a MISMATCH (0 false positives)."""
from __future__ import annotations

import pytest

np = pytest.importorskip("numpy")

from concordance.verifiers import spectral as SP  # noqa: E402
from concordance.verifiers.base import VerifierResult  # noqa: E402


def _d(spec) -> VerifierResult:
    return SP.verify_diagonalize(spec)


def _f(spec) -> VerifierResult:
    return SP.verify_fourier_convolution(spec)


def test_fibonacci_power_through_the_eigenbasis_equals_direct():
    # M^10 = [[F11,F10],[F10,F9]] = [[89,55],[55,34]]; the eigenbasis route must match
    r = _d({"matrix": [[1, 1], [1, 0]], "power": 10, "claimed_result": [[89, 55], [55, 34]]})
    assert r.status == "CONFIRMED" and r.data["eigenbasis_vs_direct_gap"] < 1e-6


def test_the_spectrum_is_phi_and_psi():
    r = _d({"matrix": [[1, 1], [1, 0]], "claimed_eigenvalues": [(1 + 5 ** 0.5) / 2, (1 - 5 ** 0.5) / 2]})
    assert r.status == "CONFIRMED"
    assert _d({"matrix": [[1, 1], [1, 0]], "claimed_eigenvalues": [2.0, -1.0]}).status == "MISMATCH"


def test_markov_steady_state_is_the_lambda_one_eigenvector():
    r = _d({"matrix": [[0.9, 0.1], [0.5, 0.5]], "claimed_eigenvalues": [1.0, 0.4]})
    assert r.status == "CONFIRMED"
    assert abs(max(abs(np.array(r.data["eigenvalues"])), default=0) - 1.0) < 1e-9


def test_a_defective_matrix_is_an_honest_error_not_a_false_confirm():
    # [[1,1],[0,1]] is a Jordan block: one independent eigenvector, no eigenbasis
    assert _d({"matrix": [[1, 1], [0, 1]]}).status == "ERROR"
    assert _d({"matrix": [[1, 1], [0, 1]], "power": 2}).status == "ERROR"
    # a diagonalizable matrix with a repeated eigenvalue still confirms
    assert _d({"matrix": [[2, 0, 0], [0, 2, 0], [0, 0, 3]]}).status == "CONFIRMED"
    assert _d({"matrix": [[1, 0], [0, 1]]}).status == "CONFIRMED"


def test_the_fourier_flip_equals_the_direct_convolution():
    r = _f({"a": [1, 2, 3], "b": [1, 1], "claimed_convolution": [1, 3, 5, 3]})
    assert r.status == "CONFIRMED" and r.data["theorem_gap"] < 1e-6
    assert _f({"a": [1, 2, 3], "b": [1, 1], "claimed_convolution": [1, 3, 5, 4]}).status == "MISMATCH"


def test_bad_inputs_and_routing():
    assert _d({"matrix": [[1, 2, 3], [4, 5, 6]]}).status == "ERROR"      # not square
    assert SP.run({})[0].status == "NOT_APPLICABLE"                       # no artifact -> honest gap
    from concordance.derivation import verify_derivation as V
    r = V([{"id": "s", "domain": "spectral", "spec": {"SPECTRAL_VERIFY": {"matrix": [[1, 1], [1, 0]], "power": 10}}}])
    assert r["verdict"] == "HOLDS"
