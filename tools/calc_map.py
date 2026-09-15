#!/usr/bin/env python3
"""THE CALCULATION MAP, drawn — a Smith-chart-like wheel, now FRACTAL.

Matt, 2026-09-13: "Think of a Smith chart." 2026-09-14: "Split into finer forms.
The model is fractal." A Smith chart folds the whole impedance plane onto one
bounded disk. This does the same for calculation: the disk is divided into SECTORS,
one per canonical FORM; each calculation is a point on its form's locus, colored by
DOMAIN. And a coarse form is a form-of-forms: the three split families (ratio,
exponential, modular) are drawn as tinted SUPER-SECTORS subdivided into their child
forms — the nesting made visible. Stdlib only; inline SVG; renders with scripting off.

    python tools/calc_map.py   # writes site/calculations.html
"""
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass
from seed_calculations import FORMS, CALCS, FORM_PARENT  # noqa: E402

PALETTE = ["#c69a4a", "#6f9ec6", "#9b7fc6", "#7fb069", "#5fa8a0", "#c67f6f", "#c6a86f",
           "#d1728f", "#7aa5d2", "#b0894a", "#68b0a0", "#a98bd0", "#8fb26a", "#cf8a5c",
           "#7f9cc8", "#c0708f", "#5aa89a", "#b59a52", "#8b7fc4", "#9cae5f", "#d0a15a",
           "#6fb0c6", "#b98fc0", "#86b57f"]
# a faint tint per split-family, so the three super-sectors read at a glance
FAMILY_TINT = {"ratio": "#c69a4a", "exponential": "#c67f6f", "modular": "#6f9ec6"}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def leaf_order():
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
    return order, parents


