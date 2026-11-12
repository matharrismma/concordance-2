"""Steps catena and catena2 (run 2026-11-11-fathers-shelf): the commentary shelf reads the Catena Aurea from its
pinned build.

Hermetic. tests/fixtures/catena_aurea/shelf/ holds files of the build tools/build_catena.py wrote from the two copies
(_books.json, _authors.json, MAT/1.json, MAT/5.json, MRK/10.json, LUK/22.json, JHN/3.json, JHN/5.json, unchanged);
each test lays them out at data/builds/catena-aurea/<the pinned hash>/ under a temporary data directory, the one
place the shelf reads them.
Matthew Henry is read from a fixture store (placeholder text, labelled so), and his responses are held byte-identical
to those the step's base gave over the same store (tests/fixtures/catena_aurea/henry_at_base.json).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import builds, commentary, mcp  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "catena_aurea"
BASE = json.loads((FIX / "henry_at_base.json").read_text(encoding="utf-8"))
GOLDEN = {e["id"]: e for e in json.loads((ROOT / "tools" / "catena_aurea" / "golden.json").read_text(
    encoding="utf-8"))["excerpts"]}
CATENA = "catena-aurea"
WIT, SEC = EngineConfig("witness"), EngineConfig("secular")


def _henry_store(root: Path) -> None:
    for rel, obj in BASE["store"].items():
        p = root / "matthew-henry" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj), encoding="utf-8")


@pytest.fixture
def shelf(tmp_path, monkeypatch):
    """Henry's fixture store and the Catena build at its pinned hash: the build's directory."""
    _henry_store(tmp_path / "commentary")
    # (with no pin, as at the base, the build lies under a hash nothing pins, and nothing reads it)
    pin = builds.pinned_hash(CATENA) or "0" * 64
    built = tmp_path / "data" / "builds" / CATENA / pin
    shutil.copytree(FIX / "shelf", built)
    monkeypatch.setenv("CONCORDANCE_COMMENTARY_DIR", str(tmp_path / "commentary"))
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path / "data"))
    return built


def _catena(ref):
    return commentary.for_ref(ref, source=CATENA)


def test_matthew_1_1_serves_golden_excerpts_with_authors_kept_distinct(shelf):
    r = _catena("Matthew 1:1")
    assert (r["status"], r["source"], r["verse"]) == ("ok", CATENA, 1)
    assert "Public Domain" in r["license"] and "1841-45" in r["attribution"] and r["via"]
    items = r["commentary"]
    # every excerpt served on Matthew 1:1 is its golden entry (the golden holds every Matthew 1:1 excerpt, read from
    # the page image), word for word, under the writer the edition prints
    for it in items:
        same = [g for g in GOLDEN.values() if g["verse"] == "Matthew 1:1" and g["words"] == it["text"]]
        assert len(same) == 1 and same[0]["author_as_printed"] == it["author_as_printed"], it["author_as_printed"]
        assert it["verse"] == 1 and it["range"] == "Matthew 1:1"
    assert [it["author_as_printed"] for it in items] == ["CHRYS", "REMIGIUS", "PSEUDO-CHRYS", "AUG", "CYRIL"]
    by = {it["author_as_printed"]: it for it in items}
    # Pseudo-Chrysostom is never Chrysostom: a work under a Father's name, not the Father
    assert (by["CHRYS"]["author"], by["CHRYS"]["writer"]) == ("John Chrysostom", "a Father")
    assert by["PSEUDO-CHRYS"]["author"] is None and by["PSEUDO-CHRYS"]["writer"] == "a work under a Father's name"
    assert by["PSEUDO-CHRYS"]["text"] != by["CHRYS"]["text"]
    # a later writer is labelled so
    assert (by["REMIGIUS"]["author"], by["REMIGIUS"]["writer"]) == ("Remigius of Auxerre", "a later writer")
    # Jerome and Rabanus on Matthew 1:1 are held (their two copies read otherwise): absent, never under another name
    assert not {"JEROME", "RABANUS"} & set(by)
    assert all(it["citation"] for it in items)                 # a citation as both copies read it, or 'not confirmed'


def test_a_verse_the_catena_does_not_reach_reads_none(shelf):
    # verses in chapters the build serves that no excerpt served reaches, and a book the Catena is not on
    for ref in ("Matthew 1:3", "Matthew 1:19", "John 3:1", "John 3:13", "John 3:19", "Genesis 1:1"):
        r = _catena(ref)
        assert (r["status"], r["commentary"]) == ("none", []), (ref, r["status"])
    # where it does reach, it is that verse's block and no other's (John 3:16 lies in John 3:16-18)
    r = _catena("John 3:16")
    assert r["status"] == "ok" and [it["range"] for it in r["commentary"]] == ["John 3:16-18"]
    assert [it["range"] for it in _catena("Matthew 1:17")["commentary"]] == ["Matthew 1:17"] * 3
    # Henry's fallback to a chapter's first block stays as it is for Henry (a want: on Matthew 5:1 it serves the
    # words of the block on 5:3)
    assert commentary.for_ref("Matthew 5:1")["commentary"][0]["verse"] == 3


def test_a_missing_build_reads_not_built(shelf, tmp_path, monkeypatch):
    shutil.rmtree(shelf)
    r = _catena("Matthew 1:1")
    assert (r["status"], r["commentary"]) == ("not_built", [])
    # another hash's directory is not the pinned build
    other = shelf.parent / ("0" * 64)
    shutil.copytree(FIX / "shelf", other)
    assert _catena("Matthew 1:1")["status"] == "not_built"
    # nor is a data directory with no builds at all
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path / "nowhere"))
    assert _catena("John 3:16")["status"] == "not_built"
    assert _catena("garbage")["status"] == "not_found"


def test_editors_notes_never_in_a_fathers_words(shelf):
    notes = [(gid, n) for gid, g in GOLDEN.items() for n in g["editors_notes"]]
    assert len(notes) >= 5
    served = [it for ref in ("Matthew 1", "John 3") for it in _catena(ref)["commentary"]]
    pages_with_notes = {GOLDEN[gid]["leaf"] - 23 for gid, _ in notes if GOLDEN[gid]["item"] == "catenaaureacomme00thomuoft"}
    # the footnotes sit on pages whose excerpts are served (Matthew 1:1 pages 10, 13 and 15), and not one word run
    # of a note reaches an excerpt
    assert {10, 13, 15} <= pages_with_notes and {10, 13, 15} <= {it["page"] for it in served}
    for gid, n in notes:
        words = n["text"].split()
        runs = {" ".join(words[i:i + 5]) for i in range(max(1, len(words) - 4))}
        for it in served:
            text = " ".join(it["text"].split())
            assert not any(run in text for run in runs), (gid, it["author_as_printed"], it["page"])
            # nor its mark, standing after the word it is set against
            if n["after"]:
                assert f"{n['after']} {n['mark']} " not in text + " " and f"{n['after']}{n['mark']} " not in text + " "


def test_sources_on_request_names_catena_beside_henry(shelf):
    want = {"matthew-henry", CATENA}
    st, p = dispatch("GET", "/commentary", {"ref": "Matthew 1:1", "sources": "1"}, None, WIT)
    assert st == 200 and p["ref"] == "Matthew 1:1" and want <= set(p["covering"])
    rows = {s["source"]: s for s in p["sources"]}
    assert rows[CATENA]["status"] == "ok" and rows[CATENA]["covers"] and "Catena Aurea" in rows[CATENA]["name"]
    assert rows["adam-clarke"]["covers"] is False                       # a source with no store here says so
    st, p = dispatch("GET", "/commentary", {"ref": "Matthew 1:3", "sources": "1"}, None, SEC)
    assert st == 200 and p["covering"] == ["matthew-henry"]            # the Catena does not reach 1:3
    r = mcp.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
        "name": "commentary", "arguments": {"ref": "Matthew 1:1", "sources": True}}}, WIT)
    assert want <= set(json.loads(r["result"]["content"][0]["text"])["covering"])
    # the request without sources is Henry's, as before
    st, p = dispatch("GET", "/commentary", {"ref": "Matthew 1:1"}, None, WIT)
    assert st == 200 and p["source"] == "matthew-henry" and "covering" not in p
    tools = mcp.handle({"jsonrpc": "2.0", "id": 4, "method": "tools/list"}, WIT)["result"]["tools"]
    schema = next(t for t in tools if t["name"] == "commentary")["inputSchema"]
    assert schema["properties"]["sources"]["type"] == "boolean"
    # the site's verse study asks for the Catena beside Henry
    html = (ROOT / "site" / "bible.html").read_text(encoding="utf-8")
    assert "/commentary?source=catena-aurea&ref=" in html and "the Fathers (Catena Aurea)" in html


def _digest(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def test_henry_responses_byte_identical(tmp_path, monkeypatch):
    """A guard that holds at the base and after: Henry's store, and beside it the Catena build where one is pinned
    (at the base none is), and every response of his as the base gave it."""
    _henry_store(tmp_path / "commentary")
    (tmp_path / "data").mkdir()
    pin = builds.pinned_hash(CATENA)
    if pin:
        shutil.copytree(FIX / "shelf", tmp_path / "data" / "builds" / CATENA / pin)
    monkeypatch.setenv("CONCORDANCE_COMMENTARY_DIR", str(tmp_path / "commentary"))
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path / "data"))
    got = {}
    for name, conf in (("witness", WIT), ("secular", SEC)):
        for ref in BASE["refs"]:
            r = mcp.handle({"jsonrpc": "2.0", "id": 7, "method": "tools/call",
                            "params": {"name": "commentary", "arguments": {"ref": ref}}}, conf)
            got[f"{name} {ref}"] = {
                "for_ref": _digest(commentary.for_ref(ref)),
                "for_ref_henry": _digest(commentary.for_ref(ref, source="matthew-henry")),
                "api": _digest(list(dispatch("GET", "/commentary", {"ref": ref}, None, conf))),
                "api_henry": _digest(list(dispatch("GET", "/commentary", {"ref": ref, "source": "matthew-henry"},
                                                   None, conf))),
                "mcp": _digest(r)}
    assert len(got) == 34 and "witness John 3:16" in got
    assert got == BASE["responses"]


# ------------------------------------------------------------------------------------------------ step catena2

def _served_golden_equal(items, verse_of):
    """Each item that has a golden entry on its verse is that entry, word for word, under the writer printed."""
    n = 0
    for it in items:
        same = [g for g in GOLDEN.values() if verse_of(g["verse"]) and g["words"] == it["text"]]
        near = [g for g in GOLDEN.values() if verse_of(g["verse"]) and g["author_as_printed"] == it["author_as_printed"]
                and g["words"].split()[:6] == it["text"].split()[:6]]
        assert not near or (same and same[0]["author_as_printed"] == it["author_as_printed"]), it["author_as_printed"]
        n += len(same)
    return n


def test_the_gloss_is_a_later_writer_at_matthew_1_17(shelf):
    r = _catena("Matthew 1:17")
    assert r["status"] == "ok"
    gloss = [it for it in r["commentary"] if it["author_as_printed"] == "GLOSS"]
    assert gloss and all(g["writer"] == "a later writer" and g["author"].startswith("the Gloss") for g in gloss)
    assert all(it["range"] == "Matthew 1:17" for it in r["commentary"])


def test_matthew_5_3_serves_its_excerpts_with_remigius_a_later_writer(shelf):
    r = _catena("Matthew 5:3")
    assert r["status"] == "ok" and r["commentary"]
    assert {it["range"] for it in r["commentary"]} == {"Matthew 5:1-3"}
    remig = [it for it in r["commentary"] if it["author_as_printed"] in ("REMIG", "REMIGIUS")]
    assert remig and all((it["author"], it["writer"]) == ("Remigius of Auxerre", "a later writer") for it in remig)
    # every golden excerpt served there is its golden entry (the golden's Matthew 5 entries lie in other sections)
    _served_golden_equal(r["commentary"], lambda v: v in ("Matthew 5:1-3", "Matthew 5:3"))
    # the Vulgate's order (verse 5 before verse 4) is held: Matthew 5:4 and 5:5 read none
    assert _catena("Matthew 5:4")["status"] == _catena("Matthew 5:5")["status"] == "none"


def test_marks_chrys_is_served_with_the_editors_mark(shelf):
    r = _catena("Mark 10:1")
    chrys = [it for it in r["commentary"] if it["author_as_printed"] == "CHRYS"]
    assert r["status"] == "ok" and chrys
    for it in chrys:
        mark = it["editors_mark"]
        assert mark["quote"] == "Many of the passages ascribed to S. Chrysostom are not found in the works of that Father."
        assert "Victor of Antioch" in mark["and"] and "Preface" in mark["where"]
        assert mark["page_image"].endswith("catenaaureacomme02thomuoft/page/n10.jpg")
    # in Matthew, CHRYS. carries no such mark
    assert all("editors_mark" not in it for it in _catena("Matthew 1:1")["commentary"])
    # the mark is the edition's own words, as the author table holds them
    authors = json.loads((ROOT / "tools" / "catena_aurea" / "authors.json").read_text(encoding="utf-8"))
    table = next(a for a in authors["authors"] if a["key"] == "chrysostom")["editors_mark_in_parts"]["mk"]
    assert table["quote"] == chrys[0]["editors_mark"]["quote"] and table["ocr_corrections"] == []


def test_mark_9_1_and_the_seven_chapters_read_none(shelf):
    books = {b["name"]: b for b in json.loads((shelf / "_books.json").read_text(encoding="utf-8"))}
    for gospel, chapter in (("Matthew", 17), ("Mark", 4), ("Mark", 8), ("Mark", 9), ("Luke", 17), ("John", 6),
                            ("John", 11)):
        assert chapter not in books[gospel]["chapters_with_excerpts"], (gospel, chapter)
        r = _catena(f"{gospel} {chapter}:1")
        assert (r["status"], r["commentary"]) == ("none", []), (gospel, chapter)
    r = _catena("Mark 9:1")
    assert (r["status"], r["commentary"]) == ("none", []) and "Mark 9:1" in r["detail"]
