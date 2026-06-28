"""The keep — operator gate + the live dashboard the operator watches.

Proves: telemetry round-trips (record → recent → stats); the gate trusts localhost,
honors a token, and stays closed to a remote caller without one (hide-existence); the
dashboard returns the operator's at-a-glance state. Runnable with pytest OR directly.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def _isolate():
    """Point the engine's data dir at a fresh temp dir so telemetry is clean."""
    d = tempfile.mkdtemp(prefix="nh-keep-")
    os.environ["CONCORDANCE_DATA_DIR"] = d
    return d


def test_telemetry_roundtrip():
    _isolate()
    from concordance import telemetry
    telemetry.record("verify", surface="secular", verdict="HOLDS", mode="equality")
    telemetry.record("search", surface="witness", query="grace", count=5)
    evs = telemetry.recent(10)
    assert len(evs) == 2 and evs[-1]["action"] == "search"
    st = telemetry.stats()
    assert st["events"] == 2
    assert st["by_action"]["verify"] == 1 and st["by_verdict"]["HOLDS"] == 1
    assert st["by_surface"]["witness"] == 1


def test_telemetry_never_raises_on_bad_dir():
    # A logging failure must never break a request: point the data dir at a FILE so the
    # log dir can't be created. record() must swallow it; recent() must return [].
    f = tempfile.NamedTemporaryFile(prefix="nh-notadir-", delete=False)
    f.write(b"x")
    f.close()
    os.environ["CONCORDANCE_DATA_DIR"] = f.name  # a file, not a directory
    from concordance import telemetry
    telemetry.record("verify", verdict="X")  # must not raise
    assert telemetry.recent() == []


def test_gate_localhost_only_when_enabled():
    os.environ.pop("CONCORDANCE_KEEP_TOKEN", None)
    os.environ.pop("CONCORDANCE_KEEP_TRUST_LOCAL", None)
    from concordance.web import keep
    # FAIL CLOSED by default: loopback is NOT trusted (behind a proxy the peer is loopback)
    assert keep.is_operator(None, "127.0.0.1") is False
    assert keep.is_operator(None, "") is False
    os.environ["CONCORDANCE_KEEP_TRUST_LOCAL"] = "1"
    assert keep.is_operator(None, "127.0.0.1") is True
    assert keep.is_operator(None, "203.0.113.7") is False  # only loopback, even when enabled
    os.environ.pop("CONCORDANCE_KEEP_TRUST_LOCAL", None)


def test_xff_is_ignored_for_auth():
    """The keep must NOT trust X-Forwarded-For — the spoof that the review flagged."""
    os.environ["CONCORDANCE_KEEP_TOKEN"] = "tok"
    os.environ.pop("CONCORDANCE_KEEP_TRUST_LOCAL", None)
    from concordance.web import keep
    # remote attacker forging XFF: 127.0.0.1, no token -> denied
    assert keep.request_is_operator("203.0.113.9", {"x-forwarded-for": "127.0.0.1"}, {}) is False
    # the operator with the token passes regardless of peer (query or header)
    assert keep.request_is_operator("203.0.113.9", {}, {"token": "tok"}) is True
    assert keep.request_is_operator("203.0.113.9", {"x-keep-token": "tok"}, {}) is True
    os.environ.pop("CONCORDANCE_KEEP_TOKEN", None)


def test_gate_closed_to_remote_without_token():
    os.environ.pop("CONCORDANCE_KEEP_TOKEN", None)
    from concordance.web import keep
    assert keep.is_operator(None, "203.0.113.7") is False
    assert keep.is_operator("anything", "203.0.113.7") is False  # no token configured = closed


def test_gate_honors_token():
    os.environ["CONCORDANCE_KEEP_TOKEN"] = "s3cret"
    from concordance.web import keep
    assert keep.is_operator("s3cret", "203.0.113.7") is True
    assert keep.is_operator("wrong", "203.0.113.7") is False
    os.environ.pop("CONCORDANCE_KEEP_TOKEN", None)


def test_dashboard_shape():
    _isolate()
    from concordance.config import EngineConfig
    from concordance.web import keep
    d = keep.dashboard(EngineConfig("witness"))
    assert d["ok"] is True and d["surface"] == "witness"
    for k in ("keeping", "seals", "ledger", "activity"):
        assert k in d
    assert "stats" in d["activity"] and "recent" in d["activity"]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} keep tests passed — operator gate + live dashboard + telemetry, sovereign.")
