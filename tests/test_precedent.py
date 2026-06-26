"""Precedent test — the grid feeds find_closest (the overlay onto a verdict).

Proves: a sealed PASS record carries grid axis-coordinates; find_closest matches a
same-domain precedent by shared dimensions; an empty ledger returns honest-novel
(precedent_id=None); an unknown axis returns None (no lookup made); and the same-domain
precedent is preferred over an unrelated one. Runnable with `pytest` OR directly.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import EngineConfig, ledger, validate_and_seal  # noqa: E402

_T0 = 1_700_000_000
_PAST = _T0 + 3601  # past the default "local" wait window


def _seal(domain: str, ld: Path, cb: Path, sealed_at: float):
    rec = validate_and_seal({"domain": domain, "created_epoch": _T0, "required_witnesses": 0},
                            now_epoch=_PAST, config=EngineConfig())
    assert rec.overall == "PASS", [(g.gate, g.status) for g in rec.gate_results]
    return ledger.seal_record(rec, summary=f"{domain} precedent", ledger_dir=ld, cas_base=cb,
                              sealed_at=sealed_at)


def test_seal_carries_grid_axis_coords():
    rec = validate_and_seal({"domain": "chemistry", "created_epoch": _T0, "required_witnesses": 0},
                            now_epoch=_PAST, config=EngineConfig())
    assert rec.axis_coords is not None and rec.axis_coords.axis == "chemistry"
    assert rec.axis_coords.dimensions, "grid should give chemistry its dimensions"


def test_find_closest_matches_same_domain():
    with tempfile.TemporaryDirectory() as t:
        ld, cb = Path(t) / "ledger", Path(t) / "cas"
        _seal("chemistry", ld, cb, 1000.0)
        cc = ledger.find_closest({"domain": "chemistry"}, ledger_dir=ld)
        assert cc is not None and cc.precedent_id is not None, cc
        assert cc.shared_dimensions, "should share chemistry's dimensions"


def test_find_closest_novel_when_empty():
    with tempfile.TemporaryDirectory() as t:
        cc = ledger.find_closest({"domain": "chemistry"}, ledger_dir=Path(t) / "empty")
        assert cc is not None and cc.precedent_id is None  # explicit honest-novel


def test_find_closest_none_for_unknown_axis():
    with tempfile.TemporaryDirectory() as t:
        cc = ledger.find_closest({"domain": "nonexistent_xyz_axis"}, ledger_dir=Path(t))
        assert cc is None  # no resolvable axis -> no lookup


def test_find_closest_prefers_same_domain():
    with tempfile.TemporaryDirectory() as t:
        ld, cb = Path(t) / "ledger", Path(t) / "cas"
        _seal("chemistry", ld, cb, 1000.0)
        _seal("finance", ld, cb, 2000.0)
        cc = ledger.find_closest({"domain": "chemistry"}, ledger_dir=ld)
        assert cc.precedent_id is not None
        assert "chemistry" in cc.precedent_id, f"expected the chemistry precedent, got {cc.precedent_id}"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} precedent tests passed — the grid feeds find_closest; precedent overlay works.")
