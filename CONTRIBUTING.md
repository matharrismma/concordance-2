# Contributing to Concordance (Narrow Highway)

A deterministic **model of reality**: a verification engine that makes no model calls at runtime.
Nothing is generated — a claim is **found, verified, cited, and sealed**, or it is honestly refused.
That covenant is the whole product, so the contributing rules below exist to protect it.

> **First thing to run:** `python tools/benchmark.py`. It is the moat — it needs **no data**, and it
> exits non-zero on a single false positive. If it prints a clean pass, you have seen the core claim
> of this project proven on your own machine in under a minute.

---

## 1. Setup

Requires **Python ≥ 3.10** (CI runs 3.12). From a fresh clone:

```bash
python -m pip install -e ".[math,signing,schema,dev]"
```

The one further optional extra is `pdf` (robust PDF intake); the server itself is pure stdlib —
`python -m concordance serve` needs no web framework. The engine is **stdlib-first**: without the `math`/`signing`/`schema`
extras it still runs, with sovereign fallbacks (truth-table logic instead of sympy, a structural
packet validator instead of jsonschema, unsigned seals instead of Ed25519).

## 2. Prove it, then test it

```bash
python tools/benchmark.py                                   # the moat: 0 false positives (needs no data)
coverage run --source=src/concordance -m pytest -q          # the suite
coverage report                                             # integrity-core floor is enforced in CI (≥75%)
```

The full local gate — MANIFEST wholeness, the moat, coverage floors — is:

```bash
PYTHONPATH=src python tools/check.py        # must print "=== GATE PASS ==="; read the exit code, not the tail
```

Many tests exercise **the keeping** (the retrieval corpus) and **skip automatically when it is
absent** — which is how CI runs green without it. A fresh clone can run the whole verifier/benchmark
layer; the data-backed paths (search, coach, Scripture at depth) come alive once you populate the
keeping (next section).

## 3. The keeping (the data) — what's in the repo and what isn't

The engine is code; **the corpus is data** (~1.2 GB) and is **gitignored**, exactly like a database
is not committed. So:

- **Runs with no data:** every verifier, the moat benchmark, most of the test suite, the engine
  process itself (it just has little to retrieve).
- **Needs the keeping:** full-text search, the coach, Scripture/word-study/cross-references, the
  card graph.

The source material the keeping is built from is **not all public**, so a fresh external clone
cannot fully reproduce it today — this is the known onboarding gap, tracked in **issue #3**. Two
ways to populate a local keeping:

1. **Seed from source** — the migration/seeder tools read their input from outside the repo via
   env vars, so no personal path is baked in. Point them at your own source data:
   ```bash
   export CONCORDANCE_IMPORT_DIR=/path/to/source      # tools/migrate_bible.py, migrate_cards.py, migrate_strongs.py
   export CONCORDANCE_DATA_DIR=./data                  # where the keeping is written/read (defaults to ./data)
   PYTHONPATH=src python tools/migrate_bible.py        # etc.
   ```
2. **Mirror a running instance** — `rsync` a `data/` directory from an existing deployment.

## 4. Run the engine

```bash
PYTHONPATH=src python -m concordance serve                       # secular reach (.com): API + site, same origin
PYTHONPATH=src python -m concordance serve --surface witness     # the witness face (.org)
PYTHONPATH=src python -m concordance mcp                         # the MCP server — the agents' door, five doors
```

## 5. Where things live

| path | what |
|---|---|
| `src/concordance/verifiers/` | the deterministic checks — the 0-false-positive heart |
| `src/concordance/mcp/` | the MCP server: the five doors (CHECK · FIND · WALK · KEEP · WORD) |
| `src/concordance/` | the engine — audit/verify, routing, the keeping, seals, the composition layer |
| `site/` | the faces (the Console and the surfaces), static-first |
| `tools/` | ops, the gate, benchmarks, and the data seeders |
| `tests/` | the suite (data-backed tests skip without the keeping) |
| `docs/ARCHITECTURE.md` | **start here** — the newcomer's map: the covenant, the verification path, the keeping, the five doors, the deploy ritual |
| `docs/` | design docs — `V2_DEFINITION.md`, `COMPONENTS.md`, `FASCIA.md` are good entry points |
| `deploy/` | systemd units + the deploy ritual |

## 6. The flow, and the covenant for code

- **Branch → PR → green CI → merge.** CI (`.github/workflows/ci.yml`) is the barrier: the moat at
  0 false positives, the suite, and the integrity-core coverage floor. A red run does not merge.
- `tools/deploy.sh` ships files to the box and runs the live gate; it **does not** `git` anything —
  commits and pushes stay explicit and human-reviewed. Stage exact paths; never `git add -A`.
- **A verifier must be deterministic and never false-positive.** Three-state verdicts (CONFIRMED /
  MISMATCH / NA + ERROR); when the evidence is incomplete, return NA — do not guess.
- **Nothing is generated at runtime.** Retrieve from the keeping, distinguish citation from proof,
  quarantine anything model-produced behind the airlock, carry provenance through every step.

### Good first contributions

- **Issue #2** — a single declarative tool registry (today a new MCP tool touches several files).
- **Issue #3** — a reproducible minimal-data bootstrap + live-wired count goldens for CI.
