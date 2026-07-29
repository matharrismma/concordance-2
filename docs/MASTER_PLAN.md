# THE MASTER ARCHITECTURE PLAN — the living document

Matt, 2026-07-28: "Prioritize what we build now and what we add in our master architecture
plan. This will be our living document of every aspect of the project and our plans.
We create SOPs and all Maps necessary to operate."

This document is ALIVE: every major directive lands here the day it is given; every shipped
system is recorded here when it ships. It never overrides `COMPLETION_CONTRACT.md` (frozen
2026-07-25 — V1 invariants, machine-testable DONE, drift ledger); the contract governs V1,
this plan maps everything, V1 and beyond. Update discipline is in §6.

Mission (one string, everywhere): a governed way to find, check, use, and preserve
information without losing source, authority, or history. Serve families first — free, no
account. Great Commission: sinners, not saints; demonstrate, never preach; never hide who
we are. The Bible is the focus; all else a tool at the right time.

---

## §0 Design principle — the mechanical system (Matt, 2026-07-28)

"Think of it like a mechanical system. Capacitors to even flow across the project."
The recurring form (effort ↔ flow) has a storage element, and every seam where flow is
uneven gets one. Named capacitors, standing and planned:

- **Shard freeze** (D4) — RAM surge absorbed into a disk reservoir; thaw/freeze/rebalance
  is the charge–discharge cycle; the LRU rebalancer is the load leveler.
- **Curation gate** (C1) — member drops arrive in bursts; the review queue absorbs the
  surge and the commons receives a steady, evaluated flow.
- **Elevation ladder** (C2) — community enthusiasm charges; the reference library only
  receives what the witnesses + verifiers + trusted reviewers discharge.
- **Steward review queue** — reports accumulate; the 3-witness threshold is the breakdown
  voltage that discharges to a human.
- **Decks / the Hare** — pre-charged retrieval: predicted top-of-deck absorbs latency.
- **Receipts ledger** — value accumulates signed and traceable until (if ever) payment
  discharges along the waybill.
- **Caches + Wayback archives** — capacitors against link rot and upstream outage.
- **The airlock chamber** (C2.5) — untrusted freight charges into quarantine; only cards,
  a map, and a hash discharge into the keeping. The bytes never enter the core.
- **Rate limits** = current limiters; **the moat** = the diode (falsehood cannot pass in
  either direction of pressure).

Rule for new features: find the uneven flow first, place the capacitor at the seam, and
name it in this list when it ships.

## §1 The standing systems (shipped, gated, live)

Each line: system — where it lives — what it guarantees.

**The floor**
- Verification engine — `src/concordance/verifiers/` (~60 domains), `grid.py`, `check` entry
  — deterministic verdict + worked trail + sealed receipt; 0 false positives, benchmarked
  every gate (`tools/benchmark.py`, 60/60).
- Trust kernel — `cas.py, ledger.py, record.py, signing.py, validate.py, receipts.py,
  derivation.py` — hash-chained precedent ledger, content-addressed store, detached
  signatures; coverage floor ENFORCED ≥90 per module (2026-07-28).
- Three-state honesty — HOLDS / BROKEN / SYSTEM_ERROR everywhere; our failure is never
  rendered as their falsehood; ambiguity returns candidates (the human walks the last mile).

**The keeping**
- Corpus — ~487k cards, one rooted tree (the Nesting: 466,401/466,401 nested, zero islands),
  found-vs-authored edge discipline, `corpus.py` IDF ranker + shard freeze (D4: heavy
  shelves ride SQLite FTS shards, graph stays resident, IDF-identical, opt-in by env).
- Acquisitions — Gutenberg (77k), history, taxonomy, geography, dictionary, languages, OEIS,
  RFCs, commentaries (Henry, Spurgeon), encyclopedia (Easton), field library (survival),
  church cards, contributors, religions-as-foreshadow. ALWAYS GROWS.
- Growth engine — `grow.py`, verifiers mint cards, 0-FP; the Tortoise (LoC/OA web fallback,
  `web_unverified`); Cards/Decks/Hare (stub+link lazy, predicted decks).

**The surfaces**
- Secular .com + witness .org — same keeping, two faces; `web/api.py` route registry +
  golden tests; MCP servers (com=engine tools, org=+Scripture); PWA + offline finding layer;
  llms.txt + tool schema = the agent surface (guarantees must REACH the reader).
- Ask/companion — `ask.py`: crisis outranks all → seekers (12 great questions) → comfort
  (always with a word) → storyboards/archetypes ("you may be many of these") → decks →
  search. The Gate opens by the classifier's verdict, never a flag.
