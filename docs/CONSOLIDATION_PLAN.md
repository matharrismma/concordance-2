# THE CONSOLIDATION — one tight-knit project

Matt, 2026-07-31: *"We should be consolidating tools. Not making more… It has to assemble into one
thing at the end."* · *"Be ruthless. Cut anything that doesn't align."* · *"13 pages. 12 plus home."*
· *"Tools are different than pages."*

**Five surfaces, counted separately, because they are different things and a target on one says
nothing about another.** Every number below is measured, not estimated. Nothing is deleted:
everything cut is archived to the 12 TB ark with a hash first, per the standing rule that a removal
is a record, never an erasure.

> **These targets are SCRIBE LINES, not commitments.** Matt, 2026-07-31: *"Target numbers, names,
> and theories are initial targets. We always step back and reframe at intervals to work ourselves
> closer and closer to truth. Just like a wood worker will scribe a line until center is found."*
> A number here is a first mark taken from one edge. `docs/THE_NAMING.md` is the second cut, taken
> from the side of *what each thing does* — and it moved the page line by finding duplicate JOBS
> (−7) that no traffic ranking could see. Where two marks disagree, that gap is the finding; the
> number is revised out loud, never defended.

| surface | now | target | cut |
|---|---:|---:|---:|
| **Pages** | 45 | **13** | 32 |
| **MCP tools** | 79 | **~40** | ~39 |
| **HTTP routes** | 147 | measure first | — |
| **src modules** | 168 | measure first | — |
| **Shelves** | 103 | ~34 | 69 |

---

## 1 · PAGES → 13 (12 + home)

**Measured:** 45 exist. **9** clear 50 hits. **13 have ZERO.** The top 5 hold 75.6% of all page
traffic.

### The correction that has to come first
`encyclopedia.html` is the #1 page at **4,209 hits and it is not a page** — a 1,000-byte JS-only
stub marked `noindex`. `canon.html` (3,041) is a Caddy 301 that **drops the `?ref=`**. They are busy
because **4,743 cards cite them as their source URL** — 2,619 → encyclopedia, 2,124 → canon.

So the order is forced: **repoint the citations, then retire the two shims.** Retiring them first
would break 4,743 provenance chains; repointing first makes the shims genuinely unused.

### The proposed 13
Traffic alone is the wrong knife — `shelf.html` is one day old, and `mesh.html` is hidden by design.
So: traffic, **plus** mission, **plus** age.

| # | page | hits | why it stays |
|---|---|---:|---|
| 1 | `index.html` | home | the front door |
| 2 | `characters.html` | 344 | the Bible Dictionary — and the true destination of encyclopedia's 4,209 |
| 3 | `bible.html` | 87 | the Word. Non-negotiable |
| 4 | `read.html` | 92 | the K-3 reading tutor — "serve families first" |
| 5 | `library.html` | 66 | the keeping |
| 6 | `ask.html` | 58 | the conduit / the Gate |
| 7 | `almanac.html` | 65 | verified-only facts |
| 8 | `journal.html` | 66 | the member's own record |
| 9 | `steward.html` | 55 | household money, never moves it |
| 10 | `community.html` | 49 | study together |
| 11 | `shelf.html` | new | THE COMMONS — one day old, the current build |
| 12 | `mesh.html` | hidden | The Way — V1 capstone, found only when revealed |
| 13 | `map.html` | 46 | the connection map |

**On the bubble, and I want a decision rather than my guess:** `walk.html` (42), `prophecy.html`
(42), `codex.html` (42), `seal.html` (39), `guarantees.html` (35), `works.html` (31),
`keep.html` (23, the operator console — arguably not a "page" at all).

### Method
1. Repoint 2,619 dictionary citations → `/characters.html?search=REF`.
2. Bring the mapping for the 2,124 canon citations **before** touching them — `aurelius_aur_07_xxiii`
   is an internal slug and the honest destination may be the card itself, not a site page.
