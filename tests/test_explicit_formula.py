"""THE ZEROS PLAY THE PRIMES on the Riemann stick (2026-11-24, Matt: "Music of primes"). number_theory.explicit_formula
reads the prime powers <= X off the stored zeta zeros by two transforms (the explicit formula's staircase, Landau's
formula's spectrum) and checks both against the sieve. These tests pin that it CONFIRMS on the real table, REFUSES a
false claim, gives NO verdict where the zeros cannot hear, and, the test that matters most, does NOT confirm when the
zeros are fakes with the right density: a check that confirmed on any table would prove nothing about this one."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from concordance.verifiers import VERIFIERS
from concordance.verifiers import number_theory as NT

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "data" / "zeta_zeros.jsonl"


@pytest.fixture
def real_zeros(monkeypatch):
    """Point the loader at the tracked table (other modules repoint CONCORDANCE_DATA_DIR process-wide)."""
    assert TABLE.exists(), "data/zeta_zeros.jsonl is tracked; its absence is a failure, not a skip"
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(ROOT / "data"))
    g = NT._load_zeta_gammas()
    assert g and len(g) == 10000 and abs(g[0] - 14.134725142) < 1e-9
    return g


def _primes_to(x):
    return [n for n in range(2, x + 1) if all(n % d for d in range(2, int(math.isqrt(n)) + 1))]


def _table(tmp_path, monkeypatch, gammas):
    (tmp_path / "zeta_zeros.jsonl").write_text(
        '{"_meta": "a test table"}\n' + "\n".join(f"{v:.9f}" for v in gammas) + "\n", encoding="utf-8")
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))


def test_the_stored_zeros_give_the_primes_to_one_hundred(real_zeros):
    r = NT.verify_explicit_formula({"explicit_formula_to": 100, "claimed_zeros_give_primes": True})
    assert r.status == "CONFIRMED", r.detail
    d = r.data
    assert d["primes_read"] == _primes_to(100) and d["prime_count_read"] == 25
    assert [8, 2, 3] in d["prime_powers_read"] and [9, 3, 2] in d["prime_powers_read"] and [64, 2, 6] in d["prime_powers_read"]
    assert len(d["prime_powers_read"]) == 10                   # 4 8 9 16 25 27 32 49 64 81
    lo, hi = d["staircase_step_over_log_p"]
    assert 0.99 < lo <= hi < 1.01                              # each step is log p, measured 0.997..1.001
    assert d["staircase_max_abs_elsewhere"] < 0.05             # and nothing at the composites (measured 0.005)
    assert d["spectrum_over_log_p"][0] > 0.9                   # Landau's formula hears them too
    psi = d["psi_at_x_plus_half"]
    assert abs(psi["rebuilt_from_zeros"] - psi["exact"]) < 0.05
    assert "NOT evidence for RH" in d["means"]


def test_the_primes_are_named_by_the_step_height_not_only_located(real_zeros):
    r = NT.verify_explicit_formula({"explicit_formula_to": 30, "claimed_primes": _primes_to(30)})
    assert r.status == "CONFIRMED", r.detail
    bad = NT.verify_explicit_formula({"explicit_formula_to": 30, "claimed_primes": _primes_to(30) + [9]})
    assert bad.status == "MISMATCH" and "not prime: [9]" in bad.detail
    short = NT.verify_explicit_formula({"explicit_formula_to": 30, "claimed_primes": _primes_to(30)[:-1]})
    assert short.status == "MISMATCH" and "left out: [29]" in short.detail


def test_a_false_claim_is_refused(real_zeros):
    r = NT.verify_explicit_formula({"explicit_formula_to": 100, "claimed_zeros_give_primes": False})
    assert r.status == "MISMATCH"


def test_no_verdict_where_the_zeros_cannot_hear(real_zeros):
    edge = NT.verify_explicit_formula({"explicit_formula_to": 356, "claimed_zeros_give_primes": True})
    assert edge.status == "CONFIRMED", edge.detail             # measured 2026-11-24: clear through 356
    past = NT.verify_explicit_formula({"explicit_formula_to": 400, "claimed_zeros_give_primes": True})
    assert past.status == "NOT_APPLICABLE" and past.data["unclear_at"][0] == 357
    few = NT.verify_explicit_formula({"explicit_formula_to": 30, "claimed_zeros_give_primes": True,
                                      "explicit_formula_zeros": 100})
    assert few.status == "NOT_APPLICABLE"                      # 100 zeros cannot hear every number to 30
    more = NT.verify_explicit_formula({"explicit_formula_to": 30, "claimed_zeros_give_primes": True,
                                       "explicit_formula_zeros": 1000})
    assert more.status == "CONFIRMED"
    assert NT.verify_explicit_formula({"explicit_formula_to": 1001, "claimed_zeros_give_primes": True}).status == "ERROR"
    assert NT.verify_explicit_formula({"explicit_formula_to": 1, "claimed_zeros_give_primes": True}).status == "ERROR"
    assert NT.verify_explicit_formula({"explicit_formula_to": 30, "claimed_zeros_give_primes": True,
                                       "explicit_formula_zeros": 5}).status == "ERROR"
    assert NT.verify_explicit_formula({"explicit_formula_to": 30}).status == "NOT_APPLICABLE"


def _smooth_zeros(n):
    """Points with the zeros' exact average density and no prime information: N0(t) = k - 1/2, N0 the smooth
    Riemann-von Mangoldt count (t/2pi)(log(t/2pi) - 1) + 7/8, solved by Newton."""
    k = np.arange(1, n + 1) - 0.5
    t = np.full(n, 20.0) + 2 * np.pi * k / np.log(np.maximum(k, 2.0))
    for _ in range(60):
        f = t / (2 * np.pi) * (np.log(t / (2 * np.pi)) - 1) + 7 / 8 - k
        t = t - f / (np.log(t / (2 * np.pi)) / (2 * np.pi))
    return t


def test_fake_zeros_with_the_right_density_do_not_give_the_primes(real_zeros, tmp_path, monkeypatch):
    fakes = {
        "smooth": _smooth_zeros(10000),
        "jittered": np.sort(np.asarray(real_zeros) + np.random.default_rng(7).uniform(-0.25, 0.25, 10000)),
        "shifted": np.asarray(real_zeros) + 0.5,
    }
    for label, gam in fakes.items():
        assert gam[0] > 14.0 and np.all(np.diff(gam) > 0), label
        _table(tmp_path, monkeypatch, gam)
        for X in (30, 100):
            r = NT.verify_explicit_formula({"explicit_formula_to": X, "claimed_zeros_give_primes": True})
            assert r.status != "CONFIRMED", (label, X, r.detail)


def test_a_damaged_table_is_refused(real_zeros, tmp_path, monkeypatch):
    g = list(real_zeros)
    g[500], g[501] = g[501], g[500]
    _table(tmp_path, monkeypatch, g)
    r = NT.verify_explicit_formula({"explicit_formula_to": 30, "claimed_zeros_give_primes": True})
    assert r.status == "ERROR" and "damaged" in r.detail


def test_the_check_is_routed_through_the_packet_and_named(real_zeros):
    out = NT.run({"NUM_VERIFY": {"explicit_formula_to": 50, "claimed_zeros_give_primes": True}})
    assert any(o.name == "number_theory.explicit_formula" and o.status == "CONFIRMED" for o in out)
    assert VERIFIERS["explicit_formula"] == VERIFIERS["zeros_to_primes"] == VERIFIERS["number_theory"]
