"""Unit-pin the cybersecurity verifier (A2, 2026-10-06). Password entropy = length * log2(charset)
(10 chars, 95 printable ASCII -> ~65.7 bits); a /24 subnet has 254 usable hosts. Wrong claim caught; NA."""
from __future__ import annotations
from concordance.verifiers import cybersecurity as CY


def test_password_entropy():
    assert CY.verify_password_entropy({"password_length": 10, "charset_size": 95, "claimed_entropy_bits": 65.7}).status == "CONFIRMED"
    assert CY.verify_password_entropy({"password_length": 10, "charset_size": 95, "claimed_entropy_bits": 30.0}).status == "MISMATCH"
    assert CY.verify_password_entropy({}).status == "NOT_APPLICABLE"


def test_subnet_hosts():
    assert CY.verify_subnet_hosts({"cidr_prefix": 24, "claimed_host_count": 254}).status == "CONFIRMED"
    assert CY.verify_subnet_hosts({"cidr_prefix": 24, "claimed_host_count": 100}).status == "MISMATCH"
