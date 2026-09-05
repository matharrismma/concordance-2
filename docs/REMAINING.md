# REMAINING — the one routed sheet

*What is left, each item with a **clear ID that IS its route**. Built 2026-09-05 by consolidating the
scattered registers ([`GAPS.md`](GAPS.md) `G#`, [`PUNCHLIST.md`](PUNCHLIST.md) `C#`/`H#`, the
`task #NNN` comments, the `HANDOFF` frontier, every SOP's "unsupported" line, and the live `/systems`
handicaps) into one taxonomy. There is no new problem under the sun: every item below already existed
somewhere; this sheet only gives it a stable address.*

## The ID is the route

```
<slug>-<n>
```

`<slug>` is the subsystem — the **same slug** used by `GET /systems`, by `docs/SOP/subsystems/<slug>.md`,
and by `src/concordance/systems.py`. `<n>` is stable for the life of the item. So an ID routes you,
with no lookup, to four things:

1. the live health line — `GET /systems` → the subsystem's `handicap` and `issues`;
2. the standing procedure — `docs/SOP/subsystems/<slug>.md` (canary, triage, known issues, refine);
3. the code — the modules that SOP names under **Wiring**;
4. the register of record — this file.

Cross-cutting work that belongs to no single subsystem uses a descriptive slug (`commons-`, `seed-`,
`record-`, `surface-`, `enum-`). **To close an item:** do the work, watch its `/systems` handicap
move, strike it here, and flip its SOP "unsupported" line to supported. A stale line here is a lie to
the next reader — the same rule the ops log holds.

Ordered by the live handicap (highest hurt first). Re-verify every number against `/systems` and the
SOP before trusting it; this sheet is a map, the running engine is the territory.

---

## find — the Tortoise · handicap 4 · degraded
- **`find-1` · Pull mis-selects a tangential source.** *Open (guarded).* A post-pull relevance check
  keeps a shared-word mis-select from leading confidently (it falls to an honest gap), but selection
  *quality* is the work. → SOP `find.md`; `find.py`, `field_canon.py`, `expand.py`, `providers.py`.
  Legacy: `HANDOFF #2`.

## verify — the Moat · handicap 3
- **`verify-1` · Domain verifier coverage ~52%.** *Open.* About half the registered domains have a
  golden case; the fix is per-domain goldens (a true claim and a false claim each; the false must not
  seal). → SOP `verify.md`; `verifiers/`. Legacy: `GAPS G5`.
- **`verify-2` · `find_verifier` is named but unresolved here.** *Open (ambiguity).* It appears in the
  `check` tool description in `mcp/server.py` with **no handler in this repo**, yet
  `mcp__concordance__find_verifier` is a live runtime tool — reconcile (implement, or correct the
  description). Do not guess-remove. → `mcp/server.py`. Legacy: review 2026-09-03.

## keeping — the Corpus · handicap 2 · degraded
- **`keeping-1` · ~67% of the keeping is a pointer, not an answer (STOCKING).** *Open — growth, not
  scoring.* The ranker is done (both facets, `32ed21a`+`a525611`); what remains is a deepening
  process (ISBE-style full text, Gutenberg chapters, per-domain reference cores), not another scoring
  change. Flip `keeping` off `degraded` only after a scale re-measure. → SOP `keeping.md`;
  `corpus.py`, `growth.py`. Legacy: `GAPS G1`, `HANDOFF #1`. Ties to `seed-1`, `field-1`, `tv-1`.
