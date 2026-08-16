"""The moral-constraint scan wired into the governance MOAT (LH-2b). engine.py's governance validation
was purely structural — a well-typed DECISION_PACKET whose way_path DESCRIBES a wrong passed. Now a RED
non-negotiable in the decision's own plan REJECTS at the RED gate, a FLOOR 'error' at the FLOOR gate,
a FLOOR 'warn' rides along; a negated mention ("we will NOT deceive") does not fire. Pure (skip schema,
no verifiers)."""
from concordance import engine
from concordance.config import EngineConfig

_CFG = EngineConfig(run_verifiers=False, skip_schema_validation=True)


def _packet(way_path, execution_steps=None):
    return {"domain": "governance", "DECISION_PACKET": {
        "title": "A plan", "scope": "local", "red_items": ["x"], "floor_items": ["y"],
        "way_path": way_path, "execution_steps": execution_steps or ["do it"],
        "witnesses": ["Alice", "Bob"]}}


def _validate(packet):
    return engine._run_validation(packet, now_epoch=10_000_000_000, config=_CFG)


def test_a_governance_plan_that_describes_a_wrong_is_rejected_at_RED():
    gates, _v, status = _validate(_packet("we will prey on the vulnerable and use fake testimonials"))
    assert status == "REJECT"
    assert any(g.gate == "RED" and g.status == "REJECT" and "RED-" in " ".join(g.reasons) for g in gates)


def test_a_financial_stability_floor_error_is_rejected_at_FLOOR():
    gates, _v, status = _validate(_packet("run it as a ponzi with no reserve, pay old with new"))
    assert status == "REJECT"
    assert any(g.gate == "FLOOR" and g.status == "REJECT" for g in gates)


def test_a_transparency_warn_rides_along_but_does_not_veto():
    # the way_path names a warn-level concern but is otherwise clean → not rejected on the moral scan
    gates, _v, status = _validate(_packet("charge an undisclosed fee at signup", execution_steps=["bill them"]))
    assert status != "REJECT"
    assert any(g.gate == "FLOOR" and "warnings" in (g.details or {}) for g in gates)


def test_a_negated_mention_does_not_reject():
    gates, _v, status = _validate(_packet("we will not deceive anyone; avoid all coercion; no hidden fees"))
    assert status != "REJECT"


def test_a_plain_good_plan_passes_the_moral_scan():
    # a clean governance plan is not rejected by the moral scan (it reaches PATH/WITNESS/WAIT as before)
    gates, _v, status = _validate(_packet("lend tools to neighbors and log who borrowed what, openly"))
    assert not any(g.status == "REJECT" and "RED-" in " ".join(g.reasons) for g in gates
                   if g.gate in ("RED", "FLOOR"))
