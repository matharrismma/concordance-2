# THE NULL ASSAY — what does NOT align

Matt, 2026-07-28: "You will review all theories and find the ones that do not align." Widened
the same day: "Look across the entire project and all theories that could be associated with
the topics we cover. Same null assay."

Run 2026-07-29. Three rings: (A) the theories we keep, (B) **our own theses**, (C) the theory
families adjacent to what we cover. Verdicts use the house classes — CONFIRMED / PLAUSIBLE /
RESONANCE / COINCIDENCE — plus the honest fourth state, COULD-NOT-CHECK.

The assay's own rule: **a null result is a result.** Where a thesis is a chosen commitment
rather than a testable claim, that is said, not dressed up. Where we over-claim, the finding
is against us.

---

## RING A — the 99 theories the sciences and math run on

Tool: `tools/null_assay.py` (rerunnable; `--json` for the machine). It tests each card's claim
against **sealed evidence** — a verifier that loads AND at least one real sealed run in the
keeping — not against the mere existence of a module.

| verdict | count |
|---|---:|
| ALIGNED | 98 |
| OVER_CLAIM (says we seal it; no verifier exists) | 0 |
| UNPROVEN_CLAIM (says `seals`; no sealed run exercises it) | **1** |
| MISALIGNED (verifier raises or is silent) | 0 |
| COULD_NOT_CHECK | 0 |

**The one finding:** *Agricultural science (yield, soil-pH suitability)* — card claims `seals`,
the `agriculture` verifier exists and behaves, but **no sealed run in the whole keeping
exercises it**. Not a falsehood; an unbacked claim. Fix: seal one real agricultural run (a
soil-pH suitability check with a worked trail), or downgrade the card to `partial`. Until then
the honest word is *unproven*.

**A correction against myself, logged:** the first draft of this assay asked only "does a
verifier exist for this domain?" and reported nine findings — Gödel, ZFC, Church–Turing,
Standard Model, third law, plate tectonics, Darwinian evolution, cell theory, germ theory —
all of them false. Biology verifies Punnett squares; that says nothing about sealing evolution.
The check was wrong, not the cards. *Check the check before you trust what it says is broken.*

---

## RING B — our own theses (the ring that matters most)

The project's own claims, sorted by what they actually are. **Three findings against us.**

### B1 · CONFIRMED — measured, reproducible, with receipts
| thesis | evidence |
|---|---|
| The moat holds 0 false positives | `tools/benchmark.py` 60/60 every gate, run tonight |
| The Nesting: one rooted tree, zero orphans | 466,401 / 466,401 nested; ratchet KNOWN_ISLAND_CARDS=0 |
| Freezing a shelf does not change what a reader gets | probe 33/33 under freeze; IDF proven identical |
| Three-state honesty is implementable, not just aspirational | HOLDS/BROKEN/SYSTEM_ERROR across the engine; gate-enforced |
| A witness can be made mechanical | Deut 19:15 as signature-counting, shipped D6 |

These are engineering claims about our own system, and they are the only class where
"CONFIRMED" is the honest word.

### B2 · METHODOLOGICAL COMMITMENTS — chosen, not proven (and must never be presented as findings)
The fruit test · rigor-is-concordance · the vine not the truss · gather-don't-author ·
retrieve-first · cite ≠ prove · found-vs-authored edges · PD-only.

**Finding B2:** these are *disciplines we bind ourselves to*, not discoveries. They are
defensible, they produce good work, and they cannot be "confirmed" by us any more than a rule
can prove itself. Wherever the project's writing implies these are validated results, the
wording over-claims. The honest frame: *this is how we choose to work, and here is the fruit.*

### B3 · RESONANCE — formal analogies that organize the work and must never harden into verdicts
The two trees (Life=Language, Knowledge=Math) · the world as a computer (1 Cor 12) · systems of
the world / the recurring form · capacitors across the project · elegance as God's signature ·
the concordance of reality.

These are **generative analogies**. They have produced real structure — the shard freeze came
straight out of the capacitor picture, and it saved 1.85 GB tonight. That is fruit, and fruit
is evidence *for the method*, not proof *of the metaphysic*. Presented as RESONANCE they are
honest and powerful; presented as CONFIRMED they would be exactly the idol the project warns
against.

