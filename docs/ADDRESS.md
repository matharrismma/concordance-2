# THE ADDRESS — a Dewey decimal system for the next age of computing

Matt, 2026-07-29: *"We need better tagging for recall. The Dewey decimal system for the next age
of computing."*

---

## Why not Dewey

Dewey's genius was that a **notation is a location**: `220` *is* the Bible shelf, and a short
string tells you where a thing sits among everything else. That is exactly what we need.

His flaw is structural: **one hierarchy**. A book on the theology of music must choose between
230 and 780 and lose half of itself. Every single-tree scheme forces that loss, and our keeping
is explicitly *not* a single tree of subjects — it is one rooted tree of MEMBERSHIP crossed by
many planes (domain, semantic, temporal, scriptural, recurring-form).

Ranganathan is the better ancestor: an address **composed from independent facets** rather than
a path chosen from a menu. And the next age adds three requirements he never faced:

1. **Derived, not assigned.** A human cataloguer assigns Dewey numbers, so they drift and
   disagree. Our address is a **pure function of fields the card already carries** — so it
   regenerates from the corpus at any time, and a disagreement is a bug, not an opinion.
2. **Machine-parseable and prefix-searchable.** An agent must be able to ask for a *region*
   of the library without reading it: every prefix is a valid, meaningful query.
3. **Provenance and verification are part of the location.** In a library whose whole claim is
   "we never lose source, authority, or history," *who says so* and *was it checked* are not
   metadata hanging off a card — they are part of where it sits. A confirmed physics result and
   an unverified web claim about physics do not belong at the same address.

---

## The shape

```
  P.D.K / SUBJECT / A.V @ SOURCE
  │ │ │      │       │ │     └── source slug (the waybill's short name)
  │ │ │      │       │ └──────── V  verification state
  │ │ │      │       └────────── A  authority tier
  │ │ │      └────────────────── the subject key (stable slug)
  │ │ └───────────────────────── K  kind
  │ └─────────────────────────── D  domain
  └───────────────────────────── P  plane
```

Worked examples, from cards that exist today:

| card | address |
|---|---|
| Optics: theta2 deg (worked check) | `SCI.optics.CHK/snell-law/REF.CONFIRMED@engine` |
| Gill on John 3:16 | `WIT.scripture.EXP/john-3-16/REF.WITNESSED@john-gill` |
| Hitchcock: Aaron | `WIT.onomastics.FCT/aaron/REF.WITNESSED@hitchcock` |
| Nave: mercy | `WIT.scripture.IDX/mercy/REF.WITNESSED@nave` |
| Ginger monograph | `PRA.apothecary.MON/ginger/REF.MIXED@herbs` |
| A member's recipe | `PRA.cookery.MBR/sourdough-starter/MBR.UNCHECKED@shelf-a1b2` |

**The facets** (each a closed vocabulary, each already present in our data):

- **P · plane** — `WIT` witness · `SCI` science/math · `PRA` practical · `HUM` humanities ·
  `OPS` the system's own operations. The coarsest cut; five values, deliberately few.
- **D · domain** — the ~64 verifier domains, plus `scripture`, `onomastics`, `cookery`… The
  existing shelf name, canonicalised (this is why shelf names had to stop being aliases).
- **K · kind** — `FCT` fact · `CHK` worked check · `EXP` exposition · `IDX` index ·
  `MON` monograph · `TXT` primary text · `MBR` member work · `OBJ` operational object.
- **subject** — a stable slug. The one part a human types.
- **A · authority tier** — `SCR` scripture · `REF` reference · `MBR` member · `WEB` unverified
  web. Already a field; now visible in the address.
- **V · verification state** — `CONFIRMED` · `WITNESSED` · `UNCHECKED` · `COULD-NOT-CHECK` ·
  `BROKEN` · `MIXED`. The three-state honesty, made addressable.
- **@ source** — the waybill's short name, so the address always answers *who says so*.

## Why this improves recall

- **Every prefix is a query.** `SCI.optics.CHK/` = every worked optics check. `WIT.*.IDX/` =
  every topical index across the witness plane. `*.*.*/mercy/` = everything addressed to mercy,
  from any source, at any authority. No new index is needed — prefix matching over a sorted
  address column is a B-tree away.
- **Recall stops depending on wording.** Today a reader finds Gill on John 3:16 only if their
  words happen to match his. The address makes the *position* findable regardless of phrasing —
  which is precisely what Dewey did for a physical shelf.
- **Authority and verification become filters, not surprises.** "Show me only CONFIRMED
  science" and "show me the tradition, marked as tradition" become one-line queries instead of
  careful reading.
- **Agents get a deterministic locator.** An MCP client can name a region of the library and
  fetch it without a similarity search — a real address, not a guess.
- **Collisions are informative.** Two cards at the same address but different sources are
  exactly the case we want visible: *the same claim, witnessed twice.* That is the
  Deuteronomy 19:15 shape appearing in the notation itself.

## The disciplines it must keep

- **Derived only.** The address is computed from existing fields. Nothing is hand-assigned, so
  it can be regenerated for all 548,585 cards and compared — drift is then a failing test, not
  an argument. A card whose facets cannot be determined gets `UNPLACED` and is **reported**,
  never guessed into a bucket.
- **No silent reclassification.** If a card's address changes, the old one is kept as an alias
  so external citations never break. Addresses are permanent; the *tree* may be reorganised,
  the *pointer* may not vanish.
