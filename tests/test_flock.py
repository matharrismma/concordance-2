"""FLOCK — the starling's topological rule (BOIDS). Pins: OFF by default; the neighborhood is the
tightest-woven handful (most shared neighbors, then degree, then a stable id), capped at k, deterministic."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402
from concordance import flock  # noqa: E402


def test_off_by_default(monkeypatch):
    monkeypatch.delenv("CONCORDANCE_FLOCK", raising=False)
    assert flock.enabled() is False


def test_empty_center_is_empty():
    assert flock.neighborhood([], {}) == []


def test_ranks_woven_then_degree():
    # center C links a, b, c. a shares {b} with C and has degree 4; b shares {a} and degree 2;
    # c shares nothing and degree 1 → order a, b, c.
    center = ["a", "b", "c"]
    nlinks = {"a": ["C", "b", "x", "y"], "b": ["C", "a"], "c": ["C"]}
    assert flock.neighborhood(center, nlinks, k=3) == ["a", "b", "c"]
    assert flock.neighborhood(center, nlinks, k=2) == ["a", "b"]


def test_capped_at_k_and_stable():
    center = [chr(ord("a") + i) for i in range(9)]     # 9 neighbors, none woven → tie on shared+degree
    nlinks = {n: [] for n in center}
    got = flock.neighborhood(center, nlinks)           # default k = 7
    assert len(got) == 7
    assert got == sorted(center)[:7]                   # stable id tie-break, reproducible


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
