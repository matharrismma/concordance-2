# Narrow Highway — The World Document

*A comprehensive, grounded reference to the whole project — for review (handoff to Sonnet), and for
anyone who needs the entire map in one place. Every number and location below was verified against the
live engine and the repo on 2026-09-02. Where a figure can drift, the live source is named so it can be
re-checked rather than trusted.*

Repo root: `concordance-2/` · Live: **narrowhighway.com** (secular / reach) · **narrowhighway.org**
(witness) · **narrowhighway.tv** (museum) · Box: `nh@5.78.186.55` · Deploy: `sh tools/deploy.sh <files>`
(box == repo, no git on the box).

---

## 0. How to read this

The engine is **one body**, not a bundle of features. A request flows through it and the parts compose
into one answer. The canonical identity, defined once in [`src/concordance/branding.py`](../src/concordance/branding.py)
(`IDENTITY_LINE`), is: **"A deterministic verification engine."** It *finds and verifies*; it does not
generate. It is a **conduit, not the source.**

The single most authoritative, always-live source of "what this is and how much of it exists" is
**`GET /capabilities`** — every number carries a `means` line saying exactly what was counted. When this
document and `/capabilities` disagree, `/capabilities` wins.

---

## 1. Identity & Mission (the telos)

- **What it is:** a sovereign, deterministic verification + finding + citation engine. Bring a claim →
  get a **verdict**, the **worked reasoning (trail)**, and a **permanent, re-checkable receipt (seal)**.
  No model in the loop; nothing generated.
- **Whom it serves first:** families, children, and communities who cannot afford to be without it —
  free, no account, works offline. (memory: *serve families first*, Mt 25.)
- **What it ultimately serves:** Jesus Christ. The `.org` witness surface names the foundation plainly
  (Scripture in the original languages, Christ at the center); the `.com` reach speaks the world's own
  language and openly links to the witness. Same engine, two voices (`branding.SECULAR_IDENTITY` vs
  `branding.WITNESS_IDENTITY`).
- **The method (Romans 12:1):** reasoned service — *elimination illuminates the narrow path by what
  survives*. Good fruit is the measure.

Key docs: [`docs/V2_DEFINITION.md`](V2_DEFINITION.md), [`docs/ROMANS_12.md`](ROMANS_12.md),
[`docs/ARCHITECTURE_ONE_BODY.md`](ARCHITECTURE_ONE_BODY.md), [`docs/CORE_USER.md`](CORE_USER.md),
[`docs/VISION_PLAN.md`](VISION_PLAN.md).

---

## 2. The Laws (the kernel, the covenant, the boundaries)

**The five-part kernel** (published at `GET /kernel`; module [`src/concordance/kernel.py`](../src/concordance/kernel.py)):
**find · distinguish · verify · preserve the trail · never silently upgrade authority.**

**The eight-rule agent covenant** (in `/llms.txt` and `GET /identity`): (1) retrieve from corpora first;
(2) distinguish citation from proof; (3) quarantine generated material; (4) request human authorization
before writes; (5) produce a receipt for consequential actions; (6) carry provenance through every
transformation; (7) respect local data and identity boundaries; (8) stop when evidence is incomplete.

**Boundaries (enforced, not aspirational):**
- **Nothing is generated** — a conduit, not a source. It declines when it cannot verify (three honest
  states: `HOLDS` / `BROKEN` / `INCOMPLETE`; plus `SYSTEM_ERROR` = *ours*, never a refutation).
- **No account, no login, no tracking** — "nothing here records who read what."
- **Writes require an Ed25519 signature**, not a session (keys born on the user's device; the server
  holds only public keys).
- **Public-domain only** for others' text (PD = the *edition/translation* year is pre-1929, or a US
  federal work under 17 USC 105 — verified at acquisition; see [`docs/HARVEST.md`](HARVEST.md)).
- **Crisis-safe** — a cry for help is met before anything else (§11).
- **Points beyond itself to Christ** — never an idol.

---

## 3. Architecture (the flow, the surfaces, the topology)

**The flow a request takes** (front door: [`src/concordance/ask.py`](../src/concordance/ask.py) `respond()`;
served at `POST /ask`):

```
Ask · Seek · Knock  →  Discern (classify: crisis-first, then the kind)  →  Verify | Find  →  Seal
```

- **Discern:** [`ask.py`](../src/concordance/ask.py) + [`discern.py`](../src/concordance/discern.py) +
  [`clarify.py`](../src/concordance/clarify.py) + [`path.py`](../src/concordance/path.py) (the answer is
  a *path*, not a card) + [`router.py`](../src/concordance/router.py).
