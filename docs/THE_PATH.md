# The Path — one source for each truth; everything on top is light

> *"We aren't copying new every time. The point is one core. Everything on top is light."* — Matt, 2026-11-01

Written 2026-11-01 from a measured survey of every repository linked to the project, then reviewed
claim by claim against the code and the live sites by an independent checker, whose findings this
version answers. It is the plan of record: each run below goes through [the harness](HARNESS.md) — a builder owns each step, a checker
grades it, the gates declare it done.

## The map

| Repository | Its one job | Its strongest aspect — keep and build on it |
|---|---|---|
| **concordance-2** (this repo) | **The keeping** and the experience engine: the cards, the ask path, the MCP, the `.com` site | The keeping (924,244 cards on 126 shelves, live `/cards/stats`, 2026-11-01) and the deterministic ask path; the deploy gates (snapshot, staggered restart, auto-revert, four on-box gates, drift check); the harness |
| **Concordance-V3** | **Verification**, as decided in the V3 split: claim in, verdict and receipt out — live for `.org` and `api.` | A receipt a stranger can check: canonical hash, Ed25519 COSE_Sign1, a Rekor entry (ML-DSA is built, not yet on live seals); a 1,796-case benchmark at 0 false positives and 0 false negatives; no required dependencies, and the engine degrades cleanly without its extras |
| **witness** | **The `.org` face**: the Console and the witness surfaces | A thin app (`nh_org`) with a tested import boundary: it loads no keeping and no verifier, and calls the engines over HTTP. The repository also carries `canon/` (see below) |
| **Lighthouse** | Integrated, not retired: its four designed pieces were rebuilt here; its repository has been idle since 2026-08-05 | Two things not yet carried: the head-to-head evaluation (a model alone against the same model with the tools) and the six domain canons as an engine-independent contract — their checks were already carried as verifiers |

Separate work, not this project: Econdev (a private client site), WorkReady (a product that should
call the cores, not copy them), and the books.

**The rule.** Each truth has exactly one source: the keeping in concordance-2, verification in V3.
Every face — the `.org` app, the `.com` site, the MCP door, the Console — is light: it loads
neither, and it calls the source.

## Where the project departs from the rule today (measured 2026-11-01)

1. **Receipts that no longer open.** concordance-2's public ledger holds 1,808 seals and its store
   3,154 records. Seals minted since 2026-08-01 cite `https://narrowhighway.org/s/<hash>`, and that
   path, like `api.narrowhighway.com/s/`, now goes to V3, which does not hold them: they answer
   404 there and 200 only on `.com`. (Up to 367 earlier seals cite `.com` and still open;
   professions issue a relative `/s/` link.) V3's own seals do the reverse. A citation is a promise.
2. **Two verification engines, live, with nothing checking they agree.** On `.org` and `api.` the
   verification doors go to V3, while `/ask`, the Console and everything else go to concordance-2;
   `.com` and the MCP door at `/mcp` verify in concordance-2 (V3 also answers its own MCP at
   `api.narrowhighway.com/v3/mcp`). Of the 91 files in `verifiers/` the two repos share, 75 differ.
   No parity test exists.
3. **Two scripture verifiers.** concordance-2's `verifiers/scripture.py`, and witness's `canon/`,
   registered as a V3 plugin but not installed live. `canon/` also carries a training pipeline for
   a "cite-only" model, which sits against *nothing generated*.
4. **A copy on top.** The MCP door runs as a second full engine beside the first.
5. **What lives only on the box.** 44 files under the served directories: 22 are excluded on purpose
   (the books, vendored model assets, a generated search index); 22 are engine modules, tools and the
   pages they build. The assembled live Caddyfile is untracked: V3 tracks its own routing snippet,
   and this repository's `deploy/Caddyfile` predates the `api.` routing. The witness app ships by
   a pull on the box, outside any gated script. And `tools/deploy.sh` sends the working copy, so a
   deploy from Windows lands CRLF.
