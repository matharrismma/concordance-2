#!/usr/bin/env python3
"""Local dev server — serve the engine + the static site for preview/testing.

    python tools/serve_local.py            # secular on :8099
    NH_PORT=8100 NH_SURFACE=witness python tools/serve_local.py

Resolves src/ and site/ relative to the repo (cwd-independent) so it works from anywhere.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
os.environ.setdefault("CONCORDANCE_DATA_DIR", os.path.join(ROOT, "data"))
os.environ.setdefault("CONCORDANCE_KEEP_TRUST_LOCAL", "1")  # local dev: trust loopback for the keep

from concordance.web.api import serve  # noqa: E402

if __name__ == "__main__":
    port = int(os.environ.get("PORT") or os.environ.get("NH_PORT") or "8099")
    surface = os.environ.get("NH_SURFACE", "secular")
    serve(host="127.0.0.1", port=port, surface=surface, site_dir=os.path.join(ROOT, "site"))
