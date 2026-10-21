# V3 — this repo is the core

**Decision (2026-10-20).** Narrow Highway splits into a pure **core engine** (this repo,
`concordance-2`) and an **application layer** (`witness` — github.com/matharrismma/witness — a separate repo). The core
serves `narrowhighway.com` and the `api.`/MCP door; the ancillary layer serves `narrowhighway.org`
and calls the core over HTTP.

## The rule this split must never break

**One engine, one corpus, never isolated.** The `.org` app holds no verifier and no corpus of its
own. Every check and every seal crosses the HTTP boundary back to this one engine. V3 moves
*surfaces and orchestration* out of the core; it does not fork the engine or duplicate the keeping.

## What stays here (the core)

- **Verification:** `verify`, `discern`, `audit`, `derivation`, the verifiers (incl. the witness
  verifiers scripture/theology — deterministic checking is core; only their *surfacing* is `.org`),
  `domain_resolver`, `candidates`, `warrant`, `factfind`, `clarify`.
- **The keeping and the map:** `corpus`, `cas`, `ledger`, `seals`, `chains`/`graph`/`roots`/floors,
  the sticks (`data/sticks`), `compendium`, `shelves`, `find`, `sources`.
- **The doors:** the HTTP dispatcher (`web/api.py`) and the MCP server (`mcp/`), core + library
  profiles, the gate/kernel. `EngineConfig(surface=...)` and `branding` stay here as the shared seam.

## What moved to `witness`

The witness **record** (seals surfaced, badges, professions, consent, moderation); the **community**
(mesh, groups, formation, flock, push, lighthouse node); the **experience** layer (Console, coach,
trajectory, steward, decks, playbook, and the witness surfacing of teachings/parable); and the
**Scribe** (its first landed tool). These call the core; they do not reimplement it.

> Migration status: the boundary is carved and the `.org` app is scaffolded with the Scribe proven
> against the core. The listed ancillary modules still live in this repo and are moved behind the
> HTTP client incrementally; this document is the agreed destination, not a completed move.

## The contract the `.org` app depends on

`POST /verify` (rate-limited; clients back off on 429):

- `{"steps": [ {"id","domain","spec"} ... ]}` → `{verdict, trail:[{id,domain,status,detail}], house:{seal}}`
- `{"claim": "<plain sentence>"}` → `{verdict, checks:[...], receipt, coverage}`
- `?seal=0` is read-only; `?seal=1` mints the permanent receipt whose `cite_url` points at
  `narrowhighway.org/s/<hash>` (the RECORD lives on `.org`).

Anything the `.org` app needs that this contract does not already expose is a reviewed addition to
`/verify` or a new core endpoint — never a reason for the app to import core code.
