# SOP · Field Library

**Purpose.** The practical homestead/prepper how-tos, the reference data, and the exact computation behind the
front door — answered FOUND or COMPUTED, never generated. "Convert 10 miles to km" gets the number; "how do I
purify water" gets a real survival card, not a keyword-matched stub.

**Wiring.** Modules: `apothecary` (herb monographs, verbatim — safety notes and an honest evidence verdict
travel with every entry; offers land in a curated queue, nothing self-publishes) · `almanac` (1.0 verdicts
RE-SEALED on the live 2.0 engine, verified-only) · `playbook` (the Body's confessed testimony — signed,
append-only, four-gate confirmation routed through `kernel.gate`: quarantine → confirmed) · `compute` (the
deterministic calculator — arithmetic, %, roots, unit + culinary + temperature conversion; declines unless
exact) · `science_cards` · `chess`. Surfaces: `POST /ask` (a conversion routes to `compute`; a how-to routes to
the practical pool), `GET /apothecary` + `POST /apothecary/propose`, `/almanac.html`, `/playbook.html` + signed
playbook writes. **DEGRADED today** (`systems.py` `degraded:True`): the shelves are thinly stocked — 12 herb
monographs, 41 re-sealed almanac entries.

## Canary — is it up?
```
curl -s -X POST https://narrowhighway.com/ask -H 'content-type: application/json' \
  -d '{"text":"how many teaspoons in a tablespoon"}' \
  | python -c "import sys,json;d=json.load(sys.stdin);print(d['kind'], d['message'])"
# expect: compute  1 tablespoon = 3 teaspoons   (computed exactly, and sealed so anyone can re-check it)
```
And a how-to: `{"text":"how do i purify water"}` → `kind:found` leading with a real survival/first-aid card —
never a drug, dictionary, or fiction stub. If a conversion returns a dictionary card, go to Triage.

## Operate
`POST /ask` classifies first: if `compute.answer(text)` is non-`None` it returns `kind:compute` with the exact
statement, sealed via `receipts.attach` (a number speaks the project's one language). Otherwise a practical
how-to runs `_practical_pool`, which searches the INSTRUCTIONAL field shelves FIRST (so a real field card is in
the pool even when an auto-generated DB row outranks it globally on a shared word), then ranks. The apothecary
and almanac are also directly browsable. Every payload carries `generated:false`.

## Triage — when it breaks
| Symptom | Likely cause | Fix |
|---|---|---|
| a how-to leads with a pill/dictionary/novel ("keep chickens" → a Tongkat Ali OTC drug) | auto-generated DB rows (`card_src_drug_*`, product noise, `fiction`) outrank a field card on a shared word | `_is_practical_junk` (`ask.py:722`) filters them off the lead — by drug-id prefix, product noise, fiction meta, junk shelves. If one slips through, extend it |
| a conversion returns a dictionary card, not the number | `compute.answer` did not parse the phrasing (classify gates `compute` on it) | add the form to `compute` (`_worded`/`_convert`) — e.g. culinary tsp/tbsp were added 2026-08-31 |
| apothecary/almanac return few or no results | shelves thinly stocked (the degraded issue) — 12 monographs, 41 entries | expected today; grow the shelves — not a break |
| a proposed remedy never appears on any endpoint | `apothecary.propose` WRITES to a queue, it never publishes | by design — the keeper curates by hand; nothing self-publishes |

## Tests
`tests/test_compute.py`, `tests/test_apothecary.py`, `tests/test_almanac.py`, `tests/test_playbook.py` —
`PYTHONPATH=src python -m pytest tests/test_compute.py tests/test_apothecary.py tests/test_almanac.py tests/test_playbook.py -q`.
They prove compute is exact-or-declines, search ranks deterministically, the almanac is verified-only, and the playbook's four gates hold.

## Known issues & support
- **Shelves thinly stocked** — unsupported. 12 herb monographs and 41 re-sealed almanac entries is a thin field
  library. Interim support: the practical-junk filter + instructional-shelf-first pool keep a thin shelf from
  LEADING with a stub, and every acquisition batch net-grows the keeping (`card_sources`); the real fix is
  stocking the shelves. (Mirrors the register in `systems.py`.)

## Refine
Work the apothecary curation queue and re-seal more 1.0 almanac entries through the live engine, so a practical
how-to leads with a real card rather than falling to the tortoise — each pass net-grows the keeping.
