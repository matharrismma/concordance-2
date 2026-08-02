# THE MAP

*One map of the whole project, written 2026-08-01 to be handed to another model.*

Every number here was **measured** on the day it was written, not remembered. Where something is
unproven or broken, it says so. If you find a number that disagrees with the running system, the
running system is right and this file is stale — correct it.

---

## 1. What this is, in one sentence

**A governed way to find, check, use, and preserve information without losing its source, its
authority, or its history.**

That is the frozen mission. Everything below is machinery in service of it.

Two faces on one engine:

| Host | Surface | Role |
|---|---|---|
| `narrowhighway.com` | `secular` | the library — world-facing, free, no account |
| `narrowhighway.org` | `witness` | the record — the same engine, the witness surface |

The author is **Matt Harris**, a solo builder. It is free, requires no sign-in, and is built to
serve people who cannot afford to be without it — children, homeschoolers, small churches, people
off-grid. That constraint is load-bearing: **any design that requires an account is wrong.**

---

## 2. Read this before you change anything

Four ways to break production, in the order you are most likely to hit them.

**The gate is the only verdict.**
```bash
PYTHONPATH=src python tools/check.py
```
It must print `=== GATE PASS ===` **and** exit 0. Never pipe it through `tail` or `head` — that
masks the exit code, and it has hidden a real failure before. It takes 9–13 minutes.

**Freeze the tree while the gate runs.** `.gate.lock` stops other *processes*; it cannot stop you.
Editing a file mid-run silently invalidates the verdict. One gate was thrown away for exactly this.

**The shards are opened `immutable=1`.** 24 shelves ride SQLite FTS5 shards that SQLite has been
promised never change. **Stop both services before writing a shard**, or readers get served pages
that no longer exist in the file beneath them.

**Deploy is `sh tools/deploy.sh <files…>`** — tar over ssh, staggered restarts (`nh-org` :8001,
then `nh-com-2` :8002), ending in a drift check that must report *the box matches the repo, file
for file*. Box is `nh@5.78.186.55`, key `~/.ssh/id_ed25519_nh`, dest `/home/nh/concordance-2`.

Git: **never `git add -A`.** Stage by name. Data and secrets are untracked by design.

---

## 3. The doctrine

These are not style preferences. Each was paid for with a defect. The code is downstream of them.

**The five-part kernel.** Find · distinguish · verify · preserve the trail · **never silently
upgrade authority.** The last one is the whole project: a fingerprint is not a verdict, a citation
is not a proof, one witness is not established fact.

**Retrieve first; generation is the last resort.** The library *finds and arranges* what it holds.
It does not author substance and let it pass as found. But — and this correction cost a real user
complaint — **composition is not generation.** Arranging two attributed cards side by side is the
concordance doing its job. Confusing "do not author" with "do not assemble" once left a user with
"nothing worth reading."

**Three or four states, never two.** `HOLDS` / `BROKEN` / `CANNOT_CHECK`. `true` / `false` /
`absent` / `malformed`. **A check that cannot run is not a check that passed.** Our failure is
never rendered as their falsehood.

**A miss must stay a miss.** A gap rendered as an answer starves the loop that would have filled
it. When the gap count rose 58 → 106 after a fix, that was *honesty*, not regression.

**Two planes, one mechanism.** A human's own ask authorises the write (`public`); an agent's does
not (`public_review`, withheld until a person looks). Same act, different authority. The plane is
the *only* variable.

**A measurement must report its coverage.** State files/rows/window *before* the number. A
verdict over 1 probe of 1,000 that exits 0 is worse than no verdict.

**Follow the guarantee to the reader.** Correct server-side and invisible to the person is **not
done**. This has failed five separate times. Agents are ~35% of traffic, so "the reader" means the
HTML page *and* the JSON *and* the MCP schema.

**Refuse abuse, not use.** Every refusal must name what *is* available.

---

## 4. The recurring failure — read this twice

Nearly every serious defect in this project has had **one shape**:

> **Correct-looking code on a path nobody walked.**

It passes review. It passes unit tests. It is structurally unable to work in production, and
nothing says so, because nothing exercises it.

Confirmed instances, all found by *touching the live system*, none by review:

- **The fd leak.** Thread-per-request × handle-per-thread → 1023/1024 descriptors → every
  `/verify` returned 500 for an hour. Three wrong instruments were tried before the right one.
- **The archive.org allowlist.** `ALLOWED_HOSTS` named one guessed storage node; archive.org
  serves every download from a per-request node. **The ark could not fetch from archive.org at
  all**, for as long as the module existed.
- **Two search fixes deployed that didn't fix the site.** Both times because there are *two*
  matchers (resident IDF ranker + shard FTS) and only one was patched.
