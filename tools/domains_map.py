#!/usr/bin/env python3
"""THE DOMAIN CONNECTIONS — which fields are joined, and by which formula.

Matt, 2026-09-14: "I can't see the connections between domains." So make the DOMAINS
the fixed nodes on a ring, and draw each MASTER EQUATION as a thread that passes
through every domain it connects. A thread IS the connection, and its colour names
the formula that makes it: the wave equation is one thread touching electrical,
acoustics, music, geology, physics and oceanography; the flux law is another through
electrical, thermal, chemical and hydraulic. A domain's node is sized by how many
master equations run through it — the hubs of reality's computation.

Stdlib only; inline SVG; renders with scripting off.

    python tools/domains_map.py   # writes site/domains.html
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
from seed_bridges import MASTER_EQUATIONS  # noqa: E402

# a warm-to-cool palette for the master threads (distinct enough to read as bundles)
MPAL = ["#c69a4a", "#6f9ec6", "#c67f6f", "#7fb069", "#9b7fc6", "#5fa8a0", "#d1728f",
        "#c6a86f", "#7aa5d2", "#68b0a0", "#a98bd0", "#8fb26a", "#cf8a5c", "#7f9cc8",
        "#c0708f", "#5aa89a", "#b59a52", "#8b7fc4", "#9cae5f", "#d0a15a", "#6fb0c6", "#b98fc0"]

# group domains by family so connected fields sit near each other (shorter, clearer threads)
FAMILY = [
    ("physical", ["physics", "electrical", "thermodynamics", "optics", "acoustics",
                  "nuclear_physics", "condensed_matter", "atomic", "materials_science", "quantum_computing"]),
    ("chemical", ["chemistry", "electrochemistry", "periodic_table"]),
    ("life", ["biology", "genetics", "neuroscience", "medicine", "ecology",
              "exercise_science", "nutrition", "agriculture", "soil_science"]),
    ("earth_sky", ["geology", "oceanography", "meteorology", "hydrology", "astronomy",
                   "ephemeris", "geography", "archaeology"]),
    ("formal", ["mathematics", "statistics", "probability", "computer_science", "information_theory",
                "combinatorics", "number_theory", "linear_algebra", "formal_logic", "networking",
                "cryptography", "operations_research"]),
    ("human", ["economics", "finance", "real_estate", "labor", "law", "governance", "game_theory",
               "sports_analytics", "linguistics", "music_theory", "photography", "architecture",
               "construction", "manufacturing", "rhetoric", "history_chronology", "calendar_time"]),
]
FAMILY_TINT = {"physical": "#c69a4a", "chemical": "#6fb0a0", "life": "#7fb069",
               "earth_sky": "#6f9ec6", "formal": "#9b7fc6", "human": "#c67f6f"}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build():
    # domains that any master equation connects, and the masters through each
    master_domains = []
    for me in MASTER_EQUATIONS:
        ds = sorted({d for d, _s, _sub in me["rows"]})
        master_domains.append((me["eq"], ds))
    dom_deg = defaultdict(int)
    for _eq, ds in master_domains:
        for d in ds:
            dom_deg[d] += 1
    present = set(dom_deg)

    # order domains by family, then keep only those actually connected
    fam_of = {}
    ordered = []
    for fam, doms in FAMILY:
        for d in doms:
            fam_of[d] = fam
            if d in present:
                ordered.append(d)
    # any connected domain not in the family table -> append at the end
    for d in sorted(present):
        if d not in ordered:
            ordered.append(d)
            fam_of.setdefault(d, "human")
    n = len(ordered)
    ang = {d: -math.pi / 2 + 2 * math.pi * i / n for i, d in enumerate(ordered)}

    W = H = 1500
    cx = cy = H / 2
    Rn = 560           # domain-node ring
    maxdeg = max(dom_deg.values())

    p = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
         f'aria-label="Connections between domains: each master equation is a thread through '
         f'the domains it joins">']
    p.append('<rect width="100%" height="100%" fill="#0f0d09"/>')

    # faint family arcs on the outside, so the families read
    fam_idx = defaultdict(list)
    for i, d in enumerate(ordered):
        fam_idx[fam_of[d]].append(i)
    for fam, idxs in fam_idx.items():
        a0 = -math.pi / 2 + 2 * math.pi * (min(idxs) - 0.42) / n
        a1 = -math.pi / 2 + 2 * math.pi * (max(idxs) + 0.42) / n
        col = FAMILY_TINT.get(fam, "#c69a4a")
        large = 1 if (a1 - a0) > math.pi else 0
        x0, y0 = cx + (Rn + 60) * math.cos(a0), cy + (Rn + 60) * math.sin(a0)
        x1, y1 = cx + (Rn + 60) * math.cos(a1), cy + (Rn + 60) * math.sin(a1)
        p.append(f'<path d="M{x0:.0f} {y0:.0f} A{Rn+60:.0f} {Rn+60:.0f} 0 {large} 1 {x1:.0f} {y1:.0f}" '
                 f'fill="none" stroke="{col}" stroke-width="2.5" opacity="0.5"/>')
        amid = (a0 + a1) / 2
        lx, ly = cx + (Rn + 78) * math.cos(amid), cy + (Rn + 78) * math.sin(amid)
        deg = math.degrees(amid) + (180 if math.cos(amid) < 0 else 0)
        anc = "start" if math.cos(amid) >= 0 else "end"
        p.append(f'<text x="{lx:.0f}" y="{ly:.0f}" fill="{col}" font-size="12" opacity="0.8" '
                 f'font-family="Georgia,serif" text-anchor="{anc}" '
                 f'transform="rotate({deg:.0f} {lx:.0f} {ly:.0f})">{esc(fam.replace("_"," "))}</text>')

    # the threads: each master equation through its domains, bundled toward the centre
    def node(d):
        return cx + Rn * math.cos(ang[d]), cy + Rn * math.sin(ang[d])
    for mi, (eq, ds) in enumerate(master_domains):
        if len(ds) < 2:
            continue
        pts = [node(d) for d in ds]
        col = MPAL[mi % len(MPAL)]
        # connect each consecutive pair with a curve bowed toward the centre (bundling)
        seg = []
        for a in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[a], pts[a + 1]
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            ctrlx, ctrly = cx + (mx - cx) * 0.32, cy + (my - cy) * 0.32
            seg.append(f'<path d="M{x0:.0f} {y0:.0f} Q{ctrlx:.0f} {ctrly:.0f} {x1:.0f} {y1:.0f}" '
                       f'fill="none" stroke="{col}" stroke-width="1.5" opacity="0.5" '
                       f'stroke-linecap="round"><title>{esc(eq)} — connects {esc(", ".join(ds))}</title></path>')
        p.extend(seg)

    # domain nodes, sized by how many master equations run through them
    for d in ordered:
        x, y = node(d)
        deg = dom_deg[d]
        r = 3.5 + (deg / maxdeg) * 8.5
        col = FAMILY_TINT.get(fam_of[d], "#c69a4a")
        p.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{col}" stroke="#0f0d09" '
                 f'stroke-width="1"><title>{esc(d)} — on {deg} master equations</title></circle>')
        lx, ly = cx + (Rn + 16) * math.cos(ang[d]), cy + (Rn + 16) * math.sin(ang[d])
        a = ang[d]
        rot = math.degrees(a) + (180 if math.cos(a) < 0 else 0)
        anc = "start" if math.cos(a) >= 0 else "end"
        p.append(f'<text x="{lx:.0f}" y="{ly+2:.0f}" fill="#cbbfa4" font-size="10.5" '
                 f'font-family="Georgia,serif" text-anchor="{anc}" '
                 f'transform="rotate({rot:.0f} {lx:.0f} {ly:.0f})">{esc(d)}</text>')

    p.append(f'<circle cx="{cx}" cy="{cy}" r="48" fill="#0f0d09" stroke="#3a3427"/>')
    p.append(f'<text x="{cx}" y="{cy-3:.0f}" fill="#c69a4a" font-size="12" font-family="Georgia,serif" text-anchor="middle">DOMAINS</text>')
    p.append(f'<text x="{cx}" y="{cy+14:.0f}" fill="#8a8378" font-size="9.5" font-family="Georgia,serif" text-anchor="middle">{n} connected</text>')
    p.append('</svg>')
    svg = "\n".join(p)

    # a small legend of the strongest connectors (masters spanning the most domains)
    strong = sorted(master_domains, key=lambda md: -len(md[1]))[:8]
    leg = "".join(
        f'<div style="margin:.2rem 0"><i style="display:inline-block;width:16px;height:0;border-top:2px solid {MPAL[master_domains.index(md)%len(MPAL)]};'
        f'vertical-align:middle;margin-right:7px"></i>'
        f'<code style="color:#e6c374">{esc(md[0].split("->")[0].strip())}</code> '
        f'<span style="color:#8a8378">&mdash; {len(md[1])} domains</span></div>'
        for md in strong)
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<script src="/shell.js"></script>
<title>Domain Connections</title>
<style>body{{margin:0;background:#0f0d09;color:#e8dfc9;font-family:Georgia,'Iowan Old Style',serif}}
.wrap{{max-width:1460px;margin:0 auto;padding:1.6rem 1rem 3rem}}
h1{{color:#c69a4a;font-weight:400;font-size:1.8rem;margin:.2rem 0}}
p{{color:#a99c82;max-width:60rem;line-height:1.62}}svg{{width:100%;height:auto;display:block}}
b{{color:#cbbfa4;font-weight:400}}code{{font-family:'DejaVu Sans Mono',monospace;font-size:.85em}}
.leg{{font-size:.82rem;color:#9a8f76;margin:1rem 0 0}}</style></head>
<body><div class=wrap><h1>Connections Between Domains</h1>
<p>Every domain is a node on the ring, grouped into families. Each <b>thread</b> is a
<b>master equation</b>, drawn through every domain it connects &mdash; the thread <b>is</b> the
connection, and its colour is the formula that makes it. Where many threads pass through one node,
that field is a <b>hub</b> of reality's computation (its node grows). {n} connected domains, joined
by the {len(MASTER_EQUATIONS)} master equations.</p>
<div class=leg>The widest bridges &mdash; one formula, this many fields:{leg}</div>
{svg}
<p style="color:#7d745f;font-size:.8rem">Found and mapped, never generated. A thread between two
fields means the same computation runs in both, under a change of variable.</p></div></body></html>"""


def main():
    out = os.path.join(ROOT, "site", "domains.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(build())
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
