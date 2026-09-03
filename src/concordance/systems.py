"""The SYSTEMS HANDICAP — the operational health of the whole, as one number per subsystem and one
for the course. Matt, 2026-08-31: "We need a visual of each system, so we can see when a portion is
not connected... a continual number, think of it like a handicap in golf. We use that number to
provide breadth to build a strong foundation. We can also discern how fast we can go."

A golf handicap: LOW IS STRONG, 0 is scratch. Each subsystem accrues strokes (gaps) across four
dimensions, and the course handicap is their mean. The number is GROUNDED, never guessed —

  * Tested   — regression coverage, counted from the test files on disk (>=90% -> 0, 70-89% -> 1, else 2)
  * SOP      — a written procedure to run and fix it, docs/SOP/subsystems/<slug>.md present or not (0 / 2)
  * Live     — does it function: every module resolvable (else OUT +4), and not a known-degraded surface (+2)
  * Supported— every known issue has a fallback/plan; +1 per UNsupported open issue in the register (cap 2)

So the number recomputes itself as tests and SOPs are added — writing an SOP drops that subsystem's
handicap by 2 the moment the file lands. Stdlib only; safe to call on every request (cheap disk + import
resolution, no corpus load). The dashboard (site/systems.html) reads report(); GET /systems serves it.
"""
from __future__ import annotations

import importlib.util
import os
import re
from pathlib import Path
from typing import Any, Dict, List

_ROOT = Path(__file__).resolve().parents[2]          # repo root (…/concordance-2)
_SRC = _ROOT / "src" / "concordance"
_SOP_DIR = _ROOT / "docs" / "SOP" / "subsystems"
_TESTS = _ROOT / "tests"

# The subsystems, each grouping the modules that make it up. `degraded` names a surface that is live but
# not yet answering well (a curated, honest flag cleared when the fix ships). `issues` is the support
# register — a known gap; mark it supported once it has a fallback/plan so it stops adding a stroke.
SUBSYSTEMS: List[Dict[str, Any]] = [
    {"name": "Front Door / Ask", "slug": "ask",
     "modules": ["ask", "router", "discern", "clarify", "seekers"]},
    {"name": "Verify / the Moat", "slug": "verify",
     "modules": ["derivation", "receipts", "gates", "kernel", "audit", "candidates", "validate", "warrant"],
     "issues": [{"what": "domain verifier coverage ~52%", "supported": False}]},
    {"name": "The Word / Scripture", "slug": "scripture",
     "modules": ["canon", "harmony", "commentary", "xrefs", "backmatter", "characters", "timeline", "bible_places"]},
    {"name": "Original Tongues", "slug": "tongues",
     "modules": ["pronounce", "translate", "isbe"]},
    {"name": "Prophecy", "slug": "prophecy",
     "modules": ["prophecy", "prophecy_fulfillments"],
     "issues": [{"what": "OT prophecy sweep not yet run", "supported": False}]},
    {"name": "Cloud of Witnesses", "slug": "witnesses",
     "modules": ["witness", "mentors", "lens", "voice"],
     "issues": [{"what": "founders gather pending (per-work start-after)", "supported": False}]},
    {"name": "Find / the Tortoise", "slug": "find", "degraded": True,
     "modules": ["find", "providers", "expand", "craft", "field_canon", "sources"],
     # supported now: a relevance guard on the pulled lead prevents a shared-word mis-selection from
     # leading confidently (it falls to an honest gap instead). Still degraded until selection improves.
     "issues": [{"what": "pull can mis-select a tangential source", "supported": True}]},
    {"name": "The Keeping / Corpus", "slug": "keeping", "degraded": True,
     "modules": ["corpus", "corpus_db", "graph", "decks", "wayfind", "growth"],
     # 2026-09-02: corpus.SUBSTANCE_WEIGHT landed (32ed21a) — within whatever tier the subject
     # partition already admits a card to, a real answer (body >= ops.STUB_BODY_CHARS) now
     # outranks a bare pointer that merely names the same subject. Deployed and unit-pinned
     # (test_retrieval_invariants.py test_VII), but NOT yet measured against real query quality
     # (no live_passes.py re-run) — so still marked degraded rather than upgraded to connected;
     # the stub flood itself is a corpus-growth question this does not touch.
     "issues": [{"what": "~67% word-match stubs", "supported": True},
                {"what": "ranker was blind to substance vs headword", "supported": True}]},
    {"name": "Crisis / Safety", "slug": "crisis",
     "modules": ["crisis_semantic", "floor", "seeds"]},
    {"name": "Coach / Shepherd", "slug": "coach",
     "modules": ["coach", "disciple", "formation", "serve"]},
    {"name": "Field Library", "slug": "field",
     # not degraded: it answers correctly for what it holds (compute is exact, the survival/apothecary
     # cards are real) — it is thinly STOCKED, a growth process the tortoise handles, not a defect.
     "modules": ["apothecary", "almanac", "playbook", "compute", "science_cards", "chess"],
     "issues": [{"what": "shelves thinly stocked (the tortoise grows them on demand)", "supported": True}]},
    {"name": "Museum / TV", "slug": "tv", "modules": ["tv"],
     "issues": [{"what": "curated feeds thin", "supported": False}]},
    {"name": "Identity / Profile / Community", "slug": "identity",
     "modules": ["identity", "profile", "community", "groups", "covenant", "consent", "signing"]},
    {"name": "Steward (money)", "slug": "steward",
     "modules": ["steward", "ledger"],
     "issues": [{"what": "concierge / swipe-fee model is future work", "supported": True}]},
    {"name": "Node / Sovereignty", "slug": "node",
     "modules": ["lighthouse_node", "node_roles", "mesh", "meshtastic_bridge", "airlock"],
     "issues": [{"what": "no off-site backup durability", "supported": False}]},
]


