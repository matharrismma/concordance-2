"""SYSTEM_ERROR is not BROKEN — our failure is never reported as the caller's falsehood.

Contract §5.6 requires "SYSTEM_ERROR distinct from BROKEN on the surface", and §7 names the
taxonomy. An audit on 2026-07-28 found it had never been implemented: `SYSTEM_ERROR` appeared in
ZERO source files, and `verify_derivation` collapsed three different things into one word — its own
comment said so: `else:  # MISMATCH / ERROR / broken link`.

The reproducer that started this, both through the public API:
    speed_of_wave=343, frequency_hz=440, wavelength_m=99      -> BROKEN   (a real falsehood)
    speed_of_wave="fast", frequency_hz=440, wavelength_m=.78  -> BROKEN   (OUR verifier failed)
Identical verdict, identical `broken_at`. A person checking a dosage, a wage, or a load rating
would be told their claim was false when the truth was that we could not parse the input.

This is the mirror image of the kernel's fifth clause. We guard against silently upgrading our own
authority; this was silently downgrading the caller's claim on the strength of our own bug.

Pinned here, in both directions:
  * an engine failure reports SYSTEM_ERROR, carries `error_at`, and NEVER sets `broken_at`;
  * a real falsehood still reports BROKEN even when the engine also stumbled elsewhere — an error
    must not become a hiding place for a falsehood;
  * a SYSTEM_ERROR seals as QUARANTINE, never REJECT (a citable "rejected" on something we never
    checked would outlive the bug that caused it);
  * the surfaces a human reads say it in words, not as a raw enum.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402


@pytest.fixture(autouse=True, scope="module")
def _isolate_data_dir():
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    yield
    if prior is None:
        os.environ.pop("CONCORDANCE_DATA_DIR", None)
    else:
        os.environ["CONCORDANCE_DATA_DIR"] = prior


# The two acoustics artifacts from the original audit. One is false; one we cannot check.
FALSEHOOD = {"speed_of_wave": 343.0, "frequency_hz": 440.0, "wavelength_m": 99.0}
UNCHECKABLE = {"speed_of_wave": "fast", "frequency_hz": 440.0, "wavelength_m": 0.7795}
TRUTH = {"speed_of_wave": 343.0, "frequency_hz": 440.0, "wavelength_m": 0.7795}


def _step(sid, spec):
    return {"id": sid, "domain": "acoustics", "spec": {"ACOUS_VERIFY": spec}}


def test_an_engine_failure_is_not_reported_as_a_falsehood():
    from concordance.derivation import verify_derivation
    r = verify_derivation([_step("a", UNCHECKABLE)])
    assert r["verdict"] == "SYSTEM_ERROR", "our own failure must not be called BROKEN"
    assert r["error_at"] == "a"
    assert r["broken_at"] is None, "nothing about the caller's claim was found to be false"
    assert "says NOTHING about whether the claim is true" in r["means"]


def test_a_real_falsehood_is_still_reported_plainly():
    from concordance.derivation import verify_derivation
    r = verify_derivation([_step("a", FALSEHOOD)])
    assert r["verdict"] == "BROKEN" and r["broken_at"] == "a" and r["error_at"] is None


def test_an_engine_error_is_not_a_hiding_place_for_a_falsehood():
    """Honesty runs both ways: if any step genuinely mismatches, BROKEN governs even when our
    engine also failed elsewhere. Otherwise a caller could bury a false step behind a bad one."""
    from concordance.derivation import verify_derivation
    r = verify_derivation([_step("a", UNCHECKABLE), _step("b", FALSEHOOD)])
    assert r["verdict"] == "BROKEN", "a real falsehood must still govern the composite"
    assert r["broken_at"] == "b"
    assert r["error_at"] == "a", "and our failure is still recorded, not swallowed"


def test_the_truth_is_unaffected():
    from concordance.derivation import verify_derivation
    r = verify_derivation([_step("a", TRUTH)])
    assert r["verdict"] == "HOLDS" and r["error_at"] is None and r["broken_at"] is None


def test_the_public_api_carries_the_distinction():
    from concordance.config import EngineConfig
    from concordance.web.api import dispatch
    cfg = EngineConfig("secular")
    _st, bad = dispatch("POST", "/verify", {}, {"steps": [_step("a", FALSEHOOD)]}, cfg)
    _st, ours = dispatch("POST", "/verify", {}, {"steps": [_step("a", UNCHECKABLE)]}, cfg)
    assert bad["verdict"] == "BROKEN"
    assert ours["verdict"] == "SYSTEM_ERROR"
    assert bad["verdict"] != ours["verdict"], "the two were indistinguishable before this fix"


def test_our_failure_is_never_SEALED_as_a_rejection():
    """A seal is permanent and citable. Sealing an engine bug as REJECT would leave a durable,
    quotable 'this claim was rejected' attached to something we never actually checked."""
    from concordance.receipts import _VERDICT_TO_OVERALL
    assert _VERDICT_TO_OVERALL["BROKEN"] == "REJECT"
    assert _VERDICT_TO_OVERALL["SYSTEM_ERROR"] == "QUARANTINE"
    assert _VERDICT_TO_OVERALL["ERROR"] == "QUARANTINE"


def test_the_auditor_counts_them_separately():
    """`broken_or_unchecked` merged the two and audit.html then labelled every one 'BROKEN'."""
    from concordance import audit as audit_mod
    from concordance.config import EngineConfig
    rep = audit_mod.audit("The total is 12 + 30 = 42. And 25% of 200 is 50.",
                          EngineConfig("secular"), seal=False)
    assert rep["claims_found"] >= 1, "probe text must actually reach an extractor"
    assert "broken" in rep and "unchecked" in rep
    assert rep["broken_or_unchecked"] == rep["broken"] + rep["unchecked"], "the sum must still add up"


def test_the_seal_records_WHERE_our_engine_gave_out():
    """`broken_at` is correctly null for a SYSTEM_ERROR, so without `error_at` the permanent
    record would name no step at all — and a seal outlives the session that produced it."""
    from concordance.config import EngineConfig
    from concordance.derivation import verify_derivation
    from concordance.receipts import attach
    res = verify_derivation([_step("a", UNCHECKABLE)])
    sealed = attach(res, config=EngineConfig("secular"), domain="acoustics", enabled=True)
    assert sealed["verdict"] == "SYSTEM_ERROR"
    from concordance import cas
    rec = cas.fetch(sealed["seal"]["content_hash"])
    details = (rec.get("gate_results") or [{}])[0].get("details") or {}
    assert details.get("error_at") == "a", "the seal must say which step we failed on"
    assert details.get("broken_at") is None


def test_a_person_reading_the_page_is_told_in_words():
    """A raw enum on the screen is not the same as telling someone what happened."""
    # audit.html was retired in the 2026-08-05 cut (lever 5); the three-state wording is
    # asserted on the module above — the page-level rendering went with the page.

    # check/ask/reason/audit retired 2026-08-05 (lever 5). The human surface for verdicts is
    # now the server-rendered card/seal pages and the desk's /ask flow, whose WORDING is
    # asserted at the module and seal layers above; agents get the same words via the tool
    # description (the parity test below). No remaining page renders the raw enum.
    assert "SYSTEM_ERROR" not in (ROOT / "site" / "index.html").read_text(encoding="utf-8")


def test_agents_are_told_the_same_thing_humans_are():
    """Parity: an agent reads the tool description the way a person reads the page. A verdict an
    agent has never been told about is one it will guess at — probably as failure."""
    from concordance import mcp
    from concordance.config import EngineConfig
    tools = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                       EngineConfig("secular"), {})["result"]["tools"]
    desc = {t["name"]: t["description"] for t in tools}["verify"]
    assert "SYSTEM_ERROR" in desc
    assert "never relay it to a human as a refutation" in desc

    llms = (ROOT / "site" / "llms.txt").read_text(encoding="utf-8")
    assert "SYSTEM_ERROR` is ours, not yours" in llms


if __name__ == "__main__":
    os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp())
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed — our failure is never told as your falsehood.")
