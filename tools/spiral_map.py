#!/usr/bin/env python3
"""THE SPIRAL — the calculations on a scale-free coil, with the domain connections woven in.

Matt, 2026-09-14: "Look for domain connections. I believe it should form a spiral in
general shape." The concordance already lays its theory map on the golden angle
(phyllotaxis); a LOGARITHMIC spiral is the scale-free, self-similar curve — the right
backbone for a model that is fractal. Here every calculation is a bead on the coil,
ordered so each DOMAIN is one continuous arc of color. The connective tissue is drawn
on top: for every canonical FORM, a thread through all its beads — and because a form
recurs across domains, those threads reach BETWEEN the domain arcs. Where a form spans
many domains it is one computation wearing many fields' clothes; those are the domain
connections, and the strongest bridges are named.

Stdlib only; inline SVG; renders with scripting off.

    python tools/spiral_map.py   # writes site/spiral.html
"""
import math
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass
from seed_calculations import CALCS, FORMS, leaf_forms_ordered  # noqa: E402

PALETTE = ["#c69a4a", "#6f9ec6", "#9b7fc6", "#7fb069", "#5fa8a0", "#c67f6f", "#c6a86f",
           "#d1728f", "#7aa5d2", "#b0894a", "#68b0a0", "#a98bd0", "#8fb26a", "#cf8a5c",
           "#7f9cc8", "#c0708f", "#5aa89a", "#b59a52", "#8b7fc4", "#9cae5f", "#d0a15a",
           "#6fb0c6", "#b98fc0", "#86b57f", "#b6844f", "#7c96c2", "#a37ec0", "#7aa86a"]


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build():
    leaf_idx = {f: i for i, f in enumerate(leaf_forms_ordered())}

    # order: each DOMAIN a contiguous arc; within a domain, forms in fractal preorder
    rows = list(CALCS)
    domains = sorted({r[3] for r in rows})
    dcol = {d: PALETTE[i % len(PALETTE)] for i, d in enumerate(domains)}
    rows.sort(key=lambda r: (r[3], leaf_idx.get(r[4], 999), r[4], r[0]))
    N = len(rows)

    W = H = 1520
    cx = cy = H / 2
    R0, Rmax = 46.0, 690.0
    turns = 5.5
    th_span = turns * 2 * math.pi
    b = math.log(Rmax / R0) / th_span
    th0 = -math.pi / 2

    def place(i):
        t = i / max(1, N - 1)
        th = th0 + t * th_span
        r = R0 * math.exp(b * (th - th0))
        return cx + r * math.cos(th), cy + r * math.sin(th), r, th

    pos = [place(i) for i in range(N)]

    # form -> bead indices (its cross-domain reach), and how many domains it spans
    form_beads = defaultdict(list)
    form_domains = defaultdict(set)
    for i, r in enumerate(rows):
        form_beads[r[4]].append(i)
        form_domains[r[4]].add(r[3])
    ranked = sorted(form_domains, key=lambda f: -len(form_domains[f]))
    top_forms = [f for f in ranked if len(form_domains[f]) >= 5][:8]

    p = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
         f'aria-label="The spiral: {N} calculations on a logarithmic coil, ordered so each domain '
         f'is one arc, with cross-domain form connections woven between them">']
    p.append('<rect width="100%" height="100%" fill="#12100c"/>')

    # faint spiral spine
    spine = []
    steps = 900
    for k in range(steps + 1):
        th = th0 + (k / steps) * th_span
        r = R0 * math.exp(b * (th - th0))
        spine.append(f'{cx + r*math.cos(th):.1f},{cy + r*math.sin(th):.1f}')
    p.append(f'<polyline points="{" ".join(spine)}" fill="none" stroke="#241f18" stroke-width="1"/>')

    # the weave: every form's thread through its beads (the connective tissue between domains)
    for form, beads in form_beads.items():
        if len(beads) < 2:
            continue
        pts = " ".join(f'{pos[i][0]:.1f},{pos[i][1]:.1f}' for i in beads)
        p.append(f'<polyline points="{pts}" fill="none" stroke="#c69a4a" stroke-width="0.7" opacity="0.13"/>')

    # emphasize the strongest bridges (forms spanning the most domains)
    for form in top_forms:
        beads = form_beads[form]
        pts = " ".join(f'{pos[i][0]:.1f},{pos[i][1]:.1f}' for i in beads)
        p.append(f'<polyline points="{pts}" fill="none" stroke="#e6c374" stroke-width="1.7" '
                 f'opacity="0.5" stroke-linejoin="round"><title>{esc(form)} — one computation across '
                 f'{len(form_domains[form])} domains</title></polyline>')

    # domain arcs -> a colored label at each domain's run midpoint (larger domains only)
    dom_runs = defaultdict(list)
    for i, r in enumerate(rows):
        dom_runs[r[3]].append(i)

    # beads, colored by domain
    for i, r in enumerate(rows):
        slug, title, formula, domain, form, note = r
        x, y, rr, th = pos[i]
        col = dcol[domain]
        rad = 3.0 + min(rr / Rmax, 1.0) * 2.2
        p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad:.1f}" fill="{col}" stroke="#12100c" '
                 f'stroke-width="0.6"><title>{esc(title)} — {esc(domain)} · {esc(form)}: {esc(formula)}</title></circle>')

    # domain labels (only where the run is long enough to earn one), at the run's outer end
    for domain, idxs in dom_runs.items():
        if len(idxs) < 4:
            continue
        i = idxs[-1]
        x, y, rr, th = pos[i]
        deg = math.degrees(th) + (180 if math.cos(th) < 0 else 0)
        anchor = "start" if math.cos(th) >= 0 else "end"
        lx = cx + (rr + 12) * math.cos(th)
        ly = cy + (rr + 12) * math.sin(th)
        p.append(f'<text x="{lx:.1f}" y="{ly:.1f}" fill="{dcol[domain]}" font-size="9.5" '
                 f'font-family="Georgia,serif" text-anchor="{anchor}" opacity="0.9" '
                 f'transform="rotate({deg:.0f} {lx:.1f} {ly:.1f})">{esc(domain)}</text>')

    # named bridges, listed at the strongest thread's outer bead
    for form in top_forms:
        i = form_beads[form][-1]
        x, y, rr, th = pos[i]
        deg = math.degrees(th) + (180 if math.cos(th) < 0 else 0)
        anchor = "start" if math.cos(th) >= 0 else "end"
        lx = cx + (rr + 30) * math.cos(th)
        ly = cy + (rr + 30) * math.sin(th)
        p.append(f'<text x="{lx:.1f}" y="{ly:.1f}" fill="#e6c374" font-size="11.5" font-weight="bold" '
                 f'font-family="Georgia,serif" text-anchor="{anchor}" '
                 f'transform="rotate({deg:.0f} {lx:.1f} {ly:.1f})">{esc(form)} · {len(form_domains[form])} domains</text>')

    p.append(f'<circle cx="{cx}" cy="{cy}" r="30" fill="#171410" stroke="#3a3427"/>')
    p.append(f'<text x="{cx}" y="{cy+4:.0f}" fill="#c69a4a" font-size="11" font-family="Georgia,serif" text-anchor="middle">SPIRAL</text>')
    p.append('</svg>')
    svg = "\n".join(p)

    leg = "".join(
        f'<span style="display:inline-block;margin:0 .6rem .35rem 0;white-space:nowrap">'
        f'<i style="display:inline-block;width:10px;height:10px;background:{dcol[d]};'
        f'border-radius:2px;vertical-align:middle;margin-right:4px"></i>{esc(d)}</span>'
        for d in domains)
    bridges = ", ".join(f"{esc(f)} ({len(form_domains[f])})" for f in top_forms)
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>The Spiral</title>
<style>body{{margin:0;background:#12100c;color:#e8dfc9;font-family:Georgia,'Iowan Old Style',serif}}
.wrap{{max-width:1520px;margin:0 auto;padding:1.6rem 1rem 3rem}}
h1{{color:#c69a4a;font-weight:400;font-size:1.7rem;margin:.2rem 0}}
p{{color:#a99c82;max-width:62rem;line-height:1.62}}svg{{width:100%;height:auto;display:block}}
b{{color:#cbbfa4;font-weight:400}}
.legend{{font-size:.78rem;color:#a99c82;margin:1rem 0 0;line-height:1.85}}</style></head>
<body><div class=wrap><a href="/" target="_top" style="color:#8a8172;font:400 .8rem system-ui,sans-serif;text-decoration:none">&#8592; narrowhighway.com</a><h1>The Spiral</h1>
<p>The calculations laid on a <b>logarithmic spiral</b> — the scale-free, self-similar curve, the
same golden-angle geometry the theory map already grows on. Every bead is a calculation; the coil is
ordered so each <b>domain</b> is one continuous arc of color. Woven on top is the connective tissue:
for each canonical <b>form</b>, a thread through all its beads — and since a form recurs across
domains, its thread reaches <b>between</b> the arcs. The gold weave IS the set of domain connections;
the brightest threads are the forms that bridge the most fields. Strongest bridges: {bridges}.
{N} calculations · {len(domains)} domains.</p>
{svg}
<div class=legend>{leg}</div>
<p style="color:#7d745f;font-size:.8rem">Found and mapped, never generated. A form that touches many
domains is one computation the whole world runs — the connection is the point, not the coincidence.</p>
</div></body></html>"""


def main():
    out = os.path.join(ROOT, "site", "spiral.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(build())
    print(f"wrote {out}  ({len(CALCS)} calculations on the spiral)")


if __name__ == "__main__":
    main()
