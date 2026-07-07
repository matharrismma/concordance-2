"""Grid atlas — the read-only exploration/render/CLI layer split out of grid.py.

Proves the split holds: grid_atlas imports the live scaffold from grid (no circular
import), and every moved function still reads the same runtime AXIS_DIMENSIONS/DIMENSIONS
the engine uses. Runnable with pytest OR `python tests/test_grid_atlas.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import grid, grid_atlas  # noqa: E402


def test_atlas_reads_live_scaffold():
    # the atlas sees the SAME runtime scaffold as the engine core (shared objects)
    assert grid_atlas.axis_dimensions("mathematics") == grid.AXIS_DIMENSIONS["mathematics"]
    assert grid_atlas.deep_axes(), "expected at least one structurally deep axis"


def test_predict_dimensions_places_a_claim():
    dims = grid_atlas.predict_dimensions("a proof about prime numbers and logic")
    assert "reasoning" in dims
    assert all(d in grid.DIMENSIONS for d in dims)  # only live dimensions survive
    assert grid_atlas.predict_dimensions("") == frozenset()


def test_alias_helpers():
    assert isinstance(grid_atlas.is_alias("not_an_alias_xyz"), bool)
    ca = grid_atlas.canonical_axes()
    assert isinstance(ca, dict) and ca
    assert all(not grid_atlas.is_alias(name) for name in ca)  # aliases collapsed out


def test_umbrella_coherence_is_a_dict():
    breaks = grid_atlas.verify_umbrella_coherence()
    assert isinstance(breaks, dict)


def test_renderers_produce_text():
    assert "| axis |" in grid_atlas.render_matrix()
    assert grid_atlas.render_depth().strip()
    assert "sits on" in grid_atlas.render_adjacent("mathematics")
    assert "axes on reasoning" in grid_atlas.render_dimension("reasoning")
    assert "unknown axis" in grid_atlas.render_adjacent("nonsense_xyz")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} grid_atlas tests passed — the split holds, the atlas reads the live scaffold.")
