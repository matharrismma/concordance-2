# SOP · Cloud of Witnesses

**Purpose.** Around any answer the tradition's own people speak in their VERBATIM words — Ellen G. White
and the fathers/reformers — but only where the work is public domain (published before 1929). The cloud
proposes a way of seeing; the gate and the Word dispose. Nothing is generated: the voice is the witness's
because it IS his, gathered, never imitated.

**Wiring.** Modules: `witness` (verbatim PD words; load-once cache keyed by `(path, mtime)`; the strict-PD
gate `_is_pd`, fail-closed) · `mentors` (25 named wise men — subject · gift · discern; the PD ones may be
voiced, the rest are characterized only) · `lens` (Matt's OWN writing, the NEAR witness — served ONLY when
`CONCORDANCE_SOVEREIGN_NODE` ∈ {1,true,yes,on}, never on a shared/.com node) · `voice` (the spoken floor:
browser speech always; ElevenLabs ceiling when keyed — `/speak`). Public surface: `GET /witness?q=…[&witness=]`
(the commons — PD text). The cloud is also attached to any served answer through `discern.served()`
(`_cloud_see` = `mentors.for_text` + `witness.see`); the near lens through `_lens_see` (sovereign only).

## Canary — is it up?
```
curl -s "https://narrowhighway.com/witness?q=grace" \
  | python -c "import sys,json;d=json.load(sys.stdin);print(d['gathered'], len(d['seeing']), d['seeing'][0]['witness'])"
# expect: 279 (gathered) · 3 (verbatim passages that frame grace) · Ellen G. White — every one public-domain, attributed
```
If it returns three attributed, public-domain passages, the cloud is connected. If `seeing:[]` with `gathered:0`, go to Triage.

## Operate
Automatic and direct. `witness.see(text, witness=None, k=3)` ranks the gathered PD passages by shared
subject words and returns them verbatim with `witness · work · ref · source`; `mentors.for_text(text)`
proposes the wise men whose craft bears on the input (their gift + the discern note that weighs it). Every
result carries `proposes:true, confirms:false` — never a verdict, never upgraded past what a witness earned.
Honest-empty where the cloud does not yet reach. `witness.available()` reports whether anything is gathered.

## Triage — when it breaks
| Symptom | Likely cause | Fix |
|---|---|---|
| `/witness` returns `seeing:[]`, `gathered:0` | corpus absent, or `CONCORDANCE_WITNESSES` mispointed | confirm `data/witnesses.jsonl` exists (279 rows); check the env override; the cache re-reads on mtime change |
| a gathered witness's words never appear | the row is not marked `public_domain:true` → the fail-closed `_is_pd` gate holds it back | correct behavior — a non-PD witness is characterized in `mentors.py`, never voiced. Only its PD standing may open it |
| the lens (Matt's writing) shows on a public node | it must not — `_lens_see` serves only when `CONCORDANCE_SOVEREIGN_NODE` is truthy | confirm the env is UNSET on shared/.com nodes; the guard is fail-closed (a mistyped `"off"` still stays closed) |
| stale corpus after the gatherer appends | `load()` caches by `(path, mtime)` | expected — it re-reads on the next mtime bump; no restart needed |

## Tests
`tests/test_witness.py`, `tests/test_mentors.py`, `tests/test_lens.py`, `tests/test_voice.py` —
`PYTHONPATH=src python -m pytest tests/test_witness.py tests/test_mentors.py tests/test_lens.py tests/test_voice.py -q`.
They prove the strict-PD gate holds (a non-PD row is never voiced), attribution travels, and honest-empty is honest.

## Known issues & support
- **Founders gather pending (per-work `--start-after`)** — unsupported. `tools/gather_witness.py` needs a
  per-work start offset to cut each work's editorial introduction, so the fathers/reformers are not yet
  gathered. Today the cloud voices the 279-passage Ellen G. White seed and honestly voices nothing where a
  founder is not yet gathered — never a fabricated voice. (Mirrors the register in `systems.py`.)

## Refine
Run `tools/gather_witness.py` per founding work with the `--start-after` offset that skips the editor's
intro, appending only the author's own PD paragraphs; the load-once cache picks them up on the next mtime bump.
