"""web — the sovereign HTTP API exposing the floor (stdlib only). See api.py."""
from __future__ import annotations

from .api import dispatch, serve

__all__ = ["dispatch", "serve"]
