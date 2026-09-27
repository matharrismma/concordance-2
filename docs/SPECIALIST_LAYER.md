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

## Phase 2 — True verifier gaps — TODO · loop executes
**First loop task:** enumerate the routable-AND-deterministically-checkable domains (router.py rules +
clarify slots + any domain named on cards) MINUS the `VERIFIERS` keys. Then add a real deterministic
verifier for each genuine gap (never a stub — a bluffing specialist is worse than an honest GAP; fails
closed; "our failure ≠ their falsehood"). Non-checkable domains (history/sociology/…) are NOT verifier
gaps — they are served by discerners (Phase 1), faces (Phase 3), or the keeping.

## Phase 3 — Expert faces — NOT BUILT · design-first, review before deploy
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
