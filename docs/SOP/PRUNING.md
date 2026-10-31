# SOP-14 — Pruning: the winning ticket

> Matt, 2026-10-31: *"Look at neural networks and the winning ticket theory. We need a pruning method and
> SOP."* — *"Transformers, language models and diffusion models."* — and, the same afternoon, the frame
> the method must honour: *"The workbench is in the river of time. No need to wipe. You are always on a
> new table top. You just need a logarithm for each timestamp."*

The keeping grows (933,479 cards, ~1M roads, 117 axes, 18 faces, their vocabularies). The industry's
answer to a dense network is the **lottery ticket**: a sparse subnetwork that carries the whole. This SOP
is that procedure carried over to a deterministic engine that never retrains and never deletes.

`Verified live 2026-10-31` — ✅ `measure` ran on the box against the gates' own corpora and 90 days of
traffic (94,147 texts): **180 of 308 scope words dead (58%)** — and the dead list (`coach me`, `quiz me`,
`see a doctor`, `symptom`, `hungry`, `evicted`, `budget`, `word study`) was the first finding: those are
not noise, they are the village's own questions, which no corpus in the window had asked. A gap in the
test set is not a reason to prune — so the labeled village battery `eval/face_routes.json` was added to
the exercise corpora before any mask. ⚠️ `apply` + the gated loop have not yet changed the live mask
(operator go required — see step 5).

---

## What was found, and what carries over

| Source | Finding | Carried over as |
|---|---|---|
| Frankle & Carbin, ICLR 2019 | a dense net holds a sparse ticket; found by **iterative magnitude pruning** — prune p%, *reset* survivors, retrain, repeat | the loop: MEASURE → PROPOSE p → APPLY → GATE → accept or REWIND |
| Zhou et al. 2019; Frankle et al. 2020 | the ticket is a **mask**; rewind, don't restart | the mask is DATA (`data/ticket/mask.json`), every version kept; regression rewinds one version |
| Sun et al. (Wanda) 2023; SparseGPT 2023 | prune **one-shot**, no retraining, by **magnitude × activation** — importance is measured under real inputs | importance = static trust × fires in a dated window; we never retrain |
| Michel et al.; Voita et al. 2019 | prune **structured** units (whole heads); survivors are the specialised ones | units are whole, reversible things: a scope word, a synonym, a road, a card |
| Sanh et al. 2020 (movement) | keep what **moves toward use** | activation is measured on the gates AND real traffic (`activity.jsonl`) |
| Fang et al. (Diff-Pruning) 2023; DeepCache | importance is **per timestep**; nothing is wiped between steps | a window per measurement — a logarithm for each timestamp; windows are kept, never summed forever |

**What does NOT carry over:** retraining, re-initialisation, deletion. A unit that fired in any gate is
never masked — the gates are our test set, and a ticket that fails the test set is not a ticket.

---

## The units (in order of instrumentation)

1. **Scope words** — the faces' routing vocabulary (`faces._FACES[*]["scope"]`), the keyword bag the Fable
   review called brittle. *Instrumented*: `faces.scope_fires`, consulted by `faces._scores`.
2. **Resolver synonyms** — `domain_resolver._SYNONYMS` (the "dead synonyms = tokenization" lesson). *Next.*
3. **Roads** — by relationship band × participation in least-doubt paths (`chains`). *Later.*
4. **Cards** — by authority × reach (gate/probe results, non-structural in-degree). *Later.*

**Never units:** the verifiers, the kernel, receipts, the ledger, Scripture, the crisis backstop
(`ticket.PROTECTED`). Pruning touches the surfaces and the map; the verification floor is not pruned.

---

## The criterion

```
importance(unit, window) = magnitude(unit) × fires(unit, window)
```

- **magnitude** — static trust. Scope word: specificity = (2 if phrase else 1) / (faces sharing it); a
  generic word shared by k faces is the likeliest false route. Road: the relationship band (1/2/3/5).
  Card: the kernel's authority ladder.
