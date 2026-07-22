# RUNBOOK — how a change goes live

The day-to-day operational runbook for narrowhighway.com/.org/.tv.
For standing a box up from scratch (venv, data migration, systemd units), see
**[DEPLOY.md](DEPLOY.md)** — that is the bootstrap; this is the daily path.

**Verified live 2026-07-12** by direct inspection of the box and the public endpoints.
✅ = confirmed by inspection. ⚠️ = still open.

> **Why this document exists.** A runbook on the Desktop still described the 1.0
> Lighthouse app — Docker/uvicorn, push-to-`main`, `/version`, `/mcp/`. None of it is
> true: the live origin runs the **2.0 `concordance` app** under systemd behind Caddy,
> and deploys are **scp + restart** — there is no git repo on the box, so pushing to
> `main` deploys nothing. An operator following the old doc would have shipped nothing
> and believed otherwise. See §11.

---

## 1. Topology — what runs where

- **Origin:** ✅ Hetzner, `5.78.186.55`. All three domains A-record straight to it.
- **Edge:** ✅ **Cloudflare IS in front — as DNS only (grey cloud).** Nameservers for
  `.com`, `.org`, `.tv` are `nelly.ns.cloudflare.com` / `vin.ns.cloudflare.com`.
  Responses carry **no `cf-ray`** and `Server: NarrowHighway`, i.e. Cloudflare is
  **not** proxying — TLS terminates on our box (Caddy). This is exactly the posture
  §7 wants: no third party inside the conversation.
