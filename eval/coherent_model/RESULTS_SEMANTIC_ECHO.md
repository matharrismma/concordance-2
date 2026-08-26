# Coherent-model step (a) — semantic echo rescues synonymous parallelism

Two cola of a synonymous parallelism mean one thing in DIFFERENT words, so lexical Jaccard
sees ~0. The deterministic semantic model (PPMI from the keeping) should see them as close.
Tested on 1500 poetic couplets.

- mean LEXICAL echo (Jaccard): **0.028**
- mean SEMANTIC echo (model): **0.213**
- random-cola semantic baseline: 0.141

**Partial rescue (soft alignment).** Parallel couplets score **0.213**
vs a random baseline of 0.141 — a real ~1.5× lift, so the model catches the specific
synonym correspondences (heavens↔expanse) that lexical echo (mean 0.028)
is blind to. But on the 1239 HARDEST couplets (near-zero shared words) it is only
0.165 vs 0.141, p=0.2110 → **RESONANCE** — modest.

**Honest why, and it sets up step (b).** The signal is real but not decisive because the
model here is Bible-ONLY (small vocab, noisy vectors for rarer words) and biblical poetry's
semantic space is cohesive (the random baseline is already high). The fix is not more clever
matching — it is a BIGGER, cleaner model: build over the WHOLE keeping (step b), which should
sharpen synonymy and lower the noise. Semantic echo rescues SYNONYMY (different words, same
sense); small-book cohesion is a job for the structure layer, not more semantics. The steps
compose — (a) shows the direction, (b) supplies the model that makes it bite.
