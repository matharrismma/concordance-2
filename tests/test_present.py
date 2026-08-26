"""THE EXPERIENCE LAYER — bare card in, magic out, and nothing of the magic gets stored.

Matt, 2026-07-29: *"We want our card to be bare, but we want the user experience to be a bit
magical, so we can take the cards and add an experience layer on top without slowing the process
down too much."*

Which sets three testable conditions:

  * **bare stays bare** — not one presentation key reaches the store on disk. Presentation written
    into a record is stale the moment it is written ("3 minutes ago" from last March) and rides
    along in every copy on every device and every shard.
  * **derived, not invented** — every string traces to a field the card actually has. Where the card
    is silent, the layer is silent: no confident label over a missing fact.
  * **free** — pure functions, no I/O, and a second presentation of the same card costs nothing.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated():
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    yield
    if prior is None:
        os.environ.pop("CONCORDANCE_DATA_DIR", None)
    else:
        os.environ["CONCORDANCE_DATA_DIR"] = prior


def _key():
    from concordance import signing
    try:
        return signing.generate_keypair()
    except Exception:  # noqa: BLE001
        pytest.skip("signing unavailable in this build")


def _drop(kind="recipe", ring="shelf", **kw):
    from concordance import shelves, signing
    priv, pub = _key()
    sg = shelves.signable_drop(pub, kind, "Cornbread in a skillet",
                               "Heat the empty skillet while you mix; the batter has to hit hot "
                               "grease and that sizzle is the crust.", ring, **kw)
    assert sg.get("ok"), sg
    sig = signing.sign_bytes(base64.urlsafe_b64decode(sg["signable"]), priv)
    return shelves.drop(sg["fields"], sig, display_name="Matt Harris"), pub, priv


def test_the_stored_card_stays_bare():
    """THE rule. The store is checked as bytes on disk, not as a returned object — the returned
    object is exactly where the presentation is *supposed* to be."""
    from concordance import shelves
    _drop()
    raw = (Path(os.environ["CONCORDANCE_DATA_DIR"]) / "shelves" / "drops.jsonl") \
        .read_text(encoding="utf-8")
    rec = json.loads(raw.splitlines()[0])

    # CHECK THE KEYS, NOT THE CHARACTERS. This was a substring scan of the whole serialized
    # record — `assert "ago" not in raw` — and it FAILED A FULL GATE RUN on 2026-08-01 because a
    # randomly generated member key contained those three letters:
    #
    #     V1ocF6KHL7agokLoaDg", "drop_kind": "recipe"
    #                  ^^^
    #
    # Nothing had leaked. Six re-runs passed. A three-letter needle in a haystack of base64 will
    # coincide sooner or later, and when it does it reads as a real data leak in the store — the
    # most alarming failure this suite can report, for no reason. Same error as reading a coincidence
    # as evidence anywhere else: the check must match the THING (a field name), not letters that
    # happen to spell it.
    def _keys(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield k
                yield from _keys(v)
        elif isinstance(obj, list):
            for v in obj:
                yield from _keys(v)

    present = set(_keys(rec))
    for leak in ("presentation", "glyph", "kind_label", "waybill_line", "standing", "ago"):
        assert leak not in present, f"presentation field {leak!r} reached the store"
    assert set(rec["extra"]) <= {"member", "ring", "display_name", "signature", "drop_kind",
                                 "signed_at", "url", "waybill", "reach", "reach_error", "embed",
                                 "quote", "attribution", "supersedes",
                                 # the gate's record of the drop — provenance, a FACT ("preserve the
                                 # trail"), deliberately stored by shelves.py:260. Not presentation.
                                 "gate_record"}, \
        "a field crept into the card that is not a fact"


def test_the_read_path_hands_back_the_magic():
    from concordance import shelves
    _r, pub, _ = _drop()
    card = shelves.shelf_of(pub, viewer=pub)["cards"][0]
    p = card["presentation"]
    assert p["kind_label"] == "A recipe" and p["glyph"]
    assert "Matt Harris" in p["by"]
    assert p["authority"] == "member"
    assert p["posted"] == "just now"
    assert p["standing"] == "yours alone" or "shelf" in p["standing"]


def test_it_is_derived_and_never_invented():
    """A card with nothing to say produces a layer that says nothing — no plausible filler."""
    from concordance import present
    assert present.derive({}) == {}
    assert present.derive({"id": "x"}).get("posted") == "", "a missing time must not read 'just now'"
    bare = present.derive({"id": "x", "extra": {"drop_kind": "unheard_of_kind"}})
    assert bare["kind_label"] == "unheard of kind", "an unknown kind is shown as-is, not dressed up"
    assert "link" not in bare, "no link block for a card with no url"
    assert "vouched" not in bare, "nobody vouched, so nothing claims they did"


def test_relative_time_is_coarse_and_honest():
    from concordance.present import when
    now = 1_800_000_000
    assert when(now - 10, now) == "just now"
    assert when(now - 600, now) == "10 minutes ago"
    assert when(now - 7200, now) == "2 hours ago"
    assert when(now - 86400 * 3, now) == "3 days ago"
    assert when(now - 86400 * 400, now) == "1 year ago"
    assert when(0, now) == "" and when(None, now) == "" and when("nonsense", now) == ""


def test_a_promotion_shows_as_someone_vouching_with_a_reason():
    """The steward's act becomes readable without becoming the library's claim."""
    from concordance import shelves
    r, _pub, _ = _drop(ring="commons")
    os.environ["CONCORDANCE_KEEP_TOKEN"] = "tok-for-this-test"
    act = shelves.curate(r["card_id"], "promoted", "matt", "concrete and checkable",
                         token="tok-for-this-test")
    assert act["ok"], act
    card = shelves.commons()["cards"][0]
    p = card["presentation"]
    assert p["vouched"] == {"by": "matt", "reason": "concrete and checkable"}
    assert p["authority"] == "member", "vouched for is still not verified by us"
    assert "not the library's claim" in p["standing"]


def test_presenting_costs_nothing_the_second_time():
    """"without slowing the process down too much" — the cache is keyed by (id, updated_at), so a
    changed card can never serve a stale presentation."""
    from concordance import present
    card = {"id": "card_x", "updated_at": 1.0, "extra": {"drop_kind": "note"}}
    a = present.derive(card)
    b = present.derive(card)
    assert a is b, "the same card was recomputed"
    changed = dict(card, updated_at=2.0)
    assert present.derive(changed) is not a, "a changed card served a cached presentation"


def test_attach_never_mutates_the_card_it_was_given():
    from concordance import present
    card = {"id": "c", "updated_at": 1.0, "extra": {"drop_kind": "note"}}
    out = present.attach([card])
    assert "presentation" in out[0]
    assert "presentation" not in card, "attach mutated the caller's card — the store is next"




def test_the_adjoining_cards_are_real_links_for_a_reader_and_an_agent():
    """Matt, 2026-07-30: "Links to adjoining cards as well for agents and users."

    The edges existed but reached a reader ONLY through a JS canvas that stays hidden until scripts
    run — so every crawler, every no-JS reader, and ClaudeBot hit a dead end on ~39k card views
    (full-log figure, 2026-08-01). A graph nobody can traverse is not a graph."""
    from concordance import present
    card = {"id": "c", "updated_at": 1.0, "connections": [
        {"to_card_id": "card_a", "relationship": "comments_on", "evidence": "expounds this verse"},
        {"to_card_id": "card_missing", "relationship": "cites"},
        {"to_card_id": "card_a", "relationship": "cites"},          # duplicate target
        {"junk": True},                                              # unusable edge
    ]}
    known = {"card_a": {"id": "card_a", "title": "Gill on John 3:16"}}
    n = present.neighbors(card, resolve=known.get)

    assert len(n) == 2, "a duplicate target or an unusable edge was not dropped"
    assert n[0]["href"] == "/card/card_a" and n[0]["title"] == "Gill on John 3:16"
    assert n[0]["relationship"] == "comments on", "the relation must read as words, not a slug"
    assert n[0]["why"] == "expounds this verse"
    # an edge we cannot resolve is KEPT with its id and NO invented title
    assert n[1]["id"] == "card_missing" and n[1]["title"] == "" and n[1]["resolved"] is False
    assert n[1]["href"] == "/card/card_missing", "an unresolved neighbour is still walkable"


def test_an_unknown_relationship_is_never_renamed():
    from concordance import present
    n = present.neighbors({"connections": [{"to_card_id": "x", "relationship": "weighs_against"}]},
                          resolve=lambda i: None)
    assert n[0]["relationship"] == "weighs against", "de-slugged, not reinterpreted"


def test_neighbors_survives_a_resolver_that_throws():
    """One bad lookup must not cost the whole page."""
    from concordance import present
    def boom(_):
        raise RuntimeError("shard is locked")
    n = present.neighbors({"connections": [{"to_card_id": "x", "relationship": "cites"}]},
                          resolve=boom)
    assert n and n[0]["id"] == "x" and n[0]["resolved"] is False


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
