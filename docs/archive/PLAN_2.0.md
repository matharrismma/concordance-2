# Concordance 2.0 — Hardening & Completion Plan

*Finalized 2026-06-28. Every load-bearing claim below was re-verified against the live repo at `C:/Users/hdven/OneDrive/Documents/Claude/Projects/concordance-2` (not the 1.0 `Lighthouse` tree). Where an earlier draft was wrong, this version corrects it and says so.*

## Vision

2.0 is a clean, sovereign rebuild of the engine: one foundation (the Bible, Christ at center), one going train (engine → gates → verifiers → record → CAS → ledger), two surfaces (`secular`/.com reach, `witness`/.org named) over a shared keeping. The architecture is genuinely sound — frozen dataclasses, a single `EngineConfig` seam, truly lazy heavy deps, zero required dependencies, the math moat verified at 58/58 with 0 false-positives and the pole guard catching `x/x=1`.

The goal of this plan is to make 2.0 **trustworthy and complete enough to eventually BE the .com without loss** — while honoring the ethos at every step: it points to Christ and never poses as the idol; it stays sovereign and stdlib-first; the 0-false-positive moat is sacred; and **the map never launders** — including this plan, which is corrected below so that no recommendation rests on an unverified assumption about the world the engine is deployed into.

## The two truths that reframe everything

**Truth 1 — The headline promise is not yet deliverable.** `cas.store` / `seal_record` / `validate_and_seal` are called **only from tests**. In the live request paths, `web/api.py:94` and `mcp/server.py` call `cas.fetch` — never `store`. `/verify` returns `{verdict, trail}` with no `content_hash` and no `cite_url`; `/seal` can only ever 404 for a real user because nothing on the public path ever wrote a seal. So "every AI answer is trust-me; this one hands you a receipt" is **architecturally present but unreachable.** This is WS1.

**Truth 2 — We do not actually know what is live on .com, and the repo's own artifacts contradict the brief.** The brief states "narrowhighway.com = 1.0, untouched." But `deploy/nh-com.service` in *this* repo runs `python -m concordance serve --port 8000 --surface secular` from `/home/nh/concordance-2`, and `deploy/Caddyfile` proxies `narrowhighway.com` → `127.0.0.1:8000`. If that unit is enabled on the droplet, **the standing "do NOT re-cut .com to 2.0" decision is already contradicted by the deploy files** — and every "SAFE, does not touch .com" label in this plan is unverified. Therefore **WS0 (audit the live droplet) gates the SAFE classification of everything else** and must run first. I could not reach the droplet from this environment; the local tree shows no `data/cas` or `data/ledger` at all, which strongly implies the live seal store is empty (consistent with Truth 1).

## Dimensions assessed

| Dimension | Status | Severity of gaps | Notes |
|---|---|---|---|
| **Deploy topology / environment** | UNVERIFIED — repo artifacts point 2.0 at .com:8000 | **High** | WS0. Must audit the droplet before trusting any SAFE label. |
| **The floor wiring (receipt)** | Present but **unreachable** on live paths | **High** | WS1. The project's whole thesis. |
| **Public surface security (keep/DoS/MCP)** | **Live keep auth bypass**; no body cap, rate limit, or timeout | **High** | WS2. Keep is effectively public on .org now. |
| **RED schema gate** | **Total live no-op** — schema file absent, `jsonschema` undeclared | **High** | WS3. Reclassified up from the draft's P3. |
| **Enforced regression gate (CI/coverage)** | Absent (no `.github/`, no coverage) | **High** | WS4. Integrity gate is manual. |
| **Canonical-JSON unity** | Two non-interoperable forms | **Medium** (Greek/Hebrew) | WS5. Migration almost certainly moot (empty store). |
| **FLOOR attestation gate** | Empty registry → attestation pass-through (math IS still checked) | **Medium** | WS6. Corrected framing. |
| **False-positive gate breadth** | Only math + ~6 domains guarded; ~55 unguarded; 122 aliases untested | **Medium** | WS7. |
| **Backups of generated data** | None | **Medium**, rising to High once WS1 ships | WS8. Empty today. |
| **Live integrity checks / watchdog** | None scheduled; keep re-hashes ledger each poll | **Medium** | WS9. |
| **Seam leaks / dead grid map** | Witness code eagerly imported on secular; grid carries dead 1.0 weight + a data bug | **Low–Medium** | WS10. |
| **Trust-boundary clarity** | Telemetry shown beside ledger as if co-authoritative | **Low** | WS11. |
| **1.0 → 2.0 feature parity** | **Un-inventoried**; ~90 MCP tools + library/walk/shepherd/schools/almanac/codex/atlas/grid have no 2.0 equivalent | **High for the stated goal** | WS12. The actual gate on "BE the .com." |
| **Witness / theology overlay** | Unreviewed (reviewer returned a stub) | Unknown | WS13. |

