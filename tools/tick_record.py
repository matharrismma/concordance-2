#!/usr/bin/env python3
"""TICK RECORD — replay a tick.py stick function through instrumented helpers and write it as DATA (issue #13).

    PYTHONPATH=src python tools/tick_record.py [OUT_DIR] [name ...]     # default OUT_DIR = data/sticks

The data files are never transcribed by hand: each function RUNS in a fresh temp keeping with `_rh_seal_num`,
`_seal_through`, `tickstick.create` and `_mint_marks` wrapped to RECORD their arguments, and the recording is
written as data/sticks/<name>.json for the loader (concordance.sticks). A function that does its own
computation — calls verify_derivation or tickstick.tick itself, takes a CLI argument, reads a table — is
written as a HANDLER entry (aliases + the Python function's name) and stays Python.

`parse_dispatch` reads the if-chain of tick.main() so the aliases carry over with FIRST-MATCH semantics: an
alias two branches claimed reached only the first (the silent collision), so it is written to the first and
reported here; the loader then refuses any duplicate at load time.
"""
from __future__ import annotations

import ast
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
os.environ["CONCORDANCE_SEAL_INDEX"] = "0"
os.environ.setdefault("CONCORDANCE_VERIFY_TIMEOUT_S", "1800")
os.environ.setdefault("CONCORDANCE_RIEMANN_MAX", "1e9")
os.environ.setdefault("WEB_FIND_DISABLED", "1")

SCHEMA = 1
MARK_KW = {"seal", "source", "up_to", "unit"}

# CLI parameters of the handlers that take one, exactly as tick.main() parsed them.
HANDLER_PARAMS = {
    "riemann": [{"type": "float", "default": 100.0}],
    "riemann_li": [{"type": "int", "default": 30}],
    "robin": [{"type": "int", "default": 1000000}],
    "schoenfeld": [{"type": "int", "default": 2000000}],
    "lagarias": [{"type": "int", "default": 1000000}],
    "nicolas": [{"type": "int", "default": 1000000}],
    "count": [{"type": "float", "default": 1000000000.0}],
    "bsd": [{"type": "str", "default": "11a1"}],
}
# main() special-cased `bsd all`; the wrapper keeps that.
HANDLER_RENAME = {"bsd": "bsd_cli"}


def entry_name(func_name: str) -> str:
    n = func_name
    if n.startswith("stick_"):
        n = n[len("stick_"):]
    if n.endswith("_stick"):
        n = n[: -len("_stick")]
    return n


