#!/usr/bin/env python3
"""COMPLETENESS SETS, drawn — the Atlas as a predictor.

The flagship: Chua's square of the four circuit variables. Voltage, current, charge and flux sit at
the corners; the six relations are the edges. Five were spoken for — two definitions, and the
resistor, capacitor and inductor. The sixth, the flux-charge diagonal, was empty, and symmetry
demanded it: the memristor, predicted 1971, built 2008. Below the figure, the full relation table,
and the CLASS the memristor belongs to — the great predictions made from the completeness of a
structure. Stdlib only; inline SVG + a little vanilla JS.

    python tools/completeness_view.py    # writes site/completeness.html
"""
import html
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass
from seed_completeness import SETS, PREDICTIONS  # noqa: E402

BG = "#0f0d09"
GOLD = "#c69a4a"
GOLD2 = "#e6c374"
DIM = "#5a5344"
STATUS_COL = {"definition": DIM, "element": GOLD, "predicted": GOLD2}


def esc(s):
    return html.escape(str(s))


def _diamond_svg(s: dict) -> str:
    W = 620
    cx = cy = W / 2
    R = 205
    pos = {"top": (cx, cy - R), "right": (cx + R, cy), "bottom": (cx, cy + R), "left": (cx - R, cy)}
    qpos = {q["sym"]: pos[q["pos"]] for q in s["quantities"]}
    qname = {q["sym"]: q["name"] for q in s["quantities"]}
    rel = {frozenset(r["pair"]): r for r in s["relations"]}

    p = [f'<svg id="fig" viewBox="0 0 {W} {W}" xmlns="http://www.w3.org/2000/svg">']
    p.append(f'<rect width="100%" height="100%" fill="{BG}"/>')

    # edges (relations)
    for fs, r in rel.items():
        a, b = list(r["pair"])
        (x0, y0), (x1, y1) = qpos[a], qpos[b]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        col = STATUS_COL[r["status"]]
        pred = r["status"] == "predicted"
        dash = ' stroke-dasharray="7 5"' if r["status"] == "definition" else ""
        wid = 3.4 if pred else (2.2 if r["status"] == "element" else 1.4)
        cls = "edge pred" if pred else "edge"
        p.append(f'<g class="{cls}" data-rel="{esc(r["name"])}">')
        if pred:   # a soft glow UNDERLAY (an SVG filter degenerates on a zero-height horizontal line)
            p.append(f'<line x1="{x0:.0f}" y1="{y0:.0f}" x2="{x1:.0f}" y2="{y1:.0f}" stroke="{col}" '
                     f'stroke-width="{wid + 7:.0f}" opacity="0.20" stroke-linecap="round"/>')
        p.append(f'<line x1="{x0:.0f}" y1="{y0:.0f}" x2="{x1:.0f}" y2="{y1:.0f}" stroke="{col}" '
                 f'stroke-width="{wid}" opacity="{0.95 if pred else 0.8}"{dash} stroke-linecap="round"/>')
        # edge label: the element letter (R/C/L/M) or the integral sign for a definition
        label = r.get("element", "").split("(")[-1].rstrip(")") if r["status"] != "definition" else "∫"
        lcol = GOLD2 if pred else col
        # both diagonals cross at the centre; lift the VERTICAL one (the resistor) up its line so it
        # does not sit on top of the horizontal one (the memristor), which keeps the centre.
        lx, ly = mx, my
        if abs(x0 - x1) < 2:        # vertical diagonal (the resistor) — lift up its line
            ly = my - 64
        elif abs(y0 - y1) < 2:      # horizontal diagonal (the memristor) — shift along its line, off the crossing
            lx = mx + 60
        rr = 13 if pred else 11
        p.append(f'<circle cx="{lx:.0f}" cy="{ly:.0f}" r="{rr}" fill="{BG}" '
                 f'stroke="{lcol}" stroke-width="{1.6 if pred else 1}"/>')
        p.append(f'<text x="{lx:.0f}" y="{ly+4:.0f}" fill="{lcol}" font-size="{15 if pred else 13}" '
                 f'font-family="Georgia,serif" font-style="italic" text-anchor="middle">{esc(label)}</text>')
        p.append('</g>')

    # nodes (the four variables)
    qmeta = {q["sym"]: q for q in s["quantities"]}
    for sym, (x, y) in qpos.items():
        p.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="26" fill="#161209" stroke="{GOLD}" stroke-width="1.5"/>')
        p.append(f'<text x="{x:.0f}" y="{y+7:.0f}" fill="{GOLD2}" font-size="22" font-family="Georgia,serif" '
                 f'font-style="italic" text-anchor="middle">{esc(sym)}</text>')
        # name label, centred on the node's x so it never clips at the sides; above the top node, below the rest
        ny = y - 38 if qmeta[sym]["pos"] == "top" else y + 44
        p.append(f'<text x="{x:.0f}" y="{ny:.0f}" fill="#a99c82" font-size="12.5" '
                 f'font-family="Georgia,serif" text-anchor="middle">{esc(qname[sym])}</text>')

    p.append('</svg>')
    return "\n".join(p)


