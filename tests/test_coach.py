"""Coach — the K-3 reading tutor that grows with the student.

Proves: the 35 units load VERBATIM from the ported curriculum; next_unit is deterministic (stable
order, first/after/last); the child-grading guardrail refuses; every response carries generated:false;
and the mastery helper's honest integer count seals via the PUBLIC receipts helper (the SAME path
steward's budget uses) WITHOUT importing verifiers/derivation.

Hermetic: writes a curriculum + seal store into a fresh temp CONCORDANCE_DATA_DIR, ported by the real
migrate_school from the real 1.0 school.html. Runnable with pytest OR directly (python tests/test_coach.py).
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))  # so `import tools.migrate_school` resolves

# Isolate all runtime data (curriculum + CAS/ledger for the seal) into a throwaway dir.
_DATA = tempfile.mkdtemp(prefix="nh-coach-")
os.environ["CONCORDANCE_DATA_DIR"] = _DATA

from concordance import coach  # noqa: E402
from concordance import receipts  # noqa: E402  (the public seal helper — same one steward's endpoint uses)
from concordance.config import EngineConfig  # noqa: E402
from tools import migrate_school  # noqa: E402

SEC = EngineConfig("secular")

# The 1.0 school.html is the verbatim source of the curriculum.
_SCHOOL = Path("C:/Users/hdven/OneDrive/Documents/Claude/Projects/Lighthouse/site/school.html")


def _ensure_curriculum() -> int:
    """Port the curriculum into the temp data dir (verbatim), like the migrator does in prod."""
    out = coach._file()
    if not out.exists():
        migrate_school.build(_SCHOOL, out)
    return coach.reload()


def test_units_load_verbatim_35():
    n = _ensure_curriculum()
    assert n == 35, f"expected 35 units, loaded {n}"
    ov = coach.overview()
    assert ov["count"] == 35
    assert ov["generated"] is False
    # VERBATIM: the raw JSON on disk equals what the migrator extracted from school.html — no rewording.
    raw = json.loads(coach._file().read_text(encoding="utf-8"))
    src_units = migrate_school.extract_units(_SCHOOL.read_text(encoding="utf-8"))
    assert raw == src_units, "curriculum on disk is not a verbatim copy of the source array"
    assert len(raw) == 35


def test_unit_returns_authored_fields_verbatim():
    _ensure_curriculum()
    ov = coach.overview()
    first_id = ov["units"][0]["id"]
    u = coach.unit(first_id)
    assert u["kind"] == "coach_unit"
    assert u["generated"] is False
    # The unit dict carries the operator's authored fields unchanged (e.g. rule/examples exist).
    src = {x["id"]: x for x in migrate_school.extract_units(_SCHOOL.read_text(encoding="utf-8"))}
    for k, v in src[first_id].items():
        assert u[k] == v, f"field {k!r} was altered — not verbatim"
    # Unknown id never guesses.
    nf = coach.unit("no_such_unit_xyz")
    assert nf["kind"] == "coach_unit_not_found" and nf["generated"] is False


def test_next_unit_deterministic():
    _ensure_curriculum()
    order = [b["id"] for b in coach.overview()["units"]]
    # Stable + reproducible: two calls give the identical order.
    assert order == [b["id"] for b in coach.overview()["units"]]
    # next(None) -> the first unit in the stable order.
    first = coach.next_unit(None)
    assert first["kind"] == "coach_next"
    assert first["unit"]["id"] == order[0]
    assert first["position"] == 1 and first["of"] == 35
    assert first["generated"] is False
    # Walking after each id yields exactly the next id in order — the whole chain, deterministically.
    for i in range(len(order) - 1):
        nx = coach.next_unit(order[i])
        assert nx["kind"] == "coach_next"
        assert nx["unit"]["id"] == order[i + 1], f"after {order[i]} expected {order[i+1]}"
        assert nx["position"] == i + 2
    # Past the last unit -> complete, not a guess.
    last = coach.next_unit(order[-1])
    assert last["kind"] == "coach_complete" and last["generated"] is False
    # Unknown anchor -> points back to the map, never fabricates.
    unk = coach.next_unit("not_a_real_id")
    assert unk["kind"] == "coach_next_unknown_anchor" and unk["generated"] is False


def test_coach_guardrail_refuses_to_grade_a_child():
    for q in ("Is my kid behind in reading?",
              "What grade level is my daughter?",
              "what reading level is he at",
              "is my child slow compared to other kids",
              "grade my kid for me"):
        g = coach.coach_guardrail(q)
        assert g is not None, f"guardrail failed to catch: {q!r}"
        assert g["kind"] == "grade_declined"
        assert g["generated"] is False
        assert "point_to" in g and g["point_to"], "must point to the adult + real help"
        # NEVER a model verdict on the child.
        msg = g["message"].lower()
        assert "grade" in msg or "rank" in msg or "label" in msg
    # A normal teaching request is NOT tripped.
    assert coach.coach_guardrail("what is the next lesson?") is None
    assert coach.coach_guardrail("show me the short-a unit") is None


def test_mastery_counts_honestly_and_seals_via_receipts():
    _ensure_curriculum()
    order = [b["id"] for b in coach.overview()["units"]]
    # Honest count: real ids counted, duplicates collapsed, bogus ids ignored — no inflation.
    completed = [order[0], order[1], order[0], "bogus_id_not_real"]
    m = coach.mastery(completed)
    assert m["kind"] == "coach_mastery"
    assert m["completed_count"] == 2, "count must be the honest, de-duplicated, existence-checked int"
    assert m["of"] == 35
    assert m["generated"] is False
    # The receipts-ready result is a well-formed HOLDS derivation shape.
    mr = coach.mastery_result(completed)
    assert mr["count"] == 2
    res = mr["result"]
    assert res["verdict"] == "HOLDS" and res["confirmed_steps"] == res["steps"] == 1
    # Seal it the SAME way steward's endpoint does: receipts.attach on the result. A real, re-fetchable
    # seal must be minted (ok path) — proving the moat's math applies to progress, not the person.
    sealed = receipts.attach(res, config=SEC, domain="mathematics")
    assert sealed.get("seal") is not None, f"seal not minted: {sealed.get('seal_error')}"
    assert sealed["seal"]["content_hash"]
    assert sealed["seal"]["cite_url"].endswith(sealed["seal"]["content_hash"])


def test_no_import_of_verifiers_or_derivation():
    """Guardrail (b): coach.py must not IMPORT from verifiers/derivation — seal only via receipts.

    Parse the module's AST and inspect real import statements (prose in the docstring that names the
    forbidden modules to explain the boundary is fine; an actual import is not)."""
    import ast
    src = (ROOT / "src" / "concordance" / "coach.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            bad += [n.name for n in node.names if "verifiers" in n.name or "derivation" in n.name]
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if "verifiers" in mod or "derivation" in mod:
                bad.append(mod)
    assert not bad, f"coach.py imports forbidden modules: {bad}"
    # And it DOES lean on the public seal helper (documented intent).
    assert "receipts" in src


def test_guidance_states_the_boundary():
    g = coach.guidance()
    assert g["generated"] is False
    joined = " ".join(g["will_not"]).lower()
    assert "grade" in joined and "generate" in joined


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
        passed += 1
    print(f"\ncoach: {passed}/{len(fns)} passed")
    return passed == len(fns)


if __name__ == "__main__":
    raise SystemExit(0 if _run_all() else 1)
