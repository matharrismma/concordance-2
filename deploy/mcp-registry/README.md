# MCP registry submission — PREPARED, NOT SUBMITTED

`server.json` is the manifest for listing Narrow Highway's MCP server in the public
[MCP registry](https://registry.modelcontextprotocol.io) so agents can discover it.

**This is an outward publish — it is the operator's call, not done automatically.** Before
submitting:

1. Confirm the namespace `io.github.matharrismma/concordance` matches the GitHub identity used
   to authenticate (the registry verifies ownership via the matching `github.com/matharrismma`).
2. Validate against the current registry schema (the `$schema` URL pins a dated version —
   check it's still current).
3. Decide whether to list both surfaces or only `.com` (the reach).
4. Authenticate (`mcp-publisher login github`) and `mcp-publisher publish` (or the current CLI).

Listing it is the single biggest discoverability step for agents — but it puts the engine on a
public index, so it waits for an explicit go.