def _rel_rows(s: dict) -> str:
    order = {"definition": 0, "element": 1, "predicted": 2}
    rows = []
    for r in sorted(s["relations"], key=lambda x: order[x["status"]]):
        col = STATUS_COL[r["status"]]
        tag = {"definition": "definition", "element": "known element", "predicted": "PREDICTED"}[r["status"]]
        prov = ""
        if r["status"] == "element":
            prov = f'<span class=prov>{esc(r.get("since",""))}</span>'
        elif r["status"] == "predicted":
            prov = (f'<span class=prov><b style="color:{GOLD2}">Predicted:</b> {esc(r["predicted"])}<br>'
                    f'<b style="color:{GOLD2}">Confirmed:</b> {esc(r["confirmed"])}</span>')
        elif r.get("note"):
            prov = f'<span class=prov>{esc(r["note"])}</span>'
        note = f'<div class=note>{esc(r["note"])}</div>' if (r.get("note") and r["status"] == "predicted") else ""
        rows.append(
            f'<div class="rel {r["status"]}" data-rel="{esc(r["name"])}">'
            f'<span class=pair style="color:{col}">{esc("–".join(r["pair"]))}</span>'
            f'<span class=main><b>{esc(r.get("element", r["name"].title()))}</b> '
            f'<code>{esc(r["formula"])}</code> <span class=tag style="color:{col}">{tag}</span>{note}</span>'
            f'{prov}</div>')
    return "".join(rows)


