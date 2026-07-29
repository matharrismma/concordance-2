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

- **⚠ THE ENTRY BELOW WAS WRONG — corrected 2026-07-28, same night, before it was acted on.**
  It reported "313,944 cards with no edge" and "1.15% connected". **The real number of unconnected
  cards is 15.** Of 466,006 non-connection cards, **465,991 carry an inline `connections` array** —
  460,707 `member_of` their shelf spine, plus 4,384 `cites`, 1,752 `proof_text`, 7,099 `same_section`,
  234 `precedes`.

  What I had actually measured was `graph.overview`'s `connected` count, and **the graph builder reads
  only cards of `kind == "connection"` (17,182 of them); it never looks at the inline `connections`
  field.** So "not rendered on the map" got reported as "unconnected in the keeping". Those are
  different claims, and only the second one would have been alarming.

  This is the SECOND time a ledger entry of mine overstated (the first: `/mesh/tend` in the
  private-key entry above). A ledger that overstates is the drift it exists to catch. Both times the
  cause was identical — **reporting a probe's output as if it were the thing the probe was named
  after.** Before writing a number here, state what was literally counted.

  **What survives as real findings:**
  1. **A LEAK, not a backlog — and it was worse in production. RESOLVED 2026-07-28.** The 15 local
     strays all came from ONE path: `find._mint_doc` (the tortoise, which fetches public-domain
     sources when the corpus cannot answer) wrote a literal `"connections": []`. Every source it kept
     was born an orphan, one more per fetch. **The live box had 41.** Fixed at the source: two spines
     (`card_spine_practical`, `card_spine_sources`) defined **in code, not in a data file** — because
     `data/web_cache.jsonl` is untracked, so a data-file spine would be absent on a fresh box and the
     leak would return — written before the card that hangs off them. The `member_of` restates a fact
     the card already carries (its shelf), so it cannot be a weak edge.
     `tools/graft_orphans.py` backfilled from the live corpus. **Box: 41 → 4. Local: 15 → 0.**
     Guarded by `tests/test_nothing_is_isolated.py`, which pins the MINT PATH end-to-end, not the
     instances — reverting `find.py` to `"connections": []` fails it.

     **The 4 that remain need Matt's decision, and the tool refused to guess.** Running it on the box
     surfaced a third shelf that does not exist locally: `web`, holding four Wikipedia cards
     (`Telephone`, `Sinking of the Titanic`, `Printing press`, `Food preservation`), created
     2026-07-23, `verified: false`. **No code in `src/` on either side mints them any more** — they
     are residue of a retired open-web fetch path, and Wikipedia is CC-BY-SA, not public domain,
     which collides with the standing PD-only gate. So the options are to give `web` a spine that
     states its real (unverified, non-PD) authority tier, or to remove the four. That is a doctrinal
     call plus a data deletion, so it was left flagged rather than defaulted. The tool now grafts
     what is certain, names what is not, and exits non-zero — holding 37 unambiguous cards hostage
     to 4 unclear ones would have been its own kind of failure.
  2. **The map under-reported the nesting. RESOLVED 2026-07-28.** `graph.overview` showed the
     authored constellation (connection cards) and not the `member_of` tree, so anyone reading it to
     answer "is anything orphaned?" got the wrong answer — as I did. The design was right and the
     numbers did not carry it: `planes.nesting` already held the skeleton, and the code's own comment
     said "the WHOLE keeping — nothing isolated". Only `connected` was reported, and a fully-nested
     shelf with no authored edges (`gutenberg`, 77,700 cards) read as `connected: 0` and looked
     abandoned.

     Every card now falls in **exactly one** bucket, per shelf and in total, so no category can hide
     in a difference — `nested + semantic_only + isolated == total_nodes`, asserted:

         total 465,983 = nested 460,821 + semantic_only 5,162 + isolated 0

     and each count carries a `means` line (the rule `/capabilities` already follows), with
     `connected_nodes` explicitly warning against the misreading that happened. Computed in the
     existing single pass — no extra cost.

  2b′. **RESOLVED 2026-07-28 by Matt's decision (final refinement).** Matt chose, from explicit
     options: **(a)** the four Wikipedia cards are **removed** (consistent with the standing PD-only
     rule; the mint path was already retired); **(b)** the islands are rooted with **shelf spines,
     the found relation** — `tools/graft_shelf_spines.py` minted nine spines (`codex`, `classics`,
     `patristics`, `the-works`, `animation`, `hymns`, `maker`, `recipes`, `atlas`) rooted `part_of`
     the Floor, redirected `dictionary`'s 2,619 and `chemistry`'s 1 structurally-bare cards to their
     siblings' established parents (`card_spine_words`, `card_k_spine_created_order`), and grafted
     **5,187 cards** across six data stores; **(c)** per-page navs stay as they are — the prior
     decision stands. After the graft: **unreachable 552 → 0; every card nested; the ratchet in
     `tests/test_reachable_from_the_floor.py` lowered to 0.** The per-card scripture matching (codex
     "Revelation 5" → that scripture card) remains deliberately NOT done — rooting did not require
     authoring matches.

     **The box then surfaced 24 more of the same class** (verified live, checked the check first):
     old-vintage cards existing only in the droplet's data — 17 `domains` ("Pressure Architecture"
     notes, a shelf with ZERO local cards), 6 `science` and 1 `labor` runtime mints from before
     `science_cards.py` carried `part_of card_k_spine_created_order` (it does now — the path is
     already fixed; these were residue). Handled under the same decision: a tenth spine (`domains`)
     plus two redirects (`science`, `labor` → the created order, their established parent on both
     vintages). Box graft: 24/24. The four Wikipedia cards were removed by title, per (a).

     **FINAL STATE, live on both surfaces 2026-07-28:**

         total = 466,401   nested = 466,401   semantic_only = 0   isolated = 0

     Nothing in the keeping is isolated, and everything walks back to the Floor — no longer a
     slogan; the overview reports it and two test files plus the ratchet guard it.

     The entry below is the pre-decision record, kept for the trail.

  2b. **552 cards sit in unrooted ISLANDS — a real gap, ratcheted not papered over.** Walking both
     planes from `card_k_floor_of_discovery`, 465,456 of 466,008 cards are reachable; **552 are not**
     — `codex` 451, `classics` 39, `animation` 24, `maker` 11, `recipes` 11, `hymns` 10,
     `patristics` 4, `dictionary` 2. They are not broken: **zero dangling edges**, every reference
     resolves. They are closed clusters (codex notes and Boethius sections bound by `same_section`)
     with no edge out to anything rooted. Grafting e.g. the codex note "Revelation 5" to its
     scripture card is a real relation, but *choosing* that match is authoring rather than finding,
     so it is left for a deliberate pass. `tests/test_reachable_from_the_floor.py` ratchets the
     number and also asserts the islands stay whole (dangling references would be a worse bug).

     **Why the real walk is a TEST and not part of the endpoint:** measured — adjacency + BFS costs
     **11.7 s and ~162 MB peak**. `overview()` serves a public route on services already at ~2.8 GB
     RSS. The gate can afford twelve seconds; a reader cannot. Recorded so the trade is not
     re-litigated from an impression.
  3. The **verse↔lemma relation is fully served** (`/word_study?strongs=` → occurrences;
     `/original?ref=` → tagged words) with **370,833 verse↔lemma pairs resolving and ZERO
     unresolved**, so minting those as connection cards would add nothing a reader cannot already get
     while inflating the corpus 77% and burying the authored edges. **Deliberately not minted.**

  *(Original entry retained below, struck, so the correction is auditable rather than tidied away.)*

