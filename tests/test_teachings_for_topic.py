"""THE WORDS IN RED, BY THEME — Christ's own teaching found for a matter (teachings.for_topic).

Matt, 2026-09-22: "all of that should connect to Red; if my words don't align with the words of Christ
or Scripture we don't use them." The curated titles carry the operator's alignment; a matter is joined
to the teaching it belongs to — "treat my enemy" -> Love your enemies, not a verse that merely contains
"enemy". Title matches hold with or without the bible text loaded; deeper (body) matches need it.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import teachings  # noqa: E402


def test_a_matter_joins_the_teaching_it_belongs_to():
    assert (teachings.for_topic("how should I treat my enemy") or {}).get("id") == "som_09"   # Love your enemies
    assert (teachings.for_topic("what about divorce") or {}).get("id") == "som_06"            # Divorce
    assert (teachings.for_topic("judging other people") or {}).get("id") == "som_15"          # Judging — the plank


def test_no_teaching_is_forced_where_none_aligns():
    assert teachings.for_topic("quantum chromodynamics lattice") is None
    assert teachings.for_topic("") is None


def test_a_match_carries_the_ref_and_the_red_flag():
    r = teachings.for_topic("what about divorce")
    assert r and r["ref"] == "Matthew 5:31-32" and r["red"] is True


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
