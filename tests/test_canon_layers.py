"""THE CANON LAYERS (run 2026-11-11-full-canons): the books beyond the 66, built on the box from eBible.org's World
English Bible (eng-web) and Douay-Rheims 1899 (engDRA) by tools/build_canon_layers.py, and read by
src/concordance/canon_layers.py, each in its own numbering with its standing from canon.py, never merged into the 66.

Nothing here fetches. The tool is tested on lines cut verbatim from the two pinned texts with eBible's own codes
(tests/fixtures/canon_layers/vpl_fixture.json), zipped here as eBible ships them; the reader is tested on the tool's
output for that fixture (built_fixture.json, which the tool must reproduce byte for byte), placed where the engine
reads a build, beside a stand-in 66 whose rows are marked as such. The guards near the end use only what the base
already had (read_passage, resolve_ref, find_ref, classify, respond, the console's reference test), so they hold at
the base and after: every reading of the 66 is the same with the layers placed as without them.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

FIX = ROOT / "tests" / "fixtures" / "canon_layers"
TOOL = ROOT / "tools" / "build_canon_layers.py"
TABLES = ROOT / "tools" / "canon_tables"
LISTING = ROOT / "tools" / "box_builds.txt"
PINS = ROOT / "src" / "concordance" / "build_pins.json"
PROBES = ROOT / "eval" / "live_probes.jsonl"
VPL = json.loads((FIX / "vpl_fixture.json").read_text(encoding="utf-8"))
BUILT = json.loads((FIX / "built_fixture.json").read_text(encoding="utf-8"))
EDITIONS = ("eng-web", "engDRA")
INPUTS = ("tools/canon_tables/book_codes.json", "tools/canon_tables/text_pins.json",
          "tools/canon_tables/verse_counts.json")

# checker-99's measurement, the run's ledger line 3: the verse lines of each added book in each pinned text
MEASURED = {
    "eng-web": {"TOB": 244, "JDT": 339, "ESG": 205, "WIS": 436, "SIR": 1383, "BAR": 213, "1MA": 924, "2MA": 555,
                "1ES": 448, "PRM": 15, "PSX": 7, "3MA": 228, "4MA": 484, "DNG": 530},
    "engDRA": {"TOB": 298, "JDT": 345, "WIS": 439, "SIR": 1591, "BAR": 213, "1MA": 929, "2MA": 558},
}
TEXT_PINS = {"eng-web": "ea6d1e59f9b9ae24ee38ff252763b1a72dab4fcb7416bec69814820d7eeba151",
             "engDRA": "96282bfa7c89a74680cea66fe873aafa5e7cd446407f0ff2531a723e19eee2c2"}


def _tool():
    spec = importlib.util.spec_from_file_location("build_canon_layers_under_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def vpl_bytes(ed: str, lines=None) -> bytes:
    return ("\n".join(VPL[ed]["lines"] if lines is None else lines) + "\n").encode("utf-8")


def zip_of(ed: str, raw: bytes) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(zipfile.ZipInfo(VPL[ed]["member"], date_time=(2026, 11, 11, 0, 0, 0)), raw)
    return buf.getvalue()


def real_tables() -> dict:
    return {k: json.loads((TABLES / f).read_text(encoding="utf-8"))
            for k, f in (("pins", "text_pins.json"), ("codes", "book_codes.json"), ("counts", "verse_counts.json"))}


def fixture_tables() -> dict:
    """The real book-code table, with the fixture's own pins and counts."""
    t = real_tables()
    for ed in EDITIONS:
        t["pins"]["editions"][ed]["sha256"] = VPL[ed]["sha256"]
    t["counts"] = {"editions": {ed: dict(VPL[ed]["counts"]) for ed in EDITIONS}}
    return t


def fixture_fetch(texts=None):
    texts = texts or {}
    urls = {real_tables()["pins"]["editions"][ed]["url"]: ed for ed in EDITIONS}

    def fetch(url):
        ed = urls[url]
        return zip_of(ed, texts.get(ed, vpl_bytes(ed)))
    return fetch


