#!/usr/bin/env python3
"""ATLAS, INTERACTIVE & UNIFIED — every view live, one selection.

Matt, 2026-09-14: "It all needs to be interactive and selectable. We need to interact
with granularity." One page, five layouts of the same body (kernel / form wheel / one
body / spiral / domains), a shared selection, and a shared detail panel. Select a
master equation, a domain, a form, a theory, or a single calculation, and every layout
and the panel respond; switch layout and the selection is kept. Data is embedded from
the seeders; interaction is vanilla JS, no dependencies, CSP-safe.

    python tools/atlas_explore.py   # writes site/explore.html
"""
import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass
from seed_bridges import MASTER_EQUATIONS, FORM_DUALITIES, _load_theory  # noqa: E402
from seed_calculations import CALCS, CALC_THEORY, FORMS, FORM_PARENT, leaf_forms_ordered  # noqa: E402

DPAL = ["#c69a4a", "#6f9ec6", "#9b7fc6", "#7fb069", "#5fa8a0", "#c67f6f", "#c6a86f",
        "#d1728f", "#7aa5d2", "#b0894a", "#68b0a0", "#a98bd0", "#8fb26a", "#cf8a5c",
        "#7f9cc8", "#c0708f", "#5aa89a", "#b59a52", "#8b7fc4", "#9cae5f", "#d0a15a",
        "#6fb0c6", "#b98fc0", "#86b57f", "#b6844f", "#7c96c2", "#a37ec0", "#7aa86a"]
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
FAMTINT = {"ratio": "#c69a4a", "exponential": "#c67f6f", "modular": "#6f9ec6", "rate": "#d0a15a"}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build():
    theory_titles = _load_theory()[0]
    all_domains = sorted({c[3] for c in CALCS})
    dcol = {d: DPAL[i % len(DPAL)] for i, d in enumerate(all_domains)}

    fam_of = {}
    for fam, ds in FAMILY:
        for d in ds:
            fam_of[d] = fam
    # domain ring order (family-grouped), all domains present
    dom_order = []
    for fam, ds in FAMILY:
        for d in ds:
            if d in all_domains:
                dom_order.append(d)
    for d in all_domains:
        if d not in dom_order:
            dom_order.append(d); fam_of.setdefault(d, "human")

    slug_masters = defaultdict(list)
    for mi, me in enumerate(MASTER_EQUATIONS):
        for _d, s, _sub in me["rows"]:
            slug_masters[s].append(mi)

    calcs = {}
    calcs_by_form = defaultdict(list)
    for slug, title, formula, domain, form, note in CALCS:
        tid = CALC_THEORY.get(slug)
        calcs[slug] = {"t": title, "f": formula, "form": form, "dom": domain,
                       "th": theory_titles.get(tid, "") if tid else "", "thid": tid or "",
                       "m": slug_masters.get(slug, [])}
        calcs_by_form[form].append(slug)

    masters = []
    for mi, me in enumerate(MASTER_EQUATIONS):
        mem = [s for _d, s, _sub in me["rows"]]
        forms = [calcs[s]["form"] for s in mem if s in calcs]
        domf = Counter(forms).most_common(1)
        masters.append({"i": mi, "eq": me["eq"], "gist": me["gist"],
                        "doms": sorted({d for d, _s, _sub in me["rows"]}),
                        "subs": [[d, sub] for d, _s, sub in me["rows"]],
                        "members": mem, "domform": domf[0][0] if domf else "",
                        "col": MPAL[mi % len(MPAL)]})

    leaf = leaf_forms_ordered()
    form_dom = {f: len({calcs[s]["dom"] for s in calcs_by_form.get(f, [])}) for f in FORMS}
    # theory same_form isomorphisms (deduped, both endpoints resolvable)
    iso_seen, theory_iso = set(), []
    for a, b, ev in _load_theory()[1]:
        key = frozenset((a, b))
        if key in iso_seen or a not in theory_titles or b not in theory_titles:
            continue
        iso_seen.add(key)
        theory_iso.append([a, b, ev])
    iso_theories = {t for e in theory_iso for t in e[:2]}
    calc_theories = {c["thid"] for c in calcs.values() if c["thid"]}
    show_theories = calc_theories | iso_theories
    data = {
        "domOrder": dom_order, "domFam": fam_of, "dcol": dcol, "ftint": FTINT,
        "calcs": calcs, "calcsByForm": {f: calcs_by_form[f] for f in calcs_by_form},
        "leaf": leaf, "formList": list(FORMS), "formEq": {f: FORMS[f][0] for f in FORMS},
        "formParent": FORM_PARENT, "formDom": form_dom, "famTint": FAMTINT, "masters": masters,
        "theoryTitles": {t: theory_titles.get(t, t) for t in show_theories},
        "dualities": [[a, b, k, e] for a, b, k, e in FORM_DUALITIES],
        "theoryIso": theory_iso, "mpal": MPAL,
        "counts": {"calcs": len(calcs), "forms": len(FORMS), "masters": len(masters),
                   "domains": len(all_domains), "theories": len(theory_titles),
                   "dualities": len(FORM_DUALITIES), "iso": len(theory_iso)},
    }
    chips = "".join(
        f'<button class="chip" data-mi="{m["i"]}" style="border-left-color:{m["col"]}">'
        f'<span class="sw" style="background:{m["col"]}"></span>'
        f'<code>{esc(m["eq"].split("->")[0].strip())}</code></button>' for m in masters)

    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")  # never break out of <script>
    return _SHELL.replace("__DATA__", payload).replace("__CHIPS__", chips)


