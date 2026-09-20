#!/usr/bin/env python3
"""THE TORUS — the Atlas on its true shape.

Matt, 2026-09-19: "Should it be tori shaped?" The measurement says yes. The Atlas is a
(domain x form) matrix — two independent cyclic axes: every one of the 39 forms threads
ACROSS domains (the bridges), and most domains thread across forms. Two cyclic axes wrapped
into circles IS a torus. So here the calculations live on a torus surface:

  * u (around the hole) = FORM. A single form is one meridian ring around the tube — the
    same computation worn by every domain that carries it. THAT ring is a bridge.
  * v (around the tube) = DOMAIN. A single domain is one longitude ring — its span of forms.

A torus has no center and no edge: after the reasoning-domain island was attached, the Atlas
is one connected body, so its honest shape has no privileged core and no rim — unlike the
radial/spiral views, which draw a fake center. It is also the canonical boundary-less
interconnect fabric, which is why a hardware fabric-designer's eye lands on it.

Interactive (drag to turn, or let it drift); stdlib only; embeds its data; graceful without JS.

    python tools/torus_map.py   # writes site/torus.html
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
from seed_calculations import CALCS, leaf_forms_ordered  # noqa: E402
from seed_bridges import MASTER_EQUATIONS  # noqa: E402

# Domain families (same grouping the interactive Atlas uses) -> one color each.
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
               "construction", "manufacturing", "rhetoric", "history_chronology", "calendar_time",
               "philosophy"]),
]
FAM_COLOR = {"physical": "#c69a4a", "chemical": "#6fb0a0", "life": "#7fb069",
             "earth & sky": "#6f9ec6", "formal": "#9b7fc6", "human": "#c67f6f", "other": "#8a8172"}
FAM_ORDER = ["physical", "chemical", "life", "earth & sky", "formal", "human", "other"]


def _family_of():
    fam = {}
    for name, doms in FAMILY:
        for d in doms:
            fam[d] = name
    return fam


def build():
    fam_of = _family_of()
    rows = list(CALCS)

    # AXIS 2 — forms around the hole (family-contiguous preorder, so neighbors are related)
    forms = leaf_forms_ordered()
    forms = [f for f in forms if any(r[4] == f for r in rows)]  # only forms actually carried
    n_forms = len(forms)
    u_of = {f: (2 * math.pi * i / n_forms) for i, f in enumerate(forms)}

    # AXIS 1 — domains around the tube, ordered by family so neighbors are related
    domains = sorted({r[3] for r in rows})
    domains.sort(key=lambda d: (FAM_ORDER.index(fam_of.get(d, "other")), d))
    n_dom = len(domains)
    v_of = {d: (2 * math.pi * j / n_dom) for j, d in enumerate(domains)}

    # master-equation membership (by calc slug) -> mark those calcs, highlight their loops
    master_of = {}
    for me in MASTER_EQUATIONS:
        for (_dom, slug, _sub) in me["rows"]:
            master_of[slug] = me["eq"]

    # points: one per calculation. Multiple calcs can share a (domain,form) cell — fan them a
    # touch along v so each is visible, deterministically (no overlap hiding a real node).
    cell_seen = defaultdict(int)
    points = []
    for slug, title, formula, domain, form, note in rows:
        if form not in u_of or domain not in v_of:
            continue
        k = cell_seen[(domain, form)]
        cell_seen[(domain, form)] += 1
        jitter = 0.0 if k == 0 else ((-1) ** k) * math.ceil(k / 2) * 0.055
        fam = fam_of.get(domain, "other")
        points.append({
            "u": round(u_of[form], 5), "v": round(v_of[domain] + jitter, 5),
            "t": title, "d": domain, "f": form, "eq": formula,
            "c": FAM_COLOR[fam], "fam": fam,
            "m": master_of.get(slug, ""),
        })

    # form loops (meridians = the bridges): occupied domains for a form, in v-order, closed
    form_dom = defaultdict(list)
    for slug, title, formula, domain, form, note in rows:
        if form in u_of and domain in v_of and domain not in [x[0] for x in form_dom[form]]:
            form_dom[form].append((domain, v_of[domain]))
    form_loops = []
    for form, dv in form_dom.items():
        if len(dv) < 2:
            continue
        dv = sorted(dv, key=lambda x: x[1])
        form_loops.append({"u": round(u_of[form], 5),
                           "vs": [round(v, 5) for _d, v in dv],
                           "n": len(dv), "f": form})

    # domain loops (longitudes): the forms a domain carries, in u-order
    dom_form = defaultdict(list)
    for slug, title, formula, domain, form, note in rows:
        if form in u_of and domain in v_of and form not in [x[0] for x in dom_form[domain]]:
            dom_form[domain].append((form, u_of[form]))
    domain_loops = []
    for domain, fu in dom_form.items():
        if len(fu) < 2:
            continue
        fu = sorted(fu, key=lambda x: x[1])
        domain_loops.append({"v": round(v_of[domain], 5),
                             "us": [round(u, 5) for _f, u in fu],
                             "d": domain})

    # master loops: for each master equation, its member calcs' (u,v) — a geodesic across domains
    master_loops = []
    for me in MASTER_EQUATIONS:
        pts = []
        for (dom, slug, _sub) in me["rows"]:
            # a calc's form is looked up from CALCS
            form = next((r[4] for r in rows if r[0] == slug), None)
            if form and form in u_of and dom in v_of:
                pts.append([round(u_of[form], 5), round(v_of[dom], 5)])
        if len(pts) >= 2:
            master_loops.append({"eq": me["eq"], "pts": pts})

    data = {
        "points": points, "form_loops": form_loops, "domain_loops": domain_loops,
        "master_loops": master_loops, "n_forms": n_forms, "n_dom": n_dom,
        "fam_color": FAM_COLOR, "fam_order": FAM_ORDER,
    }
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    legend = "".join(
        f'<span style="display:inline-block;margin:0 .7rem .35rem 0;white-space:nowrap">'
        f'<i style="display:inline-block;width:10px;height:10px;background:{FAM_COLOR[f]};'
        f'border-radius:2px;vertical-align:middle;margin-right:5px"></i>{f}</span>'
        for f in FAM_ORDER if f != "other")

    return _PAGE.replace("__BLOB__", blob).replace("__LEGEND__", legend) \
        .replace("__NDOM__", str(n_dom)).replace("__NFORM__", str(n_forms)) \
        .replace("__NPTS__", str(len(points))).replace("__NBRIDGE__", str(len(form_loops)))


_PAGE = r"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<script src="/shell.js"></script>
<title>The Torus</title>
<style>
  :root{color-scheme:dark}
  *{box-sizing:border-box}
  body{margin:0;background:#12100c;color:#e8dfc9;font-family:Georgia,'Iowan Old Style',serif}
  .wrap{max-width:1200px;margin:0 auto;padding:1.5rem 1rem 3rem}
  a.home{color:#8a8172;font:400 .8rem system-ui,sans-serif;text-decoration:none}
  a.home:hover{color:#c69a4a}
  h1{color:#c69a4a;font-weight:400;font-size:1.8rem;margin:.35rem 0 .2rem}
  p.lede{color:#a99c82;max-width:60rem;line-height:1.6;font-size:1rem}
  p.lede b{color:#cbbfa4;font-weight:400}
  .stage{position:relative;margin:1rem 0 0;border:1px solid #241f18;border-radius:12px;
    background:radial-gradient(120% 120% at 50% 35%,#151209 0%,#100e0a 70%,#0c0a07 100%);overflow:hidden;
    aspect-ratio:16/11;touch-action:none;cursor:grab}
  .stage.drag{cursor:grabbing}
  canvas{display:block;width:100%;height:100%}
  .tip{position:absolute;pointer-events:none;opacity:0;transition:opacity .1s;max-width:19rem;
    background:#1c1811;border:1px solid #3a3427;border-radius:8px;padding:.5rem .65rem;
    font:400 .78rem/1.45 system-ui,sans-serif;color:#e8dfc9;box-shadow:0 8px 30px -12px #000;z-index:5}
  .tip b{color:#e6c374;font-weight:600} .tip .dim{color:#a99c82}
  .tip .eq{font-family:ui-monospace,'Cascadia Code',Menlo,monospace;font-size:.72rem;color:#cbbfa4;
    display:block;margin-top:.25rem}
  .controls{display:flex;flex-wrap:wrap;gap:.5rem 1.1rem;align-items:center;margin:.85rem 0 0;
    font:400 .82rem system-ui,sans-serif;color:#a99c82}
  .controls label{display:inline-flex;align-items:center;gap:.35rem;cursor:pointer;user-select:none}
  .controls input{accent-color:#c69a4a}
  .controls .btn{background:#1c1811;border:1px solid #3a3427;color:#cbbfa4;border-radius:6px;
    padding:.28rem .6rem;cursor:pointer;font:inherit}
  .controls .btn:hover{border-color:#c69a4a;color:#e6c374}
  .legend{font:400 .8rem system-ui,sans-serif;color:#a99c82;margin:.9rem 0 0;line-height:1.9}
  .foot{color:#7d745f;font-size:.8rem;margin-top:1.1rem;max-width:60rem;line-height:1.55}
  noscript .ns{display:block;margin:1rem 0;padding:1rem;border:1px solid #3a3427;border-radius:10px;color:#cbbfa4}
</style></head>
<body><div class=wrap>

<h1>The Torus</h1>
<p class=lede>The Atlas is a <b>(domain &times; form) matrix</b> &mdash; two cyclic axes, so its true shape is a
<b>torus</b>. Around the hole runs the <b>form</b> axis: one form is a ring around the tube, the same
computation worn by every field that carries it &mdash; <b>that ring is a bridge</b>. Around the tube runs
the <b>domain</b> axis: one domain is a ring the other way, its span of forms. A torus has <b>no center and
no edge</b> &mdash; which is the honest shape now that the map is one connected body, nothing central and
nothing peripheral. <b>Drag to turn it</b> (or let it drift). __NPTS__ calculations &middot; __NDOM__ domains
&middot; __NFORM__ forms &middot; __NBRIDGE__ form-bridges.</p>

<div class="stage" id="stage">
  <canvas id="cv" aria-label="An interactive torus: calculations placed by form angle and domain angle"></canvas>
  <div class="tip" id="tip"></div>
</div>
<noscript><div class="ns">This view turns the Atlas in your browser and needs JavaScript. The same body is
laid out flat in <a href="/explore.html" style="color:#c69a4a">the interactive Atlas</a> and
<a href="/spiral.html" style="color:#c69a4a">the spiral</a>.</div></noscript>

<div class="controls">
  <label><input type="checkbox" id="cForm" checked> form&nbsp;rings <span style="color:#7d745f">(bridges)</span></label>
  <label><input type="checkbox" id="cDom"> domain&nbsp;rings</label>
  <label><input type="checkbox" id="cMaster"> master&nbsp;equations</label>
  <label><input type="checkbox" id="cSpin" checked> auto-turn</label>
  <button class="btn" id="reset" type="button">reset view</button>
</div>
<div class="legend">__LEGEND__</div>
<p class="foot">Found and mapped, never generated. The shape is not imposed: forms genuinely wrap across
domains and domains across forms &mdash; two circles, and two circles make a torus. Selecting a point shows
the one calculation living at that (form, domain) cell.</p>

<script id="data" type="application/json">__BLOB__</script>
<script>
(function(){
  var D = JSON.parse(document.getElementById('data').textContent);
  var cv = document.getElementById('cv'), ctx = cv.getContext('2d');
  var stage = document.getElementById('stage'), tip = document.getElementById('tip');
  var R = 1.0, r = 0.42;                 // torus radii (major, minor)
  var spin = 0.6, tilt = 1.02;           // current rotation (radians)
  var autoSpin = true, dragging = false, lastX = 0, lastY = 0, movedWhileDown = false;
  var DPR = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
  var W = 0, H = 0, cx = 0, cy = 0, scale = 1;
  var opt = {form:true, dom:false, master:false};

  function torus(u, v){                   // (u,v) -> 3D on the surface
    var cw = R + r*Math.cos(v);
    return [cw*Math.cos(u), cw*Math.sin(u), r*Math.sin(v)];
  }
  function rot(p){                        // spin about z, then tilt about x
    var cs=Math.cos(spin), sn=Math.sin(spin);
    var x=p[0]*cs - p[1]*sn, y=p[0]*sn + p[1]*cs, z=p[2];
    var ct=Math.cos(tilt), st=Math.sin(tilt);
    var y2=y*ct - z*st, z2=y*st + z*ct;
    return [x, y2, z2];
  }
  function screen(P){ return [cx + P[0]*scale, cy - P[1]*scale]; }

  // depth -> shade a base color toward the background (far = dim), near = bright
  function shade(hex, depth){
    var t = (depth + 1.6)/3.2;            // depth in ~[-1.4,1.4] -> [~0.06,~1]
    t = Math.max(0.10, Math.min(1, t));
    var n = parseInt(hex.slice(1),16), rr=(n>>16)&255, gg=(n>>8)&255, bb=n&255;
    var bg=18;                            // #12100c-ish
    rr=Math.round(bg+(rr-bg)*t); gg=Math.round(bg+(gg-bg)*t); bb=Math.round(bg+(bb-bg)*t);
    return 'rgb('+rr+','+gg+','+bb+')';
  }

  function resize(){
    var w = stage.clientWidth, h = stage.clientHeight;
    W=w; H=h; cx=w/2; cy=h/2; scale=Math.min(w,h)*0.31;
    cv.width=w*DPR; cv.height=h*DPR; cv.style.width=w+'px'; cv.style.height=h+'px';
    ctx.setTransform(DPR,0,0,DPR,0,0);
  }

  var screenPts = [];                     // cached for hover hit-testing
  function draw(){
    ctx.clearRect(0,0,W,H);
    // form rings (meridians = bridges): each form's occupied domains, closed loop
    if(opt.form){
      for(var i=0;i<D.form_loops.length;i++){
        var fl=D.form_loops[i], vs=fl.vs, bright=Math.min(1,(fl.n-1)/12);
        ctx.beginPath();
        for(var j=0;j<=vs.length;j++){
          var v=vs[j%vs.length], P=screen(rot(torus(fl.u, v)));
          if(j===0) ctx.moveTo(P[0],P[1]); else ctx.lineTo(P[0],P[1]);
        }
        ctx.strokeStyle='rgba(198,154,74,'+(0.06+0.16*bright)+')';
        ctx.lineWidth=0.6+bright*1.1; ctx.stroke();
      }
    }
    // domain rings (longitudes)
    if(opt.dom){
      for(var i=0;i<D.domain_loops.length;i++){
        var dl=D.domain_loops[i], us=dl.us;
        ctx.beginPath();
        for(var j=0;j<=us.length;j++){
          var u=us[j%us.length], P=screen(rot(torus(u, dl.v)));
          if(j===0) ctx.moveTo(P[0],P[1]); else ctx.lineTo(P[0],P[1]);
        }
        ctx.strokeStyle='rgba(111,158,198,0.12)'; ctx.lineWidth=0.6; ctx.stroke();
      }
    }
    // master-equation geodesics
    if(opt.master){
      for(var i=0;i<D.master_loops.length;i++){
        var ml=D.master_loops[i].pts;
        ctx.beginPath();
        for(var j=0;j<ml.length;j++){
          var P=screen(rot(torus(ml[j][0], ml[j][1])));
          if(j===0) ctx.moveTo(P[0],P[1]); else ctx.lineTo(P[0],P[1]);
        }
        ctx.strokeStyle='rgba(230,195,116,0.55)'; ctx.lineWidth=1.4;
        ctx.lineJoin='round'; ctx.stroke();
      }
    }
    // points, depth-sorted back -> front
    screenPts.length=0;
    var pts=D.points, order=[];
    for(var i=0;i<pts.length;i++){
      var P3=rot(torus(pts[i].u, pts[i].v));
      order.push([P3[2], i, screen(P3)]);
    }
    order.sort(function(a,b){return a[0]-b[0];});
    for(var k=0;k<order.length;k++){
      var depth=order[k][0], idx=order[k][1], S=order[k][2], pt=pts[idx];
      var near=(depth+1.4)/2.8; near=Math.max(0.12,Math.min(1,near));
      var rad=2.0+near*3.2 + (pt.m?0.8:0);
      ctx.beginPath(); ctx.arc(S[0],S[1],rad,0,6.2832);
      ctx.fillStyle=shade(pt.c, depth); ctx.fill();
      if(pt.m){ ctx.lineWidth=0.8; ctx.strokeStyle='rgba(230,195,116,'+(0.35*near)+')'; ctx.stroke(); }
      screenPts.push([S[0],S[1],rad+3,idx,depth]);
    }
  }

  var raf=null;
  function frame(){
    if(autoSpin && !dragging){ spin += 0.0032; }
    draw();
    raf=requestAnimationFrame(frame);
  }

  // hover -> nearest front-most point
  function onMove(ev){
    var rect=cv.getBoundingClientRect(), mx=ev.clientX-rect.left, my=ev.clientY-rect.top;
    var best=null, bestd=1e9;
    for(var i=0;i<screenPts.length;i++){
      var s=screenPts[i], dx=mx-s[0], dy=my-s[1], d=dx*dx+dy*dy;
      if(d < s[2]*s[2] && (d < bestd || s[4] > (best?best[4]:-9))){ best=s; bestd=d; }
    }
    if(best){
      var p=D.points[best[3]];
      tip.innerHTML='<b>'+esc(p.t)+'</b><span class="dim"> &mdash; '+esc(p.d)+' &middot; '+esc(p.f)+'</span>'+
        '<span class="eq">'+esc(p.eq)+'</span>'+(p.m?'<span class="dim" style="display:block;margin-top:.2rem">on the master equation '+esc(p.m)+'</span>':'');
      var tx=Math.min(mx+14, W-tip.offsetWidth-8), ty=Math.min(my+14, H-tip.offsetHeight-8);
      tip.style.left=Math.max(6,tx)+'px'; tip.style.top=Math.max(6,ty)+'px'; tip.style.opacity=1;
    } else { tip.style.opacity=0; }
  }
  function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

  // drag to rotate
  function down(ev){ dragging=true; movedWhileDown=false; stage.classList.add('drag');
    var t=ev.touches?ev.touches[0]:ev; lastX=t.clientX; lastY=t.clientY; }
  function move(ev){
    if(dragging){
      var t=ev.touches?ev.touches[0]:ev, dx=t.clientX-lastX, dy=t.clientY-lastY;
      if(Math.abs(dx)+Math.abs(dy)>2) movedWhileDown=true;
      spin += dx*0.008; tilt += dy*0.008;
      tilt=Math.max(-1.5,Math.min(1.5,tilt));
      lastX=t.clientX; lastY=t.clientY; tip.style.opacity=0;
      if(ev.touches) ev.preventDefault();
    } else if(!('ontouchstart' in window)) { onMove(ev); }
  }
  function up(){ dragging=false; stage.classList.remove('drag'); }

  stage.addEventListener('mousedown',down); window.addEventListener('mousemove',move);
  window.addEventListener('mouseup',up); cv.addEventListener('mousemove',onMove);
  cv.addEventListener('mouseleave',function(){tip.style.opacity=0;});
  stage.addEventListener('touchstart',down,{passive:true});
  stage.addEventListener('touchmove',move,{passive:false});
  stage.addEventListener('touchend',up);

  function bind(id,key){ var el=document.getElementById(id);
    el.addEventListener('change',function(){ if(key==='spin'){autoSpin=el.checked;} else {opt[key]=el.checked;} }); }
  bind('cForm','form'); bind('cDom','dom'); bind('cMaster','master');
  document.getElementById('cSpin').addEventListener('change',function(e){autoSpin=e.target.checked;});
  document.getElementById('reset').addEventListener('click',function(){spin=0.6;tilt=1.02;});

  window.addEventListener('resize',resize);
  resize(); frame();
})();
</script>
</div></body></html>"""


def main():
    out = os.path.join(ROOT, "site", "torus.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(build())
    print(f"wrote {out}  ({len(CALCS)} calculations on the torus)")


if __name__ == "__main__":
    main()
