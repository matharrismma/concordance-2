"""The Works volume serves without ever building — and never upgrades authority.

Proves two invariants found in the full-project review (2026-07-27):
1. GET-path functions (load/overview/demonstrations/verify_artifact) NEVER write files or mint
   signing keys when no compiled volume exists — they degrade honestly. Building is an operator
   action, not a side effect of being visited.
2. verify_artifact (compendium AND codex — same rule) never reports ok for an artifact whose
   CLAIMED signature cannot actually be verified; only an honestly-unsigned artifact may pass on
   the manifest hash alone. Authority is never silently upgraded (the kernel's fifth part).

Runnable with pytest OR directly.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import codex, compendium  # noqa: E402


def _manifest_and_hash():
    man = {"work": "test", "published": 0}
    h = hashlib.sha256(json.dumps(man, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return man, h


def test_serving_an_uncompiled_volume_writes_nothing_and_degrades_honestly():
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    try:
        with tempfile.TemporaryDirectory() as t:
            os.environ["CONCORDANCE_DATA_DIR"] = t
            compendium._CACHE = None
            before = sorted(str(p) for p in Path(t).rglob("*"))
            v = compendium.load()
            assert v.get("manifest") is None and v.get("signed") is False
            ov = compendium.overview()
            assert ov.get("published") in (0, None)
            assert compendium.demonstrations() == []
            vr = compendium.verify_artifact()
            assert vr["ok"] is False and "no volume" in vr.get("reason", "")
            after = sorted(str(p) for p in Path(t).rglob("*"))
            assert before == after, f"a GET-path call wrote files: {set(after) - set(before)}"
    finally:
        if prior is None:
            os.environ.pop("CONCORDANCE_DATA_DIR", None)
        else:
            os.environ["CONCORDANCE_DATA_DIR"] = prior
        compendium._CACHE = None


def test_uncompiled_volume_is_not_cached_so_a_shipped_file_is_picked_up():
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    try:
        with tempfile.TemporaryDirectory() as t:
            os.environ["CONCORDANCE_DATA_DIR"] = t
            compendium._CACHE = None
            assert compendium.load().get("manifest") is None
            man, h = _manifest_and_hash()
            p = compendium._compiled_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps({"manifest": man, "manifest_sha256": h, "signed": False}),
                         encoding="utf-8")
            assert compendium.load().get("manifest") == man, \
                "the degraded empty record must not stick in the cache"
    finally:
        if prior is None:
            os.environ.pop("CONCORDANCE_DATA_DIR", None)
        else:
            os.environ["CONCORDANCE_DATA_DIR"] = prior
        compendium._CACHE = None


def _verify_with(monkey_load, module, loader_name):
    original = getattr(module, loader_name)
    setattr(module, loader_name, monkey_load)
    try:
        return module.verify_artifact()
    finally:
        setattr(module, loader_name, original)


def test_unsigned_artifact_passes_on_hash_alone_and_says_so():
    man, h = _manifest_and_hash()
    r = _verify_with(lambda **kw: {"manifest": man, "manifest_sha256": h}, compendium, "load")
    assert r["ok"] is True and r["manifest_hash_ok"] is True
    assert r["signature_claimed"] is False and r["signature_ok"] is None


def test_claimed_but_unverifiable_signature_is_never_ok():
    # A garbage key/signature makes identity.verify raise or return False — under the old code
    # (`sig_ok is not False`) an exception path yielded ok: True. That silent authority upgrade
    # is the regression this pins shut, for BOTH artifact verifiers.
    man, h = _manifest_and_hash()
    bad = {"manifest": man, "manifest_sha256": h,
           "signature": "not-a-real-signature", "public_key": "not-a-real-key"}
    r = _verify_with(lambda **kw: dict(bad), compendium, "load")
    assert r["signature_claimed"] is True
    assert r["signature_ok"] is not True
    assert r["ok"] is False, "a claimed signature that cannot be verified must never be ok"

    prior_fp = codex._body_fingerprint
    codex._body_fingerprint = lambda: {"body_hash": "x"}
    try:
        r2 = _verify_with(lambda: dict(bad), codex, "load_artifact")
    finally:
        codex._body_fingerprint = prior_fp
    assert r2["signature_claimed"] is True and r2["ok"] is False


def test_tampered_manifest_fails_the_hash():
    man, h = _manifest_and_hash()
    tampered = {"manifest": {**man, "published": 999}, "manifest_sha256": h}
    r = _verify_with(lambda **kw: tampered, compendium, "load")
    assert r["manifest_hash_ok"] is False and r["ok"] is False


# ── build → publish/drop → sign → emit → serve (engine + receipts mocked) ──
_DEMOS = [
    {"id": "d_hold", "discipline": "mathematics", "field": "algebra", "title": "Two and two",
     "narrative": "2 + 2 = 4.", "steps": [{"id": "s1", "domain": "mathematics",
                                           "spec": {"mode": "equality", "params": {}}, "claim": "2+2=4"}]},
    {"id": "d_broken", "discipline": "physical", "field": "physics", "title": "A false claim",
     "narrative": "does not hold", "steps": [{"id": "s1", "domain": "mathematics",
                                              "spec": {"_break": True}, "claim": "wrong"}]},
]


def _fake_verify(runsteps):
    if any((s.get("spec") or {}).get("_break") for s in runsteps):
        return {"verdict": "BROKEN", "broken_at": "s1", "gap_at": None,
                "steps": [], "confirmed_steps": 0, "trail": []}
    return {"verdict": "HOLDS", "steps": [{"id": "s1", "verdict": "CONFIRMED"}], "confirmed_steps": 1,
            "trail": [{"domain": "mathematics", "step": "s1", "note": "2+2 = 4"}]}


def test_build_publishes_holds_drops_broken_signs_emits_and_serves():
    """The build side (the original tests only exercise the serve side). Only what HOLDS is
    published; a BROKEN demonstration is dropped; the volume is signed and every demonstration
    becomes a seed in the keeping; then the serve surfaces read the sealed file back."""
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    saved = (compendium.DEMONSTRATIONS, compendium.verify_derivation, compendium.receipts.attach)
    try:
        with tempfile.TemporaryDirectory() as t:
            os.environ["CONCORDANCE_DATA_DIR"] = t
            compendium._CACHE = None
            compendium.DEMONSTRATIONS = _DEMOS
            compendium.verify_derivation = _fake_verify
            compendium.receipts.attach = (lambda result, config=None, domain=None, enabled=True: {
                **result, "seal": {"content_hash": "h_" + result["verdict"],
                                   "cite_url": "/s/h_" + result["verdict"], "ledgered": True}})
            payload = compendium.build_all()
            man = payload["manifest"]
            assert man["published"] == 1 and man["dropped"] == ["d_broken"]
            assert man["by_discipline"] == {"mathematics": 1}
            assert payload["demonstrations"][0]["seal"]["cite_url"] == "/s/h_HOLDS"
            assert "signed" in payload and payload["manifest_sha256"]
            assert (Path(t) / "works_cards.jsonl").exists(), "demonstrations become seeds in the keeping"

            compendium._CACHE = None                      # serve must re-read the sealed file
            assert compendium.overview()["published"] == 1
            assert [d["id"] for d in compendium.demonstrations()] == ["d_hold"]
            assert compendium.demonstration("d_hold")["title"] == "Two and two"
            assert compendium.demonstration("missing") is None
            assert compendium.artifact()["manifest"]["published"] == 1
            v = compendium.verify_artifact()
            assert v["manifest_hash_ok"] is True and v["ok"] is True
    finally:
        compendium.DEMONSTRATIONS, compendium.verify_derivation, compendium.receipts.attach = saved
        compendium._CACHE = None
        if prior is None:
            os.environ.pop("CONCORDANCE_DATA_DIR", None)
        else:
            os.environ["CONCORDANCE_DATA_DIR"] = prior


def test_packet_for_wraps_domain_specs_but_passes_math():
    assert compendium._packet_for("mathematics", {"mode": "equality"}) == {"mode": "equality"}
    assert compendium._packet_for("physics", {"v": 1}) == {"PHYS_VERIFY": {"v": 1}}
    already = {"PHYS_VERIFY": {"v": 1}}
    assert compendium._packet_for("physics", already) == already   # not double-wrapped
    assert compendium._packet_for("unknown_domain", {"v": 1}) == {"v": 1}


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} compendium tests passed — serving never builds; authority is never upgraded.")
