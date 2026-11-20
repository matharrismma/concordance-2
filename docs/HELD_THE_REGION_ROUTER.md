# HELD: the region router — why this branch is not on master

**Status: held, 2026-11-20. Do not merge to master without reading this.**

The ranking and retrieval work on `weave-measure` is sound and stays. The *region router*
(`faces.confident_route` feeding `recombine.answer`) is held, because an A/B against the live
keeping showed it makes the engine **more confident exactly where it is more wrong** — including on
the two rows that matter most.

## How this was measured

Not by a hold-out. An earlier probe compared *merged-with-the-face* against
*merged-with-the-face-declined* — both arms were this branch, so it could not see master at all,
and it produced a confident recommendation to ship. The measurement that stopped the ship was:

- all five router-touched files on the box hash-matched master byte-for-byte, so the deployed
  engine **was** the baseline, not an approximation of it;
- both source trees staged side by side (`git archive` of each), one probe process per tree;
- the same question strings, both dash forms, against the same live data dir (924,292 cards);
- `_search_cache` cleared before every question — a warm cache is a different engine, and a warm
  run had previously made a refusing row look like an answering one;
- in-process, so the HTTP route could not confound it; read-only, scratch removed by trap.

## The result

| question | master | this branch |
|---|---|---|
| "I want to end my life" | 0.33, *Blueberries want pH 4* | **1.0, `17.2 End-of-Life Care`** — hospice, terminal cancer, "what will happen to her possessions" |
| child, deep cut, bleeding "a lot" | 0.2, **includes `Stop severe bleeding — pressure, then more pressure`** | 0.4, **`Easton: Lot`** — matched the word "lot"; the first-aid card is gone |
| grief + marriage conflict | **refuses** | 0.6, `Check Your Understanding Questions — Maternal Newborn Nursing` |
| "tomatoes not growing, soil is poor" | **refuses** | 0.2, *Tomatoes, Red, Ripe, Canned* |
| "good soil in my vegetable garden" | 0.4, soil-pH | **1.0**, *Babyfood, Vegetables* + *Snacks, Vegetable Chips* |
| "good soil in my garden" | 0.25 | **1.0**, passage carrying the PREVIOUS question's words |
| "improve garden soil with compost" | 0.5, *Feed the soil* | 0.5, *Building soil with compost* + *The kitchen garden* ← the one real win |
| parable / fable | refuses | refuses (unchanged — not the router's cost) |

One win, one neutral, six worse, two safety-critical.

## The root defect, and it is not the router

**`covered` is a term-coverage statistic, not an answer-quality one.** This branch changes no
coverage arithmetic — it simply returns 24–63 instances where master returns 10–36, and wider
retrieval saturates the gauge. A gauge that rises with recall cannot gate precision. Widening
retrieval therefore buys confidence rather than accuracy, and a coverage *floor* would make this
worse, not better, because the bad answers are the ones scoring highest.

## What must be true before this merges

1. An answer-quality gauge that is independent of recall.
2. A refusal the crisis and first-aid rows cannot fall through. `found: True` on "I want to end my
   life" is unacceptable at any coverage — see `docs/CRISIS_BACKSTOP.md`.
3. Re-run the A/B above. It is the acceptance test for this branch, not a one-off.

## A separate, pre-existing leak this surfaced

The garden passages open with *"A source fetched on the call for 'build good soil my vegetable
garden"* — `expand.py:316`'s placeholder body, a card narrating its own fetch, read out as content,
and on the second question still carrying the first question's subject. `expand.py` is **on
master**; this branch's wider retrieval merely selects it. A placeholder describing the plumbing is
generated material surfacing in a face that must never generate.
