"""Surface hardening — the DoS + abuse guards the review flagged.

Proves: the sliding-window rate limiter caps per key and slides; the derivation
expression-size guard rejects oversized input before sympy; the MCP HTTP transport
rejects a disallowed browser Origin (DNS-rebinding defense) while letting agents (no
Origin) and allowlisted origins through. Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.config import EngineConfig  # noqa: E402


def test_rate_limiter_caps_per_key():
    from concordance.ratelimit import RateLimiter
    rl = RateLimiter(max_events=3, window_s=100)
    assert all(rl.allow("ip", now=1.0 + i) for i in range(3))
    assert rl.allow("ip", now=1.9) is False           # 4th within window -> denied
    assert rl.allow("other", now=1.9) is True          # a different client is unaffected
    assert rl.retry_after("ip", now=1.9) >= 1


def test_rate_limiter_window_slides():
    from concordance.ratelimit import RateLimiter
    rl = RateLimiter(max_events=2, window_s=10)
    assert rl.allow("k", now=0.0)
    assert rl.allow("k", now=1.0)
    assert rl.allow("k", now=2.0) is False
    assert rl.allow("k", now=11.0) is True             # the t=0 hit expired -> room again


def test_expression_size_guard():
    """The guard exists to stop a huge expression from ever reaching the evaluator (DoS). What it
    must guarantee is that the input is REFUSED, cheaply, and never sealed as holding.

    Expected verdict changed BROKEN -> SYSTEM_ERROR on 2026-07-28, and the change is the point:
    declining to evaluate something is a fact about OUR limit, not a finding that the caller's claim
    is false. Under the old behaviour a large but perfectly true expression was told it was BROKEN —
    the same conflation that fix removed (contract §5.6, tests/test_system_error_distinct.py).
    """
    from concordance.derivation import verify
    big = "x+" * 5000 + "1"                              # ~10k chars, over the 4k cap
    r = verify({"mode": "equality", "params": {"expr_a": big, "expr_b": "1", "variables": {}}})
    assert r["verdict"] != "HOLDS", "an unevaluated expression must never be sealed as holding"
    assert r["verdict"] == "SYSTEM_ERROR", "our cap is ours to own — not a verdict on the claim"
    assert r["broken_at"] is None, "we found nothing false; we declined to look"
    assert r["error_at"] is not None, "and we say WHERE we stopped"
    assert any("too large" in (s.get("detail", "")) for s in r["trail"]), "and why, in the trail"


def test_mcp_origin_is_validated():
    from concordance.mcp.http import handle_http
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).encode()
    sec = EngineConfig("secular")
    # a disallowed browser Origin is rejected (DNS-rebinding defense)
    st, _, _ = handle_http("POST", {"Accept": "application/json", "Origin": "https://evil.example"}, body, sec)
    assert st == 403
    # an allowlisted origin is fine
    st2, _, _ = handle_http("POST", {"Accept": "application/json", "Origin": "https://narrowhighway.org"}, body, sec)
    assert st2 == 200
    # no Origin (a non-browser agent) is fine
    st3, _, _ = handle_http("POST", {"Accept": "application/json"}, body, sec)
    assert st3 == 200


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} security tests passed — rate limit, size guard, MCP origin.")
