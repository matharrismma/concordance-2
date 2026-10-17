# HARVEST — every strong aspect, mapped and ranked

Source: the 2026-08-25 review of the **Lighthouse** engine (the Aug-5 predecessor of this repo) and
the **language-side handoff** (`nh-handoff.zip`). Matt: *"We want to take every strong aspect."*

**Method (the discipline that keeps this from becoming sprawl).** Measure and map first, cohere after.
Take every strong aspect **into the candidate set** — then narrow: a need **3+ proving grounds** produce
is *structural* (cohere now); a need **one** produces is *parked* until another domain asks. The
red-team's own verdict governs the whole exercise:

> *"The engine is real and the doctrine is right. The product does not yet exist, and the sprawl is the
> thing most likely to keep it from existing."*

This file is the candidate set. `eval/proving/*/MAP.md` files narrow it by measurement.

---

## 1. HAVE — survived the rewrite; this is the floor, do not re-port

| Strong aspect | Status in concordance-2 |
|---|---|
| **66 computational verifiers** (physics … scripture) | parity with Lighthouse's 67 — the load-bearing math core is here |
| Multi-vocabulary verdicts: CONFIRMED / MISMATCH / NOT_APPLICABLE + HOLDS / BROKEN / **INCOMPLETE** | present; INCOMPLETE first-class; already touches `boundary` / `range` |
| SHA-256 ledger chain + Ed25519 seal + `/s/<hash>` citable receipt (BROKEN as citable as HOLDS) | present and **live** (the `/audit` tool uses it) |
| `check` + `find_verifier` single-door consolidation; strict oracle/verifier separation | present |
| LoRa / mesh offline distribution | `lighthouse_node.py`, `mesh.py`, `meshtastic_bridge.py` |
| Grid + archetypes | `grid.py`, `grid_atlas.py`, `archetypes.py` |
| `discern` contract — kind · propose/verify · crisis-first · lens/cloud | present (extended 2026-08) |
| airlock + steward + wants growth loop | `airlock.py`, `steward.py`, `wants.py` |
| FPR "trust-floor" benchmark concept (0 sealed falsehoods) | present as the **60-case** derivation-moat set |

## 2. PARTIAL — thin here; strengthen from Lighthouse

- **Extraction: 12 families (`audit.py`) vs Lighthouse's 92 `@_rule` in `agent/dispatch.py`.** The single
  biggest gap. The contract to adopt: `(rule_id, compiled_pattern, domain, extractor_fn)`, first-match
  wins, `confidence=1.0`, *"every rule a deterministic regex — runs on a microSD with zero network."*
