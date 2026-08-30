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


def test_schedule_parses_summary_and_time_and_never_writes_without_a_calendar(monkeypatch):
    for k in ("NH_CALENDAR_WRITE", "CONSOLE_SCHEDULE_AGENT", "CONSOLE_SCHEDULE_GRANTOR"):
        monkeypatch.delenv(k, raising=False)                   # hermetic: no calendar named anywhere
    r = console.dispatch("remind me to check the goats at 6pm", SEC)
    assert r["intent"] == "schedule"
    assert r["proposed"]["summary"] == "check the goats"
    assert r["proposed"]["start_iso"] and r["proposed"]["start_iso"].endswith("T180000")   # 6pm parsed
    assert r["kind"] != "scheduled"                            # not written — no calendar configured
    # no clear time -> ask, never guess (a wrong time is worse than a question)
    q = console.dispatch("remind me to pray", SEC)
    assert q["kind"] == "schedule" and q["proposed"]["start_iso"] is None and "when" in q["spoken"].lower()


def test_schedule_writes_to_the_operators_own_calendar_with_no_grant(monkeypatch):
    """The common case: the operator names their OWN calendar (one value) and the console writes to it
    directly — no consent ceremony, because writing to your own calendar on your own node is your own
    act, not a proxy. The guarded on-behalf create_event is NOT touched here."""
    monkeypatch.delenv("CONSOLE_SCHEDULE_AGENT", raising=False)
    monkeypatch.delenv("CONSOLE_SCHEDULE_GRANTOR", raising=False)
    monkeypatch.setenv("NH_CALENDAR_WRITE", "/tmp/mine.ics")
    from concordance import connect_write
    seen = {}

    def fake_direct(summary, start_iso, **k):
        seen.update(summary=summary, start_iso=start_iso)
        return {"ok": True, "uid": "evt-self", "target_kind": "file", "scope_used": "operator_self"}

    def forbidden(*a, **k):
        raise AssertionError("the operator's own calendar must NOT go through the consent gate")

    monkeypatch.setattr(connect_write, "create_event_direct", fake_direct)
    monkeypatch.setattr(connect_write, "create_event", forbidden)
    r = console.dispatch("remind me to check the goats at 6pm", SEC)
    assert r["kind"] == "scheduled" and r["receipt"]["uid"] == "evt-self"
    assert "needs" not in r                                    # no consent asked of the operator
    assert seen["summary"] == "check the goats" and seen["start_iso"].endswith("T180000")


def test_schedule_writes_to_the_calendar_when_configured_and_granted(monkeypatch):
    """When the operator has named a calendar and authorized the console, a parsed event is WRITTEN via
    the consent-gated create_event, and the console speaks the receipt."""
    monkeypatch.setenv("CONSOLE_SCHEDULE_AGENT", "nh_console")
    monkeypatch.setenv("CONSOLE_SCHEDULE_GRANTOR", "pubkey_hex")
    monkeypatch.setenv("NH_CALENDAR_WRITE", "/tmp/cal.ics")
    from concordance import connect_write
    seen = {}

    def fake_create(grantor, agent, summary, start_iso, **k):
        seen.update(grantor=grantor, agent=agent, summary=summary, start_iso=start_iso)
        return {"ok": True, "uid": "evt-123", "target": "/tmp/cal.ics"}

    monkeypatch.setattr(connect_write, "create_event", fake_create)
    r = console.dispatch("remind me to check the goats at 6pm", SEC)
    assert r["kind"] == "scheduled" and r["receipt"]["uid"] == "evt-123"
    assert seen["agent"] == "nh_console" and seen["summary"] == "check the goats"
    assert seen["start_iso"].endswith("T180000")


def test_copies_makes_n_copies_of_the_named_content():
    r = console.dispatch("make 3 copies of the water plan", SEC)
    assert r["intent"] == "copies" and r["count"] == 3
    assert len(r["copies"]) == 3 and all(c["text"] == "the water plan" for c in r["copies"])
    a = console.dispatch("make 2 copies", SEC)                 # nothing named -> asks, no copies made
    assert a["kind"] == "copies" and a["count"] == 2 and "copies" not in a


def test_the_coach_answers_in_their_frame_and_offers_a_choice_of_whats_next(monkeypatch):
    # monkeypatch the corpus-backed pieces so this is fast and hermetic
    # the answer plus two more found hits; the one sharing the person's OWN word ("well") must surface
    # first — their frame focuses which thread is offered next
    monkeypatch.setattr(console._ask, "respond", lambda *a, **k: {
        "kind": "search", "generated": False, "note": "conduit", "results": [
            {"id": "card_water", "title": "Purifying water",
             "snippet": "Boil for one minute at a rolling boil; at altitude, three."},
            {"id": "card_exodus", "title": "Exodus 15 the waters made sweet"},
            {"id": "card_well", "title": "Digging and keeping a well"}]})
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


