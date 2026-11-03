# RULES — the standing rules of the harness

The rules the lead retypes into every brief, and the procedures the ledgers show, kept as records
instead of memory. Each entry quotes its text verbatim from the source it names, and
`python tools/context.py check` proves that every source resolves and that every text occurs in it.
The format and the pointer grammar are in the docstring of tools/context.py. A rule's check is how a
checker decides whether the rule held; the checkers' confirmations in the ledgers, not this file,
say whether it did.

## zero-false-positives
- scope: all
- source: FILE concordance-2 docs/HARNESS.md 93b4446c20eff93e9281205672bdfffe4aedb8c8 "0 false positives; a miss stays a miss."
- check: the moat prints FALSE-POSITIVES 0 on the graded content, and no declined, failed or unchecked case is reported as a pass
> 0 false positives; a miss stays a miss. Nothing generated: found, verified, cited, sealed.

## public-repo
- scope: all
- source: FILE concordance-2 docs/HARNESS.md 93b4446c20eff93e9281205672bdfffe4aedb8c8 "Public repo: no secrets, no box details"
- check: no tracked file, ledger event or record names a secret, the box's host, user, key or paths, or the operator's private writings; any such line found is a failed confirmation
> Public repo: no secrets, no box details, none of the operator's private writings.

## data-files-and-goldens
- scope: concordance-2
- source: FILE concordance-2 docs/HARNESS.md 93b4446c20eff93e9281205672bdfffe4aedb8c8 "Never deploy data files"
- check: no deploy sent a file under data/ other than data/sticks, tools/card_theories.py was not run, and data/domain_goldens.json changed only surgically
> Never deploy data files (`data/sticks` is the one tracked exception); never run
> `tools/card_theories.py`; never regenerate `data/domain_goldens.json` whole.

## the-suite-runs-in-a-clean-clone
- scope: all
- source: FILE concordance-2 docs/HARNESS.md 93b4446c20eff93e9281205672bdfffe4aedb8c8 "The full suite runs in a **clean clone**"
- check: the full suite ran only in a gate's fresh worktree or in CI, never beside the live engine, and each builder ran only its step's tests
> The full suite runs in a **clean clone** (no keeping; corpus-dependent files skip by design),
> never on the box beside the live engine. The laptop pages under load: builders run only their
> step's tests; one heavy job at a time.

## only-the-lead-touches-the-box
- scope: all
- source: FILE concordance-2 docs/HARNESS.md 93b4446c20eff93e9281205672bdfffe4aedb8c8 "Only the lead touches the box"
- check: every change to the box in the run is a ship by the lead through a gated ship path, recorded in a ship note
> Only the lead touches the box, and only through a gated ship path, never by hand

## subagents-never-ssh
- scope: all
- source: FILE concordance-2 docs/HARNESS.md 93b4446c20eff93e9281205672bdfffe4aedb8c8 "Subagents never ssh."
- check: no builder's or checker's report, note or verdict shows an ssh session
> Subagents never ssh.

## machinery-is-off-limits
- scope: all
- source: FILE concordance-2 docs/HARNESS.md 93b4446c20eff93e9281205672bdfffe4aedb8c8 "A step never edits what grades it"
- check: git diff --name-only from the step's base lists no path matching MACHINERY in tools/harness.py, and the gate's machinery check passes
> **A step never edits what grades it**: this harness, the moat, `tools/check.py`, the vacuity
> plugin, any `conftest.py`, the pytest config (`pyproject.toml` …), the role files

## never-weaken-a-test
- scope: all
- source: FILE concordance-2 docs/HARNESS.md 93b4446c20eff93e9281205672bdfffe4aedb8c8 "A test is never weakened to pass"
- check: the step deletes no assert, adds no skip or xfail and loosens no expected value, unless its claim says the expectation was wrong and carries the evidence
> A test is never weakened to pass (deleted, skipped, loosened, its expected
> value changed) unless the claim *is* that the expectation was wrong, with the evidence; the checker
> scrutinises that hardest.

## grade-in-a-fresh-worktree
- scope: all
- source: FILE concordance-2 docs/HARNESS.md 93b4446c20eff93e9281205672bdfffe4aedb8c8 "The checker gate grades the commit-to-be, not the checkout"
- check: the verdict rests on a checker gate event for the same content hash, run in the harness's fresh worktree, never on a checkout's working copy
> **The checker gate grades the commit-to-be, not the checkout**: a worktree at the step's base
> with exactly the step's paths laid over