def _aliases_of(test: ast.expr):
    """The alias tuple of an `a[0] == "x"` / `a[0] in (...)` test, else None."""
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return None
    left = test.left
    if not (isinstance(left, ast.Subscript) and isinstance(left.value, ast.Name) and left.value.id == "a"):
        return None
    op, right = test.ops[0], test.comparators[0]
    if isinstance(op, ast.Eq) and isinstance(right, ast.Constant) and isinstance(right.value, str):
        return [right.value]
    if isinstance(op, ast.In) and isinstance(right, (ast.Tuple, ast.List)):
        vals = [e.value for e in right.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        if len(vals) == len(right.elts):
            return vals
    return None


def _called_function(body) -> str | None:
    """The module function a branch returns into (`return fn(...)`), else None."""
    for node in body:
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
            return node.value.func.id
        if isinstance(node, ast.If):
            # `bsd`: an inner `if all` then `return bsd(...)`
            inner = _called_function(node.body) or _called_function(node.orelse)
            if inner:
                return inner
    return None


def parse_dispatch(src: str):
    """[(function_name, aliases)] in main()'s order, first-match: an alias claimed earlier is dropped from
    the later branch (it never reached it). Branches that are inline commands (window/read/retract) are
    skipped. Also returns, via parse_dispatch.shadowed, the dropped (alias, first, later) triples."""
    tree = ast.parse(src)
    defs = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    claimed: dict = {}
    order: list = []
    byfn: dict = {}
    shadowed: list = []
    for node in main.body:
        if not isinstance(node, ast.If):
            continue
        aliases = _aliases_of(node.test)
        if not aliases:
            continue
        fn = _called_function(node.body)
        if fn is None or fn not in defs:
            continue
        kept = []
        for al in aliases:
            if al in claimed:
                if claimed[al] != fn:
                    shadowed.append((al, claimed[al], fn))
                continue
            claimed[al] = fn
            kept.append(al)
        if fn not in byfn:
            byfn[fn] = []
            order.append(fn)
        byfn[fn].extend(kept)
    parse_dispatch.shadowed = shadowed
    return [(fn, byfn[fn]) for fn in order]


def _dict_literal_keys(fn_node: ast.FunctionDef):
    """Every dict literal in the function whose values are all calls — the `S = {...}` seal tables — as
    lists of their string keys, in source order."""
    out = []
    for node in ast.walk(fn_node):
        if isinstance(node, ast.Dict) and node.keys and all(
                isinstance(k, ast.Constant) and isinstance(k.value, str) for k in node.keys) and all(
                isinstance(v, ast.Call) for v in node.values):
            out.append([k.value for k in node.keys])
    return out


def _jsonable(v):
    """JSON round trip must give the value back exactly (type and all) or the seal would change."""
    s = json.dumps(v, ensure_ascii=False)
    back = json.loads(s)
    return back == v and json.dumps(back, ensure_ascii=False) == s


def record(fn_name: str) -> dict:
    """Run tick.<fn_name> in a fresh keeping with the helpers instrumented; return the recording."""
    import tick as T
    from concordance import derivation as D, receipts as R, tickstick as TS, cas, science_cards

    rec = {"seals": [], "creates": [], "mints": [], "direct_ticks": 0, "direct_verify": 0, "refused": []}
    in_helper = [0]
    in_mint = [0]
    orig = {"rh": T._rh_seal_num, "st": T._seal_through, "mint": T._mint_marks,
            "vd": D.verify_derivation, "create": TS.create, "tick": TS.tick}

    def rh(nid, expr, val, domain="mathematics", tol=1e-9):
        in_helper[0] += 1
        try:
            h = orig["rh"](nid, expr, val, domain, tol)
        finally:
            in_helper[0] -= 1
        rec["seals"].append({"form": "numeric", "nid": nid, "expr": expr, "value": val, "domain": domain,
                             "tol": tol, "hash": h})
        return h

    def st(domain, artifact_key, spec):
        in_helper[0] += 1
        try:
            h = orig["st"](domain, artifact_key, spec)
        finally:
            in_helper[0] -= 1
        rec["seals"].append({"form": "verifier", "domain": domain, "artifact": artifact_key, "spec": spec, "hash": h})
        return h

    def vd(items, *a, **k):
        if not in_helper[0]:
            rec["direct_verify"] += 1
        return orig["vd"](items, *a, **k)

    def create(question, statement="", field="", references=None, data_dir=None):
        r = orig["create"](question, statement, field, references, data_dir)
        rec["creates"].append({"question": question, "statement": statement, "field": field,
                               "references": references, "id": r.get("id"), "existed": r.get("existed")})
        return r

    def tick(*a, **k):
        if not in_mint[0]:
            rec["direct_ticks"] += 1
        r = orig["tick"](*a, **k)
        if not r.get("ok"):
            rec["refused"].append(r.get("error"))
        return r

    def mint(sid, marks, by):
        rec["mints"].append({"sid": sid, "marks": [list(m) for m in marks], "by": by})
        in_mint[0] += 1
        try:
            return orig["mint"](sid, marks, by)
        finally:
            in_mint[0] -= 1

    tmp = Path(tempfile.mkdtemp(prefix="nh_record_"))
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = str(tmp)
    cas._COLD_CARDS_WRITTEN.clear(); cas._COLD_SPINE_WRITTEN = False; science_cards._MINTED = None
    T._rh_seal_num, T._seal_through, T._mint_marks = rh, st, mint
    D.verify_derivation, TS.create, TS.tick = vd, create, tick
    try:
        rec["rc"] = getattr(T, fn_name)()
    finally:
        T._rh_seal_num, T._seal_through, T._mint_marks = orig["rh"], orig["st"], orig["mint"]
        D.verify_derivation, TS.create, TS.tick = orig["vd"], orig["create"], orig["tick"]
        if prior is None:
            os.environ.pop("CONCORDANCE_DATA_DIR", None)
        else:
            os.environ["CONCORDANCE_DATA_DIR"] = prior
        shutil.rmtree(tmp, ignore_errors=True)
    return rec


def why_not_data(fn_node: ast.FunctionDef, rec: dict) -> str | None:
    """None when the recording is pure data; else the first reason it must stay a Python handler."""
    if fn_node.args.args or fn_node.args.kwonlyargs:
        return "takes arguments"
    if rec["rc"] != 0:
        return f"returned {rec['rc']}"
    if rec["direct_verify"]:
        return f"calls verify_derivation itself ({rec['direct_verify']}x)"
    if rec["direct_ticks"]:
        return f"calls tickstick.tick itself ({rec['direct_ticks']}x)"
    if not rec["creates"] or not rec["mints"]:
        return "creates or mints nothing"
    hashes = {s["hash"] for s in rec["seals"] if s["hash"]}
    created = {c["id"] for c in rec["creates"]}
    for s in rec["seals"]:
        if not s["hash"]:
            return "a seal failed"
        if s["form"] == "numeric":
            if isinstance(s["value"], bool) or not isinstance(s["value"], (int, float)):
                return f"seal {s['nid']} value is {type(s['value']).__name__}"
            if not _jsonable(s["value"]) or not _jsonable(s["tol"]):
                return f"seal {s['nid']} value/tol does not round-trip JSON"
        else:
            if not _jsonable(s["spec"]):
                return "a verifier spec does not round-trip JSON"
    for m in rec["mints"]:
        if m["sid"] not in created:
            return f"mints onto {m['sid']} which it did not create"
        for mk in m["marks"]:
            if len(mk) not in (2, 3):
                return "a mark is not (kind, claim[, extra])"
            extra = mk[2] if len(mk) == 3 else None
            if isinstance(extra, dict):
                if set(extra) - MARK_KW:
                    return f"a mark carries {sorted(set(extra) - MARK_KW)}"
                sv = extra.get("seal")
                if sv and sv not in hashes:
                    return "a mark's seal was not minted by a helper"
                for k in ("source", "unit"):
                    if k in extra and not isinstance(extra[k], str):
                        return f"a mark's {k} is not a string"
                if "up_to" in extra and (isinstance(extra["up_to"], bool) or not isinstance(extra["up_to"], (int, float))):
                    return "a mark's up_to is not a number"
            elif extra:
                if not isinstance(extra, str) or extra not in hashes:
                    return "a mark's seal was not minted by a helper"
            if not isinstance(mk[0], str) or not isinstance(mk[1], str):
                return "a mark's kind/claim is not a string"
    return None


def to_entry(fn_node: ast.FunctionDef, aliases: list, rec: dict) -> dict:
    """The data file for a recorded function: seals (keyed), then the sticks with their marks in order."""
    name = entry_name(fn_node.name)
    doc = ast.get_docstring(fn_node) or ""
    # seal keys: the function's own S = {...} table when it names every seal, else nid / <domain>_<n>
    keys = None
    for cand in _dict_literal_keys(fn_node):
        if len(cand) == len(rec["seals"]) and len(set(cand)) == len(cand):
            keys = cand; break
    seals, hash2key, used = [], {}, set()
    for i, s in enumerate(rec["seals"]):
        if keys:
            key = keys[i]
        elif s["form"] == "numeric":
            key = s["nid"]
        else:
            key = f"{s['domain']}_{sum(1 for t in rec['seals'][:i] if t['form'] != 'numeric') + 1}"
        base, n = key, 2
        while key in used:
            key = f"{base}#{n}"; n += 1
        used.add(key)
        hash2key.setdefault(s["hash"], key)
        if s["form"] == "numeric":
            seals.append({"key": key, "nid": s["nid"], "expr": s["expr"], "value": s["value"],
                          "tol": s["tol"], "domain": s["domain"]})
        else:
            seals.append({"key": key, "domain": s["domain"], "artifact": s["artifact"], "spec": s["spec"]})
    creates = {c["id"]: c for c in rec["creates"]}
    sticks = []
    minted = set()
    for m in rec["mints"]:
        c = creates[m["sid"]]
        block = {"question": c["question"]}
        if c["statement"]:
            block["statement"] = c["statement"]
        if c["field"]:
            block["field"] = c["field"]
        if c["references"] is not None:
            block["references"] = list(c["references"])
        block["by"] = m["by"]
        marks = []
        for mk in m["marks"]:
            kind, claim = mk[0], mk[1]
            extra = mk[2] if len(mk) == 3 else None
            d = {"kind": kind, "claim": claim}
            kw = dict(extra) if isinstance(extra, dict) else ({"seal": extra} if extra else {})
            if kw.get("seal"):
                d["seal"] = hash2key[kw["seal"]]
            for k in ("source", "up_to", "unit"):
                if k in kw and kw[k] is not None:
                    d[k] = kw[k]
            marks.append(d)
        block["marks"] = marks
        sticks.append(block)
        minted.add(m["sid"])
    for c in rec["creates"]:
        if c["id"] not in minted and not c["existed"]:
            block = {"question": c["question"]}
            if c["statement"]:
                block["statement"] = c["statement"]
            if c["field"]:
                block["field"] = c["field"]
            if c["references"] is not None:
                block["references"] = list(c["references"])
            block["marks"] = []
            sticks.append(block)
    return {"schema": SCHEMA, "name": name, "aliases": aliases, "doc": doc, "seals": seals, "sticks": sticks}


def handler_entry(fn_name: str, aliases: list, reason: str) -> dict:
    name = entry_name(fn_name)
    e = {"schema": SCHEMA, "name": name, "aliases": aliases, "handler": HANDLER_RENAME.get(fn_name, fn_name)}
    if fn_name in HANDLER_PARAMS:
        e["params"] = HANDLER_PARAMS[fn_name]
    e["why_python"] = reason
    return e


def main() -> int:
    a = sys.argv[1:]
    out = Path(a[0]) if a else ROOT / "data" / "sticks"
    only = set(a[1:])
    src = (ROOT / "tools" / "tick.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    nodes = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    dispatch = parse_dispatch(src)
    for al, first, later in parse_dispatch.shadowed:
        print(f"shadowed alias {al!r}: reaches {first}(), never {later}()")
    out.mkdir(parents=True, exist_ok=True)
    n_data = n_handler = 0
    for fn_name, aliases in dispatch:
        name = entry_name(fn_name)
        if only and name not in only and fn_name not in only:
            continue
        node = nodes[fn_name]
        reason = "takes arguments" if (node.args.args or node.args.kwonlyargs) else None
        rec = None
        if reason is None:
            try:
                rec = record(fn_name)
            except Exception as exc:  # noqa: BLE001
                reason = f"raised {type(exc).__name__}: {str(exc)[:80]}"
            else:
                reason = why_not_data(node, rec)
        if reason is None:
            entry = to_entry(node, aliases, rec)
            n_data += 1
            tag = f"data: {len(entry['seals'])} seals, {sum(len(s['marks']) for s in entry['sticks'])} marks"
            if rec["refused"]:
                tag += f", REFUSED {len(rec['refused'])}"
        else:
            entry = handler_entry(fn_name, aliases, reason)
            n_handler += 1
            tag = "handler: " + reason
        (out / f"{name}.json").write_text(json.dumps(entry, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{name:32s} {tag}", flush=True)
    print(f"\n{n_data} data entries, {n_handler} handler entries -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
