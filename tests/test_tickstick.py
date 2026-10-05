"""THE TICK STICK (2026-10-05) and its first mark. A stick holds an open question; a sealed tick must point at a
HOLDS verification in this keeping; a cited tick must name its source; a bound only ever goes further; the fit
says exactly what the ticks establish and no more. The Riemann mark: two independent counts of zeta's zeros."""
import json
import os
import tempfile
from pathlib import Path

import pytest

TMP = Path(tempfile.mkdtemp(prefix="nh-stick-"))
os.environ["CONCORDANCE_DATA_DIR"] = str(TMP)

from concordance import cas, tickstick  # noqa: E402
from concordance import verifiers  # noqa: E402
from concordance.engine import EngineConfig  # noqa: E402
from concordance.web import api  # noqa: E402


@pytest.fixture(autouse=True)
def _own_dir():
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = str(TMP)
    try:
        yield
    finally:
        if prior is None:
            os.environ.pop("CONCORDANCE_DATA_DIR", None)
        else:
            os.environ["CONCORDANCE_DATA_DIR"] = prior


def _sealed_holds() -> str:
    """A HOLDS record written straight into the scratch CAS (cas.store mints into the live corpus — not here)."""
    rec = {"schema_version": "2.0", "overall": "PASS", "verdict": "HOLDS", "claim": "test", "n": 1}
    h = cas.content_hash_of(rec)
    p = cas._record_path(TMP / "cas", h)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rec, sort_keys=True), encoding="utf-8")
    return h


def test_the_first_mark_counts_the_zeros_two_independent_ways():
    rs = verifiers.run_for_domain("number_theory", {"NUM_VERIFY": {"critical_line_height": 50, "claimed_zeros_on_line": 10}})
    r = [x for x in rs if x.name == "number_theory.critical_line"][0]
    assert r.status == "CONFIRMED" and r.data["zeros_on_line"] == 10 and r.data["zeros_in_strip"] == 10
    rs = verifiers.run_for_domain("number_theory", {"NUM_VERIFY": {"critical_line_height": 50, "claimed_zeros_on_line": 11}})
    assert [x for x in rs if x.name == "number_theory.critical_line"][0].status == "MISMATCH"
    rs = verifiers.run_for_domain("number_theory", {"NUM_VERIFY": {"critical_line_height": 5, "claimed_zeros_on_line": 0}})
    assert [x for x in rs if x.name == "number_theory.critical_line"][0].status == "ERROR"      # below the first zero


def test_a_stick_takes_sealed_marks_and_cited_marks_and_fits_no_further_than_they_go():
    r = tickstick.create("Riemann hypothesis", statement="Every non-trivial zero of zeta has real part 1/2.",
                         field="number_theory", references=["Riemann 1859"])
    assert r["ok"] and r["id"] == "stick_riemann_hypothesis" and r["existed"] is False
    assert tickstick.create("Riemann hypothesis")["existed"] is True
    sid = r["id"]
    # a sealed tick must point at a HOLDS verification in the keeping
    bad = tickstick.tick(sid, "bound", "all zeros up to T = 50 are on the line", seal="0" * 64, up_to=50, unit="height T")
    assert bad["ok"] is False and "not a HOLDS verification" in bad["error"]
    h = _sealed_holds()
    ok = tickstick.tick(sid, "bound", "all zeros up to T = 50 are on the line", seal=h, up_to=50, unit="height T")
    assert ok["ok"] and ok["fit"]["verified_up_to"]["up_to"] == 50 and "beyond height T 50" in ok["fit"]["open"]
    # a bound only goes further
    back = tickstick.tick(sid, "bound", "all zeros up to T = 40 are on the line", seal=h, up_to=40)
    assert back["ok"] is False and "must go further" in back["error"]
    on = tickstick.tick(sid, "bound", "all zeros up to T = 100 are on the line", seal=h, up_to=100, unit="height T")
    assert on["ok"] and on["fit"]["verified_up_to"]["up_to"] == 100 and [p["up_to"] for p in on["fit"]["progression"]] == [50, 100]
    # a cited tick needs its source; it never counts as sealed
    assert tickstick.tick(sid, "equivalence", "RH is equivalent to |pi(x) - li(x)| < sqrt(x) log x / (8 pi) for x >= 2657")["ok"] is False
    eq = tickstick.tick(sid, "equivalence", "RH is equivalent to |pi(x) - li(x)| < sqrt(x) log x / (8 pi) for x >= 2657",
                        source="Schoenfeld, Math. Comp. 30 (1976) 337-360")
    assert eq["ok"] and eq["fit"]["cited_ticks"] == 1 and eq["fit"]["sealed_ticks"] == 2
    st = tickstick.read(sid)
    assert st["ok"] and len(st["ticks"]) == 3 and st["fit"]["equivalent_statements"][0].startswith("RH is equivalent")
    assert "never says the question is settled" in st["fit"]["note"]
    assert tickstick.tick(sid, "miracle", "it is proven")["ok"] is False
    assert tickstick.read("stick_nope")["ok"] is False


def test_the_routes_open_read_and_mark_a_stick():
    cfg = EngineConfig()
    st, body = api.dispatch("POST", "/stick", {}, {"question": "P versus NP", "field": "computer_science"}, cfg)[:2]
    assert st == 200 and body["ok"] and body["id"] == "stick_p_versus_np"
    st, body = api.dispatch("POST", "/tick", {}, {"stick": "stick_p_versus_np", "kind": "exclusion",
                                                 "claim": "relativizing proof techniques cannot resolve P vs NP",
                                                 "source": "Baker, Gill, Solovay, SIAM J. Comput. 4 (1975) 431-442"}, cfg)[:2]
    assert st == 200 and body["ok"] and body["fit"]["excluded_approaches"] == ["relativizing proof techniques cannot resolve P vs NP"]
    st, body = api.dispatch("GET", "/stick", {"id": "stick_p_versus_np"}, None, cfg)[:2]
    assert st == 200 and body["fit"]["open"].startswith("no sealed bound yet")
    st, body = api.dispatch("GET", "/sticks", {}, None, cfg)[:2]
    assert st == 200 and body["count"] >= 2 and any(r["id"] == "stick_riemann_hypothesis" for r in body["sticks"])
    st, body = api.dispatch("POST", "/tick", {}, {"stick": "stick_p_versus_np", "kind": "bound", "claim": "x", "seal": "zz"}, cfg)[:2]
    assert st == 400
