"""The Dictionary — Webster's 1913 + our supplement, offline and model-free. One excellent tool for
"what does this word mean", pointing to its peers (thesaurus, pronounce, word_study) not duplicating
them. Opt-in: with no DB loaded, every call is a clean empty, never a crash. (Needs data/dictionary_en.db
built by tools/build_dictionary.py; the DB-dependent checks skip when it is absent.)"""
import os

from concordance import dictionary as D

_HAVE_DB = D.available()


def test_defines_a_common_word():
    if not _HAVE_DB:
        return
    r = D.define("grace")
    assert r["found"] is True and r["senses"]
    assert any(s["source"] == "webster-1913" for s in r["senses"])


def test_supplement_adds_a_modern_sense_each_labeled():
    if not _HAVE_DB:
        return
    r = D.define("computer")
    srcs = {s["source"] for s in r["senses"]}
    assert "webster-1913" in srcs and "supplement" in srcs, srcs  # 1913 AND modern, each labeled


def test_unknown_word_is_an_honest_miss():
    if not _HAVE_DB:
        return
    r = D.define("zzqxnotaword")
    assert r["found"] is False and r["senses"] == []


def test_points_to_peers_not_duplicates():
    r = D.define("grace")
    assert r["see_also"]["synonyms"] == "thesaurus"
    assert r["see_also"]["pronunciation"] == "pronounce"
    assert r["see_also"]["in_scripture"] == "word_study"


def test_absent_dictionary_is_safe_and_opt_in():
    # pointing at a missing file -> not available, and a novel (uncached) word is a clean miss, no crash
    old = os.environ.get("CONCORDANCE_DICTIONARY_DB")
    os.environ["CONCORDANCE_DICTIONARY_DB"] = "/no/such/dictionary.db"
    try:
        assert D.available() is False
        assert D.define("auniquewordneverlookedupbefore")["found"] is False
    finally:
        if old is None:
            del os.environ["CONCORDANCE_DICTIONARY_DB"]
        else:
            os.environ["CONCORDANCE_DICTIONARY_DB"] = old


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]:
        fn()
        print("  ok ", fn.__name__)
    print("dictionary tests passed.")
