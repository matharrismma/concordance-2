"""Grid scaffold invariant — every axis sits only on declared members.

This is the floor invariant the review asked for: it would have caught biology sitting on
an undeclared 'discreteness'. 'discreteness' is now a declared member (the "missing-1" fix),
so the scaffold is consistent. Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import grid  # noqa: E402


def test_every_axis_member_is_declared():
    violations = grid.check_dimension_members()
    assert violations == [], f"axes on undeclared members: {violations}"


def test_discreteness_is_declared_and_carried_by_biology():
    assert "discreteness" in grid.DIMENSIONS
    assert "discreteness" in grid.AXIS_DIMENSIONS["biology"]


def test_floor_consumes_axis_coords_for_biology():
    from concordance.record import axis_coords_for
    ac = axis_coords_for("biology")
    assert ac is not None and "discreteness" in ac.dimensions


def test_axis_view_and_overview():
    v = grid.axis_view("mathematics")
    assert v and v["axis"] == "mathematics" and "reasoning" in v["dimensions"]
    assert "depth" in v and isinstance(v["adjacent"], list)
    assert grid.axis_view("nonsense_xyz") is None
    o = grid.overview()
    assert o["count"] > 0 and "mathematics" in o["axes"] and "reasoning" in o["dimensions"]


def test_grid_http_and_mcp():
    import json as _j

    from concordance.config import EngineConfig
    from concordance.mcp.server import handle
    from concordance.web.api import dispatch
    sec = EngineConfig("secular")
    assert dispatch("GET", "/grid", {"axis": "mathematics"}, None, sec)[1]["axis"] == "mathematics"
    assert dispatch("GET", "/grid", {}, None, sec)[1]["count"] > 0
    assert "mathematics" in dispatch("GET", "/grid/dimension", {"d": "reasoning"}, None, sec)[1]["axes"]
    assert dispatch("GET", "/grid", {"axis": "nope_xyz"}, None, sec)[0] == 404
    r = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {"name": "grid_axis", "arguments": {"axis": "physics"}}}, sec)
    assert _j.loads(r["result"]["content"][0]["text"])["axis"] == "physics"
    names = [t["name"] for t in handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, sec)["result"]["tools"]]
    assert {"grid_axis", "grid_dimension"} <= set(names)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} grid tests passed — scaffold consistent, member invariant holds.")
