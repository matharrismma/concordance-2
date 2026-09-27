# Expert Faces — the callable life-domain composites (Phase 3 design)

*Design for review — no code deployed until Matt signs off (see docs/SPECIALIST_LAYER.md).*

A **face** is a callable servant for a life-domain — the social worker, the tutor, the steward, the
theorist — the "hands and feet" of the one body (1 Cor 12; `project_witness_wire_levels_contributors_writers`).
A face is **not a model and not a new brain.** It is a *composer*: it assembles the specialists we
already have — verifiers, shelves, discernment — into the answer a wise servant in that domain would
give. It **never generates**, holds no new knowledge of its own, and points to Christ, never to itself
(`feedback_companion_points_to_christ_not_idol`). This keeps the sovereign core deterministic and no-LLM.

## The contract (a face is data, not code)
```
Face = {
  id:          "face_steward",
  name:        "the Steward",           # the servant role, the WITNESS name (branding.COACH_NAME aware)
  scope:       [needs/keywords the router routes to this face — its life-domain],
  shelves:     [which keeping it draws on — the search is SCOPED to these first],
  verifiers:   [which deterministic checkers it runs on any checkable claim in the request],
  discernment: [which atlas charts / gates apply — e.g. stewardship: steward never executes],
  manner:      a FIXED frame for how the servant speaks (templated, never generated),
  crisis:      always defers to the crisis net first (help-first, never overridden),
}
```

## The composer (deterministic, one path)
Given a request routed to a face, `faces.compose(face, request)`:
1. **Kernel + crisis gates first** — the five-part kernel and the crisis net run before anything; a face
   never speaks over a cry (`feedback_crisis_*`). If crisis, hand off to the crisis response.
2. **Gather** — `corpus.search` scoped to the face's `shelves` (then the whole keeping as fallback), so
   the servant draws on its own domain's substance first.
3. **Verify** — run the face's `verifiers` on any checkable claim the request carries (via the existing
   engine/`verify_derivation`); attach the worked trail + seal. Honest GAP where not checkable.
4. **Discern** — apply the face's `discernment` charts/gates (the same `discern` + pairing as the front
   door), so the servant's answer is calibrated to the Word and flags what it must.
5. **Render** — present as that servant would, in the wisdom-engine frame (narrow to a discernible
   scenario, a parable/fable): a TEMPLATED rendering over the gathered+verified+discerned material.
   Never generated prose — the manner is a fixed frame, the content is the keeping's.
6. **(Optional) BYOM polish** — a face MAY call a user's BYOM worker (Phase 4) for synthesis, but ONLY
   through airlock → verify/discern → seal. Default is the deterministic assembly; BYOM is opt-in.

## First faces (drawn from EXISTING components — no new authoring)
- **the Steward** — provision/finance: stewardship shelf + finance/economics verifiers + the stewardship
  gate (`project_loss_leaders_and_stewardship_of_value` — steward never *executes* a transaction).
- **the Tutor** — learning: the coach + OpenStax + the subject shelves + math/science verifiers.
- **the Social Worker** — needs/hardship: crisis net first, then the field library (firstaid/water/food/
  power/sanitation/survival shelves) + the want-list/resources.
- **the Theorist** — science/math: theory cards + the calc/physics/chemistry verifiers + the bridges.

## Why this is a specialist, and safe
It adds a *kind* of specialist the conductor can route to (a life-domain servant) without any model, any
generation, or any new doctrine — it only *arranges* what already passed the gates. It fails closed
(GAP over bluff), defers to crisis, and turns the eye upward, not to itself. Build order: a `faces.py`
registry + `compose()` over the existing verify/discern/keeping core, one example face wired end-to-end,
tests, review — then the rest, then deploy.
