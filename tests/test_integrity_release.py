"""The integrity release (2026-11-23) — what a person RECEIVES, not only what the engine computes.

Two defects reached the public under a green suite, because the suite tested the engine and both lived in
the door:
  1. Four public renderers computed their own headline from the counts, so a PARTIAL was shown as HOLDS /
     "Every number checked out." / "Verified by Narrow Highway". The verdict is now the engine's, through one
     register (src/concordance/verdicts.py) every page carries a pinned copy of.
  2. The house ending was merged into the sealed record on GET /seal and seal_fetch, so the independent
     checker (tools/verify_seal.py) called every fetched receipt TAMPERED. A receipt is now served as sealed;
     its ending rides beside it (X-NH-House header / MCP result _meta).
Plus: the homepage presets are live fixtures — each declares data-expect and must return it.
"""
from __future__ import annotations

import hashlib
import html
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def _isolate():
    d = tempfile.mkdtemp(prefix="nh-integrity-")
    os.environ["CONCORDANCE_DATA_DIR"] = d
    os.environ.pop("CONCORDANCE_PUBLIC_BASE", None)
    return d


from concordance import doors, verdicts  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.mcp.server import handle  # noqa: E402
from concordance.web import api  # noqa: E402

SEC = EngineConfig("secular")
RENDERERS = ("site/verifier.html", "site/checkit.html", "site/com.html", "site/widget.js")
# every verdict a verify door can return (audit.py, derivation.py, the plain-claim door in web/api.py)
ENGINE_VERDICTS = {"HOLDS", "PARTIAL", "BROKEN", "INCOMPLETE", "NOTHING_TO_CHECK", "SYSTEM_ERROR", "QUARANTINE"}


def _canonical():
    spec = importlib.util.spec_from_file_location("verify_seal", ROOT / "tools" / "verify_seal.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.canonical_bytes


def _mint():
    st, p = api.dispatch("POST", "/verify", {}, {"mode": "equality", "params": {
        "expr_a": "2+2", "expr_b": "4", "variables": {}}}, SEC)
    assert st == 200 and p["verdict"] == "HOLDS" and p["seal"]["content_hash"]
    return p["seal"]["content_hash"]


# ── 2. RECEIPTS ARE SERVED AS SEALED ────────────────────────────────────────────────────────────────────
def test_get_seal_serves_the_record_byte_for_byte():
    _isolate()
    h = _mint()
    st, rec = api.dispatch("GET", "/seal", {"hash": h}, None, SEC)
    assert st == 200 and "house" not in rec
    assert hashlib.sha256(_canonical()(rec)).hexdigest() == h      # the independent checker agrees


def test_get_seal_keeps_its_ending_beside_the_record():
    _isolate()
    h = _mint()
    st, rec = api.dispatch("GET", "/seal", {"hash": h}, None, SEC)
    hdr = api.raw_house_header("/seal", st, rec, {"hash": h})
    assert hdr and set(hdr) == {"X-NH-House"}
    hdr["X-NH-House"].encode("ascii")                               # header-safe
    house = json.loads(hdr["X-NH-House"])
    assert house["door"] == "CHECK" and house["seal"] == h and house["next_step"]["tool"] == "verify"
    assert api.raw_house_header("/verify", 200, {"verdict": "HOLDS"}, {}) is None   # only raw routes
    assert api.raw_house_header("/seal", 404, {"error": "seal not found"}, {}) is None


def test_mcp_seal_fetch_serves_the_record_and_keeps_the_ending_in_meta():
    _isolate()
    h = _mint()
    r = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {"name": "seal_fetch", "arguments": {"hash": h}}}, SEC)
    res = r["result"]
    rec = json.loads(res["content"][0]["text"])
    assert "house" not in rec and hashlib.sha256(_canonical()(rec)).hexdigest() == h
    assert res["_meta"]["house"]["door"] == "CHECK" and res["isError"] is False


