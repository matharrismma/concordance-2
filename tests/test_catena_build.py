"""Steps catena and catena2 (run 2026-11-11-fathers-shelf): tools/build_catena.py, the Catena Aurea build the box runs.

Hermetic: the build reads committed fixture pages, never the network. tests/fixtures/catena_aurea/ holds cuts of the
copies' ABBYY layout files (every other leaf an empty page, so the leaf numbers stay; only the attributes the build
reads are kept): Matthew's two copies, archive.org catenaaureacomme00thomuoft leaves 32-40 and catenaaureacomme01thom
leaves 33-41 (printed pages 9-17: every excerpt on Matthew 1:1 and the section 1:2 after it), and leaves 47-56 and
48-57 (pages 24-33: Matthew 1:8-11, 1:12-15 and the opening of 1:16); and one leaf of each copy where the golden's two
mid-sentence italic I cases stand (Matthew-t01-p866: catenaaureacomme01thomuoft and catenaurecommpt301thomuoft leaf
137; John-s09-p418: catenaaureacomm204arisuoft leaf 55 and catenaaureacomme04thom leaf 428). A test census names
Matthew's two copies for one part, pages 9-17, and pins each cut's sha256 as the real census pins the archive.org
file's. The author table, the golden, the verse table and the misreading list are the committed inputs themselves.
"""
from __future__ import annotations

import copy
import gzip
import hashlib
import importlib.util
import io
import json
import shutil
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "build_catena.py"
CATENA = ROOT / "tools" / "catena_aurea"
FIX = ROOT / "tests" / "fixtures" / "catena_aurea"
KELLY, PRINCETON = "catenaaureacomme00thomuoft", "catenaaureacomme01thom"
PAGES = [9, 17]
# the Matthew 1:1 excerpts both copies read alike on these pages, each equal to its golden entry
SERVED = {"Matthew-1-1-08": "CHRYS", "Matthew-1-1-09": "REMIGIUS", "Matthew-1-1-15": "PSEUDO-CHRYS",
          "Matthew-1-1-22": "AUG", "Matthew-1-1-27": "CYRIL"}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def bc(monkeypatch):
    mod = _load("build_catena_under_test", TOOL)
    calls = []

    def no_network(*a, **k):
        calls.append(a)
        raise AssertionError("the build reached for the network")
    monkeypatch.setattr(urllib.request, "urlopen", no_network)
    monkeypatch.setattr(mod.time, "sleep", lambda s: None)
    mod.network_calls = calls
    return mod


def _golden():
    return json.loads((CATENA / "golden.json").read_text(encoding="utf-8"))


def _gz(ident):
    return FIX / f"{ident}_abbyy.gz"


def _stage(tmp_path, golden=None, cached=None, monkeypatch=None):
    """inputs/ (the listed inputs at their repository paths, the census cut to the fixture part), cache/, out/, and
    the build's working directory as its cwd."""
    inp = tmp_path / "inputs" / "tools" / "catena_aurea"
    inp.mkdir(parents=True)
    for n in ("authors.json", "gospel_verses.json", "misreadings.json"):
        shutil.copyfile(CATENA / n, inp / n)
    (inp / "golden.json").write_text(json.dumps(golden or _golden()), encoding="utf-8")
    census = json.loads((CATENA / "census.json").read_text(encoding="utf-8"))
    part = dict(census["parts"]["mt1"], printed_pages=PAGES)
    assert (part["copy_a"], part["copy_b"]) == (KELLY, PRINCETON)
    census["parts"] = {"mt1": part}
    cache = tmp_path / "cache"
    for ident in (KELLY, PRINCETON):
        census["items"][ident]["layout_files"]["abbyy_gz"]["sha256_fetched_2026_11_11"] = \
            hashlib.sha256(_gz(ident).read_bytes()).hexdigest()
        d = cache / ident / "abbyy"
        d.mkdir(parents=True)
        (d / "abbyy.gz").write_bytes((cached or {}).get(ident, _gz(ident).read_bytes()))
    (inp / "census.json").write_text(json.dumps(census), encoding="utf-8")
    work = tmp_path / "work"
    work.mkdir()
    if monkeypatch is not None:
        monkeypatch.chdir(work)
    return tmp_path / "inputs", tmp_path / "out", cache


