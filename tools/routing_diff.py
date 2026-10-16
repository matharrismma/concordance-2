#!/usr/bin/env python3
"""Routing-basis diff — what a change moves in the resolver's phrase->domain index, and whether a
pinned golden query's decision flips. Issue #31. Deterministic, stdlib only, no model.

THE INCIDENT (2026-10-16, PR #29). `domain_resolver._build()` harvests its routing vocabulary from
static source: the registry aliases, the curated `_SYNONYMS`, every verifier's `verify_*` names and
the distinctive words of every verifier's MODULE DOCSTRING (idf-weighted) — then decorrelates the
whole index by domain-frequency, so a phrase shared by d domains is worth less to each. The new
formal_logic.minimal_form docstring said "prime implicants". That credited `prime` to a THIRD
domain; decorrelation shrank number_theory's share of `prime` below the 2.5 decision floor; and
"is 17 prime" went from DECIDING number_theory to ASKING. Nothing in that PR touched number_theory
and nothing in its diff showed the move. One Born-confidence test pin caught it; the fix was wording.

The systemic fact: editing ANY verifier's docstring (or a synonym, or adding a verifier) can move
ANOTHER domain's routing, and the diff that explains it is invisible in the PR. This makes it
visible, and fences it:

  snapshot OUT.json [--root DIR]
      build the index in a checkout (default: this one) and record every phrase's {domain: weight}
      plus, for every golden query, the resolver's decision / top domain / confidence per surface.
  compare BASE.json HEAD.json [--fail-on-flip] [--limit N]
      phrases added / removed, phrases whose DOMAIN SET changed, the 20 largest weight deltas, and
      every golden query whose decision or top domain changed. With --fail-on-flip, exit 1 when a
      golden DECISION changed — the PR must then say why and move the pin deliberately — else 0.

THE GOLDEN QUERIES are the routing pins in tests/test_domain_resolver.py: every (query, domain)
string pair and every literal query handed to resolve_domain()/_menu() there, read by ast exactly
as the resolver reads the verifiers — so a pin added to that test is watched here with no second
list to drift. (data/domain_goldens.json holds per-domain verifier PACKETS, true/false pairs for
the sealing gate; it has no queries and is not read.) Each query is resolved on both surfaces.

CI (.github/workflows/ci.yml, the gate job) snapshots the base branch in a throwaway worktree and
the PR checkout, compares with --fail-on-flip, and writes the report to the job's step summary.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
PINS = Path("tests") / "test_domain_resolver.py"
SURFACES = ("secular", "witness")
TOP_DELTAS = 20


def golden_queries(root: Path) -> List[str]:
    """Every query pinned in tests/test_domain_resolver.py, harvested statically (never imported)."""
    f = root / PINS
    if not f.exists():
        return []
    tree = ast.parse(f.read_text(encoding="utf-8"))

    def _s(node):
        return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None

    out: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Tuple) and len(node.elts) == 2 and all(_s(e) is not None for e in node.elts):
            out.append(_s(node.elts[0]))                      # ("is 17 a prime number", "number_theory")
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
              and node.func.id in ("resolve_domain", "_menu") and node.args and _s(node.args[0]) is not None):
            out.append(_s(node.args[0]))                      # resolve_domain("is 17 prime")
    return sorted({q.strip() for q in out if q.strip()})


def _import_resolver(root: Path):
    """Import the resolver FROM root/src and prove it — a snapshot of the wrong checkout is a lie."""
    src = (root / "src").resolve()
    pkg = sys.modules.get("concordance")
    if pkg is not None and src not in Path(pkg.__file__).resolve().parents:
        for name in [m for m in sys.modules if m == "concordance" or m.startswith("concordance.")]:
            del sys.modules[name]
    sys.path.insert(0, str(src))
    from concordance import domain_resolver as dr
    got = Path(dr.__file__).resolve()
    if src not in got.parents:
        raise SystemExit(f"resolver imported from {got}, not from {src}")
    return dr


def build_snapshot(root: Path) -> Dict:
    """The routing basis of one checkout: the full index and every golden query's decision."""
    dr = _import_resolver(root)
    dr._build()
    index = {p: {d: round(w, 6) for d, w in sorted(doms.items())} for p, doms in sorted(dr._INDEX.items())}
    goldens: Dict[str, Dict[str, Dict]] = {}
    for q in golden_queries(root):
        goldens[q] = {}
        for s in SURFACES:
            r = dr.resolve_domain(q, surface=s)
            goldens[q][s] = {"decision": r.get("decision"),
                             "top": r["candidates"][0]["domain"] if r.get("candidates") else None,
                             "confidence": r.get("confidence"),
                             "ask": bool(r.get("ask")), "crisis": bool(r.get("crisis"))}
    meta = {"root": str(root), "domains": len(dr._DOMAINS), "phrases": len(index), "goldens": len(goldens)}
    return {"meta": meta, "index": index, "goldens": goldens}


def _fmt(doms: Dict[str, float]) -> str:
    return "{" + ", ".join(f"{d}: {w:.3f}" for d, w in sorted(doms.items())) + "}"


