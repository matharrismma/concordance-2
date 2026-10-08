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

import importlib
import importlib.util
import json
import logging
import os
import re
import socket
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

_log = logging.getLogger("concordance.systems")

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
     # 2026-10-06: MEASURED (tools/coverage_meter.py) — the "~52%" was a stale estimate. The breadth is
     # comprehensive: 74 domain verifiers (STEM + applied + humanities), all registered, ~80 benchmarked
     # (a golden per domain, re-run every deploy, 0 false positives). Unit-test DEPTH is now 100% — every
     # domain has a tests/test_<module>.py pinning a CONFIRMED + a MISMATCH + a NOT_APPLICABLE (A2, 2026-10-06).
     "issues": [{"what": "unit-test depth 100% of domains (74/74 have tests/test_<module>.py; breadth also "
                         "comprehensive: ~80 benchmarked, 0 FP) — measured, coverage_meter", "supported": True}]},
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
     # outranks a bare pointer that merely names the same subject. 2026-09-03: measuring that live
     # exposed a second facet — EVERY single-word subject lookup led with a phonetic string
     # ("gravity" -> "G R AE1 V AH0 T IY0"), because a pronunciation card's title is its headword
     # and won the exact-title boost, and its CMU-boilerplate body clears the stub bar so substance
     # couldn't catch it. Fixed (a525611): the pronunciation genre loses the exact-title boost; the
     # six live subject lookups that led with phonemes now lead with the definition, ask_probe holds
     # 25/25. Both ranker facets are now closed AND deployed. Still marked degraded, deliberately:
     # the remaining reason is STOCKING, not the ranker. 2026-10-06: MEASURED over the whole keeping
     # (ops.substance across the resident cards + the shard bodies in cards.json, connection edges
     # excluded) — 873,971 holdings, 55.8% substance / 44.2% stub, NOT the ~67% that was estimated
     # here. And the stubs are concentrated: ~97% of them sit in three shelves — science/OEIS (87%
     # stub), world (60%), dictionary (52%) — and much of that is brief-BY-NATURE reference (an OEIS
     # sequence, a headword), complete as-is, not a stocking failure. Flipping to connected still
     # wants a retrieval-QUALITY probe (does a real query land on an answer?), not just composition.
     "issues": [{"what": "44.2% stub bodies (measured 2026-10-06; 97% in science/OEIS, world, "
                         "dictionary — much brief-by-nature) — a stocking gap, not a ranker defect", "supported": True},
                {"what": "ranker blind to substance vs headword — FIXED (32ed21a + a525611)", "supported": True}]},
    {"name": "Crisis / Safety", "slug": "crisis",
     "modules": ["crisis_semantic", "floor", "seeds"]},
    {"name": "Coach / Shepherd", "slug": "coach",
     # the engine IS the coach (Matt, 2026-10-06): lead composes the discerned solution/tool/technique/
     # strategy and applies it; trajectory measures what works (success guides, failure narrows, the
     # coaching-tree floor, downline value, and the fruit test) — the mission's own mechanisms.
     "modules": ["coach", "disciple", "formation", "serve", "lead", "trajectory", "archetypes"]},
    {"name": "Field Library", "slug": "field",
     # not degraded: it answers correctly for what it holds (compute is exact, the survival/apothecary
     # cards are real) — it is thinly STOCKED, a growth process the tortoise handles, not a defect.
     # chess is the refined-system witness that is a top-level module here; pressure_fighting and
     # game_theory are verifier domains, counted in the verifier total, not as field modules
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


def _receiver_status() -> Optional[Dict[str, Any]]:
    """The receiver ladder (receiver.status) — pure over the gate artifacts; a failure to read it never takes
    the systems report down with it."""
    try:
        from . import receiver as _receiver
        return _receiver.status()
    except Exception as e:  # noqa: BLE001
        return {"complete": False, "read": f"the receiver could not be read: {type(e).__name__}", "stages": []}


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
        # THE LAUNCH ROLL-CALL (2026-10-08): what the last boot measured — ms and resident memory per
        # subsystem, the heavy singletons, and every edge priced by what it pulls in. None until a boot ran.
        "boot": last_checkin(),
        # THE RECEIVER (2026-10-08, Matt: "the receiver is a complete system. We will be complete when we have
        # all components that function correctly"): the superheterodyne's stages, each bound to its component
        # and its proof read from the gate artifacts; complete only when every stage and the whole are proven.
        "receiver": _receiver_status(),
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
            "boot": "the launch roll-call: each subsystem imported at boot and timed (ms) with its resident-memory "
                    "delta (KB); modules the server had already imported are marked preloaded (cost paid in the "
                    "server's own startup); tools/checkin.py measures each piece ALONE for its true cold cost",
        },
    }


