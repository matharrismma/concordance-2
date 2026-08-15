"""The PATH layer — the answer is a discerned path (type + ONE next step + a fitting anchor or none),
composed from what was found, never generated. The Lighthouse Model Spec's rule made testable:
'the output is always a path, never an answer', and 'John 3:16 as a default answer is a gate failure'
— so the anchor must FIT or be honestly absent. Pure (no corpus); the anchor resolver is stubbed.
"""
from concordance import path


def test_question_type_classifies_the_nine():
    cases = [
        ("how do I purify water", "found", "resource"),
        ("what does the Bible say about baptism", "", "doctrine"),
        ("when did World War 2 end", "", "historical"),
        ("should I take this job", "decision", "decision"),
        ("my marriage is falling apart", "", "relational"),
        ("how do I grow spiritually", "", "formation"),
        ("why does God allow suffering", "seeker", "wisdom"),
        ("I want to end my life", "crisis", "crisis"),
    ]
    for q, kind, want in cases:
        assert path.question_type(q, kind) == want, f"{q!r} ({kind}) -> {path.question_type(q, kind)} != {want}"


def test_compose_gives_type_framing_one_step_and_an_anchor(monkeypatch):
    # stub the canon resolver so the test is pure (no scripture data needed)
    monkeypatch.setattr(path, "_resolve", lambda ref: {"ref": ref, "text": "(the verse's own words)"})
    p = path.compose("how do I purify water", kind="found", subject="purify water",
                     lead={"title": "Making water safe to drink", "shelf": "survival"})
    assert p["type"] == "resource"
    assert p["framing"]
    assert "Making water safe to drink" in p["step"]        # the step points at real material
    assert p["anchor"] and p["anchor"]["ref"] == "John 4:14"  # a FITTING topical anchor (water)


def test_a_decision_walks_the_four_gates():
    p = path.compose("should I sell the farm", kind="decision")
    assert p["type"] == "decision"
    step = p["step"].upper()
    assert "RED" in step and "FLOOR" in step and "BROTHERS" in step and "GOD" in step


def test_wisdom_leads_with_the_word_not_a_retrieved_card(monkeypatch):
    # a life question ("how should I live") must NOT paste a random practical card onto its step —
    # that is the inverse of the Spec's named gate failure. With a fitting anchor: sit with the Word.
    monkeypatch.setattr(path, "_resolve", lambda ref: {"ref": ref, "text": "x"})
    p = path.compose("how should I live", kind="", lead={"title": "Infantry Live Fire", "shelf": "military"})
    assert p["type"] == "wisdom"
    assert "Infantry Live Fire" not in p["step"]              # the bad lead is refused
    # no fitting anchor -> Word + a brother, still never a bare card
    p2 = path.compose("how should I handle my anger", kind="", lead={"title": "Anger Card"})
    assert "Anger Card" not in p2["step"] and ("Word" in p2["step"] or "brother" in p2["step"])


def test_anchor_is_honestly_absent_when_nothing_fits(monkeypatch):
    monkeypatch.setattr(path, "_resolve", lambda ref: {"ref": ref, "text": "x"})
    # a subject with no word in the curated anchor map -> None, never a generic verse pasted on
    p = path.compose("how do I calibrate a spectrometer", kind="found", subject="calibrate spectrometer")
    assert p["anchor"] is None


def test_an_existing_answer_verse_becomes_the_anchor():
    a = path.anchor("comfort me", existing=[{"ref": "Psalm 34:18", "text": "The LORD is near…"}])
    assert a and a["ref"] == "Psalm 34:18"
