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
    usage = ("usage: python -m concordance <serve|mcp> ...\n"
             "  serve [--surface secular|witness] [--port N] [--host H] [--site DIR|--no-site]\n"
             "  mcp   [--surface secular|witness]   (MCP server over stdio, for agents)")
    if not argv:
        print(usage)
        return 0
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
