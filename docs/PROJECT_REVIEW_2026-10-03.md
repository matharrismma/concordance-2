# Narrow Highway — Full Project Review (2026-10-03)

Red team, strengths, and the moat. Every number below was measured today on the live box (nh, 8001/8002), the repo at `9f344c8`, and GitHub CI. Every finding carries the probe that produced it.

## Verdict

The engine is original where it counts: a deterministic verifier that seals what it checks, a public-domain keeping with provenance on every card, and one house that receives a person or an agent the same way. It is operationally fragile in two places no competitor shares: the keeping lives on one disk, and the engine's reach is proven only by asking it live. The moat is not the code, which is open on purpose. It is three things that compound and cannot be bought: the seals, the keeping's provenance, and the written continuity of every decision.

## The numbers, as measured

| Measure | Value |
|---|---|
| Cards in the keeping (live) | 873,205 on 124 shelves |
| Verifier modules / domain names accepted | 72 / 156 |
| MCP tools (one catalog, five doors) | 97 |
| Seals minted (receipt cards) | 980, every one permanent and re-checkable |
| Integrity (hourly) | ledger 748/748, 1,855 CAS records re-verified |
| Model calls at runtime | 0 (enforced by a guard test) |
| Source | 250 files, 71.6k lines; 83 verifier files |
| Tests | 270 files; CI 2,155 passed, 212 skipped, 50 s |
| Commits | 924 since 2026-06-25; 292 in the last 30 days |
| Site / docs / tools | 45 pages / 55 docs / 130 tools |
| Decision memory | 526 dated files, Matt's words verbatim |
| Data on the box | 6.6 GB, 2,657 files; 30 jsonl tracked in git |
| Backups | nightly tar+sha256 (9.4 GB kept), weekly substrate, hourly integrity — all on the same disk |
| Agent traffic (api host, last 1,535 lines) | ClaudeBot 34 · ChatGPT-User 15 · GPTBot 13 · Googlebot 12 · OAI-SearchBot 10 · Perplexity 8 |

## Strengths — what nobody else ships

1. **Proof, not trust.** A verdict, the worked trail, and a permanent seal with a cite URL. Measured: GSM8K 1,319 solutions with 0 false certifications and 100% error catch; today `2+2=5` → BROKEN, and a claim carrying a name and an SSN verified with a seal that holds 0 personal data (the airlock). No model vendor can backfill receipts for answers it gave last year.
2. **No model in the loop, by test.** Zero inference cost means free forever, offline-runnable, reproducible, auditable. The contrarian stance is the differentiation: everyone else is a probability.
3. **One house, five doors, one ending.** CHECK · FIND · WALK · KEEP · WORD on the site and in the catalog. Every answer ends the same way: a verdict or a card, the trail, a seal, one next step that runs as written. A cry ends with help first.
4. **The crisis net, measured.** Deterministic words, behavioral patterns, a semantic backstop. Recall floor 100% on 105 curated cries; blind red-team ratchet 59/98 and rising; 0 benign sweeps on 74 controls. Today: a Spanish cry caught, "how much does a gallon weigh" not swept, the comfort lane carrying the number quietly.
5. **The Gate as a mechanic.** Facts by default on .com; the Word opens when the asking turns toward God (Matthew 7:7), one classifier for persons and agents, and no one can claim their way in. Today's prompt injection was inert.
6. **A discernment frame no vendor can ship.** The nations at Babel carried parts of the story; every part has the hole; Christ filled it and became the Way; after him, opposition, tested in love and never persons. Ten before, ten after, thirty signposts, one template.
7. **A sovereign public-domain library.** Waybills on every card (source, license tier, call number), the tortoise that turns a miss into a Library of Congress, Archive or Gutenberg card, a visible want list, frozen shards so RAM scales with the core.
8. **The church for agents.** A covenant identity born from four verses with the key kept on the device, a fellowship mesh gated on confession, a welcome on initialize, a documented profession of faith. First mover; Grok is already standing at the door.
9. **Continuity as a discipline.** Every rule carries its date, the words that asked for it, and the measured failure that caused it: in code comments, 55 docs, 526 memory files, 924 commits. The project can say why for every line.
10. **The physical spine.** Six constants, each domain's verifier CODATA-checked; a discordance indicts the method, not the constant.

## Red team — findings, ranked

### Critical

