# CONSOLIDATION — gather the best into one coherent package

*Built 2026-09-23 from two grounded, path-cited audits (the `site/*.html` surface layer; the card /
deck / shelf / facet layer) read against the live engine, the repo, and [`WORLD.md`](WORLD.md). Every
item carries an **ID that is a route** — the same discipline as [`REMAINING.md`](REMAINING.md). To
close one: do the work, add/flip the guard named in its **durable fix**, then strike it here. A stale
line here is a lie to the next reader.*

---

## 0. The verdict

The **engine is already one coherent thing.** 15 subsystems (star topology, `ask` = hub), 72 verifier
domains, **676K cards with 0 isolated**, one `shell.js` spine on every page, `/systems` course
handicap ~1.1. The keeping is fully connected; nothing in the core is orphaned.

**`.tv` and `.org` are NOT the sprawl.** `.tv` is a single canonical surface (`tv.html` → the museum).
`.org` is a tight witness desk: `index.html` + `bible.html` with its `characters` / `harmony` /
`timeline` / `prophecy` / `read` / `reader` sub-desk, plus `fellowship` + `profile`. Leave them.

**The sprawl is in two places:**
1. **The `.com` surface** — a *front-door triad* (three pages competed for `/`) and an *Atlas suite of
   11 pages for one concept* (one interactive core + 8 static single-view renderings).
2. **The card layer (the bigger, hidden one)** — `decks.py` (the Hare) is a **hand-maintained overlay
   that has rotted against the authoritative per-card call-tree**: it routes to **6 shelves no seeder
   produces**, and **~60+ produced shelves — including the Floor (217 theories) and the bible
   dictionaries — sit in no deck at all.**

---

## 1. THE COHERENT CORE (keep — the best ~20 components)

The package is the **shared engine + these essential doors**:

- **`.com` reach:** `concordance.html` (the live door, served at `/`) · `com.html` (the engine /
  manifesto, behind it at `/com.html`) · `explore.html` (the ONE interactive Atlas, 7 views) ·
  `theories.html` + `calculations.html` + `crossing.html` (distinct data/payload) · `connect.html` +
  `gateway.html` (the agent door) · `proof.html` / `about.html` / `contact.html`
- **Human doors:** `halls.html` (lobby) → `coach.html` · `situations.html` · `plow.html` ·
  `wisdom.html` · `workshop.html`
- **`.org` witness:** `index.html` + `bible.html` (+ sub-desk `characters`/`harmony`/`timeline`/
  `prophecy`/`read`/`reader`) · `fellowship.html` + `profile.html`
- **`.tv`:** `tv.html`
- **Ops (private, unlisted):** `map.html` · `systems.html` · `keep.html` · `live.html` ·
  `playbook.html` · `steward.html`

---

## 2. SURFACE consolidation (the `.com` pages)

- **`surface-1` · Retire the front-door predecessor.** `home_for()` (`web/api.py:3544`) serves
  `concordance.html` at `/`; `com.html` is the engine behind it; **`checkit.html` is the stranded
  third contender** (the "check every number in your quote" auditor). *Action:* fold its pitch into
  `com.html#verify` / `gateway.html`, then `_RETIRED` it. Evidence: `test_reachability.py:132`.
- **`surface-2` · The Atlas suite: 8 static single-views are generated, not authored.** `explore.html`
  is the interactive core (7 views in one). `atlas` / `domains` / `bridges` / `one_body` / `spiral` /
  `torus` / `completeness` / `strategy` are single-view SVG renderings of those same views, all from
  `tools/atlas_explore.py`. *Action:* treat them as **on-demand share/print snapshots** (generated,
  not hand-maintained). Keep `calculations` / `theories` / `crossing` (distinct data/theological
  payload). Evidence: `test_reachability.py:137-140`, `WORLD.md` §5.
- **`surface-3` · Demote `domains.html`.** It is both a top-level spine-nav item (`shell.js:34`) *and*
  one of `explore.html`'s 7 views — a sub-view promoted to a sibling of its own parent. *Action:* drop
  it from the top nav; it's reachable inside the Atlas.
- **`surface-4` · Drop the `encyclopedia.html` stub — after repointing.** It's a JS+meta redirect twin
  of `characters.html` (`assay.py:149` DEAD_END), but **4,743 cards historically cite it.** *Action:*
  repoint those citations to `characters.html`, then remove the stub.
- **`surface-5` · Prune the stale sitemap.** `_SITEMAP_PAGES` (`web/api.py:565`) still advertises
  **~19 retired pages** that all 301 away (`/ask.html`, `/community.html`, `/corpus.html`,
  `/guarantees.html`, `/seal.html`, `/reason.html`, `/almanac.html`, `/teachings.html`, `/brain.html`,
  `/floor.html`, `/places.html`, `/narratives.html`, …). *Action:* prune to live pages only. **Safe,
  immediate.**

---

## 3. CARD-LAYER consolidation (`decks.py`, shelves, kinds, facets)