- **Verify:** [`engine.py`](../src/concordance/engine.py) (`validate_and_seal`) over the domain verifiers.
- **Find (the Tortoise):** [`find.py`](../src/concordance/find.py) navigates a kept canon
  ([`field_canon.py`](../src/concordance/field_canon.py)) by elimination, then pulls & cards a
  public-domain source ([`expand.py`](../src/concordance/expand.py), [`providers.py`](../src/concordance/providers.py)).
- **Seal:** [`receipts.py`](../src/concordance/receipts.py) — a content-addressed hash, addressable at
  `GET /s/<hash>` (human page) and `GET /seal?hash=<hash>` (JSON).

**Topology:** the body is currently a **star** — `ask` is the hub (composes ~13 of the parts), with
`keeping` and `verify` as the roots. This is legible on the live map (§12): the parts should mesh
peer-to-peer where logical (the polymathic pattern, fractal), not only through the hub.

---

## 4. The Three Surfaces (`.com` / `.org` / `.tv`)

One engine; the surface is chosen by host and carried as `EngineConfig(surface)`. Two **separate service
processes** on the box: `nh-org` (:8001, witness) and `nh-com-2` (:8002, secular). `home_for()` in
[`web/api.py`](../src/concordance/web/api.py) serves a different landing per surface.

- **`.com` — the reach (secular).** `/` serves [`site/com.html`](../site/com.html): the deterministic-
  engine face — a live "check a claim" instrument, the 65-domain breadth, the receipt, the API/agent
  door. Cool "ledger + verdigris" design, self-hosted Spectral/IBM Plex fonts (`site/fonts/`), sovereign.
  Its numbers are **live-wired** from `/capabilities`.
- **`.org` — the witness.** `/` serves [`site/index.html`](../site/index.html) (the "desk"): Christ
  forward — *"Christ is the center. The Word is the foundation."* — searches Scripture in the original
  Hebrew and Greek, points past itself to Jesus. Warm walnut/book aesthetic, system fonts. Doors lead
  with the Word.
- **`.tv` — the museum.** `/tv` — curated public-domain channels + the kept library.

**Site pages** (29 HTML in [`site/`](../site/), 13 JS): the desk (`index.html`), the secular landing
(`com.html`), the working checker (`checkit.html`), Scripture (`bible.html`), the dictionary
(`characters.html`), reading (`read.html`), wisdom (`wisdom.html`), the guild lobby (`halls.html`),
the coach (`coach.html`), the daily walk (`plow.html`), the profile (`profile.html`), situations
(`situations.html`), the workshop (`workshop.html`), the systems dashboard (`systems.html`), **the map
of everything (`map.html`)**, "what it proves" (`proof.html`), the agent card (`connect.html`), "under
the hood" (`live.html`), the operator console (`keep.html`, noindex). Shared JS: `nh-home.js` (the home
control), `nh-tools.js` (the Ctrl-K palette), `nh-search.js` (offline keeping search), `graph.js` (the
constellation renderer — `NHGraph.local` per-card, `NHGraph.map` the full map), `redact.js` (the
client-side privacy gateway).

---

## 5. The Subsystems (15)

Defined in [`src/concordance/systems.py`](../src/concordance/systems.py) `SUBSYSTEMS`. Each is scored by
a **golf handicap** (low is strong; live/tested/SOP/supported dimensions) and now carries an
**integration** signal (its degree in the module-import graph — the polymathic mesh made fractal).
Live at `GET /systems`; rendered at `site/systems.html` and as the constellation on `site/map.html`.
**Course handicap: 1.1** (live). Each has an SOP in [`docs/SOP/subsystems/<slug>.md`](SOP/subsystems/).

