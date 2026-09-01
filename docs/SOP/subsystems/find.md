# SOP · Find / the Tortoise

**Purpose.** When the keeping doesn't already hold what was asked, Find goes and fetches the
tried-and-true public-domain source, proves it, cuts it into cards, and keeps it — so the next asking
is instant. The Hare (kept cards) answers fast; the Tortoise (this) answers surely.

**Wiring.** Modules: `find` · `providers` · `expand` · `craft` · `field_canon` · `sources`. Reached from
`ask.respond`'s found path when the keeping is weak (`expand.pull_and_card`). Providers: Internet
Archive, USDA bulletins, Library of Congress, IA-film (.tv). Gated off in tests (`WEB_FIND_DISABLED=1`).

## Canary — is it up?
Ask something the keeping is unlikely to hold and confirm it pulls + keeps a real source:
```
curl -s -X POST https://narrowhighway.com/ask -H 'content-type: application/json' \
  -d '{"text":"how do i keep bees"}' | python -c "import sys,json;d=json.load(sys.stdin);print(d['kind'], (d.get('lead') or {}).get('title'))"
# expect: kind=found, a real PD beekeeping source (not a stub); a second identical ask returns instantly.
```

## Operate
Automatic — no operator action in normal use. `pull_and_card(text, subject, config, plane)` searches the
active providers (`providers.active()`), fetches a candidate, runs it through `craft` (cut spans that
share the subject's words, re-verified against the held bytes), and appends cards to the live keeping.
Search-once, keep-forever. Every source is credited with a link back (the CREDIT covenant).

## Triage — when it breaks
| Symptom | Likely cause | Fix |
|---|---|---|
| A how-to leads with a wrong/tangential source ("goats for milk" → a waste-water doc) | Pull's source selection matched a shared word, not the subject | The open issue below — add a post-pull relevance check (frame honestly when the lead shares no distinctive word) |
| A provider stops returning results | It failed twice → benched 6h (`providers.record`) | Expected; it re-probes automatically. Check `providers.line()` for the rotation state |
| Pull never fires | `WEB_FIND_DISABLED=1` (tests) or offline | Production only; confirm the env var is unset on the box |
| Non-ASCII source crashes acquisition | Windows cp1252 stdout | Force UTF-8 (`PYTHONIOENCODING=utf-8`) — see the lessons memory |

## Tests
`tests/test_find.py`, `tests/test_expand.py` — `PYTHONPATH=src python -m pytest tests/test_find.py tests/test_expand.py -q`.
They stub the providers (never real HTTP) and prove the pull cards + credits correctly.

## Known issues & support
- **Pull mis-selects tangential sources** — unsupported. The retrieval-relevance limit
  (`project_semantic_retrieval_arc_negative`). Interim support: the practical junk filter + relevance
  floor in `ask.py` keep the worst off the lead; the real fix is Part 3 (substance-aware ranking).

## Refine
Add a post-pull relevance guard in `expand.pull_and_card`: if the cut lead shares no distinctive word
with the subject, don't lead with it — frame it as "the nearest I found" or fall to the honest gap.
