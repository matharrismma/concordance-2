"""Ask — the conduit front door: finds/verifies/cites, never generates.

Proves deterministic routing, crisis-help-first, ultimate-matters-point-to-Christ, verify
hands a receipt, and the /ask endpoint. Runnable with pytest OR directly.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-ask-")
# Discernment validates loose references against the real canon; the deck stays isolated in
# the temp dir above, but the Bible itself comes from the repo data (droplet-primary, not git).
os.environ["CONCORDANCE_BIBLE_EN"] = str(Path(__file__).resolve().parent.parent / "data" / "bible_en.jsonl")
# the Body's characters member reads Easton's from the repo data (droplet-primary, not git)
os.environ["CONCORDANCE_CHARACTERS_DIR"] = str(
    Path(__file__).resolve().parent.parent / "data" / "characters")
os.environ["CONCORDANCE_PROPHECY_DIR"] = str(
    Path(__file__).resolve().parent.parent / "data" / "prophecy")
os.environ["CONCORDANCE_CARDS_JSONL"] = str(
    Path(__file__).resolve().parent.parent / "data" / "cards.jsonl")  # isolate seal writes

from concordance import ask  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402

SEC = EngineConfig("secular")
WIT = EngineConfig("witness")


def test_classify_routes():
    assert ask.classify("2+2 = 4") == "verify"
    assert ask.classify("John 3:16") == "scripture"
    assert ask.classify("what is G26?") == "word_study"
    assert ask.classify("honestly I want to die") == "crisis"
    assert ask.classify("what is the meaning of life") == "ultimate"
    assert ask.classify("grace and truth") == "search"


def test_comfort_meets_distress_with_a_word_not_a_search():
    """Someone bringing their own hurt is discerned and met gently — a fitting verse and real
    people first — instead of being handed a keyword search."""
    assert ask.classify("I feel anxious and afraid") == "comfort"
    assert ask.classify("I am so lonely") == "comfort"
    r = ask.respond("I feel anxious and afraid", SEC)
    assert r["kind"] == "comfort"
    assert "not carrying it alone" in r["message"]
    assert r.get("real_help") and any("church" in x.lower() for x in r["real_help"])
    assert "scripture" in r                                   # a verse is offered (text may be data-dependent)


def test_distress_never_overrides_crisis():
    """Crisis outranks the comfort lane — a mild feeling word cannot mask real danger."""
    assert ask.classify("I feel hopeless and I want to die") == "crisis"
    assert ask.distress_ref("I want to end my life") == ""    # crisis short-circuits before comfort


def test_a_remedy_question_reaches_the_apothecary():
    """An ailment or remedy is discerned to the Apothecary, not dumped into a classics search."""
    from concordance import router
    assert router.route("what helps a sore throat")["member"] == "apothecary"
    assert router.route("best tea for a cough")["member"] == "apothecary"
    assert router.route("a remedy for insomnia")["member"] == "apothecary"
    # and it does not steal ordinary study questions
    assert router.route("what does grace mean")["member"] != "apothecary"


def test_crisis_puts_real_help_first():
    r = ask.respond("sometimes I want to die", SEC)
    assert r["kind"] == "crisis"
    assert any("988" in x["label"] for x in r["resources"])


def test_ultimate_points_to_christ_and_people():
    r = ask.respond("what is the meaning of life", SEC)
    assert r["kind"] == "ultimate"
    assert any(v["ref"] == "John 14:6" for v in r["scripture"])
    assert r["real_help"] and "also_in_the_keeping" in r


def test_verify_hands_a_receipt_and_catches_falsehood():
    good = ask.respond("2+2 = 4", SEC)
    assert good["verify"]["verdict"] == "HOLDS" and good["verify"].get("seal")
    bad = ask.respond("2+2 = 5", SEC)
    assert bad["verify"]["verdict"] == "BROKEN"


def test_search_is_the_default():
    r = ask.respond("justice and mercy", SEC)
    assert r["kind"] == "found" and "results" in r


def test_scripture_routes_on_witness_but_falls_back_on_secular():
    assert "scripture" in ask.respond("John 3:16", WIT)          # witness resolves (text may be empty w/o data)
    assert ask.respond("John 3:16", SEC)["kind"] == "found"       # secular has no resolve -> search


def test_every_response_carries_the_conduit_note():
    for q in ("2+2 = 4", "grace", "the meaning of life", "I want to die"):
        assert "not generate the answer" in ask.respond(q, SEC)["note"]


def test_ask_endpoint():
    from concordance.web.api import dispatch
    st, p = dispatch("POST", "/ask", {}, {"text": "2+2 = 4"}, SEC)
    assert st == 200 and p["verify"]["verdict"] == "HOLDS"
    assert dispatch("POST", "/ask", {}, {"text": "  "}, SEC)[0] == 400


# ── how a person actually types when they are reaching for help ─────────────────────────────

# Each of these routed to an ordinary keyword SEARCH on the live site. The first is the worst:
# the phrase was already in the crisis list — a phone's curly apostrophe (U+2019) walked past it.
_WAS_MISSED = (
    "i don’t want to be here",      # phone apostrophe vs. the straight one in the list
    "I want to end it",
    "i want to end it tonight",
    "i cant go on",                        # no apostrophe at all
    "i can’t do this anymore",
    "i want to take my own life",
    "theres nothing to live for",
    "im going to unalive myself",          # the euphemism used to get past filters
    "everyone would be better off without me",
    "i am suicidal",
)


def test_the_phrasings_that_used_to_be_missed_now_reach_help():
    for text in _WAS_MISSED:
        assert ask.classify(text) == "crisis", f"routed away from help: {text!r}"


def test_a_phones_apostrophe_cannot_defeat_the_crisis_check():
    """The straight and curly forms of the same sentence must behave identically."""
    straight, curly = "i don't want to be here", "i don’t want to be here"
    assert ask.classify(straight) == ask.classify(curly) == "crisis"
    assert ask.is_crisis(straight) and ask.is_crisis(curly)


def test_the_router_and_ask_can_never_disagree_about_crisis():
    """One matcher, not two lists. A copied safety list is a list that drifts."""
    from concordance import router
    for text in _WAS_MISSED + ("i want to kill myself", "how tall is Everest", ""):
        agree = (ask.classify(text) == "crisis") == (router.route(text)["member"] == "crisis")
        assert agree, f"ask and router disagree on: {text!r}"


def test_crisis_help_is_offered_not_withheld_when_wording_is_ambiguous():
    """Deliberate asymmetry: an unnecessary helpline is a small cost, a missed person is not.
    No exclusion logic is added to the safety check — exclusions are how bypasses get built."""
    r = ask.respond("i want to die", SEC)
    assert r["kind"] == "crisis" and any("988" in x["label"] for x in r["resources"])


# ── whatever comes back has to be showable ──────────────────────────────────────────────────

# The fields site/index.html knows how to draw. A response carrying none of them renders as an
# empty turn: the page looks broken and the failure is invisible.
#
# This checks PRESENCE, not content — whether a lookup finds anything depends on which corpora
# are on the machine, and a test that demanded results would fail on a bare checkout for a
# reason that has nothing to do with the bug.
#
# Being straight about the limit: this cannot catch a field the CLIENT forgot to render, which
# is exactly what went wrong — word_study was always in the response, and index.html had no
# branch for it, so it rode along on the standing note until that note was removed. The guard
# for that half lives in the page itself, where a render producing no HTML now says so instead
# of drawing a blank.
RENDERABLE = ("message", "verify", "audit", "word_study", "scripture", "resources", "results")


def test_every_kind_returns_something_the_page_can_show():
    asks = ("is 0.1 + 0.2 = 0.3",              # verify
            "what does chesed mean in H2617",  # word_study
            "read John 3:16",                  # scripture
            "tell me about covenant",          # found / search
            "what is the meaning of life",     # ultimate
            "sometimes I want to die")         # crisis
    for text in asks:
        r = ask.respond(text, SEC)
        shown = [k for k in RENDERABLE if k in r]
        assert shown, f"{r.get('kind')!r} for {text!r} renders as an empty turn (keys: {sorted(r)})"


# ── discernment: a verse question answered however a person writes it ───────────────────────

def test_discerns_a_phone_typed_reference():
    """A phone buries the colon two keyboard layers deep; dictation never produces one.
    "John 3 16" and "John 3.16" are the same ask as "John 3:16"."""
    for t in ("explain John 3 16", "John 3.16", "what does John 3 16 mean"):
        assert ask.classify(t) == "scripture", t
        r = ask.respond(t, WIT)
        assert (r.get("scripture") or [{}])[0].get("ref") == "John 3:16", t


def test_discerns_the_churchs_own_passage_names():
    """"The prodigal son" has meant Luke 15 for two thousand years. Returning keyword junk
    for it was a failure of discernment, not phrasing."""
    cases = {"what does the parable of the sower mean": "Matthew 13:",
             "the prodigal son": "Luke 15:",
             "explain the good samaritan": "Luke 10:"}
    for t, prefix in cases.items():
        assert ask.classify(t) == "scripture", t
        rows = ask.respond(t, WIT).get("scripture") or []
        assert rows and rows[0]["ref"].startswith(prefix), (t, rows[:1])


def test_a_room_number_is_never_mistaken_for_scripture():
    """The loose form is trusted only when the canon resolves it."""
    assert ask.classify("meet me in Room 12 14") == "search"


def test_a_discerned_verse_never_ships_keyword_junk():
    r = ask.respond("what does the parable of the sower mean", WIT)
    assert r["kind"] == "scripture" and "results" not in r


def test_explain_reads_the_passage_not_one_line():
    rows = ask.respond("explain the prodigal son", WIT).get("scripture") or []
    assert len(rows) >= 20, "a named passage is the whole passage, not a single verse"


# ── the Body: prose reaches every member, and a routed ask never ships junk ─────────────────

def test_the_body_answers_money_teaching_people_and_prophecy():
    """Member data paths resolve at CALL time, so the repo-data overrides are set inside the
    test — under one pytest process the module-level env belongs to whichever test file
    imported last (SOP-11), and this test must not depend on collection order."""
    repo = Path(__file__).resolve().parent.parent / "data"
    saved = {k: os.environ.get(k) for k in
             ("CONCORDANCE_CHARACTERS_DIR", "CONCORDANCE_PROPHECY_DIR")}
    os.environ["CONCORDANCE_CHARACTERS_DIR"] = str(repo / "characters")
    os.environ["CONCORDANCE_PROPHECY_DIR"] = str(repo / "prophecy")
    try:
        cases = {"help me budget my money": "steward",
                 "I cant afford groceries this month": "steward",
                 "teach me fractions": "coach",
                 "who was Moses": "characters",
                 "prophecies about the messiah": "prophecy"}
        for text, want in cases.items():
            r = ask.respond(text, SEC)
            assert r["kind"] == want, (text, r["kind"])
            assert r.get("message") or r.get("resources"), f"{want} answered with nothing"
            assert "results" not in r, f"{want} shipped keyword junk under its answer"
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_a_member_with_nothing_falls_through_to_an_honest_search():
    """No specialist bluffs: a characters ask for nobody real ends in search, not a shrug."""
    r = ask.respond("who was Zaphenath the imaginary", SEC)
    assert r["kind"] == "found"


def test_crisis_outranks_every_member():
    """Money words plus crisis words is a person in crisis, not a budget question."""
    r = ask.respond("i cant afford rent and i want to end it", SEC)
    assert r["kind"] == "crisis"
    assert any("988" in x["label"] for x in r["resources"])


# ── the organizing book: writing is kept and pinned, never answered with junk ───────────────

def test_a_list_is_pinned_not_searched():
    r = ask.respond("milk\neggs\nbread\nchicken feed", SEC)
    assert r["kind"] == "kept_list" and r["pin"]["kind"] == "list"
    assert "results" not in r


def test_a_reminder_knows_its_day():
    r = ask.respond("remind me to call the bank on Thursday", SEC)
    assert r["kind"] == "reminder" and r["pin"]["due"] is not None


def test_stream_of_consciousness_is_kept_quietly():
    r = ask.respond("I keep circling the same thought about the barn and I want it down before it goes", SEC)
    assert r["kind"] == "kept_note" and "results" not in r


def test_a_crisis_reminder_is_a_crisis():
    r = ask.respond("remind me to end it all", SEC)
    assert r["kind"] == "crisis"


# ── leaning into the strength the traffic showed: verified, connected verse search ──────────

def test_an_exact_reference_ranks_the_verse_card_first():
    """87% of use is search, and its commonest human shape is a verse reference. The card that
    IS Philippians 4:13 must beat a card that merely says 'Philippians' more often."""
    from concordance import corpus
    hits = corpus.search("Philippians 4:13", limit=5)
    assert hits, "no results"
    top = " ".join(str(hits[0].get("title", "")).lower().split())
    assert top == "philippians 4:13", f"exact verse did not rank first: {hits[0].get('title')!r}"


def test_the_search_answer_carries_its_connected_cloud():
    """The unrepeatable strength: a hit returns WITH the witnesses connected to it."""
    r = ask.respond("Philippians 4:13", SEC)
    if r["kind"] == "found" and r.get("results"):
        cloud = r.get("cloud")
        assert cloud and cloud.get("witnesses"), "the top hit shipped no connected cloud"
        assert all(w.get("id") and w.get("title") for w in cloud["witnesses"])


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} ask tests passed — conduit routing: find/verify/cite, help-first, points to Christ.")
