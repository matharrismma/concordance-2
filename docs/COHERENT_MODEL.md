# THE COHERENT LANGUAGE MODEL — meaning without an LLM

Matt, 2026-08-26: *"what about a Small language model or developing our coherent language model to the
point we do not need an LLM."* → *"go right to probing."*

## The thesis, and why it's within reach

An LLM gives three things; we already have a *better* version of the biggest, and can build the rest
from the keeping with no neural net:

1. **Knowledge + reasoning** — already ours and deterministic: the verified keeping + the ~71 verifiers
   *prove* rather than predict. No LLM in discern→verify→connect. (An LLM hallucinates here; we can't.)
2. **Structure / meaning-as-form** — computed deterministically by the fascia line (recurring form,
   parallelism, chiasm, the concordance graph). See `docs/FASCIA.md`.
3. **Language surface** — the only thing an LLM does that we didn't: word MEANING (semantics) and
   fluent phrasing. This is the shrinking frontier — and probe #1 shows the semantic half is countable.

The model is not neural weights; it is **the keeping (knowledge) + counting (meaning) + verifiers
(truth) + structure (form)**, one coherent whole (see `docs/ARCHITECTURE_ONE_BODY.md` — one body, no
runtime agent swarm). Any neural component is a shrinking, authority-less translator, never the truth.

## Probe #1 — semantics without an LLM (CONFIRMED)

`eval/coherent_model/semantic_probe.py`. A DETERMINISTIC distributional model built from
`data/bible_en.jsonl` by plain counting — PPMI co-occurrence vectors, no neural net, no training, fully
auditable — recovers word MEANING:

- **Related word pairs score 6.2× above random** (mean 0.338 vs 0.054, p=0.0006): gold~silver 0.67,
  father~son 0.50, heaven~earth 0.48, light~darkness 0.47, sin~righteous, shepherd~sheep — all
  significant.
- **Nearest neighbours are real senses:** shepherd → flock, sheep, feed, scatter; king → judah, reign,
  jerusalem, babylon; sin → forgiven, atonement, iniquity, burnt; wisdom → understand, knowledge,
  folly, fool.

So the semantic layer needs no LLM — only the keeping and arithmetic. And because it is built ONLY
from the verified keeping, it is sovereign and sourced: unlike scraped embeddings, it cannot encode
what the keeping does not contain. This is also the instrument the OT chiasm sweep called for —
*semantic* echo where *lexical* echo fails (synonymous parallelism, small cohesive books).

## Where this goes

- **Rescue the semantic cases** the lexical measure missed (Jonah's synonymous panels, Ruth) with these
  vectors — semantic echo, not lexical.
- **Widen the context** beyond the single verse (windowed co-occurrence), and build the model over the
  whole keeping, not just the Bible.
- **Compose the layers** into the answer path: keeping (retrieve) → semantic vectors (understand the
  ask despite different words) → verifiers (prove) → structure (connect) → a template/tiny translator
  (say it). Measure, at each step, how much is deterministic and how small any neural surface must be.

The north star: a model that is transparent, sovereign, non-hallucinating, and needs no LLM — because
its knowledge is the verified keeping, its meaning is counted from that keeping, its truth is proven by
the verifiers, and its form is the fascia. Coherent by construction.
