#!/usr/bin/env python3
"""Card the Library of Congress Federal Research Division COUNTRY STUDIES — the public-domain original.

Matt, 2026-09-26 ("build the CREST seeder", area/country studies first): the declassified/PD country
reference the dig pointed at. The FRD Country Studies (many began as declassified US Army DA-Pam-550
Area Handbooks) are US-government works — public domain (17 U.S.C. §105) — and loc.gov states it plainly
per item: "The Library of Congress is not aware of any U.S. copyright protection ... in the material."

SOURCE = THE PD ORIGINAL, not a mirror or a restricted scan (look-before-build, 2026-09-26):
  * Internet Archive "country study" scans are mostly ACCESS-RESTRICTED lending copies and mix PD FRD
    works with COMMERCIAL lookalikes (Int'l Business Publications) — license-unsafe.
  * countrystudies.us asserts its OWN copyright — never anchor in a mirror.
  * loc.gov IS the PD original and is fetchable: `?fo=json` (browser UA) enumerates the collection;
    each item's resource carries a whole-book OCR text file (`fulltext_file`, *.text.txt).

License-by-source guard: a country is carded ONLY when its loc.gov item declares the FRD/PD rights
("not aware of any U.S. copyright") AND is `partof` "federal research division". Conduit, not author:
each card is a real FRD study, credited, generated=False, linked to the full PD text + PDF. One card per
country (a clean overview + the link); the flat OCR's headings recur as running-heads, so chapter-level
splitting is deferred until structured text is in hand — form first, not a fuzzy split.

    python tools/card_country_studies.py --list          # list the studies, write nothing
    python tools/card_country_studies.py --one <lccn>     # one study (prototype / inspect quality)
    python tools/card_country_studies.py --all            # the whole shelf (network-heavy)
    python tools/card_country_studies.py --all --resume   # keep those already carded, fetch the rest
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_country_studies"
_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/120 Safari/537.36"}
_COLL = "https://www.loc.gov/collections/country-studies/?fo=json&c=50&sp=%d"
_slug = re.compile(r"[^a-z0-9]+")

# front-matter / apparatus a country's narrative is NOT — skip these paragraphs when hunting the overview
_DROP = re.compile(
    r"^(figure|table|source:|see figure|see table|chapter|part [ivx]|appendix|glossary|bibliography|"
    r"index|contents|library of congress|federal research division|research completed|edited by|"
    r"on the cover|for sale by|catalog|data as of|foreword|acknowledgments|acknowledgements|preface)\b",
    re.I)
# the series boilerplate + cataloging apparatus (identical across volumes) — not country substance
_BOILER = re.compile(
    r"continuing series of (?:books|volumes)|country studies[/ ]area handbook|most books in the series|"
    r"prepared by the federal research division|sole responsibility of|area handbook series|"
    r"\bissn\b|\bda pam\b|superintendent of documents|for sale by|supersedes the|coauthored|"
    r"library of congress cataloging|research completed|data as of|edited by", re.I)
# book-MAKING meta prose (foreword/acknowledgments/preface) — about the volume, not about the country
_META = re.compile(
    r"\bthe authors?\b|wish to (?:thank|acknowledge|express)|grateful to|gratitude to|"
    r"members of the staff|of the manuscript|preparation of (?:the|this)|contributed to|"
    r"this (?:study|volume|book|edition) (?:is|was|attempts|represents|replaces|supersedes)|"
    r"the reader (?:is|should)|reflect the views|do not necessarily|acknowledg", re.I)


def _sk(s: str) -> str:
    return _slug.sub("_", s.lower()).strip("_")


_LAST = [0.0]
_MIN_GAP = 6.0          # loc.gov rate-limits HARD (escalating 429s); be a polite guest — wide, steady spacing


def _get(url: str, tries: int = 6, want_json: bool = True):
    """Fetch with politeness: a steady minimum gap between calls, and a LONG back-off on 429
    (Too Many Requests) — respecting Retry-After when given — so the whole shelf lands without a ban."""
    last = None
    for i in range(tries):
        gap = _MIN_GAP - (time.time() - _LAST[0])
        if gap > 0:
            time.sleep(gap)
        _LAST[0] = time.time()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=60) as r:
                raw = r.read().decode("utf-8", "replace")
                return json.loads(raw) if want_json else raw
        except urllib.error.HTTPError as e:  # noqa: PERF203
            last = e
            if e.code == 429:
                ra = e.headers.get("Retry-After") if e.headers else None
                wait = int(ra) if (ra and str(ra).isdigit()) else 45 * (i + 1)
                print(f"    429 rate-limited; backing off {wait}s", file=sys.stderr)
                time.sleep(min(wait, 240))
            elif e.code in (500, 502, 503, 504):
                time.sleep(5 * (i + 1))
            else:
                raise                      # 404 etc. — a real miss, not worth retrying
        except Exception as e:  # noqa: BLE001 — transient network; back off and retry
            last = e
            time.sleep(3 * (i + 1))
    raise last


def _items():
    """Every country-study ITEM (paged), with title + item url. Rights/text are read per item later."""
    sp = 1
    seen = 0
    while True:
        d = _get(_COLL % sp)
        results = d.get("results") or []
        if not results:
            break
        for r in results:
            url = r.get("id") or r.get("url") or ""
            if "/item/" in url and (r.get("title") or "").lower().find("country stud") >= 0 \
                    or (r.get("title") or "").lower().endswith("country study") \
                    or " country stud" in (r.get("title") or "").lower():
                yield url.rstrip("/") + "/", r.get("title") or ""
                seen += 1
        total = (d.get("pagination") or {}).get("of") or 0
        sp += 1
        if sp > 20 or seen >= (total or 999):
            break


def _country_name(title: str) -> str:
    """'Austria : a country study' -> 'Austria'."""
    t = re.split(r"[:;]", title)[0]
    return re.sub(r"\s+", " ", t).strip()


def _clean_overview(text: str, country: str) -> str:
    """The first substantial COUNTRY-SPECIFIC narrative, cleaned — skipping title page, cataloging block,
    table of contents, captions and the identical series foreword. The country-specificity gate is the
    key: a picked paragraph must NAME the country (or its adjective), which the series/cataloging
    boilerplate never does. The OpenStax quality bar: real prose, capped; the card links to the full
    text, so the body is the recall hook, not the whole book."""
    # country-mention test: the name, and a rough adjective (Austria->Austri, Germany->German, ...)
    low_country = country.lower()
    stem = re.sub(r"(a|land|ia|y)$", "", low_country) or low_country
    def _about(p_low: str) -> bool:
        return low_country in p_low or (len(stem) >= 4 and stem in p_low)

    paras = re.split(r"\n\s*\n", text)
    picked = []
    for p in paras:
        p = re.sub(r"[ \t]+", " ", p)
        p = re.sub(r"\s*\n\s*", " ", p).strip()
        if len(p) < 320:                       # headers, captions, ToC lines, page numbers
            continue
        if _DROP.match(p) or _BOILER.search(p) or _META.search(p):
            continue
        if p.count(". ") < 3:                   # must read like narrative, not a list/caption block
            continue
        letters = sum(c.isalpha() or c.isspace() for c in p)
        if letters / max(1, len(p)) < 0.86:     # OCR garble / tabular noise (tightened)
            continue
        if re.search(r"\.\s*\.\s*\.|\.{3,}", p):  # dot-leaders => table of contents / index
            continue
        if sum(c.isdigit() for c in p) / max(1, len(p)) > 0.02:  # page numbers => ToC / tables / stats block
            continue
        caps = re.findall(r"\b[A-Z]{2,}\b", p)   # ALL-CAPS runs => ToC headings / figure labels
        if len(caps) > 4:
            continue
        if not _about(p.lower()):               # THE GATE: must be about THIS country, not boilerplate
            continue
        picked.append(p)
        if sum(len(x) for x in picked) > 2400:
            break
    body = re.sub(r"\s+", " ", " ".join(picked)).strip()
    return body[:2400]


def card_country(item_url: str, title: str, min_chars: int = 400):
    """Fetch one FRD study, verify PD rights (license-by-source), and mint ONE overview card + link."""
    d = _get(item_url + "?fo=json")
    item = d.get("item") or {}
    it = item.get("title")
    if isinstance(it, list):
        it = it[0] if it else ""
    title = it or title                        # prefer the item's own title (the collection row may be terse)
    rights = " ".join(item.get("rights") or []) if isinstance(item.get("rights"), list) else str(item.get("rights") or "")
    partof = " ".join(str(x) for x in (item.get("partof") or [])).lower() if isinstance(item.get("partof"), list) else str(item.get("partof") or "").lower()
    # THE LICENSE-BY-SOURCE GATE: only the PD FRD original, never a commercial lookalike or a scan we
    # cannot confirm PD. loc.gov states the FRD rights per item; require it, and the FRD provenance.
    if "not aware of any u.s. copyright" not in rights.lower():
        print(f"  SKIP (rights not confirmed PD): {title}", file=sys.stderr)
        return None
    if "federal research division" not in partof and "country studies" not in partof:
        print(f"  SKIP (not the FRD country-studies collection): {title}", file=sys.stderr)
        return None
    res = (d.get("resources") or [{}])[0]
    ft_url = res.get("fulltext_file")
    if not ft_url:
        print(f"  SKIP (no full-text file): {title}", file=sys.stderr)
        return None
    country = _country_name(title)
    text = _get(ft_url, want_json=False)
    body = _clean_overview(text, country)
    if len(body) < min_chars:
        print(f"  SKIP (overview too thin: {len(body)} chars): {title}", file=sys.stderr)
        return None
    created = "; ".join(item.get("created_published") or []) if isinstance(item.get("created_published"), list) else str(item.get("created_published") or "")
    year = ""
    m = re.search(r"(19|20)\d{2}", created)
    if m:
        year = m.group(0)
    name_bands = [w for w in re.split(r"[^a-z0-9]+", country.lower()) if len(w) > 2]
    return {
        "id": f"card_src_frd_{_sk(country)[:40]}", "kind": "reference",
        "title": f"{country}: A Country Study",
        "body": body,
        "source": {"label": f"{country}: A Country Study — Federal Research Division, Library of Congress"
                            + (f" ({year})" if year else "") + " (public domain)",
                   "url": item_url, "domain": "reference", "authority_tier": "reference"},
        "shelf": "countries", "box": "country_study",
        "bands": name_bands + ["country study", "federal research division", "frd", "area handbook",
                               "reference", "geography", "history", "public domain"],
        "subject": country,
        "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                         "evidence": f"the Federal Research Division country study of {country}"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
        "extra": {"loc_item": item_url, "fulltext": ft_url, "pdf": res.get("pdf") or "",
                  "year": year, "license": "PD (US government work, 17 U.S.C. §105)",
                  "series": "LoC Federal Research Division Country Studies / US Army Area Handbook"},
    }


def _spine_card() -> dict:
    return {
        "id": SPINE, "kind": "reference", "title": "The Country Studies",
        "body": ("The Federal Research Division Country Studies (and the US Army Area Handbook series they "
                 "grew from): reference studies of the nations — historical setting, society, economy, "
                 "government and politics, and national security — prepared by the Library of Congress for "
                 "the US government and released to the public domain. Gathered and credited, one study per "
                 "country, each linked to its full public-domain text."),
        "source": {"label": "LoC Federal Research Division — Country Studies (public domain)",
                   "url": "https://www.loc.gov/collections/country-studies/", "domain": "reference",
                   "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["country studies", "federal research division", "frd", "area handbook", "nations",
                  "geography", "reference", "public domain", "spine"],
        "subject": "the country studies",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "the country studies, a shelf of the Floor of Discovery"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--one", help="one item url or lccn (prototype/inspect)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--resume", action="store_true", help="keep countries already carded, fetch the rest")
    ap.add_argument("--cooldown", type=int, default=0,
                    help="sleep N seconds before starting (let loc.gov's rate-limit reset after a block)")
    args = ap.parse_args()
    if args.cooldown > 0:
        print(f"  cooldown: waiting {args.cooldown}s for the rate-limit to reset before starting…",
              flush=True)
        time.sleep(args.cooldown)

    if args.list:
        n = 0
        for url, title in _items():
            print(f"  {title:48s} {url}")
            n += 1
        print(f"total: {n} country studies")
        return 0

    out = Path("data")
    out.mkdir(parents=True, exist_ok=True)
    (out / "country_studies_spine.jsonl").write_text(
        json.dumps(_spine_card(), ensure_ascii=False) + "\n", encoding="utf-8")

    if args.one:
        url = args.one if args.one.startswith("http") else f"https://www.loc.gov/item/{args.one}/"
        c = card_country(url.rstrip("/") + "/", "prototype : a country study")
        if c:
            print(json.dumps({"id": c["id"], "title": c["title"], "body_len": len(c["body"]),
                              "body_head": c["body"][:300]}, ensure_ascii=False, indent=1))
        return 0 if c else 1

    if not args.all:
        print("give --list, --one <lccn|url>, or --all", file=sys.stderr)
        return 2

    final = out / "country_studies_cards.jsonl"
    kept: list = []          # carded cards, in hand — always finalized, even if the run is cut short
    done = set()
    if args.resume and final.exists():
        for line in final.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            kept.append(line)
            try:
                done.add(json.loads(line).get("id"))
            except Exception:  # noqa: BLE001
                pass
        print(f"  [resume] kept {len(kept)} already carded")

    # Enumerate the whole shelf FIRST (robust: a rate-limit mid-pagination must not lose the list).
    try:
        items = list(_items())
    except Exception as e:  # noqa: BLE001
        print(f"  enumeration stopped early ({type(e).__name__}: {e}); proceeding with what we have",
              file=sys.stderr)
        items = []

    def _finalize():
        final.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")

    try:
        for url, title in items:
            probe_id = f"card_src_frd_{_sk(_country_name(title))[:40]}"
            if probe_id in done:
                continue
            try:
                c = card_country(url, title)
            except Exception as e:  # noqa: BLE001 — one bad study (or a hard 429) must not lose the rest
                print(f"  {title}: ERROR ({type(e).__name__}: {e})", file=sys.stderr)
                continue
            if c:
                kept.append(json.dumps(c, ensure_ascii=False))
                done.add(c["id"])
                _finalize()          # persist after each card — a crash keeps every study already fetched
                print(f"  + {c['title']}  ({len(c['body'])} chars)")
    finally:
        _finalize()
    print(f"[country_studies] {len(kept)} cards -> data/country_studies_cards.jsonl  (+1 spine)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
