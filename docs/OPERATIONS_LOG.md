# THE OPERATIONS LOG — every piece, mapped, verified, carded

Matt, 2026-07-29: "Everything must be logged. We must be masters of documentation and
logistics. We map, verify, and keep cards on every piece."

The keeping already cards what we *know*. This logs what we *do* — every operational event
that changes the system, with its receipt. Newest first. One line per event minimum:
**what · when · measured evidence · where the proof lives**.

Three standing rules:
1. **No silent anything.** A cap, a skip, a partial run, a thing that could not be checked —
   named here, in the words that are true (found / gone / could-not-check).
2. **Measured, not asserted.** Every claim carries the number it came from and how it was taken.
3. **Every piece gets a card.** Objects (shards, nodes, sources, wings, SOPs) belong in the
   keeping like everything else; this log records the events that create and change them.
   OPEN: operational carding (shards, nodes, curators, deploys) — task #104.

---

## 2026-08-01 (22:16Z) — THE 54-SECOND OUTAGE: 57 dead citations, both drawers

Matt authorised the outage. Taken deliberately, kept to 54 seconds (22:16:48 -> 22:17:42Z).

**VERIFIED BEFORE REPAIRING.** `tools/divergence.py` named five dead destinations; an instrument
that mistakes its own reading for a defect accuses the thing it measures, so `maker.html`,
`recipes.html` and `sermons.html` were each fetched over the wire first. All three answered 404.
Genuinely gone.

**THE RULE, added to `tools/repoint_citations.py` — one rule per KIND, never one for all.** The
card IS the content: "Build a Crystal Radio" was a section of a page that no longer exists, but
the card holds the instruction; the recipe card IS the recipe; the sermon card IS the sermon.
So the label stands and the dead door comes down — the same judgement as clearing the seal claim
from 11,084 cards rather than redirecting it somewhere plausible. Pointing a card's source at its
own permalink would close a provenance circle, which this project exists to prevent.

`/placeholders` is counted SEPARATELY and deliberately: that is not a page that went away, it is
a source that was never recorded. Different fact about the keeping, and the reader deserves the
true one.

**BOTH DRAWERS, because fixing one is how 4,039 went stale in July:**

    57 in data/cards.jsonl          (24 storyboard, 12 maker, 11 recipes, 7 placeholder, 3 sermons)
    57 in data/shards/core.db       (0 in the other five shards)

Backup taken first (/tmp/cards.jsonl.bak, 25,087 lines). Services stopped because the shards are
opened `immutable=1` — a promise the bytes do not change underneath a reader.

**AFTER, every instrument clean:**
  divergence   5 of 5 agree  (first fully clean run; was 2 diverged this morning)
  watchman     10 hold on BOTH hosts
  calibration  OFFSET 0 / 0
  the reader   "Buttermilk Biscuits · The White House Cook Book · 1887" — authority kept, no dead door

---

## 2026-08-01 — nh-steward: a retired 1.0 job running for a month, writing nothing

Asked "could anything from the outside be influencing our work?" The answer was no, but finding it
took real evidence rather than reassurance.

`nh-steward.timer` fired every 15 minutes from `/home/nh/Lighthouse` — the 1.0 tree, recorded
retired under task #37 — burning **50s CPU per run (5.6% of a core, continuously)** and reporting
`ok=True` on find_connections / codex_refresh / craft_tools.

**IT WROTE NOTHING.** No file under `concordance-2/data` changed in its run window; its OWN 1.0
data files were last modified **Jul 1 and Jun 28**. A month of work landing nowhere. Disabled
(reversible; nothing deleted).

**WHAT IS GENUINELY WORTH UPGRADING FROM IT** is in the unit's own Description, which I read past
twice: *"resource governor"*. Its three jobs are all things 2.0 already does better — but NOTHING
IN 2.0 GOVERNS. No part senses load and throttles input. That is Watt's flyball on the steam
engine, and it matters more now than when it was written, because the tortoise and the shepherd's
rounds fire on LIVE TRAFFIC rather than a schedule. The belt had come off a governor; the fix is
to reconnect it, not to port the other three jobs.

Also cleared in the same sweep: the box was missing 21 of 154 test files, so it could not verify
itself — the exact condition the MANIFEST guard exists to catch. Now 154 of 154.

---

## 2026-08-01 — LEVER 3: THE WATCHMAN (the system reports on itself)

Matt ordered the levers: landmine, flywheel, then 3/4/5/2. This is 3.

**Why it was the right one.** Six real defects were found today and THE GATE WAS GREEN THROUGH
EVERY ONE — 1,000+ tests passing, moat 60/60, while `/verify` answered 500 to every caller for
over an hour. Each was invisible to static inspection and obvious the moment the system was
DRIVEN END TO END. Tests prove the code does what it was told; only walking the doors asks whether
the library still behaves.

**`tools/watch.py` — ten live checks, each one a defect that actually happened**, walked as a
reader and as an agent, over a real socket:

  front door answers · proving still works (the /verify outage) · handles are not accumulating
  (the leak itself) · a miss stays a miss (the stopword bug) · the ceiling is announced (the
  1.67 MB request) · both doors expand (the deaf /search) · the agent plane withholds (the
  hardcoded lifecycle_stage) · the review desk is reachable (3 held, queue reporting 0) · no tool
  advertises a private key · the door does not 500 on nonsense

**FIRST RUN, BOTH HOSTS: 10 hold, 0 broken, 0 could-not-check.** Handles 0 open / peak 5,
verify HOLDS, 82 tools none asking for a key, 4 malformed shapes no 5xx.

**AND THE TENTH CHECK WAS LYING.** `the agent plane withholds` PASSED VACUOUSLY on its first run:
it searched a nonsense term, got `nothing_found` as it always would, never reached the branch that
tests withholding, and printed `ok`. The instrument built to catch vacuous passes committed one.
Rewritten to inspect what is ACTUALLY HELD (take a card the review desk says is waiting, confirm
the public door will not serve it) and to return CANNOT_CHECK — never HOLDS — when nothing is held.

**THREE STATES, NEVER TWO.** HOLDS / BROKEN / CANNOT_CHECK. A check that could not run is not a
check that passed. CANNOT_CHECK never fails the unit: crying wolf is how a watchman gets ignored.

**PROVEN TO BARK, not merely to be silent.** Each check was fed a broken world: 900 handles open
-> BROKEN; /health no longer reporting handles -> BROKEN ("the leak would be invisible again");
junk for a nonsense question -> BROKEN with the titles named; 200 results and no `limit_capped` ->
BROKEN; a held card served publicly -> BROKEN; a check that raises -> the run REFUSES to report
and exits 2. `tests/test_watch.py`, 14 tests — one of which immediately failed on my own
`check_the_front_door_answers` for having no docstring saying what it guards.

**Hourly (`nh-watch.timer`), and the interval is not habit:** the handle leak took ~81 minutes of
ordinary traffic to become fatal, so an hourly walk catches that class before a caller does.
`systemctl is-failed nh-watch.service` is the one-word answer to "is anything wrong".
`data/watch.json` holds the latest; `watch_history.jsonl` gets one line per run so DRIFT is
visible over time rather than only the newest snapshot.

Static/store drift stays with `tools/divergence.py`, which runs where the data lives. This is the
wire.

---

## 2026-08-01 — THE ANCIENT ASSAY: 1,000 probes, religions and knowledge before 1 AD

Matt: *"Run 1000 test runs... focused mainly on religions and knowledge prior to 1AD. Find errors
or regression and identify the source."*

**Coverage.** 1,000 probes / 544 distinct terms / 13 domains, live against narrowhighway.com,
via `tools/assay_ancient.py`. Four verdicts, never two: EMPTY is a GAP (want-list material), only
ERROR and DEGRADED are defects.

| | before the repairs | after |
|---|---|---|
| reached the engine | 811 (188 throttled at 6 workers) | **997** (3 workers) |
| OK | 59.4% | **85.2%** |
| DEGRADED | 33.4% | **3.9%** |
| EMPTY (gaps) | 58 | **106** |
| engine ERROR | 0 | **0** |

**The gap count ROSE, and that is the system telling the truth.** Junk answers had been masking
real misses; an honest zero is what feeds the want list.

**THE DEFECT, and its source: a miss was rendered as an answer.**

    q="Mahavira"          -> 0 results + want_hint     CORRECT
    q="what is Mahavira"  -> Aurelius Meditations 8.51, 8.10, Boethius §boe_03_10

`corpus_db._match` joined every token with OR, stopwords included, so any natural-language question
matched any card containing "what" or "is". Three classics cards surfaced across ~250 unrelated
probes. `Zuo Zhuan` returned a PLANT (Xylanche himalaica — "ding zuo cao"); `Mozi` returned a
homeopathy card. The harm is doctrinal, not cosmetic: the library said "here is what I have" when
the truth was "I do not hold that", and because results came back `want_hint` never fired — so the
miss was never recorded and the shepherd loop was silently starved. The library is designed to grow
by its misses.

**IT LIVED IN TWO PLACES, and fixing one did not fix the site.** After the shard matcher was
repaired, gated and DEPLOYED, the live wire still answered `what is Mahavira` with Marcus Aurelius.
The resident in-memory index scores with IDF, which dampens common words but never excludes them —
log(478k/20k) is about 3.2, nowhere near zero — so with the distinctive word matching nothing,
"what" and "is" carried unrelated cards on their own. Both doors now filter through ONE shared
`_STOP` list, imported not copied, with a test asserting the resident door reaches for it.
Verified on the wire, not asserted: `Mahavira` 0, `what is Mahavira` 0, `what is Zoroaster` ->
zoroaster, `what is grace` -> Amazing Grace.

**A false alarm, retracted.** The first report said "251 slug_title regressions escaped
repair_cards.py". Wrong: that was the SAME three classics cards counted repeatedly through this
bug, and their `§` slugs are ones `render_title` DELIBERATELY DECLINED rather than invent a section
number. After the fix: 6.

**A second false alarm, retracted.** The first report said "ERRORS 189 — always a defect". 188 of
those were HTTP 429 — the rate limiter working as designed, a deliberate refusal, not an engine
failure. Real engine errors across both runs: ZERO. (3 client-side TLS handshake timeouts in the
second run are ours, not the box's.)

**Remaining, identified but NOT fixed:** 33 off_topic. Part are false positives of the assay's own
substring test — `Uruk` -> "ISBE: Erech" is the correct scholarly answer, `Maat` -> "Ma'at" fails on
an apostrophe. The genuine residue is the any-word FALLBACK in `corpus_db.search()` matching a
query's COMMON word when its distinctive one is absent (`War Scroll` -> "The Black Phalanx ... War
of Independence"). Fix when taken up: require the highest-IDF term to participate in the fallback.

**106 GAPS — the want list's raw material.** Most striking: all four Vedas (Rigveda, Samaveda,
Yajurveda, Atharvaveda), Qumran, Enuma Elish, Orphism, Gathas, Mahavira, Tripitaka, Mohism,
Samkhya, Nyaya, Vaisheshika, Herophilus, Erasistratus, Berossus, Melqart, Meroitic, Ahiqar.
By domain, the emptiest: india_pre1ad (29), mesopotamia_religion (18), persia_zoroastrian (16).

---

## 2026-08-01 — P1 pressure test: THE FILE-HANDLE LEAK (an outage we caused, found, and closed)

**What happened, measured.** A deliberate read-ceiling burst against `narrowhighway.com` —
250 × `GET /search?q=grace&limit=1` — returned **249 × 200, 1 × 000 (client timeout), 0 × 429**,
confirming the split rate limit from R4 holds (the old shared cap refused at 121). The same run
left the engine broken: a following burst of 60 × `POST /verify` returned **60 × 500**, zero
successes.

**Cause, from the box, not guessed.** `journalctl` (readable only because the `[500]` stderr
logger was added earlier the same night):

    OSError: [Errno 24] Too many open files:
      '/home/nh/concordance-2/src/concordance/receipts.py'

`/proc/<pid>/fd` on nh-com-2: **1023 of 1024 held** — 255 × `dictionary.db`, 255 × `books.db`,
254 × `world.db`, 254 × `word.db`. nh-org, on lighter traffic, was at 63 and climbing (97 twenty
minutes later). Nothing was wrong with verification: Python could not open `receipts.py` to
import it. **Reading knocked out proving.**

**The arithmetic.** `ThreadingHTTPServer` opens a thread per connection; `corpus_db` opened a
connection per thread per shard; nothing ever closed one. Unbounded by construction — only the
traffic rate decided the hour. Each half was separately correct: per-thread connections were
themselves the 2026-07-29 fix for `database is locked` and for `fetchone()` returning None on a
row that exists. The defect was in their product, which no review of either half would catch.

**Repair, at the source.**
* `corpus_db.close_this_thread()` — a thread closes what it opened; called from
  `Handler.handle`'s `finally`, once per CONNECTION so keep-alive still reuses an open shard.
* `corpus_db.open_connections()` → `{open, peak, shards_thawed}`, **reported by `GET /health`**.
  This leak was invisible until the process could not open a file; it is now a number anyone
  can watch.
* `freeze()` carried the comment *"Nothing leaks: a connection dies with its thread"* — that
  sentence was the bug, written a second time, and it orphaned every other thread's handle.
  Corrected, and its close now decrements the count.
* `LimitNOFILE=65536` on both units — **headroom, explicitly not the cure**. A leak refills.

