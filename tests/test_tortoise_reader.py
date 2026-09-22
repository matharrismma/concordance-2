"""THE TORTOISE'S READ PATH — the whole public-domain source, delivered on demand, and honest at
every miss.

Matt, 2026-09-21: "We will be the card catalogue. We won't hold the texts on board... We can send
the whole source but it will be the tortoise."

The catalogue card is the hare — light, everywhere. The book is the tortoise — fetched live from the
public-domain source the moment a reader opens it, read THROUGH (never stored: the box carries the
catalogue, not the library). What matters here is the same discipline the ark's fetch carries, plus
the reader-specific promises:

  * the SAME allowlist gate — you can only read into the public-domain hosts, and a redirect must
    still land on one (an open web proxy is exactly what this is not)
  * the ceiling is enforced on the STREAM, not a header a server can lie in
  * a body that is not inline text (a PDF/epub) is handed back as a link to CARRY, not faked as text
  * nothing is written to the drive — read_through holds no copy
  * a card that points nowhere fetchable is not dressed up as a book; the miss says why, and still
    hands back the whole source to carry

No test here touches the network: urllib is mocked and Archive metadata is injected.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import io
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from concordance import sources, tortoise  # noqa: E402


class _Resp(io.BytesIO):
    """A stand-in urlopen response: bytes in, a content-type, and a final URL for the redirect check."""

    def __init__(self, body: bytes, ctype: str = "text/plain", final: str = None):
        super().__init__(body)
        self.headers = {"content-type": ctype}
        self._final = final or "https://dn790009.ca.archive.org/0/items/x/x_djvu.txt"

    def geturl(self):
        return self._final

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _urlopen(resp):
    return lambda *a, **k: resp


# ── read_through: the gate, the ceiling, the honesty ─────────────────────────────────────────────

def test_a_host_off_the_allowlist_is_refused_before_any_request(monkeypatch):
    """The reader is not an open web proxy — the same gate as the ark's fetch, refused by host."""
    called = {"n": 0}
    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda *a, **k: called.__setitem__("n", called["n"] + 1))
    r = sources.read_through("https://example.com/book.txt")
    assert r["status"] == "not_available"
    assert "not an allowed public-domain source" in r["reason"]
    assert called["n"] == 0, "a refused host must not reach the network at all"


def test_a_redirect_off_the_allowlist_is_refused(monkeypatch):
    """A redirect must still land somewhere allowed, or the allowlist is a suggestion."""
    monkeypatch.setattr(urllib.request, "urlopen",
                        _urlopen(_Resp(b"hello", final="https://evil.com/x.txt")))
    r = sources.read_through("https://archive.org/download/x/x_djvu.txt")
    assert r["status"] == "not_available"
    assert "off the allowlist" in r["reason"]


def test_it_reads_text_through_and_stores_nothing(tmp_path, monkeypatch):
    """The whole point: the text reaches the reader; no copy lands on the drive."""
    monkeypatch.setenv("CONCORDANCE_SOURCES", str(tmp_path))       # even WITH an ark configured…
    monkeypatch.setattr(urllib.request, "urlopen",
                        _urlopen(_Resp(b"In the beginning was the Word.\n")))
    r = sources.read_through("https://archive.org/download/x/x_djvu.txt")
    assert r["status"] == "read"
    assert "In the beginning" in r["text"]
    assert r["truncated"] is False
    assert not list(tmp_path.glob("*/*")), "read_through must hold NO copy — the box carries the catalogue"


def test_the_ceiling_is_enforced_on_the_stream(monkeypatch):
    """A very long book is capped, and says so — the cap is on bytes actually read, not a header."""
    monkeypatch.setattr(urllib.request, "urlopen", _urlopen(_Resp(b"a" * 50000)))
    r = sources.read_through("https://archive.org/download/x/x_djvu.txt", read_bytes=1024)
    assert r["status"] == "read"
    assert r["truncated"] is True
    assert r["chars"] <= 2048


def test_html_is_reduced_to_readable_text(monkeypatch):
    """A Gutenberg HTML edition reads as text, not as tags."""
    body = b"<html><head><style>x{}</style></head><body><h1>Title</h1><p>Line&nbsp;one.</p></body></html>"
    monkeypatch.setattr(urllib.request, "urlopen",
                        _urlopen(_Resp(body, ctype="text/html",
                                       final="https://www.gutenberg.org/files/1/1-h/1-h.htm")))
    r = sources.read_through("https://www.gutenberg.org/files/1/1-h/1-h.htm")
    assert r["status"] == "read"
    assert "Title" in r["text"] and "Line" in r["text"]
    assert "<" not in r["text"] and "style" not in r["text"]


