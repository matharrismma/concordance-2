"""The Apothecary — living-with-the-land wisdom, kept honestly.

What these tests guard: the shelf is found-never-generated, safety and evidence travel with
every entry, search discerns how people actually name their trouble, and offered wisdom is
WRITTEN but never published — the keeper curates; nothing publishes itself.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Two isolation rules at once (SOP-11):
#  - script mode (the droplet gate has no pytest): DATA_DIR must be a temp dir, or the propose
#    test WRITES INTO THE PRODUCTION QUEUE — that happened; the keeper found test entries.
#  - pytest mode: DATA_DIR belongs to whichever file imported last, so the shelf is pinned by
#    its own override, and the queue test asks the module where the queue lives at call time.
import tempfile
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-apoth-")
os.environ["CONCORDANCE_HERBS"] = str(
    Path(__file__).resolve().parent.parent / "data" / "herbs" / "monographs.jsonl")

from concordance import apothecary  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402

SEC = EngineConfig("secular")


def test_the_shelf_loads_the_revived_monographs():
    b = apothecary.browse()
    assert b["ok"] and b["total"] == 12
    names = {h["name"] for h in b["herbs"]}
    assert {"Ginger", "Chamomile", "Garlic", "Honey"} <= names


def test_safety_travels_with_every_listing():
    """A remedy without its cautions is a rumor. Even the list row carries the first caution."""
    for h in apothecary.browse()["herbs"]:
        assert "safety_notes" in h, h["name"]


def test_search_discerns_how_people_name_their_trouble():
    cases = {"trouble sleeping": "Chamomile",   # 'sleeping' meets 'sleep' at the stem
             "anxious": "Chamomile",            # folded to the monographs' word: anxiety
             "nausea": "Ginger",
             "when to plant": None}             # planting questions belong here too
    for q, want in cases.items():
        names = [r["name"] for r in apothecary.search(q)["results"]]
        assert names, f"nothing for {q!r}"
        if want:
            assert want in names, (q, names)


def test_an_absent_thing_is_an_honest_empty():
    """'tincture' is genuinely not in these 12 monographs — the shelf must say so rather
    than pad the answer."""
    assert apothecary.search("tincture")["results"] == []


def test_a_monograph_carries_its_evidence_and_growing():
    h = apothecary.get("herb_chamomile")["herb"]
    assert h["evidence_verdicts"] and h["growing"] and h["safety_notes"]


def test_offered_wisdom_is_written_but_never_published():
    """The write side: the proposal lands in the queue file — and no read surface ever
    shows it. The keeper curates; nothing publishes itself."""
    r = apothecary.propose("Plantain leaf poultice for bee stings — chew and apply.",
                           name="Plantain poultice")
    assert r["ok"]
    qfile = apothecary._data_dir() / "apothecary_proposals" / "proposals.jsonl"
    assert qfile.exists()
    assert "Plantain" in qfile.read_text(encoding="utf-8")
    blob = json.dumps(apothecary.browse()) + json.dumps(apothecary.search("plantain"))
    assert "poultice for bee stings" not in blob, "a proposal surfaced without curation"


def test_empty_and_oversized_offers_are_refused():
    assert apothecary.propose("")["ok"] is False
    assert apothecary.propose("x" * 9000)["ok"] is False


def test_the_endpoints_serve_the_shelf():
    st, b = dispatch("GET", "/apothecary", {}, None, SEC)
    assert st == 200 and b["total"] == 12
    st, s = dispatch("GET", "/apothecary", {"q": "sore throat"}, None, SEC)
    assert st == 200 and any(r["name"] == "Honey" for r in s["results"])
    st, g = dispatch("GET", "/apothecary", {"id": "herb_ginger"}, None, SEC)
    assert st == 200 and g["herb"]["name"] == "Ginger"
    assert dispatch("GET", "/apothecary", {"id": "herb_nonsense"}, None, SEC)[0] == 404
    st, p = dispatch("POST", "/apothecary/propose", {}, {"text": "rosemary for memory"}, SEC)
    assert st == 200 and p["ok"]
    assert dispatch("POST", "/apothecary/propose", {}, {}, SEC)[0] == 400


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} apothecary tests passed — found never generated; safety travels; "
          "the keeper curates.")
