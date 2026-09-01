# SOP · Original Tongues

**Purpose.** Take a reader back of the English to the word that was actually written — the Greek or
Hebrew behind a term, its Strong's definition and every place it occurs, an honest pronunciation
guide, and the full 1915 ISBE article — found and attributed, never generated. The lexicon is the
plumb-line: we serve the lexicon's own words, not our paraphrase of them.

**Wiring.** Modules: `pronounce` · `translate` · `isbe`. Reached from `ask.respond`: a Strong's
number (`G`/`H`) routes to `word_study`; "what does X mean / define X / meaning of X" routes to
`define`, looked up on `_WORD_SHELVES` (`lexicon`, `tongues`, `hebrew_ot`, `greek_nt`, `dictionary`,
`thesaurus`, `word`). `word_study` calls `verifiers.scripture.word_study(strongs)`; `translate`
glosses running text from the held Strong's lexicons; `isbe` serves full articles from
`data/acquisitions/isbe.db` behind the 9,380 stub cards.

## Canary — is it up?
Ask for a meaning and confirm the term is resolved from the word shelves (not sentence-matched):
```
curl -s -X POST https://narrowhighway.org/ask -H 'content-type: application/json' \
  -d '{"text":"what does agape mean"}' | python -c "import sys,json;d=json.load(sys.stdin);print(d['kind'], len(d.get('results') or []))"
# expect: define  <n>=1..6   (a define answer carrying lexicon/dictionary hits for 'agape', not FTS on the sentence)
```
`{"text":"meaning of shalom"}` likewise returns `kind=define` with the term in its original tongue.
If it comes back `search` with junk hits, the define route or the word shelves are not wired.

## Operate
`define_term(text)` extracts the 1–3-word term from the ask (so "what does agape mean" never becomes
"mean deviation from the mean") and `respond` searches only the word shelves for it — the definition
IS the answer, found and attributed. A `Gxxxx`/`Hxxxx` number takes the deeper `word_study` path: the
original-language entry plus every occurrence. `translate.gloss` reads a foreign string word-by-word
against a held lexicon and **reports its coverage** — it never composes a sentence (fluent output no
source contains is the one artefact this library refuses). `isbe.get(headword)` returns the whole
article; a missing/locked db falls back to the stub — a shorter answer, never a broken page.

**A pronunciation card is a phonetic key, never a substantive answer.** `pronounce` synthesizes an
approximate reading guide (plain form, respelling, IPA) from a transliteration, honestly labeled as a
guide, not a native speaker. So `ask.py` demotes `card_src_pron_*` behind any real hit unless the ask
is explicitly about how a word is *said* (`_shape_found_hits`) — "who composed the Messiah" must never
lead with a phonetic key for "messiah".

## Triage — when it breaks
| Symptom | Likely cause | Fix |
|---|---|---|
| "what does X mean" returns `kind=search` with junk | define route missed / gate closed | Confirm `define_term(text)` matches the phrasing; secular fallback still searches the word shelves first |
| A phonetic key leads a who/what answer | pron demotion not applied | The `card_src_pron_*` demotion in `_shape_found_hits` — verify the id prefix and that the ask isn't "how do you say …" |
| `word_study` returns `unavailable` | Strong's backend/data not provisioned | Expected on the lean WEB-only path; provision `concordance.strongs` data |
| `gloss` returns `NO_LEXICON` | script has no held lexicon | Honest by design — only biblical Greek/Hebrew are held; add a lexicon file + a row in `translate._LEXICONS` |
| ISBE article missing, only a stub renders | `data/acquisitions/isbe.db` absent | Rebuild via the acquisition tool; the stub is the graceful floor, not a fault |

## Tests
`tests/test_pronounce.py` · `tests/test_isbe.py` (also `test_translate.py`) — run
`PYTHONPATH=src python -m pytest tests/test_pronounce.py tests/test_translate.py tests/test_isbe.py -q`.
They prove the guide is honestly labeled and deterministic, the gloss reports true coverage and never
composes a sentence, and ISBE degrades to the stub when the db is absent.

## Known issues & support
- **None in the register.** All three modules resolve and are tested. The one real limit — the gloss
  reaches only biblical Greek and Hebrew — is a *reported* gap (`NO_LEXICON` names what is missing),
  never a silent one, so it does not add a stroke.

## Refine
Widen coverage past Greek/Hebrew by deriving per-language lexicons from verse-aligned Bibles
(`translate.derive_lexicon` already exists, counting not translating) — turning `NO_LEXICON` for the
~700 languages with a Bible into a checkable, sourced gloss.
