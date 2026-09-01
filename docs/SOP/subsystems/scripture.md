# SOP · The Word / Scripture

**Purpose.** The verse people came for — resolved verbatim from the WEB text, never generated —
handed back *with the cloud the keeping connects to it*: cross-references, a public-domain
commentator in his own words, and the communion of witnesses around the passage. This is the
richest, most-connected part of the keeping: Scripture linked to Scripture, to history, to the
people and places of the text. The Bible is the focus; every layer points at it and never replaces it.

**Wiring.** Modules: `canon` · `harmony` · `commentary` · `xrefs` · `backmatter` · `characters` ·
`timeline` · `bible_places`. Surfaces: `POST /ask` (a ref → scripture + cross-refs + commentary +
the connected cloud), `site/bible.html`, `GET /characters`. Reached from `ask.respond` when
`find_ref` discerns a reference (`classify → "scripture"`), gated by the witness surface / open door.
Verse text comes from `verifiers.scripture` over `data/bible_en.jsonl`.

## Canary — is it up?
Ask for a verse on the witness surface and confirm the real WEB text comes back:
```
curl -s -X POST https://narrowhighway.org/ask -H 'content-type: application/json' \
  -d '{"text":"John 3:16"}' | python -c "import sys,json;d=json.load(sys.stdin);s=(d.get('scripture') or [{}])[0];print(d['kind'], s.get('ref'), (s.get('text') or '')[:45])"
# expect: scripture  John 3:16  For God so loved the world, that he gave his …
```
If the text (not just the ref) comes back, the corpus is provisioned and the layer is connected.

## Operate
`find_ref(text)` discerns the reference (strict form, church passage names, then loose/chapter-only
forms validated against the canon). A bare verse reads `scripture.resolve_ref`; a range, a chapter,
or any ask for meaning (`explain …`) reads `scripture.read_passage`. When the gate is open the answer
is enriched: the connected cloud around the verse's card, and — if meaning was asked — TSK
cross-references (`xrefs.for_ref`, each verse resolved beside it) and Matthew Henry's commentary
(`commentary.for_ref`), all found and attributed. `harmony`, `timeline`, `backmatter`, `bible_places`
and `characters` serve the study surfaces (the gospel harmony, the one spine of history, the study
tables, the atlas, the Bible dictionary) — every entry carries refs a reader can open, and where
scholarship genuinely disagrees BOTH positions are carried, never one flattened.

## Triage — when it breaks
| Symptom | Likely cause | Fix |
|---|---|---|
| `/ask` returns a ref but empty `text` | `data/bible_en.jsonl` not provisioned | `python tools/migrate_bible.py` (the verifier degrades to a named gap, never a crash) |
| `.com` returns `kind=search` for a verse | Gate closed — secular fallback (`ask.py` default path) | Expected on a non-knocking context; a scripture ref itself knocks, so the door opens and the Word comes |
| Meaning asked but no `cross_refs` | `data/xrefs/xrefs.db` not built | `python tools/migrate_xrefs.py` |
| Meaning asked but no `commentary` | source not migrated for that book | `python tools/migrate_commentary.py`; a `no_source` status is honest, not a fault |
| `/characters` empty | `data/characters/easton.jsonl` absent | `python tools/migrate_characters.py` |

## Tests
`tests/test_harmony.py` · `tests/test_backmatter.py` · `tests/test_timeline.py` ·
`tests/test_bible_places.py` · `tests/test_characters.py` (also `test_commentary`, `test_xrefs`) —
run `PYTHONPATH=src python -m pytest tests/test_harmony.py tests/test_backmatter.py tests/test_timeline.py tests/test_bible_places.py tests/test_characters.py -q`.
Several are **corpus-dependent** (they fetch WEB text / read the curated tables) and skip or assert
graceful degradation when `data/bible_en.jsonl` and the layer's data are not provisioned — they guard
that the tables point at real, openable refs and never generate.

## Known issues & support
- **None in the register.** This subsystem is a strength — every module resolves and is tested, the
  canon is kept as an honest separate layer (the disputed books never merged into the 66), and every
  served layer degrades to a named gap rather than a guess.

## Refine
Add `tests/test_canon.py` (the one module here without a direct test) so the tested coverage reaches
100% — dropping the subsystem's last stroke to scratch on the Systems Handicap.
