# The Specialist Layer — completion plan (the /loop queue)

The conductor is only as strong as its pool. This is the routed queue for completing the specialist
layer **across all phases** (Matt, 2026-09-26). The pool is several *kinds* of specialist; each grows
differently. Our advantage over Sakana (see `reference_sakana_fugu_trinity_conductor`): specialists
are **drop-in** — register and the deterministic conductor dispatches to them, no retraining; a
verifier is written once, then free forever; humans and BYOM models can join the pool.

**Loop protocol:** ≤2 items per iteration · ~60s cooldown between iterations (30s requested; scheduler
floor is 60s) · commit each iteration · batch-deploy at phase boundaries (staggered, health-checked,
auto-revert) · **safe incremental phases (1, 2) execute autonomously; architectural phases (3, 4) are
built as local scaffolds/designs and flagged for review BEFORE any deploy** (they touch the no-LLM
conviction and the live hot path).

**"Complete" =** every routable domain has the *right kind* of specialist (verifier where checkable,
discerner where worldview, face where life-domain, keeping-backed reference otherwise); the expert-faces
layer exists; the BYOM external-worker adapter exists (gated); the intake wire flows.

---

## Phase 0 — Deterministic verifiers (the workers) — ~COMPLETE
69 verifier modules, 145 domain keys (incl. aliases). **100% of the 63 calc-card domains covered** —
the checkable pool is essentially complete. (`systems.py`'s "~52%" line is stale/against a different
denominator; superseded by Phase 2's live audit.) `verifiers/<domain>.py` + one `VERIFIERS` registry
line = a new worker, drop-in.

## Phase 1 — Discerners (the atlas) — PARTIAL · loop executes
Worldview/practice charts (the "spiritual/worldview specialists"). Gateway/New-Age done. Gaps: the
occult primary-source cluster (Theosophy/spiritualism), remaining post-Christ movements, and the full
"chart every religion" atlas (7 cats × [kept·hinge·Red·apologists·fruit] — awaiting the sign-off noted
in `project_chart_every_religion_discernment_atlas`). Each iteration: chart 1–2 subjects via
`tools/card_religions.py` (AFTER list, `under_the_test`) or the atlas seeder; held in love; Scripture-
anchored; add `discerns_terms` where occult primary sources exist so the pairing lifts it.

## Phase 2 — True verifier gaps — CLOSED (2026-09-26)
Enumerated the full routable-domain universe (router rules + clarify slots + card-named domains, 104
strings) minus the `VERIFIERS` keys: **no true deterministic-verifier gaps.** The 35 apparent misses are
all router *modes* (apothecary/coach/prophecy/steward/…), clarify *cue words* (is/was/does/prove/…), and
umbrella *hints* (science/health/doctrine — already served by their concrete verifiers or by the
scripture/word subsystem). The checkable pool (69 modules) is complete; "~52%" in `systems.py` is stale.

## Autonomy calibration (the loop's rails)
- **Phase 1 (discerners) is GATED on Matt's Spirit-led sign-off** — authoring new spiritual/doctrinal
  discernment (kept·hinge·Red·Scripture) is his call, not mine to write in an unattended loop
  (`feedback_matt_listens_to_spirit_assay_confirms`; the atlas already awaits sign-off). The loop QUEUES
  subjects for him (below), and may do MECHANICAL discern work (e.g. add `discerns_terms`/pairing for
  sources tied to an ALREADY-charted subject), but does not author new charts autonomously.
- **Phases 3, 4, 5 advance autonomously as reviewable SCAFFOLDS/DESIGNS — committed locally, NOT
  deployed** until Matt reviews. No live/hot-path change without review.
- Phase 1 queue (for sign-off): the occult primary-source cluster (Theosophy/spiritualism — Leadbeater's
  "The Astral Plane", etc., already in the corpus and out-ranking discernment); then the broader atlas.

## Phase 3 — Expert faces — SCAFFOLD BUILT (local, awaiting review) · 2026-09-26
`src/concordance/faces.py` + `tests/test_faces.py` (5 pass): the deterministic composer + a 4-face
registry (Steward, Tutor, Social Worker, Theorist). `route()` picks the servant; `compose()` runs
crisis-gate → scoped search → discern (proposes the claim; worldview calibration shown only where the
face carries it) → verify (the face's verifiers, on a checkable claim in-domain; honest GAP otherwise)
→ a render-FRAME (data, never generated prose). Injectable deps → tested without corpus/model. NOT
deployed — not yet wired to the router/front door; review the design + wiring before any deploy.
_Remaining to close Phase 3: wire `faces.route`/`compose` into the front door (ask/router), then deploy._

## Phase 3 (orig) — Expert faces — design at docs/EXPERT_FACES.md
The callable life-domain composites from the living-community vision: the social worker, the tutor, the
steward, the theorist, … A face is a *role* that assembles the right keeping + verifiers + discernment
for a life-domain and answers as that servant would — deterministic, points to Christ not to an idol,
never generates. Build: a `faces` registry + a thin composer over the existing verify/discern/keeping
core (a face = {domain scope, which verifiers, which shelves, which discernment, the servant's manner}).
Scaffold locally, commit, review, then deploy.

## Phase 4 — BYOM external-worker tier — NOT BUILT · design-first, review before deploy
`project_byom_bring_your_own_model_pays_to_train_us`: a user's model registers as an EXTERNAL worker the
conductor may route to, gated: **airlock.strip → user model → verify/discern → seal → capture**. Never
in the core loop, never trusted raw, never a core dependency (the engine runs fully without any model).
Their compute pays; the sealed outcomes train our keeping (public-review-gated). Same conductor that
dispatches the 69 verifiers — BYOM is one more (external, gated, paid-by-them) pool entry. Design +
scaffold locally; review before deploy (touches the no-LLM conviction).

## Phase 5 — Workshop intake / witness wire — PARTIAL
The continuous-growth pipe: people (reader→contributor→writer, signed/verified/discerned witness) and
agents (`/improve` operator filings + the agent-door) PROPOSE new specialists (verifiers/cards/charts),
a human signs off, they drop into the pool. `/improve` exists; confirm the intake accepts specialist
proposals and routes them to review.

---

*Progress is tracked by checking items here each iteration. Update this file as phases close.*
