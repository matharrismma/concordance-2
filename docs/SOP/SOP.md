# SOP — Narrow Highway standard operating procedures

Purpose: **so we never drop the same thing twice.** Each procedure below exists because
something was actually dropped, broken, or silently skipped. The matching incident is in
[LESSONS.md](LESSONS.md).

Every runbook in this project carries a **`Verified live <date>`** line. A runbook without
one is presumed stale.

---

## SOP-1 — Deploy (code)

The box has **no git repo**; pushing to `main` deploys nothing. Deploy = copy + restart.

1. Gate first: `PYTHONPATH=src .venv/bin/python tools/check.py` → `=== GATE PASS ===`.
2. `scp -i ~/.ssh/id_ed25519_nh <file> nh@5.78.186.55:/home/nh/concordance-2/<path>`
3. `ssh … "sudo systemctl restart nh-com-2 nh-org && systemctl is-active nh-com-2 nh-org"`
4. **Verify the runtime, not the file** — GET a route that exercises the change and read
   the body. `HEAD` returns 501 (GET-only app); a 200 alone proves nothing.
5. Adding a route? **Three** registries must agree or the gate fails:
   - `web/api.py::ROUTES` — the entry itself
   - `tests/test_routes.py::GOLDEN_API_GET` — if the route is `api: True`
   - `tests/test_routes.py::GOLDEN_RATELIMITED` — **if the route is `rl: True`** (easy to miss;
     the gate caught exactly this on `/bind`, which is the registry lock working as designed)

## SOP-2 — Deploy (data / cards)

1. Write the **durable master** to `Lighthouse\data\cards\<id>.json` — this is the
   backed-up source of truth. *Never* deploy to the box only.
2. Append the same lines to `/home/nh/concordance-2/data/cards.jsonl`
   (last-wins on duplicate id ⇒ re-appending is idempotent and safe to retry).
3. Card data hot-reloads by mtime; restart only if code changed.
4. Verify with a live query that counts what you added (e.g. `/graph` edge total, or a
   box count from the served corpus) — not just that the file grew.

## SOP-3 — Durability & retention

Two scripts, both writing to the external drive:

- `local\backup_to_drive.ps1` — mirrors the substrate + dated 30-day snapshot.
- `local\release_archive.ps1` — **first (genesis, immutable) + previous + current**,
  with an append-only `manifest.json` (stamp, sha256, bytes, files) so **drift is
  chartable from the first release to today**. Pulls the *deployed* tree off the box.

**Before claiming anything is durable, confirm the drive is attached:**
`Test-Path 'D:\'`. If it is absent, retention did **not** happen — say so out loud;
never report "backed up" on an unverified path. Both scripts fail loudly by design.

Policy: *the latest and best, but never lose the last — or the first.*

## SOP-4 — Documentation freshness

1. **One canonical home per document.** Duplicated copies are how docs go stale — if a
   second copy must exist, it is a stub pointing at the canonical path.
2. Every runbook states `Verified live <date>` and marks claims ✅ (inspected) or ⚠️ (open).
3. **Re-verify on deploy**: if a deploy changes topology, runtime, or endpoints, the
   runbook is updated in the same pass — not "later".
4. When a doc is found wrong, record *why it drifted* in LESSONS.md, not just the fix.

## SOP-5 — Migrations & cutovers

When moving between substrates (1.0 → 2.0 and any future cutover):

1. Migrate the **cards AND the derived indexes**. The cutover carried inline card
   connections but silently dropped a separate derived index (1,296 real edges) that
   lived outside the card files. **Enumerate every derived artifact** in the old
   substrate and account for each: migrated / regenerated / deliberately dropped.
2. After the cutover, run a **diff of the old substrate against live** and publish the
   net-new count by category. "It looks complete" is not evidence.
3. Record deliberate drops explicitly, so a later pass doesn't "restore" something that
   was culled on purpose.

## SOP-6 — Judging data before discarding it

Do **not** discard a class of data based on its label. Measure what it buys.

- A `same_section` edge looked like padding; it was the **orphan-elimination layer**.
  10.2% of cards were unreachable in the graph. Test: *does this reduce orphans or
  increase reachability?* Only then decide.
- Conversely, keep the surgical gate: 4,626 hub↔hub edges of the *same type* genuinely
  were redundant and were correctly skipped. The label didn't decide — the measurement did.

## SOP-7 — Working under session limits

1. Prefer **deterministic** harvests (local/droplet Python) over LLM subagent fan-out.
   The 1.0 harvest produced ~4× the subagent yield at zero token cost.
