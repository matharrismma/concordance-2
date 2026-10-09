"""THE BAND SWITCH (Matt, 2026-10-08: "engages only the correct components for the intended purpose"): every intent in
engagement.INTENTS runs with its forbidden components ARMED TO RAISE. If a door reaches for a component it must not
engage, the test fails there, by name. No corpus (an empty data dir): a cold process, which is also the proof that a
check never builds the keeping."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

TMP = Path(tempfile.mkdtemp(prefix="nh-engage-"))
os.environ["CONCORDANCE_DATA_DIR"] = str(TMP)

from concordance import engagement as E  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402

CFG = EngineConfig("secular")


class Engaged(Exception):
    """A forbidden component was engaged."""


def _arm(monkeypatch, names):
    """Replace each `module.attr` / `module.Class.method` in `names` with a raiser that names itself."""
    import importlib
    for dotted in names:
        parts = dotted.split(".")
        mod = importlib.import_module("concordance." + parts[0])
        target = mod
        for a in parts[1:-1]:
            target = getattr(target, a)

        def raiser(*_a, _n=dotted, **_k):
            raise Engaged(_n)
        monkeypatch.setattr(target, parts[-1], raiser)


def _intent(name):
    return [i for i in E.INTENTS if i["intent"] == name][0]


def test_every_name_in_the_map_resolves_to_code():
    v = E.verify_names()
    assert v["ok"], v["missing"]
    assert v["intents"] == 7
    m = E.engagement_map()
    assert "every name resolves" in m["read"]


def test_check_engages_no_corpus_build_no_search_no_face_no_coach(monkeypatch):
    _arm(monkeypatch, _intent("CHECK")["must_not"])
    from concordance.audit import audit
    r = audit("the word strengths has 9 letters", CFG, seal=False, index=False, card=False)
    assert r["verdict"] == "HOLDS"
    r2 = audit("salary comes from Latin", CFG, seal=False, index=False, card=False)   # a shelf read, cold: declines
    assert r2["verdict"] == "INCOMPLETE"


def test_find_engages_no_verifier_no_seal_no_coach(monkeypatch):
    _arm(monkeypatch, _intent("FIND")["must_not"])
    from concordance import dictionary
    r = dictionary.define("strength")
    assert isinstance(r, dict)


def test_walk_engages_no_seal_no_ledger_no_coach(monkeypatch):
    _arm(monkeypatch, _intent("WALK")["must_not"])
    from concordance import ask
    r = ask.respond("I lost my job and I do not know what to do next", CFG)
    assert isinstance(r, dict) and r


def test_keep_engages_no_corpus_build_no_reverify_no_coach(monkeypatch):
    from concordance.derivation import verify_derivation
    res = verify_derivation([{"id": "s", "domain": "mathematics",
                              "spec": {"mode": "numeric", "params": {"numeric_expr": "2 + 2", "claimed_value": 4}}}])
    assert res["verdict"] == "HOLDS"
    _arm(monkeypatch, _intent("KEEP")["must_not"])
    from concordance import receipts
    out = receipts.attach(res, config=CFG, domain="mathematics", enabled=True, index=False, card=False)
    assert out.get("seal") and out["seal"].get("content_hash")


def test_word_engages_no_verifier_no_seal_no_face(monkeypatch):
    _arm(monkeypatch, _intent("WORD")["must_not"])
    from concordance.verifiers import scripture
    r = scripture.read_passage("John 3:16", None)
    assert isinstance(r, dict)


def test_learn_engages_no_search_no_verifier_no_seal_no_face(monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(TMP))     # another test module may have pointed the env elsewhere at import
    (TMP / "curriculum").mkdir(parents=True, exist_ok=True)
    (TMP / "curriculum" / "qe_en.json").write_text(json.dumps([{
        "id": "qe_1", "unit_seq": 1, "track": "t", "title": "t", "rule": "r", "examples": ["Estoy aquí."],
        "decodable_sentence": "Estoy aquí.", "modes": [],
        "check": {"prompt": "?", "answer": "Estoy aquí.", "choices": ["Estoy aquí.", "Estoy en la cama."], "teaching_note": "n"}}]),
        encoding="utf-8")
    from concordance import coach
    coach.reload()                                             # the subject list is discovered once; re-read it now that qe exists
    _arm(monkeypatch, _intent("LEARN")["must_not"])
    assert coach.check_answer("qe_1", "estoy aqui", "qe")["verdict"] == "correct"
    assert coach.check_answer("qe_1", "estoy en la cama", "qe")["verdict"] == "incorrect"


def test_operate_engages_no_corpus_build_no_verifier_no_seal(monkeypatch):
    _arm(monkeypatch, _intent("OPERATE")["must_not"])
    from concordance import systems
    r = systems.report()
    assert "receiver" in r and "engagement" in r and r["engagement"]["names"]["ok"]


def test_the_sentinels_bite():
    """The guard itself: an armed component raises by name, so a silent pass can never be a missing sentinel."""
    with pytest.MonkeyPatch.context() as mp:
        _arm(mp, ["corpus.default_corpus"])
        from concordance import corpus
        with pytest.raises(Engaged) as e:
            corpus.default_corpus()
        assert "corpus.default_corpus" in str(e.value)