# ── THE LAUNCH ROLL-CALL (Matt, 2026-10-08: "each subsystem check in on launch ... see speed and memory of
# each piece. We optimize each and the connections between them to get full capability.") ─────────────────
#
# Two instruments, deliberately split, because they answer different questions:
#   checkin()          IN-PROCESS, at boot: what this server actually loads, what each subsystem costs to bring
#                      in beyond what is already resident, and what each import edge PULLS IN. Cheap; never
#                      fails boot; one journal line per subsystem; written to data/boot_checkin.json.
#   tools/checkin.py   ISOLATED, on demand: each subsystem imported ALONE in a fresh interpreter — its true cold
#                      ms and peak RSS with nothing else resident, minus a bare-interpreter baseline. The
#                      optimizable number. Also the heavy singletons (corpus, graph, verify deps) by themselves.
# Stdlib only. Memory is RESIDENT SET (RSS): /proc on Linux (the box), psapi on Windows (the desk); None where
# neither is available — a missing number is reported as missing, never as zero.

_LAST_CHECKIN: Optional[Dict[str, Any]] = None


def _ensure_rollcall_handler() -> None:
    """The service configures no logging handler anywhere, so INFO lines vanish — verified 2026-10-08: after a
    boot the journal held only systemd's own lines (including its "1.2G memory peak"), never a Python one. The
    roll-call is the operator's launch record, so it carries its own handler: stderr (the unit's journal), INFO,
    THIS logger only (propagate off — nothing else in the engine gets chattier), attached once."""
    if any(getattr(h, "_rollcall", False) for h in _log.handlers):
        return
    h = logging.StreamHandler(sys.stderr)
    h.setFormatter(logging.Formatter("%(asctime)s %(message)s", "%Y-%m-%dT%H:%M:%S"))
    setattr(h, "_rollcall", True)
    _log.addHandler(h)
    _log.setLevel(logging.INFO)
    _log.propagate = False


def _data_dir() -> Path:
    return Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or str(_ROOT / "data"))


