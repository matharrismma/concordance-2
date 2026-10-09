"""THE MILLENNIUM SOURCES (Matt, 2026-10-09: "find all 17 and add them" / "find"; the loop's rule: anything retrieved
and used is included). Pins: every located source is carded by its RECORD under a license the mint gate accepts (no
share-alike, no non-commercial - the gate refuses at the mint, loud); every card is member_of the spine and the spine
part_of the Floor; ids are deterministic and unique; every want named is one the attempts opened; the one correction
(the FGHK want's wrong arXiv number) is RECORDED on the card, never silently applied; the two found tables are read by
tick.py's pure helpers exactly as sources_crosscheck reads them (the undocumented allbsd column order, proven by the
formula; the Riemann-von Mangoldt main term)."""
from __future__ import annotations

import json
import math
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="nh-mill-")
os.environ.setdefault("CONCORDANCE_DATA_DIR", TMP)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import card_millennium_sources as M  # noqa: E402
import tick as T  # noqa: E402

# the 11a rows and 37a1 as ecdata's allbsd.00000-09999 carries them (Artistic License 2.0, attributed)
ALLBSD = """11 a 1 [0,-1,1,-10,-20] 0 5 5 1.26920930427955 0.253841860855911 1.00000000000000 1
11 a 2 [0,-1,1,-7820,-263580] 0 1 1 0.253841860855911 0.253841860855911 1.00000000000000 1
11 a 3 [0,-1,1,0,0] 0 5 1 6.34604652139777 0.253841860855911 1.00000000000000 1
37 a 1 [0,0,1,-1,0] 1 1 1 5.98691729246392 0.305999773834052 0.0511114082399688 1.00000000000000
"""


def test_every_source_is_carded_under_an_accepted_license():
    cs = M.cards()
    assert len(cs) == len(M.SOURCES) >= 40
    assert len({c["id"] for c in cs}) == len(cs)
    for c in cs:
        assert c["kind"] == "reference" and c["generated"] is False and c["shelf"] == "millennium"
        assert c["connections"] == [{"to_card_id": M.SPINE, "relationship": "member_of",
                                     "evidence": c["connections"][0]["evidence"]}]
        assert "License as found:" in c["body"] and c["source"]["url"].startswith("http")
    sp = M.spine_card(len(cs))
    assert sp["connections"][0] == {"to_card_id": M.FLOOR, "relationship": "part_of",
                                    "evidence": sp["connections"][0]["evidence"]}


def test_the_gate_refuses_share_alike_and_non_commercial_at_the_mint():
    import pytest
    bad = dict(M.SOURCES[0], key="x_sa", license="CC BY-SA 4.0")
    with pytest.raises(ValueError):
        M.card(bad)
    bad = dict(M.SOURCES[0], key="x_nc", license="CC BY-NC 4.0")
    with pytest.raises(ValueError):
        M.card(bad)
    assert not M._license_ok("share-alike") and M._license_ok("CC BY 4.0") and M._license_ok("Artistic License 2.0")


def test_every_want_named_is_one_the_attempts_opened_and_builds_stay_open():
    wants = set(M.WANTS.values())
    for s in M.SOURCES:
        if s["problem"] == "joint":
            assert s["want"] == "", s["key"]            # a joint's record serves the one map, not a want
            continue
        assert s["want"] in wants, s["key"]
    assert M.BUILD_WANTS <= wants
    # a build want receives only a METHOD source - never a card that would close it as done
    for s in M.SOURCES:
        if s["want"] in M.BUILD_WANTS:
            assert s["kind"] == "method", s["key"]
            assert "not built" in s["role"] or "not done" in s["role"], s["key"]


def test_the_fghk_correction_is_recorded_not_silently_applied():
    c = M.card(next(s for s in M.SOURCES if s["key"] == "fghk_2016"))
    assert "1512.00334" in c["body"] and "astronomy" in c["body"] and "TR15-166" in c["body"]
    assert c["source"]["url"] == "https://doi.org/10.1109/FOCS.2016.19"


def test_the_two_tables_are_read_as_sources_crosscheck_reads_them():
    rows = T._read_allbsd(ALLBSD)
    assert set(rows) == {"11a1", "11a2", "11a3", "37a1"}
    # the column reading is PROVEN by the formula holding on every row's own numbers
    for key, d in rows.items():
        val = float(d["Omega"]) * d["c"] * int(float(d["Sha"])) / d["T"] ** 2 * (float(d["Reg"]) if d["r"] else 1.0)
        assert abs(val - float(d["L"])) / float(d["L"]) < 1e-10, key
    assert (rows["11a1"]["c"], rows["11a1"]["T"]) == (T.CURVES_BSD_INPUTS["11a1"]["tamagawa_product"],
                                                      T.CURVES_BSD_INPUTS["11a1"]["torsion_order"])
    assert abs(float(rows["37a1"]["Reg"]) - T.CURVES_BSD_INPUTS["37a1"]["regulator"]) < 1e-12
    # the Riemann-von Mangoldt main term: 649 zeros below 1000 is what the stick sealed; the term lands within |S(T)| < 1
    main = T._rvm_main_term(1000.0)
    assert abs(649 - main) < 1.0
    # and at Odlyzko's 100,000th zero (74920.827498994) the remainder S(T) is 0.595
    assert abs(100000 - T._rvm_main_term(74920.827498994) - 0.595) < 0.001
    assert math.isfinite(main)


def test_the_file_is_written_once_spine_first_and_never_shrinks():
    out = Path(os.environ["CONCORDANCE_DATA_DIR"]) / "millennium_cards.jsonl"   # the dir the tool honours
    sys.argv = ["card_millennium_sources.py"]
    assert M.main() == 0
    lines = out.read_text(encoding="utf-8").split("\n")
    assert json.loads(lines[0])["id"] == M.SPINE
    assert len([l for l in lines if l]) == len(M.SOURCES) + 1
    first = out.read_bytes()
    assert M.main() == 0 and out.read_bytes() == first          # idempotent: the same bytes
