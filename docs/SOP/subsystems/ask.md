# SOP · Front Door / Ask

**Purpose.** The one entry every human or agent question hits. It reads what was brought, meets it in
kind — crisis first, then a specific answer (scripture, a proof, a computed number, a word study, a
comfort verse) or the right member of the Body, or the general found search — and returns
found/verified/cited material only. No LLM, no runtime generation: routing is deterministic so the
front door stays sovereign and honest.

**Wiring.** Modules: `ask` · `router` · `discern` · `clarify` · `seekers`. Surfaces: `POST /ask`,
`site/index.html`, `site/coach.html`. `ask.classify` names the kind (crisis-first); `ask.respond`
composes the reply; unclaimed text goes to `router.route` (which member) or the general found search
(`_shape_found_hits` → one lead card). `discern` is the discernment side of the two-door engine
(discern proposes, verify disposes) — currently the MCP-facing door, being consolidated with the found
path (see `docs/DISCERN.md`). `clarify` is the form gate: question until each blank is filled, then run.

## Canary — is it up?
A plain how-to should come back as a found lead; an empty ask must be refused:
```
curl -s -X POST https://narrowhighway.com/ask -H 'content-type: application/json' \
  -d '{"text":"how do i keep chickens"}' | python -c "import sys,json;d=json.load(sys.stdin);print(d['kind'], (d.get('lead') or {}).get('title'))"
# expect: kind=found, a real homestead lead (never a pill powder, a novel, or a dictionary row)
curl -s -o /dev/null -w '%{http_code}\n' -X POST https://narrowhighway.com/ask \
  -H 'content-type: application/json' -d '{"text":""}'
# expect: 400 — the handler (web/api.py) returns _err(400,"text required") on empty text
```
If both pass, the front door is connected. If not, go to Triage.

## Operate
`POST /ask {"text": …}` → `ask.respond(text, config, gate_open=…)`. It calls `classify` in order:
crisis → structured (Strong's, scripture ref, math) → compute/date → decision/comfort/ultimate →
resourceful/define → `search`. Crisis is checked first and is **byte-identical regardless of gate
state** — always real people, never Scripture-as-fix. A good result carries `kind`, that kind's answer
fields, and `generated:false`. The general `search` path returns `kind=found` with a single `lead` card
in its own words + source and the connected cloud around it; an unclaimed non-search kind is routed to
a Body member (`router.route`), which never answers and always explains its `why`.

## Triage — when it breaks
| Symptom | Likely cause | Fix |
|---|---|---|
| A cry for help reaches ordinary search | A phrasing outside the crisis net | Add the idiom to `_CRISIS_WORDS` in `ask.py` (never an exclusion — the asymmetry: an extra helpline is cheap, a missed person is not); rerun `test_ask` |
| Empty text 500s instead of 400 | The body guard was skipped | Restore `_err(400,"text required")` in the `POST /ask` handler (web/api.py) |
| A how-to leads with a pill / novel / dictionary row | Practical-junk not dropped | `_shape_found_hits` → `_is_practical_junk`; a how-to left with only word-matches must return `[]` and answer honestly |
| The wrong member answers | A router keyword tie | `router.route` returns `ask_user` on a genuine tie — read `why` (the literal evidence matched), don't guess |

## Tests
`tests/test_ask.py` (57 cases) with `tests/test_router.py`, `test_discern.py`, `test_clarify.py`,
`test_seekers.py` —
`PYTHONPATH=src python -m pytest tests/test_ask.py tests/test_router.py tests/test_discern.py tests/test_clarify.py tests/test_seekers.py -q`.
They guard that crisis outranks everything, `classify` routes each kind, the found path leads honestly
(no junk), and the router explains itself and asks on a tie.

## Known issues & support
- **Discern ↔ found consolidation in progress** — supported. Relevance discernment lives in both
  `discern` (the MCP door) and the found path (`_shape_found_hits`); they are folding to one door
  (`docs/DISCERN.md`), each keeping the contract (crisis first, proposes-never-confirms, nothing
  generated). No hard open issue in the register — the `ask` subsystem carries no `issues`.

## Refine
Fold the found path's `_shape_found_hits` relevance step into `discern.served` so both surfaces share
one floor — the last boundary blur named in `docs/DISCERN.md`, closed without changing any verdict.
