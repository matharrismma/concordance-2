"""THE RAS CARD SAYS ONLY WHAT ITS SOURCES SAY (2026-11-24, Matt: "Yes, correct it").

card_n_ras7gate0recv was minted by our own assay (tools/add_ras_bridge.py, 2026-07-23) and claimed more than the three
sources the keeping holds on the RAS — WordNet ("an alerting or arousal function"), OpenStax Fundamentals of Nursing
29.1 ("regulating arousal, attention, and the consciousness") and OpenStax Introduction to Behavioral Neuroscience,
whose key terms list the ascending reticular activation system as ONE of the structures that implement attention,
beside the superior colliculus, the pulvinar and the dorsal and ventral attentional networks. It said the RAS
"decides what reaches awareness", it called the bridge to Matthew 6:22 CONCORDANT ("we have found it") after the
07-29 null assay had made it RESONANCE, and it quoted Mark 8:18 and Matthew 6:22 in the King James wording.

The correction is a row in card_corrections.json, applied at load. These pin it against the exact text the tool
minted, which is the body the box serves (sha256 c078a81b…, read over MCP on 2026-11-24).
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from concordance import card_corrections as C  # noqa: E402
import add_ras_bridge as A  # noqa: E402

RULE = "ras-what-its-sources-say"
FLOOR_ID = "card_k_floor_of_discovery"      # Matt's card; the RAS is bridged to it (data/keystone_bridges.jsonl)


def _rows():
    return json.loads(C.TABLE_PATH.read_text(encoding="utf-8"))["corrections"]


def _row():
    rows = [r for r in _rows() if r["rule"] == RULE]
    assert len(rows) == 1
    return rows[0]


def _card(**kw):
    c = copy.deepcopy(A.RAS_CARD)
    c.update(kw)
    return c


def _corrected():
    c = _card()
    assert C.apply_one(c, [_row()]) == "applied"
    return c


def test_one_row_keyed_to_the_text_our_tool_minted_and_none_for_his_cards():
    r = _row()
    assert r["id"] == A.RAS_ID == "card_n_ras7gate0recv"
    assert "Yes, correct it" in r["directive"] and r["date"] == "2026-11-24"
    assert r["minted_by"] == {"file": "tools/add_ras_bridge.py", "name": "RAS_BODY"}
    body = [ch for ch in r["changes"] if ch["path"] == "body"][0]
    assert body["old_sha256"] == C._sha(A.RAS_BODY)                         # the proof it is ours: our tool's text
    assert not any(x["id"] in (A.EYE_ID, FLOOR_ID) for x in _rows())     # his eye devotional and floor: untouched


def test_it_applies_to_the_exact_minted_body_and_carries_its_provenance():
    c = _corrected()
    assert c["corrected"] == [{"rule": RULE, "date": "2026-11-24", "directive": _row()["directive"]}]
    assert c["title"] == "The Reticular Activating System — arousal, one part of attention"


OVERCLAIMS = ("decides what reaches awareness", "admits a trickle", "gate on salience", "physically implemented",
              "we have found it", "CONCORDANT", "gate of reception", "see ye not", "hear ye not", "'single'",
              "fails into coma", "thalamic reticular nucleus", "confirmed biology of reception")


def test_every_overclaim_is_gone():
    c = _corrected()
    was = A.RAS_CARD["title"] + "\n" + A.RAS_BODY
    now = c["title"] + "\n" + c["body"]
    for s in OVERCLAIMS:
        assert s in was, s                                                 # each one was really there
        assert s not in now, s


def test_it_says_what_its_sources_say():
    body = _corrected()["body"]
    for s in ("an alerting, or arousal, function (WordNet)",
              "no source held here says it chooses what is attended to",
              "regulates arousal, attention and consciousness (OpenStax, Fundamentals of Nursing, 29.1)",
              "one of the structures that implement attention, beside the superior colliculus, the pulvinar and the "
              "dorsal and ventral attentional networks",
              "executive function (OpenStax, Introduction to Behavioral Neuroscience, 19.2 and 19.6)",
              "VERDICT: RESONANCE (a reading, never a proof)"):
        assert s in body, s


# the World English Bible, as read_passage returned each verse on 2026-11-24
WEB = {"Matthew 11:15": "He who has ears to hear, let him hear",
       "Mark 8:18": "Having eyes, don’t you see? Having ears, don’t you hear?",
       "Matthew 6:22": "If therefore your eye is sound, your whole body will be full of light",
       "John 10:9": "I am the door",
       "John 8:12": "I am the light of the world"}


def test_every_quotation_is_the_world_english_bible():
    body = _corrected()["body"]
    for ref, text in WEB.items():
        assert f"'{text}' ({ref})" in body, ref


def test_what_was_right_is_kept():
    body = _corrected()["body"]
    for s in ("(Moruzzi & Magoun, 1949)", "VERDICT: CONFIRMED", "Matthew 13:13-15, quoting Isaiah 6:9-10",
              "'program your RAS to attract your goals'", "and is REFUSED", "attention is not sovereign",
              "The RAS is the honest servant of that; it is not the master of it."):
        assert s in body, s


def test_an_operator_marked_card_with_other_text_is_refused():
    """The eye devotional carries author "operator" and tier "operator", exactly as the RAS card does — so the
    author field is no guard. The body hash is: any other text, under this card's id, is left as it is."""
    c = _card(body="The light of the body is the eye.")
    assert c["author"] == "operator" and c["source"]["authority_tier"] == "operator"
    before = copy.deepcopy(c)
    assert C.apply_one(c, [_row()]) == "mismatch" and c == before


def test_the_expects_pin_refuses_a_card_whose_author_or_tier_changed():
    for kw in ({"author": "matt"}, {"source": dict(A.RAS_CARD["source"], authority_tier="matt")}):
        c = _card(**kw)
        before = copy.deepcopy(c)
        assert C.apply_one(c, [_row()]) == "mismatch" and c == before


def test_a_body_that_moved_on_is_left_exactly_as_it_is():
    c = _card(body=A.RAS_BODY + " A later line.")
    before = copy.deepcopy(c)
    assert C.apply_one(c, [_row()]) == "mismatch" and c == before


def test_it_applies_once():
    c = _corrected()
    body = c["body"]
    assert C.apply_one(c, [_row()]) == "already" and c["body"] == body and len(c["corrected"]) == 1


def test_spans_are_short_and_never_overlap():
    spans = [ch for ch in _row()["changes"] if ch["path"] == "body"][0]["spans"]
    assert all(len(rep) < 200 for _, _, rep in spans)
    ordered = sorted((int(s), int(e)) for s, e, _ in spans)
    assert all(a[1] <= b[0] for a, b in zip(ordered, ordered[1:]))


if __name__ == "__main__":
    import inspect
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and inspect.isfunction(fn):
            fn()
            print("ok", name)
