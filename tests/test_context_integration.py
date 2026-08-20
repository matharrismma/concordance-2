"""Context loop wired to the REAL verifier — the Watchman pass (drive the actual engine, not a fake).

Slow: audit.audit loads the full verifier stack, so these live apart from the instant floor-guard suite
(tests/test_context.py). They prove the closed loop against the real moat, in-process — nothing leaves
the machine, and the verdict comes back with a real re-checkable seal.
"""
from concordance import context


def test_the_loop_closes_against_the_real_engine():
    # a genuinely checkable math claim -> the real moat verifies it and mints a seal
    r = context.run_verified("2 + 2 = 4")
    assert r["ok"] and r["status"] == "HOLDS"
    assert r["checked"] == "2 + 2 = 4"
    assert r["boundary"]["seal"] and "/s/" in r["boundary"]["seal"]     # a real re-checkable seal


def test_attribution_is_stripped_before_the_real_engine_sees_it():
    seen = {}
    real = context.verify_with_engine

    def spy(skeleton):
        seen["skeleton"] = skeleton
        return real(skeleton)

    r = context.run("my mom said 2 + 2 = 4", spy)
    assert seen["skeleton"] == "2 + 2 = 4"        # the engine never saw "my mom said"
    assert r["status"] == "HOLDS" and r["boundary"]["not_checked"] == "my mom said"


def test_verify_with_engine_normalizes_a_verdict_and_seal():
    v = context.verify_with_engine("2 + 2 = 4")
    assert v["status"] == "HOLDS" and v["seal"] and v["statement"].startswith("2 + 2 = 4")


def test_the_node_local_route_runs_the_whole_loop_when_enabled():
    # the sovereign-node endpoint (POST /context/run, flag on) closes the loop behind the node's walls
    import os
    from concordance.config import EngineConfig
    from concordance.web import api
    old = os.environ.get("CONCORDANCE_SOVEREIGN_NODE")
    os.environ["CONCORDANCE_SOVEREIGN_NODE"] = "1"
    try:
        status, payload = api.dispatch("POST", "/context/run", {},
                                       {"text": "my mom said 2 + 2 = 4"}, EngineConfig(), False)
        d = payload.get("data", payload) if isinstance(payload, dict) else payload
        assert status == 200 and d["status"] == "HOLDS" and d["checked"] == "2 + 2 = 4"
        assert d["boundary"]["not_checked"] == "my mom said" and "/s/" in (d["boundary"]["seal"] or "")
    finally:
        if old is None:
            os.environ.pop("CONCORDANCE_SOVEREIGN_NODE", None)
        else:
            os.environ["CONCORDANCE_SOVEREIGN_NODE"] = old


def test_the_node_facing_lighthouse_entry_runs_the_loop():
    from concordance import lighthouse_node
    r = lighthouse_node.context_loop("she said it was 100C in Dayton")
    assert r["checked"] == "it was 100C in Dayton"        # framing stripped, location kept