## What is verified (the strengths to protect)

- The deterministic going train is faithful and fail-closed: `derivation.verify_step` catches any verifier exception → `ERROR`; `engine` REJECTs on schema failure *when a schema is present*; **RED verifier dispatch (the actual math) runs independently of the empty domain-validator registry** (`engine.py:149-164`) — so a medicine packet with wrong dosage math is still REJECTed at RED today.
- Sovereignty is real: `pyproject` declares zero required deps; `cryptography`/`sympy`/`scipy`/`numpy` are genuinely lazy; `jsonschema` degrades to a structural fallback.
- The "no `final_answer` field" doctrine is enforced *structurally* in `record.py`.
- CAS, ledger hash-chain, and Ed25519 detached signing are correctly implemented and tested in isolation.
- The benchmark is a real exit-code gate (`tools/benchmark.py`).

These must not regress.

---

## Workstreams (prioritized)

### WS0 — Audit the live droplet (gates every SAFE label) *(Priority 1, SAFE — read-only)*
The plan's repeated "does not touch .com" assurances are **unproven** while the repo ships an `nh-com.service` pointing 2.0 at :8000. Resolve reality before acting.

- On the droplet: `systemctl status nh-com.service nh-org.service`; confirm which process owns :8000 and :8001; read the **live** Caddyfile (not the repo copy) to see what `narrowhighway.com` actually proxies; confirm whether 1.0's serving stack is still the one bound to .com.
- Confirm live `data/cas` and `data/ledger` are empty/absent (informs WS5/WS8 stakes).
- Confirm `CONCORDANCE_KEEP_TOKEN` is or isn't set in the running `nh-org` unit.

**Acceptance:** a written, dated statement of what serves .com and .org right now, whether `nh-com.service` is enabled, whether the keep token is set, and whether the seal store is empty. Until this lands, no workstream below may be marked "verified SAFE on the live box."

### WS1 — Wire the floor: actually hand a receipt *(Priority 1, SAFE)*
Make the central promise true.

- Mint a seal in the live `/verify` path (and MCP `verify`): after the verdict, build a `WitnessRecord` (via `validate_and_seal` or a thin `derivation→record` adapter), `cas.store()` it, append via `seal_record`, return `{verdict, trail, content_hash, cite_url}`.
- **Honest failure policy (corrected per critic):** sealing is downstream of and must never alter the verdict — but a HOLDS that *fails to seal* must surface that fact (`seal: null` + reason). It must **never** present a verdict as receipted when it wasn't. "Hands a receipt" must not silently degrade to "usually hands a receipt."
- Bind the ledger chain to the sealed record's `content_hash` (today `seal_to_ledger` chains a human-summary projection, not the CAS address — a swapped CAS record wouldn't break the chain).
- Make `seal.html` round-trip end to end.

**Acceptance:** POST `/verify` on a HOLDS claim returns a resolvable `content_hash`; GET `/seal?hash=…` returns the same record; `cas.verify(hash)` is True; tampering a CAS record is detectable via the ledger; a forced CAS-write failure returns `seal:null` with a reason, never a bare receipted-looking verdict; round-trip covered by a test.

### WS2 — Close the public-surface security holes *(Priority 1; code fixes SAFE, alert destination GATED)*
The keep is **live on .org and effectively public.** Confirmed: `api.py` resolves `client_ip` from the **leftmost** `X-Forwarded-For` hop (`...split(",")[0]`), and `keep.is_operator` returns True whenever `client_ip in {"127.0.0.1","::1","localhost","",None}`. A forged `X-Forwarded-For: 127.0.0.1` passes the gate; behind a default Caddy `reverse_proxy` the socket peer is 127.0.0.1 regardless.

