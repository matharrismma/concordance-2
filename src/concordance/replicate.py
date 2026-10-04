"""EVERY COPY IS WHOLE — the keeping syncs between nodes (Gen 3 · 1; docs/GEN3_CHARTER.md).

Matt, 2026-10-04: "agreed, build in order." The camel's tiers (box → desktop → Pi → USB) were snapshots:
the desktop node held a Sep-20 copy, the field pack a read-only ZIM, and every seal lived only on the
box. This module makes a node a NODE: it pulls the keeping from a KNOWN BRANCH — a URL plus a pinned
identity fingerprint, never random trust — verifies the branch's signed manifest, pulls the seal ledger
incrementally (the chain is append-only, so "everything after my head" is the whole delta), pulls the
keeping files whose hashes changed, writes atomically, and then serves the same seals at /s/<hash>.
A node offline for a month catches up.

The branch side (served by every node, so any node can be a branch for the next tier):
    GET /sync/manifest           the node's identity + the ledger head + every keeping file's sha256, SIGNED
    GET /sync/ledger?since=H     the chain after content-hash H (genesis when empty), with the bound CAS records
    GET /sync/file?name=F        the bytes of one allow-listed keeping file (x-sha256 header)

The node side:
    python -m concordance sync [--branch NAME] [--dry-run]
    data/known_branches.json     {"branches": [{"name", "url", "fingerprint"}]} — the trust root, pinned by hand

What travels (v1): the top-level keeping files the servers READ (cards, spines, seeds, bridges, Bibles, the
canon, the dictionary supplement, the witnesses), the ledger, and the sealed CAS records. What never travels:
the node's private key, inboxes, profiles, groups, mesh messages, moderation, caches, backups — an explicit
ALLOW list, because a deny list forgets. Sub-directory trees (Strong's, commentary, xrefs …) are v1.1.

Sovereign: stdlib + the shared signing primitives (Ed25519 via `cryptography`; a branch that cannot sign is
refused — a node must not pull on an unsigned word).
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import socket
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import cas, identity, ledger
from .validate import canonical_json_bytes

VERSION = 1
GENESIS = ledger.GENESIS_HASH

# ── the allow list: what the keeping IS, on disk ────────────────────────────────────────────────
ALLOW = (
    "cards.jsonl", "*_cards.jsonl", "*_spine.jsonl", "*_spines.jsonl", "*_seeds.jsonl", "*_bridges.jsonl",
    "bible_*.jsonl", "canon.jsonl", "dictionary_supplement.jsonl", "witnesses.jsonl", "domain_goldens.json",
)
NEVER = ("node_identity.json", "known_branches.json", "sync_status.json", "contact_inbox.jsonl",
         "web_cache.jsonl", "watch.json", "watch_org.json", "watch_history.jsonl", "activity.jsonl",
         "traffic.json", "provider_health.json", "integrity_status.json")


def _data_dir(data_dir: Optional[Path] = None) -> Path:
    if data_dir is not None:
        return Path(data_dir)
    d = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    return Path(d) if d else Path("data")


def allowed(name: str) -> bool:
    """A file name the manifest may list: allow-listed, never-listed, no path parts, no backups."""
    if not name or "/" in name or "\\" in name or name.startswith(".") or ".bak" in name:
        return False
    if name in NEVER:
        return False
    return any(fnmatch.fnmatch(name, pat) for pat in ALLOW)


# ── the node's own identity (the branch signs with it; the private key never leaves) ───────────
def _key_path(data_dir: Optional[Path] = None) -> Path:
    env = os.environ.get("CONCORDANCE_NODE_KEY_FILE", "").strip()
    return Path(env) if env else _data_dir(data_dir) / "node_identity.json"


def node_identity(data_dir: Optional[Path] = None, create: bool = True) -> Optional[Dict[str, Any]]:
    """{fingerprint, public_key, private_key, name, created_at, signing} — created on first use, 0600."""
    p = _key_path(data_dir)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
    if not create:
        return None
    ident = identity.create_identity()
    rec = {"fingerprint": ident["id"], "public_key": ident["public_key"], "private_key": ident["private_key"],
           "signing": bool(ident.get("signing_available")), "name": socket.gethostname(),
           "created_at": int(time.time())}
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, p)
    return rec


def node_public(data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """What a node says about itself in public: fingerprint, public key, name, whether it signs, last sync."""
    rec = node_identity(data_dir) or {}
    out = {"fingerprint": rec.get("fingerprint"), "public_key": rec.get("public_key"), "name": rec.get("name"),
           "signing": bool(rec.get("signing")), "protocol": VERSION}
    st = _read_json(_data_dir(data_dir) / "sync_status.json")
    if st:
        out["last_sync"] = {k: st.get(k) for k in ("at", "branch", "fingerprint", "head_after", "records_pulled",
                                                   "files_pulled", "ok")}
    return out


# ── the manifest ────────────────────────────────────────────────────────────────────────────────
_HASH_CACHE: Dict[Tuple[str, int, int], str] = {}


def _sha256_file(p: Path) -> str:
    st = p.stat()
    key = (str(p), st.st_size, st.st_mtime_ns)
    h = _HASH_CACHE.get(key)
    if h:
        return h
    d = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            d.update(chunk)
    h = d.hexdigest()
    _HASH_CACHE[key] = h
    return h


def ledger_head(data_dir: Optional[Path] = None) -> Tuple[str, int]:
    files = ledger._ledger_chain_files(_data_dir(data_dir) / "ledger")
    if not files:
        return GENESIS, 0
    last = ledger._read_precedent_file(files[-1]) or {}
    return str(last.get("content_hash") or ledger.compute_content_hash(last)), len(files)


def manifest(data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """The branch's word, signed: who it is, where its chain stands, and the hash of every keeping file."""
    d = _data_dir(data_dir)
    ident = node_identity(d) or {}
    files: List[Dict[str, Any]] = []
    try:
        names = sorted(p.name for p in d.iterdir() if p.is_file())
    except OSError:
        names = []
    for name in names:
        if not allowed(name):
            continue
        p = d / name
        try:
            st = p.stat()
            files.append({"name": name, "sha256": _sha256_file(p), "bytes": st.st_size, "mtime": int(st.st_mtime)})
        except OSError:
            continue
    head, count = ledger_head(d)
    body = {
        "v": VERSION,
        "node": {"fingerprint": ident.get("fingerprint"), "public_key": ident.get("public_key"),
                 "name": ident.get("name")},
        "generated_at": int(time.time()),
        "ledger": {"head": head, "count": count},
        "cas": {"count": len(cas.list_hashes(base_dir=d / "cas"))},
        "files": files,
        "scope": "keeping files (top level) + ledger + sealed records; sub-directory trees are v1.1",
        "note": ("Verify: fingerprint(node.public_key) must equal the fingerprint you pinned for this branch, and "
                 "sig must verify over the canonical JSON of everything but sig/alg. Then GET /sync/ledger?since="
                 "<your head> and /sync/file?name=<name> for every sha256 you do not hold."),
    }
    sig = identity.sign(ident.get("private_key") or "", canonical_json_bytes(body)) if ident else ""
    out = dict(body)
    out["sig"] = sig
    out["alg"] = "ed25519" if ident.get("signing") else "unsigned"
    return out