def test_a_pdf_is_handed_back_to_carry_not_faked_as_text(monkeypatch):
    """A body we cannot put on a screen as text is offered as a download, honestly."""
    monkeypatch.setattr(urllib.request, "urlopen",
                        _urlopen(_Resp(b"%PDF-1.4 ...", ctype="application/pdf",
                                       final="https://archive.org/download/x/x.pdf")))
    r = sources.read_through("https://archive.org/download/x/x.pdf")
    assert r["status"] == "binary"
    assert r["download_url"].endswith(".pdf")
    assert "download the whole source" in r["reason"]


def test_a_refused_source_names_the_status(monkeypatch):
    def _raise(*a, **k):
        raise urllib.error.HTTPError("https://archive.org/download/x/x_djvu.txt", 403, "Forbidden", {}, None)
    monkeypatch.setattr(urllib.request, "urlopen", _raise)
    r = sources.read_through("https://archive.org/download/x/x_djvu.txt")
    assert r["status"] == "not_available"
    assert "403" in r["reason"]


# ── tortoise.open_work: card → the whole work, provenance carried ────────────────────────────────

def _trades_card(url="https://archive.org/details/cassellscarpentr00hasl"):
    return {
        "id": "card_arch_test", "title": "Cassells' carpentry and joinery",
        "author": "the trades catalogue (public domain, held in the ark)", "language": "english",
        "source": {"url": url, "identifier": "cassellscarpentr00hasl",
                   "pd_basis": "public domain by copyright expiry (published 1907, pre-1929)",
                   "pd_year": 1907, "license": "public-domain",
                   "held": "external drive (durability mirror); served on demand via the tortoise"},
    }


def test_readable_gates_on_the_allowlist():
    assert tortoise.readable(_trades_card()) is True
    assert tortoise.readable(_trades_card("https://example.com/x")) is False
    assert tortoise.readable({"source": {}}) is False
    assert tortoise.readable(None) is False


def test_open_work_reads_a_catalogue_card(monkeypatch):
    """The catalogue card opens into the whole work, with its public-domain provenance carried."""
    monkeypatch.setattr(sources, "resolve_text_url",
                        lambda url, meta=None: "https://archive.org/download/c/c_djvu.txt")
    monkeypatch.setattr(sources, "read_through",
                        lambda url, **k: {"status": "read", "text": "CARPENTRY AND JOINERY...",
                                          "chars": 24, "truncated": False,
                                          "media_type": "text/plain",
                                          "final_url": "https://dn7.ca.archive.org/x"})
    r = tortoise.open_work(_trades_card())
    assert r["status"] == "read"
    assert r["title"] == "Cassells' carpentry and joinery"
    assert r["text"].startswith("CARPENTRY")
    assert r["pd_basis"].startswith("public domain")
    assert r["detail_url"].endswith("cassellscarpentr00hasl"), "the whole source stays carriable"


def test_open_work_with_no_plaintext_edition_is_honest(monkeypatch):
    """Images or an access-restricted scan → say so, and still hand back the source to carry."""
    monkeypatch.setattr(sources, "resolve_text_url", lambda url, meta=None: None)
    r = tortoise.open_work(_trades_card())
    assert r["status"] == "not_available"
    assert r["detail_url"]                       # still carriable
    assert "images" in r["reason"] or "access-restricted" in r["reason"]


def test_open_work_on_a_card_pointing_nowhere_fetchable(monkeypatch):
    """A card whose source is off the allowlist never pretends to be a book."""
    r = tortoise.open_work(_trades_card("https://example.com/whatever"))
    assert r["status"] == "not_available"
    assert "no fetchable public-domain source" in r["reason"]


# ── the finding path: a work is one click from the results ───────────────────────────────────────

def test_a_search_brief_marks_a_readable_work():
    """A search hit carries `readable` so a listing can put a direct 'Read the full work' link on the
    hit itself — the whole PD source one click from the results, not two (hit -> card -> read)."""
    from concordance.web.api import _card_brief
    work = {"id": "card_arch_x", "title": "A PD work", "shelf": "trades",
            "source": {"url": "https://archive.org/details/x"}}
    plain = {"id": "card_y", "title": "A theory", "shelf": "floor", "source": {"url": ""}}
    assert _card_brief(work)["readable"] is True
    assert _card_brief(plain)["readable"] is False


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