def _files(out):
    return {p.relative_to(out).as_posix(): p.read_bytes() for p in sorted(out.rglob("*")) if p.is_file()}


def _changed(ident):
    """The fixture file with one character of its text changed: the same shape, another sha256."""
    xml = gzip.decompress(_gz(ident).read_bytes())
    at = xml.index(b">e</charParams>")
    return gzip.compress(xml[:at] + b">c</charParams>" + xml[at + len(b">e</charParams>"):], mtime=0)


# ------------------------------------------------------------------------------------------------ the build

def test_build_reads_fixture_pages_into_the_golden_excerpts(bc, tmp_path, monkeypatch, capsys):
    inputs, out, cache = _stage(tmp_path, monkeypatch=monkeypatch)
    assert bc.main([str(inputs), str(out), "fetch", str(cache)]) == 0, capsys.readouterr().err
    assert bc.network_calls == []
    report = json.loads((out / "_build.json").read_text(encoding="utf-8"))
    assert report["golden_mismatch"] == [] and set(SERVED) <= set(report["golden_checked"])
    golden = {e["id"]: e for e in _golden()["excerpts"]}
    chapter = json.loads((out / "MAT" / "1.json").read_text(encoding="utf-8"))
    served = [(b, x) for b in chapter["blocks"] for x in b["excerpts"]]
    # every excerpt served on these pages is on Matthew 1:1, and the golden holds every Matthew 1:1 excerpt: each one
    # served is its golden entry, word for word and writer for writer
    for b, x in served:
        assert (b["range"], b["covers_in_this_chapter"]) == ("Matthew 1:1", [1, 1])
        same = [g for g in golden.values() if g["verse"] == "Matthew 1:1" and g["words"] == x["text"]]
        assert len(same) == 1 and same[0]["author_as_printed"] == x["author_as_printed"], x["author_as_printed"]
    printed = sorted(x["author_as_printed"] for _, x in served)
    assert printed == sorted(SERVED.values())
    by_printed = {x["author_as_printed"]: x for _, x in served}
    for gid, head in SERVED.items():
        assert by_printed[head]["text"] == golden[gid]["words"]
    # Pseudo-Chrysostom is kept apart from Chrysostom, and each writer is the author table's for the form printed
    assert by_printed["PSEUDO-CHRYS"]["author_key"] == "pseudo_chrysostom"
    assert by_printed["CHRYS"]["author_key"] == "chrysostom"
    authors = json.loads((out / "_authors.json").read_text(encoding="utf-8"))
    assert (authors["pseudo_chrysostom"]["kind"], authors["chrysostom"]["kind"]) == ("pseudo", "father")
    assert authors["remigius"]["kind"] == "later_writer"
    # the part's counts are reported, and a second run on the same inputs writes the same bytes
    part = report["parts"]["mt1"]
    assert part["served"] == len(SERVED) and part["served"] + part["held"] == part["heads_copy_a"]
    first = _files(out)
    assert all(b"\r" not in data for data in first.values())
    inputs2, out2, cache2 = _stage(tmp_path / "again", monkeypatch=monkeypatch)
    assert bc.main([str(inputs2), str(out2), "fetch", str(cache2)]) == 0
    assert _files(out2) == first


