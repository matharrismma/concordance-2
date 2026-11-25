"""THE RIEMANN HYPOTHESIS, PROVED; THE NAVIER-STOKES STICK, RESTATED (2026-11-25, Matt: "Go back to the sticks.
and then RH").

The Riemann hypothesis is proved - a machine-checked Lean proof (Alpoge, released 2026-11-20; statement and proof
certified by the Lean FRO and the Mathlib Initiative, 2026-11-21); no human-readable proof yet. The Navier-Stokes
stick's rounds 2 and 7 said Necas-Ruzicka-Sverak and Tsai leave only a Type-II singularity (they exclude an exactly
self-similar profile only), and rounds 3 and 7 read Tao (2019) backwards (his bound on the blow-up rate is from
below). A minted mark cannot be edited and an unsealed one cannot be retracted, so the corrections are new marks
minted beside them (data/sticks/riemann_proved.json, data/sticks/navier_stokes_restated.json); the cards are
corrected in their tracked seeds and, for the almanac card whose text is not ours to prove, by a cut-only row.

These pin the precision rule (the qualifier travels inside the text a label keeps), that the almanac row only cuts,
and that nothing these files now say calls RH open.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from concordance import card_corrections as C  # noqa: E402
from concordance import tickstick as TS  # noqa: E402
import seed_millennium_chain as M  # noqa: E402

# the old words a restated note quotes, inside quotation marks, so a reader sees what it restates
QUOTED_OLD = ("while the hypothesis itself stays open", "the Riemann hypothesis remains open",
              "the Riemann hypothesis itself stays open", "the classical RH stays open",
              "the classical RH stays the open mark")
RH_OPEN = re.compile(r"(?i)(riemann hypothesis|\bRH\b)[^.;]{0,40}\b(stays open|remains open|is open|unproven|still-open)")


def _entry(name):
    return json.loads((ROOT / "data" / "sticks" / f"{name}.json").read_text(encoding="utf-8"))


def _marks(entry):
    return [(st["question"], m) for st in entry["sticks"] for m in st["marks"]]


def test_the_closed_mark_carries_its_qualifier_inside_what_the_fit_shows():
    rh = _entry("riemann_proved")
    closed = [(q, m) for q, m in _marks(rh) if m["kind"] == "closed"]
    assert [q for q, _ in closed] == ["Riemann hypothesis"]
    mark = closed[0][1]
    shown = TS.fit({"ticks": [mark]})["open"]                  # "CLOSED - " + the first 200 characters
    assert shown.startswith("CLOSED")
    assert "machine-checked Lean proof" in shown and "no human-readable proof yet" in shown
    assert len(mark["source"]) >= 8 and "Lean FRO" in mark["source"]


def test_every_restated_note_says_proved_with_its_qualifier_and_never_open():
    for q, m in _marks(_entry("riemann_proved")):
        assert "machine-checked Lean proof" in m["claim"] and "no human-readable proof yet" in m["claim"], q
        rest = m["claim"]
        for quoted in QUOTED_OLD:
            rest = rest.replace("'" + quoted + "'", "")
        assert not RH_OPEN.search(rest), (q, RH_OPEN.search(rest).group(0))
    sticks = [st["question"] for st in _entry("riemann_proved")["sticks"]]
    assert sticks == ["Riemann hypothesis", "P versus NP", "The symmetry", "The final assembly"]


def test_the_navier_stokes_restatement_names_both_errors_and_keeps_the_question_open():
    ns = _entry("navier_stokes_restated")
    marks = _marks(ns)
    assert [q for q, _ in marks] == ["Navier-Stokes existence and smoothness"] * 2
    assert all(m["kind"] == "note" for _, m in marks)
    a, b = (m["claim"] for _, m in marks)
    assert "EXACTLY self-similar" in a and "not 'Type-II'" in a and "DISCRETELY" in a and "stays open" in a
    assert "LOWER bound" in b and "log log log" in b and "bounded below, not above" in b


def test_the_millennium_seed_no_longer_calls_rh_open():
    cards = {c["id"]: c for c in M.CARDS}
    for cid in ("card_floor_millennium", "card_question_riemann", "card_joint_weil_conjectures"):
        text = cards[cid]["title"] + " " + cards[cid]["body"]
        assert not RH_OPEN.search(text), (cid, RH_OPEN.search(text).group(0))
    q = cards["card_question_riemann"]["body"]
    assert "machine-checked Lean proof" in q and "no human-readable proof yet" in q
    floor = cards["card_floor_millennium"]
    assert "seven open questions" not in floor["title"] and "Poincare (Perelman 2002-2003)" in floor["body"]


def test_the_almanac_row_only_cuts_and_stores_no_text_of_the_card():
    rows = [r for r in C.table() if r["rule"] == "rh-proved-almanac-cut"]
    assert len(rows) == 1 and rows[0]["id"] == "card_alm_connection_riemann_hypothesis_open_zeta_facts"
    row = rows[0]
    assert "minted_by" not in row and [c["path"] for c in row["changes"]] == ["title", "subject", "body"]
    for ch in row["changes"]:
        assert "new" not in ch and "old" not in ch and len(ch["old_sha256"]) == 64
        assert ch["spans"] and all(rep == "" and 0 <= s < e for s, e, rep in ch["spans"])


def test_the_almanac_row_leaves_a_card_that_moved_on_exactly_as_it_is():
    row = [r for r in C.table() if r["rule"] == "rh-proved-almanac-cut"][0]
    card = {"id": row["id"], "title": "x", "subject": "y", "body": "z"}
    assert C.apply_one(card, [row]) == "mismatch"
    assert card == {"id": row["id"], "title": "x", "subject": "y", "body": "z"}
