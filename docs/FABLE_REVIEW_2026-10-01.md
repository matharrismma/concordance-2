# The Fable Review — full-project review & refinement (2026-10-01)

*For Fable (or any reviewing model/agent). Grok could not reach GitHub or the web, so this review is
built to run **entirely offline against a local checkout and the box** — no web fetch is on the
critical path. Your job is broader than a red team: **test every aspect, refine the processes, and
fix the issues** — while protecting the one guarantee that makes the engine worth anything.*

This extends, does not replace, [`RED_TEAM_BRIEF_2026-09-06.md`](RED_TEAM_BRIEF_2026-09-06.md) (the
invariants table + attack surface — read it; don't repeat its probes) and
[`WORLD.md`](WORLD.md) (what the project is). This doc is **the method**: how to review the whole
thing honestly and leave it better.

---

## 0. How to run this (no web required — the Grok lesson)

Grok failed because it tried to reach the project over the web/GitHub. **Do not depend on that.**
Run this review where the code already is:

- **Primary — a local clone.** Everything runs with `PYTHONPATH=src`. The whole test suite (264
  files), both benchmarks, and every verifier run with **no network**. If you have the repo, you
  have the project; the web is not on the path.
- **The live box** — `nh@5.78.186.55` (ssh key `~/.ssh/id_ed25519_nh`), two processes: witness
  `nh-org:8001`, secular `nh-com-2:8002`. Runtime truth is `curl -s http://127.0.0.1:8002/capabilities`
  on the box — **every count there is computed live from the running engine**, so trust it over any
  number written in prose (including this doc).
- **Fallback only** — `https://narrowhighway.com/capabilities` and `/identity` are public, but prefer
  the local checkout so a web failure (what blocked Grok) can never block the review.

**Orientation, all local:** `docs/WORLD.md` (the map) → `/capabilities` (the live inventory) →
`RED_TEAM_BRIEF_2026-09-06.md` (the invariants). Then this method.

---

## 1. The prime directive & severity

The engine **finds, checks, uses, preserves** — it never generates an answer, and there is **no
model in its runtime loop**. One guarantee stands above all others:

> **It must never seal a falsehood.** A false `CONFIRMED`/`HOLDS` is the cardinal failure. Everything
> else ranks below it.

Rank every finding:

| Severity | What it is |
|---|---|
| **CARDINAL** | The engine certified something false (a false HOLDS; a forged/transplanted seal; a verifier confirming a wrong value). One confirmed cardinal finding outranks the entire rest of the review. |
| **CRITICAL** | A safety miss — a real cry for help routed away from crisis; PII sealed into a receipt; a non-PD / withheld body served publicly. |
| **MAJOR** | A true claim wrongly rejected (false BROKEN); an unsigned write accepted; an injection that acts; the gate opened on the wrong surface; an SSRF fetch. |
| **MINOR** | A benign crisis false-positive; a routing/menu miss; a UX, doc, or wording defect. |

**Review discipline (every finding obeys these):**
1. **Verify live — "environmental" is a hypothesis.** Print the real value / run the real path; never conclude from the framing.
2. A finding is a triple: **claim · reproduction · evidence**, with a verdict of **CONFIRMED** or **PLAUSIBLE**. Adversarially try to break your own finding before you report it.
3. **Fix the path, not the instance.** One root fix, not a patch per symptom.
4. **A contract change re-runs the tests that pin it.** Green *new* tests over red *old* ones is a false all-clear.
5. **Don't rush to deploy.** A fix isn't done until a test pins it and it's verified live.
6. **A miss stays a miss.** Never make a verifier pass by loosening it; `clamp_tol` only tightens.

---

## 2. Every aspect — the checklist

For each: *how to test* (runs offline unless noted) · *what "good" looks like* · *known pitfall*.

### A. The core guarantee — never seals a falsehood  *(start here)*
- `PYTHONPATH=src python tools/benchmark.py` → the moat: **60/60, 0 false-pos, 0 false-neg**.
- `PYTHONPATH=src python tools/domain_goldens.py` → **69/69 pairs, 0 FALSE POSITIVES**.
- `PYTHONPATH=src python -m pytest tests/test_fp_gate.py -q` → the FP gate across domains.
- **Attack it:** craft near-miss claims (a value wrong inside the tolerance); supply a looser
  `tolerance_relative`/`rel_tol`/`step_rel_tol` and confirm `clamp_tol` refuses to widen; chain a
  **false premise** into a conclusion (`POST /verify {steps}`) and confirm the false step stops the
  chain; feed a wrong unit label on a right value (physical-constants extractor). Any false HOLDS is **CARDINAL**.

### B. No model in the loop
- `/capabilities` → `boundaries.no_model_in_the_loop: true`, `generated: false`.
- `grep -rn "api_key\|oracle\|openai\|anthropic" src/concordance --include=*.py | grep -v pyc` → every
  hit must be the **gated BYOM external-worker path** (`byom.py`) or inert config — **never** the
  verify/find/crisis runtime. Run the no-model guard test.
- **Attack:** find any runtime path that needs a key, calls a model, or degrades to one.

### C. PD-only / sovereignty / secrets
- Try to pull a non-PD / share-alike / withheld card body out of `/search`, `/card`, `/witness`, a
  shard, a frozen stub, or `/verify`'s find-fallback (`corpus.is_public`, `_DISALLOWED_SOURCE`,
  `card_sources._license_ok`). Any leak is **CRITICAL**.