def test_build_refuses_a_changed_source(bc, tmp_path, monkeypatch, capsys):
    # a cached file that is not the pinned one: refused at once, nothing written, the network never asked
    inputs, out, cache = _stage(tmp_path, cached={KELLY: _changed(KELLY)}, monkeypatch=monkeypatch)
    assert bc.main([str(inputs), str(out), "fetch", str(cache)]) == 1
    err = capsys.readouterr().err
    assert err.startswith(f"REFUSED: changed source: {KELLY}_abbyy.gz has sha256 "), err
    assert not out.exists() or _files(out) == {}
    assert bc.network_calls == []
    # fetched from archive.org (here a stand-in answering with the changed bytes): refused the same way
    for ident, body, rc in ((PRINCETON, _changed(PRINCETON), 1), (PRINCETON, _gz(PRINCETON).read_bytes(), 0)):
        sub = tmp_path / f"net{rc}"
        inputs, out, cache = _stage(sub, monkeypatch=monkeypatch)
        shutil.rmtree(cache / ident)
        asked = []

        def answer(req, timeout=None, body=body):
            asked.append(req.full_url)
            return io.BytesIO(body)
        monkeypatch.setattr(urllib.request, "urlopen", answer)
        assert bc.main([str(inputs), str(out), "fetch", str(cache)]) == rc
        assert asked == [f"https://archive.org/download/{ident}/{ident}_abbyy.gz"]
        err = capsys.readouterr().err
        if rc:
            assert err.startswith(f"REFUSED: changed source: {ident}_abbyy.gz"), err
            assert not out.exists() or _files(out) == {}
        else:
            assert (out / "MAT" / "1.json").is_file()


def test_build_refuses_a_golden_mismatch(bc, tmp_path, monkeypatch, capsys):
    # the words: the golden reads one word more in Chrysostom's excerpt than both copies give
    golden = _golden()
    g = next(e for e in golden["excerpts"] if e["id"] == "Matthew-1-1-08")
    w = g["words"].split(" ")
    g["words"] = " ".join(w[:3] + ["not"] + w[3:])
    inputs, out, cache = _stage(tmp_path / "words", golden=golden, monkeypatch=monkeypatch)
    assert bc.main([str(inputs), str(out), "fetch", str(cache)]) == 1
    err = capsys.readouterr().err
    assert err.startswith("REFUSED: golden mismatch: ") and '["Matthew-1-1-08", ["words"]]' in err, err
    assert not out.exists() or _files(out) == {}
    # the writer: where the golden reads Chrysostom and both copies print Pseudo-Chrysostom, the build refuses; it
    # never serves one under the other's name
    golden = _golden()
    next(e for e in golden["excerpts"] if e["id"] == "Matthew-1-1-15")["author_as_printed"] = "CHRYS"
    inputs, out, cache = _stage(tmp_path / "author", golden=golden, monkeypatch=monkeypatch)
    assert bc.main([str(inputs), str(out), "fetch", str(cache)]) == 1
    err = capsys.readouterr().err
    assert '["Matthew-1-1-15", ["author"]]' in err, err
    assert not out.exists() or _files(out) == {}
    # the verse: Matthew 1:1's section is confirmed (both copies, the running heads, its place in the chapter), so a
    # golden reading another verse refuses the build, held or served (Jerome's Matthew-1-1-01 is held on its words)
    for gid in ("Matthew-1-1-08", "Matthew-1-1-01"):
        golden = _golden()
        next(e for e in golden["excerpts"] if e["id"] == gid)["verse"] = "Matthew 1:2"
        inputs, out, cache = _stage(tmp_path / ("verse" + gid[-2:]), golden=golden, monkeypatch=monkeypatch)
        assert bc.main([str(inputs), str(out), "fetch", str(cache)]) == 1
        err = capsys.readouterr().err
        assert '["%s", ["verse"]]' % gid in err, err
        assert not out.exists() or _files(out) == {}


def _inputs(bc):
    authors, golden, census, mis, forms, verses = bc.load_inputs(str(ROOT))
    return golden, census, forms, bc.prime(golden, mis, forms), verses