## a-pass-rests-on-the-checkers-own-gate
- scope: all
- source: FILE concordance-2 docs/HARNESS.md 93b4446c20eff93e9281205672bdfffe4aedb8c8 "A PASS rests on the checker's own full gate"
- check: every PASS verdict on a step follows a full checker gate PASS by the same checker on the same content hash
> **A PASS rests on the checker's own full gate**, run on exactly the content it passes.

## never-review-a-step-you-own
- scope: all
- source: FILE concordance-2 .claude/agents/checker.md 93b4446c20eff93e9281205672bdfffe4aedb8c8 "never reviews a step it owns"
- check: no verdict on a step is by its owner, and no file changed because of the checker's review
> Never edits files and never reviews a step it owns.

## checkers-change-nothing
- scope: all
- source: FILE concordance-2 .claude/agents/checker.md 93b4446c20eff93e9281205672bdfffe4aedb8c8 "You never edit, stage, commit or deploy anything."
- check: the reviewed checkout's git status and index are the same before and after the checker's review
> You never edit, stage, commit or deploy anything.

## builders-stage-nothing
- scope: all
- source: FILE concordance-2 .claude/agents/builder.md 93b4446c20eff93e9281205672bdfffe4aedb8c8 "Never stage, commit, push or deploy."
- check: when the builder reports, nothing is staged (git diff --cached is empty), and every commit, push and deploy in the run is the lead's
> Never stage, commit, push or deploy.

## findings-go-to-the-same-builder
- scope: all
- source: FILE concordance-2 docs/HARNESS.md 93b4446c20eff93e9281205672bdfffe4aedb8c8 "nobody else edits that step"
- check: every builder gate of a step is by the step's one owner, including the gates after a failed verdict
> When it fails a step, the findings go back to the **same** builder; nobody else edits that step.

## no-pytest-in-the-shared-concordance-2-checkout
- scope: all
- source: LEDGER concordance-2 2026-11-03-assemble-reapply 25
- check: no report, note or gate of the run shows pytest run with the shared concordance-2 checkout as its directory; concordance-2 tests ran only in a gate's worktree or a separate worktree, while a V3 builder works in V3's own checkout
> never run pytest inside the shared concordance-2 checkout. It is shared: V3's runs use its
> tools/harness.py as their grader, other sessions work in it, and its tests can write that
> checkout's stores. Run concordance-2 tests only through the harness gate, which runs them in a
> fresh worktree, or inside a separate worktree of concordance-2. This rule is about the
> concordance-2 checkout only; a V3 builder works in V3's own checkout as its brief says.

## a-timeout-is-re-run-once
- scope: all
- source: LEDGER concordance-2 2026-11-03-assemble-reapply 10
- check: a red whose only cause is a timeout was re-run once, and a note records both results before the verdict that relies on them
> a failure that is only a timeout is re-run once, and both results are recorded in a note before
> any verdict relies on them

## a-false-positive-is-never-re-run
- scope: all
- source: LEDGER Concordance-V3 2026-11-02-order-free-derivation 12
- check: no red that shows a false positive was re-run; it counted against its step at once
> any false positive counts at once and is never re-run

## record-the-re-run-judgement-first
- scope: all
- source: LEDGER Concordance-V3 2026-11-02-gate-hygiene 37
- check: a re-run judgement note stands in the ledger before every verdict that relies on a re-run
> This run's plan states no re-run rule, so the judgement is recorded here before the verdict
> relies on it.

## verify-probes-never-seal
- scope: all
- source: LEDGER witness 2026-11-02-receipts-open 32
- check: every /verify request the run makes carries ?seal=0, and the seal count and the ledger total read the same before and after it
> every /verify check carrying ?seal=0 so verifying never writes

## live-probes-are-gets
- scope: all
- source: LEDGER Concordance-V3 2026-11-03-topological-order 6
- check: the live notes and the live verdict name only GET requests, besides any POST /verify carrying ?seal=0 that the plan names, and no ssh
> public GETs only (no POST, no ssh)

## no-test-writes-the-stores
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-02-gate-hygiene 6
- check: tests/test_no_test_writes_the_stores.py passes in the gate, and the checkout's data/ is unchanged after the suite
> (D) NO TEST WRITES THE REAL STORES (bootstrap): tests/conftest.py, rewritten as V3's own, makes it
> impossible for any test to write the checkout's data/cas, data/ledger or memo stores