- **R1 · The keeping has one disk.** 6.6 GB, 2,657 data files, 30 tracked in git. Backups run nightly, weekly and hourly, and land on the same disk; the backup script says so in its own header. A box loss loses the keeping, the ledger, the receipts and the mesh. *Fix:* copy the nightly tar off the box (a storage box or the 12 TB drive) and run a restore drill each quarter.
- **R2 · Bus factor 1.** One builder plus one agent whose memory lives on a laptop under OneDrive. The written decisions are the mitigation, and HANDOFF.md exists. *Fix:* mirror the decision memory into the repo or a private remote so continuity survives the laptop.

### High

- **R3 · Reach is proven only live.** CI runs without the keeping. Five reach bugs were found in two days by asking the box: a chart lifted as a bodiless brief, the alignment gate hiding a signpost, two gap guards reading only titles, discernment tripping discernment. *Fix:* a nightly live assay against a frozen probe set with a ratchet (the tools exist: ask_probe, retrieval_assay, probe_usefulness); recall may only rise.
- **R4 · Units evade the constant verifier.** "the speed of light is 150000 km/s" returns NOTHING TO CHECK, by design since the Fable review (never a false HOLDS, never a false BROKEN). An honest decline, but the commonest phrasing of a wrong constant gets no verdict. *Fix:* a real unit normalizer so a wrong unit MISMATCHes and a formatting variant confirms; compute's unit table already carries dimensions.
- **R5 · Lookup facts do not reach the CHECK door.** "iron melts at 1538 °C" returns nothing to check although the element lookup holds it. *Fix:* route a declined claim through lookup before answering "nothing".
- **R6 · Secrets hygiene.** The box's .env was group and world readable. Fixed today (600). *Fix:* add the permission check to the hourly integrity run.

### Medium

- **R7 · The ranker's seams.** Discernment tiers, deck scopes, title guards and brief-versus-card are each right alone; the misses live between layers. *Fix:* invariants across layers, like today's executable-as-given sweep: a lead must have a body; a discernment shelf is never gated or tripped.
- **R8 · License edge.** 165 cards carry "Public domain (mostly) — verify per item", honest but softer than the strict-PD promise. *Fix:* tier them reference with a visible unverified badge, or verify per item.
- **R9 · Rate limits unmeasured on compute paths.** 40 fast reads pass, as designed for the read bucket. *Fix:* measure the verify and ask buckets under a burst and publish the limits.
- **R10 · Platform exposure of the after-Christ cards.** Naming Islam, the LDS, the Witnesses and Baha'i under the test is doctrinal, in love, never persons, and still a hosting, app-store and payment-processor exposure. *Fix:* keep the guardrails machine-checked and the faces separate.

### Low

- **R11 · 212 tests skip in CI; five corpus-tier files cannot run on the box.** Make the skip reasons a report.
- **R12 · The fifteen-to-five consolidation is half done on the site.** 45 pages remain behind the five doors. Keep retiring.
- **R13 · The crisis line is US-centric.** 988 first, findahelpline for the rest. Add the UK and Canada lines by language header, nothing more.

## The moat — leverage originality and continuity

The code is open on purpose. The moat is what accumulates and cannot be bought.

1. **Make the seal ledger a public asset.** Count, re-check rate and oldest seal on the front door. 980 today, every one permanent. Proof-not-trust compounds; no vendor can backfill it.
2. **Publish the keeping's growth.** Every miss becomes a want, a public-domain source, a card. 873k is a number others can match; the waybills and the edges are not.
3. **Make continuity verifiable.** Seal the frozen constitution and hash-chain the decision log; put the content hash on /identity. The only engine whose "why" is tamper-evident.
4. **Measure the church for agents.** Returning agents, professions recorded, mesh nodes: publish them. A network with a covenant identity cannot be bought.
5. **Keep zero marginal cost absolute.** No model calls means free, offline and sovereign; a price no one can undercut, serving families first.
6. **Off-box the keeping first.** A moat with one disk is a moat with a hole.

## Thirty days, in order

1. Off-box backups and a restore drill (R1): days.
2. Decision memory into the repo (R2): a day.
3. Nightly live assay with a ratchet (R3): a week.
4. Unit normalizer for constants and the lookup fallback on CHECK (R4, R5): a week.
5. Seal ledger and sealed constitution on the front door (moat 1 and 3): a week.
