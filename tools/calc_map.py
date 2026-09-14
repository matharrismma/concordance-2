#!/usr/bin/env python3
"""THE CALCULATION MAP, drawn — a Smith-chart-like wheel.

Matt, 2026-09-13: "Think of a Smith chart." A Smith chart folds the whole
impedance plane onto one bounded disk so every impedance is a point on one
geometry. This does the same for calculation: the disk is divided into SECTORS,
one per canonical FORM; each calculation is a point on its form's locus, colored
by DOMAIN. A sector wearing many colors is the finding — one calculation, many
domains. Stdlib only; inline SVG; renders with scripting off.

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
from seed_calculations import FORMS, CALCS  # noqa: E402

PALETTE = ["#c69a4a", "#6f9ec6", "#9b7fc6", "#7fb069", "#5fa8a0", "#c67f6f", "#c6a86f",
           "#d1728f", "#7aa5d2", "#b0894a", "#68b0a0", "#a98bd0", "#8fb26a", "#cf8a5c",
           "#7f9cc8", "#c0708f", "#5aa89a", "#b59a52", "#8b7fc4", "#9cae5f", "#d0a15a",
           "#6fb0c6", "#b98fc0", "#86b57f"]


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build():
    forms = list(FORMS)
    by = {f: [] for f in forms}
    domains = []
    for slug, title, formula, domain, form, note in CALCS:
        if form in by:
            by[form].append((slug, title, formula, domain, note))
        if domain not in domains:
            domains.append(domain)
    domains = sorted(domains)
    dcol = {d: PALETTE[i % len(PALETTE)] for i, d in enumerate(domains)}

    W = H = 1320
    cx = cy = H / 2 - 8
    Rout = 560
    n = len(forms)
    p = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
         f'aria-label="The calculation map: {len(CALCS)} calculations grouped by {n} canonical forms">']
    p.append('<rect width="100%" height="100%" fill="#12100c"/>')
    for q in (0.30, 0.55, 0.80, 1.0):                       # Smith-chart guide circles
        p.append(f'<circle cx="{cx}" cy="{cy}" r="{Rout*q:.0f}" fill="none" stroke="#2a2620" stroke-width="1"/>')

    for i, form in enumerate(forms):
        a0 = -math.pi / 2 + 2 * math.pi * i / n
        a1 = -math.pi / 2 + 2 * math.pi * (i + 1) / n
        amid = (a0 + a1) / 2
        p.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + Rout*math.cos(a0):.0f}" '
                 f'y2="{cy + Rout*math.sin(a0):.0f}" stroke="#2a2620" stroke-width="1"/>')
        rows = by.get(form, [])
        m = max(1, len(rows))
        for j, (slug, title, formula, domain, note) in enumerate(rows):
            r = 150 + (Rout - 195) * ((j + 0.5) / m)
            frac = ((j % 3) - 1) * 0.34
            ang = amid + (a1 - a0) * 0.28 * frac
            x = cx + r * math.cos(ang)
            y = cy + r * math.sin(ang)
            col = dcol.get(domain, "#8a8378")
            p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="{col}" stroke="#12100c" '
                     f'stroke-width="1"><title>{esc(title)} — {esc(domain)}: {esc(formula)}</title></circle>')
            right = math.cos(ang) >= 0
            lx = x + (8 if right else -8)
            p.append(f'<text x="{lx:.1f}" y="{y+3:.1f}" fill="#cbbfa4" font-size="8.5" '
                     f'font-family="Georgia,serif" text-anchor="{"start" if right else "end"}">'
                     f'{esc(title.split("(")[0].strip()[:22])}</text>')
        eq, desc = FORMS[form]
        lx = cx + (Rout + 10) * math.cos(amid)
        ly = cy + (Rout + 10) * math.sin(amid)
        deg = math.degrees(amid) + (180 if math.cos(amid) < 0 else 0)
        anchor = "start" if math.cos(amid) >= 0 else "end"
        p.append(f'<text x="{lx:.0f}" y="{ly:.0f}" fill="#c69a4a" font-size="12.5" '
                 f'font-family="Georgia,serif" text-anchor="{anchor}" '
                 f'transform="rotate({deg:.0f} {lx:.0f} {ly:.0f})">{esc(form)}  ·  {esc(eq)}</text>')

    p.append(f'<circle cx="{cx}" cy="{cy}" r="42" fill="#171410" stroke="#3a3427"/>')
    p.append(f'<text x="{cx}" y="{cy-3:.0f}" fill="#c69a4a" font-size="13" font-family="Georgia,serif" text-anchor="middle">FORMS</text>')
    p.append(f'<text x="{cx}" y="{cy+13:.0f}" fill="#8a8378" font-size="10" font-family="Georgia,serif" text-anchor="middle">{n}</text>')
    p.append('</svg>')
    svg = "\n".join(p)

    leg = "".join(
        f'<span style="display:inline-block;margin:0 .7rem .35rem 0;white-space:nowrap">'
        f'<i style="display:inline-block;width:11px;height:11px;background:{dcol[d]};'
        f'border-radius:2px;vertical-align:middle;margin-right:4px"></i>{esc(d)}</span>'
        for d in domains)
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>The Calculation Map</title>
<style>body{{margin:0;background:#12100c;color:#e8dfc9;font-family:Georgia,'Iowan Old Style',serif}}
.wrap{{max-width:1360px;margin:0 auto;padding:1.6rem 1rem 3rem}}
h1{{color:#c69a4a;font-weight:400;font-size:1.7rem;margin:.2rem 0}}
p{{color:#a99c82;max-width:60rem;line-height:1.6}}svg{{width:100%;height:auto;display:block}}
.legend{{font-size:.8rem;color:#a99c82;margin:1rem 0;line-height:1.9}}</style></head>
<body><div class=wrap><h1>The Calculation Map</h1>
<p>Every calculation placed by its <b>canonical form</b> — the way a Smith chart places every
impedance on one disk. A sector is one form; each dot is a calculation, colored by domain. A
sector wearing many colors is the finding: <b>one calculation, many domains, under a change of
variable</b>. {len(CALCS)} calculations &#183; {n} forms.</p>
{svg}
<div class=legend>{leg}</div>
<p style="color:#7d745f;font-size:.8rem">Found and mapped, never generated. Same form = the same
computation in different clothes.</p></div></body></html>"""


def main():
    out = os.path.join(ROOT, "site", "calculations.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(build())
    print(f"wrote {out}  ({len(CALCS)} calculations, {len(FORMS)} forms)")


if __name__ == "__main__":
    main()
