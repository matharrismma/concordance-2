# THE OPERATIONS LOG — every piece, mapped, verified, carded

Matt, 2026-07-29: "Everything must be logged. We must be masters of documentation and
logistics. We map, verify, and keep cards on every piece."

The keeping already cards what we *know*. This logs what we *do* — every operational event
that changes the system, with its receipt. Newest first. One line per event minimum:
**what · when · measured evidence · where the proof lives**.

Three standing rules:
1. **No silent anything.** A cap, a skip, a partial run, a thing that could not be checked —
   named here, in the words that are true (found / gone / could-not-check).
2. **Measured, not asserted.** Every claim carries the number it came from and how it was taken.
3. **Every piece gets a card.** Objects (shards, nodes, sources, wings, SOPs) belong in the
   keeping like everything else; this log records the events that create and change them.
   OPEN: operational carding (shards, nodes, curators, deploys) — task #104.

---

## 2026-07-29

**D7 CAPSTONE · the null assay — three rings.**
- Ring A (99 theories): 1 finding — *Agricultural science* claimed `seals` with zero sealed runs
  in the keeping. Corrected to `partial`, reason on the card, restorable when a real run seals.
  99/99 aligned AFTER the correction. Tool: `tools/null_assay.py` (rerunnable, `--json`).
- The instrument lied first: draft 1 asked only "does a verifier exist?" → 9 false findings
  (Gödel, ZFC, evolution, germ theory…). Corrected; pinned by `tests/test_null_assay.py` so it
  cannot drift back into flattering us. **Check the check before you trust it.**
- Ring B (our own theses): 3 findings AGAINST US — the RAS bridge recorded CONFIRMED (science
  yes, the Mt 6:22 bridge is RESONANCE), "the tune is the truth-CRITERION" (a heuristic; name
  its null test), coherence-as-proof (a consistent fiction is coherent). All three memories
  corrected the same night.
- Ring C (adjacent families): nothing contradicts the engine's narrow claims; every tension
  lands on the same seam — deterministic checks are safe, interpretive bridges stay marked.
- Report: `docs/NULL_ASSAY.md`. Gate: 916 passed. Commit `6b2c6e6`.

**Corpus count: 496,559 cards — 49.7% of the 1M goal** (ISBE contributed 9,381 today).

**D6 · security sweep over the new surfaces** — two real holes found and closed.
- ICS injection (`connect_write`): `start_iso`/`end_iso` interpolated into DTSTART/DTEND with no
  escaping and no validation; `_esc` did not escape a bare `\r`. One consented event write could
  have injected ATTENDEE / ORGANIZER / URL or a second VEVENT. Closed: ICS grammar validation +
  every newline form escaped. Proof: `tests/test_security_sweep_d6.py`.
- Unsigned witnesses (`moderation`): self-asserted `reporter`/`viewer` strings meant one person
  with three names could hold TRUE content from public reads, and anyone could edit another
  viewer's block list. Closed: fresh detached signatures over canonical bytes naming the exact
  target; `site/community.html` mints a device-local key so the fix reaches the reader.
- Probed clean: consent (wrong signer / tampered scope / cross-agent / cross-verb / TTL cap /
  private-key smuggling), study routes (traversal, injection, oversize, NUL), card render
  (attribute breakout, `javascript:` URLs), ambiguous-ref last mile.
- Lesson recorded: `docs/SOP/LESSONS.md` (2026-07-29 entry).

**D5 · acquisitions — ISBE 1915, Adam Clarke, John Gill.**
- ISBE: CrossWire SWORD module v2.2 (Public Domain), zLD binary parsed stdlib-only after
  reverse-verifying the layout against real offsets. 9,380 articles / 22.9 MB text →
  `data/acquisitions/isbe.db` (25.3 MB, mmap'd) + 9,381 cards (1 spine + entries, zero orphans).
  Full article renders on the card page (verified live: 19,521 bytes for `card_isbe_aaron`).
- Clarke 854 chapters, Gill 1,189 chapters via bible.helloao.org (the Matthew Henry road);
  registered in `commentary.SOURCE_META` with attribution. **Gill is not on CrossWire at all** —
  helloao was the lawful road for both. Verified live on both surfaces.
- Gate: 903 passed. Commit `f3f35a4`.

**D4 · the shards wired — the heavy shelves ride SQLite.**
- Profiled first (per Matt's decision): dictionary/gutenberg/geography/taxonomy = 258.7 MB
  serialized, ~70% body/bands/extra/source, none of it needed by the graph.
- Live measurement: RSS **2834 / 2809 MB → 1893 / 1908 MB** per process (~1.85 GB freed);
  box available 1.7 → 3.5 GB. Probe battery 33/33 under freeze. IDF proven identical frozen vs
  resident (two regressions caught by the battery first: stub length-normalization boost, then
  corpus-wide IDF drift — both pinned as tests).
- FOUND IN ROLLOUT: `corpus_db.py` had **never been deployed** — the droplet receives files by
  scp, not by checkout, so a module nothing had yet imported was simply absent. Same shape as the
  MANIFEST lesson, on the src side. Fixed by deploying it; worth a guard (see OPEN below).
- Gate: 899 passed. Commits `44fb324` (code), shards built + shipped (964.8 MB, 7 files).

**Kernel coverage floor raised 75 → 90.**
- cas 93 · derivation 90 · ledger 91 · receipts 95 · record 93 · signing 98 · validate 93.
- `tests/test_trust_kernel_edges.py` (12 tests) pins the paths that only run when something is
  wrong — corrupt files, missing signatures, tampered chains, unreachable stores.
- Gate: 892 passed. Commit `eb40812`.

**Shard inventory (from the live manifest).**
| shard | cards | MB | note |
|---|---:|---:|---|
| core | 30,063 | 68.9 | the personal floor — the whole map, any phone |
| science | 52,694 | 96.9 | |
| word | 55,255 | 166.7 | |
| world | 120,556 | 177.7 | |
| dictionary | 149,490 | 226.8 | frozen on the droplet |
| books | 79,120 | 227.8 | frozen on the droplet |
| **full node** | **487,178** | **964.8** | the entire keeping, on an $8 microSD |

---

## OPEN — logged because unfinished is a fact, not a silence

- **Operational carding** (task #104): shards, nodes, curators, sources, deploys, SOPs each get a
  card in the keeping — "cards on every piece". Not started.
- **Deploy completeness guard**: nothing yet proves every `src/concordance/*.py` on the droplet
  matches the repo; `corpus_db.py` was missing for days under a green gate. A manifest for src,
  mirroring `tests/MANIFEST.txt`, would close it.
- **Private key on the wire**: 5 endpoints still accept `private_key` inbound (contract §3/§5).
  Mesh messages were fixed via detached signatures; **§5 is NOT done** — do not claim it.
- Overall test coverage 52% (kernel ≥90). Worst user-facing module: almanac 20%.
- OneDrive drag on the working copy; nav single-source; manifest counts.
