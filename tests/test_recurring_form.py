"""Recurring form — the fascia measure as an engine primitive (docs/FASCIA.md, promoted from
eval/recurring_form/). Proves the two things the OEIS attack established: the measure discriminates a
real recurring-form family from a null, and it weights connections by RARITY (a shared generic
feature is not a form). Plus the one worked deriver — a linear recurrence detected exactly from
integer terms — reads Fibonacci as order-2 eigenstructure and refuses the primes.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from concordance import recurring_form as rf  # noqa: E402


# ---- rarity: a feature everything has is weightless; a rare one carries the signal ----

def test_idf_downweights_generic_and_lifts_rare():
    corpus = [{"common", f"rare_{i}"} for i in range(50)]
    idf = rf.idf_of(corpus)
    assert idf["common"] == 0.0            # present in every item -> no weight
    assert idf["rare_0"] > 2.0             # present once -> heavy weight


def test_neighbors_rank_by_rarity_not_count():
    idf = rf.idf_of([{"g"} for _ in range(40)] + [{"rare"}])
    corpus = [("A", {"rare", "g"}), ("B", {"g", "x", "y"})]
    target = {"rare", "g", "x", "y"}
    nb = rf.neighbors("T", target, corpus, idf=idf)
    # B shares 3 generic-ish primitives, A shares one RARE one — A must still win
    assert nb[0]["key"] == "A" and "rare" in nb[0]["shared"]
    assert nb[0]["weight"] > nb[1]["weight"]


def test_a_thing_is_not_its_own_neighbor():
    # noise makes {linrec, order_2} rare (idf > 0) so the true neighbour carries weight
    corpus = ([("me", {"linrec", "order_2"}), ("you", {"linrec", "order_2"})]
              + [(f"n{i}", {f"x{i}"}) for i in range(10)])
    nb = rf.neighbors("me", {"linrec", "order_2"}, corpus)
    assert [n["key"] for n in nb] == ["you"]


# ---- the assay: a real family beats the null; a generic-only thing is COINCIDENCE ----

def _corpus():
    form = {"linrec", "order_2", "irrational_ratio"}          # the rare shared spine
    generic = {"all_positive", "strict_inc"}                  # everyone has these
    fam = [(f"fam_{i}", form | generic) for i in range(3)]
    noise = [(f"noise_{i}", {f"uniq_{i}"} | generic) for i in range(250)]
    return fam + noise, form | generic, generic


def test_a_real_family_is_beyond_chance():
    corpus, fam_target, _generic = _corpus()
    r = rf.assay("probe", fam_target, corpus, trials=400)
    assert r["score"] > 0
    assert r["verdict"] in ("CONFIRMED", "PLAUSIBLE"), r
    assert r["p"] < 0.05, r
    assert all(n["key"].startswith("fam_") for n in r["neighbors"]), "family neighbours only"
    assert "order_2" in r["neighbors"][0]["shared"], "the connection names its rare form"


def test_generic_only_thing_is_coincidence():
    corpus, _fam, generic = _corpus()
    r = rf.assay("probe", generic, corpus, trials=400)   # shares only weightless features
    assert r["score"] == 0.0 and r["verdict"] == "COINCIDENCE", r


# ---- the worked deriver: computed, exact, honest ----

def test_sequence_signature_reads_fibonacci_as_order_2():
    fib = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233]
    s = rf.sequence_signature(fib)
    assert "linrec" in s and "order_2" in s
    assert "exp_growth" in s and "irrational_ratio" in s   # ratio -> phi, not an integer


def test_sequence_signature_reads_powers_of_two_as_order_1_integer_ratio():
    s = rf.sequence_signature([1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048])
    assert "linrec" in s and "order_1" in s and "integer_ratio" in s


def test_sequence_signature_refuses_the_primes():
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43]
    s = rf.sequence_signature(primes)
    assert "linrec" not in s, "the primes satisfy no finite linear recurrence"


def test_linear_recurrence_order_is_exact_and_verified():
    # a fitted recurrence must verify on EVERY held-out term, not just the fitting rows
    d, c = rf.linear_recurrence_order([1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144])
    assert d == 2 and [int(x) for x in c] == [1, 1]
    d0, c0 = rf.linear_recurrence_order([2, 3, 5, 7, 11, 13, 17, 19, 23, 29])
    assert d0 == 0 and c0 is None


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
