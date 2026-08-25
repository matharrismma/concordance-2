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