def _pages(bc, tmp_path, ident, name):
    """One fixture's pages, laid out as the build lays them out."""
    return bc.load_pages(bc.item_pages(str(FIX / name), str(tmp_path), name.replace(".gz", "")))


def _parsed(bc, tmp_path, pages=PAGES, suffix=""):
    golden, census, forms, misset, verses = _inputs(bc)
    recs = [_pages(bc, tmp_path, ident, f"{ident}{suffix}_abbyy.gz") for ident in (KELLY, PRINCETON)]
    part = dict(census["parts"]["mt1"], printed_pages=pages)
    by_leaf = {}
    for e in golden["excerpts"]:
        if e["item"] == KELLY:
            by_leaf.setdefault(e["leaf"], []).append(e)
    return part, recs, forms, misset, by_leaf, verses


def _head(bc, recs, page, key):
    """The first line on a printed page holding a small-capitals head, and the head's index in it."""
    for r in recs:
        if r.get("pg") == page:
            for ln in r["lines"]:
                for k, w in enumerate(ln["w"]):
                    if "s" in w[1] and bc.key_of(w[0]) == key:
                        return r, ln, k
    raise AssertionError(f"no {key} head on page {page}")


def _share(bc, recs, mutate):
    """One copy's pages with a change made after Chrysostom's head on page 10 (golden Matthew-1-1-08)."""
    out = copy.deepcopy(recs)
    r, ln, k = _head(bc, out, 10, "CHRYS")
    k += 2 if ln["w"][k + 1][0] in (";", ".") else 1
    assert k + 2 < len(ln["w"]), "the head's line runs on"
    nxt = r["lines"][r["lines"].index(ln) + 1]
    assert nxt["kind"] == "body" and "s" not in nxt["w"][0][1], "the excerpt runs on to the next line"
    mutate(ln, k, nxt)
    return out


def _word(text, flags=""):
    return lambda ln, k, nxt: ln["w"].__setitem__(k, [text, flags, ln["w"][k][2]])


SHARED = {
    "ligature ae": _word("Cæsar"),
    "character or misreading": _word("fyc."),
    "superscript not a footnote mark": _word("z", "u"),
    "italic I": _word("have", "i"),
    "unflagged head": _word("JEROME;"),
    "fused margin word": lambda ln, k, nxt: ln.__setitem__("fused", True),
    "lost hyphen": lambda ln, k, nxt: (ln["w"].__setitem__(-1, ["genera", "", ln["w"][-1][2]]),
                                       nxt["w"].__setitem__(0, ["tion", "", nxt["w"][0][2]])),
}


