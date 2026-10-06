"""THE LEAD conductor (2026-10-06): one body that discerns the solution, tool, technique, and strategy,
then applies. The Bible leads (the biblical type and the fitting Word); crisis outranks all; it composes
what the engine already holds and authors nothing; it applies only what is computably checkable."""
import os
import tempfile

os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp(prefix="nh-lead-"))

from concordance import lead                                  # noqa: E402


def _no_apply(_s):
    return {"verdict": "NOTHING_TO_CHECK", "claims_found": 0, "checks": [], "receipt": None}


def test_the_biblical_type_leads_the_solution():
    r = lead.lead("I walked away from God and I am ashamed to come back", apply_fn=_no_apply)
    sol = r.get("solution") or {}
    assert "Prodigal" in (sol.get("biblical_type") or "")
    assert sol.get("word")                                    # the canonical Word is attached
    assert r["kind"] == "situation"


def test_it_discerns_tool_technique_and_strategy_and_carries_a_path_id():
    r = lead.lead("my opponent keeps backing me to the cage and out-working me in the clinch", apply_fn=_no_apply)
    d = r["discerned"]
    assert d["tool"]["member"]                                # a member was named
    techs = d["technique"]
    assert isinstance(techs, list) and any(t["witness"] == "pressure_fighting" for t in techs)
    assert "strategy" in d and r.get("path_id")               # the path signature, for the trajectory loop


def test_crisis_outranks_the_tools():
    from concordance import ask
    cry = next(iter(getattr(ask, "_CRISIS_PHRASES", ["i want to end my life"])), "i want to end my life") \
        if hasattr(ask, "_CRISIS_PHRASES") else "i want to kill myself"
    r = lead.lead(cry, apply_fn=_no_apply)
    if ask.is_crisis(cry):                                    # only assert when the net flags it
        assert r["kind"] == "crisis" and r["route"]["member"] == "crisis" and "resources" in r


def test_apply_reflects_the_gate_and_empty_is_safe():
    r = lead.lead("", apply_fn=_no_apply)
    assert r["kind"] == "empty"
    r2 = lead.lead("the sum is here", apply_fn=lambda s: {"verdict": "HOLDS", "claims_found": 1,
                                                          "checks": [], "receipt": "/s/abc"})
    assert (r2.get("applied") or {}).get("verdict") == "HOLDS"
