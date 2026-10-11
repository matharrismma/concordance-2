"""THE ROOTS — a curated Scripture anchor for each node of reality on the one map.

The concordance of reality is keyed by the Word. Classic concordance: a word -> every verse it lives
in. One ring out: every PROVEN node — a FLOOR, a STICK, a DOMAIN — is ROOTED in the verse(s) it
answers to. This is the KEY COLUMN of a concordance entry. From it both directions read:
    root_of(node)        the LEAD    — from a node to the verse that roots it
    nodes_rooted_at(ref) the CONCORDANCE — from a verse to every node rooted in it
`cross_references` links verse<->verse; this links verse<->node. Nothing here re-derives a proof; it
only files the proofs already on the map under the Word.

An anchor is a DISCERNMENT, not a keyword hit. The operator KEEPS it (gather, don't author). The
engine SUGGESTS candidates (suggest()) from the Words-in-Red theme index, the concordance, and the
cross-references — but never commits one on its own: a forced wrong verse is worse than an open gap,
and an un-anchored node is a WANT, not a failure (a miss stays a miss). `by` records who kept it —
'proposed' (the engine offered it) vs 'operator' (confirmed by the one who keeps the keeping).

Storage: data/roots.jsonl, append-only, folded latest-wins per node (the same shape sticks.jsonl
uses); rides with the data sync. Nothing is ever overwritten in place; a re-anchor supersedes on read.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# the three kinds of reality-node the one map holds (the concordance keys every one of them)
KINDS = ("floor", "stick", "domain")


def _path(data_dir: Optional[Path] = None) -> Path:
    d = Path(data_dir) if data_dir else Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data")
    return d / "roots.jsonl"


def node_id(kind: str, raw: str) -> str:
    """The namespaced node id — 'floor:card_floor_the_capstone', 'domain:thermodynamics'. Keeping the
    kind in the key means a floor and a domain of the same name never collide."""
    kind = (kind or "").strip().lower()
    if kind not in KINDS:
        raise ValueError(f"unknown node kind {kind!r}; expected one of {KINDS}")
    return f"{kind}:{(raw or '').strip()}"


def _norm_ref(ref: str) -> str:
    """A loose normal form for matching a reference — lowercased, spaces collapsed. The real resolver
    (verifiers.scripture.resolve_ref) does canonical matching in the two-way resolver; this is the
    cheap fold key so 'Genesis 1:1' and 'genesis  1:1' are the same anchor."""
    return re.sub(r"\s+", " ", (ref or "").strip().lower())


def _append(ev: Dict[str, Any], data_dir: Optional[Path] = None) -> None:
    p = _path(data_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")


def _events(data_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    p = _path(data_dir)
    if not p.exists():
        return []
    out = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except (ValueError, TypeError):
                continue  # a torn line is skipped, never fatal (append-only logs can tear on crash)
    return out


def fold(data_dir: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """The current anchor per node — latest write wins. An anchor with no refs RETRACTS the node
    (the operator removing a bad anchor), so it folds back to un-anchored."""
    anchors: Dict[str, Dict[str, Any]] = {}
    for ev in _events(data_dir):
        node = ev.get("node")
        if not node:
            continue
        refs = [r for r in (ev.get("refs") or []) if str(r or "").strip()]
        if not refs:
            anchors.pop(node, None)  # a retraction
            continue
        anchors[node] = {"node": node, "refs": refs, "why": ev.get("why") or "",
                         "by": ev.get("by") or "operator", "at": ev.get("at")}
    return anchors


def anchor(node: str, refs: List[str], *, why: str = "", by: str = "operator",
           verify: bool = True, data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Keep a Scripture anchor for a node. `refs` are passage references ('Genesis 1:1', 'Romans 8:20-21').
    With verify=True and the Bible provisioned, each ref must RESOLVE to real Scripture or it is refused
    (never anchor a node to a verse that is not there); where the corpus is absent, the ref is stored as
    given (the seed runs where the Bible lives). An empty `refs` retracts the node's anchor."""
    node = (node or "").strip()
    if not node:
        raise ValueError("a node id is required")
    refs = [str(r).strip() for r in (refs or []) if str(r or "").strip()]
    if refs and verify:
        bad = []
        try:
            from .verifiers import scripture as _sc
            for r in refs:
                ps = _sc.read_passage(r)
                st = (ps or {}).get("status")
                if st == "source_missing":
                    bad = []  # no corpus here — store as given, verify where the Bible lives
                    break
                if not (ps or {}).get("verses"):
                    bad.append(r)
        except Exception:  # noqa: BLE001 — a verifier that cannot run does not force a false refusal
            bad = []
        if bad:
            return {"ok": False, "node": node, "refused": bad,
                    "why": "these references do not resolve to Scripture — an anchor must be a real verse"}
    ev = {"node": node, "refs": refs, "why": why, "by": by, "at": round(time.time(), 3)}
    _append(ev, data_dir)
    return {"ok": True, **({"retracted": True} if not refs else {"anchor": ev})}


