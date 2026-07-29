# SOP — RUNNING OUT OF CONTEXT (the handoff)

Matt, 2026-07-29: *"This needs a SOP for each time we are out of context."*

A context window ends mid-work every time. That is normal and it is not a failure — the
failure is ending it **badly**: half-registered data, an ungated change on disk, a claim in a
document the code does not support, or a next session that has to re-derive what this one
already learned. This SOP makes the ending an operation with steps, like a deploy.

**Trigger.** Start this at **~85% context used**, not at 99%. If you can feel the window
closing you are already late; the handoff itself costs 5–10% and must fit *inside* the window.

---

## THE FOUR STATES — leave the work in exactly one of them

Every artifact you touched must end in one of these. Say which, in the report.

| state | means | rule |
|---|---|---|
| **LIVE** | gated, deployed, verified against the running system | only if a full gate passed AND a live check was run |
| **COMMITTED** | in git, gated, not deployed | safe; next session deploys |
| **STAGED** | written to disk, NOT registered/wired, gate not run | must be *inert* — nothing loads it, nothing serves it |
| **UNDONE** | not started | say so plainly; do not imply otherwise |

**Never leave a fifth state:** written AND wired AND ungated. That is the shape that breaks a
system quietly. If you wired something and cannot gate it, **unwire it** before you stop.

---

## THE SEQUENCE

**1 · Freeze scope.** Stop starting. Finish only what can reach a clean state in the remaining
budget. A half-built tool is fine (STAGED); a half-registered data file is not.

**2 · Make STAGED work inert.** Anything on disk that a loader would pick up must be either
registered *and gated*, or not registered at all. Check the loader list, the MANIFEST, the
route registry, the palette — the places that make a file *live*.

**3 · Run the gate if anything is wired.** `PYTHONPATH=src python tools/check.py` — 7–30 min,
so this is the step you must budget for. No deploy without it, ever, including "one-line
prose changes".

**4 · Commit with the reasoning, not just the diff.** The commit message is the handoff other
people (and future you) actually read. Name what was measured, what failed, what you refused
to claim.

**5 · Update the three living documents.** They are the memory that survives the window:
- `docs/OPERATIONS_LOG.md` — what happened, with measured evidence and where the proof lives.
- `docs/MASTER_PLAN.md` — §1 shipped / §3 planned, kept strictly separate; the update log.
- `docs/GAPS.md` — anything found and not fixed, with its number.

**6 · Write the NEXT PHASE section** (below) — the single most valuable artifact of the
handoff.

**7 · Save memory.** Any durable directive, correction, or doctrine from this session goes to
the memory directory with its index line. A directive that lives only in a transcript is lost.

**8 · Stop any loop.** `ScheduleWakeup(stop: true)`. A loop that fires into an exhausted window
does bad work in your name.

**9 · Report to Matt** in this shape: what shipped (measured) · what is staged · **what I
refused to claim** · what to do next.

---

## THE NEXT PHASE SECTION — what to write

Not a to-do list. Written so the next session can act **without re-deriving anything**:

1. **State of the world** — the live numbers (cards, substance, gate count, RSS, what's
   deployed). Measured this session, with the command that measured them.
2. **First action** — the single next command to run, verbatim, and what a pass looks like.
3. **Staged artifacts** — every file written but not wired, and exactly what wiring it needs.
4. **Known failures** — what broke and the diagnosis, so nobody re-debugs it from scratch.
5. **Decisions already made** — so they are not re-litigated (with the *why*, briefly).
6. **The trap list** — traps hit this session that will be hit again (see below).

---

## THE STANDING TRAPS (hit repeatedly — check these first)

- **Check the check.** Five instruments lied before their subjects did on 2026-07-29 alone: the
  null assay's first draft (9 false findings), the reachability surface (read only `*.html`,
  missed the palette), the line-ending comparison (every file "differs"), the ≥120-char card
  rule (failed 330 *real* Clarke notes), and the shard test inheriting that same threshold.
  **Before trusting a finding, verify the instrument measures what you think it measures.**
- **The deploy target is not a checkout.** Files arrive by scp; `corpus_db.py` and `airlock.py`
  were each absent for days under a green gate. Run `python tools/verify_deploy.py`.
- **CRLF kills shell scripts on the box.** `set -euo pipefail` dies as `pipefail\r`.
  `.gitattributes` pins `*.sh` to LF; keep it that way.
- **Windows `/tmp` ≠ Git Bash `/tmp`.** Python resolves it to `C:\tmp`. Pass explicit paths.
- **Frozen shelves need rebuilt shards.** Mint cards on a frozen shelf without rebuilding, and
  the reader gets a title where the body belongs. Correct in the jsonl, empty on the page.
- **Env values with spaces need quoting.** A shelf is literally named `nuclear physics`;
  unquoted in an EnvironmentFile it truncates the list and *appears* to succeed.
- **Both numbers, always.** Total cards AND substance cards. A count is not a library.

---

## THE REFUSAL LIST — say what you did NOT do

End every handoff with what you deliberately left undone and why. Silence reads as completion.
Standing examples from 2026-07-29: contract §5 is **not** done (five endpoints still accept a
private key inbound); three dead files remain on production because deleting on a live box
needs Matt's word; overall coverage is 52%, not 90.

*A handoff that only lists wins is a handoff that lies by omission.*
