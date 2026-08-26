# Proving Ground 01 — AM Radio — MEASURE AND MAP (against concordance-2)

Run 2026-08-25. Method: run the domain end to end through the current engine; write two lists; do not
cohere anything until both exist. This is the OUTPUT of measurement, not a plan — every line traces to
a run.

## What was measured

- **Verifier coverage.** 66 verifiers present; RF-adjacent = `acoustics`, `electrical`, `optics`. **No
  `radio`/RF/modulation verifier.** So M04–M14 (sidebands, modulation index, power budget, IF, image)
  have no door.
- **Benchmark coverage.** 5 AM-radio claims through `audit` (extract → verify): **0/5 checkable** — every
  one returned `NOTHING_TO_CHECK` (found=0). The generic-arithmetic control ("50 hours at $95/hr =
  $4750") returned found=1, **HOLDS** — so the pipeline works; the domain has no rules and no verifier.
- **Language fixture** (`language_003`, the Fessenden/Armstrong paragraph). `audit` → **0 atoms**,
  `NOTHING_TO_CHECK`. The paragraph carries ~9 checkable/flag-worthy atoms; the engine sees none.
- **Discern.** `discern(language_003)` → kind=`question`, next=`retrieve`, **lens=None, cloud=None**,
  5 retrieved cards. Two findings: (a) discern routes the whole paragraph as one retrieval — it does not
  segment or atomize; (b) **D6 already HOLDS** — no devotional voice on a factual document (better than
  the predecessor's "2 devotional passages"; the sovereign-gated lens is the reason).

## List B — what AM radio NEEDED that the engine lacked (the domain produced this, in order)

1. **`segment.py` + the language flag families (F3/F4/F8/F9).** `language_003` → 0 atoms. No sentence/
   clause split; no superlative / laundered / hedge / opinion flags. The single largest gap. *(structural —
   every language input needs it.)*
2. **`verifiers/radio.py`** — M04–M14 RF/modulation formulas. No RF verifier exists. *(domain verifier.)*
3. **Radio dispatch/extraction rules** — even the formulas that a verifier could settle (m, power,
   sidebands) are never EXTRACTED (0 found). Needs `(rule_id, pattern, domain)` rules for modulation
   index, sideband location, power budget, IF/image. *(the 12→N extraction gap, made concrete.)*
4. **The `range` / within-bounds verdict** — M22/M23 (TCXO vs OCXO "more stable") is a bound, not a point;
   today it would be forced to CONFIRMED/MISMATCH. The vocab touches `range` (1) but not as a mode.
5. **Kept regulatory cards** — M01–M03, M18 (band edges, channel spacing, max power) are table facts with
   citations; no radio cards are held → these can only ever be INCOMPLETE "no kept source."
6. **Modifiers-travel / split-atoms + contested-date handling** — `language_003` has a true date inside a
   false claim ("Armstrong invented the superhet **in 1918**": date HOLDS, "invented" INCOMPLETE/contested).
   The emitter must split them and let modifiers travel. *(the correctness condition.)*
7. **The axis dialectic — `voices` / `sides` / `before`** — the Armstrong / De Forest / Lévy priority
   dispute and the spark→CW displacement. Absent.
8. **Layered fetch** — M19 (live FCC clear-channel count): live at layer 4, INCOMPLETE below. Absent.
9. **A loop runner** — to run the 50-claim benchmark + `language_003` nightly and re-seal for determinism.

## List A — features AM radio never touched (suspects — PARK, not delete)

Parked with the note "not exercised by proving ground 01"; kept only if another proving ground needs them:
- **The narrowing engine** (`candidates.py` / narrow→finish→verify). AM radio is **direct verification**,
  not a field of candidates — it never invoked narrowing. *Awaits a domain with a candidate field
  (bookkeeping's offsetting-error set, a units puzzle).* **This down-ranks narrowing from "cohere first."**
- The apophatic `ask` seed-bank, the polymathic layer, mesh/LoRa distribution — untouched by this domain.
- ~60 of the 66 verifiers (scripture, theology, genetics, geology, giving, governance, …) — untouched;
  parked for their own domains.
- The discern lens/cloud witnesses — untouched here (a factual paragraph needs no near/far witness), but
  the **priority-dispute atoms in §7 will need `voices`** — so voices moves from List A to List B via the
  dialectic, not the factual claims.

## The adjustment this measurement makes to HARVEST §6

Confirmed **cohere-first** by AM radio (a real domain needed each): ① segment + flags · ② modifiers-travel
· ④ the `range` verdict + kept-table facts · ⑤ the sealed coverage report · **+ the domain-verifier +
dispatch-rule pattern** (`verifiers/radio.py` and its rules — the general form of the 12→N extraction gap).
**Down-ranked, awaiting another domain:** ③ the narrowing engine — powerful, but AM radio did not touch it;
one domain has not yet made it structural. Cohere it when a second domain asks.
