# Narrow Highway — The World Document

*A comprehensive, grounded reference to the whole project: **what we have, and where it lives.** Core
figures re-verified on **2026-09-28** against the live engine (`GET /capabilities`), the repo, and the box;
the site/Atlas detail carries its **2026-09-20** verification unless noted. Where a figure can drift, its
live source is named so it can be re-checked rather than trusted.*

Repo: `concordance-2/` · GitHub: **github.com/matharrismma/concordance-2** (public) · Live:
**narrowhighway.com** (reach) · **narrowhighway.org** (witness) · **narrowhighway.tv** (museum) · Box:
`nh@5.78.186.55` · Deploy: `sh tools/deploy.sh <files>` (box == repo, no git on the box).

The single most authoritative always-live source of "what this is and how much of it exists" is
**`GET /capabilities`** — every number there carries a `means` line. When this document and `/capabilities`
disagree, `/capabilities` wins.

---

## 0. What it is (in one breath)

A sovereign, **deterministic model of reality** — a verification + finding + citation engine. Bring a
claim and it returns a **verdict**, the **worked reasoning (trail)**, and a **permanent, re-checkable
receipt (seal)**. No model in the loop; nothing generated. It *finds and verifies* — a **conduit, not the
source**. Identity defined once in [`src/concordance/branding.py`](../src/concordance/branding.py)
(`IDENTITY_LINE`). It serves families first — free, no account, works offline — and it ultimately serves
Jesus Christ, naming the foundation plainly on the witness face.

---

## 1. WHERE EVERYTHING LIVES  (the system check)

The project is not one place. It is **five locations**, each with a distinct job. This is the map of the
whole territory.

### 1a. GitHub — the source of truth for the code
- **`github.com/matharrismma/concordance-2`** — **public**, default branch `master`, HEAD current on
  GitHub (last push **2026-09-28**). ~**9 MB** on GitHub (code only; the large corpus/data are gitignored;
  small curated seeds like the religions atlas are tracked).
- Commit + push are **explicit, human-reviewed** actions (never `add -A`; co-author trailer). Deploy is
  separate from git.

### 1b. The local working repo — where the work is done
- **`C:\Users\hdven\OneDrive\Documents\Claude\Projects\concordance-2`** — **3.6 GB** total:
  `src` 7.9 M · `tools` 2.8 M · `site` 100 M (incl. self-hosted fonts) · `tests` 8.5 M · `docs` 888 K ·
  **`data` 3.1 G (gitignored corpus/artifacts)** · `.git` 273 M.
- The seeders here are the **source of truth** for the Atlas/calc/theory/bridge data; `data/*.jsonl` is
  generated and gitignored. **Never run `card_theories.py`.**

### 1c. The box — production
- **`nh@5.78.186.55:/home/nh/concordance-2`** — **no git**; **box == repo** verified file-for-file at the
  end of every deploy (236 src modules match, 2026-09-28).
- **Two service processes** (both hold the corpus in RAM, reload on restart): `nh-org` (:8001, witness) +
  `nh-com-2` (:8002, secular), fronted by **`caddy`**. All three **active**.
- Health (2026-09-20): disk **25 GB / 75 GB (35%)**, RAM **4.3 GB / 7.6 GB** used, box `data` **3.7 GB**.
- Deploy = one tar-over-ssh transfer + **staggered restart** (witness back to 200 *before* secular is
  touched) + patient health polling + a rollback snapshot under `/home/nh/deploy-rollback/`.

### 1d. The live sites — the three faces, public
- **narrowhighway.com** (reach/secular), **narrowhighway.org** (witness), **narrowhighway.tv** (museum) —
  all public since 2026-09-15. The whole journey is live: the shared **spine** on every page, the **Atlas**
  centerpiece, **The Crossing**, the **reach → witness → museum** road with a **reciprocal loop** from
  every face, and the **"for you and your family"** doors.

### 1e. The external drive `D:\` — the media / corpus backbone
A Seagate (~11 TB, 434 GB used). This holds the **heavy content that does not belong in the repo** — the
museum's media, the raw sources, the offline releases, and the backups.

