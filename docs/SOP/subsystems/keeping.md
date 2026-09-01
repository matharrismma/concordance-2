# SOP · The Keeping / Corpus

**Purpose.** The retrieval substrate — the one shared library the whole engine draws from. It ranks
~548k cards for a query and hands back what the keeping already holds (the Hare's fast answer), so
Find (the Tortoise) is only reached when the keeping is genuinely thin. FOUND and attributed, never
generated.

**Wiring.** Modules: `corpus` · `corpus_db` · `graph` · `decks` · `wayfind` · `growth`. `corpus` is
the ranked search (`_score`, TF-IDF over card text with a hard subject partition); `corpus_db` is the
sharded freeze/unfreeze store so it runs on small devices; `decks` is the Hare fast-path (score a
shelf subset, fall back to the whole keeping); `graph` is the connection graph behind the visual map;
`wayfind` is the floorplan; `growth` is the standing engine that improves the keeping without
regressing. Surfaces: `GET /search?q=`, `GET /cards/stats`, `GET /cards`, `GET /card`.

## Canary — is it up?
Search a common word and confirm ranked results, then confirm the two-number substance count:
```
curl -s "https://narrowhighway.com/search?q=grace" | python -c "import sys,json;d=json.load(sys.stdin);print(d['count'], (d['results'][0]['title'] if d['results'] else 'NONE'))"
curl -s https://narrowhighway.com/cards/stats | python -c "import sys,json;d=json.load(sys.stdin);print(d.get('total_cards') or d.get('total'))"
# expect: a non-zero count with a real lead card; /cards/stats returns the live totals (~548k).
```

## Operate
Automatic. `corpus.search(query, limit)` tokenizes, drops stopwords, picks the SUBJECT SEAT among the
words actually asked, and scores each candidate. The score is `sum(tf·idf)/log(len)` **plus a hard
partition**: `SUBJECT_TIER` (=1000.0, `corpus.py` ~line 456) is larger than any reachable TF-IDF
score, so a card that contains the subject word cannot be out-shouted by a card that merely repeats
the other words many times. This is what stopped "Wesleyan Church" from returning Reformed confessions
(`_score` docstring). Frozen stubs are re-scored on their real shard text so freezing never reorders
results. Substance is measured by `ops.substance` — a body under `STUB_BODY_CHARS` (=120) is a stub, a
pointer not an answer.

## Triage — when it breaks
| Symptom | Likely cause | Fix |
|---|---|---|
| A distinctive query ("what is Mahavira") returns unrelated cards | We hold nothing for the subject word, so only stopwords contributed | Working as intended — a gap must report itself and feed the want list; do not paper over it with a weak match |
| A thin "title-only" card leads the results | It's a stub (body < 120 chars) that matched on its title | The `~67% word-match stubs` issue below; substance-aware ranking is the fix, not a per-card patch |
| A card that only *mentions* the subject outranks one that *answers* it | The subject tier is pure lexical presence — it can't tell a headword from an answer | The `ranker blind to substance vs headword` issue below |
| A frozen card scores wrong / results reorder after a freeze | Rehydrate didn't fire, or the shard is missing | `rehydrate(card)` pulls the real body from the shard; confirm `CONCORDANCE_DATA_DIR` shards are present |

## Tests
`tests/test_corpus.py`, `tests/test_graph.py`, `tests/test_decks.py`, `tests/test_wayfind.py` —
`PYTHONPATH=src python -m pytest tests/test_corpus.py tests/test_graph.py tests/test_decks.py tests/test_wayfind.py -q`.
They guard the subject partition (a card without the subject word cannot outrank one with it),
stopword-only queries returning nothing, the deck fast-path falling back to the full keeping, and the
floorplan routing.

## Known issues & support
- **~67% word-match stubs** — unsupported. Two thirds of measured cards are pointers (body < 120
  chars), not answers. Interim support: `ops.substance` reports the honest two-number split (total vs
  substance) so the keeping's reach is never overstated, and Find grows real substance on a miss.
- **Ranker blind to substance vs headword** — unsupported. The subject tier is lexical presence only,
  so a card that names the subject can win over one that actually answers it. Interim support: the
  hard partition still keeps the *wrong tradition* off the lead; the real fix is substance-aware
  scoring (Part 3).

## Refine
Add a substance signal to `_score` so, *within* the subject tier, a card that answers the question
(real body, dense subject terms) ranks above one that merely mentions it — closing the headword-vs-
answer gap without disturbing the partition that keeps the wrong subject out entirely.
