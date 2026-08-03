#!/usr/bin/env python3
"""THE FLOOR, DRAWN — one page where the gaps are visible instead of counted.

    PYTHONPATH=src python tools/floor_map.py            # writes site/theories.html
    PYTHONPATH=src python tools/floor_map.py --stdout   # the gap report only

Matt, 2026-08-02: *"We may be able to see gaps if we create a visual and be able to source a
theory that fills the gap."*

A list of 110 theories cannot show you what is missing — you would have to already know. A
DRAWING can: a sector with three nodes beside one with twenty says "this side of reality is
thinly held" without anyone having to suspect it first. So the map is not decoration; it is the
gap-finding instrument, and every mark on it is a measurement:

    where a node sits    its section of knowledge (mathematics, physical, life, applied) —
                         sectors of one circle, because the floor is one body
    how big it is        how many theories it is joined to; a lone dot has one relation and is
                         a beam resting on almost nothing
    how bright it is     DEPTH — how much the card actually says beyond the assay template.
                         Measured 2026-08-02: all 110 carry template only, so today the whole
                         map is dim, and that dimness IS the finding. When the cards are
                         enriched the map lights up, and anyone can see how far that work got.
    the chords           edges. A chord crossing the circle is a cross-domain alignment; a
                         short arc is a within-field dependency. The crossing chords are the
                         thing this project exists to find, so they are drawn brightest.

Sovereign: stdlib only, one self-contained file, no fonts to fetch and no third-party anything —
the DRAWING is inline SVG, so the map itself renders with scripting off or the network down.

It loads exactly two same-origin scripts, `/nh-home.js` and `/nh-tools.js` — the shared home
control and the Ctrl-K palette that every page here carries, injected identically everywhere so
they cannot drift per page. That is why this page must not hand-roll its own link instead.

TWO DEFECTS, BOTH MINE, BOTH CAUGHT BY THE HOUSE RULES RATHER THAN BY ME (2026-08-02):

  1. THIS TOOL WROTE OVER A LIVE PAGE. Its first version emitted `site/floor.html` — an address
     already held by "The Floor of Discovery" (commits 5f2d361, 5a5b3e7), the reader's page on
     Scripture and the created order as one design. Same word, different page, and I never
     looked at the target before writing it. Recovered from git; the map now lives at
     `site/theories.html` and the two are linked to each other, because they ARE the same
     doctrine at two depths — the seeds mapped make a floor of reality (Proverbs 9:10). The
     lesson is older than the bug: LOOK AT WHAT YOU ARE ABOUT TO OVERWRITE. A generator that
     picks its own output path is a destructive act wearing a build step's clothes.
  2. NO WAY HOME. `tests/test_site.py::test_every_page_offers_a_way_home` failed gate 76 on this
     page, and its sibling caught the missing palette straight after. A reader landing here from
     a search result could see the floor and not get back to the desk.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

RELATIONS = ("rests_on", "limits", "same_form")

# The four quarters of the catalogue, in the order a floor is laid: the formal ground first, then
# the physical world it describes, then life, then what people build with it.
# READ OFF THE SHELF, NOT GUESSED. The first version invented four section names, matched 44 of
# 110 cards, and dropped the other 66 into "?" -- a drawing that would have shown a phantom gap
# belonging to me rather than to the floor. An instrument that mistakes its own vocabulary for a
# finding accuses the thing it measures; the sections below are the ones the cards actually carry.
SECTIONS = ["Mathematics & formal reasoning", "Physics & energy", "Chemistry & materials",
            "Life sciences", "Earth & space", "Applied & human systems", "Humanities & witness",
            "Applied and social sciences", "Physical sciences"]
SECTION_COLOR = {
    "Mathematics & formal reasoning": "#c69a4a",
    "Physics & energy": "#6f9ec6",
    "Physical sciences": "#6f9ec6",
    "Chemistry & materials": "#9b7fc6",
    "Life sciences": "#7fb069",
    "Earth & space": "#5fa8a0",
    "Applied & human systems": "#c67f6f",
    "Applied and social sciences": "#c67f6f",
    "Humanities & witness": "#c6a86f",
    "?": "#8a8378",
}
REL_COLOR = {"rests_on": "#8a7a55", "limits": "#a5544a", "same_form": "#4a7fa5"}

# The template every assay card carries. Depth is what a card says BEYOND it — the sentence a
# reader would actually learn something from.
_TEMPLATE_MARK = "an engine domain that can touch it"


def _load(path):
    th = {}
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        try:
            c = json.loads(line)
        except ValueError:
            continue
        if c.get("shelf") == "theories":
            th[c["id"]] = c
    return th


def _edges(th):
    out = []
    for cid, c in th.items():
        for e in (c.get("connections") or []):
            if e.get("relationship") in RELATIONS and str(e.get("to_card_id")) in th:
                out.append((cid, e["relationship"], str(e.get("to_card_id"))))
    return out


def _depth(card) -> float:
    """0.0 -> nothing but the template; 1.0 -> a card that genuinely explains itself.

    Deliberately crude and honest: the template is a known fixed preamble, so what exceeds it is
    the card's own substance. A cleverer metric would be a place to hide a flattering number.
    """
    body = str(card.get("body") or "")
    if _TEMPLATE_MARK not in body:
        return min(1.0, len(body) / 800.0)
    tail = body.split("Calibration:", 1)[-1]
    # the calibration sentence itself is boilerplate; anything past it is the card's own
    for marker in ("never HOLDS.", "seal them.", "map-only", "seals"):
        if marker in tail:
            tail = tail.split(marker, 1)[-1]
            break
    return min(1.0, max(0.0, len(tail.strip()) / 400.0))


def gaps(th, edges):
    """What the drawing shows, said in words — so the finding survives without the picture."""
    deg = defaultdict(int)
    for a, _r, b in edges:
        deg[a] += 1
        deg[b] += 1
    by_section = defaultdict(list)
    by_domain = defaultdict(list)
    for cid, c in th.items():
        by_section[(c.get("extra") or {}).get("section") or "?"].append(cid)
        by_domain[(c.get("source") or {}).get("domain") or "?"].append(cid)
    thin = sorted((cid for cid in th if deg[cid] <= 1),
                  key=lambda cid: str(th[cid].get("title")))
    lone_domains = sorted(d for d, ids in by_domain.items() if len(ids) == 1)
    depths = {cid: _depth(c) for cid, c in th.items()}
    shallow = sum(1 for v in depths.values() if v < 0.05)
    return {
        "theories": len(th), "edges": len(edges),
        "sections": {s: len(by_section.get(s, [])) for s in SECTIONS + ["?"]},
        "thin": thin, "lone_domains": lone_domains,
        "median_degree": sorted(deg[cid] for cid in th)[len(th) // 2] if th else 0,
        "shallow": shallow,
        "cross_domain": len({((th[a].get("source") or {}).get("domain"),
                              (th[b].get("source") or {}).get("domain"))
                             for a, _r, b in edges
                             if (th[a].get("source") or {}).get("domain")
                             != (th[b].get("source") or {}).get("domain")}),
    }


def svg(th, edges, W=1100, H=1100):
    cx, cy, R = W / 2, H / 2 + 10, min(W, H) * 0.38
    order, pos = [], {}
    grouped = defaultdict(list)
    for cid, c in th.items():
        grouped[(c.get("extra") or {}).get("section") or "?"].append(cid)
    sections = [s for s in SECTIONS if grouped.get(s)] + \
               [s for s in grouped if s not in SECTIONS]
    for s in sections:
        order.extend(sorted(grouped[s], key=lambda i: str(th[i].get("title"))))

    n = max(1, len(order))
    gap = 0.035                                   # a wedge of blank between sections, so the
    idx, start = 0, -math.pi / 2                  # quarters read as quarters
    seg = (2 * math.pi - gap * len(sections)) / n
    section_span = {}
    for s in sections:
        a0 = start + idx * seg + sections.index(s) * gap
        for k, cid in enumerate(sorted(grouped[s], key=lambda i: str(th[i].get("title")))):
            ang = a0 + k * seg
            pos[cid] = (cx + R * math.cos(ang), cy + R * math.sin(ang), ang)
        section_span[s] = (a0, a0 + max(0, len(grouped[s]) - 1) * seg)
        idx += len(grouped[s])

    deg = defaultdict(int)
    for a, _r, b in edges:
        deg[a] += 1
        deg[b] += 1

    parts = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
             f'role="img" aria-label="The floor: {len(th)} theories joined by {len(edges)} '
             f'relations across the sciences">']
    parts.append('<rect width="100%" height="100%" fill="#12100c"/>')

    # section arcs + labels
    for s in sections:
        a0, a1 = section_span[s]
        col = SECTION_COLOR.get(s, "#8a8378")
        rr = R + 46
        x0, y0 = cx + rr * math.cos(a0), cy + rr * math.sin(a0)
        x1, y1 = cx + rr * math.cos(a1), cy + rr * math.sin(a1)
        large = 1 if (a1 - a0) > math.pi else 0
        parts.append(f'<path d="M {x0:.1f} {y0:.1f} A {rr:.1f} {rr:.1f} 0 {large} 1 '
                     f'{x1:.1f} {y1:.1f}" fill="none" stroke="{col}" stroke-width="3" '
                     f'opacity=".55"/>')
        am = (a0 + a1) / 2
        lx, ly = cx + (R + 74) * math.cos(am), cy + (R + 74) * math.sin(am)
        anchor = "start" if math.cos(am) > 0.2 else ("end" if math.cos(am) < -0.2 else "middle")
        parts.append(f'<text x="{lx:.0f}" y="{ly:.0f}" fill="{col}" font-size="15" '
                     f'font-family="Georgia,serif" text-anchor="{anchor}" opacity=".92">'
                     f'{s.split("&")[0].strip()} <tspan opacity=".6">({len(grouped[s])})</tspan></text>')

    # the chords: cross-domain drawn brightest, because they are the point
    for a, rel, b in edges:
        if a not in pos or b not in pos:
            continue
        x1, y1, _ = pos[a]
        x2, y2, _ = pos[b]
        da = (th[a].get("source") or {}).get("domain")
        db = (th[b].get("source") or {}).get("domain")
        cross = da != db
        col = REL_COLOR.get(rel, "#8a7a55")
        parts.append(f'<path d="M {x1:.1f} {y1:.1f} Q {cx:.1f} {cy:.1f} {x2:.1f} {y2:.1f}" '
                     f'fill="none" stroke="{col}" stroke-width="{1.5 if cross else 0.9}" '
                     f'opacity="{0.62 if cross else 0.24}"/>')

    # the nodes: size = how many relations, brightness = depth
    for cid in order:
        x, y, ang = pos[cid]
        c = th[cid]
        s = (c.get("extra") or {}).get("section") or "?"
        col = SECTION_COLOR.get(s, "#8a8378")
        r = 3.2 + min(9.0, deg[cid] * 0.85)
        d = _depth(c)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{col}" '
                     f'opacity="{0.30 + 0.65 * d:.2f}" stroke="#12100c" stroke-width="1"/>')
        if deg[cid] <= 1:      # a beam resting on almost nothing — marked so it cannot hide
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r + 5:.1f}" fill="none" '
                         f'stroke="#d9534f" stroke-width="1.4" opacity=".85"/>')
        t = str(c.get("title") or "").split("(")[0].strip()[:26]
        deg_ = math.degrees(ang)
        flip = 90 < (deg_ % 360) < 270
        rot = deg_ + 180 if flip else deg_
        anchor = "end" if flip else "start"
        off = -(r + 7) if flip else (r + 7)
        parts.append(f'<text x="{x:.1f}" y="{y:.1f}" fill="#e8dfc9" font-size="9.5" '
                     f'font-family="Georgia,serif" opacity=".78" text-anchor="{anchor}" '
                     f'transform="rotate({rot:.1f} {x:.1f} {y:.1f}) translate({off:.1f} 3)">'
                     f'{_esc(t)}</text>')

    parts.append(f'<text x="{cx:.0f}" y="{cy - 10:.0f}" fill="#c69a4a" font-size="26" '
                 f'font-family="Georgia,serif" text-anchor="middle">THE FLOOR</text>')
    parts.append(f'<text x="{cx:.0f}" y="{cy + 16:.0f}" fill="#8a8378" font-size="13" '
                 f'font-family="Georgia,serif" text-anchor="middle">'
                 f'{len(th)} theories &#183; {len(edges)} relations &#183; one body</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def page(th, edges, g):
    thin_list = "".join(
        f"<li>{_esc(str(th[c].get('title')))} "
        f"<span class=dim>&#183; {(th[c].get('source') or {}).get('domain')}</span></li>"
        for c in g["thin"][:20])
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>The Floor &#8212; the assembled theories, and where they are thin</title>
<meta name=description content="Every theory the sciences run on, joined by what it rests on,
what limits it, and what shares its form &#8212; drawn so the gaps are visible.">
<style>
 body{{margin:0;background:#12100c;color:#e8dfc9;font-family:Georgia,'Iowan Old Style',serif}}
 /* top padding clears the FIXED home control injected by nh-home.js (it sits at top:.75rem and
    is ~29px tall, so it occupies y 12-41). Pages with their own top nav get this for free; this
    one has no nav, so it must make the room itself -- measured, not guessed: at 1.4rem the h1
    overlapped the Home button by 15px and "The Floor" rendered clipped. */
 .wrap{{max-width:1180px;margin:0 auto;padding:3.2rem 1.1rem 3rem}}
 h1{{font-weight:400;font-size:1.7rem;color:#c69a4a;margin:.2rem 0 .3rem}}
 p.lede{{color:#a99c82;max-width:44rem;line-height:1.6;margin:.2rem 0 1.2rem}}
 svg{{width:100%;height:auto;display:block}}
 .legend{{display:flex;flex-wrap:wrap;gap:1.1rem;margin:.6rem 0 1.4rem;font-size:.82rem;color:#a99c82}}
 .k{{display:inline-block;width:26px;height:3px;vertical-align:middle;margin-right:.35rem}}
 .panel{{border:1px solid #2e2a22;border-radius:8px;padding:.9rem 1.1rem;margin:1rem 0;
        background:#171410}}
 .panel h2{{font-size:1rem;font-weight:400;color:#c69a4a;margin:.1rem 0 .5rem}}
 ul{{margin:.3rem 0;padding-left:1.1rem;line-height:1.65}} li{{font-size:.9rem}}
 .dim{{color:#7d745f}} .num{{color:#e8dfc9}}
 table{{border-collapse:collapse;font-size:.9rem}} td{{padding:.15rem .9rem .15rem 0}}
</style></head><body><div class=wrap>
<h1>The Floor</h1>
<p class=lede>Every theory the sciences and mathematics actually run on, joined by what it
<b>rests on</b>, what <b>limits</b> it, and what <b>shares its form</b>. One body, so you can walk
from any theory to the ones holding it up. Drawn rather than listed, because a list cannot show
you what is missing &#8212; you would have to already know.</p>
<p class=lede style="font-size:.92rem">The same floor, read the other way, is
<a href="/floor.html" style="color:#c69a4a">The Floor of Discovery</a> &#8212; Scripture and the
created order as one design. That page is for seeing it; this one is for walking it.</p>
{svg(th, edges)}
<div class=legend>
  <span><i class=k style="background:#8a7a55"></i>rests on</span>
  <span><i class=k style="background:#a5544a"></i>limits</span>
  <span><i class=k style="background:#4a7fa5"></i>shares a form</span>
  <span><span class=dim>node size = relations held &#183; brightness = depth of the card &#183;
  red ring = resting on almost nothing</span></span>
</div>
<div class=panel><h2>What the drawing is telling you</h2>
<table>
<tr><td>theories</td><td class=num>{g['theories']}</td></tr>
<tr><td>relations</td><td class=num>{g['edges']} &#183; every one carrying its evidence</td></tr>
<tr><td>cross-domain pairs</td><td class=num>{g['cross_domain']}</td></tr>
<tr><td>median relations per theory</td><td class=num>{g['median_degree']}</td></tr>
<tr><td>cards with real depth</td><td class=num>{g['theories'] - g['shallow']} of {g['theories']}
 &#8212; the rest carry only the assay template, which is why the map is dim</td></tr>
</table></div>
<div class=panel><h2>Thin &#8212; a beam resting on almost nothing</h2>
<p class=lede style="margin:.2rem 0 .4rem">These hold one relation or none. Not wrong; underbuilt.
Each is a place to look for what it actually stands on.</p>
<ul>{thin_list or '<li class=dim>none &#8212; every theory holds at least two relations</li>'}</ul>
</div>
<div class=panel><h2>Lone in its domain</h2>
<p class=lede style="margin:.2rem 0 .4rem">One theory covering a whole field is a field we have
barely entered.</p>
<ul>{''.join(f'<li>{_esc(d)}</li>' for d in g['lone_domains'][:30]) or '<li class=dim>none</li>'}</ul>
</div>
<p class=dim style="font-size:.8rem">Found and checked, never generated. Every relation carries the
reason it exists; a relation without one is not written.</p>
</div>
<script src="/nh-home.js"></script>
<script src="/nh-tools.js"></script>
</body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=os.path.join(ROOT, "data", "theory_cards.jsonl"))
    # NOT floor.html — that address was already taken by "The Floor of Discovery" (5f2d361,
    # 5a5b3e7), the reader's page on Scripture and the created order as one design. The first
    # version of this tool wrote straight over it. See the note at the top of this file.
    ap.add_argument("--out", default=os.path.join(ROOT, "site", "theories.html"))
    ap.add_argument("--stdout", action="store_true", help="print the gap report only")
    args = ap.parse_args()

    th = _load(args.path)
    edges = _edges(th)
    g = gaps(th, edges)

    print(f"THE FLOOR — {g['theories']} theories, {g['edges']} relations, "
          f"{g['cross_domain']} cross-domain pairs")
    print(f"  median relations per theory : {g['median_degree']}")
    print(f"  cards with real depth       : {g['theories'] - g['shallow']} / {g['theories']}")
    print(f"  sections                    : "
          + ", ".join(f"{s.split('&')[0].strip()} {n}" for s, n in g["sections"].items() if n))
    print(f"\n  THIN (<=1 relation): {len(g['thin'])}")
    for cid in g["thin"][:14]:
        print(f"     {str(th[cid].get('title'))[:58]}")
    print(f"\n  LONE IN THEIR DOMAIN: {len(g['lone_domains'])}")
    print("     " + ", ".join(g["lone_domains"][:20]))
    if args.stdout:
        return 0

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(page(th, edges, g))
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