- **`deck-1` · ✅ DONE 2026-09-24 — and the audit was HALF WRONG.** The only real defect was the
  `"nuclear physics"` (space) token in the `matter` deck (fixed, + the `SHARD_ASSIGN` twin). The audit
  also called `patristics`/`hymns`/`recipes`/`maker`/`classics` "dead — no seeder produces them" and
  told us to drop them. **The LIVE `GET /cards/stats` proves all five are alive** (classics 1,420 ·
  patristics 216 · hymns 21 · maker 12 · recipes 11 — ~1,680 real cards). A static `shelf="..."` grep
  under-counted because seeders mint many shelves dynamically. Removing those deck routes would have
  ORPHANED live content — do NOT. Lesson: verify shelf existence against the live corpus, never a grep.
- **`deck-2` · Collapse the 7-deck "systems" family.** `systems`/`control` claim `{systems}`;
  `electronics`/`fluids`/`thermal`/`mechanical`/`waves` all claim the identical `{systems, physics}`
  (`decks.py:171-200`) — five decks over the same 1–2 shelves, differing only by keywords. *Action:*
  one `systems` deck with sub-keywords.
- **`deck-3` · Merge identical decks. — WITHDRAWN 2026-09-23.** `grieving` (L303) and `be-not-afraid`
  (L295) share the shelf set `{codex, commentary, fieldkit}` but are DISTINCT need-positions (different
  `seed` + keywords → a different hand dealt from the same shelves), and `test_decks.py` pins both as
  separate routes. Merging them contradicts this doc's own `deck-4` principle ("need-deck shelf overlap
  is by design"). Do NOT merge — the audit mistook intentional overlap for duplication.
- **`deck-4` · ✅ DONE 2026-09-24 — the high-value unrouted shelves are now routed.** Confirmed against
  the live `GET /cards/stats`: **`theories` (the Floor, 217)** → new `floor` deck; **`encyclopedia`
  (13,341 Bible dictionaries)** + **`topical` (7,301)** → the `scripture` deck; **`pronunciation`
  (125,167)** → the `word` deck; **`trades` (1,157)** → the `handyman` + `field` decks; `mathematics`
  (88) + `geometry` (9) → the `works` deck; `finance` (34) → the `nations` deck. Left unrouted on
  purpose: ops/edge shelves (`seals`, `sources`, `spine`, `connections`, `reference`, `domains`).
  (Need-deck shelf overlap is **by design** — cards cut across shelves — not a defect.)
- **`card-1` · Dead `kind`: `walk`.** `codex._CONTENT_KINDS = {"note","walk"}` (`codex.py:46`)
  recognizes `walk`, but nothing anywhere mints `kind="walk"`. *Action:* prune it. (Note: `spine` is
  NOT a kind — it's a top-level flag; spine cards are `kind="note"`.)
- **`facet-1` · 7 of 11 facet types are unpopulatable.** In `facets_for` (`corpus.py:325`), only
  `verse` / `person` / `place` / `concept` (+ the catch-all `subject`, which isn't even in the declared
  schedule) ever receive values; `mention` / `sequence` / `reference` / `dictionary` / `taxon` /
  `language` / `provenance` can only ever appear as empty presence markers. *Action:* either wire their
  values in `facets_for`, or drop them from `FACET_SCHEDULE` and add `subject` to it.

---

## 4. THE ROOT FIX (the durable gather — do this and the drift can't return)

The card layer **already has a single source of truth**: `corpus.deep_call` / `call_number` /
`call_children` (`corpus.py:161,233,447`) — every card is shelved at the gate (`shelve()` runs in
`load` and `add_card`), and the library call-tree (`graph.calltree`, `map.html`) is just the human walk
over it. `decks.py` is a **curated retrieval overlay that rotted against it** — that is the one true
duplication.

**Fix the PATH, not the instances:** stop hand-maintaining `decks.py` against reality, and add two
guard tests so it can never silently drift again —
1. **every `_DECKS` shelf is produced by some seeder** (kills the 6 dead tokens the moment they're
   introduced), and
2. **every produced content shelf is claimed by ≥1 deck** (surfaces the Floor / dictionaries /
   domain-cores the instant they go unrouted).

The other organizers are **complementary, not duplicates** — `field_canon.py` (where to *fetch* PD
sources) · `grid.py` (the verifier/domain scaffold) · `canon.py` (scripture books by tradition) ·
`compendium.py` (the `the-works` builder) · `shelves.py` (a *different* "shelf" — a member's personal
Commons shelf, a naming collision only). Leave them.

---

## 5. Execution order (safe → high-value)

1. **`surface-5` + `deck-1` (token) + `card-1`** — prune the stale sitemap, fix
   `nuclear physics`→`nuclear_physics`, drop the dead `walk` kind. ✅ **DONE 2026-09-23** — and the
   `deck-1` token had a SECOND instance the audit missed: `corpus_db.SHARD_ASSIGN` also read
   `"nuclear physics"` (space), so nuclide cards were silently falling to the `core` shard instead of
   `science`; both fixed. (Deploying the `SHARD_ASSIGN` fix moves nuclides `core`→`science` on the box —
   confirm `science` is in the thawed shard set before/at deploy.)
2. **`deck-4` guard (§4)** — add the two deck↔shelf coverage tests. *The durable win.* **BLOCKED** on
   the live corpus's distinct-shelf inventory (data is box-local; `SHARD_ASSIGN`/`_SHELF_FORMAT` are
   partial maps, not a complete registry). Get it from the live `GET /cards/stats` after deploy, then
   finish `deck-1` (remove truly-dead shelves) and `deck-4` (route the Floor/dictionaries/trades).
   `deck-2` (collapse systems family) is a routing-behaviour change (loses predict() granularity), so
   confirm before doing it. `deck-3` is **withdrawn** (see §3 — do not merge).
