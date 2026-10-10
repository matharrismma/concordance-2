"""The syntax parser (Matt, 2026-10-10: "real syntax parser"). A deterministic, offline chart
parser: it must build a real parse tree for well-formed sentences, reject word salad, and never
claim a parse it did not derive. These pin that it discriminates structure, not just length."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import syntax as SX  # noqa: E402


def test_grammatical_sentences_parse_with_a_tree():
    r = SX.parse("the cat sat on the mat")
    assert r["ok"] and r["grammatical"]
    assert r["bracket"].startswith("(S ") and "(PP (P on)" in r["bracket"]
    assert SX.parse("the dog chased a ball")["grammatical"]
    assert SX.parse("she runs")["grammatical"]
    # a famously grammatical nonsense sentence still parses (structure, not sense)
    assert SX.parse("colorless green ideas sleep furiously")["grammatical"]


def test_word_salad_does_not_parse():
    assert not SX.parse("cat the sat")["grammatical"]
    assert not SX.parse("the the the")["grammatical"]
    assert not SX.parse("sat on mat the")["grammatical"]


def test_empty_input_is_declined_not_parsed():
    assert SX.parse("")["ok"] is False
    assert SX.parse("   ...  ")["ok"] is False


def test_pos_pins_function_words():
    # a determiner is only ever a determiner here; it can never be tagged a noun or verb
    assert "DET" in SX.tag("the") and not ({"N", "V"} & SX.tag("the"))
    # a content word with no closed-class membership can be noun/verb/adjective
    assert {"N", "V", "ADJ"} <= SX.tag("cat")
