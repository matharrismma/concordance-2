#!/usr/bin/env python3
"""THE STRATEGY CONCORDANCE, drawn — the arenas woven by the recurring patterns.

The four arenas (war, politics, business, ministry — plus science and nature where a
pattern reaches) are nodes on a ring; each PATTERN is a thread through every arena it
recurs in. A thread that touches war and ministry alike is the finding: the same move
wins for a general and an apostle. Below the figure, the full catalogue — every pattern,
every case, every piece of evidence. Interactive-lite: hover a thread or a pattern to
light it. Stdlib only; inline SVG + a little vanilla JS.

    python tools/strategy_view.py   # writes site/strategy.html
"""
import html
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
from seed_strategy import PATTERNS, ARENAS  # noqa: E402

MPAL = ["#c69a4a", "#6f9ec6", "#c67f6f", "#7fb069", "#9b7fc6", "#5fa8a0", "#d1728f",
        "#c6a86f", "#7aa5d2", "#68b0a0", "#a98bd0", "#8fb26a", "#cf8a5c", "#b98fc0"]
ATINT = {"war": "#c67f6f", "politics": "#c69a4a", "business": "#6f9ec6",
         "ministry": "#7fb069", "science": "#9b7fc6", "nature": "#5fa8a0"}
ORDER = ["war", "politics", "business", "ministry", "science", "nature"]


def esc(s):
    return html.escape(str(s))