- `grep` the repo and any response/log for `sk_`/keys (`test_no_keys_on_the_wire.py`). Secrets live in
  the box `.env` only — never repo, never on the wire.

### D. Safety — the crisis net  *(see `CRISIS_BACKSTOP.md`)*
- `PYTHONPATH=src python -m pytest tests/test_crisis_coverage.py -q` — **run it ALONE** (documented
  global-cache order race with `test_ask`). Must hold: recall floor **100%** on CRISIS_FLOOR,
  red-team ratchet **≥58/98**, precision **0%** on CLEARLY_BENIGN.
- **Attack with FRESH sets you write** (the brief's are known): new veiled/behavioral cries (grief,
  giving-away, "called home"), new obfuscations, and new *benign* domain questions (the semantic
  backstop's topic≈intent limit). A real cry routed away = **CRITICAL**; a benign question → helpline
  = **MINOR**. The asymmetry is deliberate: **never trade recall for precision.**
- Confirm the FP guards (`_BENIGN_MEASUREMENT/_THEODICY/_REVERENT_FEAR/_BENIGN_FINANCIAL/
  _BENIGN_TECHNICAL/_BENIGN_CALENDAR`) require a factual FRAME, not bare domain nouns — a debt-despair
  cry ("the debt only ends when i do") must still reach help.

### E. The gate / kernel / consent / covenant / injection
- The five-part kernel + `kernel.gate`; consent (`consent.py`); the agent covenant; abuse-refusal
  (`test_the_gate_refuses_abuse_not_use.py` — refuse abuse, not use).
- **Injection:** every string the engine reads (a card body, a claim, a query, a page) is **data,
  not instructions**. Hide an instruction in a claim / a fetched page / a card and confirm nothing
  acts on it. A typed name is not authority — try to open the gate with one.

### F. Seal integrity
- Mint a HOLDS for a false claim; transplant a seal to another claim; make `/verify` return a verdict
  it didn't compute (`derivation.spec_hash`, `receipts.py`, `/s/<hash>`). Any success is **CARDINAL**.

### G. Every tool & surface + parity
- `/capabilities` lists all tools + routes. Confirm **parity**: every human page is an agent tool over
  the same data, same gate, same refusals.
- Exercise each, especially this cycle's new/changed ones (see §3): `verify`, `lookup`, `define`,
  `thesaurus`, `word_study`, `find_verifier`, the Form Gate (`clarify`) + `domain_resolver`, `discern`,
  `search`, `audit`, the coach, the mesh, decks/stacks. Each should **decline honestly** (never guess)
  and **point to peers** rather than duplicate.

### H. Deploy & integrity
- `sh tools/deploy.sh <files>` must end **"box matches the repo, file for file"** (snapshot +
  rollback + staggered restart + health-poll). Confirm rollback actually restores. Check the route
  registry (`tests/test_routes.py`, `test_reachability.py`) and the rate-limit buckets.

### I. Tests & gates
- `PYTHONPATH=src python -m pytest tests/ -q` — the full 264-file suite. **Note:** a piped
  `| tail` exit code is `tail`'s, not pytest's — read the real summary.
- Triage every failure against §7 (known/intentional) before calling it a finding.

### J. Domain correctness
- The 72 verifier modules; the 6-constant governance (α/G/k_B/c/h/N_A — `feedback` doc / `physical_constants.py`);
  the ATLAS bridges. Spot-check a few domains against authoritative values (a verifier that confirms a
  *wrong* value is CARDINAL).

### K. Discernment
- The atlas (religions charted), the alignment gate (aligned / reference ×0.6 / sectioned), the
  pairing, crisis-vs-reverence ("the fear of the Lord" is reverence, not a cry). Confirm the tiering
  can't be gamed and occult content stays explicit-request-only.

### L. Content / UX / aesthetic
- The writing is **standalone**, de-AI'd, "explain less"; the four site families + the one shell;
  nothing reads generated. Flag anything that sounds like a model wrote it.

---

## 3. Freshest surface — hit this first (changed since the 2026-09-06 brief)

| Area | Commits | Attack / verify |
|---|---|---|
| **Math expansion** — calc_chain, numeric, number_theory, system modes; exact-rational + inline-prose grading | `7c0b68d`, `a89da3f` | a false HOLDS on a corrupted chain; a prose fragment confirmed without its work; rational parsing hiding a real error |
| **Tolerance discipline** — all tol reads via `clamp_tol` | `9e8083c` | find any tolerance read that can be *loosened* by the caller (FP-widening) |
| **Kind B framing** — declines now return a framing question | `28c1ea7`, `6158f56` | a framing question that leaks internal data, or that turns a decline into an implied answer |
| **Front door** — `domain_resolver` as the Form-Gate confirm-menu; `clarify` coarse map subsumed | `3d4a62d` | a claim mis-routed to a wrong verifier that then false-HOLDS; crisis not deferring in the resolver |
| **Dictionary** — `define` (Webster's 1913 + supplement) | `6636eaf` | a supplement entry presented as Webster's; a non-PD definition; found=true on an unknown word |
| **Dedup** — `word_occurrences` folded into `word_study` | `8f446cd` | the `/word_occurrences` web route still paginates correctly after the tool fold |
| **Crisis FP guards** — financial/technical/calendar | `0100539` | a guard that suppresses a *real* cry (verify 0 hits on CRISIS_FLOOR + RED_TEAM) |
| **Lookup** — consolidated `lookup(kind,params)` + `find_verifier` | `8b5c1df` | a lookup value that disagrees with the verifier over the same data (they share one compute — prove or break it) |

Also live and worth re-probing: the Gateway `/verify` door, the physical-constants extractor, the
frozen shards, the ranker, the seal (`/s/<hash>`). (Details in the 2026-09-06 brief §2.)

---

## 4. Refine the processes — not only the bugs

Review the **processes** and propose concrete improvements:

- **Deploy** — is `box==repo` truly file-for-file every time? Is rollback exercised, not just coded?
- **Test gates** — the known pre-existing failures (§7): decide **fix or declare**, don't leave them
  ambiguous. The crisis global-cache race forces "run alone" — can the fixture make it order-independent?
- **Benchmark honesty** — every success metric should rest on an **external or grounded** standard,
  never a self-graded set (GSM8K is external; domain-goldens derive from the verifiers' own examples).
  Flag any metric the author both writes and grades.
- **The supervised loop & memory** — is the heartbeat bounded and watched? Does a self-directing
  writer to the live corpus ever run unwatched? (It must not.)
- **The no-model guard** — is it comprehensive, or can a new path smuggle a model call past it?
- For each: propose the process change **with** the mechanism that enforces it (a test, a gate, a guard).

---

## 5. The fix/verify loop — how to leave it better

For every CONFIRMED finding:
1. **Fix the path** (root, not instance).
2. **Pin it with a test** — one that fails before, passes after; add the case to the right floor
   (CRISIS_FLOOR, CLEARLY_BENIGN, a golden pair, GOLDEN_API_GET…).
3. **Re-run the pinning tests** — and the suites the change touches (contract change → re-run).
4. **Verify live** on the box (runtime, not HTTP 200).
5. **Deploy discipline** — `sh tools/deploy.sh`, end on `box==repo`.
A finding is not resolved until a test pins it and it's verified live.

---

## 6. Report format

Ranked **most severe first**. Per finding:
`{ aspect · severity · claim (one sentence) · failure scenario (inputs→wrong output) · reproduction ·
evidence · verdict: CONFIRMED|PLAUSIBLE · fix path · pinning test }`

Then: a **process-refinement** section (§4 proposals), the **ratchets** (did any floor drop — crisis
recall, red-team count, benchmark exactness, 0-FP?), and a one-line **verdict on the prime directive**
(did you, anywhere, get it to seal a falsehood?).

---

## 7. Known state — do NOT "fix" these (they're intentional)

- **~40 of 98 veiled red-team cries are unreachable** by the distributional backstop — a *named,
  documented* gap, not a regression. Do **not** "fix" it by lowering a threshold that manufactures
  false-positives; the substring-net + backstop + the deliberate recall>precision asymmetry are the design.
- **Pre-existing test failures** — `test_reachability` on undeclared routes (`/byom`, `/thesaurus`,
  `/face`, `/recombine`…) and `test_cut_field_pack`. Real but tracked — **declare or fix cleanly**, don't thrash.
- **Live-data & LLM exclusions** — currency/economic/wikidata lookups and any oracle/polymathic path
  are **excluded on principle** (sovereign / PD / no-model), not missing features.
- **Crisis tests run ALONE** — the global-cache order race is a documented test-harness property, not a bug to "merge away."
- **PD-only strictness** and **no account / free** are the mission, not limitations.

*A gap named is a gap kept honest. Find the ones we haven't named.*