def _tested_strokes(modules: List[str]) -> Dict[str, Any]:
    have = 0
    for m in modules:
        if (_TESTS / f"test_{m}.py").exists():
            have += 1
    pct = round(100 * have / max(1, len(modules)))
    strokes = 0 if pct >= 90 else 1 if pct >= 70 else 2
    return {"strokes": strokes, "pct": pct, "detail": f"{have}/{len(modules)} modules"}


def _sop_strokes(slug: str) -> Dict[str, Any]:
    present = (_SOP_DIR / f"{slug}.md").exists()
    return {"strokes": 0 if present else 2, "present": present,
            "detail": "documented" if present else "none"}


def _live(sub: Dict[str, Any]) -> Dict[str, Any]:
    # OUT if any module cannot even be resolved on the import path; else degraded (curated) or connected.
    missing = []
    for m in sub["modules"]:
        try:
            if importlib.util.find_spec("concordance." + m) is None:
                missing.append(m)
        except Exception:  # noqa: BLE001 — a resolution error is itself an out signal, never a crash
            missing.append(m)
    if missing:
        return {"strokes": 4, "status": "out", "detail": "unresolved: " + ", ".join(missing)}
    if sub.get("degraded"):
        return {"strokes": 2, "status": "degraded", "detail": "live but not yet answering well"}
    return {"strokes": 0, "status": "connected", "detail": "live"}