3. **`surface-1` / `surface-2` / `surface-3`** — retire `checkit`, mark the 8 Atlas statics as
   generated snapshots, demote `domains.html`.
4. **`surface-4`** — repoint `encyclopedia` citations, then drop the stub.
5. **`facet-1`** — wire or drop the 7 dead facet types.
6. One-line **`WORLD.md` §4** fix — it says `.com / = com.html`; it is now `concordance.html` (the flip
   landed 2026-09-21, one day after WORLD.md was verified).

---

## 6. Verified coherent — leave alone

The engine (15 subsystems, 0 isolated cards), the `.tv` museum (one surface), the `.org` witness desk,
the N=1 instruments (`golf`/`grappling`/`music`/`provision` — correctly off-nav behind the Halls
lobby), the reciprocal-road spine, and the reachability discipline itself (`test_reachability.py:193`
already enforces link-or-declare, so no page is an *accidental* orphan). These are the coherent core;
the work above is trimming the overgrowth around them, not rebuilding.

---

## 7. `corpus_db.py` shard rebuild — ✅ DONE 2026-09-24 (runbook kept for next time)

**Executed in a ~48s full maintenance window** (both services stopped → 7.1 GB free → build 688,857
cards in 13s → verify `moved True` → swap → restart). Result: `science` 49,312→52,698 (+nuclides),
`nuclear_physics` gone from `core`; live nuclide queries (uranium-238, carbon-14) return results;
both faces 200; `data/shards.old` kept as rollback. `corpus_db.py` is now deployed + box==repo.
The runbook below stands for the next SHARD_ASSIGN change:

`corpus_db.SHARD_ASSIGN` now reads `nuclear_physics` (underscore), moving ~3,385 nuclide cards from
the always-thawed `core` shard to `science`. The pre-built `data/shards/*.db` on the box were built
under the OLD assignment (nuclides in `core`), so **deploying `corpus_db.py` alone would make
`shard_of("nuclear_physics")` point at `science.db`, which does not yet contain them** — a silent
nuclide-retrieval gap. `tools/build_corpus_db.py` places each card via `corpus_db.shard_of()`, so the
fix and the shards must land together, new-file-first:

1. Stage the NEW `corpus_db.py` on the box **without a restart** (plain `scp`/`tar`, not `deploy.sh`).
2. Free RAM for the heavy load — the builder loads the full ~2.7 GB corpus resident (it disarms
   `CONCORDANCE_FREEZE_SHELVES` for itself). On the RAM-tight box, `sudo systemctl stop nh-org` first
   (the witness), so only one service holds a corpus during the build.
3. Build to a SIDE dir so live shards are untouched mid-build:
   `cd /home/nh/concordance-2 && PYTHONPATH=src python tools/build_corpus_db.py --out data/shards.new`
4. Sanity-check `data/shards.new/manifest.json`: the `science` shard's `shelves` now include
   `nuclear_physics` and its card count rose by ~3,385; `core` fell by the same.
5. Swap + restart: `mv data/shards data/shards.old && mv data/shards.new data/shards`, then
   `sudo systemctl restart nh-org nh-com-2`.
6. Verify live: a nuclide query (e.g. `/search?q=uranium-238`) returns results. Keep `data/shards.old`
   as the rollback until confirmed.

Heavy + RAM-risky on the live box — run at low traffic, with a person watching. Until then the fix
stays committed-but-undeployed and the box keeps the (working) old behaviour: nuclides resident in `core`.

---

*Current state (2026-09-23): **Step 1 executed and committed** — the sitemap pruned of its 19 retired
entries, the `nuclear physics`→`nuclear_physics` typo fixed in `decks.py` AND `corpus_db.SHARD_ASSIGN`,
the dead `walk` kind removed, and the `WORLD.md` §4 front-door line corrected (§6). The deck-layer
reconciliation (`deck-1` removals, `deck-4` routing, the §4 guard tests) is HELD pending the live
shelf inventory (`/cards/stats` after deploy); `deck-3` is withdrawn as an audit error. The rest of §2
(surfaces) and `facet-1` are not yet done.*
