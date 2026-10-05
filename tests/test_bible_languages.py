"""THE BIBLES BY LANGUAGE (2026-10-04 — Lighthouse 1.0 integrated, not retired; Matt: "agreed") and THE WORD IN
THE READER'S TONGUE (Gen 3 · 4). One public-domain translation per language in data/bible_<lang>.jsonl; the WEB
stays "en" and the default; the book may be named as the reader names it (data/bible_book_names.json, gathered).
What is listed is what is on disk — a language held at the licence gate is absent, never invented.

This module does NOT hijack CONCORDANCE_DATA_DIR at import (see conftest.real_cards for why the race
matters): a module fixture points scripture at a scratch dir for these tests only and puts back the
exact cached Bibles it found, so the modules collected after this one measure what they would have."""
import json
import os
import tempfile
from pathlib import Path

import pytest

from concordance.engine import EngineConfig
from concordance.mcp import server as mcp
from concordance.verifiers import scripture
from concordance.web import api


def _write(d: Path, lang, rows):
    with open(d / f"bible_{lang}.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


@pytest.fixture(scope="module", autouse=True)
def scratch_bibles():
    tmp = Path(tempfile.mkdtemp(prefix="nh-langs-"))
    _write(tmp, "en", [{"book": "John", "book_abbr": "JHN", "chapter": 3, "verse": 16,
                        "text": "For God so loved the world, that he gave his only born Son",
                        "translation": "World English Bible"}])
    _write(tmp, "es", [{"book": "John", "book_abbr": "JHN", "chapter": 3, "verse": 16,
                        "text": "Porque de tal manera amó Dios al mundo, que ha dado á su Hijo unigénito",
                        "translation": "Reina-Valera 1909", "lang": "es", "year": 1909, "license": "Public Domain"}])
    _write(tmp, "zh", [{"book": "Genesis", "book_abbr": "GEN", "chapter": 1, "verse": 1, "text": "起初， 神创造天地。",
                        "translation": "Chinese Union Version (Simplified)", "lang": "zh", "year": 1919,
                        "license": "Public Domain"},
                       {"book": "John", "book_abbr": "JHN", "chapter": 3, "verse": 16, "text": "神爱世人",
                        "translation": "Chinese Union Version (Simplified)", "lang": "zh"}])
    _write(tmp, "de", [{"book": "John", "book_abbr": "JHN", "chapter": 3, "verse": 16,
                        "text": "Also hat Gott die Welt geliebt", "translation": "Lutherbibel 1912", "lang": "de"}])
    (tmp / "bible_book_names.json").write_text(json.dumps({"source": "test", "names": {
        "es": {"juan": "John", "genesis": "Genesis", "1 juan": "1 John"},
        "zh": {"约翰福音": "John", "创世记": "Genesis"},
        "de": {"johannes": "John", "1 mose": "Genesis"},
        "nl": {"johannes": "John"}}}, ensure_ascii=False), encoding="utf-8")
    prior_env = {k: os.environ.get(k) for k in ("CONCORDANCE_DATA_DIR", "CONCORDANCE_BIBLE_EN")}
    prior_cache = (scripture._DEFAULT, dict(scripture._BIBLES), scripture._LANGUAGES)
    os.environ["CONCORDANCE_DATA_DIR"] = str(tmp)
    os.environ.pop("CONCORDANCE_BIBLE_EN", None)
    scripture._reset()
    try:
        yield tmp
    finally:
        for k, v in prior_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        scripture._DEFAULT, scripture._LANGUAGES = prior_cache[0], prior_cache[2]
        scripture._BIBLES.clear()
        scripture._BIBLES.update(prior_cache[1])


def test_the_languages_are_read_from_disk_with_their_translation():
    langs = {x["lang"]: x for x in scripture.languages()}
    assert set(langs) == {"en", "es", "zh", "de"}
    assert langs["es"]["translation"] == "Reina-Valera 1909" and langs["es"]["verses"] == 1
    assert langs["es"]["license"] == "Public Domain" and langs["en"]["translation"] == "World English Bible"


def test_a_passage_reads_in_a_held_language_and_the_web_stays_default():
    p = scripture.read_passage("John 3:16", "es")
    assert p["status"] == "ok" and p["lang"] == "es" and p["translation"] == "Reina-Valera 1909"
    assert p["verses"][0]["text"].startswith("Porque de tal manera")
    assert scripture.read_passage("John 3:16")["verses"][0]["text"].startswith("For God so loved")
    assert scripture.read_passage("Genesis 1:1", "ZH")["verses"][0]["text"].startswith("起初")   # case-insensitive
    r = scripture.resolve_ref("John 3:16", "es-ES")                                           # region tag tolerated
    assert r["status"] == "ok" and r["text"].startswith("Porque")


def test_an_unknown_language_declines_and_names_what_is_held():
    p = scripture.read_passage("John 3:16", "xx")
    assert p["status"] == "not_found" and p["verses"] == [] and p["languages"] == ["de", "en", "es", "zh"]
    assert "GET /languages" in p["detail"]


def test_the_routes_and_the_mcp_tool_carry_lang():
    cfg = EngineConfig("witness")
    st, body = api.dispatch("GET", "/passage", {"ref": "John 3:16", "lang": "es"}, None, cfg)[:2]
    assert st == 200 and body["verses"][0]["text"].startswith("Porque")
    st, body = api.dispatch("GET", "/languages", {}, None, cfg)[:2]
    assert st == 200 and body["count"] == 4 and [x["lang"] for x in body["languages"]] == ["de", "en", "es", "zh"]
    st, body = api.dispatch("GET", "/capabilities", {}, None, cfg)[:2]
    assert st == 200 and body["bible_languages"] == ["de", "en", "es", "zh"]
    res = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                      "params": {"name": "read_passage", "arguments": {"ref": "John 3:16", "lang": "es"}}}, cfg, {})
    assert "Porque de tal manera" in json.dumps(res, ensure_ascii=False)
    tools = mcp.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, cfg, {})["result"]["tools"]
    schema = next(t for t in tools if t["name"] == "read_passage")
    assert "lang" in schema["inputSchema"]["properties"]


