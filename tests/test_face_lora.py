"""face_lora.build_rows — one adapter per face, trained only on CITED lines (found, with a card) and the operator's
frames; nothing without a citation, nothing duplicated, the manner in every prompt. Runnable with pytest OR directly."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import face_lora  # noqa: E402


def test_rows_keep_citations_drop_uncited_and_duplicates_and_carry_the_manner():
    responses = [
        {"text": "Healthy soil grows healthy food; poor soil grows failure.", "card": "card_food_soil", "shelf": "food"},
        {"text": "healthy soil grows healthy food; poor soil grows failure.", "card": "card_dup", "shelf": "food"},   # duplicate (case)
        {"text": "A line with no card is not a found line.", "card": "", "shelf": "food"},                             # dropped
        {"text": "", "card": "card_empty"},                                                                             # dropped
    ]
    frames = ["You are not alone in it, and the walking is yours.", "", "You are not alone in it, and the walking is yours."]
    rows = face_lora.build_rows("face_gardener", responses, frames)
    assert [r["kind"] for r in rows] == ["found", "frame"]
    assert rows[0]["cite"] == "card_food_soil" and rows[1]["cite"] == "operator"
    assert all(r["face"] == "face_gardener" for r in rows)
    assert "the gardener" in rows[0]["prompt"].lower() and "soil" in rows[0]["prompt"].lower()   # the face's manner rides in the prompt
    assert rows[0]["completion"].startswith("Healthy soil")


def test_build_writes_one_train_file_per_face(tmp_path):
    (tmp_path / "faces" / "responses").mkdir(parents=True)
    (tmp_path / "faces" / "frames").mkdir(parents=True)
    (tmp_path / "faces" / "responses" / "face_coach.jsonl").write_text(
        '{"text": "The opening is the path: one next step.", "card": "card_playbook_the_game", "shelf": "playbook"}\n', encoding="utf-8")
    (tmp_path / "faces" / "frames" / "face_coach.txt").write_text("Keep going; the next step is enough.\n", encoding="utf-8")
    counts = face_lora.build(tmp_path, tmp_path / "lora")
    assert counts["face_coach"] == 2 and counts["face_bard"] == 0
    assert (tmp_path / "lora" / "face_coach" / "train.jsonl").exists()
    assert len(counts) == 18


if __name__ == "__main__":
    test_rows_keep_citations_drop_uncited_and_duplicates_and_carry_the_manner()
    print("ok (fixture test via pytest)")