def verify_manifest(m: Dict[str, Any], pinned_fingerprint: str) -> Tuple[bool, str]:
    """A manifest is trusted only when it is signed by the key whose fingerprint was pinned by hand."""
    if not isinstance(m, dict) or "sig" not in m:
        return False, "no signature"
    if m.get("alg") != "ed25519":
        return False, f"branch does not sign (alg={m.get('alg')!r}); a node never pulls on an unsigned word"
    node = m.get("node") or {}
    pub = str(node.get("public_key") or "")
    if not pub or identity.fingerprint(pub) != pinned_fingerprint:
        return False, (f"fingerprint mismatch: branch says {identity.fingerprint(pub) if pub else None!r}, "
                       f"pinned {pinned_fingerprint!r}")
    body = {k: v for k, v in m.items() if k not in ("sig", "alg")}
    if not identity.verify(pub, canonical_json_bytes(body), str(m["sig"])):
        return False, "signature does not verify"
    return True, "ok"


# ── the ledger, incrementally ───────────────────────────────────────────────────────────────────
def chain_hashes(data_dir: Optional[Path] = None) -> List[Tuple[str, str]]:
    """[(content_hash, file_name)] in chain order."""
    out = []
    for f in ledger._ledger_chain_files(_data_dir(data_dir) / "ledger"):
        rec = ledger._read_precedent_file(f)
        if rec is None:
            continue
        out.append((str(rec.get("content_hash") or ledger.compute_content_hash(rec)), f.name))
    return out


