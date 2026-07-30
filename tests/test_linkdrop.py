"""THE COMMONS · C1d — a link becomes a card with a waybill, and no page of anyone else's is kept.

Matt: *"Any link they enjoy. We can curate and evaluate before we make available."*

Four things are pinned, and each one is a promise that would be easy to break later:

  * **no page bytes are stored** — a waybill may hold only declared FACTS about the artifact
    (address, its own title, size, sha256, when we looked). No excerpt, no description, no body.
    Checked against the declared field list, so a later hand cannot add `excerpt` quietly.
  * **the fetch cannot be turned inward** — a member-supplied URL fetched by our server is an SSRF
    primitive. Loopback, private ranges, link-local, credentials-in-URL, and non-http schemes are
    refused, INCLUDING a hostname that merely resolves to them, and including a redirect into them.
  * **the url is signed** — a destination swapped after signing would stand under the member's name.
  * **our outage never silences a member** — an unreachable link still lands, carrying
    `reach: SYSTEM_ERROR`. "We could not check" is a fact about us, never about the link.

The fetch tests bind a real loopback HTTP server, because the thing under test is network
behaviour and a mocked socket proves nothing about whether we actually refuse to walk inside.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import base64
import http.server
import os
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

PAGE = (b"<html><head><title>  A page with\na multiline title  </title></head>"
        b"<body><p>Body text that must never be kept.</p></body></html>")


@pytest.fixture(autouse=True)
def _isolated():
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    yield
    if prior is None:
        os.environ.pop("CONCORDANCE_DATA_DIR", None)
    else:
        os.environ["CONCORDANCE_DATA_DIR"] = prior


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path.startswith("/gone"):
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("content-length", str(len(PAGE)))
        self.end_headers()
        self.wfile.write(PAGE)

    def log_message(self, *a):
        pass


@pytest.fixture(scope="module")
def loopback():
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


# ------------------------------------------------------------------ the refusals

def test_the_fetch_cannot_be_turned_inward(loopback):
    """The whole reason this module has a guard. Each of these is a real way in."""
    from concordance import linkdrop
    for bad in (
        loopback + "/",                       # explicit loopback
        "http://127.0.0.1/admin",
        "http://localhost:8099/keep.json",    # resolves to loopback
        "http://10.0.0.1/",                   # private
        "http://192.168.1.1/",
        "http://169.254.169.254/latest/meta-data/",   # link-local: the cloud metadata service
        "http://[::1]/",
        "file:///etc/passwd",                 # not http at all
        "gopher://example.com/",
        "http://user:pass@example.com/",      # credentials in the url
        "ftp://example.com/x",
        "",
    ):
        r = linkdrop.waybill(bad)
        assert r.get("ok") is False, f"{bad!r} was fetched — that is a way inside the machine"
        assert r.get("state") == "REFUSED", (bad, r)
        assert r.get("error"), f"{bad!r} was refused with no reason given"


def test_a_refusal_says_which_rule_it_broke():
    """A refusal nobody can read is a refusal they will work around."""
    from concordance import linkdrop
    assert "public internet" in linkdrop.waybill("http://127.0.0.1/")["error"]
    assert "http and https" in linkdrop.waybill("file:///etc/passwd")["error"]
    assert "credentials" in linkdrop.waybill("http://u:p@example.com/")["error"]


# ------------------------------------------------------------- no bytes are kept

def test_a_waybill_carries_facts_and_never_the_page(monkeypatch, loopback):
    """The completion test for C1d, asserted on the actual returned structure."""
    from concordance import linkdrop
    monkeypatch.setattr(linkdrop, "_public_ip", lambda host: (True, ""))   # allow the test server
    r = linkdrop.waybill(loopback + "/thing")
    assert r.get("ok"), r
    wb = r["waybill"]

    clean, problems = linkdrop.no_page_bytes_kept(wb)
    assert clean, problems
    assert set(wb) <= set(linkdrop.WAYBILL_FIELDS)

    blob = repr(wb)
    assert "Body text that must never be kept" not in blob, "the page's content is in the waybill"
    assert "<p>" not in blob and "<html" not in blob, "markup was kept"

    # what it DOES carry: facts about the artifact
    assert wb["bytes"] == len(PAGE)
    assert len(wb["sha256"]) == 64
    assert wb["fetched_at"] > 0 and wb["status"] == 200
    assert wb["page_title"] == "A page with a multiline title", "the title is the artifact's NAME"
    assert "\n" not in wb["page_title"], "a title that spans lines is content"


def test_the_bytes_guard_catches_a_smuggled_body():
    """The guard is the promise. If someone later adds an `excerpt`, this fails — which is the
    point of checking against a declared list instead of a remembered one."""
    from concordance import linkdrop
    ok, problems = linkdrop.no_page_bytes_kept(
        {"url": "https://x.test/", "excerpt": "three paragraphs of someone else's article"})
    assert ok is False and "excerpt" in problems[0]
    long_title = {"url": "https://x.test/", "page_title": "x" * 500}
    assert linkdrop.no_page_bytes_kept(long_title)[0] is False


def test_a_quote_is_a_citation_not_a_copy():
    from concordance import linkdrop
    assert linkdrop.quote_ok("", "")[0] is True, "no quote is fine"
    assert linkdrop.quote_ok("A line worth citing.", "G. K. Chesterton")[0] is True
    assert linkdrop.quote_ok("A line worth citing.", "")[0] is False, "unattributed"
    assert linkdrop.quote_ok("x" * (linkdrop.MAX_QUOTE + 1), "someone")[0] is False, "a chapter"


# --------------------------------------------------------- through the shelf

def _key():
    from concordance import signing
    try:
        return signing.generate_keypair()
    except Exception:  # noqa: BLE001
        pytest.skip("signing unavailable in this build")


def _drop_link(url, body="Worth your time because it shows the actual method, not the theory.",
               quote="", attribution="", ring="shelf"):
    from concordance import shelves, signing
    priv, pub = _key()
    sg = shelves.signable_drop(pub, "link", "A link worth keeping", body, ring,
                               url=url, quote=quote, attribution=attribution)
    if not sg.get("ok"):
        return sg, pub, priv
    sig = signing.sign_bytes(base64.urlsafe_b64decode(sg["signable"]), priv)
    return shelves.drop(sg["fields"], sig, display_name="Matt Harris"), pub, priv


def test_a_link_drop_lands_with_its_waybill(monkeypatch, loopback):
    from concordance import linkdrop, shelves
    monkeypatch.setattr(linkdrop, "_public_ip", lambda host: (True, ""))
    r, pub, _ = _drop_link(loopback + "/good")
    assert r.get("ok"), r
    card = shelves.shelf_of(pub, viewer=pub)["cards"][0]
    x = card["extra"]
    assert x["reach"] == "FETCHED"
    assert x["waybill"]["sha256"] and x["waybill"]["fetched_at"]
    assert card["source"]["url"] == loopback + "/good", "the card points AT the artifact"
    assert card["source"]["authority_tier"] == "member", "still the member's, never ours"
    assert "Body text that must never be kept" not in repr(card), "the page leaked into the card"
    # no actual embed markup anywhere — the POLICY text mentions the word "iframe" on purpose,
    # explaining why there isn't one, so look for the tag rather than the word.
    blob = repr(card).lower()
    for tag in ("<iframe", "<embed", "<video", "<img"):
        assert tag not in blob, f"an embed ({tag}) reached the card — that beacons the reader's IP"
    assert x["embed"] and "iframe would hand" in x["embed"], "the no-embed policy must be stated"


def test_the_url_is_inside_the_signed_bytes(monkeypatch, loopback):
    """Swapping the destination after signing must not verify — otherwise a link the member never
    chose would stand under their name."""
    from concordance import shelves, signing
    from concordance import linkdrop
    monkeypatch.setattr(linkdrop, "_public_ip", lambda host: (True, ""))
    priv, pub = _key()
    sg = shelves.signable_drop(pub, "link", "s", "why this is worth your time", "shelf",
                               url=loopback + "/one")
    sig = signing.sign_bytes(base64.urlsafe_b64decode(sg["signable"]), priv)
    swapped = dict(sg["fields"], url="https://somewhere-else.example/")
    assert shelves.drop(swapped, sig)["ok"] is False, "the url is not covered by the signature"
    assert shelves.drop(sg["fields"], sig)["ok"] is True


def test_our_outage_never_silences_the_member(monkeypatch):
    """An unreachable link still lands. `SYSTEM_ERROR` is a fact about US."""
    from concordance import linkdrop, shelves
    monkeypatch.setattr(linkdrop, "_public_ip", lambda host: (True, ""))
    monkeypatch.setattr(linkdrop, "_open",
                        lambda t: (None, {}, "could not reach it: [simulated outage]"))
    r, pub, _ = _drop_link("https://a-real-site.example/page")
    assert r.get("ok"), "the drop was refused because WE could not fetch — never do that"
    card = shelves.shelf_of(pub, viewer=pub)["cards"][0]
    assert card["extra"]["reach"] == "SYSTEM_ERROR"
    assert card["extra"]["waybill"] == {}
    line = card["presentation"]["link"]["waybill_line"]
    assert "fact about us" in line and "not about the link" in line


def test_a_link_drop_still_needs_the_member_to_say_why():
    """A bare link is not curation. This library exists because a person said why it matters."""
    from concordance import shelves
    priv, pub = _key()
    assert shelves.signable_drop(pub, "link", "s", "", "shelf",
                                 url="https://x.example/")["ok"] is False
    assert shelves.signable_drop(pub, "link", "s", "words", "shelf", url="")["ok"] is False
    assert shelves.signable_drop(pub, "note", "s", "words", "shelf",
                                 url="https://x.example/")["ok"] is False, "only a link kind"
    assert shelves.signable_drop(pub, "link", "s", "words", "shelf",
                                 url="http://127.0.0.1/")["ok"] is False, "refused at step 1"


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