def test_build_holds_what_two_copies_of_one_typesetting_share(bc, tmp_path):
    part, recs, forms, misset, by_leaf, verses = _parsed(bc, tmp_path)

    def run(a, b, golden=by_leaf):
        served, counts, checks = bc.build_part("mt1", part, a, b, forms, misset, golden, verses)
        return {x["author_as_printed"] for x in served}, counts, checks
    printed, counts, checks = run(*recs)
    assert "CHRYS" in printed and ["Matthew-1-1-08", []] in checks           # read alike, and served
    assert bc.vocab(recs, *PAGES)["generation"] > 0
    no_08 = {leaf: [e for e in es if e["id"] != "Matthew-1-1-08"] for leaf, es in by_leaf.items()}
    printed, before, _ = run(*recs, golden=no_08)
    assert "CHRYS" in printed
    for hold, mutate in SHARED.items():
        a, b = _share(bc, recs[0], mutate), _share(bc, recs[1], mutate)
        # as for every excerpt the golden does not hold: both copies read it alike, error and all, and the hold
        # keeps it back
        printed, counts, _ = run(a, b, no_08)
        assert "CHRYS" not in printed, hold
        assert counts["holds_applying"].get(hold, 0) > before["holds_applying"].get(hold, 0), hold
        printed, counts, _ = run(a, b)
        if hold == "fused margin word":
            # the words are the page's own (only the box moved): the golden, reading them alike, lifts the hold
            assert "CHRYS" in printed
        else:
            # the golden, which reads otherwise from the page image, does not lift it
            assert "CHRYS" not in printed and ["Matthew-1-1-08", hold] in counts["golden_held_by_first_hold"], hold
    # a line set at the Gospel's spacing that opens on a number, inside the excerpt, in both copies: a verse whose
    # mark neither copy read as one ('65 Pilate', no stop), so the excerpt cannot be attributed with certainty
    def numbered(ln, k, nxt):
        nxt["kind"] = "gospel"
        nxt["w"][0] = ["65", "", nxt["w"][0][2]]
    a, b = _share(bc, recs[0], numbered), _share(bc, recs[1], numbered)
    for golden in (no_08, by_leaf):
        printed, counts, _ = run(a, b, golden)
        assert "CHRYS" not in printed
        assert counts["holds_applying"].get("numbered Gospel line in the words", 0) == 1
    held = dict((gid, h) for gid, h in counts["golden_holds"])
    assert "numbered Gospel line in the words" in held["Matthew-1-1-08"]
    # the same line set at the Gospel's spacing with no number is the commentary's own words, not held for it
    def wide(ln, k, nxt):
        nxt["kind"] = "gospel"
    printed, counts, _ = run(_share(bc, recs[0], wide), _share(bc, recs[1], wide))
    assert "CHRYS" in printed and "numbered Gospel line in the words" not in counts["holds_applying"]
    # the golden lifts a hold only where both copies and the page image read the same words
    a, b = _share(bc, recs[0], SHARED["ligature ae"]), _share(bc, recs[1], SHARED["ligature ae"])
    lifted = copy.deepcopy(by_leaf)
    g = next(e for e in lifted[33] if e["id"] == "Matthew-1-1-08")
    g["words"] = " ".join(["Cæsar"] + g["words"].split(" ")[1:])
    printed, counts, checks = run(a, b, lifted)
    assert "CHRYS" in printed and ["Matthew-1-1-08", []] in checks
    # one word at a time: the stated punctuation, the holds on characters, the italic I, the footnote mark
    voc = {"generation": 3}

    def holds_of(*words, marks=()):
        """Each word is text, or (text, flags, ends its line)."""
        ws = [w if isinstance(w, tuple) else (w, "", False) for w in words]
        toks = [[t, f, 33, 0, False, end, False, list(marks)] for t, f, end in ws]
        return bc.words_of({"toks": toks}, voc, misset)
    for fine in ("Father's", "money-changer", "(saith", "him),", '"Lord"', "it—", "&c.", "this?", "Ver."):
        assert holds_of("and", fine, "so")[1] == set(), fine
    # a figure is outside the stated set, alone or inside a word: '109th' and 'wor1d' as much as '3' or '1:2;'
    for bad in ("w^as", "&", "fyc.", "tlie", "Christ*", "one|", "109th", "wor1d", "3", "1:2;", "xlii.2"):
        assert "character or misreading" in holds_of("and", bad, "so")[1], bad
    for i_read in ("/", "1", "l", "J"):              # the italic I read as another mark, before a word in lower case
        assert "italic I" in holds_of("and", i_read, "say", "so")[1], i_read
    assert "italic I" not in holds_of("and", "J", "Saith")[1]
    # an italic run whose first word is lower case, wherever it opens, is held; one that opens with a capital, and the
    # words that carry a run on, are not
    assert "italic I" in holds_of("follows,", ("hungred", "i", False), ("and", "i", False))[1]
    assert "italic I" in holds_of(("curialis", "i", False), "and")[1]
    assert "italic I" not in holds_of("follows,", ("Blessed", "i", False), ("are", "i", False))[1]
    assert holds_of("and", ("a", "u", False), "so", marks=["a"]) == (["and", "so"], set(), [])   # a mark answered
    assert holds_of(("genera", "", True), "tion")[1] == {"lost hyphen"}
    words, holds, undecided = holds_of("the", ("water-", "", True), "pots")
    assert undecided == [(1, "water", "pots")]                                         # neither form settles it


