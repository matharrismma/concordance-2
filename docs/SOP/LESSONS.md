# LESSONS — the "don't drop it twice" register

Append-only. One entry per thing that was actually dropped, broken, or silently skipped.
Every entry names **the guard now in place** — a lesson without a guard is just a regret.

Format: `date · what happened · why it happened · guard (SOP ref)`

---

### 2026-07-22 · My verification harness double-sent the request and hid the success
Verifying the key-binding flow live, my helper called `urlopen(req)` **twice** — once to read
`.status`, once to read the body. That sent the POST twice: the first spent the single-use
nonce and succeeded, the second got a correct 403, and I reported the second. For a moment it
looked like binding was broken when it was working perfectly — and the *replay protection*
was what produced the confusing result.
**Why:** a throwaway test helper written without noticing it performed the side effect twice.
**Guard:** when verifying anything with single-use or stateful semantics (nonces, tokens,
idempotency keys), send **once** and inspect one response (`with urlopen(...) as f`). If a
result contradicts a passing unit test, suspect the harness before the code. → SOP-1.

### 2026-07-22 · A third route registry existed that the SOP did not mention
Adding `POST /bind` with `rl: True` failed the gate: `RATELIMITED drifted: extra={'/bind'}`.
SOP-1 named two registries (`ROUTES`, `GOLDEN_API_GET`) but there is a **third** —
`GOLDEN_RATELIMITED`. The gate caught it before deploy, which is the registry lock working
exactly as designed.
**Why:** the SOP was written from the routes I had added before, not from the full contract.
**Guard:** SOP-1 now names all three and flags `GOLDEN_RATELIMITED` as the easy miss. → SOP-1.

### 2026-07-22 · I described an architecture without reading the code — and published it
`THE_COMPANION.md` and the live `companion.html` both claimed a **"Drafter — the only true
LLM call"**, with a "Tier 3: run a local model" offline rung and "offline you lose drafting."
All false. `ask.py` says in its own docstring: *"It FINDS, VERIFIES, and CITES; it never
generates the answer… **No LLM. No runtime generation.**"* Routing is already deterministic.
The system has **zero model and zero provider dependency** — the exact property the operator
was asking me to protect — and I had written a plan to *add* a dependency to close a "gap"
that did not exist.
**Why:** I reasoned from a plausible mental model of "an AI companion" instead of reading the
module I was describing. The error then propagated into a public page.
**Guard:** a claim about how the system works is a **finding, not a premise** — read the
module and quote it before writing it down, especially before publishing. When the answer is
"what is the most independent option," check what is *already* true before proposing to build
anything: here the answer was **build nothing.** → SOP-4, SOP-6.

### 2026-07-22 · I health-checked a service worker with HEAD and read a 501 error page
Checking `sw.js`'s MIME type with `curl -I` returned `Content-Type: text/html` — which would
mean browsers refuse to register the worker. It was the **501 HEAD error page**, not the file;
a GET showed the correct `text/javascript`. I had documented this exact trap in SOP-1 and
LESSONS earlier the same session, then walked into it.
**Why:** reached for the habitual header check instead of the documented one.
**Guard:** SOP-1 already says it — *health-check with GET and read the body.* Written twice
now; the cost of the third time is shipping a silently-dead service worker. → SOP-1.

### 2026-07-12 · The runbook described an app that no longer runs
`DEPLOY.md` documented the 1.0 Lighthouse app — Docker/uvicorn, push-to-`main` deploys,
`/version`, `/mcp/`. None of it was true: the box runs the 2.0 `concordance` app under
systemd behind Caddy, `/home/nh/concordance-2` isn't a git repo, and pushing to `main`
deploys **nothing**. An operator following it would have "deployed" and changed nothing.
**Why:** the doc was written pre-cutover and never re-verified.
**Guard:** every runbook carries `Verified live <date>`; re-verification is a step inside
the deploy procedure itself. → SOP-4.

### 2026-07-12 · The external drive was disconnected; retention silently could not run
`release_archive.ps1` failed with "D: drive not present". The earlier backup had
succeeded, so the state *looked* durable. Had the script defaulted to skipping quietly,
we'd have believed releases were being retained when nothing was.
**Why:** durability depends on removable hardware being attached.
**Guard:** both durability scripts fail loudly; `Test-Path 'D:\'` is checked before any
claim that something is backed up. Never report "backed up" on an unverified path. → SOP-3.