**Proof the test is real.** `tests/test_shard_handles.py` runs over a real socket (the close
lives in the handler; a unit test would pass while the wire leaked) and asserts `peak > 0` before
any verdict — its first version passed having opened ZERO connections, because the suite runs
with no shards configured. With the close disabled: **60 handles after 60 reads**. Restored: **≤4**.

**Service restored** 15:47Z by restarting nh-com-2 — fds 1023 → **4**; `POST /verify` answered
`{"verdict": "HOLDS"}`. The fix itself ships with this deploy.

**Not yet done:** the MCP surface fuzz, the last deferred part of P1.

---

## 2026-07-29

**PUNCH LIST item 1 · THE COMMONS · C1a — the member shelf. DONE, live.**
- `shelves.py` + 9 tests. A shelf is a covenant key with signed cards on it, not an account.
- Three rings: private / **shelf (UNGATED — the gate is on amplification, never on speech)** /
  commons (enters `public_review`, waits for a HUMAN steward).
- VERIFIED LIVE on the box, whole flow: signable → signed on the member's side → drop lands
  `public_review` at tier `member` → commons count 0 (nothing uncurated reaches it) → review
  queue 1 → **a signature from another key was REFUSED** ("nobody can put words on another
  member's shelf") → steward promoted with a reason → commons 1, **tier still `member`**.
- Member tier is never upgraded: the library amplified it; the library did not verify it.
- Every curation act names a steward AND a reason. A refusal withholds amplification but leaves
  the member's words on their own shelf. Append-only, so a withdrawal keeps the record.
- `corpus.is_public` independently withholds private drops — two agreeing checks, not one.
- The deploy guard caught `address.py` absent from the box and it was shipped: STAGED means "not
  wired into the loader", not "not present", and a box deliberately unlike the repo defeats the
  guard's whole purpose.
- Live-test drops were removed afterward: a verification is not content.
- Gate: **941 passed.**

**Ground recorded: Romans 12:1-2.** Matt: "Romans 12:1 was the beginning of all of this...
12:1 leads to 12:2. Maybe we also build in opportunities to serve?" λογικὴν λατρείαν (reasoned
service, present your BODIES) → δοκιμάζειν (the assayer's word: PROVE what is good). Offering,
then assay. C1f added to the punch list: needs & offers matched by proximity and capability,
never profiling; attested BY THE ONE SERVED; **no leaderboards** (service is not currency) and
the act **recorded but unseen by default** (Mt 6:3).

**SEEDING BEGUN (Matt: "get started") — the commentaries carded verse by verse.**
- The deepest substance already on our disk was reachable only through `/commentary`: not
  searchable, not in the graph, invisible unless you knew to ask. Now **44,371 verse cards**
  — Clarke 13,318 · Gill 29,707 · Henry 1,346 — average **1,462 chars** of the commentator's
  OWN public-domain words, `generated: false`, licence travelling with each card.
- **44,031 carry a `comments_on` edge to their verse card** — FOUND (the commentary file says
  which verse it expounds), never invented.
- Henry's store existed only on the box; pulled down so all three could be carded.
- Count, both numbers as the discipline requires: **541,103 total · 311,040 substance (57.5%)**,
  up from 268,033 (54.0%). +43,007 substance in one pass. To 1M substance: 688,960.
- Shards rebuilt on the BOX (cheaper than shipping ~1 GB): 544,260 cards, `word` shard 387 MB.
- LIVE: Gill on John 3:16 renders **14,578 bytes** of his own words; commentary is searchable;
  RSS 1572/1560 MB — still ~1.2 GB below where the night began, with 44k more cards.
- TWO CORRECTIONS MY OWN GATE FORCED (checks 4 and 5 of the day): I asserted "every body ≥120
  chars", which failed **330 real cards** — Clarke on 1 Chr 1:12 is *"Caphthorim — 'The
  Cappadocians.' — T."*, 37 characters and the whole of what he wrote. The wrong response
  would have been dropping genuine exposition to satisfy an instrument. And the shard test
  inherited the same bad threshold; it now asks the real question — does the shard serve
  EXACTLY what was minted, byte for byte.
- Gate: 926 passed.

**THE FREEZE WIDENED — the runway to 1M, taken.**
- Measured first (never guessed): maximal freeze = **985 MB/process** locally for 496,730 cards
  vs ~1,980 MB with four shelves — 2.03 KB/card, so **1M cards projects to 1,984 MB/process**,
  ~3.97 GB for both, inside a 7.75 GB box. Probe battery **33/33 under maximal freeze** before
  any change was made.
- Applied: `CONCORDANCE_FREEZE_SHELVES` 4 → **24 shelves**, `.env` backed up first, value QUOTED
  (one shelf is literally `nuclear physics` — unquoted it would have truncated the list in the
  systemd EnvironmentFile, silently freezing less). Parse verified: 24 shelves, space intact.
- LIVE RESULT: **2018/1940 → 1448/1466 MB per process**; box available **3,355 → 4,326 MB**.
  Since the night began: 2834/2809 → 1448/1466 MB (**~2.7 GB freed**).
- Reader loses nothing, verified live on both surfaces: frozen-shelf search (dictionary),
  ISBE full article 19,521 bytes, Gill on John 3:16, a domain-core card showing its CONFIRMED
  worked math, the seeker path, and passage lookup.
- Rollback: `.env.bak-*` on the box; unset the env and everything loads resident as before.

**DURABILITY · the ark is real, and a green backup log was hiding a hole.**
- FOUND: the daily backup named 6 items (`cas ledger activity.jsonl cards.jsonl bible_en.jsonl
  strongs`) = 18 MB, while data/ held 1.9 GB. **Every acquisition was backed up nowhere** —
  source_cards 227M, gutenberg 116M, scripture_cards 52M, taxonomy 38M, ISBE, OEIS, minted
  edges. The weekly "full" on the box belongs to Lighthouse 1.0 and covers none of 2.0.
  A green backup log meant the receipts were safe and the library was not.
- FIXED: `tools/backup.sh` now takes the whole data dir minus the derivable (shards rebuild in
  ~2 min; acquisitions re-fetch). Measured after the change: **86 items, 133 MB compressed**.
- OFFSITE: `tools/ark_pull.sh` pulls the newest tarball to the 12 TB drive and RE-HASHES the
  landed copy against the box's signature. First run: **VERIFIED
  eeaab915afb324c5… · 134 MB**, plus all 7 shards and the source archives.
- RESTORE REHEARSED (an untested backup is a hope): unpacked the ark's copy to a scratch dir →
  **499,716 cards loaded, search answered, ISBE card present.**
- ALSO FOUND: the deploy path corrupts shell scripts — Windows CRLF broke `set -euo pipefail`
  the moment backup.sh was deployed; the nightly cron would have failed silently. Normalized,
  and `.gitattributes` pins `*.sh` to LF.
- The three tiers Matt named are now the topology: **Hetzner** serves · **12 TB** is the ark ·
  **this device** builds. Node roles (task #103) generalize it.

**GAP PROGRAM (docs/GAPS.md) — G5, G2, G4, G6 closed.**
- G5: 48 domains carry a PROVEN golden pair (derived from each verifier's own documented
  example, run, kept only if it held). **0 false positives.** Gated.
- G1/G2: 171 substance cards minted from those runs (avg 565 chars: inputs, verdict, refused
  falsehood). Shelves holding exactly one card: **33 → 20**.
- G4: reachability gated — but the first measurement was WRONG (read only *.html, ignoring
  `nh-tools.js`, the Everything palette). True count: one page genuinely lost (`mesh.html`),
  now listed. Third "check the check" correction of the day.
- G6: `tools/verify_deploy.py` proves the box matches the repo; first run found **airlock.py
  never deployed**, web/keep.py stale, 3 dead files from a July 25-26 refactor.

**D7 CAPSTONE · the null assay — three rings.**
- Ring A (99 theories): 1 finding — *Agricultural science* claimed `seals` with zero sealed runs
  in the keeping. Corrected to `partial`, reason on the card, restorable when a real run seals.
  99/99 aligned AFTER the correction. Tool: `tools/null_assay.py` (rerunnable, `--json`).
- The instrument lied first: draft 1 asked only "does a verifier exist?" → 9 false findings
  (Gödel, ZFC, evolution, germ theory…). Corrected; pinned by `tests/test_null_assay.py` so it
  cannot drift back into flattering us. **Check the check before you trust it.**
- Ring B (our own theses): 3 findings AGAINST US — the RAS bridge recorded CONFIRMED (science
  yes, the Mt 6:22 bridge is RESONANCE), "the tune is the truth-CRITERION" (a heuristic; name
  its null test), coherence-as-proof (a consistent fiction is coherent). All three memories
  corrected the same night.
- Ring C (adjacent families): nothing contradicts the engine's narrow claims; every tension
  lands on the same seam — deterministic checks are safe, interpretive bridges stay marked.
- Report: `docs/NULL_ASSAY.md`. Gate: 916 passed. Commit `6b2c6e6`.

**Corpus count: 496,559 cards — 49.7% of the 1M goal** (ISBE contributed 9,381 today).

**D6 · security sweep over the new surfaces** — two real holes found and closed.
- ICS injection (`connect_write`): `start_iso`/`end_iso` interpolated into DTSTART/DTEND with no
  escaping and no validation; `_esc` did not escape a bare `\r`. One consented event write could
  have injected ATTENDEE / ORGANIZER / URL or a second VEVENT. Closed: ICS grammar validation +
  every newline form escaped. Proof: `tests/test_security_sweep_d6.py`.
- Unsigned witnesses (`moderation`): self-asserted `reporter`/`viewer` strings meant one person
  with three names could hold TRUE content from public reads, and anyone could edit another
  viewer's block list. Closed: fresh detached signatures over canonical bytes naming the exact
  target; `site/community.html` mints a device-local key so the fix reaches the reader.
- Probed clean: consent (wrong signer / tampered scope / cross-agent / cross-verb / TTL cap /
  private-key smuggling), study routes (traversal, injection, oversize, NUL), card render
  (attribute breakout, `javascript:` URLs), ambiguous-ref last mile.
- Lesson recorded: `docs/SOP/LESSONS.md` (2026-07-29 entry).

**D5 · acquisitions — ISBE 1915, Adam Clarke, John Gill.**
- ISBE: CrossWire SWORD module v2.2 (Public Domain), zLD binary parsed stdlib-only after
  reverse-verifying the layout against real offsets. 9,380 articles / 22.9 MB text →
  `data/acquisitions/isbe.db` (25.3 MB, mmap'd) + 9,381 cards (1 spine + entries, zero orphans).
  Full article renders on the card page (verified live: 19,521 bytes for `card_isbe_aaron`).
- Clarke 854 chapters, Gill 1,189 chapters via bible.helloao.org (the Matthew Henry road);
  registered in `commentary.SOURCE_META` with attribution. **Gill is not on CrossWire at all** —
  helloao was the lawful road for both. Verified live on both surfaces.
- Gate: 903 passed. Commit `f3f35a4`.

**D4 · the shards wired — the heavy shelves ride SQLite.**
- Profiled first (per Matt's decision): dictionary/gutenberg/geography/taxonomy = 258.7 MB
  serialized, ~70% body/bands/extra/source, none of it needed by the graph.
- Live measurement: RSS **2834 / 2809 MB → 1893 / 1908 MB** per process (~1.85 GB freed);
  box available 1.7 → 3.5 GB. Probe battery 33/33 under freeze. IDF proven identical frozen vs
  resident (two regressions caught by the battery first: stub length-normalization boost, then
  corpus-wide IDF drift — both pinned as tests).
- FOUND IN ROLLOUT: `corpus_db.py` had **never been deployed** — the droplet receives files by
  scp, not by checkout, so a module nothing had yet imported was simply absent. Same shape as the
  MANIFEST lesson, on the src side. Fixed by deploying it; worth a guard (see OPEN below).
- Gate: 899 passed. Commits `44fb324` (code), shards built + shipped (964.8 MB, 7 files).

**Kernel coverage floor raised 75 → 90.**
- cas 93 · derivation 90 · ledger 91 · receipts 95 · record 93 · signing 98 · validate 93.
- `tests/test_trust_kernel_edges.py` (12 tests) pins the paths that only run when something is
  wrong — corrupt files, missing signatures, tampered chains, unreachable stores.
- Gate: 892 passed. Commit `eb40812`.

**Shard inventory (from the live manifest).**
| shard | cards | MB | note |
|---|---:|---:|---|
| core | 30,063 | 68.9 | the personal floor — the whole map, any phone |
| science | 52,694 | 96.9 | |
| word | 55,255 | 166.7 | |
| world | 120,556 | 177.7 | |
| dictionary | 149,490 | 226.8 | frozen on the droplet |
| books | 79,120 | 227.8 | frozen on the droplet |
| **full node** | **487,178** | **964.8** | the entire keeping, on an $8 microSD |

---

## 2026-07-29 · C1b — THE COMMONS reaches HTTP and the agent surface

**Six routes, six MCP tools, one store.** `GET /drop/signable` · `POST /drop` · `GET /shelf` ·
`GET /commons` · `GET /curate/queue` · `POST /curate`, and `shelf_signable` · `shelf_drop` ·
`shelf_read` · `commons_read` · `curate_queue` · `curate` for agents. Rate limiting on the three
write paths only — reading a shelf is not a write, and `viewer` decides what is SERVED without
being kept anywhere. A test asserts the string `viewer` never appears in the store.

**Measured live** (`tools/live_shelf_check.py` against narrowhighway.com, 18/18):
a key born on this device signed bytes the server minted; the drop landed; a forged signature was
refused 400 with its reason; a `private_key` was refused at the live door and again when smuggled
inside `fields`; a commons drop sat in `public_review` and the commons stayed at 0; the agent door
and the HTTP door saw the same store in both directions. Every card the probe made was **withdrawn**
at the end — the queue is back to 0 and each act is in the record with its reason. Nothing deleted.

**Two things I got wrong, both caught by checking the check:**
- the first live run "failed" two assertions asserting a stranger sees ≥2 cards on that shelf. A
  stranger sees ONE — the commons drop is awaiting a steward and correctly withheld, surfacing only
  as `awaiting_review`. The system was right; the expectation was wrong.
- the first golden patch put all six paths in `GOLDEN_RATELIMITED`, including the three read-only
  ones. The route-golden test caught it immediately.

`shelf_drop` needed a second private-key check one level down, inside `fields` — the top-level guard
the older write tools use would not have seen it. `tests/test_mcp_no_private_keys.py` now pins both
depths. The Commons tools are on the **secular** surface: a maker who never opened the Gate still
gets a shelf.

Gate PASS (kernel 93%, 60/60 moat). Deploy reported the same 3 known EXTRA files on the box
(`web/ask.py`, `branding.py`, `config.py` — punch-list item 4, awaiting Matt's word to archive).

---

## 2026-07-29 · C1c — `shelf.html`, and two things it uncovered

The page: a key born in the browser, a name you choose, three rings, your own shelf, the commons,
someone else's shelf by address, and the steward queue. `nh-tools.js` lists it, so the six shelf
routes came **off** the `AGENT_ONLY` declaration C1b put them on — which is what that declaration
was for.

**FINDING 1 — `POST /curate` was open, and I shipped it that way.** C1a took the steward's name on
faith; `steward` is a string anyone can type. C1b deployed that to the live box, so for the window
between that deploy and this fix, any passer-by could have promoted their own drop into the commons
or pulled someone else's card down. Nothing was: the live store held only my 9 verification drops
and 7 curations, checked directly on the box.

Closed with two authorizations and nothing else, **in `shelves.curate` so the MCP door cannot
bypass what the HTTP door enforces**:
- `promoted` / `refused` → the steward token (reuses `CONCORDANCE_KEEP_TOKEN`, the gate the keep
  already uses — one authority, one place to rotate). **Fails closed**: no token configured, no
  promotion.
- `withdrawn` → the steward token OR the member's own signature over `/curate/signable` bytes. A
  member never needs permission to take their own words down.

`tests/test_shelves.py` grew 4 tests, including "a typed name is not authority" and "one member
cannot pull down another's card".

**FINDING 2 — no JSON response on this server had ever carried a `cache-control` header, on any
route, ever.** Surfaced as a shelf that was exactly ONE WRITE BEHIND in a real browser: a member
withdrew their card, the store recorded it with its reason, and the page still showed the card.
The reader was being told the opposite of the record.

Diagnosis took three wrong turns, each corrected by measuring instead of reasoning:
1. "It's a race" — no; `await`ing the refresh did not fix it (the `await` was still right).
2. "It's the store" — no; append-then-read is correct in one process, in the OneDrive working copy
   *and* in a plain temp dir. Measured both.
3. "It's the missing header" — the header was genuinely missing and now `no-store` ships on every
   JSON answer including errors (a cached 403 is worse than a cached 200) — **but it did not fix
   it either.** The decisive measurement: same url → 0 (stale), url + unique query → 1 (true), with
   `cache:'no-store'` on the request AND `cache-control: no-store` on the response.

So the client ignored both directives. Some client, proxy, or middlebox always will — which means
**a page whose correctness depends on a fresh read must carry that in the url itself**. `getJSON`
in `shelf.html` now appends a unique token. Both fixes stand: the header because it is correct for
every client, the url because the guarantee has to reach the reader regardless.

`api.serve()` was split into `build_server()` + `serve()` so a test can bind port 0 and check the
real wire — `tests/test_no_stale_reads.py` (3 tests). A dispatch-level test would have passed for
as long as the wire stayed silent.

---

## 2026-07-29 · C1d — a link becomes a card with a waybill · and THE EXPERIENCE LAYER

**`linkdrop.py`.** A member drops a URL; we open it once in the airlock, write down what is true
*about* it, and throw the bytes away. The waybill is a closed list — address, the page's own
`<title>`, content type, `bytes`, `sha256`, `fetched_at`, `status` — and `no_page_bytes_kept()`
checks against that list rather than against a remembered set, so a later hand cannot add `excerpt`
and quietly turn a pointer into a copy. An attributed `quote` is allowed and capped; unattributed is
refused. The `body` is still required — a bare link is not curation.

**The fetch is the dangerous part**, and it is guarded as such: a member-supplied URL fetched by our
server is an SSRF primitive. `_safe_target` refuses non-http(s) schemes, credentials in the URL, and
any host that *resolves* to loopback/private/link-local/multicast/reserved — every address the name
returns, not just the first — and redirects are followed by hand so each hop is re-checked. Verified
through the live page: `127.0.0.1:8099/keep.json`, `169.254.169.254` (cloud metadata),
`file:///etc/passwd`, and `localhost` were each refused with the rule they broke.

**No embed, by design.** An iframe or remote image would hand the reader's IP, user-agent, and
referrer to the provider the instant the page painted. This library promises nothing records who
read what; we cannot make that promise and then place a beacon. A link renders as a card with its
waybill and a plain link, and `EMBED_POLICY` says so in the payload so no client has to guess.

**`present.py` — the experience layer** (Matt, mid-build: *"We want our card to be bare, but we want
the user experience to be a bit magical, so we can take the cards and add an experience layer on top
without slowing the process down too much."*). Cards hold facts; presentation holds phrasing, and
the two never mix. `derive(card)` returns a separate block — glyph, kind label, who, "3 minutes
ago", standing, provider name, a readable waybill line, who vouched and why — and `attach()`
shallow-copies each card so the store is never touched. A test reads `drops.jsonl` **as bytes** and
fails if any presentation field is in it.

Pure functions, no I/O, cached on `(id, updated_at)`. Two bugs of my own, both caught by my own
tests: `derive({})` returned a block of plausible defaults ("A member of the Commons", "on this
member's shelf") for a card that said neither — invention, now silence; and the cache collided for
two different cards sharing an id with no `updated_at`, so a versionless card is no longer cached at
all. Correctness before speed.

Verified on a real fetch (Project Gutenberg): waybill 24,270 bytes + sha256 + status 200, page title
taken, provider named, `looked at just now · 24 KB · fingerprint b577fb153136…`, quote attributed,
and no page text anywhere in the card.

---

## 2026-07-30 · TRAFFIC, measured — who is actually using this

Read from the Caddy access logs on the box (127,377 requests across api/site/tv), not guessed.

**The dominant reader is an AI agent, by a wide margin.**

| who | requests | share |
|---|---:|---:|
| **ClaudeBot** | 44,439 | 35% |
| SemrushBot (SEO crawler) | 26,894 | 21% |
| real browsers | ~20,725 | 16% |
| GPTBot | 2,203 | 2% |
| no user-agent | 5,252 | 4% |

**What is used** (status 200 unless noted): `/card` **46,190** · `/search` **16,210** ·
`/encyclopedia.html` 4,037 · `/keep.json` 3,879 · `/mcp` **3,037** · `/canon.html` 2,899 · `/` 608.
The card permalink is the single most-used thing this project has built, and search is second. Both
were built for agents to cite; both are being used that way.

**The MCP surface is being INDEXED, not just called.** `/mcp` callers: SentinelOracle liveness prober
(1,398), python-httpx (875), node (240), undici (121), Bun (64), agent-tools.cloud-crawler (61),
**MCPScoringEngine (50)**. Agent registries are discovering and scoring us.

**Volume stepped up hard on 2026-07-27**: 26.6k · 30.2k · 14.8k · 11.0k per day, against ~1k/day the
week before.

**Health:** 217 × 429 (rate-limited `/search`), 18 × 502 on `/card`, 8 × 502 on `/search` — small but
real. 37,052 × 404 (29% of all traffic) is almost entirely hostile scanning (`.env` ×112 and 8 more
variants, `.git/config` ×63, `.aws/credentials` ×36, `phpinfo.php`) — correctly refused.

### ~~FINDING — 246 live cards carry a literal placeholder in their title~~ — **RETRACTED, I WAS WRONG**

**`_xxx` is the Roman numeral XXX.** `§aur_07_xxx` is *Meditations* Book 7, section 30. All 246
verified: the tail after the section number is a Roman numeral every time (`i`, `xxxi`, `xxxiii`,
`xxxix`). And the "titles truncated mid-slug" were my terminal truncating a search snippet — the
real count of titles ending mid-token is **0**.

There is no defect here. The titles carry a structured citation (work · book · section), which is
the provenance discipline this project is built on, working as intended.

I concluded "placeholder" from a SUBSTRING — the exact error
[[feedback_science_math_is_the_core_2026-07-08]] exists to forbid ("never conclude 'no science' from
a substring"), and I made it while reporting confidently with numbers attached. The measured facts
below were right; the interpretation was not. The one thing worth carrying forward from it is a
**polish** item, not a defect: `§aur_04_xxxviii` is honest but unreadable, and `Meditations 4.38`
would serve a reader and an agent better. Low priority, and NOT the top of any list.

The original claim, kept because the record is append-only:

> ~~The search log is not human queries. It is crawlers searching **our own card titles**, which is
> how this surfaced... **246 titles contain `_xxx`** — a placeholder marker that shipped.~~

The search log is not human queries. It is crawlers searching **our own card titles**, which is how
this surfaced: the top "searches" are strings like `Aurelius, Meditations §aur_07_xxx` and
`Augustine, Confessions §aug_conf_`. Measured against the live corpus (548,585 cards):

- 246 titles contain `_xxx` — **all 246 are the Roman numeral XXX**, verified.
- 2,177 titles carry a `§slug` — a legitimate work·book·section citation.
- The "truncated" titles were a search-snippet artifact in my terminal; real count is 0.

What IS true and useful from this: the search log is not human queries — it is crawlers reading our
own card titles back to us. That tells us titles ARE the product for our largest audience, which
makes readability (`Meditations 4.38` over `§aur_04_xxxviii`) a real if minor improvement.

### NOT ATTRIBUTED — 784 requests to `/card/null` and `/null`

`Sec-Fetch-Dest: image`, 781 of 784 on narrowhighway.tv, referred by our own card pages and
`characters.html`. But the served HTML contains **no** null-valued `src`/`href`/`content`, and
`render_card_html` emits none when given null connections. So it looks like ours and I cannot yet
show that it is — a browser extension or preview crawler injecting a null image is equally
consistent. Recorded as unattributed rather than claimed as a fix.

---

## OPEN — logged because unfinished is a fact, not a silence

- **Operational carding** (task #104): shards, nodes, curators, sources, deploys, SOPs each get a
  card in the keeping — "cards on every piece". Not started.
- **Deploy completeness guard**: nothing yet proves every `src/concordance/*.py` on the droplet
  matches the repo; `corpus_db.py` was missing for days under a green gate. A manifest for src,
  mirroring `tests/MANIFEST.txt`, would close it.
- **Private key on the wire**: 5 endpoints still accept `private_key` inbound (contract §3/§5).
  Mesh messages were fixed via detached signatures; **§5 is NOT done** — do not claim it.
- Overall test coverage 52% (kernel ≥90). Worst user-facing module: almanac 20%.
- **Stale-read sweep across the other pages.** `shelf.html` now busts the cache in its own
  `getJSON`; every other page has its own copy of that helper and does NOT. Any page that reads
  after a write on the same url can show a stale answer — `community.html` (groups, contributions),
  `mesh.html` (inbox, doors), `journal.html`, `walk.html` are the read-after-write candidates. The
  right fix is one shared helper rather than eight copies. Measured on one page; NOT yet measured on
  the others, so this is a suspicion with a mechanism, not a finding.
- OneDrive drag on the working copy; nav single-source; manifest counts.

## 2026-07-31 · The 4,743 citations that resolved to nothing

**What was wrong.** 2,619 cards cited `/encyclopedia.html?ref=X` — a 1,000-byte `noindex`
JavaScript stub, and the #1 page in the access log at 4,209 hits. 2,124 cited `/canon.html?ref=X`,
which was 3,020 hard 404s on the witness host and, on the secular host, a 301 to `/bible.html` that
**dropped the `?ref=`** — the reader landing on a generic Bible page with the reference silently
gone. The second failure is the worse one: nothing reports it.

**What measuring changed.** The plan was one rule for the canon citations: send them to the card
permalink. Measuring split them. 468 name a real passage ("Revelation 5") — the Word can show that.
1,656 name an internal slug (`aurelius_aur_07_xxiii`) that no page has ever resolved, and for those
**the citing card IS the passage**: Aurelius §7.23 is the body of that card. Pointing its source at
its own permalink would close a circle — a provenance chain whose evidence is itself. So the URL is
cleared and the label kept. Checking first showed this erases nothing: `source.ref` already holds
`aur_07_xxiii` beside the label, so the reference and the authority both survive.

| n | citation | now |
|---:|---|---|
| 2,619 | `/encyclopedia.html?ref=Slave` | `/characters.html?search=Slave` — the Dictionary entry, with its verses |
| 468 | `/canon.html?ref=Revelation 5` | `/bible.html?ref=Revelation 5` — the passage itself |
| 1,656 | `/canon.html?ref=aurelius_aur_07_xxiii` | no url; the label and `ref` stand alone |

**The half that was nearly missed.** After `data/cards.jsonl` was repointed and the services
restarted, the codex cards served the new citation and the dictionary and classics cards still
served the old one. **24 shelves are FROZEN** — their bodies ride SQLite shards and are rehydrated
on read, so the shard's copy is what a reader gets. 4,039 of the 4,743 were still broken, and a
check that only read the file would have reported the job done. The shards were updated in place
(a full rebuild wants ~2.7 GB on a box with 3 GB free), with both services stopped first because
the server opens those files `immutable=1` — a promise that they do not change underneath it.

**Verified live**, not inferred: `/characters.html?search=Slave` on .org opens Easton's entry for
Slave; `/bible.html?ref=Revelation 5` opens the chapter; the Aurelius card page shows
"Marcus Aurelius, Meditations (c. AD 170) · aur_07_xxiii" with no link at all.

**Still open for Matt:** on the secular surface `/characters` answers `gate_closed`, so a reader
following one of the 2,619 citations on .com meets the Gate — while the cards themselves are
public there. The content is published and the page that shows it is gated. That inconsistency is
a decision, not a bug, and it is his to make.

## 2026-07-31 · The Gate holds the deeper reading, never the text

Matt: *"I think seeing them is fine. Understanding the deeper meaning comes after the gate."* ·
*"We don't need to refuse use. We refuse abuse."*

The Gate held twenty paths, and fifteen of them were the text or its reference apparatus. A reader
on the secular surface who asked for John 3:16 was handed a door. A reader who followed one of the
2,619 citations to the Bible Dictionary met `gate_closed` — while the cards those citations live on
were public on that very surface. We were publishing the content and gating the page that shows it.

**Out from behind the Gate (seeing):** `/passage` · `/original` · `/canon` · `/character` ·
`/characters` · `/cross_refs` · `/tsk` · `/word_study` · `/word_occurrences` · `/resolve` ·
`/places` · `/harmony` · `/timeline` · `/backmatter` · `/study_find`

**Still after the Gate (understanding):** `/commentary` · `/prophecy` · `/seeds` · `/narratives` ·
`/teachings` — exposition and the tracing of meaning. Not withheld because it is precious;
withheld because it only lands when it is sought.

The refusal text changed too. It used to say "The Word opens as you seek it". It now says
"**The text itself is already yours**" — because that is now true, and a refusal that does not
name what IS available reads as a locked door.

**Abuse is still refused**, by the instruments built for it: the rate ceiling (600/min read,
120/min write), the named crawler refusals in robots.txt, the operator token, the steward warrants
with their terms, the moderation floor. A gate is a poor instrument against abuse and a very good
one against the curious.

The line lives in one place now — `api.AFTER_THE_GATE` — and a test walks the code to prove no
path drifts across it in either direction. Fifteen tests encoded the old rule and were rewritten,
not deleted: each now asserts the opposite, with the reason written beside it.

**1,037 tests. Verified live on .com:** all fifteen answer; all five still wait; and
`/characters.html?search=Slave` opens Easton's entry for Slave with its verses.

## 2026-08-01 · THREE INSTRUMENT FAILURES, RETRACTED IN THE OPEN

**1 · Every traffic figure quoted 2026-07-30/31 was measured on 9% of traffic.** `site.access.log`
and `api.access.log` are permission-denied to the deploy user; `cat /var/log/caddy/*.log` silently
read `tv.access.log` alone and the subset was reported as the whole. Corrected, full logs + ten
rotated archives (865,371 requests, 2026-06-02 → 2026-08-01):

| host | requests | share | IPs | human | ClaudeBot | SEO |
|---|---:|---:|---:|---:|---:|---:|
| narrowhighway.com | 749,040 | 86.6% | 16,624 | 80.6%* | 3.0% | 9.4% |
| narrowhighway.tv | 77,950 | 9.0% | 1,487 | 5.0% | 28.6% | 34.5% |
| api.narrowhighway.com | 38,381 | 4.4% | 830 | 32.3% | 58.2% | 0% |

*"human" on .com is inflated: ~64% of .com is machine polling with plain user-agents (see 3).
Retracted claims now corrected in code and docs: "ClaudeBot is 35% of traffic" (it is ~7.7%
site-wide); "/card at 46,190 is the front door" (that was .tv; full figure ~39k, and `/` reaches
2,318 distinct IPs — the widest genuine audience); "SemrushBot 21% of ALL traffic" (34.5% of .tv);
"134 429s ever" (441: 313 ClaudeBot, 128 Python-urllib on the verify paths).

**2 · "19 of the Codex's 20 receipts answer 404" was false — the test was broken, not the seals.**
The URL list was written with Windows line endings; every curl got a `\r`-suffixed URL, failed with
code 000, and the failure was printed under a hardcoded "404" label. All 20 resolve; all 321
seal-claiming cards on the box have their objects. The 16,146 receipt 404s in the log are 1.0-era
`/s/` URLs crawled by bots on the retired .tv host — zero overlap with either CAS. The
receipt-as-card build keeps its structural justification (data/cas is node-local, 127 seals lived
only on the operator's machine) and loses its false one, in the code comment itself.

**3 · "The canon 404s are on the witness host" — they were on .tv.** And `.org` was never zero
traffic: its vhost had NO log directive, so absence of instrumentation was reported as absence of
visitors. Fixed 2026-08-01 — `.org` logs for the first time (org.access.log; the first reload
failed on file permissions and was completed after pre-creating the file caddy-owned).

**Also found while correcting:** ~480k requests on .com are 1.0-era consoles still polling dead
endpoints (`/api/testimony/matters` 35,800 · `/misalignments` · `/inbox` · `/robot/all` ·
`/keep/insights` — none exist in 2.0) from a handful of operator IPs, chiefly 107.127.49.124,
107.119.65.17, 129.222.255.28. The 2.0 Keep (`/keep.html` + `/keep.json`) is live and answering;
the stale clients are on the devices, not the server.

**The rule this buys, now in memory:** a measurement that can silently cover a subset must report
its own coverage — file list, row count, date window — before any conclusion is drawn from it.

## 2026-08-01 · THE TWO KEEPERS — the library lives on .com, the record lives on .org

Matt: *"We could also make the .org keep the receipts."* Done, and verified from the far side:
a seal minted through the SECULAR door now carries `cite_url: https://narrowhighway.org/s/…`,
and the witness serves it. Cards still canonicalize to `https://narrowhighway.com`. The system
half-believed this before the change — witness-minted seals already named .org; now the record
has ONE keeper whichever surface mints. Old sealed records carry .com cite_urls inside hashed
content — unrewritable by construction, still resolving on every door. Badges follow the same
rule: a badge is a record.

This gives .org its job without waiting for traffic: **the witness keeps the testimony.** Every
receipt any reader or agent ever cites now points at .org by name — reach that grows with every
verification performed.

## 2026-08-01 · THE LLM LEAVES THE DOORS — disabled on the box, moved to the ark

Matt: *"Disable and move the LLM to the external hard drive."* Measured first: zero references to
Ollama anywhere in the codebase; qwen2.5:3b + nomic-embed-text sat on the box for seven weeks,
enabled and never once called. The serving path is deterministic by design — the Gate classifier
is word-lists, the engine verifies and never generates — so there was never a seat for it at the
doors.

Executed with the ark rule: store tarred on the box (2.1 GB), pulled to
`D:\NarrowHighway-Backups\ollama\2026-08-01-box-models\`, sha256 `010325dd…` verified byte-for-byte
on both sides, THEN removed from the box. Service disabled and inactive; binary left in place (one
command reverses). Box disk: 4 GB freed, 55 GB available.

The model's future seat, assigned by standing doctrine, not improvised: **the MINT** — at build
time, on the dedicated workshop machine, embeddings may PROPOSE connection candidates; the assay
disposes; nothing generative ever serves. The fleet now matches its names: the DOORS serve, the
MINT makes, the ARK remembers.

---

**2026-08-26 — Phase 0, honesty debt §5 (private-key-on-the-wire): RESOLVED.** The punchlist claim
"5 endpoints accept `private_key` inbound" was stale — zero do (the AST guard already passes; the
five handlers were retired in 4a86cf8). The two `test_no_keys_on_the_wire.py` failures were a stale
expectation from before the signed-posts policy (9ea6d93); updated to the shipped behavior (unsigned
refused, crisis-exempt) — file green (5/5). Metric: that honesty debt closes; a directive/addendum
misdiagnosis corrected. Held open: the contract §5 DONE line is frozen — its strike is the operator's,
flagged in PUNCHLIST §4.

**2026-08-26 — Phase 0, corpus-dependent tests skip on a clean clone: DONE.** Measured against a real
clean clone (a local shallow clone = committed state only, no generated keeping): 48 failed / 1675
passed / 27 skipped — matching Fable's count. The honesty check (running the 19 failing files WITH the
corpus present) split them: 16 files pass with data → genuinely corpus-only → guarded; 3 tests fail
even with data → real reds, fixed not skipped (`test_site.py` ×2 = self-contained pages added this
session undeclared in its way-home/palette checks; `test_present.py` ×1 = stale allow-set missing the
`gate_record` provenance field). `tests/conftest.py` gained `_CORPUS_DEPENDENT` + a collection hook that
skips those 17 files with a stated reason when their data is absent. Result — clean clone: 1554 pass /
196 skip / **0 fail**; box (data present): they run and pass. Metric moved: a stranger's clean clone now
reports 0 reds, and 3 genuine reds (that would have failed the box gate too) are fixed. Held open: the
whole-file granularity over-skips the non-corpus tests in those files on a clean clone (acceptable, noted).

---

**2026-09-02/03 — "All 3": the Console joins the Deck, and the ranker learns substance from headword.**
Two of the three items from Matt's mandate ("an agent that never forgets a conversation... focus on
Console and Ranker... anything started needs to be completed and connected"), the memory-continuity
work being the third and standing.

*The Console (`9fbb605`).* `/console` spoke every utterance and forgot it instantly — no `thread_id`
in or out, so `threads.py`'s own keystone never reached the voice door, only `/ask`'s typed-chat door.
`web/api.py`'s `/console` handler now mirrors `/ask` exactly: creates/resumes a thread, appends the
exchange, runs `recall.land`/`remember`, off to the side so a deck-write failure never breaks the
spoken answer. `site/coach.html` carries the same `nh_tid` localStorage key `index.html` already used,
so a member who types on `/ask` and later speaks to the Console is in ONE conversation, not two silos.
Live-verified: two `/console` POSTs of "John 3:16" returned the identical `thread_id`, second call
`landed` on the card the first one promoted. A first draft duplicated `coach.html`'s functionality in
a new `console.html` before this was caught (`rm`'d, never shipped) — look-before-you-build held.

*The ranker (`32ed21a`).* docs/HANDOFF.md's own #1 open item: the subject-tier partition in
`corpus.Corpus._score` could tell "about this" from "not about this," never a thin gloss from a real
excerpt — and ~67% of the keeping are stubs (`ops.STUB_BODY_CHARS`). Added `SUBSTANCE_WEIGHT = 2.0`
next to `SUBJECT_TIER`/`THEORY_WEIGHT`, applied to the BASE score before the tier addition so it only
ever reorders cards WITHIN a tier they already earned — a boosted stub cannot cross into the tier
alone. New `tests/test_retrieval_invariants.py::test_VII`; all six prior invariants plus 100 other
tests across `test_corpus`, `test_graph`, `test_decks`, `test_wayfind`, `test_ask`, `test_growth` pass
unchanged (every existing fixture uses sub-threshold bodies, so the new signal is a true no-op there).
Deployed, live-verified against production search. `systems.py`'s self-report for `keeping` was then
stale by construction — it still called the fix "unsupported" — corrected in the same sitting
(`32e5a36`) rather than left to drift; `"degraded"` itself was deliberately left standing since the fix
is unit-pinned but not yet measured against real query quality at scale (no `live_passes.py` re-run).

**Found in passing, not fixed here:** running the entire 219-file suite in one `pytest` invocation
(not per-file) fails `tests/test_ask.py::test_a_greek_word_study_can_be_said_tongues_woven_into_the_word`
— confirmed identical on a clean baseline via `git stash`, so pre-existing and unrelated to either
change above. Root cause found and a fix begun independently (a second, concurrent local session, per
Matt's own click on the flagged task) in `tests/test_bible.py`: `CONCORDANCE_STRONGS_DIR`'s target
module reads that env var into a MODULE-LEVEL constant once, at import time, and pytest imports every
test file during collection before any test runs — so whichever file's import happened to trigger the
`strongs` module first "won" the env var for the whole process. Uncommitted as of this entry; the next
session should check `git status` on `tests/test_bible.py` before assuming it needs (re)work.

Metric moved: Keeping's `/systems` self-report `supported.unsupported` went 1 -> 0; its `handicap`
4 -> 2 (uncommitted numbers reflect the box, re-verify via `GET /systems` rather than trusting this
line). Held open: the ranker's real-world lift is unmeasured; Find's pull-selection quality; the
subsystem-mesh thinning (scripture/prophecy/witnesses); the surfacing decision (Gateway/grid/Floor/
atlas); the test-order-dependency fix (in flight, see above).

---

**2026-09-03 (Opus) — the ranker's real impact, MEASURED; a live defect found and fixed; and the
OT→NT witness woven into a passage study.** "Review everything; anything open is yours."

*Measured the ranker (the prior handoff's #1).* `tools/ask_probe.py` against production: **25/25** — the
front-door voice routes every probe correctly (practical how-tos lead with a field card not a theory,
crisis stays crisis, compute computes), and `SUBSTANCE_WEIGHT` caused no regression. But the probe
tests *routing*, not the substance-vs-headword facet, so I measured that directly — and it exposed a
real, still-live defect: **every single-word subject lookup led with a phonetic string.** "gravity"
returned `G R AE1 V AH0 T IY0` (a 186-char pronunciation card) ahead of the definition, Newton's law
(1032 ch), and general relativity (1417 ch); "baptism" led with ARPABET over a 3,801-char article.
Cause: a pronunciation card's title IS its headword for all ~125k of them, so it won the exact-title
9x boost on any bare word, and its CMU boilerplate clears `STUB_BODY_CHARS` so `SUBSTANCE_WEIGHT`
couldn't catch it — a genre problem, not a length one. Measured, not believed: I pulled the real card
bodies over the wire before judging.

*Fixed (`a525611`).* The pronunciation shelf is withheld from the exact-title boost — an index
collision is not evidence of definitiveness, the way a verse card titled "Philippians 4:13" is. The
six live lookups that led with phonemes now lead with the definition (or a substantive theory card);
ask_probe holds 25/25; pronunciation stays admitted (leads when it's all we hold, and surfaces via the
pronounce/word-study door). `test_VIII` pins both directions. `systems.py` + the keeping SOP updated
(`5727c7d`): BOTH ranker facets are now closed and deployed; `"degraded"` stays for one honest reason —
the ~67% stub STOCKING gap, a growth question, not a scoring one. Flipping it wants a scale re-measure,
not a commit.

*Wove the OT→NT witness into a Scripture study (`25d0932`) — the prior handoff's #3, done as real
composition.* `prophecy_fulfillments.for_ref()` and `GET /prophecy?ref=` already held the data
(messianic.jsonl) but were reachable only by asking about prophecy as a topic — never woven into a
passage study beside the cross-refs, commentary, and cloud that already were. Now studying an OT
passage the New Testament itself takes up surfaces those fulfillments (verdict CONCORDANT, Scripture's
own witness, attributed): Isaiah 53 → Matthew 8:17 / Luke 22:37 / Acts 8:32 / John 12:38; Micah 5:2 →
Matthew 2:6; Psalm 22 → the passion. **Self-gating** — John 3:16 and Philemon add nothing, so it shows
exactly where the cross-Testament connection actually exists. Wired on BOTH reader surfaces (the `/ask`
answer on `index.html`, the `bible.html` study desk) and **live-verified visually on `.org`** — the
"Taken up in the New Testament" block renders for the reader, each pairing with its citation beneath.
`test_a_messianic_passage_study_carries_its_new_testament_fulfillments` pins Isaiah 53 carries it and
Philemon does not.

*Docs kept honest:* `docs/THE_MAP.md` gained a SUPERSEDED banner (its Aug-1 numbers have drifted; WORLD
/ HANDOFF / the live endpoints are the truth). `find_verifier` checked: it appears only in a `check`
tool description string in `mcp/server.py` with no handler there, yet `mcp__concordance__find_verifier`
is in the runtime tool list — an unresolved ambiguity, left alone rather than guess-implemented or
guess-removed; flagged for verification.

Metric moved: Keeping's ranker is fully closed (2 facets); a single-word lookup now answers with
substance, not phonemes (6/6 live); the scripture/prophecy/witnesses cluster gained a real weave that
reaches the reader on both surfaces. Held open (needs Matt or is corpus growth): flipping Keeping off
degraded (a stocking/growth process + scale re-measure); Find's pull-selection quality; the *original
words* half of the scripture weave; `.tv` (resources); the surfacing decision (Gateway/grid/Floor/
atlas — which door first); founders gather; OT→NT full sweep; verifier coverage ~52%; off-site backup;
`find_verifier` verification; the test-order-dependency fix (a separate session — `tests/test_bible.py`
is still modified-but-uncommitted in the working tree as of this entry, origin unchanged; left
untouched, re-check `git status`/`git log` before touching it).

---

**2026-09-03 (Opus) — THE AUTOMATON: a witness who faced your situation testifies in his own words
(`37d2e49`).** Matt: "Automaton. give me that." The hall of the .tv museum, and the purest live demo
of strength #1 (real sourced words, never generated, points past itself) — a museum of TRUE testimony,
never a hall of talking deepfakes. `src/concordance/automaton.py` composes `witness.py`'s strict,
fail-closed public-domain cloud: bring a situation, ONE figure emerges who faced it and testifies with
his real, cited PD passages. `GET /tv/automaton?seeking=&witness=` (read-bucket rate-limited),
surfaced as "The Hall of Witnesses" on `site/tv.html` (blockquote + citation per passage; "also in the
hall" re-consults a named witness). The load-bearing law made STRUCTURAL — it TESTIFIES, never
IMPERSONATES; `test_automaton.py`'s key test proves a non-PD witness is voiced by nobody even when his
words match best. Honest-empty on a miss; the frame names the figure so it reads as testimony you are
reading, not a voice speaking TO you; points past itself (Heb 12:1-2). Live-verified visually on `.tv`:
"I am weary…" → Spurgeon (Around the Wicket Gate); "I am afraid and doubting" → Ellen G. White (Steps
to Christ, cited to p251/p7) — both gathered witnesses surface by situation; a nonsense query returns
the honest empty. Cloud today: 385 PD passages, 2 witnesses; it fills as the gather runs. Box == repo
at 212 modules. Held open: gather more witnesses (demand-driven, never generation); the two PRE-EXISTING
reachability reds (`/days /journal /harmony /timeline` unreachable; `com.html`/`steward.html` orphan
pages) confirmed by stash-baseline to predate this and unrelated — part of the ~52-orphan triage.

---

**2026-09-05 (Opus) — WIRE IN EVERY ASPECT: reachability green, both interfaces (`03a9322`).** Matt:
"make sure all aspects are wired in for the agent and human interface; if obviously a future standalone
project, hide it from navigation but leave it on the nearest page." Used `tests/test_reachability.py`
as the grounded instrument (every route reachable-or-declared, every page linked-or-declared) and drove
its two reds to zero, honestly:
- **A broken promise found and fulfilled.** `_SITEMAP_PAGES` listed `/harmony.html` and `/timeline.html`
  and the index copy promises "timelines," but the pages did not exist — the clean URLs 301'd to
  `/bible.html` (stale dead-link redirects). Built both as self-contained scripture viewers (modeled on
  `prophecy.html`) over the live `/harmony` (97 events, gospel columns) and `/timeline` (100 events, one
  spine; disputed dates carry both reckonings, marked). Linked from the Bible study-desk nav (bible.html),
  OFF the main witness nav — exactly "leave it on the nearest page." Removed the two shadowing redirects
  so the pages serve (`/harmony.html` → the page, `/harmony` → the JSON route, coexisting like prophecy).
  Live-verified: both 200 with their own content; the timeline renders events + dates + DISPUTED tags on
  `.org`.
- **The orphan Steward wired.** `steward.html` (household money — shows, never moves money) was built but
  linked from nowhere; now on the `.com` footer (money on the business face) → reachable.
- **Declared, with reasons, what is genuinely agent-flow or a homepage** (not hidden to dodge the check):
  `/days` + `/journal` — personal keeping-flow POSTs carrying client data (a note; thread ids that must
  stay out of query strings), reached by the coach/keeping flow, human dashboards a FUTURE standalone
  project (sibling `/journal/dates` already declared) → AGENT_ONLY. `com.html` — the LIVE `.com` homepage,
  served at `/` by `home_for()`, invisible to the static href-checker (same limit as checkit/about) →
  UNLISTED_PAGES. Dropped the dead `/journal.html` sitemap entry.
Reachability + site + clean-url suites green; box == repo at 212 modules. Held open (genuinely future,
now honestly reachable-or-declared, not hidden): the human dashboards for `/days` + `/journal`; richer
interactive Harmony/Timeline; the broader ~52-orphan surfacing triage; `tests/test_bible.py` still the
other session's in-flight work, untouched.

---

**2026-09-05 (Opus) — BOX RAM CLEANUP + seed-1 lands Matthew Henry.** Matt: "do a clean up to ensure we
have maximum ram" (confirmed target: the production box, its only purpose is the site). Grounded review
found the RAM was almost entirely the two serving processes (~4.8 GB), and TWO real issues:
(1) `CONCORDANCE_FREEZE_SHELVES` was EMPTY — the whole corpus loaded fully resident in both processes,
the memory-efficient shard design switched off; and (2) the shards were month-STALE (551k cards, built
2026-07-29) vs the live 673k — so freezing couldn't be switched on safely (121k cards would serve as
empty stubs). The fix converged with seed-1: complete Matthew Henry (`migrate_commentary` re-fetched the
~892 missing chapters from the PD helloao source → store 269→1166 chapters; `card_commentary_verses.py`
re-carded → 47,152 commentary cards, **MH 1,347→4,124, avg body 1,882 chars — substance**), upload the
new `commentary_verse_cards.jsonl`, then **rebuild the shards** (`build_corpus_db.py`, safe while serving
since freezing was off so the live procs don't read shards; 6 GB swap as insurance) → fresh 687,344-card
shards including MH, and **enable freezing** + staggered restart (witness first, per discipline).
Verified live: rehydration serves FULL bodies (MH Genesis 1:1 = 10,383 chars, Genesis 50:20 = 5,944 —
a previously-missing chapter, so **MH is complete and live**), all three surfaces 200, both frozen.

Safe hygiene alongside: swap 2 GB → **6 GB** (rebuild can't OOM); journald capped 150M; deploy-rollback
pruned to 3; multipathd disabled (single-disk VPS). Result: **available RAM 2.4 → 3.3 GB**, **swap
un-swapped** (2.7 GB churn during the rebuild → 129 MB, 5.9 GB free), fresh complete shards, MH landed.
HONEST metric: +0.9 GB available. seed-1: Matthew Henry `complete` — one PUNCHLIST #5 module done.

**SAME DAY, follow-up — the freezing was SILENTLY OFF; found by measuring, fixed in code (`b3e3d56`).**
Matt: "I can always upgrade the server, but I want to purposefully make it as efficient and compact as
reasonable." Pursued `keeping-2` and measured the resident cost directly (the `/health/memory` estimate
is broken — it reports 15 GB for a 2 GB process): the hog is **card stubs ~1.9 GB (connections ~449 MB)
+ token index ~375 MB**, NOT the bodies. Then the root cause surfaced: even with `CONCORDANCE_FREEZE_SHELVES`
set and shards present, `corpus.frozen_shelves()` returned EMPTY — because `corpus_db.available()` reads a
SEPARATE env var, `CONCORDANCE_CORPUS_SHARDS`, which was never set → `available()` False → the whole
corpus loaded resident (~3.5 GB/proc) with freezing silently off. One env var quietly disarming the other.
FIX: `corpus_db._shards_dir()` now falls back to `<CONCORDANCE_DATA_DIR>/shards` (where `build_corpus_db`
writes them), so the lean design is discoverable from the data-dir alone; explicit override still wins;
still None where no shards exist. `test_corpus_db.py` pins it. Removed the redundant box env var and
PROVED the fallback live: `available()` True, both procs frozen (`frozen_shelves`=16), PSS ~1.9 GB, full
bodies rehydrate (MH Psalm 23:1 = 15,607 chars), both surfaces 200. A fresh box now runs lean by default
(sovereignty: the whole ark, carried in the pocket). Deeper compaction is `keeping-2` (frozen-shelf FTS
search to drop the ~375 MB resident index; compact/lazy stubs+connections ~449 MB) — real, not yet done.
Box config note: the completed MH store + rebuilt shards + the `FREEZE_SHELVES` env are box-side
(gitignored); the code fallback + tests are in git.

## 2026-10-03 — the two guards: the live assay with a ratchet, and the restore drill

**The live assay** (`tools/live_assay.py`, 39 probes in `eval/live_probes.jsonl`, nightly 05:10 UTC via `nh-assay.timer`,
results in `/home/nh/backups/assay/<date>.json`, the floor in `floor.json`, one line per run in `assay.log`). First run,
21:12 UTC: **36/39 passed in 14.1 s; floor 36; regressed none.** The three failures are the three `known_miss` probes —
the assay's want list: a wrong constant in km/s gets no verdict (R4), a lookup fact does not reach CHECK (R5), the
Egyptian chart does not lead "what did the egyptians believe about judgment after death" (narrow terms by design). A floor
probe that fails on a later night exits 1 and logs REGRESSED; recall may only rise. No alert webhook is set on the box
(`CONCORDANCE_ALERT_WEBHOOK`): the log and the exit code are the signals until one is.

**The restore drill** (`tools/ark/restore_drill.sh`, monthly on the 1st 05:30 UTC via `nh-restore-drill.timer`, one line per
run in `/home/nh/backups/restore-drill.log`). First run failed honestly on four "unparseable" lines that were the `#`
comment header of `dictionary_supplement.jsonl`; the drill now skips comments and measures the copy against the live
keeping (only a line the copy lost or broke fails it). Second run, 21:15 UTC, **DRILL OK in 36 s**: `nh-2.0-data-20261003-030001.tar.gz`
sha256-verified, restored to scratch, **integrity OK — ledger 748/748 verified, 1,854 CAS records re-verified** against the
restored keeping, 1,044,475 jsonl lines parsed (live 1,044,912 — the keeping grew since 03:00), cards 25,087 = live, 748
ledger files. Not in the tar by design: the shards and the acquisitions (they ride the ark and the Storage Box). A backup
is a backup now.

## 2026-10-03 (night) — "go in order": the unit normalizer, fact find, the seal ledger, the hive cutover

- **R4 — the SI unit normalizer** (`verifiers/si_units.py`, 2fbb79c). "The speed of light is 150000 km/s" → BROKEN (converted to
  1.5e8 m/s and judged); "299792.458 km/s" → HOLDS; "J K^-1 mol^-1" → HOLDS; "300000000 kg" → BROKEN (a unit of mass; c is a
  speed, both dimensions named); "furlongs per fortnight" → declined, not judged. A preposition after the number is not a
  unit ("299792458 in a vacuum" checks the bare value). The km/s probe graduated from the assay's want list to its floor.
- **R5 — fact find** (`factfind.py`, c5985ed). When nothing is computable the CHECK door answers in one of three honest
  shapes: a FOUND FACT from the keeping's own sourced table (iron's standard atomic weight 55.845, IUPAC — agrees/disagrees;
  cited, no receipt); on-subject cards only (the title must name the subject); or found: [] with a WANT OFFERED. The keeping
  holds no melting points; "iron melts at 1538 C" says so plainly and offers the want, and stays the assay's want-list item.
- **The seal ledger as a public number** (`seals.py`, GET /seals, 3823021): 755 seals minted since 2026-06-28, 750 of 750
  re-verified by the hourly integrity check, 1,859 sealed records, 992 receipt cards — computed at request time, shown on
  the root creed line, the .com footer and the proof page. `/identity` carries the sha256 of FOUNDATION.md (frozen
  2026-07-25), docs/WORLD.md and HANDOFF.md as served now: a reader hashes their copy and compares.
- **The hive cutover** (c65fcb0). nh-gather.timer (Lighthouse 1.0's API-based generator, $0.15 this month, writing
  devotionals nothing in 2.0 reads) and nh-daily-reading.timer (a psalm rendered into a folder no site serves) are
  disabled. 2.0's own hive — never deployed since it was written on 2026-08-02 — is installed under a 3 GB cap in the
  10:00 slot. First supervised turn, 22:59 UTC: **5 ok, 0 failed, 0 skipped**, 2 min 49 s, 1.4 GB peak, $0.00: watch 10/10
  doors hold; shepherd dug the want list; connections proposed (never sealed); theorymap rewrote site/theories.html;
  grow measured. The psalm of the day now rides `/daily` (Psalm 126 today). The Lighthouse folder is used only by its own
  substrate-backup timer now and is archived whole on the ark.
- Live assay floor: 42 probes. CI: 2208 passed.
- **Hive, second turn** (9fbe51c, 23:07 UTC): the first turn had run its two writing workers in check mode — the hive's own
  `--apply` never reached them. Fixed (apply_argv), pinned. Second supervised turn: **5 ok, 0 failed**, 2 min 33 s, 1.2 GB
  peak, $0.00 — watch 10/10 hold; **shepherd filed 14 options** for open wants from public-domain sources; connections
  proposed; theorymap rewrote the floor; grow: nothing to draw — the keeping is fully connected on this gate. The hive runs
  daily at 10:00 UTC from now on.

## 2026-10-03 (late) — "fix those": the 137 slide's three gaps, and the cardinal bug under them (37f2710)
- **CARDINAL, found while fixing the gaps:** "2 * 2 * 3 = 12" came back BROKEN through the CHECK door. The pair
  extractor took "2 * 3 = 12" out of the middle of the chain and judged a true claim false — the same shape was
  latent in sum ("2 * 3 + 4 = 10" → "3 + 4 = 10"). Sum, product and quotient now take their chain WHOLE and refuse a
  chain that starts after an operator on the same line; a mixed-operator expression is left unextracted — a miss,
  never a verdict. Pinned (12 × 12 × 1000 = 144,000 HOLDS; "2 + 3 * 4 = 14" is never BROKEN) and probed live.
- **The three gaps:** division claims ("72 / 2 = 36", "÷") extract to the mathematics equality verifier ("/ 0" stays a
  gap); number_theory gains `verify_divisor_count` (τ(n), exact, divisors listed) with the audit extractor for "the
  number of divisors of 12 is 6" / "60 has twelve divisors"; "mod"/"modulo" join the word-form arithmetic ("64 mod 9
  is 1" HOLDS). `/original_words` was never a route — the route is `/original` (works on both faces; MCP tool
  `original_words`). The defect was the bare 404: an unknown path now answers `did_you_mean` from the one route
  table plus the catalog (`/original_words` → `/original`; `/verifiy` → `/verify`). A dead end became a door.
- **Base 12, sealed not asserted:** the digital-root chain (doubling mod 9 never lands on 3, 6, 9; 3→6→3; 9 stays;
  64 mod 11 = 9 in base 12; 12 = "10" and 144 = "100" in base 12 — and 10 = "10" in base 10) sealed through POST
  /verify: https://narrowhighway.org/s/7092e2f4d58c4214762cd7400ec062c1cf921a42f50274eeb36e1744b87305f7. A base is
  notation; the divisor count is arithmetic (12 has 6, 60 has 12, 10 has 4 — all HOLD live).
- **Seen, not fixed (chip filed):** `/original` returns only the Strong's-tagged words of a verse (John 1:1: 14 of 17;
  Rev 7:4: 5) — the concordance.db alignment is partial; the route is honest to its data but says nothing of the gap.
- CI green (run 37172770710). Deployed 03:02–03:03 UTC, both faces 200. Live assay: **50/52, floor 45 → 50**,
  5 newly passing, 0 regressed (the two known misses stand). Local full suite on the desktop crawls on the
  OneDrive-synced checkout (two runs starved each other on the shared data files); CI is the full-suite gate.

## 2026-10-04 — the Strong's gap, measured and made visible: a reader is never told 14 words is the verse
- **Measured against the full word tables** (the Lighthouse source still holds greek.db 137,554 words / hebrew.db
  306,785 words, the same tables tools/card_scripture.py carded): concordance.db tags **59,845 of 137,554 Greek words
  (43.5%)** — 3 of 7,927 verses whole, 14 verses with no row at all (Luke 4:19, Romans 1:29-31, 12:12-13, 1 Cor 13:7,
  Eph 5:10 …) — and **300,807 of 306,785 Hebrew words (98.1%)**, 79.3% of verses whole. John 1:1 is 14 of 17 (ἀρχῇ, τὸν,
  θεόν untagged); Revelation 7:4 is 5 of 16.
- **The discordance indicts the method, not the data.** Lighthouse's build_concordance.py read MorphGNT column 5 (the
  NORMALIZED surface form) as the lemma, so a Greek word was tagged only when its inflected form equals a Strong's
  lemma (ἦν → G2258, λόγος → G3056; ἀρχῇ → nothing). The lemma IS in the source (column 6); the fuller greek.db built
  from it maps 98.5%. Second fact: a Greek `word_pos` is the word's line index in its BOOK file (Rev 7:4 starts at 2747);
  a Hebrew `word_pos` is per-verse. Both facts are now stated on `Concordance.verse_words`.
- **Licenses, verified at the source (not from memory):** SBLGNT text — **CC BY 4.0** (sblgnt.com/license; the greek.db
  meta's "EULA, non-commercial" is stale). MorphGNT morphology + lemmatization — **CC BY-SA 3.0** (share-alike, the class
  corpus._DISALLOWED_LICENSE withholds; the Greek Strong's in concordance.db AND greek.db were derived from these lemmas,
  and the greek_nt verse cards carry `extra.lemmas` under a label naming only SBLGNT). OSHB/morphhb — WLC text public
  domain, tagging **CC BY 4.0** (inside the reference-corpus gate PD/CC0/CC-BY; not strict PD). Robinson-Pierpont
  Byzantine Majority Text (byztxt, RP2018) — **Unlicense/public domain, every word Strong's-tagged** — a PD fully-tagged
  Greek NT, but the BYZANTINE text, not the SBLGNT: no PD fill exists for the SBLGNT's words. Tischendorf-data: no
  license stated. No strict-PD Strong's-tagged Hebrew OT found.
- **Shipped — the gap made visible from what is kept:** `/original` (and the MCP tool, and `scripture_for`) now return
  `coverage {tagged, total, untagged_positions, untagged_words, complete, aligned, card}` + `note`. The verse's full word
  list comes from its held verse card (`card_src_greek_nt_john_1_1` … extra.text); tagged words are placed inside it —
  Hebrew by position, Greek by in-order token match (letters only; sigla and punctuation dropped) — proven to give ONE
  constant offset in every one of the 7,913 tagged Greek verses and to align all 23,213 Hebrew verses. Each placed word
  carries `verse_pos`. Where the card is not held: `total: null` and the note says these are not necessarily the whole
  verse. bible.html renders the whole verse in order — chips for tagged words, dashed plain words for the untagged — under
  a coverage line; the console speaks "17 words, 14 of them with a Strong's number", never "14 words". Nothing generated:
  the untagged words are the card's own. Pinned in tests/test_canon_original.py (+9) and tests/test_console.py (+1).
- **Open decision (chips filed):** (a) rebuild concordance.db from the lemma column (98.5%, per-verse positions) — the
  method fix — which changes served Strong's (ἦν G2258 → εἰμί G1510) and occurrence counts, and expands the
  MorphGNT-derived layer under the share-alike question above; (b) the Greek verse cards' license label. Matt's call.
- CI green (run 37204689922, ff6ac17). Deployed 13:12–13:14 UTC, both faces 200, HARD scope box==repo. Live on 8001/8002: John 1:1 14/17 (ἀρχῇ, τὸν, θεόν untagged, verse_pos 0,2,3…16), Revelation 7:4 5/16, Genesis 1:1 7/7 complete, Romans 1:29 and 1 Cor 13:7 0 tagged but the verse shown whole; John 99:99 → total null, never a claim. bible.html verified in the browser: 17 in order — 14 chips + 3 dashed words — under the coverage line.

## 2026-10-04 — Lighthouse 1.0: integrated, not retired (232cc33)
- **The look.** The desktop's hidden python (PID 2080, 18 CPU-hours) was the Lighthouse 1.0 engine — uvicorn on :8000,
  504 routes in 151 families against 2.0's 211 in 121 — started by the `Concordance-API` logon task, kept alive by two
  watchdogs, exposed through the Cloudflared service; the YouTube fast channel (five scheduled channels over a 339 GB
  PD media library on D:) ran beside it and had looped the May 18 schedule for four and a half months from the
  desktop uplink. api.narrowhighway.com already resolves to the box (Caddy → 8002). The Claude Desktop "concordance"
  connector pointed at localhost:8000 — this app was 1.0's last caller.
- **Matt: "instead of retiring it, is there a way to integrate it?" → "agreed."** The one body: fold what 1.0 holds
  into 2.0, make the desktop a 2.0 NODE (camel tier 3), never a second engine. Of the 120 families only 1.0 has, most
  are experiments the constitution refused (swarm, agent/tts/serial-generate/radio-produce = model + ElevenLabs,
  wallet, market) or rebuilt in 2.0 form; 1.0's "61,008 journal entries" are activity events, not content. Augustine's
  Confessions turned out to be IN the keeping already (1,469 lines, §aug_conf sections) — search ranking missed it.
- **Move 1 (the connector + the engine).** `claude_desktop_config.json` (backed up `.bak-20261004`): the 1.0 connector
  replaced by `narrowhighway` = `python -m concordance mcp --surface witness` on the desktop checkout (PYTHONPATH src,
  CONCORDANCE_DATA_DIR data, PYTHONIOENCODING utf-8) — the one kernel, locally, offline-capable; the live box stays
  attached through the claude.ai connector. Its first run died on cp1252 meeting an arrow in the welcome →
  `serve_stdio` now reconfigures stdin/stdout to UTF-8 (pinned). Stopped non-elevated: the engine watchdog, the
  watchdog shell, the YouTube streamer. STILL RUNNING, elevated (Access is denied from this session; three UAC
  attempts came back "canceled" instantly): the engine, its launcher shell, the three task registrations, the
  Cloudflared service. `C:\Users\hdven\OneDrive\Desktop\retire_lighthouse_desktop.ps1` (+ the double-click `.cmd`)
  finishes it; it leaves the YouTube task alone (move 3 is Matt's) and touches no backup task.
- **Move 2 (the Bibles).** 2.0 was English-only (John 3:16 lang=es returned the WEB). `tools/migrate_bible.py --all`
  under the STRICT PD gate: 16 languages crossed on established grounds (ar Smith-Van Dyck 1865, de Luther 1912, es
  RV 1909, fa OPV 1895, fr Segond 1910, he Leningrad, it Diodati, ja Kogoyaku, ko 1910, la Clementina, my Judson, nl
  Statenvertaling, ru Synodal, uk Kulish, vi 1934, zh CUV); 5 HELD with the reason (hi IRV = CC BY-SA; ht unidentified
  edition; pt unidentified; ro Cornilescu contested; sw Kiswahili Contemporary = Biblica) and filed as PD gathers on
  the want list (want_d98918a430ac … want_ce704ae285a5). 177 MB to the box (compressed — the raw transfer crawled at
  45 KB/s). `scripture.bible(lang)/languages()/read_passage(ref, lang)`; `GET /passage?lang=`, `GET /languages`,
  `/capabilities.bible_languages`; MCP `read_passage(lang)` (97 tools unchanged). Live on both faces: 17 languages,
  John 3:16 in es/zh/he/la/ja, an unknown lang names what is held. CI green; assay **54/56, floor 50 → 54**.
- **Move 3 (the television) — Matt's.** Keep the desktop as the broadcast station (it holds the library; costs the
  uplink) or move a curated slice to the box/Storage Box and stream from Hetzner. The streamer is stopped now; its
  task is enabled and returns at next logon or `Start-ScheduledTask`.
- **Move 3 decided (Matt, 2026-10-04): "go with most efficient. We can build out .TV at a later date."** No stream
  now: the YouTube broadcaster task joins the retire script (it re-encoded 24/7 from the desktop uplink, looping the
  May 18 schedule). Nothing is lost for the build-out: the five channel schedules are in the Lighthouse archive on the
  ark (lighthouse-20261003.tar.gz), the 339 GB PD media library stays on D:\library_files, and the HLS producer
  (fast_channel_youtube_live.py) is portable and model-free. The elevated click is still Matt's.

## 2026-10-04 — Gen 3 · 1 — EVERY COPY IS WHOLE: the keeping syncs between nodes (9ceddf4)
- **The charter.** Matt: "what capabilities should a Gen 3 of this project have?" → eight, in order (docs/GEN3_CHARTER.md:
  every copy whole · verifiers as data · a claim grammar · the Word in the reader's tongue · the household keeping ·
  standing by fruit · the engine measures itself in public · the appliance) → "agreed, build in order."
- **Built.** `src/concordance/replicate.py`. Branch side on every node: `GET /sync/manifest` (identity + chain head +
  sha256 of every keeping file, Ed25519-signed; 89 files / 1,287 MB on the box, first call 1.1 s, cached after),
  `GET /sync/ledger?since=H` (the chain after a hash with its bound CAS records; `hashes_only=1` for the common-prefix
  search), `GET /sync/file?name=` (raw, x-sha256, handler-served), `/identity.node`. Node side: `python -m concordance
  sync` over `data/known_branches.json` pinned by hand (`--add-branch`, `--whoami`, `--dry-run`); one pull at a time
  per data dir (`sync.lock`). Explicit ALLOW list of what travels; never the node key, inboxes, profiles, groups, mesh,
  caches, backups. A local-only chain tail is set aside in `ledger-local/`, never deleted. The box's key lives at
  `/home/nh/.config/nh/node_identity.json` (0600, `CONCORDANCE_NODE_KEY_FILE` in .env). Pinned (8 tests, hermetic —
  `cas.store()` mints into the LIVE corpus, a 450-second lesson), probed (4), CI green, assay **54 → 58**.
- **The box is branch `nh_74e58b3581ab1b74e97a0c924e0cf5dc` (nh-engine-1); the desktop node is
  `nh_60aabafec6e4e55d95f446406f9490db` (HarrisMotors).** First catch-up from the desktop: the 122 local ledger
  records were not a prefix of the box's chain → set aside; **776 records + the bound CAS records pulled and the chain
  verified end to end**; 36 keeping files (894 MB) streaming at ~75 KB/s on the desktop line — the proof (a seal
  minted on the box served by the desktop node) follows when it lands. Daily at 23:30: `tools/ark/node_sync.cmd`
  (task "NarrowHighway Node Sync").
- **Found on the way:** the YouTube encoder (ffmpeg) had outlived its supervisor and was still pushing to YouTube — the
  uplink hog — stopped; the retire script now takes it too.
- **PROOF (the charter's own test for #1), 2026-10-04 23:30 UTC:** the desktop node, over stdio, answers `seal_fetch` for
  `7092e2f4d58c4214762cd7400ec062c1cf921a42f50274eeb36e1744b87305f7` — the 13-step digital-root derivation sealed on
  the box this afternoon, weeks after the desktop's last snapshot — byte-identical to the box's `/seal`; the manifest
  probe verifies the signature; the assay floor rose, not fell. The first catch-up died at 31 min on a read timeout
  mid-file (the desktop line) → `/sync/file` honors Range, the node streams and resumes from the stalled byte, smallest
  first (0657a25, deployed); the catch-up of the 894 MB of keeping files restarted with resume in place.
  **Capability 1 is DONE by its own proof; capability 2 (verifiers as data) may start.**

## 2026-10-04 (night) — Gen 3 · 2 — VERIFIERS AS DATA, NOT DEPLOYS (34d73c7) — PROVEN
- **Built.** `verifiers/spec.py`: one generic evaluator runs a declarative spec — a law applied to a claim. The
  expression language is an AST whitelist (numbers, bound inputs, + − × ÷ ** %, lists/indexing, a fixed set of math
  functions; anything else is an ERROR, never run). A check fires when its inputs and the claimed key are present; a
  compute LIST is a set of equivalent forms that must all match (the cross-check `electrical.power` does in code);
  guards name errors; tolerance is the spec's (a caller may tighten, never loosen). **A spec carries its own goldens
  and is refused at load if they fail.** SHADOW: a result a Python module already produced shadows the spec's — a
  spec extends, never contradicts, code; a domain with no module is served by its specs alone. Only admitted specs
  run; the file is re-read on change — a new law runs without a restart. `GET /specs` lists what a node holds;
  `/capabilities.verifiers.spec_checks` counts it; `verifier_specs.jsonl` rides with capability 1's sync.
  `tools/spec_verifier.py` is the operator's door (--check / --admit with a CAS seal / --shadow / --catalog); the
  contributor's door with standing is capability 6.
- **The charter's proof, live on the box.** `eval/specs/electrical.json` re-expresses the electrical verifier as
  data; admitted as data on the box (seal `a47e58944ed7da7652f4ae67159b14e618c19ad85b18eb3fea9c844d2ac44fb2`),
  **no restart**: the shadow run shows *identical verdicts on every check both produce* across the domain goldens
  (true and false packets); the NEW check `voltage_divider` — no Python behind it — answers HOLDS (12 V, 1 kΩ/2 kΩ
  → 8 V) and BROKEN (claimed 4 V) through POST /verify. CI green; assay **58 → 60**. Capability 2 is DONE by its
  own proof. Next in order: 3 (a claim grammar) and 7 (the engine measures itself in public) run alongside.

## 2026-10-04 (night) — Gen 3 · 3 (first cut) — THE CLAIM GRAMMAR (a759d7b) — arithmetic claims, one parser
- **Built.** `audit.py`: sum, product, quotient and word arithmetic were four pair/chain regexes (the cardinal of
  2026-10-03 was a pair cut out of a chain; a mixed expression was a miss by design). One grammar now —
  `expr := term (op term)*`, `term := NUM | (expr) | -term`, ops `+ − × ÷ % plus minus times multiplied-by
  divided-by mod` — takes the MAXIMAL expression ending at the claim verb and hands the whole of it to the
  mathematics equality verifier (precedence honoured). The zero-false-positive discipline lives in the tokenizer:
  tokens adjacent (only whitespace between), at least one binary operator, a symbolic minus binary only with its
  spaces ("3-5" is a range), "/" and "x" operators only between numbers ("$18.50/hr" is a rate), "^" and "%" end an
  expression (their extractors own them), division by a literal zero stays a gap. The labels the pins know survive
  (sum / product / quotient / arith_words); a mix is "expression".
- **Proof against the charter.** Every audit golden holds unchanged (127 audit/compose/house pins); the
  mixed-operator claims that were misses are verdicts — live: "2 + 3 * 4 = 14" HOLDS, "(2 + 3) * 4 = 20" HOLDS,
  "10 − 2 × 3 = 4" HOLDS, "2 plus 3 times 4 is 14" HOLDS, "2 + 3 * 4 = 20" BROKEN, "pages 3-5 is 2 pages" nothing;
  GSM8K cannot regress by construction — it was graded through `calc_chain` (MATH_VERIFY), which the grammar does
  not touch, and its pins hold. Assay **61 → 64**. The rest of #3 — quantities with units, relations, references
  folded into the same grammar — continues alongside; #7 (the engine measures itself in public) starts now.

## 2026-10-04 (night) — Gen 3 · 7 — THE ENGINE MEASURES ITSELF IN PUBLIC (d3125f5) — PROVEN on its first deploy
- **Built.** `tools/benchmarks.py` runs the standing benchmarks on the box and writes `data/benchmarks.json`: every
  golden pair in `data/domain_goldens.json` through the real router (did the domain SEAL its truth and REFUSE its
  falsehood; a confirmed falsehood is a false positive), the derivation-moat set (`tools/benchmark.py`, 60 claims,
  three modes; its false positives must be 0), every admitted spec's own goldens. THE RATCHET, as the assay's: a
  floor of every domain ever ok and every spec ever admitted; a regression is "in the floor, not ok tonight",
  named again every night until fixed. `GET /benchmarks` serves the measured file with its age (stale after 36 h;
  `?detail=1` per domain). `/proof`'s scorecard reads it — false positives and domains-ok are measured numbers
  with the time they were measured. `tools/deploy.sh` gained THE GATE: after both doors answer, the box runs the
  benchmarks (`--gate`) and the live assay; a regression REVERTS the files and restarts (`DEPLOY_NO_GATE=1` is the
  emergency bypass, to be written up when used). `nh-benchmarks.timer` nightly 05:20 UTC after the assay.
- **The first gated deploy, 23:28 UTC:** BENCHMARKS OK — domains **68/69** ok (sealed 69, refused 68, false
  positives 0), moat **60/60**, 0 false positives, specs 5 checks admitted; ASSAY OK 65/67, floor **64 → 65**.
  The engine's first public self-measurement found one thing: **physical_constants: its golden FALSEHOOD cannot be judged — the generator perturbed the unit label ('m/s' → 'm/s_NOT') as well as the value, and the verifier rightly DECLINES an unknown unit (the 2026-10-01 unit-label rule), so the pair never tests the value; the generator must perturb values, never unit strings** — recorded here as the benchmark's
  first finding, not hidden.
- **Lesson (CI red twice on 5870000/a7954e7):** a `pytest … | tail` chain reports tail's exit, not pytest's — the
  commit went in red. Run the tests to a file and branch on their own exit code. And the suite's known
  CONCORDANCE_DATA_DIR race bit a third module: pin the dir per test, pass it explicitly.
- **The finding fixed (d53d2ac, deployed 23:40 UTC through the gate):** the generator leaves unit labels alone, the
  physical_constants pair is repaired, and a new pin requires every golden falsehood to draw a MISMATCH or an ERROR
  (a domain that cannot judge in an environment — linguistics on CI, its source absent — is exempt, not a shrug).
  Benchmarks now **69/69** domains, moat 60/60, 0 false positives; the floor rose to 69.

## 2026-10-05 — Gen 3 · 4 (first cut) — THE WORD IN THE READER'S TONGUE (2ce8d91 · 784f853)
- **Gathered, never authored.** `tools/gather_book_names.py` takes the 66 books' names in every held language from
  Wikidata (CC0): each item found by its English name with a Bible disambiguation and VERIFIED by its description;
  labels + aliases in 16 languages (zh, zh-hans, zh-hant folded into zh). The SHORT names are DERIVED: a token that
  names a book in most of that book's names and in few of any other's ("juan" in John's, in a few of Revelation's)
  is the bare name; numbered siblings fold into their root the way an English reader treats a bare "John"; keys
  casefolded, accents and points stripped. 66/66 books; es/de/fr/ru/zh/ja/ko/… complete; reported misses: Burmese
  14, Arabic 1–2 Kings, Vietnamese 2 — never filled in by hand. `data/bible_book_names.json` (data-only) rides with
  capability 1's sync.
- **Built.** `scripture.localize_ref`: "Juan 3:16", "Johannes 3,16", "約翰福音3:16", "Иоанна 3:16", "Jean 3:16" →
  John 3:16; unless the caller chose a language, the passage comes in the tongue the book was named in; an English
  name stays English; an ambiguous name (Johannes: de and nl) picks a held Bible and says what it saw
  (`named_in`); lang=None is auto, lang="en" is the caller's choice. Live on both faces in six tongues.
- **The first live run regressed, and the gate let it through — both fixed the same hour.** "what is 2 + 2" came
  back as Isaiah 2 in French: a two-letter Wikidata alias ("Is") was a key and the ask door's candidate "is 2"
  matched it. Fixes: the gather drops Latin keys and derived tokens under three letters; `localize_ref` acts only on
  one to three words, digits only as a leading ordinal, Latin names of three letters or more (pinned). And the
  gate's `cmd | tail` had reported tail's exit, so the REGRESSED assay did not refuse the deploy — each check now
  writes a file and its own exit code is the verdict. The corrected gate passed 784f853: benchmarks 69/69, assay
  **68/70, floor 68** (three new probes: Spanish, Chinese, Russian names).
- **Not yet (the rest of #4):** the house ending's four labels are still English chrome; a simplified-script
  Chinese name for John is absent from the source (Wikidata has only the traditional label) — a want, not a guess.

## 2026-10-05 — THE TICK STICK: the Millennium problems as open questions with sealed marks (6a92c53)
- **Matt:** "The Millennium problems. I feel like we have gathered enough to make an attempt at them." The look said
  otherwise (no card for any of the six; "Yang-Mills" landed on the Greek for mill) and the constitution says what an
  attempt can be: the engine finds, checks and seals — it does not author a proof. **Matt: "We build a tick stick. A
  tool that allows us to infer closer and closer."** A joiner ticks the points of a crooked wall he can reach and
  infers the shape from the ticks, never past the last mark.
- **Built.** `tickstick.py`: a stick is an open question; a tick is a mark the engine can stand behind — bound /
  instance / witness (must name a HOLDS seal in this keeping; checked before acceptance), equivalence / exclusion
  (must name a source), note. The FIT is computed from the ticks and nothing else: the greatest sealed bound (a
  ratchet), sealed instances, cited equivalences and exclusions, and the open remainder — it never says the question
  is settled. Doors `GET /sticks`, `GET/POST /stick`, `POST /tick`; `data/sticks.jsonl` rides with the node sync.
  `docs/TICK_STICK.md` is the method.
- **The first mark.** `number_theory.critical_line`: every zero of ζ up to a height T lies on the critical line, by
  two INDEPENDENT counts that must agree — sign changes of Hardy's Z on the line and Backlund's argument-principle
  count N(T) = θ(T)/π + 1 + S(T) in the strip, S(T) followed continuously from σ = 2 to ½. A missed close pair makes
  the counts disagree (a miss stays a miss). Turing's/Backlund's method, the way every published verification is
  done; ours is small and sealed. `tools/tick.py riemann T` mints the mark through the same sealing path as POST
  /verify with the 8-second shed lifted.
- **Live on the box.** Seven sticks (`tools/tick.py seed`; Poincaré kept as the solved one). Riemann: three sealed
  bounds in progression — **T = 200 (79 zeros) `d66bae9d…`, T = 500 (269) `28a7b4d2…`, T = 1000 (649)
  `6317ceac…`** — plus three cited equivalences (Schoenfeld 1976, Robin 1984, Titchmarsh §14.25); fit: *verified up to
  height T 1000; beyond: not verified here*. P versus NP carries the three barriers as cited exclusions (Baker–Gill–
  Solovay 1975, Razborov–Rudich 1997, Aaronson–Wigderson 2009). The other four are open sticks awaiting marks. CI
  green; the gate passed; four probes added.
- **What this is and is not.** It is the map a human attempt needs and the honest referee for one — verified to here,
  excluded there, open beyond. It is not, and will not become, a proof generator.

## 2026-10-05 — "push and keep going": Riemann to ten thousand by Riemann–Siegel; the BSD stick gets its first sealed instances
- **Riemann, pushed.** The on-line count now runs the Riemann–Siegel formula in floats (a hundred times faster than
  mpmath) a twenty-fourth of the mean spacing apart above t = 501, mpmath a quarter apart below, on ONE grid with one
  exact correction (a span whose two samples both sit within the formula's own error without a crossing is recounted
  with mpmath). Two wrong turns on the way, both caught by the independent strip count: a plain float scan missed close
  pairs (t ≈ 2262.9, |Z| ≈ 0.003); a layered refinement double-counted near crossings. One grid, one count, nothing
  counted twice. Agreement at T = 50, 100, 1000, 3000, 10000 in ~20 s each; the door's cap rises to 200000.
  **Mark: T = 10000 — 10,142 zeros, all on the line, seal `a4e07b75…`**; **T = 100000 — 138,069 zeros, all on the line, seal `7f393638…`, 79 s on the box**.
- **BSD, first marks.** `verifiers/elliptic_curves.py` (the 70th domain): a_p by point counting, a_n multiplicatively,
  L(E,1) by the approximate functional equation whose cutoff-independence CHECKS the root number, L′(E,1) by E1, and
  the analytic rank with the theorem that carries it (Kolyvagin; Gross–Zagier) or the honest "≥ 2 numerically". Sealed
  on the BSD stick: **11a1** (L(E,1) = 0.253842 ⇒ rank 0, instance `ea3a1e78…`), **37a1** (L′(E,1) = 0.305999 ⇒ rank 1,
  instance `d69c398b…`), **389a1** (analytic rank ≥ 2 numerically, witness `e3ad1055…`), **5077a1** (≥ 3, witness
  `d483293b…`). Conductors divisible by 2 or 3 are declined (no Tate's algorithm) — a want.
- The live-wired-numbers guard caught the seventieth verifier ("69 domains" on three surfaces → 70). Benchmarks 70/70.

## 2026-10-05 — "Do C then numpy": the Riemann sweep accelerated, and a million zeros sealed (2f3cd99, b5c66f2)
- **The problem it solves.** The pure-python critical-line scan to T=1e6 took 4.2 hours and came up 18 zeros
  short of Backlund's independent strip count — so it rightly sealed NOTHING (a miss stayed a miss). Both the
  speed and the shortfall are fixed.
- **C then numpy (src/concordance/verifiers/_rs.c + riemann_accel.py).** The bulk sweep of Hardy's Z runs through
  the fastest backend present: **C** compiled on first use (`cc -O3 -fopenmp`, parallel across cores, ~2.4 us/point
  at T=1e6; on the box's libm it matches python to the last bit, 0.0 diff), else **numpy** (vectorised over
  equal-m grid points), else the **pure-python** reference. All compute the same first-order Riemann-Siegel
  formula and the scan defers to exact mpmath near every zero, so the COUNT is identical whichever ran — a speed,
  never a verdict. The compiled .so lives in the data cache (per-node, never synced); _rs.c ships and each node
  builds it. `/capabilities.boundaries.riemann_backend` names the live one (box: "c").
- **The dip detector (number_theory._count_changes / _dip_crossings).** A same-sign triple whose fitted parabola
  is predicted to dip below zero is a close pair the grid stepped over; it is recounted EXACTLY with mpmath. It
  fires at most once every two steps (a skip after it fires), so it can never count a crossing twice — the worst
  it can do is miss a second pair in one span, which the strip count then exposes. This is what closed the 18-zero
  gap at a million. The scan evaluates Z in blocks and folds in O(1) memory (no million-long list).
- **Sealed.** T=1e6: **on-line 1,747,146 = strip 1,747,146**, 0 localised rescans, **220 s** (was 15,193 s and
  off by 18). Seal `9a6b18a8f0238c548c963171fd63af30ecaedfa39756300b094ec2d733d0ee29` (re-checkable, 200). The
  Riemann stick's progression: 200, 500, 1000, 10000, 100000, 200000, **1,000,000**; fit: verified up to height
  T 1e6, open beyond. Benchmarks 70/70, assay floor 75. CI green; the gate passed.
- **Noted:** a mark runs the scan twice (tick.py counts, then the verifier recounts to confirm) — the price of
  the seal's verifier being its own skeptic, left as is. Beyond 1e6 the main sum grows as sqrt(T); 1e7 is ~hours
  even in C — a want for a blocked/FFT main sum if we push higher.

## 2026-10-05 — "push to 10 million": T=1e7 sealed — 21,136,125 zeros on the critical line (49126be + the mark)
- **Sealed.** Every non-trivial zero of zeta with 0 < Im(s) <= 10,000,000 lies on the line: the on-line count
  (21,136,125, Riemann-Siegel sweep + parabolic dip detector) equals Backlund's independent strip count exactly,
  S(T) = -0.206, 0 localised rescans, in 7822 s (~2.2 h) on the box. Seal
  `5a560183a60e1d39ce2707dc7c4670123040d60d6c11b9a8a28d9911ad2c7d0c` (re-checkable, 200). The Riemann stick's progression: 200, 500, 1k, 10k, 100k, 200k, 1M, **10M**.
- **Two fixes the first 1e7 run surfaced** (it scanned fine and the counts AGREED, but did not seal):
  * the height cap in verify_critical_line (1e6, to protect the public /verify worker) is now lifted for the
    trusted operator by CONCORDANCE_RIEMANN_MAX (tools/tick.py sets 1e9), read live;
  * _rs.c precomputes log(k) and 1/sqrt(k) (they were ~85% of the per-point work at m~1262) — same doubles to
    ~7e-15, so the count is unchanged (1e6 still exactly 1,747,146); ~1.3x faster (the cosines are now the floor).
- A mark scans once (the _zeros_on_line_checked memo spares the verifier's second scan). Benchmarks 70/70,
  assay floor 76. The literature value for N(10^7) is 21,136,125 — the two independent methods landed on it.

## 2026-10-05 — the Riemann attempt documented in its stick, and the Large Numbers Hypothesis as a stick (afe2c47, 4e18127)
- **Riemann documented (afe2c47, live).** fit() now surfaces the note ticks as `record` and carries each bound's
  seal in the progression. `tools/tick.py document` wrote four notes onto stick_riemann_hypothesis — method (two
  independent counts must agree), the honest record (the first 1e6 came up 18 short and sealed nothing), compute
  (C/numpy/python, exact mpmath near zeros), open (bound at 1e7; the hypothesis itself unproven). The stick now
  reads, live: verified to T=1e7 (seal 5a560183), 8 sealed bounds 200→1e7 each with its seal, 3 cited
  equivalences, the 4-line record, and the honest "open beyond".
- **Large Numbers Hypothesis (4e18127, live) — "large number hypothesis".** Dirac's LNH as a tick stick, the
  project's discernment exactly: SEAL the arithmetic, CITE the conjecture, endorse nothing. `tools/tick.py lnh`:
  * WITNESS (sealed `46d112d47badc282…`, re-checkable 200): N1 = e^2/(4*pi*eps0*G*m_p*m_e) = 2.268661e39, the
    electromagnetic-to-gravitational force ratio, computed from the engine's attested CODATA constants (numeric mode);
  * NOTE: Dirac's N2 = T_Hubble/atomic-time ~ 10^40.7 is within an order of magnitude — cited, not sealed (N2 rests
    on the Hubble time, a measured cosmological quantity, not a constant);
  * EXCLUSION (cited: lunar laser ranging Williams-Turyshev-Boggs 2004; Oklo Shlyakhter 1976 / Damour-Dyson 1996):
    the time-varying-G prediction is disfavored — |G_dot/G| is bounded far below a 1/t law;
  * NOTE: a coincidence of magnitudes is not a law; the engine seals that N1 IS ~2.27e39 and endorses nothing more.
  Fit: one sealed witness, the general question open. Eight sticks now stand (7 Millennium + LNH).
- Ties the standing guardrail [[project_numbers_bases_triangulation_2026-06-13]] (seal the arithmetic, attribute
  the pattern, NO numerology) — the LNH stick is that rule made a public, re-checkable object.

## 2026-10-05 — "Fine Number Constant": the fine-structure constant as a stick (2359262)
- Read as the fine-structure constant. `tools/tick.py alpha` opened stick_the_fine_structure_constant: WITNESS
  seals alpha = e^2/(2*eps0*h*c) = 7.2973525693e-3, 1/alpha = 137.035999, from the attested CODATA constants
  (seal a35b3122…, re-checkable 200); NOTE records that 1/alpha is NOT the integer 137 and Eddington's 1/137 is
  historical and false; EXCLUSION cites the Oklo + atomic-clock bounds that make alpha constant to the evidence;
  NOTE keeps the discernment — seal the value, cite the claims, endorse nothing. The 137 numerology made a
  public object that refuses itself. Nine sticks now. Also: the sticks probe asserts membership not a brittle
  count (the gate had correctly refused a deploy when the 8th stick broke "count eq 7").

## 2026-10-05 — RH by elimination: not the brute scan, the other tools charting a narrower window (d932455)
- Matt, three turns: we are NOT running the normal method (the brute zero-scan to 1e8, a ~3-day job); use the
  ticks from the OTHER tools to chart a narrower window; and we are looking at what RH is NOT. So RH is charted
  by ELIMINATION, and the eliminations are run by the engine itself, not by hand.
- `verify_robin` (number_theory; domain alias "robin"/"robins_inequality"; its own golden so the nightly
  benchmark runs it — domains 70->71; callable at POST /verify). Robin 1984: RH <=> sigma(n) < e^gamma*n*ln ln n
  for all n > 5040. The divisor-sum sieve finds NO counterexample in (5040, N] and so RULES OUT an RH failure by
  this route below N — it narrows the window, it does not confirm RH. Bounded N <= 2e7; numpy sieve.
- Live on the Riemann stick: a sealed WITNESS (elimination), c083a632…, "no RH counterexample via the divisor-sum
  route at n <= 20,000,000 (closest approach n=10,080, ratio 0.9858 < 1)"; and a note stating the frame — the
  stick is charted by what RH is NOT: no zero off the line below height 1e7 (directly), no Robin counterexample
  below 2e7 (through the divisor sum), so a counterexample must evade every eliminated region at once. The
  pursuit of 1e8 by brute scan is set aside for this: a counterexample's window is pushed up by cheap, exact
  eliminations from independent tools, which is the engine's own method (narrow by elimination).