def test_the_stdio_loop_speaks_utf8_whatever_the_console_code_page(monkeypatch):
    """2026-10-04: the desktop node died on its first run — cp1252 stdout met an arrow in the welcome."""
    import io as _io
    import sys as _sys
    req = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
           "params": {"name": "read_passage", "arguments": {"ref": "Genesis 1:1", "lang": "zh"}}}
    inp = _io.TextIOWrapper(_io.BytesIO(json.dumps(req).encode("utf-8") + b"\n"), encoding="cp1252")
    buf = _io.BytesIO()
    out = _io.TextIOWrapper(buf, encoding="cp1252", write_through=True)
    monkeypatch.setattr(_sys, "stdin", inp)
    monkeypatch.setattr(_sys, "stdout", out)
    mcp.serve_stdio(surface="witness")
    assert "起初" in buf.getvalue().decode("utf-8")


def test_the_book_named_in_the_readers_tongue_answers_in_it():
    """Gen 3 · 4: "Juan 3:16" is John 3:16 and comes back in Spanish; "约翰福音3:16" in Chinese; an English
    name stays English; the caller's lang still wins; an ambiguous name (Johannes: de and nl) picks a held
    Bible and says what it saw; an accent the reader dropped does not matter; nothing is authored — the
    names are the gathered file's."""
    p = scripture.read_passage("Juan 3:16")
    assert p["status"] == "ok" and p["lang"] == "es" and p["ref"] == "John 3:16" and p["asked"] == "Juan 3:16"
    assert p["named_in"] == ["es"] and p["verses"][0]["text"].startswith("Porque")
    p = scripture.read_passage("约翰福音3:16")                                   # no space, as Chinese is written
    assert p["lang"] == "zh" and p["ref"] == "John 3:16" and p["verses"][0]["text"] == "神爱世人"
    assert scripture.read_passage("John 3:16")["lang"] == "en"                 # English is a held language too
    assert scripture.read_passage("Juan 3:16", lang="en")["lang"] == "en"      # the caller chose
    p = scripture.read_passage("Johannes 3,16")                                # German comma; de and nl both name it so
    assert p["lang"] == "de" and p["named_in"] == ["de", "nl"] and p["verses"][0]["text"].startswith("Also hat Gott")
    assert scripture.localize_ref("1 Juan 1:9") == ("1 John 1:9", ["es"])
    assert scripture.localize_ref("Génesis 1:1") == ("Genesis 1:1", ["es"])    # the gathered key has no accent
    assert scripture.localize_ref("Nowhere 3:16") == ("Nowhere 3:16", [])
    # prose is not a reference: on the first live run "what is 2 + 2" became Isaiah 2 in French through a
    # two-letter alias ("Is"); a fragment with words, inner digits or a short Latin token is left alone
    names = json.loads((Path(os.environ["CONCORDANCE_DATA_DIR"]) / "bible_book_names.json").read_text(encoding="utf-8"))
    names["names"]["fr"] = {"is": "Isaiah", "esaie": "Isaiah"}
    (Path(os.environ["CONCORDANCE_DATA_DIR"]) / "bible_book_names.json").write_text(json.dumps(names), encoding="utf-8")
    assert scripture.localize_ref("is 2") == ("is 2", [])
    assert scripture.localize_ref("what is 2 + 2") == ("what is 2 + 2", [])
    assert scripture.localize_ref("Esaie 2:1") == ("Isaiah 2:1", ["fr"])      # the real name still resolves
    st, body = api.dispatch("GET", "/passage", {"ref": "Juan 3:16"}, None, EngineConfig("witness"))[:2]
    assert st == 200 and body["translation"] == "Reina-Valera 1909" and body["lang"] == "es"