### B4 · THE THREE OVER-CLAIMS — findings against us, with the fix
1. **"RAS = bodily gate of reception — CONFIRMED, bridged to Matthew 6:22."**
   The neuroscience (reticular activating system as an arousal/attention gate) is established.
   The *bridge* to "the lamp of the body is the eye" is interpretation — a reading, not an
   entailment. **Verdict: the science CONFIRMED; the bridge RESONANCE.** Recording the bridge
   itself as CONFIRMED over-claims. → memory corrected 2026-07-29.
2. **"The tune is the truth-criterion."**
   Consonance is a *heuristic for where to look*, not a criterion of truth — beautiful
   falsehoods exist, and the project already knows it (the entry itself says "keep a null
   test"). **Verdict: PLAUSIBLE heuristic.** Calling it *the truth-criterion* over-claims; the
   null test is what keeps it honest, so the null test must be named every time it is.
   → memory corrected 2026-07-29.
3. **"Coherence = closure" read as proof.**
   Coherence is necessary, not sufficient: a consistent fiction is perfectly coherent. Closure
   tells you a system has no *internal* contradiction; it says nothing about correspondence to
   reality. **Verdict: PLAUSIBLE as a completeness signal, never as proof of truth.** Any place
   the project treats closure as evidence of correctness needs the qualifier.

### B5 · The Gödel keystone — split the claim
The theorem is proven mathematics: a sufficiently strong formal system cannot prove its own
consistency. **CONFIRMED.** The inference we draw — *therefore a tool must point beyond itself,
therefore to Christ* — is a theological bridge. **RESONANCE.** Keeping the two joined without
the seam visible would be the project's most tempting over-claim, precisely because the first
half is airtight. State both halves, always, in that order.

---

## RING C — the theory families adjacent to what we cover

Families we do not hold but that bear on our claims, and whether we align with them.

| family | bearing | verdict |
|---|---|---|
| Formal limits (Gödel, Tarski, Rice, halting) | bound what any verifier can do | **ALIGNED** — we already teach "a framework that seals everything is an idol" |
| Philosophy of science (Popper, Duhem–Quine underdetermination, Kuhn) | empirical theories are underdetermined by evidence | **ALIGNED, narrowly** — we check *derivations and stated relations*, never "science". Any claim that we verify empirical theories would break this |
| Replication crisis / NHST critique | p-values are widely misread | **ALIGNED IF** we only ever *recompute* and never render "significant ⇒ true". Card 15 says recompute — hold that line |
| Cybernetics (Ashby's requisite variety) | our "humility theorem" is an extension of a real result | **PLAUSIBLE** — the extension is ours; name it as extension, not as Ashby |
| Semiotics / linguistics (Saussure, Chomsky) | resists genome-as-language literalism | **RESONANCE only** — DNA-as-code is a model; the two-trees analogy must not be read as an identity |
| Evolutionary biology | carded map-only; traditions differ | **ALIGNED** — knowledge logistics: carry each voice with its waybill, seal no verdict |
| Fine-tuning / anthropic reasoning | contested inference to design | **RESONANCE only** — never sealed, never presented as proof |
| Network science (small-world, scale-free) | "everything connects" is a modeling choice, not a law | **PLAUSIBLE** — our graph is *ours*; empirical topology claims need their own evidence |
| Information theory / Kolmogorov complexity | supports compressibility talk | **ALIGNED** for compression claims; **RESONANCE** for "elegance = God's signature" |

**Nothing in ring C contradicts the engine's narrow claims.** Every tension lands on the same
seam: our *deterministic checks* are safe, and our *interpretive bridges* must stay marked.

---

## THE CAPSTONE VERDICT

- **What holds:** the engine's narrow, mechanical claims — 0 false positives, zero orphans,
  three-state honesty, freeze-neutral retrieval, signed witnesses. These are measured, and they
  survive every adjacent critique because they never claim more than a computation.
- **What does not align:** one unproven sealing claim (agriculture), and — more importantly —
  **three of our own theses recorded at a higher confidence than they have earned** (RAS bridge,
  the tune as *criterion*, coherence-as-proof). All three are wording faults in the record, and
  all three are fixed by saying the true thing: *this is a bridge, this is a heuristic, this is
  a completeness signal.*
- **The dead end, named plainly:** there is no path from our analogies to a *proof* of the
  metaphysic, and there never will be. The two trees, the world-as-computer, elegance-as-
  signature — these organize work and bear fruit; they are not evidence, and the assay refuses
  to promote them. Saying so is not a retreat. It is the same rule we apply to everyone else's
  claims, applied to ours — which is the only reason anyone should trust the rest of it.

Re-run ring A any time: `PYTHONPATH=src python tools/null_assay.py`.