| On `D:\` | Size | What it is |
|---|---|---|
| **`library_files`** | **343.7 GB** (19,694 files) | The `.tv` museum's public-domain media — animation (Clutch Cargo, Fleischer Color Classics, Herman & Katnip, Little Lulu), historical film, board-game books, pilots, channel assets. The broadcast corpus. |
| `NarrowHighway-Backups` | 58.3 GB | Rolling backups. |
| `nh-backup` | 8.7 GB | Backup set. |
| `NarrowHighway-Sources` | 2.65 GB | Raw source downloads before carding — `archive_org`, `gutenberg`, `8f`. |
| `NarrowHighway-Releases` | 1.06 GB | The offline **field-library bundles** (`current`, `field-library`, `field-pack`, `first`, `previous`, `staging`) — self-verifying, each carries a MANIFEST seal. Written by `tools/export_commons_bundle.py`. |
| `NarrowHighway-1.0-backup` | 1.36 GB | The archived 1.0. |
| `NarrowHighway` | 320 MB | A synced repo copy (`concordance-2` + `MANIFEST.sha256` + `RUN-ME.md`). |
| `NarrowHighway-Origins` | 254 MB | `iCloud-work-snapshot-2026-07-23` — the origins. |
| `NarrowHighway-2.0-backup` | 141 MB | A 2.0 snapshot. |

> **The whole picture:** GitHub + local repo carry the **~9 MB of code**; the box **runs** it and holds the
> **~3.7 GB corpus in RAM**; the external drive holds the **~340 GB of media + backups + sources** that the
> museum and the offline bundles draw on. The engine is small; the keeping is large; the media is largest.

---

## 2. The Laws (kernel, covenant, boundaries)

**The five-part kernel** (`GET /kernel`; [`kernel.py`](../src/concordance/kernel.py)):
**find · distinguish · verify · preserve the trail · never silently upgrade authority.**

**The eight-rule agent covenant** (`/llms.txt`, `GET /identity`): retrieve from corpora first · distinguish
citation from proof · quarantine generated material · request human authorization before writes · produce a
receipt for consequential actions · carry provenance through every transformation · respect local data and
identity boundaries · stop when evidence is incomplete.

**Boundaries (enforced):** nothing is generated (three honest states `HOLDS` / `BROKEN` / `INCOMPLETE`;
`SYSTEM_ERROR` = *ours*, never a refutation) · no account/login/tracking · writes require an **Ed25519
signature**, not a session · **public-domain only** for others' text (edition/translation pre-1929, or a US
federal work under 17 USC 105) · **crisis-safe** (a cry is met first) · **points beyond itself to Christ.**

**The mechanism** (Matt's endorsed frame): **IMMUTABLE CORE → VALIDATION BOUNDARY → CONFIGURABLE SURFACE.**
The model of reality and the keeping do not bend to the question; every claim is checked at the boundary
before it crosses; the surface speaks your words but hands you only what passed. Anchored to an external
reference, so it cannot drift or be captured.

---

## 3. Architecture (the flow, the surfaces, the topology)

**The flow a request takes** (front door [`ask.py`](../src/concordance/ask.py) `respond()`, `POST /ask`):

```
Ask · Seek · Knock  →  Discern (crisis-first, then the kind)  →  Verify | Find  →  Seal
```

- **Discern:** `ask.py` + `discern.py` + `clarify.py` + `path.py` (the answer is a *path*) + `router.py`.
- **Verify:** `engine.py` (`validate_and_seal`) over the domain verifiers.
- **Find (the Tortoise):** `find.py` navigates a kept canon (`field_canon.py`) by elimination, then pulls
  and cards a public-domain source (`expand.py`, `providers.py`).
- **Seal:** `receipts.py` — a content-addressed hash, addressable at `GET /s/<hash>` + `GET /seal`.

**Topology:** the body is a **star** — `ask` is the hub; `keeping` and `verify` are the roots. Legible on
the live `map.html` constellation; the parts mesh peer-to-peer where logical (the polymathic/fractal
pattern), not only through the hub.

---

## 4. The Three Surfaces, the Spine, and the Journey

One engine; the surface is chosen by host and carried as `EngineConfig(surface)`. `home_for()` in
[`web/api.py`](../src/concordance/web/api.py) serves a different landing per surface.

- **`.com` — the reach (secular).** `/` = [`concordance.html`](../site/concordance.html): "a guide to what
  is true" — the discern-anything box over the live engine (the flip landed 2026-09-21, `home_for`). The
  manifesto/breadth page [`com.html`](../site/com.html) — the live "check a claim" instrument, the domain
  breadth, the receipt, the API/agent door — sits behind it at `/com.html`; numbers **live-wired** from
  `/capabilities`. The **Atlas** (§5) is embedded as the centerpiece.
- **`.org` — the witness.** `/` = [`index.html`](../site/index.html) (the cream "book"): *"Christ is the
  center. The Word is the foundation."* — Scripture in the original Hebrew/Greek, pointing past itself to
  Jesus.
- **`.tv` — the museum.** Curated public-domain channels + the kept library, drawing on `D:\library_files`.

**The spine** ([`site/shell.js`](../site/shell.js), 2026-09): one shared header on **all ~47 pages** —
wordmark, canonical nav, the **reach / witness / museum** switcher, theme toggle, responsive menu. Self-
contained, non-drifting; every page-generator template now carries the include so a regen can't drop it. It
also renders the **reciprocal road** into any `<div data-nh-road>` — the reach → witness → museum loop,
framed by the face you're on, so the journey **circles** instead of ending.

**The journey (the landing arc):** proof → **for your app/agent** (the API) → **for you and your family**
(the human doors: Coach, Situations, the Halls) → **the reach → witness → museum road.** Each face receives
the arriving traveler and sends them on: `.org` says *"You've found the foundation,"* `.tv` says *"You're in
the kept library,"* `.com` says *"You've seen it hold."*

**Site pages:** 46 HTML in [`site/`](../site/) + shared JS. The doors — the desk (`index.html`), the reach
(`com.html`), the checker (`checkit.html`), Scripture (`bible.html`), dictionary (`characters.html`),
reading (`read.html`), wisdom (`wisdom.html`), the halls (`halls.html`), coach (`coach.html`), daily walk
(`plow.html`), situations (`situations.html`), workshop (`workshop.html`), provision (`provision.html`),
the guild instruments (`golf.html`, `grappling.html`, `music.html`), the systems dashboard
(`systems.html`), the map of everything (`map.html`), the Gateway (`gateway.html`), and the whole **Atlas
suite** (§5). Shared JS: `shell.js` (the spine), `nh-tools.js` (Ctrl-K palette), `nh-search.js`, `graph.js`
(constellation), `redact.js` (client-side privacy gateway).

---

## 5. The Atlas — the concordance-of-reality's math (the .com centerpiece)

The Atlas is Narrow Highway's demonstration: the finite math kernel under every science, drawn as one body,
pointing past itself to the Designer. Generator: [`tools/atlas_explore.py`](../tools/atlas_explore.py) →
[`site/explore.html`](../site/explore.html), embedded on the landing. Seeders are the source of truth
([`seed_bridges.py`](../tools/seed_bridges.py), [`seed_calculations.py`](../tools/seed_calculations.py),
[`seed_strategy.py`](../tools/seed_strategy.py)).

- **30 master equations** — the finite set of couplings that genuinely connect across domains, in **four
  families** (recorded in `seed_bridges.py` `MASTER_FAMILY`, exhaustive by construction): **Continuous 23**
  (how things change), **Discrete 5** (combine exactly), **Measure 1** (take up space), **Inference 1**
  (weigh a belief). Colored by family across all views; grouped and named in the panel.
- **408 calculations** across **39 leaf forms** (a fractal calc map — `calculations.html`), each placed by
  its canonical form, joined to the theory it rests on, and bridged to the same computation in other fields.
- **217 theories** — the **Floor** (`theories.html`): every theory the sciences run on, joined by what it
  rests on / limits it / shares its form.
- **Seven live views** (`explore.html`, one persistent selection): kernel · form wheel · one body · spiral ·
  domains · bridges · **strategy** (the same method turned on history — patterns × arenas × cases).
- **The Crossing** (`crossing.html`): geometry is the doorway (`measure ~ length^d`, a narrow crosser — 4
  domains); the **logarithm** is the actual widest-crossing form (**13** verified domains, function =
  multiplicative → additive), the very form that closed the Atlas's last homological void (the Prime Number
  Theorem, `π(x) ~ x/ln x`). Closes at the **Macedonian cross** (Acts 16:9, διαβαίνω, "to cross over").
- **Related surfaces:** `torus.html` (the (domain × form) shape), `bridges.html`, `one_body.html`,
  `spiral.html`, `domains.html`, `completeness.html`, `strategy.html`. All generated; all carry the spine.

Intrinsic shape (measured, not asserted): after merging dual forms and closing the primes↔log seam, the
honest signature is a **ring** — nothing central, nothing peripheral, one connected body.

---

## 6. Verification (the moat)

- **Engine:** [`engine.py`](../src/concordance/engine.py) `validate_and_seal(packet)` — governance → gate →
  domain validation → seal. Gates in `gates.py`; candidate engine in `candidates.py`.
- **Domains (live `/capabilities` → `verifiers`):** **72 distinct verifier modules** (69 secular + 3
  witness — theology/doctrine, scripture, witness); **74 files on disk**; **153 domain names accepted**
  (aliases — NOT a capability count). Registry `verifiers/__init__.py`. Each check returns `CONFIRMED` /
  `MISMATCH` / `NOT_APPLICABLE` with a worked trail.
- **The seal:** spec [`docs/SEAL_SPEC.md`](SEAL_SPEC.md); independent checker
  [`tools/verify_seal.py`](../tools/verify_seal.py) (~60 lines, stdlib only). Anyone re-checks without
  trusting us.
- **The benchmark:** [`docs/BENCHMARK.md`](BENCHMARK.md) — "0 false positives" is **always** bounded to the
  published, versioned cases.

---

## 7. The Keeping / Corpus

- **Size (live `/capabilities` → `substrate`, 2026-09-28):** **872,178 cards** — **11,235 substance** (body
  ≥ 120 chars), **262 stubs** (stub_ratio 0.023); the remainder frozen on shards (body not resident, judged
  from the shard FTS). The base is the Bible; every kept card is a gradient step (*the keeping is the model*).
- **Store:** [`corpus.py`](../src/concordance/corpus.py) (resident cards, TF-IDF + subject-tier partition)
  + [`corpus_db.py`](../src/concordance/corpus_db.py) (SQLite FTS shards). **Lazy RAM (2026-09-26):** frozen
  shelves ride the shards and their full text is **no longer indexed resident** (the token index was
  measured ~69% of resident RAM); search pulls frozen hits from the shard FTS and re-scores them through the
  *same* ranker (rank-neutral), and their document frequencies ride in `_df_extra` so corpus-wide IDF is
  unchanged. `SHARD_ASSIGN` routes each shelf to a shard — the logistics / load-balancing layer (freeze /
  unfreeze / rebalance). Production keep is **appended** to the box's `data/`.
- **Reference section (the wisdom engine's substance):** the dictionary **+ thesaurus** (WordNet; `GET
  /thesaurus` and the offline `thesaurus.py`, which also sharpens `/search` recall), the **OpenStax** open
  textbooks (CC-BY — mathematics/physics/chemistry/biology/…; `tools/card_openstax.py`), the **tree-of-life
  backbone** (recognizable taxa; `tools/card_taxonomy.py`), plus the field library. **License gate: PD +
  CC0 + CC-BY** (attribution kept on each card); **CC-BY-SA + NC withheld** (`corpus._DISALLOWED_LICENSE`).
- **The connection graph:** [`graph.py`](../src/concordance/graph.py) → `GET /graph` — everything connects,
  0 isolated. Rendered by `site/graph.js` on `site/map.html`.
- **Scripture substrate:** **97 harmony events**, **100 timeline events** (11 disputed, carrying both
  positions).
- **Growth:** the corpus *always grows*; every cleaning batch net-grows it.

### 7.1 The self-organization layer (collective intelligence, measured — 2026-09-28)

Coordination modeled on the measured superorganisms — decentralized local rules → a coherent whole, ordered
to the Head, **never a runtime LLM swarm** (cards `card_ci_*`; ants→keeping, bees→conductor, birds→mesh,
orcas→witness). Each lever is gated by a `CONCORDANCE_<X>` flag (inert when off → byte-for-byte unchanged),
built + tested, and enabled per node. **All seven signalling/regulation levers are ON in production; the
learned repellent is retired.**

| Lever | Nature | Module | Flag | State |
|---|---|---|---|---|
| **stigmergy** (ants) | recall pheromone — travelled trails lead within tier; ONE shared store, merge-on-flush under a cross-process lock (no lost deposits) | `stigmergy.py` + `corpus._finalize` | `STIGMERGY` | on |
| **quorum** (bees / Deut 19:15) | counts distinct independent witnesses on the lead's subject — "established" vs "a single witness" | `quorum.py` → `out["quorum"]` | `QUORUM` | on |
| **flock** (starlings / BOIDS) | a node's topological neighbourhood (fixed ~7 most-woven) on the fellowship map | `flock.py` + `mesh.map_around` | `FLOCK` | on |
| **eldership** (orcas / matriarch) | weights witnesses by endurance — a PD-by-age or canonical source is an elder | `eldership.py` → `out["eldership"]` | `ELDERSHIP` | on |
| **physiology** (the body) | division of labor + homeostasis over the faces — engage the caste with capacity, re-allocate when one is out, damp the busy; the governor the amplifiers lacked | `physiology.py` + `faces.route` | `ALLOCATION` | on |
| **inhibition** (bee stop signal) | names the strongest competing answer (different subject) the lead was committed over — the elimination made visible | `inhibition.py` → `out["inhibition"]` | `INHIBITION` | on |
| **repellent** (Pharaoh-ant no-entry) | learned negative trail — **retired**, superseded by the alignment gate | `repellent.py` | `REPELLENT` | off |

Quarantine / social immunity was already built: `moderation.py` (signed report → 3-reporter HOLD →
human-steward restore/remove) + `is_public` withholds `quarantine`/`retracted`.

**Teaching ≡ training — the training loop** ([`docs/TRAINING_LOOP.md`](TRAINING_LOOP.md); `training.py`,
`CONCORDANCE_TRAINING`, off): there is no train/infer wall — one OPERATE cycle (SELECT a gap by demand →
READ → FIND → VERIFY/GATE → BIND → REINFORCE → CLOSE) both serves and grows the keeping, the same act by
which the engine teaches (the Cubo way). Pure orchestration over the proven acquire paths
(`expand.pull_and_card` for PD, `byom.ingest` for a user's model); mints nothing itself, so every write
guard holds. `run(steps=N)` on a cadence = continuous training driven by demand — the corpus grows by
being used.

### 7.2 The alignment gate — tier the keeping by agreement (`alignment.py`, `ALIGNMENT`, on — 2026-09-28)

Matt's directive: *"section off occult for only call on explicit … much of the philosophy and other
religions should be able to be referenced, but not fully integrated as the more aligned material."* Read
from the discernment atlas (each chart carries `discerns_terms` + an `alignment` tier), every card is tiered
and gated in `corpus.search`:
- **ALIGNED** — Scripture, the fathers, science, math, the reference section, everything else — **and the
  discernment charts themselves** (never gated): fully integrated.
- **REFERENCE** — other religions + philosophy (worldviews not held in agreement): referenceable,
  **down-weighted ×0.6** unless the query names the subject.
- **SECTIONED** — the occult (Gateway process, Theosophy/spiritualism): **explicit-only** — withheld from a
  result set unless the query names it; never deleted, always beside the chart that tests it.

**19 subjects tiered** (2 occult sectioned, 17 reference), from distinctive worldview markers only — every
word shared with the faith (logos, resurrection, judgment, "the way") deliberately excluded so aligned
content is never touched. Off → `(keep, 1.0)` for all → byte-for-byte unchanged. Verified live: a paraphrase
that does not name the occult returns Scripture; naming it surfaces it beside its discernment.

### 7.3 The gradient manifold (the structure, one form across the planes)

The whole is one recurring form — energy (Matt's Universal Gradient Manifold, carded as
`card_doctrine_reservoir_manifold`), biology (ATP as the common interface), and this software: the **CARD**
is the common interface, the **KEEPING** the reservoir, the **KERNEL/gate** the manifold, the **faces +
verifiers** the converters, and the **models are FUEL** — the manifold endures while the fuels evolve
(*a model of reality, not an LLM*). Source → Gradient → Reservoir → Manifold → Converter → Work.

---

## 8. The API

- **Router:** [`web/api.py`](../src/concordance/web/api.py) — a stdlib `http.server`; `ROUTES` ↔
  `dispatch()` are bidirectionally test-locked. **204 registered routes, 144 JSON GET paths, 79
  rate-limited** (live `/capabilities` → `routes`, 2026-09-28). Includes the expert-faces door
  (`GET /faces`, `POST /face`), the gated `POST /byom`, and the shelf `POST /place`.
- **Start here:** `POST /audit` ({text} → sealed report), `POST /verify` (structured), `POST /ask` (front
  door), `GET /search`, `/card`, `/graph`, `/capabilities`, `/systems`, `/kernel`, `/identity`, `/health`,
  `/s/<hash>` (receipt).
- **CORS open on every response** — any browser app or agent can call read/verify with no key (safe: no
  ambient credential; writes still need a signature). **Rate limits:** 600 reads/min, 120 writes/min.
- **Privacy gateway:** [`gateway.py`](../src/concordance/gateway.py) + `site/redact.js` — "private in,
  verified out." Doc: [`docs/GATEWAY.md`](GATEWAY.md).

---

## 9. The MCP (agent interface)

- **Server:** [`mcp/server.py`](../src/concordance/mcp/server.py) (JSON-RPC) + `mcp/http.py` (Streamable
  HTTP). Mounted at `POST /mcp` and six profile planes.
- **Catalog: 95 tools across 6 profiles** — `core, library, sovereign, coach, witness, community` (every
  tool in exactly one; community off unless the host enables it).
- **Install:** `claude mcp add --transport http narrow-highway https://narrowhighway.com/mcp`. Sovereign:
  `python -m concordance mcp`. Agent card: **`/llms.txt`**.

