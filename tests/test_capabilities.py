"""The capability statement is LIVE — computed, defined, ungated, and it cannot go stale.

Restores the guard 1.0 had: Matt's standing rule (2026-06-10) is "do NOT hardcode capability counts
— they drift and break trust." With no live endpoint in 2.0, they drifted again. These tests pin the
properties that make the statement trustworthy:

  * every count is DERIVED from the live registries — change a registry, the number moves with it
    (this is what makes hardcoding unnecessary, and it is asserted, not hoped for);
  * every count carries a 'means' line, so "130 domain names accepted" can never be misread as
    "130 capabilities" — the exact confusion that produced three different verifier counts on one
    site;
  * the statement is UNGATED on both surfaces (a reader who cannot check our claims cannot trust
    them) while still telling the truth about per-surface tool counts.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import capabilities, mcp  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402

WIT = EngineConfig("witness")
SEC = EngineConfig("secular")


def test_every_count_carries_its_definition():
    """A bare number is how the drift happened. Each one must say what it counted."""
    s = capabilities.statement("secular")
    for group in ("verifiers", "routes", "substrate"):
        for key, val in s[group].items():
            assert isinstance(val, dict), f"{group}.{key} must be a dict with count + means"
            assert "count" in val, f"{group}.{key} has no count"
            assert val.get("means") or val.get("unavailable"), \
                f"{group}.{key} has a count with no 'means' — that is how a number gets misread"
    assert s["tools"]["means"]


def test_counts_are_derived_from_the_live_registries_not_written_down():
    """The anti-staleness property: perturb a registry, the statement follows."""
    from concordance import verifiers as V
    before = capabilities.statement("secular")["verifiers"]["secular_modules"]["count"]
    sentinel = object()

    class _FakeMod:
        __name__ = "concordance.verifiers._sentinel_for_test"

        @staticmethod
        def run(_packet):
            return []

    V.VERIFIERS["_sentinel_for_test"] = _FakeMod
    try:
        after = capabilities.statement("secular")["verifiers"]["secular_modules"]["count"]
    finally:
        V.VERIFIERS.pop("_sentinel_for_test", None)
    assert after == before + 1, "the count did not follow the registry — it is not really derived"
    assert capabilities.statement("secular")["verifiers"]["secular_modules"]["count"] == before
    assert sentinel is not None  # keep the local referenced; the assertion above is the real check


def test_alias_names_are_never_presented_as_capabilities():
    s = capabilities.statement("secular")
    v = s["verifiers"]
    assert v["domain_names_accepted"]["count"] > v["distinct_modules_total"]["count"], \
        "aliases should outnumber modules; if not, the two counts are measuring the same thing"
    assert "alias" in v["domain_names_accepted"]["means"].lower()
    assert "NOT a count of capabilities" in v["domain_names_accepted"]["means"]
    # The honest answer to "how many verifiers" is the distinct-module total. Registry values may be
    # module objects OR lazy import strings, so identity is taken the same way capabilities.py takes
    # it — that tolerance is deliberate in the module and must not be "tightened" here.
    from concordance import verifiers as V
    distinct = {getattr(m, "__name__", str(m))
                for m in list(V.VERIFIERS.values()) + list(V.WITNESS_VERIFIERS.values())}
    assert v["distinct_modules_total"]["count"] == len(distinct)


def test_statement_is_ungated_on_both_surfaces_but_surface_aware():
    st_sec, sec = dispatch("GET", "/capabilities", {}, None, SEC)
    st_wit, wit = dispatch("GET", "/capabilities", {}, None, WIT)
    assert st_sec == 200 and st_wit == 200, "the capability statement must never be gated"
    assert sec["surface"] == "secular" and wit["surface"] == "witness"
    # the witness surface genuinely exposes more tools; the statement must say so, not flatten it
    assert wit["tools"]["count"] > sec["tools"]["count"]
    assert "harmony" in wit["tools"]["names"] and "harmony" not in sec["tools"]["names"]


def test_the_mission_string_is_the_frozen_one():
    assert capabilities.MISSION == (
        "Narrow Highway gives humans and agents a governed way to find, check, use, and preserve "
        "information without losing its source, authority, or history.")
    assert dispatch("GET", "/capabilities", {}, None, SEC)[1]["mission"] == capabilities.MISSION


def test_boundaries_state_the_refusals_plainly():
    b = capabilities.statement("secular")["boundaries"]
    assert b["generated"] is False
    assert b["authority_is_never_silently_upgraded"] is True
    assert b["declines_when_it_cannot_verify"] is True
    assert b["no_account_required"] is True
    assert "parity" in b


def test_mcp_capabilities_tool_is_on_both_surfaces():
    for cfg, label in ((SEC, "secular"), (WIT, "witness")):
        names = {t["name"] for t in mcp.handle(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, cfg)["result"]["tools"]}
        assert "capabilities" in names, f"agents on the {label} surface cannot read the statement"
    c = mcp.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "capabilities", "arguments": {}}}, WIT)
    body = json.loads(c["result"]["content"][0]["text"])
    assert body["surface"] == "witness" and body["verifiers"]["distinct_modules_total"]["count"] > 0


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} capability tests passed — computed, defined, ungated, cannot go stale.")