- Coach — K-3 reading tutor entry + curricula; badges; shared-study groups; journal/stacks.
- Reference — bible.html (parallel WEB + original tongues), Harmony, Timeline, back-matter
  tables, Atlas (real coordinates), encyclopedia-as-cards, study quick-find (`study_index`),
  narratives/storyboards (12 boards, 17 movements), voices.html (unify-the-church face).
- The Works, Codex, Brain, connection-MAP, proof/corrected/guarantees pages — receipts shown.

**The fellowship**
- Covenant identity — 4 verses → PBKDF2 → Ed25519, keys born on device, server holds only
  the public key; the Gate then the covenant ("we open doors, never approach").
- Fellowship Mesh — map/message/door/whiteboard, confession-gated; Guardians/Guides; LoRa
  substrate planned (Reticulum).
- Consent — `consent.py`: signed grants (closed verb set, TTL≤30d, revocation tombstones,
  storage re-verified); write-back pilot: calendar events (`connect_write.py`), D3.
- Moderation floor — `moderation.py`: report (1=claim, 3 distinct SIGNING witnesses=held for a
  HUMAN steward, Deut 19:15), block/unblock (viewer-side sovereign boundary). Every act carries
  a fresh detached signature over canonical bytes — a witness is a key, never a typed name.
- Connect — `connect.py`: read-only pass-through to the user's OWN calendar/email/storage;
  EDGE, store nothing.

**Operations**
- Gate — `tools/check.py`: MANIFEST-whole suite (899 tests), moat 60/60, kernel coverage
  floor 90; full gate before EVERY deploy. Probe — `tools/probe_usefulness.py`: 33/33, the
  mission carried as an instrument (seeker category permanent).
- Deploy — `tools/deploy.sh`: tar-over-ssh, STAGGERED restarts, patient health polling.
  Git discipline: never `add -A`; push every commit. Data/secrets untracked.

## §2 NOW — the current build series (in flight, in order)

1. ~~Trust-kernel coverage ≥90 + floor raised~~ — DONE 2026-07-28 (commit eb40812).
2. ~~D4 wire the shards~~ — DONE 2026-07-29, LIVE: RSS 2834/2809 → 1893/1908 MB per
   process (~1.85 GB freed; box available 1.7 → 3.5 GB); battery 33/33; IDF-identical;
   found live: corpus_db.py had never been deployed (scp target ≠ checkout — the MANIFEST
   lesson, src side).
3. ~~D5 acquisitions~~ — DONE 2026-07-29, LIVE: ISBE 1915 (9,380 articles, SWORD zLD
   parsed stdlib-only, full article on every card page) + Adam Clarke (854 ch) + John
   Gill (1,189 ch) via helloao into the commentary registry. Gill was NOT on CrossWire —
   helloao was the lawful road for both.
