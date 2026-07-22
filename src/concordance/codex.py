"""The Codex — the project as a compiled, signed, cross-referenced manuscript.

Per Matt: "the codex is what the engine produces." Not authored — COMPILED. The engine
binds and indexes the chosen body (Scripture + the Fathers + Matt's works); it never
synthesizes doctrine. Three layers: the BODY (kept whole, in the corpus), the ENGINE
OUTPUTS (the indexes here), the INDEX (navigational surfaces). Graded by the four-tier
AUTHORITY SPINE — Words in Red → the Bible → Disciples/Didache/Fathers → Matt's writing
(lens, never authority). Emitted in three faces: live URLs, a signed Ed25519 artifact,
and this API.

2.0 upgrade — SEALED, not only witnessed. 1.0's cross-references were *witnessed* (Deut
19:15, two sources agree). 2.0 carries the moat: every note card whose source.url is a
live re-checkable receipt is surfaced as the codex's SEALED spine — authority-graded AND
receipt-backed. Scripture cross-refs stay witnessed (they are textual facts); the seal is
the engine-derived layer that can be re-run.

Build reads the live corpus (corpus.default_corpus().cards); writes data/codex/index/*.json
+ data/codex/compiled/codex_latest.json. Rebuild: python -m concordance.codex build.
"""
from __future__ import annotations

import collections
import hashlib
import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import corpus

_LOCK = threading.RLock()
_CACHE: Dict[str, Dict[str, Any]] = collections.defaultdict(lambda: {"data": None, "mtime": 0.0})

# Structural / plumbing bands — machinery, not themes. Dropped from the theme index.
_STRUCTURAL_BANDS = {
    "cites", "sequence", "prev", "next", "auto_detected", "chapter_verse", "dictionary",
    "bidirectional", "connection", "proof_text", "reference", "references", "citation",
    "resonates_with", "see_also", "capstone", "old_testament", "new_testament", "scripture",
}
_ENUM_RE = re.compile(r"^(chapter|verse|book|q|section|part|episode)[ _]?\d+$")
_VERSEREF_RE = re.compile(r"\b\d?\s?[a-z]+ \d+:\d+\b")
_SEAL_RE = re.compile(r"/s/([0-9a-f]{8,})")
_THEME_MIN_SITES = 3          # Deut 19:15 + one — a theme binds only if it reaches 3+ sites
_CONTENT_KINDS = {"note", "walk"}


def _data_dir() -> Path:
    import os
    d = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    return (Path(d) if d else Path("data"))


def _index_dir() -> Path:
    return _data_dir() / "codex" / "index"


def _compiled_dir() -> Path:
    return _data_dir() / "codex" / "compiled"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _book_slugs() -> Dict[str, str]:
    """slug -> canonical book name for the 66 books, from bible_en.jsonl."""
    out: Dict[str, str] = {}
    p = _data_dir() / "bible_en.jsonl"
    if not p.exists():
        return out
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            b = d.get("book") or d.get("book_name")
            if b and b not in out.values():
                out[b.lower().replace(" ", "_")] = b
    except OSError:
        return out
    return out


def _seal_of(card: Dict[str, Any]) -> str:
    """The live re-checkable receipt for a card, if its source.url is a /s/ seal."""
    url = (card.get("source") or {}).get("url") or ""
    return url if _SEAL_RE.search(url) else ""


def _write(path: Path, payload: Dict[str, Any]) -> Dict[str, Any]:
    with _LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
        _CACHE[str(path)] = {"data": payload, "mtime": path.stat().st_mtime}
    return payload