def test_listing_and_pin_name_the_catena_build(bc):
    bb = _load("box_build_under_test", ROOT / "tools" / "box_build.py")
    entries = bb.parse_listing((ROOT / "tools" / "box_builds.txt").read_text(encoding="utf-8"))
    e = entries["catena-aurea"]
    assert e.tool == "tools/build_catena.py" and e.args == ("fetch",)
    assert sorted(e.inputs) == sorted(bc.INPUTS) == sorted(
        "tools/catena_aurea/" + n for n in ("authors.json", "census.json", "golden.json", "gospel_verses.json",
                                            "misreadings.json"))
    assert 256 <= e.cap_mb <= 1024
    pins = json.loads((ROOT / "src" / "concordance" / "build_pins.json").read_text(encoding="utf-8"))
    assert pins["catena-aurea"] == e.hash
    # the shelf reads the build by the listed name; every copy the census names is pinned by its sha256
    commentary = _load("commentary_under_test", ROOT / "src" / "concordance" / "commentary.py")
    assert commentary.CATENA == e.name == "catena-aurea"
    census = json.loads((CATENA / "census.json").read_text(encoding="utf-8"))
    for part in census["parts"].values():
        for ident in (part["copy_a"], part["copy_b"]):
            sha = census["items"][ident]["layout_files"]["abbyy_gz"]["sha256_fetched_2026_11_11"]
            assert len(sha) == 64 and set(sha) <= set("0123456789abcdef"), ident


# ------------------------------------------------------------------------------------------------ step catena2

def test_matthew_1_1_as_served_and_held(bc, tmp_path, monkeypatch, capsys):
    """Every golden excerpt of Matthew 1:1 on pages 9-16 is either served word for word or held with its reasons, or
    named as matched to no head: Jerome and Rabanus are held there (their two copies read otherwise), never shown
    under another name."""
    inputs, out, cache = _stage(tmp_path, monkeypatch=monkeypatch)
    assert bc.main([str(inputs), str(out), "fetch", str(cache)]) == 0, capsys.readouterr().err
    part = json.loads((out / "_build.json").read_text(encoding="utf-8"))["parts"]["mt1"]
    golden = {e["id"]: e for e in _golden()["excerpts"] if e["verse"] == "Matthew 1:1" and 32 <= e["leaf"] <= 39}
    report = json.loads((out / "_build.json").read_text(encoding="utf-8"))
    served = set(report["golden_checked"]) & set(golden)
    held = {gid: holds for gid, holds in part["golden_holds"] if gid in golden}
    no_head = {gid: why for gid, why in part["golden_no_head_matched"] if gid in golden}
    assert served == set(SERVED)
    assert served | set(held) | set(no_head) == set(golden) and not (served & set(held))
    assert all(holds for holds in held.values())
    for gid, g in golden.items():
        if g["author_as_printed"] in ("JEROME", "RABANUS"):
            assert gid in held or gid in no_head, gid
    assert {"Matthew-1-1-01", "Matthew-1-1-02", "Matthew-1-1-07", "Matthew-1-1-14"} <= set(held)
    assert "words differ" in held["Matthew-1-1-02"]                     # Rabanus: the copies read otherwise
    chapter = json.loads((out / "MAT" / "1.json").read_text(encoding="utf-8"))
    printed = [x["author_as_printed"] for b in chapter["blocks"] for x in b["excerpts"]]
    assert "JEROME" not in printed and "RABANUS" not in printed


