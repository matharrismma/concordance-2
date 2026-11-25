"""THE STATUS DOOR (2026-11-25, Matt: "build the status door").

"The Riemann hypothesis has been proved" holds nothing an extractor can compute, so /verify said NOTHING_TO_CHECK while
the keeping charts that very question on a tick stick. Now the stick answers: GET /status?q=..., and the verify
fallback on both doors - CITED, the stick's own reading, never a computed verdict, never a receipt. Only a question
named plainly is seated; no bare acronym ("RH" is also relative humidity, "BSD" a licence).
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

TMP = Path(tempfile.mkdtemp(prefix="nh-status-"))

from concordance import doors, factfind, status, tickstick as TS  # noqa: E402
from concordance.engine import EngineConfig  # noqa: E402
from concordance.web import api  # noqa: E402

CLOSED_CLAIM = ("Every non-trivial zero of the Riemann zeta function has real part 1/2: PROVED - a machine-checked Lean "
                "proof (L. Alpoge, released 2026-11-20); no human-readable proof yet.")


@pytest.fixture()
def keeping():
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = str(TMP)
    if not TS.fold(TMP).get("stick_riemann_hypothesis"):
        TS.create("Riemann hypothesis", "Every non-trivial zero of the Riemann zeta function has real part 1/2.",
                  "number_theory", data_dir=TMP)
        TS.tick("stick_riemann_hypothesis", "closed", CLOSED_CLAIM, source="L. Alpoge, Lean proof (2026-11-20)", data_dir=TMP)
        TS.create("P versus NP", "Is every problem whose solutions can be verified quickly also solvable quickly?",
                  "computer_science", data_dir=TMP)
        TS.tick("stick_p_versus_np", "exclusion", "relativizing proof techniques cannot resolve P vs NP",
                source="Baker, Gill, Solovay, SIAM J. Comput. 4 (1975) 431-442", data_dir=TMP)
    try:
        yield TMP
    finally:
        if prior is None:
            os.environ.pop("CONCORDANCE_DATA_DIR", None)
        else:
            os.environ["CONCORDANCE_DATA_DIR"] = prior


@pytest.mark.parametrize("text, sid", [
    ("The Riemann hypothesis has been proved", "stick_riemann_hypothesis"),
    ("Riemann's hypothesis is still open", "stick_riemann_hypothesis"),
    ("the generalized Riemann hypothesis holds for Dirichlet L-functions", "stick_generalized_riemann_hypothesis"),
    ("the Riemann hypothesis over finite fields is a theorem", "stick_finite_field_the_weil_riemann_hypothesis"),
    ("Deligne proved the Weil conjectures", "stick_finite_field_the_weil_riemann_hypothesis"),
    ("the de Bruijn-Newman constant is zero", "stick_the_de_bruijn_newman_constant"),
    ("the Hilbert-Polya conjecture", "stick_the_hilbert_polya_conjecture"),
    ("Perelman proved the Poincaré conjecture", "stick_poincare_conjecture"),
    ("Is P = NP?", "stick_p_versus_np"),
    ("P versus NP is solved", "stick_p_versus_np"),
    ("Navier-Stokes blows up", "stick_navier_stokes_existence_and_smoothness"),
    ("the 3D Euler equations blow up in finite time", "stick_3d_euler_equations_finite_time_singularity"),
    ("the Yang-Mills mass gap is proved", "stick_yang_mills_existence_and_mass_gap"),
    ("the Hodge conjecture is false", "stick_hodge_conjecture"),
    ("the Birch and Swinnerton-Dyer conjecture", "stick_birch_and_swinnerton_dyer_conjecture"),
    ("the Jacobian conjecture fails in dimension three", "stick_the_jacobian_conjecture"),
    ("the Langlands program", "stick_the_langlands_program"),
])
def test_a_question_named_plainly_seats_its_stick(text, sid):
    assert status.match(text) == sid


@pytest.mark.parametrize("text", [
    "RH is proved", "the relative humidity, RH 45%, damages wood", "the BSD licence is permissive",
    "Euler's formula V - E + F = 2", "the Euler-Lagrange equations", "the mass of the gap is 4 kg",
    "the area of a circle of radius 2 is 12.566", "",
])
def test_no_bare_acronym_or_neighbour_seats_a_stick(text):
    assert status.match(text) is None


def test_every_named_stick_id_is_unique():
    ids = [sid for sid, _ in status.NAMED]
    assert len(ids) == len(set(ids))


def test_a_closed_stick_reads_closed_with_its_mark_and_an_open_one_open(keeping):
    st = status.status_of("The Riemann hypothesis has been proved", keeping)
    assert st["status"] == "CLOSED" and st["kind"] == "CITED" and st["link"] == "/stick?id=stick_riemann_hypothesis"
    assert st["closed_by"]["claim"] == CLOSED_CLAIM and "Lean" in st["closed_by"]["source"]
    assert "not a computed verdict" in st["means"] and "machine-checked" in status.sentence(st)
    op = status.status_of("Is P = NP?", keeping)
    assert op["status"] == "OPEN" and "closed_by" not in op and op["held"]["excluded_approaches"] == 1
    assert status.status_of("the Hodge conjecture", keeping) is None         # named, but not on this node


def test_the_verify_fallback_answers_with_the_stick(keeping):
    out = factfind.verify_fallback("The Riemann hypothesis has been proved", search=lambda q, limit=3: [])
    assert out["status"]["status"] == "CLOSED" and out["found"] == []
    assert "reads CLOSED" in out["note"] and "not a computed verdict" in out["note"] and "want" not in out
    end = doors.house("verify", {"verdict": "NOTHING_TO_CHECK", **out}, {"claim": "x"})
    assert end["next_step"]["web"] == "/stick?id=stick_riemann_hypothesis" and end["next_step"]["door"] == "FIND"


def test_the_verify_fallback_is_unchanged_for_a_question_no_stick_names(keeping):
    out = factfind.verify_fallback("the best recipe for bread", search=lambda q, limit=3: [])
    assert "status" not in out


def test_get_status_reads_the_stick_and_never_echoes_the_words(keeping):
    cfg = EngineConfig()
    st, body = api.dispatch("GET", "/status", {"q": "the Riemann hypothesis, my-secret-word"}, None, cfg)[:2]
    assert st == 200 and body["found"] and body["status"] == "CLOSED" and body["stick"] == "stick_riemann_hypothesis"
    assert body["house"]["next_step"]["web"] == "/stick?id=stick_riemann_hypothesis"
    assert "my-secret-word" not in str(body)
    st, body = api.dispatch("GET", "/status", {"q": "the best recipe for bread"}, None, cfg)[:2]
    assert st == 200 and body["found"] is False and "bread" not in str(body)
    st, _ = api.dispatch("GET", "/status", {}, None, cfg)[:2]
    assert st == 400
