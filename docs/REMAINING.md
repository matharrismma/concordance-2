# REMAINING — the one routed sheet

*What is left, each item with a **clear ID that IS its route**. Built 2026-09-05 by consolidating the
scattered registers ([`GAPS.md`](GAPS.md) `G#`, [`PUNCHLIST.md`](archive/PUNCHLIST.md) `C#`/`H#`, the
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
- **`find-2` · A named-entity query returns nothing of the entity.** *Open — measured 2026-11-22.*
  "harmony of the spheres Kepler music of the planets" returns the **honeycomb conjecture at rank 1**
  and no Kepler card at all. "Harmonices Mundi … musical consonance" returns six OpenStax sections on
  simple **harmonic motion** — a stem match on "harmonic", not the concept — including a merry-go-round
  photo credit. "Ptolemy Harmonics Almagest" puts **five John Gill biblical commentaries** in the top
  ten. This is `find-1` with a proper name attached, and it is the same word-sense hole: no rule picks
  the sense. → SOP `find.md`; `find.py`, `corpus.py`.

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
- **`keeping-3` · The card graph is a filing cabinet, not a graph.** *Open — measured 2026-11-22.*
  **1,053,914 edges, 39 relationship types.** `member_of` is **86.2%**; with the citation plumbing
  (`comments_on`, `speaks_to`, `see_also`, `cites`, `same_section`, `shares_scripture`, `part_of`,
  `proof_text`) it is **99.6% filing**. Edges that assert how two ideas relate: **0.40%**. Edges that
  can carry a limit or a refutation (`counterexample_of` 82, `limits` 34, `bounded_by` 1,
  `falsified_by` 1): **118, or 0.011%** — about one per 8,900 cards. Ties to `bound-1`.
- **`keeping-4` · Zero edges between music and astronomy.** *Open — measured 2026-11-22.* Across
  946,739 cards, **not one edge** joins the music shelves to astronomy. The single edge in the whole
  keeping joining anything musical to anything celestial is
  `acoustic_wave_theory --same_form--> celestial_mechanics` — the **wave-physics bridge, not the ratio
  bridge** that actually produced Kepler's third law. `music_theory` itself has no path to anything
  celestial. There is **no `Harmonice Mundi` card**. This is the best-documented cross-domain link in
  the history of science, and the keeping has none of it.
- **`keeping-5` · Ptolemy is filed as half a man.** *Open.* `card_builder_claudius_ptolemy` credits the
  *Almagest* only; the *Harmonics* — the founding text of Western music theory — is absent. He is the
  single strongest piece of evidence for `keeping-4` and we hold half of him.
- **`keeping-6` · Music is 13 cards, 9 of them verifier stubs.** *Open.* The only content card is
  "C → G = 7 semitones (a perfect fifth) · MIDI 69 = A4 = 440 Hz". Shelves: `music_theory` 6,
  `acoustics` 4. Source acquisition is part of the fix: *Harmonice Mundi* is public domain in **Latin**
  but the standard English translations are in copyright, same for Ptolemy's *Harmonics*.
- **`keeping-7` · 13 of 848 principle cards are translation apparatus.** *Open (1.5%, small and real).*
  Lionel Giles's 1910 footnotes arguing with rival translators, filed as `kind: "principle"`,
  `authority_tier: "primary"`, with evidence falsely reading "a principle stated by Sun Tzu"; one body
  ends in a dangling `]` from a slice inside a bracket. → `data/principle_cards.jsonl`.
- **`keeping-8` · All 848 principle cards share ONE call address.** *Open.* Every one resolves to the
  literal string `strategy.principle`, while a pronunciation card gets `pronunciation.g.gr.greene`.
  The address space for that shelf has collapsed to a point.
- **`keeping-9` · 715 of 848 principle cards are `labelled: false`.** *Open (84% never checked).*
- **`keeping-10` · Local/live card drift.** *Open — reconcile on the box, do not guess.* 3,850 astronomy
  cards on disk against **794 served live**. `source_cards.jsonl` and `openstax_cards.jsonl` are not in
  `EXTRA_CARD_SOURCES`; the live count matches openstax + 4 exactly. Cause unconfirmed.
- **`keeping-11` · No shelf or verifier in this engine can be priced.** *Open — measured 2026-11-22,
  `docs/THE_PRICE_OF_THE_PRIOR.md`.* An outside benchmark scores the payload **plus** the decoder and
  any offline weights, and its sharpest result is a prior that predicted better and lost on cost. We
  have the cost half of that accounting now (`tools/keeping_bits.py`: 933,210 cards, 326.3 MB,
  **96.84% of cards and 96.64% of bytes are `kind=reference`**, 510 `verified`; `connection` 6.24x and
  `receipt` 4.81x inter-card redundancy, `note` 1.38x and the densest content in the keeping). The
  usage half is blocked on `own-2` — traffic is not being collected — so no shelf can be shown to earn
  its keep. Ties to `keeping-1` (which measures *stocking*, a different question) and `keeping-2`.

## crisis — Safety · handicap 2 · connected
*This section read "no open defect" until 2026-11-22. That was false: the net was measured and the
measurements are below. The net still catches everything it is pinned to catch — CRISIS_FLOOR
108/108, CLEARLY_BENIGN 0 false fires — but its reach beyond the pinned phrases is poor.*

- **`crisis-1` · The semantic backstop is near-random on unseen phrasings.** *Open — measured
  2026-11-21.* On 12 benign homestead questions against 12 hand-built veiled cries: benign median
  **0.5500** vs cry median **0.5284**, and the benign line out-scores the cry in **75 of 144 pairs
  (52%)**. The orderings are inverted, so **no threshold admits the cries and excludes the benign.**
  Its own docstring example ("how peaceful it would be to just stop", 0.5945) is missed. It cannot
  simply be deleted: it uniquely carries **21** pinned catches. And `is_crisis` *unions* it, so a
  backstop false positive has **no veto** on any of the nine doors. → SOP `crisis.md`;
  `crisis_semantic.py`, `data/crisis_semantic.json`.
- **`crisis-2` · 34 of 98 blind red-team cries are caught by nothing.** *Open.* The ratchet floor is
  64. → `tests/test_crisis_coverage.py` (`RED_TEAM_BLIND`).
- **`crisis-3` · Veiled-cry recall does not generalise.** *Open — the important one.* The 11-21/22
  additions moved the ratchet 59→64, but catch **0 of 8 fresh cries written afterwards, before and
  after**. A deterministic phrase net only ever measures what it already names. **Do not read a
  ratchet move as improved recall**, and do not read a flat ratchet as an inert change.
- **`crisis-4` · The sick-child row reaches the wrong help.** *Open (deliberate fire, wrong target).*
  "throwing up for two days and cannot keep water down" fires on purpose — a vomiting child may be an
  overdose, and the asymmetry favours an unnecessary helpline — but it answers with **988**, which is
  not the help for dehydration. Needs a second help target, not a gate change.
- **`crisis-5` · Two pre-existing backstop sweeps remain.** *Open.* Verified against a clean `git
  archive HEAD` tree: "wouldn't mind if I didn't wake up before the alarm" (0.6970) and "no reason for
  me to be here at this meeting" (0.6613). Neither was introduced by the 11-21/22 work.
- **`crisis-6` · 80 tests unverified.** *Open.* `test_ask.py` and `test_lead.py` skip for want of the
  corpus; only the three crisis files actually ran. The gate has never been exercised end-to-end here.

- **`crisis-7` · `test_crisis_threshold.py` was not covered by the race guard — the issue #41 pins
  had been inert in CI since they were written.** *FIXED 2026-11-22: the autouse fixture moved to
  `tests/conftest.py`, gated to `test_crisis*`.* Found while checking whether CI violates the law
  below. It does not; this file did. The autouse `_backstop_from_real_data` fixture lived in
  `test_crisis_coverage.py`; `test_crisis_profession.py` pulled it in the pytest way
  (`from test_crisis_coverage import (...)` with `# noqa: F401`, which **registers** it), while
  `test_crisis_threshold.py` **never referenced it at all** — it does only
  `import test_crisis_coverage as T`, a module-alias import, which cannot register another module's
  autouse fixture.
  **It did not fail. It SKIPPED, and CI was green.** Of the asked question — favourable order, or
  assertions that never reach the artifact — the answer was the second, and worse than either
  phrasing: four of the six tests sit behind `pytest.skip("crisis_semantic.json artifact not
  present")` with the artifact present and 2.1 MB on disk. Measured at `e064b0f`:

      pytest tests/test_crisis_threshold.py                     ->  6 passed
      pytest tests/test_ask.py tests/test_crisis_threshold.py   ->  2 passed, 4 SKIPPED
      ask + coverage + profession + threshold (real order)      ->  4 SKIPPED

  `pytest -q` — what CI runs — prints those as an `s` indistinguishable from the 76 legitimate
  corpus skips, which is why nobody saw it. Two further findings fell out. **A skipped file still
  poisons:** every `test_ask` test was itself skipped for want of a corpus and the variable was
  still set, because `pytest_collection_modifyitems` adds the skip marker *after* collection has
  imported the module and run its env assignment. And **`test_crisis_coverage.py` carries four of
  the same `available()` skip guards**, safe today only because that file has the fixture — the
  reason the guard belongs in the conftest and not in a file each sibling must remember to import.
  After the move, verified order-independent: threshold alone, with `test_ask` first, and in the
  real collection order all give **6 passed / 24 passed** with no artifact skip. Whole-tree
  before/after on a 115-file slice (1,416 executed tests): **+4 passed, −4 skipped, same 15
  pre-existing failures and 8 errors**, and collection identical at 5,934 items.

**The "run them ALONE" law was STALE — struck 2026-11-22.** It read as standing operational law here
and the SOP it pointed at (`crisis.md`) never documented it at all; the only real account of the race
is a docstring in `test_crisis_coverage.py`, which is the right place for the mechanism and the wrong
place for a law. The race itself is specific and was already closed: `test_ask` sets
`CONCORDANCE_DATA_DIR` to an **empty tempdir at import**, `crisis_semantic` loads its artifact **once**
into a module global, and whichever data dir wins that first `_load()` is settled by collection order
— co-collected, the cache is poisoned with "artifact absent" and blind red-team recall silently falls
to the substring-only floor (**37 vs 58**), a safety gate reporting false-red on nothing but test
order. `_backstop_from_real_data` closes it by saving both globals, pointing at the real data dir,
dropping the cache, reloading, and restoring on the way out. **So the whole suite in one process is
fine** — CI (`coverage run -m pytest -q`) passed on `64a470d`, and locally alone and mixed gave
identical crisis results. The law should never have outlived its fix. → SOP `crisis.md` wants the
mechanism written into it.

**Standing owner decision, not a defect (2026-11-22):** the ambiguous presence branch
("no reason for me to be here") is caught, and the five ordinary sentences it sweeps are pinned
**FIRING** in `test_the_accepted_false_positives_are_a_decision`. Matt was asked and chose the false
positive over the missed person. Silencing one of them means reversing that decision explicitly and
dropping the three matching `CRISIS_FLOOR` cries in the same change.

## ask — the Walk door · reviewed live 2026-11-21
- **`ask-1` · `house.next_step` contradicted crisis-first on a cry.** **FIXED 2026-11-22.** Both this
  and `ask-2` were the same two lines, and **not in `discern.py`** where this sheet pointed — in
  `doors.py`'s `house()`. `discern()` already returned `kind="crisis"` **and** the resources; the
  envelope threw both away for every tool except `ask`. So a cry at the `discern` door was answered
  `next_step: "ask it"` → tool `ask`, while the `ask` branch's own guard (added 2026-10-02, when the
  generic ending was caught pointing a cry **at** discern) sent it back: **a person in crisis handed a
  loop between two doors.** Fixed at the path — `_help_ending()` is decided ONCE, above the per-tool
  branches **and above the internal/plumbing early return**. That placement came from the test: a
  parametrised "every door" case caught `parable`, an INTERNAL, answering a cry with a pointer to
  another tool. 18 pins in `tests/test_doors_help_first.py`. → `doors.py`; SOP `ask.md`.