- **Fix the keep gate IN CODE first (defense-in-depth, not reliant on the proxy):** require `CONCORDANCE_KEEP_TOKEN` for *any non-loopback TCP peer*, decided on `self.client_address` (the real socket peer), **ignoring `X-Forwarded-For` for the operator decision entirely**; remove `""`/`None` from `_LOCAL` (fail closed); use `hmac.compare_digest`. Set the token in `nh-org.service`. Additionally set `header_up X-Forwarded-For {remote_host}` in the live Caddyfile — but treat that as belt-and-suspenders, since the repo Caddyfile may differ from the live one (WS0).
- **Body cap + compute timeout:** reject `content-length` over a cap (e.g. 64 KB) with 413 before reading `rfile`; wrap `verify_derivation` in a hard timeout + sympy complexity guard so a crafted expression returns ERROR/QUARANTINE, never a hang (systemd `Restart=on-failure` does NOT recover a hang).
- **Rate limiter:** stdlib token-bucket keyed by the real socket peer on `/verify`, `/search`, `/mcp`; 429 + Retry-After.
- **MCP compliance (HTTP and stdio):** validate `Origin` against an allowlist on the HTTP transport (DNS-rebinding defense); map tool exceptions to generic messages (stop echoing `str(e)` in `server.py`/`scripture.py`) — apply the same error-leak/size hygiene to the **stdio** MCP path, which the draft omitted; add `X-Content-Type-Options: nosniff`, `Cache-Control: no-store` on keep.
- **Watchdog/alerting destination GATED on Matt** (see WS9).

**Acceptance:** a remote request with forged `X-Forwarded-For: 127.0.0.1` and no token gets 404 to `/keep*` **even when XFF says loopback** (regression test using the socket peer); a 10 MB body → 413; a pathological expression → verdict within N seconds; burst → 429; cross-origin browser request without an allowed Origin rejected; no error response contains a file path (HTTP and stdio).

### WS3 — Make the RED schema gate real *(Priority 1, SAFE — reclassified UP from the draft's P3)*
**Corrected severity.** There is **no `schema/` directory and no `packet.schema.json`** anywhere in 2.0; `engine._DEFAULT_SCHEMA_PATH` (`parents[2]/"schema"/"packet.schema.json"`) points at a non-existent file, so `load_schema` raises, `_get_schema` returns None, and `if schema is not None:` skips validation. **The RED "malformed input" guarantee is a 100% no-op today, in dev and prod.** And `jsonschema` is not a declared dependency, so even with a file, validation silently degrades to `validate._fallback_validate` (required-fields + `additionalProperties` only). This is a live integrity hole on par with the missing receipt, not a packaging chore.

- Write a real `schema/packet.schema.json` (or formally adopt the structural fallback as the contract and document it as such — no laundering: pick one and name it).
- Declare `jsonschema` as an optional `validation` extra (or accept fallback-as-contract explicitly); install it in the deploy env if jsonschema is the contract.
- Package the schema under `src/concordance/` (or add package-data) so it ships in the wheel.
- Make schema absence **loud**: log + surface `schema_active` on `/health` and the keep; in a non-dev config, a missing schema should fail startup or visibly flag, never silently no-op.

**Acceptance:** a malformed packet is REJECTed at RED on a fresh install; `/health` reports `schema_active: true` in prod; the schema ships in the wheel/site deploy; the chosen contract (jsonschema vs fallback) is documented.

### WS4 — Establish the enforced regression gate (CI + coverage) *(Priority 1, SAFE)*
Confirmed: no `.github/`, no CI, no coverage tooling.

- CI workflow: install `.[math,signing,validation,dev]`, run `python tools/benchmark.py` (fail build on non-zero exit) and `pytest -q` on push/PR; pin `sympy`/`cryptography`/`jsonschema`/`pytest`. Gate .org deploys on green.
- Add `coverage` under `[dev]`; floor on the integrity core (`cas, ledger, signing, record, engine, derivation, validate`).
- Add the `signing = ["cryptography"]` extra (currently only under `math`), and fix `signing.py`'s wrong install string (`concordance-engine[signing]` → `concordance[signing]`) and its stale 1.0 docstring references.