## live-before-and-after
- scope: all
- source: LEDGER Concordance-V3 2026-11-03-restatement-audit 7
- check: a checker's live-before note stands before the push, and a live-after note or the live verdict after the last commit compares the same fields
> a checker records a public before-snapshot (/health, /capabilities without its cache block,
> every /seals hash with its page's sha256, /ledger/verify) before this run's push to main and,
> after the last commit lands, grades that every field is identical, any new seal named as traffic

## record-from-a-worktree-at-origin
- scope: all
- source: LEDGER Concordance-V3 2026-11-03-topological-order 4
- check: the record commit's parent is origin's default branch, the commit was made in a separate worktree, and the shared checkout is as it was
> any other run's record is made from a separate worktree at origin/main

## record-a-run-from-a-worktree
- scope: all
- source: LEDGER concordance-2 2026-11-03-assemble-reapply 30
- check: git diff origin/<default branch> -- <ledger path> is empty in the checkout
> The corrected procedure: (1) git fetch, and confirm origin's default branch is at the run's last
> pushed commit; (2) add a detached git worktree at origin's default branch; (3) copy the run's
> ledger from the checkout into the same path in the worktree; (4) run harness record for the run
> with HARNESS_ROOT set to the worktree; (5) push the worktree's HEAD to the default branch; (6)
> compare the recorded ledger (git show HEAD:<ledger path> in the worktree) with the checkout's
> copy, ignoring CRLF; they must be equal; (7) remove the worktree; (8) discard the checkout's
> working copy of the ledger (git checkout -- <ledger path>), then bring the checkout to the record
> commit: git fetch, then git merge --ff-only origin/<default branch> while on the default branch,
> or git switch -c <next branch> origin/<default branch>. Never append to that run's ledger in a
> checkout that lacks the record commit. Held when git diff origin/<default branch> -- <ledger path>
> is empty in the checkout.

## rebase-only-over-ledgers
- scope: all
- source: LEDGER Concordance-V3 2026-11-03-topological-order 4
- check: git diff --name-only from the old base to the new main lists only other runs' ledgers, and a rebase note follows
> a rebase is allowed only over other runs' ledgers, with a patch-id note

## the-rebase-note-maps-by-patch-id
- scope: all
- source: LEDGER Concordance-V3 2026-11-02-halt-and-order 12
- check: the rebase note lists each old sha, its new sha and their identical git patch-id --stable; otherwise every checker gate was re-run on the new base
> git diff --name-only between this run's base and the new main touches nothing but other runs'
> ledgers under docs/harness/runs/, with a ledger note mapping each old sha to its new sha by identical
> git patch-id; if main moved any other path, every step's checker gate is re-run on the new base
> before main moves

## correct-another-sessions-commit
- scope: all
- source: LEDGER Concordance-V3 2026-11-02-order-free-derivation 32
- check: when the shared checkout's HEAD holds a commit no step of the run made, a correction note names it and the sha the run's record lands on
> The ship note's recorded head (c4cc8fb) is the shared checkout's HEAD at the moment it was written:
> another session had committed c4cc8fb (the receipt page) onto this branch in the same checkout. It
> is not part of this run.

## v3-install-is-owner-only
- scope: Concordance-V3
- source: FILE Concordance-V3 CLAUDE.md 842938686b1a1bb9ea7accccaf9b72c03611153a "Owner-only steps (never attempt)"
- check: no V3 ship ran deploy/install.sh without the owner's word quoted in its ship note
> Owner-only steps (never attempt): GitHub Release, PyPI upload, running `deploy/install.sh` on the
> box, the Caddy route, `python -m concordance keygen` into the production `.env`.

## v3-ships-through-install-on-the-owners-word
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-02-order-free-derivation 30
- check: each V3 ship note names deploy/install.sh at the shipped sha and quotes the owner's word the ship rests on
> SHIP on the owner's word in chat (2026-11-02: 'you run and install'), which releases V3
> CLAUDE.md's owner-only install for this ship.

## v3-standing-word-to-ship
- scope: Concordance-V3
- source: OWNER owner, chat, 2026-11-02 "you run and install for the whole. Ship everything"
- check: a V3 ship made on this standing word quotes it in its ship note
> you run and install for the whole. Ship everything
