# Narrow Highway — Completion Contract (FROZEN 2026-07-25)

> Matt: *"We need to freeze and work towards this from this point forward. No deviation until we finish."*

This is the single authoritative definition of what Narrow Highway is, who it is for, the invariants it
must never break, and what "finished" means. From this point, work drives toward this contract. No new
surfaces, no renames, no scope expansion. Out-of-scope discoveries go in the drift ledger (below), not
into the build.

---

## 1. The mission (frozen — say this, everywhere, verbatim)

**Narrow Highway gives humans and agents a governed way to find, check, use, and preserve information
without losing its source, authority, or history.**

It is the five-part kernel stated for the world: **find · check · use · preserve — without losing
source, authority, or history.**

## 2. Who we serve — first

**Families, children, and communities that need us — the people who cannot afford to be without it.**
The governance is the means; serving the least is the end (Matthew 25:40). This is why the tool is
**free and needs no account**. Reach the market — homeschoolers, Christian schools, preppers, the radio
community, and makers/creators of anything — by serving the least within it first.

## 3. The invariants (the constitution — a change that breaks any of these does not ship)

**The five-part kernel** — every feature, card, response, and deploy must:
1. Find what is relevant. 2. Distinguish what kind of thing it is. 3. Verify what can actually be
verified (and decline the rest — a system failure is never a false verdict; ERROR ≠ BROKEN).
4. Preserve the trail. 5. Prevent authority from being silently upgraded (monotonic: saving, citing,
repeating, hashing, sealing never upgrade — only a real gate with evidence does).

**The gate record** — every pass/reject/quarantine answers nine fields: what entered · what kind of
object · what authority it carried · which gates it passed · which it failed · what assumptions ·
what changed · what was preserved · what can safely happen next.

