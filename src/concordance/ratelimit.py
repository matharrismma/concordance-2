"""A tiny sovereign rate limiter — a sliding-window cap per client, in memory.

Stdlib only, no Redis: a single-instance ThreadingHTTPServer keeps per-key timestamps and
refuses a key that exceeds `max_events` within `window_s`. Generous by default (agents are
welcome) but a ceiling so one source cannot exhaust the box. Keyed by the real client IP.
Configurable via CONCORDANCE_RATE_MAX / CONCORDANCE_RATE_WINDOW_S.
"""
from __future__ import annotations

import os
import threading
import time
from typing import Dict, List


class RateLimiter:
    def __init__(self, max_events: int = 120, window_s: float = 60.0):
        self.max = max_events
        self.window = window_s
        self._hits: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
        self._sweeps = 0

    def allow(self, key: str, *, now: float | None = None) -> bool:
        """Record a hit for `key`; return False if it exceeds the window cap."""
        if self.max <= 0:  # disabled
            return True
        t = time.time() if now is None else now
        cutoff = t - self.window
        with self._lock:
            q = self._hits.get(key)
            if q is None:
                q = []
                self._hits[key] = q
            while q and q[0] < cutoff:
                q.pop(0)
            if len(q) >= self.max:
                return False
            q.append(t)
            # opportunistic memory hygiene: drop empty/stale keys periodically
            self._sweeps += 1
            if self._sweeps % 500 == 0:
                for k in [k for k, v in self._hits.items() if not v or v[-1] < cutoff]:
                    if k != key:
                        self._hits.pop(k, None)
            return True

    def retry_after(self, key: str, *, now: float | None = None) -> int:
        """Seconds until the oldest hit in the window expires (for the Retry-After header)."""
        t = time.time() if now is None else now
        with self._lock:
            q = self._hits.get(key) or []
            if not q:
                return 0
            return max(1, int(self.window - (t - q[0])) + 1)


def from_env() -> RateLimiter:
    try:
        mx = int(os.environ.get("CONCORDANCE_RATE_MAX", "120") or 120)
    except ValueError:
        mx = 120
    try:
        win = float(os.environ.get("CONCORDANCE_RATE_WINDOW_S", "60") or 60)
    except ValueError:
        win = 60.0
    return RateLimiter(max_events=mx, window_s=win)
