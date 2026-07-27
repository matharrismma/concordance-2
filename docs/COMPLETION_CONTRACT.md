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
3. One `capabilities-manifest.json`; all public counts derive from it.
4. Import/community quarantine + a minimal moderation floor (report/block) before any public community.
5. Result taxonomy on the surface: HOLDS / BROKEN_CLAIM / INCOMPLETE / OUT_OF_SCOPE / SYSTEM_ERROR.
6. Facts coverage (moon distance, boiling point, dates) so factual questions get the number.
7. Human plane: authority by shape+badge, gate explanations, first-success, WCAG AA pass.

## 7. Drift ledger (discoveries out of scope — recorded, not chased)

- _(append here as found; do not repair unless it is a security-critical dependency of the current item)_

---

*Completion is reached when §5 all pass against one named commit. The implementing model does not
declare completion in prose; the gates declare it.*
