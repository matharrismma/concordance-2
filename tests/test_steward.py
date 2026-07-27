"""Steward — the money-management helper that NEVER moves money.

Proves the deterministic budget + cost-destroyed math, the hard money-move/advice guardrail, the
sealed budget endpoint, and the MCP tools. Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-steward-")

from concordance import steward, mcp  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402

SEC = EngineConfig("secular")


def test_budget_math():
    b = steward.budget(1000, [{"label": "rent", "amount": 600, "category": "housing"},
                              {"label": "food", "amount": 200, "category": "food"}])
    assert b["income"] == 1000 and b["total_expenses"] == 800 and b["net"] == 200
    assert b["savings_rate_pct"] == 20.0
    assert b["by_category"] == {"housing": 600.0, "food": 200.0}


def test_cost_destroyed_math():
    d = steward.cost_destroyed([{"label": "sub", "was": 15, "now": 0},
                                {"label": "plan", "was": 80, "now": 50}])
    assert d["total_saved"] == 45.0 and d["items"][0]["saved"] == 15.0


def test_a_non_list_expenses_or_items_declines_instead_of_crashing():
    # found: "expenses or []" / "items or []" only substitutes the fallback for a FALSY value —
    # a truthy non-list (e.g. POST /steward/budget with {"expenses": 123}) survived past that
    # guard and crashed "for e in 123" with a TypeError. Both routes require no authentication.
    for bad in (123, "not a list", {"a": 1}):
        b = steward.budget(1000, bad)
        assert b["total_expenses"] == 0
        d = steward.cost_destroyed(bad)
        assert d["total_saved"] == 0.0


def test_extreme_numeric_input_never_produces_inf_or_nan():
    # found: float("1"+"0"*400) parses to inf without raising (float() only rejects unparseable
    # strings, not magnitude). That inf then broke two callers: json.dumps() emits the
    # non-standard Infinity/NaN tokens a strict JSON.parse() rejects, and /steward/budget's
    # round(income*100) (single-arg round() -> int) raised OverflowError on inf — an unhandled
    # 500 for a caller-reachable, unauthenticated POST route. _num() must reject non-finite
    # results at the one place every caller here converts a number.
    huge = "1" + "0" * 400
    b = steward.budget(huge, [{"label": "x", "amount": huge}])
    for v in (b["income"], b["total_expenses"], b["net"], b["savings_rate_pct"]):
        assert v == v and abs(v) != float("inf")          # v == v is False for NaN
    json.dumps(b)                                          # must not emit Infinity/NaN tokens

    d = steward.cost_destroyed([{"label": "y", "was": huge, "now": 1}])
    assert d["items"][0]["was"] == 0.0 and d["total_saved"] == -1.0
    json.dumps(d)


def test_budget_endpoint_survives_extreme_income_without_crashing():
    huge = "1" + "0" * 400
    st, p = dispatch("POST", "/steward/budget", {}, {"income": huge, "expenses": []}, SEC)
    assert st == 200, f"expected a clean 200, got {st}: {p}"          # not an unhandled 500


def test_money_guardrail_declines_moves_and_advice():
    assert steward.money_guardrail("please transfer $500 to my landlord")["kind"] == "move_declined"
    assert steward.money_guardrail("buy bitcoin for me")["kind"] == "move_declined"
    assert steward.money_guardrail("should i buy Tesla stock")["kind"] == "advice_declined"
    assert steward.money_guardrail("help me build a budget") is None


def test_budget_endpoint_seals_the_math():
    st, p = dispatch("POST", "/steward/budget", {},
                     {"income": 1000, "expenses": [{"label": "rent", "amount": 800}]}, SEC)
    assert st == 200 and p["net"] == 200
    assert p.get("seal") and p["seal"].get("content_hash")   # a receipt for your money


def test_ask_endpoint_enforces_the_boundary():
    _st, move = dispatch("POST", "/steward/ask", {}, {"text": "wire money to this account"}, SEC)
    assert move["kind"] == "move_declined"
    _st, ok = dispatch("POST", "/steward/ask", {}, {"text": "what is my savings rate"}, SEC)
    assert ok["kind"] == "ok" and "will_not" in ok
    st, g = dispatch("GET", "/steward", {}, None, SEC)
    assert st == 200 and any("never" in w.lower() or "not" in w.lower() for w in g["will_not"])


def test_mcp_steward_tools():
    r = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, SEC)
    names = {t["name"] for t in r["result"]["tools"]}
    assert {"steward_budget", "steward_cost_destroyed"} <= names
    c = mcp.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "steward_budget", "arguments": {"income": 500, "expenses": []}}}, SEC)
    assert json.loads(c["result"]["content"][0]["text"])["net"] == 500


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} steward tests passed — it stewards the math; it never moves the money.")
