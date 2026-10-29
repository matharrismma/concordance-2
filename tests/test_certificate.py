"""The independently-checkable certificate (verifiers/certificate.py) — the bbchallenge pattern.

The point is ASYMMETRY + INDEPENDENCE: the checker re-confirms a true certificate and REJECTS a
forged one, using only the witness — never the producer. A forged certificate is a lie the trust
anchor must catch.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.verifiers import certificate as C  # noqa: E402


def test_prime_certificate_checks():
    cert = C.certify_primality(17)
    assert cert.claim == {"n": 17, "verdict": "prime"}
    ok, why = C.check(cert)
    assert ok, why


def test_composite_certificate_checks():
    cert = C.certify_primality(15)
    assert cert.claim["verdict"] == "composite"
    ok, why = C.check(cert)
    assert ok, why


def test_a_larger_prime_round_trips_through_a_dict():
    # 1,299,709 is the 100,000th prime — the certificate rides as a plain dict (as in VerifierResult.data)
    d = C.to_dict(C.certify_primality(1299709))
    ok, why = C.check(d)
    assert ok, why


def test_many_small_numbers_agree_with_trial_division():
    def trial(n: int) -> str:
        return "prime" if n >= 2 and all(n % k for k in range(2, int(n ** 0.5) + 1)) else "composite"
    for n in range(2, 300):
        cert = C.certify_primality(n)
        ok, why = C.check(cert)
        assert ok, f"{n}: {why}"
        assert cert.claim["verdict"] == trial(n), n


def test_forged_prime_for_a_composite_is_rejected():
    # claim 15 is prime with real sub-certs for 2 and 7 (which DO generate 14 = n-1) and any base:
    # Lucas must fail, because a composite has no element of order n-1. The checker catches it.
    for a in range(2, 15):
        forged = C.Certificate("primality", {"n": 15, "verdict": "prime"},
                               {"base": a, "factors": [[2, C.to_dict(C.certify_primality(2))],
                                                       [7, C.to_dict(C.certify_primality(7))]]})
        ok, _ = C.check(forged)
        assert not ok, f"base {a} wrongly accepted for composite 15"


def test_forged_composite_for_a_prime_is_rejected():
    # claim 17 (prime) is composite with a bogus "factor" 4 — 17 % 4 != 0, so the checker rejects.
    forged = C.Certificate("primality", {"n": 17, "verdict": "composite"}, {"factor": 4})
    ok, _ = C.check(forged)
    assert not ok


def test_omitting_a_prime_divisor_of_n_minus_1_is_rejected():
    # 31 is prime; n-1 = 30 = 2*3*5. A certificate that lists only {2,3} fails completeness,
    # even though each listed factor is a true prime — Lucas needs EVERY prime divisor.
    full = C.certify_primality(31)
    trimmed = C.Certificate("primality", {"n": 31, "verdict": "prime"},
                            {"base": full.witness["base"],
                             "factors": [f for f in full.witness["factors"] if f[0] in (2, 3)]})
    ok, why = C.check(trimmed)
    assert not ok, why


def test_polynomial_root_certificate_checks():
    cert = C.certify_polynomial_root([1, -5, 6], 2)        # x^2-5x+6 = (x-2)(x-3)
    ok, why = C.check(cert)
    assert ok, why
    cert2 = C.certify_polynomial_root([2, -1, -3], "3/2")  # 2x^2-x-3 = (2x-3)(x+1); 3/2 is a root
    ok2, why2 = C.check(cert2)
    assert ok2, why2


def test_forged_polynomial_root_is_rejected():
    import pytest
    with pytest.raises(ValueError):
        C.certify_polynomial_root([1, -5, 6], 4)           # p(4)=2, not a root — producer refuses
    forged = C.Certificate("polynomial_root", {"coeffs": [1, -5, 6], "verdict": "root"}, {"root": "4"})
    ok, _ = C.check(forged)                                 # and the independent checker rejects the lie
    assert not ok


def test_linear_system_certificate_checks():
    cert = C.certify_linear_system([[2, 1], [1, 3]], [5, 10], [1, 3])   # [[2,1],[1,3]]·[1,3]=[5,10]
    ok, why = C.check(cert)
    assert ok, why


def test_forged_linear_system_is_rejected():
    import pytest
    with pytest.raises(ValueError):
        C.certify_linear_system([[2, 1], [1, 3]], [5, 10], [1, 2])     # [1,2] does not solve
    forged = C.Certificate("linear_system",
                           {"verdict": "solves", "A": [["2", "1"], ["1", "3"]], "b": ["5", "10"]},
                           {"x": ["1", "2"]})
    ok, _ = C.check(forged)
    assert not ok


def test_certificate_rides_the_sealed_record_and_rechecks():
    """The spine: a certificate carried through record_from_derivation survives into the sealed
    WitnessRecord, and recheck_all re-confirms it from the record ALONE — and catches a tamper."""
    from concordance import receipts
    cert = C.to_dict(C.certify_primality(97))
    result = {"verdict": "CONFIRMED", "steps": 1, "confirmed_steps": 1,
              "trail": [{"id": "number_theory.primality", "domain": "number_theory",
                         "claim": "97 is prime", "status": "CONFIRMED", "uses": [],
                         "link_ok": True, "spec_hash": "", "certificate": cert}]}
    rec = receipts.record_from_derivation(result, domain="number_theory").to_dict()
    carried = [(vr.get("data") or {}).get("certificate") for vr in rec["verifier_results"]]
    assert any(isinstance(c, dict) and c.get("kind") == "primality" for c in carried), \
        "the certificate did not ride into the sealed record"
    rows = C.recheck_all(rec)
    assert rows and all(r["ok"] for r in rows), f"re-check from the sealed record failed: {rows}"
    for vr in rec["verifier_results"]:                     # forge the sealed verdict...
        c = (vr.get("data") or {}).get("certificate")
        if c:
            c["claim"]["verdict"] = "composite"
    assert any(not r["ok"] for r in C.recheck_all(rec)), "a tampered sealed certificate slipped through"
