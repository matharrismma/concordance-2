# Listing the engine in the MCP registries — the distribution step

The flagship is ready (transport whole, surface consolidated, guarantee independently
checkable). These listings are how agents' humans find it. Everything below is prepared;
the authenticated steps need Matt's accounts.

## 1. Official MCP Registry (registry.modelcontextprotocol.io)

The publish file is beside this note: `docs/registry/server.json`.

```bash
brew install mcp-publisher || go install github.com/modelcontextprotocol/registry/cmd/mcp-publisher@latest
cd docs/registry
mcp-publisher login github        # opens browser; your GitHub account proves domain/repo
mcp-publisher publish
```

If the namespace check asks for domain proof, it verifies `com.narrowhighway` via a
DNS TXT record or the GitHub repo — the CLI prints the exact record to add.

## 2. Passive discovery (already live, nothing to do)

- `https://narrowhighway.com/.well-known/mcp.json` — directories and scorers that crawl
  well-known paths find the full descriptor themselves.
- `https://narrowhighway.com/llms.txt` — agents' start-here, with the seal-verification
  and benchmark links.

## 3. Community directories (each ~5 minutes, a form + a link)

- mcp.so — "Submit" with https://narrowhighway.com/mcp
- glama.ai/mcp/servers — submit the GitHub repo
- pulsemcp.com — submit form
- smithery.ai — submit (remote server, streamable-http)

One paragraph that fits all of them:

> Narrow Highway — deterministic verification with receipts. Hand it any claim and get
> a verdict, the worked trail, and a permanent seal you can re-check with 60 lines of
> stdlib Python and zero trust in us. 60 domains, 0 false positives on the published
> benchmark. Free, no key: https://narrowhighway.com/mcp (docs: /llms.txt)

## 4. claude.ai (your own account — also the end-to-end test)

Settings → Connectors → Add custom connector → `https://narrowhighway.com/mcp`.
If it mounts green and tools list, the fix of 2026-08-05 is confirmed from the
client side — the same path every other Claude user would take.