def built_bytes() -> dict:
    out = {}
    for name, held in BUILT["files"].items():
        if name.endswith(".jsonl"):
            out[name] = b"".join(json.dumps(r, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n"
                                 for r in held)
        else:
            out[name] = (json.dumps(held, ensure_ascii=False, indent=1, sort_keys=True) + "\n").encode("utf-8")
    return out


# ------------------------------------------------------------------------------------------------ the 66, stood in

THE_66 = [("Genesis", "GEN"), ("Exodus", "EXO"), ("Leviticus", "LEV"), ("Numbers", "NUM"), ("Deuteronomy", "DEU"),
          ("Joshua", "JOS"), ("Judges", "JDG"), ("Ruth", "RUT"), ("1 Samuel", "1SA"), ("2 Samuel", "2SA"),
          ("1 Kings", "1KI"), ("2 Kings", "2KI"), ("1 Chronicles", "1CH"), ("2 Chronicles", "2CH"), ("Ezra", "EZR"),
          ("Nehemiah", "NEH"), ("Esther", "EST"), ("Job", "JOB"), ("Psalms", "PSA"), ("Proverbs", "PRO"),
          ("Ecclesiastes", "ECC"), ("Song of Solomon", "SOL"), ("Isaiah", "ISA"), ("Jeremiah", "JER"),
          ("Lamentations", "LAM"), ("Ezekiel", "EZE"), ("Daniel", "DAN"), ("Hosea", "HOS"), ("Joel", "JOE"),
          ("Amos", "AMO"), ("Obadiah", "OBA"), ("Jonah", "JON"), ("Micah", "MIC"), ("Nahum", "NAH"),
          ("Habakkuk", "HAB"), ("Zephaniah", "ZEP"), ("Haggai", "HAG"), ("Zechariah", "ZEC"), ("Malachi", "MAL"),
          ("Matthew", "MAT"), ("Mark", "MAR"), ("Luke", "LUK"), ("John", "JOH"), ("Acts", "ACT"), ("Romans", "ROM"),
          ("1 Corinthians", "1CO"), ("2 Corinthians", "2CO"), ("Galatians", "GAL"), ("Ephesians", "EPH"),
          ("Philippians", "PHI"), ("Colossians", "COL"), ("1 Thessalonians", "1TH"), ("2 Thessalonians", "2TH"),
          ("1 Timothy", "1TI"), ("2 Timothy", "2TI"), ("Titus", "TIT"), ("Philemon", "PHM"), ("Hebrews", "HEB"),
          ("James", "JAM"), ("1 Peter", "1PE"), ("2 Peter", "2PE"), ("1 John", "1JO"), ("2 John", "2JO"),
          ("3 John", "3JO"), ("Jude", "JUD"), ("Revelation", "REV")]
ONE_CHAPTER = {"Obadiah", "Philemon", "2 John", "3 John", "Jude"}
EXTRA_66 = [("Daniel", 3, 24), ("Daniel", 3, 30), ("Daniel", 12, 13), ("Esther", 10, 1), ("Esther", 10, 3),
            ("Ecclesiastes", 3, 1), ("Psalms", 23, 1), ("Psalms", 150, 6), ("John", 3, 16)]


def the_66_rows() -> list:
    """The 66 as data/bible_en.jsonl names them (book and book_abbr), with stand-in text that says so."""
    rows = []
    for book, abbr in THE_66:
        cvs = [(1, 1)] + ([] if book in ONE_CHAPTER else [(2, 1)]) + [(c, v) for b, c, v in EXTRA_66 if b == book]
        for c, v in cvs:
            rows.append({"book": book, "book_abbr": abbr, "chapter": c, "verse": v,
                         "text": f"[a stand-in row of the 66: {book} {c}:{v}]", "translation": "World English Bible"})
    return rows


def _clear_memos():
    from concordance import ask
    for fn in (ask.find_ref, ask.classify):
        if hasattr(fn, "cache_clear"):
            fn.cache_clear()


def layer_dir(data: Path) -> Path:
    pin = json.loads(PINS.read_text(encoding="utf-8")).get("canon-layers") or "f" * 64
    return data / "builds" / "canon-layers" / pin


@pytest.fixture
def placed(tmp_path, monkeypatch):
    """A data directory holding the stand-in 66 and the built fixture where the engine reads the pinned build."""
    from concordance.verifiers import scripture as S
    data = tmp_path / "data"
    data.mkdir()
    bible = data / "bible_en.jsonl"
    bible.write_bytes(b"".join(json.dumps(r).encode() + b"\n" for r in the_66_rows()))
    where = layer_dir(data)
    where.mkdir(parents=True)
    for name, body in built_bytes().items():
        (where / name).write_bytes(body)
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(data))
    monkeypatch.setenv("CONCORDANCE_BIBLE_EN", str(bible))
    S._reset()
    _clear_memos()
    yield data
    S._reset()
    _clear_memos()