| Subsystem | slug | key modules (in `src/concordance/`) | state |
|---|---|---|---|
| Front Door / Ask | `ask` | ask, router, discern, clarify, seekers | hub (deg 13) |
| Verify / the Moat | `verify` | derivation, receipts, gates, kernel, audit, candidates, validate, warrant | connected; verifier coverage ~52% (open) |
| The Word / Scripture | `scripture` | canon, harmony, commentary, xrefs, backmatter, characters, timeline, bible_places | connected (thin at module level) |
| Original Tongues | `tongues` | pronounce, translate, isbe | connected via `pronounce → word study` (was isolated; §12) |
| Prophecy | `prophecy` | prophecy, prophecy_fulfillments | thin; OT→NT sweep not yet run |
| Cloud of Witnesses | `witnesses` | witness, mentors, lens, voice | thin; founders gather pending |
| Find / the Tortoise | `find` | find, providers, expand, craft, field_canon, sources | **degraded** (pull can mis-select; guarded) |
| The Keeping / Corpus | `keeping` | corpus, corpus_db, graph, decks, wayfind, growth | **degraded** (ranker blind to substance vs headword) |
| Crisis / Safety | `crisis` | crisis_semantic, floor, seeds | connected |
| Coach / Shepherd | `coach` | coach, disciple, formation, serve | connected |
| Field Library | `field` | apothecary, almanac, playbook, compute, science_cards, chess | connected; thinly stocked (grows on demand) |
| Museum / TV | `tv` | tv | connected; feeds thin |
| Identity / Profile / Community | `identity` | identity, profile, community, groups, covenant, consent, signing | connected |
| Steward (money) | `steward` | steward, ledger | connected; concierge/swipe-fee is future |
| Node / Sovereignty | `node` | lighthouse_node, node_roles, mesh, meshtastic_bridge, airlock | connected; off-site backup open |

> **Honest caveat on the graph:** the integration degree is derived from *top-level module imports*, so
> it misses `verifiers.*` composition and runtime handoffs. A "thin" part (scripture/prophecy/witnesses)
> is **functionally integrated in the flow** (a scripture study answer already weaves the verse +
> cross-refs + commentary + the witnesses cloud) — it just doesn't mesh at the source level. The graph
> is a real but partial lens; treat "thin" as "does not peer-mesh," not "the flow never reaches it."

---

## 6. Verification (the moat)

- **Engine:** [`src/concordance/engine.py`](../src/concordance/engine.py) — `validate_and_seal(packet)`:
  governance → gate → domain validation → seal. Gates in [`gates.py`](../src/concordance/gates.py);
  candidate engine in [`candidates.py`](../src/concordance/candidates.py).
- **Domains:** **65 distinct verifier modules** (66 files; `retrieval` is the find mechanism, not a
  domain) in [`src/concordance/verifiers/`](../src/concordance/verifiers/) — acoustics, astronomy,
  chemistry, cryptography, finance, law, medicine, music_theory, nuclear_physics, quantum_computing,
  scripture, thermodynamics, … **133 domain names accepted** (aliases). Registry:
  `verifiers/__init__.py` (`VERIFIERS`, `WITNESS_VERIFIERS`, `run_for_domain`). Live counts:
  `GET /capabilities` → `verifiers`.
- **The receipt/seal:** spec at [`docs/SEAL_SPEC.md`](SEAL_SPEC.md); independent verifier
  [`tools/verify_seal.py`](../tools/verify_seal.py) (~60 lines, stdlib only → MATCHES / TAMPERED-OR-WRONG
  / NO_CLAIM). Anyone can re-check without trusting us.
- **The benchmark:** [`docs/BENCHMARK.md`](BENCHMARK.md) + [`tools/benchmark.py`](../tools/benchmark.py) —
  "0 false positives" is **always** bounded to the published, versioned cases, never asserted in the
  abstract.

---

## 7. The Keeping / Corpus

- **Size (live `/capabilities` → `substrate`):** **673,243 cards** (~163k substance, ~499k frozen, ~2.8k
  stubs). The base is the Bible; every kept card is a gradient step (memory: *the keeping is the model*).
- **Store:** [`corpus.py`](../src/concordance/corpus.py) (in-RAM, TF-IDF + a `SUBJECT_TIER` lexical
  partition), [`corpus_db.py`](../src/concordance/corpus_db.py) (the acquisition DBs). Production keep is
  APPENDED to `nh@5.78.186.55:/home/nh/concordance-2/data/`.
- **The connection graph:** [`graph.py`](../src/concordance/graph.py) → `GET /graph?scope=overview|shelf|card`.
  Live: **653,337 ideas across 110 shelves, 3 planes (nesting · found · crossings), 0 isolated** —
  everything connects. Rendered by `site/graph.js` (`NHGraph.map`), hosted on **`site/map.html`**.
- **Growth:** [`expand.py`](../src/concordance/expand.py) + [`card_sources.py`](../src/concordance/card_sources.py) —
  the corpus *always grows*; every cleaning batch net-grows it.

---

## 8. The API