def _load(path: Path, empty: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        return empty
    try:
        mt = path.stat().st_mtime
    except OSError:
        return empty
    c = _CACHE[str(path)]
    if c["data"] is not None and mt <= c["mtime"]:
        return c["data"]
    with _LOCK:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return empty
        _CACHE[str(path)] = {"data": data, "mtime": mt}
        return data


# ── Scripture index — invert connection cards into a per-book cross-reference index ──
def build_scripture_index() -> Dict[str, Any]:
    books = _book_slugs()
    index: Dict[str, List[dict]] = {}
    n_conn = n_witnessed = n_verse = n_sealed = 0
    rels: Dict[str, int] = {}
    cards = corpus.default_corpus().cards
    for c in cards.values():
        if c.get("kind") != "connection" or not corpus.is_public(c):
            continue
        extra = c.get("extra") or {}
        src = c.get("source") or {}
        verse_refs = (extra.get("verse_refs") or extra.get("refs")
                      or ([extra["ref"]] if extra.get("ref") else None)
                      or ([src["ref"]] if src.get("ref") else []))
        rel = extra.get("relationship_kind") or (c.get("bands") or ["cites"])[0] or "cites"
        bands = [str(b).lower() for b in (c.get("bands") or [])]
        book_slugs = [b for b in bands if b in books]
        if not book_slugs:
            for vr in verse_refs:
                s = re.sub(r"[^a-z0-9 ]", "", str(vr or "").lower())
                for slug, _name in books.items():
                    if s.startswith(slug.replace("_", " ")):
                        book_slugs.append(slug)
                        break
        if not book_slugs:
            continue
        wit = c.get("witness_status") or extra.get("witness_status")
        seal = _seal_of(c)
        entry = {
            "by": c.get("title"),
            "relationship": rel,
            "verse_refs": verse_refs,
            "explanation": (extra.get("explanation") or c.get("body") or "")[:300],
            "witness_status": wit,
            "tier": src.get("authority_tier"),
            "card_id": c.get("id"),
        }
        if seal:
            entry["seal"] = seal
            n_sealed += 1
        n_conn += 1
        if wit == "passed":
            n_witnessed += 1
        if verse_refs:
            n_verse += 1
        rels[rel] = rels.get(rel, 0) + 1
        for bs in set(book_slugs):
            index.setdefault(books[bs], []).append(entry)

    canon = list(books.values())
    ordered = {
        b: sorted(index[b], key=lambda e: (
            not e.get("verse_refs"), e.get("witness_status") != "passed", e.get("relationship") or ""))
        for b in canon if b in index
    }
    payload = {
        "generated": _now(),
        "stats": {
            "cross_references": n_conn, "verse_level": n_verse, "witnessed": n_witnessed,
            "sealed": n_sealed, "books_indexed": len(ordered),
            "by_relationship": dict(sorted(rels.items(), key=lambda x: -x[1])[:20]),
        },
        "books": ordered,
    }
    return _write(_index_dir() / "scripture.json", payload)


def load_scripture() -> Dict[str, Any]:
    return _load(_index_dir() / "scripture.json", {"generated": None, "stats": {}, "books": {}})


# ── Theme index — invert conceptual bands into a theme web ──
def build_theme_index() -> Dict[str, Any]:
    books = set(_book_slugs().keys())
    themes: Dict[str, dict] = {}
    for c in corpus.default_corpus().cards.values():
        if c.get("kind") not in _CONTENT_KINDS or not corpus.is_public(c):
            continue
        tier = (c.get("source") or {}).get("authority_tier") or ""
        seal = _seal_of(c)
        entry = {"id": c.get("id"), "title": c.get("title") or "", "shelf": c.get("shelf") or "", "tier": tier}
        if seal:
            entry["seal"] = seal
        for b in (c.get("bands") or []):
            low = str(b).strip().lower()
            if (not low or low in _STRUCTURAL_BANDS or low in books
                    or _ENUM_RE.match(low) or _VERSEREF_RE.search(low)):
                continue
            t = themes.setdefault(low, {"label": str(b).strip(), "cards": [], "tiers": set(), "sealed": 0})
            t["cards"].append(entry)
            if tier:
                t["tiers"].add(tier)
            if seal:
                t["sealed"] += 1
    out: Dict[str, dict] = {}
    for k, t in themes.items():
        if len(t["cards"]) < _THEME_MIN_SITES:
            continue
        out[k] = {"label": t["label"], "count": len(t["cards"]), "tiers": sorted(t["tiers"]),
                  "span": len(t["tiers"]), "sealed": t["sealed"], "cards": t["cards"][:120]}
    ordered = dict(sorted(out.items(), key=lambda kv: (-kv[1]["span"], -kv[1]["count"], kv[0])))
    payload = {
        "generated": _now(),
        "stats": {
            "themes": len(ordered),
            "tagged_sites": sum(v["count"] for v in ordered.values()),
            "cross_tradition": sum(1 for v in ordered.values() if v["span"] >= 2),
            "sealed_sites": sum(v["sealed"] for v in ordered.values()),
            "min_sites": _THEME_MIN_SITES,
        },
        "themes": ordered,
    }
    return _write(_index_dir() / "themes.json", payload)


def load_themes() -> Dict[str, Any]:
    return _load(_index_dir() / "themes.json", {"generated": None, "stats": {}, "themes": {}})


# ── Connection index — witnessed co-citation hubs + the SEALED spine (the moat) ──
def _source_label(by: str) -> str:
    for sep in (" ↔ ", " <-> ", " cites ", ":"):
        if by and sep in by:
            return by.split(sep, 1)[0].strip()
    return (by or "").strip()


def build_connection_index() -> Dict[str, Any]:
    # Witness tier: a verse two+ sources both cite is a witnessed connection between them.
    scr = load_scripture()
    by_verse: Dict[str, Dict[str, Any]] = {}
    for book, refs in (scr.get("books") or {}).items():
        for e in refs:
            if e.get("witness_status") != "passed":
                continue
            src = _source_label(e.get("by") or "")
            for vr in (e.get("verse_refs") or []):
                key = re.sub(r"\s+", " ", str(vr).strip())
                if not key:
                    continue
                slot = by_verse.setdefault(key, {"sources": {}, "book": book})
                if src:
                    slot["sources"][src] = e.get("tier") or ""
    hubs = []
    for verse, slot in by_verse.items():
        srcs = sorted(slot["sources"].keys())
        if len(srcs) >= 2:
            hubs.append({"verse": verse, "book": slot["book"], "sources": srcs,
                         "source_count": len(srcs), "tier": "witnessed", "witness_status": "passed"})
    hubs.sort(key=lambda h: -h["source_count"])

    # Sealed spine (the moat): every note card whose source.url is a live re-checkable seal.
    sealed: List[dict] = []
    for c in corpus.default_corpus().cards.values():
        if c.get("kind") != "note" or not corpus.is_public(c):
            continue
        seal = _seal_of(c)
        if not seal:
            continue
        sealed.append({"id": c.get("id"), "title": c.get("title") or c.get("id"),
                       "shelf": c.get("shelf") or "", "box": c.get("box") or "",
                       "bands": [b for b in (c.get("bands") or []) if str(b).lower() not in _STRUCTURAL_BANDS][:8],
                       "seal": seal})
    sealed.sort(key=lambda s: (s["shelf"], s["box"], s["title"]))
    payload = {
        "generated": _now(),
        "stats": {
            "witnessed_hubs": len(hubs),
            "witnessed_sources": sum(h["source_count"] for h in hubs),
            "sealed_cards": len(sealed),
            "sealed_shelves": len({s["shelf"] for s in sealed}),
        },
        "witnessed": hubs[:2000],
        "sealed": sealed,
    }
    return _write(_index_dir() / "connections.json", payload)


def load_connections() -> Dict[str, Any]:
    return _load(_index_dir() / "connections.json",
                 {"generated": None, "stats": {}, "witnessed": [], "sealed": []})


# ── The signed artifact — a tamper-evident manifest of the codex as of a date ──
def _body_fingerprint() -> Dict[str, Any]:
    cards = corpus.default_corpus().cards
    by_shelf: "collections.Counter" = collections.Counter()
    by_tier: "collections.Counter" = collections.Counter()
    by_kind: "collections.Counter" = collections.Counter()
    sealed = 0
    h = hashlib.sha256()
    for cid in sorted(cards.keys()):
        c = cards[cid]
        if not corpus.is_public(c):
            continue
        by_kind[c.get("kind") or "?"] += 1
        by_shelf[c.get("shelf") or "?"] += 1
        by_tier[(c.get("source") or {}).get("authority_tier") or "?"] += 1
        if _seal_of(c):
            sealed += 1
        h.update(cid.encode())
        h.update(str(c.get("source_hash") or "").encode())
    return {
        "body_hash": h.hexdigest(),
        "public_cards": sum(by_kind.values()),
        "by_kind": dict(by_kind), "by_shelf": dict(by_shelf.most_common()),
        "by_tier": dict(by_tier.most_common()), "sealed_cards": sealed,
    }


def _index_fingerprint() -> Dict[str, Any]:
    out = {}
    for name, path in (("scripture", _index_dir() / "scripture.json"),
                       ("themes", _index_dir() / "themes.json"),
                       ("connections", _index_dir() / "connections.json")):
        if path.exists():
            raw = path.read_bytes()
            data = json.loads(raw)
            out[name] = {"stats": data.get("stats", {}), "sha256": hashlib.sha256(raw).hexdigest()}
    return out


def build_artifact() -> Dict[str, Any]:
    """Assemble + sign the manifest: body fingerprint + index fingerprints, Ed25519-signed
    by the node's codex identity (degraded-but-portable if `cryptography` is absent)."""
    manifest = {
        "codex": "narrowhighway", "generated": _now(),
        "authority_spine": ["Words in Red", "The Bible",
                            "Disciples / Didache / Fathers", "Matt's writing (lens)"],
        "body": _body_fingerprint(), "indexes": _index_fingerprint(),
    }
    manifest_hash = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    signed = {"manifest": manifest, "manifest_sha256": manifest_hash}
    try:
        from . import identity as _id
        idp = _compiled_dir() / "codex_identity.json"
        if idp.exists():
            ident = json.loads(idp.read_text(encoding="utf-8"))
        else:
            ident = _id.create_identity()
            _compiled_dir().mkdir(parents=True, exist_ok=True)
            idp.write_text(json.dumps(ident, indent=2), encoding="utf-8")
        signed["signature"] = _id.sign(ident["private_key"], manifest_hash)
        signed["public_key"] = ident["public_key"]
        signed["fingerprint"] = _id.fingerprint(ident["public_key"])
        signed["signed"] = bool(_id.signing_available())
    except Exception as e:  # never crash the codex over signing
        signed["signature"] = None
        signed["signed"] = False
        signed["sign_error"] = str(e)[:120]
    _write(_compiled_dir() / "codex_latest.json", signed)
    return signed


def load_artifact() -> Dict[str, Any]:
    return _load(_compiled_dir() / "codex_latest.json", {"manifest": None, "signed": False})


def verify_artifact() -> Dict[str, Any]:
    """Re-check the signature + detect index drift since sealing."""
    art = load_artifact()
    man = art.get("manifest")
    if not man:
        return {"ok": False, "reason": "no artifact sealed yet"}
    recomputed = hashlib.sha256(
        json.dumps(man, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    hash_ok = recomputed == art.get("manifest_sha256")
    sig_ok = None
    if art.get("signature") and art.get("public_key"):
        try:
            from . import identity as _id
            sig_ok = _id.verify(art["public_key"], art["manifest_sha256"], art["signature"])
        except Exception:
            sig_ok = None
    live_body = _body_fingerprint().get("body_hash")
    drift = live_body != (man.get("body") or {}).get("body_hash")
    return {"ok": bool(hash_ok and (sig_ok is not False)), "manifest_hash_ok": hash_ok,
            "signature_ok": sig_ok, "body_drift_since_seal": drift,
            "generated": man.get("generated")}


# ── Public surface helpers ──
def overview() -> Dict[str, Any]:
    scr, thm, con = load_scripture(), load_themes(), load_connections()
    art = load_artifact()
    return {
        "codex": "The project as a compiled, signed, cross-referenced manuscript.",
        "authority_spine": ["Words in Red", "The Bible",
                            "Disciples / Didache / Fathers", "Matt's writing (lens)"],
        "scripture": scr.get("stats", {}),
        "themes": thm.get("stats", {}),
        "connections": con.get("stats", {}),
        "artifact": {"generated": (art.get("manifest") or {}).get("generated"),
                     "signed": art.get("signed"), "fingerprint": art.get("fingerprint")},
        "faces": ["GET /codex/index/scripture[/{book}]", "GET /codex/index/themes[/{theme}]",
                  "GET /codex/connections", "GET /codex/artifact", "GET /codex/verify"],
        "note": ("Compiled, never authored — the engine binds and indexes; it never opines. "
                 "Witnessed cross-references (Deut 19:15) plus the SEALED spine (live receipts). "
                 "Tier 4 (Matt's writing) is lens, never authority."),
    }


def scripture_summary() -> Dict[str, Any]:
    """Books with cross-reference counts (the index list) — not the full entries."""
    scr = load_scripture()
    books = {name: len(refs) for name, refs in (scr.get("books") or {}).items()}
    return {"generated": scr.get("generated"), "stats": scr.get("stats", {}), "books": books}


def scripture_book(book: str) -> Optional[Dict[str, Any]]:
    books = load_scripture().get("books") or {}
    key = (book or "").strip().lower().replace("_", " ")
    for name, refs in books.items():
        if name.lower() == key:
            return {"book": name, "count": len(refs), "cross_references": refs}
    return None


def theme(name: str) -> Optional[Dict[str, Any]]:
    themes = load_themes().get("themes") or {}
    key = (name or "").strip().lower()
    if key in themes:
        return {"theme": key, **themes[key]}
    return None


def build_all() -> Dict[str, Any]:
    build_scripture_index()
    build_theme_index()
    build_connection_index()
    art = build_artifact()
    return {"scripture": load_scripture().get("stats"), "themes": load_themes().get("stats"),
            "connections": load_connections().get("stats"),
            "artifact_signed": art.get("signed"), "fingerprint": art.get("fingerprint")}


__all__ = ["build_all", "build_scripture_index", "build_theme_index", "build_connection_index",
           "build_artifact", "verify_artifact", "load_scripture", "load_themes", "load_connections",
           "load_artifact", "overview", "scripture_summary", "scripture_book", "theme"]


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "build":
        print(json.dumps(build_all(), indent=2))
    elif cmd == "verify":
        print(json.dumps(verify_artifact(), indent=2))
    else:
        print("usage: python -m concordance.codex [build|verify]")