**The agent covenant** — agents (and the operator's own agent) must: retrieve from corpora first;
distinguish citation from proof; quarantine generated material; request human authorization before
writes; produce a receipt for consequential actions; carry provenance through every transformation;
respect local data and identity boundaries; stop when evidence is incomplete.

**Response shape** — one discerned POV first, then the thinking with the sources. Have a POV; never
dump options; never omit the sources.

**Identity & access** — the tool has NO sign-in for anyone; every read works with zero account. Keys
are born on the device (WebCrypto/covenant/local), never minted or returned by the server; the server
holds only public keys and verifies signed challenges. The covenant (four verses / a sovereign key) is
the key to the Way, unlocked only after the statement of faith — *"Jesus Christ is Lord and Messiah."*
We open doors when sought; we never approach.

**Sovereignty & witness** — runs on our own box, offline-capable, stdlib-first, no per-call cost;
personal data stays local; nothing generated. A window, not a wall — points past itself to Christ.

## 4. The freeze rule

Do NOT, until this contract is satisfied: add an unrelated feature, introduce a new product surface,
rename foundational concepts, change the doctrine, or rewrite a working subsystem for style. DO: make
the gates universal, typed, visible, and non-bypassable; complete the worklist; prove, don't declare.
Discoveries outside scope → the drift ledger.

## 5. Definition of DONE (machine-testable — prove it, don't assert it)

- [ ] `PYTHONPATH=src python tools/check.py` → `=== GATE PASS ===` (currently 621 tests).
- [ ] `PYTHONPATH=src python tools/probe_usefulness.py` → ≥ 90% useful, no category at 0.
- [ ] Nesting: no orphans — every spine reachable from the Floor (`/floor`, `graph.overview`).
- [ ] Identity: no private key ever crosses the wire (`POST /identity/create` returns none; verified live).
- [ ] One mission string on every canonical surface (`/identity`, `llms.txt`, front door) — no drift.
- [ ] Security P0s closed: state-changing MCP tools require proof-of-possession; imports/community
      enter QUARANTINED, never cited/verified; SYSTEM_ERROR distinct from BROKEN on the surface.
- [ ] Counts derive from one canonical manifest (no hand-maintained public numbers).

## 6. The completion worklist (the finite set to finish — nothing else)

1. Wire the covenant into the Way (confession → establish key → node identity). *(in flight)*
2. Gate the state-changing MCP tools (badges/study_import/group_*) behind proof-of-possession + consent.
   *(**Proof-of-possession: DONE 2026-07-28.** Two mechanisms, both proven: detached signatures for
   messages (`mesh.signable_message`, `signable_door_note`) and two-phase attestation for
   server-built records (`attest.bear_witness` + `POST /attest`). No agent tool asks for or accepts a
   private key (`ccce761`); no HTTP handler does either (`af52593`); the browser signs locally
   (`4a86cf8`). Guards: `tests/test_mcp_no_private_keys.py`, `tests/test_no_keys_on_the_wire.py`,
   `tests/test_mesh_signed_speech.py`, `tests/test_attest_witnesses.py`.
   **Remaining for this item: CONSENT** — a human-authorized write path for agents (the agent covenant's
   "request human authorization before writes"). Possession is proven; permission is not yet asked.)*
3. One `capabilities-manifest.json`; all public counts derive from it.
4. Import/community quarantine + a minimal moderation floor (report/block) before any public community.
5. Result taxonomy on the surface: HOLDS / BROKEN_CLAIM / INCOMPLETE / OUT_OF_SCOPE / SYSTEM_ERROR.
6. Facts coverage (moon distance, boiling point, dates) so factual questions get the number.
7. Human plane: authority by shape+badge, gate explanations, first-success, WCAG AA pass.
8. **The "use" pillar — connect the user's OWN tools (Matt, 2026-07-26).** A pass-through to the
   tools they already carry — their calendar, email, storage — so Narrow Highway can *use*
   information without owning it. Bring-your-own-credential over standard protocols (iCalendar/
   CalDAV, IMAP, folder/WebDAV) now; OAuth one-click later (additive). Invariant: it is an EDGE
   capability — credentials stay on the user's box, reads happen in the moment, and **nothing is
   stored** (join their apps, never absorb their data). `src/concordance/connect.py`, read-only,
   store-nothing enforced by `tests/test_connect.py`. Write-back to a user's tools stays gated
   behind the agent-covenant write-consent path (worklist item 2).
9. **The last large build for V1 (Matt, 2026-07-27): "Like X-ray when you watch movies. We have
   everything that you can research. Already organized."** Every Bible-study back-matter resource,
   found and organized under the same invariants as the rest of the contract — real sourced text,
   never generated; disputed points shown as disputed, never flattened ("We live in the nuance").
   - Harmony of the Gospels — every gospel witness to an event, side by side. **DONE** (shipped
     2026-07-27, `src/concordance/harmony.py`, witness-gated `/harmony` + MCP tool + `harmony.html`).
   - OT / NT (Acts–Revelation) / church-history unified timeline — from creation through today.
     Where chronology systems genuinely disagree (Ussher vs. others on OT dates, early vs. late
     Revelation dating, etc.), present the competing systems side by side, not one settled view.
     **DONE** (shipped 2026-07-27, `src/concordance/timeline.py`, 100 events, witness-gated
     `/timeline` + MCP tool + `timeline.html`).
   - Maps/Atlas — real biblical place coordinates.
   - Back-matter reference material — topical index, weights/measures, parables/miracles lists,
     book introductions, names of God.
   - Commentaries — migrate Matthew Henry's data locally; evaluate adding Gill/Clarke.
   - Biblical Encyclopedia — built AS Cards in the existing corpus/Cards system (not a separate
     structure), with a clean card-catalog browsing interface ("the entire reference and
     nonfiction section of the library in a card catalog").

## 7. Drift ledger (discoveries out of scope — recorded, not chased)

- **§5's "no private key ever crosses the wire" was being read too narrowly (found 2026-07-28).**
  The server never *returns* a private key — but it *accepts* one in the request body at **five**
  places: `POST /mesh/post`, `POST /mesh/door`, `/badges` (attest), `/study/export`, and
  `/group/contribute`. (Corrected 2026-07-28: an earlier draft of this entry also listed
  `/mesh/tend` — that was wrong, it passes only fp/target/role. Verified by grepping
  `private_key` in `web/api.py`.) Inbound is still "on the wire", and §3 says keys "are born on the device… the
  server holds only public keys and verifies signed challenges". Root cause: those flows built the
  signable body server-side (minting the nonce and timestamp *after* the request), so no client
  could have signed the stored bytes — handing over the key was the only way to get a signature.
  **RESOLVED 2026-07-28 — §5's identity line now reads true as written.** The fix, in the order it had
  to happen:
  1. `mesh.signable_message()` / `signable_door_note()` — the caller gets the exact canonical bytes,
     signs locally, sends only the signature (`GET /mesh/signable`; `signature`/`nonce`/`created_at`
     on `POST /mesh/post` and `/mesh/door`). Commits `fe40334`, `498ff6a`.
  2. `src/concordance/attest.py` + `POST /attest` — the two-phase path for records whose hash the
     server builds (badges, study bundles, contributions): act unsigned → sign the returned
     `content_hash` locally → submit the attestation. Because attestations live beside the record
     rather than inside it, MANY parties can bear witness to one record, so `established` flips at two
     (Deut 19:15) instead of holding a single issuer signature. Commit `5c1feff`.
  3. No agent tool asks for a key: the three schemas that ADVERTISED `private_key` no longer do, and
     all refuse one — a schema is documentation an agent imitates. Commit `ccce761`.
  4. `site/nh-keys.js` — the key is born in the browser and never leaves it. This also fixed a LIVE
     BUG: `mesh.html` was calling `POST /identity/create` (which rightly 400s), so **human mesh
     onboarding was broken**. Commit `4a86cf8`.
  5. Only then: the `private_key` parameter removed from all five HTTP handlers (`af52593`). Order
     mattered — removing it before step 4 would have broken real users to satisfy a checklist.

  **The distinction kept deliberately:** `private_key` remains on the MODULE signatures, because on
  your own box, with nothing travelling, handing the library your own key is legitimate. It is gone
  only from the wire. Guarded by `tests/test_no_keys_on_the_wire.py`, which walks the HTTP layer by
  AST and flags ANY request-sourced key-shaped read (so a sixth handler cannot add one quietly), and
  which also asserts the local parameters still exist — if that assertion fails, the retirement went
  too far.

  **Corrected along the way:** an earlier draft of this entry listed `/mesh/tend` among the offenders.
  It never took a key. The count was FIVE, not six. Verify with
  `grep -n private_key src/concordance/web/api.py`.

- **§5.6's "SYSTEM_ERROR distinct from BROKEN" had never been implemented (found 2026-07-28).**
  Found by auditing §5 line by line instead of declaring it. `SYSTEM_ERROR` appeared in **zero**
  source files, and `verify_derivation` collapsed three different things into one word — its own
  comment admitted it: `else:  # MISMATCH / ERROR / broken link`. Reproduced through the public API:

      speed_of_wave=343,      frequency_hz=440, wavelength_m=99     -> BROKEN, broken_at='a'
      speed_of_wave="fast",   frequency_hz=440, wavelength_m=0.7795 -> BROKEN, broken_at='a'

  The first is a real falsehood. The second is **our verifier failing to parse an input**. Identical
  output. Someone checking a dose, a wage, or a load rating would be told their claim was false when
  the truth was that we could not check it. This is the mirror of the kernel's fifth clause: we guard
  against silently upgrading OUR authority, and here we were silently downgrading THEIR claim on the
  strength of our own bug. `receipts.py` compounded it — `"ERROR": "REJECT"` sealed engine failures as
  permanent, citable rejections — and `audit.html` labelled every non-confirmed claim `BROKEN` from a
  server field whose name already confessed the merge, `broken_or_unchecked`.

  **RESOLVED 2026-07-28.** `verify_derivation` now returns `SYSTEM_ERROR` with `error_at` and a
  `means` line; precedence is **BROKEN > SYSTEM_ERROR > INCOMPLETE > HOLDS** so honesty runs both
  ways — an engine error never becomes a hiding place for a genuine falsehood. `SYSTEM_ERROR` seals
  as QUARANTINE, never REJECT. The auditor now counts `broken` and `unchecked` separately (the sum is
  kept for existing callers). Every surface says it in words rather than showing a raw enum:
  `audit.html` ("NOT CHECKED", dashed, never the failure colour), `check.html`, `ask.html`, and — for
  parity — the MCP `verify` description and `llms.txt` both instruct agents never to relay it as a
  refutation. Guarded by `tests/test_system_error_distinct.py` (three of its tests fail against the
  pre-fix engine; verified by reverting).

  **A second, live instance surfaced when the gate ran.** `tests/test_security.py::test_expression_size_guard`
  asserted `verdict == "BROKEN"` for an expression over the 4k cap. So the same conflation was already
  reaching real callers by a different road: someone submitting a large but perfectly **true**
  expression was told their claim was false, when all that happened is that we declined to evaluate
  it. The test now asserts what it actually guards — refused cheaply, never evaluated, never sealed as
  holding — plus `broken_at is None` ("we found nothing false; we declined to look"). Worth noting the
  discipline: the expected value was changed only after confirming the *security* property still
  holds (refused in 0.000s, never HOLDS), not to make a red test go green.

  **Deliberately NOT done:** the §7 taxonomy also names `BROKEN_CLAIM` and `OUT_OF_SCOPE`, but the
  live vocabulary is `BROKEN` / `INCOMPLETE` across the engine, seals, tests and five pages. A
  sweeping rename for cosmetic conformance to a word would risk real breakage and buy nothing a
  reader can feel. The load-bearing half of §5.6 — the distinction a person actually relies on — is
  what was implemented.

---

*Completion is reached when §5 all pass against one named commit. The implementing model does not
declare completion in prose; the gates declare it.*