# ---------------------------------------------------------------------------- the page
_SHELL = r"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Atlas</title>
<style>
:root{--bg:#0f0d09;--ink:#e8dfc9;--dim:#a99c82;--faint:#7d745f;--gold:#c69a4a;--gold2:#e6c374;--line:#241f18;--panel:#15120d}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:Georgia,'Iowan Old Style',serif}
.wrap{display:flex;min-height:100vh}
.figwrap{flex:1 1 63%;min-width:0;padding:.8rem 1rem;display:flex;flex-direction:column}
.top{display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;margin:.1rem 0 .3rem}
.top h1{color:var(--gold);font-weight:400;font-size:1.2rem;margin:0;letter-spacing:.5px}
.tabs{display:flex;gap:.25rem;flex-wrap:wrap}
.tab{background:#161209;border:1px solid var(--line);color:var(--dim);border-radius:5px;padding:.22rem .6rem;
  cursor:pointer;font:inherit;font-size:.8rem}
.tab:hover{color:var(--ink)}.tab.on{background:#241a0b;color:var(--gold2);border-color:#5a4a28}
.hint{color:var(--faint);font-size:.76rem;margin:0}
#fig{width:100%;height:auto;display:block;flex:1;min-height:0}
.side{flex:0 0 34%;max-width:34%;background:var(--panel);border-left:1px solid var(--line);
  padding:.9rem 1rem 2rem;overflow-y:auto;max-height:100vh}
.side h2{color:var(--gold2);font-weight:400;font-size:.98rem;margin:.6rem 0 .4rem;border-bottom:1px solid var(--line);padding-bottom:.25rem}
.bar{display:flex;gap:.5rem;align-items:center;margin:0 0 .5rem}
.reset{background:#1a1610;border:1px solid var(--line);color:var(--gold);border-radius:4px;padding:.25rem .6rem;cursor:pointer;font:inherit;font-size:.8rem}
.reset:hover{background:#221a0c}
.search{flex:1;background:#120f0a;border:1px solid var(--line);color:var(--ink);border-radius:4px;padding:.28rem .5rem;font:inherit;font-size:.82rem}
.detail .eq{font-family:'DejaVu Sans Mono',monospace;color:var(--gold2);font-size:1.02rem;margin:.2rem 0;word-break:break-word}
.detail .gist{color:var(--dim);font-size:.85rem;margin:.1rem 0 .5rem}
.detail table{border-collapse:collapse;width:100%;font-size:.8rem}
.detail td{padding:.2rem .4rem;border-top:1px solid #201c15;vertical-align:top}
.detail td.d{color:var(--gold);white-space:nowrap;cursor:pointer}.detail td.d:hover{color:var(--gold2);text-decoration:underline}
.detail td.s{color:var(--dim)}
.detail .lead{color:var(--dim);font-size:.86rem}
.mlist .row{padding:.3rem 0;border-top:1px solid #201c15;cursor:pointer;display:flex;gap:.5rem;align-items:center;font-size:.82rem}
.mlist .row:hover{color:var(--gold2)}.mlist .sw{flex:0 0 auto;width:14px;height:3px;border-radius:2px}
.calc{color:var(--faint);font-size:.78rem;padding:.16rem .25rem;cursor:pointer;border-radius:3px}
.calc code{color:#8a7f63;font-family:'DejaVu Sans Mono',monospace}
.calc:hover{background:#1c1710}.calc:hover b{color:var(--gold2)}.calc:hover code{color:var(--gold)}
.calc b{color:#bcae8a;font-weight:400}
.domlink,.formlink,.thlink{color:var(--gold);cursor:pointer}.domlink:hover,.formlink:hover,.thlink:hover{color:var(--gold2);text-decoration:underline}
.chips{display:flex;flex-wrap:wrap;gap:.3rem;margin:.3rem 0}
.chip{background:#161209;border:1px solid var(--line);border-left-width:3px;border-radius:4px;color:var(--ink);
  padding:.18rem .4rem;font:inherit;font-size:.7rem;cursor:pointer}
.chip code{font-family:'DejaVu Sans Mono',monospace}.chip .sw{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px;vertical-align:middle}
.chip:hover,.chip.on{background:#241a0b}
/* selection states, applied to any layout */
.node,.thread{transition:opacity .1s}
.dim{opacity:.06 !important}
.calcdot{cursor:pointer}
.hi{opacity:1 !important}
.hi.calcdot{stroke:#fff !important;stroke-width:1.6px !important}
.hi.mnode{stroke:#fff !important;stroke-width:2px !important}
text.lbl{font-family:Georgia,serif;pointer-events:none}
@media(max-width:900px){.wrap{flex-direction:column}.side{max-width:100%;flex-basis:auto;border-left:none;border-top:1px solid var(--line)}}
</style></head>
<body><div class=wrap>
<div class=figwrap>
  <div class=top>
    <h1>Atlas</h1>
    <div class=tabs id=tabs>
      <button class=tab data-l=kernel>kernel</button>
      <button class=tab data-l=wheel>form wheel</button>
      <button class=tab data-l=onebody>one body</button>
      <button class=tab data-l=spiral>spiral</button>
      <button class=tab data-l=domains>domains</button>
      <button class=tab data-l=bridges>bridges</button>
    </div>
  </div>
  <div class=hint id=hint>Hover to preview, click to select. Selection is kept when you switch layout.</div>
  <svg id=fig viewBox="0 0 1200 1200" xmlns="http://www.w3.org/2000/svg"></svg>
</div>
<div class=side>
  <div class=bar><button class=reset id=reset>&#8635;</button>
    <input class=search id=search placeholder="search a calculation, field, theory…" autocomplete=off></div>
  <div class=detail id=detail></div>
  <h2>The 22 master equations</h2>
  <div class=chips id=chips>__CHIPS__</div>
</div>
</div>
<script>
const D = __DATA__;
const NS="http://www.w3.org/2000/svg";
const fig=document.getElementById('fig'), detail=document.getElementById('detail');
const CX=600, CY=600;
let layout='kernel';
let sel=null;              // {type:'master'|'domain'|'calc'|'form'|'theory', id}
let pinned=false;

function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function E(tag,at,kids){const e=document.createElementNS(NS,tag);for(const k in at)e.setAttribute(k,at[k]);
  if(kids)kids.forEach(c=>e.appendChild(c));return e;}
function pol(r,a){return [CX+r*Math.cos(a),CY+r*Math.sin(a)];}
const dcol=d=>D.dcol[d]||'#8a8378';
const domIdx={}; D.domOrder.forEach((d,i)=>domIdx[d]=i);
const leafIdx={}; D.leaf.forEach((f,i)=>leafIdx[f]=i);
function formRoot(f){while(D.formParent[f])f=D.formParent[f];return f;}

// ---- registries so applyHi can find drawn elements ----
let reg;
function tt(node,text){const t=E('title',{});t.textContent=text;node.appendChild(t);return node;}

function clearFig(){fig.innerHTML='';reg={calc:{},dom:{},master:{},form:{},theory:{},thread:{},du:{}};
  fig.appendChild(E('rect',{id:'bg',x:0,y:0,width:1200,height:1200,fill:'#0f0d09'}));}

function calcDot(slug,x,y,r){const c=D.calcs[slug];const dot=E('circle',{cx:x,cy:y,r:r||4.4,
  fill:dcol(c.dom),stroke:'#0f0d09','stroke-width':.7,class:'node calcdot','data-id':slug});
  tt(dot,c.t+' — '+c.dom+' · '+c.form);
  dot.addEventListener('mouseenter',()=>{if(!pinned)showCalc(slug);});
  dot.addEventListener('click',e=>{e.stopPropagation();pinned=true;showCalc(slug);});
  (reg.calc[slug]=reg.calc[slug]||[]).push(dot);fig.appendChild(dot);return dot;}

function lbl(x,y,text,size,fill,anchor,rot){const t=E('text',{x:x,y:y,'font-size':size||10,
  fill:fill||'#cbbfa4','text-anchor':anchor||'middle',class:'lbl'});
  if(rot!==undefined)t.setAttribute('transform','rotate('+rot+' '+x+' '+y+')');
  t.textContent=text;fig.appendChild(t);return t;}

// theory placement helper (mean angle of its calcs given an angle map)
function theoryRim(angleOf, Rt){
  const byT={};
  for(const slug in D.calcs){const c=D.calcs[slug];if(c.thid&&angleOf[slug]!==undefined)(byT[c.thid]=byT[c.thid]||[]).push(angleOf[slug]);}
  const mean=a=>Math.atan2(a.reduce((s,x)=>s+Math.sin(x),0),a.reduce((s,x)=>s+Math.cos(x),0));
  const ids=Object.keys(byT).sort((p,q)=>mean(byT[p])-mean(byT[q]));
  const gap=2*Math.PI/Math.max(1,ids.length)*0.9; let prev=null; const place={};
  ids.forEach(t=>{let a=mean(byT[t]); if(prev!==null&&a-prev<gap)a=prev+gap; place[t]=a; prev=a;});
  ids.forEach(t=>{const [x,y]=pol(Rt,place[t]);
    const n=E('circle',{cx:x,cy:y,r:3.3,fill:'#e6c374',stroke:'#7a5f28','stroke-width':.8,class:'node','data-th':t});
    tt(n,D.theoryTitles[t]||t);
    n.addEventListener('mouseenter',()=>{if(!pinned)showTheory(t);});
    n.addEventListener('click',e=>{e.stopPropagation();pinned=true;showTheory(t);});
    (reg.theory[t]=reg.theory[t]||[]).push(n);fig.appendChild(n);
    const c=Math.cos(place[t]); const [lx,ly]=pol(Rt+12,place[t]);
    lbl(lx,ly+2,(D.theoryTitles[t]||t).split('(')[0].trim().slice(0,22),8,'#a08a5a',c>=0?'start':'end',
        (place[t]*180/Math.PI)+(c<0?180:0));});
  return place;
}

// ------------------------------------------------------------------ layouts
function renderWheel(){clearFig();
  const forms=D.leaf, n=forms.length, Rin=110, Rout=560;
  const parents=new Set(Object.values(D.formParent));
  // family tint wedges
  const span={}; forms.forEach((f,i)=>{const p=D.formParent[f]; if(p){span[p]=span[p]||[i,i]; span[p][0]=Math.min(span[p][0],i);span[p][1]=Math.max(span[p][1],i);}});
  for(const p in span){const [lo,hi]=span[p];const a0=-Math.PI/2+2*Math.PI*lo/n,a1=-Math.PI/2+2*Math.PI*(hi+1)/n;
    const large=(a1-a0)>Math.PI?1:0;const [x0,y0]=pol(Rout,a0),[x1,y1]=pol(Rout,a1),[xi,yi]=pol(Rin,a1),[x0i,y0i]=pol(Rin,a0);
    fig.appendChild(E('path',{d:`M${x0} ${y0} A${Rout} ${Rout} 0 ${large} 1 ${x1} ${y1} L${xi} ${yi} A${Rin} ${Rin} 0 ${large} 0 ${x0i} ${y0i} Z`,fill:D.famTint[p]||'#c69a4a',opacity:.05}));}
  for(const q of [.3,.55,.8,1])fig.appendChild(E('circle',{cx:CX,cy:CY,r:Rout*q,fill:'none',stroke:'#241f18'}));
  forms.forEach((f,i)=>{const a0=-Math.PI/2+2*Math.PI*i/n, amid=-Math.PI/2+2*Math.PI*(i+.5)/n;
    const [sx,sy]=pol(Rin,a0),[ex,ey]=pol(Rout,a0);
    fig.appendChild(E('line',{x1:sx,y1:sy,x2:ex,y2:ey,stroke:'#241f18'}));
    const rows=D.calcsByForm[f]||[], m=Math.max(1,rows.length);
    rows.forEach((slug,j)=>{const r=Rin+30+(Rout-Rin-70)*((j+.5)/m);const frac=((j%3)-1)*.34;
      const [x,y]=pol(r,amid+(2*Math.PI/n)*.28*frac);calcDot(slug,x,y);});
    const [lx,ly]=pol(Rout-8,amid);const c=Math.cos(amid);
    const tl=lbl(lx,ly,f,10,'#cbbfa4',c>=0?'end':'start',(amid*180/Math.PI)+(c<0?180:0));
    tl.setAttribute('data-form',f);tl.style.pointerEvents='auto';tl.style.cursor='pointer';
    tl.addEventListener('mouseenter',()=>{if(!pinned)showForm(f);});
    tl.addEventListener('click',e=>{e.stopPropagation();pinned=true;showForm(f);});
    (reg.form[f]=reg.form[f]||[]).push(tl);});
  hub(Rin-2,'form wheel',n+' forms');
}

function renderOneBody(){clearFig();
  const forms=D.leaf, n=forms.length, Rin=120, Rout=470, Rt=560;
  for(const q of [.28,.55,.82,1])fig.appendChild(E('circle',{cx:CX,cy:CY,r:Rout*q,fill:'none',stroke:'#221d15'}));
  const angleOf={};
  forms.forEach((f,i)=>{const a0=-Math.PI/2+2*Math.PI*i/n,a1=-Math.PI/2+2*Math.PI*(i+1)/n,amid=(a0+a1)/2;
    const [sx,sy]=pol(Rin,a0),[ex,ey]=pol(Rout,a0);fig.appendChild(E('line',{x1:sx,y1:sy,x2:ex,y2:ey,stroke:'#221d15'}));
    const rows=D.calcsByForm[f]||[],m=Math.max(1,rows.length);
    rows.forEach((slug,j)=>{const r=Rin+(Rout-Rin-30)*((j+.5)/m);const frac=((j%3)-1)*.34;const ang=amid+(a1-a0)*.3*frac;
      angleOf[slug]=ang;});});
  const place=theoryRim(angleOf,Rt);
  // rests_on chords under dots
  for(const slug in angleOf){const c=D.calcs[slug];if(c.thid&&place[c.thid]!==undefined){
    const [x,y]=pol(fromR(slug,forms,Rin,Rout),angleOf[slug]);const [tx,ty]=pol(Rt,place[c.thid]);
    const mx=(x+tx)/2,my=(y+ty)/2,ctx=CX+(mx-CX)*.5,cty=CY+(my-CY)*.5;
    fig.appendChild(E('path',{d:`M${x} ${y} Q${ctx} ${cty} ${tx} ${ty}`,fill:'none',stroke:dcol(c.dom),'stroke-width':.6,opacity:.12}));}}
  // dots
  for(const slug in angleOf){const [x,y]=pol(fromR(slug,forms,Rin,Rout),angleOf[slug]);calcDot(slug,x,y,4.2);}
  hub(Rin-4,'one body',D.counts.calcs+' calcs');
}
function fromR(slug,forms,Rin,Rout){const f=D.calcs[slug].form;const rows=D.calcsByForm[f]||[];const j=rows.indexOf(slug),m=Math.max(1,rows.length);
  return Rin+(Rout-Rin-30)*((j+.5)/m);}

function renderSpiral(){clearFig();
  const rows=Object.keys(D.calcs).sort((p,q)=>{const a=D.calcs[p],b=D.calcs[q];
    return a.dom<b.dom?-1:a.dom>b.dom?1:(leafIdx[a.form]||0)-(leafIdx[b.form]||0);});
  const N=rows.length, R0=42,Rmax=560,turns=5.2,th0=-Math.PI/2,thspan=turns*2*Math.PI,b=Math.log(Rmax/R0)/thspan;
  const pos={},ang={};
  rows.forEach((slug,i)=>{const t=i/Math.max(1,N-1),th=th0+t*thspan,r=R0*Math.exp(b*(th-th0));
    pos[slug]=pol(r,th);ang[slug]=th;});
  // spine
  let sp='';for(let k=0;k<=600;k++){const th=th0+(k/600)*thspan,r=R0*Math.exp(b*(th-th0));const [x,y]=pol(r,th);sp+=(k?' ':'')+x.toFixed(1)+','+y.toFixed(1);}
  fig.appendChild(E('polyline',{points:sp,fill:'none',stroke:'#241f18'}));
  // form threads
  const byForm={};rows.forEach(s=>{(byForm[D.calcs[s].form]=byForm[D.calcs[s].form]||[]).push(s);});
  for(const f in byForm){if(byForm[f].length<2)continue;let pts=byForm[f].map(s=>pos[s].map(v=>v.toFixed(0)).join(',')).join(' ');
    fig.appendChild(E('polyline',{points:pts,fill:'none',stroke:'#c69a4a','stroke-width':.7,opacity:.12,class:'node','data-form':f}));}
  rows.forEach(slug=>{const [x,y]=pos[slug];calcDot(slug,x,y,3.6);});
  hub(30,'spiral',N+' calcs');
}

function renderKernel(){clearFig();
  const ms=D.masters.slice().sort((a,b)=>(leafIdx[a.domform]||99)-(leafIdx[b.domform]||99));
  const nM=ms.length, Rm=250;
  const mang={}; ms.forEach((m,i)=>mang[m.i]=-Math.PI/2+2*Math.PI*i/nM);
  // member dots + angle map for theory rim
  const angleOf={}; const memberpos={};
  ms.forEach((m,i)=>{const a=mang[m.i],k=m.members.length;
    m.members.forEach((slug,j)=>{const frac=(j-(k-1)/2)/Math.max(1,k);const ang=a+frac*(2*Math.PI/nM)*.8;
      const r=360+206*(.15+.7*(j+.5)/Math.max(1,k));memberpos[m.i+'|'+slug]=[pol(r,ang),m.i];angleOf[slug]=angleOf[slug]===undefined?ang:angleOf[slug];});});
  const place=theoryRim(angleOf,680);
  // duality arcs between master forms
  const formMasters={}; ms.forEach(m=>{(formMasters[m.domform]=formMasters[m.domform]||[]).push(m.i);});
  D.dualities.forEach(([fa,fb])=>{(formMasters[fa]||[]).forEach(ia=>(formMasters[fb]||[]).forEach(ib=>{
    const [x0,y0]=pol(Rm,mang[ia]),[x1,y1]=pol(Rm,mang[ib]);
    fig.appendChild(E('path',{d:`M${x0} ${y0} Q${CX} ${CY} ${x1} ${y1}`,fill:'none',stroke:'#c69a4a','stroke-width':.8,opacity:.26}));}));});
  // reach rays + member dots
  for(const key in memberpos){const [[x,y],mi]=memberpos[key];const slug=key.split('|')[1];const [mx,my]=pol(Rm,mang[mi]);
    const ray=E('line',{x1:mx,y1:my,x2:x,y2:y,stroke:dcol(D.calcs[slug].dom),'stroke-width':.7,opacity:.32,class:'node','data-id':slug});
    fig.appendChild(ray);calcDot(slug,x,y,4.4);}
  // master nodes
  ms.forEach(m=>{const [mx,my]=pol(Rm,mang[m.i]);
    const node=E('circle',{cx:mx,cy:my,r:7.5,fill:'#f0d68a',stroke:'#7a5f28','stroke-width':1.3,class:'node mnode','data-mi':m.i});
    tt(node,m.eq);node.style.cursor='pointer';
    node.addEventListener('mouseenter',()=>{if(!pinned)showMaster(m.i);});
    node.addEventListener('click',e=>{e.stopPropagation();pinned=true;showMaster(m.i);});
    (reg.master[m.i]=reg.master[m.i]||[]).push(node);fig.appendChild(node);
    const c=Math.cos(mang[m.i]);const [lx,ly]=pol(Rm-16,mang[m.i]);
    lbl(lx,ly,m.eq.split('->')[0].trim(),9,'#e8dfc9',c>=0?'end':'start',(mang[m.i]*180/Math.PI)+(c<0?180:0));});
  hub(46,'ATLAS','the one kernel');
}

function renderDomains(){clearFig();
  const present=new Set(); D.masters.forEach(m=>m.doms.forEach(d=>present.add(d)));
  const ord=D.domOrder.filter(d=>present.has(d)); const n=ord.length, Rn=520;
  const ang={}; ord.forEach((d,i)=>ang[d]=-Math.PI/2+2*Math.PI*i/n);
  const deg={}; D.masters.forEach(m=>m.doms.forEach(d=>deg[d]=(deg[d]||0)+1)); const maxd=Math.max(...Object.values(deg));
  // family arcs
  const fi={}; ord.forEach((d,i)=>{(fi[D.domFam[d]]=fi[D.domFam[d]]||[]).push(i);});
  for(const fam in fi){const idx=fi[fam];const a0=-Math.PI/2+2*Math.PI*(Math.min(...idx)-.42)/n,a1=-Math.PI/2+2*Math.PI*(Math.max(...idx)+.42)/n;
    const large=(a1-a0)>Math.PI?1:0;const [x0,y0]=pol(Rn+52,a0),[x1,y1]=pol(Rn+52,a1);
    fig.appendChild(E('path',{d:`M${x0} ${y0} A${Rn+52} ${Rn+52} 0 ${large} 1 ${x1} ${y1}`,fill:'none',stroke:D.ftint[fam]||'#c69a4a','stroke-width':2.5,opacity:.5}));
    const amid=(a0+a1)/2,cc=Math.cos(amid),[lx,ly]=pol(Rn+68,amid);
    lbl(lx,ly,fam,12,D.ftint[fam]||'#c69a4a',cc>=0?'start':'end',(amid*180/Math.PI)+(cc<0?180:0));}
  // threads
  D.masters.forEach(m=>{if(m.doms.length<2)return;const g=E('g',{class:'thread node','data-mi':m.i,stroke:m.col});
    for(let a=0;a<m.doms.length-1;a++){const [x0,y0]=pol(Rn,ang[m.doms[a]]),[x1,y1]=pol(Rn,ang[m.doms[a+1]]);
      const mx=(x0+x1)/2,my=(y0+y1)/2,ctx=CX+(mx-CX)*.3,cty=CY+(my-CY)*.3;
      const p=E('path',{d:`M${x0} ${y0} Q${ctx} ${cty} ${x1} ${y1}`,fill:'none','stroke-width':1.5,opacity:.42,'stroke-linecap':'round'});
      g.appendChild(p);}
    g.addEventListener('mouseenter',()=>{if(!pinned)showMaster(m.i);});
    g.addEventListener('click',e=>{e.stopPropagation();pinned=true;showMaster(m.i);});
    (reg.thread[m.i]=reg.thread[m.i]||[]).push(g);fig.appendChild(g);});
  // domain nodes
  ord.forEach(d=>{const [x,y]=pol(Rn,ang[d]);const r=3.5+(deg[d]/maxd)*8.5;
    const node=E('circle',{cx:x,cy:y,r:r,fill:D.ftint[D.domFam[d]]||'#c69a4a',stroke:'#0f0d09','stroke-width':1,class:'node','data-dom':d});
    tt(node,d+' — '+deg[d]+' master equations');node.style.cursor='pointer';
    node.addEventListener('mouseenter',()=>{if(!pinned)showDomain(d);});
    node.addEventListener('click',e=>{e.stopPropagation();pinned=true;showDomain(d);});
    (reg.dom[d]=reg.dom[d]||[]).push(node);fig.appendChild(node);
    const c=Math.cos(ang[d]),[lx,ly]=pol(Rn+14,ang[d]);
    lbl(lx,ly+2,d,10,'#cbbfa4',c>=0?'start':'end',(ang[d]*180/Math.PI)+(c<0?180:0));});
  hub(46,'ATLAS',n+' domains');
}

function hub(r,a,b){fig.appendChild(E('circle',{cx:CX,cy:CY,r:r<40?46:r,fill:'#0f0d09',stroke:'#3a3427','stroke-width':1.4}));
  const t1=E('text',{x:CX,y:CY-2,'font-size':a==='ATLAS'?15:12,fill:'#c69a4a','text-anchor':'middle',class:'lbl'});t1.textContent=a;fig.appendChild(t1);
  const t2=E('text',{x:CX,y:CY+14,'font-size':9,fill:'#8a8378','text-anchor':'middle',class:'lbl'});t2.textContent=b;fig.appendChild(t2);}

function renderBridges(){clearFig();
  const forms=D.formList, n=forms.length, Rn=460;
  const ang={}; forms.forEach((f,i)=>ang[f]=-Math.PI/2+2*Math.PI*i/n);
  const maxdom=Math.max(1,...Object.values(D.formDom));
  fig.appendChild(E('circle',{cx:CX,cy:CY,r:Rn,fill:'none',stroke:'#221d15'}));
  D.dualities.forEach((du,i)=>{const a=du[0],b=du[1];if(ang[a]===undefined||ang[b]===undefined)return;
    const [x0,y0]=pol(Rn,ang[a]),[x1,y1]=pol(Rn,ang[b]);const mx=(x0+x1)/2,my=(y0+y1)/2,ctx=CX+(mx-CX)*.25,cty=CY+(my-CY)*.25;
    const p=E('path',{d:`M${x0} ${y0} Q${ctx} ${cty} ${x1} ${y1}`,fill:'none',stroke:'#c69a4a','stroke-width':1.6,opacity:.5,class:'node','data-du':i});
    tt(p,a+' ↔ '+b+' : '+du[2]);p.style.cursor='pointer';
    p.addEventListener('mouseenter',()=>{if(!pinned)showDuality(i);});
    p.addEventListener('click',e=>{e.stopPropagation();pinned=true;showDuality(i);});
    (reg.du[i]=reg.du[i]||[]).push(p);fig.appendChild(p);});
  forms.forEach(f=>{const [x,y]=pol(Rn,ang[f]);const r=3.2+(D.formDom[f]/maxdom)*7.5;
    const root=formRoot(f);const col=D.famTint[root]||(D.formParent[f]?'#9a8f76':'#c6a86f');
    const node=E('circle',{cx:x,cy:y,r:r,fill:col,stroke:'#0f0d09','stroke-width':1,class:'node','data-form':f});
    tt(node,f+' — spans '+D.formDom[f]+' domains');node.style.cursor='pointer';
    node.addEventListener('mouseenter',()=>{if(!pinned)showForm(f);});
    node.addEventListener('click',e=>{e.stopPropagation();pinned=true;showForm(f);});
    (reg.form[f]=reg.form[f]||[]).push(node);fig.appendChild(node);
    const c=Math.cos(ang[f]),[lx,ly]=pol(Rn+12,ang[f]);
    lbl(lx,ly+2,f,9,'#cbbfa4',c>=0?'start':'end',(ang[f]*180/Math.PI)+(c<0?180:0));});
  hub(46,'bridges',D.counts.dualities+' dualities');
}
const RENDER={kernel:renderKernel,wheel:renderWheel,onebody:renderOneBody,spiral:renderSpiral,domains:renderDomains,bridges:renderBridges};
function render(){RENDER[layout]();applyHi();}

// ---------------------------------------------------------------- selection
function hiSets(){
  if(!sel)return null;
  const calcs=new Set(),doms=new Set(),mis=new Set(),forms=new Set(),ths=new Set(),dualf=new Set(),dus=new Set();
  const addCalc=s=>{const c=D.calcs[s];if(!c)return;calcs.add(s);doms.add(c.dom);forms.add(c.form);if(c.thid)ths.add(c.thid);c.m.forEach(m=>mis.add(m));};
  if(sel.type==='master'){const m=D.masters[sel.id];mis.add(sel.id);m.doms.forEach(d=>doms.add(d));m.members.forEach(s=>{calcs.add(s);forms.add(D.calcs[s].form);});}
  else if(sel.type==='domain'){doms.add(sel.id);D.masters.forEach(m=>{if(m.doms.includes(sel.id))mis.add(m.i);});for(const s in D.calcs)if(D.calcs[s].dom===sel.id)calcs.add(s);}
  else if(sel.type==='calc'){addCalc(sel.id);}
  else if(sel.type==='form'){
    for(const g in D.calcsByForm){let x=g;while(x!==undefined){if(x===sel.id){forms.add(g);D.calcsByForm[g].forEach(s=>calcs.add(s));break;}x=D.formParent[x];}}
    forms.add(sel.id);
    D.dualities.forEach((d,i)=>{if(d[0]===sel.id){dualf.add(d[1]);dus.add(i);}else if(d[1]===sel.id){dualf.add(d[0]);dus.add(i);}});}
  else if(sel.type==='theory'){ths.add(sel.id);for(const s in D.calcs)if(D.calcs[s].thid===sel.id)calcs.add(s);}
  else if(sel.type==='duality'){const d=D.dualities[sel.id];dus.add(sel.id);forms.add(d[0]);forms.add(d[1]);
    (D.calcsByForm[d[0]]||[]).forEach(s=>calcs.add(s));(D.calcsByForm[d[1]]||[]).forEach(s=>calcs.add(s));}
  return {calcs,doms,mis,forms,ths,dualf,dus};
}
function applyHi(){
  const H=hiSets();
  const all=fig.querySelectorAll('.node');
  all.forEach(n=>{n.classList.remove('hi','dim');});
  document.querySelectorAll('.chip').forEach(c=>c.classList.toggle('on',!!H&&sel.type==='master'&&+c.dataset.mi===sel.id));
  if(!H)return;
  all.forEach(n=>{
    let on=false;
    if(n.dataset.id!==undefined)on=H.calcs.has(n.dataset.id);
    else if(n.dataset.dom!==undefined)on=H.doms.has(n.dataset.dom);
    else if(n.dataset.mi!==undefined)on=H.mis.has(+n.dataset.mi);
    else if(n.dataset.form!==undefined)on=H.forms.has(n.dataset.form)||H.dualf.has(n.dataset.form);
    else if(n.dataset.th!==undefined)on=H.ths.has(n.dataset.th);
    else if(n.dataset.du!==undefined)on=H.dus.has(+n.dataset.du);
    else return; // structural, leave as is
    n.classList.add(on?'hi':'dim');
  });
}

// ---------------------------------------------------------------- panels
function wireMasterRows(){detail.querySelectorAll('.mlist .row[data-mi]').forEach(r=>r.onclick=()=>{pinned=true;showMaster(+r.dataset.mi);});}
function wireLinks(){
  detail.querySelectorAll('.domlink[data-dom]').forEach(el=>el.onclick=()=>{pinned=true;showDomain(el.dataset.dom);});
  detail.querySelectorAll('.formlink[data-form]').forEach(el=>el.onclick=()=>{pinned=true;showForm(el.dataset.form);});
  detail.querySelectorAll('.thlink[data-th]').forEach(el=>el.onclick=()=>{pinned=true;showTheory(el.dataset.th);});
  detail.querySelectorAll('td.d[data-dom]').forEach(el=>el.onclick=()=>{pinned=true;showDomain(el.dataset.dom);});
  detail.querySelectorAll('.calc[data-id]').forEach(el=>el.onclick=()=>{pinned=true;showCalc(el.dataset.id);});
}
function setCount(t){document.getElementById('hint').textContent=t;}

function showMaster(mi){sel={type:'master',id:mi};const m=D.masters[mi];
  const rows=m.subs.map(([d,s])=>`<tr><td class=d data-dom="${esc(d)}">${esc(d)}</td><td class=s>${esc(s)}</td></tr>`).join('');
  detail.innerHTML=`<div class=eq>${esc(m.eq)}</div><div class=gist>${esc(m.gist)}</div><table>${rows}</table>`;
  wireLinks();applyHi();setCount('master equation — '+m.doms.length+' domains');}
function showDomain(dom){sel={type:'domain',id:dom};
  const ms=D.masters.filter(m=>m.doms.includes(dom));
  const calcs=Object.keys(D.calcs).filter(s=>D.calcs[s].dom===dom);
  const mrows=ms.map(m=>`<div class=row data-mi="${m.i}"><span class=sw style="background:${m.col}"></span><code style="color:${m.col}">${esc(m.eq.split('->')[0].trim())}</code></div>`).join('');
  const crows=calcs.map(s=>`<div class=calc data-id="${s}"><b>${esc(D.calcs[s].t)}</b> <code>${esc(D.calcs[s].f)}</code></div>`).join('');
  detail.innerHTML=`<div class=eq style="font-family:Georgia,serif;color:var(--gold)">${esc(dom)}</div>`+
    `<div class=gist>${ms.length} master equation${ms.length==1?'':'s'} run through this field; ${calcs.length} calculation${calcs.length==1?'':'s'} live here.</div>`+
    `<div class=mlist>${mrows||'<div class=lead>no master equation through this field</div>'}</div>`+
    `<h2>Calculations here</h2>${crows||'<div class=lead>none</div>'}`;
  wireLinks();applyHi();setCount(dom);}
function showForm(f){sel={type:'form',id:f};const par=D.formParent[f];
  let calcs=[];for(const g in D.calcsByForm){let x=g;while(x!==undefined){if(x===f){calcs=calcs.concat(D.calcsByForm[g]);break;}x=D.formParent[x];}}
  const duals=[];D.dualities.forEach((d,i)=>{if(d[0]===f||d[1]===f)duals.push([d[0]===f?d[1]:d[0],d[2],i]);});
  const durows=duals.map(([o,k,i])=>`<div class=row data-du="${i}"><code style="color:var(--gold)">↔ ${esc(o)}</code> <span style="color:#5f584a">${esc(k)}</span></div>`).join('');
  const crows=calcs.map(s=>`<div class=calc data-id="${s}"><b>${esc(D.calcs[s].t)}</b> <code>${esc(D.calcs[s].f)}</code> <span style="color:#5f584a">${esc(D.calcs[s].dom)}</span></div>`).join('');
  detail.innerHTML=`<div class=eq style="color:var(--gold)">${esc(f)}</div><div class=gist>${esc(D.formEq[f]||'')}`+
    (par?` · a finer case of <span class=formlink data-form="${esc(par)}">${esc(par)}</span>`:'')+`</div>`+
    (duals.length?`<h2>Dualities <span style="color:#5f584a">(${duals.length})</span></h2><div class=mlist>${durows}</div>`:'')+
    `<h2>Calculations of this form <span style="color:#5f584a">(${calcs.length})</span></h2>${crows}`;
  wireLinks();detail.querySelectorAll('.row[data-du]').forEach(r=>r.onclick=()=>{pinned=true;showDuality(+r.dataset.du);});
  applyHi();setCount('form: '+f);}
function showDuality(idx){sel={type:'duality',id:idx};const d=D.dualities[idx];
  detail.innerHTML=`<div class=eq><span class=formlink data-form="${esc(d[0])}">${esc(d[0])}</span> ↔ <span class=formlink data-form="${esc(d[1])}">${esc(d[1])}</span></div>`+
    `<div class=gist>${esc(d[2])}</div><div class=lead>${esc(d[3])}</div>`;
  wireLinks();applyHi();setCount('duality');}
function showTheory(th){sel={type:'theory',id:th};const calcs=Object.keys(D.calcs).filter(s=>D.calcs[s].thid===th);
  const isos=[];D.theoryIso.forEach(e=>{if(e[0]===th||e[1]===th)isos.push([e[0]===th?e[1]:e[0],e[2]]);});
  const isorows=isos.map(([o,ev])=>`<div class=row data-th="${esc(o)}"><span class=thlink data-th="${esc(o)}">↔ ${esc(D.theoryTitles[o]||o)}</span><div style="color:#6f6555;font-size:.76rem;margin-left:.2rem">${esc(ev)}</div></div>`).join('');
  const crows=calcs.map(s=>`<div class=calc data-id="${s}"><b>${esc(D.calcs[s].t)}</b> <code>${esc(D.calcs[s].f)}</code> <span style="color:#5f584a">${esc(D.calcs[s].dom)}</span></div>`).join('');
  detail.innerHTML=`<div class=eq style="font-family:Georgia,serif;color:var(--gold2)">${esc(D.theoryTitles[th]||th)}</div>`+
    `<div class=gist>A theory on THE FLOOR.</div>`+
    (isos.length?`<h2>Same form as <span style="color:#5f584a">(${isos.length})</span></h2><div class=mlist>${isorows}</div>`:'')+
    `<h2>Calculations that rest here <span style="color:#5f584a">(${calcs.length})</span></h2>${crows||'<div class=lead>none</div>'}`;
  wireLinks();detail.querySelectorAll('.row[data-th]').forEach(r=>r.onclick=()=>{pinned=true;showTheory(r.dataset.th);});
  applyHi();setCount('theory');}
function showCalc(slug){sel={type:'calc',id:slug};const c=D.calcs[slug];
  const mchips=c.m.map(mi=>{const m=D.masters[mi];return `<div class=row data-mi="${mi}"><span class=sw style="background:${m.col}"></span><code style="color:${m.col}">${esc(m.eq.split('->')[0].trim())}</code></div>`;}).join('');
  detail.innerHTML=`<div class=eq>${esc(c.f)}</div>`+
    `<div class=gist>${esc(c.t)} — <span class=domlink data-dom="${esc(c.dom)}">${esc(c.dom)}</span> · form <span class=formlink data-form="${esc(c.form)}">${esc(c.form)}</span></div>`+
    (c.thid?`<div class=lead>rests on <span class=thlink data-th="${esc(c.thid)}">${esc(c.th)}</span></div>`:'<div class=lead>an honest theory-gap</div>')+
    (c.m.length?`<h2>Master equation${c.m.length>1?'s':''}</h2><div class=mlist>${mchips}</div>`:'<div class=lead style="margin-top:.4rem">a domain-specific calculation</div>');
  wireLinks();applyHi();setCount(c.t);}

function reset(){sel=null;pinned=false;detail.innerHTML='<div class=lead>Atlas — '+D.counts.masters+' master equations, '+D.counts.calcs+' calculations, '+D.counts.theories+' theories. Pick a layout above; select a master, a field, a form, a theory, or any calculation. Your selection is kept across layouts.</div>';applyHi();setCount('Hover to preview, click to select. Selection is kept across layouts.');}

// search
document.getElementById('search').addEventListener('input',e=>{const q=e.target.value.toLowerCase().trim();
  if(!q){if(!sel)reset();return;}
  const hits=[];
  for(const s in D.calcs){if(D.calcs[s].t.toLowerCase().includes(q)||s.includes(q))hits.push(['calc',s,D.calcs[s].t]);}
  D.domOrder.forEach(d=>{if(d.includes(q))hits.push(['dom',d,d]);});
  for(const t in D.theoryTitles){if((D.theoryTitles[t]||'').toLowerCase().includes(q))hits.push(['th',t,D.theoryTitles[t]]);}
  const rows=hits.slice(0,40).map(([k,id,label])=>`<div class=calc data-k="${k}" data-v="${esc(id)}">${esc(label)} <span style="color:#5f584a">${k}</span></div>`).join('');
  detail.innerHTML=`<div class=lead>${hits.length} match${hits.length==1?'':'es'}</div>`+rows;
  detail.querySelectorAll('.calc[data-k]').forEach(el=>el.onclick=()=>{pinned=true;const k=el.dataset.k,v=el.dataset.v;
    if(k==='calc')showCalc(v);else if(k==='dom')showDomain(v);else showTheory(v);});});

// tabs
document.querySelectorAll('.tab').forEach(t=>t.addEventListener('click',()=>{
  layout=t.dataset.l;document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('on',x===t));render();}));
document.querySelectorAll('.chip').forEach(c=>{
  c.addEventListener('mouseenter',()=>{if(!pinned)showMaster(+c.dataset.mi);});
  c.addEventListener('click',()=>{pinned=true;showMaster(+c.dataset.mi);});});
document.getElementById('reset').addEventListener('click',reset);
fig.addEventListener('click',e=>{if(e.target.id==='bg')reset();});

// init
document.querySelector('.tab[data-l=kernel]').classList.add('on');
render();reset();
</script>
</body></html>"""


def main():
    out = os.path.join(ROOT, "site", "explore.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(build())
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
