"""Run the engine from the command line.

    python -m concordance serve [--surface secular|witness] [--port N] [--host H] [--site DIR|--no-site]

Serves the sovereign HTTP API and (by default) the static site, same-origin, stdlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

from .web import serve


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    usage = ("usage: python -m concordance <serve|mcp|connect|sync> ...\n"
             "  serve [--surface secular|witness] [--port N] [--host H] [--site DIR|--no-site]\n"
             "  mcp   [--surface secular|witness]   (MCP server over stdio, for agents)\n"
             "  connect [calendar|email|storage]    (read YOUR own tools, locally; keeps nothing)\n"
             "  sync  [--branch NAME] [--dry-run]   (pull the keeping from every KNOWN branch — Gen 3 · 1)\n"
             "  sync --add-branch NAME URL FINGERPRINT   (pin a branch by hand: the trust root)\n"
             "  sync --whoami                       (this node's fingerprint + public key)")
    if not argv:
        print(usage)
        return 0
    if argv[0] == "connect":
        from .connect import run as connect_run
        return connect_run(argv[1:])
    if argv[0] == "sync":
        import json as _json
        from . import replicate as _rep
        opts = argv[1:]
        if "--whoami" in opts:
            print(_json.dumps(_rep.node_public(), indent=1))
            return 0
        if "--add-branch" in opts:
            j = opts.index("--add-branch")
            if len(opts) < j + 4:
                print(usage)
                return 2
            rec = _rep.add_branch(opts[j + 1], opts[j + 2], opts[j + 3])
            print(_json.dumps(rec, indent=1))
            return 0
        only = ""
        for j, o in enumerate(opts):
            if o == "--branch" and j + 1 < len(opts):
                only = opts[j + 1]
        reports = _rep.sync_all(only=only, dry_run="--dry-run" in opts)
        if not reports:
            print("no known branches — pin one: python -m concordance sync --add-branch NAME URL FINGERPRINT")
            return 2
        for r in reports:
            print(_json.dumps(r, indent=1))
        return 0 if all(r.get("ok") for r in reports) else 1
    if argv[0] == "mcp":
        from .mcp import serve_stdio
        surface = "secular"
        opts = argv[1:]
        for j, o in enumerate(opts):
            if o == "--surface" and j + 1 < len(opts):
                surface = opts[j + 1]
        serve_stdio(surface=surface)
        return 0
    if argv[0] != "serve":
        print(usage)
        return 0

    surface, port, host = "secular", 8000, "127.0.0.1"
    default_site = Path(__file__).resolve().parents[2] / "site"
    site = str(default_site) if default_site.is_dir() else None

    opts = argv[1:]
    i = 0
    while i < len(opts):
        o = opts[i]
        if o == "--surface" and i + 1 < len(opts):
            surface = opts[i + 1]; i += 2
        elif o == "--port" and i + 1 < len(opts):
            port = int(opts[i + 1]); i += 2
        elif o == "--host" and i + 1 < len(opts):
            host = opts[i + 1]; i += 2
        elif o == "--site" and i + 1 < len(opts):
            site = opts[i + 1]; i += 2
        elif o == "--no-site":
            site = None; i += 1
        else:
            i += 1

    serve(host=host, port=port, surface=surface, site_dir=site)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