2. If subagents are needed, run **mine-only** (no verify fan-out) and rely on a
   deterministic guard for correctness; batch ~16 and pace them.
3. Keep large results **out of the conversation** — write to a file, print a summary.
4. On hitting a limit mid-batch, **roll the cursor back** by the batch size before retrying.

## SOP-8 — 0-FP gates (never regress the moat)

Every minted edge/claim passes a **deterministic** gate that re-verifies in the *live*
corpus — never trust the source artifact:

| Harvest | Gate |
|---|---|
| Subagent-mined concords | evidence quote must appear in the hub card's real body |
| Shared-scripture parallels | the shared verse must be present in **both** live cards |
| Nesting / same_section | both cards must genuinely share shelf+box live |

Both endpoints must be public NOTE cards; dedupe against existing edges. Theology is
sealed as CONCORDANT, never HOLDS.

## SOP-10 — Who can see this?

Answer these **before** shipping any endpoint that reads or lists:

1. **Who may call it?** Public, or only the holder of the key? Anonymous-by-default is a
   decision, not an absence of one.
2. **What can be enumerated with it?** A listing endpoint is an oracle. If it returns ids,
   assume every id will be fetched. Never list other people's records publicly — return only
   the caller's own, proven by key.
3. **What is in the summary field?** Titles are the trap: a thread's title is the person's
   first message verbatim, so "just the titles" leaked crisis disclosures.
4. **Protected by secrecy or by ownership?** An unguessable id is secrecy — it fails the moment
   anything enumerates it. Bind the record to a key and check the key.
5. **Has the surrounding assumption changed?** `/threads` was safe when threads were
   browser-held and ephemeral, and became a breach when they persisted. Re-ask on every change
   of storage, identity or persistence.

When removing such an endpoint, **delete it** rather than gating it: dead code that still knows
how to enumerate is one edit away from being live again.

## SOP-9 — Environment traps (Windows/PowerShell)

- Python heredocs: use **forward slashes** (`D:/path`) — `\v`, `\i`, `\k` become escapes.
- Quoted heredoc (`<<'PY'`) does not interpolate `$VAR`; pass paths as literals.
- PowerShell 5.1: no `&&`/`||`, no ternary; `Set-Content` needs explicit `-Encoding utf8`.
- Tailscale SSH (`nh-engine-1`) is unreliable here → use public IP + `~/.ssh/id_ed25519_nh`.
- Scanning ~11k files on the external drive exceeds a 2-minute tool timeout → tar once,
  ship one archive, process on the box.

---

*Verified live 2026-07-12.*

## SOP-11 — The suite must be whole before its result means anything

`tests/MANIFEST.txt` is the declared suite. `tools/check.py` compares it to what is on disk
and fails on either direction of drift:

* **listed but absent** — the file never ran; the gate would otherwise report PASS without it
* **present but unlisted** — a new test file that nobody declared

1. Adding a test file: add its name to `tests/MANIFEST.txt` in the same commit.
2. Deploying: sync the **whole** `tests/` directory (and `tests/fixtures/`), not single files —
   `scp -r tests/ nh@5.78.186.55:/home/nh/concordance-2/`
3. Never reference a fixture by absolute path. Vendor it under `tests/fixtures/` so the test
   runs on every machine, and the source lives in version control.
4. Two test files that both set `CONCORDANCE_DATA_DIR` at import share one store under a single
   pytest process — the first import wins. Give each ranking/ordering assertion an artifact
   unique to its own file rather than weakening the assertion.

## SOP-12 — Safety matching (crisis)

1. **One matcher.** `ask.is_crisis()` is it. Never import `_CRISIS_WORDS` to re-implement the
   check — every surface calls the function, and a test asserts `ask` and `router` agree.
2. **Normalize before matching.** `ask.normalize()`: lowercase, straighten smart quotes, drop
   apostrophes, collapse whitespace. Phrases are stored in that same form (`dont`, not `don't`).
3. **Never add exclusions.** A false positive costs an unnecessary helpline. A false negative
   costs a person. Do not "fix" `die my hair` with a negative lookahead — that is a bypass.
4. **Widening the list needs a test, not a deploy.** Add the phrasing to `_WAS_MISSED` in
   `tests/test_ask.py`; it locks routing on both `ask` and `router`.
5. **Test how people type**, not how you write: no punctuation, phone autocorrect, euphemism
   ("unalive"), and mid-sentence ("i want to end it, i have 2 kids").
6. **Crisis is never enriched.** No gate, no scripture-as-fix, no auditor. Numbers in the
   message must not summon arithmetic at someone who needs help.
