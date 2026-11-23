#!/usr/bin/env python3
"""THE DOORS AS A PERSON RECEIVES THEM — an operator check (stdlib only; on the box or from anywhere).

Where it stands in the gate: tools/deploy.sh is pinned line for line (tests/test_build_ship.py,
tests/test_mint_ship.py), so this file is NOT called from it. The same door behaviour is gated instead as
live-assay probes (eval/live_probes.jsonl, ids `door.*`), which deploy.sh already runs on the box and which
ratchet: once passed, a failure is a regression and reverts the deploy. This tool adds what a JSON probe
cannot do — re-hash each receipt under the canonical form and read the served page's verdict table — and is
run by hand after a deploy (`python tools/door_integrity.py --base https://narrowhighway.com --mcp
https://narrowhighway.com`). Wiring it into deploy.sh is a change to a pinned file: its own reviewed step.

2026-11-23, the improvement plan's integrity release. Two defects reached the public under a green gate —
the derivation benchmark passed 60/60 and every targeted test passed — because those test the ENGINE, and
both defects lived in the DOOR: a page that computed its own verdict (PARTIAL shown as HOLDS) and a wrapper
that added a key to every sealed receipt (so the independent checker called each one TAMPERED). This check
asks the running site what a visitor and an agent actually get:

  1. THE PAGE      GET /  — the served homepage carries the engine-verdict table and reads it.
  2. THE PRESETS   every example button declares data-expect; each, sent as a visitor sends it (seal=0 here —
                   a probe never writes), must return exactly that verdict.
  3. PARTIAL       a checked constant beside an unchecked conjecture must come back PARTIAL, naming the rest.
  4. RECEIPTS      known receipts fetched through GET /seal and the agent door's seal_fetch must hash, byte for
                   byte under the canonical form of tools/verify_seal.py, to the seal that names them.

It prints how many checks RAN, and fails if fewer than the minimum ran — a skipped check is not a pass.

    python tools/door_integrity.py [--base http://127.0.0.1:8002] [--mcp http://127.0.0.1:8003]
"""
from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))

# Receipts linked from this repo's own docs — permanent, public, and already fetched live through both doors.
KNOWN_RECEIPTS = (
    "fe0ae96567afab81669ad5ed7b1556e62d84354dcc7bd648c33a911d9a0f1480",
    "f86419e863a613296958a3d005fb69acb0ed2a94122639dee2a34e918826885f",
    "9799c5b8b4cc90939ed3908ffa8130c0e1f7d6ff5ea49c89618727746818b27b",
)
PARTIAL_CLAIM = ("The speed of light is 299792458 m/s. "
                 "Every even number greater than 2 is the sum of two primes.")
ENGINE_VERDICTS = ("HOLDS", "PARTIAL", "BROKEN", "INCOMPLETE", "NOTHING_TO_CHECK", "SYSTEM_ERROR", "QUARANTINE")
MIN_PRESETS = 4
UA = {"User-Agent": "nh-door-integrity", "Content-Type": "application/json"}


