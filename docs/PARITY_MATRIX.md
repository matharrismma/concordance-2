# 1.0 → 2.0 parity matrix (2026-06-28)

The honest distance between **1.0** (live on `narrowhighway.com`) and **2.0** (live on
`narrowhighway.org`), so the `.com` cutover decision is *falsifiable* — not a vibe.

**Headline:** 1.0 exposes **103 MCP tools** and **174 site pages**. 2.0 exposes **5 MCP tools**
(`verify, search, seal_fetch, resolve, word_study`) and ~5 site pages (landing, verify-demo,
search, seal, keep). 2.0 is **not** a feature-superset of 1.0 — it is a deliberately distilled,
hardened **engine + lean witness face**. The verification core is at parity-or-better; the
entire 1.0 **application layer** (atlas, almanac, workspace, shepherd, schools, missions,
scholar, dozens of reference lookups, the rich site) is **absent** from 2.0.

## By functional area

| Area | 1.0 surface (examples) | 2.0 status | Blocks .com cutover? |
|------|------------------------|-----------|----------------------|
| **Verification engine** | `check` + ~62 `verify_*` domain tools + `find_verifier`, `validate_packet`, `get_example_packet`, `attest_red/floor` | **CONSOLIDATED** — 2.0 has all 62 verifiers + the moat (58/58) behind ONE `verify` tool + auto-seal. Granular per-domain tools not individually exposed. | No (engine is parity); *but* a consumer that calls `verify_<domain>` by name breaks |
| **Polymathic / cross-domain** | `run_polymathic`, `polymathic_run`, `triangulate_claim`, `arrangement_probe` | **NONE** | If any agent flow depends on it — **yes** |
| **Seals / receipts** | `seal_packet`, the fabrication gauntlet | **PARITY+** — `/verify` auto-mints a re-checkable seal; `seal_fetch`; ledger bound | No |
| **Scripture / witness** | `scripture`, `resolve_scripture_ref`, `read_passage`, `lexicon`, `original_words`, `word_study`, `word_meaning`, `word_pronunciation`, `commentary`, `cross_references`, `concord`, `sermon` | **PARTIAL** — 2.0 has `resolve` (WEB) + `word_study` (Strong's). Missing: commentary, cross-refs, concord, sermon, pronunciation, read_passage, word_meaning | Witness-surface depth; not a secular blocker |
| **Keeping / library** | `cards_browse`, `card_get`, `card_notes`, `card_connections`, `cards_stats`, `cards_walk`, `search`, `locate`, `library_health`, `daily_card` | **MOSTLY PORTED** (2026-06-28, commit 099aa91) — 2.0 now has `search`, `card_get`, `cards_browse`, `cards_stats`, `daily_card` over the 11,138-card corpus (HTTP + MCP). Plus a browser **library page** (site/library.html — shelf filter, pagination, open a card). Still missing: card_notes, card_connections, cards_walk, locate, library_health. | mostly resolved |
| **Atlas / map** | `atlas`, `atlas_path`, `atlas_paths` | **READ-ONLY EXPOSED** (2026-06-28) — grid.py is now queryable: `GET /grid` (overview), `/grid?axis=`, `/grid/dimension?d=` + MCP `grid_axis`, `grid_dimension`. Path-finding (atlas_path) not ported. | mostly (path-finding optional) |
| **Almanac** | `almanac`, `almanac_search`, `propose_almanac_entry` | **NONE** | Yes, if almanac users exist |
| **Workspace / Walk / flow** | `walk_start`, `walkthrough_packet`, `cards_walk`, `flow_list`, `flow_run`, `scribe_submit` | **NONE** | **Yes** — the Walk is a primary 1.0 front door |
| **Shepherd / companion / learning** | `shepherd_answer`, `shepherd_interview`, `sermon`, `curriculum_list`, `mastery_mark`, `autonomy` | **NONE** — the *generative* companion is intentionally not in 2.0 (the engine verifies, it doesn't generate) | Decision: is the companion part of .com? **GATED** |
| **Schools / reading** | curriculum, phonics/reading school | **NONE** | If the school is on .com — yes |
| **Missions** | `missions` | **NONE** | Per the Acts-2 telos — **GATED** |
| **Scholar / external** | `scholar`, `wikidata`, `rfc_lookup`, `fetch` | **NONE** | No (additive) |
| **Reference lookups** | `drug_lookup`, `element_data`, `molar_mass`, `nuclide_data`, `food_nutrition`, `species_lookup`, `star_lookup`, `place_lookup`, `port_lookup`, `sequence_lookup`, `unit_convert/get`, `currency_convert`, `timezone_offset`, `economic_indicator`, `language_data`, `activity_mets`, `fluid_property` (~19) | **NONE as tools** (some data embedded inside verifiers) | No (additive), unless agents call them |
| **Site (HTML)** | 174 pages | **PARTIAL** — ~5 pages (landing, verify, search, seal, keep) | **Yes** — the rich site is the public face |

## What this means

- **2.0 can BE the .org** (it is — the witness/engine face) and is the right home for the
  verification core: it's hardened, sealed, tested, and honest.
- **2.0 cannot yet BE the .com** without regressing every user who relies on the keep, the
  Walk, the library, the schools, the almanac, the atlas, or the ~100 granular tools. The
  flip mechanism is trivial (see CUTOVER.md); the **loss** is the blocker.
- The cutover-blocking set, in rough priority: **keep/library → Walk/workspace → site →
  almanac/atlas → granular card+reference tools**. The companion/missions are separate GATED
  product decisions (the generative companion is intentionally absent from the engine).

## Recommendation
Do **not** cut `.com` to 2.0 as a replacement. Two honest paths:
1. **Keep the split** (current): 1.0 = `.com` (the application), 2.0 = `.org` (the verified
   engine + witness). Stable; ship 2.0 capabilities to `.org` and let 1.0 serve `.com`.
2. **Port piecewise into 2.0** — bring the keep, then the library/search UI, then the Walk,
   etc., each its own greenlit effort, re-running this matrix until 2.0 is a true superset.
   This is a **multi-session program**, not a single cutover — each surface is a decision.

(Counts: 1.0 = 103 MCP tools / 174 pages; 2.0 = 5 tools / ~5 pages, on 62 verifiers + the moat.)