- **Reverse proxy:** ✅ `caddy.service` — TLS (Let's Encrypt) + host routing + the
  host allowlist.
- **App:** ✅ two systemd services, **not Docker**:
  - `nh-com-2.service` → narrowhighway.com (secular plane)
  - `nh-org.service` → narrowhighway.org (witness plane)
  - Interpreter: `PYTHONPATH=src /home/nh/concordance-2/.venv/bin/python -m concordance`
- **Data:** ✅ `/home/nh/concordance-2/data/cards.jsonl` — append-only; **last line
  wins on duplicate id**, so re-appending is idempotent. Card/graph data **hot-reloads
  by mtime** (no restart needed). **Code** changes need a restart.
- **Not in the path:** ✅ no Docker, no Railway, no `api/app.py`. `railway.toml` and the
  1.0 `Dockerfile` are vestigial.

## 2. How a change goes live

✅ **Push to `main` does NOT deploy.** `/home/nh/concordance-2` is not a git repo.
Deploys are **manual scp + restart**. (This was the single biggest error in the old doc.)

```bash
# code change (needs restart)
scp -i ~/.ssh/id_ed25519_nh <file> nh@5.78.186.55:/home/nh/concordance-2/<path>
ssh -i ~/.ssh/id_ed25519_nh nh@5.78.186.55 \
  "sudo systemctl restart nh-com-2 nh-org && systemctl is-active nh-com-2 nh-org"

# data change (cards) — append; hot-reloads, restart optional
cat new_cards.jsonl >> /home/nh/concordance-2/data/cards.jsonl
```

**Always also write the durable master** to `Lighthouse\data\cards\<id>.json` — that
is the backed-up source of truth (§8). Deploying only to the box means the next
restore loses it.

**SSH note:** ✅ Tailscale (`nh-engine-1`) is unreliable from this workstation
("failed to look up local user hdven"). Use the public-IP + key path above.

## 3. Verify the deploy landed

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://narrowhighway.com/          # 200
curl -s https://narrowhighway.com/graph | head -c 200                        # live JSON
ssh -i ~/.ssh/id_ed25519_nh nh@5.78.186.55 "systemctl is-active nh-com-2 nh-org"
```
Gate before shipping code: `PYTHONPATH=src .venv/bin/python tools/check.py` → `=== GATE PASS ===`.

⚠️ **HEAD returns 501** — the app implements GET, not HEAD. Health-check with GET.

## 4. What is actually live (measured 2026-07-12)

| Endpoint | Status |
|---|---|
| `/` · `/graph` · `/identity` · `/llms.txt` | ✅ 200 |
| `/ask.html` · `/threads` | ✅ 200 (both .com and .org) |
| `/thread/verify` | ✅ route exists (400 without args) |
| `narrowhighway.org/` · `narrowhighway.tv/` | ✅ 200 — already in the allowlist |
| `/version` · `/health/lite` | ❌ 404 — 1.0 endpoints, never ported |
| `/openapi.json` · `/mcp/` · `/connect` | ❌ 404 — **§9 is not shipped** |

## 5. Rollback

Releases are archived to the external drive by `local\release_archive.ps1` (§8):
`first` (genesis, immutable) · `previous` · `current`. To roll back, extract
`D:\NarrowHighway-Releases\previous\release-*.tgz`, scp the tree back, restart.
There is no git history on the box to revert to — **the archive is the rollback.**

## 6. Domains and the host allowlist

✅ The operator holds `.com`, `.org`, `.tv`; all three resolve to the origin and all
three **serve 200** — the allowlist admits them today. The allowlist lives in
**Caddy** on the box, not in the repo. Adding a new hostname = a Caddy edit + reload.

| Domain | Role |
|---|---|
| `.com` | the secular plane — the app, the map, the private conversation |
| `.org` | the witness plane — the keeping, teachings, the ledger |
| `.tv` | the voice/media surface |

## 7. Cloudflare posture (settled)

✅ **DNS-only (grey cloud) — keep it that way.** An orange-cloud proxy terminates TLS
and would sit inside the trust boundary of a conversation we promise is sealed. Reserve
any proxying for a purely public marketing host; **never** the conversation/sync path.

## 8. Durability — nothing is lost

Two scripts, both to `D:`:

- `local\backup_to_drive.ps1` — mirrors the substrate (`data\cards`, codex, almanac) +
  a dated 30-day snapshot. Last run: 14,082 cards, snapshot 17.1 MB.
- `local\release_archive.ps1` — **release retention**: pulls the *deployed* tree off the
  box and keeps **first (genesis, never overwritten) + previous + current**, with an
  append-only `manifest.json` (stamp, sha256, bytes, files) **so drift can be charted
  from the first release to today.** No-ops when nothing changed.

Policy: *the latest and best, but never lose the last — or the first.*

## 9. Exposing the engine to AI clients — NOT SHIPPED

⚠️ `/mcp/` and `/openapi.json` return **404** on the live 2.0 app. The `mcp/` module
exists in the repo but is not mounted/served. Until it is, the Claude-connector and
custom-GPT stories in the old doc are **aspirational, not available**. Local stdio MCP
still works and bypasses the edge.

## 10. Secrets & env (never commit)

Keys live in a `.env` on the box only (`ANTHROPIC_API_KEY`, `ELEVENLABS_*`, path vars).
Never in the repo, CI logs, or a chat. The deploy key `~/.ssh/id_ed25519_nh` is
0600, box-only, never in git or OneDrive. Rotate anything exposed.

## 11. The drift lesson (why this doc was wrong)

The old runbook was written against 1.0 and never revised after the 2.0 cutover, so it
confidently documented a deploy path that does nothing. **A runbook that is not
re-verified is worse than no runbook** — it sends the operator down a path that fails
silently. Mitigation is now an SOP: `docs/SOP/` — every runbook carries a
"verified live <date>" line, and re-verification is a step in the deploy SOP itself.

## Open items

1. ⚠️ Mount `/mcp/` + `/openapi.json` on the 2.0 app (§9) if connector access is wanted.
2. ⚠️ Decide OAuth-to-identity for per-user threads (needed for "one conversation across
   devices"; `identity.py` Ed25519 already exists as the sovereign alternative).
3. ⚠️ Reconcile the duplicate copy at `concordance-2\docs\DEPLOY.md` — one canonical home.
