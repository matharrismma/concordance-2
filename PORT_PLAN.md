# Port Plan — the parts manifest

A watch has a bounded, counted parts manifest, solved and locked before assembly. So does this.
Port only the **gold** from 1.0 (`v1.0-frozen`); machine each part clean; verify; check it off.
Put the jewels on the seams (the contact points between subsystems get the most care).

Legend: `[ ]` todo · `[~]` in progress · `[x]` done & verified

## Movement — the deterministic core (sovereign, stdlib hot path)

- [x] `config` / `branding` / `layers` — the surface seam (one foundation, two surfaces) + seam test
- [x] `packet` / `gates` / `verifiers/base` / `validate` — verdict types · gate constructors · verifier base · schema+hash helpers (ported as-is)
- [x] `record` (was `witness_record`) — sealed-result schema, **SourceLayer un-hardcoded** (`Anchor.layer: str`, validated from config) — hotspot #2 closed; 6 core tests green
- [x] `cas` — content-addressed seal store (SHA-256, 256-way sharded) — ported as-is
- [x] `engine` — `validate_and_seal`: claim → gates → verifiers → (verdict, trail, seal); gates **RED·FLOOR·PATH·WITNESS·WAIT** (WAY→PATH, BROTHERS→WITNESS, GOD→WAIT; neutral scopes local/mesh/archived) — hotspots #4/#7 closed; 6 engine tests green
- [x] `verifiers` registry (`run_for_domain`, lazy) + `domains` loader (`load_domain_validator`) — the two seams the engine plugs into
- [x] `ledger` — append-only **hash chain** (prev_hash links, verify_chain catches tampering) + `seal_record` wiring **seal→CAS→ledger** — 4 ledger tests green. `find_closest` (precedent search) deferred — needs the grid
- [ ] `foundation/` — truth-model + the disciplines (docs) + Scripture substrate hook (shared)
- [ ] `signing` — Ed25519 attestation (optional crypto, graceful degradation)
- [x] `ranker` — `corpus.py`: IDF inverted-index retrieval, distinctiveness-floored, **surface-filtered**
      (#7 BUILT; fixture + real-corpus proven). **Floor now 7/7.** `tools/migrate_cards.py` consolidates
      the keeping → `data/cards.jsonl` (gitignored, 11,085 cards). ⚠ CLASSIFICATION DECISION FOR MATT:
      the shelf-based surface tag is COARSE — the keeping is ~Christian, so Easton's Bible Dictionary
      (2,619), Pilgrim's Progress/Pirkei Avot (classics), and scripture-connections (5,095) are tagged
      "secular" but are religious and would LEAK onto the .com. Genuinely-secular slice ≈ 50 cards
      (maker/recipes/atlas/animation). The ranker is correct; the .com's secular CORPUS must be defined
      (content-level reclassify · fresh secular corpus · or .com = engine-only, no library).

## Complications — the verifiers (mount on the train; each earns its place)

- [x] secular verifiers — **60 modules mounted** (118 domain names + aliases), copied byte-faithful
      (all import only `from .base`; heavy deps sympy/scipy/numpy lazy, present locally). ALL load+run
      on an empty packet (tests/test_verifiers.py load-guard) + 7 behavior cases across math-moat,
      number_theory, information_theory, geometry, physics, finance (confirm truths / catch falsehoods).
      DEFERRED: `governance` (carries a 1 Cor 14:40 anchor → hotspot #5 strip first), `giving` /
      `layer_zero_grounding` (review). WITNESS-surface verifiers (scripture/theology/witness) = .org.
- [x] `derivation` moat — `verify` / `verify_step` / `verify_derivation` (mode→verifier→verdict,
      first-break-governs); the crown jewel, the engine verifies, never generates
- [x] **benchmark GREEN — 58/58, 0 false-positives** (LOCAL `tools/benchmark.py` + `tests/test_benchmark.py`
      regression gate). The 5 removable-singularity traps caught; the symmetric rational identity held
- [ ] conditional registration by `surface` for the witness verifiers (hotspot #6)

## Witness surface (.org) — config-gated, NOT a separate install

- [x] `theology_doctrine` + `witness` verifiers — surfaced ONLY when `surface=witness` (WITNESS_VERIFIERS
      map + `surface` threaded through run_for_domain + the engine). 4 witness-surface tests green: the
      witness surfaces them, the secular reach does not, the secular path is unaffected
- [x] `canon` — layered canon ported (self-contained)
- [x] `scripture` (ref resolution) — LEAN port on the WEB verses (data/bible_en.jsonl, 31,098 verses,
      public domain, gitignored; tools/migrate_bible.py). resolve_ref → WEB text (incl. abbreviations
      Jn/Mt/Ps...) + verify cited anchors (ref resolves; quoted text matches), witness-surface-gated,
      graceful when data absent. 5 scripture tests green. Strong's / word-study / original-language
      triangulation DEFERRED — needs the lw/00_source backend (a separate subsystem).
- [x] governance: **de-laundered secular port** — structural checks kept (decision-packet shape,
      witness-count consistency, decision timing, rationale alignment, domain profiles for
      business/household/education); the 5 scriptural anchors + "church" profile removed from the
      core, scopes neutralized (local/mesh/archived). Hotspot #5 closed. Proven true+false.

## Case + dial — the thin web layer (later)

- [ ] `web/` — handlers · services · generation (flagged LLM edge) · data · middleware
- [ ] verify/seal/search API (the floor, exposed)
- [ ] MCP server — conditional tool registration by surface
- [ ] `web/witness/` routers (/shepherd /codex /scripture) — surfaced when `surface=witness`

## Dial faces — the site (later)

- [ ] real build step (templates, no 211 hand-authored pages); `.com` secular + `.org` witness builds
- [ ] minimal: what it is · "bring a claim → get a receipt" demo · the seal viewer

## Data contracts to preserve (from 1.0)

- ledger entry (seq, packet_hash, prev_hash, entry_hash — the hash chain) · CAS seal record
- card schema (migrate 800 files → keyed/indexed JSONL) · case-store nearest-neighbor (rebuildable)

## Refactor hotspots (the 9 religion-coupling points → the surface seam)

1. eager `scripture` import → lazy  · 2. `SourceLayer` hardcoded → injected  · 3. `IDENTITY` at
import → injected (done in `branding`)  · 4. witness layer-check → config  · 5. governance anchor →
witness  · 6. MCP eager theology import → conditional  · 7. grid "scripture" axis → pluggable  ·
8. WAY gate comments / "canon" scope → neutral  · 9. app.py religious endpoints → witness routers
