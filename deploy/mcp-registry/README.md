# MCP registry submission

> **LISTED (checked 2026-11-23).** The public registry already holds the server:
> `GET https://registry.modelcontextprotocol.io/v0/servers?search=narrowhighway` returns
> **`com.narrowhighway/concordance` v2.0.0, status `active`, one remote: `https://narrowhighway.com/mcp`**
> (streamable HTTP). The `com.narrowhighway` namespace is verified by the domain key served at
> `https://narrowhighway.com/.well-known/mcp-registry-auth`.
>
> It was NOT published from the `server.json` beside this file, which still names
> `io.github.matharrismma/concordance` v2.0.0a0 with both the `.com` and `.org` remotes; and
> `site/.well-known/mcp.json` names a third identity, `io.github.matharrismma/narrow-highway` v1.0.0.
> Three names for one server: which is canonical — and whether the listing should also name the
> read-only profiles (`/mcp/witness`, `/mcp/core`) instead of only the full catalog — is the
> operator's call. The text below is the original playbook, kept as written.

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
