# recurring-form deriver on SCRIPTURE — computed parallelism, poetry vs narrative

The representation problem attacked on a new modality (Matt: 'A'). The form is Hebrew
PARALLELISM; signatures are COMPUTED from the verse text (colon balance, terse lines,
the antithetic hinge, anaphora, lexical echo) — never keyword-matched. Family = the
poetic books; null = narrative books.

- poetry verses (family): 1837   narrative verses (null): 2290

What distinguishes poetry (family_rate vs narrative_rate):

| primitive | poetry | narrative | lift | idf |
|---|---|---|---|---|
| terse | 0.72 | 0.38 | +0.34 | 0.63 |
| short_lines | 0.61 | 0.31 | +0.30 | 0.82 |
| balanced | 0.59 | 0.39 | +0.20 | 0.73 |
| bicolon | 0.67 | 0.58 | +0.09 | 0.48 |
| antithetic | 0.13 | 0.06 | +0.08 | 2.40 |
| anaphora | 0.05 | 0.03 | +0.02 | 3.23 |
| multicolon | 0.10 | 0.12 | -0.02 | 2.17 |
| lexical_echo | 0.17 | 0.24 | -0.06 | 1.57 |

**The honest lesson.** Parallelism is a WEAK, DISTRIBUTED per-verse signal — a terse
narrative verse looks like a terse poetry verse — so the per-verse recurring-form assay
reads COINCIDENCE. Unlike a linear recurrence (a per-instance binary), Scripture
structure is a POPULATION fact, so the measure must be group-level.

**Parallelism score** (each primitive's poetry-vs-narrative LIFT learned on a train
split, summed per verse, scored on a held-out test split): held-out poetry mean 0.599 vs narrative 0.342 (gap +0.257); permutation p(gap by chance) = 0.0000 → **CONFIRMED**. 82% of held-out poetry verses score above the narrative median.

So the deriver recovers Hebrew parallelism from raw text — the poetry population carries
the computed parallelism structure the narrative population does not — a real second,
non-numeric modality for the fascia measure. The finding that carries forward: for text
the recurring form is statistical, measured on populations, not on single verses. Next:
chiasm (mirror symmetry about a centre), and the cross-domain reach (the same balance
form in music/math).