def added_texts() -> list:
    """Every text of the built fixture's added books: none may reach a reading of the 66."""
    return [r["text"] for name in ("eng-web.jsonl", "engDRA.jsonl") for r in BUILT["files"][name] if r["text"]]


def no_added_text(payload) -> bool:
    blob = json.dumps(payload, ensure_ascii=False)
    return not any(t in blob for t in added_texts())


# ------------------------------------------------------------------------------------------------ the tool

def test_the_tool_builds_the_fixture_exactly_as_committed_and_the_same_twice():
    tool = _tool()
    first = tool.build(fixture_tables(), fetch=fixture_fetch())
    again = tool.build(fixture_tables(), fetch=fixture_fetch())
    assert first == again == built_bytes()
    assert sorted(first) == ["eng-web.jsonl", "engDRA.jsonl", "layers.json"]
    assert all(b"\r" not in body for body in first.values())


def test_the_fixture_is_cut_from_the_pinned_texts_with_ebibles_own_codes():
    for ed in EDITIONS:
        assert VPL[ed]["cut_from_sha256"] == TEXT_PINS[ed]
        assert hashlib.sha256(vpl_bytes(ed)).hexdigest() == VPL[ed]["sha256"]
    codes = {ln[:3] for ed in EDITIONS for ln in VPL[ed]["lines"]}
    assert {"PSX", "PRM", "ESG", "DNG", "4ES", "JOH"} <= codes            # eBible's codes, not USFM's
    assert not codes & {"PS2", "MAN", "LJE", "DAG", "JHN"}
    assert "SIR 1:5 " in VPL["eng-web"]["lines"]                          # the empty line, as the file holds it


def test_the_tool_refuses_an_unmapped_code():
    tool = _tool()
    raw = vpl_bytes("eng-web", VPL["eng-web"]["lines"] + ["XYZ 1:1 a line under a code no table names"])
    t = fixture_tables()
    t["pins"]["editions"]["eng-web"]["sha256"] = hashlib.sha256(raw).hexdigest()     # the pin passes; the code fails
    with pytest.raises(tool.Refused, match="neither mapped nor skipped: \\['XYZ'\\]"):
        tool.build(t, fetch=fixture_fetch({"eng-web": raw}))


def test_the_tool_refuses_a_count_mismatch():
    tool = _tool()
    t = fixture_tables()
    t["counts"]["editions"]["engDRA"]["TOB"] += 1
    with pytest.raises(tool.Refused, match="verse lines \\(found, committed\\) differ: \\{'TOB': \\(2, 3\\)\\}"):
        tool.build(t, fetch=fixture_fetch())


def test_the_tool_refuses_a_changed_text_and_writes_nothing(tmp_path, monkeypatch):
    tool = _tool()
    changed = vpl_bytes("eng-web").replace(b"what you yourself hate", b"what you yourself love")
    assert changed != vpl_bytes("eng-web")
    with pytest.raises(tool.Refused, match="hashes to .*, not to its pin"):
        tool.build(fixture_tables(), fetch=fixture_fetch({"eng-web": changed}))
    inputs, out = _stage(tmp_path, fixture_tables())
    monkeypatch.setattr(tool, "fetch_https", fixture_fetch({"eng-web": changed}))
    assert tool.main([str(inputs), str(out)]) == 1
    assert list(out.iterdir()) == []


def test_an_unreachable_source_exits_1_and_writes_nothing(tmp_path, monkeypatch):
    import urllib.error
    import urllib.request
    tool = _tool()

    def unreachable(*a, **k):
        raise urllib.error.URLError("no route to the source")
    monkeypatch.setattr(urllib.request, "urlopen", unreachable)
    with pytest.raises(tool.Refused, match="could not be fetched"):
        tool.fetch_https("https://ebible.org/Scriptures/eng-web_vpl.zip")
    inputs, out = _stage(tmp_path, fixture_tables())
    assert tool.main([str(inputs), str(out)]) == 1
    assert list(out.iterdir()) == []


