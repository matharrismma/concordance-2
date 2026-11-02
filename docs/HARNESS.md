# The Harness — plan, build, check, fix; the gates grade

> *"The implementing model does not declare completion in prose; the gates declare it."*
> — [COMPLETION_CONTRACT.md](COMPLETION_CONTRACT.md) §8

Every change to this repo made by agents runs through one loop, recorded in one ledger, graded by
machines. Trust tests, not confidence — including the lead's.

## The crew — one owner per step

| role | owns | never |
|---|---|---|
| **lead** | the goal, the plan, the ledger, dispatch, commit, push, deploy | owns a step · grades anything |
| **builder-N** ([.claude/agents/builder.md](../.claude/agents/builder.md)) | exactly one step: the next smallest faithful one | grades · commits · deploys · touches another step |
| **checker-N** ([.claude/agents/checker.md](../.claude/agents/checker.md)) | every review: the plan, each step, the live result | edits a file · reviews a step it owns |

The names are the roles: only a `builder-N` can own a step, only a `checker-N` can run the checker
gate or record a verdict, and `lead` can do neither. A fresh checker reviews each step and is given
the step's claim and diff, not the builder's reasoning, so its read is its own. When it fails a step,
the findings go back to the **same** builder; nobody else edits that step.

## The loop

```
open (goal + done criteria) ─► a checker passes the plan
  └─► builder: reproduce the red ─► open the step (claim · scope · tests) ─► build ─► builder gate
        └─► checker: brief ─► read the diff ─► checker gate ─► verdict
              FAIL ─► findings to the same builder ─► fix ─► builder gate ─► checker again (3 rounds, then BLOCKED)
              PASS ─► close (mechanical) ─► commit (mechanical) ─► push
  └─► next step … until the done criteria hold
ship: tools/deploy.sh (its own gate grades and auto-reverts) ─► note ship ─► a checker verifies live
  ─► done (mechanical) ─► record the ledger
```

All of it is `python tools/harness.py <command>`; its docstring lists the commands. Before the lead
closes or commits, and before a checker trusts a gate, each asks git directly whether the step
touched a grader (`git diff --name-only BASE`); if it did, the step fails without its gate.

## What the machine enforces

- **No step before the plan is checked**, and only a checker's verdict counts.
- **One step at a time, one owner**, and it opens on a clean tree (or `--adopt`s the work, recorded).
- **The builder gate**: every path a plain file inside the step's scope · no
  forbidden path (a box-owned file, a *new* data file — tracked data may be edited, guarded files
  only surgically and by exact name) · **no grader touched** · no secret in an added line or in
  the ledger · hygiene (conflict markers, trailing whitespace, every `.py` compiles, every
  `.json`/`.jsonl` parses) · `tests/MANIFEST.txt` whole · the step's tests pass **and actually ran**
  — run, like every test the harness runs, in a fresh worktree holding the commit-to-be, so one
  checkout serves every role and no local keeping or ignored file can sway a result.
- **The checker gate grades the commit-to-be, not the checkout**: a worktree at the step's base
  with exactly the step's paths laid over, so a file only the checkout has (ignored, untracked
  elsewhere) cannot pass a test, and **reset before every stage** so nothing one stage writes
  reaches the next. The stages: **the pin check** (the step's test files laid over, the fix left
  out — at least one of the step's own test ids must fail; a skip, an unknown id or "no tests ran"
  is not red. When the whole fix is in `tests/` — an expectation or fixture that a later deliberate
  commit made stale — there is nothing to revert, the pin is N/A, the gate names the baselined reds
  the step retires, and the checker must justify each changed expectation against the commit the
  claim names) · the step's tests · **the full suite** (`-vv`, with the vacuity plugin) · **the moat**
  (`tools/benchmark.py`, 0 false positives). **Results are streamed, never read from a file the
  run leaves behind**: a reporter plugin, written outside the tree under a random name, sends every
  test's result over a localhost socket as pytest makes it, from the innermost of the wrappers
  present at startup, so nothing that runs later (an exit hook, a wrapper that flips an outcome) can
  take a delivered failure back. **A plugin from inside the tree that hooks how tests are judged or
  which tests run fails the run** — save the graders a step cannot edit (any `conftest.py`,
  `tools/vacuity_plugin.py`); installed plugins are the environment. The stream opens with a
  per-run token, binds everything it uses before any test exists, decides xfail by pytest's own
  evaluation rather than a marker, and keeps every failure message a test produced. A run whose
  collected tests do not all report, that never finishes, or whose printed summary disagrees with
  the stream on red or green, fails. The gate runs alone (`.gate.lock`, taken atomically).