- **Router:** [`src/concordance/web/api.py`](../src/concordance/web/api.py) (3,414 lines) — a stdlib
  `http.server`. `ROUTES` registry ↔ `dispatch()` are **bidirectionally test-locked**
  ([`tests/test_routes.py`](../tests/test_routes.py)): every dispatched path is registered and vice-versa.
  **191 registered routes (184 live + 7 tombstones), 133 GET paths, 72 rate-limited** (live `/capabilities`
  → `routes`).
- **Start-here endpoints:** `POST /audit` ({text} → sealed multi-claim report), `POST /verify` (structured
  claim), `POST /ask` (the front door), `GET /search`, `GET /card?id=`, `GET /graph`, `GET /capabilities`,
  `GET /systems`, `GET /kernel`, `GET /identity`, `GET /health`, `GET /s/<hash>` (receipt).
- **CORS:** **open on every response** (`Access-Control-Allow-Origin: *`, `OPTIONS` preflight answered) —
  any browser app or agent can call the read/verify API with no key. Safe because there is no ambient
  credential (the one cookie, `nh_gate`, is not sent cross-origin); writes still need a signature.
- **Rate limits:** 600 reads/min, 120 writes/min per client ([`ratelimit.py`](../src/concordance/ratelimit.py)).
- **Privacy gateway:** [`gateway.py`](../src/concordance/gateway.py) + `site/redact.js` — "private in,
  verified out": PII stripped client-side before a call, reapplied locally. Docs: [`docs/GATEWAY.md`](GATEWAY.md).

---

## 9. The MCP (agent interface — the scale surface)

- **Server:** [`src/concordance/mcp/server.py`](../src/concordance/mcp/server.py) (JSON-RPC) +
  [`mcp/http.py`](../src/concordance/mcp/http.py) (Streamable HTTP transport). Mounted at `POST /mcp` and
  six profile planes: `/mcp/{core,library,sovereign,coach,witness,community}`.
- **Catalog: 94 tools across 6 profiles** (live `/capabilities` → `tools`, `substrate.mcp_profiles`).
- **One-line install:** `claude mcp add --transport http narrow-highway https://narrowhighway.com/mcp`.
  Sovereign option: `python -m concordance mcp` (stdio). Agent-facing card: **`/llms.txt`**
  ([`site/llms.txt`](../site/llms.txt)).

---

## 10. Identity / Gate / Covenant

- **Keys:** Ed25519, born on the user's device. Derived from **four covenant verses** (`covenant.py`);
  the server stores only public keys and verifies signed challenges ([`identity.py`](../src/concordance/identity.py),
  [`signing.py`](../src/concordance/signing.py)). No account, no password, no recovery backdoor.
- **The Gate:** the Ask/Seek/Knock discernment; witness content surfaces on `.com` only once the reader's
  own seeking opens it (carried by the `nh_gate` cookie, same-origin only). "Nothing is hidden" — the two
  surfaces differ in *voice*, never in *what they will show*. Doc: [`docs/DOOR.md`](DOOR.md),
  [`docs/AUTH_POSTURE.md`](AUTH_POSTURE.md).

---

## 11. Crisis / Safety

- **The net:** `ask.is_crisis` = a substring matcher UNION a deterministic **semantic backstop**
  ([`crisis_semantic.py`](../src/concordance/crisis_semantic.py); artifact built by
  [`tools/build_crisis_semantic.py`](../tools/build_crisis_semantic.py)). Recall floor + benign-precision
  are test-pinned ([`tests/test_crisis_coverage.py`](../tests/test_crisis_coverage.py)).
- **Honest guards:** `_BENIGN_MEASUREMENT` (a physical "how much does X weigh" is not a cry) and
  `_THEODICY` (the problem-of-evil is the *seeker's* question, routed to the god-ward gate — the guard
  only mutes the backstop; the substring net still catches any real cry). Doc: [`docs/CRISIS_BACKSTOP.md`](CRISIS_BACKSTOP.md).
- **The floor:** [`floor.py`](../src/concordance/floor.py), [`seeds.py`](../src/concordance/seeds.py) — the
  rooted foundation; real people first (`real_help`), the word, then a door — never a helpline alone.

---

## 12. The Map & the Systems Handicap (health, order, the fractal)

- **`GET /systems`** ([`systems.py`](../src/concordance/systems.py)) → the golf handicap per subsystem +
  the course handicap (1.1) + the **subsystem graph** (`subsystem_graph()`: who wires to whom, from real
  import edges) + a per-part `integration` (isolated/thin/connected). This measures the *order* — a part
  wired to nothing is out of order where "its code imports fine" never shows it.
