"""THE LANGUAGE CUBES — French, German, Latin, Hebrew, Mandarin — are well-formed teaching.

Matt, 2026-09-21: "wire french, german, latin, and hebrew ... mandarin as well."

The cube is the fixed frame (Cubo's method): five embodied anchors + a review, learned in the
learner's own room; only the target language changes. These cubes are authored curriculum served
verbatim by coach.py — so what matters is that each is STRUCTURALLY SOUND for the player and the
learner: six units in order, every anchor present, a check whose answer is actually among its
choices (a check whose answer is not offered can never be passed), and nothing generated.

This reads the AUTHORING TOOL (tools/build_language_cubes.py) directly, so it is independent of the
box-local curriculum data (data/curriculum/*_en.json is gitignored, like every cube) and runs
anywhere. The tool is the source of truth for the content; the JSON it writes is what ships.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402


def _load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_language_cubes", ROOT / "tools" / "build_language_cubes.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TOOL = _load_tool()
CUBES = [TOOL.FR, TOOL.DE, TOOL.LA, TOOL.HE, TOOL.ZH, TOOL.GR]
EXPECTED_SUBJECTS = {"fr", "de", "la", "he", "zh", "grc"}
# The five anchors the cube is built on — every language teaches these, in this order, then a review.
ANCHOR_SUFFIXES = ["iam", "thereis", "thisis", "igo", "path", "review"]


def test_all_five_languages_are_present():
    assert {c["subject"] for c in CUBES} == EXPECTED_SUBJECTS


@pytest.mark.parametrize("cube", CUBES, ids=[c["subject"] for c in CUBES])
def test_a_cube_is_six_ordered_units_on_the_five_anchors(cube):
    units = cube["units"]
    assert len(units) == 6, f"{cube['subject']}: a cube is five anchors + a review"
    assert [u["unit_seq"] for u in units] == [1, 2, 3, 4, 5, 6], "units must be in order 1..6"
    # every anchor, in order, under this language's own track
    track = cube["track"]
    assert [u["id"] for u in units] == [f"{track}_{s}" for s in ANCHOR_SUFFIXES], \
        f"{cube['subject']}: the six anchors must be present, in order, under {track}"
    for u in units:
        assert u["track"] == track


@pytest.mark.parametrize("cube", CUBES, ids=[c["subject"] for c in CUBES])
def test_every_unit_carries_the_teaching_the_player_reads(cube):
    for u in cube["units"]:
        assert u.get("rule", "").strip(), f"{u['id']}: a unit must carry its rule"
        ex = u.get("examples")
        assert isinstance(ex, list) and len(ex) >= 3 and all(isinstance(x, str) and x.strip() for x in ex), \
            f"{u['id']}: at least three example sentences"
        assert u.get("decodable_sentence", "").strip(), f"{u['id']}: a decodable sentence"
        modes = u.get("modes")
        assert isinstance(modes, list) and len(modes) == 2, f"{u['id']}: two modes (coach shows / take turns)"
        assert {m["id"] for m in modes} == {"coach_models", "take_turns"}, f"{u['id']}: the two named modes"
        for m in modes:
            assert m.get("instruction", "").strip() and m.get("script", "").strip(), \
                f"{u['id']}/{m['id']}: an instruction and a script"
        assert u.get("generated") is False, f"{u['id']}: authored curriculum, never generated"


@pytest.mark.parametrize("cube", CUBES, ids=[c["subject"] for c in CUBES])
def test_every_check_can_actually_be_passed(cube):
    """A check whose answer is not among its choices can never be passed — the one failure that would
    quietly break a lesson while looking complete."""
    for u in cube["units"]:
        chk = u.get("check")
        assert isinstance(chk, dict), f"{u['id']}: the check is a dict (prompt/answer/choices)"
        for field in ("prompt", "answer", "teaching_note"):
            assert chk.get(field, "").strip(), f"{u['id']}: check.{field} is present"
        choices = chk.get("choices")
        assert isinstance(choices, list) and len(choices) >= 3, f"{u['id']}: at least three choices"
        assert chk["answer"] in choices, \
            f"{u['id']}: the answer '{chk['answer']}' must be one of the offered choices"
        assert len(set(choices)) == len(choices), f"{u['id']}: choices must be distinct"


def test_unit_ids_are_globally_unique():
    """coach.unit() searches ACROSS subjects by id, so an id collision would serve the wrong lesson."""
    ids = [u["id"] for c in CUBES for u in c["units"]]
    assert len(ids) == len(set(ids)), "unit ids collide across the language cubes"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
