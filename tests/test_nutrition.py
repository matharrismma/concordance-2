"""Unit-pin the nutrition verifier (A2, 2026-10-06). Macronutrient calories: 4/4/9 kcal per gram of
carb/protein/fat; 10 g each = 40+40+90 = 170 kcal. Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import nutrition as NU


def test_macronutrient_calories():
    assert NU.verify_macronutrient_calories({"carb_g": 10, "protein_g": 10, "fat_g": 10,
                                             "calories_claimed": 170}).status == "CONFIRMED"
    assert NU.verify_macronutrient_calories({"carb_g": 10, "protein_g": 10, "fat_g": 10,
                                             "calories_claimed": 100}).status == "MISMATCH"
    assert NU.verify_macronutrient_calories({}).status == "NOT_APPLICABLE"
