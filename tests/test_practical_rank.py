"""VOICE-2 retrieval quality — the real "responses aren't great".

A practical / how-to answer must LEAD with an INSTRUCTIONAL field card, never the academic
Theory-Assay catalog or a drug/food-DB product row it merely shares a word with. And a CONSTRUCTION
how-to ("make lye soap from wood ash") must reach the full practical pipeline — not the weaker
`resourceful` branch, which returned a bare results list with no lead (measured empty live 2026-08-14).

Pure: the distinctive-word check (which consults the corpus) is stubbed, so no corpus is needed.
"""
from concordance import ask


def _card(cid, shelf, title, body=""):
    return {"id": cid, "shelf": shelf, "title": title, "body": body}


def test_rank_leads_with_the_instructional_field_card(monkeypatch):
    # shares-a-word stubbed to a simple title/body overlap so the TIERING is what's under test
    monkeypatch.setattr(ask, "_shares_a_word",
                        lambda q, c: any(w in (c.get("title", "") + " " + c.get("body", "")).lower()
                                         for w in q.lower().split()))
    pool = [
        _card("t", "theories", "Hess's law of constant heat summation"),   # academic — must sink
        _card("d", "medicine", "Warm Vanilla Hand Sanitizer"),             # product noise — must sink
        _card("x", "history", "The water supply of ancient Rome"),         # shares 'water', not a field card
        _card("f", "survival", "Purify water: boiling and filtration"),    # instructional — must LEAD
    ]
    ranked = ask._practical_rank("purify water", pool)
    assert ranked[0]["id"] == "f", f"led with {ranked[0]['shelf']}"        # a field how-to leads
    assert ranked[-1]["shelf"] in ("theories", "medicine")                # academic / product noise last


def test_within_a_tier_the_card_that_names_the_subject_in_its_title_leads(monkeypatch):
    # both are instructional field cards that share the word 'fire' — but one is ABOUT starting a
    # fire (title) and the other merely mentions fire in its body. The title match must lead.
    monkeypatch.setattr(ask, "_shares_a_word", lambda q, c: "fire" in
                        (c.get("title", "") + " " + c.get("body", "")).lower())
    pool = [
        _card("k", "survival", "The knots worth knowing", body="useful near a fire pit"),  # body-only
        _card("f", "survival", "Starting a fire without matches"),                          # title match
    ]
    assert ask._practical_rank("start a fire", pool)[0]["id"] == "f"


def test_theory_and_product_never_lead_even_when_all_share_a_word(monkeypatch):
    monkeypatch.setattr(ask, "_shares_a_word", lambda q, c: True)          # everything shares a word
    pool = [_card("t", "theories", "Thermochemistry"),
            _card("s", "medicine", "Scented Foaming Hand Wash"),           # product noise
            _card("f", "first_aid", "Treat a burn")]
    assert ask._practical_rank("treat a burn", pool)[0]["id"] == "f"


def test_stem_collapses_common_inflections():
    for a, b in [("burn", "burns"), ("burn", "burning"), ("fire", "fires"),
                 ("preserve", "preserves"), ("preserve", "preserving"), ("deliver", "delivering")]:
        assert ask._stem(a) == ask._stem(b), f"{a!r} vs {b!r}: {ask._stem(a)} != {ask._stem(b)}"


def test_title_miss_fires_the_tortoise_but_stemming_keeps_a_real_card():
    # "start a fire" -> a knots card names NONE of the subject -> a masked gap, fire the tortoise
    assert not ask._title_names_subject("start a fire", {"title": "The knots worth knowing"})
    # BUT stemming must keep a genuine card: "treat a burn" -> "Burns and scalds" is the answer, and
    # exact-token matching ('burn' != 'burns') would wrongly fire the tortoise past it.
    assert ask._title_names_subject("how do I treat a burn", {"title": "Burns and scalds"})
    assert ask._title_names_subject("how do I purify water", {"title": "Making water safe to drink"})
    # a query with no real subject word (all generic/stop) never forces the tortoise
    assert ask._title_names_subject("how do I make it", {"title": "Anything at all"})


def test_construction_howto_routes_to_the_full_pipeline():
    # "make X from Y" is a how-to that names its materials — it must NOT be swallowed by resourceful,
    # and must raise the practical flag so it gets the ranked pool + the tortoise.
    assert not ask._wants_resourceful("make lye soap from wood ash")
    assert ask._MAKE_FROM.search("make lye soap from wood ash")
    assert ask._MAKE_FROM.search("build a water filter with sand and charcoal")


def test_the_genuinely_constrained_question_stays_resourceful():
    assert ask._wants_resourceful("what can I do with a tarp and some rope")
    assert ask._wants_resourceful("all I have is flour and water")
    assert not ask._MAKE_FROM.search("what can I do with a tarp and some rope")
