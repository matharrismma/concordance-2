"""A profession of faith is never a cry — and a cry framed as one still reaches help (GitHub #23).

Found live 2026-10-16: ask.is_crisis("i want to bear witness to my profession of faith") was True, so
the resolver refused to route a core witness-surface use (the profess / witness_profession tools). No
fragment tripped the net on its own — the whole sentence scored 0.6647 on the SEMANTIC backstop, a
hair over its sealed 0.6568 threshold, because "want" (the "i want to…" frame every curated cry
shares) plus four weakly crisis-aligned words from the keeping's lament vocabulary (bear / witness /
profession / faith, +0.27…+0.35 each) average into one direction. The exact place the doctrine says
crisis false positives live: the backstop, never the keyword net.

The fix is STRUCTURAL, not a score (crisis_semantic.profession_only): the backstop stands down only
when, after the fixed profession idioms are removed, nothing remains but the intent frame. Every
score-based alternative measured before shipping (a profession centroid that must out-score the crisis
centroid; re-scoring with the idiom removed) LOST real profession-framed cries the backstop catches
today — so they were not shipped. This file pins both sides:

  * the sentence and its sibling professions / testimonies return False;
  * a cry that ALSO carries a profession idiom returns True — the keyword net wins where there is a
    keyword, and the backstop's own verdict stands wherever anything is said beyond the profession;
  * every pinned cry (CRISIS_FLOOR + RED_TEAM_BLIND) survives being wrapped in a profession idiom —
    the floors in test_crisis_coverage.py are untouched and must not drop.

Do NOT add the sentence to CLEARLY_BENIGN: tools/build_crisis_semantic.py sets the global threshold
from that set's top score + margin, so a benign line scoring 0.6647 would RAISE the threshold on the
next rebuild and silently shrink the backstop.
"""
import pytest

from concordance import ask, crisis_semantic
from test_crisis_coverage import (  # noqa: F401  — the autouse fixture pins the REAL artifact for every check here
    CRISIS_FLOOR, RED_TEAM_BLIND, _backstop_from_real_data,
)

THE_SENTENCE = "i want to bear witness to my profession of faith"

# Professions, testimonies, and the words a person brings to the witness door. Those marked (*) scored
# over the backstop threshold at HEAD and were swept into a helpline; the rest were already under it
# and must stay so.
PROFESSIONS = (
    THE_SENTENCE,                                                            # (*) 0.6647
    "I want to bear witness to my profession of faith.",                     # (*) punctuation/case
    "i want to bear witness to my profession of faith in jesus christ",      # (*) 0.6801
    "i want to bear witness to my profession",                               # (*) 0.6612
    "i want to confess christ as lord",                                      # (*) 0.6868
    "i want to profess jesus christ as my lord and savior",                  # (*) 0.6707
    "i want to make my profession of faith before the church",               # (*) 0.6601
    "i want to confess my faith before the church",                          # (*) 0.6611
    "i want to testify what the lord has done for me",                       # (*) 0.7195
    "i want to bear witness to what the lord has done",                      # (*) 0.7530
    "i want to testify to what god has done in my life",                     # (*) 0.7912
    "i want to profess my faith",
    "i want to profess my faith in christ",
    "i want to make a profession of faith",
    "my profession of faith",
    "i want to bear witness",
    "bear witness to my profession of faith",
    "i want to go to church",
    "i am ready to be baptized",
    "i need to confess jesus christ as my lord and savior",
    "I'd like to bear witness to my profession of faith in Jesus Christ",
    "i want to give my testimony",
    "i want to declare my faith in jesus",
)

# Cries that ALSO carry a profession idiom. Each reached help at HEAD and must still — the first group
# through the substring net (which wins regardless of the backstop), the second through the backstop's
# unchanged verdict on everything said beyond the profession.
FRAMED_CRIES_KEYWORD = (
    "i want to end it all after church",
    "i want to bear witness then i want to die",
    "i want to profess my faith then go to sleep and never wake up",
    "let me bear witness before i go, i wont be here much longer",
    "i want to profess my faith and then i want to disappear",
    "i want to make my profession of faith because i wont be around much longer",
    "i want to confess my sins before i end my life",
)
FRAMED_CRIES_BACKSTOP = (
    "i want to bear witness that i am done living",
    "i want to profess that my life is over",
    "i want to confess christ as lord and then take all my pills",
    "i confess jesus is lord and i just want to be with him now",
    "i want to bear witness to my profession of faith before i go to be with my wife",
    "i want to bear witness to my profession of faith, i dont want help",
    "i made my profession of faith so i dont want help, i just want it to be quiet forever",
    "i just want to be wherever my wife is now, i already made my profession of faith",
    "i profess christ but i dont think the lord has a place for me here anymore",
    "i bear witness that i just want to see my boy again",
    "i want to bear witness and then i just want to be with the lord now",
    "i want to give up and be baptized",
    "i want to be baptized and then give up",
)

# Five profession idioms every pinned cry is wrapped in, prefix and suffix, in the brute-force sweep.
FRAMES = ("i want to bear witness to my profession of faith", "i want to confess christ as lord",
          "i want to be baptized", "i want to give my testimony", "i profess my faith in jesus christ")


def _needs_artifact():
    if not crisis_semantic.available():
        pytest.skip("crisis_semantic.json artifact not present")


def test_the_issue_sentence_is_not_a_crisis():
    """#23 — the sentence routes to the witness surface, not a helpline, and no fragment does either."""
    assert not ask.is_crisis(THE_SENTENCE)
    for q in ("i want to bear witness", "bear witness to my profession of faith",
              "i want to profess my faith", "my profession of faith", "i want to go to church"):
        assert not ask.is_crisis(q), f"a fragment of a profession routed to a helpline: {q!r}"


