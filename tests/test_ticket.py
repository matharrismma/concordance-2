"""The winning ticket — pruning as a versioned MASK (ticket.py), pinned without the box.

Importance is magnitude × activation; only the DEAD are ever proposed; the mask is data with every version kept and a
rewind; the faces' router honours it; the IMP loop accepts, or rewinds and halves p. Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import ticket  # noqa: E402


def _units():
    #            unit: (magnitude, fires)
    return {"f1|money": (0.5, 12), "f1|budget": (1.0, 3), "f1|generic": (0.25, 0), "f1|specific phrase": (2.0, 0),
            "f2|rare": (1.0, 0), "f2|generic": (0.25, 0)}


def test_importance_is_magnitude_times_activation_and_dead_is_zero():
    assert ticket.importance(2.0, 3) == 6.0
    assert ticket.importance(2.0, 0) == 0.0 and ticket.importance(2.0, -1) == 0.0


def test_propose_draws_only_from_the_dead_least_specific_first_and_never_a_fired_unit():
    pick = ticket.propose(_units(), p=0.5)                     # ceil(0.5 * 6) = 3 of the 4 dead
    assert pick == ["f1|generic", "f2|generic", "f2|rare"]      # magnitude 0.25, 0.25 (id tiebreak), 1.0; the 2.0 phrase last
    assert "f1|money" not in ticket.propose(_units(), p=1.0)   # fired units are never proposed, even at p = 1
    assert ticket.propose(_units(), p=1.0, protect={"f1|generic", "f2|generic"}) == ["f2|rare", "f1|specific phrase"]
    assert ticket.propose({}, 0.5) == [] and ticket.propose(_units(), 0.0) == []


def test_mask_store_versions_kept_rewind_and_hot_reload(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    ticket.reset_cache()
    assert ticket.current()["version"] == 0 and not ticket.masked("scope", "f1|generic")       # absent file = nothing masked
    v1 = ticket.save({"scope": ["f1|generic"]}, window={"days": 90}, totals={"scope": 6})
    assert v1["version"] == 1 and v1["parent"] is None and v1["sparsity"]["scope"] == {"masked": 1, "total": 6}
    assert ticket.masked("scope", "f1|generic") and not ticket.masked("scope", "f1|money")
    v2 = ticket.save({"scope": ["f1|generic", "f2|generic"]}, totals={"scope": 6})
    assert v2["version"] == 2 and v2["parent"] == ticket.receipt(v1)                          # the chain of tickets
    assert ticket.masked("scope", "f2|generic")
    assert ticket.versions() == [1, 2]
    back = ticket.rewind()                                                                      # the river keeps v2 on disk
    assert back["version"] == 1 and ticket.versions() == [1, 2]
    assert ticket.masked("scope", "f1|generic") and not ticket.masked("scope", "f2|generic")
    ticket.rewind()
    assert ticket.current()["version"] == 0 and not ticket.masked("scope", "f1|generic")       # back to the dense keeping
    # a corrupt current file masks NOTHING — fail open to the dense keeping, never silently narrow
    (tmp_path / "ticket" / "mask.json").write_text("{not json", encoding="utf-8")
    ticket.reset_cache()
    assert ticket.current()["version"] == 0


def test_receipt_is_deterministic_over_what_is_masked():
    a = {"version": 3, "masked": {"scope": ["x", "y"]}, "window": {"days": 90}, "gates": {"g": 1}}
    b = {"version": 3, "masked": {"scope": ["x", "y"]}, "window": {"days": 90}, "gates": {"g": 2}}
    assert ticket.receipt(a) == ticket.receipt(b)                                               # gates are evidence, not identity
    assert ticket.receipt(a) != ticket.receipt({**a, "masked": {"scope": ["x"]}})


def test_the_faces_router_honours_the_mask(tmp_path, monkeypatch):
    from concordance import faces
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    ticket.reset_cache()
    fid = "face_steward"
    word = next(s for s in faces._FACES[fid]["scope"] if " " not in s)
    text = f"a question about {word} today"
    before = faces._scores(text)[fid]
    assert before >= 1
    ticket.save({"scope": [f"{fid}|{word}"]}, totals={"scope": 1})
    assert faces._scores(text)[fid] == before - 1                                               # the masked word no longer routes
    ticket.rewind()
    assert faces._scores(text)[fid] == before                                                   # and comes back on rewind


def test_scope_fires_measures_activation_and_specificity(monkeypatch):
    from concordance import faces
    # the live registry keeps scopes disjoint (the routing guard), so the 1/k rule is proven on a tiny registry
    monkeypatch.setattr(faces, "_FACES", {"fa": {"scope": ["budget", "shared", "see a doctor"]}, "fb": {"scope": ["shared"]}})
    fires = faces.scope_fires(["how do I make a budget for groceries", "a budget again, shared", "I should see a doctor"])
    assert fires["fa|budget"] == {"fires": 2, "magnitude": 1.0, "face": "fa"}
    assert fires["fa|shared"]["magnitude"] == 0.5 and fires["fb|shared"]["magnitude"] == 0.5        # shared by k=2 → 1/k
    assert fires["fa|see a doctor"] == {"fires": 1, "magnitude": 2.0, "face": "fa"}                # a phrase counts double
    assert fires["fb|shared"]["fires"] == 1
    # and on the live registry every unit is accounted for, once
    monkeypatch.undo()
    live = faces.scope_fires(["money"])
    assert len(live) == sum(len(f["scope"]) for f in faces._FACES.values())


def test_imp_accepts_then_rewinds_and_halves_p(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    ticket.reset_cache()
    applied, gates = [], iter([True, False, False])
    hist = ticket.imp(lambda: {"scope": _units()},
                      lambda cum: applied.append(json.loads(json.dumps(cum))),
                      lambda: (next(gates), {"g": "fake"}),
                      p0=0.5, p_min=0.2, rounds=6, rewind_fn=lambda: applied.append("REWIND"))
    assert hist[0]["accepted"] and hist[0]["proposed"] == {"scope": 3}                           # round 1: 3 dead masked, gate passes
    assert hist[1]["rewound"] and hist[1]["p"] == 0.5 and hist[2]["p"] == 0.25                 # round 2 fails → rewind, p halves
    assert hist[-1].get("stop", "").startswith("p ")                                             # stops under p_min
    assert applied.count("REWIND") == 2
    assert set(applied[0]["scope"]) == {"f1|generic", "f2|generic", "f2|rare"}
    assert "f1|money" not in {u for a in applied if isinstance(a, dict) for u in a["scope"]}    # never a fired unit


if __name__ == "__main__":
    import tempfile
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            if fn.__code__.co_argcount:
                import pytest  # noqa: F401 — fixtures need pytest
                continue
            fn()
            print("ok", name)
    print("ALL PASS (fixture tests via pytest)")
