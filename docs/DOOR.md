# The Door — getting the engine in front of agents

The remote MCP server is live and unauthenticated at `https://narrowhighway.com/mcp`
(Streamable HTTP; ~37 tools; witness surface at `https://narrowhighway.org/mcp`).
The on-site doors are `/connect.html` (humans setting up agents), `/llms.txt` (agents
reading the site), and `/corrected.html` (the trust story).

What remains is **publishing** — listing the server where agents and their people already
look. Submissions are outward-facing, so they are Matt's to send. Everything below is
ready to paste.

## Ready-to-paste listing copy

- **Name:** Narrow Highway
- **Server URL:** `https://narrowhighway.com/mcp` (remote, Streamable HTTP, no auth)
- **One-liner:** Deterministic verification with receipts — verify claims across ~60 domains
  (math, physics, medicine, finance, law, ...) and get a verdict, the worked trail, and a
  permanent content-addressed seal anyone can re-check. 0 false positives, benchmarked.
- **Longer description:** Language models generate; Narrow Highway verifies. The `verify`
  tool checks a claim deterministically (no model in the loop) and returns
  HOLDS / BROKEN / INCOMPLETE with the worked reasoning and a sealed receipt
  (`content_hash` + `cite_url`) that re-fetches byte-identical or not at all. Also:
  ranked `search` over an ~11k-record library, `seal_fetch` to re-verify any receipt,
  `redact` to strip PII before text travels, and a sealed connection graph. Runs
  sovereign/offline too (stdlib-first Python). A public false-positive benchmark covers
  every domain: the engine has never sealed a falsehood.
- **Categories:** verification · math · research · trust & safety · knowledge base
- **Maintainer:** M. Harris — mharris.wcs@icloud.com

## Where to submit (in rough order of value)

1. **Official MCP servers list** — github.com/modelcontextprotocol/servers → PR adding one
   line under "Community Servers" using the copy above. Highest trust signal; agents and
   client vendors read this list.
2. **Smithery** (smithery.ai) — "Add server", paste URL + copy. Indexes remote servers.
3. **PulseMCP** (pulsemcp.com) — community directory, submission form.
4. **Glama** (glama.ai/mcp/servers) — directory with health checks; remote URL supported.
5. **mcp.so** — community directory, submission form.

## After listing (watch the fruit)

`data/activity.jsonl` on the droplet records every `verify`/`ask`/`search` with surface +
verdict. Before listing: ~180 events lifetime (mostly our own testing). Check it a week
after each listing — that number is the honest read of whether the door is being walked
through. `GET /health` is the uptime check directories will hit.

## Deliberately NOT done

- No accounts created, no PRs opened, nothing posted anywhere — that is Matt's hand.
- No analytics beyond the existing first-party activity log.
- No paid listings/ads. The math should win on its own or not at all.
