"""THE WORKSHOP — the operator's improvement queue (workshop.py).

The interface Matt asked for on 2026-09-23: file improvements through the site, the agent drains
them. The whole security claim, made testable:

  * a filing is provably the operator (a detached Ed25519 signature over the canonical bytes), AND
  * authorized (the signer's fingerprint is in the operator allowlist) — a VALID signature from an
    unlisted key is refused, because holding a key is not the same as being allowed to task the queue;
  * stale or tampered signed bytes are refused;
  * the drain (read + status) is gated by a separate operator TOKEN, so the agent never needs the
    operator's private key;
  * nothing here executes — it records intent and status only.

Hermetic; real Ed25519 (skips only if the crypto library is absent).
"""
import time

import pytest

from concordance import identity, workshop

pytestmark = pytest.mark.skipif(not identity.signing_available(),
                                reason="Workshop filing needs real Ed25519 signing")

PHRASE = "in the beginning God created the heavens and the earth and it was very good"
OTHER = "the Lord is my shepherd I shall not want he makes me lie down in green pastures"


@pytest.fixture
def op():
    return identity.derive_identity(PHRASE)


@pytest.fixture
def other():
    return identity.derive_identity(OTHER)


@pytest.fixture(autouse=True)
def _env(tmp_path, monkeypatch):
    """Each test gets a private ledger and a clean gate config (both closed by default)."""
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("CONCORDANCE_OPERATOR_FPS", raising=False)
    monkeypatch.delenv("CONCORDANCE_OPERATOR_TOKEN", raising=False)
    yield


def _sign(idn, fields):
    return identity.sign(idn["private_key"], workshop._canon(fields))


def _file(idn, monkeypatch, authorize=True, kind="improve", title="Fix the stacks walk",
          body="the library walk skips a produced shelf", target=""):
    if authorize:
        monkeypatch.setenv("CONCORDANCE_OPERATOR_FPS", idn["id"])
    s = workshop.signable(idn["public_key"], kind, title, body, target)
    assert s["ok"], s
    return workshop.file(s["fields"], _sign(idn, s["fields"]))


# ── the happy path ──────────────────────────────────────────────────────────────────────────

def test_operator_files_a_signed_authorized_improvement(op, monkeypatch):
    r = _file(op, monkeypatch, title="Route the Floor", body="the 217 theories sit in no deck")
    assert r["ok"] and r["id"].startswith("wk_")
    q = workshop.queue()
    assert q["total"] == 1
    it = q["items"][0]
    assert it["title"] == "Route the Floor" and it["state"] == "open"
    assert it["author_fp"] == op["id"]


# ── gate 2: authorization is not authenticity ─────────────────────────────────────────────────

def test_valid_signature_from_unlisted_key_is_refused(op, monkeypatch):
    # A perfectly valid signature — but the key is not on the operator allowlist.
    r = _file(op, monkeypatch, authorize=False)
    assert not r["ok"] and "authorized operator" in r["error"]


def test_filing_is_closed_when_no_operator_is_configured(op, monkeypatch):
    # Fail-safe: an empty allowlist means the queue is unclaimed, not open to all.
    assert workshop.operator_fps() == set()
    r = _file(op, monkeypatch, authorize=False)
    assert not r["ok"]


def test_a_different_operator_can_be_authorized(other, monkeypatch):
    r = _file(other, monkeypatch)      # authorize=True lists OTHER's fingerprint
    assert r["ok"]


# ── gate 1: authenticity ──────────────────────────────────────────────────────────────────────

