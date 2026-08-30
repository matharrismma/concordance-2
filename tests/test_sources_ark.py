"""THE SOURCE ARK — a body lands and is verifiable, or the card says plainly that it did not.

Matt, 2026-08-01: *"We want as many of the sources on the external hard drive as possible. We will
have multiple drives and store them in many locations... we spread the Card Corpus across the world
by being useful and cheap and small."*

Cards travel; bodies anchor. This is the anchoring half, and the whole value of it is that a drive
copied to another drive stays verifiable BY ITS HOLDER — no network, no index, no trusting us. So
the tests that matter most here are not "did it download" but:

  * a stored body re-hashes to the name it is filed under (and a corrupted one is reported INVALID,
    never quietly skipped — storage is never trusted, same rule as attestations)
  * the same content fetched twice is stored ONCE
  * a host outside the public-domain allowlist is refused BEFORE any byte is requested
  * a body over the ceiling is refused DURING streaming, because a Content-Length header can lie
  * a failed fetch still yields an honest answer with a reason, so the caller can mint a card that
    admits the gap rather than claiming a holding it does not have

Runnable with pytest OR directly.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from concordance import sources  # noqa: E402


@pytest.fixture()
def ark(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_SOURCES", str(tmp_path))
    return tmp_path


def _plant(ark: Path, body: bytes, ext: str = ".txt") -> str:
    """Put a body on the drive the way fetch() would, and return its sha."""
    sha = hashlib.sha256(body).hexdigest()
    d = ark / sha[:2]
    d.mkdir(parents=True, exist_ok=True)
    (d / (sha + ext)).write_bytes(body)
    (d / (sha + ".waybill.json")).write_text(json.dumps({
        "sha256": sha, "bytes": len(body), "media_type": "text/plain",
        "origin_url": "https://www.gutenberg.org/ebooks/1", "path": str(d / (sha + ext)),
    }), encoding="utf-8")
    return sha


def test_a_stored_body_reverifies_against_its_own_name(ark):
    """The promise a copied drive makes to whoever holds it."""
    sha = _plant(ark, b"In the beginning was the Word.\n")
    v = sources.verify(sha)
    assert v["status"] == "valid", v
    assert v["sha256"] == v["actual"]


def test_a_corrupted_body_is_reported_invalid_not_skipped(ark):
    """A copy that arrives corrupt is worse than no copy, because it looks like safety."""
    body = b"the original bytes"
    sha = _plant(ark, body)
    p = Path(sources.held(sha)["path"])
    p.write_bytes(b"the original bytes, tampered")     # same name, different content

    v = sources.verify(sha)
    assert v["status"] == "invalid", (
        "a file whose bytes no longer match its name must be reported INVALID — storage is never "
        f"trusted, and a silent pass here would launder corruption as provenance. got {v}")
    assert v["actual"] != sha


def test_a_body_we_do_not_hold_is_absent_not_an_error(ark):
    assert sources.verify("0" * 64)["status"] == "absent"
    assert sources.held("0" * 64) is None


def test_a_host_off_the_allowlist_is_refused_before_any_request(ark):
    """PD/OA only, and the refusal names the host so it can be acted on."""
    r = sources.fetch("https://example.com/whatever.txt")
    assert r["status"] == sources.NOT_HELD
    assert "not an allowed public-domain source" in r["reason"]
    assert "example.com" in r["reason"]


def test_the_allowlist_is_the_same_hosts_the_finder_searches(ark):
    """One gate, not two that can drift apart."""
    for host in ("www.gutenberg.org", "archive.org", "www.loc.gov"):
        assert host in sources.ALLOWED_HOSTS


def test_an_archive_storage_node_is_reachable(ark):
    """THE ARK COULD NOT FETCH FROM ARCHIVE.ORG AT ALL, and nothing said so for as long as it
    existed. Every `archive.org/download/...` redirects to a numbered storage node chosen per
    request — ia601905, ia801905, ia902703 — and the allowlist named a single guessed one
    (`ia801.us.archive.org`). So the redirect check, which is correct, refused every real
    download: "redirected off the allowlist to ia801905.us.archive.org".

    Found 2026-08-01 on the first acquisition ever attempted through the real fetch (the 1923
    Manual of the Church of the Nazarene). The same shape as the fd leak and both search fixes —
    code that looks right on a path nobody walked.
    """
    # THREE CONTINENTS, because the first fix admitted only `.us.` — the suffix of the single node
    # observed that morning — and the same evening a six-book batch was refused entire when the
    # CDN answered from `.ca.` and `.eu.`. Generalizing from exactly what you saw is how this
    # constant has been wrong twice; the trust boundary is the DNS zone, not the continent.
    for node in ("ia801905.us.archive.org", "dn790008.ca.archive.org",
                 "dn760107.eu.archive.org", "ia902703.us.archive.org"):
        assert sources._host_ok(f"https://{node}/0/items/x/x_djvu.txt"), \
            f"{node} refused — archive.org downloads cannot be fetched"


def test_the_widening_did_not_open_the_gate(ark):
    """A suffix allowlist is only safe if the leading dot is doing its job. Only archive.org
    controls the archive.org zone; everything else must still be refused."""
    for host in ("evil.com", "archive.org.evil.com", "notarchive.org", "evil-archive.org",
                 "evil-us.archive.org.attacker.net", "us.archive.org.evil.net"):
        assert not sources._host_ok(f"https://{host}/x.txt"), f"{host} was let through"
    r = sources.fetch("https://archive.org.evil.com/whatever.txt")
    assert r["status"] == sources.NOT_HELD


def test_a_device_that_anchors_nothing_says_so(monkeypatch):
    """A phone carries cards, not the ark — that is legitimate, and must not read as failure."""
    monkeypatch.delenv("CONCORDANCE_SOURCES", raising=False)
    r = sources.fetch("https://www.gutenberg.org/ebooks/1")
    assert r["status"] == sources.NOT_HELD
    assert "anchors no sources" in r["reason"]
    assert sources.stats()["anchoring"] is False


def test_an_empty_url_is_refused_with_a_reason(ark):
    r = sources.fetch("")
    assert r["status"] == sources.NOT_HELD and r["reason"]


def test_stats_counts_what_is_actually_on_the_drive(ark):
    _plant(ark, b"one")
    _plant(ark, b"two")
    s = sources.stats()
    assert s["anchoring"] is True
    assert s["bodies"] == 2, "stats must WALK the drive — a maintained count drifts"
    assert s["bytes"] == 6


def test_the_same_content_is_stored_once(ark):
    """Content-addressed: the hash IS the name, so a second copy has nowhere different to go."""
    body = b"identical bytes"
    sha1 = _plant(ark, body)
    sha2 = _plant(ark, body)
    assert sha1 == sha2
    assert len(list(ark.glob("*/*.txt"))) == 1


def test_the_ceiling_is_enforced_on_the_stream_not_the_header(ark, monkeypatch):
    """A server can lie in Content-Length; it cannot lie about how many bytes it actually sent."""
    import io
    import urllib.request

    monkeypatch.setattr(sources, "MAX_BYTES", 1024)

    class _Resp(io.BytesIO):
        headers = {"content-type": "text/plain", "content-length": "10"}   # the lie

        def geturl(self):
            return "https://www.gutenberg.org/files/1/1.txt"

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda *a, **k: _Resp(b"x" * 5000))               # the truth
    r = sources.fetch("https://www.gutenberg.org/files/1/1.txt")
    assert r["status"] == sources.NOT_HELD
    assert "ceiling" in r["reason"], r
    assert not list(ark.glob("*/*.txt")), "the oversized body must not be left on the drive"


def test_a_refusal_names_the_status_code(ark, monkeypatch):
    """"could not fetch: HTTPError" is not actionable.

    The Library of Congress answers 403 to our agent on item pages — an ACCESS REFUSAL, acted on
    quite differently from a dead link or a network fault. The first version collapsed both into
    the exception's class name and cost a separate investigation to learn which it was.
    """
    import urllib.error
    import urllib.request

    def _raise(*a, **k):
        raise urllib.error.HTTPError("http://www.loc.gov/item/1/", 403, "Forbidden", {}, None)

    monkeypatch.setattr(urllib.request, "urlopen", _raise)
    r = sources.fetch("http://www.loc.gov/item/1/")
    assert r["status"] == sources.NOT_HELD
    assert "403" in r["reason"] and "Forbidden" in r["reason"], r


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))


def test_a_catalogue_page_resolves_to_the_text_behind_it(ark):
    """The tortoise finds DETAIL pages; for months the mint carded the citation because nothing
    could open the book behind it ("I asked it to find the information, and it couldn't do
    that"). Gutenberg resolves deterministically; archive.org through its metadata — injected
    here so no test depends on the network."""
    assert sources.resolve_text_url("https://www.gutenberg.org/ebooks/1342") == \
        "https://www.gutenberg.org/cache/epub/1342/pg1342.txt"
    meta = {"metadata": {}, "files": [{"name": "x_scandata.xml"}, {"name": "abc_djvu.txt"}]}
    assert sources.resolve_text_url("https://archive.org/details/abc", _meta=meta) == \
        "https://archive.org/download/abc/abc_djvu.txt"


def test_a_scan_filename_with_a_space_is_percent_encoded(ark):
    """Some scans (e.g. an 'in.gov.ignca…' item) name their text file with a space or stray control
    character. Built raw, that URL made urllib refuse ("URL can't contain control characters") and the
    openable book was lost. The path segments are percent-encoded now, so no literal space survives."""
    spacey = {"metadata": {}, "files": [{"name": "in.gov 2047_djvu.txt"}]}
    url = sources.resolve_text_url("https://archive.org/details/in.gov.2047", _meta=spacey)
    assert url == "https://archive.org/download/in.gov.2047/in.gov%202047_djvu.txt"
    assert " " not in url          # the exact thing that made urllib refuse


def test_a_restricted_or_textless_item_resolves_to_nothing(ark):
    """None is an honest answer; a guessed URL that 404s would waste the fetch and log a lie."""
    restricted = {"metadata": {"access-restricted-item": "true"},
                  "files": [{"name": "abc_djvu.txt"}]}
    assert sources.resolve_text_url("https://archive.org/details/abc", _meta=restricted) is None
    no_text = {"metadata": {}, "files": [{"name": "abc.pdf"}, {"name": "abc.gif"}]}
    assert sources.resolve_text_url("https://archive.org/details/abc", _meta=no_text) is None
    assert sources.resolve_text_url("https://www.loc.gov/item/12003656/") is None
    assert sources.resolve_text_url("") is None