def test_a_section_both_copies_misread_alike_is_held(bc, tmp_path):
    """Matthew-s10-p32 stands in the section 1:12-15. Read as printed, its verse follows 1:8-11 and the section is in
    order; where both copies misread the mark alike (here '12—15.' read '2.' in both, as the earlier parse read it)
    the section no longer follows the one before it, and it is held, never served under 1:2 and never refused."""
    part, recs, forms, misset, by_leaf, verses = _parsed(bc, tmp_path, pages=[24, 33], suffix="_pages24-33")
    part["opens_in_chapter"] = 1                                           # the cut opens inside chapter 1

    def holds_of_s10(a, b):
        served, counts, checks = bc.build_part("mt1", part, a, b, forms, misset, by_leaf, verses)
        holds = dict((gid, h) for gid, h in counts["golden_holds"])
        assert not [c for c in checks if c[1]], checks                     # nothing refused
        return holds.get("Matthew-s10-p32"), counts, served
    holds, counts, served = holds_of_s10(*recs)
    for one in recs:
        _, _, _, secs = bc.walk(one, 24, 33, 1, forms, 1)
        assert ((1, 8), (1, 11)) in secs and ((1, 12), (1, 15)) in secs
    assert holds is not None and "verse out of order" not in holds          # held on its words, not its verse
    assert counts["golden_verse_disputes"] == []

    def misread(one):
        out = copy.deepcopy(one)
        hits = 0
        for r in out:
            for ln in r["lines"]:
                if ln["w"] and ln["w"][0][0] == "12—15.":
                    ln["w"][0][0] = "2."
                    hits += 1
        assert hits == 1
        return out
    holds, counts, served = holds_of_s10(misread(recs[0]), misread(recs[1]))
    assert "verse out of order" in holds
    assert ["Matthew-s10-p32", "Matthew 1:12-15", "Matthew 1:2"] in counts["golden_verse_disputes"]
    assert not [x for x in served if x["verse"] == "Matthew 1:2"]


ITALIC_I = (("Matthew-t01-p866", ("catenaaureacomme01thomuoft_leaf137", "catenaurecommpt301thomuoft_leaf137"), 866,
             "follows,", "was"),
            ("John-s09-p418", ("catenaaureacomm204arisuoft_leaf55", "catenaaureacomme04thom_leaf428"), 418,
             "this,", "will"))


def test_the_italic_i_hold_holds_the_golden_mid_sentence_cases(bc, tmp_path):
    """The golden's two cases of an italic I in mid-sentence, after a comma ('It follows, I was an hungred';
    'understand this, I will not judge'). Both copies read the I as '/'. With the I removed in both copies, as
    where both drop it, the copies read alike and the italic run opens on 'was' or 'will' in lower case: the hold
    keeps the excerpt back, and the golden, which holds the I, does not lift it."""
    golden, census, forms, misset, verses = _inputs(bc)
    G = {e["id"]: e for e in golden["excerpts"]}
    for gid, names, page, before, first in ITALIC_I:
        words = []
        for name in names:
            recs = _pages(bc, tmp_path, None, name + "_abbyy.gz")
            exs, _, _, _ = bc.walk(recs, page, page, 1, forms)
            ex = next(e for e in exs if bc.key_of(e["head"]) == bc.key_of(G[gid]["author_as_printed"]) and
                      any(t[0] == before for t in e["toks"]))
            k = next(i for i, t in enumerate(ex["toks"]) if t[0] == before)
            assert [t[0] for t in ex["toks"][k:k + 3]] == [before, "/", first] and "i" in ex["toks"][k + 2][1]
            assert "italic I" in bc.words_of(ex, {}, misset)[1]                         # as read: '/' for the I
            ex["toks"] = ex["toks"][:k + 1] + ex["toks"][k + 2:]                       # the I gone in this copy
            w, holds, _ = bc.words_of(ex, {}, misset)
            assert "italic I" in holds, (gid, name)
            j = next(i for i in range(len(w) - 1) if w[i:i + 2] == [before, first])
            words.append(w[j:j + 3])
        assert words[0] == words[1] == [before, first, words[0][2]]                    # the copies read alike
        gt = bc.tokens(G[gid]["words"])
        assert any(gt[i:i + 3] == [before, "I", first] for i in range(len(gt)))       # the page prints the I


