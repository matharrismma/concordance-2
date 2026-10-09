"""THE STEWARD SPEAKS (Matt, 2026-10-08: "steward does speak" · "same voice. Just another role" · "task determines
title" · "Harmonics. cords are different shapes of same note"). The walk door's response carries the fitting role —
the face's name, manner and composed material — in the SAME voice: the door's own keys are untouched, crisis is
byte-identical, no seal is ever minted, and a situation no face fits carries no role. No corpus here (an empty data
dir): the role's gathered material is empty, the role itself still names itself."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="nh-steward-"))
os.environ["CONCORDANCE_DATA_DIR"] = str(TMP)

from concordance import ask, faces  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402

CFG = EngineConfig("secular")


def test_task_determines_title():
    assert faces.faces()["face_steward"]["name"] == "the Bookkeeper"        # its task: count the cost
    assert "bookkeeper" in faces.faces()["face_steward"]["manner"]


def test_the_steward_brings_the_role_that_fits_in_the_same_voice():
    rows = {
        "my hours were cut and I cannot afford my rent this month, how do I budget": "the Bookkeeper",
        "how do I teach my son to read, help me learn the lesson": "the Tutor",
        "we have no food and no money and the power is off": "the Social Worker",
        "explain why the same equation and principle show up in heat and in money": "the Theorist",
    }
    for text, name in rows.items():
        r = ask.respond(text, CFG)
        assert "role" in r, text
        assert r["role"]["name"] == name, (text, r["role"]["name"])
        assert "the same voice" in r["role"]["means"] and r["generated"] is False
        assert "kind" in r and "note" in r                                    # the door's own keys, untouched
        assert "seal" not in r and "seal" not in r["role"]                    # ask never seals


def test_no_fit_no_role_and_crisis_byte_identical():
    r = ask.respond("the Hebrew alphabet has 22 letters", CFG)
    assert "role" not in r
    c = ask.respond("I want to end my life", CFG)
    assert c["kind"] == "crisis" and "role" not in c
    assert c == ask._respond_core("I want to end my life", CFG)             # the wrapper adds nothing to a cry


def test_the_role_is_the_composer_output_not_a_second_voice(monkeypatch):
    """What the role carries is exactly what faces.compose served — the one voice in another shape."""
    seen = {}

    def fake_compose(fid, text, config=None, **_k):
        seen["fid"] = fid
        return {"face": fid, "name": "the Bookkeeper", "kind": "served", "manner": "m", "gathered": [{"id": "c1"}],
                "verify": None, "discern": None}
    monkeypatch.setattr(faces, "compose", fake_compose)
    r = ask.respond("how do I budget my money and pay down debt", CFG)
    assert seen["fid"] == "face_steward"
    assert r["role"]["id"] == "face_steward" and r["role"]["gathered"] == [{"id": "c1"}] and r["role"]["manner"] == "m"
    assert "face" not in r["role"] and "kind" not in r["role"]


def test_a_failing_composer_never_fails_the_door(monkeypatch):
    def boom(*_a, **_k):
        raise RuntimeError("no")
    monkeypatch.setattr(faces, "compose", boom)
    r = ask.respond("how do I budget my money and pay down debt", CFG)
    assert isinstance(r, dict) and "role" not in r and "error" not in r
