# Deploy topology (narrowhighway.*)

The live routing on `nh-engine-1`, recorded here for recoverability. Caddy terminates
TLS and reverse-proxies each host to a backend.

## Hosts → backends

| Host                     | Backend            | What runs there                              |
|--------------------------|--------------------|----------------------------------------------|
| `narrowhighway.com`      | `:8002` (2.0)      | **2.0 secular face** — the world-facing front door, app, engine, seals |
| ↳ `/card.html*`, `/card/*`, `/nh-*` | `:8000` (1.0) | **1.0 fallback** — preserves cited/crawled per-card permalinks + their assets (no 404s) |
| `narrowhighway.org`      | `:8001` (2.0)      | **2.0 witness face** — the full Word (scripture, dictionary, signposts, the Gate) |
| `api.narrowhighway.com`  | `:8000` (1.0)      | 1.0 API / MCP (unchanged)                    |
| `narrowhighway.tv`       | `:8000` (1.0)      | 1.0 media center (unchanged)                 |

The `.com → 2.0` cutover (2026-07-01) made 2.0 the world-facing face while keeping every
cited 1.0 URL alive via the path fallback. There is **no asset collision**: 1.0's
`card.html` uses `/nh-*.css/js`; 2.0 uses `/styles.css` and its own paths.

## Services (systemd, user `nh`)

- `nh-com-2.service` → 2.0 **secular** on `:8002` (see `nh-com-2.service`)
- `nh-org.service`   → 2.0 **witness** on `:8001`
- `nh-engine.service`→ 1.0 (uvicorn `api.app:app`) on `:8000`

Both 2.0 services read `EnvironmentFile=-/home/nh/concordance-2/.env` (chmod 600, gitignored)
which holds only `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID` — the operator's cloned voice
for `/speak`. Secrets never live in source; the `.env` was copied server-side from the 1.0
`.env`, never printed.

## Rollback

The pre-cutover Caddyfile is backed up on the droplet at
`/etc/caddy/Caddyfile.bak.pre2cut`. To revert `.com` to 1.0:

```sh
sudo cp /etc/caddy/Caddyfile.bak.pre2cut /etc/caddy/Caddyfile
sudo systemctl reload caddy
```
