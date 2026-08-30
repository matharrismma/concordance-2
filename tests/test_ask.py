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


def test_kept_tortoise_source_is_recognised_only_when_tagged_and_on_subject():
    """SEARCH ONCE, KEEP IT hinges on recognising the tortoise's OWN kept passages — the ones it
    went and cut FOR this subject on an earlier ask — so a second identical how-to is answered from
    the keeping instantly instead of re-fetching the same public-domain book. The recognition must
    be tight: the `tortoise` tag (so the millions of bulk source excerpts, same shape, never
    short-circuit a real gap) AND the crafted subject sharing a word with what is asked now."""
    kept = {"id": "card_span_x", "shelf": "practical", "subject": "start fire",
            "source": {"authority_tier": "primary_pd"}, "extra": {"tortoise": True}}
    assert ask._is_kept_tortoise_source("how do I start a fire", kept)
    # a BULK source excerpt about fire (no tortoise tag) must NOT short-circuit the gap
    bulk = {**kept, "extra": {}}
    assert not ask._is_kept_tortoise_source("how do I start a fire", bulk)
    # a tortoise card kept for a DIFFERENT subject does not answer this one
    other = {**kept, "subject": "tan a hide"}
    assert not ask._is_kept_tortoise_source("how do I start a fire", other)


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


def test_honest_when_it_does_not_know_a_question():
    """A random classic is worse than honesty. A question the keeping can't match says so plainly
    and offers the real next steps, instead of dumping an irrelevant hit."""
    r = ask.respond("is xqzptn wibbleforp glorptastic", SEC)   # a question with no keeping match
    assert r["kind"] == "found"
    assert not r.get("results")                              # no confident irrelevant dump
    assert "won't invent" in r["message"] or "don't have a verified" in r["message"]
    assert any("check" in (x.get("label", "").lower()) for x in (r.get("resources") or []))


def test_off_domain_shift_flags_a_topic_shift_not_a_related_form():
    """The intent guard the distributional model could NOT do (it conflates topic with intent and
    penalizes synonyms). A how-to answered by a book merely ABOUT the subject in a different frame is a
    masked gap; a related FORM and a health question met by a health book are not — deterministically."""
    c = lambda t: {"title": t}                                   # noqa: E731
    # a related form, a synonym, and a health-intent ask met by a health book -> NOT a shift
    assert ask._off_domain_shift("how do i keep honeybees", c("Every Step in Beekeeping")) is None
    assert ask._off_domain_shift("how do i raise chickens", c("Open-air poultry houses")) is None
    assert ask._off_domain_shift("how do i treat a sick chicken", c("Poultry diseases and their care")) is None
    # a shift to a frame the asker never entered -> flagged (which routes it to the pull)
    assert ask._off_domain_shift("how do i raise hogs", c("Hog cholera: its nature and treatment")) == "health"
    assert ask._off_domain_shift("how do i keep bees", c("The anatomy of the honey bee")) == "science"
    assert ask._off_domain_shift("how do i raise chickens", c("The natural history of chickens")) == "reference"


def test_crisis_puts_real_help_first():
    r = ask.respond("sometimes I want to die", SEC)
    assert r["kind"] == "crisis"
    assert any("988" in x["label"] for x in r["resources"])


def test_ultimate_points_to_christ_and_people():
    r = ask.respond("what is the meaning of life", SEC)
    assert r["kind"] == "ultimate"
    assert any(v["ref"] == "John 14:6" for v in r["scripture"])
    assert r["real_help"] and "also_in_the_keeping" in r


def test_decision_is_more_specific_than_ultimate_and_opens_the_gate():
    """Someone ready to respond in faith right now gets the Romans Road, not the generic
    'ultimate matters' bucket — and it opens the Gate itself (this IS the knock, Mt 7:7-8)."""
    phrasings = ("I want to be saved", "how do I become a christian",
                 "I want to accept Jesus as my Lord and Savior",
                 "i want to give my life to christ", "sinners prayer",
                 "I want to ask Jesus into my heart")
    for p in phrasings:
        assert ask.classify(p) == "decision", p
        assert ask.gate_signal(p) is True, p
    # a generic ultimate question is NOT swallowed into "decision"
    assert ask.classify("what is the meaning of life") == "ultimate"


