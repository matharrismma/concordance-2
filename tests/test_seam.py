"""The seam test — proves the riskiest design claim in code:

ONE engine, ONE foundation, TWO surfaces. The secular reach surfaces no religious
wording; the witness surfaces the foundation explicitly; both stand on the same
foundation. Runnable with `pytest` OR directly with `python tests/test_seam.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import SURFACES, EngineConfig  # noqa: E402

_RELIGIOUS_WORDS = ("jesus", "christ", "scripture", "bible", "gospel", "lord", "god", "word")


def test_default_surface_is_secular_reach():
    assert EngineConfig().surface == "secular"


def test_secular_surface_hides_religious_wording():
    text = EngineConfig("secular").identity.lower()
    leaked = [w for w in _RELIGIOUS_WORDS if w in text]
    assert not leaked, f"secular reach leaked religious wording: {leaked}"


def test_witness_surface_names_the_foundation():
    text = EngineConfig("witness").identity.lower()
    assert "christ" in text, "witness surface must name the foundation"


def test_source_layers_differ_by_surface():
    assert EngineConfig("secular").source_layers != EngineConfig("witness").source_layers
    assert "jesus_words" in EngineConfig("witness").source_layers
    assert "jesus_words" not in EngineConfig("secular").source_layers


def test_witness_surfaced_flag():
    assert EngineConfig("witness").witness_surfaced is True
    assert EngineConfig("secular").witness_surfaced is False


def test_invalid_surface_rejected():
    try:
        EngineConfig("clockwork")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid surface must raise ValueError")


def test_surfaces_enumerated():
    assert SURFACES == ("secular", "witness")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} seam tests passed — one foundation, two surfaces.")