def _stage(tmp_path: Path, tables: dict, crlf: bool = False, tag: str = "a"):
    inputs, out = tmp_path / f"inputs-{tag}", tmp_path / f"out-{tag}"
    for key, rel in (("codes", INPUTS[0]), ("pins", INPUTS[1]), ("counts", INPUTS[2])):
        p = inputs / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(tables[key], indent=1) + "\n"
        p.write_bytes((text.replace("\n", "\r\n") if crlf else text).encode("utf-8"))
    out.mkdir()
    return inputs, out


def test_the_tool_parses_its_inputs_so_their_line_endings_never_reach_the_output(tmp_path, monkeypatch):
    """A Windows checkout sends its inputs with CRLF line endings: the output must not move."""
    tool = _tool()
    monkeypatch.setattr(tool, "fetch_https", fixture_fetch())
    got = {}
    for crlf, tag in ((False, "lf"), (True, "crlf")):
        inputs, out = _stage(tmp_path, fixture_tables(), crlf=crlf, tag=tag)
        assert tool.main([str(inputs), str(out)]) == 0
        got[tag] = {p.name: p.read_bytes() for p in out.iterdir()}
    assert got["lf"] == got["crlf"] == built_bytes()


def test_the_tool_takes_exactly_its_three_inputs(tmp_path):
    tool = _tool()
    inputs, _out = _stage(tmp_path, fixture_tables())
    (inputs / "tools" / "canon_tables" / "extra.json").write_text("{}", encoding="utf-8")
    with pytest.raises(tool.Refused, match="not the three tables"):
        tool.read_tables(str(inputs))


def test_a_lettered_verse_keeps_its_label():
    """Neither pinned text has a lettered verse id (measured: 0 in each), so the rule is pinned on a stand-in id."""
    tool = _tool()
    got = tool.parse(b"TOB 4:7 a stand-in line\nTOB 4:7a a stand-in lettered line\n", "stand-in")
    assert got == [("TOB", 4, "7", "a stand-in line"), ("TOB", 4, "7a", "a stand-in lettered line")]
    with pytest.raises(tool.Refused, match="twice"):
        tool.parse(b"TOB 4:7a x\nTOB 4:7a y\n", "stand-in")


def test_the_committed_tables_hold_the_measured_counts_and_the_pinned_texts():
    t = real_tables()
    assert t["counts"]["editions"] == MEASURED
    assert {ed: t["pins"]["editions"][ed]["sha256"] for ed in EDITIONS} == TEXT_PINS
    for ed in EDITIONS:
        assert set(t["codes"]["editions"][ed]["books"]) == set(MEASURED[ed])
    assert t["codes"]["editions"]["eng-web"]["skip"] == {
        "4ES": "2 Esdras: canon.py lists it on no Catholic or Eastern Orthodox layer, so it is left out and named"}
    assert len(t["codes"]["the_66"]["codes"]) == 66
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import migrate_bible
    finally:
        sys.path.remove(str(ROOT / "tools"))
    for ed in EDITIONS:                                   # the strict PD-only gate, keyed by source, holds each one
        pin = t["pins"]["editions"][ed]
        assert migrate_bible.PD_VERIFIED_SOURCES[pin["source"]][1] == pin["license"], ed
    assert sorted(migrate_bible.PD_VERIFIED_SOURCES) == ["eBible.org eng-web", "eBible.org engDRA"]


def test_the_listing_entry_builds_from_the_tables_and_its_hash_is_pinned():
    spec = importlib.util.spec_from_file_location("box_build_for_canons", ROOT / "tools" / "box_build.py")
    bb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bb)
    e = bb.parse_listing(LISTING.read_text(encoding="utf-8"))["canon-layers"]
    assert (e.tool, e.inputs, e.args) == ("tools/build_canon_layers.py", INPUTS, ())
    assert 1 <= e.cap_mb <= 1024
    assert json.loads(PINS.read_text(encoding="utf-8"))["canon-layers"] == e.hash