def test_decision_response_carries_the_romans_road_in_order_and_points_to_a_real_person():
    r = ask.respond("I want to be saved", SEC, gate_open=True, gate_just_opened=False)
    assert r["kind"] == "decision"
    refs = [v["ref"] for v in r["romans_road"]]
    assert refs == ["Romans 3:23", "Romans 6:23", "Romans 5:8", "Romans 10:9", "Romans 10:10",
                     "Romans 10:11", "Romans 10:13"]
    for v in r["romans_road"]:
        assert v["text"], f"{v['ref']} must carry real, verbatim text"
    assert r["real_help"] and any("pastor" in x.lower() or "church" in x.lower() for x in r["real_help"])
    # the tool presents Scripture and points away from itself — it never writes a prayer to say
    assert "amen" not in r["message"].lower() and "dear god" not in r["message"].lower()


def test_decision_is_never_shadowed_by_crisis_but_crisis_always_wins():
    """Safety is not negotiable: real danger outranks a decision-of-faith statement too."""
    assert ask.classify("I want to kill myself but I also want to be saved") == "crisis"
    r = ask.respond("I want to kill myself but I also want to be saved", SEC)
    assert r["kind"] == "crisis" and "romans_road" not in r


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


def test_is_crisis_never_crashes_on_a_truthy_non_string():
    # found: normalize()'s "text or ''" only substitutes the fallback for a FALSY text — a
    # truthy non-string (an int/list from an uncoerced caller) survived past that guard and
    # crashed on ".lower()". is_crisis() is the one safety-critical check every surface calls
    # ("a copied list is a list that drifts") — it must never crash instead of answering.
    for bad in (123, 45.6, ["a", "b"], {"x": 1}):
        assert ask.is_crisis(bad) is False
        assert isinstance(ask.normalize(bad), str)


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


# ── long-carried, past-tense ideation: the present-tense imperative never fired ──────────────
# "I have wanted to die for 3 years" routed to an ordinary keyword SEARCH (verified 2026-08-05):
# the substring "want to die" cannot match across the "-ed" in "wanted", and genuine, settled,
# long-carried ideation is phrased in exactly this past/perfect/progressive way. Crisis is the
# highest-cost miss in the system — a person this far in must reach real help, not a search box.
_DURATION_IDEATION = (
    "I have wanted to die for 3 years",    # the verified miss
    "i've wanted to die for years",
    "for a long time now i have wanted to die",
    "i have felt like ending it for a long time",
    "i feel like ending it",
    "i've been wanting to die",
    "i keep thinking about ending it all",
    "i have wanted to end it for years",
    "ive been thinking of ending my life",
)


def test_long_carried_past_tense_ideation_reaches_help():
    """Past / perfect / progressive ideation carried for years must reach crisis, not search.
    The present-tense list ('want to die', 'end it all') never matched across the '-ed'/'-ing'."""
    for text in _DURATION_IDEATION:
        assert ask.is_crisis(text), f"is_crisis missed: {text!r}"
        assert ask.classify(text) == "crisis", f"routed away from help: {text!r}"


def test_the_past_tense_additions_do_not_sweep_in_ordinary_study_questions():
    """The additions are CONJUGATIONS of phrases already treated as crisis, not new concepts, so
    everyday factual and study queries must still route away from crisis. (Bible narratives where
    a character longs to die — Jonah, Elijah — share the present-tense list's already-accepted
    cost and are deliberately out of scope; widening the net is not the same as closing a hole.)"""
    for text in ("what year did the Titanic sink",
                 "explain the parable of the sower",
                 "how far away is the moon",
                 "what does agape mean",
                 "when did the Babylonian exile end",       # 'end', not ideation
                 "how do I end a letter in Koine Greek",     # 'end', not ideation
                 "the ending of the book of Job"):           # 'ending', not ideation
        assert ask.classify(text) != "crisis", f"ordinary query swept into crisis: {text!r}"


# ── red team, 2026-08-06: 30 realistic phrasings, all missed ─────────────────────────────────
# An external red-team pass wrote how a person actually reaches for help; the matcher missed every
# one. These pin the closed holes: an attempt already in progress (the highest-cost miss — a person
# mid-act must reach real help, not a search box), the commonest idioms of ideation, a euphemism,
# and the Spanish of the es_en curriculum's own audience.
_RED_TEAM_MISSED = (
    "i took a whole bottle of pills tonight",     # attempt in progress
    "i swallowed a bunch of pills",
    "i slit my wrists",
    "im going to jump off a bridge",
    "i put a gun to my head",
    "i wish i was dead",                            # idiom
    "i cant take it anymore",
    "im such a burden to everyone",
    "i want it all to be over",
    "life isnt worth living",
    "nobody would miss me",
    "im going to unalive myself",                   # euphemism
    "sewerslide",
    "quiero morir",                                 # Spanish
    "ya no quiero vivir",
    "me quiero matar",
)


