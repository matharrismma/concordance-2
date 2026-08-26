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

The tendon holds where the force is real: scriptural and paraphrased questions retrieve
the right material (the semantic expansion bridges 'different words'), out-of-corpus
questions MISS honestly (no fabrication — the load doesn't make it lie), and a cry for
help routes to crisis-first before any retrieval. Where it SLIPS is where to load next —
heal the PATH (better expansion, floor calibration, index coverage), not the instance.
This is the Yijin Jing for the answer path: progressive, measured loading. Bench — not
deployed; the tendon carries public weight only after it carries this.
