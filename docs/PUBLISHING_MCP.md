# Publishing the MCP — make the engine discoverable

The engine is already **irresistible and provable** for a builder who *lands* on it:
`https://narrowhighway.com/connect.html` gives a one-URL, no-key, no-cost MCP connector; every verdict
returns a content-addressed **seal** (`{content_hash, cite_url}`) that anyone can re-fetch at
`/s/<hash>` and re-check with a ~60-line stdlib verifier (`docs/SEAL_SPEC.md`, `tools/verify_seal.py`);
and a published benchmark holds 0 false positives every build. "LLMs generate; they don't verify —
this is the other half."

What remains is **discovery**: builders find MCP servers through *registries*, and those need a
listing. This is an external step (accounts / PRs the operator makes); everything needed is prepared:

- The registry manifest is committed at **`site/.well-known/mcp.json`** and served (auto-discovery) at
  **`https://narrowhighway.com/.well-known/mcp.json`**. It follows the official registry `server.json`
  shape (name `io.github.matharrismma/narrow-highway`, `remotes[].url = https://narrowhighway.com/mcp`,
  transport `streamable-http`).

## Where to list it (highest-leverage first)

1. **Official MCP Registry** — `registry.modelcontextprotocol.io`. Install the `mcp-publisher` CLI,
   authenticate the `io.github.matharrismma/*` namespace via GitHub, then publish the manifest:
   ```
   mcp-publisher login github
   mcp-publisher publish   # from a dir containing the server.json (site/.well-known/mcp.json)
   ```
   (Confirm the manifest validates against the registry's *current* schema at publish time — the
   schema URL in the manifest may need bumping; the registry error message names the expected one.)
2. **Smithery** (`smithery.ai`) — "Add server", point it at the GitHub repo + the remote URL. Remote,
   no-auth HTTP servers are first-class there.
3. **Glama** (`glama.ai/mcp/servers`) — largely auto-discovers from GitHub; ensure the repo README
   links `connect.html` and the manifest. Claim the listing once it appears.
4. **PulseMCP** (`pulsemcp.com`) — submission form; remote URL + description.
5. **mcp.so** and **mcpservers.org** — community directories; submit the repo + remote URL.
6. **`punkpeye/awesome-mcp-servers`** (GitHub) — open a PR adding one line under the right category
   (a hosted, remote verification server) linking `connect.html`.

## The pitch to paste (consistent everywhere)

> **Narrow Highway** — a deterministic verification engine for AI agents. Hand it a claim; get a
> verdict, the worked trail, and a permanent, re-checkable receipt. No model in the loop. Stops an
> agent's answers from being taken on faith — every one can carry proof. Free, one URL, no key:
> `https://narrowhighway.com/mcp`.

## Keep it honest

Every listing must be able to back its claim. The seal spec, the independent verifier, and the
benchmark are public precisely so a skeptic can **re-check us without trusting us** — link them, and
never state a bound stronger than the benchmark's published cases.
