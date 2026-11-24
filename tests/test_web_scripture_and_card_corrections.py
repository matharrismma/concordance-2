"""The WEB as the user-facing Scripture, and the card corrections (2026-11-23).

Matt: "Use the WEB as the user facing content." and "Cut the raven story if it isn't scriptural."
  1. References people actually write — an en dash range, a translation tag — must open the passage. Before this,
     "John 15:1–3" and "John 15:1-3 NKJV" both answered "could not parse passage".
  2. His devotional cards say WEB, not NKJV; the raven sermon keeps only what Scripture says — applied at load
     from a tracked table, fail-closed per card, never by rewriting the box's card files.
"""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import card_corrections as C  # noqa: E402
from concordance.verifiers import scripture as S  # noqa: E402

VERSES = [{"book": "John", "chapter": 15, "verse": v, "text": t} for v, t in (
    (1, "I am the true vine, and my Father is the farmer."),
    (2, "Every branch in me that doesn't bear fruit, he takes away."),
    (3, "You are already pruned clean because of the word which I have spoken to you."))]


# ── 1. THE REFERENCE AS PEOPLE WRITE IT ─────────────────────────────────────────────────────────────
def test_clean_ref_normalises_every_dash_and_lifts_a_translation_tag():
    assert S.clean_ref("John 15:1–3") == ("John 15:1-3", None)          # en dash
    assert S.clean_ref("John 15:1—3") == ("John 15:1-3", None)          # em dash
    assert S.clean_ref("John 15:1−3") == ("John 15:1-3", None)          # minus sign
    assert S.clean_ref("John 15:1–3 NKJV") == ("John 15:1-3", "NKJV")
    assert S.clean_ref("1 Peter 5:9—11 (KJV)") == ("1 Peter 5:9-11", "KJV")
    assert S.clean_ref("Mark 1:1 net.") == ("Mark 1:1", "NET")
    assert S.clean_ref("John 15:1-3 WEB") == ("John 15:1-3", "WEB")


def test_clean_ref_never_eats_a_book_or_a_bare_tag():
    assert S.clean_ref("Amos 5:24") == ("Amos 5:24", None)
    assert S.clean_ref("Song of Solomon 2:1") == ("Song of Solomon 2:1", None)
    assert S.clean_ref("NKJV") == ("NKJV", None)                         # nothing left would be no reference at all


def test_a_dashed_tagged_range_opens_the_passage():
    b = S.Bible(VERSES)
    for ref in ("John 15:1–3", "John 15:1-3 NKJV", "John 15:1–3 NKJV", "John 15:1 — 3"):
        p = b.passage(ref)
        assert p["status"] == "ok" and p["count"] == 3, (ref, p)
    assert b.resolve("John 15:2 NKJV")["status"] == "ok"


def test_the_note_says_which_text_is_shown_and_only_when_it_is_not_the_one_asked():
    out = S._translation_note({"translation": "World English Bible"}, "NKJV")
    assert out["translation_asked"] == "NKJV"
    assert out["translation_note"] == "NKJV is not held here; the text shown is the World English Bible"
    assert "translation_note" not in S._translation_note({"translation": "World English Bible"}, "WEB")
    assert "translation_note" not in S._translation_note({}, None)


# ── 2. THE CARD CORRECTIONS ──────────────────────────────────────────────────────────────────────────
def _rows():
    return json.loads(C.TABLE_PATH.read_text(encoding="utf-8"))["corrections"]


def test_the_table_is_complete_and_says_why():
    rows = _rows()
    assert rows and all(r.get("id") and r.get("rule") and r.get("date") and r.get("directive") and r.get("changes")
                        for r in rows)
    web = [r for r in rows if r["rule"] == "web-user-facing"]
    assert len(web) == 26
    for r in web:
        for ch in r["changes"]:
            assert ("old" in ch) != ("old_sha256" in ch)                  # every change names what it expects
            assert ("new" in ch) != ("spans" in ch)
            if "new" in ch:
                assert "NKJV" not in json.dumps(ch["new"], ensure_ascii=False), (r["id"], ch["path"])
            else:
                assert all(rep == " (World English Bible)" for _, _, rep in ch["spans"]), (r["id"], ch["spans"])


REFERENCE_OR_NOTHING = re.compile(r"^( \([1-3]? ?[A-Z][a-z]+ \d+:\d+(–\d+)?\))?\.?$")


OURS = {"author": "operator", "source.authority_tier": "operator"}


