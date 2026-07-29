# THE RECORD — one mechanism, designed from what it must do

Matt, 2026-07-29: *"Look at all of the record keeping mechanisms we have built. Should be one
that can be used. What is the best method for this. Don't look at past. Look at what should be."*

So this is not a migration plan. It is the design a record-keeping system for this library would
have if it were built once, correctly, knowing what it must do.

---

## What a record must do

1. **Be findable** — it has an address, not a location someone has to remember.
2. **Be verifiable** — it carries its own proof, or names plainly what could not be proved.
3. **Be attributable** — who claimed it, when, and on what basis. The waybill travels.
4. **Be tamper-evident** — history extends; it never rewrites. A correction is a new record
   that supersedes, never an edit that erases.
5. **Be one shape** — a reader learns one grammar and can then read *everything*, including
   things written after they learned it.
6. **Be self-describing** — the system's own operations are records of the same kind as its
   content. No privileged metadata tier that plays by different rules.

A seventh, which this project cares about more than most: **survive us.** A record must be
readable with no running code — plain bytes a person can open in fifty years.

## The one insight

**There is no difference in kind between the library's content and the library's own history.**

A verse, a herb monograph, a deploy, a measured gap, a lesson learned, a decision taken — each
is *a claim, with provenance, at an address*. We split them into cards-and-documents only
because prose files were easy to write, and the cost showed up immediately: two copies of
DEPLOY.md drifted, a backup log said "green" while the library was unprotected, and a plan
described systems the code did not have.

Dewey did not keep his cataloguing decisions in a different medium. Those were cards too.

## The method: ONE record, ONE chain, MANY views

### 1 · One record — the card

```
  id · address · kind · subject · body
  waybill    (source, author, when, licence)
  verification (CONFIRMED | WITNESSED | UNCHECKED | COULD-NOT-CHECK | BROKEN | MIXED)
  connections  (typed, directional, each with its evidence)
  content_hash
```

Nothing else is a record type. A gap is a card. A deploy is a card. An SOP is a card. A lesson
is a card. The verification field is what makes this honest rather than merely uniform: a deploy
card that says CONFIRMED carries its gate number and its live check; one that says
COULD-NOT-CHECK says so in the same field a physics claim would.

### 2 · One chain — append-only, superseding

Every card's hash appends to a single chain. That is not a second mechanism sitting beside the
cards; it is **the spine of the one mechanism** — what makes the collection a *record* instead of
a pile.

- **Nothing is edited.** A wrong card is answered by a new card with a `supersedes` edge. Both
  remain. The reader always sees the current answer and can always walk back to what we used to
  believe and *when we stopped believing it*.
- **Retraction is a record too.** A `retracts` card with its reason. Deleting would destroy the
  most valuable thing we own: the trail of our own corrections. (Tonight alone: seven instruments
  that lied before their subjects did. That history is an asset, not an embarrassment.)

### 3 · Many views — rendered, never hand-kept

Every document a human reads is a **query rendered as prose**:

| view | the query behind it |
|---|---|
| `GAPS.md` | `OPS.gaps.*` where state ≠ closed, ordered by harm |
| `OPERATIONS_LOG.md` | `OPS.events.*` newest first |
| `MASTER_PLAN.md` §1 | `OPS.systems.*` where shipped |
| `SOP/*.md` | `OPS.sop.*` |
| `THE_RECORD.md` | this card and its children |

**Nobody edits a view.** You write a card; the view changes. This is where drift dies: there is
one truth and N renderings, instead of N truths pretending to agree. And it inverts the failure
we keep hitting — a view cannot claim a system the cards do not describe, because the view is
*made of* the cards.

## What legitimately does NOT fold in — and why

Not "because legacy." Because they are different objects:

- **Git** records the *code*, whose identity is a tree of text rather than a claim with
  provenance. Different thing; keep it, and let a deploy card cite the commit.
- **The frozen contract.** A constitution's worth comes precisely from *not* being regenerable.
  Freezing is the feature. It cites cards; it is not one.
- **The agent's memory.** That is the librarian's notebook, not the library's record — it holds
  what to *do* next time, not what is *true*. Different purpose, different lifetime.

Everything else — 26 prose documents, the activity log, the tasks, the reports, the seals —
becomes cards, or a view of them.

## Why this is the best method and not merely a tidy one

- **Recall works the same everywhere.** The address that finds Gill on John 3:16 finds the
  deploy that put him there: `OPS.deploys.OBJ/2026-07-29-topical/REF.CONFIRMED@engine`.
- **Verification is uniform.** "Was it checked?" is answerable about our operations with exactly
  the machinery that answers it about optics. Today it is not — a document can assert anything.
- **The library can audit itself.** Query for `OPS.*` with verification ≠ CONFIRMED and you have
  the honest state of the house, generated rather than remembered.
- **It survives.** Cards are JSON lines; the chain is a file of hashes. No server, no schema
  registry, no code. A person with a text editor in 2076 can read all of it and check the chain
  by hand if they must.
- **It scales to the Commons without a second design.** A member's shelf card, a lend, an
  elevation, a payment receipt — same record, same chain, same views. The doctrine we wrote for
  people is already the doctrine for our own operations.

## The honest cost, stated up front

- Prose is *easier* than a card. Writing a paragraph into a file takes seconds; minting a card
  with a waybill and a verification state takes thought. That friction is the point — it is the
  same friction that stops us claiming CONFIRMED when we mean WITNESSED — but it is real, and a
  bad renderer would make it feel like bureaucracy instead of rigor.
- **Views must be beautiful or they will be bypassed.** If `GAPS.md` renders worse than the
  hand-written one, someone will start hand-writing again and the drift returns. The renderer is
  not an afterthought; it is the load-bearing part of adoption.
- This is a real build: a card schema extension, a chain writer, a view renderer, and the
  migration of 26 documents. It should be **one arc, gated like any other** — and until it
  ships, the current documents remain the record, because a half-migrated record is worse than
  either state.

---

*One record. One chain. Many views. The library's history kept the way the library keeps
everything else — because a system that cannot record its own life in its own terms does not yet
believe its own method.*
