"""Ask — the conduit front door: finds/verifies/cites, never generates.

Proves deterministic routing, crisis-help-first, ultimate-matters-point-to-Christ, verify
hands a receipt, and the /ask endpoint. Runnable with pytest OR directly.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-ask-")  # isolate seal writes

from concordance import ask  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402

SEC = EngineConfig("secular")
WIT = EngineConfig("witness")


def test_classify_routes():
    assert ask.classify("2+2 = 4") == "verify"
    assert ask.classify("John 3:16") == "scripture"
    assert ask.classify("what is G26?") == "word_study"
    assert ask.classify("honestly I want to die") == "crisis"
    assert ask.classify("what is the meaning of life") == "ultimate"
    assert ask.classify("grace and truth") == "search"


def test_crisis_puts_real_help_first():
    r = ask.respond("sometimes I want to die", SEC)
    assert r["kind"] == "crisis"
    assert any("988" in x["label"] for x in r["resources"])


def test_ultimate_points_to_christ_and_people():
    r = ask.respond("what is the meaning of life", SEC)
    assert r["kind"] == "ultimate"
    assert any(v["ref"] == "John 14:6" for v in r["scripture"])
    assert r["real_help"] and "also_in_the_keeping" in r


def test_verify_hands_a_receipt_and_catches_falsehood():
    good = ask.respond("2+2 = 4", SEC)
    assert good["verify"]["verdict"] == "HOLDS" and good["verify"].get("seal")
    bad = ask.respond("2+2 = 5", SEC)
    assert bad["verify"]["verdict"] == "BROKEN"


def test_search_is_the_default():
    r = ask.respond("justice and mercy", SEC)
    assert r["kind"] == "found" and "results" in r


def test_scripture_routes_on_witness_but_falls_back_on_secular():
    assert "scripture" in ask.respond("John 3:16", WIT)          # witness resolves (text may be empty w/o data)
    assert ask.respond("John 3:16", SEC)["kind"] == "found"       # secular has no resolve -> search


def test_every_response_carries_the_conduit_note():
    for q in ("2+2 = 4", "grace", "the meaning of life", "I want to die"):
        assert "not generate the answer" in ask.respond(q, SEC)["note"]


def test_ask_endpoint():
    from concordance.web.api import dispatch
    st, p = dispatch("POST", "/ask", {}, {"text": "2+2 = 4"}, SEC)
    assert st == 200 and p["verify"]["verdict"] == "HOLDS"
    assert dispatch("POST", "/ask", {}, {"text": "  "}, SEC)[0] == 400


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} ask tests passed — conduit routing: find/verify/cite, help-first, points to Christ.")
