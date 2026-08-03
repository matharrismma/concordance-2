#!/usr/bin/env python3
"""THE FLOOR, DRAWN — one page where the gaps are visible instead of counted.

    PYTHONPATH=src python tools/theory_map.py            # writes site/theories.html
    PYTHONPATH=src python tools/theory_map.py --stdout   # the gap report only

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


def _substance(card) -> int:
    """The SAME measurement as _depth, without the ceiling: characters the card adds to the template.

    _depth() clamps at 400 chars because it answers one question -- "is this still a stub?" -- and
    for that a ceiling is right. But measured on the live page, 177 of 178 cards now peg at 1.0,
    so ORDERING by it would arrange the floor by tie-break and present the result as a finding.
    The unclamped count is the same honest quantity with its range intact.
    """
    body = str(card.get("body") or "")
    if _TEMPLATE_MARK not in body:
        return len(body)
    tail = body.split("Calibration:", 1)[-1]
    for marker in ("never HOLDS.", "seal them.", "map-only", "seals"):
        if marker in tail:
            tail = tail.split(marker, 1)[-1]
            break
    return len(tail.strip())


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


# THE GOLDEN ANGLE. 2*pi*(1 - 1/phi) ~= 137.507 degrees. Place each successive cell at this
# turn and the arrangement never repeats and never leaves a gap -- because phi is the "most
# irrational" number, the one worst approximated by any fraction, so no whole number of turns
# ever closes. A sunflower head, a pinecone and a pineapple all use it, and they use it because
# it is the packing that wastes least. It is also this floor's own subject matter arriving in the
# floor's own drawing: aperiodic order, the golden ratio of the Penrose tiling, and the honeycomb
# question of how to fill a plane.
GOLDEN_ANGLE = math.pi * (3 - math.sqrt(5))


def _hex_points(x, y, r, tilt=0.0):
    """A honeycomb cell. Six vertices, flat-topped when tilt=0."""
    return " ".join(
        "%.1f,%.1f" % (x + r * math.cos(tilt + i * math.pi / 3),
                       y + r * math.sin(tilt + i * math.pi / 3))
        for i in range(6))


def lattice(th, W=1240, H=760):
    """THE GEOMETRIC COMB — a lattice with sites that can be EMPTY, so holes are visible.

    Matt, 2026-08-03: "Close. It should be geometric, so we can use this to find what is missing."

    That is the correction, and it is exact. A phyllotactic spiral fills every position it
    creates, so it CANNOT show a gap -- however beautiful, it can only draw what exists. To find
    what is missing you need coordinates that can be VACANT.

    So the frame is the grid this project already carries: `grid.py`'s eight DIMENSIONS down, the
    catalogue's SECTIONS across, hexagonal cells with offset rows. Every site is a real question
    -- "what does this section contribute to this dimension?" -- and an empty site is that
    question with no answer on the shelf.

    AN EMPTY SITE IS A QUESTION, NOT AUTOMATICALLY A GAP, and the drawing says so rather than
    crying wolf. `metabolism x mathematics` being empty is a category that need not exist.
    `discreteness` being empty in eight of nine sections is a real hole -- and it matches the
    independent measurement that discreteness carries ONE axis where the other dimensions carry
    33 to 75. The instrument found a thin place in our own grid, which is what it is for.

    A theory appears in EVERY dimension its domain touches, so the counts sum to more than the
    number of theories. That is what a facet means, and the caption states it.
    """
    try:
        from concordance import grid, grid_atlas
        dims = list(grid.DIMENSIONS)
    except Exception:                                        # noqa: BLE001
        return ""                                            # no grid -> no lattice, say nothing
    cells = defaultdict(list)
    for cid, c in th.items():
        s = (c.get("extra") or {}).get("section") or "?"
        d = (c.get("source") or {}).get("domain")
        try:
            ds = grid_atlas.axis_dimensions(d) if d else frozenset()
        except Exception:                                    # noqa: BLE001
            ds = frozenset()
        for dim in ds:
            cells[(dim, s)].append(cid)

    secs = [s for s in SECTIONS if any((d, s) in cells for d in dims)]
    secs += sorted({s for (_d, s) in cells if s not in secs})
    if not secs:
        return ""

    hx, hy = 96.0, 76.0                        # horizontal pitch, vertical pitch
    x0, y0 = 268.0, 96.0
    R = 33.0
    parts = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
             f'aria-label="The floor as a geometric comb: eight dimensions by '
             f'{len(secs)} sections, with empty sites marking what is missing">']
    parts.append('<rect width="100%" height="100%" fill="#12100c"/>')

    for j, s in enumerate(secs):               # column headings
        col = SECTION_COLOR.get(s, "#8a8378")
        cxx = x0 + j * hx
        parts.append(f'<text x="{cxx:.0f}" y="{y0 - 44:.0f}" fill="{col}" font-size="11" '
                     f'font-family="Georgia,serif" text-anchor="middle" '
                     f'transform="rotate(-32 {cxx:.0f} {y0 - 44:.0f})">'
                     f'{_esc(s.split("&")[0].strip()[:18])}</text>')

    empty = filled = 0
    for i, dim in enumerate(dims):
        cy = y0 + i * hy
        off = (hx / 2) if i % 2 else 0.0       # offset rows -> a true honeycomb, not a chequerboard
        parts.append(f'<text x="{x0 - 74:.0f}" y="{cy + 4:.0f}" fill="#a99c82" font-size="12" '
                     f'font-family="Georgia,serif" text-anchor="end">{_esc(dim)}</text>')
        for j, s in enumerate(secs):
            cxx = x0 + j * hx + off
            here = cells.get((dim, s), [])
            if here:
                filled += 1
                col = SECTION_COLOR.get(s, "#8a8378")
                d = sum(_depth(th[c]) for c in here) / len(here)
                rad = 12.0 + min(20.0, len(here) * 1.15)
                parts.append(f'<polygon points="{_hex_points(cxx, cy, rad)}" fill="{col}" '
                             f'opacity="{0.30 + 0.62 * d:.2f}" stroke="#12100c" '
                             f'stroke-width="1.2"/>')
                parts.append(f'<text x="{cxx:.0f}" y="{cy + 4:.0f}" fill="#12100c" '
                             f'font-size="12" font-family="Georgia,serif" '
                             f'text-anchor="middle" font-weight="bold">{len(here)}</text>')
            else:
                empty += 1
                # THE HOLE. Dashed, hollow, and deliberately as visible as a filled cell -- the
                # whole reason this drawing exists is that an absence should be as legible as a
                # presence.
                parts.append(f'<polygon points="{_hex_points(cxx, cy, 20)}" fill="none" '
                             f'stroke="#d9534f" stroke-width="1.5" stroke-dasharray="4 3" '
                             f'opacity=".72"/>')

    tot = filled + empty
    parts.append(f'<text x="{x0 - 74:.0f}" y="{y0 + len(dims) * hy + 34:.0f}" fill="#c69a4a" '
                 f'font-size="15" font-family="Georgia,serif" text-anchor="end">THE COMB</text>')
    parts.append(f'<text x="{x0 - 60:.0f}" y="{y0 + len(dims) * hy + 34:.0f}" fill="#a99c82" '
                 f'font-size="12" font-family="Georgia,serif">'
                 f'{tot} sites &#183; {filled} filled &#183; '
                 f'<tspan fill="#d9534f">{empty} empty</tspan> '
                 f'&#8212; a dashed cell is a question with no answer on the shelf. A theory '
                 f'appears in every dimension its domain touches, so counts exceed '
                 f'{len(th)}.</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def svg(th, edges, W=1160, H=1160):
    """THE VORTEX OF HONEYCOMB.

    Matt, 2026-08-03: "Look at the arrangement as a vortex of honeycomb." / "most aligned to
    spiraling out."

    So the drawing was rebuilt to say something the ring could not. The old layout put every
    theory on one circle grouped by section, which showed WHICH FIELD each belonged to and hid
    the thing that actually matters -- how well each one is joined to the rest.

    Now position carries the finding. Cells are ordered by DEGREE, most-connected first, and
    placed on a phyllotactic spiral at the golden angle: the theories that align with the most
    others sit at the CENTRE, and alignment decreases as you spiral out. Distance from the middle
    IS how peripheral a theory is to the assembled floor. Section is still readable, in colour.

    Each cell is drawn as a hexagon rather than a dot, because the corpus was measured as a comb
    (3.23 walls per cell against a theoretical 3.0) and the drawing should not contradict the
    measurement.
    """
    cx, cy = W / 2, H / 2 + 6

    deg = defaultdict(int)
    for a, _r, b in edges:
        deg[a] += 1
        deg[b] += 1

    grouped = defaultdict(list)
    for cid, c in th.items():
        grouped[(c.get("extra") or {}).get("section") or "?"].append(cid)
    sections = [s for s in SECTIONS if grouped.get(s)] + \
               [s for s in grouped if s not in SECTIONS]

    # MOST ALIGNED FIRST. Ties broken by title so the drawing is deterministic -- the same floor
    # must always produce the same picture, or a diff of the SVG stops meaning anything.
    order = sorted(th, key=lambda i: (-deg[i], str(th[i].get("title"))))

    n = max(1, len(order))
    spread = min(W, H) * 0.455 / math.sqrt(n)     # r = spread*sqrt(k) keeps cell density even
    pos = {}
    for k, cid in enumerate(order):
        ang = k * GOLDEN_ANGLE
        r = spread * math.sqrt(k + 0.6)           # +0.6 lifts the first cell clear of the title
        pos[cid] = (cx + r * math.cos(ang), cy + r * math.sin(ang), ang, r)

    # id=vortex, not role=img, is what the enhancement script selects: the lattice above is ALSO
    # role="img" and is drawn first, so a role selector would have found the wrong drawing.
    parts = [f'<svg id="vortex" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
             f'role="img" aria-label="The floor as a vortex of honeycomb: {len(th)} theories '
             f'joined by {len(edges)} relations, the most-aligned at the centre spiralling out">']
    parts.append('<rect width="100%" height="100%" fill="#12100c"/>')

    # Faint rings mark where alignment falls off, so "further out = less joined" is legible
    # rather than implied.
    for q, lab in ((0.25, "most aligned"), (0.55, ""), (0.85, "least aligned")):
        rr = spread * math.sqrt(n * q)
        parts.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{rr:.0f}" fill="none" '
                     f'stroke="#2e2a22" stroke-width="1" opacity=".7"/>')
        if lab:
            parts.append(f'<text x="{cx:.0f}" y="{cy - rr - 5:.0f}" fill="#5d564a" '
                         f'font-size="10.5" font-family="Georgia,serif" text-anchor="middle">'
                         f'{lab}</text>')

    # The chords. Bowed toward the centre so the spiral stays readable; cross-domain brightest,
    # because a relation that crosses a field is the thing this floor exists to find.
    for a, rel, b in edges:
        if a not in pos or b not in pos:
            continue
        x1, y1, _a1, _r1 = pos[a]
        x2, y2, _a2, _r2 = pos[b]
        da = (th[a].get("source") or {}).get("domain")
        db = (th[b].get("source") or {}).get("domain")
        cross = da != db
        col = REL_COLOR.get(rel, "#8a7a55")
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        qx, qy = mx + (cx - mx) * 0.45, my + (cy - my) * 0.45
        parts.append(f'<path d="M {x1:.1f} {y1:.1f} Q {qx:.1f} {qy:.1f} {x2:.1f} {y2:.1f}" '
                     f'fill="none" stroke="{col}" stroke-width="{1.4 if cross else 0.85}" '
                     f'opacity="{0.55 if cross else 0.20}"/>')

    # The cells. Hexagons: size = relations, brightness = depth, colour = section.
    #
    # Each carries data-i, its index into the THEORIES payload emitted with the page. That single
    # attribute is what lets the reader click a cell and get the card, and lets the layout be
    # re-sorted from another angle — WITHOUT the page depending on JavaScript to draw anything.
    # The SVG below is complete and readable with scripting off; the script only enhances it.
    for k, cid in enumerate(order):
        x, y, ang, _r = pos[cid]
        c = th[cid]
        s = (c.get("extra") or {}).get("section") or "?"
        col = SECTION_COLOR.get(s, "#8a8378")
        rad = 4.0 + min(10.0, deg[cid] * 0.80)
        d = _depth(c)
        parts.append(f'<polygon class="cell" data-i="{k}" points="{_hex_points(x, y, rad, ang)}" '
                     f'fill="{col}" opacity="{0.32 + 0.63 * d:.2f}" stroke="#12100c" '
                     f'stroke-width="1"><title>{_esc(str(c.get("title"))[:80])}</title></polygon>')
        if deg[cid] <= 1:      # a beam resting on almost nothing — marked so it cannot hide
            parts.append(f'<polygon class="thinring" data-i="{k}" '
                         f'points="{_hex_points(x, y, rad + 5, ang)}" fill="none" '
                         f'stroke="#d9534f" stroke-width="1.3" opacity=".85"/>')

    # Label only the core. Naming all 172 on a spiral is unreadable; the centre is what the
    # layout is asserting, so the centre is what gets named.
    for cid in order[:22]:
        x, y, ang, _r = pos[cid]
        t = str(th[cid].get("title") or "").split("(")[0].strip()[:30]
        anchor = "start" if math.cos(ang) >= 0 else "end"
        off = 15 if math.cos(ang) >= 0 else -15
        parts.append(f'<text x="{x + off:.1f}" y="{y + 3:.1f}" fill="#e8dfc9" font-size="9.5" '
                     f'font-family="Georgia,serif" opacity=".82" text-anchor="{anchor}">'
                     f'{_esc(t)}</text>')

    # Section key, since colour no longer sits in contiguous arcs.
    ky = 26
    for s in sections:
        col = SECTION_COLOR.get(s, "#8a8378")
        parts.append(f'<polygon points="{_hex_points(24, ky - 3, 5.5)}" fill="{col}" '
                     f'opacity=".85"/>')
        parts.append(f'<text x="36" y="{ky:.0f}" fill="{col}" font-size="11.5" '
                     f'font-family="Georgia,serif" opacity=".9">'
                     f'{s.split("&")[0].strip()} <tspan opacity=".55">'
                     f'({len(grouped[s])})</tspan></text>')
        ky += 18

    parts.append(f'<text x="{cx:.0f}" y="{H - 34:.0f}" fill="#c69a4a" font-size="24" '
                 f'font-family="Georgia,serif" text-anchor="middle">THE FLOOR</text>')
    parts.append(f'<text x="{cx:.0f}" y="{H - 14:.0f}" fill="#8a8378" font-size="12.5" '
                 f'font-family="Georgia,serif" text-anchor="middle">'
                 f'{len(th)} theories &#183; {len(edges)} relations &#183; one body '
                 f'&#183; most aligned at the centre</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def interactive(th, edges) -> str:
    """Zoom, other angles, and a card on selection — as ENHANCEMENT, never as the page itself.

    Matt, 2026-08-03: "For the visual model, I want to be able to zoom in and view from other
    angles. Selecting one should bring up a card to explain."

    The static SVG above is complete on its own: with scripting off the floor is still drawn,
    still labelled, still readable. That is not an accident and it is not a fallback — this
    library is for people whose only device may be old, borrowed or locked down, and a page that
    is blank without JavaScript is a page that has chosen who it serves. So everything here
    LAYERS ON: the script finds the hexagons already in the document and gives them behaviour.

    WHAT 'ANOTHER ANGLE' MEANS HERE. Not a camera — a re-sort. The spiral encodes ONE ordering at
    a time, so changing the ordering genuinely changes what the picture asserts: by ALIGNMENT the
    centre is what the floor leans on most; by DEPTH it is what we actually know most about; by
    SECTION the fields separate into arms; by CALIBRATION the sealable core sits apart from the
    map-only rim. Four honest views of the same 178 cells, and each one is a different question.
    """
    payload = []
    deg = defaultdict(int)
    for a, _r, b in edges:
        deg[a] += 1
        deg[b] += 1
    rel_by = defaultdict(list)
    for a, rel, b in edges:
        if a in th and b in th:
            rel_by[a].append([rel, str(th[b].get("title"))])
            rel_by[b].append(["← " + rel, str(th[a].get("title"))])

    order = sorted(th, key=lambda i: (-deg[i], str(th[i].get("title"))))
    for cid in order:
        c = th[cid]
        x = c.get("extra") or {}
        payload.append({
            "t": str(c.get("title") or ""),
            "s": str(x.get("section") or "?"),
            "c": str(x.get("calibration") or "?"),
            "d": str((c.get("source") or {}).get("domain") or "?"),
            "g": deg[cid],
            "w": _substance(c),
            "b": str(c.get("body") or "")[:1800],
            "r": rel_by.get(cid, [])[:14],
        })

    return """