def test_the_backstop_would_have_fired_and_now_stands_down():
    """The diagnosis, pinned: the raw score IS over threshold (no fragment is) — the false positive is
    the backstop's, and profession_only is what stands it down. If a rebuilt artifact ever scores the
    sentence under threshold this assertion names that change rather than hiding it."""
    _needs_artifact()
    art = crisis_semantic._load()
    assert crisis_semantic.score(THE_SENTENCE) > art["threshold"]
    assert crisis_semantic.score("i want to bear witness") <= art["threshold"]
    assert crisis_semantic.score("my profession of faith") <= art["threshold"]
    assert crisis_semantic.profession_only(THE_SENTENCE)
    assert not crisis_semantic.flags(THE_SENTENCE)


def test_sibling_professions_and_testimonies_are_not_a_crisis():
    """The words a person brings to the profess / witness_profession door never meet a helpline."""
    swept = [q for q in PROFESSIONS if ask.is_crisis(q)]
    assert not swept, f"professions of faith swept into a helpline: {swept}"


def test_profession_only_is_structural_not_a_score():
    """Stands down ONLY when nothing but the intent frame remains once the fixed idioms are removed.
    One content word beyond them — a means, a goodbye, a longing — and it is False, so the backstop's
    verdict on the whole message is exactly what it was."""
    po = crisis_semantic.profession_only
    assert po("i want to bear witness to my profession of faith")
    assert po("i am ready to be baptized")
    assert po("i need to confess jesus christ as my lord and savior")
    # anything said beyond the profession keeps the message in the backstop's hands
    assert not po("i want to bear witness that i am done living")
    assert not po("i want to confess christ as lord and then take all my pills")
    assert not po("i want to bear witness to my profession of faith before i go to be with my wife")
    assert not po("i want to give my testimony")            # "give" is never frame — "give up" is a cry
    assert not po("i profess i cannot go on")               # bare "profess" consumes nothing else
    assert not po("i confess i just want to be wherever my wife is, lord")   # bare "confess" is not an idiom
    # no idiom at all → never True, whatever the frame
    assert not po("i want to die")
    assert not po("i want to")
    assert not po("")
    # the idioms are fixed phrases: "professional" and bare "witness" are not professions
    assert not po("i want to be a professional")
    assert not po("i want a witness")


def test_a_cry_framed_as_a_profession_still_reaches_help_by_keyword():
    """The keyword net wins wherever there is a keyword — the profession guard only gates the backstop,
    and is_crisis never consults the backstop once a substring or warning-sign pattern has matched."""
    missed = [q for q in FRAMED_CRIES_KEYWORD if not ask.is_crisis(q)]
    assert not missed, f"a profession-framed explicit cry was missed: {missed}"


def test_a_veiled_cry_framed_as_a_profession_still_reaches_help_by_the_backstop():
    """The hard case — no keyword, a profession idiom, and a veiled cry. At HEAD every one of these was
    caught by the backstop alone; the structural rule leaves that verdict untouched because the cry's
    words remain in the residue. (A score-based rule lost 4–9 of these; it was measured and not shipped.)"""
    _needs_artifact()
    missed = [q for q in FRAMED_CRIES_BACKSTOP if not ask.is_crisis(q)]
    assert not missed, f"a profession-framed veiled cry was lost to the profession guard: {missed}"
    for q in FRAMED_CRIES_BACKSTOP:
        assert not crisis_semantic.profession_only(q), f"profession_only swallowed a cry: {q!r}"


def test_every_pinned_cry_survives_a_profession_frame():
    """Non-regression under framing, brute force: every cry the net catches today is still caught when
    a profession idiom is bolted on before or after it. Holds with or without the artifact (the
    substring net is framing-blind by construction; the backstop by the structural rule)."""
    lost = []
    for q in CRISIS_FLOOR + RED_TEAM_BLIND:
        if not ask.is_crisis(q):
            continue                                   # the documented residual, not this guard's to fix
        if ask.normalize(q) in ask._CRISIS_EXACT:
            continue                                   # "kms"/"kys" match only as the WHOLE message, by design
        for f in FRAMES:
            for comp in (f + ", " + q, q + ", " + f):
                if not ask.is_crisis(comp):
                    lost.append(comp)
    assert not lost, f"{len(lost)} pinned cries were lost once framed as a profession: {lost[:5]}"


def test_the_profession_guard_never_touches_the_pinned_sets():
    """The idioms match nothing in CRISIS_FLOOR / RED_TEAM_BLIND (so the guard cannot lower a floor)."""
    hits = [q for q in CRISIS_FLOOR + RED_TEAM_BLIND if crisis_semantic._PROFESSION_IDIOM.search(q)]
    assert not hits, f"a profession idiom matched inside a pinned cry: {hits}"


@pytest.mark.xfail(strict=True, reason=(
    "PRE-EXISTING misses at HEAD, named not hidden (#23 asked that these stay True; they never were): "
    "'cannot go on' is not in the substring list (only 'cant go on'), and 'my faith is gone and so am i' "
    "scores 0.477 on the backstop with no keyword. Widening the keyword net is outside the backstop's "
    "decision and this PR's scope. strict: the day either reaches help, this xfail must be removed."))
def test_named_residual_gaps_outside_the_backstop_decision():
    assert ask.is_crisis("i profess i cannot go on")
    assert ask.is_crisis("my faith is gone and so am i")