def rss_kb() -> Optional[int]:
    """Resident set size of THIS process in KB, or None if the platform offers no cheap reading."""
    try:
        if os.name == "posix" and os.path.exists("/proc/self/statm"):
            with open("/proc/self/statm", "r", encoding="ascii") as f:
                pages = int(f.read().split()[1])
            return pages * (os.sysconf("SC_PAGE_SIZE") // 1024)
        if os.name == "nt":
            import ctypes
            import ctypes.wintypes as w

            class _PMC(ctypes.Structure):
                _fields_ = [("cb", w.DWORD), ("PageFaultCount", w.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
            # argtypes/restype are REQUIRED: without them the pseudo-handle from GetCurrentProcess is marshalled
            # as a 32-bit int and the call fails silently (measured 2026-10-08: None on the desk until declared)
            k32 = ctypes.windll.kernel32
            k32.GetCurrentProcess.restype = w.HANDLE
            f = ctypes.windll.psapi.GetProcessMemoryInfo
            f.argtypes = [w.HANDLE, ctypes.POINTER(_PMC), w.DWORD]
            f.restype = w.BOOL
            pmc = _PMC()
            pmc.cb = ctypes.sizeof(_PMC)
            if f(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
                return int(pmc.WorkingSetSize // 1024)
    except Exception:  # noqa: BLE001 — a reading we cannot take is None, never a crash and never a fake 0
        pass
    return None


def measure(label: str, fn: Callable[[], Any]) -> Dict[str, Any]:
    """Time one step and its resident-memory delta. Never raises: a failing step is recorded, not thrown —
    the boot must go on (the original warm block swallowed errors for the same reason)."""
    t0 = time.perf_counter()
    r0 = rss_kb()
    ok, err = True, None
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        ok, err = False, (type(e).__name__ + ": " + str(e))[:160]
    r1 = rss_kb()
    return {"label": label, "ms": round((time.perf_counter() - t0) * 1000.0, 1),
            "rss_kb": (r1 - r0) if (r0 is not None and r1 is not None) else None, "ok": ok, "error": err}


def checkin(extra: Optional[List[Dict[str, Any]]] = None, *, write: bool = True, log: bool = True) -> Dict[str, Any]:
    """Every subsystem checks in: import each of its modules, timed, with the resident-memory delta.

    A module the server already imported before the roll-call is marked `preloaded` — its cost was paid in the
    server's own startup and is NOT re-attributed here (an honest zero, labelled). `extra` carries the heavy
    singletons the caller measured around the warm (corpus, graph, verify deps). Every import edge is then
    priced by what it pulls in. Writes data/boot_checkin.json (box-generated; untracked) and logs one line per
    subsystem. Pure stdlib; never raises."""
    global _LAST_CHECKIN
    if log:
        _ensure_rollcall_handler()
    t_all = time.perf_counter()
    rss_start = rss_kb()
    rows: List[Dict[str, Any]] = []
    for s in SUBSYSTEMS:
        ms = 0.0
        kb = 0
        kb_known = True
        loaded_now: List[str] = []
        preloaded: List[str] = []
        missing: List[str] = []
        for m in s["modules"]:
            name = "concordance." + m
            if name in sys.modules:
                preloaded.append(m)
                continue
            t0 = time.perf_counter()
            r0 = rss_kb()
            try:
                importlib.import_module(name)
                loaded_now.append(m)
            except Exception as e:  # noqa: BLE001 — an absent piece is a finding, never a boot failure
                missing.append(f"{m}: {type(e).__name__}")
            ms += (time.perf_counter() - t0) * 1000.0
            r1 = rss_kb()
            if r0 is None or r1 is None:
                kb_known = False
            else:
                kb += max(0, r1 - r0)
        status = "absent" if missing else ("degraded" if s.get("degraded") else "ready")
        rows.append({"slug": s["slug"], "name": s["name"], "status": status, "ms": round(ms, 1),
                     "rss_kb": kb if kb_known else None, "loaded_now": loaded_now, "preloaded": preloaded,
                     "missing": missing})
    singletons = list(extra or [])
    by_slug = {r["slug"]: {"status": r["status"], "ms": r["ms"], "rss_kb": r["rss_kb"]} for r in rows}
    g = subsystem_graph()
    edges = [{**e, "pulls_ms": by_slug.get(e["to"], {}).get("ms"), "pulls_kb": by_slug.get(e["to"], {}).get("rss_kb")}
             for e in g["edges"]]
    roll_ms = round((time.perf_counter() - t_all) * 1000.0, 1)
    out: Dict[str, Any] = {
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": socket.gethostname(), "pid": os.getpid(), "python": sys.version.split()[0],
        "platform": sys.platform,
        "rollcall_ms": roll_ms,
        "singletons_ms": round(sum(float(x.get("ms") or 0) for x in singletons), 1),
        "total_ms": round(roll_ms + sum(float(x.get("ms") or 0) for x in singletons), 1),
        "rss_kb_start": rss_start, "rss_kb_process": rss_kb(),
        "ready": sum(1 for r in rows if r["status"] != "absent"), "total": len(rows),
        "absent": [r["slug"] for r in rows if r["status"] == "absent"],
        "heaviest_ms": max(rows, key=lambda r: r["ms"])["slug"] if rows else None,
        "heaviest_kb": (max((r for r in rows if r["rss_kb"] is not None), key=lambda r: r["rss_kb"], default={"slug": None})["slug"]),
        "subsystems": rows, "singletons": singletons, "by_slug": by_slug, "edges": edges,
        "note": ("the roll-call measures what boot loads beyond the server's own imports (preloaded modules cost "
                 "0 here, labelled); the heavy singletons are measured around the warm; tools/checkin.py gives each "
                 "piece's cost alone"),
    }
    if log:
        for r in rows:
            _log.info("check-in %-30s %-8s %8.1f ms %9s KB  (%d loaded now, %d preloaded%s)",
                      r["name"], r["status"], r["ms"], (r["rss_kb"] if r["rss_kb"] is not None else "?"),
                      len(r["loaded_now"]), len(r["preloaded"]),
                      ("; MISSING " + ", ".join(r["missing"])) if r["missing"] else "")
        for x in singletons:
            _log.info("check-in %-30s %-8s %8.1f ms %9s KB%s", x.get("label"), "ok" if x.get("ok") else "FAILED",
                      float(x.get("ms") or 0), (x.get("rss_kb") if x.get("rss_kb") is not None else "?"),
                      (" — " + str(x.get("error"))) if x.get("error") else "")
        _log.info("check-in: %d/%d ready, %.1f ms (roll-call %.1f + singletons %.1f), process RSS %s KB",
                  out["ready"], out["total"], out["total_ms"], roll_ms, out["singletons_ms"],
                  out["rss_kb_process"] if out["rss_kb_process"] is not None else "?")
    if write:
        try:
            d = _data_dir()
            d.mkdir(parents=True, exist_ok=True)
            p = d / "boot_checkin.json"
            tmp = p.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(out, indent=1), encoding="utf-8")
            os.replace(tmp, p)
        except Exception:  # noqa: BLE001 — the record is best-effort; the boot never depends on the disk
            pass
    _LAST_CHECKIN = out
    return out


def last_checkin() -> Optional[Dict[str, Any]]:
    """The last roll-call: this process's own if it ran one, else the last one written to disk (so a request
    process that did not boot-check — tests, a tool — still shows the last known), else None."""
    if _LAST_CHECKIN is not None:
        return _LAST_CHECKIN
    try:
        p = _data_dir() / "boot_checkin.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        pass
    return None