3. Archive the 32 to the ark, hash-verified, then remove.
4. Caddy: the retired paths 301 to their true destination, so no citation anywhere dies.
5. `daily.html` (116 hits) and `hymns.html` (96) are **404s that do not exist** — either restore or
   remove the links pointing at them. 212 hits into nothing.

**Done when** `site/*.html` = 13, the gate passes, every retired path resolves somewhere true, and
`tools/assay_cards.py` reports zero cards citing a shim.

---

## 2 · MCP TOOLS → ~40

**First, a correction I owe this document.** The earlier plan said "collapse 71 near-identical
`verify_*` tools." **There are none.** All 79 live tools are distinct; the 71 `verify_*` belong to a
*different, locally-registered* MCP server in my own environment. I planned the largest item of a
consolidation on a misread of my own tooling. Measured properly:

**40 tools sit in 13 families; 39 are singletons.**

| family | n | collapses to |
|---|---:|---|
| `coach_*` | 7 | `coach(action=…)` |
| `mesh_*` | 6 | `mesh(action=…)` |
| `study_*` | 4 | `study(action=…)` |
| `group_*` | 4 | `group(action=…)` |
| `identity_*` · `shelf_*` · `curate_*` | 3 ea | one each |
| `card_*` · `cards_*` · `grid_*` · `steward_*` · `badges_*` · `word_*` | 2 ea | one each |

40 → 13 is **−27**. Add the singleton review (`cross_references` vs `tsk_cross_references`;
`character_get` vs `characters_browse` vs `cards_browse`) for roughly **79 → ~40**.

### The tension worth naming before we swing
An MCP tool's *description is the documentation an agent reads.* One fat tool with a `mode`
parameter can be **worse** for discovery than three clear ones — and agents are 35% of our traffic,
so this surface is our most-read documentation. The rule I propose: **collapse a family only when
the members share a subject and differ by verb** (`coach_next` / `coach_overview` → yes).
**Never collapse across subjects** to make a number look better.

**Done when** the tool list is ~40, every capability still reachable, `tests/test_mcp*.py` green,
and a live agent walk proves nothing was lost.

---

## 3 · SHELVES → ~34

**69 of 103 hold fewer than 50 cards.** A shelf is a top-level organising idea; two-thirds are
aspirational. Prior passes fought this and it refilled (33 → 20 one-card shelves, now regrown).

**Method:** propose the 69→N mapping **as a document Matt reads first**, then apply. A shelf rename
touches search ranking, `SHARD_ASSIGN`, the zero-orphan invariant, and the nesting tests — this is a
data migration, not a tidy-up. **Never a silent rewrite.**

---

## 4 · ROUTES (147) and MODULES (168 src + 62 tools) — MEASURE BEFORE TARGETING

I have a count and **no evidence** about which are dead. Setting a target now would be the same
error as the `verify_*` miscount. First: which routes were called in the whole access log, and which
`tools/*.py` are one-shot carders that already ran. **Then** a number.

---

## 5 · EXPAND WHAT IS PROMISING

Consolidation is not shrinkage everywhere. Three things earn *more*:

- **`/card` — 46,190 hits.** The real front door. Now carries the overlay and adjoining links; next
  is making its citation resolve (see §1).
- **`/search` — 16,210.** Now carries authority tier. Next: it is throttling the use we want
  (217 × 429).
- **The MCP surface — being indexed by agent registries.** Fewer, better-described tools is itself
  the expansion.

---

## THE STANDING RULES FOR THIS WORK

1. **Nothing is deleted — it is archived to the ark with a hash, then removed.** A removal is a
   record. *(THE_RECORD.md)*
2. **Never a silent rewrite.** Mappings that touch cards are proposed and read first.
3. **Measure before targeting.** Two plans tonight were built on miscounts; both were caught by
   checking, and neither would have been caught by reading.
4. **Add nothing unless it removes more than it adds.**
5. **The gate arbitrates.** Nothing is done because it is written here.

---

*Order: §1 pages (after the citation repoint) → §2 tools → §3 shelves → §4 measure → §5 expand.*
