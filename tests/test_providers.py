"""The providers — the Tortoise's forage sources, with rotation and credit (2026-10-06).

Two covenants (Matt 2026-08-30): a source that fails us MORE THAN ONCE is benched for a cooldown and
checked back later (not deleted); and every surfaced source carries its name + a link as an easy way
back, reaching the READER. Both are pinned here. No network: rotation is time-driven (the `now` param)
and credit is pure."""
import os
import tempfile

os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-prov-")

from concordance import providers as P                         # noqa: E402

DAY = 86400.0


def _reset():
    try:
        P._health_path().unlink()
    except OSError:
        pass


def test_second_failure_benches_then_cooldown_lets_it_return():
    _reset()
    t = 1_000_000.0
    P.record("internet_archive", False, now=t)                 # first strike
    assert P.benched("internet_archive", now=t) is False       # "fails us more than once" — one is not enough
    P.record("internet_archive", False, now=t + 10)            # SECOND strike within the window -> benched
    assert P.benched("internet_archive", now=t + 10) is True
    assert P.benched("internet_archive", now=t + P.COOLDOWN_SECONDS + 20) is False   # cooldown expired -> back
    # a failure AFTER the cooldown is a FRESH first strike, not a pile-on (clean two-strike window)
    P.record("internet_archive", False, now=t + P.COOLDOWN_SECONDS + 30)
    assert P.benched("internet_archive", now=t + P.COOLDOWN_SECONDS + 40) is False


def test_success_clears_the_slate():
    _reset()
    t = 2_000_000.0
    P.record("library_of_congress", False, now=t)
    P.record("library_of_congress", False, now=t + 5)
    assert P.benched("library_of_congress", now=t + 5) is True
    P.record("library_of_congress", True, now=t + 6)           # a win wipes the strikes
    assert P.benched("library_of_congress", now=t + 6) is False


def test_active_excludes_paused_and_benched():
    _reset()
    t = 3_000_000.0
    ids = {p["id"] for p in P.active("text", now=t)}
    assert "internet_archive" in ids and "usda_bulletins" in ids and "library_of_congress" in ids
    assert "project_gutenberg" not in ids and "youtube_cc" not in ids   # paused by policy
    P.record("usda_bulletins", False, now=t)
    P.record("usda_bulletins", False, now=t + 1)                # bench it
    assert "usda_bulletins" not in {p["id"] for p in P.active("text", now=t + 1)}
    # video plane carries its own sources (Prelinger), not the text-only ones
    assert "usda_bulletins" not in {p["id"] for p in P.active("video", now=t)}


def test_credit_reaches_the_reader_with_a_way_back():
    doc = {"provider_id": "internet_archive", "url": "https://archive.org/details/somebook"}
    c = P.credit(doc)
    assert c["name"] == "Internet Archive" and c["url"].endswith("somebook")
    line = P.line(doc)
    assert "Internet Archive" in line and "archive.org/details/somebook" in line   # the way back, to the reader
    # resolve by the human source name when no provider_id is given
    assert P.credit({"source": "Project Gutenberg", "url": "u"})["name"] == "Project Gutenberg"


def test_unknown_source_is_ignored_and_credits_nothing():
    _reset()
    P.record("not_a_provider", False, now=1.0)                  # never raises, never benches a stranger
    assert P.benched("not_a_provider", now=2.0) is False
    assert P.line({"source": "Some Random Blog", "url": "x"}) == ""   # better to say nothing than credit no one
