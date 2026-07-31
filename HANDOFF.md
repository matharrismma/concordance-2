# Handoff — Narrow Highway / Concordance 2.0

> **THE REMAINING BUILD IS DONE (Fable, 2026-07-28 ~12:30). Head: `580875d`, pushed. Gate:
> `=== GATE PASS ===` 866/866, exit 0. Deployed and live-verified on both surfaces.**
>
> Matt said "go through and build what is remaining," and §6's worklist is now built end to end:
> - **Item 9 complete**: study tables (6/262 entries), the Atlas (72 places, honest blanks),
>   commentaries evaluated (Henry serving; Gill/Clarke recorded as bounded work), and the
>   **Encyclopedia AS Cards** (Easton's 3,962 in four card-catalog drawers, catalog.html).
> - **Item 2 complete**: CONSENT — scoped signed expiring grants, revocation tombstones, and
>   `consent.guard()` installed before any on-behalf write exists. Member ≠ proxy preserved.
> - **Item 4 complete**: the moderation floor — report (1 = claim, 3 distinct = held for a HUMAN,
>   Deut 19:15), viewer-side block, report buttons live on community.html.
> - **Matt's directives from the session**, all built: the **last mile** (right page or ask —
>   "Jud 1:2" returns candidates; "Jud 5" self-disambiguates; prefix inference floors at 3 letters
>   after "is 15" resolved as Isaiah 15), the **storyboards** (12 narratives charted in the Bible,
>   17 shared movements that mix and match, framing on every payload: "a reference point, not an
>   identity"), the **quick-find index** (one door across the whole reference section), and the
>   **14 voices** under the knowledge-logistics/unify-the-church frame (honest on both ends; White
>   carries both positions; Graham facts-and-pointer only).
> - **Found and fixed along the way**: Song of Solomon was UNREACHABLE live (the core reader's
>   book regex admitted no spaces); guarded now by a 66-book sweep.
> - **Still open, deliberately**: shard wiring (the ledger now holds the measured peaks — nh-org
>   3.2 GB + ~1 GB swap); Gill/Clarke acquisition (needs a network fetch Matt should see land);
>   nav generation (Matt chose leave-alone); the ISBE as a future second encyclopedia deck.
>
> The section below is the prior handoff, kept for the trail.

> **FINAL REFINEMENT DONE (Fable, 2026-07-28 ~09:45).** Matt decided the three flagged items and all
> three are executed, gated (812/812, exit 0), deployed, and live-verified on BOTH surfaces:
> **(1)** the four Wikipedia cards are **removed** (PD-only gate holds); **(2)** the 552 unrooted
> islands are **rooted with shelf spines** — ten spines, two redirects, 5,187 cards grafted locally
> and 5,225 on the box via `tools/graft_shelf_spines.py` (the box surfaced 24 extra old-vintage
> cards, incl. a `domains` shelf that exists ONLY there — handled under the same found rule);
> **(3)** per-page navs left alone. **Live final state, both surfaces:**
>
>     total = 466,401   nested = 466,401   semantic_only = 0   isolated = 0
>
> "Everything connects — nothing isolated" is now a measured fact the overview itself reports, not a
> slogan. Ratchet lowered to 0; any future rise is a regression with a named culprit. The section
> below is the pre-refinement handoff, kept for the trail.

**Written 2026-07-28 ~09:10. Head of `master`: `f61079d` (pushed). Gate: `=== GATE PASS ===` 812/812,
exit 0. Everything below is deployed and live-verified on both surfaces.**

---

## Read these first, in this order

1. **`docs/COMPLETION_CONTRACT.md` — FROZEN, and it is the authority.** §5 is the machine-testable
   DONE list, §6 the finite worklist, §7 the drift ledger. **Read §7 in full before touching
   anything** — it is where the last two nights' findings live, including two entries that record my
   own mistakes and their corrections.
2. This file, for state and gotchas.
3. The memory index at
   `C:\Users\hdven\.claude\projects\C--Users-hdven-OneDrive-Desktop\memory\MEMORY.md` — the standing
   guidance section at the top is the working discipline, not decoration.

## The ethos, compressed (load-bearing — do not optimize it away)

The five-part kernel: **find · distinguish · verify · preserve the trail · never silently upgrade
authority.** One mission string everywhere. No sign-in. Keys born on the device. Nothing generated —
the engine eliminates what is not the answer and hands back a re-checkable seal. **We live in the
nuance:** where scholarship genuinely disagrees, carry both positions rather than flattening to one.
The moat sits at 60/60 with **0 false positives** — it has never sealed a falsehood.

Serve families and children first. Free, no account.

---

## Environment

- **Repo:** `C:\Users\hdven\OneDrive\Documents\Claude\Projects\concordance-2` (branch `master`).
- **Gate:** `PYTHONPATH=src python tools/check.py` → must print `=== GATE PASS ===`. **Read the real
  exit code**, not the tail of the log. ~5–6 min. Run it backgrounded and wait for the notification.
- **Deploy:** `sh tools/deploy.sh <repo-relative files…>` — one tar-over-ssh, **staggered** restarts
  (witness `nh-org` :8001 first, health-polled, then secular `nh-com-2` :8002), so one face is always
  up. Patient polling built in.
- **Live:** `narrowhighway.com` = secular (:8002), `narrowhighway.org` = witness (:8001), behind
  Caddy. Both load the corpus into RAM at boot; the port binds only after that.
- **Droplet:** `nh@5.78.186.55`, key `~/.ssh/id_ed25519_nh`, path `/home/nh/concordance-2`.
- **Git:** never `git add -A`. Keep OUT of commits: `data/*.jsonl*`, `data/shards/`,
  `.claude/launch.json`, `docs/reviews/`, `HANDOFF.md`.

## Gotchas that cost real time (do not re-learn)

1. **Local dev server takes ~10–30 s to bind** (corpus load), **80 s+ if a gate is running.** A first
   `000`/exit-7 is normal, not failure.
2. **Orphaned `serve_local.py` processes serve stale code** and look exactly like a code bug.
3. **Background `Bash` with `cd &&` fails (exit 127) here.** Write a small `.sh` in the scratchpad.
4. **Env leakage between test files is the #1 cause of "passes alone, fails in the suite."** Three
   variants: `CONCORDANCE_BIBLE_EN`, `CONCORDANCE_DATA_DIR`, and **`CONCORDANCE_STACKS_DIR`, which
   takes PRECEDENCE over `CONCORDANCE_DATA_DIR`**. Fix by asking the module where state lives (e.g.
   `stacks._card_path(cid)`) plus an `autouse, scope="module"` fixture that restores what it found.
5. **Two golden guards fail on any new route or page, by design:** `tests/test_routes.py`
   (`GOLDEN_API_GET` + `GOLDEN_RATELIMITED` — a write needs BOTH) and
   `tests/test_site.py::test_the_palette_reaches_every_public_page` (add to `TOOLS` in
   `site/nh-tools.js`, or to the `excused` set).
6. `stacks.put_card` **flattens `extra`** onto the card — it is not nested.
7. **Windows console mangles UTF-8 on print** (`λ`, `—`) and raises `UnicodeEncodeError` mid-run.
   Write ASCII-safe probes: `s.encode('ascii','replace').decode('ascii')`.
8. **`narrowhighway.com` is blocked in the Browser pane by policy** — you cannot render the live site
   there. Verify served assets with `curl` and check JS logic directly, and say so plainly rather
   than implying you watched a page paint.
9. **Register every new test in `tests/MANIFEST.txt`** or suite-integrity fails.

---

## What shipped since the previous handoff (`087b3c8` → `f61079d`)

Four commits, each gated, deployed, and live-verified.

### `b5b9794` — SYSTEM_ERROR distinct from BROKEN (contract §5.6)

Auditing §5 line by line instead of declaring it. **`SYSTEM_ERROR` appeared in zero source files**,
and `verify_derivation` confessed the merge in its own comment: `else:  # MISMATCH / ERROR / broken
link`. Reproduced through the public API:

    speed_of_wave=343,    frequency_hz=440, wavelength_m=99     -> BROKEN
    speed_of_wave="fast", frequency_hz=440, wavelength_m=0.7795 -> BROKEN

The first is a falsehood; the second is **our verifier failing to parse an input**. Identical output.
Someone checking a dose, a wage, or a load rating was told their claim was false when the truth was
that we could not check it — the mirror of the kernel's fifth clause.

Fixed with precedence **BROKEN > SYSTEM_ERROR > INCOMPLETE > HOLDS**, so an engine error never becomes
a hiding place for a real falsehood either. Seals as QUARANTINE, never REJECT (a citable "rejected"
would outlive the bug). The auditor counts `broken` and `unchecked` separately. Said in words on
`audit/check/ask/reason.html`, and documented for agents in the MCP `verify` description and
`llms.txt`.

The gate then found a **second, live instance**: the expression size guard meant a large but *true*
expression was already being told it was false. Changed only after confirming the security property
held — refused in 0.000 s, never evaluated, never sealed as holding.

Also §5.5: the mission string was present in `llms.txt` but **wrapped across a `> ` blockquote**,
unmatchable by a machine on the one document written for agents. Reflowed and guarded.

### `979ec05` — §5 audited live, connectedness recorded with its measurement

### `825c5d2` — the orphan LEAK, not the orphans

`find._mint_doc` (the tortoise, which fetches PD sources when the corpus cannot answer) hardcoded
`"connections": []`. Every source it kept was **born an orphan, one more per fetch**. Local 15;
**production 41.** Fixed at the source with two spines defined **in code, not a data file** —
`web_cache.jsonl` is untracked, so a data-file spine would vanish on a fresh box and the leak would
return. **Local 15 → 0, box 41 → 4.**

### `f61079d` — the map tells the truth about itself

`graph.overview` reported only `connected` (the semantic plane), so `gutenberg` — 77,700 fully-nested
cards — read `connected: 0` and looked abandoned. Every card now lands in exactly one bucket, per
shelf and in total, each count carrying a `means` line:

    total 466,395 = nested 461,191 + semantic_only 5,200 + isolated 4     (live, right now)

---

## §5 status — all seven checked live against one commit

| # | Criterion | State |
|---|---|---|
| 5.1 | gate passes | ✅ 812/812, exit 0 |
| 5.2 | usefulness ≥ 90%, no category at 0 | ✅ 21/21 (100%) |
| 5.3 | nesting, no orphans | ⚠️ **passes as written** — see gaps 1 and 2 |
| 5.4 | no private key on the wire | ✅ 0 returned, 0 accepted, 0 advertised |
| 5.5 | one mission string everywhere | ✅ 1/1/1 live |
| 5.6 | security P0s incl. SYSTEM_ERROR | ✅ fixed this session |
| 5.7 | counts from one manifest | ✅ 14 integers, every one with a `means` |

---

## Open, honestly — the four things worth your refinement

### 1. Four cards need Matt's decision, not a default (blocking, tiny)

`isolated_nodes: 4` live. Wikipedia cards on a `web` shelf — *Telephone*, *Sinking of the Titanic*,
*Printing press*, *Food preservation* — created 2026-07-23, `verified: false`, minted by a path that
**no longer exists in `src/` on either side**. Wikipedia is CC-BY-SA, which collides with the standing
**PD-only gate**.

Either give `web` a spine stating its real (unverified, non-PD) authority tier, or remove the four.
**This is a doctrinal call plus a data deletion — ask Matt, do not default it.**
`tools/graft_orphans.py` already refuses to guess and exits non-zero while they remain.

### 2. 552 cards sit in unrooted islands (real, bounded, needs judgement)

Walking both planes from the Floor: 465,456 of 466,008 reachable; **552 are not** — `codex` 451,
`classics` 39, `animation` 24, `maker` 11, `recipes` 11, `hymns` 10, `patristics` 4, `dictionary` 2.

They are **not broken**: zero dangling edges, every reference resolves. They are closed clusters
(codex notes and Boethius sections bound by `same_section`) with no edge out to anything rooted.

Grafting e.g. the codex note "Revelation 5" to its scripture card is a *real* relation — but
**choosing that match is authoring, not finding**, which is why the count is ratcheted in
`tests/test_reachable_from_the_floor.py` rather than minted. If you take it on, do it as a deliberate
pass with a rule that can be checked, and **lower the ratchet constant** when it drops. **Do not close
it by minting weak edges** — the 53-false-edge cleanup is the precedent; an edge carrying no real
relation makes the map lie.

The full walk costs **11.7 s and ~162 MB peak** (measured), which is why it lives in the gate and not
in `overview()`, on services already at ~2.8 GB RSS.

### 3. CONSENT — the other half of contract worklist item 2 (needs design input)

Proof-of-possession is **DONE**, guarded by four test files. Consent is **not**: there is no
human-authorized write path for an agent acting **on a human's behalf, with their data**.

**Note the distinction before building:** an agent that confessed and holds its own covenant key,
speaking its own words, is a **member, not a proxy** — and a human needs no approval to speak in the
fellowship, so demanding it of agents would break the parity Matt asked for. **Do not build a blanket
consent gate.**

### 4. Smaller, still open

- **Shard engine unwired.** `corpus_db.py` exists, `data/shards/` built locally (~590 MB), the droplet
  has none, and nothing imports it but its builder. Each service holds **~2.8 GB RSS** (measured; that
  it is *mostly corpus* is inference — **profile before promising a reclaim**).
- **Denominational voices — NOT STARTED.** One major voice per tradition (Ellen G. White, Billy
  Graham…), chosen by *their* reckoning, honest on both ends, calibrated by our tools, always
  resolving to Christ. Extends `card_churches.py`; do not build a new silo.
- **V1 back-matter remaining:** Maps/Atlas, topical index / weights & measures / book intros / names
  of God, commentaries (Matthew Henry local; evaluate Gill & Clarke), and the **Biblical Encyclopedia
  as Cards** with a card-catalog UI (ISBE 1915 or Smith's — checked: `gutenberg_cards.jsonl.gz` does
  **not** already contain them).
- **Nav drift:** ~28 pages still lack Harmony/Timeline links. The durable fix is generating nav from
  one list, but a prior decision deliberately left per-page navs alone — **check with Matt first.**
- `proof.html`'s **330 / 235 / 53** are a past assay run, not a live capability. A fixed number is
  correct there. **Do not "fix" them** without the real artifact.
- The security-weakness sweep is **paused, not abandoned**.

### Deliberately NOT done — please do not "finish" these

- **The verse↔lemma graft.** Both directions are already served (`/word_study?strongs=` →
  occurrences; `/original?ref=` → tagged words), with **370,833 pairs resolving and ZERO unresolved**.
  Minting them as connection cards would add nothing a reader cannot already get, while inflating the
  corpus ~77% and burying the authored edges.
- **`BROKEN_CLAIM` / `OUT_OF_SCOPE`.** §7's taxonomy names them, but the live vocabulary is
  `BROKEN`/`INCOMPLETE` across the engine, seals, tests and five pages. A sweeping rename for cosmetic
  conformance risks real breakage and buys nothing a reader can feel.
- **`private_key` on the MODULE signatures.** It is gone from the wire and stays in the library — on
  your own box, handing the library your own key is legitimate. `tests/test_no_keys_on_the_wire.py`
  guards **both** directions; if its "local params still exist" assertion fails, the retirement went
  too far.

---

## The rhythm that held

**Read the real state → change → prove it (revert-and-confirm-the-test-fails for a fix; measure for a
perf claim) → full gate, real exit code → deploy → verify live on both surfaces → commit by explicit
path → push.**

Four habits earned their place and are in memory as standing guidance:

1. **Our failure is not their falsehood.** "We could not check" is a fact about us. Three states,
   never two. Never *seal* our failure as a judgement.
2. **Follow the guarantee all the way to the reader.** Correct server-side and invisible to the
   person is not done — found **five times** in one night. For agents, the surface is the tool schema
   and `llms.txt`.
3. **Fix the PATH, not the instances.** A backlog you clean once; a leak refills. **A production count
   higher than local is the signature of an active leak** — run tools against the box, not only
   locally.
4. **When a check says "broken", check the check first.** Wrong probe shapes outnumbered real bugs
   this session; one reading of "0 orphans out of 0 nodes" would have been reported confidently and
   been completely wrong.

**The one I most want to pass on:** I wrote two ledger entries this session that were **wrong** — an
endpoint miscount, and a "313,944 unconnected cards" figure whose real value was 15. Both times the
cause was identical: **reporting a probe's output as if it were the thing the probe was named after.**
Both are corrected in §7 with the originals struck through rather than deleted, so the corrections are
auditable. Check your own entries the way you would check the code.
