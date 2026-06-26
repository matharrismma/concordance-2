# Port Plan — the parts manifest

A watch has a bounded, counted parts manifest, solved and locked before assembly. So does this.
Port only the **gold** from 1.0 (`v1.0-frozen`); machine each part clean; verify; check it off.
Put the jewels on the seams (the contact points between subsystems get the most care).

Legend: `[ ]` todo · `[~]` in progress · `[x]` done & verified

## ✅ 2.0 COMPLETE — built end to end, every part verified

Engine + scripture depth + front door + polish, all green. **63 tests across 14 suites; the
derivation moat 58/58 with 0 false-positives; every module imports; AGPL-3.0 + CC-BY-SA.** One
sovereign engine (stdlib-first; sympy/scipy/numpy/cryptography optional + lazy), Christ at the
foundation (FOUNDATION.md + `foundation.py`), two surfaces — `.com` reach, `.org` witness.
Run: `python -m concordance serve`.

**Honestly deferred (optional / not blocking, flagged not faked):** precedent amendments
(`latest_in_amendment_chain` returns id unchanged); morphhb/morphgnt deep morphology (the Strong's
lexicons + concordance are in); an MCP server (the HTTP API covers agents); a templated build + the
`.org` witness site (the lean site suffices now). **Deployment configs PREPARED** — Dockerfile ·
`deploy/Caddyfile` · `deploy/nh-com.service` + `nh-org.service` (the two surfaces) · `docs/DEPLOY.md`
runbook; env-var data loading (`CONCORDANCE_DATA_DIR`) validated live. **Deploying to
narrowhighway.com is the operator's — outward/gated (DNS + droplet + Caddy).**

## Movement — the deterministic core (sovereign, stdlib hot path)

- [x] `config` / `branding` / `layers` — the surface seam (one foundation, two surfaces) + seam test
- [x] `packet` / `gates` / `verifiers/base` / `validate` — verdict types · gate constructors · verifier base · schema+hash helpers (ported as-is)
- [x] `record` (was `witness_record`) — sealed-result schema, **SourceLayer un-hardcoded** (`Anchor.layer: str`, validated from config) — hotspot #2 closed; 6 core tests green
- [x] `cas` — content-addressed seal store (SHA-256, 256-way sharded) — ported as-is
- [x] `engine` — `validate_and_seal`: claim → gates → verifiers → (verdict, trail, seal); gates **RED·FLOOR·PATH·WITNESS·WAIT** (WAY→PATH, BROTHERS→WITNESS, GOD→WAIT; neutral scopes local/mesh/archived) — hotspots #4/#7 closed; 6 engine tests green
- [x] `verifiers` registry (`run_for_domain`, lazy) + `domains` loader (`load_domain_validator`) — the two seams the engine plugs into
- [x] `ledger` — append-only **hash chain** (prev_hash links, verify_chain catches tampering) +
      `seal_record` wiring **seal→CAS→ledger** + **`find_closest`** (precedent overlay onto a verdict:
      grid-dimension Jaccard blended with anchor overlap) — 4 ledger + 5 precedent tests green
- [x] `grid` — the axes/scaffold map (886 lines, stdlib, 117 axes; data/grid/axis_extensions.jsonl
      optional + graceful). Feeds find_closest + record.axis_coords_for. The scripture/theology axes
      stay (the grid is the shared conceptual map — we are not hiding)
- [ ] `foundation/` — truth-model + the disciplines (docs) + Scripture substrate hook (shared)
- [x] `signing` — Ed25519 attestation (optional `cryptography`, graceful when absent). Detached
      `sign_seal`/`verify_seal` over a seal's content_hash (no circularity); `seal_record(sign_key=)`
      attaches a verifiable attestation. 3 signing tests green.
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
      now DONE (see the `strongs` backend below).
- [x] `strongs` backend — original-language triangulation ported (lookup/concordance/drift_check,
      stdlib sqlite3+json) over data/strongs/ (web.db + concordance.db + Strong's Greek/Hebrew
      lexicons, ~31M gitignored; tools/migrate_strongs.py; ROOT via CONCORDANCE_STRONGS_DIR).
      `scripture.word_study(strongs)` → lexicon definition + every occurrence (G26 ἀγάπη: 36 verses),
      witness-gated, graceful when absent. morphhb/morphgnt deep morphology not migrated (optional).
      4 strongs tests green.
- [x] governance: **de-laundered secular port** — structural checks kept (decision-packet shape,
      witness-count consistency, decision timing, rationale alignment, domain profiles for
      business/household/education); the 5 scriptural anchors + "church" profile removed from the
      core, scopes neutralized (local/mesh/archived). Hotspot #5 closed. Proven true+false.

## Case + dial — the thin web layer (later)

- [x] `web/api.py` — **sovereign stdlib HTTP API** (zero deps; pure testable `dispatch()` + a thin
      `serve()` http.server shell), BOTH surfaces via EngineConfig: GET /health · /identity ·
      POST /verify (the moat) · GET /search (shared keeping) · /seal (the receipt) · /resolve +
      /word_study (witness-gated). 7 API tests green.
- [ ] MCP server — conditional tool registration by surface (optional; the HTTP API covers agents for now)

## Dial faces — the site (later)

- [x] **Narrow Highway** (narrowhighway.com) — lean static site: landing ("wisdom & discernment by
      narrowing the possibilities"), the live "bring a claim → receipt" demo (POST /verify), search,
      the seal viewer, an honest link to .org. Served **same-origin** by `python -m concordance serve`
      (the API serves the static site too). 4 site tests + a live end-to-end smoke (health, index,
      moat HOLDS/BROKEN, search, witness-gating) — all green.
- [ ] (later) a templated build + the .org witness build, if the page count grows; minimal suffices now.

## Data contracts to preserve (from 1.0)

- ledger entry (seq, packet_hash, prev_hash, entry_hash — the hash chain) · CAS seal record
- card schema (migrate 800 files → keyed/indexed JSONL) · case-store nearest-neighbor (rebuildable)

## Refactor hotspots (the 9 religion-coupling points → the surface seam)

1. eager `scripture` import → lazy  · 2. `SourceLayer` hardcoded → injected  · 3. `IDENTITY` at
import → injected (done in `branding`)  · 4. witness layer-check → config  · 5. governance anchor →
witness  · 6. MCP eager theology import → conditional  · 7. grid "scripture" axis → pluggable  ·
8. WAY gate comments / "canon" scope → neutral  · 9. app.py religious endpoints → witness routers