- **The baseline matches exactly** ([baseline.txt](harness/baseline.txt)): every red must be listed
  *and fail the way it was listed* — its fingerprint hashes the whole `-vv` failure message, so an
  "every page" test already red for one page cannot hide a second · every listed red must still be
  red · every listed vacuous pass must still be vacuous and no new one may appear · and the
  baseline may only **lose** lines. A step that fixes a listed red deletes its line in the same step.
- **A step never edits what grades it**: this harness, the moat, `tools/check.py`, the vacuity
  plugin, any `conftest.py`, the pytest config (`pyproject.toml` …), the role files — nor adds a
  grader in disguise: a module in the repo root, `src/`, `tools/` or `tests/` named like the
  standard library or the test runner (`pytest.py`, `sitecustomize.py`, `fnmatch.py` …), or a
  `.pth` file. The manifest may only gain tests; the baseline may only shrink. Whatever the working
  copy holds, the harness that runs is **HEAD's** (a modified `tools/harness.py` re-executes the
  committed one), and it runs with nothing from the repo on its own import path.
- **A PASS rests on the checker's own full gate**, run on exactly the content it passes.
- **Close** needs a builder gate PASS, a full checker gate PASS and that checker's verdict PASS, all
  on the same content hash (full sha256) as the tree at that moment. One byte changed after the
  check and it refuses; a FAIL recorded after the close voids it.
- **Commit** stages exactly the step's paths plus the ledger, refuses anything else staged, then
  proves the commit holds exactly those paths — byte for byte, no mode change — or takes itself back.
- **Three failed verdicts BLOCK a step.** A blocked step waits for a human: it cannot be abandoned
  to reset its count, and no new run opens past it. Only a human releases it
  (`abandon … --human`; agents never pass that flag).
- **The ledger is public**: every event is scanned for secrets as it is written, and the whole file
  again before any commit stages it.
- **Done** needs every step committed or abandoned, the latest ship note passing after the last
  commit, and a checker's passing live verdict after that ship. `record` then commits the ledger
  alone, and only when no step is in flight.

**What it cannot enforce** — said plainly, so nobody leans on it: the ledger is a local file, so a
forged line is possible; it is committed with each step, where review can see it. Agent names are
declared, not authenticated. Code under test runs inside the pytest process, so code written to hunt
down the reporter by name can still lie, and the vacuity report is a file the run writes; both take
code a checker reading the diff will see. A working copy of `tools/harness.py` edited to skip its own
re-exec cannot be stopped by any file, which is why the checker asks git for the changed paths before
it trusts the gate. A post-commit hook runs before the commit is verified. On Windows the worktrees
are CRLF checkouts, and `tools/deploy.sh` sends the working copy, so files deployed from Windows
arrive on the box as CRLF while the rest stay LF (found by checker-9, 2026-11-01). Nothing breaks —
browsers and Python accept both, and `tools/verify_deploy.py` normalises line endings — but a test
that compares raw bytes would see it; deploying committed blobs instead is a want.
Because the manifest only grows, renaming or deleting a test file is a bootstrap. A change to the
machinery itself is a **bootstrap**: the lead writes it, a fresh checker reviews it outside any run,
and its commit says so.

## What "smallest" and "faithful" mean

- **Smallest**: one root cause, one claim, the fewest files. If it could be split into two
  independently useful steps, it is two steps.
- **Faithful**: it does what the claim says and nothing else, and it honours the intent of the test
  or contract it touches. A test is never weakened to pass (deleted, skipped, loosened, its expected
  value changed) unless the claim *is* that the expectation was wrong, with the evidence; the checker
  scrutinises that hardest. Golden and data files are fixed at their source, never regenerated whole.

## The standing rules every role carries

- 0 false positives; a miss stays a miss. Nothing generated: found, verified, cited, sealed.
- Public repo: no secrets, no box details, none of the operator's private writings.
- Never deploy data files (`data/sticks` is the one tracked exception); never run
  `tools/card_theories.py`; never regenerate `data/domain_goldens.json` whole.
- The full suite runs in a **clean clone** (no keeping; corpus-dependent files skip by design),
  never on the box beside the live engine. The laptop pages under load: builders run only their
  step's tests; one heavy job at a time.
- Only the lead touches the box, and only through `tools/deploy.sh`. Subagents never ssh.

## Where things live

- `tools/harness.py` — the gate and the ledger; `tests/test_harness.py` pins its rules.
- `docs/harness/baseline.txt` — the known reds (with fingerprints) and vacuous passes, each with its
  reason. Re-measured only in a bootstrap, with `python tools/harness.py measure`.
- `docs/harness/runs/<run>.jsonl` — one ledger per run, committed with its steps: the audit trail.
- Private secret patterns (box host, key file names) go one regex per line in
  `~/.config/harness/secret_patterns.txt`, never in this repo.
