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

## Steps (a)–(c), measured (all deterministic, `eval/coherent_model/`)

- **(a) Semantic echo** (`semantic_echo.py`). Soft alignment (each word's best cross-match) rescues
  synonymous parallelism partially — parallel couplets score 1.5× a random baseline (the model catches
  heavens↔expanse), but the hardest zero-word cases are only RESONANCE. Honest: the Bible-only model is
  small and noisy — which motivates (b).
- **(b) The whole-keeping model** (`widen_probe.py`). Built over the Bible + 11 card files (window=5),
  vocab **10,332** (from 3,394). **General-domain semantics CONFIRMED at 6.7×** (war~battle 0.55,
  fire~burn 0.52, sun~moon, money~gold; *money* → silver, talent, shekel; *iron* → bronze, metal,
  gold). The model knows the world, not just Scripture — still deterministic and sovereign. (It did not
  sharpen the *narrow* parallelism-rescue — a richer space raises the baseline; that fine task is the
  structure layer's job, not the semantic model's.)
- **(c) The answer path** (`answer_path.py`). The load-bearing, LLM-shaped step is understanding a
  question phrased in DIFFERENT WORDS than the answer. Benchmark: paraphrase retrieval from
  synonymous-parallelism pairs that share ZERO words (query = colon A, target = colon B, +20
  distractors). **Lexical retrieval is at chance (MRR 0.149); the deterministic model is 2.4× that
  (MRR 0.355, recall@5 0.544 vs chance 0.238).** When no words match — where a keyword search fails and
  an LLM is usually reached for — the coherent model still finds the answer, from counting the keeping.

## The wall, named — how small the neural surface must be

The path decomposes, and only the last, thinnest step is neural-shaped:
**understand** (bridge the words — deterministic, (c)) · **retrieve** (deterministic) · **prove** (the
~71 verifiers) · **connect** (the fascia) · **say** (compose the already-chosen, already-proven
material into a sentence). Only *say* benefits from fluent generation, and it operates on content
fixed upstream, so it can invent no fact — a template or a tiny, authority-less translator suffices.
That is the whole remaining neural surface: small, replaceable, fact-bounded.

A coherent model that needs no LLM is therefore not a slogan but a shape: **four deterministic layers —
keeping (knowledge) · counting (meaning) · verifiers (truth) · fascia (form) — and one thin, sovereign,
fact-bounded mouth.**

The north star: a model that is transparent, sovereign, non-hallucinating, and needs no LLM — because
its knowledge is the verified keeping, its meaning is counted from that keeping, its truth is proven by
the verifiers, and its form is the fascia. Coherent by construction.