def compare(base: Dict, head: Dict, limit: int = 50) -> Tuple[List[str], int]:
    """The report (markdown-ish lines, plain ASCII) and the number of golden DECISION flips."""
    bi, hi = base.get("index", {}), head.get("index", {})
    bg, hg = base.get("goldens", {}), head.get("goldens", {})
    common = sorted(set(bi) & set(hi))

    added = [f"`{p}` -> {_fmt(hi[p])}" for p in sorted(set(hi) - set(bi))]
    removed = [f"`{p}` was {_fmt(bi[p])}" for p in sorted(set(bi) - set(hi))]
    domset = [f"`{p}`: {sorted(bi[p])} -> {sorted(hi[p])}" for p in common if set(bi[p]) != set(hi[p])]
    deltas = []
    for p in common:
        for d in sorted(set(bi[p]) & set(hi[p])):
            if abs(hi[p][d] - bi[p][d]) > 1e-9:
                deltas.append((-abs(hi[p][d] - bi[p][d]), p, d, bi[p][d], hi[p][d]))
    deltas.sort()
    moved: List[str] = []
    flips = 0
    for q in sorted(set(bg) & set(hg)):
        for s in SURFACES:
            a, b = bg[q].get(s), hg[q].get(s)
            if not a or not b:
                continue
            if a["decision"] != b["decision"]:
                flips += 1
                moved.append(f"FLIP `{q}` [{s}]: decision {a['decision']} -> {b['decision']} "
                             f"(top {a['top']} -> {b['top']}, confidence {a['confidence']} -> {b['confidence']})")
            elif a["top"] != b["top"]:
                moved.append(f"top `{q}` [{s}]: {a['top']} -> {b['top']} (decision {b['decision']} unchanged)")
    pins_new, pins_gone = sorted(set(hg) - set(bg)), sorted(set(bg) - set(hg))

    bm, hm = base.get("meta", {}), head.get("meta", {})
    lines = [f"Routing basis: {bm.get('phrases', len(bi))} -> {hm.get('phrases', len(hi))} phrases, "
             f"{bm.get('domains', '?')} -> {hm.get('domains', '?')} domains; "
             f"{len(set(bg) & set(hg))} golden queries checked on {len(SURFACES)} surfaces"
             + (f" (+{len(pins_new)} new pin(s))" if pins_new else "")
             + (f" (-{len(pins_gone)} pin(s) gone)" if pins_gone else "") + "."]
    changed = added or removed or domset or deltas or moved
    if not changed:
        lines.append("no routing changes: every phrase, weight and golden decision is identical.")
        return lines, 0
    lines.append(f"{len(added)} added, {len(removed)} removed, {len(domset)} domain-set changes, "
                 f"{len(deltas)} weight changes, {len(moved)} golden moves, {flips} golden DECISION flip(s).")
    lines.append("")

    def section(title: str, rows: List[str], cap: int) -> None:
        lines.append(f"### {title} ({len(rows)})")
        lines.extend(f"- {r}" for r in rows[:cap])
        if not rows:
            lines.append("- none")
        if len(rows) > cap:
            lines.append(f"- ... and {len(rows) - cap} more")
        lines.append("")

    section("Golden queries whose decision or top domain changed", moved, limit)
    section("Phrases whose domain set changed", domset, limit)
    section(f"Largest weight deltas (top {TOP_DELTAS})",
            [f"`{p}` / {d}: {b:.3f} -> {h:.3f} ({h - b:+.3f})" for _, p, d, b, h in deltas[:TOP_DELTAS]], TOP_DELTAS)
    section("Phrases added", added, limit)
    section("Phrases removed", removed, limit)
    if pins_new or pins_gone:
        section("Golden pins added", [f"`{q}`" for q in pins_new], limit)
        section("Golden pins removed", [f"`{q}`" for q in pins_gone], limit)
    if flips:
        lines.append(f"FAIL: {flips} golden decision(s) flipped. If the move is intended, say why in the PR "
                     f"and move the pin in tests/test_domain_resolver.py deliberately.")
    return lines, flips


def _load(path: str) -> Dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot", help="write the routing basis of a checkout")
    s.add_argument("out")
    s.add_argument("--root", default=str(ROOT), help="the checkout to snapshot (its src/ and tests/)")
    c = sub.add_parser("compare", help="report what moved between two snapshots")
    c.add_argument("base")
    c.add_argument("head")
    c.add_argument("--fail-on-flip", action="store_true", help="exit 1 when a golden decision changed")
    c.add_argument("--limit", type=int, default=50, help="rows listed per section")
    a = ap.parse_args(argv)
    if a.cmd == "snapshot":
        snap = build_snapshot(Path(a.root).resolve())
        Path(a.out).write_text(json.dumps(snap, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                               encoding="utf-8")
        m = snap["meta"]
        print(f"wrote {a.out}: {m['phrases']} phrases, {m['domains']} domains, {m['goldens']} golden queries")
        return 0
    lines, flips = compare(_load(a.base), _load(a.head), limit=a.limit)
    print("\n".join(lines))
    return 1 if (flips and a.fail_on_flip) else 0


if __name__ == "__main__":
    sys.exit(main())
