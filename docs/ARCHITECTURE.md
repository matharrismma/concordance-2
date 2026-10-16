# ARCHITECTURE — the newcomer's map

For a software engineer arriving at Concordance 2.0 (Narrow Highway). The design journals in
`docs/` explain *why*; this page says *what is there and where*. Every count below was derived
from the source at commit `0954cdb` on 2026-10-16 and is dated so — when the code moves,
re-derive it. A stale number here is a lie to the reader.

Run it: `PYTHONPATH=src python -m concordance serve` (the secular face on `:8000`, API + site
same-origin), `--surface witness` for the witness face, `python -m concordance mcp` for the
agents' door over stdio (`src/concordance/__main__.py`). `python tools/benchmark.py` proves the
core claim in under a minute with no data.

## 1. The covenant

The engine makes **no model calls at runtime**. Nothing is generated: a claim is **found,
verified, cited, and sealed** — or refused in plain words (`CONTRIBUTING.md`; the doctrine is
typed in `src/concordance/kernel.py`). In code that means:

- **Three-state verdicts plus an honest error.** A verifier returns `CONFIRMED`, `MISMATCH`,
  `NOT_APPLICABLE` or `ERROR` (`verifiers/base.py`: `confirm` / `mismatch` / `na` / `error`).
  A derivation's composite is `HOLDS`, `BROKEN`, `INCOMPLETE` or `SYSTEM_ERROR`, with precedence
  `BROKEN > SYSTEM_ERROR > INCOMPLETE > HOLDS` (`derivation.py::verify_derivation`). The kernel's
  gate answers `REJECT | QUARANTINE | CONFIRMED` (`kernel.py::gate`).
- **An honest gap is NA, never a guess.** No applicable verifier → `NOT_APPLICABLE` → the composite
  is `INCOMPLETE`. A verifier that raises or times out → `ERROR` → `SYSTEM_ERROR`, which carries a
  `means` field saying the failure is ours, not the claim's. A `SYSTEM_ERROR` is sealed as
  `QUARANTINE`, never `REJECT` (`receipts.py::_VERDICT_TO_OVERALL`).
- **Tolerances only tighten.** A caller may narrow a verifier's window, never widen it
  (`base.py::clamp_tol`); a prose claim's window comes only from its own stated precision and a
  hedge word (`base.py::stated_window`).
- **Authority is monotonic.** `kernel.py` types every artifact into one of 6 `KINDS`, holds a
  three-step lattice `quarantined → cited → verified`, and lets only an evidenced, witnessed
  `gate` raise to `verified`; saving, citing, hashing, sealing, popularity and agent confidence
  never do (`NON_UPGRADING`). Imports and community content are born quarantined. The 8-rule
  `AGENT_COVENANT` the MCP greets agents with lives here too.
- **The floor is seven primitives** — claim, verifier, verdict, seal, ledger, ranker, surface
  (`README.md`; `docs/V2_DEFINITION.md` §1).