def build():
    forms, parents = leaf_order()
    by = {f: [] for f in forms}
    domains = []
    for slug, title, formula, domain, form, note in CALCS:
        if form in by:
            by[form].append((slug, title, formula, domain, note))
        if domain not in domains:
            domains.append(domain)
    domains = sorted(domains)
    dcol = {d: PALETTE[i % len(PALETTE)] for i, d in enumerate(domains)}

    W = H = 1440
    cx = cy = H / 2 - 8
    Rout = 600
    Rin = 96
    n = len(forms)

    def ang(i):   # sector i boundary angle
        return -math.pi / 2 + 2 * math.pi * i / n

    # child form -> its parent family, and each family's contiguous sector span
    fam_span = {}
    for i, f in enumerate(forms):
        p = FORM_PARENT.get(f)
        if p:
            lo, hi = fam_span.get(p, (i, i))
            fam_span[p] = (min(lo, i), max(hi, i))

    p = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
         f'aria-label="The calculation map: {len(CALCS)} calculations grouped by {n} canonical '
         f'forms, with three coarse forms split into finer children">']
    p.append('<rect width="100%" height="100%" fill="#12100c"/>')

    # faint tinted super-sector wedges behind the split families (the fractal nesting)
    for fam, (lo, hi) in fam_span.items():
        a0, a1 = ang(lo), ang(hi + 1)
        col = FAMILY_TINT.get(fam, "#c69a4a")
        x0o, y0o = cx + Rout * math.cos(a0), cy + Rout * math.sin(a0)
        x1o, y1o = cx + Rout * math.cos(a1), cy + Rout * math.sin(a1)
        x1i, y1i = cx + Rin * math.cos(a1), cy + Rin * math.sin(a1)
        x0i, y0i = cx + Rin * math.cos(a0), cy + Rin * math.sin(a0)
        large = 1 if (a1 - a0) > math.pi else 0
        p.append(f'<path d="M{x0o:.1f},{y0o:.1f} A{Rout},{Rout} 0 {large} 1 {x1o:.1f},{y1o:.1f} '
                 f'L{x1i:.1f},{y1i:.1f} A{Rin},{Rin} 0 {large} 0 {x0i:.1f},{y0i:.1f} Z" '
                 f'fill="{col}" opacity="0.055"/>')

    for q in (0.30, 0.55, 0.80, 1.0):                       # Smith-chart guide circles
        p.append(f'<circle cx="{cx}" cy="{cy}" r="{Rout*q:.0f}" fill="none" stroke="#2a2620" stroke-width="1"/>')

    for i, form in enumerate(forms):
        a0 = ang(i)
        amid = ang(i + 0.5)
        # a boundary between two different families (or family/standalone) is drawn heavier
        prev = forms[i - 1] if i > 0 else forms[-1]
        same_family = FORM_PARENT.get(form, form) == FORM_PARENT.get(prev, prev)
        stroke = ("#2a2620", 1) if same_family else ("#4a4230", 1.4)
        p.append(f'<line x1="{cx + Rin*math.cos(a0):.0f}" y1="{cy + Rin*math.sin(a0):.0f}" '
                 f'x2="{cx + Rout*math.cos(a0):.0f}" y2="{cy + Rout*math.sin(a0):.0f}" '
                 f'stroke="{stroke[0]}" stroke-width="{stroke[1]}"/>')
        rows = by.get(form, [])
        m = max(1, len(rows))
        for j, (slug, title, formula, domain, note) in enumerate(rows):
            r = Rin + 34 + (Rout - Rin - 74) * ((j + 0.5) / m)
            frac = ((j % 3) - 1) * 0.34
            aa = amid + (ang(i + 1) - a0) * 0.28 * frac
            x = cx + r * math.cos(aa)
            y = cy + r * math.sin(aa)
            col = dcol.get(domain, "#8a8378")
            p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.6" fill="{col}" stroke="#12100c" '
                     f'stroke-width="0.8"><title>{esc(title)} — {esc(domain)}: {esc(formula)}</title></circle>')
        # child/leaf form label just inside the rim
        eq, _desc = FORMS[form]
        lr = Rout - 8
        lx = cx + lr * math.cos(amid)
        ly = cy + lr * math.sin(amid)
        deg = math.degrees(amid) + (180 if math.cos(amid) < 0 else 0)
        anchor = "end" if math.cos(amid) >= 0 else "start"
        p.append(f'<text x="{lx:.0f}" y="{ly:.0f}" fill="#cbbfa4" font-size="10.5" '
                 f'font-family="Georgia,serif" text-anchor="{anchor}" '
                 f'transform="rotate({deg:.0f} {lx:.0f} {ly:.0f})">{esc(form)}</text>')

    # family (parent) labels on an outer arc spanning their children
    for fam, (lo, hi) in fam_span.items():
        amid = ang((lo + hi + 1) / 2)
        lr = Rout + 30
        lx = cx + lr * math.cos(amid)
        ly = cy + lr * math.sin(amid)
        deg = math.degrees(amid) + (180 if math.cos(amid) < 0 else 0)
        anchor = "start" if math.cos(amid) >= 0 else "end"
        eq = FORMS[fam][0]
        p.append(f'<text x="{lx:.0f}" y="{ly:.0f}" fill="{FAMILY_TINT.get(fam, "#c69a4a")}" font-size="14" '
                 f'font-weight="bold" font-family="Georgia,serif" text-anchor="{anchor}" '
                 f'transform="rotate({deg:.0f} {lx:.0f} {ly:.0f})">{esc(fam)}  ·  {esc(eq)}</text>')

    p.append(f'<circle cx="{cx}" cy="{cy}" r="{Rin-6:.0f}" fill="#12100c"/>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="42" fill="#171410" stroke="#3a3427"/>')
    p.append(f'<text x="{cx}" y="{cy-3:.0f}" fill="#c69a4a" font-size="12" font-family="Georgia,serif" text-anchor="middle">FORMS</text>')
    p.append(f'<text x="{cx}" y="{cy+13:.0f}" fill="#8a8378" font-size="10" font-family="Georgia,serif" text-anchor="middle">{n}</text>')
    p.append('</svg>')
    svg = "\n".join(p)

    leg = "".join(
        f'<span style="display:inline-block;margin:0 .7rem .35rem 0;white-space:nowrap">'
        f'<i style="display:inline-block;width:11px;height:11px;background:{dcol[d]};'
        f'border-radius:2px;vertical-align:middle;margin-right:4px"></i>{esc(d)}</span>'
        for d in domains)
    n_parents = len(fam_span)
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>The Calculation Map</title>
<style>body{{margin:0;background:#12100c;color:#e8dfc9;font-family:Georgia,'Iowan Old Style',serif}}
.wrap{{max-width:1480px;margin:0 auto;padding:1.6rem 1rem 3rem}}
h1{{color:#c69a4a;font-weight:400;font-size:1.7rem;margin:.2rem 0}}
p{{color:#a99c82;max-width:62rem;line-height:1.6}}svg{{width:100%;height:auto;display:block}}
b{{color:#cbbfa4;font-weight:400}}
.legend{{font-size:.8rem;color:#a99c82;margin:1rem 0;line-height:1.9}}</style></head>
<body><div class=wrap><a href="/" target="_top" style="color:#8a8172;font:400 .8rem system-ui,sans-serif;text-decoration:none">&#8592; narrowhighway.com</a><h1>The Calculation Map</h1>
<p>Every calculation placed by its <b>canonical form</b> — the way a Smith chart places every
impedance on one disk. A sector is one form; each dot is a calculation, colored by domain. And the
model is <b>fractal</b>: a coarse form is a form-of-forms, so the three families that ran too wide —
<b>{esc("ratio")}</b>, <b>{esc("exponential")}</b>, <b>{esc("modular")}</b> — are drawn as tinted
super-sectors split into their finer children. {len(CALCS)} calculations &#183; {n} leaf forms under
{n_parents} split families.</p>
{svg}
<div class=legend>{leg}</div>
<p style="color:#7d745f;font-size:.8rem">Found and mapped, never generated. Same form = the same
computation in different clothes; a finer form is that sameness seen closer.</p></div></body></html>"""


def main():
    out = os.path.join(ROOT, "site", "calculations.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(build())
    print(f"wrote {out}  ({len(CALCS)} calculations, {len(leaf_order()[0])} leaf forms)")


if __name__ == "__main__":
    main()
