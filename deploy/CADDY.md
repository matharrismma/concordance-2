# Caddy — the pre-release lock and the un-dark toggle

The edge (TLS + reverse proxy) is Caddy on the box (`/etc/caddy/Caddyfile`). The Caddyfile is **not
rsynced by `tools/deploy.sh`** — it is edited on the box out of band. This file version-controls the
one switch that matters (dark ↔ public) so it is reviewable and revertible; the box's live file is the
source of truth (snapshot below is from 2026-09-14, reviewer IP redacted as `<REVIEWER_IP>`).

## Current state: DARK (pre-release review lock, since 2026-09-07)

Every public site (`.com`, `api.com`, `.org`, `.tv`) is gated to the reviewer's IP; everyone else gets
a `503 "under review"` (with `Retry-After: 86400`, so crawlers back off instead of de-indexing). This is
**intentional, not an outage.** Each of the four site blocks carries:

```
	@blocked not remote_ip <REVIEWER_IP> 127.0.0.1/8 ::1
	handle @blocked {
		header @blocked Retry-After "86400"
		respond @blocked "Narrow Highway — under review before release. Back soon." 503
	}
```

To let another reviewer in: add their IP to **every** `@blocked not remote_ip …` line, then
`sudo systemctl reload caddy`.

## Un-dark (go public) — Matt's call

The open (public) config is kept on the box as `/etc/caddy/Caddyfile.bak-prereview-2026-09-07`
(the state before the lock). To publish:

```bash
sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak-locked-$(date +%Y%m%d)   # keep a way back
sudo cp /etc/caddy/Caddyfile.bak-prereview-2026-09-07 /etc/caddy/Caddyfile     # restore the open config
sudo caddy validate --config /etc/caddy/Caddyfile                              # never reload an invalid file
sudo systemctl reload caddy
```

To re-dark: reverse it (restore the locked backup, reload). The difference between the two is exactly
the four `@blocked` blocks above — nothing else.

## Rate limiting at the edge — NOT present, and why that is OK for launch

The box's Caddy is **v2.11.3 with no `rate_limit` module** (`caddy list-modules | grep rate_limit` is
empty). Adding a `rate_limit {…}` directive would be an unknown directive and Caddy would refuse to
load — breaking serving. So edge rate-limiting needs a Caddy **rebuilt with the plugin**
(`caddy-ratelimit`), which is a deliberate infra task, not a launch-eve edit.

It is acceptable to launch without it: the **application layer already rate-limits** every heavy public
route (`src/concordance/ratelimit.py` — 120 writes/60s and 600 reads/60s per real client IP, XFF-spoof
resistant; `/verify`, `/audit`, `/ask`, `/search` are all enrolled). Edge rate-limiting is
defense-in-depth to add later, not a blocker. Tracked as future hardening.