def test_the_red_team_phrasings_now_reach_help():
    """Every phrasing the adversarial pass found the matcher missing must now route to crisis."""
    for text in _RED_TEAM_MISSED:
        assert ask.is_crisis(text), f"is_crisis missed: {text!r}"
        assert ask.classify(text) == "crisis", f"routed away from help: {text!r}"


# ── answer-path benchmark, 2026-08-26: 25 realistic cries routed only 18/25 to help ──────────
# The stable graded set built to gate the answer path (eval/coherent_model/benchmark.py) doubled as
# an adversarial pass on the ONE crisis matcher. Seven softer idioms of ideation missed — not the
# blunt "kill myself" the list already caught, but the quieter way despair speaks: giving up on
# life, no hope left, the pain, ending "things", wanting it all to stop, life should be over. These
# are near-synonyms and conjugations of phrases already treated as crisis, so closing them adds no
# exclusion and keeps the asymmetry (an unnecessary helpline is a small cost; a missed person is not).
_BENCH_SOFTER_MISSED = (
    "i want it all to stop",
    "ive been thinking about ending things",
    "ready to give up on life",
    "i cant take the pain anymore and want out",
    "cutting myself feels like the only relief",
    "there is no hope left for me",
    "my life should be over",
    # a few natural conjugations of the same idioms, to prove the fix is the phrase, not the sentence
    "i think i want to give up on life",
    "honestly there is no hope left",
    "i just want the pain to stop",
    "i keep thinking of ending things",
)


def test_the_answer_path_benchmark_softer_idioms_now_reach_help():
    """The seven softer cries the 25-item benchmark found missing must now route to crisis."""
    for text in _BENCH_SOFTER_MISSED:
        assert ask.is_crisis(text), f"is_crisis missed: {text!r}"
        assert ask.classify(text) == "crisis", f"routed away from help: {text!r}"


def test_the_kms_kys_abbreviations_count_only_as_a_whole_message():
    """'kms'/'kys' (kill myself / kill yourself) are caught, but ONLY as the entire message — as
    bare substrings they collided with the engine's OWN unit-conversion domain and ordinary text.
    A crisis abbreviation typed alone means it; a distance never does. This guards the regression:
    adding them as substrings routed 'convert 5 kms to miles' and 'i ran 10 kms' to a helpline."""
    for alone in ("kms", "kys", "KMS", "  kys  "):
        assert ask.is_crisis(alone), f"bare abbreviation missed: {alone!r}"
    for ordinary in ("convert 5 kms to miles", "how many kms to the store",
                     "i ran 10 kms today", "a glass of whiskys", "how far in kms is it"):
        assert not ask.is_crisis(ordinary), f"unit/ordinary text swept into crisis: {ordinary!r}"


def test_coach_never_grades_or_labels_a_named_child():
    """SAFETY: a request to grade / rank / label the user's OWN child is refused with a caring
    redirect however it routes — including 'is my kid behind for his age', which carries no teaching
    keyword and so never reached the Coach branch (the guardrail there was, in fact, dead code).
    Scoped to a NAMED child: a book's reading level, a car diagnosis, or a grade-norm question is a
    legitimate use and must NOT get the child refusal (refuse abuse, not use)."""
    def _is_child_refusal(text: str) -> bool:
        r = ask.respond(text, SEC)
        return r.get("kind") == "coach" and "grade, rank, or label" in (r.get("message") or "")
    for text in ("is my kid behind for his age", "is my child slow",
                 "compare my child to other kids", "what grade level is my child reading at",
                 "grade my kid", "does my son have dyslexia", "how smart is my daughter"):
        assert _is_child_refusal(text), f"a child was not protected: {text!r}"
    for text in ("how do I diagnose a car problem", "what grade level is this book written at",
                 "what should a 2nd grader be reading", "teach me the next phonics lesson"):
        assert not _is_child_refusal(text), f"a legitimate use was wrongly refused: {text!r}"


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


