#!/usr/bin/env python3
"""ATLAS, INTERACTIVE — drive the connections between domains.

Matt, 2026-09-14: "It all needs to be interactive." A single page you operate:
domains on a ring, each master equation a thread through the fields it joins. Click a
master to light up only its thread and read its substitution table; click a field to
see every master equation that runs through it and every calculation it holds; hover
to preview. Data is embedded (so it stays in sync with the seeders); interaction is
vanilla JS, no dependencies, CSP-safe.

    python tools/atlas_explore.py   # writes site/explore.html
"""
import json
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
from seed_bridges import MASTER_EQUATIONS, _load_theory  # noqa: E402
from seed_calculations import CALCS, CALC_THEORY  # noqa: E402

MPAL = ["#c69a4a", "#6f9ec6", "#c67f6f", "#7fb069", "#9b7fc6", "#5fa8a0", "#d1728f",
        "#c6a86f", "#7aa5d2", "#68b0a0", "#a98bd0", "#8fb26a", "#cf8a5c", "#7f9cc8",
        "#c0708f", "#5aa89a", "#b59a52", "#8b7fc4", "#9cae5f", "#d0a15a", "#6fb0c6", "#b98fc0"]
FAMILY = [
    ("physical", ["physics", "electrical", "thermodynamics", "optics", "acoustics",
                  "nuclear_physics", "condensed_matter", "atomic", "materials_science", "quantum_computing"]),
    ("chemical", ["chemistry", "electrochemistry", "periodic_table"]),
    ("life", ["biology", "genetics", "neuroscience", "medicine", "ecology",
              "exercise_science", "nutrition", "agriculture", "soil_science"]),
    ("earth & sky", ["geology", "oceanography", "meteorology", "hydrology", "astronomy",
                     "ephemeris", "geography", "archaeology"]),
    ("formal", ["mathematics", "statistics", "probability", "computer_science", "information_theory",
                "combinatorics", "number_theory", "linear_algebra", "formal_logic", "networking",
                "cryptography", "operations_research"]),
    ("human", ["economics", "finance", "real_estate", "labor", "law", "governance", "game_theory",
               "sports_analytics", "linguistics", "music_theory", "photography", "architecture",
               "construction", "manufacturing", "rhetoric", "history_chronology", "calendar_time"]),
]
FTINT = {"physical": "#c69a4a", "chemical": "#6fb0a0", "life": "#7fb069",
         "earth & sky": "#6f9ec6", "formal": "#9b7fc6", "human": "#c67f6f"}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def sid(s):
    return "".join(ch if ch.isalnum() else "_" for ch in s)