- **A `^`-anchored regex** used with `.match(text, pos)`, where `^` only matches at position 0. It
  fired on titles (fresh strings) and could never fire on bodies (position 11,687 of a book).
- **The `/card` JSON telling agents nobody had checked a card** while the HTML page said "checked
  by 2 readers" — one surface fixed, the sibling forgotten.

**The practice that catches these:** after the gate passes and the deploy lands, *query the live
wire and read what comes back*. Prove the test fails before you trust that it passes. Disable your
own fix and watch the check go red.

Second, related trap: **an instrument that mistakes its own reading for a defect accuses the thing
it measures.** Calibration's first run reported 7 false positives; 4 were correct refusals and the
reader was wrong. A "251 regressions" finding was 3 cards counted repeatedly. **Check the check
first.**

---

## 5. The shape of the thing

### The card
The atom. A JSON record: `id, kind, title, body, source{label,url,authority_tier}, shelf, bands,
subject, connections[], lifecycle_stage, generated, extra{}`.

Rules that hold across every card:
- **Bare in the store, magic on the read.** No presentation field ever reaches disk — a
  "3 minutes ago" written into a record is stale forever and rides every copy. `present.derive()`
  is pure, cached by `(id, updated_at)`, and never written back.
- **No orphans.** Every card is `member_of` a shelf spine, or `excerpt_of` a source.
- **`lifecycle_stage`** gates visibility: `corpus.is_public()` admits only `public` / `featured`.

### Scale, measured 2026-08-01
| | |
|---|---|
| cards searchable | **551,861** across **107 shelves** |
| largest shelves | dictionary 149,490 · gutenberg 77,700 · geography 69,135 · commentary 48,493 · taxonomy 37,933 |
| core modules | **97** (24,221 lines) + 3 web + **66 verifiers** |
| HTTP routes | **159** (116 GET, 51 POST, 1 DELETE) |
| MCP tools (live) | **82** |
| tests | **1,192 passing**, 158 files, 1,179 test functions |
| site pages | 42 HTML + 12 JS |
| tools/ | 77 scripts |
| commits | 365 |

### The stores
- `data/cards.jsonl` — the resident keeping (~25k)
- `data/shards/*.db` — SQLite FTS5, `immutable=1`. **24 shelves** (named in `.env` as
  `CONCORDANCE_FREEZE_SHELVES`) ride **5 databases** — `books` 228 MB, `word` 387 MB,
  `dictionary` 227 MB, `world` 178 MB, `science` 97 MB — plus `core.db` 117 MB. ~1.2 GB total.
  `frozen_shelves()` returns **empty** unless the env names them *and* the shards exist, so a
  shell without the service env reports 0. Do not read that as "nothing is frozen."
- `data/web_cache.jsonl` — what the tortoise minted (the acquisition store)
- `data/church_cards.jsonl` — 29 records: 1 spine + **28 on the `churches` shelf**, which is
  **13 traditions** + 1 ecumenical-creeds card + **14 individual voices** (Wesley, Calvin, Luther,
  Aquinas, Spurgeon…). *Not* 28 traditions — that error was repeated all through 2026-08-01 and
  was written into `compare.py`'s docstring before being measured and corrected.
- `data/sources/` — the ark: content-addressed bodies `<sha[:2]>/<sha><ext>` + `.waybill.json`
- `data/wants.jsonl` · `data/unchecked.jsonl` — the ledgers

`cards.jsonl` and the shards **partition with overlap; both are canonical.** Do not assume one is
a copy of the other — that was assumed once and measurement disproved it.

---

## 6. The modules that matter

Do not read all 97. These carry the design.

**Retrieval & keeping**
- `corpus.py` — the resident ranker. Holds `SUBJECT_TIER = 1000.0`: the max-IDF token of a query
  is a **partition, not a weight**. Cards without the subject word are *excluded*, never ranked
  last and shipped. No padding the tail.
- `corpus_db.py` — the shard layer. Per-thread connections, a thread registry + reaper, and a
  monotonic `opened_total`. The `_STOP` frozenset lives here and **both matchers must share it.**
- `graph.py`, `address.py`, `cabinet.py` — the nesting, addressing, and the filing-cabinet census.

**Acquisition (the slow lane)**
- `find.py` — the tortoise. LoC, Internet Archive, Gutenberg. PD/CC0 only, never Wikipedia.
- `sources.py` — the ark. Host allowlist + `*.us.archive.org` suffix, 64 MB ceiling enforced *on
  the stream*, re-hashes the copy that landed.
- `craft.py` — cuts cards out of a held source. **`card_from_span(sha, start, end)` has no `body`
  parameter**: the body is read *out of* the anchored bytes, so generation has no door. A Tesla
  valve, not a policed rule. `verify_spans()` re-reads and proves it, in four states.
- `expand.py` — one mechanism, two planes. The want list is **only** for offline; online we
  execute now and let the person assist.