def test_the_tables_name_canon_pys_books_and_kept_as_says_where_each_addition_stands():
    from concordance import canon, canon_layers
    names = {b for t in ("catholic", "eastern_orthodox") for b in canon.TRADITION_ADDITIONS[t]["books"]}
    codes = real_tables()["codes"]["editions"]
    for ed in EDITIONS:
        for part in ("within", "in_the_66"):
            assert set(codes[ed][part]) <= names | set(canon.GREEK_FORMS), (ed, part)
        for name in codes[ed]["books"].values():
            assert canon_layers.NAMES.get(canon_layers._key(name)), name
    web = BUILT["files"]["layers.json"]["editions"]["eng-web"]["within"]
    assert canon.KEPT_AS["susanna"] == "Daniel (Greek) 13" and web["susanna"]["chapter"] == 13
    assert canon.KEPT_AS["bel and the dragon"] == "Daniel (Greek) 14" and web["bel and the dragon"]["chapter"] == 14
    assert canon.KEPT_AS["letter of jeremiah"] == "Baruch 6" and web["letter of jeremiah"]["book"] == "Baruch"
    assert canon.KEPT_AS["prayer of azariah"].startswith("Daniel (Greek) 3:24-90")
    assert (web["prayer of azariah"]["first"], web["prayer of azariah"]["last"]) == (24, 90)
    assert canon.KEPT_AS["additions to esther"].startswith("read within Esther (Greek)")
    assert canon.canon_status("Susanna")["kept_as"] == "Daniel (Greek) 13"
    dg = canon.canon_status("Daniel (Greek)")
    assert dg["greek_form_of"] == "Daniel" and "catholic" in dg["held_by"]


def test_no_name_of_the_66_is_a_name_of_an_added_book():
    from concordance import canon_layers
    from concordance.verifiers import scripture as S
    b = S.Bible(the_66_rows())
    for key in canon_layers.NAMES:
        assert not b.book_candidates(key), key
        assert key not in S._COMMON_ABBREV, key
    assert canon_layers.FULL_NAMES <= set(canon_layers.NAMES)
    for word in ("sir", "bar", "tob", "bel", "wisdom"):                  # common words, never full names
        assert word in canon_layers.NAMES and word not in canon_layers.FULL_NAMES


# ------------------------------------------------------------------------------------------------ the reader

def test_web_tobit_4_15_and_douay_rheims_4_16_hold_the_saying_and_dra_4_15_is_about_wages(placed):
    from concordance.verifiers import scripture as S
    web = S.read_passage("Tobit 4:15")
    assert (web["status"], web["ref"], web["edition"]) == ("ok", "Tobit 4:15", "eng-web")
    assert "what you yourself hate, do to no man" in web["verses"][0]["text"]
    dra = S.read_passage("Tobit 4:16", edition="engDRA")
    assert (dra["status"], dra["ref"], dra["edition"]) == ("ok", "Tobit 4:16", "engDRA")
    assert "See thou never do to another what thou wouldst hate" in dra["verses"][0]["text"]
    wages = S.resolve_ref("Tobit 4:15", edition="Douay-Rheims")
    assert wages["status"] == "ok" and "pay him his hire" in wages["text"]
    assert "Vulgate" in dra["numbering"] and "World English Bible's own numbering" in web["numbering"]
    for r in (web, dra, wages):
        assert r["layer"].startswith("a book beyond the 66") and r["license"].startswith("Public domain")
        assert r["standing"]["in_undisputed_66"] is False and "catholic" in r["standing"]["held_by"]


def test_sirach_3_30_and_douay_rheims_3_33_are_the_almsgiving_verse(placed):
    from concordance.verifiers import scripture as S
    assert "almsgiving will make atonement for sins" in S.resolve_ref("Sirach 3:30")["text"]
    assert "alms resisteth sins" in S.resolve_ref("Sirach 3:33", edition="engDRA")["text"]
    assert "congregation of the proud" in S.resolve_ref("Sir 3:30", edition="engDRA")["text"]


def test_psalm_151_and_1_maccabees_resolve_with_their_standing(placed):
    from concordance.verifiers import scripture as S
    ps = S.read_passage("Psalm 151:1")
    assert (ps["status"], ps["ref"], ps["verses"][0]["ref"]) == ("ok", "Psalm 151:1", "Psalm 151:1")
    assert "This Psalm is a genuine one of David" in ps["verses"][0]["text"]
    assert ps["standing"]["held_by"] == ["eastern_orthodox"]
    assert S.read_passage("Psalm 151")["ref"] == "Psalm 151"                # the name alone: the whole psalm
    mac = S.resolve_ref("1 Maccabees 2:1")
    assert (mac["status"], mac["ref"]) == ("ok", "1 Maccabees 2:1") and "Mattathias the son of John" in mac["text"]
    assert mac["standing"]["held_by"] == ["catholic", "eastern_orthodox", "ethiopian_orthodox"]


