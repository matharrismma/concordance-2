# SOP — Continuous Improvement & Refinement

> Matt, 2026-07-25: *"Create a plan to improve and SOPs for continuing the practices at regular
> intervals. We should continuously improve and refine our processes and methodology."* — and the
> standing measure: *"as useful as possible... still falling short in real life use."*

The engine is never "done"; it is **kept** and it **grows**. This is the repeatable loop that makes
it more useful every cycle, without ever regressing the moat. The score only goes up.

---

## The loop (run every cycle)

```
  MEASURE → TRIAGE → FIX → GATE → DEPLOY → VERIFY LIVE → PUSH → RE-MEASURE
```

1. **MEASURE** real-life usefulness on the questions ordinary people actually ask:
   ```bash
   PYTHONPATH=src python tools/probe_usefulness.py          # local, fast
   PYTHONPATH=src python tools/probe_usefulness.py --live    # against the deployed site
   ```
   It prints a **score** (% useful) and the **BIGGEST GAPS** — the failing questions, and what the
   front door wrongly routed them to. This is the steering instrument (grounded gap analysis, not a
   guess). Baseline when this SOP was written: **47% → 76%** after the compute route.

2. **TRIAGE** — take the biggest gap category first (frequency × how wrong the current answer is). A
   confidently WRONG answer (agape → "mean deviation"; "how far is the moon" → Augustine) is worse
   than a graceful miss and is always top priority.

3. **FIX** at the right layer:
   - *Routing gap* (the tool exists, the front door doesn't reach it) → `src/concordance/ask.py`
     `classify()` + a `respond()` handler. Most real-life gaps are here.
   - *Capability gap* (no deterministic tool yet) → a small, tested module (e.g. `compute.py`), then
     route to it. **Compute, never generate. Decline what you cannot do exactly** (a wrong number is
     worse than none).
   - *Coverage gap* (the knowledge isn't carded) → a `tools/card_*.py` carder (PD/CC0 sources only),
     nested to the Floor/Word, git-tracked spine.

4. **GATE — the discipline that never bends.** Read the REAL exit code and the pass line, never a
   piped tail:
   ```bash
   PYTHONPATH=src python tools/check.py > /tmp/gate.txt 2>&1; echo "REAL_CHECK_EXIT=$?"
   grep -E "GATE (PASS|FAIL)|passed|failed" /tmp/gate.txt | tail -3
   ```
   Deploy ONLY on `REAL_CHECK_EXIT=0` and `=== GATE PASS ===`. New behavior gets a test; new test
   files go in `tests/MANIFEST.txt`.

5. **DEPLOY** — `scp` the changed source/data to the droplet, `systemctl restart nh-com-2 nh-org`,
   confirm `active`.

6. **VERIFY LIVE** — hit the real endpoint; a green local gate is not a live proof (the /mesh
   confession-forwarding bug passed unit tests and only showed live).

7. **PUSH** — commit by explicit path (never `git add -A`; secrets stay untracked), secret-scan the
   diff, push to `origin/master`. Continuous — one push per landed change.

8. **RE-MEASURE** — re-run the probe. The number must have gone up, and nothing else may have fallen.
   When a new gap is found in the wild, **add the question to the battery** in
   `tools/probe_usefulness.py` so it can never silently regress.

---

## The cadence (regular intervals)

| Interval | Practice | Instrument |
|---|---|---|
| **Every change** | the gate, live-verify, continuous push | `tools/check.py` |
| **Weekly** | usefulness probe → fix the top gap → deploy | `tools/probe_usefulness.py` |
| **Weekly** | integrity check (ledger + re-verify seals) | `tools/integrity_check.py` / the Keep |
| **Fortnightly** | connection growth (safe, 0-FP edges) + map harvest | `tools/grow.py`, `tools/mint_edges.py` |
| **Monthly** | corpus expansion — the biggest coverage gap, academics first | `tools/card_*.py` |
| **Monthly** | nesting integrity — no orphans; every spine roots in the Floor | `/floor`, `graph.overview()` |
| **Quarterly** | theory/tradition re-calibration; prune what bore no fruit | the calibration decks |

---

## Invariants — what must NEVER regress (check every cycle)

- **The moat**: nothing is generated; every claim is found, verified, or declined. `generated:false`.
- **Crisis is sacred**: help-first, never gated, never enriched, byte-identical regardless of state.
- **The gate is honest**: facts by default; the Word comes when sought; never coerced.
- **Decline over guess**: a wrong answer betrays the whole thesis. Silence beats a fabrication.
- **Sovereignty**: personal data never leaves the device; secrets never committed; deploys are `scp`.
- **A window, not a wall**: every surface points past itself — to real people, and to Christ.

---

## The gap backlog (living — top of the list is next)

Regenerate the current list any time with the probe; as of this writing:

1. **facts** — route factual questions (moon distance, boiling point, chemical formulas, historical
   dates) to the almanac / element-data / history decks instead of keyword search.
2. **passage phrasing** — "what does Psalm 23 say" (a chapter, no verse) should read the passage.
3. **the vias** — mine more two-tree grafts + the recurring-form crossings (the deepest connections).
4. **more transparencies** — the temporal and scriptural planes on the map.

Keep this list honest: when a gap is fixed, delete it; when a new one is found in real use, add it —
and add its question to the probe battery.
