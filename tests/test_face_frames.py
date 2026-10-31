"""The frames (data/face_frames.json) — every character complete, every line scaffold, never content.

Pins: all 18 faces present; all 17 slots on each, at least two variants; only the declared placeholders; NO digits (a
frame carries no fact — a number would be content); every credentialed face's boundary names its credential and
negates it; no crisis slot (the backstop's words are byte-identical by invariant); the loader fills slots
deterministically and never leaks an empty one; compose carries the voice. Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import faces  # noqa: E402

DATA = json.loads((ROOT / "data" / "face_frames.json").read_text(encoding="utf-8"))
SLOTS = tuple(DATA["_slots"])
PLACEHOLDERS = set(DATA["_placeholders"])
CREDENTIAL = {"face_engineer": "engineer", "face_counsel": "attorney", "face_physician": "doctor",
              "face_counselor": "therapist", "face_nutrition": "doctor", "face_builder": "tradesman"}


def test_every_face_has_every_slot_with_at_least_two_variants():
    assert SLOTS == faces.FRAME_SLOTS
    for fid in faces._FACES:
        assert fid in DATA, f"{fid} has no frames"
        for slot in SLOTS:
            variants = DATA[fid].get(slot)
            assert isinstance(variants, list) and len(variants) >= 2, f"{fid}.{slot} incomplete"
            assert all(isinstance(v, str) and 8 <= len(v) <= 240 for v in variants), f"{fid}.{slot} length"
        assert set(DATA[fid]) <= set(SLOTS), f"{fid} has a slot outside the contract: {set(DATA[fid]) - set(SLOTS)}"
    assert "crisis" not in SLOTS


def test_frames_are_scaffold_not_content():
    for fid in faces._FACES:
        for slot, variants in DATA[fid].items():
            for v in variants:
                assert not re.search(r"\d", v), f"{fid}.{slot} carries a digit (a fact): {v!r}"
                used = set(re.findall(r"\{([a-z_]+)\}", v))
                assert used <= PLACEHOLDERS, f"{fid}.{slot} unknown placeholder {used - PLACEHOLDERS}"
                assert "{" not in re.sub(r"\{[a-z_]+\}", "", v), f"{fid}.{slot} stray brace: {v!r}"
    # the slots that carry content MUST have a placeholder; the honest gap MUST NOT (it asserts nothing)
    for fid in faces._FACES:
        assert all("{found}" in v and "{source}" in v for v in DATA[fid]["found"]), fid
        assert all("{claim}" in v for v in DATA[fid]["holds"] + DATA[fid]["broken"] + DATA[fid]["incomplete"]), fid
        assert all("{step}" in v for v in DATA[fid]["step"]), fid
        assert all("{name}" in v and "{source}" in v for v in DATA[fid]["witness"]), fid
        assert all("{" not in v for v in DATA[fid]["gap"]), fid


def test_review_findings_stay_fixed():
    """The 2026-10-31 review of the draft: (1) a `found` frame must not claim what KIND of thing was found — the
    live GOD gate filled "The Word says, in {source}" with a commentary; (2) a `name` frame quotes the ask, since
    it is a whole request; (3) the Social Worker and the Shepherd always hand off to real people (their gap and
    manner promise it); (4) no `holds` frame asserts a judgment past the verdict (margin met, stage closed)."""
    genre = re.compile(r"the word says|the text reads|canonical work|the theory it rests on|for exactly this", re.I)
    judgment = re.compile(r"within margin|stage can close|the gate is met|the land agrees", re.I)
    for fid in faces._FACES:
        for v in DATA[fid]["found"]:
            assert not genre.search(v), f"{fid}.found claims a genre: {v!r}"
        for v in DATA[fid]["name"]:
            assert "“{ask}”" in v, f"{fid}.name must quote the ask: {v!r}"
        for v in DATA[fid]["holds"]:
            assert not judgment.search(v), f"{fid}.holds asserts past the verdict: {v!r}"
    assert {"face_social_worker", "face_shepherd"} <= set(faces._REFERS)
    out = faces.compose("face_social_worker", "I have no food and no power",
                        crisis_fn=lambda t: False, search_fn=lambda q, limit=12, **kw: [], discern_fn=lambda t, **kw: None,
                        verify_fn=lambda t, **kw: None)
    assert out["voice"].get("gap") and out["voice"].get("refer") in DATA["face_social_worker"]["refer"]   # the promise is kept
    # character, not boilerplate: the once-shared generic lines are gone
    for shared in ("Next: {step}.", "One thing I need: {ask}?", "That is from {source}, {tier}.", "{source} ({tier})."):
        owners = [fid for fid in faces._FACES for slot in DATA[fid] for v in DATA[fid][slot] if v == shared]
        assert len(owners) <= 1, f"{shared!r} is spoken by {owners} — one line, many faces"


def test_a_credentialed_face_names_and_negates_its_credential():
    for fid, word in CREDENTIAL.items():
        joined = " ".join(DATA[fid]["boundary"]).lower()
        assert word in joined and re.search(r"\bnot\b|\bnever\b|\bno\b", joined), f"{fid} boundary must say it is NOT the {word}"
        assert any(w in " ".join(DATA[fid]["refer"]).lower() for w in ("real", "licensed", "clinician", "lawyer", "inspector", "teacher", "dietitian", "professional", "church")), fid


def test_loader_fills_slots_deterministically_and_never_leaks():
    fr = faces.frames("face_shepherd")
    assert set(fr) == set(SLOTS)
    a = faces.frame("face_shepherd", "found", found="The Lord is my shepherd.", source="Psalm")
    b = faces.frame("face_shepherd", "found", found="The Lord is my shepherd.", source="Psalm")
    assert a == b and "The Lord is my shepherd." in a and "Psalm" in a and "{" not in a
    assert faces.frame("face_shepherd", "found", found="x") is None                 # a missing placeholder never leaks
    assert faces.frame("face_shepherd", "gap") and "{" not in faces.frame("face_shepherd", "gap")
    assert faces.frame("face_nope", "gap") is None and faces.frame("face_shepherd", "crisis") is None
    seen = {faces.frame("face_coach", "step", step=f"drill {w}") for w in ("a", "b", "c", "d", "e", "f")}
    assert len(seen) >= 2                                                          # different requests vary; same request repeats


def test_compose_speaks_in_frames_and_the_gap_is_honest():
    out = faces.compose("face_tutor", "explain how photosynthesis works",
                        crisis_fn=lambda t: False, search_fn=lambda q, limit=12, **kw: [], discern_fn=lambda t, **kw: None,
                        verify_fn=lambda t, **kw: None)
    voice = out.get("voice") or {}
    assert voice.get("receive") in DATA["face_tutor"]["receive"]
    assert voice.get("gap") in DATA["face_tutor"]["gap"] and "found" not in voice      # nothing found → the honest gap, no found frame
    assert voice.get("close") in DATA["face_tutor"]["close"]
    hit = {"id": "card_x", "title": "Photosynthesis", "source": {"label": "OpenStax Biology", "authority_tier": "reference"}}
    out2 = faces.compose("face_tutor", "explain how photosynthesis works",
                         crisis_fn=lambda t: False, search_fn=lambda q, limit=12, **kw: [hit], discern_fn=lambda t, **kw: None,
                         verify_fn=lambda t, **kw: None)
    v2 = out2.get("voice") or {}
    assert "gap" not in v2 and "Photosynthesis" in (v2.get("found") or "") and "OpenStax Biology" in v2["found"]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("ALL PASS")
