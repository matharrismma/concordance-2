#!/usr/bin/env python3
"""THE ONE BODY — the calculation map joined to the theory FLOOR, in one picture.

Matt, 2026-09-13: draw the one body. Three layers, one figure:

  FORM  (the spine)   ->  a calculation sits in its form's SECTOR   =  same_form
  CALCULATION (a dot) ->  a chord reaches out to the theory it needs =  rests_on
  THEORY (the rim)    ->  THE FLOOR, the theories the calculations stand on

The inner disk is the calculation map (a Smith-chart wheel of canonical forms).
The outer rim is THE FLOOR: only the theories that actually carry a calculation
light up, each placed near the calculations that lean on it. The chords are the
joins — one connected body, form through calculation to theory.

Stdlib only; inline SVG; renders with scripting off.

    python tools/one_body_map.py   # writes site/one_body.html
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass
from seed_calculations import CALCS, CALC_THEORY, FORMS, FORM_PARENT  # noqa: E402

PALETTE = ["#c69a4a", "#6f9ec6", "#9b7fc6", "#7fb069", "#5fa8a0", "#c67f6f", "#c6a86f",
           "#d1728f", "#7aa5d2", "#b0894a", "#68b0a0", "#a98bd0", "#8fb26a", "#cf8a5c",
           "#7f9cc8", "#c0708f", "#5aa89a", "#b59a52", "#8b7fc4", "#9cae5f", "#d0a15a",
           "#6fb0c6", "#b98fc0", "#86b57f"]
FAMILY_TINT = {"ratio": "#c69a4a", "exponential": "#c67f6f", "modular": "#6f9ec6"}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def theory_titles() -> dict[str, str]:
    """id -> human title, read from THE FLOOR (never regenerated here)."""
    out = {}
    p = Path(ROOT) / "data" / "theory_cards.jsonl"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    c = json.loads(line)
                    out[c["id"]] = c.get("title", c["id"])
                except (ValueError, KeyError):
                    pass
    return out


def short(t: str, n: int = 30) -> str:
    t = t.split("(")[0].split(" - ")[0].strip()
    return t if len(t) <= n else t[: n - 1].rstrip() + "…"


def circ_mean(angles: list[float]) -> float:
    s = sum(math.sin(a) for a in angles)
    c = sum(math.cos(a) for a in angles)
    return math.atan2(s, c)


def _leaf_order():
    """Leaf forms ordered so a parent's children are contiguous (the fractal grouping)."""
    parents = set(FORM_PARENT.values())
    order, seen = [], set()
    for f in FORMS:
        if f in parents:
            continue
        key = FORM_PARENT.get(f, f)
        if key in seen:
            continue
        seen.add(key)
        order.extend([g for g in FORMS if g not in parents and FORM_PARENT.get(g, g) == key])
    return order


