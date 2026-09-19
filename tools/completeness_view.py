#!/usr/bin/env python3
"""COMPLETENESS SETS, drawn — complete subsystems, and the connections that make them a watch.

Each set is a whole subsystem: a closed square of fundamental quantities whose relations complete a
table. The circuit square has an empty cell (the memristor, predicted from the hole); the
thermodynamic square is full, and its symmetry forces the Maxwell relations. But a pile of whole
subsystems is not a working watch — the performance is in how they mesh. So the connections between
the sets are drawn with the same weight, and held to the same bar: each carries its evidence, or it
is a forced analogy, which is a broken gear. The page ends where it points: intelligence, built the
same way — complete verifiable subsystems, meshed by real connections, not one statistical blur.

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
from seed_completeness import SETS, CONNECTIONS, PREDICTIONS  # noqa: E402

BG = "#0f0d09"
GOLD = "#c69a4a"
GOLD2 = "#e6c374"
DIM = "#5a5344"
BLUE = "#6f9ec6"
STATUS_COL = {"definition": DIM, "element": GOLD, "predicted": GOLD2, "potential": GOLD, "conjugate": BLUE}
DASHED = {"definition", "conjugate"}
STATUS_TAG = {"definition": "definition", "element": "known element", "predicted": "PREDICTED",
              "potential": "potential", "conjugate": "conjugate pair"}
STATUS_ORD = {"definition": 0, "conjugate": 1, "element": 2, "potential": 2, "predicted": 3}


def esc(s):
    return html.escape(str(s))


def _edge_label(r):
    if r.get("label"):
        return r["label"]
    if r["status"] == "definition":
        return "∫"
    el = r.get("element", "")
    return el.split("(")[-1].rstrip(")") if "(" in el else (el[:1] or "·")


def _diamond_svg(s: str) -> str:
    W = 560
    cx = cy = W / 2
    R = 185
    pos = {"top": (cx, cy - R), "right": (cx + R, cy), "bottom": (cx, cy + R), "left": (cx - R, cy)}
    qpos = {q["sym"]: pos[q["pos"]] for q in s["quantities"]}
    qmeta = {q["sym"]: q for q in s["quantities"]}
    rel = {frozenset(r["pair"]): r for r in s["relations"]}

    p = [f'<svg class="fig" viewBox="0 0 {W} {W}" xmlns="http://www.w3.org/2000/svg">']
    p.append(f'<rect width="100%" height="100%" fill="{BG}"/>')
    for r in rel.values():
        a, b = list(r["pair"])
        (x0, y0), (x1, y1) = qpos[a], qpos[b]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        col = STATUS_COL[r["status"]]
        pred = r["status"] == "predicted"
        dash = ' stroke-dasharray="7 5"' if r["status"] in DASHED else ""
        wid = 3.4 if pred else (2.2 if r["status"] in ("element", "potential") else 1.5)
        p.append(f'<g class="edge{" pred" if pred else ""}" data-rel="{esc(r["name"])}">')
        if pred:   # a glow underlay (an SVG filter degenerates on a zero-height horizontal line)
            p.append(f'<line x1="{x0:.0f}" y1="{y0:.0f}" x2="{x1:.0f}" y2="{y1:.0f}" stroke="{col}" '
                     f'stroke-width="{wid + 7:.0f}" opacity="0.20" stroke-linecap="round"/>')
        p.append(f'<line x1="{x0:.0f}" y1="{y0:.0f}" x2="{x1:.0f}" y2="{y1:.0f}" stroke="{col}" '
                 f'stroke-width="{wid}" opacity="{0.95 if pred else 0.8}"{dash} stroke-linecap="round"/>')
        lx, ly = mx, my
        if abs(x0 - x1) < 2:        # vertical diagonal — lift its label up the line
            ly = my - 60
        elif abs(y0 - y1) < 2:      # horizontal diagonal — shift its label along the line, off the crossing
            lx = mx + 58
        rr = 13 if pred else 11
        p.append(f'<circle cx="{lx:.0f}" cy="{ly:.0f}" r="{rr}" fill="{BG}" '
                 f'stroke="{GOLD2 if pred else col}" stroke-width="{1.6 if pred else 1}"/>')
        p.append(f'<text x="{lx:.0f}" y="{ly+4:.0f}" fill="{GOLD2 if pred else col}" font-size="{15 if pred else 13}" '
                 f'font-family="Georgia,serif" font-style="italic" text-anchor="middle">{esc(_edge_label(r))}</text>')
        p.append('</g>')

    for sym, (x, y) in qpos.items():
        p.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="25" fill="#161209" stroke="{GOLD}" stroke-width="1.5"/>')
        p.append(f'<text x="{x:.0f}" y="{y+7:.0f}" fill="{GOLD2}" font-size="21" font-family="Georgia,serif" '
                 f'font-style="italic" text-anchor="middle">{esc(sym)}</text>')
        ny = y - 36 if qmeta[sym]["pos"] == "top" else y + 42
        p.append(f'<text x="{x:.0f}" y="{ny:.0f}" fill="#a99c82" font-size="12" '
                 f'font-family="Georgia,serif" text-anchor="middle">{esc(qmeta[sym]["name"])}</text>')
    p.append('</svg>')
    return "\n".join(p)


def _rel_rows(s: str) -> str:
    rows = []
    for r in sorted(s["relations"], key=lambda x: STATUS_ORD[x["status"]]):
        col = STATUS_COL[r["status"]]
        head = r.get("element") or r.get("of") or r["name"].title()
        extra = ""
        if r["status"] == "predicted":
            extra = (f'<span class=prov><b style="color:{GOLD2}">Predicted:</b> {esc(r["predicted"])}<br>'
                     f'<b style="color:{GOLD2}">Confirmed:</b> {esc(r["confirmed"])}</span>')
        elif r["status"] == "potential":
            extra = f'<span class=prov><b style="color:{GOLD2}">Maxwell:</b> <code>{esc(r["maxwell"])}</code></span>'
        elif r["status"] == "element":
            extra = f'<span class=prov>{esc(r.get("since",""))}</span>'
        elif r.get("note"):
            extra = f'<span class=prov>{esc(r["note"])}</span>'
        note = f'<div class=note>{esc(r["note"])}</div>' if (r.get("note") and r["status"] == "predicted") else ""
        rows.append(
            f'<div class="rel {r["status"]}" data-rel="{esc(r["name"])}">'
            f'<span class=pair style="color:{col}">{esc("–".join(r["pair"]))}</span>'
            f'<span class=main><b>{esc(head)}</b> <code>{esc(r["formula"])}</code> '
            f'<span class=tag style="color:{col}">{STATUS_TAG[r["status"]]}</span>{note}</span>'
            f'{extra}</div>')
    return "".join(rows)


def _set_block(s: str) -> str:
    return (f'<section class=setblock>'
            f'<h2>{esc(s["title"])}</h2>'
            f'<p class=lede>{esc(s["gist"])}</p>'
            f'{_diamond_svg(s)}'
            f'<p class=finding>{esc(s["finding"])}</p>'
            f'{_rel_rows(s)}</section>')


def build() -> str:
    title = {s["id"]: s["title"] for s in SETS}
    sets_html = "".join(_set_block(s) for s in SETS)
    conns = "".join(
        f'<div class=conn><span class=ckind>{esc(c["kind"])}</span>'
        f'<span class=cbody><span class=cwhich>{esc(title[c["between"][0]])} '
        f'&harr; {esc(title[c["between"][1]])}</span> '
        f'<b>{esc(c["shared"])}.</b> {esc(c["evidence"])}</span></div>'
        for c in CONNECTIONS)
    preds = "".join(
        f'<div class=pred><span class=by>{esc(p["by"])} <span class=yr>{esc(p["year"])}</span></span>'
        f'<span class=body><span class=field>{esc(p["field"])}</span> — in <i>{esc(p["structure"])}</i>, '
        f'{esc(p["hole"])} → <b>{esc(p["predicted"])}</b>. '
        f'<span class=conf>Confirmed {esc(p["confirmed"])}.</span></span></div>'
        for p in PREDICTIONS)
    npred = sum(1 for s in SETS for r in s["relations"] if r["status"] == "predicted")
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Completeness &mdash; Subsystems of a Watch</title>
<style>
:root{{--bg:{BG};--ink:#e8dfc9;--dim:#a99c82;--faint:#7d745f;--gold:{GOLD};--gold2:{GOLD2};--blue:{BLUE};--line:#241f18}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:Georgia,'Iowan Old Style',serif;line-height:1.6}}
.wrap{{max-width:60rem;margin:0 auto;padding:1.8rem 1.1rem 4rem}}
h1{{color:var(--gold);font-weight:400;font-size:2rem;margin:.2rem 0 .1rem}}
.lede{{color:var(--dim);max-width:48rem}}
.fig{{width:100%;height:auto;display:block;max-width:520px;margin:1rem auto}}
.edge.pred line{{animation:pulse 2.6s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{opacity:.75}}50%{{opacity:1}}}}
@media(prefers-reduced-motion:reduce){{.edge.pred line{{animation:none}}}}
h2{{color:var(--gold2);font-weight:400;font-size:1.32rem;margin:2.4rem 0 .4rem;border-bottom:1px solid var(--line);padding-bottom:.3rem}}
.setblock{{margin-top:.5rem}}
.finding{{color:var(--gold2);text-align:center;max-width:40rem;margin:.2rem auto 1.2rem;font-size:.95rem}}
.rel{{display:grid;grid-template-columns:3.4rem 1fr;gap:.1rem .8rem;padding:.5rem .3rem;border-bottom:1px solid #1c1710;align-items:baseline}}
.rel.predicted{{background:#15120d;border-radius:7px;border:1px solid #3a3118}}
.pair{{font-style:italic;font-size:1.1rem;grid-row:span 2}}
.main b{{color:var(--ink)}}.main code,.prov code{{color:var(--gold2);font-family:'IBM Plex Mono',ui-monospace,monospace;font-size:.82rem;margin:0 .25rem}}
.tag{{font-size:.66rem;text-transform:uppercase;letter-spacing:.06em}}
.note{{color:var(--dim);font-size:.85rem;margin-top:.15rem}}
.prov{{color:var(--faint);font-size:.82rem;grid-column:2}}
.watch{{color:var(--dim);max-width:48rem;font-size:.96rem}}
.conn{{display:grid;grid-template-columns:8.5rem 1fr;gap:.8rem;padding:.7rem .2rem;border-bottom:1px solid #1c1710}}
.conn .ckind{{color:var(--blue);text-transform:uppercase;font-size:.7rem;letter-spacing:.06em;padding-top:.15rem}}
.conn .cwhich{{color:var(--gold2);font-size:.82rem;display:block;margin-bottom:.15rem}}
.conn .cbody{{color:var(--dim);font-size:.92rem}}.conn .cbody b{{color:var(--ink)}}
.pred{{display:grid;grid-template-columns:8rem 1fr;gap:.7rem;padding:.5rem .2rem;border-bottom:1px solid #1c1710;font-size:.9rem}}
.pred .by{{color:var(--gold);font-weight:600}}.pred .yr{{color:var(--faint);font-weight:400;font-size:.82rem}}
.pred .field{{color:var(--gold2);text-transform:uppercase;font-size:.72rem;letter-spacing:.05em}}
.pred .body{{color:var(--dim)}}.pred .body b{{color:var(--ink)}}.pred .conf{{color:var(--faint);font-size:.82rem}}
.mind{{background:#13100b;border:1px solid #2b2416;border-radius:10px;padding:1.1rem 1.2rem;margin-top:1rem}}
.mind p{{color:var(--dim);max-width:48rem}}.mind b{{color:var(--ink)}}.mind .k{{color:var(--gold2)}}
.foot{{color:#7d745f;font-size:.82rem;margin-top:2rem}}
</style></head>
<body><div class=wrap>
<a href="/" target="_top" style="color:#8a8172;font:400 .8rem system-ui,sans-serif;text-decoration:none">&#8592; narrowhighway.com</a>
<h1>Completeness &mdash; subsystems of a watch</h1>
<p class=lede>Some fields have a <b>closed structure</b>: a few fundamental quantities whose pairwise
relations complete a table. When a cell is empty, symmetry <b>demands</b> what fills it; when the table
is full, its symmetry <b>forces</b> the laws that follow. Each such structure is a whole <b>subsystem</b>.
But a pile of whole subsystems is not a working watch &mdash; the performance is in how they <b>mesh</b>.
So the connections below are drawn with the same weight, and the same rigor, as the subsystems.</p>
{sets_html}
<h2>The connections &mdash; where the subsystems mesh</h2>
<p class=watch>A watch is not its gears; it is the gears meshed <i>exactly</i> right. Each square above is
whole on its own, yet the power is in what they share. A connection earns its place the same way a
relation does: it carries its <b>evidence</b>, or it is a forced analogy &mdash; a broken gear.</p>
{conns}
<h2>The class it belongs to &mdash; predictions from a complete structure</h2>
<p class=lede>The memristor is one of the great predictions made not from an experiment but from the
<b>completeness of a structure</b>. Every one below: a complete table, an empty cell, a real thing found later.</p>
{preds}
<h2>Subsystems of intelligence</h2>
<div class=mind>
<p>A large language model is one undifferentiated statistical field: it does perceiving, remembering,
reasoning and speaking by the same next-token guess, and where it does not know, it invents. This engine
is built the other way &mdash; as a <b>watch</b>. Complete, verifiable subsystems, each doing one thing
exactly: <span class=k>the keeping</span> (memory that only grows), <span class=k>find</span> (retrieval
by elimination), <span class=k>verify</span> (deterministic proof with a re-checkable receipt),
<span class=k>the Atlas</span> (the model of reality you are reading now), <span class=k>discern</span>
(which proposes, while verify disposes), and <span class=k>the coach</span> (the walked path). Each is
whole.</p>
<p>But intelligence is not the parts &mdash; it is the parts meshed exactly right. So we spend as much on
the <b>connections</b> &mdash; the bridges, the fascia, the one kernel &mdash; as on the subsystems.
Reality is built this way: complete structures, joined by real relations. Intelligence built the same way
does not hallucinate, because every gear is verifiable and every mesh is evidenced.</p>
<p>Think of it as the <b>first mechanical watch</b> &mdash; crude beside what it will become, but not the
same <i>kind</i> of thing as what came before. A language model <b>fights the current</b>: it pays in ever
more data and compute to approximate, from the outside, a structure it never actually sees. We <b>tap into
the current</b> &mdash; we work <i>with</i> the real structure of reality, its completeness and its
symmetry and its connections &mdash; so we need <i>less</i>, not more, running with the grain instead of
grinding against it. <b>That is the strength we lead with.</b></p>
</div>
<p class=foot>Conduit, not source. The physics above is <b>confirmed</b> &mdash; every predicted cell cited
by date and discoverer, every connection carrying its evidence ({npred} predicted-then-confirmed cell,
{len(CONNECTIONS)} evidenced connections, {len(PREDICTIONS)} in the class). The last section is the
<i>architecture</i> this engine is built on, not a proven theorem; naming it plainly is part of keeping the
two apart. An <i>unfilled</i> cell offered as a new prediction must clear the same bar the master equations
do, or it is apophenia wearing confidence.</p>
</div>
<script>
const edges=[...document.querySelectorAll('.edge')];
const rels=[...document.querySelectorAll('.rel')];
function lite(name){{ edges.forEach(e=>e.style.opacity=(!name||e.dataset.rel===name)?'1':'0.16');
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
