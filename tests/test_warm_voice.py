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


def test_it_gathers_only_what_is_spoken_verbatim(tmp_path, monkeypatch):
    """The player speaks examples + decodables byte-for-byte; the rules/checks are woven into dynamic
    lines, so warming them would never HIT. The tool must gather only the verbatim set."""
    unit = [{
        "id": "u1", "rule": "The   rule.", "decodable_sentence": "A decodable.",
        "examples": ["Ex one.", "Ex two."],
        "check": {"prompt": "The check?", "answer": "x", "choices": ["x"]},
    }]
    (tmp_path / "de_en.json").write_text(json.dumps(unit), encoding="utf-8")
    monkeypatch.setattr(WV, "CURR", tmp_path)
    lines = WV.spoken_lines()
    assert "A decodable." in lines and "Ex one." in lines and "Ex two." in lines
    assert "The rule." not in lines and "The check?" not in lines   # never spoken verbatim -> not warmed


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
