"""EVERY COPY IS WHOLE (Gen 3 · 1, 2026-10-04) — a node pulls the keeping from a KNOWN branch and ends up
holding the same seals, the same chain, the same keeping files; it refuses an unsigned or mis-pinned word,
re-hashes everything before it writes, never deletes, and sets aside a chain tail it minted on its own.
Two scratch data dirs play branch and node; the HTTP is a fake fetch that routes to the same functions the
routes call, so what is proven here is the protocol, not the socket."""
import json
import os
import tempfile
import time
from pathlib import Path

import pytest

# Scratch data dir at import (the suite's convention): nothing here may touch the real keeping — cas.store
# mints a receipt card into the live data dir, which is why _mint below writes records directly instead.
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-replicate-")
os.environ.pop("CONCORDANCE_NODE_KEY_FILE", None)

from concordance import cas, ledger, replicate  # noqa: E402
from concordance.validate import canonical_json_bytes

pytestmark = pytest.mark.skipif(not replicate.identity.signing_available(), reason="needs cryptography")


def _mint(d: Path, n: int, prev: str, t0: float) -> str:
    """Append n sealed precedents (each bound to a CAS record) to d/ledger; returns the new head."""
    for i in range(n):
        rec = {"kind": "test", "claim": f"{i} + {i} = {2*i}", "sealed_by": "test", "n": i, "t": t0 + i}
        rh = cas.content_hash_of(rec)
        cp = cas._record_path(d / "cas", rh)
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps(rec, sort_keys=True), encoding="utf-8")
        prec = {"precedent_id": f"ledger://test/{t0}/{i}", "summary": f"seal {i}", "sealed_at": t0 + i,
                "record_hash": rh, "prev_hash": prev}
        prec["content_hash"] = ledger.compute_content_hash(prec)
        (d / "ledger").mkdir(parents=True, exist_ok=True)
        (d / "ledger" / f"test-{int(t0)}-{i}.json").write_text(json.dumps(prec), encoding="utf-8")
        prev = prec["content_hash"]
    return prev


def _branch(tmp: Path) -> Path:
    b = tmp / "branch"
    b.mkdir()
    (b / "cards.jsonl").write_text('{"id": "card_a", "title": "A"}\n', encoding="utf-8")
    (b / "bible_en.jsonl").write_text('{"book": "John", "chapter": 3, "verse": 16, "text": "For God"}\n', encoding="utf-8")
    (b / "history_spine.jsonl").write_text('{"id": "s1"}\n', encoding="utf-8")
    (b / "contact_inbox.jsonl").write_text('{"from": "someone", "text": "private"}\n', encoding="utf-8")
    (b / "cards.jsonl.bak2").write_text("old\n", encoding="utf-8")
    _mint(b, 3, replicate.GENESIS, time.time() - 1000)
    replicate.node_identity(b)                       # the branch's key, created on first use
    return b


