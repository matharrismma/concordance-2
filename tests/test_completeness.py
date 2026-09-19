"""Completeness sets — the structure must be complete, and every prediction cited (no hallucination).

The flagship is Chua's square: the four circuit variables, their six relations, and the memristor as
the one cell that was empty and predicted. This test pins the no-hallucination bar the seed's --check
enforces — a predicted cell must name who predicted it AND who confirmed it, and the relation table
must be the COMPLETE set of pairs.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import seed_completeness  # noqa: E402


def test_relation_tables_complete_and_predictions_cited():
    assert seed_completeness.check() == 0


def test_flagship_circuit_set_has_the_memristor_as_the_one_predicted_cell():
    s = next(x for x in seed_completeness.SETS if x["id"] == "circuit_variables")
    predicted = [r for r in s["relations"] if r["status"] == "predicted"]
    assert len(predicted) == 1, "exactly one empty cell — the memristor"
    m = predicted[0]
    assert set(m["pair"]) == {"φ", "q"}, "the predicted cell is the flux–charge relation"
    assert "memristor" in m["name"].lower()
    assert m.get("predicted") and m.get("confirmed"), "cite BOTH the prediction and its confirmation"


def test_every_historical_prediction_is_a_confirmed_result():
    assert seed_completeness.PREDICTIONS, "the class must not be empty"
    for p in seed_completeness.PREDICTIONS:
        assert p.get("confirmed"), f"{p.get('by')} prediction is not marked confirmed"


if __name__ == "__main__":
    import pytest
    sys.exit(int(pytest.main([__file__, "-q"])))