def test_the_additions_read_in_their_own_numbers_on_their_spans_with_both_numberings(placed):
    from concordance.verifiers import scripture as S
    for asked, ref, own, words in (("Susanna 1", "Daniel (Greek) 13:1", "Susanna 1", "A man lived in Babylon"),
                                   ("Bel and the Dragon 1", "Daniel (Greek) 14:1", "Bel and the Dragon 1",
                                    "King Astyages was gathered to his fathers"),
                                   ("Prayer of Azariah 1", "Daniel (Greek) 3:24", "Prayer of Azariah 1",
                                    "They walked in the midst of the fire"),
                                   ("Letter of Jeremiah 1", "Baruch 6:1", "Letter of Jeremiah 1",
                                    "A copy of a letter that Jeremy sent")):
        for got in (S.read_passage(asked), S.resolve_ref(asked)):
            assert (got["status"], got["ref"], got["addition_ref"]) == ("ok", ref, own), asked
            assert words in json.dumps(got, ensure_ascii=False), asked
            assert got["within"][0]["addition"] == own.rsplit(" ", 1)[0]
    direct = S.resolve_ref("Daniel (Greek) 13:1")
    assert (direct["ref"], direct["addition_ref"]) == ("Daniel (Greek) 13:1", "Susanna 1")
    assert direct["standing"]["canonical_name"] == "susanna"
    whole = S.read_passage("Susanna")
    assert whole["addition_ref"] == "Susanna" and [v["addition_ref"] for v in whole["verses"]] == \
        ["Susanna 1", "Susanna 2"]
    azariah = S.read_passage("Prayer of Azariah 8")
    assert (azariah["ref"], azariah["addition_ref"]) == ("Daniel (Greek) 3:31", "Prayer of Azariah 8")
    assert "1-68" in azariah["within"][0]["note"]                       # the KJV and NRSV count it otherwise
    esther = S.read_passage("Additions to Esther 2:1")
    assert (esther["status"], esther["ref"]) == ("ok", "Esther (Greek) 2:1")
    assert "read within Esther (Greek)" in esther["within"][0]["note"]


def test_an_empty_verse_reads_as_missing_never_as_found(placed):
    from concordance.verifiers import scripture as S
    one = S.resolve_ref("Sirach 1:5")
    assert (one["status"], one["text"], one["missing"]) == ("not_found", "", ["Sirach 1:5"])
    assert "no text" in one["detail"]
    span = S.read_passage("Sirach 1:4-6")
    assert span["status"] == "ok" and [v["ref"] for v in span["verses"]] == ["Sirach 1:4", "Sirach 1:6"]
    assert span["missing"] == ["Sirach 1:5"]


def test_douay_rheims_susanna_is_a_miss_that_says_where_that_edition_prints_it(placed):
    from concordance.verifiers import scripture as S
    for asked, at in (("Susanna 1", "Daniel 13"), ("Bel and the Dragon", "Daniel 14"),
                      ("Prayer of Azariah 1", "Daniel 3:24-90"), ("Additions to Esther 1:1", "Esther 10:4-16:24")):
        got = S.read_passage(asked, edition="engDRA")
        assert (got["status"], got["printed_at"], got["edition"]) == ("not_found", at, "engDRA"), asked
        assert at in got["detail"] and got["verses"] == []
    assert S.read_passage("1 Esdras 1:1", edition="engDRA")["status"] == "not_found"


def test_a_build_that_is_not_there_reads_as_not_built_and_is_found_once_it_is(placed):
    from concordance.verifiers import scripture as S
    from concordance import canon_layers
    moved = placed / "elsewhere"
    shutil.move(str(layer_dir(placed)), str(moved))
    S._reset()
    got = S.read_passage("Tobit 4:15")
    assert (got["status"], got["built"]) == ("not_found", False) and "not built" in got["detail"]
    assert canon_layers.loaded() == []
    shutil.move(str(moved), str(layer_dir(placed)))
    assert S.read_passage("Tobit 4:15")["status"] == "ok"                 # a miss is never cached