def test_no_prose_of_his_is_stored_only_spans_and_references():
    """His sermons and devotionals stay out of the public repo: a body change is spans of a hashed body, and the
    only text a span may insert is a Scripture reference (or a translation name), never his words. The one
    exception (2026-11-24, the RAS card) is our own short wording on our own card: a row whose `expects` pins the
    card's author AND tier to "operator", which card_corrections checks fail-closed before it changes anything."""
    for r in _rows():
        for ch in r["changes"]:
            if ch["path"] == "body":
                assert "new" not in ch and len(ch["old_sha256"]) == 64 and ch["spans"], r["id"]
                for s, e, rep in ch["spans"]:
                    assert 0 <= int(s) < int(e)
                    assert (r.get("expects") == OURS or rep == " (World English Bible)"
                            or REFERENCE_OR_NOTHING.match(rep)), (r["id"], rep)
    text = C.TABLE_PATH.read_text(encoding="utf-8")
    assert max(len(t) for t in re.findall(r'"([^"]*)"', text)) < 200        # no paragraph anywhere in the table


def test_the_raven_row_cuts_and_never_adds():
    raven = [r for r in _rows() if r["rule"] == "raven-scriptural-only"]
    assert len(raven) == 1 and raven[0]["id"] == "card_n_91dc28d5681a"
    spans = raven[0]["changes"][0]["spans"]
    assert len(spans) >= 6 and all(rep in ("", " (Leviticus 11:15).") for _, _, rep in spans)
    ordered = sorted((int(s), int(e)) for s, e, _ in spans)
    assert all(a[1] <= b[0] for a, b in zip(ordered, ordered[1:]))           # spans never overlap


def test_spans_cut_the_exact_body_right_to_left():
    body = "Keep this. Cut this. Keep that, cut too."
    row = {"id": "card_x", "rule": "r", "date": "d", "directive": "x",
           "changes": [{"path": "body", "old_sha256": C._sha(body),
                        "spans": [[10, 20, ""], [30, 40, " (John 1:1)."]]}]}
    c = {"id": "card_x", "body": body}
    assert C.apply_one(c, [row]) == "applied"
    assert c["body"] == "Keep this. Keep that (John 1:1)."


def _card(**kw):
    c = {"id": "card_x", "title": "Devotional: X", "body": "His words.",
         "source": {"label": "Operator-authored devotional", "ref": "John 15:1–3 NKJV", "authority_tier": "matt"},
         "bands": ["devotional", "John 15:1–3 NKJV"], "facets": {"subject": ["John 15:1–3 NKJV"]}}
    c.update(kw)
    return c


ROW = {"id": "card_x", "rule": "web-user-facing", "date": "2026-11-23", "directive": "test",
       "changes": [{"path": "source.ref", "old": "John 15:1–3 NKJV", "new": "John 15:1–3"},
                   {"path": "bands", "old": ["devotional", "John 15:1–3 NKJV"], "new": ["devotional", "John 15:1–3"]}]}


def test_a_matching_card_is_corrected_with_its_provenance_and_only_once():
    c = _card()
    assert C.apply_one(c, [ROW]) == "applied"
    assert c["source"]["ref"] == "John 15:1–3" and c["bands"] == ["devotional", "John 15:1–3"]
    assert c["corrected"] == [{"rule": "web-user-facing", "date": "2026-11-23", "directive": "test"}]
    assert C.apply_one(c, [ROW]) == "already" and len(c["corrected"]) == 1


def test_a_card_that_moved_on_is_left_exactly_as_it_is():
    c = _card(bands=["devotional", "John 15:1–3 NKJV", "a later band"])
    before = copy.deepcopy(c)
    assert C.apply_one(c, [ROW]) == "mismatch"
    assert c == before                                                    # never half-corrected


def test_a_body_change_is_keyed_on_the_hash_of_the_body_it_replaces():
    row = {"id": "card_x", "rule": "r", "date": "d", "directive": "x",
           "changes": [{"path": "body", "old_sha256": C._sha("His words."), "new": "Cut."}]}
    c = _card()
    assert C.apply_one(c, [row]) == "applied" and c["body"] == "Cut."
    other = _card(body="Different words.")
    assert C.apply_one(other, [row]) == "mismatch" and other["body"] == "Different words."


def test_apply_counts_every_outcome_and_never_raises_on_an_absent_card():
    cards = {"card_x": _card()}
    st = C.apply(cards)            # the real table: card_x is not in it, and every id in it is absent here
    assert st["rows"] == len(_rows()) and st["applied"] == 0 and st["absent"] == len(_rows())


def test_the_corrections_are_in_the_corpus_cache_key():
    src = (ROOT / "src" / "concordance" / "corpus.py").read_text(encoding="utf-8")
    assert re.search(r"code_fingerprint\(\[Path\(__file__\), Path\(_corr\.__file__\),\s*_corr\.TABLE_PATH\]\)", src)
    assert "_corr.apply(out)" in src and "_corr.apply_one(full)" in src  # resident at load, frozen on read


if __name__ == "__main__":
    import inspect
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and inspect.isfunction(fn):
            fn()
            print("ok", name)