def test_a_section_bounded_at_a_listed_pair_is_held(bc, tmp_path):
    """The input lists every Gospel chapter's English verse numbers, the seven chapters numbered otherwise, and the
    pairs the Latin divides otherwise, among them the five checker-100 read; a section whose first or last verse is
    either verse of a listed pair is held."""
    verses = json.loads((CATENA / "gospel_verses.json").read_text(encoding="utf-8"))
    pairs = {(p["gospel"], p["chapter"], tuple(p["verses"])) for p in verses["pairs"]}
    assert {("Luke", 4, (18, 19)), ("Luke", 9, (42, 43)), ("John", 4, (13, 14)), ("John", 10, (41, 42)),
            ("Matthew", 16, (2, 3))} <= pairs
    # and the three a short speech formula carries across, which the word-ratio band misses (checker-100, line 64)
    assert {("Mark", 3, (11, 12)), ("Luke", 22, (34, 35)), ("John", 5, (18, 19))} <= pairs
    assert verses["boundary_detectors"]["read"] == len(verses["boundaries_read"]) > 0
    # the build serves no section bounded at a listed pair: every block in the cut of its output, among them Luke
    # 22 and John 5, where Luke 22:31-34 and John 5:14-18 stood before these pairs were listed
    at = {(p["gospel"], p["chapter"], v) for p in verses["pairs"] for v in p["verses"]}
    books = {b["code"]: b["name"] for b in json.loads((FIX / "shelf" / "_books.json").read_text(encoding="utf-8"))}
    blocks = 0
    for f in sorted((FIX / "shelf").glob("*/*.json")):
        gospel = books[f.parent.name]
        for blk in json.loads(f.read_text(encoding="utf-8"))["blocks"]:
            blocks += 1
            assert (gospel, blk["chapter"], blk["verse"]) not in at, (f.name, blk["range"])
            assert (gospel, blk["end_chapter"], blk["verse_end"]) not in at, (f.name, blk["range"])
            assert blk["range"] not in ("Luke 22:31-34", "John 5:14-18")
    assert blocks >= 20 and (FIX / "shelf" / "LUK" / "22.json").is_file() and (FIX / "shelf" / "JHN" / "5.json").is_file()
    assert all(p["reading"] for p in verses["pairs"])
    assert {(h["gospel"], h["chapter"]) for h in verses["held_whole"]} == {
        ("Matthew", 17), ("Mark", 4), ("Mark", 8), ("Mark", 9), ("Luke", 17), ("John", 6), ("John", 11)}
    assert sum(len(c) for c in verses["chapters"].values()) == 89
    assert verses["chapters"]["Luke"]["17"][-3:] == [34, 35, 37]                   # no verse 36 in the English
    assert verses["band"]["read"] == len(verses["candidates_read"]) >= verses["band"]["outside"]
    # on the fixture pages, Matthew 1:1's section is served; with a pair listed at 1:1/2 it is held whole
    part, recs, forms, misset, by_leaf, verses = _parsed(bc, tmp_path)
    served, counts, _ = bc.build_part("mt1", part, recs[0], recs[1], forms, misset, by_leaf, verses)
    assert [x for x in served if x["verse"] == "Matthew 1:1"]
    listed = copy.deepcopy(verses)
    listed["pairs"].append({"gospel": "Matthew", "chapter": 1, "verses": [1, 2], "reading": "a test pair"})
    served, counts, _ = bc.build_part("mt1", part, recs[0], recs[1], forms, misset, by_leaf, listed)
    assert not [x for x in served if x["verse"] == "Matthew 1:1"]
    assert counts["holds_applying"]["bounded at a listed pair"] >= len(SERVED)
