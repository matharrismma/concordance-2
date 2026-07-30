"""Every JSON answer says it is fresh — because a stale read tells the reader the opposite of the
record.

Found 2026-07-29 while walking `shelf.html` in a real browser: a member withdrew their own card,
the store recorded the act with its reason, and the page still showed the card. The queue was
exactly ONE WRITE BEHIND — the tell that it was a cache, not a race.

No API response on this server had ever carried a `cache-control` header. A response with no
directive is *heuristically cacheable*: a browser, a proxy, or a CDN may serve a stale copy and be
entirely within spec. So this was never a shelf bug — it was every read endpoint, and the class of
bug is the one this project keeps meeting: correct server-side, wrong in front of the person.

This runs over a REAL socket rather than `dispatch()`, because the header is added by the request
handler and a dispatch-level test would pass while the wire stayed silent. Check the check.

Runnable with pytest OR directly.
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

# One route per shape of answer: a static-ish read, a computed read, a store-backed read, and the
# member-facing Commons reads that surfaced the bug.
READ_PATHS = ("/health", "/capabilities", "/commons", "/curate/queue", "/cards/stats")


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


def _head_and_body(base, path):
    with urllib.request.urlopen(base + path, timeout=30) as r:
        return {k.lower(): v for k, v in r.getheaders()}, r.read()


def test_no_json_read_is_cacheable(server):
    """The guarantee, on the wire. `no-store` (not merely `no-cache`) because `no-cache` still
    permits storing a copy and revalidating — and a revalidation this server never fields with an
    ETag is a copy that can be served."""
    missing = []
    for path in READ_PATHS:
        try:
            headers, _ = _head_and_body(server, path)
        except Exception as exc:  # noqa: BLE001 — a route that will not answer is its own failure
            missing.append(f"{path}: {exc}")
            continue
        cc = headers.get("cache-control", "")
        if "no-store" not in cc:
            missing.append(f"{path}: cache-control={cc!r}")
    assert not missing, ("JSON reads a client may cache — a stale answer shows the reader the "
                         "opposite of the record: " + "; ".join(missing))


def test_an_error_answer_is_not_cacheable_either(server):
    """A cached 404 or 403 is worse than a cached 200: the reader is refused for something that has
    since been granted, and no retry clears it."""
    req = urllib.request.Request(server + "/nope-not-a-route")
    try:
        urllib.request.urlopen(req, timeout=30)
        pytest.fail("expected an error status")
    except urllib.error.HTTPError as e:
        cc = {k.lower(): v for k, v in e.headers.items()}.get("cache-control", "")
        assert "no-store" in cc, f"an error response is cacheable: {cc!r}"


def test_a_write_is_visible_to_the_very_next_read(server):
    """The behaviour the header exists for, end to end over HTTP: append, then read, and see it.
    This is the assertion the browser walkthrough failed."""
    import base64

    from concordance import shelves, signing
    try:
        priv, pub = signing.generate_keypair()
    except Exception:  # noqa: BLE001
        pytest.skip("signing unavailable in this build")

    def post(path, body):
        req = urllib.request.Request(server + path, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            return json.loads(e.read())

    def get(path):
        with urllib.request.urlopen(server + path, timeout=30) as r:
            return json.loads(r.read())

    before = get("/curate/queue")["count"]
    sg = shelves.signable_drop(pub, "note", "Freshness",
                               "A drop made to prove the very next read can see it.", "commons")
    sig = signing.sign_bytes(base64.urlsafe_b64decode(sg["signable"]), priv)
    r = post("/drop", {"fields": sg["fields"], "signature": sig, "display_name": "a member"})
    assert r.get("ok"), r
    assert get("/curate/queue")["count"] == before + 1, \
        "the write is not visible to the next read — the reader is being shown a stale record"


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