- **`ask-2` · The envelope re-emitted raw PII.** **FIXED 2026-11-22.** The same step carried the
  submitted text into its params, so the envelope echoed the person's words back — measured on a
  realistic cry, it returned the name, email, phone, age and the means. Two changes: on a cry the
  ending now carries **no prose at all** (no tool, no params — nothing to ride along), and `_step()`
  redacts prose params (`text`/`claim`/`query`/`q`/`word`, never `ref`/`id`/`domain`) at the single
  point every ending passes through. A reference param is left intact so a step still runs as
  written. → `doors.py`.
- **`ask-5` · `redact.py` catches no phone number and no name.** *Open — measured 2026-11-22.* It
  catches **EMAIL, SSN, CARD, IP** and misses `555-0134`, `(512) 555-0134` and `+1 512 555 0134`, and
  cannot catch a name without NER (which the engine refuses). **This is why `ask-2`'s fix removes the
  prose rather than trusting redaction** — relying on it would have been false confidence. A phone
  pattern is cheap and would also strengthen the Gateway (`surface-1`), which shares the redactor.
  `tests/test_doors_help_first.py` pins the gap as a **tripwire**: when redact.py grows the pattern
  that test fails, and the instruction in its docstring is to delete the assertion and close this.
  → `redact.py`.