def test_whats_next_prefers_clean_titles_and_drops_the_unambiguously_broken(monkeypatch):
    """Title hygiene for 'what's next' in a partly-OCR'd corpus: mojibake and lowercase sentence-
    fragments are dropped from the offers; among equally-relevant threads the cleaner title surfaces
    first. We SELECT, never repair the stored title (legitimate acronyms/accents/prefixes are untouched)."""
    monkeypatch.setattr(console._ask, "respond", lambda *a, **k: {
        "kind": "search", "generated": False, "results": [
            {"id": "card_ans", "title": "Making water safe", "snippet": "Boil one minute."},
            {"id": "card_frag", "title": "for the use of unfiltered water a connec"},   # fragment -> dropped
            {"id": "card_moji", "title": "Taste of the � water"},                   # mojibake -> dropped
            {"id": "card_ocr", "title": "Taste of the Rh'cr Water"},                     # OCR garble -> penalized
            {"id": "card_clean", "title": "Storing Water Safely"}]})                     # clean -> preferred
    r = console.dispatch("how do I keep water safe", SEC)
    threads = [n["label"] for n in r["next"] if n.get("ref")]
    assert threads and threads[0] == "Storing Water Safely"        # cleaner title preferred over garble
    assert "for the use of unfiltered water a connec" not in threads
    assert not any("�" in l for l in threads)                 # mojibake never offered


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


def test_a_topicless_ask_is_met_with_the_hare_question_not_a_blind_answer(monkeypatch):
    # the FORM GATE in front of the keeping: an ask with no topic asks the one blank and looks nothing
    # up (Prov 18:13 — never answer before hearing). The keeping is not even touched.
    called = {"n": 0}
    def spy(*a, **k):
        called["n"] += 1
        return {"kind": "search", "results": [], "generated": False}
    monkeypatch.setattr(console._ask, "respond", spy)
    r = console.dispatch("look up", SEC)
    assert r["intent"] == "ask" and r["kind"] == "clarify"
    assert r["spoken"] == "What would you like me to find?"
    assert r["cost"] == "free" and called["n"] == 0            # nothing fetched before we heard


def test_a_real_ask_is_the_free_hare_from_the_keeping_with_the_tortoise_offered(monkeypatch):
    monkeypatch.setattr(console._ask, "respond", lambda *a, **k: {
        "kind": "search", "generated": False, "results": [
            {"id": "card_water", "title": "Purifying water",
             "snippet": "Boil for one minute at a rolling boil."}]})
    r = console.dispatch("how do I purify water", SEC)
    assert r["kind"] != "clarify" and r["cost"] == "free"      # the keeping answer is the free hare
    assert r["tortoise"]["offered"] is True and r["tortoise"]["cost"] == "cheap"
    assert r["source"] and r["source"]["ref"].startswith("/card/")   # the waybill to the full source


def test_a_miss_offers_the_tortoise_and_makes_no_false_promise(monkeypatch):
    monkeypatch.setattr(console._ask, "respond", lambda *a, **k: {
        "kind": "search", "results": [], "generated": False})
    r = console.dispatch("what is the torque spec for a Lister CS head", SEC)
    assert r["kind"] == "miss" and "not in the keeping" in r["spoken"].lower()
    assert r["tortoise"]["offered"] is True                    # offered, the user's to choose
    low = r["spoken"].lower()
    assert "written down the want" not in low                  # no claim of a want we didn't open
    assert "24" not in low and "48" not in low and "hour" not in low   # no clock promised


def test_a_checkable_claim_gets_the_verdict_not_a_false_miss(monkeypatch):
    """THE CORE PROMISE on the console door: a verify payload must be spoken as its verdict + worked
    reasoning, never fall through to 'not in the keeping'. ("is 91 prime" was returning a false miss.)"""
    monkeypatch.setattr(console._ask, "respond", lambda *a, **k: {
        "kind": "verify", "generated": False,
        "verify": {"verdict": "BROKEN", "detail": "91 is NOT prime (7 x 13); it was claimed prime.",
                   "trail": [], "seal": {"cite_url": "/s/abc123", "content_hash": "abc123"}}})
    r = console.dispatch("is 91 prime", SEC)
    assert r["kind"] == "verify"                                # not "miss"
    assert "does not hold" in r["spoken"].lower() and "91" in r["spoken"]
    assert r["source"] and r["source"]["ref"] == "/s/abc123"   # the re-checkable receipt is offered
    assert "tortoise" not in r                                  # a computed verdict has no source to fetch


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


_MINI_PDF = (b"%PDF-1.4\n"
             b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
             b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
             b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 200]/Contents 4 0 R>>endobj\n"
             b"4 0 obj<</Length 60>>\nstream\n"
             b"BT /F1 18 Tf 20 120 Td (Sovereign PDF text extraction works) Tj ET\n"
             b"endstream endobj\ntrailer<</Root 1 0 R>>\n%%EOF")


def test_pdf_intake_extracts_text_and_keeps_the_location_not_the_blob():
    """A dropped PDF's TEXT is extracted (sovereign stdlib floor, or pypdf if present) and the bytes are
    discarded — the card keeps the LOCATION and the usable text, never the blob."""
    from concordance import pdf_extract
    assert "Sovereign PDF text extraction works" in pdf_extract.text(_MINI_PDF)
    a = console.intake_artifact(source_location="/sd/docs/note.pdf", pdf_bytes=_MINI_PDF)
    assert a["ok"]
    art = a["artifact"]
    assert art["artifact_kind"] == "pdf"
    assert "Sovereign PDF text extraction works" in art["extracted_text"]
    assert art["source_location"] == "/sd/docs/note.pdf"       # the location is kept
    assert len(art["sha256"]) == 64                            # the source is hashed for identity
    assert "pdf_bytes" not in art and "blob" not in art        # the blob is never kept


def test_pdf_extract_returns_empty_not_garbage_on_a_non_pdf():
    """Honest emptiness, never noise: a non-PDF or an unreadable/scanned PDF yields "" — the location
    is still kept, and the person can dictate a description."""
    from concordance import pdf_extract
    assert pdf_extract.text(b"this is plainly not a pdf") == ""
    assert pdf_extract.text(b"") == ""