- **It never overrides the nesting.** `member_of` remains the load-bearing tree (zero orphans).
  The address is a coordinate, not a container — the same lesson as the planes: crossings are
  vias, not new homes.
- **Faceted, so nothing has to choose.** Theology of music is `WIT.music_theory.EXP/…`, and it
  is reachable from the witness plane *and* the music domain. Nothing is lost to make it fit.

## Build order (bounded, gated, measurable)

1. `src/concordance/address.py` — the pure derivation function + parser + validator. No writes.
2. **Measure before adopting**: derive addresses for all cards; report how many are `UNPLACED`,
   how many collide, and the distribution per facet. If a facet is mostly unknown, the
   vocabulary is wrong and gets fixed *before* anything is stored.
3. A gate test: every card derives a valid address; `UNPLACED` stays under a named ceiling;
   the derivation is stable across runs (same input, same address).
4. Add `address` to the card render, `/search` output, and the MCP surface — **the guarantee
   must reach the reader**, or it is a private index.
5. Prefix-query route + a browse-by-address surface (the card catalogue's real drawers).
6. Only then: store it in the shards for B-tree prefix search at scale.

*Nothing here is stored or claimed until step 2 says the vocabulary survives contact with
548,585 real cards.*

---

## MEASURED 2026-07-29 — the vocabulary FAILED its own gate (v1)

Step 2 said: *derive for all cards, and if a facet is mostly unknown, the vocabulary is wrong
and gets fixed before anything is stored.* It ran against all **548,585** cards:

| result | count |
|---|---:|
| addressed | 302,361 (55.1%) |
| **UNPLACED** | **246,224 (44.9%)** |

Why, in order: **204,136 cannot determine plane** · 20,200 no subject · 17,109 no kind+authority
· 2,631 no plane+authority.

**So nothing was stored.** A coordinate system that cannot place 45% of the library is not a
Dewey for the next age; it is a filing cabinet with the drawers missing. The design holds — the
*first vocabulary* is wrong, in a specific and cheap way:

- My plane tables were hand-written and missed the **largest shelves in the keeping**:
  `dictionary` (149,490), `geography` (69,135), `taxonomy` (37,933), `oeis`, `rfcs`,
  `networking`, `nuclide`, `star`… Together those are nearly all of the 204,136.
- **Fix**: stop hand-listing. Derive the plane from machinery that already classifies every
  shelf — `corpus_db.SHARD_ASSIGN` (core/word/science/world/dictionary/books) crossed with the
  verifier registry — and fall back to `surface` only as a last resort.
- **20,200 cards carry no subject or title** worth slugging. That is a *corpus* finding, not an
  address finding, and it belongs in GAPS: a card nobody can name is a card nobody can recall.
- Authority resolved to only `REF` (301,857) and `SCR` (504) — no member or web tier exists yet,
  which is correct today, but it means the facet is currently carrying almost no information.

**What DID work, and is worth keeping:** the parser round-trips every derived address; the
verification facet correctly found the 123 worked checks (119 `MIXED` — truth *and* refusal on
one card — plus the sealed ones); and **23,697 coordinates already collide across sources** —
the same subject witnessed twice, which is the Deuteronomy 19:15 shape appearing in the notation
by itself, exactly as designed.

Prefix querying works mechanically but is misleading until coverage is fixed: `SCI.` matched 141
of a 40,000-card sample because most science shelves are currently UNPLACED, not because the
science is absent.

**Status: v1 measured and rejected. `src/concordance/address.py` is STAGED — imported by
nothing, stored nowhere.** Next session: replace the hand-written plane tables with the derived
classification above, re-measure, and only proceed past 90% placement.

## v3 — MEASURED AND ACCEPTED, 2026-07-29

| version | addressed | what changed |
|---|---:|---|
| v1 | 55.1% | hand-written plane tables — **rejected** |
| v2 | 96.8% | planes DERIVED from `SHARD_ASSIGN` × the verifier registry; non-Latin titles fall back to ref/id; a named source implies REF authority |
| **v3** | **99.97%** | added `REL` — a minted edge is a *relation*, not a subject; split `card_src_` so a dictionary headword is `FCT` and a book is `TXT` |

**548,440 of 548,585 cards addressed. 145 UNPLACED (0.03%)**, each named by shelf (the-works 66,
sources 12, mathematics 7, atlas 3, chemistry 3) rather than absorbed into a default.

Facet spread — the test of whether a facet is real: `FCT` 360,898 · `TXT` 115,939 ·
`EXP` 49,495 · `REL` 17,182 · `IDX` 4,690 · `CHK` 123 · `OBJ` 101 · `MON` 12. In v2 `TXT` alone
was 84% of everything, which meant the kind facet distinguished nothing; the fact/text split
fixed it. **23,789 coordinates collide across sources** — the same subject witnessed twice.

Gated by `tests/test_address.py` (6 tests): the parser round-trips, every prefix is a query,
derivation is deterministic across repeated calls, a card with nothing to go on still comes back
`UNPLACED`, coverage holds above a 90% floor over the REAL corpus, and **no single facet value
may exceed 90% of the library** — so the collapse that made v2 useless fails the gate instead of
passing quietly.

**Still STAGED, deliberately**: nothing stores the address yet. Steps 4–6 (render it on the card
page, `/search` output, and the MCP surface; then a prefix-query route; then the shard column)
remain — because an index the reader cannot see is a private index, and that is the one failure
this project keeps re-learning.