- **The narrowing engine** — the un-copyable moat. Lighthouse `api/narrowing.py`: **NARROW → FINISH →
  VERIFY** with a **62-eliminator registry** (*"pure deterministic predicates from a fixed registry, never
  an LLM judgment"*), candidate space `{range,lo,hi}` or `{set,values}`, emits the elimination trail +
  a tiny residual. `candidates.py` here is lighter (no eliminator registry).
- **Self-growing rules** — `runtime_rules.jsonl` (operator-promoted, `confidence=0.95`) + `rule_extractor.py`
  (mine oracle-confirmed misses → propose regexes; promotion manual). Lets extraction grow without code
  edits. Absent here.
- **Verdict vocabulary breadth** — add `OUT_OF_SCOPE`, `UNCHECKABLE`, first-class `range`/**`NORM`**, and
  from the fighting doc the **authority-class** qualifier (`invariant/doctrine/default/style_preference/
  fighter_variable/evidence_rule`) and the **ruleset-context** parameter (same claim, different verdict,
  must name the ruleset — GAAP vs IFRS, gi vs nogi, Region 2 vs 1/3; refuse to answer without it).
- **1,147 pre-verified domain packets** (`data/packets/*.jsonl`, 51 domains) + the **307-invariant
  catalog** across the verifiers — absent here (this is data, materialize/port).

## 3. MISSING — port from Lighthouse

- **The apophatic `ask` engine** — Lighthouse `ask.py` seed-bank: `AskResult{survivors[], eliminated[],
  new_seed_id}`, cataphatic fruit-scoring + apophatic elimination passes; *"if nothing survives, the
  question becomes a new seed."* concordance-2's `ask.py` is only `is_crisis`. This is the engine's
  identity made executable.
- **Polymathic layer** — `poly_agent.py`, `triangulate_claim`, `PolymathicRecord` (3+ domains sharing a
  scaffold axis = the polymathic pattern).

## 4. NEW DESIGN — build from the handoff (in neither repo yet)

- **The language side.** `segment.py` (span-preserving sentence/clause split) → **F1–F10** rule families
  → coverage report with **residue + preservation %** and the verdict quartet **HOLDS / BROKEN /
  INCOMPLETE(reason) / UNCHECKABLE(reason)**. Prior-art borrows are precise: VeriScore's verifiability
  definition *("a single event or state with all necessary modifiers")*; MinIE's **modifiers-as-
  annotations**; Claimify's **stop-on-ambiguity = INCOMPLETE**; RARR's **preservation** metric; ClausIE's
  synthetic-appositive split. The two strongest fabrication signals get first-class kinds:
  **LAUNDERED** ("studies show" — flagged HIGH, never filtered) and **SUPERLATIVE** ("first/only/largest").
  Doctrine: *UNCHECKABLE* = no truth value (opinion/advice); *INCOMPLETE* = has one, unresolved + what
  would resolve it.
- **The axis dialectic.** `positions` (a ladder) · `sides` (where thought divides) · **`before`** (prevailing
  / was-before / displaced-by / still-held-by — dated; *"older is not truer any more than prevailing is"*) ·
  **`voices`** (2–3 named minds in tension, oldest-first, each a PD `passage` card that **outranks** a
  copyright-era `position-card`; *"a voice with no name is laundered authority"*).
- **The proving-ground + overlay/HEX method** + a **loop runner** (reference · oscillators · comparator ·
  tolerance `sealed_falsehoods==0 & false_BROKEN==0` · corrector=airlock · divider=CURVE · oven=steward).
  The overlay is the governance rule itself. HEX: six domains as a hexagon — vertices=domains,
  edges=pairwise-shared capabilities, **center=the 6/6 needs = the kernel; cohere from the center out.**
- **Workstreams D–H** (teach-while-answering · witnesses · reach-without-a-feed · paths · portfolios).
  Red-team ranking to honor: **A–C are the product, E is the corpus, F–H are the *next* product — do not
  build all eight at once.**

## 5. The doctrine to carry (cross-cutting — appears in 3+ sources)

- **No verdict is generated.** The oracle may *propose* at `authority=quarantined`; only a rule + witness
  upgrades it. (Change site copy from "nothing is generated" to "no verdict is generated.")
- **Extend, never rebuild.** **Every atom is a span of the input** — nothing rewritten or paraphrased.
- **False-BROKEN = 0 is the one red number.** A wrong BROKEN is a release blocker; an INCOMPLETE is always
  acceptable. (Asymmetric error.)
- **Modifiers travel** — an atom that loses a modifier that would change its verdict does not emit. (The
  correctness condition, promoted from a refinement.)
- **"Brought because …"** — every witness, voice, recommendation, placement carries its reason or does not
  render.
- **Determinism (same input → same hash → same witnesses)** is the proof that retrieval/verdict is
  rule-based, not generated.
- **Authority tiering everywhere** — canon > commentary > cards > quarantined; passage > position-card;
  expert 1/2/3.
- **The measurable/subjective split is the core lesson** — it runs *inside a single sentence* (a legal
  holding vs who really invented it; "recapitulation returns to the tonic"). The report splits them and
  never speaks in the witnesses' place.
- **No feed.** Reach = a sealed count of people taught, not people watching. Rank by what was checked,
  linked, and stood behind — never by who looked.

## 6. Ranking — cohere the center, park the points (overlay applied)

**Cohere first (cross-cutting / 3+ domains):**
1. `segment.py` + F3/F4/F8/F9 flags (superlative, laundered, hedge, opinion — no resolver, visible day one)
2. modifiers-travel / split-atoms — build into the emitter from day one (the correctness condition)
3. the narrowing engine + 62-eliminator registry
4. verdict-vocab additions — `range`/`NORM`/authority-class/ruleset-context
5. the sealed coverage report (numeric atoms + language atoms + residue + preservation)

**Park (one domain's need, until another asks):** artifact parsers, registry-verified-expert lookup, the
axis-dialectic *corpus* (a reading project — "budget a person, not a sprint"), self-growing runtime rules,
the apophatic `ask` engine, workstreams F–H.

### Narrowed by measurement (adjust at the end, not before)

Proving ground **01 AM radio** has been run against concordance-2 (`eval/proving/am-radio/MAP.md`).
Measured result: 0/5 benchmark claims checkable (no RF verifier, no radio rules), 0 atoms on the language
fixture, and **D6 already holds** (no devotional voice on a factual paragraph — a HAVE the predecessor
lacked). This adjusts the ranking above:

- **Confirmed cohere-first** (a real domain needed each): ① segment + flags, ② modifiers-travel, ④ the
  `range` verdict + kept-table facts, ⑤ the coverage report — **plus** the **domain-verifier + dispatch-rule
  pattern** (`verifiers/radio.py` and its rules; the general form of the 12→N extraction gap).
- **Down-ranked, awaiting a 2nd domain:** ③ **the narrowing engine** — AM radio is direct verification and
  never invoked it. One domain has not made it structural; cohere it when bookkeeping/TCP-IP (candidate
  fields) confirm it.

The next proving grounds (02 bookkeeping → the inference atom + document-level identity; 06 fighting →
authority-class + ruleset-context + evidence floor) will keep narrowing this. Nothing coheres on one
domain's vote.

## 7. The candidate set + the proving grounds that narrow it

Everything in §§2–4 is committed to the candidate set. It is narrowed, by measurement not taste, by the
proving grounds — each a fully-quantified domain run end-to-end, producing **List A** (features it never
touched → suspects, park) and **List B** (what it *needed* that was missing → the backlog it produced):

- **01 AM radio** — RF formulas, tables, contested dates in true/false superlatives (the reference)
- **02 double-entry bookkeeping** — document-level identities; the **inference atom** (premise vs conclusion)
- **03 four-stroke engine** — the **range** verdict; measurable-inside-judged; registry-verified expert
- **04 TCP/IP** — the **citation resolver** vs numbered docs; **layer-aware** verdict; a `before` in progress
- **05 sonata form** — the inverse fixture (mostly subjective); the **`NORM`** qualifier; voices under load
- **06 fighting** — **authority-class** + **ruleset-context** verdicts; the **evidence floor** on a judged gate;
  the oven rule (a steward cannot seal their own witness); the candidate-finish rule

The kernel that survives all six is the working tool. Cohere then.
