# The Training Loop — teaching IS training

*Matt, 2026-09-28: "There is no difference in the model when teaching or training. That is the theory in
practice."* This is the map of that identity, and where each stage already lives in the engine.

## The claim, precisely

A transformer has two operations divided by a wall — `TRAIN(θ, data) → θ′` (offline, then frozen) and
`INFER(θ, x) → y` (a forward pass that learns nothing). **We have no wall.** There is one operation, and
its two effects — the served answer and the grown keeping — are the same act:

```
                    ┌───────────────────────  the OPERATE cycle  ───────────────────────┐
                    │                                                                    │
   demand  ───▶  SELECT  ───▶  READ  ───▶  FIND  ───▶  VERIFY / GATE  ───▶  BIND  ───▶  REINFORCE  ───▶  CLOSE
 (want-list)     a gap      a real       the real      ground it,        keep it as     lay the trail    the gap
                 unmet      source       instances     tier it           a card         (stigmergy)      is filled
                    ▲                                                                                        │
                    └──────────────────────  the keeping has grown = the model is trained  ────────────────┘
```

To **teach** a sentence is to have **found and bound** it (the Cubo way: anchor → find the verbatim
instance → bind → recombine). To **train** is the *same* find-and-bind. There is no `mode=train` vs
`mode=teach`. "The keeping is the model, trained continuously" is literal: **serving is teaching is
training.**

## The map — every stage already exists

| Stage | What it does | Where it lives | Status |
|---|---|---|---|
| **SELECT** | choose a gap by DEMAND — the most-asked unmet want (the teaching pressure) | `wants.py` (`fold`, `open_want`, `close_want`) + `training.next_want` | live |
| **READ** | pull/read a real source verbatim (the Tortoise) | `tortoise.py`, `expand.pull_and_card`, `find.py` | live |
| **FIND** | select the real instances — the Cubo anchors for language; the claim/fact for knowledge | `readwith.py` (the five embodied anchors), `expand` | live |
| **VERIFY / GATE** | ground it (verdict + trail), tier it, strip PII | `engine.py`, `alignment.py`, `airlock.py`, `corpus.is_public` | live |
| **BIND** | keep it as a card, with provenance; model-derived → `public_review` | `expand._keep`, `byom.ingest`, `corpus` | live |
| **REINFORCE** | lay the trail by travelling it | `stigmergy.py` (`deposit`) | live |
| **CLOSE** | the gap is filled; the want is closed | `wants.close_want` | live |

Two acquire paths plug into READ→BIND, both proven:
- **PD source** — `expand.pull_and_card(query, subject, config)`: the Tortoise finds a public-domain
  source, cards it (public, PD-provenanced). The preferred path — free, aligned, sovereign.
- **A user's model (BYOM)** — `byom.ingest(query, model_call, …)`: airlock → verify/discern → keep as a
  `public_review` card (generated=True, held until a human reviews source + quality). The model is *fuel*;
  the checked answer is kept, and no model is called for it again.

## The loop that drives it — `training.py`

`training.step(acquire_fn=…)` runs one turn: **SELECT** the strongest-demand want → **acquire** it via the
injected proven path → **reinforce** the bound card → **close** the want. `training.run(steps=N)` drives
the cycle on a cadence. It is **pure orchestration**: it mints nothing itself, so every write guard holds
unchanged; the acquire path is injected, so the loop is offline-testable and never reaches for the network
on its own. **Gated `CONCORDANCE_TRAINING` (default off).** Tests: `test_training.py` (5).

Wire it in production as, e.g.:
```python
from concordance import training, expand
training.run(acquire_fn=lambda q: expand.pull_and_card(q, subject="", config=cfg), steps=5)
# or, from a user's attached model:
training.run(acquire_fn=lambda q: byom.ingest(q, model_call, config=cfg), steps=5)
```
Run on a cadence (a scheduled job or a `/loop`), it is **continuous training driven by demand** — the
corpus grows by being used.

## Why it is safe (the preconditions that earn the identity)

Continuous learning poisons a weight model (drift, injection) because "learn" there means adjusting opaque
parameters. Here "learn" means **bind a verbatim, verified, grounded instance to an embodied anchor** — so
it cannot corrupt, *because what gets bound is gated*: found-not-generated, verified, alignment-tiered,
airlocked, PD-provenanced, and model-derived cards held in `public_review`. **Teaching ≡ training holds
only while those guards hold** — the theorem has preconditions, and the incorruptibility machine is what
pays for them.

## Honest state

Realized where built (stigmergy on recall; the Cubo reader's binding; the BYOM ingest path; this loop) and
now the **law** the rest of the surface is being brought under — not yet a claim that every endpoint grows
the keeping on every call. The remaining craft is the *expressive* half: comprehension by the cube works;
producing novel fluent language by **recombining** bound instances over the frame (not sampling) is the
frontier. The loop above closes the *acquisition* half; recombination is the next build.