def test_a_comparison_answer_carries_the_voices_in_full():
    """THE RESPONSE, not the module. compare.py was correct and covered while TWO live runs
    delivered empty voices, because the ask hook's response shaping briefed the voice back down —
    `_brief` keeps a 200-char snippet and drops `body`, so the message promised "the tradition's
    own voice, in its own reckoning" while the shaping threw the reckoning away. The module's own
    tests could never see it; only asserting on what ask.respond() actually returns can."""
    r = ask.respond("compare and contrast Baptist vs Anglican", SEC)
    assert r["kind"] == "comparison"
    assert r["missing"] == []
    for side in r["sides"]:
        v = side["voice"]
        assert v is not None, f"{side['subject']} lost its voice"
        assert v.get("body") and "Confession" in v["body"], \
            f"{side['subject']}'s voice arrived without its reckoning (body missing or briefed)"
    # membership is not doctrine: the shelf spine must never be reported as shared ground
    assert not any(str(g).startswith("card_spine_") for g in r["shared_ground"]), \
        "the bookcase was reported as common doctrine"


def test_a_crisis_never_receives_a_comparison_table():
    """The comparison hook sits AFTER the crisis path, and must stay there."""
    r = ask.respond("compare and contrast dying vs I want to kill myself", SEC)
    assert r["kind"] == "crisis", "a person in danger was handed a comparison"


def test_the_original_dud_query_finally_answers_about_its_subject():
    """Matt, 2026-08-01: "I asked for information on the Wesleyan Church. Just random cards...
    right now its a dud." Two fixes later it was STILL a dud on the live wire: the deck router
    scoped the search to shelves where "wesleyan" never occurs, the local partition fell back to
    "church", and the weakness guard accepted six confession cards about the church in general
    because they shared A distinctive word — the generic one. The subject now outranks every
    other distinctive word: a hit that does not carry "wesleyan" is weak, and weak sends the
    router back to the unscoped search where the partition holds."""
    r = ask.respond("Tell me about the Wesleyan Church", SEC)
    hits = r.get("results") or []
    assert hits, "the keeping holds a Wesleyan voice card; this must not come back empty"
    top_text = ((hits[0].get("title") or "") + " " + (hits[0].get("snippet") or "")
                + " " + (hits[0].get("body") or "")).lower()
    assert "wesley" in top_text, \
        f"the top hit is not about the subject asked: {hits[0].get('title')!r}"


def test_the_subject_guard_rejects_the_generic_word():
    """The guard itself, at the unit: a card sharing only the COMMON distinctive word is weak."""
    generic = {"title": "Belgic Art. 29: The Marks of the True Church",
               "body": "We believe that we ought diligently to discern the true church."}
    named = {"title": "Methodist / Wesleyan",
             "body": "Wesleyan confession: grace freely offered to all."}
    assert ask._shares_a_word("Tell me about the Wesleyan Church", named) is True
    assert ask._shares_a_word("Tell me about the Wesleyan Church", generic) is False, \
        "a hit on 'church' alone carried a question about the Wesleyans"


def test_baptists_finds_baptist_the_plural_is_not_an_empty_shelf():
    """"Now it says it doesn't have anything for southern baptists." There is no stemming, so the
    subject partition demanded the exact token "baptists" — which _idf reads as MAXIMALLY rare
    precisely because no card contains it (df=0) — and a library full of Baptist material
    reported an empty shelf. The present form now takes the subject seat, and only when the
    asked form is absent: expansion adds, never rewrites."""
    from concordance import corpus
    # The mechanism, deterministically: a fixture corpus that holds only the singular. The real
    # corpus happens to contain "baptists" too, so the live assertion below is necessary but not
    # sufficient — this one pins the df=0 fallback itself.
    fix = corpus.Corpus({
        "c1": {"id": "c1", "title": "Baptist", "body": "the baptist tradition confesses",
               "lifecycle_stage": "public"},
        "c2": {"id": "c2", "title": "Geography", "body": "the southern hemisphere",
               "lifecycle_stage": "public"},
    }, min_idf=0.0)
    assert fix._present_form("baptists") == "baptist", "the absent plural did not yield the seat"
    assert fix._present_form("baptist") == "baptist", "a present form must never be rewritten"
    assert fix._subject_of(fix._with_variants({"southern", "baptists"}),
                           fix._idf(fix._with_variants({"southern", "baptists"}))) in (
        "baptist", "southern"), "an absent token held the subject seat"
    assert corpus.subject_of("Tell me about the Southern Baptists") in ("baptist", "baptists")
    r = ask.respond("What do Southern Baptists believe", SEC)
    hits = r.get("results") or []
    assert hits, "a full library reported an empty shelf on a plural"
    top = ((hits[0].get("title") or "") + " " + (hits[0].get("snippet") or "")
           + " " + (hits[0].get("body") or "")).lower()
    assert "baptist" in top, f"top hit is not about the subject: {hits[0].get('title')!r}"


