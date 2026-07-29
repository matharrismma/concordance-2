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
- Moderation floor — `moderation.py`: report (1=claim, 3 distinct=held for HUMAN steward,
  Deut 19:15), block (viewer-side sovereign boundary).
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
2. **D4 wire the shards** — code done + gated (44fb324); remaining: fresh shard build,
   droplet rollout (shards + env drop-ins + staggered restart), live RSS + probe verify.
   Measured locally: −540MB RSS per process, battery 33/33, IDF-identical.
3. **D5 acquisitions** — ISBE 1915 first (CrossWire SWORD, PD, verified), then Gill, then
   Clarke → commentary registry.
4. **D6 security sweep** — over the new surfaces: consent, report/block, study routes,
   ambiguous-ref, write-back pilot. (Now doubly important: the Commons will reuse all of it.)
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

**Stage C3 — when reached**
- Live lessons P2P: WebRTC 1-on-1/small workshops — server does signaling only, video bytes
  never touch us. Guardian-present policy for children BEFORE the feature ships.
- SFU (Jitsi/LiveKit) only if scale forces it.
- Creator payments if we reach that point: voluntary giving routed along the waybill
  (provenance royalty-split); processor/tax/KYC decided that day; Steward never moves money.
- Agents/robots: the same shelf model via MCP — Acts church for agents (parity of
  substance, difference of form); an agent stocks receipts, lends verified cards.

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
