# recurring-form probe -- results

`fabric_routability.py` lifted from copper to form. Real family = {watch, PCB, engine}
with hand-built, source-cited signatures; null = random families of the same signature
sizes drawn from the same universe. The universe grows across rows (the apophenia dial).

| universe | real jumpers | real spine | null jumpers | null spine | p(j≤real) | p(spine≥real) | verdict |
|---|---|---|---|---|---|---|---|
| 0+base (66) | 0 | 9 | 0.0 | 12.45 | 1.0 | 0.9808 | COINCIDENCE |
| 60+base (126) | 0 | 9 | 0.01 | 7.22 | 0.995 | 0.2628 | COINCIDENCE |
| 200+base (266) | 0 | 9 | 0.2 | 3.59 | 0.8228 | 0.003 | CONFIRMED |
| 600+base (666) | 0 | 9 | 0.86 | 1.48 | 0.3488 | 0.0 | CONFIRMED |
| 2000+base (2066) | 0 | 9 | 1.54 | 0.5 | 0.0628 | 0.0 | CONFIRMED |

**Named null** (grocery + song + tax, honest signatures): jumpers=2, shared_spine=0 — three unrelated systems do not become one form.

**Reading.** The SPINE is the recurring-form measure — how much form the family shares
for free (real = 9 shared primitives). `p(spine≥real)` is the fraction of random
families that share a spine as big; at a realistically sparse universe (≥200 distinct
structural primitives) it is 0.003 → 0, so the shared FORM is beyond chance. The
jumper-count (components−1) only CORROBORATES here: it saturates at 0 for a 3-body
family (any transitive sharing collapses it), so it separates from the null only at an
implausibly huge universe. That is a real finding, not a failure: the jumper axis
sharpens with FAMILY SIZE — Matt's fabric routes 12–20 nets, not 3 — so the next probe
should gather MANY instances of a form, not three.

**Apophenia dial.** Top row (tiny dense universe) → random families also connect and
share a bigger spine than real → COINCIDENCE: the instrument correctly refuses to call a
form when everything trivially connects (Matt's 'short-risk' regime). As the universe
sparsens the real form separates cleanly. The verdict is therefore honest about WHERE it
can and cannot read.

**Positive control.** grocery + song + tax (unrelated) → spine 0, jumpers 2. The measure
sees unrelated systems as unrelated.

**Limit.** This proves the *measure* discriminates on hand-built signatures. It does NOT
yet derive signatures automatically — that (the representation problem, FASCIA.md §6) is
the real frontier. This is the bench proof that the instrument reads true before we
trust any verdict it gives.
