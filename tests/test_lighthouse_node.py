"""LIGHTHOUSE NODE — the engine as infrastructure behind a radio.

Pure: compose_reply/daily_word take injectable search/crisis/daily fns, so the whole chain
(compose -> sign -> chunk -> reassemble -> verify offline) runs with NO radio and NO corpus. The
composer is sovereign and deterministic: crisis-first, then the verified keeping, then an honest
miss (a gap stays a gap). Every reply is signed by the station and verifies AUTHENTIC when the
station key is pinned.
"""
from concordance import lighthouse_node as ln

_STATION = ("dummy", "dummy")  # replaced per-test with a real keypair


def _card(cid, title, body):
    return {"id": cid, "title": title, "body": body}


def test_crisis_is_answered_first_with_real_help_and_no_lookup():
    def _search(q, n):        # a crisis must never depend on retrieval
        raise AssertionError("crisis path must not hit the corpus")
    r = ln.compose_reply("i want to end it all", is_crisis_fn=lambda t: True, search_fn=_search)
    assert r["kind"] == "crisis" and r["verified"] and "988" in r["text"] and r["ref"] == "tel:988"


def test_a_verified_card_rides_the_mesh_and_verifies_authentic():
    card = _card("first-aid-bleeding", "Control severe bleeding",
                 "Press hard directly on the wound with a clean cloth and do not let up.")
    r = ln.simulate_answer("how do i stop bad bleeding",
                           search_fn=lambda q, n: [card], is_crisis_fn=lambda t: False)
    assert r["reply"]["kind"] == "answer" and r["reply"]["verified"]
    assert r["reassembled"] and r["verify"]["unaltered"] and r["verify"]["authentic"]
    assert r["reply"]["ref"] == "/c/first-aid-bleeding"
    assert r["reply"]["ref"] in r["reply"]["text"]                 # the pull-ref always survives


def test_the_relevance_floor_holds_a_tangential_top_hit_becomes_a_miss():
    # the top hit shares NO content word with the question -> not dressed up as the answer
    tangential = _card("knots", "The knots worth knowing", "A bowline and a clove hitch for the camp.")
    r = ln.compose_reply("how do i purify water", search_fn=lambda q, n: [tangential],
                         is_crisis_fn=lambda t: False)
    assert r["kind"] == "miss" and not r["verified"] and r["found"] is False


def test_an_empty_corpus_is_an_honest_miss_never_a_crash():
    r = ln.compose_reply("anything at all", search_fn=lambda q, n: [], is_crisis_fn=lambda t: False)
    assert r["kind"] == "miss" and not r["verified"]


def test_a_corpus_error_degrades_to_a_miss_not_an_exception():
    def _boom(q, n):
        raise RuntimeError("shard unavailable")
    r = ln.compose_reply("start a fire", search_fn=_boom, is_crisis_fn=lambda t: False)
    assert r["kind"] == "miss" and not r["verified"]


def test_the_answer_fits_the_byte_budget_and_still_keeps_the_ref():
    big = _card("x", "Long card", "word " * 500)
    r = ln.compose_reply("long card word", max_bytes=200,
                         search_fn=lambda q, n: [big], is_crisis_fn=lambda t: False)
    assert len(r["text"].encode("utf-8")) <= 200 and r["text"].rstrip().endswith(r["ref"])


def test_the_daily_word_is_signed_and_verifies_authentic():
    verse = _card("john-15-5", "I am the vine", "Apart from me you can do nothing.")
    r = ln.simulate_daily("2026-08-16", daily_fn=lambda s: verse)
    assert r["reply"]["kind"] == "daily" and r["reply"]["verified"]
    assert r["verify"]["authentic"] and r["reply"]["ref"] == "/c/john-15-5"


def test_the_same_seed_gives_the_same_daily_word():
    verse = _card("v", "A word", "for the day")
    a = ln.daily_word("2026-08-16", daily_fn=lambda s: verse)
    b = ln.daily_word("2026-08-16", daily_fn=lambda s: verse)
    assert a["text"] == b["text"] and a["card_id"] == b["card_id"]


def test_packets_fit_the_lora_budget():
    card = _card("c", "A card", "with a reasonable amount of body text to answer the question well")
    r = ln.simulate_answer("a card question", search_fn=lambda q, n: [card], is_crisis_fn=lambda t: False)
    assert r["packets"] >= 1 and r["max_packet_bytes"] <= ln._wire.MTU
