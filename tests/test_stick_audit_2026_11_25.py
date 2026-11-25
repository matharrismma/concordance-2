"""THE STICK AUDIT (2026-11-25, Matt: "look for tick sticks. Also look for where we are missing a stick" ... "Build all
of it").

Read from the box's own ledger: 179 sticks, 1,404 marks. Found and fixed here:
  * DEAD LINKS - 40 stick ids that marks, cards and code name but no stick was minted under (shortened forms and older
    names). A minted mark cannot be edited, so GET /stick resolves them through src/concordance/stick_aliases.json;
    tickstick.read never does, so a mint cannot land on an alias.
  * STALE MARKS - the de Bruijn-Newman constant (Lambda = 0 now follows from the machine-checked Riemann hypothesis),
    the Weil stick's classical gap, and the Langlands stick's "geometric Langlands remains a web of conjectures"
    (proved in 2024): data/sticks/stale_marks_restated.json, marks minted beside them.
  * MISSING STICKS - the 3D Euler singularity, the generalized Riemann hypothesis, Markov chains and MCMC (named by
    the Monte Carlo stick, never minted): data/sticks/euler_blowup.json, grh.json, markov_chains.json.
"""
from __future__ import annotations

import json
import math
import os
import re
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TMP = Path(tempfile.mkdtemp(prefix="nh-stick-audit-"))

from concordance import tickstick as TS  # noqa: E402
from concordance.engine import EngineConfig  # noqa: E402
from concordance.web import api  # noqa: E402

ALIASES = json.loads((ROOT / "src" / "concordance" / "stick_aliases.json").read_text(encoding="utf-8"))["aliases"]


@pytest.fixture()
def keeping():
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = str(TMP)
    try:
        yield TMP
    finally:
        if prior is None:
            os.environ.pop("CONCORDANCE_DATA_DIR", None)
        else:
            os.environ["CONCORDANCE_DATA_DIR"] = prior


def _entry(name):
    return json.loads((ROOT / "data" / "sticks" / f"{name}.json").read_text(encoding="utf-8"))


def _golden_ids():
    out = set()
    for f in (ROOT / "tests" / "fixtures" / "tick_golden").glob("*.json"):
        out |= set(json.loads(f.read_text(encoding="utf-8")).get("sticks") or {})
    return out


def test_every_alias_names_a_real_stick_and_no_alias_is_one():
    ids = _golden_ids()
    assert len(ALIASES) == 40
    for dead, real in ALIASES.items():
        assert re.fullmatch(r"stick_[a-z0-9_]+", dead) and dead != real
        assert real in ids, (dead, real)                      # a stick some catalog entry creates
        assert dead not in ids, dead                          # an alias never shadows a stick
        assert real not in ALIASES, real                      # no chains: one hop
    assert ALIASES["stick_hilbert_polya"] == "stick_the_hilbert_polya_conjecture"
    assert ALIASES["stick_four_forces_under_alpha"] == "stick_the_fine_structure_constant"   # tools/tick.py forces


def test_get_stick_resolves_a_dead_id_and_says_so(keeping):
    cfg = EngineConfig()
    st, body = api.dispatch("POST", "/stick", {}, {"question": "The Hilbert-Polya conjecture"}, cfg)[:2]
    assert st == 200 and body["id"] == "stick_the_hilbert_polya_conjecture"
    st, body = api.dispatch("GET", "/stick", {"id": "stick_hilbert_polya"}, None, cfg)[:2]
    assert st == 200 and body["id"] == "stick_the_hilbert_polya_conjecture" and body["resolved_from"] == "stick_hilbert_polya"
    st, body = api.dispatch("GET", "/stick", {"id": "stick_the_hilbert_polya_conjecture"}, None, cfg)[:2]
    assert st == 200 and "resolved_from" not in body
    st, _ = api.dispatch("GET", "/stick", {"id": "stick_no_such_thing_anywhere"}, None, cfg)[:2]
    assert st == 404


def test_read_itself_never_resolves_an_alias(keeping):
    TS.create("The Hilbert-Polya conjecture")
    assert TS.read("stick_hilbert_polya")["ok"] is False      # the mint path reads ids create() returned, never aliases
    assert TS.alias("stick_hilbert_polya") == "stick_the_hilbert_polya_conjecture"
    assert TS.alias("stick_the_hilbert_polya_conjecture") is None


def test_the_de_bruijn_closed_mark_carries_its_qualifier_inside_what_the_fit_shows():
    marks = {st["question"]: st["marks"] for st in _entry("stale_marks_restated")["sticks"]}
    closed = [m for m in marks["The de Bruijn-Newman constant"] if m["kind"] == "closed"]
    assert len(closed) == 1
    shown = TS.fit({"ticks": closed})["open"]
    assert shown.startswith("CLOSED") and "machine-checked Lean proof" in shown and "no human-readable proof yet" in shown
    assert "Rodgers" in closed[0]["source"] and "Bruijn" in closed[0]["source"]
    lang = marks["The Langlands program"][0]["claim"]
    assert all(a in lang for a in ("2405.03599", "2405.03648", "2409.07051", "2409.08670", "2409.09856"))
    assert "stays open" in lang


def test_the_new_sticks_say_what_is_proved_and_what_is_not():
    euler = _entry("euler_blowup")["sticks"][0]
    assert all(m["kind"] != "closed" for m in euler["marks"])
    assert any("NOT YET" in m["claim"] and "independent build" in m["claim"] for m in euler["marks"])
    grh = _entry("grh")["sticks"][0]
    text = " ".join(m["claim"] for m in grh["marks"])
    assert all(m["kind"] != "closed" for m in grh["marks"])
    assert "machine-checked Lean proof" in text and "no human-readable proof yet" in text and "OPEN" in text
    mc = _entry("markov_chains")
    assert TS._slug(mc["sticks"][0]["question"]) == "markov_chains_and_mcmc"   # the id the Monte Carlo stick names


def test_the_markov_seals_are_the_arithmetic_they_claim():
    for s in _entry("markov_chains")["seals"]:
        got = eval(s["expr"], {"__builtins__": {}})            # plain arithmetic, no names
        assert math.isclose(got, s["value"], rel_tol=s["tol"]), (s["key"], got, s["value"])
