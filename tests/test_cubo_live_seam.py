"""THE LIVE SEAM WITH CUBO (Matt's standalone language coach; reviewed 2026-10-08). The live coach judges the way
Cubo judges: accent-insensitive, the kana voicing marks and the tilde of ñ kept, Japanese punctuation and spaces
folded, exact or the whole answer inside the reply — never a fragment. The authored distractor choices, which Cubo's
export drops, are carried into the curriculum so a known wrong turn is taught instead of called "unclear"."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="nh-seam-"))
os.environ["CONCORDANCE_DATA_DIR"] = str(TMP)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from concordance import coach  # noqa: E402


def _unit(uid, seq, answer, choices, track="cubo_qq"):
    return {"id": uid, "unit_seq": seq, "track": track, "title": uid, "rule": "r", "examples": [answer],
            "decodable_sentence": answer, "modes": [],
            "check": {"prompt": "Which one is true?", "answer": answer, "choices": choices, "teaching_note": "note"}}


def _write_subject(code, units):
    d = TMP / "curriculum"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{code}_en.json").write_text(json.dumps(units, ensure_ascii=False), encoding="utf-8")


def test_the_answer_law_matches_cubo():
    n = coach._norm_answer
    assert n("estoy aqui") == n("Estoy aquí.")                       # accents optional
    assert n("Fui para a porta!") == n("fui para a porta")
    assert n("año") != n("ano")                                        # ñ is a letter
    assert n("がっこう") != n("かっこう")                                # voicing is phonemic
    assert n("ここにいます") == n("ここに います。")                     # no word spaces in kana; 。 folded
    assert n("テーブルに パンが あります。") == n("テーブルにパンがあります")
    assert n("Daidokoro ni imasu.") == "daidokoro ni imasu"
    assert coach._whole(n("Fui para a porta."), n("sim, fui para a porta"))
    assert not coach._whole(n("Fui para a porta."), n("porta"))      # a fragment is not the answer
    assert coach._whole(n("ここに います。"), n("はい、ここにいます"))


def test_check_answer_exact_or_whole_never_a_fragment_and_teaches_the_known_wrong_turn():
    _write_subject("qq", [
        _unit("qq_ir", 1, "Fui para a porta.", ["Fui para a porta.", "Vou para a porta.", "Depois vou para a porta."]),
        _unit("qq_estoy", 2, "Estoy aquí.", ["Estoy aquí.", "Estoy en la cama."]),
        _unit("qq_imasu", 3, "ここに います。", ["ここに います。", "くるまに います。"]),
    ])
    C = lambda uid, a: coach.check_answer(uid, a, "qq")["verdict"]  # noqa: E731
    assert C("qq_ir", "fui para a porta") == "correct"
    assert C("qq_ir", "Fui para a porta!") == "correct"
    assert C("qq_ir", "sim, fui para a porta") == "correct"           # the whole answer inside the reply
    assert C("qq_ir", "porta") == "unclear"                           # the live seam's false match, closed
    assert C("qq_ir", "Vou para a porta.") == "incorrect"             # a known wrong turn, taught
    assert C("qq_ir", "utterly unrelated words") == "unclear"
    assert C("qq_estoy", "estoy aqui") == "correct"                   # Cubo's law honored live
    assert C("qq_estoy", "estoy en la cama") == "incorrect"
    assert C("qq_imasu", "ここにいます") == "correct"
    assert C("qq_imasu", "くるまにいます") == "incorrect"
    r = coach.check_answer("qq_ir", "Vou para a porta.", "qq")
    assert r["teaching_note"] == "note" and r["correct_answer"] == "Fui para a porta."


def test_ingest_carries_the_authored_choices_from_the_bucket_files():
    import ingest_cubo as IC
    assert IC.CURR == TMP / "curriculum"                               # honours CONCORDANCE_DATA_DIR
    (TMP / "curriculum" / "cubo").mkdir(parents=True, exist_ok=True)
    u = _unit("zz_estoy", 1, "Estoy en la cocina.", [], track="cubo_zz")
    del u["check"]["choices"]                                          # the export's shape: no choices
    (TMP / "curriculum" / "cubo" / "coach_export_zz.json").write_text(
        json.dumps({"kind": "coach_tracks", "subject": "zz", "units": [u]}, ensure_ascii=False), encoding="utf-8")
    src = TMP / "cubo_src" / "corpus" / "zz"
    src.mkdir(parents=True)
    b = _unit("zz_estoy", 1, "Estoy en la cocina.", ["Estoy en la cocina.", "Estoy en la cama."], track="cubo_zz")
    (src / "bucket1.json").write_text(json.dumps({"subject": "zz", "track": "cubo_zz", "units": [b]}, ensure_ascii=False), encoding="utf-8")
    sys.argv = ["ingest_cubo.py", "--choices-from", str(TMP / "cubo_src")]
    assert IC.main() == 0
    got = json.loads((TMP / "curriculum" / "zz_en.json").read_text(encoding="utf-8"))
    assert got[0]["check"]["choices"] == ["Estoy en la cocina.", "Estoy en la cama."]
    assert IC.main() == 0                                              # idempotent: a second run changes nothing
    again = json.loads((TMP / "curriculum" / "zz_en.json").read_text(encoding="utf-8"))
    assert again == got