def test_a_reading_of_the_66_opens_no_layer(placed):
    from concordance import canon_layers
    from concordance.verifiers import scripture as S
    from concordance.web import api  # noqa: F401  (the app's import opens nothing either)
    for ref in ("John 3:16", "Genesis 1:1", "Daniel 13:1", "Jud 1:1", "Ps 23:1"):
        S.read_passage(ref)
        S.resolve_ref(ref)
    assert canon_layers.loaded() == []
    S.read_passage("Tobit 4:15")
    assert canon_layers.loaded() == ["eng-web"]
    assert S.read_passage("John 3:16", edition="engDRA")["edition_note"].startswith("the canon layers hold only")


def test_the_passage_route_and_the_mcp_tool_serve_the_layer_with_its_edition(placed):
    from concordance.engine import EngineConfig
    from concordance.mcp import server as mcp
    from concordance.web import api
    cfg = EngineConfig("witness")
    st, body = api.dispatch("GET", "/passage", {"ref": "Tobit 4:16", "edition": "engDRA"}, None, cfg)[:2]
    assert st == 200 and (body["status"], body["edition"]) == ("ok", "engDRA")
    assert body["translation"] == "Douay-Rheims 1899 American Edition"
    res = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                      "params": {"name": "read_passage", "arguments": {"ref": "Psalm 151:1"}}}, cfg, {})
    blob = json.dumps(res, ensure_ascii=False)
    assert "This Psalm is a genuine one of David" in blob and "eng-web" in blob
    tools = mcp.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, cfg, {})["result"]["tools"]
    schema = next(t for t in tools if t["name"] == "read_passage")["inputSchema"]
    assert schema["properties"]["edition"]["enum"] == ["eng-web", "engDRA"]


@pytest.mark.empty_corpus_ok("the ask path's reading of a reference is asserted, not the keeping: in a clean clone "
                             "the keeping is empty and the verse's cloud of cards is simply absent")
def test_the_ask_path_reads_an_added_book_by_its_full_name_with_its_labels(placed):
    from concordance import ask
    from concordance.engine import EngineConfig
    r = ask.respond("what does Tobit 4:15 say", EngineConfig("witness"))
    assert r["kind"] == "scripture" and r["scripture"][0]["ref"] == "Tobit 4:15"
    assert "what you yourself hate" in r["scripture"][0]["text"]
    assert (r["canon_layer"]["edition"], r["canon_layer"]["standing"]["in_undisputed_66"]) == ("eng-web", False)


def test_the_console_reads_an_added_book_by_its_full_name_with_its_labels(placed):
    from concordance import console
    from concordance.engine import EngineConfig
    assert console._is_bare_scripture_ref("Tobit 4:15") is True
    got = console._read("read Tobit 4:15", EngineConfig("witness"), True)
    assert got["kind"] == "scripture" and got["canon_layer"]["edition"] == "eng-web"
    assert "World English Bible" in got["spoken"]


def test_the_live_probes_read_tobit_4_15_and_psalm_151_1():
    probes = [json.loads(ln) for ln in PROBES.read_text(encoding="utf-8").splitlines()
              if ln.strip() and not ln.startswith("#")]
    by_ref = {p.get("query", {}).get("ref"): p for p in probes if p["path"] == "/passage"}
    for ref in ("Tobit 4:15", "Psalm 151:1"):
        p = by_ref[ref]
        expect = {(e["at"], next(k for k in e if k != "at")) for e in p["expect"]}
        assert ("status", "eq") in expect and ("edition", "eq") in expect and ("standing.held_by[*]", "has") in expect


# ------------------------------------------------------------------------------------------------ the guards
# Each holds at the base and after: the base ignores the placed layers, and the reader must never let them reach
# a reading of the 66, an ambiguity among the 66, or prose.

AS_AT_THE_BASE = {
    "Daniel 13:1": ("not_found", "Daniel 13:1", "Daniel 13:1-1 not in the WEB", "Daniel 13:1 not in the WEB"),
    "Dan 14:1": ("not_found", "Dan 14:1", "Daniel 14:1-1 not in the WEB", "Daniel 14:1 not in the WEB"),
    "Daniel 3:31": ("not_found", "Daniel 3:31", "Daniel 3:31-31 not in the WEB", "Daniel 3:31 not in the WEB"),
    "Esther 10:4": ("not_found", "Esther 10:4", "Esther 10:4-4 not in the WEB", "Esther 10:4 not in the WEB"),
    "Est 10:5": ("not_found", "Est 10:5", "Esther 10:5-5 not in the WEB", "Esther 10:5 not in the WEB"),
    "Ecc 3:1": ("ok", "Ecclesiastes 3:1", None, None),
    "Eccles 3:1": ("ok", "Ecclesiastes 3:1", None, None),
    "Est 1:1": ("ok", "Esther 1:1", None, None),
    "Esth 1:1": ("ok", "Esther 1:1", None, None),
    "Dan 3:24": ("ok", "Daniel 3:24", None, None),
    "Ps 23:1": ("ok", "Psalms 23:1", None, None),
}


