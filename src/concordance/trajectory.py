"""THE TRAJECTORY OF A PATH — measure what works, honestly, so the path narrows with use.

Matt, 2026-10-06: *"Success guides. We focus on what works. Success dictates future paths. Failure allows
us to better define parameters and the path narrows for future use."* And: *"We need a good method to
measure the trajectory of each path."*

A PATH is any named choice the engine can reuse — a tool, a technique, a strategy, a biblical type, or a
whole discerned route. Each USE of a path has an OUTCOME: success or failure. This measures the path's
trajectory from its outcomes, with real statistics, not a made-up score:

  * rate        — the raw success fraction s/n.
  * floor       — the WILSON score lower bound: a CONSERVATIVE success rate that accounts for how little
                  evidence there is. 3/3 scores lower than 30/30; success must be EARNED by repetition.
                  This is the honest "success dictates future paths" ranking value, and it RISES toward the
                  rate as n grows — the path narrows for future use.
  * width       — the Wilson interval width, which shrinks like 1/sqrt(n): literally how narrow the path is.
  * trend       — an EWMA of recent outcomes vs the overall rate: the DIRECTION (improving / steady /
                  declining) and the drift. The "is the group walking off the target" watch, per path.

The guard (so success cannot be self-graded): a SUCCESS is recorded only with a witness — a HOLDS seal in
this node's keeping, or a named external witness (the BROTHERS gate). A FAILURE is recorded freely; a miss
is cheap to keep and it is the thing that narrows the path. Found, never generated; outcomes ride the sync.
"""
from __future__ import annotations

import json
import math
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

_Z = {0.90: 1.6448536269514722, 0.95: 1.959963984540054, 0.99: 2.575829303548901}


def _path(data_dir: Optional[Path] = None) -> Path:
    d = Path(data_dir) if data_dir else Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data")
    return d / "path_outcomes.jsonl"


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")[:80]


def wilson(s: int, n: int, confidence: float = 0.95):
    """The Wilson score interval (lower, centre, upper) for s successes in n trials. The lower bound is the
    conservative, evidence-weighted success rate; the width shrinks like 1/sqrt(n)."""
    if n <= 0:
        return 0.0, 0.0, 1.0
    z = _Z.get(round(confidence, 2), 1.959963984540054)
    p = s / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return max(0.0, centre - half), centre, min(1.0, centre + half)