---

## 10. Identity / Gate / Crisis

- **Keys:** Ed25519, born on the device, derived from four covenant verses (`covenant.py`); the server
  stores only public keys. No account, no password, no recovery backdoor.
- **The Gate:** the Ask/Seek/Knock discernment; witness content surfaces on `.com` once the reader's own
  seeking opens it (`nh_gate`, same-origin). Same content on both faces; the difference is *voice*.
- **Crisis:** `ask.is_crisis` = a substring matcher UNION a deterministic semantic backstop
  (`crisis_semantic.py`), recall + benign-precision test-pinned. Guards (`_THEODICY`, `_BENIGN_MEASUREMENT`)
  mute only the backstop; the substring net is the floor. Real help first — never a helpline alone.

---

## 11. Operations

- **Deploy:** `sh tools/deploy.sh <files>` — staggered restart, rollback snapshots, **box == repo** verified
  file-for-file. Deliberately does **not** touch git.
- **Tests:** **252 `test_*.py`** ([`tests/`](../tests/)); `test_routes` locks the API surface. Crisis tests
  run alone (documented global-cache race). **Watchman** discipline: tests prove code, e2e proves the
  library — CANNOT_CHECK ≠ pass. Verify runtime, not HTTP 200.
- **Docs:** **49 `.md`** in [`docs/`](.) + `docs/SOP/subsystems/` per-subsystem procedures.
- **Git discipline:** commit by exact paths, human-reviewed; co-author trailer; deploy separate from commit.

