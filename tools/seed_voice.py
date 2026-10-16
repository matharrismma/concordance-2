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
DEFAULT_DIR = os.environ.get("CONCORDANCE_WRITING_DIR", "").strip()  # your writing folder; no personal path baked in
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


# ── THE BOOKS — his narrative voice, widening the vocabulary (Matt, 2026-10-14: "build from the books a
# decent vocabulary"). A novel is NOT pastoral address: it carries DIALOGUE (a character's voice, not
# Matt's own) and dark/violent moments that must never surface as "a word on this" to someone hurting. So
# the book ingest is hard-guarded — skip dialogue, skip a graphic stoplist, keep only clean reflective
# sentences — and tiered BELOW the Christian writing. Verbatim units only; never style-mimicry.
_DIALOGUE = re.compile(r"[“”\"]")                       # a double-quote => dialogue, a character speaks
_DARK = re.compile(r"\b(kill(ed|ing|s)?|murder|blood(y|ied)?|corpse|rape|slaughter|gun|knife|stab|"
                   r"damn(ed|it)?|bastard|whore|bitch|fuck|shit|naked|sex|breast|thigh|drunk|whiskey|"
                   r"vomit|piss|rot(ting|ted)?|maggot|scream(ed|ing)?|torture)\b", re.I)
_SENT = re.compile(r"[^.!?]*[.!?]")


def _book_ok(s: str) -> bool:
    s = s.strip()
    if not (40 <= len(s) <= 240):
        return False
    if s[-1] not in ".!?" or s[0].islower():
        return False
    if _DIALOGUE.search(s) or _DARK.search(s):
        return False
    letters = sum(c.isalpha() for c in s)
    if letters < 0.6 * len(s):                                   # tables / headers / junk
        return False
    caps = sum(1 for w in s.split() if w[:1].isupper())
    if caps > 0.4 * max(1, len(s.split())):                      # name/place-heavy narration — skip
        return False
    return True


def _epub_text(path: Path) -> str:
    import zipfile
    import html as _html
    out = []
    try:
        with zipfile.ZipFile(str(path)) as z:
            names = [n for n in z.namelist() if n.lower().endswith((".xhtml", ".html", ".htm"))]
            for n in sorted(names):
                try:
                    raw = z.read(n).decode("utf-8", "ignore")
                except Exception:  # noqa: BLE001
                    continue
                raw = re.sub(r"(?is)<(script|style|head)[^>]*>.*?</\1>", " ", raw)
                raw = re.sub(r"(?s)<[^>]+>", " ", raw)
                out.append(_html.unescape(raw))
    except Exception as e:  # noqa: BLE001
        print("  epub read failed:", path.name, e)
    return " ".join(" ".join(x.split()) for x in out)


def _from_book(path: Path) -> List[Dict]:
    title = re.sub(r"\s*[—-].*$", "", path.stem).strip() or path.stem
    if path.suffix.lower() == ".epub":
        text = _epub_text(path)
    else:
        import docx
        text = " ".join(p.text for p in docx.Document(str(path)).paragraphs)
        text = " ".join(text.split())
    out, k = [], 0
    for m in _SENT.finditer(text):
        s = m.group(0).strip()
        if _book_ok(s):
            out.append({"id": f"voice_book_{_slug(title)}_{k}", "text": s,
                        "source": f"{title} (M.R. Harris)", "ref": "", "kind": "book", "by": _BY})
            k += 1
    return out


# NOVELS ONLY — AN ALLOWLIST, safe by default. The source directory MIXES his fiction with
# CONFIDENTIAL business, engineering, and planning documents (private design bibles, planning and
# assessment memos, series maps, and the like). A stoplist is whack-a-mole and one miss leaks
# confidential material into a public voice, so NOTHING enters unless its title is a KNOWN NOVEL.
# Everything excluded is printed, so a novel missing from this list is visible and Matt can add it —
# never silently dropped, never silently leaked. Fragments matched case-insensitively.
_NOVELS = (
    "apokalypsis", "the door", "root access", "the keeping", "the line", "dancing plague",
    "tell me you got that", "treebound", "molasses", "kings of appalachia",
)


def _is_novel(stem: str) -> bool:
    s = " ".join(re.sub(r"[_\-–—]", " ", stem.lower()).split())
    return any(n in s for n in _NOVELS)


def gather_books(dirs: List[Path]) -> List[Dict]:
    recs: List[Dict] = []
    kept, skipped = [], []
    for d in dirs:
        if not d.is_dir():
            continue
        for f in sorted(list(d.glob("*.epub")) + list(d.glob("*.docx"))):
            if _is_novel(f.stem):
                kept.append(f.name)
                recs += _from_book(f)
            else:
                skipped.append(f.name)
    if skipped:
        print("  EXCLUDED (not on the novel allowlist — add a title to _NOVELS if it belongs):")
        for n in skipped:
            print("    -", n)
    seen, uniq = set(), []
    for r in recs:
        key = r["text"][:160].lower()
        if key not in seen:
            seen.add(key); uniq.append(r)
    return uniq


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


# Book directories live outside this repo; set CONCORDANCE_BOOKS_DIRS (os.pathsep-separated) or pass
# dirs as argv. No personal path baked into this public tool.
_BOOK_DIRS = [Path(p) for p in os.environ.get("CONCORDANCE_BOOKS_DIRS", "").split(os.pathsep) if p.strip()]
BOOK_OUT = DATA / "voice_book_lines.jsonl"


def main() -> int:
    argv = [a for a in sys.argv[1:] if a != "--check"]
    check = "--check" in sys.argv[1:]
    if argv and argv[0] == "books":
        dirs = [Path(a) for a in argv[1:]] or _BOOK_DIRS
        recs = gather_books(dirs)
        bysrc = {}
        for r in recs:
            bysrc[r["source"]] = bysrc.get(r["source"], 0) + 1
        print(f"gathered {len(recs)} clean reflective units from {len(dirs)} book dir(s)")
        for s in sorted(bysrc, key=lambda k: -bysrc[k])[:12]:
            print(f"  {bysrc[s]:4}  {s}")
        if check:
            import random
            random.seed(7)
            print("--- random samples (what would be voiced) ---")
            for r in random.sample(recs, min(10, len(recs))):
                print(f"  [{r['source'][:28]:28}] {r['text']}")
            return 0
        DATA.mkdir(parents=True, exist_ok=True)
        BOOK_OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n", encoding="utf-8")
        print("wrote", BOOK_OUT, f"({len(recs)} units)")
        return 0
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
