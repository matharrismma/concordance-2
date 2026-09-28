"""RECOMBINE — the expressive half (extractive, v0). Pins: composes ONLY from the given verbatim
instances; orders by the frame (existence → identity → motion) then relevance; every fragment keeps its
source; honest empty when nothing fits; nothing invented."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402
from concordance import recombine  # noqa: E402


def _ins(text, anchor, source="a book"):
    return {"text": text, "anchor": anchor, "source": source}


def test_off_by_default_gate():
    # the wiring gate is off by default; the pure core still composes
    import os
    os.environ.pop("CONCORDANCE_RECOMBINE", None)
    assert recombine.enabled() is False


def test_orders_by_the_frame_then_relevance():
    inst = [
        _ins("I go to the river each morning.", "I go"),           # motion (role 2)
        _ins("There is clean water in the spring.", "there is"),   # existence (role 0)
        _ins("This is the way to purify it.", "this is"),          # identity (role 1)
    ]
    r = recombine.compose("purify water spring", inst)
    assert r["found"] is True and len(r["fragments"]) == 3
    order = [f["anchor"] for f in r["fragments"]]
    assert order == ["there is", "this is", "I go"]               # existence → identity → motion
    assert r["passage"].startswith("There is clean water")
    assert all(f["source"] == "a book" for f in r["fragments"])   # provenance kept


def test_every_fragment_is_verbatim_from_the_pool():
    inst = [_ins("There is a fire on the hill.", "there is")]
    r = recombine.compose("fire", inst)
    assert r["passage"] == "There is a fire on the hill."          # verbatim, not reworded
    assert r["fragments"][0]["text"] in {i["text"] for i in inst}


def test_honest_empty_when_nothing_fits():
    r = recombine.compose("anything", [])
    assert r["found"] is False and r["passage"] == "" and "honest gap" in r["means"]


def test_limit_and_dedup():
    inst = [_ins("There is water.", "there is"), _ins("There is water.", "there is"),  # dup
            _ins("This is good.", "this is"), _ins("I go.", "I go")]
    r = recombine.compose("water", inst, limit=2)
    assert len(r["fragments"]) == 2
    texts = [f["text"] for f in r["fragments"]]
    assert texts == ["There is water.", "This is good."]           # dedup + frame order, capped


def test_weave_splits_into_verbatim_clauses():
    src = "There is water in the spring; there is fire on the hill."
    r = recombine.weave("water spring fire hill", [_ins(src, "there is", "Foxfire")])
    found = [p for p in r["pieces"] if p["kind"] == "found"]
    assert r["found"] is True and len(found) == 2                      # split into two clauses
    for p in found:
        assert p["text"] in src                                        # each clause is verbatim from the source
    joints = [p for p in r["pieces"] if p["kind"] == "frame"]
    assert joints and all(j["text"] == ", " for j in joints)           # same source → smooth joint


def test_weave_holds_different_sources_apart():
    # the guard: a poison clause and a "safe" clause from DIFFERENT sources must not fuse into one claim
    inst = [_ins("There is poison in the water.", "there is", "A"),
            _ins("This is safe to drink.", "this is", "B")]
    r = recombine.weave("water safe drink poison", inst)
    found = [p for p in r["pieces"] if p["kind"] == "found"]
    frame = [p for p in r["pieces"] if p["kind"] == "frame"]
    assert {p["source"] for p in found} == {"A", "B"}                  # both, each attributed
    assert frame and all(j["text"] == "; " for j in frame)            # BOUNDARY across sources, never ", "


def test_weave_frame_joints_are_non_assertive():
    inst = [_ins("There is a well here.", "there is", "A"), _ins("This is the path.", "this is", "B")]
    r = recombine.weave("well path", inst)
    for p in r["pieces"]:
        if p["kind"] == "frame":
            assert p["text"].strip() in {",", ";"}                     # only structure — asserts nothing


def test_weave_honest_empty():
    r = recombine.weave("anything", [])
    assert r["found"] is False and r["passage"] == ""


def test_resolve_refs_found_for_found_same_source():
    pieces = [{"kind": "found", "text": "There is clean water in the spring", "source": "A", "anchor": "there is"},
              {"kind": "frame", "text": ", "},
              {"kind": "found", "text": "It is cold and pure", "source": "A", "anchor": "it is"}]
    rr = recombine.resolve_refs(pieces)
    second = [p for p in rr["pieces"] if p["kind"] == "found"][1]
    assert second["resolution"]["antecedent"] == "clean water" and second["resolution"]["pronoun"] == "It"
    assert second["resolved"] == "The clean water is cold and pure"       # found-for-found substitution
    assert second["text"] == "It is cold and pure"                        # the verbatim is never overwritten
    assert "The clean water is cold and pure" in rr["resolved_passage"]


def test_resolve_refs_will_not_cross_sources():
    pieces = [{"kind": "found", "text": "There is a well here", "source": "A", "anchor": "there is"},
              {"kind": "frame", "text": "; "},
              {"kind": "found", "text": "It is deep", "source": "B", "anchor": "it is"}]
    rr = recombine.resolve_refs(pieces)
    second = [p for p in rr["pieces"] if p["kind"] == "found"][1]
    assert "resolved" not in second                                        # a pronoun is never resolved across sources


def test_resolve_refs_leaves_the_pronoun_when_no_found_antecedent():
    pieces = [{"kind": "found", "text": "The path goes uphill", "source": "A", "anchor": ""},
              {"kind": "frame", "text": ", "},
              {"kind": "found", "text": "It is steep", "source": "A", "anchor": "it is"}]
    rr = recombine.resolve_refs(pieces)
    second = [p for p in rr["pieces"] if p["kind"] == "found"][1]
    assert "resolved" not in second                                        # no frame-introduced antecedent → stands


def test_answer_speaks_from_the_keeping():
    cards = [{"title": "Foxfire", "id": "c1"}, {"title": "Manual", "id": "c2"}]
    def decodable_fn(card):
        if card["id"] == "c1":
            return {"found": [{"text": "There is clean water in the spring", "anchor": "there is"},
                              {"text": "It is safe to drink", "anchor": "it is"}]}
        return {"found": [{"text": "This is how you purify it", "anchor": "this is"}]}
    r = recombine.answer("purify water spring drink", search_fn=lambda q: cards, decodable_fn=decodable_fn)
    assert r["found"] is True and r["instances"] == 3
    assert "Foxfire" in r["sources"]
    assert isinstance(r["resolved_passage"], str) and r["resolved_passage"]  # spoken from the (injected) keeping


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
