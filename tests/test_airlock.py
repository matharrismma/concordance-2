"""The input airlock — a dragged file becomes cards + a map, and the file is kicked back out.

The invariants: cards are minted and map back to the USER's file (their link is the waybill); the
cards are PRIVATE and the user's, never merged into core; and ingest persists NOTHING to disk — the
file was worked in the chamber and ejected.
"""
from __future__ import annotations

from concordance import airlock

_TEXT = ("# Chapter One\n\nThe quick brown fox jumps over the lazy dog; faith and grace abound in the "
         "morning light.\n\n# Chapter Two\n\nAnother section, on wisdom and knowledge and the fear of "
         "the Lord, which is the beginning of understanding.\n")


def test_ingest_mints_cards_that_map_back_to_the_users_file():
    r = airlock.ingest(_TEXT, source="mybook.txt", title="My Book", link="file:///D:/mybook.txt")
    assert r["ok"] and len(r["cards"]) >= 1
    c = r["cards"][0]
    assert c["shelf"] == "dropbox" and c["visibility"] == "private" and c["author"] == "user"
    assert c["source"]["url"] == "file:///D:/mybook.txt"          # the waybill back to their file
    assert c["extra"]["carried_by_user"] is True and c["generated"] is False
    assert r["map"]["sections"] == len(r["cards"]) and r["map"]["outline"] and r["map"]["top_terms"]
    assert "kept nothing" in r["note"].lower()


def test_empty_file_is_refused():
    assert airlock.ingest("   ")["ok"] is False


def test_ingest_persists_nothing_to_disk(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    airlock.ingest(_TEXT, source="x.txt")
    assert not any(tmp_path.iterdir())                           # nothing deposited — the file was ejected
