"""The source ark — the Tortoise's anchoring half (2026-10-06).

The catalogue page is not the book; this is the step that opens it (Matt 2026-08-02: "I asked it to find
the information, and it couldn't do that"). Pinned here, network-free: the host gate (only trusted hosts
anchor), the deterministic Gutenberg text URL, the archive.org metadata→text resolution with the
access-restriction honoured, and the honest None where there is no openable text (a LoC scan)."""
import os
import tempfile

from concordance import sources as S


def test_host_gate_admits_only_trusted_hosts():
    assert S._host_ok("https://archive.org/download/x/x_djvu.txt") is True
    assert S._host_ok("https://ia800000.us.archive.org/0/items/x/x.txt") is True   # *.archive.org suffix
    assert S._host_ok("https://www.gutenberg.org/cache/epub/1/pg1.txt") is True
    assert S._host_ok("https://evil.example.com/x.txt") is False
    assert S._host_ok("not a url") is False


def test_gutenberg_text_url_is_deterministic():
    assert S.resolve_text_url("https://www.gutenberg.org/ebooks/1342") == \
        "https://www.gutenberg.org/cache/epub/1342/pg1342.txt"


def test_archive_resolves_from_injected_metadata_never_the_network():
    meta = {"metadata": {}, "files": [{"name": "cover.jpg"}, {"name": "thebook_djvu.txt"}]}
    url = S.resolve_text_url("https://archive.org/details/thebook", _meta=meta)
    assert url == "https://archive.org/download/thebook/thebook_djvu.txt"
    # an access-restricted item yields no openable text — honestly None, not a guess
    restricted = {"metadata": {"access-restricted-item": "true"}, "files": [{"name": "x_djvu.txt"}]}
    assert S.resolve_text_url("https://archive.org/details/x", _meta=restricted) is None


def test_no_openable_text_is_honest_none():
    assert S.resolve_text_url("https://www.loc.gov/item/2017-maps-00123/") is None   # a scan, not text
    assert S.resolve_text_url("") is None


def test_path_for_shards_by_prefix_and_needs_an_ark():
    prev = os.environ.get("CONCORDANCE_SOURCES")
    try:
        os.environ.pop("CONCORDANCE_SOURCES", None)
        assert S.sources_dir() is None and S.path_for("abc123", ".txt") is None   # a phone carries cards, not the ark
        d = tempfile.mkdtemp(prefix="nh-ark-")
        os.environ["CONCORDANCE_SOURCES"] = d
        sha = "deadbeef" + "0" * 56
        p = S.path_for(sha, ".txt")
        assert p is not None and p.name == sha + ".txt" and p.parent.name == sha[:2]
    finally:
        if prev is None:
            os.environ.pop("CONCORDANCE_SOURCES", None)
        else:
            os.environ["CONCORDANCE_SOURCES"] = prev
