"""The field library (tools/card_survival.py) — outdoor/survival/homestead knowledge from PD
sources. Validate the carder's output CONTRACT without any corpus/data dependency: real topics
are covered, every source is public-domain/open, nothing is generated, and there are no orphans."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().parents[1] / "tools" / "card_survival.py"


def _load():
    spec = importlib.util.spec_from_file_location("card_survival", _PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # runs imports only; main() is guarded by __main__
    return mod


def test_covers_the_survival_priorities():
    mod = _load()
    boxes = {box for _slug, _t, box, *_ in mod.CARDS}
    for need in ("water", "fire", "shelter", "first_aid", "food", "navigation", "homestead"):
        assert need in boxes, f"the field library is missing a {need} card"
    assert len(mod.CARDS) >= 20, "the field library should be substantial"


def test_every_source_is_public_domain_or_open():
    mod = _load()
    for slug, title, box, src_label, *_ in mod.CARDS:
        low = src_label.lower()
        assert any(k in low for k in ("public domain", "usda", "cdc", "epa", "ready.gov",
                                      "u.s. army", "boy scouts", "hesperian", "woodcraft",
                                      "traditional")), f"{slug}: source not clearly PD/open: {src_label!r}"


def test_cards_are_gathered_not_generated_and_have_no_orphans():
    mod = _load()
    # exercise the real builder into a temp dir so we validate the emitted cards, not just the table
    import os
    import json
    import tempfile
    cwd = os.getcwd()
    d = tempfile.mkdtemp(prefix="nh-survival-")
    try:
        os.chdir(d)
        assert mod.main() == 0
        rows = [json.loads(ln) for ln in (Path(d) / "data" / "survival_cards.jsonl").read_text(encoding="utf-8").splitlines()]
    finally:
        os.chdir(cwd)
    assert len(rows) >= 22
    spine = next(c for c in rows if c["id"] == mod.SPINE)
    assert any(l["to_card_id"] == mod.FLOOR for l in spine["connections"]), "spine must root in the Floor"
    for c in rows:
        assert c.get("generated") is False, f"{c['id']} must not be generated"
        assert c.get("surface") == "secular"
        if c["id"] != mod.SPINE:
            assert any(l["to_card_id"] == mod.SPINE for l in c["connections"]), f"{c['id']} is an orphan"


def test_the_boundary_is_honest_about_its_limits():
    mod = _load()
    assert "not a substitute" in mod.BOUNDARY.lower()
    assert "training" in mod.BOUNDARY.lower()
