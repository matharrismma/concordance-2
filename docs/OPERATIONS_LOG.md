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
