#!/usr/bin/env python3
"""Nutrition floor on the one map (Matt, 2026-10-10, down the list). Uses tools/_seedlib.py.
    PYTHONPATH=src python tools/seed_nutrition.py [--check]
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _seedlib as L

FLOOR = "card_floor_nutrition"
STICK = "stick_nutrition_the_body_s_fuel_counted"
PILLARS = [
    dict(key="calories", title="Calories — energy is heat",
         body="Carbohydrate and protein give 4 kcal/g, fat 9; a meal's calories add up by the Atwater factors "
              "(sealed). A calorie is the heat the food releases when burned - nutrition is oxidation chemistry.",
         rests=[("card_floor_chemistry", "the calorie is heat; metabolism is oxidation chemistry")]),
    dict(key="macronutrients", title="Macronutrients — the body burns and stores",
         body="Fat packs 2.25 times the energy of carbohydrate (sealed), so the body stores energy as fat and burns "
              "carbohydrate first. Proteins also build tissue, not just fuel.",
         rests=[("card_floor_biology", "the body metabolizes, stores and builds - macronutrients in biology")]),
    dict(key="health", title="Health — diet and the body",
         body="Diet bears on health - deficiency, excess, disease. The engine seals the arithmetic of energy and "
              "macronutrients; it does not prescribe a diet, a clinical call, declined.",
         rests=[("card_floor_medicine", "diet and health - the clinical call is declined")]),
]
CARDS, BRIDGES, known_nodes, _validate, main = L.make(
    "nutrition", FLOOR, "card_spine_nutrition", STICK,
    "Nutrition — the body's fuel, counted",
    ("Food energy is carbohydrate and protein at 4 kcal/g and fat at 9; a calorie is heat; the body burns and "
     "stores. Three pillars rest on chemistry (metabolism is oxidation), biology (the body) and medicine (health). "
     "The engine seals the arithmetic and declines the dietary prescription. The stick (" + STICK + ") seals a "
     "meal's calories and fat's energy density over carbohydrate (tools/seed_nutrition.py)."),
    PILLARS, "the body's fuel on the one map, rooted in the Floor of Discovery",
    ["seed_chemistry", "seed_biology", "seed_medicine"])

if __name__ == "__main__":
    raise SystemExit(main())