**Acceptance:** a PR introducing one false-positive or breaking any test cannot merge; integrity-core coverage above the floor; the documented signing install command works.

### WS5 — Unify the canonical form & protect the witness hashes *(Priority 2, SAFE)*
Confirmed two non-interoperable canonical forms: `cas.py:42` and `record.py:168` use `json.dumps(..., sort_keys, separators)` at default `ensure_ascii=True`; `validate.canonical_json_bytes` uses `ensure_ascii=False`. For Greek/Hebrew these produce different bytes and different SHA-256.

- Route `cas.content_hash_of`, `record.to_dict`, and `ledger.compute_content_hash` through one shared canonicalizer (recommend `ensure_ascii=False`).
- Add a regression test sealing a record containing Greek + Hebrew, asserting all three hashes agree and re-verify.
- **Migration anxiety downgraded (per critic):** with `data/cas`/`data/ledger` absent locally and no live mint path (WS1), the live store is almost certainly empty, so unifying is a clean switch, not a migration — **confirm via WS0 before assuming.**

**Acceptance:** grep finds exactly one canonical-JSON implementation; a non-ASCII seal round-trips and re-verifies across CAS, record, and ledger.

### WS6 — Wire the protective FLOOR attestation gate *(Priority 2, GATED on Matt for scope/rules)*
**Corrected framing.** `_DOMAIN_VALIDATOR_REGISTRY = {}`, so `dv` is None and the engine emits "no domain validator registered" for both RED-validator and FLOOR (`engine.py:147,173`). This does **not** mean safety math is unguarded — RED verifier dispatch still runs (WS-verified). What is absent is the **attestation gate**: the "reference not advice" required-attestation rejection for medicine/herb/giving is carried only by verifier docstrings, not gate-enforced. This must exist before any .com cutover.

- Populate the registry with FLOOR attestation checks for the safety-critical domains (medicine, herb, giving) so a packet missing its required attestation is REJECTed at FLOOR.
- Tests cover one true and one false case per ported domain.
- *GATED:* which domains carry which rules is Matt's call (it shapes the named medicine/witness guarantees).

**Acceptance:** a medicine packet missing attestation is REJECTed at FLOOR; per-domain true/false tests pass; docs state plainly that the math is checked at RED and the attestation is checked at FLOOR (no conflation).

### WS7 — Extend the false-positive gate beyond mathematics *(Priority 2, SAFE)*
Confirmed: `test_verifiers.py` has real true/false pairs for ~6 domains; the rest get an empty-packet smoke test proving only "imports and doesn't throw." The 0-false-positive promise is *measured* only for the math moat + 6 domains; ~55 modules (medicine, law, finance, statistics, cryptography, nuclear_physics…) have no false-positive guard.

- Build a data-driven gate: ≥1 TRUE and ≥1 FALSE case per verifier module, aggregated into a single false-positive count asserted == 0. Prioritize high-stakes domains. **Do not count empty-packet smoke tests as guards.**
- Test that every one of the 122 registered domain aliases routes to its intended module. **Tightened acceptance (per critic):** the routing check must use a *known-TRUE/known-FALSE* canonical pair, so it proves the verifier is correct — not merely that two wrong answers match.

**Acceptance:** the gate reports one aggregate false-positive count across all domains and it is 0; each alias is proven to reach the right verifier *and* return the correct verdict on a labeled case.

### WS8 — Back up the new generated data *(Priority 2, GATED on off-site destination)*
Confirmed: no backup script; `DEPLOY.md` silent. 1.0 has `backup_substrate.sh` + crons + off-site; 2.0 has nothing for `data/cas`, `data/ledger`, `data/activity.jsonl`, `cards.jsonl`, `bible_en.jsonl`, `data/strongs`.

- Ship a backup script (tar the data paths, sha256 the tar, copy off-site, document restore + post-restore `verify_chain`). Wire a cron/timer.
- **Stakes note (per critic):** the seal store is empty today, so there is nothing irreplaceable to lose *yet*. Ship the script early but **schedule the cron to start the moment WS1 lands** — backups become critical exactly when minting begins. Do not call empty-dir loss "unrecoverable integrity loss" today.
- *GATED:* the off-site destination is an outward operational choice.

