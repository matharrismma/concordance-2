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


# ── read-only helpers: canonical / depth / adjacent / dimension_axes / umbrella_children ──────────
def test_pure_grid_helpers():
    if grid.ALIASES:                                   # an alias resolves to its canonical axis
        alias, canon = next(iter(grid.ALIASES.items()))
        assert grid.canonical(alias) == canon
    assert grid.canonical("unknown_axis_xyz") == "unknown_axis_xyz"   # unknown passes through
    assert grid.depth("biology") == len(grid.AXIS_DIMENSIONS["biology"])
    adj = grid.adjacent("biology")                     # neighbours share ≥1 dimension, overlap-sorted
    assert adj and all(len(shared) >= 1 for _a, shared in adj)
    if len(adj) >= 2:
        assert len(adj[0][1]) >= len(adj[1][1])
    assert isinstance(grid.dimension_axes(grid.DIMENSIONS[0]), list)
    try:
        grid.dimension_axes("phantom_dimension_xyz")
        assert False, "unknown dimension must raise"
    except ValueError:
        pass
    if grid.UMBRELLAS:
        parent = next(iter(grid.UMBRELLAS))
        assert grid.umbrella_children(parent) == grid.UMBRELLAS[parent]
    assert grid.umbrella_children("no_such_umbrella_xyz") == ()


# ── the mutating journal: add_axis / remove_axis / _load_axis_extensions ──────────────────────────
# These mutate the module globals DIMENSIONS/AXIS_DIMENSIONS and write a hardcoded repo file, so each
# test snapshots and restores the globals and redirects _AXIS_EXT_FILE to a temp path (never the repo).
def _snapshot():
    return list(grid.DIMENSIONS), dict(grid.AXIS_DIMENSIONS), grid._AXIS_EXT_FILE


def _restore(snap):
    dims, ax, extfile = snap
    grid.DIMENSIONS[:] = dims
    grid.AXIS_DIMENSIONS.clear()
    grid.AXIS_DIMENSIONS.update(ax)
    grid._AXIS_EXT_FILE = extfile


def test_add_then_remove_axis_round_trip():
    import tempfile
    snap = _snapshot()
    try:
        with tempfile.TemporaryDirectory() as t:
            grid._AXIS_EXT_FILE = Path(t) / "axis_extensions.jsonl"
            rec = grid.add_axis("recurrence_x", "Recurrence",
                                "a value defined by earlier values", ["biology", "physics"])
            assert rec["name"] == "recurrence_x"
            assert "recurrence_x" in grid.DIMENSIONS
            assert "recurrence_x" in grid.AXIS_DIMENSIONS["biology"]
            assert grid._AXIS_EXT_FILE.exists()
            assert "biology" in grid.dimension_axes("recurrence_x")

            r = grid.remove_axis("recurrence_x")
            assert r["removed_entries"] == 1
            assert "recurrence_x" not in grid.DIMENSIONS
            assert "recurrence_x" not in grid.AXIS_DIMENSIONS["biology"]
            assert "# REMOVED" in grid._AXIS_EXT_FILE.read_text(encoding="utf-8")
    finally:
        _restore(snap)


def test_add_axis_validation_and_remove_errors():
    import tempfile
    snap = _snapshot()
    try:
        with tempfile.TemporaryDirectory() as t:
            grid._AXIS_EXT_FILE = Path(t) / "ext.jsonl"

            def _rejects(fn):
                try:
                    fn()
                    assert False, "expected ValueError"
                except ValueError:
                    pass
            _rejects(lambda: grid.add_axis("ab", "l", "crit", ["biology"]))          # name too short
            _rejects(lambda: grid.add_axis("goodname", "l", "", ["biology"]))        # no criterion
            _rejects(lambda: grid.add_axis("goodname", "l", "crit", []))             # no carriers
            _rejects(lambda: grid.add_axis("goodname", "l", "crit", ["not_a_domain"]))  # unknown carrier
            _rejects(lambda: grid.add_axis(grid.DIMENSIONS[0], "l", "crit", ["biology"]))  # already a dim
            # remove: invalid name, and no journal / no entry
            _rejects(lambda: grid.remove_axis("BAD NAME"))
            _rejects(lambda: grid.remove_axis("goodname"))    # journal file does not exist yet
    finally:
        _restore(snap)


def test_load_axis_extensions_skips_comments_and_bad_json():
    import tempfile
    snap = _snapshot()
    try:
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "ext.jsonl"
            f.write_text('# a comment\n\n{"name":"good_x","carriers":["biology"]}\nnot json here\n',
                         encoding="utf-8")
            grid._AXIS_EXT_FILE = f
            loaded = grid._load_axis_extensions()
            assert len(loaded) == 1 and loaded[0]["name"] == "good_x"
    finally:
        _restore(snap)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} grid tests passed — scaffold consistent, member invariant holds.")
