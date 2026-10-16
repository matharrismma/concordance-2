# The dedicated MCP host

The MCP — the agents' door (`/mcp`) — runs as its **own process**, `nh-mcp`, separate from the site engine
(`nh-engine`). A site deploy or restart never interrupts an agent mid-call, and an MCP spike never touches
the site. Same code, the same **read-only** corpus.

## What's set up (2026-10-16)

- **`nh-mcp.service`** (`deploy/nh-mcp.service`) — a second engine, secular surface, on `127.0.0.1:8003`,
  serving `/mcp`. Installed and running on the box. Verified: `tools/list` returns 102 tools.
- The box has the headroom: ~5.7 GB free; the second engine adds ~1.3 GB.
- `tools/deploy.sh` restarts `nh-mcp` alongside `nh-engine`, staggered, so the two never drift in code.

## The `/mcp` route — APPLIED to the live Caddy on 2026-10-16, tracked in `deploy/Caddyfile`

`api.narrowhighway.com/mcp` goes to the dedicated process; everything else on that host still goes to the site
engine. The block, in the `api.narrowhighway.com` route **before** its `:8002` upstream (the same text as the live
`/etc/caddy/Caddyfile`):

```caddy
	route {
		# /mcp -> the DEDICATED MCP host (nh-mcp :8003), decoupled from the site engine
		reverse_proxy /mcp* 127.0.0.1:8003 {
			lb_try_duration 10s
			lb_try_interval 250ms
		}
		reverse_proxy 127.0.0.1:8002 {
			lb_try_duration 10s
			lb_try_interval 250ms
		}
	}
```

To re-apply on a rebuilt box (back up, validate, reload — never edit-and-pray):

```bash
sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak.$(date +%Y%m%dT%H%M%S)
sudo -e /etc/caddy/Caddyfile            # add the /mcp route above
sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
sudo systemctl reload caddy
# verify: /mcp hits the dedicated process, the rest still the site engine
curl -s -X POST https://api.narrowhighway.com/mcp -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 -c 'import sys,json;print(len(json.load(sys.stdin)["result"]["tools"]),"tools")'
curl -s -o /dev/null -w '%{http_code}\n' https://api.narrowhighway.com/health
```
Rollback: restore the `.bak` Caddyfile and `sudo systemctl reload caddy`.

## A cleaner name (optional): `mcp.narrowhighway.com`

Add a DNS **A record** `mcp.narrowhighway.com → 5.78.186.55`, then add a Caddyfile block:

```caddy
mcp.narrowhighway.com {
	encode gzip zstd
	reverse_proxy 127.0.0.1:8003
}
```
Caddy fetches the TLS cert automatically once the DNS resolves. Agents then use `https://mcp.narrowhighway.com/mcp`.

## Moving to a separate MACHINE (full independence)

The dedicated *process* above decouples the MCP from the site engine but shares the box's hardware. For a
truly separate host (own failure domain):

1. Provision a small VM (2+ GB RAM) and add its SSH key.
2. Clone the repo there, create `.venv`, `pip install -e ".[math,signing,schema]"`.
3. Bring the keeping: `rsync` the `data/` dir from the box, **or** regenerate it with the `tools/migrate_*.py`
   seeders (gitignored, ~1.2 GB).
4. Install `deploy/nh-mcp.service` (adjust paths), `systemctl enable --now nh-mcp`.
5. Point `mcp.narrowhighway.com` DNS at the new host and give it its own Caddy block (above).
6. Add the new host to a deploy path (a second target in `tools/deploy.sh`, or its own script).

Same code, same covenant — found, verified, cited, sealed.
