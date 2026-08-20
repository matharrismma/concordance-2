# Discern & Verify — the two-function core

Matt, 2026-08-20: *"What is necessary? This at its core should do two things. It should verify and
discern."*

The whole machine is two primitives. Everything else — the corpus, the mesh, the cards, the coach, the
lighthouse, the field packs — is delivery wrapped around them.

> **Discern proposes. Verify disposes.**
> Discern decides *what* is worth checking and *what it means*; the gate decides *whether it holds* and
> proves it.

```
proposal = discern(anything)          # what KIND · the necessary CLAIM · which MEMBER · the trail
verdict  = check(proposal.claim)      # the gate confirms — never discern
```

The engine's own tagline is these two: *"eliminates what is not the answer so the narrow path is
illuminated by what survives."* Elimination is **discern** (the narrowing); what survives, anchored to a
source and sealed, is **verify**.

## The asymmetry this map corrects

**Verify has a single door.** `check` / the moat (`derivation.verify`, the 71 verifiers, `receipts`):
a claim in, a sealed three-state verdict out. As an idea it is finished.

**Discernment was scattered** across seven places that never introduced themselves as one thing. The new
`discern` ([src/concordance/discern.py](../src/concordance/discern.py)) is its single door — a seed that
already unifies the front, with the rest folding in one kind at a time.

## Inventory — every act of discernment, and where it stands

| # | Discernment | What it decides | Lives in | In `discern`? |
|---|---|---|---|---|
| 1 | **Front door / kind** | cry for help vs a claim vs nothing | `ask.is_crisis` + `_CRISIS_RESOURCES` | **folded** — `kind`, crisis first |
| 2 | **Necessity** | reduce to only what could change the verdict; hold private/framing home | `context.decontextualize(minimal)` (the context loop) | **folded** — `claim` + `held` |
| 3 | **Route** | which member / verifier should check it | `router.route` | **folded** — `route` |
| 4 | **Claim extraction** | what in a text *is* a checkable claim, and its `(domain, spec)` | `audit.extract` | **to fold** — lives on the verify side today |
| 5 | **Relevance** | a real match vs a word-collision (retrieval) | `ask._practical_rank`, `_title_names_subject` | **to fold** — the retrieval branch |
| 6 | **Narrowing** | which candidate *survives* a wide field | `candidates.route` (fixed pre-registered policy, blind to `proposal_weight`) | **to fold** — the deepest form |
| 7 | **Authority** | quarantined < cited < verified | `kernel` (`AUTHORITY`, born-quarantined kinds) | **stays at the gate** (correct) |

Two of these are load-bearing findings:

- **#4 is a boundary blur.** `audit.extract` turns prose into structured `(domain, spec, claim)` steps —
  that is discernment (what *is* a claim), but it currently lives inside the verify path (`audit`). The
  clean factoring: **discern extracts and proposes; verify checks.** Folding `extract` into `discern`
  makes the door hand structured candidate claims to the gate instead of a bare skeleton string.
- **#6 is the archetype.** `candidates.route` already embodies *discern proposes, verify disposes*: a
  wide field is proposed, routed to verifiers under a **pre-registered policy that is blind to the
  generator's `proposal_weight`**, and the gate eliminates until a lone survivor passes. The candidate
  engine is what the whole two-primitive core looks like at full strength.
- **#7 belongs at the gate, and correctly does.** `discern` only ever tags `authority: "proposed"`;
  quarantined < cited < verified is *earned* at the gate, never granted at the door. The lattice staying
  in `kernel` is the right separation — discern must not upgrade authority.

## The seed, today

`discern(text)` orchestrates the three pure front pieces (no corpus, no model): `is_crisis` → the
context loop's necessity extraction → `router.route` (routed on the *discerned claim*, not the framing).
It returns a proposal — `{kind, claim, held, route, authority: "proposed", why, next}` — and **never a
verdict** (`confirms: False`). Crisis outranks everything; empty or a genuine routing tie asks rather
than guesses. Proven composing with the real gate: `discern("my mom said 2 + 2 = 4")` → claim
`"2 + 2 = 4"` routed to the *verify* member → `check` → **HOLDS**.

## Migration — fold the rest in, one kind at a time

Each step keeps the contract (proposes never confirms; crisis first; nothing generated; explains itself;
fails safe) and stays green:

1. **Extraction (#4)** — `discern` calls `audit.extract` to propose *structured* claims `(domain, spec)`
   rather than a skeleton string, so the gate receives exactly what it verifies. This is the biggest
   clarifier of the two-primitive boundary.
2. **Relevance (#5)** — when `route` lands on `search` (no checkable claim, a retrieval), `discern`
   applies the relevance floor to propose the genuinely-matching card, not a word-collision.
3. **Narrowing (#6)** — for a wide field, `discern` proposes the candidate set and the pre-registered
   routing; the gate narrows. The candidate engine becomes `discern`'s deep mode.

When these are folded, the engine is exactly two doors — `discern` and `check` — and every other module
hangs off one of them.
