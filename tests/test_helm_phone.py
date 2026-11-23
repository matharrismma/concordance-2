"""THE HELM on the operator's phone — the gate, and the one property that makes this door
necessary at all.

The site's own POST /push/subscribe and /push/unsubscribe are UNAUTHENTICATED by design: a mesh
node is keyed by its own public fingerprint and proves nothing to subscribe itself. If the Helm had
reused that, a stranger who guessed the key could register their own device and RECEIVE the
operator's alerts, or unsubscribe his phone and SILENCE them. So the Helm's subscription key is a
server-side secret and the only door is operator-gated.

That is the property these tests hold: the fingerprint is never returned to a browser, never
accepted from a request, and nothing can be registered or dropped without the operator token.

Runs over a real socket, with the push store pointed at a temp dir so no test touches data/push.
"""
from __future__ import annotations

import http.client
import json
import os
import re
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

SITE = ROOT / "site"
TOKEN = "helm-phone-test-token"
SUBSCRIPTION = {                     # the shape a browser's PushSubscription.toJSON() produces
    "endpoint": "https://push.example.invalid/f/abc123",
    "keys": {"p256dh": "BG" + "A" * 85, "auth": "B" * 22},
}

pytest.importorskip("cryptography", reason="VAPID needs the optional signing extra")


@pytest.fixture(scope="module")
def server():
    from concordance.web import api
    prior = {k: os.environ.get(k) for k in
             ("CONCORDANCE_HELM_TOKEN", "CONCORDANCE_DATA_DIR", "CONCORDANCE_PUSH_DIR",
              "CONCORDANCE_PUSH_ENABLED")}
    os.environ["CONCORDANCE_HELM_TOKEN"] = TOKEN
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    os.environ["CONCORDANCE_PUSH_DIR"] = tempfile.mkdtemp()
    os.environ.pop("CONCORDANCE_PUSH_ENABLED", None)      # delivery OFF, as on any host by default
    httpd = api.build_server(host="127.0.0.1", port=0, surface="secular",
                            site_dir=str(SITE), warm=False)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        yield ("127.0.0.1", httpd.server_address[1])
    finally:
        httpd.shutdown()
        for k, v in prior.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _req(addr, method, path, body=None, token=None):
    conn = http.client.HTTPConnection(addr[0], addr[1], timeout=60)
    try:
        hdrs, payload = {}, None
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
            hdrs = {"content-type": "application/json", "content-length": str(len(payload))}
        if token:
            hdrs["X-Helm-Token"] = token
        conn.request(method, path, body=payload, headers=hdrs)
        r = conn.getresponse()
        raw = r.read()
        try:
            return r.status, json.loads(raw or b"{}")
        except ValueError:
            return r.status, {}
    finally:
        conn.close()


def test_the_phone_door_is_404_without_the_operator_token(server):
    for method, body in (("GET", None), ("POST", {"subscription": SUBSCRIPTION}),
                         ("POST", {"forget": True}), ("POST", {"test": True})):
        status, payload = _req(server, method, "/helm/push", body=body)
        assert status == 404, (method, body, status)
        assert payload == {"error": "not found"}
    # and nothing was registered by any of those attempts
    status, st = _req(server, "GET", "/helm/push", token=TOKEN)
    assert status == 200 and st["devices"] == 0, st


def test_status_hands_over_the_public_key_and_never_the_fingerprint(server):
    status, st = _req(server, "GET", "/helm/push", token=TOKEN)
    assert status == 200, st
    assert st["available"] is True, st
    assert st["delivery_enabled"] is False          # off by default; a device may still register
    assert isinstance(st["key"], str) and len(st["key"]) > 80   # the VAPID P-256 public point
    assert "fp" not in json.dumps(st).lower().replace("unavailable_because", "")
    from concordance.web import helm_push
    assert helm_push._fp() not in json.dumps(st), "the Helm's secret fingerprint reached a browser"


def test_a_malformed_body_is_the_only_400(server):
    status, payload = _req(server, "POST", "/helm/push", body={"nonsense": 1}, token=TOKEN)
    assert status == 400
    assert "subscription" in payload["error"]


def test_a_device_registers_under_a_server_secret_the_caller_cannot_choose(server):
    from concordance.web import helm_push
    fp = helm_push._fp()
    assert re.fullmatch(r"[0-9a-f]{32}", fp), fp          # a random secret, not a guessable name

    status, res = _req(server, "POST", "/helm/push",
                       body={"subscription": SUBSCRIPTION}, token=TOKEN)
    assert status == 200 and res["ok"] is True, res
    assert res["devices"] == 1

    # THE PROPERTY: an fp in the request body is ignored. A caller cannot steer where the
    # subscription lands, so it can never be filed under a key a stranger knows.
    other = {"endpoint": "https://push.example.invalid/f/attacker", "keys": {"p256dh": "BG" + "Z" * 85}}
    status, res = _req(server, "POST", "/helm/push",
                       body={"fp": "attacker-chosen-key", "subscription": other}, token=TOKEN)
    assert status == 200 and res["ok"] is True
    store = Path(os.environ["CONCORDANCE_PUSH_DIR"]) / "subs"
    files = sorted(p.name for p in store.glob("*.json"))
    assert files == [fp + ".json"], files                 # one file, under the SERVER's key only


def test_a_test_alert_with_delivery_off_says_so_instead_of_pretending(server):
    status, res = _req(server, "POST", "/helm/push", body={"test": True}, token=TOKEN)
    assert status == 200, res
    assert res["ok"] is True
    assert res["sent"] == 0                               # nothing left the host
    assert res["devices"] >= 1
    assert "delivery is off" in res["why_nothing_arrived"], res


def test_forget_drops_every_device_and_only_the_operator_may_do_it(server):
    status, _ = _req(server, "POST", "/helm/push", body={"forget": True})
    assert status == 404                                  # a stranger cannot silence the phone
    status, st = _req(server, "GET", "/helm/push", token=TOKEN)
    assert st["devices"] >= 1                             # still registered

    status, res = _req(server, "POST", "/helm/push", body={"forget": True}, token=TOKEN)
    assert status == 200 and res["ok"] is True
    status, st = _req(server, "GET", "/helm/push", token=TOKEN)
    assert st["devices"] == 0, st


def test_the_manifest_makes_it_installable_and_points_at_the_helm():
    m = json.loads((SITE / "helm.webmanifest").read_text(encoding="utf-8"))
    assert m["start_url"] == "/helm.html" and m["scope"] == "/helm.html"
    assert m["display"] == "standalone"
    page = (SITE / "helm.html").read_text(encoding="utf-8")
    assert '<link rel="manifest" href="/helm.webmanifest">' in page
    assert "viewport-fit=cover" in page                   # iOS safe areas
    assert 'navigator.serviceWorker.register("/sw.js")' in page   # push needs a worker
    assert "@media (max-width:640px)" in page             # thumbs
