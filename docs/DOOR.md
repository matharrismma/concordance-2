# The Door — getting the engine in front of agents

The remote MCP server is live and unauthenticated at `https://narrowhighway.com/mcp`
(Streamable HTTP; ~37 tools; witness surface at `https://narrowhighway.org/mcp`).
The on-site doors are `/connect.html` (humans setting up agents), `/llms.txt` (agents
reading the site), and `/corrected.html` (the trust story).

What remains is **publishing** — listing the server where agents and their people already
look. Submissions are outward-facing, so they are Matt's to send. Everything below is
ready to paste.

## Ready-to-paste listing copy

- **Name:** Concordance
- **Server URL:** `https://narrowhighway.com/mcp` (remote, Streamable HTTP, no auth)
- **One-liner:** Deterministic verification with receipts — verify claims across ~60 domains
  (math, physics, medicine, finance, law, ...) and get a verdict, the worked trail, and a
  permanent content-addressed seal anyone can re-check. 0 false positives, benchmarked.
- **Longer description:** Language models generate; Concordance verifies. The `verify`
  tool checks a claim deterministically (no model in the loop) and returns
  HOLDS / BROKEN / INCOMPLETE with the worked reasoning and a sealed receipt
  (`content_hash` + `cite_url`) that re-fetches byte-identical or not at all. Also:
  ranked `search` over an ~11k-record library, `seal_fetch` to re-verify any receipt,
  `redact` to strip PII before text travels, and a sealed connection graph. Runs
  sovereign/offline too (stdlib-first Python). A public false-positive benchmark covers
  every domain: the engine has never sealed a falsehood. 38 tools live.
- **Categories:** verification · math · research · trust & safety · knowledge base
- **Maintainer:** M. Harris — mharris.wcs@icloud.com
- **Homepage:** `https://narrowhighway.com` (the site brand is Narrow Highway; the engine
  is Concordance — the tool is named for the engine)

## Where to submit — grounded against what's already listed (checked 2026-07-07)

0. **mcp.so — UPDATE, don't duplicate.** Matt's past submission is live at
   `mcp.so/server/concordance-engine/matharrismma` but describes the 1.0 engine
   ("eleven verifier tools", stdio). Update it in place (keeps any accumulated standing +
   the existing `concordance-engine` slug already matches the name): the REMOTE url
   `https://narrowhighway.com/mcp`, 38 tools, ~60 domains, the copy above.
1. **Official MCP servers list** — github.com/modelcontextprotocol/servers → PR adding one
   line under "Community Servers" using the copy above. Highest trust signal; agents and
   client vendors read this list. NOT currently listed.
2. **Smithery** (smithery.ai) — "Add server", paste URL + copy. NOT currently listed.
3. **PulseMCP** (pulsemcp.com) — community directory, submission form. NOT currently listed.
4. **Glama** (glama.ai/mcp/servers) — directory with health checks; remote URL supported.
   NOT currently listed.

Naming note: the server is listed as **Concordance** — the engine's own name, and the one
Matt's existing `mcp.so` listing already uses (`concordance-engine`). Do NOT list it as
"Lighthouse": searches for that drown in Google-Lighthouse performance tools, so the 1.0
name was uncitable there. The public site remains branded "Narrow Highway" at
narrowhighway.com; the tool is named for the engine, not the domain.

## Exact paste blocks

**GitHub PR line** (modelcontextprotocol/servers → `README.md`, "Community Servers",
alphabetical — insert at the "C" position). This is the only destination that needs a
special one-line markdown format:

```
- **[Concordance](https://narrowhighway.com)** – Deterministic verification with receipts across ~60 domains (math, physics, medicine, finance, law…). Returns HOLDS/BROKEN/INCOMPLETE with the worked trail and a permanent, re-checkable content-addressed seal. No model in the loop; 0 false positives, benchmarked.
```
PR title: `Add Concordance (deterministic verification server)`
PR body: one sentence + link to `https://narrowhighway.com/proof.html` as evidence.

**Smithery / PulseMCP / Glama form fields** (paste from the listing copy above):

| Field | Value |
|---|---|
| Name | `Concordance` |
| Remote URL | `https://narrowhighway.com/mcp` |
| Transport | Streamable HTTP (no auth) |
| Summary | the one-liner above |
| Description | the longer description above |
| Categories/Tags | verification, math, research, trust-and-safety, knowledge-base |
| Homepage | `https://narrowhighway.com` |
| Health check | `https://narrowhighway.com/health` |

**mcp.so** — edit the existing `concordance-engine` listing: swap the description for the
longer copy above, set the URL to the remote `https://narrowhighway.com/mcp`, tool count 38.

## After listing (watch the fruit)

Two honest reads on the droplet:
- `data/traffic.json` — first-party request tally by class. **As of 2026-07-08:**
  4,683 human requests (1,205 unique IPs), 1,257 agent requests, 10,157 bot/crawler hits.
  Arrival is real; the top human page after `/` is `/almanac.html`.
- `data/ledger/` — durable seals minted. **As of 2026-07-08: 26.** This is the number that
  matters: it counts how often the *moat itself* was used, not just browsed. The gap between
  1,257 agent requests and 26 seals is the whole reason to list — to convert arrival into
  verification.

Check both a week after each listing. `GET /health` is the uptime check directories will hit.

## Deliberately NOT done

- No accounts created, no PRs opened, nothing posted anywhere — that is Matt's hand.
- No analytics beyond the existing first-party activity log.
- No paid listings/ads. The math should win on its own or not at all.