- **`ask-3` · "Genuinely names the subject" is an overclaim.** *Open.* The test behind the phrase is
  **one shared stem** (`ask._title_names_subject` is `bool(subj & title)`). Either weaken the claim or
  strengthen the test. → `ask.py`.
- **`ask-4` · `voice.gathered` is 0, and `_off_domain_shift` is unused on the discern path.** *Open —
  dead wiring, verify before removing.* → `discern.py`.

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

- **`surface-1` · The surfacing decision.** *In progress — the Gateway shipped.* The **Gateway**
  ("private in, verified out") is now a live, demo-able product surface (`c454d5a`): `site/gateway.html`
  strips PII in the browser (redact.js, nothing sent) and verifies a claim into a re-checkable receipt;
  the `/verify` door was extended to take a plain-language `claim`. **This is THE wedge** (the 2026-09-05
  pivot: narrow the mode, validate with one real user — get a design partner to try it). Still unhosted:
  the theory **grid**, the **Floor**, the **Bible atlas** — but those wait behind the wedge, deliberately.
  Legacy: `HANDOFF #5`, the pivot. (Generic orphan-route triage CLOSED — reachability green `03a9322`.)
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
- **`enum-2` · The relationship vocabulary has synonyms and a singleton tail.** *Open — measured
  2026-11-22.* `same_form` (489) / `same_form_as` (100) / `shares_form_with` (1) are three spellings of
  one relation, so a query for the first **silently misses 101 edges**; `related` (15) / `relates_to`
  (1) / `related_to` (1) likewise. Of 39 types, nine are singletons. **This must be deduped before
  `bound-1` lands**, or the new relationships inherit the rot. → `corpus.py` (`_graft_edge`).

