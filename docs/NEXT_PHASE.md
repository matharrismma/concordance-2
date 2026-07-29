# NEXT PHASE — written 2026-07-29, to be acted on without re-deriving anything

Handoff written under `docs/SOP/HANDOFF.md`. Read that first if you are picking this up cold.

---

## 1 · STATE OF THE WORLD (measured this session)

| | value | how it was measured |
|---|---|---|
| cards | **541,281** | `corpus.default_corpus()` after loader registration |
| substance (body ≥120 chars) | **311,218 (57.5%)** | same pass; **both numbers, always** |
| to 1M substance | **688,782** | |
| gate | **926 passing** | `PYTHONPATH=src python tools/check.py` |
| live RSS | **1,572 / 1,560 MB** (was 2,834/2,809) | `ps aux` on the box after the freeze widened to 24 shelves |
| box headroom | ~4.3 GB of 7.75 GB | `free -m` |
| ark | verified backup + 7 shards + source archives | `tools/ark_pull.sh`, hash re-checked locally |
| restore | **rehearsed** — 499,716 cards loaded from the ark's copy | unpacked to a scratch dir and searched |

Deployed and live: D4 shard freeze, D5 acquisitions (ISBE/Clarke/Gill), D6 signed witnesses,
the commentary verse cards, domain-core cards.

---

## 2 · FIRST ACTION (verbatim)

```bash
cd /c/Users/hdven/OneDrive/Documents/Claude/Projects/concordance-2 && PYTHONPATH=src python tools/extract_topical.py --dry-run
```

That re-runs the topical extractor (Nave's) and prints the counts. It is already **written to
disk** (`data/topical_cards.jsonl`, 7.2 MB, 2,929 cards / 29,221 edges) but deliberately **NOT
registered** — the keeping is unchanged and nothing is half-live.

**To finish the pass:** add `"topical_cards.jsonl"` to the extras list in
`src/concordance/corpus.py::load_cards` (next to `commentary_verse_cards.jsonl`), run the full
gate, rebuild shards **on the box** (not locally — cheaper than shipping a gigabyte), restart
staggered, verify a topic card renders its links, commit.

---

## 3 · STAGED — written, inert, needs wiring

| artifact | state | what it needs |
|---|---|---|
| `data/topical_cards.jsonl` | 2,929 cards, 29,221 edges, **not registered** | loader entry → gate → shard rebuild → deploy |
| `tools/extract_topical.py` | works for Nave; guards refuse unparsed modules | commit |
| `tools/card_sword_dicts.py` | full-text carder — **do not run as written** | rewrite to the SCAN doctrine (its docstring already says how) |
| `data/acquisitions/{Smith,Nave,Torrey,Hitchcock,AmTract}.zip` | fetched, PD, quarantined | Smith/AmTract need definitional-core extraction |

---

## 4 · KNOWN FAILURES (diagnosed — do not re-debug)

- **Torrey**: the zLD walk recovers **0 entries**. Its module uses a different internal layout
  (likely RawLD, not zLD). Reported UNPARSED; nothing taken. Fix = a RawLD reader.
- **Hitchcock**: parses **7 "entries"**, each a blob of many names run together — the block
  splitting does not match this module. A guard now refuses any names module returning <100
  entries, because a wrong card is worse than none. Fix = correct block boundaries.
- **Nave**: 93 entries had no resolvable reference (nothing taken); 4,069 references did not
  resolve to a book we hold. Both counted, neither hidden.

---

## 5 · DECISIONS ALREADY MADE (do not re-litigate)

- **SCAN, do not reproduce.** Matt: *"We aren't trying to give away the source. We want the
  knowledge."* Take structure (topic→verse), facts (name→meaning), definitional cores with a
  pointer back. Never mirror an article. Where prose is all there is, take nothing and say so.
- **Lawful access is the line, not ownership.** Owning a book does not authorize downloading
  someone else's copy. Facts and ideas are not copyrightable, so extraction from lawfully
  accessed work is fine — buy the ebook, scan only the pages you need, or read and card.
- **The airlock is the machine**: quarantine → extract → flush. `airlock.py` exists.
- **Translation**: lawful for PD works, and a derivative work for copyrighted ones (so it
  unlocks nothing there). Needs its own arc — offline model or BYO-credential, edge-only,
  always marked machine-translated with the original beside it.
- **Both numbers, every time.** Total and substance.
- **Buying books is not the growth path.** PD/open covers most of it: 101 PD English CrossWire
  modules, 77,700 Gutenberg volumes, all US-government works.

---

## 6 · THE QUEUE, IN LEVERAGE ORDER

1. **Finish the topical pass** (above) — 29,221 found edges, already computed.
2. **Fix the two parsers** — RawLD reader for Torrey; block boundaries for Hitchcock. Together
   ~2,500 name facts + a second topical index.
3. **Smith's + American Tract**, definitional-core extraction (~4,000 substance cards).
4. **The other 96 PD CrossWire modules** — Matthew Henry *complete* (we hold only 269 chapter
   files), Jamieson-Fausset-Brown, Keil & Delitzsch, Calvin, Catena Aurea, Spurgeon's Treasury.
5. **The probed-live open sources**: NIST constants, openFDA, DailyMed, NOAA, GBIF, OpenAlex
   (all reachable; Gutendex needs a trailing slash, USDA's API moved).
6. **Then the standing arcs**: #102 Commons · #103 Distributed node roles · #104 Card every
   piece.

---

## 7 · WHAT I DID NOT DO (the refusal list)

- **Contract §5 is NOT done** — five endpoints still accept `private_key` inbound. Only mesh
  messages were converted to detached signatures. Do not read the D6 sweep as closing it.
- **Three dead files remain on production** (`web/ask.py`, `web/branding.py`, `web/config.py`,
  leftovers from a July 25–26 refactor, inert and imported only by each other). Deleting on a
  live box is destructive; it waits for Matt's word.
- **The topical cards are not live** — written, not registered, not gated, not deployed.
- **Overall test coverage is 52%**, not 90. The kernel is ≥90; the domain verifiers are 13–25%.
- **`tools/card_sword_dicts.py` was never run** — it was built to card full articles, which is
  the thing Matt said not to do. It is staged for rewrite, not for use.
