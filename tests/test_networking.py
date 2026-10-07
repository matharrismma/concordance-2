"""Unit-pin the networking verifier (A2, 2026-10-06). 192.168.1.1 is a valid IPv4; a /24 subnet has 254
usable hosts (2^8 - 2). Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import networking as NW


def test_ip_format():
    assert NW.verify_ip_format({"address": "192.168.1.1", "claimed_format_valid": True}).status == "CONFIRMED"
    assert NW.verify_ip_format({"address": "192.168.1.1", "claimed_format_valid": False}).status == "MISMATCH"
    assert NW.verify_ip_format({}).status == "NOT_APPLICABLE"


def test_subnet_host_count():
    assert NW.verify_subnet_host_count({"subnet_prefix": 24, "claimed_usable_hosts": 254}).status == "CONFIRMED"
    assert NW.verify_subnet_host_count({"subnet_prefix": 24, "claimed_usable_hosts": 100}).status == "MISMATCH"