**Honesty surfaces**
- `unchecked.py` — engine-written cards go in **wearing their open question**; the first reader to
  recall one is asked to close it. One reader is a check, not a proof. One "wrong" marks disputed
  and never erases.
- `attest.py` — cryptographic witness over a content hash. Never takes a private key.
- `present.py` — the presentation layer. Derived, never invented; where the card is silent, it is
  silent.
- `compare.py` — reads "X vs Y" as two subjects. `held_as_tradition` distinguishes **having the
  word from having the thing** (searching "Nazarene" returns cards about Jesus of Nazareth).

**Front doors**
- `ask.py` — the conduit. **The crisis path outranks everything** and must stay first.
- `web/api.py` — all 159 routes + the route registry. Two governance tests guard it: a golden
  route history and reachable-or-declared-agent-only.
- `mcp` surface — 82 tools, the agent's door.

**The 66 verifiers** (`verifiers/`) are the math: physics, chemistry, statistics, scripture,
geometry… `check` routes to them; `find_verifier(keyword)` locates one without scanning.

---

## 7. The four instruments

Each answers a different question. None substitutes for another.

| Tool | Question |
|---|---|
| `tools/check.py` | Does the code do what it was told? (the gate) |
| `tools/divergence.py` | Do the stores agree with each other? |
| `tools/watch.py` | Is it behaving **on the wire**? (hourly timer, both hosts) |
| `tools/calibrate.py` | Is it still **true**, and by how much off? (36 reference points, half of them null tests) |

`watch.py` reports `HOLDS` / `BROKEN` / `CANNOT_CHECK` and **refuses to report** when a check
crashes. A vacuous pass was once written into the very tool built to catch vacuous passes.

---

## 8. Where it actually stands

**Working and verified live:** both hosts serving; search relevance partition on both matchers;
comparison as composition; the tortoise; the ark (fetch → sha → verify); craft (10/10 spans
verified against a real 311k-char public-domain source); the unchecked ask reaching both the HTML
page and the JSON; 1,192 tests green; box matches repo file-for-file.

**Known incomplete — do not report these as done:**

- **The `churches` shelf has 29 voice cards and no Church of the Nazarene.** Ten cards of its own
  1923 Manual are now in the keeping; distilling them into a 30th voice card is a human act.
- **`craft` is not wired into `/ask`** — deliberately. Crafting downloads a whole book (313 KB to
  64 MB); inline on a miss it would wreck response times. It belongs on the acquisition path.
- **The both-sides-held comparison path has never run on real data.** Every test used fixtures.
- **One-store SQLite migration** — approved, not begun. Index first, then cards, then the
  connection graph; parity-check with `calibrate.py` before and after. The "index is ~72% of
  resident memory" figure that set that order is a **ratio from the estimator named directly
  below**, so treat the ordering as sound and the magnitude as unverified.
- **The memory estimator's absolute numbers are knowingly ~8× wrong** (needs a stratified sample,
  counting only resident). Its ratios are more trustworthy than its totals.
- **"Agents are ~35% of traffic"** appears throughout the code comments as justification for
  agent-facing work. It came from an access-log rollup, not from a live counter — re-measure with
  `tools/traffic_rollup.py` before resting a decision on it.
- **The resource governor is unbuilt.** 1.0's steward had the strongest version; nothing in 2.0
  governs.
- **Consent for an agent acting on a human's behalf** is still open. (The private-key-on-the-wire
  problem itself is RESOLVED — 0 of 82 tool schemas accept one, and the live box refuses.)
- **An open question:** can an agent open the Gate?

**A live decision worth revisiting:** the droplet now anchors source bodies at `data/sources`
(313 KB). That cuts against the two-tier design where bodies live on drives and only cards travel
— but it lets `verify_spans` re-prove cards against real bytes in production. Cards carry the sha
and origin URL, so anyone can re-verify without our copy. Easy to reverse.

---

## 9. If you pick this up

1. **Read `docs/COMPLETION_CONTRACT.md`** — the invariants, the machine-testable definition of
   done, and the drift ledger. It outranks this file.
2. **Run the gate before you touch anything**, so you know the baseline is green and not something
   you caused.
3. **Work one thing to done**: gated → deployed → *verified on the live wire* → committed. A
   change that is gated but not verified live is not finished; this project has proven that five
   times over.
4. **When you find a defect, ask what path nobody walked** — then walk it.
5. **Correct the record backward.** When a number turns out wrong, fix it in the places that
   already reported it. A removal is a record, never an erasure.

The standing instruction, in Matt's words: *keep what is good, consolidate or eliminate what will
not be fruitful, expand what shows promise.* **Add nothing new unless it removes more than it
adds**, and report the net change in modules, tools, routes, and pages.