4. ~~D6 security sweep~~ — DONE 2026-07-29. Two real holes found and closed: ICS injection in
   the calendar pilot (unvalidated DTSTART/DTEND + an unescaped
   carriage return) and UNSIGNED WITNESSES in the
   moderation floor (three invented names could quarantine true content; anyone could edit
   another viewer's block list). Report/block/unblock now require fresh detached signatures
   naming their exact target, and site/community.html mints a device-local reporting key so
   the fix reaches the reader. Probed clean: consent (wrong signer / tampered scope / cross-
   agent / cross-verb / TTL cap / private-key smuggling), study routes (traversal, injection,
   oversize, NUL), card render (attribute breakout, javascript: URLs), ambiguous-ref last mile.
5. **D7 CAPSTONE null assay** — three rings: 103 kept theory cards (recover+classify), the
   project's OWN theses, associated theory families per covered topic. Verdicts
   CONFIRMED/PLAUSIBLE/RESONANCE/COINCIDENCE + honest could-not-check; say "dead end" plainly.

Standing trajectories (cross-session): overall test coverage 52%→90 (worst user-facing
modules first — almanac 20%); private-key-on-the-wire — 5 endpoints still to port to
detached signatures (do NOT claim contract §5 done); OneDrive drag on the working copy;
nav single-source; manifest counts.

## §3 NEXT — THE COMMONS (social-first arc; Matt 2026-07-28; task #102)

The page becomes social first: a giant library where every member stocks their OWN shelf,
writes and is read, lends to friends met through the app. Communities form around the cards
they pull; every hobby gets its wing; the best information because the people who know tell
us. Full design + legal lines: memory `project_social_first_member_shelves_lending_2026-07-28`.

**Stage C1 — the shelf and the commons (build first; all on existing machinery)**
- Member shelves: signed member-authored cards (`authority_tier: member`, never silently
  upgraded), `/shelf/<fingerprint>` pages.
- Identity doctrine (Matt 2026-07-28): REAL NAMES as the community norm on shelves
  (self-asserted, key-signed; no ID documents collected). Known when you speak, unseen
  when you read: identification on work, never surveillance of reading. Name is the only
  profile field; readers always anonymous; aggregate tallies only; nothing tracked or sold.
- Drops: ANY link — videos (platform embeds only), quotes (short+attributed), book recs
  (PD recs point INTO the keeping), curated pages (stub+link + curator note + fetched-at +
  content hash; archives via Wayback save-page-now — we never host the bytes).
- Curation gate: three rings — private → own shelf (friends, ungated) → commons (gated:
  `public_review` + automated pre-checks + steward review queue). Gates amplification,
  not speech.
- Commons front surface: new-on-the-shelves, voices, hobby wing pages.
- First wings: RECIPES + MUSIC (all instruments) + ART (all categories). PD value day one:
  pre-1930 sheet music, hymnals, method books, chord charts; sovereign in-app tuner +
  metronome (Web Audio, no deps).
- Live sessions stage 1: session cards + platform embeds + consent-pilot calendar RSVPs +
  threads for Q&A.
- Giving stage 1: creators put their own giving links on their shelf (link lane); people
  give when they want; free stays free, nothing ever paywalled.

**Stage C2 — lending, elevation, attestation**
- Lending: consent.py lend verbs (signed, TTL, revocable, borrowed ledge). Owned items:
  card + loan ledger in-app; copyrighted BYTES never hosted (Hachette v. IA); physical
  hand-off via mesh or the owner's platform's own loan feature.
- "I MADE THIS" practitioner attestations (Works pattern for hobbies; fruit made mechanical).
- Elevation ladder into the reference library: contribute → 2-3 distinct signed witnesses →
  verifier check (else witnessed-not-verified) → trusted-reviewer feedback (trust = earned,
  visible badge with its own receipt trail) → recorded elevation with the full trail (the
  one honest authority upgrade — in the open, never silent) → reversible with tombstone.
  Hard lines: almanac stays verified-only (community feeds `propose_almanac_entry` queue);
  apothecary keeps the medicine floor (tradition elevates as witness; dosage/medical claims
  never elevate on feedback alone).
- Receipt substrate for payments: every value act emits a signed receipt complete enough to
  compute payouts retroactively. Pay for FRUIT, never traffic; readers stay anonymous.

**Stage C2.5 — THE DISTRIBUTED AIRLOCK (Matt, 2026-07-29)** — the substrate under lending
- Seed exists: `airlock.py` (mint cards+map in the chamber, kick the FILE back out, 2026-07-25)
  and `corpus_db.airlock_search` (thaw one shard, pull only what we need, seal it back). The
  same discipline one plane up — a member's own cloud folder instead of a shard.
- INTAKE: a folder link (Drive / Dropbox / Nextcloud / S3 / self-hosted) opened in QUARANTINE —
  size caps, type allowlist, no executables, blocklists, text extraction only. Out come cards +
  a map + a CONTENT HASH; the chamber seals and the bytes are dropped.
- PATH NOT PAYLOAD: the card holds the origin URL, a fetch recipe, and the hash. Another member
  retrieves FROM THE ORIGINATOR (client-direct where possible — the bytes never transit us).
  The broker holds the waybill, never the cargo; no copy is made, so the lending problem
  dissolves.
- TAMPER-EVIDENT: a retriever checks the bytes against the carded hash; a mismatch is said
  plainly. No other file-sharing network can make that claim.
- THE ORIGIN'S PERMISSIONS ARE THE ONLY PERMISSIONS: read on the named folder, never a crawl
  beyond it, and revocation must actually work — found / source gone / could-not-check. Never
  cache to paper over an outage.
- REPLICATION BY CONSENT: PD/CC0/member-authored work may be mirrored by volunteers (seeded
  resilience); anything else stays one copy, at its owner's.
- Intake lands in `public_review` behind the curation gate, marked unverified until checked.

**Stage C2.6 — THE DISTRIBUTED CORPUS (Matt, 2026-07-29)** — knowledge across many devices
"Some can act as nodes and backups. Some may only want personal. Others may want to curate a
specific aspect of the corpus." The D4 shards ARE the distribution unit (self-contained SQLite
FTS + manifest; a device thaws only what it holds) — this adds the role layer and the trust layer.
- ROLES: **personal** (core.db = 69 MB: the whole map, every title and connection, offline on a
  phone; add the wings you love; serves nothing) · **node** (holds many shards, serves peers who
  ask — a backup by construction, not a separate feature) · **curator** (owns a slice: a shelf +
  its spine, tends and elevates into it, signs it, publishes it as a shard others subscribe to).