<div class=controls>
  <span class=ctl-label>angle</span>
  <button class="ang on" data-ang="align">alignment</button>
  <button class=ang data-ang="depth">depth</button>
  <button class=ang data-ang="section">section</button>
  <button class=ang data-ang="calib">calibration</button>
  <span class=ctl-sep></span>
  <button id=zin title="zoom in">+</button>
  <button id=zout title="zoom out">&#8722;</button>
  <button id=zreset>reset</button>
  <span class=hint>drag to pan &#183; scroll to zoom &#183; click a cell for its card</span>
</div>
<div id=cardpane class=cardpane hidden>
  <button id=cardclose class=cardclose aria-label="close">&#215;</button>
  <h3 id=cardtitle></h3>
  <div id=cardmeta class=cardmeta></div>
  <div id=cardbody class=cardbody></div>
  <div id=cardrels class=cardrels></div>
</div>
<script>
/* PROGRESSIVE ENHANCEMENT. Everything below decorates an SVG that is already drawn and already
   readable. If this script never runs, the floor is still there. */
(function(){
  var TH = %s;
  var svg = document.getElementById('vortex');
  if (!svg || !TH.length) return;
  var cells = svg.querySelectorAll('.cell');
  if (!cells.length) return;
  /* Reveal the controls and their description ONLY once we know the drawing is really here and
     really wired. Anything that fails above this line leaves the page as a plain static map,
     which is a complete and honest thing to be. */
  document.querySelectorAll('.controls,.ifjs').forEach(function(e){ e.classList.add('ready'); });

  /* ── zoom + pan, by moving the viewBox. No library, no dependency. ── */
  var vb = (svg.getAttribute('viewBox')||'0 0 1160 1160').split(/\\s+/).map(Number);
  var home = vb.slice(), cur = vb.slice();
  function apply(){ svg.setAttribute('viewBox', cur.join(' ')); }
  function zoom(f, cx, cy){
    var nw = Math.min(home[2]*3, Math.max(home[2]*0.08, cur[2]*f));
    var nh = nw * (home[3]/home[2]);
    if (cx === undefined){ cx = cur[0]+cur[2]/2; cy = cur[1]+cur[3]/2; }
    cur[0] = cx - (cx-cur[0]) * (nw/cur[2]);
    cur[1] = cy - (cy-cur[1]) * (nh/cur[3]);
    cur[2] = nw; cur[3] = nh; apply();
  }
  function pt(e){
    var r = svg.getBoundingClientRect();
    return [cur[0] + (e.clientX-r.left)/r.width*cur[2],
            cur[1] + (e.clientY-r.top)/r.height*cur[3]];
  }
  svg.addEventListener('wheel', function(e){
    e.preventDefault(); var p = pt(e); zoom(e.deltaY > 0 ? 1.15 : 0.87, p[0], p[1]);
  }, {passive:false});
  /* NO setPointerCapture HERE. Capturing on the <svg> made the whole drawing pan correctly and
     silently killed every cell selection: with capture set, the browser retargets the follow-up
     click to the capture element, so it fires on the <svg> and never reaches the polygon whose
     listener opens the card. Source-reading would not have caught it — it took driving the page.
     Listening on window instead keeps the drag alive past the edge of the drawing without
     stealing the click. */
  var drag = null, moved = 0;
  svg.addEventListener('pointerdown', function(e){ drag = pt(e); moved = 0; });
  window.addEventListener('pointermove', function(e){
    if (!drag) return;
    var p = pt(e);
    moved += Math.abs(p[0]-drag[0]) + Math.abs(p[1]-drag[1]);
    cur[0] -= (p[0]-drag[0]); cur[1] -= (p[1]-drag[1]); apply();
  });
  window.addEventListener('pointerup', function(){ drag = null; });
  window.addEventListener('pointercancel', function(){ drag = null; });
  document.getElementById('zin').onclick = function(){ zoom(0.8); };
  document.getElementById('zout').onclick = function(){ zoom(1.25); };
  document.getElementById('zreset').onclick = function(){ cur = home.slice(); apply(); setangle('align'); };

  /* ── the card ── */
  var pane=document.getElementById('cardpane'), T=document.getElementById('cardtitle'),
      M=document.getElementById('cardmeta'), B=document.getElementById('cardbody'),
      R=document.getElementById('cardrels');
  function esc(s){ var d=document.createElement('div'); d.textContent=s; return d.innerHTML; }
  function show(i){
    var t = TH[i]; if (!t) return;
    T.textContent = t.t;
    /* The card states the two numbers the angles sort on, so a reader who wonders why a cell sat
       where it sat can read the reason instead of inferring it from the picture. */
    M.innerHTML = esc(t.s) + ' &#183; ' + esc(t.d) + ' &#183; <b>' + esc(t.c) + '</b> &#183; ' +
                  t.g + ' relation' + (t.g===1?'':'s') + ' &#183; ' + t.w + ' chars of its own';
    B.textContent = t.b;
    R.innerHTML = t.r.length
      ? '<h4>joined to</h4>' + t.r.map(function(r){
          return '<div class=rel><span class=relk>'+esc(r[0])+'</span> '+esc(r[1])+'</div>'; }).join('')
      : '<div class=rel><span class=relk>no relations</span> this cell rests on nothing yet</div>';
    pane.hidden = false;
    cells.forEach(function(c){ c.classList.toggle('sel', +c.getAttribute('data-i') === i); });
  }
  document.getElementById('cardclose').onclick = function(){
    pane.hidden = true; cells.forEach(function(c){ c.classList.remove('sel'); }); };
  cells.forEach(function(c){ c.style.cursor='pointer'; });
  /* ONE handler on the drawing, not one per cell, and it selects the NEAREST cell rather than
     demanding a direct hit. The smallest hexagons are 8px across: on a phone that is well under
     the ~44px a fingertip can reliably land on, and a map that only answers a perfect tap is a
     map that answers nobody in a hurry. Beyond a generous radius the click means "nothing here"
     and is left alone — near-miss forgiveness, not a guess. */
  svg.addEventListener('click', function(e){
    if (moved >= 6) return;   /* they were panning, not choosing */
    var best = null, bestd = Infinity;
    cells.forEach(function(c){
      var b = c.getBoundingClientRect();
      var dx = e.clientX - (b.left + b.width/2), dy = e.clientY - (b.top + b.height/2);
      var d = Math.sqrt(dx*dx + dy*dy) - Math.max(b.width, b.height)/2;   /* distance to the edge */
      if (d < bestd){ bestd = d; best = c; }
    });
    if (best && bestd < 22) show(+best.getAttribute('data-i'));
  });

  /* ── other angles: the SAME cells, re-sorted, so the centre means something different ──
     Position is the assertion, so changing the sort changes the claim the picture makes. */
  var GA = Math.PI*(3-Math.sqrt(5)), cx0=580, cy0=586;
  var SEC = {}, secn = 0;
  TH.forEach(function(t){ if (!(t.s in SEC)) SEC[t.s] = secn++; });
  var CAL = {'seals':0, 'partial':1, 'map-only':2};
  var KEYS = {
    align:   function(t){ return [-t.g, t.t]; },
    depth:   function(t){ return [-t.w, t.t]; },
    section: function(t){ return [SEC[t.s], -t.g, t.t]; },
    calib:   function(t){ return [(t.c in CAL ? CAL[t.c] : 3), -t.g, t.t]; }
  };
  function relayout(mode){
    /* 'align' is the layout the server already drew, so it is restored by REMOVING the transform
       rather than by recomputing it. Re-deriving it in JS would land within a pixel, but "within
       a pixel" is a claim I would then have to keep true across two languages' float and sort
       behaviour. Removing the attribute is exact by construction. */
    if (mode === 'align'){
      svg.querySelectorAll('.cell,.thinring').forEach(function(el){ el.removeAttribute('transform'); });
      svg.querySelectorAll('path').forEach(function(p){ p.style.opacity = ''; });
      svg.querySelectorAll('text').forEach(function(t){
        if (t.getAttribute('font-size') === '9.5') t.style.opacity = ''; });
      return;
    }
    var key = KEYS[mode] || KEYS.align;
    var idx = TH.map(function(t,i){ return i; });
    idx.sort(function(a,b){
      var ka=key(TH[a]), kb=key(TH[b]);
      for (var i=0;i<ka.length;i++){ if (ka[i]<kb[i]) return -1; if (ka[i]>kb[i]) return 1; }
      return 0;
    });
    var spread = 1160*0.455/Math.sqrt(TH.length);
    var place = {};
    idx.forEach(function(orig, rank){
      var a = rank*GA, r = spread*Math.sqrt(rank+0.6);
      place[orig] = [cx0 + r*Math.cos(a), cy0 + r*Math.sin(a), a];
    });
    svg.querySelectorAll('.cell,.thinring').forEach(function(el){
      var i = +el.getAttribute('data-i'), p = place[i];
      if (!p) return;
      var old = el.getAttribute('points').split(' ').map(function(s){ return s.split(',').map(Number); });
      var ox = old.reduce(function(s,q){ return s+q[0]; },0)/old.length;
      var oy = old.reduce(function(s,q){ return s+q[1]; },0)/old.length;
      el.setAttribute('transform', 'translate('+(p[0]-ox).toFixed(1)+','+(p[1]-oy).toFixed(1)+')');
    });
    /* The chords are drawn as fixed curves between the ALIGNMENT positions, and the 22 printed
       names sit at those positions too. Under any other sort both would point at the wrong cells,
       so they are hidden. A stale line that still looks authoritative is worse than no line. */
    svg.querySelectorAll('path').forEach(function(p){ p.style.opacity = 0; });
    svg.querySelectorAll('text').forEach(function(t){
      if (t.getAttribute('font-size') === '9.5') t.style.opacity = 0;
    });
  }
  function setangle(mode){
    document.querySelectorAll('.ang').forEach(function(x){
      x.classList.toggle('on', x.getAttribute('data-ang') === mode); });
    relayout(mode);
  }
  document.querySelectorAll('.ang').forEach(function(b){
    b.onclick = function(){ setangle(b.getAttribute('data-ang')); };
  });
})();
</script>""" % (json.dumps(payload, ensure_ascii=False).replace("</", "<\\/"),)


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
 /* ── the enhancement layer. Every rule below styles a control that only appears once the
    script has run; with scripting off none of these elements exist and nothing shifts. ── */
 /* HIDDEN UNTIL THE SCRIPT SAYS OTHERWISE. With scripting off these buttons would still paint,
    and the hint beside them would tell the reader to drag, zoom and click a page that does none
    of those things. Dead controls that describe themselves as live are worse than no controls:
    the reader concludes the site is broken rather than that the feature is absent. Same for the
    .ifjs sentence in the lede. The script adds .ready; nothing else does. */
 .controls,.ifjs{{display:none}}
 .controls.ready{{display:flex;flex-wrap:wrap;align-items:center;gap:.4rem;margin:.7rem 0 .5rem;
        font-family:Georgia,serif;font-size:.85rem}}
 .ifjs.ready{{display:inline}}
 .ctl-label{{color:#7d745f;margin-right:.15rem}}
 .ctl-sep{{width:1px;height:18px;background:#2e2a22;margin:0 .5rem}}
 .controls button{{background:#171410;color:#a99c82;border:1px solid #2e2a22;border-radius:5px;
        padding:.24rem .6rem;font-family:Georgia,serif;font-size:.85rem;cursor:pointer}}
 .controls button:hover{{border-color:#5d564a;color:#e8dfc9}}
 .controls button.on{{background:#c69a4a;border-color:#c69a4a;color:#12100c}}
 .hint{{color:#5d564a;font-size:.78rem;margin-left:.3rem}}
 /* touch-action so a finger drag pans the map instead of scrolling the page; user-select so a
    drag does not paint the cell labels blue on the way past. */
 #vortex{{touch-action:none;-webkit-user-select:none;user-select:none}}
 /* Only the cells are clickable. Measured on the live page: a click aimed at a hexagon landed on
    a chord instead — 285 relation curves lie across the drawing and each one is a hit target the
    reader never meant to press. Nothing but a theory should answer a click. */
 #vortex path,#vortex text,#vortex circle,#vortex .thinring{{pointer-events:none}}
 .cell.sel{{stroke:#c69a4a;stroke-width:2.5}}
 .cell,.thinring{{transition:transform .55s cubic-bezier(.4,0,.2,1)}}
 .cardpane{{position:fixed;right:1rem;bottom:1rem;width:min(27rem,calc(100vw - 2rem));
        max-height:min(30rem,72vh);overflow:auto;background:#171410;border:1px solid #3a3427;
        border-radius:9px;padding:1rem 1.1rem 1.1rem;box-shadow:0 8px 34px rgba(0,0,0,.62);z-index:40}}
 .cardpane[hidden]{{display:none}}
 .cardclose{{float:right;background:none;border:0;color:#7d745f;font-size:1.3rem;line-height:1;
        cursor:pointer;padding:0 0 0 .5rem}}
 .cardclose:hover{{color:#e8dfc9}}
 .cardpane h3{{margin:0 0 .3rem;font-weight:400;font-size:1.08rem;color:#c69a4a}}
 .cardmeta{{color:#7d745f;font-size:.79rem;margin-bottom:.6rem}}
 .cardmeta b{{color:#a99c82;font-weight:400}}
 .cardbody{{color:#cbbfa4;font-size:.87rem;line-height:1.6;white-space:pre-wrap}}
 .cardrels h4{{margin:.9rem 0 .35rem;font-weight:400;font-size:.83rem;color:#7d745f}}
 .rel{{font-size:.84rem;color:#a99c82;line-height:1.5}}
 .relk{{color:#5d564a}}
 @media(max-width:640px){{.cardpane{{right:.5rem;left:.5rem;width:auto;max-height:58vh}}}}
</style></head><body><div class=wrap>
<h1>The Floor</h1>
<p class=lede>Every theory the sciences and mathematics actually run on, joined by what it
<b>rests on</b>, what <b>limits</b> it, and what <b>shares its form</b>. One body, so you can walk
from any theory to the ones holding it up. Drawn rather than listed, because a list cannot show
you what is missing &#8212; you would have to already know.</p>
<p class=lede style="font-size:.92rem">The same floor, read the other way, is
<a href="/floor.html" style="color:#c69a4a">The Floor of Discovery</a> &#8212; Scripture and the
created order as one design. That page is for seeing it; this one is for walking it.</p>

<h2 style="font-weight:400;font-size:1.15rem;color:#c69a4a;margin:1.6rem 0 .2rem">
Where the floor is missing</h2>
<p class=lede style="font-size:.92rem;margin:.2rem 0 .8rem">A lattice, because a lattice has
sites that can be <b>empty</b>. Eight dimensions down, the catalogue's sections across; each
site asks what a section contributes to a dimension, and a <span style="color:#d9534f">dashed
red cell</span> is that question with nothing on the shelf to answer it. An empty site is a
question, not automatically a gap &#8212; some combinations need not exist &#8212; but a whole
row of them is a thin place worth walking to.</p>
{lattice(th)}

<h2 style="font-weight:400;font-size:1.15rem;color:#c69a4a;margin:2rem 0 .2rem">
How well each theory is joined</h2>
<p class=lede style="font-size:.92rem;margin:.2rem 0 .8rem">The same {g['theories']}, arranged by
how many relations each holds &#8212; most aligned at the centre, spiralling out at the golden
angle. Distance from the middle is how peripheral a theory is to the assembled floor.
<span class=ifjs><b>Zoom in, turn it to another angle, and click any cell for its card.</b>
Changing the angle changes the question the picture is answering: by <i>depth</i> the centre is
what we actually know most about, by <i>calibration</i> the sealable core separates from the
map-only rim.</span></p>
{svg(th, edges)}
{interactive(th, edges)}
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
    ap.add_argument("--catalog", default=os.path.join(ROOT, "docs", "THEORY_CATALOG.md"),
                    help="catalogue whose header count this instrument keeps true")
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

    if stamp_catalog(g, args.catalog):
        print(f"stamped  {args.catalog}")
    return 0


def stamp_catalog(g, path) -> bool:
    """Write the measured count INTO the catalogue, so the header cannot rot.

    docs/THEORY_CATALOG.md opens with a count. It has now gone stale twice: it said "The 100"
    for months after the shelf passed 100, and it said "110 theories / 131 relations" while the
    shelf actually held 114 / 141 -- inside the very paragraph that warns "Numbers in prose rot."
    A number a human has to remember to retype is a number that will be wrong.

    So the instrument that COMPUTES these three writes them. Fix the path, not the instance.
    Only the one marked line is touched; the rest of the catalogue is left exactly as it is.
    """
    if not os.path.isfile(path):
        return False
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    want = (f"> **{g['theories']} theories · {g['edges']} relations · one connected body "
            f"· {g['cross_domain']} cross-domain pairs**")
    for i, line in enumerate(lines[:12]):
        if line.startswith("> **") and "theories" in line and "relations" in line:
            if line == want:
                return False
            lines[i] = want
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write("\n".join(lines))
            return True
    return False


if __name__ == "__main__":
    sys.exit(main())
