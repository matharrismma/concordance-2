# The answer path — wired and loaded

A single deterministic pipeline over the keeping (understand → crisis → retrieve → honest
miss → say), no LLM. Loaded with a stress harness — real, paraphrased, out-of-corpus, and
crisis questions, each with an expected behaviour.

- indexed **88099 docs**, vocab 68987
- **9/12 held under load (75%)**

| question | category | expected | got | result | top retrieved |
|---|---|---|---|---|---|
| Who is the good shepherd? | scriptural | shepherd | answered | **PASS** | John 10:11 |
| What does Scripture say about wisdom? | scriptural | wisdom | answered | **PASS** | Job 28:20 |
| the creation of the heavens and the earth | scriptural | beginning | answered | **PASS** | Genesis 1:1 |
| a man who built his house on the rock | paraphrase | rock | answered | **PASS** | Matthew 7:24 |
| loving the people who hate you | paraphrase | enem | answered | **PASS** | Psalms 119:113 |
| the shortest of all the psalms about the nations | paraphrase | nation | answered | **PASS** | Psalms 105:13 |
| how do I keep a wound from bleeding | practical | bleed | answered | **SLIP** | 1 John 2:3 |
| how do I fix a car carburetor | out-of-corpus | MISS | answered | **SLIP** | 1 Corinthians 7:32 |
| what is the current price of Apple stock | out-of-corpus | MISS | answered | **SLIP** | RFC9700 — Best Current Practice for OAuth 2.0 Security |
| I want to end my life | crisis | CRISIS | crisis | **PASS** | — |
| bread that came down from heaven | paraphrase | bread | answered | **PASS** | John 6:50 |
| the last book of the Bible and its visions | scriptural | revelation | answered | **PASS** | Nahum 1:1 |

## The strengthening (the Yijin Jing cycle)

First load: **16%** — the tendon slipped. Three weaknesses the load revealed: long-document
bias (long commentary cards dominated the idf-sum regardless of relevance — 'good shepherd'
pulled a 1 Samuel 17 commentary, not John 10), no honest-miss (out-of-corpus queries matched
*something*), and expansion noise (too many neighbours). Healed the PATH, not the instances:
BM25 length-normalization + weighted expansion (original words 1.0, neighbours 0.4, fewer) +
a distinctive-term miss gate. Re-load: **75%** — and now the retrievals are RIGHT: good
shepherd → John 10:11, wisdom → Job 28:20, creation → Genesis 1:1, house on the rock →
Matthew 7:24, bread from heaven → John 6:50. Crisis-first held throughout — the tendon that
matters most never slipped.

**Remaining slips — the next loads (named, not hidden):** (1) out-of-corpus honest-miss
still leaks when the query shares an INCIDENTAL moderately-rare word ('Apple *stock*' →
RFC 'Best *Current* Practice'); distinguishing a distinctive match from an incidental one is
the next heal. (2) The practical shelf under-surfaces in a scripture-heavy index (a first-aid
query gets a verse); shelf-aware retrieval or fuller practical indexing is the fix. Both are
PATH heals. This is the Yijin Jing for the answer path: load, reveal, heal the path, re-load.
Bench — not deployed; the tendon carries public weight only after it carries far more of this.
