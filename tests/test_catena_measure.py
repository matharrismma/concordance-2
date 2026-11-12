"""Run 2026-11-11-fathers-shelf, step measure: the census, the golden and the author table of the Catena Aurea.

The three files under tools/catena_aurea/ are the measured inputs of the catena build (the golden tests its
parser; the table names who may head an excerpt). These tests hold what the plan asks of them: two physical
copies of the 1841-45 printing for every volume part served, at least 30 seeded excerpts per served Gospel,
every excerpt of Matthew 1:1, the named hard cases, editors' notes kept out of a Father's words, and an author
table that holds every attribution, cites the Catholic Encyclopedia and keeps later writers and Pseudo-
authors apart. Stdlib only; no network.
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent / "tools" / "catena_aurea"
GOSPELS = ["Matthew", "Mark", "Luke", "John"]


def _load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def _norm(form):
    return re.sub(r"\s+", " ", re.sub(r"[;:,.]+$", "", form.strip())).upper()


def test_census_names_two_physical_copies_per_served_part():
    census = _load("census.json")
    parts = census["parts"]
    assert sorted(parts) == sorted(["mt1", "mt2", "mt3", "mk", "lk1", "lk2", "jn1", "jn2"])
    served = set()
    for key, part in parts.items():
        a, b = part["copy_a"], part["copy_b"]
        assert a != b, key
        for ident in (a, b):
            item = census["items"][ident]
            # archive.org's mark where it gives one; otherwise the census says so and quotes the title-page date
            assert item["possible_copyright_status"] == "NOT_IN_COPYRIGHT" or "MDCCCXL" in item.get("rights_note", ""), ident
            # the title page's own date, as the item's OCR reads it (MDCCCXLII is read MDCCCXUI in one copy)
            assert any(re.search(r"MDCCCX[LU][IVU]*", t.replace(" ", "")) for t in item["title_pages_ocr"]), ident
            assert "abbyy_gz" in item["layout_files"], ident  # the small-capitals flag lives there
            assert re.fullmatch(r"[0-9a-f]{64}", item["layout_files"]["abbyy_gz"]["sha256_fetched_2026_11_11"]), ident
            assert "not_usable" not in item, ident
        assert part["distinct_copies"].strip(), key
        assert part["chapters_without_two_copies"] == [], key
        assert part["expected_served"] and 0 < part["expected_served"][0]["expected_served_share_of_a"] < 1, key
        first, last = part["printed_pages"]
        assert first < last
        served.add(part["gospel"])
    assert served == set(GOSPELS) == set(census["served_gospels"])
    # the Second Edition of 1865 bound into two Princeton volumes is not used for the parts it holds
    assert "MDCCCLXV" in census["items"]["catenaaureacomme02thom"]["parts_bound"]
    assert parts["mt3"]["copy_b"] != "catenaaureacomme02thom" and parts["lk2"]["copy_b"] != "catenaaureacomme03thom"
    for label in ("CCEL catena1.xml", "CCEL catena2.xml"):
        assert "never served" in census["transcriptions"][label]["use"]


def test_golden_holds_thirty_seeded_excerpts_per_served_gospel():
    golden = _load("golden.json")
    census = _load("census.json")
    sel = golden["selection"]
    covered = {g: set() for g in GOSPELS}
    generators = {}
    for draw_key in sel["draw_order"]:  # one generator per seed, drawing in this order
        spec = sel["populations"][draw_key]
        pages = [p for first, last in spec["page_ranges"] for p in range(first, last + 1)]
        covered[spec["gospel"]] |= set(pages)
        rng = generators.setdefault(spec["seed"], random.Random(spec["seed"]))
        assert rng.sample(pages, spec["sample_size"]) == sel["draws"][draw_key], draw_key
    for gospel in GOSPELS:
        served = set()
        for part in census["parts"].values():
            if part["gospel"] == gospel:
                first, last = part["printed_pages"]
                served |= set(range(first, last + 1))
        assert covered[gospel] == served, gospel  # every served page could be drawn
        seeded = [e for e in golden["excerpts"] if e["gospel"] == gospel and e["selected_by"] == "seed"]
        assert len(seeded) >= 30, gospel
        assert sorted(e["id"] for e in seeded) == sorted(sel["taken"][gospel])
        drawn = {p for k, spec in sel["populations"].items() if spec["gospel"] == gospel for p in sel["draws"][k]}
        for e in seeded:
            page = int(e["id"].rsplit("-p", 1)[1])
            assert page in drawn and page == e["pages"][0], e["id"]
            assert e["words"].strip() and e["head_as_printed"].strip() and e["checked_against_page_image"] is True, e["id"]
            assert re.fullmatch(r"%s \d+:\d+(-\d+)?(-\d+:\d+)?" % gospel, e["verse"]), e["id"]


def test_golden_holds_every_matthew_1_1_excerpt():
    golden = _load("golden.json")
    authors = {f["form"]: a["key"] for a in _load("authors.json")["authors"] for f in a["printed_forms"]}
    mt11 = [e for e in golden["excerpts"] if e["verse"] == "Matthew 1:1"]
    assert len(mt11) == 31
    assert all(e["selected_by"] == "matthew_1_1" for e in mt11)
    keys = {authors[_norm(e["author_as_printed"])] for e in mt11}
    # Jerome, Rabanus and Pseudo-Chrysostom stay apart from Chrysostom
    assert {"jerome", "rabanus", "pseudo_chrysostom", "chrysostom", "gloss", "remigius", "pseudo_athanasius"} <= keys
    pages = sorted({p for e in mt11 for p in e["pages"]})
    assert pages[0] == 9 and pages[-1] == 17


def test_golden_holds_the_named_hard_cases():
    golden = _load("golden.json")
    cases = {}
    for e in golden["excerpts"]:
        for c in e["cases"]:
            cases.setdefault(c, []).append(e)
    for need in ("page_break", "margin_citation", "footnote_page", "footnote_reference_mark", "running_head_in_span",
                 "money_changer", "line_end_real_hyphen", "small_capitals_author", "mid_line_start",
                 "author_name_inside_another_fathers_words", "range", "margin_notes_change_attribution",
                 "editors_dispute_ascription", "link_phrase_it_goes_on", "head_missed_by_ocr_copy_a",
                 "word_flagged_superscript_in_both_copies", "both_ocr_copies_agree_on_a_wrong_word"):
        assert cases.get(need), need
    assert any("money-changer" in e["words"].split() for e in cases["money_changer"])
    assert any(e["editors_notes"] for e in cases["footnote_reference_mark"])
    assert any(len(e["pages"]) > 1 for e in cases["page_break"])
    assert any("It goes on" in e["words"] for e in cases["link_phrase_it_goes_on"])
    leo = [e for e in cases["author_name_inside_another_fathers_words"] if e["author_as_printed"] == "LEO"]
    assert leo and "Origen," in leo[0]["words"].split()


def test_golden_keeps_editors_notes_out_of_the_words():
    golden = _load("golden.json")
    notes = 0
    for e in golden["excerpts"]:
        words = e["words"]
        assert not re.search(r"\[ed\.? note|\[margin note|\[marg\. note|[\^|\\{}<>$]", words), e["id"]
        for note in e["editors_notes"]:
            notes += 1
            assert note["mark"] and len(note["text"].split()) >= 4, e["id"]
            assert note["text"] not in words, e["id"]
            assert note["after"] == "" or note["after"] in words, e["id"]
        for margin in e["margin"]:
            if len(margin.split()) >= 3:
                assert margin not in words, (e["id"], margin)
        if e["citation"]:
            assert e["citation"] in e["margin"], e["id"]
    assert notes >= 8
    for e in golden["excerpts"]:
        for corr in e["ocr_corrections"]:
            assert set(corr) >= {"ocr", "read"}, e["id"]


def test_author_table_holds_every_attribution():
    authors = _load("authors.json")
    census = _load("census.json")
    golden = _load("golden.json")
    forms = {}
    for a in authors["authors"]:
        for f in a["printed_forms"]:
            assert f["form"] not in forms, f["form"]  # one form, one entry
            forms[f["form"]] = a["key"]
    for e in golden["excerpts"]:
        assert _norm(e["author_as_printed"]) in forms, e["id"]
    not_held = {x["form"] for x in authors["census_forms_not_held"]}
    for form, _count, _parts in census["structure"]["printing_head_forms_read_alike_in_both_copies"]:
        assert form in forms or form in not_held, form
    table = [t["name"] for t in authors["edition_table"]["entries"]]
    assert len(table) == 59 and table[0] == "Origen" and "Laufranc" in table and "Bede" in table
    for a in authors["authors"]:
        if a["edition_table_name"]:
            for name in a["edition_table_name"].split("; "):
                assert name in table, (a["key"], name)


def test_author_table_cites_the_encyclopedia_and_keeps_kinds_apart():
    authors = {a["key"]: a for a in _load("authors.json")["authors"]}
    for key in ("gloss", "remigius", "rabanus", "theophylact", "alcuin", "haymo"):
        assert authors[key]["kind"] == "later_writer", key
    for key in ("jerome", "augustine", "chrysostom", "bede", "ambrose", "john_damascene"):
        assert authors[key]["kind"] == "father", key
    for pseudo, real in (("pseudo_chrysostom", "chrysostom"), ("pseudo_jerome", "jerome"), ("pseudo_augustine", "augustine"),
                         ("pseudo_origen", "origen"), ("pseudo_athanasius", "athanasius"), ("pseudo_basil", "basil")):
        assert authors[pseudo]["kind"] == "pseudo"
        assert not {f["form"] for f in authors[pseudo]["printed_forms"]} & {f["form"] for f in authors[real]["printed_forms"]}
    for a in authors.values():
        ce = a["catholic_encyclopedia"]
        if ce:
            assert 1 <= ce["volume"] <= 15 and 1907 <= ce["year"] <= 1914 and ce["archive_org_item"] and ce["article"], a["key"]
        else:
            assert a.get("catholic_encyclopedia_missing"), a["key"]
        if a["kind"] == "unresolved":
            assert a["identified_as"] is None, a["key"]
        # Greek or Latin only where the article states it, with the phrase and its page image; else 'not stated'
        assert a["language"] in ("Greek", "Latin", "not stated"), a["key"]
        if a["language"] == "not stated":
            assert a["language_basis"] is None, a["key"]
        else:
            assert a["language"] in a["language_basis"]["phrase"], a["key"]
            assert a["language_basis"]["page_image"].startswith("https://archive.org/download/"), a["key"]
    assert "MDCCCLXV" not in json.dumps(authors)
    assert authors["hilary"]["editors_mark"] and authors["pseudo_chrysostom"]["editors_mark"]


_MONTHS = "January February March April May June July August September October November December".split()
_WORDS = set("""about c. probably before after not later than or between and some time the year in of at beginning middle
latter half end early late first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth century
centuries from to A. D. fl. b. d.""".split()) | set(_MONTHS)
_NUMBER = re.compile(r"^\(?\d{1,4}(st|nd|rd|th)?([–-]\d{1,4})?\??\)?$")


def _is_date(value):
    tokens = value.replace(",", " ").split()
    return bool(tokens) and any(_NUMBER.match(t) or t in ("century", "centuries") for t in tokens) and all(
        t in _WORDS or _NUMBER.match(t) for t in tokens)


def test_author_dates_hold_only_dates_read_from_the_page_image():
    authors = _load("authors.json")["authors"]
    for good in ("c. 1005", "d. 749", "296-373", "fl. 450", "about the year 340–2", "probably 18 March, 386",
                 "the 9th or the 27th of June, 444", "in the latter half of the fourth century", "about 776 (784?)"):
        assert _is_date(good), good
    for bad in ("c. 100.\"", "about wo", "about WiO", "ec. 296", "at Pavia, c. 1005",
                "Finally Pope Damasus (366-384) is mentioned", "the third oecumenical council, 431"):
        assert not _is_date(bad), bad
    dated = 0
    for a in authors:
        d = a["dates"]
        if a["catholic_encyclopedia"] is None or a["kind"] == "unresolved":
            assert d is None, a["key"]  # no article, or not identified: no dates
            continue
        assert d["page_image"].startswith("https://archive.org/download/"), a["key"]
        fields = [f for f in ("born", "died", "flourished", "held") if f in d]
        for f in fields:
            assert _is_date(d[f]), (a["key"], f, d[f])
        if fields:
            dated += 1
        else:
            assert d["left_out"].strip(), a["key"]  # no date: the reason is said
        if "born" not in d and "died" in d:
            assert d.get("born_left_out", "").strip(), a["key"]
        if "office" in d:
            assert _is_date(d["office"]["dates"]), a["key"]
        for corr in d["ocr_corrections"]:
            assert corr["field"] in fields and corr["read"] == d[corr["field"]] and corr["kind"], a["key"]
    assert dated >= 30
    by_key = {a["key"]: a for a in authors}
    assert by_key["lanfranc"]["dates"]["born"] == "c. 1005"
    assert {"ocr": "ec. 296", "read": "c. 296"}.items() <= by_key["athanasius"]["dates"]["ocr_corrections"][0].items()
