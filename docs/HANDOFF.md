# Narrow Highway — Handoff (2026-09-06)

*Where the work stands and how to pick it up. For the whole picture of what the project **is**, read
[`docs/WORLD.md`](WORLD.md) first — this handoff is **where we are and what's next**, not a
re-explainer. For the full dated history behind every line below, read
[`docs/OPERATIONS_LOG.md`](OPERATIONS_LOG.md) (newest entries at the bottom). Full open work, ID'd and
routed: [`REMAINING.md`](REMAINING.md). A red team from Fable is being prepared for —
[`RED_TEAM_BRIEF_2026-09-06.md`](RED_TEAM_BRIEF_2026-09-06.md).*

---

## THE PIVOT — read this first (2026-09-05)

A strategic call Matt made and agreed to, and it changes what "next" means: **keep the lane, narrow the
mode.** The lane (verifiable, sourced, re-checkable provenance — the one thing generative AI can't do)
is right and appreciating. The risk was *breadth* — one builder spreading across 15 subsystems, three
domains, and ever more surfaces, doing maintenance-and-polish instead of *validating the thesis with a
real user*. So the mode changed: **focus on the single sharpest wedge — the Gateway ("private in,
verified out") — and get one real design partner to try it.** The Gateway is now shipped and demo-able
(see below). **Freeze the breadth** — no more "found another orphan to wire" sessions — until the wedge
pulls. The next move is not more building; it's Matt finding one real user/customer. Honor this.

---

## In one paragraph

The engine is live and healthy on all three surfaces (**narrowhighway.com** secular, **.org** witness,
**.tv** museum), running on the box `nh@5.78.186.55` (two processes: `nh-org` :8001, `nh-com-2` :8002).
Deploy is `sh tools/deploy.sh <repo-relative files>` — staggered canary, auto-verified **box == repo**.
15 subsystems, 0 out, 0 isolated, 2 degraded (Find, Keeping — both ranker facets fixed; the remaining
degradation is the ~67% stub count, a *stocking*/corpus-growth question, not a scoring one). Re-verify
every number against `/capabilities` + `/systems` before trusting it; a stale read is a lie to the reader.

---

## Current live state (2026-09-06)

- **`.com` / `.org` / `.tv`** all return 200; `/gateway.html` live on both faces. Re-verify against the
  running engine — a stale read is a lie to the reader.
- **The Gateway is live and demo-able** (`gateway.html`): PII stripped in the browser (redact.js),
  a claim verified into a re-checkable receipt. The `/verify` door takes a plain `claim` now.
- **The box runs lean and healthy.** Freezing was silently OFF (a missing `CONCORDANCE_CORPUS_SHARDS`
  env; fixed in code `b3e3d56` — shards default to `DATA_DIR/shards`). RAM available 2.4 → 3.3 GB, swap
  2 → 6 GB. The deeper resident floor (~1.9 GB/proc) is the token index + stubs (`keeping-2`), not bodies.
- **Matthew Henry is complete** (seed-1, `1565a6f`): commentary +2,777 substance cards, live.
- Thread continuity across `/ask` + `/console` (same `nh_tid`); both ranker facets fixed
  (`tests/test_retrieval_invariants.py::test_VII`, `test_VIII`).

---

## What shipped recently (newest first)

| Commit | What |
|---|---|
| `69499e6` | **Red-team brief for Fable** + honest Gateway privacy wording (the hero no longer overclaims "both run at your edge") |
| `c454d5a`, `5293770` | **The Gateway, demo-able** — `gateway.html` + the free-text `/verify` "verified out" door (the pivot's wedge) |
| `b3e3d56`, `1565a6f` | **Box freeze fix + seed-1 Matthew Henry** — freezing was silently off (shards default to DATA_DIR/shards); MH completed + shards rebuilt |
| `03a9322` | Wired in every aspect: Harmony + Timeline viewers, Steward link, reachability green |
| `25d0932` | **Prophecy woven into a Scripture study** — Isaiah 53 → its NT fulfillments (CONCORDANT) on both reader surfaces; self-gating; live-verified visually on `.org` |
| `5727c7d` | Keeping self-report records the phonetic-index fix; `"degraded"` now = stocking, not the ranker |
| `a525611` | **Ranker facet 2: a phonetic guide never leads a bare subject lookup** — "gravity" led with ARPABET; pronunciation genre loses the exact-title boost; ask_probe 25/25 |
| `25d0932` | **Prophecy woven into a Scripture study** — Isaiah 53 → its NT fulfillments (CONCORDANT) on both reader surfaces; self-gating; live-verified visually on `.org` |
| `5727c7d` | Keeping self-report records the phonetic-index fix; `"degraded"` now = stocking, not the ranker |
| `a525611` | **Ranker facet 2: a phonetic guide never leads a bare subject lookup** — "gravity" led with ARPABET; pronunciation genre loses the exact-title boost; ask_probe 25/25 |
| `32e5a36` | **Keeping's self-report catches up** — `systems.py` + the keeping SOP no longer call the fixed ranker issue "unsupported"; `"degraded"` deliberately left standing (unmeasured at scale) |
| `32ed21a` | **The ranker: substance vs headword** — `corpus.SUBSTANCE_WEIGHT`, docs/HANDOFF's own #1 open item from the prior snapshot. Full detail + design rationale in `docs/OPERATIONS_LOG.md`'s newest entry and memory `ranker-substance-vs-headword`. |
| `9fbb605` | **The Console joins the Deck** — `/console` now shares `/ask`'s thread + recall pipeline. Full detail in the operations log and memory `console-joins-the-deck`. |
| `074cc51` | **Never forgets, part 1** — surfaced `recall.land`/`remember`'s existing (but silent) output on `/ask`'s typed-chat UI (`index.html`) |

Earlier sessions' shipped work (`.com` face, the map, the subsystem constellation, tongues→Word, etc.)
is unchanged and still live — see the previous revision of this file in git history or
`docs/OPERATIONS_LOG.md` for that record; not re-listed here to keep this snapshot current rather than
ever-growing.

All of the above: deployed, box == repo, Watchman-verified (live smoke tests, not just HTTP 200).

---

## In flight — not mine, don't duplicate it

A **separate, concurrent local session** (Matt clicked the flagged task chip) is fixing a genuine,
pre-existing bug found while testing the ranker change: running the WHOLE 219-file suite in one
`pytest tests/` invocation fails
`tests/test_ask.py::test_a_greek_word_study_can_be_said_tongues_woven_into_the_word` — confirmed
identical on a clean `git stash` baseline, so unrelated to the ranker. Root cause: `CONCORDANCE_STRONGS_DIR`
feeds a MODULE-LEVEL constant in `strongs/{concordance,lookup}.py`, read once at import time; pytest
imports every test file during collection before any test runs, so whichever file's import triggers
`concordance.strongs` first wins the env var for the whole process. The fix is in
`tests/test_bible.py`, **uncommitted as of this handoff**.

**Before touching `tests/test_bible.py` or re-diagnosing this bug: run `git status` and `git log` to
see whether that session finished and committed.** If it's still dirty and you need the file for
something else, don't discard the changes — that's someone else's in-progress work, not scratch state.

---

## The open frontier — but read THE PIVOT first

**The #1 move is not on this list: it's validation.** The Gateway wedge is shipped and demo-able
(`surface-1`, below) — the next step is Matt finding **one real design partner / user** to try it, and
learning from that. Everything else here is **frozen behind the wedge, deliberately**, until it pulls.
So this is the "when the wedge is validated, or Matt redirects" list — not a build queue to grind now.

*The full, ID'd, routed list of everything remaining is [`REMAINING.md`](REMAINING.md) — each item a
`<subsystem>-<n>` that routes to `/systems`, its SOP, and its code. The IDs below in brackets are the
routing IDs.*

1. **The Keeping — the ranker is DONE, what's left is STOCKING** *(2026-09-03, Opus)*. Measuring
   `SUBSTANCE_WEIGHT` live (`tools/ask_probe.py` → 25/25) exposed and fixed a second facet: every
   single-word subject lookup led with a phonetic string ("gravity" → `G R AE1 V AH0 T IY0`) because a
   pronunciation card's title is its headword and won the exact-title boost. Fixed (`a525611`): the
   pronunciation genre is withheld from that boost; those lookups now lead with the definition. **Both
   ranker facets are now closed.** Keeping stays `"degraded"` for one honest reason only — **~67% of the
   keeping is a thin pointer** (a *stocking* gap, not a ranker defect). To move it off degraded: a
   growth process that deepens niche subjects, not another ranker change; the SOP's "Refine" note says
   what a scale re-measure would take before flipping the flag. Remaining Keeping leverage is **corpus
   growth**, not scoring.
2. **Find's pull selection** *(degraded, guarded)*. The post-pull relevance guard stops a confident
   wrong lead (it falls to an honest gap), but selection quality is the open work. Files: `find.py`,
   `field_canon.py`, `expand.py`.
3. **Subsystem mesh — one weave DONE, more to do** *(2026-09-03, Opus)*. The prophecy weave shipped
   (`25d0932`): studying an OT passage the NT itself takes up (Isaiah 53 → Matthew 8:17, Luke 22:37…)
   now surfaces those fulfillments (verdict CONCORDANT) on BOTH reader surfaces — the `/ask` study
   answer (`index.html`) and the `bible.html` study desk — self-gating to nothing on a non-messianic
   passage. Live-verified visually on `.org`. **Still thin:** the *original words* half of that weave
   (Strong's beside a studied passage in the `/ask` answer — `bible.html` already has it via
   `/original`), and peer-meshing the witnesses cluster further. Real composition, never decorative.
4. **`.tv` — entertainment, its season now open.** Matt: *"You need to complete all 3. .org is family.
   .com is business .tv will be entertainment."* New resources disclosed but not yet used: a YouTube
   channel already set up, PD episodes on an external hard drive, and Matt's pro ElevenLabs account
   (voice cloning already wired for Coach/Console TTS — see `NHSpeak`/`site/speak.js`). Ask what's on
   the drive and what the channel needs before building; this is unscoped, not a bug to close.
5. **The Gateway wedge — SHIPPED (`c454d5a`+`5293770`), now validate it** `[surface-1]`. `site/gateway.html`
   is live: strip PII in the browser (redact.js, nothing sent) and verify a claim → a re-checkable
   receipt (the `/verify` door was extended to take a plain-language `claim`). **This is THE thing** —
   the next move is one real user, not more surfaces. Still unhosted, behind the wedge: the theory
   **grid**, the **Floor**, the **Bible atlas**.
6. **Tracked gaps:** verifier domain coverage ~52%; OT→NT prophecy sweep not run; founders (Ellen G.
   White) gather pending (needs per-work `--start-after`); off-site backup durability; `find_verifier`
   is referenced in the MCP tool description but unimplemented here; `docs/THE_MAP.md` has stale counts
   (superseded by `WORLD.md`); Lighthouse's 71 `verify_*` tools folded behind one `check`+`find_verifier`
   is a portable pattern for concordance-2's own 94-tool MCP surface — noted as an opportunity, not
   started.

*Housekeeping done this pass, not carried forward:* the auto-memory index `MEMORY.md` was compacted
from ~21.9KB to ~17.5KB (every pointer preserved, links intact) — no longer an open item.

---

## How to continue (the disciplines that must hold)

- **Method:** look before you build · grounded gap analysis (query the live state, *then* act) · seek a
  stronger method first · don't rush to deploy · two things can be true at once (compose, don't
  replace) · when you change what a self-report claims, verify the claim was actually true before
  changing it, and re-verify the dashboard reflects the change live.
- **Loop:** build → test **locally** (fast pure suite; integration where the engine is needed) → deploy
  (`sh tools/deploy.sh <exact files>`) → **live-verify on prod (the Watchman)** → clean up test data.
- **Git:** commit by **exact paths** (never `add -A`), push, co-author trailer; commit ≠ deploy. Before
  any destructive git operation, or before assuming a dirty working tree is yours to overwrite, run
  `git status` — another session may be mid-work in the same checkout (see "In flight," above).
- **Never weaken:** the crisis net, the gate, PD-only for others' text, "nothing generated", points to
  Christ. Crisis tests run **alone** (a documented global-cache ordering race — the same CLASS of bug
  as the `CONCORDANCE_STRONGS_DIR` issue above: a module-level constant read once from an env var at
  import time). Never print the ElevenLabs `sk_` key or `YOUTUBE_API_KEY`.
- **Truth:** verify against `/capabilities` + `/systems` + the repo, not memory or a prior handoff. A
  stale read is a lie to the reader; CANNOT_CHECK ≠ pass.
- **Box:** keep `tests/` and `docs/SOP/subsystems/` synced to the box for `/systems` accuracy.

---

## Pointers

- **Reference:** [`docs/WORLD.md`](WORLD.md) (all aspects + locations + a reviewer section).
- **Live truth:** `GET /capabilities`, `GET /systems`, `https://narrowhighway.com/map.html`.
- **The record:** `git log --oneline` (this handoff written at `32e5a36`); `docs/OPERATIONS_LOG.md`
  (newest entry: "All 3" — the Console + the ranker, 2026-09-02/03).
- **Memory:** the auto-memory index (loaded each session) carries the constitution, the standing
  guidance, and the per-topic project/feedback notes — see `console-joins-the-deck_2026-09-02` and
  `ranker-substance-vs-headword_2026-09-02` for this session's own notes, and the frozen constitution
  block at the top of `MEMORY.md` for what may never be traded away in the name of a metric.

*Snapshot as of 2026-09-03. The engine is the truth; re-verify before you trust any number here.*