- **`site/systems.html`** — the flat health dashboard (status pill + 4 handicap dimensions, worst-first).
- **`site/map.html` — the map of everything** (linked from both faces + the Ctrl-K palette): the flow,
  the three surfaces, live counts, **the body drawn as a constellation** (the subsystems, colored by
  health, edges the real import links — the polymathic pattern *fractal*, one scale up from the cards),
  and the live **card constellation** (`NHGraph.map`). This is where "a subsystem out of order" reads at
  a glance. As of 2026-09-02, **0 isolated** (Original Tongues was the last, now wired via `pronounce`).
- **The polymathic principle (fractal):** connections recur at every scale — cards ↔ cards, domains ↔
  domains, subsystems ↔ subsystems, surfaces ↔ surfaces. The parts should mesh *where logical*. Docs:
  [`docs/FASCIA.md`](FASCIA.md) (the connective domain / recurring form), [`docs/ARCHITECTURE_ONE_BODY.md`](ARCHITECTURE_ONE_BODY.md).

---

## 13. Operations

- **Deploy:** `sh tools/deploy.sh <repo-relative files>` ([`tools/deploy.sh`](../tools/deploy.sh)) — one
  tar-over-ssh transfer; **staggered restart** (witness back to 200 *before* secular is touched — a real
  canary); patient health polling; a rollback snapshot under `/home/nh/deploy-rollback/`. It deliberately
  does NOT touch git. **box == repo** is verified file-for-file at the end.
- **The box:** `nh@5.78.186.55:/home/nh/concordance-2` — no git; both services hold the corpus in RAM and
  reload on restart. `tests/` and `docs/SOP/subsystems/` must be synced to the box for `/systems`
  accuracy. Doc: [`docs/DEPLOY.md`](DEPLOY.md), [`docs/RUNBOOK.md`](RUNBOOK.md), [`docs/SELF_HOST.md`](SELF_HOST.md).
- **Tests:** **219 `test_*.py`** in [`tests/`](../tests/) (stdlib + pytest; standalone-runnable). Crisis
  tests must run alone (a documented global-cache ordering race). The **Watchman** discipline: tests
  prove code, end-to-end proves the library — CANNOT_CHECK ≠ pass.
- **Backup:** [`tools/backup.sh`](../tools/backup.sh); HD bundle to `/d/NarrowHighway-2.0-backup/`.
- **Git discipline:** commit by exact paths (never `add -A`); commit + push are explicit, human-reviewed;
  co-author trailer on commits. Deploy is separate from commit.

---

## 14. Current State (2026-09-02)

- **Live and healthy:** course handicap **1.1**; 15 subsystems, **0 out, 0 isolated**, 2 **degraded**.
- **The two degraded (the real frontier):**
  1. **Find / the Tortoise** — the pull can mis-select a tangential source (guarded now by a post-pull
     relevance check so a mis-select falls to an honest gap, never a confident wrong lead).
  2. **The Keeping / Corpus** — the ranker is blind to *substance vs headword* (~67% of source cards are
     word/pronunciation stubs). The connection signal is composed but near-inert until the graph
     densifies (memory: *connection signal composed into found lead*).
- **Open, tracked (not bugs to auto-fix):** verifier domain coverage ~52%; OT→NT prophecy sweep not run;
  founders (Ellen G. White, etc.) gather pending; off-site backup durability; the theory grid / Floor /
  Bible-atlas renderers exist but have no host page (a *surfacing* project, deliberately paused);
  `find_verifier` is referenced in the MCP verify tool description + some docs but not implemented in this
  repo; [`docs/THE_MAP.md`](THE_MAP.md) carries stale counts (superseded by this file).
- **Recently shipped:** the secular `.com` face + surface sort; Christ forward on `.org`; the CORS agent
  door; the theodicy crisis fix; the map of everything + the subsystem constellation; live-wired numbers;
  the tongues↔Word reconnection.

---

## 15. Directory & Location Index