- **`keeping-2` · Compact the resident floor (~1.9 GB/process).** *Open (2026-09-05).* Freezing is now
  correctly ACTIVE (the silent-off env-var bug is fixed, `b3e3d56` — it sheds card bodies to the mmap'd
  shards). Measured floor: card **stubs ~1.9 GB** (connections alone ~449 MB) + **token index ~375 MB**;
  bodies are already on the shards. To go leaner (Matt: "make it efficient and compact as reasonable"):
  (a) move frozen-shelf candidate generation to the **shard FTS** so the resident `_by_token` only
  indexes non-frozen shelves (~-375 MB); (b) **compact the stubs** — intern repeated field values
  (shelf/surface/kind/lifecycle), lazy-load `connections` from the graph store instead of holding them
  on every stub (~-449 MB). Both are careful retrieval-/graph-path changes, well-tested before deploy.
  → `corpus.py` (`_by_token`, `_candidates`, `_STUB_KEEPS`), `corpus_db.py`, `graph.py`. Legacy: box
  RAM cleanup + freeze-config fix, ops log 2026-09-05.

## crisis — Safety · handicap 2 · connected
- *No open defect.* The handicap is coverage/SOP strokes on a deliberately hardened net, not a gap.
  **Standing operational law, not a task:** crisis tests run ALONE (a documented global-cache
  ordering race). → SOP `crisis.md`.

## scripture — the Word · handicap 1 · connected
- **`scripture-1` · Cross-references need the xrefs DB built.** *Operational.* If a "meaning" ask
  returns no `cross_refs`, `data/xrefs/xrefs.db` is absent — `python tools/migrate_xrefs.py`. → SOP
  `scripture.md`.

## tongues — Original Tongues · handicap 0 · connected
- **`tongues-1` · The original-words half of the study weave.** *Open.* Prophecy fulfillments now
  weave into an `/ask` scripture study (`25d0932`); the matching *Strong's original words beside the
  studied passage* in the `/ask` answer is not yet there (the `tongues → the Word` integration already
  wired pronunciation into word-study; bible.html already shows original words via `/original`). →
  `ask.py` scripture handler; `strongs/`, `verifiers/scripture.py`, `pronounce.py`. Legacy: `HANDOFF #3`.

## prophecy — handicap 1 · connected
- **`prophecy-1` · The full OT→NT sweep is not run.** *Open (future).* The weave and data exist
  (`prophecy_fulfillments`); the exhaustive OT-prophecy → NT-fulfillment pass across the canon is the
  larger work. → SOP `prophecy.md`; `prophecy.py`, `prophecy_fulfillments.py`. Legacy: `systems.py`.

## witnesses — the Cloud · handicap 1 · connected
- **`witnesses-1` · Founders gather pending.** *Open (content op).* `tools/gather_witness.py` needs a
  per-work `--start-after` to skip front-matter and append only the author's own PD paragraphs; the
  load-once cache picks them up on the next mtime bump. The cloud today is 385 passages / 2 witnesses
  (Spurgeon, Ellen White). → SOP `witnesses.md`. Legacy: `FOUNDERS INGESTION` memory. Feeds `tv-1`.

## tv — the Museum · handicap 1 · connected
- **`tv-1` · Fill the thin halls; grow the automaton's cloud.** *Open (demand-driven, never
  generation).* The automaton (`37d2e49`) testifies from whoever is gathered; richer halls come from
  gathering more PD witnesses via the want-list/tortoise, not from authoring. → SOP `tv.md`; `tv.py`,
  `automaton.py`. Legacy: `GAPS G3` (flagship wings), automaton memory. Shares work with `witnesses-1`.

## node — Sovereignty · handicap 1 · connected
- **`node-1` · No off-site backup durability.** *Open (honesty debt).* Every backup lives on the same
  box it backs up; `node_roles` already designs the capacitor answer (a second node holds a copy
  off-box). → SOP `node.md`; `node_roles.py`, `tools/backup.sh`. Legacy: `GAPS G6`.
- **`node-2` · LoRa/Meshtastic bridge is hardware-field-test pending.** *Open (needs the radio).* The
  code + 3-state (UNALTERED/SIGNED/AUTHENTIC) are built; it wants a real `--dev` on real hardware. →
  SOP `node.md`. Legacy: `LoRa` memory. **Blocked on Matt/hardware.**

## field — the Field Library · handicap 0 · connected
- **`field-1` · Shelves thinly stocked** (12 herb monographs, 41 almanac entries). *Open — grown on
  demand by the Tortoise, not a defect.* → SOP `field.md`. Legacy: `GAPS G2`. Ties to `keeping-1`.

