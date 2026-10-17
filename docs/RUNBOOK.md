# RUNBOOK — the one runbook for narrowhighway.com / .org / .tv

The box, the services, the timers, how a change goes live, and how it is proved. This is the
**one** operational document: the old bootstrap (`DEPLOY.md`, verified live 2026-07-12) was merged
into it on 2026-10-16 and `DEPLOY.md` is now a pointer here. The dedicated MCP host has its own
note, [`MCP_HOST.md`](MCP_HOST.md); the Caddy dark/un-dark switch is [`../deploy/CADDY.md`](../deploy/CADDY.md);
the host → backend table and the 1.0 retirement are [`../deploy/README.md`](../deploy/README.md).

**Consolidated 2026-10-16** from DEPLOY.md + RUNBOOK (both verified live 2026-07-12), MCP_HOST.md
(verified live 2026-10-16), `deploy/Caddyfile` (the `/mcp` route applied live 2026-10-16) and the unit
files in `deploy/`. The merge itself did not touch the box; the next deploy re-verifies it (§9).
✅ = confirmed by inspection on the date given. ⚠️ = still open.

---

## 1. Topology — what runs where

- **Origin:** ✅ Hetzner, `nh@5.78.186.55`, deploy key `~/.ssh/id_ed25519_nh`, path `/home/nh/concordance-2`.
  All three domains A-record straight to it.
- **Edge:** ✅ Cloudflare is in front as **DNS only (grey cloud)** — no `cf-ray`, `Server: NarrowHighway`;
  TLS terminates on our Caddy. Keep it that way (§7).
- **Reverse proxy:** ✅ `caddy.service` — Let's Encrypt TLS, host routing, the `/mcp` route (§4). The live
  Caddyfile is `/etc/caddy/Caddyfile` on the box; `deploy/Caddyfile` tracks it, `tools/deploy.sh` never
  rsyncs it.
- **App:** ✅ systemd, **not Docker**. The units are the files in `deploy/`:

| Unit | Role | Listens | ExecStart (abridged) |
|---|---|---|---|
| `nh-engine.service` | **ONE process, both faces, one corpus** — the current unit | witness `:8001` + secular `:8002` | `python -m concordance serve --surface both --witness-port 8001 --secular-port 8002` |
| `nh-mcp.service` | **the dedicated MCP host** — the agents' door, decoupled from the site engine (`MCP_HOST.md`) | `:8003` | `python -m concordance serve --surface secular --port 8003` |
| `nh-org.service` + `nh-com-2.service` | **the fallback pair** — the two-process layout `nh-engine` replaced (2026-10-08); disabled while `nh-engine` is enabled | `:8001` / `:8002` | `serve --surface witness --port 8001` / `serve --surface secular --port 8002` |

  Every unit runs `/home/nh/concordance-2/.venv/bin/python` with `PYTHONPATH=…/src`,
  `CONCORDANCE_DATA_DIR=…/data`, and `EnvironmentFile=-/home/nh/concordance-2/.env` (§10).
- **Caddy → backends:** `narrowhighway.com`, `api.narrowhighway.com`, `narrowhighway.tv` → `:8002`;
  `narrowhighway.org` → `:8001`; `api.narrowhighway.com/mcp*` → `:8003` (§4). `.tv`'s bare `/` is
  rewritten to `/tv`. `/releases/*` on `.com` is a `file_server` over `/srv/nh-releases` (the field pack
  and the ZIM, cut by `nh-zim.timer`).
- **Data:** ✅ `/home/nh/concordance-2/data/` — the keeping, **gitignored**, populated on the box by the
  seeders (never deployed as files). `cards.jsonl` is append-only, last line wins on a duplicate id; card
  and graph data hot-reload by mtime. **Code changes need a restart.**
- **Box-owned files:** `site/theories.html` is rewritten **on the box** by the hive's theorymap step
  (`tools/hive_cycle.py`, daily 10:00 UTC). The box's copy is the live truth and the repo's is the seed;
  `verify_deploy.py` reports it under its own `BOX_OWNED` heading, never as drift. Do not "fix" that
  DIFFERENT, and do not deploy the repo's copy over it.