def test_a_true_miss_tries_the_pull_before_the_citation_fallback():
    """"It should find what I need, when I need it" — on EVERY door. The pull was wired into the
    comparison path only; a plain question about an absent subject fell through to citations.
    Spied here: the miss path must attempt pull_and_card, and when it cards, the answer is the
    cards — not a pointer to a book that exists."""
    from concordance import expand
    calls = []
    fake_cards = [{"id": "card_span_pulltest", "title": "Of the Zorblatt Confession",
                   "shelf": "sources", "body": "The zorblatt fellowship holds its confession...",
                   "source": {"authority_tier": "primary_pd"}}]
    def fake_pull(text, subj, config, plane="human"):
        calls.append(subj)
        return {"status": "carded", "cards": fake_cards,
                "message": "fetched and cut on the call — kept for next time"}
    orig = expand.pull_and_card
    expand.pull_and_card = fake_pull
    try:
        r = ask.respond("tell me about the zorblatt fellowship", SEC)
    finally:
        expand.pull_and_card = orig
    assert calls, "the miss path never attempted the pull"
    hits = r.get("results") or []
    assert any(h.get("id") == "card_span_pulltest" for h in hits), \
        "the pull carded an answer and the response did not carry it"
    assert "kept for next time" in (r.get("message") or "")


def test_the_candidate_pool_is_deterministic_and_never_starves_the_rare_word():
    """A HEISENBUG THAT SURVIVED EVERY GATE: candidates were gathered in set-iteration order,
    which is hash-seed dependent and re-rolls each restart. For "southern baptists" (df 2,702 vs
    160) whichever token iterated first flooded the 600-candidate cap — one restart returned 8
    Baptist histories, the next returned 1, same query, same corpus. A ranking that changes with
    a restart cannot be trusted or tested. Rarest tokens now seed first, deterministically."""
    from concordance import corpus
    cards = {}
    for i in range(700):                     # the common word floods far past the cap
        cards[f"c{i}"] = {"id": f"c{i}", "title": f"southern note {i}",
                          "body": "a southern matter", "lifecycle_stage": "public"}
    for i in range(3):                       # the rare word — the actual subject
        cards[f"b{i}"] = {"id": f"b{i}", "title": f"Baptists of town {i}",
                          "body": "the baptists gathered", "lifecycle_stage": "public"}
    fix = corpus.Corpus(cards, min_idf=0.0)
    cand = set(fix._candidates({"southern", "baptists"}))
    for i in range(3):
        assert f"b{i}" in cand, "the common word starved the subject out of the candidate pool"
    hits = fix.search("southern baptists", limit=8)
    got = {h["id"] for h in hits}
    assert {"b0", "b1", "b2"} <= got, "subject-holding cards missing from the results"


def test_the_singular_voice_answers_the_plural_question():
    """"methodists" must find the card that says "Methodist" — the partition demands the subject
    in EITHER number, at both partitions and in the guard."""
    from concordance import corpus
    fix = corpus.Corpus({
        "v": {"id": "v", "title": "Methodist / Wesleyan",
              "body": "the methodist tradition confesses", "lifecycle_stage": "public"},
        "x": {"id": "x", "title": "Geography", "body": "a southern town",
              "lifecycle_stage": "public"},
    }, min_idf=0.0)
    hits = fix.search("methodists", limit=4)
    assert hits and hits[0]["id"] == "v", "the singular voice was partitioned out of the plural"
    assert ask._shares_a_word("tell me about the methodists",
                              {"title": "Methodist / Wesleyan",
                               "body": "the methodist tradition"}) is True


