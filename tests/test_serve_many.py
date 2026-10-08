"""One process, every surface (2026-10-08): two listeners in one interpreter, each answering as its own
surface, sharing the module-level singletons — and the CLI routing `--surface both` to them."""
from __future__ import annotations

import json
import sys
import threading
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance.web import api  # noqa: E402


def _get(port: int, path: str) -> dict:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def test_two_surfaces_one_process_each_answer_as_themselves():
    servers = [api.build_server(host="127.0.0.1", port=0, surface=s, warm=False) for s in ("witness", "secular")]
    threads = [threading.Thread(target=h.serve_forever, daemon=True) for h in servers]
    for t in threads:
        t.start()
    try:
        ports = [h.server_address[1] for h in servers]
        assert ports[0] != ports[1]
        w, s = _get(ports[0], "/health"), _get(ports[1], "/health")
        assert w["ok"] and s["ok"]
        assert w["surface"] == "witness" and s["surface"] == "secular"
        # the same process: one interpreter, one set of singletons (the corpus module global is shared by construction)
        from concordance import corpus
        assert corpus._DEFAULT is corpus._DEFAULT and threading.active_count() >= 3
    finally:
        for h in servers:
            h.shutdown()
            h.server_close()


def test_cli_routes_both_to_serve_many(monkeypatch):
    import concordance.__main__ as M
    from concordance.web import api as _api
    seen = {}
    monkeypatch.setattr(_api, "serve_many", lambda host, listeners, site_dir=None: seen.update(host=host, listeners=listeners, site=site_dir))
    monkeypatch.setattr(M, "serve", lambda **kw: seen.update(single=kw))
    M.main(["serve", "--surface", "both", "--host", "127.0.0.1", "--witness-port", "18001", "--secular-port", "18002", "--no-site"])
    assert seen["listeners"] == [(18001, "witness"), (18002, "secular")] and seen["host"] == "127.0.0.1" and seen["site"] is None
    assert "single" not in seen
    seen.clear()
    M.main(["serve", "--surface", "witness", "--port", "18001", "--no-site"])
    assert seen["single"]["surface"] == "witness" and seen["single"]["port"] == 18001 and "listeners" not in seen


def test_cli_refuses_port_with_both(monkeypatch, capsys):
    import concordance.__main__ as M
    from concordance.web import api as _api
    called = {}
    monkeypatch.setattr(_api, "serve_many", lambda **kw: called.update(many=kw))
    monkeypatch.setattr(M, "serve", lambda **kw: called.update(single=kw))
    rc = M.main(["serve", "--surface", "both", "--port", "9000", "--no-site"])
    assert rc == 2 and not called and "--witness-port" in capsys.readouterr().err
