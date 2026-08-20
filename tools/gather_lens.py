#!/usr/bin/env python3
"""Gather the LENS CORPUS — Matt's writing, read into `lens.see()`'s way of seeing.

Matt: "I had seen my writing as the lens." His writing lives in the iCloud M.R_ folder — novels,
screenplays, planning bibles. This reads them into `data/lens.jsonl`: one attributed PASSAGE per line
({text, work, ref, id}), his words verbatim, so the lens proposes how HIS witness frames a thing.

The boundary, held: this is a LOCAL, gitignored layer (his creative work is never published — only seen
through). Nothing is rewritten; passages are his exact paragraphs, each carrying its work and position.
The lens is only ever as full as what is gathered here, and it says so.

Stdlib only. Formats: .epub (spine XHTML), .docx (document.xml), .md/.txt/.fountain (plain text).
PDFs/images are skipped (no stdlib text layer); superseded folders are skipped.

    python tools/gather_lens.py            # gather M.R_ -> data/lens.jsonl
    python tools/gather_lens.py --check    # list the works and passage counts, write nothing
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import sys
import zipfile
from pathlib import Path

SRC = Path(os.environ.get("CONCORDANCE_LENS_SRC", "").strip() or "C:/Users/hdven/iCloudDrive/M.R_")
OUT = Path(os.environ.get("CONCORDANCE_LENS", "").strip() or "data/lens.jsonl")
_MIN, _MAX = 60, 2400          # a passage worth seeing through: a real paragraph, not a fragment or a chapter
_SKIP_DIRS = ("superseded", "_superseded", ".git")
_EXTS = (".epub", ".docx", ".md", ".txt", ".fountain")


def _clean_work(name: str) -> str:
    """A readable work title from a filename (drop version/status/author noise)."""
    w = re.sub(r"\.(epub|docx|md|txt|fountain)$", "", name, flags=re.I)
    w = re.sub(r"[\-_—]+\s*(COMPLETE|FINAL|Final|Integrated.*|voice.*|EDITED.*|VOICE.*|v\d+.*)\s*$", "", w)
    w = re.sub(r"\b(FINAL|COMPLETE|Final Novel|MRHarris|v\d+)\b", "", w)
    w = re.sub(r"\s+", " ", w.replace("_", " ")).strip(" -—_")
    return w or name


def _paras_from_html(xml: str) -> list:
    xml = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", xml, flags=re.S | re.I)
    out = []
    for block in re.split(r"</(?:p|div|h[1-6]|li|blockquote|br\s*/?)>", xml, flags=re.I):
        t = html.unescape(re.sub(r"<[^>]+>", " ", block))
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            out.append(t)
    return out


def _paras_from_epub(path: Path) -> list:
    out = []
    try:
        z = zipfile.ZipFile(path)
    except Exception:  # noqa: BLE001
        return out
    names = [n for n in z.namelist() if n.lower().endswith((".xhtml", ".html", ".htm"))]
    order = {}
    try:  # follow the spine so the reading order (and refs) are the author's
        opf = next((n for n in z.namelist() if n.lower().endswith(".opf")), None)
        if opf:
            man = dict(re.findall(r'<item[^>]*id="([^"]+)"[^>]*href="([^"]+)"', z.read(opf).decode("utf-8", "replace")))
            spine = re.findall(r'<itemref[^>]*idref="([^"]+)"', z.read(opf).decode("utf-8", "replace"))
            base = os.path.dirname(opf)
            order = {os.path.normpath(os.path.join(base, man[i])).replace("\\", "/"): k
                     for k, i in enumerate(spine) if i in man}
    except Exception:  # noqa: BLE001
        pass
    names.sort(key=lambda n: order.get(n.replace("\\", "/"), 999))
    for ci, n in enumerate(names, 1):
        try:
            for t in _paras_from_html(z.read(n).decode("utf-8", "replace")):
                out.append((f"ch.{ci}", t))
        except Exception:  # noqa: BLE001
            continue
    return out


def _paras_from_docx(path: Path) -> list:
    out = []
    try:
        z = zipfile.ZipFile(path)
        xml = z.read("word/document.xml").decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return out
    for pi, para in enumerate(re.split(r"</w:p>", xml), 1):
        t = html.unescape("".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", para, re.S)))
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            out.append((f"¶{pi}", t))
    return out


def _paras_from_text(path: Path) -> list:
    out = []
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return out
    for bi, block in enumerate(re.split(r"\n\s*\n", raw), 1):
        t = re.sub(r"\s+", " ", block).strip()
        # drop pure screenplay scene headings / section markers
        if t and not re.match(r"^(INT\.|EXT\.|#|=|\.[A-Z]|FADE|CUT TO)", t):
            out.append((f"¶{bi}", t))
    return out


def _passages(path: Path) -> list:
    ext = path.suffix.lower()
    if ext == ".epub":
        return _paras_from_epub(path)
    if ext == ".docx":
        return _paras_from_docx(path)
    if ext in (".md", ".txt", ".fountain"):
        return _paras_from_text(path)
    return []


def gather(src: Path):
    works = {}
    for p in sorted(src.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in _EXTS:
            continue
        if any(s in part.lower() for part in p.parts for s in _SKIP_DIRS):
            continue
        work = _clean_work(p.name)
        for ref, text in _passages(p):
            if _MIN <= len(text) <= _MAX:
                works.setdefault(work, []).append((ref, text))
    return works


def main() -> int:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    if not SRC.exists():
        print("lens source not found:", SRC)
        return 1
    works = gather(SRC)
    total = sum(len(v) for v in works.values())
    print("lens source:", SRC)
    for w, ps in sorted(works.items(), key=lambda kv: -len(kv[1])):
        print("  %5d passages  %s" % (len(ps), w))
    print("  %d works, %d passages" % (len(works), total))
    if "--check" in sys.argv:
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    n = 0
    with open(OUT, "w", encoding="utf-8") as f:
        for work, ps in works.items():
            for ref, text in ps:
                # dedup by CONTENT, so version-duplicates of a work (Dancing Plague, TMYGT) collapse to
                # one passage, keeping the first work/ref it appeared under.
                pid = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]
                if pid in seen:
                    continue
                seen.add(pid)
                f.write(json.dumps({"text": text, "work": work, "ref": ref, "id": pid},
                                   ensure_ascii=False) + "\n")
                n += 1
    print("wrote %d passages -> %s (local, gitignored — his writing is never published)" % (n, OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