6. **The documents disagree on which repository is the core** (`V3_BOUNDARY.md` here, V3's
   `docs/plans/V3_PLAN.md`, witness's `docs/ARCHITECTURE.md`), and several plans are stale.
7. **Smaller defects.** In V3, a second `_check_cases` in `tools/benchmark.py` shadows the first, so
   115 golden pairs (230 cases) never run; live `trust` reads keys `deploy/install.sh` never writes.
   In witness, the `/find` pass-through also catches `/find_verifier`, which V3 does not serve.
8. **One name, claimed twice.** Both repos declare a Python package named `concordance` and an MCP
   registry name `io.github.matharrismma/concordance`; concordance-2's `server.json` points at a
   repository that does not exist; a third-party server named "Concordance" is proposed upstream in
   an open pull request.

## Decisions that are Matt's — the runs that depend on them wait for them

- **Retire concordance-2's verifier copies** once the parity run passes, so verification has one
  source. (Recommended: V3 carries the stronger receipt and the larger benchmark.) Gates run 5.
- **One name and one license.** concordance-2 is AGPL-3.0-or-later and V3 is MIT, and both declare
  the package `concordance`; concordance-2 cannot import V3 in-process until that is settled. Gates
  runs 5 and 9.
- **`canon/`'s model pipeline**: keep it out of the project, or say how it stays outside *nothing
  generated*. And which scripture verifier is the one. Gates run 5.
- **Merge the V3 Rust re-checker** after review: an independent, second-language check of the receipt.
- **Close Lighthouse** once its two pieces are carried (run 8).
- **The stale `awesome-mcp-servers` fork**: thousands of commits behind, no pull request. Delete it
  and list the server from a fresh fork once the name is settled.
- **Version control for WorkReady**, which has none.

## The runs, in order

Each is one harness run with its own checked plan. Nothing is cut before it is measured, and nothing
is rewired while something the gates cannot see still depends on it. A run in witness or V3 uses
the same harness, pointed at that repository (`HARNESS_ROOT=<repo> python tools/harness.py …`); its
plan first measures that repository's baseline (witness measured green on 2026-11-01: 43 passed,
0 failed, and 6 skipped that need the live core) and names its ship path.

1. **Every receipt opens again where it is cited.** In the `.org` app, a seal V3 does not hold is
   asked of the keeping's engine, and the `/find` pass-through is made exact. The witness app gets
   a gated ship path of its own — scripted, verified, rolling back on failure — and the runbook names
   it beside `tools/deploy.sh`. Done when each answers 200 at the address it cites: a concordance-2
   seal minted after August (on `.org`), one minted before (on `.com`), a V3 seal, and a profession
   (on both `.org` and `.com`, since its link is relative).
2. **Nothing lives only on the box.** The 22 box-only modules, tools and pages come into this
   repository, reviewed, or are retired by name; the assembled Caddy and unit configuration is
   tracked in `deploy/` with a gated ship path; deploys send committed files, not the working copy.
   Then, if anything still cites `api.narrowhighway.com/s/`, the same fallback is added there.
3. **V3 keeps its own word.** First, V3's ship path is named in the runbook beside `tools/deploy.sh`:
   its `deploy/install.sh` already gates and rolls back, and the lead runs it through one scripted,
   verified call, never by hand. Then its shadowed goldens run; live `trust` reads what is written;
   its documents agree with production (signing, Rekor, case counts, license); the Rust re-checker
   is reviewed and, on Matt's word, merged, with a CI job.
4. **Measure the two verifiers against each other.** A parity test runs both engines over V3's whole
   benchmark — goldens included — and this repository's goldens, and names every disagreement.
5. **One verification core** — after decisions on the name, the license and the scripture verifier.
   What only concordance-2 verifies moves into V3: the exact certificates (`certificate.py`) and the
   witness checks (`scripture.py`'s `run()`, `theology_doctrine.py`, `witness.py`) as one plugin,
   reconciled with `canon/`, whose own tests (`canon/tests/`) come under the gate. The Bible reader inside `scripture.py` stays in the keeping, split from
   the check. The callers are listed mechanically — every module whose import closure reaches the
   verifiers or `derivation`, as V3 lists its own core — and each calls V3. The keeping records each
   V3 receipt as a pointer (its hash and V3's citation), never a copy, and its integrity check
   verifies against V3. The verifier copies retire last, and run 1's sample is checked again.
6. **The MCP door becomes light.** It answers from the one engine instead of a second copy; the
   seconds of an engine restart are covered by a retry at the joint, not by a duplicate.
7. **One architecture, written once.** A single map of the boundary, in each repository's terms,
   replacing the documents that disagree.
8. **Lighthouse is carried, then closed.** The head-to-head evaluation comes in as a measurement
   (its model calls stay out of the runtime and out of V3's core), with its uncommitted results; the
   six canons come in as a contract; the daily job that still writes into its checkout moves here;
   its open pull request and issue are resolved. Then the repository is archived read-only.
9. **Be found.** Publish V3 under the settled name to PyPI and the MCP registry, fix both
   `server.json` files, and list the server where agents look.

## What stays true throughout

0 false positives; a miss stays a miss; nothing generated — found, verified, cited, sealed. A
citation, once issued, keeps opening. The harness grades every change, and only machines declare a
run done.