- **Not in the path:** no Docker, no Railway, no `api/app.py`, no 1.0 (`/home/nh/Lighthouse` is preserved,
  stopped — `deploy/README.md`).

## 2. The standing timers (`deploy/*.timer`, all user `nh` unless noted)

| Timer | When (UTC) | What it runs |
|---|---|---|
| `nh-traffic` | every 10 min (root) | `tools.traffic_rollup` — Caddy access logs → `data/traffic.json` |
| `nh-watch` | hourly | `tools/watch.py` — the watchman: live invariants over the wire |
| `nh-storagebox` | 03:40 nightly | `tools/ark/storagebox_sync.sh` — the keeping to the Hetzner Storage Box (inert until configured) |
| `nh-zim` | Sun 04:30 weekly | the field library cut as a Kiwix ZIM into `/srv/nh-releases` |
| `nh-assay` | 05:10 nightly | `tools/live_assay.py` — every probe that ever passed must still pass; recall may only rise |
| `nh-benchmarks` | 05:20 nightly | `tools/benchmarks.py` — every domain golden, the derivation moat, every admitted spec, ratcheted |
| `nh-restore-drill` | 1st of the month 05:30 | `tools/ark/restore_drill.sh` — restore the newest nightly tar to scratch and check it |
| `nh-hive` | 10:00 daily | the hive (dig, fill, refine, connect) — writes the box-owned `site/theories.html` |

`systemctl list-timers 'nh-*'` shows the next and last runs. Install a new or changed timer with the
same `cp` + `daemon-reload` + `enable --now` as a service (§8).

## 3. How a change goes live — the deploy ritual

✅ **Push to `master` does NOT deploy.** `/home/nh/concordance-2` is not a git checkout; there is no git
on the box. The ritual is `tools/deploy.sh`, and it is the whole ritual:

```bash
PYTHONPATH=src python tools/check.py            # the local gate first: must print === GATE PASS ===, exit 0
sh tools/deploy.sh src/concordance/web/api.py site/index.html   # repo-relative paths, exactly the files you mean
```

What `deploy.sh` does, in order (read the script; it is the authority):

1. **Snapshot** the files it is about to replace into `/home/nh/deploy-rollback/<timestamp>/` (`prev.tar` +
   `added.txt`; the last 10 snapshots are kept).
2. **One `tar | ssh` transfer** of exactly the files named — never `git`, never the whole tree.
3. **Restart and poll.** If `nh-engine` is enabled: restart it once and poll `/health` on **both** `:8001`
   and `:8002` (up to 90 s each; a first `000` right after a restart is normal — the port binds only after
   the corpus loads). If it is disabled, the fallback order: `nh-org` first as the canary, polled back to
   200, **then** `nh-com-2`. Either way, a port that does not come back **reverts the snapshot** and
   restarts, so a bad deploy never reaches both faces.
4. **`nh-mcp`** is restarted after the site engine is back (same code — it must not drift), non-fatal: a
   slow MCP never reverts a good site deploy, it is reported.
5. **The gate, on the box**: `tools/benchmarks.py --gate`, `tools/live_assay.py`, `tools/frontdoor.py --gate`,
   `tools/recall.py --gate`. Any regression **reverts and restarts** — a deploy refused, in public.
   `DEPLOY_NO_GATE=1` skips it: emergencies only, and say so in the record.
6. **`tools/verify_deploy.py --soft`** — proves the box matches `HEAD` blob-for-blob (CRLF normalised) over
   the HARD set (`src/ tests/ tools/ conductor/ site/` + `README.md HANDOFF.md pyproject.toml`); SOFT
   drift (`docs/ eval/ deploy/ …`) is counted, listed with `--all`, never fatal. Advisory at the end of
   a deploy; run it by hand (`python tools/verify_deploy.py`, exit 1 on HARD drift) whenever "the box
   should match". `--soft --all` is the deploy set: everything it lists as DIFFERENT or MISSING is what
   still has to be sent.

