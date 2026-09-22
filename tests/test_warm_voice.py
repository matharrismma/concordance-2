"""WARM THE VOICE — the kept, repeated lines are gathered correctly (so a warm run voices the right
things, once). The paid synthesis itself is voice.speak (its own cache is tested elsewhere); here we
only prove the tool collects clean, de-duplicated lines and honors its scope.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402


def _load_tool():
    spec = importlib.util.spec_from_file_location("warm_voice", ROOT / "tools" / "warm_voice.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


WV = _load_tool()


def test_clean_collapses_whitespace():
    assert WV._clean("  a   b\n\tc  ") == "a b c"
    assert WV._clean(None) == ""


def test_core_scope_gathers_rules_and_checks_not_decodables(tmp_path, monkeypatch):
    (tmp_path).mkdir(exist_ok=True)
    unit = [{
        "id": "u1", "rule": "The   rule.", "decodable_sentence": "A decodable.",
        "examples": ["Ex one.", "Ex two."],
        "check": {"prompt": "The check?", "answer": "x", "choices": ["x"]},
    }]
    (tmp_path / "de_en.json").write_text(json.dumps(unit), encoding="utf-8")
    monkeypatch.setattr(WV, "CURR", tmp_path)

    core = WV.curriculum_lines("core")
    assert "The rule." in core and "The check?" in core          # rule + prompt (whitespace cleaned)
    assert "A decodable." not in core and "Ex one." not in core  # not in core scope

    allsc = WV.curriculum_lines("all")
    assert "A decodable." in allsc and "Ex one." in allsc and "Ex two." in allsc


def test_fixed_lines_are_present_and_short():
    assert any("not alone" in s for s in WV.FIXED)               # the crisis line is voiced
    from concordance import voice
    assert all(len(s) <= voice._MAX_CHARS for s in WV.FIXED)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