### The reversal — a card that knows its own limit

- **`bound-1` · No card in the keeping carries a limit.** *Designed, not built — `docs/THE_REVERSAL.md`
  (2026-11-22).* Zero limit/bound/scope/caveat/reversal keys across **1,478,343 rows**. Build:
  `data/reversal_bridges.jsonl` (an overlay in the existing `*_bridges.jsonl` idiom, so no card file is
  rewritten and it survives seed regeneration) + a loader sibling of `_apply_bridges` (reciprocal
  attach, 0-FP endpoint test, warn on unresolved) + **one line in the `house` envelope**, which is the
  change that turns 946,739 silent cards into countable wants. Three twin kinds — `relative`,
  `parallel`, `mirror`. Ties to `keeping-3`, `enum-2`.
- **`bound-2` · Reflection is undefined for a proposition.** *Open — the real blocker.* `self_bounding`
  is *falsifiable* (fixed points come in pairs or not at all, always a tritone apart, so the overlay is
  checkable by counting rows per axis: 0 or 2, never 1) but not *derivable* — nothing yet says what it
  means to reflect a claim. Until it does, `self_bounding` is a check, not a construction.
- **`bound-3` · Migrate the 118 existing limiting edges into the field**, not beside it. Two ways to say
  one thing is how `same_form_as` happened.
