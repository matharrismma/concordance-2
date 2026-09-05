# THE PUNCH LIST — one item at a time, finished before the next is started

> **The live routed sheet is now [`REMAINING.md`](REMAINING.md)** — every open item there carries a
> `<subsystem>-<n>` ID (or a cross-cutting `commons-`/`seed-`/`record-` slug) that routes to
> `/systems`, its SOP, and its code. This file is kept for its **unit definitions and completion
> tests** (the `C#`/`H#` breakdowns REMAINING points back to); the surviving units are mapped there.

Matt, 2026-07-29: *"Build the priority punch list and work on one until complete. Then move to
the next. Start with the commons."*

**The rule for this list:** an item is DONE when it is gated, deployed, verified live, and
committed — not when the code exists. Nothing below is started until the item above it is done.
Each item names its own completion test, so "done" is not a judgement call.

---

## 0 · THE HARDENING  ← NEXT (from the lessons)

`docs/LESSONS_AND_HARDENING.md` — thirteen measured lessons from 2026-07-30 and the seven units they
obligate (H1–H7). It goes FIRST because three of its items are things that are currently **wrong**,
not merely missing: a steward token that never expires, a stale-read helper duplicated across eight
pages, and a gate that names no owner. The Commons resumes at C1e once H1–H3 are closed.

## 1 · THE COMMONS  ← C1a–C1d DONE and live

The page becomes social first: every member stocks their own shelf, writes and is read, and the
commons is what the fellowship has chosen to put on it. Design: `MASTER_PLAN.md` §3 and memory
`project_social_first_member_shelves_lending_2026-07-28`.

Broken into units that each stand alone:

| unit | what it is | done when |
|---|---|---|
| **C1a** | `shelves.py` — the member shelf: signed drops, the three rings, the curation state machine | a member can stock a shelf with a signed card, a commons drop lands in `public_review`, a steward's promotion is a recorded act, and every refusal carries its reason — gated |
| **C1b** ✅ | routes + MCP: `/shelf`, `/drop/signable`, `/drop`, `/curate` | ~~the whole flow works over HTTP and through an agent; goldens updated~~ **DONE 2026-07-29** — 6 routes + 6 MCP tools, gate PASS, deployed, `tools/live_shelf_check.py` walks it on the live box 18/18 and leaves the steward queue clean |
| **C1c** ✅ | `shelf.html` + the commons surface | ~~a real person can stock a shelf and read someone else's in a browser, key born on device~~ **DONE 2026-07-29** — walked in a real browser: key born in the page, drop signed and stocked, read back with the member's name, own card withdrawn by its own signature, a commons offer promoted by a steward. Two bugs it uncovered, both fixed and pinned: `POST /curate` accepted any typed name, and no JSON response on this server had ever carried `cache-control` |
| **C1d** ✅ | drops that are links: embeds, quotes, curated pages with fetched-at + content hash | ~~a video/quote/page drop renders with its waybill; no byte of anyone else's page is stored~~ **DONE 2026-07-29** — `linkdrop.py` (SSRF-guarded fetch, waybill of facts only, `no_page_bytes_kept()` checkable) + `present.py` (**the experience layer**: bare card in, derived block out, never stored). Verified on a real page: waybill captured, provider named, quote attributed, four SSRF attempts refused at the door. **No embed by design** — an iframe would beacon the reader's IP |
| **C1e** | first wings stocked: recipes · music · art (PD seed cards) | each wing has real cards before it is announced — never an empty room |
| **C1f** | **OPPORTUNITIES TO SERVE** — needs & offers, grounded in Romans 12:1 | a member can post a need or an offer, be matched by PROXIMITY AND CAPABILITY (never by profiling), and have the service attested BY THE ONE SERVED — with no leaderboard anywhere and the act recorded but UNSEEN by default (Mt 6:3) |

