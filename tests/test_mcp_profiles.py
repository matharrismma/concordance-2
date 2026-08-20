"""The MCP profiles — every tool on exactly one plane, and the planes hold their shape.

Task #123, specified by docs/MCP_ASSESSMENT_2026-08-04.md §3.3. The properties pinned here are
the ones that rot silently: the partition (a tool in two profiles, or in none, breaks permission
review without breaking any call), the effect vocabulary (risk metadata a client can trust), the
read-only planes staying read-only, and the social plane staying a deliberate deployment
decision rather than a default.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.config import EngineConfig  # noqa: E402
from concordance.mcp import handle  # noqa: E402
from concordance.mcp.server import EFFECTS, PROFILES, profile_of  # noqa: E402

SEC = EngineConfig()


def _full_catalog():
    r = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, SEC)
    return {t["name"] for t in r["result"]["tools"]}


def test_the_partition_is_exact():
    """Every exposed tool in exactly ONE profile; every profiled tool actually exposed.

    Both directions matter: an unprofiled tool escapes permission review, and a phantom profile
    entry silently excuses a tool that no longer exists (the stale-declaration failure the
    reachability tests already guard against for routes)."""
    catalog = _full_catalog()
    profiled = [t for p in PROFILES.values() for t in p["tools"]]
    assert len(profiled) == len(set(profiled)), (
        "a tool appears in more than one profile: "
        + str({t for t in profiled if profiled.count(t) > 1}))
    assert set(profiled) == catalog, (
        f"unprofiled tools: {catalog - set(profiled)}; phantom entries: {set(profiled) - catalog}")


def test_every_effect_is_from_the_declared_vocabulary():
    for pname, p in PROFILES.items():
        for tool, effect in p["tools"].items():
            assert effect in EFFECTS, f"{pname}.{tool} has undeclared effect '{effect}'"
        assert p["description"].strip() and p["version"].count(".") == 2


def test_core_stays_small_a_ratchet():
    """The consolidation directive made countable: core is the front door, and a front door with
    dozens of handles is a wall. Raising this number is a decision, not a drift."""
    assert len(PROFILES["core"]["tools"]) <= 12, sorted(PROFILES["core"]["tools"])


def test_the_read_planes_hold_no_publish_or_external_tools():
    """core and library must never gain a tool that changes the world outside the caller's own
    records — that is the whole point of mounting narrow."""
    for pname in ("core", "library", "witness", "coach"):
        bad = {t: e for t, e in PROFILES[pname]["tools"].items()
               if e in ("publish", "external_action")}
        assert not bad, f"{pname} holds world-changing tools: {bad}"


def test_every_publish_tool_lives_on_the_community_plane():
    for pname, p in PROFILES.items():
        for tool, effect in p["tools"].items():
            if effect == "publish":
                assert pname == "community", f"publish-class '{tool}' escaped to '{pname}'"


def test_a_mounted_profile_lists_only_its_plane_with_effects():
    r = handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, SEC, profile="library")
    tools = r["result"]["tools"]
    names = {t["name"] for t in tools}
    assert names == set(PROFILES["library"]["tools"]) & _full_catalog()
    assert all(t.get("effect") in EFFECTS for t in tools), "a listed tool carries no effect class"


def test_a_cross_plane_call_is_refused_by_name_with_directions():
    """The refusal must say where the tool lives — a boundary with a sign, not a void."""
    r = handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {"name": "verify", "arguments": {}}}, SEC, profile="library")
    assert "error" in r
    assert "not in the mounted profile 'library'" in r["error"]["message"]
    assert "/mcp/core" in r["error"]["message"]


def test_a_call_inside_the_mounted_plane_still_works():
    r = handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                "params": {"name": "now", "arguments": {}}}, SEC, profile="core")
    body = r["result"]["content"][0]["text"] if "content" in r.get("result", {}) else json.dumps(r["result"])
    assert "utc" in body


def test_the_full_catalog_on_mcp_is_unchanged_a_golden():
    """Existing clients keep the wide door until narrowing is a deliberate cutover. 94 tools
    (83 + 3 Candidate Engine, #135 + 2 deck, 2026-08-12 + 2 gate-kernel, #152 + 3 Playbook, #153,
    2026-08-15 + 1 discern, 2026-08-20): this golden moves only when the catalog does, and moving it is
    a conscious act. `discern` is the sanctioned rise here — the proposal half of the two-door core
    ('discern proposes, verify disposes'), a read-class tool on the `library` profile next to `ask`. +1,
    deliberate."""
    assert len(_full_catalog()) == 94


def test_the_witness_gate_semantics_survive_the_mount():
    """Mounting /mcp/witness narrows DISCOVERY; it must not widen ACCESS — the Gate's rules are
    the same on every door (one rule, both doors, per _tools_for's own contract)."""
    wide = handle({"jsonrpc": "2.0", "id": 5, "method": "tools/list"}, SEC)
    narrow = handle({"jsonrpc": "2.0", "id": 6, "method": "tools/list"}, SEC, profile="witness")
    wide_names = {t["name"] for t in wide["result"]["tools"]}
    narrow_names = {t["name"] for t in narrow["result"]["tools"]}
    assert narrow_names <= wide_names, "a mount surfaced a tool the full door does not show"


def test_the_route_mounts_and_the_profiles_cannot_drift_apart():
    """dispatch() enumerates the mounts literally so the route auditor can see them; this pins
    that enumeration to PROFILES, so adding a profile without its mount (or a mount without its
    profile) fails here instead of appearing as a mystery 404 in production."""
    from concordance.web import api
    mounted = {r["path"][len("/mcp/"):] for r in api.ROUTES if r["path"].startswith("/mcp/")}
    assert mounted == set(PROFILES), (
        f"mounted-but-unprofiled: {mounted - set(PROFILES)}; "
        f"profiled-but-unmounted: {set(PROFILES) - mounted}")


def test_community_is_a_closed_door_with_a_sign_by_default():
    """The social plane is a deployment decision. Unset env -> 403 that names WHY and lists what
    IS available (refuse abuse, not use: a refusal must name what is available)."""
    from concordance.web import api
    prior = os.environ.pop("CONCORDANCE_COMMUNITY_MCP", None)
    try:
        profile, refusal = api.resolve_mcp_profile("/mcp/community")
        assert profile is None and refusal is not None
        status, body = refusal
        assert status == 403
        assert "governance" in body["why"] and "library" in body["available"]
        os.environ["CONCORDANCE_COMMUNITY_MCP"] = "1"
        profile, refusal = api.resolve_mcp_profile("/mcp/community")
        assert profile == "community" and refusal is None
        p2, r2 = api.resolve_mcp_profile("/mcp/nonsense")
        assert p2 is None and r2[0] == 404 and "profiles" in r2[1]
    finally:
        if prior is None:
            os.environ.pop("CONCORDANCE_COMMUNITY_MCP", None)
        else:
            os.environ["CONCORDANCE_COMMUNITY_MCP"] = prior