- **`bound-4` · Load rules to enforce.** `reverses_mirror` without an `axis` is **rejected**, not warned
  — an unreproducible twin is worse than none. Open: axis per-shelf or per-row; whether an `unbounded`
  card is rankable at all on a claim query.
- **`bound-5` · Attribution for the mirror material.** *~~Open~~ **DONE 2026-11-22** — attribution
  corrected in `docs/THE_REVERSAL.md`.* The frames are **Áureo Puerta Carreño's**
  (*El Patrón Secreto de la Música*, thesecretpatternofmusic.com, 2017–; a book, a research body and a
  shop). **The standing rule it leaves behind:** the mod-12 arithmetic is public — the Tonnetz is
  Euler's, reflection is arithmetic, and I recomputed every number rather than taking it. His
  presentation, naming and diagrams are his. **Use the mathematics, never the wall.** Same rule that
  governs Greene: we may hold every brick a living author built from, and never copy their wall.

---

## On the bench right now (2026-11-22) — uncommitted, and the owner's calls

- **`bench-1` · Commit or shelve the working tree.** *~~Open~~ **DONE 2026-11-22.*** Four unrelated
  changes had been sharing one tree. Committed as four, staged by explicit path, never `git add -A`:
  `3cc7f98` the crisis gate · `0d21443` the blocked NUFFT main sum · `533359d` the family battery ·
  `884ae93` these two documents. Tree clean. **Not pushed — `master` is 4 ahead of `origin/master`,
  and the box deploys from `master`, so pushing is a release decision, not a cleanup.**
  Verified before committing: crisis tests alone 24 passed / 1 xfailed (the standing law), FFT 7/7,
  secrets and confidential-IP scan clean across all eleven files.

**Owner's call, not engineering** — carried forward and still open:

- **`own-1` · An outstanding credential rotation and spend limit at a third-party provider.**
  *Owner-only; details are in the private ops log, deliberately not in this public file.* The engine
  side is closed — the `/speak` door is gated (`0a51b59`) and mints nothing without the operator — so
  this is an account action, not a code change. **Highest consequence on this sheet: it is money, and
  it lives outside the repo.**
- **`own-2` · `nh-traffic.timer` is DISABLED**, so `data/traffic.json` is stale and **The Helm is
  showing numbers that are not true**. Either re-enable the timer or make the panel say the data is stale.
- **`own-3` · 63 stick entries carry older seals.** Matt decides before any listing.
- **`own-4` · `stick_mint.py` refuses handler entries, and `riemann` is one** — so no new Riemann mark
  can reach the shelf by *any* route. Verification is the sweep, so there is no shortcut around it.
- **`own-5` · The FFT main sum is built, and it is not the bottleneck.** 1e6 went 423.6s → 166.8s, but
  the Z sweep is now 17.7s of that: **89% is the counting pass.** A component speedup is not a system
  speedup; the next work is the counter, not the transform.
- **`own-6` · 11 food cards are shelved `agriculture`,** so the `foods` shelf is live by accident.
  Rename or re-shelf; `corpus.EXTRA_CARD_SOURCES` hides any unregistered card file.
- **`own-7` · PCK gates vote instead of vetoing.** `K.admit` is `trues >= Q` (Q=2), so a False gate does
  not stop an action — adding 20 always-deny gates changed **nothing**. Restore deadlocks 40/40 with $0
  reserved and $100M idle; registry ∩ ledger packet types = **zero**.

---

## Recently closed (so the delta is visible; do not re-open)
`G4` reachability — green, re-confirmed 2026-09-05 (`03a9322`). · `keeping` ranker, both facets
(`32ed21a` substance, `a525611` phonetic-index). · `§5` private-key-on-the-wire (`4a86cf8`). ·
corpus-dependent tests skip cleanly on a clean clone. · the prophecy weave into a scripture study
(`25d0932`). · the Console shares the Deck (`9fbb605`). · the Automaton (`37d2e49`). · THE_MAP
superseded by WORLD. · the harmony + timeline viewers, the Steward link, the sitemap/redirect
cleanup (`03a9322`).

*Blocked on Matt (not engineering): `node-2` (hardware), `steward-1` (business model), `surface-1`
(which door first), and the whole `own-*` block above — `own-1` (the unrevoked voice key) first.
Everything else is ours to route.*
