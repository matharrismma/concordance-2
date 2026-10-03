#!/usr/bin/env python3
"""THE ZIM — the verified field library as one Kiwix file, so it rides into the offline boxes other people
already run (Kiwix, Internet-in-a-Box, Prepper Disk). Matt, 2026-10-03: "Lean into the open doors" — a layer
on current offerings, a known branch: one file, one hash, cut weekly on the box.

Runs tools/export_commons_bundle.py (the standalone HTML field library: the whole Bible + the clean-licensed
field shelves) into the releases root, then packs the newest bundle into a ZIM with python-libzim (full-text
indexed, English). Nothing fetched, nothing generated — the bundle's own files, byte for byte.

    CONCORDANCE_RELEASES=/srv/nh-releases CONCORDANCE_DATA_DIR=... PYTHONPATH=src python tools/export_zim.py
    python tools/export_zim.py --only-zim <bundle dir>      # pack an existing bundle

Writes <releases>/zim/narrowhighway-commons_<YYYY-MM-DD>.zim (+ .sha256), keeps the last 4, and rewrites
<releases>/index.html + <releases>/index.json so the releases root lists what it holds, with hashes.
"""
from __future__ import annotations

import hashlib
import html
import json
import mimetypes
import os
import re
import struct
import subprocess
import sys
import zlib
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RELEASES = Path(os.environ.get("CONCORDANCE_RELEASES", "").strip() or "/srv/nh-releases")
KEEP = int(os.environ.get("NH_ZIM_KEEP", "4"))
NAME = "narrowhighway-commons"
_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.I | re.S)


def _png_48() -> bytes:
    """A 48x48 solid PNG (the ZIM illustration Kiwix libraries expect), built with the stdlib."""
    w = h = 48
    row = b"\x00" + bytes([0x8a, 0x5a, 0x1e] * w)            # the house's accent, one filter byte per row
    raw = row * h
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def build_bundle() -> Path:
    """Run the bundle tool and return the newest bundle directory it wrote."""
    env = dict(os.environ, CONCORDANCE_RELEASES=str(RELEASES), PYTHONPATH=str(REPO / "src"))
    r = subprocess.run([sys.executable, str(REPO / "tools" / "export_commons_bundle.py")], env=env,
                       capture_output=True, text=True)
    sys.stdout.write(r.stdout[-2000:])
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-2000:])
        raise SystemExit(f"bundle failed ({r.returncode})")
    root = RELEASES / "field-library-html"
    dirs = sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime)
    if not dirs:
        raise SystemExit("no bundle directory found")
    return dirs[-1]


def pack(bundle: Path, out: Path) -> dict:
    from libzim.writer import Creator, FileProvider, Hint, Item, StringProvider

    class FileItem(Item):
        def __init__(self, rel: str, fpath: Path, mime: str, title: str):
            super().__init__()
            self._rel, self._fpath, self._mime, self._title = rel, fpath, mime, title
        def get_path(self): return self._rel
        def get_title(self): return self._title
        def get_mimetype(self): return self._mime
        def get_contentprovider(self): return FileProvider(str(self._fpath))
        def get_hints(self): return {Hint.FRONT_ARTICLE: self._mime.startswith("text/html")}

    class Illustration(Item):
        def get_path(self): return "Illustration_48x48@1"
        def get_title(self): return ""
        def get_mimetype(self): return "image/png"
        def get_contentprovider(self): return StringProvider(_png_48())
        def get_hints(self): return {}

    files = sorted(p for p in bundle.rglob("*") if p.is_file())
    n = 0
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".zim.part")
    if tmp.exists():
        tmp.unlink()
    with Creator(str(tmp)).config_indexing(True, "eng") as c:
        c.set_mainpath("index.html")
        for k, v in {
            "Name": f"{NAME}_en", "Title": "Narrow Highway — the field library and the whole Bible",
            "Creator": "narrowhighway.com", "Publisher": "narrowhighway.com", "Date": date.today().isoformat(),
            "Language": "eng", "Tags": "_category:other;_pictures:no;_videos:no;_details:yes;_ftindex:yes",
            "Description": "The verified, clean-licensed field library (survival, water, first aid, comms, the "
                           "field kit, the playbook) and the whole Bible (WEB) — found, cited, sealed; nothing generated.",
            "Source": "https://narrowhighway.com/releases/", "License": "Public domain sources; attribution on each card",
        }.items():
            c.add_metadata(k, v)
        c.add_metadata("Illustration_48x48@1", _png_48(), "image/png")
        for f in files:
            rel = f.relative_to(bundle).as_posix()
            mime = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
            title = rel
            if mime.startswith("text/html"):
                m = _TITLE_RE.search(f.read_text(encoding="utf-8", errors="replace")[:4000])
                title = html.unescape(m.group(1)).strip() if m else rel
            c.add_item(FileItem(rel, f, mime, title))
            n += 1
    tmp.rename(out)
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    (out.parent / (out.name + ".sha256")).write_text(f"{sha} *{out.name}\n", encoding="utf-8")
    return {"zim": out.name, "files": n, "bytes": out.stat().st_size, "sha256": sha, "bundle": bundle.name}


