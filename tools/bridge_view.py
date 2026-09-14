#!/usr/bin/env python3
"""THE BRIDGES, catalogued — the cross-domain isomorphisms as a browsable page.

Renders site/bridges.html from seed_bridges.build_bridges(): the universal
computations (forms across many domains), the deep form-to-form dualities, and the
theory isomorphisms THE FLOOR asserts. This is the "integrate" artifact — every
bridge in one place, ranked, each carrying its evidence.

    python tools/bridge_view.py
"""
import html
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass
from seed_bridges import build_bridges, _load_theory  # noqa: E402


def esc(s):
    return html.escape(str(s))


def build():
    cards, _report = build_bridges()
    titles, _ = _load_theory()
    by_kind = defaultdict(list)
    for c in cards:
        by_kind[c["extra"]["bridge_kind"]].append(c)

    # --- master equations: one connecting formula + a substitution table (the crown) ---
    masters = sorted(by_kind["master"], key=lambda c: -c["extra"]["span"])
    master_blocks = []
    for c in masters:
        rows = "".join(
            f'<tr><td class=dom>{esc(d)}</td><td class=sub>{esc(sub)}</td></tr>'
            for d, sub in c["extra"]["substitutions"])
        master_blocks.append(
            f'<div class=master><div class=eq>{esc(c["extra"]["equation"])}</div>'
            f'<div class=gist>{esc(c["extra"]["gist"])}</div>'
            f'<table class=subtab><tbody>{rows}</tbody></table></div>')

    # --- universal computations: form bridges as ranked bars ---
    forms = sorted(by_kind["form"], key=lambda c: -c["extra"]["span"])
    maxspan = forms[0]["extra"]["span"] if forms else 1
    bars = []
    for c in forms:
        span = c["extra"]["span"]
        w = 6 + 94 * (span / maxspan)
        doms = ", ".join(c["extra"]["domains"])
        bars.append(
            f'<div class=bar-row><div class=bar-label>{esc(c["extra"]["form"])}</div>'
            f'<div class=bar-track><div class=bar-fill style="width:{w:.1f}%">'
            f'<span class=bar-n>{span}</span></div></div>'
            f'<div class=bar-doms title="{esc(doms)}">{esc(doms)}</div></div>')

    # --- form dualities ---
    duals = by_kind["duality"]
    dual_rows = []
    for c in duals:
        fa, fb = c["extra"]["forms"]
        dual_rows.append(
            f'<li><span class=pair>{esc(fa)} <b>↔</b> {esc(fb)}</span>'
            f'<span class=kind>{esc(c["extra"]["relation"])}</span>'
            f'<span class=ev>{esc(c["body"].split(". ", 1)[-1])}</span></li>')

    # --- theory isomorphisms (the crown) ---
    theos = sorted(by_kind["theory"], key=lambda c: c["title"])
    theo_rows = []
    for c in theos:
        a, b = [m["to_card_id"] for m in c["connections"][:2]]
        ta, tb = titles.get(a, a), titles.get(b, b)
        ev = c["extra"].get("evidence", "")
        theo_rows.append(
            f'<li><span class=pair>{esc(ta)} <b>↔</b> {esc(tb)}</span>'
            f'<span class=ev>{esc(ev)}</span></li>')

    # --- hubs ---
    hubs = sorted(by_kind["hub"], key=lambda c: -c["extra"]["span"])
    hub_rows = []
    for c in hubs:
        tid = c["connections"][0]["to_card_id"]
        hub_rows.append(
            f'<li><span class=pair>{esc(titles.get(tid, tid))}</span>'
            f'<span class=kind>{c["extra"]["span"]} domains</span>'
            f'<span class=ev>{esc(", ".join(c["extra"]["domains"]))}</span></li>')

    nm, nf, nd, nt, nh = len(masters), len(forms), len(duals), len(theos), len(hubs)
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>The Bridges</title>
<style>
:root{{--bg:#12100c;--ink:#e8dfc9;--dim:#a99c82;--faint:#7d745f;--gold:#c69a4a;--gold2:#e6c374;--line:#2a2620;--panel:#171410}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:Georgia,'Iowan Old Style',serif;line-height:1.6}}
.wrap{{max-width:64rem;margin:0 auto;padding:2rem 1.2rem 4rem}}
h1{{color:var(--gold);font-weight:400;font-size:2rem;margin:.2rem 0 .4rem}}
h2{{color:var(--gold2);font-weight:400;font-size:1.25rem;margin:2.4rem 0 .3rem;border-bottom:1px solid var(--line);padding-bottom:.3rem}}
.lede{{color:var(--dim);max-width:46rem}}
.sub{{color:var(--faint);font-size:.85rem;margin:.1rem 0 1rem}}
.bar-row{{display:grid;grid-template-columns:8.5rem 1fr;align-items:center;gap:.5rem .8rem;margin:.28rem 0}}
.bar-label{{font-size:.92rem;color:var(--ink);text-align:right}}
.bar-track{{background:#1c1913;border-radius:3px;overflow:hidden;height:1.35rem;position:relative}}
.bar-fill{{background:linear-gradient(90deg,#8a6a2e,var(--gold));height:100%;display:flex;align-items:center;justify-content:flex-end;min-width:1.4rem}}
.bar-n{{color:#1a1509;font-size:.78rem;font-weight:bold;padding-right:.4rem}}
.bar-doms{{grid-column:2;font-size:.72rem;color:var(--faint);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
ul.bridges{{list-style:none;padding:0;margin:.4rem 0}}
ul.bridges li{{padding:.55rem 0;border-bottom:1px solid #201c15}}
.pair{{display:block;color:var(--ink);font-size:1rem}}
.pair b{{color:var(--gold);font-style:normal;padding:0 .15rem}}
.kind{{display:inline-block;color:var(--gold2);font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;margin:.1rem .5rem .1rem 0}}
.ev{{display:block;color:var(--dim);font-size:.86rem;margin-top:.15rem}}
.count{{color:var(--gold);font-weight:bold}}
.master{{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--gold);border-radius:5px;padding:.7rem .9rem;margin:.7rem 0}}
.master .eq{{font-family:'DejaVu Sans Mono',ui-monospace,monospace;font-size:1.05rem;color:var(--gold2);letter-spacing:.02em}}
.master .gist{{color:var(--dim);font-size:.86rem;margin:.25rem 0 .5rem}}
table.subtab{{border-collapse:collapse;width:100%;font-size:.82rem}}
table.subtab td{{padding:.2rem .5rem;border-top:1px solid #201c15;vertical-align:top}}
table.subtab td.dom{{color:var(--gold);white-space:nowrap;width:9rem;font-size:.8rem}}
table.subtab td.sub{{color:var(--dim)}}
</style></head>
<body><div class=wrap>
<h1>The Bridges</h1>
<p class=lede>A bridge is one structure that appears in more than one domain — the universality of the
one kernel, seen as a connection. And a real bridge <b>must have a formula that connects</b>: not
just a shared category, but one equation instantiated in each domain under a change of variable.
When the same computation runs a circuit and a chemical reaction and an economy, the connection is
the finding, not the coincidence. <span class=count>{nm+nf+nd+nt+nh}</span> bridges, each carrying
its evidence.</p>

<h2>Master equations <span class=sub>&mdash; one formula, a substitution dictionary across domains</span></h2>
<p class=sub>The strongest bridge: the SAME equation in every domain, connected by naming what each
symbol becomes. This is a formula that connects.</p>
{''.join(master_blocks)}

<h2>Universal computations <span class=sub>&mdash; one canonical form, many domains</span></h2>
<p class=sub>The forms that run the widest. Bar length is the number of domains the same computation appears in.</p>
{''.join(bars)}

<h2>Form dualities <span class=sub>&mdash; deep bridges between two forms</span></h2>
<p class=sub>Not a shared domain but a shared identity: two forms that are the same thing transformed.</p>
<ul class=bridges>{''.join(dual_rows)}</ul>

<h2>Theory isomorphisms <span class=sub>&mdash; the same form in two sciences ({nt})</span></h2>
<p class=sub>The cross-domain isomorphisms THE FLOOR asserts: two theories that are one structure in
different clothes.</p>
<ul class=bridges>{''.join(theo_rows)}</ul>

<h2>Theory hubs <span class=sub>&mdash; one theory holding up many fields</span></h2>
<ul class=bridges>{''.join(hub_rows)}</ul>

<p class=sub style="margin-top:2rem">Found and mapped, never generated. A bridge with no evidence is
not a bridge — that rule is the line between a map of reality and apophenia.</p>
</div></body></html>"""


def main():
    out = os.path.join(ROOT, "site", "bridges.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(build())
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
