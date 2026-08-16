"""FIELD PACK — a runnable, verifiable Lighthouse drop-in (FIELD-PACK-1).

Proves the packer selects the right slice, seals it, and that the CUT pack runs SELF-CONTAINED in a
clean subprocess (no PYTHONPATH to the repo) — verify passes, a question surfaces its field card, a
cry for help routes to real help, and the no-radio self-test verifies authentic.
"""
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

_TOOLS = Path(__file__).resolve().parent.parent / "tools"
_spec = importlib.util.spec_from_file_location("cut_field_pack", _TOOLS / "cut_field_pack.py")
cfp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cfp)

_HAVE_CRYPTO = importlib.util.find_spec("cryptography") is not None


def _write_fixture(d: Path):
    d.mkdir(parents=True, exist_ok=True)
    firstaid = [
        {"id": "fa-bleed", "title": "Stop bleeding fast", "shelf": "first_aid",
         "body": "Press hard on the wound with a clean cloth and do not let up.",
         "visibility": "public", "lifecycle_stage": "public", "source": {"label": "field"}},
        {"id": "fa-priv", "title": "Private draft", "body": "not for release",
         "visibility": "private", "lifecycle_stage": "draft"},
    ]
    (d / "firstaid_cards.jsonl").write_text("\n".join(json.dumps(c) for c in firstaid), encoding="utf-8")
    water = [{"id": "wa-purify", "title": "Purify water", "shelf": "water",
              "body": "Boil water for one minute to make it safe to drink.",
              "visibility": "public", "lifecycle_stage": "public", "source": {}}]
    (d / "water_cards.jsonl").write_text("\n".join(json.dumps(c) for c in water), encoding="utf-8")
    verses = [
        {"book": "John", "book_abbr": "JOH", "chapter": "14", "verse": "27",
         "text": "Peace I leave with you.", "translation": "WEB"},
        {"book": "Genesis", "book_abbr": "GEN", "chapter": "1", "verse": "1",
         "text": "In the beginning God created the heavens and the earth.", "translation": "WEB"},
    ]
    (d / "bible_en.jsonl").write_text("\n".join(json.dumps(v) for v in verses), encoding="utf-8")


def test_select_cards_filters_to_public_and_normalizes(tmp_path):
    data = tmp_path / "data"
    _write_fixture(data)
    cards = cfp.select_cards(data)
    ids = {c["id"] for c in cards}
    assert "fa-bleed" in ids and "wa-purify" in ids
    assert "fa-priv" not in ids                          # non-public is withheld
    assert "web-JOH-14-27" in ids                        # a verse, normalized
    john = next(c for c in cards if c["id"] == "web-JOH-14-27")
    assert john["title"] == "John 14:27" and john["shelf"] == "bible"
    for c in cards:                                      # every card has what the node needs
        assert c["id"] and c["title"] and c["body"]


def test_cut_produces_a_sealed_self_contained_pack(tmp_path):
    data = tmp_path / "data"
    _write_fixture(data)
    dest = tmp_path / "pack"
    cfp.cut(dest, data)
    for rel in ["run.py", "field_search.py", "crisis.py", "verify_pack.py", "requirements.txt",
                "README.md", "MANIFEST.json", "data/cards.jsonl", "code/concordance/__init__.py",
                "code/concordance/lighthouse_node.py", "code/concordance/meshtastic_bridge.py"]:
        assert (dest / rel).is_file(), rel
    man = json.loads((dest / "MANIFEST.json").read_text(encoding="utf-8"))
    assert man["counts"]["field_cards"] == 2 and man["counts"]["bible_verses"] == 2
    for f in man["files"]:                               # the seal holds
        assert hashlib.sha256((dest / f["path"]).read_bytes()).hexdigest() == f["sha256"], f["path"]


def test_the_frozen_crisis_test_matches_the_engine(tmp_path):
    data = tmp_path / "data"
    _write_fixture(data)
    dest = tmp_path / "pack"
    cfp.cut(dest, data)
    ns = {}
    exec((dest / "crisis.py").read_text(encoding="utf-8"), ns)   # load the frozen module
    assert ns["is_crisis"]("i want to end it all") is True
    assert ns["is_crisis"]("how do i cook rice") is False
    assert ns["normalize"]("I DON’T want to be here") == "i dont want to be here"  # smart quotes


@pytest.mark.skipif(not _HAVE_CRYPTO, reason="signing needs the cryptography library")
def test_the_cut_pack_runs_self_contained(tmp_path):
    data = tmp_path / "data"
    _write_fixture(data)
    dest = tmp_path / "pack"
    cfp.cut(dest, data)

    def run(*args):
        r = subprocess.run([sys.executable, *args], cwd=str(dest), capture_output=True)
        return (r.stdout + r.stderr).decode("utf-8", "replace"), r.returncode

    out, rc = run("verify_pack.py")
    assert rc == 0 and "VERIFIED" in out

    out, _ = run("run.py", "--ask", "how do i stop bleeding")
    assert "verified=True" in out and "bleeding" in out.lower()

    out, _ = run("run.py", "--ask", "i want to end it all")
    assert "988" in out                                  # a cry for help gets real help

    out, rc = run("run.py")                              # the no-radio self-test
    assert rc == 0 and "Field pack OK." in out and "authentic=True" in out
