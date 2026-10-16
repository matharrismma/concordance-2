"""Tool dispatch parity — the add-a-tool-forget-the-handler guard (issue #2).

Adding one MCP tool this session (parable) touched FOUR places: the tool list, the `_call_tool` dispatch,
`doors.TOOL_VERB/KIND`, and a `PROFILES` entry — plus a count pin. Verb + profile parity are already pinned
(test_five_doors, test_mcp_profiles). This pins the one still unguarded: every tool the catalog lists has a
branch in `_call_tool`, so a call can never fall through to `raise KeyError('unknown tool')`. (A single tool
registry, issue #2, would make all four one declarative entry; until then, these guards catch the drift.)

Static — reads the dispatch source, executes no tool (no side effects). Runs under pytest OR directly.
"""
from __future__ import annotations

import inspect
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.config import EngineConfig  # noqa: E402
from concordance.mcp import server  # noqa: E402


def _catalog_names() -> set:
    names = set()
    for surface in ("secular", "witness"):
        for t in server._tools_for(EngineConfig(surface), gate_open=True):
            names.add(t["name"])
    return names


def _handled_names() -> set:
    src = inspect.getsource(server._call_tool)
    handled = set(re.findall(r'name == "([a-z0-9_]+)"', src))
    for grp in re.findall(r'name in \(([^)]*)\)', src):          # multi-name branches, e.g. mesh_map/inbox/door
        handled |= set(re.findall(r'"([a-z0-9_]+)"', grp))
    return handled


def test_every_catalog_tool_has_a_dispatch_handler():
    missing = sorted(_catalog_names() - _handled_names())
    assert not missing, ("catalog tools with no branch in _call_tool (a call would raise "
                         f"'unknown tool'): {missing} — add the dispatch, or remove the tool")


def test_catalog_matches_the_single_registry():
    """The other half of issue #2: the single tool registry (concordance.tool_registry) is the source
    of every tool's verb/kind/profile/capability, and `doors`/`PROFILES`/counts derive from it. This
    pins catalog <-> registry: a tool in the catalog with no registry entry has no verb/kind/profile
    (it would vanish from the doors and escape profile review); a registry entry with no catalog tool
    is a phantom. So adding a tool is one registry entry + its schema + its handler — all three checked
    against each other here and above, never silent drift."""
    from concordance import tool_registry
    catalog = _catalog_names()
    reg = set(tool_registry.NAMES)
    assert catalog == reg, (f"catalog-but-not-in-registry: {sorted(catalog - reg)}; "
                            f"registry-but-not-in-catalog: {sorted(reg - catalog)}")


if __name__ == "__main__":
    test_every_catalog_tool_has_a_dispatch_handler()
    print("ok — every catalog tool has a dispatch handler")