def _supported_strokes(issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    unsupported = [i for i in issues if not i.get("supported")]
    return {"strokes": min(2, len(unsupported)),
            "open": len(issues), "unsupported": len(unsupported),
            "detail": "; ".join(i["what"] for i in unsupported) or "—"}


def _one(sub: Dict[str, Any]) -> Dict[str, Any]:
    live = _live(sub)
    tested = _tested_strokes(sub["modules"])
    sop = _sop_strokes(sub["slug"])
    supported = _supported_strokes(sub.get("issues") or [])
    handicap = live["strokes"] + tested["strokes"] + sop["strokes"] + supported["strokes"]
    return {"name": sub["name"], "slug": sub["slug"], "modules": sub["modules"],
            "live": live, "tested": tested, "sop": sop, "supported": supported,
            "handicap": handicap}


_GRAPH_CACHE: Dict[str, Any] | None = None


def subsystem_graph() -> Dict[str, Any]:
    """The subsystems as a GRAPH — who wires to whom — derived from the REAL import edges between their
    modules (`a → b` when a module of subsystem `a` imports a module of subsystem `b`). This is the
    polymathic connection made FRACTAL (Matt, 2026-09-02: "our polymathic concept should be fractal
    across the project"): the body's parts are meant to mesh the way the cards do and the domains do, so
    a part that wires to nothing — degree 0 — is a portion OUT OF ORDER, visible here where "its code
    imports fine" (what _live checks) never could. Cached; stdlib-only, no corpus.

    It reads the module-import structure, so it catches how the parts are wired at the source, not every
    runtime handoff — a leaf here means the part does not MESH with its siblings, even if the front door
    still reaches it. Integrate where logical, and the leaves fill in."""
    global _GRAPH_CACHE
    if _GRAPH_CACHE is not None:
        return _GRAPH_CACHE
    mod2slug = {m: s["slug"] for s in SUBSYSTEMS for m in s["modules"]}
    weights: Dict[str, int] = {}
    for s in SUBSYSTEMS:
        for m in s["modules"]:
            p = _SRC / (m + ".py")
            if not p.exists():
                continue
            try:
                txt = p.read_text(encoding="utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                continue
            names = set(re.findall(r"from \.([a-z0-9_]+) import", txt))
            for grp in re.findall(r"from \. import ([a-zA-Z0-9_,\s]+)", txt):
                for n in re.split(r"[,\s]+", re.sub(r"\s+as\s+\w+", "", grp)):
                    n = n.strip()
                    if n:
                        names.add(n)
            for n in names:
                tgt = mod2slug.get(n)
                if tgt and tgt != s["slug"]:
                    key = s["slug"] + ">" + tgt
                    weights[key] = weights.get(key, 0) + 1
    degree = {s["slug"]: 0 for s in SUBSYSTEMS}
    edges = []
    for key in sorted(weights):
        a, b = key.split(">")
        degree[a] += 1
        degree[b] += 1
        edges.append({"from": a, "to": b, "weight": weights[key]})
    isolated = sorted([s for s, d in degree.items() if d == 0])
    _GRAPH_CACHE = {"edges": edges, "degree": degree, "isolated": isolated}
    return _GRAPH_CACHE


def _integration(degree: int) -> str:
    return "isolated" if degree == 0 else ("thin" if degree <= 1 else "connected")


def report() -> Dict[str, Any]:
    """The whole course, sorted worst-first so what needs attention reads first. Cheap enough per
    request: disk stats + import resolution + the module-import graph, no corpus."""
    rows = sorted((_one(s) for s in SUBSYSTEMS), key=lambda r: -r["handicap"])
    g = subsystem_graph()
    out_edges: Dict[str, List[str]] = {}
    for e in g["edges"]:
        out_edges.setdefault(e["from"], []).append(e["to"])
    for r in rows:
        d = g["degree"].get(r["slug"], 0)
        r["integration"] = {"degree": d, "status": _integration(d),
                            "connects_to": sorted(set(out_edges.get(r["slug"], [])))}
    n = len(rows)
    total = sum(r["handicap"] for r in rows)
    return {
        "course_handicap": round(total / n, 1) if n else 0.0,
        "subsystems": rows,
        "graph": g,
        "counts": {
            "connected": sum(1 for r in rows if r["live"]["status"] == "connected"),
            "degraded": sum(1 for r in rows if r["live"]["status"] == "degraded"),
            "out": sum(1 for r in rows if r["live"]["status"] == "out"),
            "isolated": len(g["isolated"]),
            "total": n,
        },
        "model": {
            "live": "0 connected · 2 degraded · 4 out (a module fails to resolve)",
            "tested": "0 if >=90% modules covered · 1 if 70-89% · 2 under 70%",
            "sop": "0 if docs/SOP/subsystems/<slug>.md exists · 2 if none",
            "supported": "+1 per unsupported open issue in the register (cap 2)",
            "integration": "degree = how many other subsystems it wires to (import edges); "
                           "isolated(0) / thin(≤1) / connected — the polymathic mesh, fractal with the card graph",
            "note": "a golf handicap — low is strong, 0 is scratch; the mean is the course handicap",
        },
    }