def build():
    masters = []
    for mi, me in enumerate(MASTER_EQUATIONS):
        doms = sorted({d for d, _s, _sub in me["rows"]})
        masters.append({"i": mi, "eq": me["eq"], "gist": me["gist"], "doms": doms,
                        "subs": [[d, sub] for d, _s, sub in me["rows"]]})
    dom_deg = defaultdict(int)
    for m in masters:
        for d in m["doms"]:
            dom_deg[d] += 1
    present = set(dom_deg)

    fam_of, ordered = {}, []
    for fam, doms in FAMILY:
        for d in doms:
            fam_of[d] = fam
            if d in present:
                ordered.append(d)
    for d in sorted(present):
        if d not in ordered:
            ordered.append(d); fam_of.setdefault(d, "human")
    n = len(ordered)
    ang = {d: -math.pi / 2 + 2 * math.pi * i / n for i, d in enumerate(ordered)}
    maxdeg = max(dom_deg.values())

    # calc slug -> which master equations include it, and its parent theory (for granular drill-down)
    theory_titles = _load_theory()[0]
    slug_masters = defaultdict(list)
    for mi, me in enumerate(MASTER_EQUATIONS):
        for _d, s, _sub in me["rows"]:
            slug_masters[s].append(mi)
    all_calcs = {}
    dom_calcs = defaultdict(list)
    for slug, title, formula, domain, form, note in CALCS:
        tid = CALC_THEORY.get(slug)
        all_calcs[slug] = {"t": title, "f": formula, "form": form, "dom": domain,
                           "th": theory_titles.get(tid, "") if tid else "",
                           "m": slug_masters.get(slug, [])}
        dom_calcs[domain].append(slug)

    W = Hh = 1360
    cx = cy = Hh / 2
    Rn = 500

    def node(d):
        return cx + Rn * math.cos(ang[d]), cy + Rn * math.sin(ang[d])

    p = [f'<svg id="fig" viewBox="0 0 {W} {Hh}" xmlns="http://www.w3.org/2000/svg">']
    p.append(f'<rect id="bg" width="100%" height="100%" fill="#0f0d09"/>')

    # family arcs
    fam_idx = defaultdict(list)
    for i, d in enumerate(ordered):
        fam_idx[fam_of[d]].append(i)
    for fam, idxs in fam_idx.items():
        a0 = -math.pi / 2 + 2 * math.pi * (min(idxs) - 0.42) / n
        a1 = -math.pi / 2 + 2 * math.pi * (max(idxs) + 0.42) / n
        col = FTINT.get(fam, "#c69a4a")
        large = 1 if (a1 - a0) > math.pi else 0
        x0, y0 = cx + (Rn + 58) * math.cos(a0), cy + (Rn + 58) * math.sin(a0)
        x1, y1 = cx + (Rn + 58) * math.cos(a1), cy + (Rn + 58) * math.sin(a1)
        p.append(f'<path d="M{x0:.0f} {y0:.0f} A{Rn+58:.0f} {Rn+58:.0f} 0 {large} 1 {x1:.0f} {y1:.0f}" '
                 f'fill="none" stroke="{col}" stroke-width="2.5" opacity="0.5"/>')
        amid = (a0 + a1) / 2
        lx, ly = cx + (Rn + 74) * math.cos(amid), cy + (Rn + 74) * math.sin(amid)
        deg = math.degrees(amid) + (180 if math.cos(amid) < 0 else 0)
        anc = "start" if math.cos(amid) >= 0 else "end"
        p.append(f'<text x="{lx:.0f}" y="{ly:.0f}" fill="{col}" font-size="12" opacity="0.85" '
                 f'font-family="Georgia,serif" text-anchor="{anc}" '
                 f'transform="rotate({deg:.0f} {lx:.0f} {ly:.0f})">{esc(fam)}</text>')

    # threads: one <g> per master (all its segments), so JS toggles the whole thread
    p.append('<g id="threads">')
    for m in masters:
        ds = m["doms"]
        if len(ds) < 2:
            continue
        col = MPAL[m["i"] % len(MPAL)]
        p.append(f'<g class="thread" data-mi="{m["i"]}" stroke="{col}">')
        pts = [node(d) for d in ds]
        for a in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[a], pts[a + 1]
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            ctrlx, ctrly = cx + (mx - cx) * 0.30, cy + (my - cy) * 0.30
            p.append(f'<path d="M{x0:.0f} {y0:.0f} Q{ctrlx:.0f} {ctrly:.0f} {x1:.0f} {y1:.0f}" '
                     f'fill="none" stroke-width="1.5" stroke-linecap="round"/>')
        p.append('</g>')
    p.append('</g>')

    # nodes
    p.append('<g id="nodes">')
    for d in ordered:
        x, y = node(d)
        r = 3.5 + (dom_deg[d] / maxdeg) * 8.5
        col = FTINT.get(fam_of[d], "#c69a4a")
        a = ang[d]
        lx, ly = cx + (Rn + 14) * math.cos(a), cy + (Rn + 14) * math.sin(a)
        rot = math.degrees(a) + (180 if math.cos(a) < 0 else 0)
        anc = "start" if math.cos(a) >= 0 else "end"
        p.append(f'<g class="dnode" data-dom="{esc(d)}" data-fam="{esc(fam_of[d])}">'
                 f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{col}" stroke="#0f0d09" stroke-width="1"/>'
                 f'<text x="{lx:.0f}" y="{ly+2:.0f}" fill="#cbbfa4" font-size="10.5" '
                 f'font-family="Georgia,serif" text-anchor="{anc}" '
                 f'transform="rotate({rot:.0f} {lx:.0f} {ly:.0f})">{esc(d)}</text></g>')
    p.append('</g>')

    p.append(f'<circle cx="{cx}" cy="{cy}" r="46" fill="#0f0d09" stroke="#3a3427"/>')
    p.append(f'<text x="{cx}" y="{cy-2:.0f}" fill="#c69a4a" font-size="12" font-family="Georgia,serif" text-anchor="middle">ATLAS</text>')
    p.append(f'<text x="{cx}" y="{cy+14:.0f}" fill="#8a8378" font-size="9" font-family="Georgia,serif" text-anchor="middle">{n} domains</text>')
    p.append('</svg>')
    svg = "\n".join(p)

    data = {
        "masters": [{"i": m["i"], "eq": m["eq"], "gist": m["gist"], "doms": m["doms"],
                     "subs": m["subs"], "col": MPAL[m["i"] % len(MPAL)]} for m in masters],
        "domDeg": dict(dom_deg),
        "domFam": {d: fam_of[d] for d in ordered},
        "domCalcs": {d: dom_calcs[d] for d in ordered},
        "calcs": all_calcs,
    }
    master_chips = "".join(
        f'<button class="chip" data-mi="{m["i"]}" style="border-color:{MPAL[m["i"]%len(MPAL)]}">'
        f'<span class="sw" style="background:{MPAL[m["i"]%len(MPAL)]}"></span>'
        f'<code>{esc(m["eq"].split("->")[0].strip())}</code></button>'
        for m in masters)

    return """<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Atlas — Explore</title>
<style>
:root{--bg:#0f0d09;--ink:#e8dfc9;--dim:#a99c82;--faint:#7d745f;--gold:#c69a4a;--gold2:#e6c374;--line:#241f18;--panel:#15120d}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:Georgia,'Iowan Old Style',serif}
.wrap{display:flex;gap:0;min-height:100vh;align-items:stretch}
.figwrap{flex:1 1 62%;min-width:0;padding:1rem;display:flex;flex-direction:column}
.figwrap h1{color:var(--gold);font-weight:400;font-size:1.3rem;margin:.2rem .2rem .1rem;letter-spacing:.5px}
.hint{color:var(--faint);font-size:.8rem;margin:0 .2rem .5rem}
#fig{width:100%;height:auto;display:block;flex:1;min-height:0}
.side{flex:0 0 33%;max-width:33%;background:var(--panel);border-left:1px solid var(--line);
  padding:1rem 1rem 2rem;overflow-y:auto;max-height:100vh}
.side h2{color:var(--gold2);font-weight:400;font-size:1rem;margin:.2rem 0 .5rem;border-bottom:1px solid var(--line);padding-bottom:.3rem}
.detail .eq{font-family:'DejaVu Sans Mono',monospace;color:var(--gold2);font-size:1.05rem;margin:.3rem 0}
.detail .gist{color:var(--dim);font-size:.85rem;margin:.1rem 0 .6rem}
.detail table{border-collapse:collapse;width:100%;font-size:.8rem}
.detail td{padding:.2rem .4rem;border-top:1px solid #201c15;vertical-align:top}
.detail td.d{color:var(--gold);white-space:nowrap;cursor:pointer}
.detail td.d:hover{color:var(--gold2);text-decoration:underline}
.detail td.s{color:var(--dim)}
.detail .lead{color:var(--dim);font-size:.86rem}
.mlist{font-size:.82rem}
.mlist .row{padding:.32rem 0;border-top:1px solid #201c15;cursor:pointer;display:flex;gap:.5rem;align-items:center}
.mlist .row:hover{color:var(--gold2)}
.mlist .sw{flex:0 0 auto;width:14px;height:3px;border-radius:2px}
.calc{color:var(--faint);font-size:.78rem;padding:.16rem .2rem;cursor:pointer;border-radius:3px}
.calc code{color:#8a7f63;font-family:'DejaVu Sans Mono',monospace}
.calc:hover{background:#1c1710}.calc:hover b{color:var(--gold2)}.calc:hover code{color:var(--gold)}
.domlink{color:var(--gold);cursor:pointer}.domlink:hover{color:var(--gold2);text-decoration:underline}
.detail .hint{font-size:.72rem}
.chips{display:flex;flex-wrap:wrap;gap:.3rem;margin:.4rem 0}
.chip{background:#161209;border:1px solid var(--line);border-left-width:3px;border-radius:4px;color:var(--ink);
  padding:.18rem .4rem;font:inherit;font-size:.72rem;cursor:pointer}
.chip code{font-family:'DejaVu Sans Mono',monospace}
.chip .sw{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px;vertical-align:middle}
.chip:hover,.chip.on{background:#221a0c}
.bar{display:flex;gap:.5rem;align-items:center;margin:.2rem 0 .5rem}
button.reset{background:#1a1610;border:1px solid var(--line);color:var(--gold);border-radius:4px;padding:.25rem .6rem;cursor:pointer;font:inherit;font-size:.8rem}
button.reset:hover{background:#221a0c}
/* interaction states */
.thread{opacity:.42;transition:opacity .12s}
.thread.dim{opacity:.05}
.thread.hi{opacity:.98}
.thread.hi path{stroke-width:2.6}
.dnode{cursor:pointer}
.dnode circle{transition:opacity .12s}
.dnode.dim{opacity:.28}
.dnode.hi circle{stroke:#fff;stroke-width:1.6}
.dnode.hi text{fill:#fff}
@media(max-width:900px){.wrap{flex-direction:column}.side{max-width:100%;flex-basis:auto;border-left:none;border-top:1px solid var(--line)}}
</style></head>
<body><div class=wrap>
<div class=figwrap>
  <h1>Atlas — the connections between domains</h1>
  <div class=hint>Click a field, or a master equation on the right, to light up its connections. Hover to preview. Click the centre to reset.</div>
  """ + svg + """
</div>
<div class=side>
  <div class=bar><button class=reset id=reset>↺ Reset</button><span id=count class=hint></span></div>
  <div class=detail id=detail></div>
  <h2>The 22 master equations</h2>
  <div class=chips id=chips>""" + master_chips + """</div>
</div>
</div>
<script>
const DATA = """ + json.dumps(data, ensure_ascii=False) + """;
const fig = document.getElementById('fig');
const detail = document.getElementById('detail');
const threads = [...fig.querySelectorAll('.thread')];
const nodes = [...fig.querySelectorAll('.dnode')];
const chips = [...document.querySelectorAll('.chip')];
const nodeByDom = {}; nodes.forEach(g=>nodeByDom[g.dataset.dom]=g);
let pinned = null;

function clearHi(){ threads.forEach(t=>t.classList.remove('hi','dim')); nodes.forEach(nn=>nn.classList.remove('hi','dim')); chips.forEach(c=>c.classList.remove('on')); }
function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function showMaster(mi){
  const m = DATA.masters.find(x=>x.i==mi);
  clearHi();
  threads.forEach(t=>t.classList.add((t.dataset.mi==mi)?'hi':'dim'));
  const dset = new Set(m.doms);
  nodes.forEach(nn=>nn.classList.add(dset.has(nn.dataset.dom)?'hi':'dim'));
  chips.forEach(c=>{ if(c.dataset.mi==mi) c.classList.add('on'); });
  let rows = m.subs.map(([d,s])=>`<tr><td class=d data-dom="${esc(d)}">${esc(d)}</td><td class=s>${esc(s)}</td></tr>`).join('');
  detail.innerHTML = `<div class=eq>${esc(m.eq)}</div><div class=gist>${esc(m.gist)}</div>`+
    `<table>${rows}</table>`;
  wireDomLinks();
  document.getElementById('count').textContent = m.doms.length+' domains connected';
}

function showDomain(dom){
  clearHi();
  const ms = DATA.masters.filter(m=>m.doms.includes(dom));
  const miset = new Set(ms.map(m=>m.i));
  const domset = new Set([dom]); ms.forEach(m=>m.doms.forEach(d=>domset.add(d)));
  threads.forEach(t=>t.classList.add(miset.has(+t.dataset.mi)?'hi':'dim'));
  nodes.forEach(nn=>{ if(nn.dataset.dom===dom) nn.classList.add('hi'); else if(!domset.has(nn.dataset.dom)) nn.classList.add('dim'); });
  const calcs = (DATA.domCalcs[dom]||[]);
  let mrows = ms.map(m=>`<div class=row data-mi="${m.i}"><span class=sw style="background:${m.col}"></span><code style="color:${m.col}">${esc(m.eq.split('->')[0].trim())}</code></div>`).join('');
  let crows = calcs.map(id=>{const c=DATA.calcs[id]; return `<div class=calc data-id="${id}"><b style="color:#bcae8a">${esc(c.t)}</b> <code>${esc(c.f)}</code></div>`;}).join('');
  detail.innerHTML = `<div class=eq style="font-family:Georgia,serif;color:var(--gold)">${esc(dom)}</div>`+
    `<div class=gist>${ms.length} master equation${ms.length==1?'':'s'} run through this field; ${calcs.length} calculation${calcs.length==1?'':'s'} live here.</div>`+
    `<div class=mlist>${mrows||'<div class=lead>No master equation runs through this field yet.</div>'}</div>`+
    `<h2 style="margin-top:.8rem">Calculations here <span class=hint>(click one)</span></h2>${crows||'<div class=lead>none plotted</div>'}`;
  wireMasterRows(); wireDomLinks(); wireCalcRows();
  document.getElementById('count').textContent = dom+' — '+ms.length+' formulas, '+calcs.length+' calcs';
}

function showCalc(slug){
  const c = DATA.calcs[slug]; if(!c) return;
  clearHi();
  const miset = new Set(c.m);
  threads.forEach(t=>t.classList.add(miset.has(+t.dataset.mi)?'hi':'dim'));
  nodes.forEach(nn=>{ if(nn.dataset.dom===c.dom) nn.classList.add('hi'); else nn.classList.add('dim'); });
  const mchips = c.m.map(mi=>{const m=DATA.masters.find(x=>x.i==mi); return `<div class=row data-mi="${mi}"><span class=sw style="background:${m.col}"></span><code style="color:${m.col}">${esc(m.eq.split('->')[0].trim())}</code></div>`;}).join('');
  detail.innerHTML = `<div class=eq>${esc(c.f)}</div>`+
    `<div class=gist>${esc(c.t)} — <span class=domlink data-dom="${esc(c.dom)}">${esc(c.dom)}</span> · form: <b>${esc(c.form)}</b></div>`+
    (c.th?`<div class=lead>rests on the theory: <b style="color:#cbbfa4">${esc(c.th)}</b></div>`:'<div class=lead>an honest theory-gap — no parent theory carded yet</div>')+
    (c.m.length?`<h2 style="margin-top:.6rem">Master equation${c.m.length>1?'s':''} it is part of</h2><div class=mlist>${mchips}</div>`
               :'<div class=lead style="margin-top:.5rem">a domain-specific calculation, not on a master equation</div>');
  wireMasterRows();
  detail.querySelectorAll('.domlink[data-dom]').forEach(el=>el.onclick=()=>{pinned='d'+el.dataset.dom; showDomain(el.dataset.dom);});
  document.getElementById('count').textContent = c.t;
}
function wireCalcRows(){ detail.querySelectorAll('.calc[data-id]').forEach(el=>el.onclick=()=>{pinned='c'+el.dataset.id; showCalc(el.dataset.id);}); }

function wireMasterRows(){ detail.querySelectorAll('.mlist .row').forEach(r=>r.onclick=()=>{pinned='m'+r.dataset.mi; showMaster(r.dataset.mi);}); }
function wireDomLinks(){ detail.querySelectorAll('td.d[data-dom]').forEach(td=>td.onclick=()=>{pinned='d'+td.dataset.dom; showDomain(td.dataset.dom);}); }

function reset(){ pinned=null; clearHi(); detail.innerHTML='<div class=lead>Atlas holds '+DATA.masters.length+' master equations — the formulas that connect across domains. Pick one, or a field, to trace its reach.</div>'; document.getElementById('count').textContent=''; }

threads.forEach(t=>{
  t.addEventListener('mouseenter',()=>{ if(!pinned) showMaster(t.dataset.mi); });
  t.addEventListener('click',(e)=>{ e.stopPropagation(); pinned='m'+t.dataset.mi; showMaster(t.dataset.mi); });
});
nodes.forEach(g=>{
  g.addEventListener('mouseenter',()=>{ if(!pinned) showDomain(g.dataset.dom); });
  g.addEventListener('click',(e)=>{ e.stopPropagation(); pinned='d'+g.dataset.dom; showDomain(g.dataset.dom); });
});
chips.forEach(c=>{
  c.addEventListener('mouseenter',()=>{ if(!pinned) showMaster(c.dataset.mi); });
  c.addEventListener('click',()=>{ pinned='m'+c.dataset.mi; showMaster(c.dataset.mi); });
});
fig.addEventListener('mouseleave',()=>{ if(!pinned) reset(); });
document.getElementById('bg').addEventListener('click',reset);
document.querySelector('#fig circle:last-of-type');
document.getElementById('reset').addEventListener('click',reset);
reset();
</script>
</body></html>"""


def main():
    out = os.path.join(ROOT, "site", "explore.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(build())
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
