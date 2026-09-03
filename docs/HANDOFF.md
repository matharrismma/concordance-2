# Narrow Highway — Handoff (2026-09-03, prepared for Opus)

*Where the work stands and how to pick it up. For the whole picture of what the project **is**, read
[`docs/WORLD.md`](WORLD.md) first — this handoff is **where we are and what's next**, not a
re-explainer. For the full dated history behind every line below, read
[`docs/OPERATIONS_LOG.md`](OPERATIONS_LOG.md) (newest entries at the bottom).*

---

## In one paragraph

The engine is live and healthy on all three surfaces (**narrowhighway.com** secular, **.org** witness,
**.tv** museum), running on the box `nh@5.78.186.55` (two processes: `nh-org` :8001, `nh-com-2` :8002).
Deploy is `sh tools/deploy.sh <repo-relative files>` — staggered canary, auto-verified **box == repo**.
Course handicap **1.1**; 15 subsystems, **0 out, 0 isolated, 2 degraded** (Find, Keeping — Keeping's
"blind ranker" issue is now fixed, see below; the remaining degradation is the ~67% stub count, a
corpus-growth question, and that the fix is unmeasured at scale). Every number here was re-verified
live against the running engine on 2026-09-03, minutes before writing this — re-verify again before
you trust it further; a stale read is a lie to the reader.

---

## Current live state (re-verified 2026-09-03)

- **`.com` / `.org` / `.tv`** all return 200. `/capabilities`, `/systems`, `/search`, `/cards/stats`,
  `/console`, `/ask` all live-smoke-tested this session — working.
- **Numbers (live, just pulled):** 65 verifier domains (62 secular + 3 witness-only) · 133 accepted
  domain names · 94 MCP tools · 673,253 cards. (The `map.html` card/shelf breakdown and route count
  from the prior snapshot were not re-pulled this pass — re-check `/map.html` and `/systems` rather
  than trusting the old figures.)
- **Thread continuity is now real across BOTH doors.** A member typing on `/ask` (`site/index.html`)
  and one speaking to `/console` (`site/coach.html`) share the same `nh_tid` — verified live: two
  `/console` POSTs with a carried `thread_id` returned the same id and the second call's `landed`
  found the card the first one promoted.
- **The ranker now separates a real answer from a bare pointer**, within whatever tier the subject
  partition already put a card in — verified live against `/search`, and unit-pinned
  (`tests/test_retrieval_invariants.py::test_VII`).

---

## What shipped this session (2026-09-02/03, newest first)

| Commit | What |
|---|---|
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

## The open frontier — pick up here (highest leverage first)

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
5. **The surfacing decision** *(a project, not a bug)*. Built-but-unhosted features — the **Gateway**
   page (the "private in, verified out" product, only a code snippet today), the theory **grid**, the
   **Floor**, the **Bible atlas** — have endpoints/renderers but no door. Which gets one first?
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