def test_other_doors_still_end_the_house_way():
    _isolate()
    st, p = api.dispatch("POST", "/verify", {"seal": "0"}, {"claim": "2+2=4"}, SEC)
    assert st == 200 and p["house"]["door"] == "CHECK"             # only the raw routes moved their ending
    assert doors.RAW_ROUTES <= set(doors.DOOR_ROUTES) and doors.RAW_TOOLS == {doors.DOOR_ROUTES[r] for r in doors.RAW_ROUTES}


# ── 1. EVERY RENDERER READS THE ENGINE'S VERDICT ────────────────────────────────────────────────────────
def _table(text):
    m = re.search(r"var NH_VERDICTS = (\{.*?\});", text)
    assert m, "no NH_VERDICTS table"
    return json.loads(m.group(1))


def test_the_register_covers_every_engine_verdict_and_never_promotes_an_unknown():
    assert set(verdicts.VERDICTS) >= ENGINE_VERDICTS
    assert all(t in verdicts.TONES for _, t in verdicts.VERDICTS.values())
    assert verdicts.VERDICTS["PARTIAL"][1] != "pass"                 # part checked is not a pass
    assert verdicts.headline("SOMETHING_NEW") == ["SOMETHING_NEW", "idle"]


def test_every_renderer_carries_the_register_exactly():
    for f in RENDERERS:
        text = (ROOT / f).read_text(encoding="utf-8")
        assert _table(text) == verdicts.VERDICTS, f"{f}: NH_VERDICTS differs from src/concordance/verdicts.py"
        assert re.search(r"NH_VERDICTS\[(d|res|report)\.verdict\]", text), f"{f} does not read the engine verdict"


def test_no_renderer_derives_a_verdict_from_counts_again():
    banned = [r'broken > 0 \? "DOES NOT HOLD"', r'"Every number checked out\."', r'broken>0\?"broken":"holds"',
              r"Verified by Narrow Highway", r"Your customer sees every number was verified",
              r"Sealed\. Every claim, every check"]
    for f in RENDERERS:
        text = (ROOT / f).read_text(encoding="utf-8")
        for b in banned:
            assert not re.search(b, text), f"{f} still carries {b!r}"


def test_renderers_show_what_was_not_checked():
    for f in RENDERERS:
        assert "unchecked_text" in (ROOT / f).read_text(encoding="utf-8"), f"{f} never shows the unchecked text"


# ── PRESETS ARE LIVE FIXTURES ───────────────────────────────────────────────────────────────────────────
def _presets():
    page = (ROOT / "site" / "verifier.html").read_text(encoding="utf-8")
    out = []
    for tag in re.findall(r"<button[^>]*\bdata-eg=\"[^\"]*\"[^>]*>", page):
        eg = re.search(r"\bdata-eg=\"([^\"]*)\"", tag).group(1)
        ex = re.search(r"\bdata-expect=\"([A-Z_]+)\"", tag)
        out.append((html.unescape(eg), ex.group(1) if ex else None))
    return out


def test_every_preset_declares_and_returns_its_verdict():
    _isolate()
    ps = _presets()
    assert len(ps) >= 4 and all(e for _, e in ps), ps
    assert {"HOLDS", "BROKEN", "PARTIAL"} <= {e for _, e in ps}      # the page shows each kind of answer
    for claim, expect in ps:
        st, p = api.dispatch("POST", "/verify", {"seal": "0"}, {"claim": claim}, SEC)
        assert st == 200 and p["verdict"] == expect, (claim, expect, p.get("verdict"))
        if expect == "PARTIAL":
            assert (p.get("coverage") or {}).get("unchecked_text"), "PARTIAL must name what it did not check"


def test_no_medication_dose_on_the_front_page():
    assert not any(re.search(r"\bmg/kg\b|\bdos(e|ed|age)\b", c, re.I) for c, _ in _presets())


if __name__ == "__main__":
    import inspect
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and inspect.isfunction(fn):
            fn()
            print("ok", name)
