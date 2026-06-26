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
- [ ] `foundation/` — truth-model + the disciplines (docs) + Scripture substrate hook (shared)
- [ ] `ledger` — append-only hash chain + precedent search — *already clean, port as-is*
- [ ] `signing` — Ed25519 attestation (optional crypto, graceful degradation)
- [ ] `ranker` — IDF/full-text retrieval over the keeping

## Complications — the verifiers (mount on the train; each earns its place)

- [~] secular verifiers — **1/57 mounted**: `combinatorics` (proves the pipeline end-to-end).
      Remaining 56 port next — lazy-load (no eager scripture import, hotspot #1 already avoided);
      heavy deps (sympy/scipy/numpy) lazy
- [ ] conditional registration by `surface` for the witness verifiers (hotspot #6)
- [ ] **benchmark** ported and GREEN (58/58, 0 false-positives) — the regression gate, the proof

## Witness surface (.org) — config-gated, NOT a separate install

- [ ] `scripture` / `theology_doctrine` / `witness` verifiers — surfaced only when `surface=witness`
- [ ] `canon` — layered canon
- [ ] governance: keep the structural check in core; anchor surfaced on witness (hotspot #5)

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
