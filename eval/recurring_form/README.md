# recurring-form probe — the fascia measure on the bench

The connective-domain measure from [`docs/FASCIA.md`](../../docs/FASCIA.md): `fabric_routability.py`
(Matt's Programmable Fabric routability sim) lifted from copper to **form**. It asks whether a family
of systems is *one recurring form* — measured against a random null — the way the fabric asks whether
a net's pads route with few jumpers under placement-locality.

- **`probe.py`** — run it: `python eval/recurring_form/probe.py`. Pure stdlib, seeded, no network.
  Encodes hand-built, source-cited signatures for `{watch, PCB, engine}` (Matt's three design
  bibles) plus a null of unrelated systems, and measures the shared **spine** and the **jumpers to
  one form** against 5000 random families per universe size (the apophenia dial).
- **`RESULTS.md`** — regenerated on each run.

**Finding (first probe):** the three architectures share a free spine of 9 form primitives — one
connected form — beyond chance (p ≤ 0.003) at any realistic sparsity, while unrelated systems
(grocery/song/tax) sit at the floor (spine 0). The measure discriminates. It does **not** yet derive
signatures automatically — that is the representation problem (FASCIA.md §6), the real frontier.

Bench experiment, not wired to production. Credit for the union-find + jumpers-as-components−1:
Matt's `fabric_routability.py`.