- TRUST LAYER (do not skip — an unsigned distributed corpus is a rumor mill): every shard carries
  a content hash, the manifest carries every shard's hash, and the manifest is SIGNED. A device
  verifies what it received against what the manifest says (the airlock's tamper-evidence, the
  same kernel that gates our releases). NO NODE IS AUTHORITATIVE: verification is local, so any
  device checks any card's seal without reaching us. If we vanish, the library keeps proving itself.
- BUILD EARLY: a **coverage map** (how many known nodes hold each shard — an honest seed count so
  the community can volunteer where it is thin, never a leaderboard) and **versioned deltas** (pull
  only what changed, not a fresh 200 MB shard).
- DISCOVERY rides what exists: the Fellowship Mesh over IP; LoRa/Reticulum where there is no
  internet. Shards travel by microSD as well as by wire — the ark is a set of files you can hand
  to a neighbor.
- MEASURED (from the live manifest, 2026-07-29): core 68.9 MB / 30,063 cards (the personal floor
  — the whole map on any phone) · science 96.9 · word 166.7 · world 177.7 · dictionary 226.8 ·
  books 227.8. FULL NODE = 964.8 MB / 487,178 cards — the entire keeping fits on an $8 microSD.
  A curator carries core + their one wing. This is why "spread across many devices" is real and
  not aspirational: the cost of holding the library is a rounding error on any modern device.

**Stage C3 — when reached**
- Live lessons P2P: WebRTC 1-on-1/small workshops — server does signaling only, video bytes
  never touch us. Guardian-present policy for children BEFORE the feature ships.
- SFU (Jitsi/LiveKit) only if scale forces it.
- Creator payments if we reach that point: voluntary giving routed along the waybill
  (provenance royalty-split); processor/tax/KYC decided that day; Steward never moves money.
- Agents/robots: the same shelf model via MCP — Acts church for agents (parity of
  substance, difference of form); an agent stocks receipts, lends verified cards.

## §3.5 The feature metabolism (Matt, 2026-07-28)

"If it is requested and it aligns we build and add. Use of the feature gets it promoted.
Unused aspects go in cold storage."

- SUGGEST — a feature request is a member drop (kind: suggestion), signed, in their own
  words; rides the standard curation gate; duplicates cluster visibly by overlap.
- ALIGN — assayed against the plumb-line (the frozen mission string + kernel); verdict
  RECORDED with reasons: ALIGNED (build) / NOT ALIGNED (say why plainly, keep the record) /
  NOT YET (parked with what would change the answer). The suggester stays on the receipt
  trail — a shipped suggestion is value created (payment substrate applies).
- PROMOTE — aggregate route tallies (never reader identities) earn placement: nav, front
  page, docs. Promotion is a recorded act with the numbers attached (elevation pattern).
- COLD STORAGE — unused features FREEZE, never delete (the shard-freeze pattern applied to
  features: disk, not attention): code stays in git, the route answers "in cold storage —
  ask and it reopens", data compresses to archive, the freeze is recorded WITH the usage
  numbers. Dependency audit runs BEFORE any freeze (a passing gate != a safe removal).
  Revival is cheap by design; one aligned request can thaw a room.
- Cadence: one steward decision per season per feature; everything reversible + receipted.
- SOP-FEATURES joins the §5 worklist (ships with the first /suggest surface, Commons C1 —
  suggestions are drops, so C1 carries them natively).

## §3.9 THE MILLION (Matt, 2026-07-29) — the growth target and the seeding order

"Our goal is 1M cards. Once everything is complete on the list, begin seeding all of the
identified possible uses."

Measured 2026-07-29: **496,559 cards — 49.7%.** The second half is not a stretch; it is a
worklist of sources already identified and lawful (PD/CC0/open), plus a card per identified USE.

ORDER (after the list — the D-series capstone and the queued tasks — is complete):
1. **Seed every identified use.** Each use case we have named gets its cards: the hobby wings
   (recipes, music by instrument, art by medium), the field library's practical how-tos, the
   storyboards + archetypes + their movements, the access-tools catalog, the SOPs and
   operational objects (§104). A use with no card is a use we cannot find.
2. **Deepen what is already stubbed.** Gutenberg's 77,700 volumes are one card each — chapter
   and section cards multiply that severalfold. Commentary (Henry + Clarke + Gill) at verse
   granularity is tens of thousands more, each attributed to its author.
