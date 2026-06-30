"""Redact — strip personal context to stable placeholders, reapply, and never seal PII.

Proves the deterministic layer (email/SSN/card[Luhn]/IPv4/URL) strips + restores losslessly
with stable tokens, that checksums/ranges keep false positives out, that math text is left
untouched, and — the load-bearing one — that a sealed record stores the REDACTED claim, so
personal data never reaches the permanent ledger. Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import receipts, redact  # noqa: E402

VALID_CARD = "4111111111111111"    # Luhn-valid Visa test number
INVALID_CARD = "4111111111111112"  # one digit off -> not a card


def test_email_ssn_ip_url_stripped_and_restored():
    text = "mail a@b.com, ssn 123-45-6789, ip 10.0.0.1, see https://x.io/p"
    clean, m = redact.redact(text)
    for raw in ("a@b.com", "123-45-6789", "10.0.0.1", "https://x.io/p"):
        assert raw not in clean
    assert "[EMAIL_1]" in clean and "[SSN_1]" in clean and "[IP_1]" in clean and "[URL_1]" in clean
    assert redact.restore(clean, m) == text  # lossless reapply


def test_placeholders_are_stable():
    clean, m = redact.redact("a@b.com then again a@b.com and c@d.com")
    assert clean.count("[EMAIL_1]") == 2 and "[EMAIL_2]" in clean  # same value -> same token


def test_luhn_and_ipv4_guards():
    clean_ok, _ = redact.redact(f"card {VALID_CARD}")
    assert "[CARD_1]" in clean_ok
    clean_bad, m_bad = redact.redact(f"num {INVALID_CARD}")
    assert not m_bad  # fails Luhn -> not redacted
    clean_ip, m_ip = redact.redact("addr 999.1.1.1")
    assert not m_ip  # out-of-range octet -> not an IP


def test_math_text_is_untouched():
    text = "(x-1)*(x+1) = x**2-1"
    clean, m = redact.redact(text)
    assert clean == text and m == {}


def test_has_pii():
    assert redact.has_pii("reach me at a@b.com") is True
    assert redact.has_pii("2 + 2 = 4") is False


def test_seal_stores_redacted_claim_not_pii():
    result = {"verdict": "HOLDS", "steps": 1, "confirmed_steps": 1, "trail": [
        {"id": "s1", "domain": "mathematics", "status": "CONFIRMED", "detail": "ok",
         "claim": "for john@example.com confirm 2+2=4", "uses": [], "link_ok": True}]}
    rec = receipts.record_from_derivation(result)
    stored = rec.verifier_results[0].data["claim"]
    assert "john@example.com" not in stored and "[EMAIL_1]" in stored


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} redact tests passed — strip, restore, guard, and never seal PII.")