---

## 12. Current State (2026-09-28)

**Live and healthy.** All services active; box == repo verified file-for-file each deploy.

**Recently shipped (the self-organization arc, 2026-09-27 → 28):**
- **The collective-intelligence layer (§7.1):** seven measured levers — stigmergy, quorum, flock,
  eldership, physiology, inhibition (repellent retired) — each gated, tested, deployed inert, then enabled
  per node. Stigmergy's cross-process trail race fixed (merge-on-flush under a shared lock; proven with a
  4-process test). Cards `card_ci_*` chart the mechanisms + the Head + the gradient manifold.
- **The alignment gate (§7.2):** the keeping tiered by agreement — occult explicit-only, other
  religions/philosophy referenceable/down-weighted, everything aligned else; 19 subjects tiered from the
  discernment atlas, gated and enabled.
- **The gradient-manifold frame (§7.3):** Matt's UGM recognized as the project's structure — card = ATP,
  keeping = reservoir, kernel = manifold, models = fuel.

**Earlier (the site-experience arc, 2026-09-20):**
- **Phase 1 — the spine:** one `shell.js` header across all ~47 pages; every viz generator's template
  fixed so a regen keeps it (drift closed).
- **Phase 2 — the four families** made visible on the Atlas (Continuous 23 / Discrete 5 / Measure 1 /
  Inference 1), generated from the seeder.