def build():
    used = [a for a in ORDER if any(a in {x[0] for x in p["cases"]} for p in PATTERNS)]
    n = len(used)
    ang = {a: -math.pi / 2 + 2 * math.pi * i / n for i, a in enumerate(used)}
    deg = defaultdict(int)
    for p in PATTERNS:
        for a in {x[0] for x in p["cases"]}:
            deg[a] += 1
    maxd = max(deg.values())

    W = Hh = 1160
    cx = cy = W / 2
    Rn = 430

    def pol(r, a):
        return cx + r * math.cos(a), cy + r * math.sin(a)

    p = [f'<svg id="fig" viewBox="0 0 {W} {Hh}" xmlns="http://www.w3.org/2000/svg">']
    p.append(f'<rect width="100%" height="100%" fill="#0f0d09"/>')
    # threads: each pattern through its arenas
    for pi, pat in enumerate(PATTERNS):
        arenas = [a for a in used if a in {x[0] for x in pat["cases"]}]
        if len(arenas) < 2:
            continue
        col = MPAL[pi % len(MPAL)]
        pts = [pol(Rn, ang[a]) for a in arenas]
        segs = []
        for k in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[k], pts[k + 1]
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            cxp, cyp = cx + (mx - cx) * 0.28, cy + (my - cy) * 0.28
            segs.append(f'<path d="M{x0:.0f} {y0:.0f} Q{cxp:.0f} {cyp:.0f} {x1:.0f} {y1:.0f}" '
                        f'fill="none" stroke="{col}" stroke-width="1.6" opacity="0.5" stroke-linecap="round"/>')
        p.append(f'<g class="thread" data-pi="{pi}" stroke="{col}"><title>{esc(pat["title"])}</title>{"".join(segs)}</g>')
    # arena nodes
    for a in used:
        x, y = pol(Rn, ang[a])
        r = 5 + (deg[a] / maxd) * 9
        col = ATINT.get(a, "#c69a4a")
        p.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{col}" stroke="#0f0d09" stroke-width="1">'
                 f'<title>{esc(a)} — {esc(ARENAS.get(a,""))}: {deg[a]} patterns run through it</title></circle>')
        c = math.cos(ang[a]); lx, ly = pol(Rn + 20, ang[a])
        anchor = "start" if c >= 0 else "end"
        rot = math.degrees(ang[a]) + (180 if c < 0 else 0)
        p.append(f'<text x="{lx:.0f}" y="{ly+3:.0f}" fill="{col}" font-size="15" font-family="Georgia,serif" '
                 f'text-anchor="{anchor}" transform="rotate({rot:.0f} {lx:.0f} {ly:.0f})">{esc(a)}</text>')
        p.append(f'<text x="{lx:.0f}" y="{ly+18:.0f}" fill="#7d745f" font-size="9.5" font-family="Georgia,serif" '
                 f'text-anchor="{anchor}" transform="rotate({rot:.0f} {lx:.0f} {ly+15:.0f})">{esc(ARENAS.get(a,""))}</text>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="52" fill="#0f0d09" stroke="#3a3427"/>')
    p.append(f'<text x="{cx}" y="{cy-4:.0f}" fill="#c69a4a" font-size="14" font-family="Georgia,serif" text-anchor="middle">STRATEGY</text>')
    p.append(f'<text x="{cx}" y="{cy+13:.0f}" fill="#8a8378" font-size="9.5" font-family="Georgia,serif" text-anchor="middle">{len(PATTERNS)} patterns</text>')
    p.append('</svg>')
    svg = "\n".join(p)

    # catalogue
    blocks = []
    for pi, pat in enumerate(sorted(PATTERNS, key=lambda x: -len({a for a, *_ in x["cases"]}))):
        real_pi = PATTERNS.index(pat)
        arenas = sorted({a for a, *_ in pat["cases"]})
        col = MPAL[real_pi % len(MPAL)]
        rows = "".join(
            f'<div class=case><span class=ar style="color:{ATINT.get(a,"#c69a4a")}">{esc(a)}</span>'
            f'<span class=who>{esc(who)} <span class=when>{esc(when)}</span></span>'
            f'<span class=ev>{esc(move)}. <i>{esc(ev)}</i></span></div>'
            for a, who, when, move, ev in pat["cases"])
        blocks.append(
            f'<div class=pat data-pi="{real_pi}" id="pat{real_pi}">'
            f'<h3 style="border-color:{col}"><span class=dot style="background:{col}"></span>{esc(pat["title"])}'
            f'<span class=span>{len(arenas)} arenas</span></h3>'
            f'<p class=gist>{esc(pat["gist"])}</p>{rows}</div>')

    ncases = sum(len(p["cases"]) for p in PATTERNS)
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<script src="/shell.js"></script>
<title>The Strategy Concordance</title>
<style>
:root{{--bg:#0f0d09;--ink:#e8dfc9;--dim:#a99c82;--faint:#7d745f;--gold:#c69a4a;--gold2:#e6c374;--line:#241f18}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:Georgia,'Iowan Old Style',serif;line-height:1.6}}
.wrap{{max-width:66rem;margin:0 auto;padding:1.8rem 1.1rem 4rem}}
h1{{color:var(--gold);font-weight:400;font-size:2rem;margin:.2rem 0}}
.lede{{color:var(--dim);max-width:48rem}}svg{{width:100%;height:auto;display:block;max-width:840px;margin:.5rem auto}}
.thread{{transition:opacity .12s}}.thread.dim{{opacity:.06}}.thread.hi{{opacity:1}}.thread.hi path{{stroke-width:2.7}}
h2{{color:var(--gold2);font-weight:400;font-size:1.2rem;margin:2rem 0 .3rem;border-bottom:1px solid var(--line);padding-bottom:.3rem}}
.pat{{padding:.7rem .2rem;border-bottom:1px solid #201c15}}
.pat.hi{{background:#15120d;border-radius:6px}}
.pat h3{{font-weight:400;font-size:1.08rem;color:var(--ink);margin:.1rem 0 .3rem;border-left:3px solid var(--gold);padding-left:.55rem}}
.pat h3 .dot{{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px;vertical-align:middle}}
.span{{float:right;color:var(--faint);font-size:.72rem;text-transform:uppercase;letter-spacing:.04em}}
.gist{{color:var(--gold2);font-size:.92rem;margin:.15rem 0 .5rem .55rem}}
.case{{display:grid;grid-template-columns:5.5rem 1fr;gap:.15rem .7rem;padding:.28rem 0 .28rem .55rem;border-top:1px solid #1c1710;font-size:.86rem}}
.case .ar{{grid-row:span 2;font-size:.8rem;padding-top:.1rem}}
.case .who{{color:var(--ink)}}.case .when{{color:var(--faint);font-size:.8rem}}
.case .ev{{color:var(--dim);font-size:.82rem}}.case .ev i{{color:var(--faint)}}
</style></head>
<body><div class=wrap>

<h1>The Strategy Concordance</h1>
<p class=lede>The same method that found the master equations of computation, turned on <b>history</b>: the
recurring <b>patterns</b> of building things that win and endure. Each arena on the ring &mdash; the field,
the state, the enterprise, the church &mdash; is a domain; each <b>thread</b> is one pattern, drawn through
every arena it recurs in. A thread that ties war to ministry is the finding: the same move wins for a
general and an apostle. Found across time, not invented; every case carries its evidence.
{len(PATTERNS)} patterns &middot; {ncases} cases &middot; {n} arenas.</p>
{svg}
<h2>The patterns, and their cases across time</h2>
{''.join(blocks)}
<p class=lede style="color:#7d745f;font-size:.82rem;margin-top:2rem">Gathered, not generated. A pattern that
recurs across arenas and across centuries is a bridge &mdash; the universality of the form, in the world of
action. We look across time.</p>
</div>
<script>
const fig=document.getElementById('fig');
const threads=[...fig.querySelectorAll('.thread')];
const pats=[...document.querySelectorAll('.pat')];
function lite(pi){{ threads.forEach(t=>t.classList.toggle('hi',t.dataset.pi==pi)); threads.forEach(t=>t.classList.toggle('dim',t.dataset.pi!=pi)); pats.forEach(x=>x.classList.toggle('hi',x.dataset.pi==pi)); }}
function clear(){{ threads.forEach(t=>t.classList.remove('hi','dim')); pats.forEach(x=>x.classList.remove('hi')); }}
threads.forEach(t=>{{ t.addEventListener('mouseenter',()=>lite(t.dataset.pi)); t.addEventListener('mouseleave',clear);
  t.addEventListener('click',()=>{{ const el=document.getElementById('pat'+t.dataset.pi); el&&el.scrollIntoView({{behavior:'smooth',block:'center'}}); lite(t.dataset.pi); }}); }});
pats.forEach(x=>{{ x.addEventListener('mouseenter',()=>lite(x.dataset.pi)); x.addEventListener('mouseleave',clear); }});
</script>
</body></html>"""


def main():
    out = os.path.join(ROOT, "site", "strategy.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(build())
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
