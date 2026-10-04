"""Migrate Bible verses into 2.0 (data, gitignored — like the keeping).

Copies verse rows the scripture verifier reads: the World English Bible (public domain) as
data/bible_en.jsonl, and — since 2026-10-04 (Matt: "agreed" to integrate Lighthouse 1.0 rather than
retire it) — the 1.0 keeping's other-language Bibles as data/bible_<lang>.jsonl, ONE FILE PER
LANGUAGE, same slim row. The deep Strong's / original-language layer (lw/00_source) is NOT migrated
here — it is a separate subsystem; this is verse-text ref-resolution only.

THE GATE IS STRICT PD-ONLY. Every 1.0 row carries license "Public Domain", but that field is 1.0's
own assertion. A translation crosses only when its public-domain status is established by its date
and author (listed below, with the reason); the rest are HELD and named — they go to the want list as
"verify the licence", never into the keeping on a self-asserted label.

    python tools/migrate_bible.py                       # WEB -> data/bible_en.jsonl (as before)
    python tools/migrate_bible.py --all                 # every PD-verified language, 1.0 data -> data/
    python tools/migrate_bible.py --lang es [--lang zh] # named languages only
    python tools/migrate_bible.py SRC.jsonl OUT.jsonl   # one explicit file (legacy form)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_LH_DATA = Path(r"C:\Users\hdven\OneDrive\Documents\Claude\Projects\Lighthouse\data")
_DEFAULT_SRC = _LH_DATA / "bible_en" / "verses.jsonl"
_OUT_DIR = Path(__file__).resolve().parent.parent / "data"

# lang -> (translation as the 1.0 rows name it, why it is public domain)
PD_VERIFIED = {
    "ar": ("Smith-Van Dyck", "1865; translators d. 1857/1895"),
    "de": ("Lutherbibel 1912", "1912 revision; PD worldwide"),
    "es": ("Reina-Valera 1909", "1909 revision; PD worldwide"),
    "fa": ("Persian Old Version (OPV)", "1895 Bruce revision"),
    "fr": ("Louis Segond 1910", "1910; Segond d. 1885"),
    "he": ("Hebrew (Leningrad-Aleppo basis)", "Masoretic text; Leningrad Codex 1008"),
    "it": ("Diodati Riveduta 1885", "Diodati 1649 / 1885 edition"),
    "ja": ("口語訳聖書 (Kogoyaku 1954/1955)", "JBS corporate work; Japanese term expired 2005, JBS released it"),
    "ko": ("Korean Bible 1910", "1910/1911 Old Korean Version"),
    "la": ("Vulgata Clementina", "1592"),
    "my": ("Judson Burmese", "1835; Judson d. 1850"),
    "nl": ("Statenvertaling", "1637"),
    "ru": ("Russian Synodal Translation", "1876"),
    "uk": ("Kulish Ukrainian 1871", "1871/1903; Kulish d. 1897"),
    "vi": ("Vietnamese 1934", "1934 Cadman; Cadman d. 1948"),
    "zh": ("Chinese Union Version (Simplified)", "1919 CUV; simplified-script transcription of a PD text"),
}
# lang -> why it is HELD (the 1.0 label says Public Domain; the edition says otherwise or is unidentified)
HELD = {
    "hi": "Indian Revised Version (Bridge Connectivity Solutions, 2017-19) is CC BY-SA 4.0, not public domain",
    "ht": "edition unidentified; the Haitian Creole 'Bib La' (1985/1999, Société Biblique Haïtienne) is copyrighted",
    "pt": "'Bíblia Portuguesa Mundial' edition unidentified (not Almeida 1911); verify before keeping",
    "ro": "Cornilescu 1924: Cornilescu d. 1975 and the Societatea Biblică asserts copyright — contested, so held",
    "sw": "Kiswahili Contemporary Version (Biblica) is licensed, not public domain",
}

_FIELDS = ("book", "book_abbr", "chapter", "verse", "text", "translation", "lang", "year", "license")


def _convert(src: Path, out: Path, lang: str) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(src, encoding="utf-8") as r, open(out, "w", encoding="utf-8") as w:
        for line in r:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("book") and d.get("chapter") is not None and d.get("verse") is not None:
                row = {k: d.get(k) for k in _FIELDS}
                row["text"] = d.get("text", "")
                row["lang"] = d.get("lang") or lang
                w.write(json.dumps(row, ensure_ascii=False) + "\n")
                n += 1
    return n


def main() -> int:
    argv = sys.argv[1:]
    if "--all" in argv or "--lang" in argv:
        langs = list(PD_VERIFIED) if "--all" in argv else [argv[i + 1] for i, a in enumerate(argv) if a == "--lang"]
        rc = 0
        for lang in langs:
            if lang in HELD:
                print(f"HELD  {lang}: {HELD[lang]}")
                continue
            if lang not in PD_VERIFIED and lang != "en":
                print(f"SKIP  {lang}: not on the PD-verified list — establish the licence first")
                rc = 1
                continue
            src = _LH_DATA / f"bible_{lang}" / "verses.jsonl"
            if not src.exists():
                print(f"MISS  {lang}: {src}")
                rc = 1
                continue
            n = _convert(src, _OUT_DIR / f"bible_{lang}.jsonl", lang)
            print(f"wrote {lang}: {n} verses ({PD_VERIFIED.get(lang, ('WEB', ''))[0]}) -> data/bible_{lang}.jsonl")
        for lang, why in HELD.items():
            if "--all" in argv:
                print(f"HELD  {lang}: {why}")
        return rc
    src = Path(argv[0]) if argv else _DEFAULT_SRC
    out = Path(argv[1]) if len(argv) > 1 else (_OUT_DIR / "bible_en.jsonl")
    if not src.exists():
        print(f"source not found: {src}")
        return 1
    n = _convert(src, out, "en")
    print(f"wrote {n} verses -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
