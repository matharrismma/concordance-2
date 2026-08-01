"""A search door has a ceiling, and it SAYS when it uses it.

FOUND BY PRESSURE TEST 2026-08-01, measured on the live secular host:

    limit asked      count says   results given       bytes    secs
              5               5               5       1,745    0.58
             25              25              25       8,302    0.56
          1,000           1,000           1,000     320,884    1.37
  1,000,000,000           5,007           5,007   1,667,823    5.10

No silent truncation — `count` and `results` agreed every time, which is the honest half. The
problem is the other half: a 200-byte unauthenticated request bought 1.67 MB of egress and 5.1
seconds of server CPU, at a rate limit deliberately set generous so agents would feel welcome
(R4). That is cheap amplification against a box that had just been taken down by descriptor
exhaustion the same afternoon.

THIS WAS AN OVERSIGHT, NOT A DESIGN. Four other routes in api.py already clamp:
`min(int(...), 500)`, `min(int(...), 50)`, `min(50, ...)`. The two BUSIEST doors — the MCP
`search` tool (46,190 hits) and `GET /search` (16,210) — were the two with no ceiling at all.

THE CEILING IS ANNOUNCED, NEVER SILENT. Matt's standing rule: a cap that does not report itself
reads as "that was all of them". So a caller who asks for more than the ceiling still gets the
ceiling's worth AND a `limit_capped` field saying what they asked for, what they got, and why.
That is the same judgement as the want desk refusing a 300-character query out loud rather than
truncating it, and the opposite of the old encyclopedia stub that 301'd away a `?ref=` in silence.

We refuse abuse, not use: 200 is eight times the default and more than any real reader needs.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

MAX = 200          # must match api.SEARCH_MAX


@pytest.fixture(scope="module")
def server():
    from concordance.web import api
    os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp())
    httpd = api.build_server(host="127.0.0.1", port=0, surface="secular",
                             site_dir=str(ROOT / "site"), warm=False)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def _get(base, path):
    with urllib.request.urlopen(base + path, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def test_the_ceiling_holds(server):
    j = _get(server, f"/search?q=grace&limit={10**9}")
    assert len(j.get("results") or []) <= MAX, (
        f"no ceiling: asked 10^9, got {len(j.get('results') or [])} results. A 200-byte request "
        f"must not buy megabytes of egress and seconds of CPU.")


def test_the_ceiling_announces_itself(server):
    """A cap that does not report itself reads as 'that was all of them'."""
    j = _get(server, f"/search?q=grace&limit={10**9}")
    cap = j.get("limit_capped")
    assert cap, "the response used a ceiling and did not say so — a silent cap is a lie"
    assert cap.get("asked") == 10**9
    assert cap.get("served") == MAX
    assert cap.get("why")


def test_an_ordinary_request_is_untouched(server):
    """We refuse abuse, not use — a normal limit must pass through with no cap notice."""
    j = _get(server, "/search?q=grace&limit=5")
    assert len(j.get("results") or []) <= 5
    assert "limit_capped" not in j, "an in-bounds request must not be told it was capped"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
