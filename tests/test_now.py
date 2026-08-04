"""The clock — the actual date and time, current at the call, coverage stated.

Matt, 2026-08-04: "One thing that concordance must have is the actual date and time always
current for the time zone you are in." An agent's own 'today' is its training cutoff — months
stale. These tests pin the three properties that make a served clock trustworthy: it is FRESH
(read at the call, not remembered), it is HONEST about zones it cannot resolve (a declared
failure, never a silently wrong offset), and it always carries UTC — the clock the seals are
stamped in — beside any local reading.
"""
from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import ops  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.mcp import handle  # noqa: E402


def _tzdb_available() -> bool:
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo("America/New_York")
        return True
    except Exception:                                          # noqa: BLE001
        return False


def test_utc_is_always_present_and_actually_current():
    """FRESH is the whole point: the reading must be within seconds of this test's own clock,
    and two calls a moment apart must not serve one remembered instant."""
    before = datetime.now(timezone.utc).timestamp()
    n = ops.now()
    after = datetime.now(timezone.utc).timestamp()
    assert before - 2 <= n["utc"]["unix"] <= after + 2, "the served instant is not now"
    assert n["utc"]["iso"].startswith(n["utc"]["date"])
    time.sleep(1.1)
    n2 = ops.now()
    assert n2["utc"]["unix"] > n["utc"]["unix"], "two calls served one remembered instant"


def test_the_home_zone_is_named_and_the_coverage_is_stated():
    n = ops.now()
    assert n["home"]["tz"] == ops.HOME_TZ
    assert "clock_source" in n and "not independently verified" in n["clock_source"]
    assert "never cached" in n["freshness"]
    for k in ("utc", "home", "requested"):
        assert n["means"][k].strip(), f"{k} carries no definition"


@pytest.mark.skipif(not _tzdb_available(), reason="no tz database on this host — the unresolved "
                    "path is exercised instead by test_an_unresolvable_zone_is_declared")
def test_a_resolved_zone_carries_correct_dst_aware_offset():
    """The offset math, checked against zoneinfo's own independent computation — including DST,
    which is where naive clock code goes wrong twice a year."""
    from zoneinfo import ZoneInfo
    n = ops.now(tz="America/New_York")
    r = n["requested"]
    assert r["tz"] == "America/New_York" and "unresolved" not in r
    live = datetime.now(ZoneInfo("America/New_York"))
    off = live.utcoffset().total_seconds()
    want = f"{'+' if off >= 0 else '-'}{int(abs(off)//3600):02d}:{int(abs(off)%3600//60):02d}"
    assert r["utc_offset"] == want
    assert r["dst_in_effect"] == bool(live.dst())
    assert r["iso"][:13] == live.isoformat()[:13]              # same date and hour
    # and UTC still rides beside it — the local reading never replaces the receipts' clock
    assert "utc" in n and n["utc"]["iso"].endswith("+00:00")


def test_an_unresolvable_zone_is_declared_never_guessed():
    """THE HONESTY PROPERTY. A wrong offset served confidently is the worst thing a clock can
    do; 'cannot resolve, and here is why' never is."""
    n = ops.now(tz="Nowhere/Imaginary_Zone")
    r = n["requested"]
    assert r["tz"] == "Nowhere/Imaginary_Zone"
    assert r.get("unresolved"), "an unknown zone came back without a declared failure"
    assert "utc_offset" not in r, "an offset was invented for a zone that does not exist"
    assert n["utc"]["unix"] > 0                                # the call still tells UTC time


def test_the_mcp_tool_serves_the_clock_ungated_with_a_strict_schema():
    """End to end through tools/call on the secular surface, no gate needed — the time of day
    belongs to everyone. And the schema practices MCP-2 discipline from birth: additionalProperties
    false, bounded, patterned."""
    cfg = EngineConfig()
    r = handle({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                "params": {"name": "now", "arguments": {}}}, cfg)
    import json as _json
    payload = _json.loads(r["result"]["content"][0]["text"]) if "content" in r["result"] else r["result"]
    body = payload if "utc" in payload else payload.get("result", payload)
    assert "utc" in body and "home" in body

    tools = handle({"jsonrpc": "2.0", "id": 6, "method": "tools/list"}, cfg)
    schema = next(t for t in tools["result"]["tools"] if t["name"] == "now")["inputSchema"]
    assert schema["additionalProperties"] is False
    assert schema["properties"]["tz"]["maxLength"] == 64
    assert schema["properties"]["tz"]["pattern"].startswith("^")