**Data changes are not deploys.** Cards are appended on the box (hot-reload; restart optional) by the
seeders — run them on the box, idempotently, then restart if the seed touches code paths. Never deploy a
`data/` file over the box's copy.

**SSH:** the public-IP + key path above. Tailscale from this workstation has been unreliable; do not
depend on it.

## 4. The `/mcp` route (Caddy)

`api.narrowhighway.com/mcp*` is reverse-proxied to the dedicated host on `:8003` **before** the host's
`:8002` upstream; everything else on that host still goes to the site engine. Applied to the live
Caddyfile 2026-10-16 and tracked in `deploy/Caddyfile`. To re-apply on a rebuilt box: back up, edit,
`sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile`, then `sudo systemctl reload caddy`
— never reload an unvalidated file. Details and the verification calls: [`MCP_HOST.md`](MCP_HOST.md).
`narrowhighway.com/mcp` and `narrowhighway.org/mcp` still answer from the site engine (the full catalog;
profile mounts at `/mcp/<name>`).

## 5. Verify the deploy landed

```bash
curl -s https://narrowhighway.org/health          # {"ok":true,"surface":"witness",...}
curl -s https://narrowhighway.com/health          # {"ok":true,"surface":"secular",...}
curl -s https://narrowhighway.com/graph | head -c 200                        # live JSON
curl -s -X POST https://narrowhighway.com/verify -H content-type:application/json \
  -d '{"mode":"equality","params":{"expr_a":"2+2","expr_b":"4","variables":{}}}'   # verdict HOLDS
curl -s 'https://narrowhighway.org/word_study?strongs=G26'   # agape — witness-only
curl -s 'https://narrowhighway.com/word_study?strongs=G26'   # 404 — gated off the secular reach
ssh -i ~/.ssh/id_ed25519_nh nh@5.78.186.55 "systemctl is-active nh-engine nh-mcp caddy"
python tools/verify_deploy.py                     # exit 0 = box == repo on the HARD set
```

Verify the **runtime**, not an HTTP 200: a 200 from a stale process looks identical to a deploy. The
box gate (§3 step 5) is the proof that the engine still measures the same; `verify_deploy` is the proof
that the bytes are the ones you sent. ⚠️ **HEAD returns 501** — the app implements GET; health-check with GET.

## 6. Rollback

- **A deploy that failed its poll or its gate already reverted itself** (§3) — `/home/nh/deploy-rollback/<ts>/`
  holds `prev.tar` + `added.txt`; the script restores the first and deletes the second.
- **To revert by hand**: `cd /home/nh/concordance-2 && tar -xf /home/nh/deploy-rollback/<ts>/prev.tar`,
  delete each path in `added.txt`, restart `nh-engine` (or `nh-org` then `nh-com-2`) and `nh-mcp`.
- **Older than ten deploys**: re-deploy the files from the git commit you want — the repo is the history;
  the box has none.
- **Engine layout**: `sudo systemctl disable --now nh-engine; sudo systemctl enable --now nh-org nh-com-2`
  returns to the two-process layout; `deploy.sh` adapts to whichever is enabled.
- **Caddy**: backups live beside the live file (`/etc/caddy/Caddyfile.bak.*` — `deploy/README.md` names
  them); `sudo cp` one back, validate, reload.
- **The keeping**: the nightly tar on the box, the Storage Box copy (`nh-storagebox`), and the monthly
  restore drill prove it restores (`tools/ark/`).

## 7. Domains, the allowlist, and the edge posture

The operator holds `.com`, `.org`, `.tv`; all three resolve to the origin and serve. The host allowlist
lives in **Caddy on the box**, not in the repo: a new hostname is a Caddy edit + validate + reload.
Cloudflare stays **DNS-only (grey cloud)**: an orange-cloud proxy would terminate TLS inside the trust
boundary of a conversation we promise is sealed. The pre-release dark lock (every site 503 except the
reviewer's IP) and its un-dark are in `deploy/CADDY.md`. Edge rate limiting is **not** present (the box's
Caddy has no `rate_limit` module); the application layer rate-limits every heavy public route
(`src/concordance/ratelimit.py`).