def build() -> str:
    s = SETS[0]  # flagship
    svg = _diamond_svg(s)
    rels = _rel_rows(s)
    preds = "".join(
        f'<div class=pred><span class=by>{esc(p["by"])} <span class=yr>{esc(p["year"])}</span></span>'
        f'<span class=body><span class=field>{esc(p["field"])}</span> — in <i>{esc(p["structure"])}</i>, '
        f'{esc(p["hole"])} → <b>{esc(p["predicted"])}</b>. '
        f'<span class=conf>Confirmed {esc(p["confirmed"])}.</span></span></div>'
        for p in PREDICTIONS)
    npred = sum(1 for r in s["relations"] if r["status"] == "predicted")
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Completeness &mdash; the Memristor</title>
<style>
:root{{--bg:{BG};--ink:#e8dfc9;--dim:#a99c82;--faint:#7d745f;--gold:{GOLD};--gold2:{GOLD2};--line:#241f18}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:Georgia,'Iowan Old Style',serif;line-height:1.6}}
.wrap{{max-width:60rem;margin:0 auto;padding:1.8rem 1.1rem 4rem}}
h1{{color:var(--gold);font-weight:400;font-size:2rem;margin:.2rem 0}}
.lede{{color:var(--dim);max-width:48rem}}
svg{{width:100%;height:auto;display:block;max-width:560px;margin:1rem auto}}
.edge{{cursor:default;transition:opacity .12s}}
.edge.pred line{{animation:pulse 2.6s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{opacity:.75}}50%{{opacity:1}}}}
@media(prefers-reduced-motion:reduce){{.edge.pred line{{animation:none}}}}
h2{{color:var(--gold2);font-weight:400;font-size:1.2rem;margin:2.2rem 0 .4rem;border-bottom:1px solid var(--line);padding-bottom:.3rem}}
.rel{{display:grid;grid-template-columns:3.2rem 1fr;gap:.1rem .8rem;padding:.5rem .3rem;border-bottom:1px solid #1c1710;align-items:baseline}}
.rel.predicted{{background:#15120d;border-radius:7px;border:1px solid #3a3118}}
.pair{{font-style:italic;font-size:1.15rem;grid-row:span 2}}
.main b{{color:var(--ink)}}.main code{{color:var(--gold2);font-family:'IBM Plex Mono',ui-monospace,monospace;font-size:.85rem;margin:0 .3rem}}
.tag{{font-size:.68rem;text-transform:uppercase;letter-spacing:.06em}}
.note{{color:var(--dim);font-size:.85rem;margin-top:.15rem}}
.prov{{color:var(--faint);font-size:.8rem;grid-column:2}}
.pred{{display:grid;grid-template-columns:8rem 1fr;gap:.7rem;padding:.5rem .2rem;border-bottom:1px solid #1c1710;font-size:.9rem}}
.pred .by{{color:var(--gold);font-weight:600}}.pred .yr{{color:var(--faint);font-weight:400;font-size:.82rem}}
.pred .field{{color:var(--gold2);text-transform:uppercase;font-size:.72rem;letter-spacing:.05em}}
.pred .body{{color:var(--dim)}}.pred .body b{{color:var(--ink)}}.pred .conf{{color:var(--faint);font-size:.82rem}}
.foot{{color:#7d745f;font-size:.82rem;margin-top:2rem}}
</style></head>
<body><div class=wrap>
<a href="/" target="_top" style="color:#8a8172;font:400 .8rem system-ui,sans-serif;text-decoration:none">&#8592; narrowhighway.com</a>
<h1>Completeness &mdash; the hole in the table is the prediction</h1>
<p class=lede>Some fields have a <b>closed structure</b>: a few fundamental quantities whose pairwise
relations form a complete table. When one cell is empty, symmetry does not merely suggest &mdash; it
<b>demands</b> that something fill it. This is the Atlas as a <b>predictor</b>, not only a map: the same
move that placed every calculation, at the grade of a fundamental element.</p>
<h2>The four circuit variables &mdash; Chua's square</h2>
<p class=lede>{esc(s["gist"])}</p>
{svg}
<p class=lede style="text-align:center;color:var(--faint);font-size:.85rem;max-width:38rem;margin:.2rem auto 0">
The two <span style="color:{DIM}">definitions</span> and the three <span style="color:{GOLD}">known elements</span>
filled five edges. The sixth &mdash; the flux&ndash;charge diagonal, <span style="color:{GOLD2}">M</span> &mdash;
was empty. That emptiness was the prediction.</p>
<h2>The complete relation table</h2>
{rels}
<h2>The class it belongs to &mdash; predictions from a complete structure</h2>
<p class=lede>The memristor is not a curiosity; it is one of the great predictions made not from an
experiment but from the <b>completeness of a structure</b>. Every one below: a complete table, an empty
cell, a real thing found later.</p>
{preds}
<p class=foot>Conduit, not source. Every entry is a <b>confirmed historical</b> prediction, cited by date
and discoverer &mdash; grounded, never invented. Having the Atlas emit a <i>new</i> prediction &mdash; an
unfilled cell we claim must exist &mdash; is the next step, and it must clear the same rigor bar (the
master equations' <code>--check</code>) or it is only apophenia wearing confidence. {npred} predicted-then-
confirmed cell here; {len(PREDICTIONS)} in the class.</p>
</div>
<script>
const edges=[...document.querySelectorAll('#fig .edge')];
const rels=[...document.querySelectorAll('.rel')];
function lite(name){{ edges.forEach(e=>e.style.opacity=(!name||e.dataset.rel===name)?'1':'0.18');
  rels.forEach(r=>r.style.background=(r.dataset.rel===name)?'#1c1810':''); }}
edges.forEach(e=>{{ e.addEventListener('mouseenter',()=>lite(e.dataset.rel)); e.addEventListener('mouseleave',()=>lite(null)); }});
rels.forEach(r=>{{ r.addEventListener('mouseenter',()=>lite(r.dataset.rel)); r.addEventListener('mouseleave',()=>lite(null)); }});
</script>
</body></html>"""


def main():
    out = os.path.join(ROOT, "site", "completeness.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(build())
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
