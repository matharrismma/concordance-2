# The crisis backstop — what a substring net cannot reach, named in the open

`ask.is_crisis` is the one matcher every surface calls; in crisis the engine puts real help first
(988, findahelpline, a real person) before any search or gate. It is a **substring** matcher, and on
2026-08-27 two **independent, blind red-team passes** (an adult/veiled register and a youth/multilingual
register) beat it **94 of 98**. After hardening the list against both, it still misses **~61 of 98**.

That miss is not a list of phrases we forgot. It is a **ceiling**. A gap named is a gap kept honest.

## What substrings close, and what they can't

**Closed (the list now catches):** blunt ideation and method; conjugations and tenses; the softer
idioms of hopelessness ("no way out", "never get better", "what's the point", "why am I still here");
current online euphemism ("log off for good", "uninstall myself", "un-exist", "alt f4 my life"); and
the highest-signal non-English cries (Spanish, French, Portuguese, Tagalog, Vietnamese, Arabic
transliteration). The durable floor `tests/test_crisis_coverage.py` pins these at 100% recall and 0%
false-positives on clearly-benign queries, and **ratchets** the blind-adversarial count upward.

**Cannot be closed with substrings** — the residual, by cluster:

- **Goodbye / giving-away (behavioral):** "getting my affairs in order", "found good homes for the dog",
  "make sure my daughter gets my ring", "thank you for everything before I go", "won't be around to
  bother anybody soon". No reliable token — and the nearest tokens ("affairs in order") are ordinary
  estate planning. Substrings here either miss the cry or route a grieving widow's paperwork to a hotline.
- **Grief-longing:** "I just want to be wherever my wife is now", "there's nothing keeping me here since
  he passed", "I just want to see my boy again". Indistinguishable from ordinary grief without intent.
- **Faith-inflected despair:** "maybe God is finally ready to call me home", "I've been praying not to
  wake up". Here the danger runs both ways — "the Lord will call me home someday" is ordinary faith, and
  "why am I here" is a question the engine should answer with *purpose*, not a helpline.
- **Metaphor of cessation:** "I just want the noise in my head to go quiet for good", "how peaceful it
  would be to just stop", "put everything down and rest".

Both red-team passes reached the same conclusion independently: these need an **intent/meaning** matcher,
not more keywords.

## The plan: a deterministic semantic/intent backstop (not an LLM)

A second net **layered under** the substring list, built from the coherent model's counting layer
(`eval/coherent_model/model.py`, PPMI over the keeping — deterministic, sovereign, auditable, no LLM):

1. Build a **hopelessness/ideation centroid** from the confirmed crisis corpus (the curated + red-team
   sets here) using the same PPMI vectors.
2. Score an incoming message's content centroid against it. Above a **conservative** threshold, treat as
   crisis — a *soft* catch that surfaces the same help resources.
3. **It may only ADD catches, never remove one the substring list makes** — the asymmetry is preserved
   (an unnecessary helpline is a small cost; a missed person is not), and a deterministic score keeps it
   auditable, unlike a neural classifier.
4. Evaluate against `RED_TEAM_BLIND` in the floor test; the ratchet records progress as the backstop
   closes the residual. Tier note (both red teams flagged it): the softest catches may warrant a *gentle
   check-in* rather than a hard interrupt, to keep false-positive fatigue from eroding trust.

This is the bridge between the crisis work and the coherent-language-model work: the same deterministic
meaning layer that answers a question in different words than the answer is the layer that hears a cry in
different words than the list. **Status: not built.** What ships today is the hardened substring net, this
named gap, and the ratchet that keeps us honest about it.