def _fake_fetch(b: Path):
    """Route the node's requests to the branch functions, as the HTTP handler would."""
    def fetch(path: str):
        from urllib.parse import parse_qs, urlparse
        u = urlparse(path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path == "/sync/manifest":
            return 200, json.dumps(replicate.manifest(b)).encode()
        if u.path == "/sync/ledger":
            return 200, json.dumps(replicate.ledger_since(q.get("since", ""), int(q.get("limit", 500)), b,
                                                          hashes_only=q.get("hashes_only") == "1")).encode()
        if u.path == "/sync/file":
            blob = replicate.file_bytes(q.get("name", ""), b)
            return (200, blob[0]) if blob else (404, b"{}")
        return 404, b"{}"
    return fetch


@pytest.fixture()
def world(tmp_path):
    b = _branch(tmp_path)
    n = tmp_path / "node"
    n.mkdir()
    fp = replicate.node_identity(b)["fingerprint"]
    spec = {"name": "box", "url": "https://example.invalid", "fingerprint": fp}
    return b, n, spec


def test_the_manifest_lists_only_the_keeping_and_is_signed(world):
    b, _, spec = world
    m = replicate.manifest(b)
    names = {f["name"] for f in m["files"]}
    assert names == {"cards.jsonl", "bible_en.jsonl", "history_spine.jsonl"}      # never the inbox, never a .bak
    assert m["alg"] == "ed25519" and m["ledger"]["count"] == 3 and m["cas"]["count"] == 3
    assert replicate.verify_manifest(m, spec["fingerprint"]) == (True, "ok")
    tampered = dict(m)
    tampered["files"] = list(m["files"]) + [{"name": "node_identity.json", "sha256": "0" * 64, "bytes": 1, "mtime": 0}]
    assert replicate.verify_manifest(tampered, spec["fingerprint"])[0] is False
    assert replicate.verify_manifest(m, "deadbeef")[0] is False                   # the pin is the trust root
    unsigned = dict(m, alg="unsigned")
    assert "unsigned" in replicate.verify_manifest(unsigned, spec["fingerprint"])[1]
    assert not replicate.allowed("node_identity.json") and not replicate.allowed("../cards.jsonl")
    assert replicate.file_bytes("contact_inbox.jsonl", b) is None


def test_the_ledger_pages_from_genesis_and_from_any_hash(world):
    b, _, _ = world
    page = replicate.ledger_since("", 2, b)
    assert page["count"] == 2 and page["done"] is False and page["records"][0]["record"]["n"] == 0
    rest = replicate.ledger_since(page["next"], 500, b)
    assert rest["count"] == 1 and rest["done"] is True and rest["head"] == rest["records"][0]["content_hash"]
    assert replicate.ledger_since("f" * 64, 10, b)["error"] == "unknown since"
    assert len(replicate.ledger_since("", 1, b, hashes_only=True)["hashes"]) == 3


def test_a_node_pulls_the_whole_keeping_and_verifies_it(world):
    b, n, spec = world
    rep = replicate.pull(spec, fetch=_fake_fetch(b), data_dir=n)
    assert rep["ok"] and rep["records_pulled"] == 3 and rep["cas_pulled"] == 3 and rep["files_pulled"] == 3
    assert rep["chain_ok"] and rep["chain_verified"] == 3 and rep["head_after"] == replicate.ledger_head(b)[0]
    assert (n / "cards.jsonl").read_bytes() == (b / "cards.jsonl").read_bytes()
    assert not (n / "contact_inbox.jsonl").exists()
    # the same seal is now served by the node — "every copy is whole"
    h = ledger._read_precedent_file(replicate.ledger._ledger_chain_files(b / "ledger")[-1])["record_hash"]
    assert cas.fetch(h, base_dir=n / "cas") == cas.fetch(h, base_dir=b / "cas")
    assert json.loads((n / "sync_status.json").read_text())["ok"] is True
    # a second pull finds nothing to do
    again = replicate.pull(spec, fetch=_fake_fetch(b), data_dir=n)
    assert again["ok"] and again["records_pulled"] == 0 and again["files_pulled"] == 0


def test_a_node_offline_for_a_while_catches_up_incrementally(world):
    b, n, spec = world
    replicate.pull(spec, fetch=_fake_fetch(b), data_dir=n)
    head = replicate.ledger_head(b)[0]
    _mint(b, 2, head, time.time())                                   # the branch moved on
    (b / "cards.jsonl").write_text('{"id": "card_a"}\n{"id": "card_b"}\n', encoding="utf-8")
    rep = replicate.pull(spec, fetch=_fake_fetch(b), data_dir=n)
    assert rep["ok"] and rep["records_pulled"] == 2 and rep["files_pulled"] == 1 and rep["chain_verified"] == 5
    assert "card_b" in (n / "cards.jsonl").read_text()


def test_a_local_only_tail_is_set_aside_never_deleted(world):
    b, n, spec = world
    replicate.pull(spec, fetch=_fake_fetch(b), data_dir=n)
    head = replicate.ledger_head(n)[0]
    _mint(n, 1, head, time.time())                                   # the node sealed something of its own
    _mint(b, 1, head, time.time() + 5)                               # meanwhile the branch sealed too
    rep = replicate.pull(spec, fetch=_fake_fetch(b), data_dir=n)
    assert rep["ok"] and rep["local_only_set_aside"] == 1 and rep["records_pulled"] == 1
    assert len(list((n / "ledger-local").glob("*.json"))) == 1       # kept, not deleted
    assert replicate.ledger_head(n)[0] == replicate.ledger_head(b)[0]


def test_a_mis_pinned_or_unsigned_branch_is_refused_and_nothing_is_written(world):
    b, n, spec = world
    bad = dict(spec, fingerprint="0" * 32)
    rep = replicate.pull(bad, fetch=_fake_fetch(b), data_dir=n)
    assert rep["ok"] is False and "fingerprint mismatch" in rep["detail"]
    assert not (n / "cards.jsonl").exists() and not (n / "ledger").exists()
    dry = replicate.pull(spec, fetch=_fake_fetch(b), data_dir=n, dry_run=True)
    assert dry["files_pulled"] == 3 and not (n / "cards.jsonl").exists()


def test_a_tampered_file_or_record_in_flight_is_refused(world):
    b, n, spec = world
    real = _fake_fetch(b)

    def evil(path):
        st, body = real(path)
        if path.startswith("/sync/file?name=cards"):
            return st, body + b'{"id": "card_evil"}\n'
        if path.startswith("/sync/ledger?since=&"):
            page = json.loads(body)
            page["records"][0]["record"]["claim"] = "1 + 1 = 3"
            return st, json.dumps(page).encode()
        return st, body
    rep = replicate.pull(spec, fetch=evil, data_dir=n)
    whys = {r["why"] for r in rep["refused"]}
    assert any("sha256" in w for w in whys) and any("re-hash" in w for w in whys)
    assert not (n / "cards.jsonl").exists()


def test_a_stalled_file_resumes_with_range_and_still_verifies(world):
    """2026-10-04: the first catch-up died 31 minutes in on a read timeout mid-way through a 41 MB file (the
    desktop line). A stall now keeps what arrived and resumes from that byte; the whole file is still hashed
    against the manifest before it is moved into place."""
    b, n, spec = world
    (b / "cards.jsonl").write_bytes(b"".join(b'{"id": "card_%06d"}\n' % i for i in range(20000)))   # ~400 KB
    calls = []

    def flaky(path, offset=0):
        calls.append(offset)
        from urllib.parse import parse_qs, urlparse
        q = {k: v[0] for k, v in parse_qs(urlparse(path).query).items()}
        data, sha, total = replicate.file_bytes(q["name"], b, offset)
        if q["name"] == "cards.jsonl" and offset == 0:
            return 0, data[:100_000], False                               # the line stalls after 100 KB
        return (206 if offset else 200), data, True
    rep = replicate.pull(spec, fetch=_fake_fetch(b), data_dir=n, fetch_file=flaky)
    assert rep["ok"] and rep["refused"] == [] and (n / "cards.jsonl").read_bytes() == (b / "cards.jsonl").read_bytes()
    assert calls[0] == 0 and 100_000 in calls and not (n / "cards.jsonl.part").exists()
    # a branch that ignores Range (answers 200 from the top) still ends verified
    (b / "cards.jsonl").write_bytes(b"x" * 50_000)
    calls.clear()

    def ignores_range(path, offset=0):
        from urllib.parse import parse_qs, urlparse
        q = {k: v[0] for k, v in parse_qs(urlparse(path).query).items()}
        data, sha, total = replicate.file_bytes(q["name"], b, 0)
        calls.append(offset)
        if q["name"] == "cards.jsonl" and offset == 0:
            return 0, data[:10_000], False
        return 200, data, True
    rep = replicate.pull(spec, fetch=_fake_fetch(b), data_dir=n, fetch_file=ignores_range)
    assert rep["ok"] and (n / "cards.jsonl").read_bytes() == b"x" * 50_000


def test_a_file_that_never_completes_keeps_its_partial_for_next_time(world):
    b, n, spec = world

    def dead(path, offset=0):
        from urllib.parse import parse_qs, urlparse
        q = {k: v[0] for k, v in parse_qs(urlparse(path).query).items()}
        data, sha, total = replicate.file_bytes(q["name"], b, offset)
        if q["name"] == "cards.jsonl":
            return 0, data[:5] if offset == 0 else b"", False
        return 200, data, True
    rep = replicate.pull(spec, fetch=_fake_fetch(b), data_dir=n, fetch_file=dead)
    assert rep["ok"] is True and any("incomplete" in r["why"] for r in rep["refused"])
    assert (n / "cards.jsonl.part").read_bytes() == (b / "cards.jsonl").read_bytes()[:5] and not (n / "cards.jsonl").exists()


def test_known_branches_are_pinned_by_hand_and_the_node_has_a_public_face(tmp_path):
    d = tmp_path / "n"
    d.mkdir()
    assert replicate.known_branches(d) == []
    replicate.add_branch("box", "https://narrowhighway.org/", "abc123", d)
    assert replicate.known_branches(d)[0]["url"] == "https://narrowhighway.org"
    pub = replicate.node_public(d)
    assert pub["fingerprint"] and pub["public_key"] and pub["signing"] is True and "private_key" not in pub
    key = json.loads((d / "node_identity.json").read_text())
    assert key["private_key"] and replicate.identity.fingerprint(key["public_key"]) == pub["fingerprint"]
    if os.name != "nt":
        assert oct(os.stat(d / "node_identity.json").st_mode & 0o777) == "0o600"
