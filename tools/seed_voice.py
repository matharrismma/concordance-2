#!/usr/bin/env python3
"""THE VOICE CORPUS — Matt's own words, gathered as the house shepherd's voice (composition layer #4,
2026-10-14). The engine FINDS + CHECKS claims; the connective tissue that MEETS a person and draws the
thread should sound like Matt shepherding — so it is composed from his OWN writing, SELECTED verbatim and
fit to the moment, never generated. His ElevenLabs clone then speaks it. "All Matt's writing is witness."

This EXTRACTS his Christian writing (devotionals + sermons) into data/voice_lines.jsonl — one verbatim
pastoral unit per record, tagged with the Scripture it sits on (so voice.see can fit it to a situation).
It reads only the writing it is pointed at; it never touches the personal/PII files beside them.

    python tools/seed_voice.py "<writing dir>"   # default: the Christian writing folder; writes voice_lines.jsonl
    python tools/seed_voice.py --check "<dir>"    # parse + count, write nothing

Output record: {id, text, source, ref, kind, by}  (text = Matt's verbatim reflection paragraph).
NOTE: the output is Matt's personal content — box-side data like witnesses.jsonl, never committed, never
treated as public-domain. The extractor (this file) is the tracked source.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or str(ROOT / "data"))
DEFAULT_DIR = r"C:\Users\hdven\iCloudDrive\Christian writing"
OUT = DATA / "voice_lines.jsonl"

_DATE = re.compile(r"^Date:\s*\d", re.I)
_SCRIP = re.compile(r"^Scripture\s*\(([^)]+)\)")
_TRANS = re.compile(r"\s+(NKJV|KJV|ESV|NIV|NASB|WEB|ASV)\b.*$", re.I)
_BY = "M.R. Harris"


def _norm_ref(raw: str) -> str:
    s = _TRANS.sub("", (raw or "").strip()).strip()
    return s.replace("\u2013", "-").replace("\u2014", "-").strip(" :")


def _slug(s: str, n: int = 40) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")[:n] or "x"


def _from_devotional(path: Path) -> List[Dict]:
    import docx
    paras = [p.text.strip() for p in docx.Document(str(path)).paragraphs if p.text.strip()]
    out: List[Dict] = []
    i = 0
    while i < len(paras):
        if i + 1 < len(paras) and _DATE.match(paras[i + 1]):
            title = paras[i]
            i += 2
            ref, reflection = "", []
            while i < len(paras) and not (i + 1 < len(paras) and _DATE.match(paras[i + 1])):
                m = _SCRIP.match(paras[i])
                if m:                                  # the verse (canon) follows the label — stop; we keep OUR words
                    ref = _norm_ref(m.group(1))
                    while i < len(paras) and not (i + 1 < len(paras) and _DATE.match(paras[i + 1])):
                        i += 1
                    break
                if len(paras[i]) >= 40 and not paras[i].lower().startswith(("reflection:", "scripture")):
                    reflection.append(paras[i])
                i += 1
            for k, para in enumerate(reflection):
                out.append({"id": f"voice_dev_{_slug(title)}_{k}", "text": para,
                            "source": f"Devotional Reflections — {title}", "ref": ref,
                            "kind": "reflection", "by": _BY})
        else:
            i += 1
    return out


def _from_sermon_docx(path: Path) -> List[Dict]:
    import docx
    paras = [p.text.strip() for p in docx.Document(str(path)).paragraphs if p.text.strip()]
    title = paras[0] if paras else path.stem
    out = []
    for k, p in enumerate(paras):
        if len(p) >= 60 and not _DATE.match(p) and not _SCRIP.match(p):
            out.append({"id": f"voice_serm_{_slug(path.stem)}_{k}", "text": p,
                        "source": f"Sermon — {title}", "ref": "", "kind": "sermon", "by": _BY})
    return out


def _from_pdf(path: Path) -> List[Dict]:
    import subprocess
    try:
        txt = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True,
                             timeout=60).stdout
    except Exception as e:  # noqa: BLE001
        print("  pdf extract failed:", path.name, e); return []
    out, k = [], 0
    for para in re.split(r"\n\s*\n", txt):
        para = " ".join(para.split())
        if len(para) >= 60:
            out.append({"id": f"voice_serm_{_slug(path.stem)}_{k}", "text": para,
                        "source": f"Sermon — {path.stem}", "ref": "", "kind": "sermon", "by": _BY})
            k += 1
    return out


def gather(src: Path) -> List[Dict]:
    recs: List[Dict] = []
    for f in sorted(src.glob("*.docx")):
        recs += (_from_devotional(f) if "devotional" in f.name.lower() else _from_sermon_docx(f))
    for f in sorted(src.glob("*.pdf")):
        recs += _from_pdf(f)
    # dedupe on text
    seen, uniq = set(), []
    for r in recs:
        key = r["text"][:200]
        if key not in seen and len(r["text"]) >= 40:
            seen.add(key); uniq.append(r)
    return uniq


def main() -> int:
    argv = [a for a in sys.argv[1:] if a != "--check"]
    check = "--check" in sys.argv[1:]
    src = Path(argv[0]) if argv else Path(DEFAULT_DIR)
    if not src.is_dir():
        print("not a directory:", src); return 2
    recs = gather(src)
    bykind = {}
    for r in recs:
        bykind[r["kind"]] = bykind.get(r["kind"], 0) + 1
    print(f"gathered {len(recs)} verbatim voice units from {src}  ({bykind})")
    if check:
        for r in recs[:4]:
            print(f"  [{r['kind']}|{r['ref']}] {r['text'][:120]}")
        return 0
    DATA.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n", encoding="utf-8")
    print("wrote", OUT, f"({len(recs)} units)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