def test_the_named_references_of_the_66_read_exactly_as_at_the_base(placed):
    from concordance.verifiers import scripture as S
    for ref, (status, out_ref, p_detail, r_detail) in AS_AT_THE_BASE.items():
        p, r = S.read_passage(ref), S.resolve_ref(ref)
        assert (p["status"], p["ref"], r["status"], r["ref"]) == (status, out_ref, status, out_ref), ref
        if status == "ok":
            assert p["verses"][0]["text"].startswith("[a stand-in row of the 66") and p["translation"] == \
                "World English Bible", ref
            assert r["text"].startswith("[a stand-in row of the 66"), ref
        else:
            assert (p["detail"], r["detail"], p["verses"], r["text"]) == (p_detail, r_detail, [], ""), ref
        assert no_added_text(p) and no_added_text(r), ref
        assert "edition" not in p and "standing" not in p and "edition" not in r, ref
    for got in (S.read_passage("Jud 1:1"), S.resolve_ref("Jud 1:1")):
        assert got["status"] == "ambiguous" and got["candidates"] == ["Jude 1:1", "Judges 1:1"]
        assert no_added_text(got)


def _forms_of_the_66() -> list:
    from concordance.verifiers import scripture as S
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())  # noqa: E731
    forms = set(S._COMMON_ABBREV)
    for book, abbr in THE_66:
        for name in (book, abbr):
            forms.add(name)
            key = norm(name)
            forms.update(key[:n] for n in range(3, len(key) + 1))
    return sorted(forms)


def test_every_form_of_a_66_name_reads_the_same_with_the_layers_placed_as_without(placed):
    from concordance.verifiers import scripture as S
    forms = _forms_of_the_66()
    assert len(forms) > 400
    refs = [f"{f} {cv}" for f in forms for cv in ("1:1", "2:1", "13:1")]

    def read_all():
        S._reset()
        return [(S.read_passage(r), S.resolve_ref(r)) for r in refs]
    with_layers = read_all()
    moved = placed / "elsewhere"
    shutil.move(str(layer_dir(placed)), str(moved))
    without = read_all()
    shutil.move(str(moved), str(layer_dir(placed)))
    assert with_layers == without
    assert all(no_added_text(pair) for pair in with_layers)


PROSE = {
    # sentence: (find_ref, classify, the answer's kind), each as the base gives them with the fixture placed
    "yes sir 2:15 works for me": (" sir 2:15", "scripture", "scripture"),
    "meet me at the bar 3:15": (" bar 3:15", "scripture", "scripture"),
    "yes sir 2 more questions": (None, "search", "found"),
    "wisdom 2": (None, "search", "found"),
    "bar 3": (None, "search", "found"),
}


@pytest.mark.empty_corpus_ok("the prose guard reads references, not cards: in a clean clone the keeping is empty "
                             "and the answer's reading of Scripture is the whole of what is asserted")
def test_prose_reads_as_prose_through_the_ask_path_and_never_as_sirach_or_baruch(placed):
    from concordance import ask
    from concordance.engine import EngineConfig
    wit = EngineConfig("witness")
    for text, (ref, routed, answered) in PROSE.items():
        assert (ask.find_ref(text), ask.classify(text)) == (ref, routed), text
        r = ask.respond(text, wit)
        assert r["kind"] == answered and no_added_text(r), text
        assert "canon_layer" not in r, text
        if routed == "scripture":
            assert r["scripture"] == [], text                            # as at the base: no verse at all


def test_the_console_reads_prose_as_prose(placed):
    from concordance import console
    for text in ("sir 2:15", "bar 3:15", "wisdom 2", "bar 3", "tob 1:1", "bel 1"):
        assert console._is_bare_scripture_ref(text) is False, text