## steward — money · handicap 0 · connected
- **`steward-1` · The swipe-fee concierge earner is not built.** *Open (business model).* The engine
  STEWARDS the swipe, never moves money — the boundary holds regardless. → SOP `steward.md`;
  `steward.py`. Legacy: `LOSS LEADERS` memory. **Needs Matt (a business decision).**

## coach — the personal keeping · handicap 0 · connected
- **`coach-1` · The personal-keeping dashboards are unbuilt (endpoints ready).** *Open (future
  standalone).* `POST /days` ("your days" — time + concentration from this browser's threads) and
  `POST /journal` (keep the day's ideas) stand ready and are declared agent-flow-reachable; their
  human dashboards are the future work. → `api.py` (`/days`, `/journal`); `stacks.py`; `coach.html`.
  Legacy: 2026-09-05 wiring pass.

---

## Cross-cutting — no single subsystem

- **`surface-1` · The surfacing decision.** *Open — needs Matt.* Built-but-unhosted features have
  endpoints/renderers but no front door: the **Gateway** ("private in, verified out", a code snippet
  today), the theory **grid**, the **Floor**, the **Bible atlas**. Which gets a door first is a
  product call. Legacy: `HANDOFF #5`, map audit. (The generic orphan-route triage is otherwise
  CLOSED — reachability is green as of `03a9322`.)
- **`commons-1` · First wings stocked** (recipes · music · art, PD seed cards) — a wing never
  announced before it is stocked. Legacy: `PUNCHLIST C1e`, `GAPS G3`.
- **`commons-2` · Opportunities to serve** (Romans 12:1): a member posts a need or an offer, matched
  by proximity + capability (never profiling), attested by the one served, unseen by default (Mt 6:3),
  no leaderboard. Legacy: `PUNCHLIST C1f`.
- **`seed-1` · Seeding continued toward 400k substance cards** — ~~Matthew Henry complete~~ **DONE
  2026-09-05** (1,347→4,124 cards, avg 1,882 chars, live). Remaining: Torrey's unresolved references,
  Smith's + AmTract cores, the other PD CrossWire modules, the probed-live open sources (NIST, openFDA,
  DailyMed, NOAA, GBIF, OpenAlex). The single biggest lever on `keeping-1`/`field-1`. **Landing path
  proven:** mint locally → scp the `*_cards.jsonl` → rebuild shards on the box (safe live) → staggered
  restart. Legacy: `PUNCHLIST #5`, `GAPS G1/G2`.
- **`record-1` · THE_RECORD — this sheet, GAPS, and the ops log rendered from cards**, so hand-editing
  is impossible without the renderer disagreeing. This file is a step toward it, not the end. Legacy:
  `PUNCHLIST #2`.
- **`enum-1` · `curate.action` needs a `CURATE_ACTIONS` constant** (`shelves.py` compares
  'promoted'/'withdrawn' inline). The only real entry in `mcp/server.py`'s `ENUM_TODO`; `grid_axis.axis`
  there is deliberately NOT an enum (dimensions grow). → `shelves.py`, `mcp/server.py`.

---

## Recently closed (so the delta is visible; do not re-open)
`G4` reachability — green, re-confirmed 2026-09-05 (`03a9322`). · `keeping` ranker, both facets
(`32ed21a` substance, `a525611` phonetic-index). · `§5` private-key-on-the-wire (`4a86cf8`). ·
corpus-dependent tests skip cleanly on a clean clone. · the prophecy weave into a scripture study
(`25d0932`). · the Console shares the Deck (`9fbb605`). · the Automaton (`37d2e49`). · THE_MAP
superseded by WORLD. · the harmony + timeline viewers, the Steward link, the sitemap/redirect
cleanup (`03a9322`).

*Blocked on Matt (not engineering): `node-2` (hardware), `steward-1` (business model), `surface-1`
(which door first). Everything else is ours to route.*
