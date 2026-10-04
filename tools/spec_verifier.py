#!/usr/bin/env python3
"""VERIFIERS AS DATA — the operator's door (Gen 3 · 2, 2026-10-04).

    PYTHONPATH=src python tools/spec_verifier.py --check eval/specs/electrical.json      # validate + prove, change nothing
    PYTHONPATH=src python tools/spec_verifier.py --admit eval/specs/electrical.json      # prove, SEAL, append admitted
    PYTHONPATH=src python tools/spec_verifier.py --catalog                               # what this node holds as data
    PYTHONPATH=src python tools/spec_verifier.py --shadow electrical                     # spec vs the Python module on the goldens

--admit writes data/verifier_specs.jsonl (data-only; capability 1 carries it to every node) and seals the spec as a
CAS record. The agent path — a contributor with standing filing a spec for public review — is capability 6.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("CONCORDANCE_DATA_DIR", str(ROOT / "data"))

from concordance.verifiers import spec as S  # noqa: E402


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def shadow(domain: str) -> int:
    """The proof the charter asks for: the spec's verdicts equal the module's on the domain goldens."""
    from concordance import verifiers as V
    goldens = json.loads((ROOT / "data" / "domain_goldens.json").read_text(encoding="utf-8")).get(domain)
    if not goldens:
        print(f"no goldens for {domain}")
        return 2
    key = goldens["packet_key"]
    mod = V._get_module(domain)
    bad = 0
    for side in ("true", "false"):
        packet = {key: goldens[side]}
        code = {r.name: r.status for r in (mod.run(packet) if mod else [])}
        data = {r.name: r.status for r in S.run_for_domain(domain, packet)}
        for name in sorted(set(code) | set(data)):
            a, b = code.get(name, "—"), data.get(name, "—")
            same = (a == b) or (name not in code) or (name not in data)
            flag = "  " if same else "!!"
            if not same:
                bad += 1
            print(f"{flag} {side:5} {name:40} code={a:14} spec={b}")
    print("identical on every check both produce" if not bad else f"{bad} disagreements")
    return 0 if not bad else 1


def main() -> int:
    a = sys.argv[1:]
    if not a or a[0] not in ("--check", "--admit", "--catalog", "--shadow"):
        print(__doc__)
        return 2
    if a[0] == "--catalog":
        print(json.dumps(S.catalog(), indent=1, ensure_ascii=False))
        return 0
    if a[0] == "--shadow":
        return shadow(a[1] if len(a) > 1 else "electrical")
    spec = _load(a[1])
    why = S.validate(spec)
    if why:
        print("MALFORMED:", *why, sep="\n  ")
        return 1
    fails = S.prove(spec)
    if fails:
        print("DOES NOT PROVE ITSELF:", *fails, sep="\n  ")
        return 1
    print(f"{spec['id']}: {len(spec['checks'])} checks, every golden holds")
    if a[0] == "--admit":
        r = S.admit(spec)
        print(json.dumps(r, indent=1))
        return 0 if r.get("ok") else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
