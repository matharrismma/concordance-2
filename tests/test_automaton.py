"""The Automaton — a witness who faced your situation, testifying in his OWN recorded words.

The whole integrity of the hall is the ONE law tested hardest here: it TESTIFIES, it never
IMPERSONATES. Every passage voiced must be the witness's real, public-domain, cited text; a non-PD
witness is voiced by nobody; a situation no gathered witness has faced returns an honest empty, never
a fabricated match. Injected corpora keep these deterministic and free of any gathered-data
dependency — the structural gate is proved, not assumed.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import automaton  # noqa: E402

# Two figures. "Aa" holds the most passages that touch a storm/fear/courage situation (depth); "Bb"
# is off in the garden. public_domain is the structural gate witness.py enforces and automaton rides.
PD = [
    {"witness": "Aa", "work": "On Courage", "text": "courage in the storm, and the fear that passes",
     "public_domain": True, "id": "a1", "ref": "1.1", "source": "On Courage (1880)"},
    {"witness": "Aa", "work": "On Courage", "text": "the storm again, and courage to face the dark night",
     "public_domain": True, "id": "a2", "ref": "1.2", "source": "On Courage (1880)"},
    {"witness": "Bb", "work": "The Garden", "text": "a quiet note about gardening and turnips",
     "public_domain": True, "id": "b1", "ref": "3.1", "source": "The Garden (1875)"},
]


def test_a_witness_who_faced_it_testifies_in_his_own_words():
    r = automaton.consult("I face a storm and fear", corpus=PD)
    assert r["witness"] == "Aa", "the figure holding the most matching passages should testify"
    assert r["testimony"], "he testified with no words"
    assert all(p.get("text") and p.get("witness") == "Aa" for p in r["testimony"]), \
        "every testimony passage must be his own attributed, verbatim text"
    assert r["generated"] is False and r["confirms"] is False   # conduit: found + cited, never a verdict
    assert "Aa" in r["discipline"], "the frame must NAME him, so it reads as testimony, not a voice speaking TO you"


def test_it_never_voices_a_non_public_domain_witness():
    """The load-bearing law: a copyrighted witness is NEVER voiced, even when his words match best.
    The gate is structural (witness.py, fail-closed) and the automaton cannot reach past it."""
    tainted = [{"witness": "Cc", "work": "Still Copyrighted", "text": "courage in the storm and the fear",
                "public_domain": False, "id": "c1", "ref": "9.9"}]
    r = automaton.consult("storm and fear and courage", corpus=tainted)
    assert r["witness"] is None and not r["testimony"], "a non-PD witness was voiced — the gate leaked"
    assert not automaton.hall(corpus=tainted), "the hall must list only witnesses whose PD words are gathered"


def test_a_miss_stays_a_miss_never_a_fabricated_match():
    r = automaton.consult("lattice gauge quantum chromodynamics", corpus=PD)
    assert r["witness"] is None and not r["testimony"], "no gathered witness faced this — none should be invented"
    assert "miss stays a miss" in r["note"] or "still being gathered" in r["note"]


def test_you_can_consult_a_named_witness():
    r = automaton.consult("gardening turnips", corpus=PD, witness="Bb")
    assert r["witness"] == "Bb", "asking for a witness by name should scope the hall to his voice"
    assert r["testimony"] and all(p.get("witness") == "Bb" for p in r["testimony"])


def test_empty_situation_invites_without_inventing():
    r = automaton.consult("", corpus=PD)
    assert r["witness"] is None and r["testimony"] == []
    assert r["hall"] == ["Aa", "Bb"], "the hall is still named — you can see who you may consult"


def test_the_hall_names_the_others_you_may_also_consult():
    r = automaton.consult("I face a storm and fear", corpus=PD)
    assert "Bb" in (r.get("also_in_the_hall") or []), "the other gathered witnesses should be offered"
    assert r["witness"] not in (r.get("also_in_the_hall") or []), "the one testifying isn't listed as an 'other'"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
