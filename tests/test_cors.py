"""CORS — the open door for browser apps and browser-agents.

The read/verify API carries no ambient credential (the one cookie, nh_gate, is never sent
cross-origin because we allow no credentials), so it is safe to answer every origin. These
tests drive the REAL wire (build_server on port 0, warm=False) and prove:
  - every response carries `Access-Control-Allow-Origin: *`, so a page's fetch() can read it;
  - the OPTIONS preflight is answered 204 with the methods/headers a browser asks about.
Runnable with `pytest` OR `python tests/test_cors.py`.
"""
from __future__ import annotations

import http.client
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.web.api import build_server  # noqa: E402


def _spun():
    """The real server, bound to an ephemeral port, serving in a daemon thread. warm=False so the
    test never pays the ~5s corpus/graph warm — CORS lives in the handler, above the engine."""
    httpd = build_server(host="127.0.0.1", port=0, warm=False)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def test_every_response_carries_open_cors():
    httpd, port = _spun()
    try:
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        c.request("GET", "/systems")                 # engine-free route (disk + imports, no corpus)
        r = c.getresponse()
        r.read()
        assert r.getheader("access-control-allow-origin") == "*"   # a browser page may read it
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_preflight_is_answered():
    httpd, port = _spun()
    try:
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        c.request("OPTIONS", "/audit", headers={
            "Origin": "https://some-app.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"})
        r = c.getresponse()
        r.read()
        assert r.status == 204                                      # preflight, no body
        assert r.getheader("access-control-allow-origin") == "*"
        assert "POST" in (r.getheader("access-control-allow-methods") or "")
        assert "content-type" in (r.getheader("access-control-allow-headers") or "").lower()
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_a_write_still_needs_a_signature_not_an_origin():
    """Open CORS grants READ access from any origin — never authority. A write with no signature is
    refused on its merits (the gate is server-side), so opening the door leaks nothing."""
    httpd, port = _spun()
    try:
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        c.request("POST", "/book", body=b'{"op":"write","text":"x"}',
                  headers={"content-type": "application/json", "Origin": "https://some-app.example"})
        r = c.getresponse()
        r.read()
        assert r.status >= 400                    # no valid signature → refused regardless of origin
        assert r.getheader("access-control-allow-origin") == "*"   # ...but still CORS-visible
    finally:
        httpd.shutdown()
        httpd.server_close()


if __name__ == "__main__":
    test_every_response_carries_open_cors()
    test_preflight_is_answered()
    test_a_write_still_needs_a_signature_not_an_origin()
    print("ok")
