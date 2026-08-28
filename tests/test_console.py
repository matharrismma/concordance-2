"""The Console — the audio-native coach & scribe router.

Proves: crisis outranks everything (even a crisis phrased as a note); dictation is kept VERBATIM with
the command word stripped; schedule/copies route by intent; the coach speaks a short verified answer
with a connection woven in and the source deferred; and intake keeps the LOCATION, never the blob.
Light by design — the coach path is monkeypatched so the suite never loads the 671k-card corpus.
"""
from concordance import console
from concordance.config import EngineConfig

SEC = EngineConfig("secular")


def test_crisis_outranks_every_other_intent():
    """A cry is met first (Mt 25) — even when it wears the shape of a note or a schedule."""
    for text in ("I want to end my life", "note that there is no hope left for me",
                 "remind me that I want to die", "ready to give up on life"):
        assert console.classify_intent(text) == "crisis", text
    r = console.dispatch("note that I don't want to be here anymore", SEC)
    assert r["intent"] == "crisis" and "988" in r["spoken"]


def test_dictation_is_kept_verbatim_with_the_command_stripped():
    r = console.dispatch("note that the well by the barn is dry", SEC)
    assert r["intent"] == "dictate"
    assert r["record"]["text"] == "the well by the barn is dry"     # the command word is not kept
    assert r["record"]["kept"] == "edge"                            # no owner -> store-nothing on server
    assert r["caption"] == "the well by the barn is dry"            # verbatim, exactly as said


def test_dictation_writes_to_the_book_of_days_when_an_owner_is_proven(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    r = console.dispatch("write down that the goats got out", SEC, owner="nh_farmer")
    assert r["record"]["kept"] == "book_of_days" and r["record"]["entry_id"]
    from concordance import bookofdays
    entries = bookofdays.entries("nh_farmer")["entries"]
    assert any(e["text"] == "the goats got out" for e in entries)   # kept verbatim, command word stripped


def test_schedule_and_copies_route_and_never_act_without_confirmation():
    s = console.dispatch("put on my calendar a meeting tuesday", SEC)
    assert s["intent"] == "schedule" and s.get("proposed")     # proposed, not written
    c = console.dispatch("make 3 copies of this", SEC)
    assert c["intent"] == "copies" and c["count"] == 3


def test_the_coach_answers_in_their_frame_and_offers_a_choice_of_whats_next(monkeypatch):
    # monkeypatch the corpus-backed pieces so this is fast and hermetic
    monkeypatch.setattr(console._ask, "respond", lambda *a, **k: {
        "kind": "search", "results": [{"id": "card_water", "title": "Purifying water",
        "snippet": "Boil for one minute at a rolling boil; at altitude, three."}],
        "generated": False, "note": "conduit"})
    # two found threads; the one sharing the person's OWN word ("well") must surface first — their frame
    monkeypatch.setattr(console, "_connection_list", lambda cid: [
        {"id": "card_exodus", "title": "Exodus 15 the waters made sweet"},
        {"id": "card_well", "title": "Digging and keeping a well"}])
    r = console.dispatch("how do I keep my well water safe", SEC)
    assert r["intent"] == "ask" and r["generated"] is False
    assert "Boil for one minute" in r["spoken"]
    assert "well" in r["frame"]                                       # their vocabulary is read
    assert r["connections"][0]["id"] == "card_well"                  # frame-focus: their word ranks first
    assert r["source"]["ref"] == "/card/card_water"                 # the full source, deferred
    # ALWAYS offers what's next, and ALWAYS a door to a new path (freedom; we present, we do not cross)
    labels = [n["label"] for n in r["next"]]
    assert any("well" in l.lower() for l in labels)                 # a next step in their frame
    assert labels[-1].lower().startswith("or ask about anything else")
    assert "Your choice" in r["spoken"] and len(r["spoken"]) < 700   # short — speakable, LoRa-small


def test_an_honest_miss_stays_a_miss():
    monkeypatch = None
    from concordance import console as C
    orig = C._ask.respond
    try:
        C._ask.respond = lambda *a, **k: {"kind": "search", "results": [], "generated": False}
        r = C.dispatch("what is the airspeed of a laden swallow over Jerusalem", SEC)
        assert r["kind"] == "miss" and "not in the keeping" in r["spoken"].lower()
    finally:
        C._ask.respond = orig


def test_intake_keeps_the_location_not_the_blob():
    a = console.intake_artifact(source_location="/sd/photos/well_pump.jpg", kind="image",
                                extracted_text="Shurflo 9300, 24V")
    assert a["ok"]
    art = a["artifact"]
    assert art["source_location"] == "/sd/photos/well_pump.jpg"     # the location is kept
    assert art["title"] == "well_pump.jpg" and art["artifact_kind"] == "image"
    assert art["extracted_text"] == "Shurflo 9300, 24V"            # the usable form
    assert "blob" not in art and "bytes" not in art                # never the file itself


def test_intake_requires_a_location():
    a = console.intake_artifact(source_location="   ")
    assert not a["ok"] and "location" in a["error"].lower()