- **~~§5.3 passes as written, and the principle behind it has a large measured gap (found 2026-07-28).~~**
  ~~Recording both halves, because reporting only one would be a different kind of dishonesty.~~

  **Passes as written:** `/floor` is reachable and carries 14 grafts; every structural spine hangs off
  it. The criterion says "every *spine* reachable from the Floor" and that is true.

  **The gap:** measured live at `b5b9794` via `GET /graph?scope=overview` —

      total cards       466,393
      connected cards     5,384   (1.15%)
      shelves                90
      shelves with ZERO connected cards: 78, holding 313,944 cards

  Largest with nothing connected: `gutenberg` 77,700 · `geography` 69,135 · `taxonomy` 37,933 ·
  `hebrew_ot` 23,213 · `lexicon` 19,570 · `medicine` 18,596 · `greek_nt` 7,927. Only twelve shelves
  connect at all, and those are the authored ones (`codex`, `scripture`, `classics`, `patristics`,
  `science`, `domains`).

  This does not violate §5.3, but it does sit against the standing rule that *everything connects —
  no orphans, never say "isolated"*. The sharpest instance: `hebrew_ot`, `greek_nt` and `lexicon`
  (50,710 cards) carry no edges, while "original language FIRST" and "the lexicon is the plumb-line"
  are core. Strong's numbers already bind lexicon entries to specific verses, so that graft is
  available and cheap — the edges were simply never minted.

  **Not chased in this round** (the round's scope was auditing §5 and fixing what it found). Named
  here so the next round starts from a measurement rather than an impression. **Do not "fix" this by
  minting weak edges** — [[fruit ranking]] and the 53-false-edge cleanup are the precedent: an edge
  that does not carry a real relation is worse than an absent one, because it makes the map lie.

  **Check the check, recorded:** three probe shapes were wrong before this measurement was trustworthy
  — `/graph?scope=overview` returns `clusters`/`links`, not `nodes`/`edges` (a naive read reported
  "0 orphans out of 0 nodes", which proves nothing); clusters are keyed by `shelf`, not `id`; and
  `scope=shelf` takes different shelf names again. The first two readings would have been reported
  confidently and been wrong.

- **The box's memory, MEASURED (2026-07-28, task: shard decision groundwork).** `systemctl` on the
  droplet: `nh-org` Main PID at **2.0 GB RSS, peak 3.2 GB, swap 734 MB (peak 1012 MB)**; `nh-com-2`
  at **1.7 GB, peak 2.6 GB, swap 916 MB**. The box IS swapping at peaks. What was previously
  "~2.8 GB measured, mostly-corpus inferred" is now: combined peaks ~5.8 GB against physical RAM
  plus ~1 GB of swap in use. The shard engine (`corpus_db.py`, built and unwired) is no longer a
  nice-to-have question; it is a dated capacity finding. Still true: *which* structures dominate
  the RSS is unprofiled — measure per-structure before promising a specific reclaim.

- **Gill & Clarke, EVALUATED (2026-07-28, contract §6 item 9 "evaluate adding Gill/Clarke").**
  Both are public domain (John Gill d. 1771; Adam Clarke d. 1832). The house already has the whole
  pattern: `commentary.py` is registry-driven (`SOURCES` dict, one entry per commentary) and
  Matthew Henry's migration (source db in the lw base → per-verse sqlite) is the template. Adding
  either = (1) a fetch recipe into the lw source base from a verified PD digitization (CCEL hosts
  both; the SPECIFIC digitization's provenance should be checked deliberately, not assumed), (2) a
  migrate run producing `gill.db`/`clarke.db`, (3) one `SOURCES` entry each. Bounded work; deferred
  because it requires a network acquisition Matt should see land, not because anything is unknown.
  Recorded so the next session starts from a plan rather than a survey.

  **ISBE source VERIFIED (2026-07-28):** the CrossWire SWORD module `ISBE` (v2.2, 2009) — the
  International Standard Bible Encyclopedia, James Orr ed., distribution status **Public Domain**
  per the module's own metadata page. Structured and machine-readable (a SWORD dictionary module:
  headword-keyed), which beats OCR'd page scans for carding. The fetch itself is D5's first act,
  done where Matt can see it land; the parser is a bounded read of the RawLD/zLD key index.

  **Per-shelf memory ATTRIBUTION (2026-07-28) — the shard freeze list, measured:** serialized
  payload of the whole keeping is 535 MB (RSS multiplies this ~4× through Python object overhead).
  `dictionary` 128.5 MB (24.0%) + `gutenberg` 120.5 (22.5%) + `geography` 51.3 (9.6%) +
  `taxonomy` 39.1 (7.3%) = **63% in four cold reference decks** — the freeze set. Hot shelves stay
  resident (lexicon is only 18.9 MB; scripture, codex, the originals). Expected effect: roughly
  halving each service's corpus footprint. Means: `len(json.dumps(card))` summed per shelf over the
  live local corpus — a proxy for resident size, not a direct RSS measurement per structure.

- **MATT'S SEVEN DECISIONS (2026-07-28, asked directly — "grill me" — and answered):**
  1. **Memory: wire the shards** (profile per-structure first; freeze cold shelves; the measured
     peaks above are the warrant).
  2. **Acquisitions: ALL THREE — ISBE 1915 FIRST**, then Gill's Exposition, then Clarke.
  3. **Write-back: calendar-only pilot** behind `consent.guard()` — the least dangerous verb,
     reversible, proves the grant flow end to end. Email/storage wait.
  4. **Storyboards: wire into the companion/ask layer** — the pastoral layer may meet a person with
     the movement they stand in, with the framing guard ALWAYS attached; crisis still outranks all.
  5. **Voices: build voices.html** — the visible face of "one system meant to unify the church."
  6. **Security sweep: resume as the next loop**, over the NEW surfaces especially.
  7. **proof.html: leave the historical run** — re-assay only when the fleet changes materially.
  8. **THE CAPSTONE (Matt, 2026-07-28, scope widened same day): once the program is complete, run
     a NULL THEORY ASSAY ACROSS THE ENTIRE PROJECT** — "all theories that could be associated with
     the topics we cover." The universe under review, all three rings:
       a. **The kept theories** — every theory card in the keeping (the assay-330 lineage and
          whatever joined since).
       b. **The project's OWN theses** — the two trees, coherence-as-closure, the recurring form,
          the RAS reception bridge, the body-systems/spirit-archetypes mapping, the numbers/bases
          triangulation, the QM+formal-logic dig, the hydromechanics readings, the storyboard/
          archetype design itself — nothing of ours is exempt; a null test that spares the house's
          own beams proves nothing.
       c. **The associated theory families per covered topic** — the standard competing theories in
          each domain the verifiers span, where they touch claims we card or serve.
     The opposite polarity of the sealed 330: not celebrating what held, but HUNTING what fails.
     Verdicts on the standing scale — CONFIRMED / PLAUSIBLE / RESONANCE / COINCIDENCE — plus the
     honest third state throughout: "we could not check" is a fact about US, never a verdict on
     the theory. The misaligned are NAMED, plainly ("say 'dead end' plainly" — the fruit test),
     including our own if they fail. Deliverable: the misalignment list with worked reasons.
     Distinct from item 7: proof.html's history stands; this is a fresh REVIEW.

---

## §8 CLOSE-OUT — the D-series, run and gated (2026-07-29, accepted by Matt)

Recorded here because the contract is the frozen record and this is what happened against it.
Every line is a gate result or a live measurement, never prose.

| item | outcome | gate | evidence |
|---|---|---|---|
| Trust-kernel coverage floor | 75 → **90** enforced | 892 | cas 93 · derivation 90 · ledger 91 · receipts 95 · record 93 · signing 98 · validate 93 |
| D4 · wire the shards | LIVE | 899 | RSS 2834/2809 → 1893/1908 MB per process; battery 33/33; IDF identical frozen vs resident |
| D5 · acquisitions | LIVE | 903 | ISBE 1915 (9,380 articles, PD) + Clarke 854 ch + Gill 1,189 ch, all attributed |
| D6 · security sweep | LIVE | 912 | 2 real holes closed (ICS injection; unsigned witnesses); signed report verified end-to-end in a browser |
| D7 · null assay capstone | COMPLETE | 916 | `docs/NULL_ASSAY.md`; 1 unbacked claim corrected; **3 findings against our own theses**, memories corrected |

**What this close-out does NOT claim.** §5 is not declared done by this session:
- **§3/§5 private-key-on-the-wire: 5 endpoints still accept `private_key` inbound.** Mesh
  messages were fixed by detached signatures; the rest are not. Do not read the D6 sweep as
  closing this.
- Overall test coverage is 52% (the kernel is ≥90). Almanac sits at 20%.
- No src-side deploy manifest exists yet; `corpus_db.py` was absent from the droplet for days
  under a green gate, and only a rollout failure revealed it.

The gates declare completion, not this table. These lines are the record of the run.

*Completion is reached when §5 all pass against one named commit. The implementing model does not
declare completion in prose; the gates declare it.*