def rotate(zdir: Path) -> None:
    zims = sorted(zdir.glob(f"{NAME}_*.zim"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in zims[KEEP:]:
        old.unlink(missing_ok=True)
        (zdir / (old.name + ".sha256")).unlink(missing_ok=True)


def write_index(root: Path) -> None:
    """The releases root lists what it holds — every file with its hash, as a page and as JSON."""
    rows = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.name in ("index.html", "index.json") or p.suffix == ".part" or p.name.endswith(".sha256"):
            continue
        if p.is_relative_to(root / "field-library-html"):
            continue                                   # the HTML bundle is served as pages, not listed as files
        sha_file = p.parent / (p.name + ".sha256")
        sha = sha_file.read_text(encoding="utf-8").split()[0] if sha_file.exists() else ""
        rows.append({"path": p.relative_to(root).as_posix(), "bytes": p.stat().st_size, "sha256": sha,
                     "modified": date.fromtimestamp(p.stat().st_mtime).isoformat()})
    (root / "index.json").write_text(json.dumps({"releases": rows, "note": "every file carries its sha256; a copy "
                                                 "that arrives unverified is not a copy"}, indent=1), encoding="utf-8")
    items = "\n".join(f'<li><a href="{html.escape(r["path"])}">{html.escape(r["path"])}</a> — {r["bytes"]/1e6:.1f} MB — '
                      f'<code>{r["sha256"][:16]}…</code> — {r["modified"]}</li>' for r in rows)
    (root / "index.html").write_text(
        "<!doctype html><meta charset=utf-8><title>Narrow Highway — releases</title>"
        "<style>body{font:16px/1.5 Georgia,serif;max-width:52rem;margin:2rem auto;padding:0 1rem;color:#1f1d18}"
        "code{font-size:.85em}</style><h1>Releases</h1><p>The field pack (a runnable node for a Pi beside a radio), "
        "the field library as a Kiwix ZIM, and their hashes. Verify before you trust: <code>sha256sum -c</code>.</p>"
        f"<ul>{items}</ul><p><a href='index.json'>index.json</a> · <a href='/'>narrowhighway.com</a></p>\n",
        encoding="utf-8")


def main() -> int:
    if "--only-zim" in sys.argv:
        bundle = Path(sys.argv[sys.argv.index("--only-zim") + 1])
    else:
        bundle = build_bundle()
    out = RELEASES / "zim" / f"{NAME}_{date.today().isoformat()}.zim"
    info = pack(bundle, out)
    rotate(out.parent)
    write_index(RELEASES)
    print(f"zim: {out} ({info['bytes']/1e6:.1f} MB, {info['files']} files) sha256={info['sha256'][:16]}… from {info['bundle']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