**Acceptance:** a scheduled backup produces a checksummed off-box archive; a documented restore + `verify_chain` succeeds on a test box.

### WS9 — Schedule live integrity checks & cheapen the keep *(Priority 3, GATED on alert destination)*
Confirmed: `verify_chain` is tested only against tempdir ledgers; nothing runs it against live data; `keep.dashboard` re-runs `verify_chain` (re-hashes every file) + `cas.stats` on every poll.

- Cron/timer on the .org box: run `verify_chain` + a `cas.verify` sweep against live data; exit non-zero and notify on any tampered/broken-link/missing record. *(Becomes meaningful once WS1 mints seals.)*
- Cache `verify_chain`/`cas.stats` (TTL 30–60s) or maintain incremental counters updated on seal-write, so the keep poll doesn't re-hash the whole ledger.
- systemd `WatchdogSec` + `sd_notify` heartbeat (or external cron curling `/health`) so a hung process is restarted, not just a crashed one.
- *GATED:* alert destination/channel is Matt's outward choice.

**Acceptance:** a deliberately corrupted seal triggers a non-zero check + visible alert within the window; keep.json latency stays roughly constant as the ledger grows; a simulated hang is restarted automatically.

### WS10 — Close the seam leaks & trim/repair the grid map *(Priority 3, SAFE)*
- **Lazy-import scripture at the seam:** confirmed `web/api.py:25` and `mcp/server.py` eagerly `from ..verifiers import scripture` even on the secular surface — the .com process loads witness code it must never surface, contradicting `PORT_PLAN` hotspots #1/#6. Move the import inside the `if config.witness_surfaced:` branches.
- **Trim/quarantine `grid.py`:** only `AXIS_DIMENSIONS`/`UMBRELLAS` are consumed by the floor; the rest is 1.0 carry-over (DIMENSION_KIND, retag machinery, CLI). Extract the consumed slice or quarantine the rest behind a labeled "extended map (off the floor)" boundary; fix the stale docstring.
- **Fix the grid data bug + add an invariant:** `biology` maps onto `discreteness`, which is NOT in `_BASE_DIMENSIONS` (the ported "missing-1" bug). Add `discreteness` to the declared members or correct the mapping, and add a load-time assertion that every axis dimension is a declared member.

**Acceptance:** importing `concordance.web` with `surface='secular'` does not import `concordance.verifiers.scripture` (assert via `sys.modules`); the member-set invariant test passes; `grid.py` shrinks and its docstring matches reality.

### WS11 — State the trust boundary loudly *(Priority 3, SAFE)*
- Add an explicit trust-boundary statement (keep docstring, keep.html, STATUS doc): the ledger hash-chain + CAS are the authoritative integrity record; the activity log is best-effort, unsigned, and tamperable. Visually separate them so an operator can't mistake activity counts for sealed truth.

**Acceptance:** the keep visibly distinguishes authoritative vs advisory; the STATUS doc names which subsystems are tamper-evident and which are not.

### WS12 — Inventory the 1.0 → 2.0 feature-parity delta + define a reversible cutover *(Priority 2, GATED on Matt; the real gate on the headline goal)*
**Elevated from the draft's hand-wave (per critic).** The brief's cutover bar is "2.0 carries the keep + the 1.0 features users depend on." 1.0 has ~90 MCP tools and library/workspace/walk/shepherd/schools/phonics/almanac/codex/atlas/grid surfaces; 2.0 has a verification engine, a lean site, and the keep. Calling 2.0 "complete enough to BE the .com" while treating this delta as out-of-scope makes the headline goal unfalsifiable.

- Produce a **gap matrix**: every 1.0 surface and MCP tool → has a 2.0 equivalent / partial / none. This makes the true distance visible so Matt can prioritize.
- Define a **reversible cutover** (the honest way to honor "no regression"): run 2.0 alongside 1.0 on a distinct port/subdomain, shadow-test against real traffic, and require a **one-command revert** (DNS/Caddy flip back to 1.0) before any flip. 1.0 is backed up to the 12TB drive, but its *live serving stack* must not be displaced without a tested rollback.

**Acceptance:** a committed gap matrix; a documented alongside-run + shadow-test procedure; a tested one-command rollback that restores 1.0 serving on .com.

