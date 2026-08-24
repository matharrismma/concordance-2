# Conductor Canon — Corrections before integration

**Source:** the red team of CONDUCTOR CANON + NARROWHIGHWAY DOMAIN SORT (2026-08-24).
**Authority:** Matt directed "follow that path" (the red team's six-step safe-integration path), 2026-08-24.
**What this file is:** the corrections that must hold before any Conductor code integrates with the
live engine. The patched reference (`conductor/reference.py`) and its tests
(`tests/test_conductor_reference.py`) implement §4 of this document. The canon in iCloud is the
vision; this file is the amendment layer the red team required.

---

## 1. Ratifications (constitutional calls, recorded so they are conscious, not slipped in)

These touch the FROZEN mission, so they are named in the open per the project's own discipline.

- **D-1 — Efficiency-first front door. RATIFIED (Matt, "follow that path", 2026-08-24).**
  The `.com` front door leads with the working verification tool in plain English — no theology, no
  gate names, no architecture vocabulary. The confession is **not hidden**: it moves off the front
  door but stays **whole** at `/about` and the identity endpoint, and the footer links to it. This is
  the Areopagus pattern (name the Source when asked), not a retreat from it. Mitigation is structural:
  the declaration is one click away and complete.
- **D-2 — "Keeping is paid" with a preserved free floor. RATIFIED (same).**
  The free **checking** (verify/audit) stays free, no account, for everyone — that is the mission
  floor and it is never gated behind the paid tier. The paid **keeping** (a shop's accumulating
  sealed records) uses **sovereign Ed25519 identity only** — no username/password account, consistent
  with the covenant. The paid tier is additive; it never stands in front of the free tool.
- **Scope note.** Integrating the Conductor expands the project from "the Concordance" into *also* a
  manufacturing-federation business. The canon subordinates business to mission (firstfruits before
  harvest; non-extractive; "the mission is the moat"), and that ordering is the condition of the
  expansion: the free family/teaching floor is never drawn below to feed revenue.

## 2. §4 "What already exists" — corrected against the live repo (cite ≠ prove)

The canon's audit table overstated two rows. Corrected:

| Canon claim | Reality (verified 2026-08-24) |
|---|---|
| "722-claim benchmark at 100%" | **No such benchmark.** The real one is a **60-case** derivation-moat set (30 true / 30 false), and its claim is deliberately BOUNDED: *0 false positives on 60 cases; establishes nothing beyond them* (`docs/BENCHMARK.md`). Do not cite 722 or "100% accuracy." |
| "API key auth at narrowhighway.com" | **Does not exist.** Auth is sovereign Ed25519 + the gate + the operator token for `/keep`. There is no API-key layer (`src/concordance/web/api.py`). Build against sovereign identity, not API keys. |
| validate_packet / attest_red / attest_floor | **True** — `src/concordance/engine.py`. |
| Candidate Engine (candidate_commit/narrow/get) | **True** — `src/concordance/mcp/server.py`. |
| The four gates | **True and already named in the kernel** — see §3. |

**Rule going forward (the canon's own SOP-11):** no case study, demo, or spec may cite a number that
is not a live query/verified result. The 722 error is exactly what that rule exists to prevent.

## 3. Gate reconciliation — the Conductor's gates are a DOMAIN PROFILE under the live kernel

The canon's gates are not new and must not redefine the kernel's. The live kernel
(`src/concordance/engine.py`) runs **RED → FLOOR → PATH → WITNESS → WAIT**; it renamed the old
BROTHERS→WITNESS and GOD→WAIT. Mapping:

| Canon name | Live kernel | Reconciliation |
|---|---|---|
| RED (spindle rpm, coolant, tolerance) | RED (hard reject) | Manufacturing envelope is a **domain profile layered UNDER** kernel RED. Kernel **RED-005 (identity branding, Rev 13:16-17)** and **RED-006 (harm to children)** in `constraints.py` STILL GOVERN — the shop envelope adds to RED, never replaces it. |
| FLOOR (margin, tool life, capacity) | FLOOR (hard reject) | Shop economics are a FLOOR domain profile; the kernel FLOOR semantics remain. |
| *(absent)* | **PATH** | The Conductor omitted PATH. The reference adds a fail-closed **INPUT/presence** step in its place; production delegates to the kernel's PATH. |
| BROTHERS | **WITNESS** (quarantine) | Rename to WITNESS. Irreversible → 2 human witnesses; the agent identifies the need, never witnesses. |
| GOD | **WAIT** (quarantine) | Rename to WAIT. Timing/discernment hold. |

Verdict lattice: the kernel's WITNESS/WAIT **quarantine** (they do not hard-halt); RED/FLOOR hard
reject. Map the Conductor's WAIT/HOLD onto the kernel's quarantine authority state
(quarantined < cited < verified). In production the reference gates DELEGATE to
`attest_red` / `attest_floor` / `validate_packet`; they do not re-implement the kernel.

## 4. Reference bug fixes (implemented in `conductor/reference.py`, locked by tests)

| # | Finding | Fix | Test |
|---|---|---|---|
| C1 | Nutrient export leaked price/margin out of the building via the nested `reusable` dict on a gate-trip packet (top-level denylist). ITAR/EAR exposure. | Export is a strict **allowlist**, applied **recursively**; only named boundary-knowledge fields leave; the sound work is kept locally under `_private_reusable` and never exported. | `test_export_never_leaks_money_even_on_a_gate_trip`, `test_success_quote_exports_no_numbers` |
| C3a | Gates PASSED by omission (FLOOR skipped absent fields). | Fail-closed **presence gate** first: a missing required field HALTs (CANNOT_CHECK ≠ PASS). | `test_missing_required_field_halts_not_passes` |
| C3b | RED defaulted a missing `tolerance_source` to the accepted value. | No default: a tolerance-bearing payload with a wrong/absent source trips RED. | `test_tolerance_without_source_halts` |
| C3c | WITNESS bypassable via the input's own `irreversible=False`. | Irreversibility is decided by a **rule over the work** in dispatch; a raw flag can ratchet up, never down. | `test_irreversibility_is_ruled_not_self_declared`, `test_irreversible_action_waits_for_witnesses` |
| C3d | A disguised CRISIS defaulted to a QUOTE. | classify() is **crisis-first**, confidence-scored; unknown → CLARIFY, never a silent QUOTE. | `test_crisis_is_first_and_never_a_quote`, `test_unknown_work_clarifies_never_guesses_quote` |
| C4 | Unsigned ledger; integrity claim overstated. | Honest docstring (hash chain = corruption evidence, not forgery resistance) + optional Ed25519 **signer seam**; production passes the engine's signer. | `test_hashchain_detects_corruption`, `test_signature_seam_resists_forgery` |

## 5. Scoped OUT of the build (honor the canon's own gates + Claude's hard limits)

- **Settlement layer past rung 1.** Money transmission is regulated state-by-state; the canon itself
  gates it behind a payments attorney + partner bank. Claude may build the **record-keeping** (sealed
  invoice packets) only. Claude will **not** build money-movement/clearing/payfac/token systems and
  will not give financial or investment advice.
- **Defense / ITAR / EAR / CMMC.** No controlled technical data may cross the mycelium. The allowlist
  export (C1) is the structural guard; do not widen it without an export-control review.
- **Federated joint-bidding / "virtual prime."** Antitrust and joint-employer structure is a
  human-plus-counsel decision, not a code feature.

## 6. M0 is now safe to start (next increment)

With §1–§5 in hand, M0 may begin, one milestone per session (SOP-01). **M0 exit criteria:** a work
order flows capture → `validate_packet` → chain end-to-end using only existing organs; the reference
contracts are ported as a **thin package over the engine** (gates delegate to
attest_red/attest_floor/validate_packet); `contracts.py` frozen with a CI surface check.

**Repo decision (Claude, rationale recorded):** the Conductor package lives at `conductor/` **inside
concordance-2**, not a separate `Lighthouse` repo — because the canon's own rule is "connect to the
engine, never rebuild," and same-repo makes the connection trivial and reuses the test/deploy harness.
It is portable to a separate repo later if Matt directs. The canon's `github.com/matharrismma/Lighthouse`
reference is superseded by this decision unless overridden.

---

*The reference is canon for behavior; this file is the amendment the red team required. Efficiency is
the front door; the confession is whole at /about. Checking is free; keeping is paid. He is risen.*
