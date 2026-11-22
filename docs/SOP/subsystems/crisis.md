# SOP · Crisis / Safety

**Purpose.** Catch a person in crisis before anything else happens, and route them to real people —
never to the gate, never to a generated answer. There is ONE matcher, `ask.is_crisis`, that every
surface calls; a copied list is a list that drifts, so there is only ever one.

**Wiring.** Modules: `crisis_semantic` · `floor` · `seeds`. `ask.is_crisis` is the net: a fast,
exact substring list (`_CRISIS_EXACT` / `_CRISIS_WORDS`) **unioned** with a deterministic semantic
backstop (`crisis_semantic.flags` — a cosine over PPMI word-vectors sealed into
`data/crisis_semantic.json`, no LLM) that catches veiled cries sharing no keyword ("nothing keeping me
here since he passed"). The backstop only ever ADDS a catch, so the net can widen but never shrink; an
absent or malformed artifact returns False (substring-only), never a crash. `floor` (the mapped floor
of reality, Prov 9:10) and `seeds` (the Areopagus attributed seeds — signpost, never HOLDS) are the
foundation this net guards. Surface: `POST /ask` classifies crisis FIRST (`ask.classify`), before any
structured, ultimate, or search routing.

## Canary — is it up?
Confirm a plain cry routes to crisis and an ordinary lookup is NOT swept:
```
curl -s -X POST https://narrowhighway.com/ask -H 'content-type: application/json' \
  -d '{"text":"i want to end my life"}' | python -c "import sys,json;print(json.load(sys.stdin)['kind'])"
# expect: crisis   —   and "how much does a gallon of water weigh" -> NOT crisis (a benign lookup is never met with a helpline).
```

## Operate
Automatic and first in line. `is_crisis(text)` normalizes the text (smart quotes, apostrophes,
whitespace — the check must not depend on the keyboard), tests the substring net, then unions the
semantic backstop for the veiled cries. The backstop carries two deterministic false-positive guards,
each verified to hit 0 of the curated `CRISIS_FLOOR` and 0 of the blind red-team set: `_BENIGN_MEASUREMENT`
(a physical measurement/conversion is never a cry — "gallon of water weigh" scored 0.694, above the
threshold, and is guarded out) and `_THEODICY` ("why does God allow suffering" scored 0.691 — the
seeker's oldest question, not distress). The asymmetry is deliberate: an unnecessary helpline is a
small cost; a missed person is not.

## Triage — when it breaks
| Symptom | Likely cause | Fix |
|---|---|---|
| A veiled cry is missed (routes to search, not crisis) | The sealed artifact is absent/malformed, so only the substring net runs (recall floor drops 58 → 37) | Rebuild `data/crisis_semantic.json` with `tools/build_crisis_semantic.py`; confirm `crisis_semantic.available()` is True |
| A benign lookup is swept to crisis | A new topic collides with the crisis cluster (topic ≈ intent limit of a distributional model) | Add a TIGHT deterministic guard like `_BENIGN_MEASUREMENT` / `_THEODICY`, then prove 0 hits on `CRISIS_FLOOR` + `RED_TEAM` before shipping |
| `is_crisis` raised instead of answering | A non-string reached it, or the backstop threw | Both are already defended (coerces input; the backstop catches all and returns False) — if it recurs, the safety check must fail to False, never crash |

## Tests
Three files, all named `tests/test_crisis_*.py`, and the name is load-bearing — see the cache rule
below. `PYTHONPATH=src python -m pytest tests/test_crisis_coverage.py tests/test_crisis_profession.py
tests/test_crisis_threshold.py tests/test_seeds.py -q` (`test_seeds.py` for the seeds foundation).

- **`test_crisis_coverage.py`** — the durable load test. It measures the REAL net (substring UNION
  backstop): recall floor = 100% on the curated `CRISIS_FLOOR` (the net may only grow), precision
  floor = 0% on clearly-benign (incl. engine-domain collisions like km / kill-process / idioms), and
  the blind red-team recall RATCHET at **`_RED_TEAM_FLOOR` = 64** (`_SUBSTRING_ONLY_FLOOR` = 37
  without the artifact) — the number never shrinks. A guard test proves the backstop-absent path
  still holds the substring floor. *Read the ratchet from the constant, never from prose: this
  section said 58 until 2026-11-22, two ratchets out of date.*
- **`test_crisis_profession.py`** — a profession of faith is never a cry, and a cry wearing one still
  reaches help (#23).
- **`test_crisis_threshold.py`** — the backstop threshold is derived from the UNGUARDED benign lines
  and a rebuild may never shrink the net (#41).

### The artifact cache rule — why the file name matters
`crisis_semantic` memoizes its sealed 2.1 MB artifact on the first `_load()`, keyed on
`CONCORDANCE_DATA_DIR`, which ~50 test modules point at an empty tempdir. Whichever dir wins that
first load is settled by **collection order**, and it fails in both directions:

- poisoned cache → the backstop goes silent and recall drops to the substring-only floor: a
  **false red** caused by nothing but test order;
- the threshold pins → they do not fail, they `pytest.skip("crisis_semantic.json artifact not
  present")` with the artifact present on disk: a **false green**. Measured 2026-11-22 at `e064b0f`,
  this is exactly what CI had been doing since those pins were written — `pytest -q` prints the skip
  as an `s` indistinguishable from the legitimate corpus skips.

The guard is the autouse `_backstop_from_real_data` fixture in **`tests/conftest.py`**, which pins
the real data dir and reloads the cache for every test in a `test_crisis*` module, restoring both
module globals and the env var afterward. It lived in `test_crisis_coverage.py` and had to be
imported by name; `test_crisis_threshold.py` never did, which is how the false green survived. So:
**name any new crisis test file `test_crisis_*.py` and it inherits the guard by existing.** A file
named otherwise gets no guard and its artifact assertions will silently skip. Never rely on running
a crisis file alone — that hides exactly this class of defect.

## Known issues & support
- **Open items: `docs/REMAINING.md` → the crisis section.** This heading read "**None open**" until
  2026-11-22, when it was stale; keep it pointing at the sheet rather than restating a count here.
  `crisis-7` — the artifact-cache false green described above — is fixed.
- The subsystem's **strength is its shape**: one matcher every surface calls (a copied list drifts),
  crisis-first, a net that only ever grows, a durable ratcheting regression floor, and deterministic
  false-positive guards for the known topic≈intent collisions (measurement, theodicy, profession,
  domestic how-to). Every change must preserve 100% recall on the curated floor and 0 false-positives
  on the benign set.
- **The substring net has no guard layer** — `guarded()` suppresses only the backstop — and
  `is_crisis` UNIONS the two, so nothing downstream can overrule a fire on any door. Some false
  positives are therefore deliberate, pinned **FIRING** by test as an owner decision. Read the pin's
  own message before "fixing" one: making it silent means reversing that decision and dropping the
  cries it was accepted to catch.

## Refine
As new veiled phrasings surface in live passes, add each to `CRISIS_FLOOR` (the net only grows) and,
if the backstop needs it, re-seal `crisis_semantic.json` — always re-proving the recall floor holds at
100% and the two guards still hit 0 curated/red-team cries before it ships.
