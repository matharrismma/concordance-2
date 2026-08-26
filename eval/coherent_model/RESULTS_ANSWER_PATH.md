# Coherent-model step (c) — the answer path, and the NLU gap it closes

The path: question → UNDERSTAND (bridge the asker's words to the keeping's words) → RETRIEVE
→ prove/connect → say. The LLM-shaped step is the first. Benchmark: paraphrase retrieval
from synonymous-parallelism pairs (query = colon A, target = colon B, near-zero shared
words) — rank the true target against 20 distractors, lexical vs the model's semantic
alignment. 800 pairs.

| ranker | MRR | recall@1 | recall@5 |
|---|---|---|---|
| chance | 0.174 | 0.048 | 0.238 |
| **lexical** (keyword search) | 0.149 | 0.033 | 0.191 |
| **semantic** (coherent model) | **0.355** | **0.181** | **0.544** |

**Semantic MRR is 2.4× the lexical MRR.** When the question and the answer
use different words — the case a keyword search fails and an LLM is usually reached for — the
deterministic model retrieves the right answer far more often, from counting the keeping
alone. The NLU step of the answer path needs no LLM.

## Where the wall is (how small the neural surface must be)

The answer path decomposes, and only the last, thinnest step is neural-shaped:
- **understand** (bridge the words) — DETERMINISTIC, measured here (semantic retrieval).
- **retrieve** — DETERMINISTIC (search the keeping).
- **prove** — DETERMINISTIC (the ~71 verifiers).
- **connect** — DETERMINISTIC (the fascia / concordance graph).
- **say** — compose the retrieved, proven, connected material into a sentence. This is the
  only step where fluent generation helps — and it operates on material already chosen and
  verified, so a template or a tiny authority-less translator suffices; it can invent no
  fact, because the facts are fixed upstream. That is the whole remaining neural surface,
  and it is small, replaceable, and holds no authority.

So across (a)→(c): meaning is countable (probe #1, 6.7×), a query in other words still finds
its answer (here), and the only irreducibly-neural step is surface phrasing over
already-decided content. A coherent model that needs no LLM is not a slogan — it is four
deterministic layers (keeping · counting · verifiers · fascia) and one thin, sovereign,
fact-bounded mouth.
