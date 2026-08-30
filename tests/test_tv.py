"""narrowhighway.tv — the museum as an old-school cable network (the shell).

Proves the frame: channels are built from the keeping (real card links, never invented); each channel
has what's ON NOW, what's UP NEXT, and the whole line 'from the start'; 'now playing' rotates with the
clock so a channel feels live; a 'For You' lane leads when the viewer says what they seek; a channel
with nothing to show is dropped, never faked; and nothing is generated. Light — corpus.search is
monkeypatched so the suite never loads the 671k-card keeping.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import tv  # noqa: E402


def _fake_search(query, limit=25, include_witness=True, shelves=None):
    # a deterministic stand-in keeping: `limit` verified-looking cards for any seed
    return [{"id": f"card_{abs(hash(query)) % 9973}_{i}",
             "title": f"{query.split()[0].title()} program {i}",
             "snippet": f"A verified program about {query}, number {i}."} for i in range(limit)]


def test_lineup_builds_channels_from_the_keeping_with_now_and_from_start(monkeypatch):
    monkeypatch.setattr(tv.corpus, "search", _fake_search)
    d = tv.lineup(now_epoch=0.0)
    assert d["generated"] is False and d["seeking"] == ""
    assert len(d["channels"]) == len(tv.CHANNELS)          # every standing channel has content
    c = d["channels"][0]
    assert c["now"]["ref"].startswith("/card/")            # 'now playing' is a real card link
    assert c["from_start"] and c["from_start"][0]["ref"].startswith("/card/")  # wind back to the top
    assert c["up_next"]                                     # a schedule, not a lone item


def test_for_you_leads_when_the_viewer_says_what_they_seek(monkeypatch):
    monkeypatch.setattr(tv.corpus, "search", _fake_search)
    d = tv.lineup(seeking="a founder who failed first", now_epoch=0.0)
    assert d["seeking"] == "a founder who failed first"
    assert d["channels"][0]["id"] == "foryou"              # the relationship engine leads
    assert "founder who failed first" in d["channels"][0]["line"]


def test_now_playing_rotates_with_the_clock(monkeypatch):
    monkeypatch.setattr(tv.corpus, "search", _fake_search)
    a = tv.lineup(now_epoch=0.0)["channels"][0]["now"]["id"]
    b = tv.lineup(now_epoch=float(tv.PROGRAM_SECONDS))["channels"][0]["now"]["id"]  # one slot later
    assert a != b                                          # the schedule advanced — it feels live


def test_a_dark_channel_is_dropped_not_faked(monkeypatch):
    def _empty(query, limit=25, include_witness=True, shelves=None):
        return [] if "golf" in query else _fake_search(query, limit, include_witness)
    monkeypatch.setattr(tv.corpus, "search", _empty)
    ids = [c["id"] for c in tv.lineup(now_epoch=0.0)["channels"]]
    assert "golf" not in ids and "witnesses" in ids        # nothing to show -> dark, never invented


def test_field_channel_airs_public_domain_films_from_the_video_canon(monkeypatch):
    """The video plane — the SAME find/canon mechanism, on film. The Field channel leads with Prelinger
    public-domain films from the kept VIDEO canon; each links OUT to the archive.org player (crediting
    the source and driving traffic to it), and a film is what's on now."""
    monkeypatch.setattr(tv.corpus, "search", _fake_search)
    fld = next(c for c in tv.lineup(now_epoch=0.0)["channels"] if c["id"] == "field")
    films = [it for it in fld["from_start"] if it.get("video")]
    assert films, "the Field channel airs at least one film from the video canon"
    assert films[0]["ref"].startswith("https://archive.org/")   # links out to the player, credits the source
    assert films[0]["id"].startswith("vid_")
    assert fld["now"].get("video") == "1"                        # a film leads the channel


if __name__ == "__main__":
    import types
    tv.corpus.search = _fake_search  # type: ignore
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and isinstance(v, types.FunctionType)]
    class _M:
        def setattr(self, *a): pass
    for fn in fns:
        fn(_M())
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed — the channels are built from the keeping, and rotate like a broadcast.")