def test_tampered_fields_do_not_verify(op, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_OPERATOR_FPS", op["id"])
    s = workshop.signable(op["public_key"], "improve", "t", "the original words")
    sig = _sign(op, s["fields"])
    swapped = dict(s["fields"], body="words the operator never signed")
    r = workshop.file(swapped, sig)
    assert not r["ok"] and "verify" in r["error"]


def test_stale_signed_bytes_are_refused(op, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_OPERATOR_FPS", op["id"])
    fields = {"at": int(time.time()) - workshop.SIGNATURE_TTL_S - 100,
              "author": op["public_key"], "body": "b", "kind": "improve",
              "nonce": "deadbeef0001", "target": "", "title": "t"}
    r = workshop.file(fields, _sign(op, fields))
    assert not r["ok"] and "stale" in r["error"]


def test_a_signature_from_another_key_cannot_impersonate(op, other, monkeypatch):
    # OTHER signs, but the fields claim OP as author: the signature will not verify against OP's key.
    monkeypatch.setenv("CONCORDANCE_OPERATOR_FPS", op["id"])
    s = workshop.signable(op["public_key"], "improve", "t", "b")
    r = workshop.file(s["fields"], _sign(other, s["fields"]))
    assert not r["ok"] and "verify" in r["error"]


# ── idempotency ───────────────────────────────────────────────────────────────────────────────

def test_the_same_signed_filing_twice_is_one_item(op, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_OPERATOR_FPS", op["id"])
    s = workshop.signable(op["public_key"], "improve", "t", "b")
    sig = _sign(op, s["fields"])
    a = workshop.file(s["fields"], sig)
    b = workshop.file(s["fields"], sig)
    assert a["ok"] and b["ok"] and a["id"] == b["id"] and b.get("duplicate")
    assert workshop.queue()["total"] == 1


# ── the drain: token, status lifecycle, notes ─────────────────────────────────────────────────

def test_status_lifecycle_and_queue_filtering(op, monkeypatch):
    r = _file(op, monkeypatch)
    wid = r["id"]
    # open shows in the live queue
    assert wid in {it["id"] for it in workshop.queue()["items"]}
    # drainer takes it, then finishes it
    assert workshop.update(wid, state="in_progress", by="claude", note="reading the seeders")["ok"]
    assert workshop.queue()["items"][0]["state"] == "in_progress"
    assert workshop.update(wid, state="done", by="claude", note="routed; tests green")["ok"]
    # done drops out of the live queue but is reachable by explicit state
    assert workshop.queue()["total"] == 0
    done = workshop.queue(state="done")
    assert done["total"] == 1
    it = done["items"][0]
    assert it["state"] == "done" and len(it["notes"]) == 2
    assert it["notes"][-1]["text"] == "routed; tests green"


def test_update_requires_a_name_and_a_real_change(op, monkeypatch):
    wid = _file(op, monkeypatch)["id"]
    assert not workshop.update(wid, state="done", by="")["ok"]          # no name
    assert not workshop.update(wid, by="claude")["ok"]                   # neither state nor note
    assert not workshop.update(wid, state="bogus", by="claude")["ok"]    # bad state
    assert not workshop.update("wk_nope", state="done", by="claude")["ok"]  # no such item


def test_declined_is_a_recorded_refusal(op, monkeypatch):
    wid = _file(op, monkeypatch)["id"]
    assert workshop.update(wid, state="declined", by="claude",
                           note="out of scope — spun to its own task")["ok"]
    d = workshop.queue(state="declined")
    assert d["total"] == 1 and d["items"][0]["notes"][-1]["text"].startswith("out of scope")


# ── the API layer (dispatch-level, hermetic): file through the site, drain as operator ──────────

def test_route_signable_file_and_operator_drain(op, monkeypatch):
    from concordance.web import api
    from concordance.web.api import EngineConfig
    monkeypatch.setenv("CONCORDANCE_OPERATOR_FPS", op["id"])
    # 1) ask the site for the exact bytes to sign
    s, p = api.dispatch("POST", "/workshop/signable", {},
                        {"author": op["public_key"], "kind": "improve",
                         "title": "Route the Floor", "body": "217 theories sit in no deck"}, EngineConfig())
    assert s == 200 and p["ok"], p
    sig = _sign(op, p["fields"])
    # 2) file it — signature-gated (no operator flag needed; the signature IS the auth)
    s, p = api.dispatch("POST", "/workshop", {}, {"fields": p["fields"], "signature": sig}, EngineConfig())
    assert s == 200 and p["ok"], p
    wid = p["id"]
    # 3) the queue is the operator's — refused without the keep operator decision, served with it
    s, _ = api.dispatch("GET", "/workshop", {}, None, EngineConfig())
    assert s == 403
    s, p = api.dispatch("GET", "/workshop", {}, None, EngineConfig(), operator=True)
    assert s == 200 and p["items"][0]["id"] == wid
    # 4) status is the operator's too
    s, _ = api.dispatch("POST", "/workshop/status", {}, {"id": wid, "state": "done", "by": "claude"}, EngineConfig())
    assert s == 403
    s, p = api.dispatch("POST", "/workshop/status", {},
                        {"id": wid, "state": "done", "by": "claude"}, EngineConfig(), operator=True)
    assert s == 200 and p["ok"]


def test_route_file_from_unlisted_key_is_403(op, monkeypatch):
    from concordance.web import api
    from concordance.web.api import EngineConfig
    # no allowlist configured → a valid signature, but the key is not an authorized operator
    s, p = api.dispatch("POST", "/workshop/signable", {},
                        {"author": op["public_key"], "kind": "fix", "title": "t", "body": "b"}, EngineConfig())
    sig = _sign(op, p["fields"])
    s, p = api.dispatch("POST", "/workshop", {}, {"fields": p["fields"], "signature": sig}, EngineConfig())
    assert s == 403 and "authorized operator" in str(p)