### WS13 — Complete the owed witness/theology review *(Priority 4, GATED on Matt for priorities)*
The witness/theology reviewer returned only a probe stub. Before 2.0 carries the .org named-foundation guarantees, a real review is owed: scripture ref-resolution on the WEB bible, Strong's word-study, canon layering (`canon.py` + canon-aware `verify_scripture_anchors`), theology/witness verifiers — checked against the ethos (points to Christ not idol; show-don't-crown on disputed canon; never launder a doctrinal claim as verified).

**Acceptance:** a written witness-overlay review with severities; canon layering confirmed historically-framed and non-over-claiming; doctrinal verifiers confirmed to attest only what is checkable.

---

## Sequencing

1. **WS0 first (read-only).** Resolve the live topology and seal-store state. Until done, treat every "SAFE" label as provisional.
2. **Then the integrity foundation, in parallel (all SAFE):** WS2 keep-gate sub-task (close the live auth bypass — most urgent; exploitable on .org now), WS3 (real schema gate), WS4 (CI), WS1 (wire the receipt). WS4 should land early so WS1/WS3/WS5 changes are gated by it.
3. **Then:** WS5 (canonical unity — clean switch if WS0 confirms empty store), rest of WS2 (DoS, MCP HTTP+stdio hygiene), WS7 (fp gate — depends on WS4 harness), WS10 (seam + grid), WS11 (trust boundary).
4. **Right after WS1 ships:** turn on WS8 (backups) and WS9 (live integrity checks + watchdog) — they become meaningful the instant minting begins.
5. **Gated tier (need Matt):** WS6 (FLOOR scope), WS8 dest, WS9 alert dest, WS12 (parity + cutover), WS13 (witness review).
6. **Cutover-blocking set** (ALL must be true before .com becomes 2.0 without loss): WS0 (topology known + intentional), WS1 (receipts deliverable), WS2 (surfaces secured), WS3 (RED schema gate real), WS5 (hashes unified), WS6 (FLOOR attestation enforced), WS8 (backups live), **and WS12 (parity matrix resolved + reversible cutover)**. The draft's five-workstream cutover set was necessary-but-insufficient; WS12 is the actual gate.

## Risks

- **Wiring the seal could perturb the moat.** Keep sealing strictly downstream of the verdict; never let CAS/ledger touch verifier output. WS4's gate is the safety net. But (per the seal honesty policy) a seal failure must be *surfaced*, never swallowed into a receipted-looking verdict.
- **The .com face may already be 2.0.** Until WS0, do not assume the live secular surface is 1.0; the repo's deploy files say otherwise. Any "SAFE" step that "doesn't touch .com" is unverified until the droplet is audited.
- **Canonical-form change could be a hash migration** — but almost certainly isn't, because the seal store appears empty. Confirm via WS0; if any real seals exist, decide migrate-vs-reseal deliberately.
- **Don't launder coverage.** WS7 must add *real* false cases and labeled alias-routing checks; an empty-packet smoke test must never be counted as a guard.
- **Seal permanence vs privacy (ethos).** Auto-minting a permanent, content-addressed record of every query — including user claim text — is a privacy/permanence decision that sits in tension with telemetry's existing query-text truncation. This is why the seal policy (WS1) is an open question, not a default.
- **Cutover without rollback is the one irreversible move.** WS12's tested one-command revert is the guardrail against the "no regression for users" promise being broken.

## What is gated on Matt

- Whether `nh-com.service` is intended to be live (and thus whether .com is *already* 2.0) — and what the standing decision now means in light of the repo artifacts.
- Any .com cutover or running 2.0 alongside 1.0 (standing decision) — and the reversible-cutover design (WS12).
- FLOOR domain scope and exact attestation rules (WS6).
- Off-site backup destination (WS8) and alert destination/channel (WS2 watchdog, WS9).
- Seal policy: always-on-HOLDS vs opt-in (WS1) — tied to the privacy/permanence stance, not just "receipt vs record."
- Canonical-form migration vs clean switch, pending WS0's confirmation that the live store is empty (WS5).
- The schema contract decision: real JSON Schema + `jsonschema` dependency, or structural fallback formally adopted as the contract (WS3).
- Priorities/red lines for the owed witness/theology review (WS13).
- MCP registry publish / DNS / anything that changes the live public face.