def ledger_since(since: str = "", limit: int = 500, data_dir: Optional[Path] = None,
                 hashes_only: bool = False) -> Dict[str, Any]:
    """The chain after `since` (a content hash; empty = genesis), oldest first, with each record's bound CAS
    record so a node can re-verify before it writes. `hashes_only` returns the whole chain's hashes (cheap)
    so a node can find where its own chain parted from the branch's."""
    d = _data_dir(data_dir)
    chain = chain_hashes(d)
    if hashes_only:
        return {"hashes": [h for h, _ in chain], "count": len(chain), "head": chain[-1][0] if chain else GENESIS}
    start = 0
    if since and since != GENESIS:
        idx = next((i for i, (h, _) in enumerate(chain) if h == since), None)
        if idx is None:
            return {"error": "unknown since", "detail": "that hash is not on this branch's chain — pull "
                                                       "hashes_only=1 and find the common prefix",
                    "head": chain[-1][0] if chain else GENESIS, "count": len(chain)}
        start = idx + 1
    limit = max(1, min(int(limit or 500), 2000))
    items = []
    for h, name in chain[start:start + limit]:
        rec = ledger._read_precedent_file(d / "ledger" / name)
        if rec is None:
            continue
        bound = None
        rh = rec.get("record_hash")
        if rh:
            bound = cas.fetch(rh, base_dir=d / "cas")
        items.append({"file": name, "content_hash": h, "precedent": rec, "record": bound})
    nxt = items[-1]["content_hash"] if items else since
    return {"since": since or GENESIS, "records": items, "count": len(items), "next": nxt,
            "done": start + len(items) >= len(chain), "head": chain[-1][0] if chain else GENESIS,
            "chain_count": len(chain)}


def file_bytes(name: str, data_dir: Optional[Path] = None) -> Optional[Tuple[bytes, str]]:
    """(bytes, sha256) of one allow-listed keeping file, or None."""
    if not allowed(name):
        return None
    p = _data_dir(data_dir) / name
    if not p.is_file():
        return None
    data = p.read_bytes()
    return data, hashlib.sha256(data).hexdigest()


# ── the node side: pull from a known branch ─────────────────────────────────────────────────────
Fetch = Callable[[str], Tuple[int, bytes]]