3. **The remaining PD reference shelf.** McClintock & Strong (12 vols), Schaff-Herzog, Smith's,
   Fausset's, Nave's, Torrey's — the same ISBE road, already proven tonight.
4. **The open scientific commons.** Taxonomy beyond the recognizable subset (GBIF/Catalogue of
   Life), OEIS beyond the core, IMSLP's PD scores for the music wing, Wikidata's dated events.
5. **The community's own hands.** Member shelves, curated finds, elevated contributions — the
   only source that grows without us, and the reason the Commons matters to the count.

RULE FOR EVERY SEED (unchanged): found, attributed, nested (zero orphans), 0-FP, and honest
about what was not checked. A million cards of slop would be worse than 496,559 true ones.

## §4 LATER / horizon (recorded, not scheduled)

- Denominational voices completion (one major voice per tradition, their own reckoning).
- LoRa/Reticulum mesh hardware path; microSD full-body offline distribution (the ark).
- Kingdom economy substrate maturation; The Way fellowship growth (Guardians/Guides).
- Knowledge-layer outreach: academics + Jews via Hebrew/Greek (lexicon = plumb-line).
- .tv watch/listen/learn face growth; kids channel.
- Programmable Fabric PCB (Matt's hardware) — separate track, connects at the maker wing.

## §5 SOPs and MAPS (what we operate by)

**Standing SOPs** (`docs/SOP/`): SOP.md (general), CONTINUOUS_IMPROVEMENT.md
(probe_usefulness → triage → fix → gate → deploy → push → re-probe), LESSONS.md.
Also operative: DEPLOY.md, RUNBOOK.md, SELF_HOST.md, the gate ritual (§1 Operations).

**SOPs to write with the Commons** (each ships WITH its feature, not after):
- SOP-CURATION — the review queue: automated pre-checks, steward judgment, promotion with
  reason, appeal path.
- SOP-ELEVATION — the ladder end to end; who counts as a trusted reviewer (badge criteria,
  earned + visible + revocable); almanac/apothecary hard lines.
- SOP-STEWARD — human review duties: held reports (3-witness), review queue cadence,
  elevation sign-offs; never a bot.
- SOP-LIVE — session listing rules, guardian-present policy, live report/block handling.
- SOP-RECEIPTS — what every Commons feature must emit; payout-completeness check.
- SOP-FEATURES — the metabolism end to end: suggestion intake, alignment assay verdicts,
  promotion thresholds, the cold-storage freeze/thaw ritual + dependency audit.

**Maps** (drawn, kept current):
- The Nesting (one rooted tree) — live at /brain + /map; counts in the manifest.
- Route/tool map — the registry IS the map (`web/api.py` ROUTES + MCP tools + goldens).
- Deploy map — DEPLOY.md + deploy.sh (droplet, services, ports, staggered ritual).
- Data map — data/*.jsonl registry in `corpus.load_cards` (the one load list); shard
  manifest (`data/shards/manifest.json`); what is tracked vs untracked (git discipline).
- Community rings map — private / shelf-friends / commons; where each gate sits (to draw
  with C1).
- Value-flow map — act → receipt → ledger → (someday) payout along the waybill (to draw
  with C2).

## §6 Update discipline (how this document stays alive)

- Every major directive from Matt lands here the day it is given (§2-§4 placement + memory
  file cross-reference).
- Every shipped system moves to §1 with its guarantee named.
- Every SOP/map ships WITH its feature.
- This file is tracked in git; changes ride normal commits; the contract stays frozen and
  is never edited except its own §7 drift ledger.

## Update log

- 2026-07-28 — Document created. Kernel floor 90 shipped; D4 code shipped (rollout in
  flight); Commons arc recorded and staged (C1/C2/C3); SOP/map worklist added. Source
  directives: Matt's social-first series (shelves, lending, curation, hobbies, elevation,
  music/art wings, receipts→payments, giving, live teaching, this plan itself).
- 2026-07-29 — **The D-series closed and accepted.** Kernel floor 90 · D4 shards live (~1.85 GB
  freed) · D5 ISBE+Clarke+Gill live · D6 two vulnerabilities closed · D7 null assay complete
  with three findings against our own theses (record corrected, not defended). Four gates:
  892 → 899 → 903 → 912 → 916. New standing doctrine recorded the same day: the mechanical
  system (§0 capacitors), the Commons (§3), the feature metabolism (§3.5), the million (§3.9),
  the distributed airlock (C2.5) and distributed corpus roles (C2.6), real names without
  tracking, and the operations log. Queued next: #102 Commons · #103 Distributed · #104 Card
  every piece · then seeding toward 1M.