def root_of(node: str, data_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """THE LEAD — the verse(s) a node is rooted in, or None if the node is still an open want."""
    return fold(data_dir).get((node or "").strip())


def nodes_rooted_at(ref: str, data_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """THE CONCORDANCE (data level) — every node whose anchor includes this reference. Loose match on
    the normal form; the two-way resolver (move 2) refines with the canonical scripture resolver so a
    chapter query gathers its verses. Found, never generated."""
    want = _norm_ref(ref)
    if not want:
        return []
    out = []
    for a in fold(data_dir).values():
        if any(_norm_ref(r) == want for r in a["refs"]):
            out.append(a)
    return sorted(out, key=lambda a: a["node"])


def _universe(data_dir: Optional[Path] = None) -> Dict[str, List[str]]:
    """Every reality-node the one map holds, by kind — the denominator of coverage. Each source is
    read where it lives: the floors from the registry (code), the sticks and domains from the data."""
    uni: Dict[str, List[str]] = {"floor": [], "stick": [], "domain": []}
    try:
        from . import chains
        uni["floor"] = [node_id("floor", f) for f in chains.FLOORS]
    except Exception:  # noqa: BLE001
        pass
    try:
        from . import tickstick
        uni["stick"] = [node_id("stick", r["id"]) for r in tickstick.listing(data_dir)["sticks"]]
    except Exception:  # noqa: BLE001
        pass
    try:
        d = Path(data_dir) if data_dir else Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data")
        g = json.loads((d / "domain_goldens.json").read_text(encoding="utf-8"))
        uni["domain"] = [node_id("domain", k) for k in (g.keys() if isinstance(g, dict) else g)]
    except Exception:  # noqa: BLE001
        pass
    return uni


def coverage(data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """The measured gap — how much of reality is rooted in the Word, by kind, with the open nodes named
    (every open node is a WANT for the operator's discernment). Also the share kept by 'operator' vs
    merely 'proposed' by the engine, so a proposed anchor is never mistaken for a confirmed one."""
    uni = _universe(data_dir)
    anchored = fold(data_dir)
    by_counts = {"operator": 0, "proposed": 0, "other": 0}
    for a in anchored.values():
        b = a.get("by")
        by_counts[b if b in ("operator", "proposed") else "other"] += 1
    kinds = {}
    total = rooted = 0
    for k in KINDS:
        nodes = uni.get(k, [])
        have = [n for n in nodes if n in anchored]
        openn = [n for n in nodes if n not in anchored]
        kinds[k] = {"total": len(nodes), "anchored": len(have), "open": openn}
        total += len(nodes)
        rooted += len(have)
    return {"total_nodes": total, "anchored": rooted,
            "pct": round(100.0 * rooted / total, 1) if total else 0.0,
            "kept_by": by_counts, "by_kind": kinds,
            "note": ("Each open node is a want — a piece of reality not yet rooted in the Word. An anchor "
                     "is the operator's discernment; the engine only suggests (roots.suggest).")}


# ── PLACEMENTS — a light taxonomy edge: a node is FILED UNDER the floor whose subject it shares ───────
# Inheritance needs only the floor, not a per-mark basis, so a node too far from the map to chart (an
# uncharted stick, an unmapped domain) can still be FILED under its floor by subject — a categorization
# the operator keeps, not a proof the engine forges. data/placements.jsonl, append-only/folded like the
# anchors; an empty floor retracts. Marked `by` ('proposed' vs 'operator'). resolve() reads it last, so a
# real chart or a name-match always wins over a filing.
def _pl_path(data_dir: Optional[Path] = None) -> Path:
    d = Path(data_dir) if data_dir else Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data")
    return d / "placements.jsonl"


def placements_fold(data_dir: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """The current floor a node is filed under — latest write wins; an empty floor retracts."""
    out: Dict[str, Dict[str, Any]] = {}
    p = _pl_path(data_dir)
    if not p.exists():
        return out
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except (ValueError, TypeError):
                continue
            node = ev.get("node")
            if not node:
                continue
            floor = str(ev.get("floor") or "").strip()
            if not floor:
                out.pop(node, None)
                continue
            out[node] = {"node": node, "floor": floor, "why": ev.get("why") or "",
                         "by": ev.get("by") or "operator", "at": ev.get("at")}
    return out


def place(node: str, floor: str, *, why: str = "", by: str = "operator",
          verify: bool = True, data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """File a node under a floor (a taxonomy edge for inheritance). With verify=True the floor must be a
    real floor on the one map, or it is refused. An empty floor retracts the filing."""
    node = (node or "").strip()
    floor = (floor or "").strip()
    if not node:
        raise ValueError("a node id is required")
    if floor and verify and floor not in _floors_set():
        return {"ok": False, "node": node, "refused": floor,
                "why": "not a floor on the one map — a filing must point at a real floor"}
    ev = {"node": node, "floor": floor, "why": why, "by": by, "at": round(time.time(), 3)}
    p = _pl_path(data_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return {"ok": True, **({"retracted": True} if not floor else {"placement": ev})}


# ── INHERITANCE (move 2) — a node not directly anchored inherits the root of the floor it sits on ─────
# The one map already holds the edges; this only reads them. Three ways a node reaches a floor, strongest
# edge first: a STICK is CHARTED onto a node of the map (the `charts` bridge, tools/seed_charts.py); a
# DOMAIN corresponds to its floor by name (card_floor_<domain>); a FLOOR stands on the floors it BUILDS_ON.
# Inheritance is marked by='inherited' with the floor it came through, never mistaken for a kept anchor; a
# node that reaches no anchored floor stays a WANT (an uncharted stick / unmapped domain cannot inherit).
_SPINE = "card_spine_charts"


def _floors_set() -> set:
    try:
        from . import chains
        return set(chains.FLOORS)
    except Exception:  # noqa: BLE001
        return set()


def _to_floor(nid: Optional[str], get_card, floors: set, depth: int = 0) -> Optional[str]:
    """Walk from a map node up to the floor it belongs to, bounded; the charted node may be a question
    or a joint under a floor, not the floor itself."""
    if not nid or depth > 5:
        return None
    if nid in floors:
        return nid
    for conn in ((get_card(nid) or {}).get("connections") or []):
        if conn.get("relationship") in ("part_of", "open_end_of", "builds_on", "member_of", "enables"):
            f = _to_floor(conn.get("to_card_id"), get_card, floors, depth + 1)
            if f:
                return f
    return None


def stick_floor_index(get_card=None) -> Dict[str, str]:
    """{stick_id -> floor_id} read from the corpus: the charts spine lists every chart card; each names
    its stick (source.ref) and the node it charts (the `charts` edge), walked up to its floor."""
    from . import corpus
    gc = get_card or corpus.get_card
    floors = _floors_set()
    idx: Dict[str, str] = {}
    spine = gc(_SPINE) or {}
    charts = [c.get("to_card_id") for c in (spine.get("connections") or [])
              if str(c.get("to_card_id") or "").startswith("card_chart_")]
    for chid in charts:
        ch = gc(chid) or {}
        stick = str((ch.get("source") or {}).get("ref") or "").strip()
        target = next((c.get("to_card_id") for c in (ch.get("connections") or [])
                       if c.get("relationship") == "charts"), None)
        fl = _to_floor(target, gc, floors)
        if stick and fl:
            idx[stick] = fl
    return idx


def _floor_of(node: str, get_card, floors: set, stick_index: Optional[Dict[str, str]],
              placements: Optional[Dict[str, str]] = None) -> List[str]:
    """The floor id(s) a node sits on, for inheritance — strongest edge first, a taxonomy FILING last."""
    out: List[str] = []
    kind, _, raw = (node or "").partition(":")
    if kind == "domain":
        cand = f"card_floor_{raw}"
        if cand in floors:
            out.append(cand)
    elif kind == "stick":
        fl = (stick_index or {}).get(raw)
        if fl:
            out.append(fl)
    elif kind == "floor":
        out += [conn.get("to_card_id") for conn in ((get_card(raw) or {}).get("connections") or [])
                if conn.get("relationship") in ("builds_on", "part_of") and conn.get("to_card_id") in floors]
    placed = (placements or {}).get(node)      # the filing — last, so a real edge always wins
    if placed and placed in floors and placed not in out:
        out.append(placed)
    return out


def resolve(node: str, *, get_card=None, stick_index: Optional[Dict[str, str]] = None,
            placements: Optional[Dict[str, str]] = None, data_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """A node's root — DIRECT or INHERITED. A direct anchor wins; else the node inherits the anchor of
    the floor it sits on (the lead through the map, or the floor it is filed under). {node, refs, why, by,
    via, through} or None when the node reaches no anchored floor (still a want)."""
    node = (node or "").strip()
    direct = root_of(node, data_dir)
    if direct:
        return {**direct, "via": "direct"}
    from . import corpus
    gc = get_card or corpus.get_card
    floors = _floors_set()
    if stick_index is None and node.startswith("stick:"):
        stick_index = stick_floor_index(gc)
    if placements is None:
        placements = {n: r["floor"] for n, r in placements_fold(data_dir).items()}
    for fl in _floor_of(node, gc, floors, stick_index, placements):
        fa = root_of(node_id("floor", fl), data_dir)
        if fa:
            return {"node": node, "refs": fa["refs"], "why": fa["why"], "by": "inherited",
                    "via": "inherited", "through": node_id("floor", fl)}
    return None


def resolved_coverage(get_card=None, data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Coverage WITH inheritance — how much of reality the Word reaches once a node may inherit its
    floor's root. Direct vs inherited vs still-open by kind, and the connectivity gap named: the nodes
    that reach no floor at all (unconnected) are the deeper want — connect them to the map, then root."""
    from . import corpus
    gc = get_card or corpus.get_card
    uni = _universe(data_dir)
    si = stick_floor_index(gc)
    pl = {n: r["floor"] for n, r in placements_fold(data_dir).items()}
    floors = _floors_set()
    out: Dict[str, Any] = {}
    agg = {"total": 0, "direct": 0, "inherited": 0, "open": 0, "unconnected": 0}
    for k in KINDS:
        row = {"total": 0, "direct": 0, "inherited": 0, "open": 0, "unconnected": 0}
        for n in uni.get(k, []):
            row["total"] += 1
            r = resolve(n, get_card=gc, stick_index=si, placements=pl, data_dir=data_dir)
            if r and r["via"] == "direct":
                row["direct"] += 1
            elif r:
                row["inherited"] += 1
            else:
                row["open"] += 1
                # "unconnected" is the inherit-dependent want: a stick/domain that reaches no floor at
                # all. An open FLOOR is root-level — its fix is a direct anchor, not map-connecting.
                if k != "floor" and not _floor_of(n, gc, floors, si, pl):
                    row["unconnected"] += 1
        out[k] = row
        for key in agg:
            agg[key] += row[key]
    resolved = agg["direct"] + agg["inherited"]
    return {"total_nodes": agg["total"], "resolved": resolved,
            "pct": round(100.0 * resolved / agg["total"], 1) if agg["total"] else 0.0,
            "direct": agg["direct"], "inherited": agg["inherited"],
            "open": agg["open"], "unconnected": agg["unconnected"], "by_kind": out,
            "note": ("A node inherits its floor's root through the map. The open nodes that reach no floor "
                     "at all (unconnected) are the deeper want: an uncharted stick or an unmapped domain "
                     "must first be connected to the map before it can be rooted in the Word.")}


def _title_of(node: str, kind: str, get_card, stick_titles: Dict[str, str]) -> str:
    raw = node.split(":", 1)[1] if ":" in node else node
    if kind == "domain":
        return raw.replace("_", " ")
    if kind == "stick":
        return stick_titles.get(node, raw.replace("stick_", "").replace("_", " "))
    c = get_card(raw) or {}
    return c.get("title") or raw.replace("card_floor_", "").replace("_", " ")


def confirmations(ref: str, *, get_card=None, data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """THE CONCORDANCE for a verse — every reality-node rooted in it, DIRECTLY or by inheritance. The
    outward direction: a verse of Scripture -> every place in the keeping's map of reality that answers
    to it, each with how it is rooted (direct / inherited, and through which floor). Found, never
    generated. {verse, count, nodes:[{node, kind, title, via, through}]}."""
    want = _norm_ref(ref)
    if not want:
        return {"verse": ref, "count": 0, "nodes": []}
    from . import corpus
    gc = get_card or corpus.get_card
    si = stick_floor_index(gc)
    pl = {n: r["floor"] for n, r in placements_fold(data_dir).items()}
    uni = _universe(data_dir)
    stick_titles: Dict[str, str] = {}
    try:
        from . import tickstick
        stick_titles = {("stick:" + r["id"]): (r.get("question") or r["id"])
                        for r in tickstick.listing(data_dir)["sticks"]}
    except Exception:  # noqa: BLE001
        pass
    out: List[Dict[str, Any]] = []
    for k in KINDS:
        for n in uni.get(k, []):
            r = resolve(n, get_card=gc, stick_index=si, placements=pl, data_dir=data_dir)
            if r and any(_norm_ref(x) == want for x in r["refs"]):
                out.append({"node": n, "kind": k, "title": _title_of(n, k, gc, stick_titles),
                            "via": r["via"], "through": r.get("through")})
    out.sort(key=lambda d: (0 if d["via"] == "direct" else 1, d["kind"], d["title"].lower()))
    return {"verse": ref, "count": len(out), "nodes": out}


def entry(ref: str, *, get_card=None, data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """THE UNIFIED CONCORDANCE ENTRY — a verse and everything the keeping ties to it, in one view:
    the TEXT, its CONFIRMATIONS in reality (the roots — the new connection), its CROSS-REFERENCES (TSK),
    its ORIGINAL WORDS (Strong's), and the COMMENTARY. The concordance of reality woven into the
    concordance of Scripture, keyed by the Word. Found, never generated — each dimension is a real,
    cited public-domain source; a dimension the keeping cannot reach is honestly null, never invented."""
    ref = (ref or "").strip()
    out: Dict[str, Any] = {"verse": ref}
    try:
        from .verifiers import scripture as sc
    except Exception:  # noqa: BLE001
        sc = None
    try:
        ps = sc.read_passage(ref) if sc else {}
        out["text"] = {"ref": ps.get("ref") or ref,
                       "verses": [{"verse": v.get("verse"), "text": v.get("text")}
                                  for v in (ps.get("verses") or [])][:12]}
    except Exception:  # noqa: BLE001
        out["text"] = None
    try:
        c = confirmations(ref, get_card=get_card, data_dir=data_dir)
        out["reality"] = {"count": c["count"], "nodes": c["nodes"][:12]}
    except Exception:  # noqa: BLE001
        out["reality"] = {"count": 0, "nodes": []}
    try:
        from . import xrefs
        xr = xrefs.for_ref(ref, limit=12)
        out["cross_references"] = {"source": "Treasury of Scripture Knowledge",
                                   "refs": [r["ref"] for r in (xr.get("cross_references") or [])]}
    except Exception:  # noqa: BLE001
        out["cross_references"] = None
    try:
        from . import translate as _tr
    except Exception:  # noqa: BLE001
        _tr = None
    try:
        ow = sc.original_words(ref) if sc else {}
        ws = ow.get("words") or []
        tongue = "Greek" if (ws and str(ws[0].get("strongs", "")).startswith("G")) else ("Hebrew" if ws else None)
        words = []
        for w in ws[:60]:
            s = w.get("strongs")
            # WHERE THERE IS DOUBT, DON'T CONVERT — a word better left in the tongue is marked, and its
            # definition is carried so the reader keeps the actual word instead of a lossy single gloss.
            irr = (_tr.irreducible(s) if (_tr and s) else None)
            words.append({"word": w.get("word"), "strongs": s, "doubt": bool(irr),
                          "translit": (irr or {}).get("translit"),
                          "definition": (((irr.get("definition") or "")[:220]) or None) if irr else None})
        out["original_words"] = {"tongue": tongue, "words": words} if words else None
    except Exception:  # noqa: BLE001
        out["original_words"] = None
    try:
        from . import commentary
        cm = commentary.for_ref(ref)
        txt = ""
        for b in (cm.get("commentary") or []):
            txt = b.get("text") or b.get("body") or b.get("comment") or ""
            if txt:
                break
        out["commentary"] = {"source": cm.get("attribution"), "text": txt[:900]} if txt else None
    except Exception:  # noqa: BLE001
        out["commentary"] = None
    # SERMONS & THE CLOUD — the witnesses whose own words frame this passage (Spurgeon's sermons, et al.),
    # verbatim and attributed, public domain. Connect to the texts we hold. Proposes, never confirms.
    try:
        from . import witness as _wit
        vtext = " ".join(v.get("text", "") for v in ((out.get("text") or {}).get("verses") or [])) or ref
        seen = (_wit.see(vtext, k=2) or {}).get("seeing") or []
        out["sermons"] = [{"who": s.get("witness"), "work": s.get("work"), "text": (s.get("text") or "")[:460]}
                          for s in seen if str(s.get("text") or "").strip()] or None
    except Exception:  # noqa: BLE001
        out["sermons"] = None
    return out


def suggest(text: str, k: int = 3) -> Dict[str, Any]:
    """OFFER candidate anchors for a node from what the keeping already holds — the Words-in-Red theme
    index first (Christ's own teaching on the matter), then the concordance (a key term -> its verse),
    then the cross-references of those. A SUGGESTION, never a commit: the operator reads and keeps.
    Found, never generated — every candidate is a real verse the engine can already cite."""
    text = (text or "").strip()
    cands: List[Dict[str, str]] = []
    seen = set()

    def _add(ref, why):
        ref = (ref or "").strip()
        if ref and ref.lower() not in seen:
            seen.add(ref.lower())
            cands.append({"ref": ref, "why": why})

    try:
        from . import teachings
        red = teachings.for_topic(text)
        if red and str(red.get("ref") or "").strip():
            _add(red["ref"], f"the Words in Red on this: {red.get('title') or 'a teaching of Christ'}")
    except Exception:  # noqa: BLE001
        pass
    try:
        from .verifiers import scripture as _sc
        for term in sorted(set(re.findall(r"[A-Za-z]{4,}", text)), key=len, reverse=True)[:4]:
            r = _sc.for_word(term)
            if r.get("status") == "ok" and str(r.get("ref") or "").strip():
                _add(r["ref"], f"the concordance home of '{term}'")
            if len(cands) >= k:
                break
    except Exception:  # noqa: BLE001
        pass
    return {"text": text, "candidates": cands[:k],
            "note": "suggestions only — a real verse each, offered for the operator to keep or refuse; "
                    "an anchor is discernment, not a keyword hit."}