- **fires** — activation in the window: how many of the exercise texts tripped it. The exercise texts are
  the gates' own inputs plus real traffic: `data/recall_phrasings.json`, `data/frontdoor_claims.json`,
  `tools/probe_usefulness.BATTERY`, `eval/face_routes.json` (the village's labeled battery),
  `eval/live_probes.jsonl`, `data/activity.jsonl` (the window), and any `--extra` file (one query per line).
- **dead** — fires = 0. Only the dead are ever proposed; among them, least magnitude first.
- **false fires** (next — needs the labels in `eval/face_routes.json`): a word that fires on requests meant
  for ANOTHER face is a false route even though it is alive; with labels, importance becomes
  magnitude × (true fires − false fires), and a net-negative word is proposed ahead of the dead. This is the
  criterion "dead only" cannot see — the generic words (`why`, `need`, `help`, `law`, `cold`) that fire
  everywhere.

---

## The loop (run every cycle)

```
  MEASURE → PROPOSE p → APPLY (version N+1) → GATE → accept  ──┐
                                               └→ regress → REWIND (version N) → p/2 → repeat
```

1. **MEASURE** on the box (read-only):
   ```bash
   PYTHONPATH=src python tools/winning_ticket.py measure --window-days 90 --extra eval/convene_queries.txt
   ```
   It prints, per face, alive/dead scope words and the sources the activation was measured on. Read the
   dead list — a dead word is either noise (prune) or a phrasing the corpora never exercised (then **add
   the phrasing to the battery first**; a gap in the test set is not a reason to prune).
2. **PROPOSE** (read-only): `… propose --p 0.2` — at most 20% of units, dead only, least specific first.
3. **APPLY**: `… apply --p 0.2` writes `data/ticket/mask.vN+1.json` and makes it current. The live engine
   hot-reloads it (mtime); nothing is restarted, nothing is deleted.
4. **GATE — the discipline that never bends** (SOP-8). All of these must hold with the mask on:
   ```bash
   PYTHONPATH=src python tools/check.py                                      # local suite, MANIFEST whole
   PYTHONPATH=src CONCORDANCE_DATA_DIR=data python tools/benchmarks.py --gate # 0 false positives
   PYTHONPATH=src CONCORDANCE_DATA_DIR=data python tools/live_assay.py
   PYTHONPATH=src CONCORDANCE_DATA_DIR=data python tools/frontdoor.py --gate
   PYTHONPATH=src CONCORDANCE_DATA_DIR=data python tools/recall.py --gate
   ```
   plus the convene benchmark (panel selection and combined reach may not fall). Or let the tool drive it:
   `… run --p 0.2 --gate-cmd "<each command>"` — it applies, gates, and on a failure **rewinds and halves
   p** until p < 0.05 or nothing dead remains, printing one row per round.
5. **ACCEPT** is an operator decision: a passing version is left in force only on an explicit go; otherwise
   `… rewind`. The mask is box-owned data (like `benchmarks.json`) — never deployed as a file; it is
   reproduced by the tool from tracked corpora.
6. **RECORD**: the version's `receipt` (sha-256 over what it masks and its window) and gate lines go in the
   cycle's commit message; `… status` prints them. The chain of versions (`parent`) is the river.
7. **RE-MEASURE** next cycle. A word that fires again in a later window is **unmasked** by the next version
   — the mask is reversible by construction. A regression found in the wild is a rewind, then a battery
   addition, never a hand edit of the mask.

---

## Cadence

| Interval | Practice | Instrument |
|---|---|---|
| **Every deploy** | the mask in force is reported with the gate (`status`) | `tools/winning_ticket.py status` |
| **Monthly** | measure; read the dead list; grow the battery where the corpora were thin | `measure` |
| **Quarterly** | the pruning cycle (this SOP) — the row "prune what bore no fruit" in CONTINUOUS_IMPROVEMENT, made concrete | `run` + the gates |
| **On a new unit kind** | instrument `fires` for it, pin it in `tests/test_ticket.py`, add it here | — |

---

## Invariants

- **A mask, never a deletion.** Every version is kept; `rewind` moves the pointer, removes nothing.
- **Dead only.** A unit that fired in any gate or in traffic in the window is never proposed.
- **0-FP first.** A mask that lets one false claim through is rewound regardless of what it saved.
- **The floor is not pruned.** Verifiers, kernel, receipts, ledger, Scripture, crisis — never units.
- **Measured, dated, reproducible.** Importance comes from the tool over tracked corpora in a stated
  window; no hand-tuned list; the report names the sources and the window.
- **Fail open.** An absent or corrupt mask file masks nothing — the dense keeping is the default.
