# Deploy topology (narrowhighway.*)

The live routing on `nh-engine-1`, recorded here for recoverability. Caddy terminates
TLS and reverse-proxies each host to a backend.

## Hosts → backends (as of 2026-07-02 — 1.0 RETIRED, everything is 2.0)

| Host                     | Backend            | What runs there                              |
|--------------------------|--------------------|----------------------------------------------|
| `narrowhighway.com`      | `:8002` (2.0)      | **2.0 secular face** — front door, app, engine, seals, and the card permalinks (`render_card_html` at `/card.html?id=` and `/card/<id>`) |
| `api.narrowhighway.com`  | `:8002` (2.0)      | **2.0 secular** — verify / derivation.verify / search / seal / mcp / identity |
| `narrowhighway.org`      | `:8001` (2.0)      | **2.0 witness face** — the full Word (scripture, dictionary, signposts, the Gate) |
| `narrowhighway.tv`       | `:8001` (2.0)      | **2.0 watch/listen/learn face** — `tv.html` landing (the Word read aloud in Matt's voice, reading tutor, literacy) |

Retired 1.0 lifestyle pages (`almanac.html`, `apothecary.html`, `walk.html`, `kept.html`,
`enter.html`, `packets.html`, `breath.html`, `missions.html`, `search.html`, `voices`) `301`
to `/` on `.com` so cited links don't hard-404; their content is archived (below).

## 1.0 retirement (2026-07-02)

`nh-engine` (1.0, uvicorn `api.app:app` on `:8000`) is **stopped + disabled**. Nothing routes
to `:8000`. The `.com` per-card fallback was removed once `render_card_html` covered the cited
corpus (4,397/4,398 crawled card ids resolve on 2.0); `api.` was repointed `:8000 → :8002`
(accepted MCP tool-parity delta: ~103 granular 1.0 tools → 2.0's consolidated ~30).

1.0 is preserved, not deleted:
- files remain at `/home/nh/Lighthouse`
- full archive: `~/backups/lighthouse-1.0-full-<date>.tar.gz` (~569 MB, restorable)
- **re-enable:** `sudo systemctl enable --now nh-engine` + restore a Caddyfile backup below

## Services (systemd, user `nh`)

- `nh-com-2.service` → 2.0 **secular** on `:8002` (serves `.com` + `api.`)
- `nh-org.service`   → 2.0 **witness** on `:8001` (serves `.org` + `.tv`)
- `nh-traffic.timer` → traffic rollup every 10 min (root; access logs → `data/traffic.json`)
- `nh-engine.service`→ 1.0, **retired** (disabled; files + archive kept)

Both 2.0 services read `EnvironmentFile=-/home/nh/concordance-2/.env` (chmod 600, gitignored):
`ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID` (the cloned voice for `/speak`), and
`CONCORDANCE_KEEP_TOKEN` (the operator keep link). Secrets never live in source.

## Rollback

Caddyfile backups on the droplet (restore + `sudo systemctl reload caddy`):
- `/etc/caddy/Caddyfile.bak.pre2cut`    — before the `.com → 2.0` cutover
- `/etc/caddy/Caddyfile.bak.pretv`      — before `.tv → 2.0`
- `/etc/caddy/Caddyfile.bak.pre1retire` — before the 1.0 retirement (api.→:8000, .com fallback)

```sh
sudo cp /etc/caddy/Caddyfile.bak.pre1retire /etc/caddy/Caddyfile
sudo systemctl enable --now nh-engine
sudo systemctl reload caddy
```