def build() -> str:
    forms = _leaf_order()
    n = len(forms)
    # group calcs by form, collect domains
    by = defaultdict(list)
    domains = []
    for slug, title, formula, domain, form, note in CALCS:
        by[form].append((slug, title, formula, domain, note))
        if domain not in domains:
            domains.append(domain)
    domains = sorted(domains)
    dcol = {d: PALETTE[i % len(PALETTE)] for i, d in enumerate(domains)}

    W = Hgt = 1780
    cx = cy = Hgt / 2
    Rin, Rout = 150, 560        # calculation disk: forms + calc dots
    Rtheory = 690               # the FLOOR rim
    Rlabel = 700

    # --- place every calc dot; remember its angle so its theory can sit near it ---
    calc_xy: dict[str, tuple[float, float, str]] = {}   # slug -> (x, y, domain)
    calc_ang: dict[str, float] = {}
    dots = []
    for i, form in enumerate(forms):
        a0 = -math.pi / 2 + 2 * math.pi * i / n
        a1 = -math.pi / 2 + 2 * math.pi * (i + 1) / n
        amid = (a0 + a1) / 2
        rows = by.get(form, [])
        m = max(1, len(rows))
        for j, (slug, title, formula, domain, note) in enumerate(rows):
            r = Rin + (Rout - Rin - 40) * ((j + 0.5) / m)
            frac = ((j % 3) - 1) * 0.34
            ang = amid + (a1 - a0) * 0.30 * frac
            x = cx + r * math.cos(ang)
            y = cy + r * math.sin(ang)
            calc_xy[slug] = (x, y, domain)
            calc_ang[slug] = ang
            dots.append((x, y, domain, title, formula, note))

    # --- place each targeted theory near the mean angle of the calcs that rest on it ---
    theory_calcs: dict[str, list[str]] = defaultdict(list)
    for slug in calc_ang:
        tid = CALC_THEORY.get(slug)
        if tid:
            theory_calcs[tid].append(slug)
    tmean = {tid: circ_mean([calc_ang[s] for s in slugs]) for tid, slugs in theory_calcs.items()}
    order = sorted(tmean, key=lambda t: tmean[t])
    # de-clump: walk the ring, enforce a minimum angular gap
    gap = 2 * math.pi / max(1, len(order)) * 0.92
    placed: dict[str, float] = {}
    prev = None
    for tid in order:
        a = tmean[tid]
        if prev is not None and a - prev < gap:
            a = prev + gap
        placed[tid] = a
        prev = a
    # relax the wrap-around seam
    if order:
        span = placed[order[-1]] - placed[order[0]]
        if span > 2 * math.pi:
            shrink = 2 * math.pi / span
            base = placed[order[0]]
            placed = {t: base + (placed[t] - base) * shrink for t in order}

    titles = theory_titles()

    p = [f'<svg viewBox="0 0 {W} {Hgt}" xmlns="http://www.w3.org/2000/svg" role="img" '
         f'aria-label="The one body: {len(CALCS)} calculations across {n} forms, joined to '
         f'{len(order)} theories on the floor by rests_on chords">']
    p.append(f'<rect width="100%" height="100%" fill="#12100c"/>')
    for q in (0.28, 0.5, 0.72, 0.94):
        p.append(f'<circle cx="{cx}" cy="{cy}" r="{Rout*q:.0f}" fill="none" stroke="#241f18" stroke-width="1"/>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="{Rout:.0f}" fill="none" stroke="#2f2a20" stroke-width="1.5"/>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="{Rtheory:.0f}" fill="none" stroke="#3a3120" stroke-width="1" stroke-dasharray="2 6"/>')

    # --- faint tinted super-sectors behind the three split families (the fractal nesting) ---
    fam_span = {}
    for i, f in enumerate(forms):
        par = FORM_PARENT.get(f)
        if par:
            lo, hi = fam_span.get(par, (i, i))
            fam_span[par] = (min(lo, i), max(hi, i))
    for fam, (lo, hi) in fam_span.items():
        a0 = -math.pi / 2 + 2 * math.pi * lo / n
        a1 = -math.pi / 2 + 2 * math.pi * (hi + 1) / n
        col = FAMILY_TINT.get(fam, "#c69a4a")
        x0o, y0o = cx + Rout * math.cos(a0), cy + Rout * math.sin(a0)
        x1o, y1o = cx + Rout * math.cos(a1), cy + Rout * math.sin(a1)
        large = 1 if (a1 - a0) > math.pi else 0
        p.append(f'<path d="M{cx:.1f},{cy:.1f} L{x0o:.1f},{y0o:.1f} '
                 f'A{Rout},{Rout} 0 {large} 1 {x1o:.1f},{y1o:.1f} Z" fill="{col}" opacity="0.05"/>')
        amid = (a0 + a1) / 2
        lx, ly = cx + (Rout + 24) * math.cos(amid), cy + (Rout + 24) * math.sin(amid)
        deg = math.degrees(amid) + (180 if math.cos(amid) < 0 else 0)
        anchor = "start" if math.cos(amid) >= 0 else "end"
        p.append(f'<text x="{lx:.0f}" y="{ly:.0f}" fill="{col}" font-size="11" opacity="0.75" '
                 f'font-family="Georgia,serif" text-anchor="{anchor}" '
                 f'transform="rotate({deg:.0f} {lx:.0f} {ly:.0f})">{esc(fam)}</text>')

    # --- chords: calc -> theory (rests_on) — drawn first, under the nodes ---
    for slug, (x, y, domain) in calc_xy.items():
        tid = CALC_THEORY.get(slug)
        if tid not in placed:
            continue
        ta = placed[tid]
        tx = cx + Rtheory * math.cos(ta)
        ty = cy + Rtheory * math.sin(ta)
        mx, my = (x + tx) / 2, (y + ty) / 2
        ctrlx = cx + (mx - cx) * 0.45         # bow the chord inward -> radial bundling
        ctrly = cy + (my - cy) * 0.45
        col = dcol.get(domain, "#8a8378")
        p.append(f'<path d="M{x:.1f} {y:.1f} Q{ctrlx:.1f} {ctrly:.1f} {tx:.1f} {ty:.1f}" '
                 f'fill="none" stroke="{col}" stroke-width="0.8" opacity="0.22"/>')

    # --- form sector spokes + labels ---
    for i, form in enumerate(forms):
        a0 = -math.pi / 2 + 2 * math.pi * i / n
        amid = -math.pi / 2 + 2 * math.pi * (i + 0.5) / n
        p.append(f'<line x1="{cx + Rin*math.cos(a0):.0f}" y1="{cy + Rin*math.sin(a0):.0f}" '
                 f'x2="{cx + Rout*math.cos(a0):.0f}" y2="{cy + Rout*math.sin(a0):.0f}" '
                 f'stroke="#241f18" stroke-width="1"/>')
        lx = cx + (Rout - 92) * math.cos(amid)
        ly = cy + (Rout - 92) * math.sin(amid)
        deg = math.degrees(amid) + (180 if math.cos(amid) < 0 else 0)
        anchor = "start" if math.cos(amid) >= 0 else "end"
        p.append(f'<text x="{lx:.0f}" y="{ly:.0f}" fill="#8f7a45" font-size="12" '
                 f'font-family="Georgia,serif" text-anchor="{anchor}" opacity="0.85" '
                 f'transform="rotate({deg:.0f} {lx:.0f} {ly:.0f})">{esc(form)}</text>')

    # --- calc dots ---
    for x, y, domain, title, formula, note in dots:
        col = dcol.get(domain, "#8a8378")
        p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.6" fill="{col}" stroke="#12100c" '
                 f'stroke-width="0.8"><title>{esc(title)} — {esc(domain)}: {esc(formula)}</title></circle>')

    # --- theory nodes on the FLOOR rim + radial labels ---
    for tid in order:
        a = placed[tid]
        tx = cx + Rtheory * math.cos(a)
        ty = cy + Rtheory * math.sin(a)
        load = len(theory_calcs[tid])
        rr = 3.2 + min(load, 8) * 0.9
        p.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="{rr:.1f}" fill="#e6c374" stroke="#7a5f28" '
                 f'stroke-width="1"><title>{esc(titles.get(tid, tid))} — carries {load} calculation'
                 f'{"s" if load != 1 else ""}</title></circle>')
        lx = cx + Rlabel * math.cos(a)
        ly = cy + Rlabel * math.sin(a)
        deg = math.degrees(a) + (180 if math.cos(a) < 0 else 0)
        anchor = "start" if math.cos(a) >= 0 else "end"
        p.append(f'<text x="{lx:.1f}" y="{ly+2.5:.1f}" fill="#cbbfa4" font-size="10" '
                 f'font-family="Georgia,serif" text-anchor="{anchor}" '
                 f'transform="rotate({deg:.1f} {lx:.1f} {ly:.1f})">{esc(short(titles.get(tid, tid)))}</text>')

    # --- core ---
    p.append(f'<circle cx="{cx}" cy="{cy}" r="{Rin-2:.0f}" fill="#12100c" opacity="0.55"/>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="46" fill="#171410" stroke="#3a3427"/>')
    p.append(f'<text x="{cx}" y="{cy-6:.0f}" fill="#c69a4a" font-size="13" font-family="Georgia,serif" text-anchor="middle">ONE</text>')
    p.append(f'<text x="{cx}" y="{cy+11:.0f}" fill="#c69a4a" font-size="13" font-family="Georgia,serif" text-anchor="middle">BODY</text>')
    p.append('</svg>')
    svg = "\n".join(p)

    leg = "".join(
        f'<span style="display:inline-block;margin:0 .7rem .35rem 0;white-space:nowrap">'
        f'<i style="display:inline-block;width:11px;height:11px;background:{dcol[d]};'
        f'border-radius:2px;vertical-align:middle;margin-right:4px"></i>{esc(d)}</span>'
        for d in domains)
    linked = sum(1 for s in calc_xy if CALC_THEORY.get(s) in placed)
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>The One Body</title>
<style>body{{margin:0;background:#12100c;color:#e8dfc9;font-family:Georgia,'Iowan Old Style',serif}}
.wrap{{max-width:1500px;margin:0 auto;padding:1.6rem 1rem 3rem}}
h1{{color:#c69a4a;font-weight:400;font-size:1.8rem;margin:.2rem 0}}
p{{color:#a99c82;max-width:62rem;line-height:1.62}}svg{{width:100%;height:auto;display:block}}
b{{color:#cbbfa4;font-weight:400}}
.key{{color:#a99c82;margin:.6rem 0 0;font-size:.84rem}}
.key i.line{{display:inline-block;width:26px;height:0;border-top:1px solid #c69a4a;vertical-align:middle;margin-right:5px;opacity:.6}}
.key i.dot{{display:inline-block;width:9px;height:9px;border-radius:50%;background:#e6c374;vertical-align:middle;margin-right:5px}}
.legend{{font-size:.8rem;color:#a99c82;margin:1.1rem 0 0;line-height:1.9}}</style></head>
<body><div class=wrap><a href="/" target="_top" style="color:#8a8172;font:400 .8rem system-ui,sans-serif;text-decoration:none">&#8592; narrowhighway.com</a><h1>The One Body</h1>
<p>The calculation map and the theory <b>FLOOR</b>, drawn as one figure. The inner disk is
every calculation, placed in the <b>sector of its canonical form</b> &mdash; sharing a sector is
sharing a computation (<b>same&#95;form</b>). Each calculation then throws a <b>chord</b> outward to
the theory it stands on (<b>rests&#95;on</b>); those theories are the lit points of the FLOOR on the
rim, sized by how many calculations lean on them. Form through calculation to theory &mdash; one
connected body. {len(CALCS)} calculations &#183; {n} forms &#183; {len(order)} load-bearing theories
&#183; {linked} joins.</p>
<p class=key><i class=line></i>a chord = one calculation resting on its theory &nbsp;&nbsp;
<i class=dot></i>a lit theory on the FLOOR, sized by the load it carries</p>
{svg}
<div class=legend>{leg}</div>
<p style="color:#7d745f;font-size:.8rem">Found and mapped, never generated. Two calculations in the
same sector are the same computation in different clothes; a bright rim-node is a theory that many
computations quietly depend on.</p></div></body></html>"""


def main() -> int:
    out = os.path.join(ROOT, "site", "one_body.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(build())
    linked = sum(1 for s, *_ in [(c[0],) for c in CALCS] if CALC_THEORY.get(s))
    print(f"wrote {out}  ({len(CALCS)} calculations, {len(FORMS)} forms, "
          f"{len(set(CALC_THEORY.values()))} theories on the rim, {linked} joins)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