```
concordance-2/
├── src/concordance/           127 modules — the engine
│   ├── ask.py                 the front door / router (respond())          [1877 lines]
│   ├── engine.py              validate_and_seal — the verify core          [270]
│   ├── corpus.py              the keeping (in-RAM store + ranking)         [1016]
│   ├── systems.py             the handicap + the subsystem graph           [222]
│   ├── branding.py            IDENTITY_LINE + per-surface identity/persona [78]
│   ├── kernel.py, gates.py, receipts.py, candidates.py, validate.py   the moat
│   ├── find.py, expand.py, providers.py, field_canon.py               the Tortoise
│   ├── graph.py, corpus_db.py, decks.py, growth.py                    the keeping
│   ├── crisis_semantic.py, floor.py, seeds.py                        crisis / safety
│   ├── identity.py, signing.py, covenant.py, consent.py, profile.py  identity / gate
│   ├── gateway.py             the privacy gateway (redact / reapply)
│   ├── verifiers/             67 files — the 65 domains + registry
│   ├── web/                   api.py (the HTTP router, 3414) + support     [3 files]
│   └── mcp/                   server.py (JSON-RPC, 1781) + http.py         [2 files]
├── site/                      29 HTML pages + 13 JS — the surfaces
│   ├── com.html               the .com secular landing (live-wired)
│   ├── index.html             the .org witness desk (Christ forward)
│   ├── map.html               THE MAP OF EVERYTHING (flow · body · constellation)
│   ├── systems.html           the handicap dashboard
│   ├── graph.js               the constellation renderer (NHGraph)
│   ├── nh-tools.js            the Ctrl-K palette   ·   nh-home.js  the home control
│   ├── llms.txt               the agent-facing contractor card
│   └── fonts/                 self-hosted Spectral + IBM Plex (woff2)
├── tests/                     219 test_*.py  (test_routes locks the API surface)
├── tools/                     deploy.sh, backup.sh, verify_seal.py, benchmark.py, build_*.py
├── docs/                      45 .md  (SEAL_SPEC, BENCHMARK, DEPLOY, GATEWAY, DISCERN, this file …)
│   └── SOP/subsystems/        16 per-subsystem operating procedures (<slug>.md)
├── data/                      the corpus + artifacts (mirrors the box's data/)
├── conductor/  deploy/  eval/  engineering-reference/   supporting
```

---

## 16. Glossary

- **The keeping** — the corpus; the substrate that *is* the model.
- **The Tortoise** — the find/fetch fallback: when the keeping lacks something, go find a trustworthy
  public-domain source, verify it, and keep it, so the next asking is here at once.
- **The seal / receipt** — a content-addressed hash over the sealed record; re-fetchable, re-checkable.
- **The Gate** — the Ask/Seek/Knock discernment that surfaces the witness on the reader's own seeking.
- **Handicap** — golf-style operational health per subsystem (low is strong; 0 is scratch).
- **The fascia** — the connective tissue / recurring form: the polymathic connection as a design pattern
  that recurs at every scale.
- **Fractal / polymathic** — the same "everything connects" pattern from a card, to a domain, to a
  subsystem, to a surface.

---

## 17. For the reviewer (Sonnet)

Highest-value things to check:
1. **Honesty of claims** — every user-facing number should trace to `/capabilities` or a benchmark; the
   `.com` page is live-wired. Flag any prose number that could drift.
2. **The degraded frontier** — the ranker's substance-vs-headword blindness (Keeping) and the pull
   mis-selection (Find) are the real open engineering. Is the guarded behavior genuinely safe?
3. **The order / integration** — the subsystem graph is a *partial* (import-only) lens. Is the honest
   caveat (§5, §12) fair, or does "thin" hide a real disconnection the flow doesn't cover?
4. **Crisis safety** — the `_THEODICY`/`_BENIGN_MEASUREMENT` guards mute only the semantic backstop; the
   substring net is the floor. Confirm a combined cry ("…and i want to die") still fires.
5. **Surfacing project** — the built-but-unhosted features (Gateway page, theory grid, Floor, Bible
   atlas) are a deliberate pause, not a bug. Which deserve a door first?
6. **Sovereignty vs common language** — the rule (memory): sovereign for what's *ours* (engine, keys,
   data), but speak the *common tongue* (standard fonts, formats, protocols) from our own ground. Three
   secondary pages still call Google Fonts; the primary faces self-host.

Open questions worth a second mind: should `integration` fold into the handicap number? Should the
subsystem mesh move from a star toward a true peer-mesh (and where is that genuinely logical vs
forced)? Is the `.com`→rest-of-engine navigation too thin (a human on `.com` reaches checkit/live/
systems/map, but not bible/characters/read without going to `.org`)?

*— End of the world document. Re-verify any figure against `GET /capabilities`, `GET /systems`, and the
repo; this file is a snapshot, the engine is the truth.*