def _http_fetch(base_url: str, timeout: int = 120) -> Fetch:
    def fetch(path: str) -> Tuple[int, bytes]:
        req = urllib.request.Request(base_url.rstrip("/") + path,
                                     headers={"user-agent": "narrowhighway-node/1", "accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:   # noqa: S310 — a pinned known branch
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            # a dropped line (the branch restarting mid-pull, a timeout) is a refusal of that one request,
            # never a crash: what was written stays, and the next run resumes by hash
            return 0, str(e).encode("utf-8", "replace")
    return fetch


def _read_json(p: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _atomic_write(p: Path, data: bytes) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".part")
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, p)


def known_branches(data_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    rec = _read_json(_data_dir(data_dir) / "known_branches.json") or {}
    return [b for b in (rec.get("branches") or []) if b.get("url") and b.get("fingerprint")]


def add_branch(name: str, url: str, fingerprint: str, data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Pin a branch by hand — the trust root. Replaces an entry of the same name."""
    d = _data_dir(data_dir)
    rec = _read_json(d / "known_branches.json") or {"branches": []}
    rec["branches"] = [b for b in rec.get("branches", []) if b.get("name") != name]
    rec["branches"].append({"name": name, "url": url.rstrip("/"), "fingerprint": fingerprint,
                            "pinned_at": int(time.time())})
    _atomic_write(d / "known_branches.json", json.dumps(rec, indent=1).encode("utf-8"))
    return rec


def pull(branch: Dict[str, Any], fetch: Optional[Fetch] = None, data_dir: Optional[Path] = None,
         dry_run: bool = False) -> Dict[str, Any]:
    """Pull the keeping from one known branch. Refuses an unsigned or mis-pinned manifest. Every ledger
    record is re-hashed and chain-linked before it is written; every CAS record is re-hashed; every file is
    re-hashed. Never deletes: a local-only chain tail (seals this node minted while the branch moved on) is
    set aside in ledger-local/ and reported, so the node's chain mirrors the branch's."""
    d = _data_dir(data_dir)
    fetch = fetch or _http_fetch(str(branch["url"]))
    rep: Dict[str, Any] = {"ok": False, "branch": branch.get("name"), "url": branch.get("url"),
                           "fingerprint": branch.get("fingerprint"), "at": int(time.time()), "dry_run": dry_run,
                           "records_pulled": 0, "cas_pulled": 0, "files_pulled": 0, "bytes": 0,
                           "local_only_set_aside": 0, "refused": [], "detail": ""}
    lock = d / "sync.lock"
    if not dry_run:
        # one pull at a time per data dir: a nightly timer must never overlap a long first catch-up
        held = _read_json(lock) or {}
        if held and time.time() - float(held.get("at") or 0) < 6 * 3600:
            rep["detail"] = f"another sync holds {lock.name} since {int(held.get('at') or 0)} (pid {held.get('pid')})"
            return rep
        d.mkdir(parents=True, exist_ok=True)
        _atomic_write(lock, json.dumps({"pid": os.getpid(), "at": int(time.time())}).encode("utf-8"))
    try:
        return _pull_locked(rep, branch, fetch, d, dry_run)
    finally:
        if not dry_run:
            try:
                lock.unlink()
            except OSError:
                pass


def _pull_locked(rep: Dict[str, Any], branch: Dict[str, Any], fetch: Fetch, d: Path, dry_run: bool) -> Dict[str, Any]:
    status, raw = fetch("/sync/manifest")
    if status != 200:
        rep["detail"] = f"manifest: HTTP {status}"
        return _finish(rep, d, dry_run)
    try:
        m = json.loads(raw.decode("utf-8"))
    except ValueError:
        rep["detail"] = "manifest: not JSON"
        return _finish(rep, d, dry_run)
    ok, why = verify_manifest(m, str(branch["fingerprint"]))
    if not ok:
        rep["detail"] = f"manifest refused: {why}"
        return _finish(rep, d, dry_run)
    rep["branch_head"] = (m.get("ledger") or {}).get("head")
    rep["branch_files"] = len(m.get("files") or [])
    _pull_ledger(rep, fetch, d, dry_run)          # a broken chain stops the ledger, never the files
    _pull_files(rep, m, fetch, d, dry_run)
    rep["ok"] = not rep["detail"]
    if not dry_run and rep["records_pulled"]:
        chk = ledger.verify_chain(d / "ledger", cas_base=d / "cas")
        rep["chain_ok"] = bool(chk.get("ok"))
        rep["chain_verified"] = chk.get("verified")
        if not chk.get("ok"):
            rep["ok"] = False
            rep["detail"] = "the pulled chain does not verify end to end"
    return _finish(rep, d, dry_run)


def _pull_ledger(rep: Dict[str, Any], fetch: Fetch, d: Path, dry_run: bool) -> None:
    # ── the ledger: find where our chain and the branch's part, set aside our tail, pull the rest ──
    local = chain_hashes(d)
    rep["head_before"] = local[-1][0] if local else GENESIS
    status, raw = fetch("/sync/ledger?hashes_only=1")
    if status != 200:
        rep["detail"] = f"ledger hashes: HTTP {status}"
        return
    branch_hashes = (json.loads(raw.decode("utf-8")) or {}).get("hashes") or []
    common = 0
    while common < len(local) and common < len(branch_hashes) and local[common][0] == branch_hashes[common]:
        common += 1
    tail = local[common:]
    if tail and not dry_run:
        aside = d / "ledger-local"
        aside.mkdir(parents=True, exist_ok=True)
        for h, name in tail:
            os.replace(d / "ledger" / name, aside / name)
    rep["local_only_set_aside"] = len(tail)
    since = local[common - 1][0] if common else ""
    expected_prev = since or GENESIS
    while True:
        status, raw = fetch(f"/sync/ledger?since={urllib.parse.quote(since)}&limit=500")
        if status != 200:
            rep["detail"] = f"ledger: HTTP {status}"
            return
        page = json.loads(raw.decode("utf-8"))
        if page.get("error"):
            rep["detail"] = f"ledger: {page['error']}"
            return
        for item in page.get("records") or []:
            prec = item.get("precedent") or {}
            h = str(item.get("content_hash") or "")
            if ledger.compute_content_hash(prec) != h or str(prec.get("content_hash") or h) != h:
                rep["refused"].append({"record": h[:12], "why": "content hash does not recompute"})
                rep["detail"] = "a pulled record does not recompute; the ledger stopped there"
                return
            if str(prec.get("prev_hash", GENESIS)) != expected_prev:
                rep["refused"].append({"record": h[:12], "why": "prev_hash does not link"})
                rep["detail"] = "chain broke at a pulled record; the ledger stopped there"
                return
            bound = item.get("record")
            rh = prec.get("record_hash")
            if rh:
                if not isinstance(bound, dict) or cas.content_hash_of(bound) != rh:
                    rep["refused"].append({"record": h[:12], "why": "bound CAS record missing or does not re-hash"})
                    rep["detail"] = "a bound record does not re-hash; the ledger stopped there"
                    return
                if not dry_run:
                    cp = cas._record_path(d / "cas", rh)
                    if not cp.exists():
                        _atomic_write(cp, json.dumps(bound, ensure_ascii=False, sort_keys=True).encode("utf-8"))
                        rep["cas_pulled"] += 1
            name = str(item.get("file") or f"{h[:16]}.json")
            if "/" in name or "\\" in name or not name.endswith(".json"):
                name = f"{h[:16]}.json"
            if not dry_run:
                _atomic_write(d / "ledger" / name, json.dumps(prec, ensure_ascii=False, indent=2).encode("utf-8"))
            rep["records_pulled"] += 1
            expected_prev = h
        since = str(page.get("next") or since)
        if page.get("done", True) or not page.get("records"):
            break
    rep["head_after"] = expected_prev


def _pull_files(rep: Dict[str, Any], m: Dict[str, Any], fetch: Fetch, d: Path, dry_run: bool) -> None:
    # ── the keeping files: pull every sha256 we do not hold ──
    for entry in m.get("files") or []:
        name = str(entry.get("name") or "")
        want = str(entry.get("sha256") or "")
        if not allowed(name) or not want:
            continue
        p = d / name
        have = _sha256_file(p) if p.is_file() else ""
        if have == want:
            continue
        if dry_run:
            rep["files_pulled"] += 1
            rep["bytes"] += int(entry.get("bytes") or 0)
            continue
        status, raw = fetch(f"/sync/file?name={urllib.parse.quote(name)}")
        if status != 200:
            rep["refused"].append({"file": name, "why": f"HTTP {status}"})
            continue
        got = hashlib.sha256(raw).hexdigest()
        if got != want:
            rep["refused"].append({"file": name, "why": "sha256 does not match the manifest"})
            continue
        _atomic_write(p, raw)
        rep["files_pulled"] += 1
        rep["bytes"] += len(raw)


def _finish(rep: Dict[str, Any], d: Path, dry_run: bool) -> Dict[str, Any]:
    if not dry_run:
        try:
            _atomic_write(d / "sync_status.json", json.dumps(rep, indent=1).encode("utf-8"))
        except OSError:
            pass
    return rep


def sync_all(data_dir: Optional[Path] = None, only: str = "", dry_run: bool = False) -> List[Dict[str, Any]]:
    out = []
    for b in known_branches(data_dir):
        if only and b.get("name") != only:
            continue
        out.append(pull(b, data_dir=data_dir, dry_run=dry_run))
    return out
