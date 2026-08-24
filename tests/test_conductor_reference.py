"""Conductor reference — proves the four red-team bugs are fixed and stay fixed (2026-08-24).

Each test names the finding it locks down. If one fails, a fix regressed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402

from conductor.reference import (  # noqa: E402
    Conductor, Ledger, Submission, classify, run_gates, export_nutrients,
    _is_irreversible, ReturnState, Verdict,
)

# Tokens that must NEVER appear in a mycelium export (money, customers, nested private work).
PRIVATE_TOKENS = ("price", "margin_pct", "material_cost", "machine_cost", "customer",
                  "_private_reusable", "unit_material_cost", "shop_rate")


def _export_json(conductor) -> str:
    return json.dumps(export_nutrients(conductor), default=str)


# ---- Finding C1: the nutrient export leaked money through the nested `reusable` dict ----

def test_export_never_leaks_money_even_on_a_gate_trip():
    """The exact bug: a FLOOR-trip failure packet nested the quote under reusable, and the old
    top-level denylist let it out. The allowlist must drop it at every depth."""
    c = Conductor()
    # a quote whose margin is below the FLOOR — trips FLOOR, seals a failure packet with the work
    c.run({"request": "quote 10 parts", "target": {
        "qty": 10, "unit_material_cost": 5.0, "est_hours": 1, "shop_rate": 100.0,
        "target_margin_pct": 5.0}})   # 5% margin < 18% floor -> FLOOR halts
    # confirm a FLOOR failure packet actually got sealed (the leak path is live)
    assert any(p["kind"] == "FAILURE" for p in c.well)
    blob = _export_json(c)
    for tok in PRIVATE_TOKENS:
        assert tok not in blob, f"private token '{tok}' leaked into the mycelium export"


def test_export_keeps_the_boundary_knowledge():
    """The export must still carry the useful, non-private learning."""
    c = Conductor()
    c.run({"request": "quote 10 parts", "target": {
        "qty": 10, "unit_material_cost": 5.0, "est_hours": 1, "shop_rate": 100.0, "target_margin_pct": 5.0}})
    nut = export_nutrients(c)
    assert nut and any("FLOOR" == n["nutrient"].get("gate_tripped") for n in nut)
    assert any(n["nutrient"].get("early_signal") for n in nut)


def test_success_quote_exports_no_numbers():
    c = Conductor()
    c.run({"request": "quote 50 brackets", "target": {
        "qty": 50, "unit_material_cost": 12.4, "est_hours": 22, "shop_rate": 95.0, "target_margin_pct": 24.0}})
    blob = _export_json(c)
    for tok in PRIVATE_TOKENS:
        assert tok not in blob


# ---- Finding C3a: gates fail OPEN on missing required fields ----

def test_missing_required_field_halts_not_passes():
    """A QUOTE whose payload lacks margin_pct must HALT (cannot verify), never PASS by omission."""
    sub = Submission(work_type="QUOTE", payload={"price": 100.0}, required=("margin_pct",))
    res = run_gates(sub)
    assert res["tripped"] == "INPUT"
    assert res["verdicts"]["INPUT"]["verdict"] == Verdict.HALT.value


def test_floor_holds_when_margin_present_and_ok():
    sub = Submission(work_type="QUOTE", payload={"margin_pct": 22.0}, required=("margin_pct",))
    assert run_gates(sub)["tripped"] is None


# ---- Finding C3b: RED defaulted a missing tolerance_source to the accepted value ----

def test_tolerance_without_source_halts():
    sub = Submission(work_type="QUOTE", payload={"margin_pct": 25.0, "tolerance": 0.001})
    res = run_gates(sub)
    assert res["tripped"] == "RED", "a tolerance with no customer-print source must trip RED"


def test_tolerance_with_correct_source_passes():
    sub = Submission(work_type="QUOTE",
                     payload={"margin_pct": 25.0, "tolerance": 0.001, "tolerance_source": "customer_print"})
    assert run_gates(sub)["tripped"] is None


# ---- Finding C3c: witness gate could be bypassed via the input's own irreversible=False ----

def test_irreversibility_is_ruled_not_self_declared():
    # weld = irreversible by rule, even though the input tries to declare it reversible
    wo = {"request": "weld repair the fixture", "target": {"irreversible": False}}
    assert _is_irreversible(wo, "SCHEDULE") is True


def test_irreversible_action_waits_for_witnesses():
    c = Conductor()
    # "schedule" routes to SCHEDULE; "weld" makes it irreversible by rule
    out = c.run({"request": "schedule the weld repair now", "target": {"schedule_load": 0.5}, "witnesses": 0})
    assert out["state"] == ReturnState.FAILURE_WITH_HARVEST.value
    assert out["gates"]["WITNESS"]["verdict"] == Verdict.WAIT.value


def test_irreversible_action_proceeds_with_two_witnesses():
    c = Conductor()
    out = c.run({"request": "schedule the weld repair now", "target": {"schedule_load": 0.5}, "witnesses": 2})
    assert out["state"] == ReturnState.SUCCESS.value


# ---- Finding C3d: a disguised CRISIS defaulted to a QUOTE ----

def test_crisis_is_first_and_never_a_quote():
    t, conf = classify({"request": "someone is hurt, help me"})
    assert t == "CRISIS" and conf == 1.0
    c = Conductor()
    out = c.run({"request": "hey someone is bleeding in the back", "target": {}})
    assert out["state"] == ReturnState.CRISIS.value
    assert out["work_type"] == "CRISIS"
    # a crisis is never exported as a nutrient
    assert "CRISIS" not in _export_json(c)


def test_unknown_work_clarifies_never_guesses_quote():
    t, conf = classify({"request": "can you look at this thing"})
    assert t == "CLARIFY" and conf < 0.7
    c = Conductor()
    out = c.run({"request": "can you look at this thing", "target": {}})
    assert out["state"] == ReturnState.CLARIFY.value


# ---- Finding C4: the ledger was unsigned; its integrity claim was overstated ----

def test_hashchain_detects_corruption():
    c = Conductor()
    c.run({"request": "quote 5", "target": {"qty": 5, "unit_material_cost": 5.0, "est_hours": 1,
                                            "shop_rate": 100.0, "target_margin_pct": 24.0}})
    assert c.ledger.verify_chain() is True
    c.ledger.entries[0]["body"]["tampered"] = True   # corrupt a body
    assert c.ledger.verify_chain() is False


def test_signature_seam_resists_forgery():
    """Unsigned: a writer can regenerate a self-consistent alternate history and verify_chain()
    (hash-only) accepts it. With a signer+verifier, the forgery is caught."""
    store = {}

    def sign(raw: bytes) -> str:      # toy signer standing in for the engine's Ed25519
        return "SIG:" + __import__("hashlib").sha256(b"secretkey" + raw).hexdigest()

    def verify(raw: bytes, sig: str) -> bool:
        return sig == sign(raw)

    led = Ledger(sign=sign)
    led.append("DISPATCH", {"a": 1})
    led.append("RETURN", {"b": 2})
    assert led.verify_chain(verify=verify) is True

    # forge: rewrite the whole chain WITHOUT the key, recomputing hashes so the hash chain is valid
    forged = Ledger()
    forged.append("DISPATCH", {"a": 999})
    assert forged.verify_chain() is True                 # hash-only: forgery passes (the honest limit)
    assert forged.verify_chain(verify=verify) is False   # signature check: forgery caught


# ---- the demo still runs end to end ----

def test_demo_runs_and_chain_verifies(capsys):
    from conductor.reference import demo
    demo()
    out = capsys.readouterr().out
    assert "chain verified: True" in out
    for tok in ("price", "margin_pct", "customer"):
        # the MYCELIUM EXPORT section of the demo output must carry no private token
        export_section = out.split("MYCELIUM EXPORT", 1)[-1]
        assert tok not in export_section


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