def test_both_numbers_enter_at_the_tokens_not_just_the_verdict():
    """Measured live 2026-08-02: "methodists" has df>0, so no singular was added, common came up
    empty against the singular-only voice card, and the card died at the no-common gate BEFORE
    the family partition could fire. The family must enter at the tokens."""
    from concordance import corpus
    fix = corpus.Corpus({
        "v": {"id": "v", "title": "Methodist / Wesleyan", "body": "the methodist tradition",
              "lifecycle_stage": "public"},
        "p": {"id": "p", "title": "A history", "body": "founder of the methodists",
              "lifecycle_stage": "public"},
    }, min_idf=0.0)
    # both forms present in the index; the plural query must find the singular-only card too
    got = {h["id"] for h in fix.search("methodists", limit=4)}
    assert "v" in got, "the singular-only card died at the no-common gate"
    assert "p" in got


def test_a_mod_claim_verifies_through_the_front_door():
    """The reader's surface, not just the module: "16 mod 9 = 7" typed into ask must seal."""
    r = ask.respond("16 mod 9 = 7", SEC)
    assert (r.get("verify") or {}).get("verdict") == "HOLDS", r.get("verify")
    r2 = ask.respond("16 mod 9 = 3", SEC)
    assert (r2.get("verify") or {}).get("verdict") == "BROKEN"


def test_the_gauge_panel_locates_every_constant_on_the_measured_curve():
    """A constant is a promise about a distribution; when the distribution moves the promise
    rots unless something re-measures it. First measurement (2026-08-02) found min_idf=1.5
    admitting 100.0% of 300,463 live tokens — a floor believed load-bearing, doing nothing.
    The panel FLAGS and never auto-tunes: re-deriving a ranking constant changes what every
    reader sees and goes through the gate, not through a monitor."""
    from concordance import corpus
    g = corpus.gauges()
    assert set(g) >= {"zipf", "min_idf", "candidate_cap", "subject_tier", "population"}
    assert g["min_idf"]["verdict"] in ("VACUOUS", "MARGINAL", "BINDING")
    for panel in ("zipf", "min_idf", "candidate_cap", "subject_tier"):
        assert g[panel].get("means"), f"{panel} reports a number without its coverage"
    # on the real local corpus the floor is measurably vacuous — the finding that started this
    assert g["min_idf"]["admits_fraction"] > 0.99, \
        "if this ever fails, the floor became binding: re-run the probe battery before trusting it"
    fix = corpus.Corpus({
        "a": {"id": "a", "title": "one", "body": "rare word xylotomy", "lifecycle_stage": "public"},
        "b": {"id": "b", "title": "two", "body": "the the the", "lifecycle_stage": "public"},
    }, min_idf=0.0)
    # the panel must also read a tiny fixture without division blowups
    import concordance.corpus as _c
    old = _c.default_corpus
    _c.default_corpus = lambda: fix
    try:
        g2 = _c.gauges()
        assert g2["population"]["tokens"] > 0
    finally:
        _c.default_corpus = old


# ── The Candidate Engine, invisible under /ask (task #136, 2026-08-05) ───────────────────────

def test_a_prose_claim_is_narrowed_and_shown_as_checked():
    """A person writes prose carrying a checkable claim; the general path narrows it through the
    Candidate Engine and returns kind=='checked' with a per-claim audit block the desk renders —
    the honest answer, not a keyword dump. A true claim reads 'pass'."""
    r = ask.respond("15% of 80 is 12", SEC)
    assert r["kind"] == "checked", r.get("kind")
    results = r["audit"]["results"]
    assert results and any(x["status"] == "pass" for x in results)
    assert "checked" in r["message"].lower()


def test_a_false_prose_claim_is_shown_broken_not_hidden():
    """The rejected candidate is shown, never dropped — the answer includes what did not hold."""
    r = ask.respond("1900 was a leap year", SEC)
    assert r["kind"] == "checked"
    assert any(x["status"] == "reject" for x in r["audit"]["results"])


def test_the_checked_branch_never_touches_crisis():
    """The load-bearing safety proof: the narrowing branch lives in the general fallthrough,
    far below the crisis return at the top of respond(). Crisis stays byte-identical — same
    message, same resources, never a 'checked' block — even though a crisis line may contain
    numbers an extractor could otherwise read."""
    r = ask.respond("sometimes I want to die", SEC)
    assert r["kind"] == "crisis"
    assert "audit" not in r and r.get("message", "").startswith("You matter")
    assert any("988" in x["label"] for x in r["resources"])
    # a crisis line WITH a number still never reaches the checker
    r2 = ask.respond("I want to end my life, it has been 3 years", SEC)
    assert r2["kind"] == "crisis" and "audit" not in r2
