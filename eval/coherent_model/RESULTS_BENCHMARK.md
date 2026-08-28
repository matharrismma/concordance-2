# Answer-path benchmark — the deploy gate

A stable, hundreds-of-item graded set (crisis · honest-miss · retrieval) so the answer
path is tuned on real numbers, not 12 questions. Deploy requires: crisis 100%, honest-miss
≥80%, retrieval recall@5 ≥60%.

- indexed 88099 docs

| set | size | result | bar |
|---|---|---|---|
| CRISIS (route to crisis-first) | 25 | **44%** | 100% |
| HONEST-MISS (out-of-corpus) | 25 | **16%** | ≥80% |
| RETRIEVE recall@1 | 150 | 8% | — |
| RETRIEVE recall@5 | 150 | **16%** | ≥60% |

**Deploy gate: NOT YET.** One or more bars unmet — heal the path to the bar before deploying (crisis is non-negotiable; a miss must not fabricate; retrieval must surface real content).

This is the honest gate the 12-question harness could not give: a stable measure that says
whether the answer path is safe and useful enough to deploy. Build out to the bars, then
deploy — not before.
