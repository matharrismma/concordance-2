# recurring-form attack on OEIS -- computed signatures, many bodies, rarity-weighted

Signatures DERIVED BY COMPUTATION from `data/oeis_cards.jsonl` (exact linear-recurrence
detection over the actual terms -- no keyword matching). Family = sequences satisfying a
linear recurrence of order <=3 (eigenstructure in integers, since the characteristic
root is the growth ratio); null = random sequences from the same sample.

- corpus sample: 1500 sequences with >=12 terms; recurrence family: 127

**The lesson the attack forced.** Naive shared-primitive counting is dominated by generic
features (`all_positive`, `monotonic_inc`) that nearly every sequence has -- Matt's
'short-risk' regime, where a too-rich fabric connects everything. The fix is the apophenia
dial made precise: weight each shared connection by rarity (IDF). Generic sharing
contributes ~0; the RARE shared spine carries the signal.

What makes the family a family (family_rate vs base_rate):

| primitive | family rate | base rate | lift | idf |
|---|---|---|---|---|
| linrec | 1.00 | 0.12 | +0.88 | 2.16 |
| exp_growth | 0.91 | 0.24 | +0.67 | 1.44 |
| order_3 | 0.53 | 0.04 | +0.48 | 3.11 |
| irrational_ratio | 0.61 | 0.19 | +0.42 | 1.64 |
| order_2 | 0.31 | 0.03 | +0.29 | 3.62 |
| integer_ratio | 0.29 | 0.04 | +0.25 | 3.17 |
| strict_inc | 0.73 | 0.54 | +0.19 | 0.61 |
| alternating_parity | 0.24 | 0.05 | +0.19 | 2.98 |

| M (bodies) | family weighted-spine | null weighted-spine | ratio | p(null≥fam) |
|---|---|---|---|---|
| 3 | 10.7 | 2.0 | 5.23 | 0.005 |
| 5 | 16.9 | 4.1 | 4.1 | 0.0 |
| 10 | 25.1 | 8.4 | 2.98 | 0.0025 |
| 20 | 31.2 | 15.6 | 2.0 | 0.0 |
| 40 | 36.0 | 25.1 | 1.43 | 0.015 |

**Verdict (weighted spine, M=10, p=0.0025): CONFIRMED.**
At a practical family size (M=10 — Matt's fabric runs 12–20 nets), a random family
reaches the recurrence family's typical rare-sharing with probability p above: the
recurring form is beyond chance. The ratio is largest at small M and narrows as bodies
grow only because the family has 127 members and large random draws start sharing rare
structure by accident — the absolute gap persists. The signatures were **computed** from
raw terms (exact linear-recurrence detection), not hand-built: the representation problem
attacked on the one modality our corpus lets us compute exactly. Two findings carry
forward: (1) the fascia measure MUST weight connections by rarity — a shared generic
feature is not a recurring form (the apophenia dial, made precise); (2) generalizing the
computed-signature deriver to non-numeric modalities is the standing frontier (FASCIA.md §6).