def _canonical():
    """The ONE canonical form: tools/verify_seal.py's own, loaded by path — never a second copy."""
    spec = importlib.util.spec_from_file_location("verify_seal", os.path.join(HERE, "verify_seal.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.canonical_bytes


def _get(url, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.status, r.read().decode("utf-8"), dict(r.headers)


def _post(url, body, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def presets(page: str):
    """(claim, expected verdict) for every example button on the page that declares one."""
    out = []
    for tag in re.findall(r"<button[^>]*\bdata-eg=\"[^\"]*\"[^>]*>", page):
        eg = re.search(r"\bdata-eg=\"([^\"]*)\"", tag)
        ex = re.search(r"\bdata-expect=\"([A-Z_]+)\"", tag)
        out.append((html.unescape(eg.group(1)), ex.group(1) if ex else None))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get("NH_DOOR_BASE", "http://127.0.0.1:8002"))
    ap.add_argument("--mcp", default=os.environ.get("NH_DOOR_MCP", "http://127.0.0.1:8003"))
    a = ap.parse_args(argv)
    ran, failed = 0, []

    def check(name, ok, detail=""):
        nonlocal ran
        ran += 1
        print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  — " + detail) if detail else ""))
        if not ok:
            failed.append(name)

    # 1. THE PAGE
    try:
        st, page, _ = _get(a.base + "/")
    except Exception as e:  # noqa: BLE001
        st, page = 0, ""
        print("      could not fetch the homepage: %s" % e)
    check("homepage serves", st == 200, "HTTP %s" % st)
    table = re.search(r"var NH_VERDICTS = (\{.*?\});", page)
    try:
        t = json.loads(table.group(1)) if table else {}
    except ValueError:
        t = {}
    missing = [v for v in ENGINE_VERDICTS if v not in t]
    check("page carries every engine verdict", bool(t) and not missing, "missing %s" % missing if missing else "")
    check("page reads the engine's verdict", "NH_VERDICTS[d.verdict]" in page)

    # 2. THE PRESETS — each must do what it declares
    ps = presets(page)
    undeclared = [c for c, e in ps if not e]
    check("every preset declares its verdict", len(ps) >= MIN_PRESETS and not undeclared,
          "%d presets, %d undeclared" % (len(ps), len(undeclared)))
    for claim, expect in ps:
        if not expect:
            continue
        try:
            got = _post(a.base + "/verify?seal=0", {"claim": claim}).get("verdict")
        except Exception as e:  # noqa: BLE001
            got = "unreachable: %s" % e
        check("preset %r" % claim[:60], got == expect, "expected %s, got %s" % (expect, got))

    # 3. PARTIAL is PARTIAL, and it names what it did not check
    try:
        d = _post(a.base + "/verify?seal=0", {"claim": PARTIAL_CLAIM})
    except Exception as e:  # noqa: BLE001
        d = {"verdict": "unreachable: %s" % e}
    left = (d.get("coverage") or {}).get("unchecked_text") or []
    check("a partial claim is PARTIAL", d.get("verdict") == "PARTIAL", "got %s" % d.get("verdict"))
    check("PARTIAL names the unchecked text", bool(left), "unchecked_text=%s" % left)

    # 4. RECEIPTS, byte for byte, through both doors
    canonical = _canonical()
    for h in KNOWN_RECEIPTS:
        try:
            st, body, headers = _get(a.base + "/seal?hash=" + h)
            rec = json.loads(body)
            got = hashlib.sha256(canonical(rec)).hexdigest()
            check("GET /seal %s… re-hashes" % h[:12], got == h and "house" not in rec,
                  "" if got == h else "computed %s…%s" % (got[:12], " (has house)" if "house" in rec else ""))
        except Exception as e:  # noqa: BLE001
            check("GET /seal %s… re-hashes" % h[:12], False, str(e))
    mcp_bases = [b for b in (a.mcp, a.base) if b]
    mcp_ok = False
    for mb in mcp_bases:
        try:
            r = _post(mb + "/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                    "params": {"name": "seal_fetch", "arguments": {"hash": KNOWN_RECEIPTS[0]}}})
        except Exception:  # noqa: BLE001 — this base has no agent door; try the next
            continue
        mcp_ok = True
        res = r.get("result") or {}
        try:
            rec = json.loads(res["content"][0]["text"])
            got = hashlib.sha256(canonical(rec)).hexdigest()
        except Exception as e:  # noqa: BLE001
            rec, got = {}, "unreadable: %s" % e
        check("MCP seal_fetch at %s re-hashes" % mb, got == KNOWN_RECEIPTS[0] and "house" not in rec,
              "" if got == KNOWN_RECEIPTS[0] else "computed %s" % str(got)[:24])
        check("MCP seal_fetch keeps its ending beside the record", bool((res.get("_meta") or {}).get("house")))
        break
    check("an agent door answered", mcp_ok, "tried %s" % mcp_bases)

    minimum = 3 + 1 + MIN_PRESETS + 2 + len(KNOWN_RECEIPTS) + 3
    print("door_integrity: %d checks ran (minimum %d), %d failed" % (ran, minimum, len(failed)))
    if ran < minimum:
        print("FAIL  fewer checks ran than the minimum — a skipped check is not a pass")
        return 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