## 8. Bootstrap — standing a box up from scratch

Only when the box is new or rebuilt. Everything here is the operator's: it touches DNS, the server and
live traffic, and nothing runs by itself.

1. **Prerequisites.** A server with Python ≥ 3.10 and Caddy; DNS A records for `narrowhighway.com`,
   `.org`, `.tv` (and `www`, `api.`) → the box; a `nh` user with `/home/nh`.
2. **Code.** Put the repo tree at `/home/nh/concordance-2` (rsync or a one-time clone — it is not kept as
   a checkout afterwards), then a **dedicated** venv:
   ```bash
   cd /home/nh/concordance-2 && python3 -m venv .venv
   .venv/bin/pip install -e ".[math,signing,schema]"        # sympy (the moat), cryptography (signing), the heavier verifiers
   PYTHONPATH=src .venv/bin/python -m pytest tests/ -q       # the suite is green before anything is enabled
   ```
3. **Data.** `data/` is gitignored: run the seeders on the box (idempotent) or rsync a local `data/` up.
   The engine runs without it (the moat, the verifiers and signing need nothing); search, Scripture and
   word study need it.
4. **Secrets.** Create `/home/nh/concordance-2/.env` (chmod 600) — §10.
5. **Services and timers.**
   ```bash
   sudo cp deploy/nh-*.service deploy/nh-*.timer /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now nh-engine nh-mcp
   sudo systemctl enable --now nh-traffic.timer nh-watch.timer nh-assay.timer nh-benchmarks.timer \
        nh-storagebox.timer nh-restore-drill.timer nh-zim.timer nh-hive.timer
   systemctl status nh-engine nh-mcp                      # both active; the ports bind after the corpus loads
   ```
   Leave `nh-org` and `nh-com-2` installed but **disabled** — they are the fallback (§1, §6).
6. **Caddy.** `sudo cp deploy/Caddyfile /etc/caddy/Caddyfile` (or merge its blocks into the existing
   file), `sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile`, `sudo systemctl reload caddy`.
   Confirm the `/mcp` route (§4) is in the `api.` block.
7. **The keep** (operator dashboard, `keep.html`) is operator-gated: served only to localhost or a request
   carrying the operator token, 404 to everyone else. Set `CONCORDANCE_KEEP_TOKEN` in `.env` (or a systemd
   drop-in), restart, open `https://narrowhighway.org/keep.html?token=…`. Rotate by changing it.
8. **Verify** (§5), then run `python tools/verify_deploy.py` from the workstation: a fresh box must report
   no HARD drift.

Docker is an alternative (`docker build -t narrowhighway .`, one container per surface with `-v data:/data`),
not the live path.

## 9. Keep this document true

Every topology claim above carries the date it was last inspected. If a deploy changes topology, a unit,
a port or a timer, **this file changes in the same pass** (SOP-4 in `SOP/SOP.md`), and the next deploy
re-verifies §1 and §5. A runbook that is not re-verified sends an operator down a path that fails
silently — the 1.0 runbook did exactly that (the record is in `archive/LESSONS.md`, 2026-07-12).

## 10. Secrets and env — never in the repo

`/home/nh/concordance-2/.env` (chmod 600, gitignored; every unit reads it with `EnvironmentFile=-`):
`ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID` (the cloned voice for `/speak`), `CONCORDANCE_KEEP_TOKEN`, and
the feature switches the box turns on (`STIGMERGY`, `QUORUM`, `FLOCK`, `ELDERSHIP`, `ALLOCATION`,
`ALIGNMENT`, `INHIBITION`). The deploy key `~/.ssh/id_ed25519_nh` is 0600, workstation-only, never in git
or OneDrive. Nothing from `.env` goes in a commit, a CI log, or a chat; rotate anything exposed.
