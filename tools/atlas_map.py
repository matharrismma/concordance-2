#!/usr/bin/env python3
"""ATLAS — the whole body in one frame.

Matt, 2026-09-14: "What has Atlas become? Draw it." The four layers as one image:
the KERNEL (the master equations) at the heart; each master
reaches OUTWARD through its CALCULATIONS (the same formula in many domains, colored
by domain) to the THEORIES on the rim (THE FLOOR); and the master forms are woven to
each other by the DUALITIES. One equation, many domains, bounded whole.

Stdlib only; inline SVG; renders with scripting off.

    python tools/atlas_map.py   # writes site/atlas.html
"""
import math
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass
from seed_calculations import CALCS, CALC_THEORY, FORMS, leaf_forms_ordered  # noqa: E402
from seed_bridges import MASTER_EQUATIONS, FORM_DUALITIES, _load_theory  # noqa: E402

PALETTE = ["#c69a4a", "#6f9ec6", "#9b7fc6", "#7fb069", "#5fa8a0", "#c67f6f", "#c6a86f",
           "#d1728f", "#7aa5d2", "#b0894a", "#68b0a0", "#a98bd0", "#8fb26a", "#cf8a5c",
           "#7f9cc8", "#c0708f", "#5aa89a", "#b59a52", "#8b7fc4", "#9cae5f", "#d0a15a",
           "#6fb0c6", "#b98fc0", "#86b57f", "#b6844f", "#7c96c2", "#a37ec0", "#7aa86a"]


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build():
    calc_form = {c[0]: c[4] for c in CALCS}
    calc_dom = {c[0]: c[3] for c in CALCS}
    titles = dict(_load_theory()[0]) if _load_theory() else {}
    domains = sorted({c[3] for c in CALCS})
    dcol = {d: PALETTE[i % len(PALETTE)] for i, d in enumerate(domains)}

    leaf_idx = {f: i for i, f in enumerate(leaf_forms_ordered())}

    # per-master: members (domain, slug), dominant form, resting theories
    masters = []
    for me in MASTER_EQUATIONS:
        mem = [(d, s) for d, s, _sub in me["rows"]]
        forms = [calc_form.get(s, "") for _d, s in mem]
        dom_form = Counter(f for f in forms if f).most_common(1)
        masters.append({
            "eq": me["eq"], "members": mem,
            "form": dom_form[0][0] if dom_form else "",
        })
    # order masters around the ring by their dominant form's place in the fractal order
    masters.sort(key=lambda m: leaf_idx.get(m["form"], 999))
    nM = len(masters)

    W = Hh = 1600
    cx = cy = Hh / 2
    Rcore = 66
    Rm = 292          # master-equation ring
    Rd0, Rd1 = 360, 566   # calculation reach band
    Rt = 690          # theory rim

    mang = {}
    for i, m in enumerate(masters):
        mang[i] = -math.pi / 2 + 2 * math.pi * i / nM

    # theory placement: each resting theory at the mean angle of the member-dots on it
    # first compute member-dot angles
    memberdots = []   # (x,y,domain,slug,theory,mi)
    theory_angles = defaultdict(list)
    for i, m in enumerate(masters):
        a = mang[i]
        mem = m["members"]
        k = len(mem)
        for j, (d, s) in enumerate(mem):
            frac = (j - (k - 1) / 2) / max(1, k)      # spread within the fan
            ang = a + frac * (2 * math.pi / nM) * 0.82
            r = Rd0 + (Rd1 - Rd0) * (0.15 + 0.7 * (j + 0.5) / max(1, k))
            x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
            tid = CALC_THEORY.get(s)
            memberdots.append((x, y, d, s, tid, i, ang))
            if tid:
                theory_angles[tid].append(ang)

    def cmean(angs):
        return math.atan2(sum(math.sin(a) for a in angs), sum(math.cos(a) for a in angs))
    theories = sorted(theory_angles, key=lambda t: cmean(theory_angles[t]))
    # de-clump theory nodes on the rim
    tplace = {}
    if theories:
        raw = {t: cmean(theory_angles[t]) for t in theories}
        order = sorted(theories, key=lambda t: raw[t])
        gap = 2 * math.pi / len(order) * 0.9
        prev = None
        for t in order:
            ang = raw[t]
            if prev is not None and ang - prev < gap:
                ang = prev + gap
            tplace[t] = ang
            prev = ang

    p = [f'<svg viewBox="0 0 {W} {Hh}" xmlns="http://www.w3.org/2000/svg" role="img" '
         f'aria-label="Atlas: the {len(MASTER_EQUATIONS)} master equations at the kernel, reaching through their '
         f'calculations to the theories on the floor">']
    p.append('<rect width="100%" height="100%" fill="#0f0d09"/>')
    for q in (Rm, Rd1, Rt):
        p.append(f'<circle cx="{cx}" cy="{cy}" r="{q}" fill="none" stroke="#221d15" stroke-width="1"/>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="{Rt}" fill="none" stroke="#3a3120" stroke-width="1" stroke-dasharray="2 7"/>')

    # --- rest_on chords: member dot -> its theory on the rim (layer: calculations->theories) ---
    for x, y, d, s, tid, mi, ang in memberdots:
        if tid in tplace:
            ta = tplace[tid]
            tx, ty = cx + Rt * math.cos(ta), cy + Rt * math.sin(ta)
            mx, my = (x + tx) / 2, (y + ty) / 2
            ctrlx, ctrly = cx + (mx - cx) * 0.5, cy + (my - cy) * 0.5
            p.append(f'<path d="M{x:.0f} {y:.0f} Q{ctrlx:.0f} {ctrly:.0f} {tx:.0f} {ty:.0f}" '
                     f'fill="none" stroke="{dcol.get(d,"#8a8378")}" stroke-width="0.5" opacity="0.10"/>')

    # --- duality weave: arcs between master forms (the bridge-weave over the kernel) ---
    form_masters = defaultdict(list)
    for i, m in enumerate(masters):
        form_masters[m["form"]].append(i)
    for fa, fb, _kind, _ev in FORM_DUALITIES:
        for ia in form_masters.get(fa, []):
            for ib in form_masters.get(fb, []):
                a0, a1 = mang[ia], mang[ib]
                x0, y0 = cx + Rm * math.cos(a0), cy + Rm * math.sin(a0)
                x1, y1 = cx + Rm * math.cos(a1), cy + Rm * math.sin(a1)
                p.append(f'<path d="M{x0:.0f} {y0:.0f} Q{cx:.0f} {cy:.0f} {x1:.0f} {y1:.0f}" '
                         f'fill="none" stroke="#c69a4a" stroke-width="0.8" opacity="0.28"/>')

    # --- reach rays: master node -> its member calc dots (the universality: one eq, many domains) ---
    for x, y, d, s, tid, mi, ang in memberdots:
        mx, my = cx + Rm * math.cos(mang[mi]), cy + Rm * math.sin(mang[mi])
        p.append(f'<line x1="{mx:.0f}" y1="{my:.0f}" x2="{x:.0f}" y2="{y:.0f}" '
                 f'stroke="{dcol.get(d,"#8a8378")}" stroke-width="0.7" opacity="0.33"/>')
    # member dots
    for x, y, d, s, tid, mi, ang in memberdots:
        p.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="4.4" fill="{dcol.get(d,"#8a8378")}" '
                 f'stroke="#0f0d09" stroke-width="0.7"><title>{esc(s.replace("v_","").replace("_"," "))} — {esc(d)}</title></circle>')

    # --- theory rim nodes (THE FLOOR) ---
    for t in theories:
        ta = tplace[t]
        tx, ty = cx + Rt * math.cos(ta), cy + Rt * math.sin(ta)
        p.append(f'<circle cx="{tx:.0f}" cy="{ty:.0f}" r="3.4" fill="#e6c374" stroke="#7a5f28" stroke-width="0.8">'
                 f'<title>{esc(titles.get(t,t))}</title></circle>')
        lx, ly = cx + (Rt + 12) * math.cos(ta), cy + (Rt + 12) * math.sin(ta)
        deg = math.degrees(ta) + (180 if math.cos(ta) < 0 else 0)
        anc = "start" if math.cos(ta) >= 0 else "end"
        nm = esc((titles.get(t, t)).split("(")[0].strip()[:24])
        p.append(f'<text x="{lx:.0f}" y="{ly+2:.0f}" fill="#a08a5a" font-size="8.5" font-family="Georgia,serif" '
                 f'text-anchor="{anc}" transform="rotate({deg:.0f} {lx:.0f} {ly:.0f})">{nm}</text>')

    # --- master equation nodes (THE KERNEL) ---
    for i, m in enumerate(masters):
        a = mang[i]
        mx, my = cx + Rm * math.cos(a), cy + Rm * math.sin(a)
        p.append(f'<circle cx="{mx:.0f}" cy="{my:.0f}" r="7.5" fill="#f0d68a" stroke="#7a5f28" stroke-width="1.3">'
                 f'<title>{esc(m["eq"])}</title></circle>')
        lr = Rm - 16
        lx, ly = cx + lr * math.cos(a), cy + lr * math.sin(a)
        deg = math.degrees(a) + (180 if math.cos(a) < 0 else 0)
        anc = "end" if math.cos(a) >= 0 else "start"
        eqs = m["eq"].split("->")[0].strip()
        p.append(f'<text x="{lx:.0f}" y="{ly:.0f}" fill="#e8dfc9" font-size="10" '
                 f'font-family="\'DejaVu Sans Mono\',monospace" text-anchor="{anc}" '
                 f'transform="rotate({deg:.0f} {lx:.0f} {ly:.0f})">{esc(eqs)}</text>')

    # --- core ---
    p.append(f'<circle cx="{cx}" cy="{cy}" r="{Rcore}" fill="#0f0d09" stroke="#3a3427" stroke-width="1.5"/>')
    p.append(f'<text x="{cx}" y="{cy-8:.0f}" fill="#c69a4a" font-size="26" font-family="Georgia,serif" text-anchor="middle" letter-spacing="3">ATLAS</text>')
    p.append(f'<text x="{cx}" y="{cy+14:.0f}" fill="#8a8378" font-size="10.5" font-family="Georgia,serif" text-anchor="middle">the one kernel</text>')
    p.append(f'<text x="{cx}" y="{cy+30:.0f}" fill="#7d745f" font-size="9" font-family="Georgia,serif" text-anchor="middle">{len(MASTER_EQUATIONS)} master equations</text>')
    p.append('</svg>')
    svg = "\n".join(p)

    nthe = len({c["id"] for c in []})  # placeholder
    total_theory = len([1 for _ in open(os.path.join(ROOT, "data", "theory_cards.jsonl"), encoding="utf-8") if _.strip()])
    leg = "".join(
        f'<span style="display:inline-block;margin:0 .55rem .3rem 0;white-space:nowrap">'
        f'<i style="display:inline-block;width:9px;height:9px;background:{dcol[d]};border-radius:2px;'
        f'vertical-align:middle;margin-right:3px"></i>{esc(d)}</span>' for d in domains)
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Atlas</title>
<style>body{{margin:0;background:#0f0d09;color:#e8dfc9;font-family:Georgia,'Iowan Old Style',serif}}
.wrap{{max-width:1560px;margin:0 auto;padding:1.6rem 1rem 3rem}}
h1{{color:#c69a4a;font-weight:400;font-size:1.9rem;margin:.2rem 0;letter-spacing:1px}}
p{{color:#a99c82;max-width:60rem;line-height:1.62}}svg{{width:100%;height:auto;display:block}}
b{{color:#cbbfa4;font-weight:400}}
.legend{{font-size:.75rem;color:#9a8f76;margin:1rem 0 0;line-height:1.85}}
.key{{color:#a99c82;font-size:.82rem;margin:.5rem 0 0}}
.key i.dot{{display:inline-block;width:10px;height:10px;border-radius:50%;background:#f0d68a;vertical-align:middle;margin:0 4px}}
.key i.line{{display:inline-block;width:22px;height:0;border-top:1px solid #c69a4a;opacity:.5;vertical-align:middle;margin:0 4px}}</style></head>
<body><div class=wrap><a href="/" target="_top" style="color:#8a8172;font:400 .8rem system-ui,sans-serif;text-decoration:none">&#8592; narrowhighway.com</a><h1>ATLAS</h1>
<p>The whole body in one frame. At the heart is the <b>kernel</b> &mdash; the {len(MASTER_EQUATIONS)} <b>master equations</b>,
the finite set of formulas that genuinely connect across domains. Each
master reaches outward through its <b>calculations</b> (the same equation in many fields, colored by
domain) to the <b>theories</b> it rests on, on the rim &mdash; <b>THE FLOOR</b>, {total_theory} theories.
The gold arcs across the centre are the <b>dualities</b>, where two master forms are themselves one thing
transformed. One kernel, reaching everywhere, and bounded.</p>
<p class=key><i class=dot></i>a master equation &nbsp; <i class=line></i>its reach into a domain &nbsp;
&#9679; a calculation (by domain) &nbsp; <span style="color:#e6c374">&#9679;</span> a theory on the floor</p>
{svg}
<div class=legend>{leg}</div>
<p style="color:#7d745f;font-size:.8rem">Found and mapped, never generated. Every line is a formula that
connects, verified against a real calculation. The kernel is finite &mdash; that is the finding.</p>
</div></body></html>"""


def main():
    out = os.path.join(ROOT, "site", "atlas.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(build())
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