The moat: `python tools/benchmark.py` needs no data and exits non-zero on a single false positive.
Measured 2026-10-16: 60 cases (30 equality, 14 inequality, 16 derivative), 60/60 correct,
0 false positives, 0 false negatives. `docs/BENCHMARK.md` describes the set and its bounds. (The CI
step's label still reads "58/58"; the exit code is what gates, not the label.)

## 2. One engine, two faces

One codebase, one keeping, one process. The face is a config value, never a fork.

| | secular (`.com`) | witness (`.org`) |
|---|---|---|
| `EngineConfig.surface` (`config.py`) | `"secular"` | `"witness"` |
| what differs | the identity line (`branding.py`), the provenance layers (`layers.py`), and whether the witness verifiers are surfaced (`EngineConfig.witness_surfaced`) | the foundation named explicitly |
| what is shared | the verifiers, the seal path, the keeping (`corpus.search(include_witness=True)` on both), the full MCP catalog (102 tools listed on either face, `mcp/server.py::_tools_for`) | same |
| home page (`web/api.py::home_for`) | `/console.html` | `/console.html` |

The gate on the secular face is a voice, not a wall: `dispatch()` computes
`allow_witness = config.witness_surfaced or session_gate_open` (`web/api.py`), and
`mcp/server.py::_tools_for` applies the same line. Only `ask` can open it for a session, when the
classifier says so (`server.py::handle`); a caller cannot assert it.

Processes on the box (`deploy/*.service`, 2026-10-16):

- **`nh-engine.service`** — ONE process, `python -m concordance serve --surface both
  --witness-port 8001 --secular-port 8002` (`__main__.py` → `web/api.py::serve_many`): two
  listeners, one interpreter, one corpus.
- **`nh-mcp.service`** — the dedicated MCP host, a second engine process on `:8003`
  (`--surface secular --port 8003`), so a site restart never interrupts an agent mid-call
  (`docs/MCP_HOST.md`).
- **`nh-org.service` + `nh-com-2.service`** — the older two-process pair, kept as the rollback.
- **Caddy** (`deploy/Caddyfile`) terminates TLS: `narrowhighway.com`, `api.narrowhighway.com` and
  `narrowhighway.tv` → `:8002`; `narrowhighway.org` → `:8001`. Routing `/mcp` to `:8003` is a
  production Caddy change recorded in `docs/MCP_HOST.md`; the repo's Caddyfile does not carry it yet.

## 3. The verification path, step by step

A plain sentence enters; a verdict, a trail and a seal leave. One module per step:

| step | module | what happens |
|---|---|---|
| 1. front door | `audit.py::extract` | 68 deterministic regex extractors (64 named + 4 slot fillers in `_EXTRACTORS`, at 2026-10-16) turn prose into steps `{id, domain, spec, claim, extractor}`; deduped on `(domain, spec)`; capped at `MAX_CLAIMS = 40` over `MAX_TEXT = 20000` chars; memoized per text. A hedge word before a number sets `hedged: True` on the spec. |
| 2. routing | `domain_resolver.py::resolve_domain` | Model-free. The phrase→domain index is built once by `ast`-parsing `verifiers/*.py` (never importing them): registry aliases (weight 3), the curated `_SYNONYMS` table (3), `verify_*` / `check_*` function names (2), docstring words IDF-weighted (≤ 1), then decorrelated by domain frequency. Crisis text is checked first (`ask.is_crisis`) and never routed. A clear leader (score ≥ 2.5, lead ≥ 0.34) decides; a near-tie **asks** (`decision: None, ask: True`) with the candidates and the literal terms that matched; bare arithmetic falls back to its shape. 77 canonical domains at 2026-10-16. |
| 3. verifiers | `verifiers/__init__.py::run_for_domain` | `VERIFIERS` maps 189 domain names and aliases to 77 secular modules; `WITNESS_VERIFIERS` maps 8 names to 3 modules (`scripture`, `theology_doctrine`, `witness`), run only when `surface == "witness"`. Modules import lazily. Of the 93 `.py` files in `verifiers/`, 80 are domain verifiers and 13 are helpers (`base`, `spec`, `bridges`, `si_units`, `scale_base`, six `*_scale`, `_boolean`, `riemann_accel`). After the module, `spec.run_for_domain` runs the admitted spec-as-data checks. |
| 4. derivation | `derivation.py::verify_derivation` | Each step goes through `verify_step`: math → `verify_math` (the sympy modes); anything else → `verify_domain`, which calls `run_for_domain(..., surface="secular")`, so a witness verifier can never mint a `HOLDS`. Fail-closed: a raise, a timeout (`CONCORDANCE_VERIFY_TIMEOUT_S`, 8 s) or a saturated pool → `ERROR`. `uses` edges gate a step on confirmed ground; `bind` substitutes a confirmed prior output; cross-domain edges pass `verifiers/bridges.py`. Every step carries `spec_hash`, the SHA-256 of exactly what was checked. |
| 5. the seal | `receipts.py::attach → mint` | below. |

The seal path (`receipts.py`, `cas.py`, `ledger.py`):

1. `record_from_derivation` builds the canonical `WitnessRecord` (`record.py`); the claim text is
   passed through `redact.py` first, so PII never enters a permanent record.
2. `cas.store` content-addresses it: SHA-256 over canonical JSON (`validate.py`), written to
   `data/cas/<h[:2]>/<h[2:]>.json`, idempotent.
3. The receipt also becomes a card: `cas._mint_receipt_card` appends to `data/receipt_cards.jsonl`
   and inserts into the live corpus. `CONCORDANCE_SEAL_INDEX=0` (cold batch tools such as
   `tools/tick.py`) still writes the CAS object and the card file but skips the live insert.
4. `PASS` records only are appended to the ledger (`ledger.seal_to_ledger`): a hash chain in which
   each file's `prev_hash` is the prior file's `content_hash`, the tip read in O(1) from
   `.chain.head`, under a file lock so two sealers cannot fork it. `BROKEN` is sealed (proof of a
   falsehood is kept) but never chained.
5. The caller receives `seal: {content_hash, cite_url, ledgered}` with
   `cite_url = https://narrowhighway.org/s/<hash>` (`CONCORDANCE_PUBLIC_BASE` overrides). If minting
   fails, `seal: null` plus `seal_error` — never a receipt that cannot be re-fetched.

`engine.py::validate_and_seal` is the packet-level train (gates `RED · FLOOR · PATH · WITNESS ·
WAIT`) for structured packets; the prose and MCP `verify` path is `derivation` + `receipts` above.

## 4. The keeping: data vs code

The engine is code; the corpus is data and is **not committed**. `.gitignore` ignores `data/**`
and names back 39 tracked files at 2026-10-16: the spines, seeds and bridges, `domain_goldens.json`,
`frontdoor_claims.json`, `recall_phrasings.json`, and `crisis_semantic.json` (a committed model
asset, gate-tested like code).

| what | where | env |
|---|---|---|
| cards | `data/cards.jsonl` plus the extras `corpus.load_cards` lists (`receipt_cards`, `verified_cards`, `reference_cards`, the spines, the bridges, …) | `CONCORDANCE_DATA_DIR` (default `./data`) |
| seals | `data/cas/` | `CONCORDANCE_CAS_DIR` |
| the chain | `data/ledger/` + `.chain.head` | `CONCORDANCE_LEDGER_DIR` |
| Strong's | `data/strongs/` | `CONCORDANCE_STRONGS_DIR` |
| frozen shards (opt-in) | SQLite FTS5 files, one per tier (`corpus_db.py`) | `CONCORDANCE_CORPUS_SHARDS` or `CONCORDANCE_CORPUS_DB` |

Populating it: the 8 `tools/migrate_*.py` and 78 `tools/seed_*.py` scripts (counted 2026-10-16).
`migrate_bible.py`, `migrate_cards.py` and `migrate_strongs.py` read their source from
`CONCORDANCE_IMPORT_DIR`, so no personal path is baked into the repo. The other way is to `rsync` a
`data/` directory from a running instance (`CONTRIBUTING.md` §3). The source material is not all
public, so a fresh external clone cannot fully rebuild it today (issue #3).

Without the keeping: every verifier, the moat, the HTTP API, the MCP server and most of the suite
run; data-backed tests skip with a named reason (`tests/conftest.py`, the gated-module table).
With it: full-text search (`corpus.Corpus`, a distinctiveness-floored IDF ranker), the Coach,
Scripture at depth, the card graph. The ranker serves only what `corpus.is_public` allows and
withholds share-alike and non-commercial sources (`corpus._DISALLOWED_LICENSE`).

## 5. The five doors and the MCP

Every page, tool and route belongs to one verb — `CHECK · FIND · WALK · KEEP · WORD` — or is
plumbing (`doors.py`, from the audit in `docs/FIVE_DOORS_MAP.md`).

`src/concordance/tool_registry.py` is the **single source of truth** for tool routing: one
`ToolSpec(name, verb, kind, profile, capability)` per tool. `doors.py` derives `TOOL_VERB` and
`TOOL_KIND` from it; `mcp/server.py` derives `PROFILES` from it. Adding a tool is one registry
entry + its schema in `server._secular_tools` / `_witness_tools` + its handler branch in
`server._call_tool`; `tests/test_tool_dispatch_parity.py` checks the three agree.

From the registry at 2026-10-16: **102 tools** — 17 doors, 80 internals, 5 plumbing.

| verb | doors (`doors.TOOL_DOORS`) | door page (`doors.DOOR_PAGE`) |
|---|---|---|
| CHECK | `verify` · `audit` · `seal_fetch` · `find_verifier` | `/concordance.html` |
| FIND | `search` · `card_get` · `lookup` · `define` | `/explore.html` |
| WALK | `ask` · `discern` · `coach_next` | `/situations.html` |
| KEEP | `identity_create` · `study_create` · `decks` | `/profile.html` |
| WORD | `read_passage` · `word_study` · `cross_references` | `/bible.html` |

Profiles (mount one plane; `PROFILE_ORDER`): core 13 · library 22 · sovereign 14 · coach 10 ·
witness 17 · community 26. Capability classes (`server.EFFECTS`): read 60 · derive 18 ·
preserve 13 · publish 10 · external_action 1 (`calendar_create`). Every publish-class tool sits in
`community`, which the registry describes as off by default on a hosted box.

The server (`mcp/server.py`) is stdlib JSON-RPC 2.0. `handle()` is a pure function; `initialize`
returns `doors.welcome(surface)` as the client's instructions; `tools/list` is sorted doors-first
and every description is prefixed with its tag (`[CHECK · door]`); a tool called outside its
mounted profile is refused by name; business errors leave as typed MCP errors (`ERROR_CODES`);
and every door's answer gets the house ending (`doors.house`: a verdict or a card, the trail, a
seal, one next step). Transports: stdio (`python -m concordance mcp`) and Streamable HTTP
(`mcp/http.py`) behind `POST /mcp` and `/mcp/{core,library,sovereign,coach,witness,community}` in
`web/api.py`, with an exact-match Origin allowlist. The 16 web twins of the door tools are listed in
`doors.DOOR_ROUTES`.

## 6. Surfaces

- `home_for()` (`web/api.py`) sends `/` on both faces to `/console.html` when it exists — the
  Console: speak or type anything, read or hear the trail — falling back on the secular face to
  `concordance.html` then `com.html`, and otherwise to `index.html` (the .org desk).
- `site/` holds 50 `.html` pages at 2026-10-16, served same-origin by the stdlib server
  (`build_server`). The main ones: the five door pages above; `console.html`; `parable.html`;
  `books.html` and `reader.html` (the Reading Room); `connect.html` (the one page for agents);
  `about.html` and `proof.html`. `keep.html` and `steward.html` are operator surfaces
  (`docs/FIVE_DOORS_MAP.md`); `bridge.html` is the Bridge (`docs/COMPONENTS.md` §6).
- `ROUTES` is the route registry: 231 entries, of which 170 are API GET paths; `RATELIMITED`,
  `READ_LIMITED` and `_API_GET_PATHS` derive from it. `/s/<hash>` is the server-rendered, citable
  receipt page; `/seal?hash=` is the raw JSON.
- `_RETIRED` maps 39 old paths to their final home with a 301 that carries the query string
  (`_retire_to`); `MOVED_TO_ORG = {bible, read, encyclopedia}` sends those human pages from `.com`
  to `.org` (`redirect_for`).
- `site/theories.html` is **box-owned**: `tools/theory_map.py` rewrites it on the box every day
  (the `theorymap` step of `tools/hive_cycle.py`, fired by `nh-hive.timer` at 10:00 UTC).
  `verify_deploy.py` lists it under `BOX_OWNED`. Never deploy it from the repo.

## 7. Where things live

| path | what |
|---|---|
| `src/concordance/kernel.py` | the doctrine: five moves, kinds, the authority lattice, `gate()` |
| `src/concordance/doors.py`, `tool_registry.py` | the five verbs; the one tool registry |
| `src/concordance/audit.py`, `domain_resolver.py`, `derivation.py` | front door → routing → the moat |
| `src/concordance/verifiers/` | 93 files: 80 domain verifiers + 13 helpers; `base.py` is the contract |
| `src/concordance/receipts.py`, `cas.py`, `ledger.py`, `record.py`, `validate.py`, `signing.py` | the seal path — CI's integrity core |
| `src/concordance/corpus.py`, `corpus_db.py` | the keeping: ranker, shelves, shards |
| `src/concordance/ask.py`, `discern.py`, `coach.py`, `path.py` | the WALK door |
| `src/concordance/mcp/` | `server.py` (JSON-RPC, profiles), `http.py` (Streamable HTTP) |
| `src/concordance/web/api.py` | `dispatch`, `ROUTES`, `_RETIRED`, `home_for`, `serve` / `serve_many` |
| `site/` | the static faces |
| `tools/` | 224 entries: the local gate (`check.py`, `benchmark.py`), the box gate (`benchmarks.py`, `live_assay.py`, `frontdoor.py`, `recall.py`), the seeders, `deploy.sh`, `verify_deploy.py` |
| `tests/` | 401 `test_*.py` files; `MANIFEST.txt` pins the suite's wholeness |
| `deploy/` | the systemd units and timers, `Caddyfile`, `README.md` |
| `docs/` | the design journals; `GAPS.md`, `RUNBOOK.md`, `DEPLOY.md`, `MCP_HOST.md`, `SEAL_SPEC.md` |
| `data/` | the keeping (gitignored) + the 39 tracked spines, seeds and goldens |

## 8. The deploy ritual and CI

The box is not a git checkout; pushing deploys nothing. `sh tools/deploy.sh <repo-relative
files…>` does, in order:

1. snapshots the files it is about to replace into `/home/nh/deploy-rollback/<timestamp>` (the
   last 10 are kept);
2. one `tar | ssh` transfer of exactly the files named;
3. restarts `nh-engine` and polls `/health` on `:8001` and `:8002` (up to 90 s); if `nh-engine` is
   disabled it restarts `nh-org` first as the canary, then `nh-com-2`; then restarts `nh-mcp`
   (`:8003`), non-fatal;
4. the gate, on the box: `tools/benchmarks.py --gate`, `tools/live_assay.py`,
   `tools/frontdoor.py --gate`, `tools/recall.py --gate` — any regression reverts the snapshot and
   restarts (`DEPLOY_NO_GATE=1` skips it; emergencies only);
5. `tools/verify_deploy.py --soft` proves the box matches `HEAD` blob-for-blob (CRLF normalised)
   over `src/ tests/ tools/ conductor/ site/` plus `README.md`, `HANDOFF.md`, `pyproject.toml`;
   the one expected difference is the box-owned `site/theories.html`.

It never runs `git`, and it ships only the files you name — the keeping is populated on the box by
the seeders, not deployed. Secrets live in `/home/nh/concordance-2/.env` (gitignored;
`EnvironmentFile=` in every unit). Standing timers in `deploy/`: `nh-hive`, `nh-assay`,
`nh-benchmarks`, `nh-watch`, `nh-traffic`, `nh-zim`, `nh-storagebox`, `nh-restore-drill`.

CI (`.github/workflows/ci.yml`, every push and PR): Python 3.12 → `pip install -e
".[math,signing,schema,dev]"` → `tools/benchmark.py` (non-zero on any false positive) →
`coverage run -m pytest -q` → `coverage report` → a 75 % floor over the integrity core
(`cas`, `ledger`, `record`, `signing`, `validate`, `receipts`, `derivation`). Locally,
`PYTHONPATH=src python tools/check.py` must print `=== GATE PASS ===`.

## 9. Known gaps and the program

The gaps are tracked, not restated here: the umbrella issue
https://github.com/matharrismma/concordance-2/issues/8 (the review program's order and status) and
the whole-project review it came from, https://claude.ai/artifact/4dAos5bCUWEVRwTgojfGa4.
`docs/GAPS.md` holds the earlier measured gap list; issue #3 is the data-bootstrap gap named in §4.
