# THE GAPS — measured 2026-07-29, not guessed

Matt: "Identify the gaps." Grounded gap analysis is the steering instrument: **query the live
state, then name what is missing.** Every number below came from a command run against the
live corpus, the deployed box, or the last gate — none of it is estimated.

Ordered by what would hurt a real person first.

---

## G1 · HALF THE KEEPING IS A POINTER, NOT CONTENT
**228,697 of 496,559 cards (46.1%) have bodies under 120 characters.**

These are stubs — a title, a link, a category. Legitimate by design for Gutenberg volumes and
encyclopedia entries (stub+link, the lazy Hare), but at 46% it means **the 1M goal can be hit
without adding a sentence of substance**. That would be a count, not a library.

*The line to hold:* the million must be measured in **substance cards**, with stub-to-body
ratio reported alongside it. A card whose body is a pointer is inventory; a card that answers
something is stock.

**Fix:** publish both numbers in `capabilities` and the ops log, every time the count is
claimed. Deepening (ISBE-style full text, Gutenberg chapters) counts; stub minting does not.

## G2 · THE SCIENCES ARE VERIFIED BUT NOT STOCKED
**33 shelves hold exactly ONE card** — architecture, atomic, biology, chess, cybersecurity,
electrical, formal_logic, genetics, geology, geometry, information_theory, law, linear_algebra,
manufacturing, meteorology, molecular_geometry, music_theory, operations_research, optics,
periodic_table, philosophy, photography, and more. **58 of 88 shelves hold fewer than 60.**

We can *check* claims in ~64 domains and we *hold* almost nothing in most of them. A reader
who asks about optics gets a verifier they must feed, not a shelf they can browse.

**Fix:** seed each verifier domain with its own reference core (constants, laws, worked
examples as Works cards). This is the fastest honest path toward the million *and* it closes
G1 at the same time, because those are substance cards.

## G3 · THE FLAGSHIP WINGS DO NOT EXIST YET
Measured: **music 0 cards · art 0 · woodworking 0 · gardening 0 · radio 0 · recipes 11.**

The Commons was designed today around recipes + music + art as the widest doors. Right now the
doors have no rooms behind them. Everything about hobby wings, "I made this" seals, and
community-by-shelf-overlap is **doctrine with zero cards and zero code**.

**Fix:** wings ship *with* their seed cards (PD sheet music, method books, chord charts,
color theory, PD cookery) — never a wing announced before it is stocked.

## G4 · REACHABILITY — CORRECTED, THEN GATED  ✅ closed 2026-07-29
**My first measurement was wrong, and the correction is the finding.** It read only `*.html`,
so it reported 51 unreachable routes and 8 orphan pages. But most routes are called from
scripts, and `site/nh-tools.js` — the Everything palette (Ctrl-K) — *is* a reachability
surface listing 39 pages, with its deliberate exclusions already documented in a comment.

**The true numbers:** of 8 "orphan" pages, `keep.html` (operator surface, noindex),
`encyclopedia.html` (redirect stub onto characters.html) and `ask.html` (kept for old links)
were documented decisions. **Exactly one page was genuinely lost: `mesh.html`** — the
Fellowship Mesh, a V1 capstone, reachable only by typing the URL. It is now in the palette
("The Way"). Routes: the remainder are agent/machine surfaces (identity, consent, attest,
thread internals), now declared as such, by name, with a reason.

`tests/test_reachability.py` gates all three from here: every route is REACHED or DECLARED
agent-only; every page is LINKED (href or palette) or DECLARED unlisted; and a declaration
naming a route that no longer exists fails too, so exemptions cannot rot.

*The lesson, twice in one day (see also the null assay's first draft): an instrument that
measures the wrong surface manufactures findings. Check the check before you trust it.*

## G5 · THE VERIFIERS THEMSELVES ARE THE LEAST-TESTED CODE
From the last gate's coverage: **foundation 0% · witness verifier 13% · teachings 14% ·
codex 15% · geometry 15% · operations_research 15% · optics 15% · soil_science 15% ·
atomic 16% · statistics 16% · chemistry 18% · thermodynamics 18% · biology 19% ·
linear_algebra 19% · linguistics 19% · almanac 20% · probability 20%** … a long tail at 15–25%.

The trust kernel is ≥90 (raised tonight). The *domain* verifiers — the thing the product
claims — are largely unexercised individually.

**And a claim of ours needs correcting:** `tools/benchmark.py` is **60 claims across three
derivation modes** (equality 30, inequality 14, derivative 16) — it is the *derivation moat*,
not a 60-domain sweep. `site/guarantees.html` says this correctly ("60 checks… alongside it,
64 verification domains"). **`docs/MASTER_PLAN.md` §1 juxtaposes "~60 domains" with "60/60"
and implies the benchmark covers the domains. That wording is mine, from tonight, and it
over-claims.** Corrected below.

**Fix:** per-domain golden cases (a true claim and a false claim per verifier, false must not
seal), raising both coverage and the honesty of the 0-FP statement.

## G6 · SIX GAPS ALREADY LOGGED, STILL OPEN
Carried from the ops log so this document is the single sheet:
- **§5 private-key-on-the-wire: 5 endpoints still accept `private_key` inbound.** The contract
  item is NOT done; only mesh messages were converted to detached signatures.
- **No src-side deploy manifest** — `corpus_db.py` sat missing from the droplet for days under
  a green gate; nothing yet proves the box matches the repo.
- **Operational carding not started** (#104): shards, nodes, curators, deploys, SOPs have no
  cards, so the system cannot describe itself from its own keeping.
- **Overall coverage 52%.**
- OneDrive drag on the working copy; nav single-source; manifest counts.

## G7 · DOCTRINE FAR AHEAD OF CODE
Written today, built zero: the Commons (shelves, drops, curation gate, elevation ladder,
receipts→payments, live teaching), the distributed airlock, node roles, the feature
metabolism, real-names identity. No `commons.py`, `shelves.py`, `lending.py`, or `nodes.py`
exists. **This is not a failure — it is a plan — but the gap must be named so no reader of the
master plan mistakes design for delivery.** The plan already marks these as stages; the risk
is drift between a rich document and a thinner system.

**Fix:** the master plan's §1 (shipped) and §3 (planned) must stay strictly separated, and
every §3 line needs a task id. Done for #102–#104.

## G8 · THE SEEKER SURFACE IS NARROW
The probe battery is 33/33, but it holds **12 great questions**. A stranger's real question
is often practical ("how do I fix…", "what do I plant…") or relational. Everything outside the
12 falls through to card search, which is the filing-cabinet failure we already fixed once for
the great questions.

**Fix:** widen the battery with practical and relational categories *before* widening the
answers, so the instrument shows the gap before the fix claims to close it.

---

## What is NOT a gap (checked, so it is not re-litigated)
- **Nesting: 0 orphans** across 496,559 cards; every card carries a source label.
- Both surfaces healthy; RSS 1964/1939 MB after the freeze (was 2834/2809).
- Kernel coverage ≥90 enforced; moat 60/60 with 0 false positives *within its stated scope*.
- Consent, moderation, study routes, card render: probed adversarially, clean.

---

## The order I would take them
1. **G5 + G1/G2 together** — per-domain golden cases and per-domain reference cores. One pass
   raises coverage, stocks the empty shelves, and adds substance cards toward the million.
2. **G4** — the reachability gate. Cheap, and it makes work already paid for visible.
3. **G6** — private-key endpoints and the src manifest: both are honesty debts, not features.
4. **G3 + G7** — the Commons wings, shipped stocked.
5. **G8** — widen the probe, then widen the answers.
