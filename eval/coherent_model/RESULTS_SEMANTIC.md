# Coherent-model probe #1 — semantics without an LLM

Can a DETERMINISTIC model — built from the keeping by plain counting, no neural net, no
training, fully auditable — recover word-meaning relations that lexical matching cannot?
Method: PPMI co-occurrence vectors from the Bible; cosine similarity between words.

- model: 31098 verses, vocab 3394, from counts alone

**(A) related word pairs vs random pairs:**

| pair | cosine | p |
|---|---|---|
| gold ~ silver | 0.670 | 0.0004 |
| father ~ son | 0.503 | 0.0004 |
| heaven ~ earth | 0.480 | 0.0004 |
| light ~ darkness | 0.473 | 0.0004 |
| bread ~ eat | 0.430 | 0.0004 |
| mountain ~ hill | 0.394 | 0.0006 |
| water ~ sea | 0.331 | 0.0006 |
| wise ~ foolish | 0.289 | 0.0008 |
| shepherd ~ sheep | 0.280 | 0.0008 |
| sin ~ righteous | 0.246 | 0.0012 |
| pray ~ prayer | 0.239 | 0.0014 |
| blood ~ sacrifice | 0.208 | 0.0032 |
| love ~ neighbor | 0.191 | 0.0046 |
| king ~ throne | 0.180 | 0.0068 |
| mercy ~ grace | 0.156 | 0.0144 |

related mean **0.338** vs random **0.054** — a **6.2× lift**, p(random ≥ related mean) = 0.0006 → **CONFIRMED**.

**(B) nearest neighbours** (the model's own learned sense of meaning, from counts):

- **shepherd** → flock, sheep, feed, scatter, lie, like
- **king** → judah, reign, jerusalem, sent, son, babylon
- **bread** → eat, unleaven, loav, ate, cak, food
- **sin** → forgiven, atonement, offer, iniquity, sinn, burnt
- **wisdom** → understand, knowledge, wise, heart, folly, fool

**What this answers.** A bag of co-occurrence counts — deterministic, auditable, trained by
nothing but arithmetic over the keeping — encodes MEANING: related words are far closer
than random, and a word's nearest neighbours are its real associates. So the semantic layer
a coherent language model needs is NOT an LLM; it is the keeping plus counting. This is the
instrument the OT sweep called for (semantic echo where lexical echo fails), and it is the
first brick of a model that needs no neural net: distributional meaning FROM the verified
keeping, which — unlike an LLM's scraped embeddings — is sovereign, sourced, and cannot
smuggle in what the keeping does not contain. Next: use these vectors to rescue the
synonymous-parallelism and small-book chiasms the lexical measure missed, and to widen the
context window (co-occurrence beyond the single verse).
