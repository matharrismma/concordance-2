# SOP · Prophecy

**Purpose.** Show how the Old Testament points to Jesus Christ — the OT prophecy laid beside the New
Testament verse that names it fulfilled, both texts in full, plus the cross-cultural signposts (Plato,
the Shatapatha Brahmana, the Great Isaiah Scroll) that turn toward the same destination. A conduit,
not an interpreter: the pairing is Scripture's own witness, carried in `source`, never asserted by us.

**Wiring.** Modules: `prophecy` · `prophecy_fulfillments`. Surfaces: `GET /prophecy` (and `?ref=`,
`?id=mp_*`, `?id=<trace>`, `?fulfillments=1`, `?q=`), `site/prophecy.html`. Also reached from
`ask.respond` when a "prophecies about X" ask routes to the prophecy member (searched by topic, not by
the routing words). `prophecy` loads `data/prophecy/signposts.jsonl` (cross-cultural traces);
`prophecy_fulfillments` loads `data/prophecy/messianic.jsonl` (the OT→NT map).

## Canary — is it up?
Confirm both maps answer under the one door:
```
curl -s "https://narrowhighway.com/prophecy" | python -c "import sys,json;d=json.load(sys.stdin);print('traces', d['total'])"
# expect: traces 30  (the cross-cultural signposts, each with a verdict)
curl -s "https://narrowhighway.com/prophecy?fulfillments=1" | python -c "import sys,json;d=json.load(sys.stdin);print('pairs', sum(len(v) for v in d['themes'].values()), 'themes', list(d['themes']))"
# expect: pairs 50  themes [birth, ministry, passion, resurrection, …]  (the curated NT-explicit map)
```
`?ref=Isaiah 53` returns the fulfillments touching that chapter; `?id=mp_*` returns one whole pair.

## Operate
`GET /prophecy` with no params lists the signpost traces (`prophecy.list_traces`); `?q=` searches
them; `?id=<trace>` opens one. `?fulfillments=1` returns the whole OT→NT map grouped by theme
(`pf.list_all`); `?ref=<verse|chapter>` matches book+chapter against every OT and NT ref so a reader
standing on Isaiah 53 sees what the NT takes up from it (`pf.for_ref`); `?id=mp_*` returns one pair
whole, both verses' text carried so the reader weighs the pairing themselves, never on our say-so.

**It NEVER HOLDS.** Fulfillment is not a deterministic proof, so nothing here is sealed as math: the
verdict is `CONCORDANT` (for the NT-explicit map) or `CONCORDANT`/`MIXED` (for the signposts), and the
destination is always Jesus Christ, not this map (1 John 4:1-3 the discriminator). The build tool
**omitted, never guessed**, any pair whose references did not resolve — an honest gap over a fabricated link.

## Triage — when it breaks
| Symptom | Likely cause | Fix |
|---|---|---|
| `?fulfillments=1` returns 0 pairs | `data/prophecy/messianic.jsonl` absent | `python tools/build_prophecy_fulfillments.py` (it omits any pair whose refs don't resolve) |
| `/prophecy` returns 0 traces | `data/prophecy/signposts.jsonl` absent | `python tools/migrate_prophecy.py` (ports the 1.0 almanac) |
| A pair shows `HOLDS` or a seal | contract violation — prophecy must never seal | This layer is a signpost; verdict stays CONCORDANT, unsealed. Investigate the record's source |
| An OT prophecy has no NT pair | it's outside the NT-explicit set (see below) | Expected today — only the pairs the NT itself names are mapped |

## Tests
`tests/test_prophecy.py` · `tests/test_prophecy_fulfillments.py` — run
`PYTHONPATH=src python -m pytest tests/test_prophecy.py tests/test_prophecy_fulfillments.py -q`.
They guard that verdicts are CONCORDANT/MIXED and never HOLDS, that both verses' text is carried, and
that `for_ref` matches by book+chapter.

## Known issues & support
- **The full OT prophecy sweep is not yet run** — *unsupported* (mirrors the `systems.py` register).
  The shipped `messianic.jsonl` is the **50 pairs the New Testament itself names as fulfilled** — the
  verified, conduit-safe subset. Sweeping *every* OT prophecy to its NT fulfillment (per the vision,
  `project_prophecy_ot_to_nt_fulfillment`) is future work: it needs a build that stays a conduit —
  each pair carried by Scripture's own citation, unresolvable refs omitted — never an interpreter.

## Refine
Extend `tools/build_prophecy_fulfillments.py` to admit the next tier — OT prophecies the NT alludes to
(not only "that it might be fulfilled" quotations) — each still carrying its NT citation and omitting
what does not resolve, growing the map toward the full sweep without ever guessing a link.