## 2 · THE RECORD
`THE_RECORD.md` — one record, one chain, many views. **Done when** `GAPS.md` and
`OPERATIONS_LOG.md` are *rendered from cards* and hand-editing them is impossible without the
renderer disagreeing.

## 3 · THE ADDRESS, finished
v3 places 99.97% but stores nothing. **Done when** the address renders on the card page, in
`/search`, and on the MCP surface, and a prefix query route answers — *then* the shard column.

## 4 · THE HONESTY DEBTS
- **§5 private-key-on-the-wire — RESOLVED (2026-08-26)**: zero endpoints read `private_key` inbound.
  The five handlers were retired once the browser could sign (commit 4a86cf8); the AST guard
  `test_no_http_handler_reads_a_private_key_out_of_a_request` proves no handler sources one, and the
  two remaining failures in `test_no_keys_on_the_wire.py` were a STALE expectation — they predated the
  signed-posts policy (9ea6d93) and asserted "unsigned still allowed." Updated to the shipped policy
  (unsigned refused, crisis-exempt); the file is green. **The contract §5 DONE line can now be
  truthfully struck — operator's call, since `COMPLETION_CONTRACT.md` is frozen.**
- **The "three dead files" were a STALE PREMISE — verified 2026-08-26, nothing archived.** The
  named files are not dead: `config.py` has 11 src importers, `branding.py` 3, and `web/ask.py`
  does not exist (the module is `ask.py`, with 14 importers). A wider sweep for a real archival
  target found only `grid_atlas.py` unwired from any production code path (0 src refs) — but it is
  tested (`test_grid_atlas.py` exercises its full surface) and named a strong aspect in
  `docs/HARVEST.md`; it renders the axis atlas over the live `grid` scaffold. That is **latent, not
  dead** — archiving it would remove a working, tested capability, so it stays. `inlet.py`, briefly
  eyed as a candidate, is live too (serves `POST /inlet` + returns). **Conclusion: no file here is
  safe to archive. This debt is closed as a documentation error, not a removal.**
- **Coverage 52% → 90%**, worst user-facing modules first (almanac 20%).
- **Corpus-dependent tests skip on a clean clone — DONE (2026-08-26)**: a clean clone lacks the
  gitignored keeping (`cards.jsonl`, `bible_en.jsonl`, `strongs/`, `characters/`, …), so 48 tests
  across 17 files failed for a stranger. `tests/conftest.py` now skips those files WITH A STATED
  REASON when their data is absent (`_CORPUS_DEPENDENT` + a `pytest_collection_modifyitems` hook);
  on the box (data present) they run. **Clean clone: 1554 passed / 196 skipped / 0 FAILED** (was
  48 failed); box: they run and pass. Whole-file granularity — robust across renames, at the cost
  of also skipping the non-corpus tests in those files on a clean clone. The honesty check surfaced
  **3 reds that were NOT corpus** (they failed WITH the data too) and were FIXED, never skipped:
  `test_site.py` ×2 (the self-contained pages added this session — checkit/about/halls/golf/tatami —
  were undeclared in its way-home + palette checks; declared as exceptions alongside mesh/live) and
  `test_present.py` ×1 (a stale allow-set — the `gate_record` provenance field, deliberately stored
  by `shelves.py:260`, added to the allowed facts). So Fable's "48 all corpus" was slightly off: 45
  corpus, 3 real.

## 5 · THE SEEDING, continued
Torrey's 96% unresolved-reference rate · Smith's + AmTract definitional cores · Matthew Henry
complete · the other 96 PD CrossWire modules · the probed-live open sources (NIST, openFDA,
DailyMed, NOAA, GBIF, OpenAlex). **Done when** substance passes 400,000.

## 6 · DISTRIBUTED
The airlock intake (path-not-payload) and node roles (personal · node · curator) with the signed
manifest. **Done when** a second machine serves a shard it verified against a signed manifest it
did not produce.

---

*Order is by what a real person feels first. The Commons is first because a library nobody can
contribute to is a monument, not a commons.*
