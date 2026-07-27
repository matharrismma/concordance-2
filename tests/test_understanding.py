"""Understanding what's asked (subject extraction) + anticipating what's next (with the pastoral
guardrail: NEVER anticipate on crisis or grief)."""
from concordance import ask
from concordance.config import EngineConfig


def test_subject_strips_the_scaffolding():
    assert ask.subject("how far away is the moon") == "moon"
    assert ask.subject("what is the boiling point of water") == "boiling point water"
    assert "world" in ask.subject("when did World War 2 end")
    # an all-scaffolding query leaves nothing (caller falls back to the raw text)
    assert ask.subject("what is it") == ""


def test_chapter_reference_resolves_the_whole_chapter():
    # A chapter is trusted ONLY when the canon resolves it, so a look-alike is never Scripture —
    # this holds with or without provisioned bible text, and must always be true.
    assert ask.find_ref("I have 3 apples") is None
    assert ask.find_ref("meet me at 7") is None
    # The positive case needs the WEB text present (some test envs isolate the data dir); when it
    # is there, real phrasing — a chapter, no verse — resolves and reads the WHOLE chapter.
    from concordance.verifiers import scripture as _s
    if not (_s.read_passage("Psalm 23").get("verses")):
        return
    assert ask.find_ref("what does Psalm 23 say") == "Psalm 23"
    assert ask.find_ref("read Romans 8")
    d = ask.respond("what does Psalm 23 say", EngineConfig(), gate_open=True)
    assert d.get("kind") == "scripture"
    assert len(d.get("scripture") or []) >= 5, "a chapter reads its verses, not just one"


def test_resourceful_routes_materials_but_never_preempts_crisis():
    # "use what you have" — a materials question routes to the practical keeping (pure routing)
    assert ask.classify("what can I do with a tarp and rope") == "resourceful"
    assert ask.classify("I have a plastic bottle and dirty water, what can I do") == "resourceful"
    # SAFETY INVARIANT: crisis always wins first, even when phrased as 'what can I do'
    assert ask.classify("I want to end my life") == "crisis"
    # positive result needs the field library provisioned (some envs isolate the data dir)
    from concordance import corpus
    if not corpus.search("survival shelter", limit=1):
        return
    d = ask.respond("what can I do with a tarp and rope", EngineConfig(), gate_open=True)
    assert d.get("kind") == "resourceful" and d.get("results"), "materials should surface practical cards"


def test_how_to_queries_reach_the_field_library():
    # A practical/how-to question must consult the WHOLE keeping (not shortcut to a mis-predicted
    # deck), so the field library competes and wins. Positive check guarded on provisioned data.
    from concordance import corpus
    if not corpus.search("survival shelter", limit=1):
        return
    d = ask.respond("how to build a fire", EngineConfig(), gate_open=True)
    results = d.get("results") or []
    assert any(r.get("shelf") == "survival" for r in results), \
        "a how-to question should reach the field library, not shortcut past it"


def test_anticipate_offers_next_for_content():
    cfg = EngineConfig()
    d = ask.respond("John 3:16", cfg, gate_open=True)
    assert ask.anticipate("John 3:16", d), "a verse should offer next steps"
    d = ask.respond("what does agape mean", cfg, gate_open=True)
    assert ask.anticipate("what does agape mean", d)


def test_anticipate_is_silent_on_crisis_and_grief():
    # the pastoral invariant — you do not upsell someone who is hurting
    cfg = EngineConfig()
    for q in ["I want to end my life", "I feel like a total failure", "nobody would miss me"]:
        d = ask.respond(q, cfg, gate_open=True)
        if d.get("kind") in ("crisis", "comfort"):
            assert ask.anticipate(q, d) == [], f"anticipation must be silent on {d.get('kind')}"


def test_anticipate_silent_on_a_complete_number():
    cfg = EngineConfig()
    d = ask.respond("what is 8 times 7", cfg, gate_open=True)
    assert d.get("kind") == "compute"
    assert ask.anticipate("what is 8 times 7", d) == []