def _events(data_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    p = _path(data_dir)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def _lineage(data_dir: Optional[Path] = None) -> Dict[str, str]:
    """path -> parent, from the first lineage event for each path (set once)."""
    out: Dict[str, str] = {}
    for e in _events(data_dir):
        if e.get("event") == "lineage" and e.get("path") and e.get("path") not in out:
            out[e["path"]] = e.get("parent")
    return out


def _parent_of(pid: str, data_dir: Optional[Path] = None) -> Optional[str]:
    """The path this one BUILDS ON (its coaching-tree parent), if declared — fixed once set."""
    return _lineage(data_dir).get(pid)


def _ancestors(pid: str, data_dir: Optional[Path] = None) -> List[str]:
    """The chain of paths this one builds on, parent-first (cycle- and depth-guarded)."""
    lin = _lineage(data_dir)
    out: List[str] = []
    cur = lin.get(pid)
    seen = {pid}
    while cur and cur not in seen and len(out) < 32:
        out.append(cur); seen.add(cur); cur = lin.get(cur)
    return out


def _children(pid: str, data_dir: Optional[Path] = None) -> List[str]:
    return sorted(p for p, par in _lineage(data_dir).items() if par == pid)


def record(path: str, success: bool, *, seal: str = "", witness: str = "", note: str = "",
           parent: str = "", data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Record one outcome of a path. A SUCCESS needs a witness — a HOLDS seal in this keeping, or a named
    external witness — so success is never self-graded. A FAILURE is recorded freely (it narrows the path).
    `parent` declares the path this one BUILDS ON (the coaching tree): it inherits the parent's floor as its
    starting standard, and its own outcomes move its branch up or down from there. Set once."""
    pid = _slug(path)
    if not pid:
        return {"ok": False, "error": "a path name is required"}
    par = _slug(parent)
    if par and par != pid and _parent_of(pid, data_dir) is None:
        if par in _ancestors(pid, data_dir):   # (pid has no parent yet, so this only guards an obvious self-loop)
            return {"ok": False, "error": "a path cannot build on itself"}
        p = _path(data_dir)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps({"event": "lineage", "path": pid, "parent": par, "at": int(time.time())},
                               ensure_ascii=False) + "\n")
    success = bool(success)
    seal = (seal or "").strip().lower()
    witness = (witness or "").strip()
    if success:
        sealed_ok = bool(re.fullmatch(r"[0-9a-f]{64}", seal))
        if sealed_ok:
            from . import tickstick
            if tickstick._seal_holds(seal, data_dir) is None:
                return {"ok": False, "error": f"seal {seal[:12]}… is not a HOLDS verification in this keeping"}
        if not sealed_ok and len(witness) < 3:
            return {"ok": False, "error": "a SUCCESS needs a witness: a 64-hex HOLDS seal, or a named "
                                          "external witness — success is never self-graded"}
    ev = {"event": "outcome", "path": pid, "success": success, "seal": seal, "witness": witness[:120],
          "note": (note or "")[:300], "at": int(time.time())}
    p = _path(data_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return {"ok": True, "path": pid, "recorded": {"success": success}, "trajectory": measure(pid, data_dir=data_dir)}


_INHERIT = 6          # the weight (in equivalent observations) of the floor a microposition inherits


def _rate_of(pid: str, data_dir: Optional[Path], _depth: int = 0):
    """(successes, trials) recorded directly for a path."""
    evs = [e for e in _events(data_dir) if e.get("event") == "outcome" and e.get("path") == pid]
    s = sum(1 for e in evs if e.get("success"))
    return s, len(evs)


def measure(path: str, *, confidence: float = 0.95, alpha: float = 0.3,
            data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """The trajectory of one path, as a coaching tree: the conservative success FLOOR (Wilson), inherited
    from the path it builds on (a microposition starts at its parent's floor — the new floor — and its own
    outcomes move its branch up or down from there), how narrow it is (interval width), and the trend
    (EWMA direction). Success guides, failure narrows; the floor rises each generation."""
    pid = _slug(path)
    evs = [e for e in _events(data_dir) if e.get("event") == "outcome" and e.get("path") == pid]
    evs.sort(key=lambda e: e.get("at", 0))
    n = len(evs)
    parent = _parent_of(pid, data_dir)
    generation = len(_ancestors(pid, data_dir))

    # INHERITANCE — a microposition starts at the floor of the position it refines. The parent's own rate
    # enters as a prior of _INHERIT equivalent observations; the branch's own outcomes then dominate.
    prior_s = prior_n = 0.0
    parent_floor = None
    if parent:
        ps, pn = _rate_of(parent, data_dir)
        if pn > 0:
            p_parent = ps / pn
            prior_s, prior_n = p_parent * _INHERIT, float(_INHERIT)
            parent_floor = round(wilson(ps, pn, confidence)[0], 4)

    if n == 0 and prior_n == 0:
        return {"path": pid, "n": 0, "parent": parent, "generation": generation,
                "detail": "a new path with no outcomes and no inherited floor yet"}

    outcomes = [1 if e.get("success") else 0 for e in evs]
    s = sum(outcomes)
    rate = (s / n) if n else None
    own_lb = round(wilson(s, n, confidence)[0], 4) if n else None
    # the effective (inherited) floor: own outcomes + the inherited prior
    eff_s, eff_n = s + prior_s, n + prior_n
    lb, centre, ub = wilson(eff_s, eff_n, confidence)
    # EWMA of the path's OWN outcomes (recent-weighted) — the direction THIS branch is heading
    if outcomes:
        ewma = outcomes[0]
        for x in outcomes[1:]:
            ewma = alpha * x + (1 - alpha) * ewma
    else:
        ewma = centre
    base = rate if rate is not None else centre
    drift = ewma - base
    direction = "improving" if drift > 0.05 else ("declining" if drift < -0.05 else "steady")
    verdict = ("proven" if (lb >= 0.70 and n >= 5) else
               "failing" if ((rate is not None and rate < 0.5) or (direction == "declining" and n >= 5)) else
               "promising" if lb >= 0.55 else "provisional")
    return {"path": pid, "n": n, "successes": s, "failures": n - s,
            "parent": parent, "generation": generation, "inherited_floor": parent_floor,
            "rate": round(rate, 4) if rate is not None else None, "own_floor": own_lb,
            "floor": round(lb, 4), "ceiling": round(ub, 4), "width": round(ub - lb, 4),
            "ewma": round(ewma, 4), "drift": round(drift, 4), "direction": direction, "verdict": verdict,
            "confidence": confidence,
            "means": ("floor is the Wilson lower bound on own outcomes PLUS the inherited floor of the "
                      "position this refines (a microposition starts at its parent's standard); width "
                      "shrinks like 1/sqrt(n) — the path narrowing; direction is the branch's EWMA trend. "
                      "Success guides, failure narrows, the floor rises each generation.")}


def rank(paths: List[str], *, data_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Order paths by the conservative floor (success dictates the path, earned by evidence)."""
    rows = [measure(p, data_dir=data_dir) for p in paths]
    rows = [r for r in rows if r.get("floor") is not None]
    rows.sort(key=lambda r: (-r.get("floor", 0.0), -r.get("n", 0)))
    return rows


# A UNIT is a coaching tree: a root standard and everything that builds on it. Each unit is balanced to a
# bounded set of positions. The cap is 144,000 (Rev 7:4, 14:1 — the sealed, a complete set): a deliberate
# design target per unit, stated as such, not a law read out of the number.
MAX_POSITIONS_PER_UNIT = 144_000


def _root(pid: str, data_dir: Optional[Path] = None) -> str:
    anc = _ancestors(pid, data_dir)
    return anc[-1] if anc else _slug(pid)


def _unit_members(root: str, data_dir: Optional[Path] = None) -> List[str]:
    root = _slug(root)
    seen = [root]; i = 0
    while i < len(seen) and len(seen) < 200_000:
        for c in _children(seen[i], data_dir):
            if c not in seen:
                seen.append(c)
        i += 1
    return seen


def standard(unit: str, *, min_n: int = 3, data_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """The current floor-setter of a unit: the member with the highest proven floor — the standard the next
    generation inherits (the Saban of this tree)."""
    rows = [measure(m, data_dir=data_dir) for m in _unit_members(_root(unit, data_dir), data_dir)]
    rows = [r for r in rows if r.get("floor") is not None and r.get("n", 0) >= min_n]
    if not rows:
        return None
    rows.sort(key=lambda r: (-r["floor"], -r["n"]))
    return rows[0]


def tree(unit: str, *, data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """The coaching tree of a unit: the root standard and every branch with its floor and direction."""
    root = _root(unit, data_dir)
    members = _unit_members(root, data_dir)
    rows = [measure(m, data_dir=data_dir) for m in members]
    nodes = [{"path": r["path"], "parent": r.get("parent"), "generation": r.get("generation"),
              "floor": r.get("floor"), "direction": r.get("direction"), "n": r.get("n"),
              "verdict": r.get("verdict")} for r in rows]
    nodes.sort(key=lambda z: (z.get("generation") or 0, -(z.get("floor") or 0)))
    std = standard(root, data_dir=data_dir)
    return {"unit": root, "positions": len(members), "standard": (std or {}).get("path"),
            "standard_floor": (std or {}).get("floor"), "nodes": nodes}


def downline_value(path: str, *, data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """The value a path has created DOWNLINE — the mission's measure (Matt, 2026-10-06: 'we judge ourselves
    on their success and the value they create downline'). A node's value is its own witnessed fruit (sealed
    or witnessed successes) PLUS the fruit of every branch that builds on it: the multiplication, each one
    served becoming one sent. The engine is the coach; its self-judgment is the total fruit of the tree."""
    root = _slug(path)
    succ: Dict[str, int] = {}
    children: Dict[str, List[str]] = {}
    for e in _events(data_dir):
        if e.get("event") == "outcome" and e.get("success"):
            succ[e["path"]] = succ.get(e["path"], 0) + 1
        elif e.get("event") == "lineage" and e.get("path") and e.get("parent"):
            children.setdefault(e["parent"], []).append(e["path"])

    def rec(pid: str, seen: set):
        if pid in seen:
            return 0, 0
        seen.add(pid)
        own = succ.get(pid, 0)
        down, desc = own, 0
        for c in sorted(set(children.get(pid, []))):
            d, td = rec(c, seen)
            down += d
            desc += 1 + td
        return down, desc

    down, desc = rec(root, set())
    return {"path": root, "own_fruit": succ.get(root, 0), "direct_branches": len(set(children.get(root, []))),
            "total_descendants": desc, "downline_fruit": down,
            "means": ("own witnessed fruit + the fruit of every branch that builds on this — the value "
                      "created downline. The coach is judged by the harvest of the whole line, not its own.")}


def fruit(path: str, *, data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Judge by the fruit (Matthew 7:16-20; John 15:1-8). Two questions, not one: DOES it produce fruit,
    and IS the fruit good? Bearing = fruit exists down the line; good = the fruit is high-quality (a strong
    floor), WITNESSED (never self-graded), and not declining. A branch that bears no fruit is taken away
    (John 15:2); a branch that bears corrupt fruit is cut down (Matt 7:19); a branch that bears good fruit
    is kept and pruned to bear MORE (John 15:2). The engine is judged by this, and judges itself by it."""
    dv = downline_value(path, data_dir=data_dir)
    m = measure(path, data_dir=data_dir)
    bears = dv["downline_fruit"] > 0
    floor = m.get("floor")
    good = bool(bears and (floor is not None and floor >= 0.5)
                and m.get("direction") != "declining" and m.get("verdict") != "failing")
    verdict = "barren" if not bears else ("good" if good else "corrupt")
    frame = {"barren": "bears no fruit — taken away (John 15:2)",
             "good": "good fruit — kept, and pruned to bear more (John 15:2)",
             "corrupt": "it bears, but not good fruit — examined, and if it stays corrupt, cut down (Matt 7:19)"
             }[verdict]
    return {"path": _slug(path), "produces_fruit": bears, "fruit_is_good": good, "verdict": verdict,
            "own_fruit": dv["own_fruit"], "downline_fruit": dv["downline_fruit"],
            "total_descendants": dv["total_descendants"], "floor": floor, "direction": m.get("direction"),
            "frame": frame,
            "means": ("by their fruits ye shall know them (Matt 7:16): the measure is bearing AND goodness. "
                      "Good fruit is witnessed (never self-graded), stands on a strong floor, and is not "
                      "declining — and the only fruit that finally counts is what flows down the whole line.")}


def balance(unit: str, *, max_positions: int = MAX_POSITIONS_PER_UNIT,
            data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Continuously balance a unit toward a bounded set of positions (default 144,000 per unit). Reports the
    count, the standard, and — when over capacity — the WEAKEST positions (lowest floor) to prune or merge,
    so the strong are kept and the floor keeps rising. Reports the prune set; it does not delete on its own."""
    root = _root(unit, data_dir)
    rows = [measure(m, data_dir=data_dir) for m in _unit_members(root, data_dir)]
    ranked = sorted(rows, key=lambda r: (r.get("floor") if r.get("floor") is not None else -1.0,
                                         r.get("n", 0)))     # weakest first
    count = len(rows)
    over = max(0, count - int(max_positions))
    prune = [{"path": r["path"], "floor": r.get("floor"), "n": r.get("n"), "verdict": r.get("verdict")}
             for r in ranked[:over]] if over else []
    std = standard(root, data_dir=data_dir)
    return {"unit": root, "positions": count, "max_positions": int(max_positions),
            "status": "over_capacity" if over else "balanced", "over_by": over,
            "headroom": max(0, int(max_positions) - count),
            "standard": (std or {}).get("path"), "standard_floor": (std or {}).get("floor"),
            "prune_candidates": prune,
            "means": ("a unit is a coaching tree (a root standard + its branches). Balance keeps it bounded "
                      "(144,000 positions per unit, Rev 7:4 — a chosen complete set): when over, the weakest "
                      "by floor are named to prune or merge, so the strong stay and the floor rises.")}
