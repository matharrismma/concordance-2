"""Unit-pin the linear_algebra verifier (A2, 2026-10-06). Dot [1,2,3].[4,5,6]=32; det[[1,2],[3,4]]=-2.
The module loads numpy lazily, so _ensure_numpy() is primed before the direct-call checks.
"""
from __future__ import annotations
from concordance.verifiers import linear_algebra as LA

LA._ensure_numpy()


def test_vector_dot():
    assert LA.verify_vector_dot({"vec_a": [1, 2, 3], "vec_b": [4, 5, 6], "claimed_dot_product": 32}).status == "CONFIRMED"
    assert LA.verify_vector_dot({"vec_a": [1, 2, 3], "vec_b": [4, 5, 6], "claimed_dot_product": 30}).status == "MISMATCH"
    assert LA.verify_vector_dot({}).status == "NOT_APPLICABLE"


def test_matrix_determinant():
    assert LA.verify_matrix_determinant({"matrix": [[1, 2], [3, 4]], "claimed_determinant": -2}).status == "CONFIRMED"
    assert LA.verify_matrix_determinant({"matrix": [[1, 2], [3, 4]], "claimed_determinant": 5}).status == "MISMATCH"
