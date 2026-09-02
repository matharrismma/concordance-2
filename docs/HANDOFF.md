# Narrow Highway — Handoff (2026-09-02)

*Where the work stands and how to pick it up. For the whole picture of what the project **is**, read
[`docs/WORLD.md`](WORLD.md) first — this handoff is **where we are and what's next**, not a re-explainer.*

---

## In one paragraph

The engine is live and healthy on all three surfaces (**narrowhighway.com** secular, **.org** witness,
**.tv** museum), running on the box `nh@5.78.186.55` (two processes: `nh-org` :8001, `nh-com-2` :8002).
Deploy is `sh tools/deploy.sh <repo-relative files>` — staggered canary, auto-verified **box == repo**.
Course handicap **1.1**; 15 subsystems, **0 out, 0 isolated, 2 degraded** (Find, Keeping). Every number
is live-wired or re-checkable against `GET /capabilities` and `GET /systems`.

---

## Current live state (verified 2026-09-02)

- **`.com`** = the secular verification-engine face (`site/com.html`): live "check a claim" instrument,
  65-domain breadth, receipt, agent/API door, **numbers live-wired from `/capabilities`**, self-hosted
  fonts, sovereign. **CORS open** (any browser/agent can call read/verify; writes still need a signature).
- **`.org`** = Christ forward (`site/index.html`): *"Christ is the center. The Word is the foundation."*
- **`/map.html`** = the map of everything: the flow, the three surfaces, live counts, the **subsystem
  constellation** (the body wired, fractal with the cards — `isolated: NONE`), and the live card
  constellation (653k ideas / 110 shelves / 3 planes). Linked from both faces + the Ctrl-K palette.
- **Numbers (live):** 65 verifier domains · 133 accepted · 94 MCP tools · 6 profiles · 191 routes ·
  673,243 cards · course handicap 1.1.

---

## What shipped this session (newest first)

| Commit | What |
|---|---|
| `cf30b2f` | `docs/WORLD.md` — the comprehensive world document (reference / review handoff) |
| `3717e11` | Integrate where logical: **tongues → the Word** (`pronounce` gives Greek words a real pronunciation; isolated → connected) |
| `1be4b5f` | **The body as a constellation** — `systems.py` learns the subsystem graph (integration degree, fractal); `map.html` renders it |
| `62e81a4` | **The map of everything** — lit the dark `NHGraph.map` renderer, un-retired `/map.html`, wired it in; fixed dead links (study-desk nav, `llms.txt` → dead `/corpus.html`) |
| `2e2fa96`, `0a86999` | `.com` review: **live-wired the stat numbers** from `/capabilities`; domains grid/copy consistent at 65 |
| `e0173fa` | Self-hosted Spectral + IBM Plex on `.com` (sovereign, no Google call) |
| `d4b81a2` | **Christ forward on `.org`** |
| `842f256`, `1252b11` | **Secular `.com` face + surface sort + CORS agent door + theodicy crisis fix** |
| `bc881f7` | Composed the connection map into the found lead (two signals, both true) |

All deployed, box == repo, Watchman-verified (console clean, endpoints checked).

---

## The open frontier — pick up here (highest leverage first)

1. **The Keeping's substance-aware ranker** *(the real retrieval fix; degraded)*. The ranker is blind to
   *substance vs headword* — ~67% of source cards are word/pronunciation stubs, so a thin gloss can
   outrank a real excerpt. The connection signal is composed but near-inert until this lands. This is the
   single highest-leverage engineering. Files: `corpus.py` (`_score`, `SUBJECT_TIER`), `ask.py`
   (the found-path shaping). See memory *coherent-model / responses-aren't-great-is-retrieval*.
2. **Find's pull selection** *(degraded, guarded)*. The post-pull relevance guard stops a confident wrong
   lead (it falls to an honest gap), but selection quality is the open work. Files: `find.py`,
   `field_canon.py`, `expand.py`.
3. **Continue the subsystem mesh** *(the star → a peer-mesh)*. The scripture/prophecy/witnesses cluster is
   "thin" — functionally integrated in the flow but not peer-meshed. The next genuine weave: add
   `prophecy.for_ref(ref)` and surface a passage's fulfillments + original words in a Scripture study
   answer (`ask.py` scripture handler ~line 1369). Do it as real composition, never decorative imports.
4. **The surfacing decision** *(a project, not a bug)*. Built-but-unhosted features — the **Gateway** page
   (the "private in, verified out" product, only a code snippet today), the theory **grid**, the **Floor**,
   the **Bible atlas** — have endpoints/renderers but no door. Which gets one first?
5. **Tracked gaps:** verifier domain coverage ~52%; OT→NT prophecy sweep not run; founders (Ellen G.
   White) gather pending (needs per-work `--start-after`); off-site backup durability; `find_verifier` is
   referenced in docs/the MCP tool description but unimplemented here; `docs/THE_MAP.md` has stale counts
   (superseded by `WORLD.md`).
6. **Housekeeping:** the auto-memory index `MEMORY.md` (~21KB) is due for an archive-reorg — move the
   oldest completed-work pointers into `reference_archive_index_completed_work.md`. Do it carefully
   (preserve every pointer; diff the link set before/after).

---

## How to continue (the disciplines that must hold)

- **Method:** look before you build · grounded gap analysis (query the live state, *then* act) · seek a
  stronger method first · don't rush to deploy · two things can be true at once (compose, don't replace).
- **Loop:** build → test **locally** (fast pure suite; integration where the engine is needed) → deploy
  (`sh tools/deploy.sh <exact files>`) → **live-verify on prod (the Watchman)** → clean up test data.
- **Git:** commit by **exact paths** (never `add -A`), push, co-author trailer; commit ≠ deploy.
- **Never weaken:** the crisis net, the gate, PD-only for others' text, "nothing generated", points to
  Christ. Crisis tests run **alone** (a documented global-cache ordering race). Never print the
  ElevenLabs `sk_` key or `YOUTUBE_API_KEY`.
- **Truth:** verify against `/capabilities` + `/systems` + the repo, not memory. A stale read is a lie to
  the reader; CANNOT_CHECK ≠ pass.
- **Box:** keep `tests/` and `docs/SOP/subsystems/` synced to the box for `/systems` accuracy.

---

## Pointers

- **Reference:** [`docs/WORLD.md`](WORLD.md) (all aspects + locations + a reviewer section).
- **Live truth:** `GET /capabilities`, `GET /systems`, `https://narrowhighway.com/map.html`.
- **The record:** `git log --oneline` (this session ends at `cf30b2f`); `docs/OPERATIONS_LOG.md`.
- **Memory:** the auto-memory index (loaded each session) carries the constitution, the standing
  guidance, and the per-topic project/feedback notes.

*Snapshot as of 2026-09-02. The engine is the truth; re-verify before you trust any number here.*
