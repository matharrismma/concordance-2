# Conductor — DECISIONS ledger (SOP-01)

One paragraph per session: what was built, what failed, what was harvested, next step (singular).
A step that produces no record did not happen.

---

## 2026-08-24 — M0: Baseline & Wiring Proof — COMPLETE, suite green

**Built.** The thin package over the deployed engine. `contracts.py` freezes the interfaces
(WorkOrder, AgentReturn, GateResult, SealedPacket) with a CI drift check. `engine_bridge.py` maps a
manufacturing WorkOrder onto the engine's DECISION_PACKET envelope and runs it through
`validate_and_seal` (the kernel's real RED→FLOOR→PATH→WITNESS→WAIT gates), sealing only PASS records
to the chain via `ledger.seal_to_ledger`. The manufacturing envelope rides as red_items/floor_items
(a domain profile, fuller in M2); the reference's standalone gates stay canon-for-behavior only, so
the kernel's RED-005/RED-006 still govern every shop packet. **Exit met:** a work order flows
capture → validate_packet → chain end-to-end using only existing organs (`tests/test_conductor_m0.py`,
5 tests). Delegation is real, not cosmetic: a predatory way_path trips **RED REJECT** and never seals;
an order inside its **WAIT** window quarantines and never seals; the sealed chain verifies (ok:True).

**What failed / harvested.** First run: two test-assertion errors (not wiring bugs) —
`verify_chain` returns a dict `{ok: ...}` not a bare bool, and the gate trail carries several RED
sub-checks so a strict positional `[:5]` slice was wrong. Harvest: assert on `["ok"]` and on the
dedup-in-order gate spine. The probe before writing (empirical, not assumed) is what caught that a
clean packet QUARANTINEs on WAIT until its window elapses — so the test simulates elapsed time via
now_epoch, which also proves the WAIT gate genuinely governs.

**Repo note.** Package lives at `conductor/` inside concordance-2 (connect-not-rebuild), per
CANON_CORRECTIONS §6. Not deployed — M0 is groundwork, not a served surface. Full concordance suite
is corpus-slow on the dev box; the M0 change is purely additive (new package + tests, no engine
edits), and the fast pure set (conductor + clean-urls + reachability, 29 tests) is green.

**Next step (singular).** M1 — the classifier: rule-based, confidence-scored, CLARIFY below 0.7,
nine-type shop taxonomy, CRISIS routes to RED and halts autonomous action, 100% on Matt's 50
hand-labeled orders (SOP-02) before it ships.

---

## 2026-08-24 — M1: the classifier — built, suite green (SHIP GATE pending Matt's labels)

**Built.** `conductor/classify.py` — the nine-type shop taxonomy (QUOTE, TOOLING, SCHEDULE, QUALITY,
MATERIAL, MAINTENANCE, PROCESS, HISTORICAL, + CRISIS), rule-based and confidence-scored. Strong
keyword hit -> 0.9; weak-only -> 0.62 which collapses to CLARIFY (the disposition is 'ask, don't
guess', the weak guess kept in the note). CRISIS is first and halts autonomous action. `is_crisis`
ORs a local shop PHYSICAL-injury list with the kernel's PASTORAL matcher (concordance.ask.is_crisis)
— never defers to one, because they are different notions of crisis. `run_benchmark(cases)` is the
harness; 100% is the ship gate. Locked by tests/test_conductor_classify.py (7): seed benchmark 100%,
every type covered, CRISIS-first even disguised ('someone got hurt bad on the saw'), CLARIFY on vague
work, confident types are not CLARIFY.

**What failed / harvested.** First run caught two real bugs: (1) `is_crisis` deferred to the kernel
matcher, which is the PASTORAL crisis (suicide/despair) and does NOT flag a physical-injury shop cry
('someone is hurt, call 911') — fixed to OR a local injury list; (2) below-threshold weak matches
returned the weak type instead of CLARIFY — fixed to collapse to CLARIFY as the disposition. The
tests are what surfaced both.

**The ship gate is NOT met and cannot be by me.** SOP-02: the classifier ships at 100% on 50 of
MATT'S real work orders, in the shop's own words, disguised cases marked — Matt only, not delegated.
The SEED in the test is SYNTHETIC placeholder that exercises the rules and the harness; it is not the
gate. When Matt provides the 50, load them and iterate the rules to 100% on THAT set.

**Next step (singular).** Matt gathers the 50 real orders (SOP-02) -> tune classify.py to 100% on
them; THEN M2 (the shop domain: domains/machine_shop.py + verifiers/manufacturing.py, the real
engineering).
