"""The form gate — question until the blanks are filled, THEN run. Never answer before hearing.

Proves the doctrine of clarify.py: a complete request runs; an incomplete one asks ONE question in
the person's frame; a term the keeping can't place is itself a blank (we ask, we do not guess); the
coach's prefill fills blanks so a known person answers fewer; and only load-bearing blanks are asked
(an optional slot left empty never stops the form). Pure — no corpus, no I/O.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import clarify  # noqa: E402


def test_a_complete_lookup_runs_and_names_its_verifier():
    r = clarify.run(clarify.LOOKUP, "find the boiling point of water at altitude")
    assert r["complete"] is True
    assert r["verifier"] == "search" and r["keep"] == "trail"
    assert "boiling point of water at altitude" in r["filled"]["subject"]


def test_an_empty_blank_asks_one_question_and_does_not_run():
    # a look-up with no topic at all -> the subject blank is asked, nothing runs
    r = clarify.run(clarify.LOOKUP, "look up")
    assert r["complete"] is False and r["slot"] == "subject" and r["why"] == "missing"
    assert r["ask"] == "What would you like me to find?"


def test_verify_extracts_the_claim_and_thin_input_is_asked():
    r = clarify.run(clarify.VERIFY, "is it true that the Jordan river flows south")
    assert r["complete"] is True and r["verifier"] == "check"
    assert r["filled"]["claim"] == "the Jordan river flows south"
    # too thin to be a testable claim -> ask, never guess a verdict on a bare word
    q = clarify.run(clarify.VERIFY, "verify gravity")
    assert q["complete"] is False and q["slot"] == "claim"


def test_learn_reads_the_subject_and_binds_the_coach():
    r = clarify.run(clarify.LEARN, "teach me about hydroponics")
    assert r["complete"] is True and r["verifier"] == "coach"
    assert r["filled"]["subject"] == "hydroponics"


def test_domain_is_optional_prefill_and_never_over_asks():
    # no domain cue -> the optional domain slot is simply skipped; the form still completes
    r = clarify.run(clarify.LOOKUP, "find a good knot for a ridgeline")
    assert r["complete"] is True and "domain" not in r["filled"]
    # a scripture cue -> domain is prefilled by the classifier, still without a question
    r2 = clarify.run(clarify.LOOKUP, "what does the bible say about rest")
    assert r2["complete"] is True and r2["filled"]["domain"] == "scripture"


def test_the_coachs_prefill_answers_a_blank_so_a_known_person_is_not_asked():
    # the relationship is the autofill: subject supplied from what we already know -> no question,
    # even though the request text alone would not carry it
    r = clarify.run(clarify.LEARN, "the next step please", known={"subject": "beekeeping"})
    assert r["complete"] is True and r["filled"]["subject"] == "beekeeping"


def test_a_term_the_keeping_cannot_place_is_a_blank_we_ask_about():
    # "we don't understand it" is itself a blank — the honest move is to ask, not to guess. The pure
    # gate cannot know the keeping, so the caller injects a resolver; when it says no, we ask.
    def resolver(slot, value):
        return "florgle" not in value.lower()

    r = clarify.run(clarify.LOOKUP, "look up the florgle manifold", resolver=resolver)
    assert r["complete"] is False and r["slot"] == "subject" and r["why"] == "unresolved"
    # a subject the keeping CAN place passes the same resolver and runs
    ok = clarify.run(clarify.LOOKUP, "look up water purification", resolver=resolver)
    assert ok["complete"] is True


def test_an_ambiguous_value_outside_a_closed_set_is_asked():
    # a domain handed in out-of-set (e.g. a bad prefill) is ambiguous -> asked, not silently accepted
    r = clarify.run(clarify.LOOKUP, "find the water table depth", known={"domain": "astrology"})
    assert r["complete"] is False and r["slot"] == "domain" and r["why"] == "ambiguous"


def test_route_ask_sorts_verify_learn_and_lookup():
    assert clarify.route_ask("is it true that manna fell for forty years") == "verify"
    assert clarify.route_ask("teach me how a diode works") == "learn"
    assert clarify.route_ask("who was Polycarp") == "look-up"
    # the convenience wrapper routes AND runs in one call
    r = clarify.clarify_ask("explain photosynthesis")
    assert r["form"] == "learn" and r["complete"] is True


def test_envelope_incomplete_gate_speaks_the_question_and_offers_no_tortoise():
    # nothing is sourced until we have heard — the hare IS the question, free, no tortoise yet
    gate = clarify.run(clarify.LOOKUP, "look up")
    env = clarify.envelope(gate)
    assert env["hare"]["kind"] == "question"
    assert env["hare"]["spoken"] == "What would you like me to find?"
    assert env["hare"]["cost"] == "free" and env["tortoise"] is None


def test_envelope_keeping_hit_is_the_free_hare_with_the_tortoise_only_offered():
    gate = clarify.run(clarify.LOOKUP, "find water purification")
    def keeping(_g):
        return {"found": True, "spoken": "Boil one minute at a rolling boil.",
                "source": {"ref": "/card/card_water"}}
    env = clarify.envelope(gate, keeping)
    assert env["hare"]["kind"] == "answer" and "Boil one minute" in env["hare"]["spoken"]
    assert env["hare"]["cost"] == "free"                       # the keeping answer costs the family nothing
    assert env["hare"]["source"]["ref"] == "/card/card_water"
    # the tortoise is OFFERED, never fired here; it is the cheap, chosen trip to the full source
    assert env["tortoise"]["offered"] is True and env["tortoise"]["cost"] == "cheap"


def test_envelope_miss_is_an_honest_free_hare_and_never_auto_fetches():
    gate = clarify.run(clarify.LOOKUP, "find the maintenance interval for a Lister CS")
    def keeping(_g):
        return {"found": False}                               # the keeping does not hold it
    env = clarify.envelope(gate, keeping)
    assert env["hare"]["kind"] == "miss" and env["hare"]["cost"] == "free"
    assert env["tortoise"]["offered"] is True                 # offered, but NOT run — no want opened here
    # nothing the user hears promises a clock (the no-automatic-ETA correction)
    heard = (env["hare"]["spoken"] + " " + env["tortoise"]["spoken"]).lower()
    assert "24" not in heard and "48" not in heard and "hour" not in heard
    assert not any(ch.isdigit() for ch in heard)


def test_send_tortoise_goes_to_the_source_and_produces_for_the_keeping():
    # the user chose the tortoise: it fetches a good source AND produces for the keeping (the loop),
    # so next time the hare serves it free
    gate = clarify.run(clarify.LOOKUP, "find the Lister CS oil change interval")
    produced = {}
    def fetch(_g):
        return {"found": True, "source": {"url": "https://example.org/lister-cs-manual"},
                "spoken": "Every 250 hours, per the manual."}
    def produce(r):
        produced["card"] = r["source"]["url"]                 # enters the keeping through the gate
        return "cand_lister"
    r = clarify.send_tortoise(gate, fetch=fetch, produce=produce, online=True)
    assert r["status"] == "ready" and r["produced"] == "cand_lister"
    assert produced["card"].endswith("lister-cs-manual")      # the source was produced FOR the keeping


def test_send_tortoise_with_no_access_queues_the_errand_not_a_promise():
    gate = clarify.run(clarify.LOOKUP, "find the Lister CS oil change interval")
    seen = {}
    def open_want(g):
        seen["want"] = g["filled"]["subject"]
        return "want_7"
    r = clarify.send_tortoise(gate, fetch=lambda g: {"found": True}, open_want=open_want, online=False)
    assert r["status"] == "queued" and r["want_id"] == "want_7"
    assert seen["want"]                                        # remembered for when a connection returns
    assert not any(ch.isdigit() for ch in r["spoken"].lower())  # still no clock


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed — the gate asks until the blanks are filled, then runs.")
