"""Decks — the Hare. The need-decks must (a) ROUTE a frightened, plain-language query to the right
frontloaded hand (predict), and (b) OPEN to real cards drawn from their own shelves (open_deck),
with no query needed. This is the 'anticipate need' promise made testable. Hermetic; no network.
"""
from concordance import corpus, decks, graph


def _card(cid, shelf, title, body):
    return {"id": cid, "kind": "reference", "shelf": shelf, "title": title,
            "body": body, "lifecycle_stage": "public",
            "source": {"authority_tier": "reference", "label": "public domain"}}


def _setup(cards):
    corpus._DEFAULT = corpus.Corpus({c["id"]: c for c in cards})
    graph._GRAPH = None


def teardown_function(_fn):
    corpus._DEFAULT = None
    graph._GRAPH = None


def test_deck_definitions_are_wellformed():
    """Every deck is complete and uniquely identified; every NEED deck carries the `seed` that lets
    it be opened without a query; every deck has a non-empty routing vocabulary."""
    seen = set()
    for d in decks._DECKS:
        assert d["id"] and d["id"] not in seen, f"duplicate/blank deck id {d.get('id')!r}"
        seen.add(d["id"])
        assert d["name"] and d["desc"] and d["shelves"], f"{d['id']} missing name/desc/shelves"
        assert d["_route"], f"{d['id']} has no routing vocabulary"
        if d.get("need"):
            assert d.get("seed"), f"need-deck {d['id']} has no seed to open on"


def test_need_decks_route_distress_queries_to_the_right_hand():
    """The core of 'anticipate need': a plain-language query in the words a frightened person would
    use routes to the deck built for that situation. predict() names the position."""
    cases = [
        ("no electricity the power is out and food will spoil", "power-out"),
        ("how do I make dirty water safe to drink", "water-safe"),
        ("someone is bleeding badly and the hospital is far", "first-aid-far"),
        ("I am so afraid and anxious tonight", "be-not-afraid"),
        ("teach my kids to read and do arithmetic at home", "teach-kids"),
        ("grow a vegetable garden and save seed", "grow-food"),
        ("two way radio to call for help off grid", "offgrid-comms"),
        ("my father died and I am grieving", "grieving"),
    ]
    for q, expected in cases:
        top = decks.predict(q, k=3)
        assert top, f"{q!r} routed to nothing"
        assert top[0]["id"] == expected, f"{q!r} -> {top[0]['id']} (wanted {expected}); top={[t['id'] for t in top]}"


def test_all_decks_marks_need_and_lists_the_new_situations():
    """all_decks exposes the need flag so a surface can offer 'by your situation' vs 'by domain',
    and the new situational decks are present."""
    _setup([_card("w1", "water", "Boil water to make it safe",
                  "purify contaminated water by boiling it for one minute; safe drinking water")])
    everything = {d["id"]: d for d in decks.all_decks()}
    for need_id in ("power-out", "water-safe", "first-aid-far", "homestead", "be-not-afraid"):
        assert need_id in everything, f"{need_id} missing from all_decks"
        assert everything[need_id]["need"] is True
    # a domain deck is not flagged as a need-deck
    assert everything["scripture"]["need"] is False


def test_open_deck_deals_a_frontloaded_hand_from_its_own_shelves(monkeypatch):
    """open_deck deals cards drawn from the deck's OWN shelves, with no query — the anticipated hand
    for a moment of need. Its ranker is the corpus's; here we stub that ranker (so the test is
    deterministic and does not depend on IDF over a synthetic corpus) and prove the logic open_deck
    ADDS: it scopes to the deck's shelves, shapes each card, and the SAME card can be dealt into more
    than one deck. Real ranked results are proven live after deploy."""
    from concordance import corpus as _corpus
    universe = [
        _card("w1", "water", "Boil water to make it safe", "purify contaminated water by boiling"),
        _card("w2", "water", "Filtering cloudy water", "filter cloudy water through cloth"),
        _card("s1", "sanitation", "A simple pit latrine", "dig a latrine away from any well"),
        _card("x1", "networking", "TCP port 443", "https rides on tcp port 443"),
    ]

    def fake_search(query, limit=25, include_witness=True, shelves=None):
        hits = [c for c in universe if shelves is None or c["shelf"] in shelves]
        return hits[:limit]

    monkeypatch.setattr(_corpus, "search", fake_search)
    opened = decks.open_deck("water-safe", limit=10)      # shelves: water, sanitation, medicine, ...
    assert opened is not None and opened["need"] is True
    ids = {c["id"] for c in opened["cards"]}
    assert {"w1", "w2", "s1"} <= ids, f"water-safe opened to {ids}"
    assert "x1" not in ids                                # networking is not in the deck's shelves
    assert {c["shelf"] for c in opened["cards"]} <= set(opened["shelves"])
    assert all({"id", "title", "shelf", "snippet"} <= set(c) for c in opened["cards"])
    # the SAME w1 card is also dealt into the sanitation deck (water is one of its shelves too)
    san = decks.open_deck("sanitation", limit=10)
    assert san is not None and "w1" in {c["id"] for c in san["cards"]}


def test_open_unknown_deck_is_none():
    assert decks.open_deck("no-such-deck") is None
