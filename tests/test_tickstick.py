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
    # a note documents the attempt without counting toward the fit; it surfaces in the record, not the bound
    nt = tickstick.tick(sid, "note", "Method: two independent counts must agree before any bound is sealed.",
                        by="the record")
    assert nt["ok"] and nt["fit"]["record"][0]["claim"].startswith("Method:") and nt["fit"]["record"][0]["by"] == "the record"
    assert nt["fit"]["sealed_ticks"] == 2 and nt["fit"]["cited_ticks"] == 1   # the note counts as neither
    assert nt["fit"]["verified_up_to"]["up_to"] == 100 and nt["fit"]["progression"][-1]["seal"]   # bound + seal unchanged
    # the surviving window (narrow by elimination): a sealed bound makes it narrow numerically
    w = nt["fit"]["window"]
    assert w["narrows_numerically"] is True and any("no failure below" in e for e in w["eliminations"])
    assert "evade every elimination" in w["surviving"]
    # a stick with only cited barriers does not narrow numerically
    bar = tickstick.create("A barrier-only open question for the window test", field="logic")["id"]
    tickstick.tick(bar, "exclusion", "a relativizing argument cannot settle this question",
                   source="a cited barrier, 1975")
    bw = tickstick.read(bar)["fit"]["window"]
    assert bw["narrows_numerically"] is False and bw["eliminations"] and "barrier" in bw["note"]
    # a stick with sealed instances but no bound says so — the general question stays open
    r2 = tickstick.create("Birch and Swinnerton-Dyer conjecture", field="number_theory")
    inst = tickstick.tick(r2["id"], "instance", "E = 11a1: L(E,1) != 0 => rank 0 (Kolyvagin)", seal=h)
    assert inst["ok"] and inst["fit"]["verified_instances"] == 1 and "general question stays open" in inst["fit"]["open"]
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


def test_a_mark_keeps_its_full_text_and_a_cut_copy_is_superseded_by_its_fuller_self():
    """2026-10-08: the claim cap was 600, and 45 kept marks - the guard notes, mostly - were stored cut mid-sentence;
    a re-run could never match its own cut copy, so it added the note again. The cap is CLAIM_CAP (2000) now; a mark
    kept cut at the old cap is superseded in the reading by a later tick of the same kind and seal whose text begins
    with the whole cut text; an exact duplicate collapses onto its first copy. The file keeps every event (append-
    only); the reading shows each mark once, in full, and says how many it superseded."""
    r = tickstick.create("A long note is kept whole", statement="cap pin", field="test")
    sid = r["id"]
    full = ("[the guard] " + ("every word of this note is kept, up to the cap; " * 30)).strip()   # tick() strips
    assert 600 < len(full) < tickstick.CLAIM_CAP
    # the old store: the note cut at 600, twice (a re-run's duplicate), written as the old cap wrote it
    tickstick._append({"event": "tick", "stick": sid, "kind": "note", "claim": full[:600], "at": 1, "by": "old"})
    tickstick._append({"event": "tick", "stick": sid, "kind": "note", "claim": full[:600], "at": 2, "by": "old"})
    st = tickstick.read(sid)
    assert len(st["ticks"]) == 1 and st["superseded"] == 1 and len(st["ticks"][0]["claim"]) == 600
    assert tickstick.tick(sid, "note", full, by="new")["ok"]
    st = tickstick.read(sid)
    assert len(st["ticks"]) == 1 and st["ticks"][0]["claim"] == full and st["superseded"] == 2
    assert len(st["fit"]["record"]) == 1
    # a sealed witness the same way: the cut copy yields to the full one carrying the same seal
    h = _sealed_holds()
    w = ("[witness] " + ("sealed and kept whole; " * 40)).strip()
    tickstick._append({"event": "tick", "stick": sid, "kind": "witness", "claim": w[:600], "seal": h, "at": 3, "by": "old"})
    assert tickstick.tick(sid, "witness", w, seal=h, by="new")["ok"]
    st = tickstick.read(sid)
    ws = [x for x in st["ticks"] if x["kind"] == "witness"]
    assert len(ws) == 1 and ws[0]["claim"] == w and st["fit"]["witnesses"] == 1 and st["superseded"] == 3
    # a different mark that merely shares a prefix is NOT collapsed: only a strict extension of the whole cut text is
    assert tickstick.tick(sid, "note", "[the guard] but a different note", by="new")["ok"]
    assert len([x for x in tickstick.read(sid)["ticks"] if x["kind"] == "note"]) == 2
    # the cap itself: past CLAIM_CAP a claim is cut, and its length says so
    assert tickstick.tick(sid, "note", "x" * (tickstick.CLAIM_CAP + 100), by="new")["ok"]
    assert max(len(x["claim"]) for x in tickstick.read(sid)["ticks"]) == tickstick.CLAIM_CAP



def test_a_postulate_is_cited_never_a_fact_and_the_fit_says_inferred():
    """Matt, 2026-10-08: 'Think postulates. They work, so we don't keep them as fact, but we can make them work, so we
    can infer that truth is there.' A postulate is a cited kind (a source is required); the fit counts the sealed marks
    that work under it and says INFERRED, never proven."""
    sid = tickstick.create("Does the Born rule hold?", statement="Probability is the squared overlap.", field="physics",
                           references=["M. Born (1926)"])["id"]
    assert tickstick.tick(sid, "postulate", "The Born rule: the probability of an outcome is |<phi|psi>|^2")["ok"] is False  # no source
    r = tickstick.tick(sid, "postulate", "The Born rule: the probability of an outcome is |<phi|psi>|^2", source="M. Born (1926)")
    assert r["ok"] is True
    f = tickstick.read(sid)["fit"]
    assert f["postulates"] == ["The Born rule: the probability of an outcome is |<phi|psi>|^2"]
    assert "1 postulate(s) cited, 0 sealed mark(s)" in f["inferred"] and "inferred" in f["inferred"] and "proven" in f["inferred"]
    assert "fact" not in f["open"].split("never kept as fact")[0].split("never proven")[-1]   # the word fact appears only in the denial
    assert f["cited_ticks"] == 1 and f["sealed_ticks"] == 0
