# Witness overlay review (2026-06-28)

Read-only multi-agent review of the 2.0 witness surface (scripture, Strong's, canon,
theology/witness verifiers, foundation, surface gating). The reviewer assessed the
*mechanism* — not whether any theological position is correct — and flagged anything
touching contested theology as **GATED** for Matt rather than proposing the engine decide.

## Verdict: theologically sound

The witness overlay holds against its own guardrail ("points to Christ, not idol; conduit
not source; the map never launders"):

- **Conduit-not-source is enforced mechanically.** `witness.verify_no_fabricated_answer`
  rejects any sealed record carrying a `final_answer`/`answer` field (Mt 5:37) — "categorize,
  don't answer" as a runtime check, not a slogan.
- **The theology verifier checks structure against cited Scripture; it never interprets.**
  Every check compares a *claimed* value to a rule from a quoted, attributed verse; disputed
  passages and denominational distinctives are explicitly out of scope.
- **Source hierarchy encoded** (Jesus' words primary → Bible → apostles → recognized elders).
- **Scripture is found, not generated** — genuine public-domain WEB (verified live), quoted
  text must match or it's a MISMATCH. **Strong's is genuine lookup** of the openscriptures
  lexicon (G26→ἀγάπη, 36 occurrences; H430→אֱלֹהִים), not paraphrase.
- **Canon layering is honest + concentric** — the undisputed 66 kept strictly separate from
  disputed/deuterocanonical, framed historically, the engine refusing to rule which canon is
  "correct" (show, don't crown). Ethiopian count flagged as genuinely debated, not overstated.
- **Surface gating is defense-in-depth** — witness verifiers/MCP-tools/endpoints all behind
  `witness_surfaced`, lazily imported so `.com` never loads witness code; the shared corpus is
  intentionally shared (Matt's directive).
- **The drift-check is honest about its limits** — returns NEEDS_MANUAL_VERIFICATION rather
  than fabricating a verdict when morphology isn't available.

## Gaps + disposition

| # | Finding | Severity | Disposition |
|---|---------|----------|-------------|
| 1 | Witness `verify_gate_chain_complete` checks `REQUIRED_GATES=(RED,FLOOR,WAY,BROTHERS,GOD)` but the engine emits `RED,FLOOR,PATH,WITNESS,WAIT` — the self-check validates a vocabulary nothing emits | high | **GATED** — the names WAY/BROTHERS/GOD carry Matt's "Four Gates" doctrinal framing. Whether the witness surface keeps the doctrinal names or aligns to the engine's neutral names is Matt's call. (Mechanical fix is one line once the naming is chosen.) |
| 2 | Two WEB stores differ in punctuation (`web.db` vs `bible_en.jsonl`) | medium | **FOLLOW-UP** — both are public-domain WEB (provenance clean); the verifier already normalizes punctuation in `_norm_text`, so impact is mainly display. Pick one canonical edition later. |
| 3 | `theology_doctrine.py` docstring said "KJV / ESV equivalents" (ESV is copyrighted) | low | **FIXED** (2026-06-28) — docstring now states only public-domain KJV (anchors) + WEB (served); no ESV shipped. |
| 4 | `canon.py` intends a single source of truth (`scripture._CANON_BOOKS`) but that symbol is absent, so it uses its embedded mirror | medium | **FOLLOW-UP** — contents of the 66 are uncontested (not an integrity issue); make the source explicit OR document the embedded list as authoritative. Any change to what counts as the core is **GATED**. |
| 5 | `lookup.py` comment claimed zero-padded keys; shipped lexicons are unpadded | low | **FIXED** (2026-06-28) — comment corrected. |
| 6 | `verify_anchors_resolve` checks the `layer` label, not that the ref resolves | low | **FOLLOW-UP** — real resolution lives in the scripture verifier; this self-check's name over-promises. Rename or wire resolution in. |

## Standing guardrail (for future work)
Leave the canon layering's substance as-is. Do **not** add code that ranks or endorses one
canon over another — that would be the engine crowning a contested position. The two GATED
items (gate naming, canon contents) wait for Matt.