### 2026-07-11 · The cutover dropped a whole derived index (1,296 real edges)
The 1.0→2.0 migration carried every inline card connection, but a *separate* derived
artifact — `rebalance/verified_connections.json`, 1,098 cards of shared-scripture
cross-references — lived outside the card files and was never migrated. It sat unused on
the drive until audited.
**Why:** the migration reasoned about cards, not about derived indexes built from cards.
**Guard:** cutovers must enumerate **every** derived artifact and account for each
(migrated / regenerated / deliberately dropped), then publish a net-new diff against
live. → SOP-5.

### 2026-07-11 · I called real connectivity "padding" and nearly discarded it
3,824 `same_section` edges were dismissed as structural padding because the *label*
carried no concordance meaning. The operator pushed back. Measurement showed 554 cards
(10.2%) were **orphans** — unreachable in the graph — and these edges were 1.0's
orphan-elimination layer. Harvesting 971 of them took orphans to 178.
**Why:** judged a class of data by its label instead of by what it buys.
**Guard:** before discarding a class of data, measure its effect (orphan reduction /
reachability). The same measurement correctly rejected 4,626 hub↔hub edges of the *same
type* — the measurement decides, not the name. → SOP-6.

### 2026-07-11 · Heavy subagent fan-out repeatedly hit the operator's session limits
The connection miner ran mine+verify (~58 agents/batch, ~2.8M tokens) and exhausted the
5-hour window twice mid-batch, losing partial work.
**Why:** reached for LLM fan-out where a deterministic pass would do.
**Guard:** prefer deterministic harvests (the 1.0 harvest yielded ~4× the subagent
output at zero token cost); if subagents are needed, run mine-only with a deterministic
guard, batch ~16, pace them, and roll the cursor back on a limit error. → SOP-7.

### 2026-07-12 · Health checks returned 501 and looked like an outage
`curl -I` (HEAD) returned `501 Not Implemented` on all three domains. The app serves GET
only; the sites were fine.
**Why:** probed with a method the app doesn't implement.
**Guard:** health-check with GET and read the body; a status code alone is not proof the
runtime path works. → SOP-1.

### 2026-07-12 · I overwrote a good doc while fixing a stale one — minutes after writing SOP-4
While reconciling the duplicate runbooks I ran `cp Desktop/DEPLOY.md → repo/docs/DEPLOY.md`
**without reading the destination first.** The repo copy was not the stale doc at all — it
was a different, valuable **2.0 bootstrap** guide (venv setup, data-migration commands,
systemd units). My own check printed `stale-markers: 0` and `97 lines vs 144` — evidence it
was a different file — and I copied over it anyway. Recovered with `git checkout --` because
it happened to be tracked and uncommitted. Had it been untracked (like `docs/SOP/` and
`THE_COMPANION.md` are right now), it would have been **gone**.
**Why:** treated "reconcile duplicates" as a mechanical copy instead of a merge, and did not
stop when the evidence contradicted the assumption.
**Guard:** never overwrite a file you have not read *in this session*; if a pre-flight check
contradicts the assumption (different length, missing expected markers), **stop and diff**.
Two docs with the same name may serve different purposes — the fix is to split them
(`DEPLOY.md` = bootstrap, `RUNBOOK.md` = daily path), not to flatten one onto the other.
→ SOP-4, SOP-5.

### 2026-07-12 · Two copies of DEPLOY.md — the drift source itself
The runbook existed at both `Desktop\DEPLOY.md` and `concordance-2\docs\DEPLOY.md`.
Duplicated docs are precisely how the first lesson above happened.
**Why:** no canonical home.
**Guard:** one canonical home per document; any second copy is a stub pointing at it. → SOP-4.

### 2026-07-11 · Windows path and heredoc traps cost repeated retries
`"...\verified_connections.json"` became `\x0b` (vertical tab); `\i`/`\k` raised escape
warnings; a quoted heredoc silently failed to interpolate `$SCRATCH`; scanning 11k files
on the external drive blew a 2-minute tool timeout twice.
**Why:** mixing Windows paths into POSIX-shell heredocs and Python literals.
**Guard:** forward slashes in Python paths; literal paths inside quoted heredocs; tar
once and ship one archive rather than walking many files over USB. → SOP-9.