- **The Crossing** rebuilt on the actual form (the logarithm, 13 verified domains), the pivot drawn from
  the real function, closing at the Macedonian cross.
- **Phase 3 — the reach → witness → museum road;** **Phase 4 — "for you and your family"** human doors;
  **the reciprocal loop** so the journey circles from any face.
- **Housekeeping:** stale `calculations.html` / `theories.html` refreshed to current seed data.

**Open, tracked (not bugs to auto-fix):**
- The two **degraded** frontiers: **Find/the Tortoise** (pull can mis-select; guarded) and **the
  Keeping/ranker** (blind to substance vs headword).
- Verifier domain coverage; OT→NT prophecy sweep; founders gather; off-site backup durability.
- The **deferred multi-master form-splits** — must NOT move the PNT off the `logarithmic` stud (would
  re-open the closed void).
- The **memory-index file-merge** (a housekeeping pass, not blocking).

**Governing principle for all of the above:** *we don't force — we show what is there.* Add only structure
that genuinely belongs; verify a claim's reach before building on it (**form follows function**).

---

## 13. Glossary

- **The keeping** — the corpus; the substrate that *is* the model.
- **The Tortoise** — find/fetch fallback: when the keeping lacks something, go find a trustworthy PD source,
  verify it, keep it.
- **The seal / receipt** — a content-addressed hash over the sealed record; re-fetchable, re-checkable.
- **The Atlas** — the finite master-equation kernel drawn as one body; the .com math-first demonstration.
- **The four families** — the four kinds of master coupling (continuous, discrete, measure, inference).
- **The Crossing** — the form that crosses domain boundaries (the logarithm); the .org witness-twin is the
  Macedonian call (διαβαίνω).
- **The spine** — `shell.js`; the one shared header/journey component on every page.
- **The fractal / polymathic** — the "everything connects" pattern from a card, to a domain, to a
  subsystem, to a surface.
- **The levers / self-organization** — the seven gated collective-intelligence mechanisms (§7.1) modeled on
  ants/bees/birds/orcas + the body's physiology; decentralized, ordered to the Head, no runtime LLM swarm.
- **The alignment gate** — tiering the keeping by agreement (§7.2): aligned / reference / sectioned; the
  occult is explicit-only, "front door must discern" made structural.
- **The gradient manifold** — the project's structure (§7.3): the card is the common interface (ATP), the
  keeping the reservoir, the kernel the manifold, the models mere fuel; one form across energy/biology/software.

*— End. Re-verify any figure against `GET /capabilities`, `GET /systems`, the repo, and the drive; this
file is a snapshot, the engine is the truth.*
