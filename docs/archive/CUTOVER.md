# .com cutover — a reversible, shadow-tested design

How `narrowhighway.com` could move from **1.0** (`nh-engine`, :8000) to **2.0-secular**
(`nh-com`) *without a leap of faith* — shadow-tested first, flipped in one command, rolled
back in one command. The flip mechanism is easy; the real gate is feature parity
(see PARITY_MATRIX.md). **This is a design, not an instruction to execute.**

## Standing precondition
Do **not** flip until the cutover-blockers in PARITY_MATRIX.md are resolved or explicitly
accepted as losses. Today they are **not** resolved — 2.0 lacks the keep, Walk, library UI,
almanac, atlas, and ~100 granular tools that `.com` users rely on. So the flip is **gated**.

## Phase 0 — safety net (DONE)
- 1.0 fully archived to the 12TB drive (code+data+config, sha256-verified).
- 2.0 data backed up (12TB + daily on-droplet cron) + hourly integrity check.
- 1.0 stays installed and `enable`-able throughout — rollback is always one command.

## Phase 1 — run 2.0 alongside 1.0 (no traffic change)
Run 2.0-secular on a **temp port**, never touching :8000:
```bash
# a shadow unit (copy of nh-com.service) on :8002, NOT enabled on :8000
ExecStart=… -m concordance serve --host 127.0.0.1 --port 8002 --surface secular
sudo systemctl start nh-com-shadow      # 1.0 still owns :8000 and .com
```
Optionally expose it at a temp hostname (e.g. `v2.narrowhighway.com` → :8002) for human
testing — additive, reversible, does not touch the `.com` block.

## Phase 2 — shadow-test (diff 1.0 vs 2.0)
A script hits both stacks with a suite of real requests and diffs the comparable ones:
- **Comparable (must match / improve):** `/health`, the moat (`/derivation/verify` —
  preserved as a 2.0 alias), `/search` shape, `/seal`, MCP `initialize`/`tools/list`.
- **Expected-different (the parity gaps):** every 1.0-only tool/page → record as a known loss
  from PARITY_MATRIX.md, not a regression. The shadow-test's job is to surface *surprises*.
- Acceptance: zero diffs on the comparable set; the loss set equals the matrix (nothing
  unexpected); 2.0 integrity check green; moat 58/58.

## Phase 3 — the flip (one command, off-hours)
```bash
sudo systemctl stop nh-engine && sudo systemctl disable nh-engine      # free :8000
sudo cp deploy/nh-com.service /etc/systemd/system/ && sudo systemctl enable --now nh-com   # 2.0 on :8000
# Caddy .com already → :8000 (no Caddy change needed); reload only if edited
curl -s https://narrowhighway.com/health   # expect surface:secular, v2
```

## Phase 4 — rollback (one command)
```bash
sudo systemctl disable --now nh-com
sudo systemctl enable --now nh-engine      # 1.0 back on :8000; .com restored
curl -s https://narrowhighway.com/health   # expect 1.0 body
```
1.0's code, venv, and data are untouched throughout, so rollback is instant and total. (This
is exactly the rollback that restored `.com` after the premature 2026-06-27 cutover.)

## Honest summary
The cutover is **mechanically trivial and fully reversible**. The reason it is gated is not
risk of the flip — it is that 2.0 is not yet a superset of what `.com` serves. Resolve the
PARITY_MATRIX blockers (piecewise, each greenlit), shadow-test, then flip with confidence.
Until then, the stable split (1.0 = .com, 2.0 = .org) is the right state.
