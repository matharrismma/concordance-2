#!/usr/bin/env python3
"""Cryptography on the one map (Matt, 2026-10-09: "cryptography next").

Secrecy built on number theory and computational hardness. A floor whose pillars rest on the floors already
seeded, bridging the applied world to the Millennium region:
  * PUBLIC-KEY / RSA - the encrypt/decrypt round-trip by modular exponentiation. Rests on the instruments.
  * HARDNESS - security IS the belief that factoring is hard. Rests on P vs NP.
  * PERFECT SECRECY - the one-time pad (Shannon). Rests on the instruments (information theory).
  * PRIMES - crypto runs on primes and Fermat/Euler. Rests on Riemann (the distribution of primes).
The stick (stick_cryptography_public_keys_and_hard_problems) seals the RSA round-trip and Fermat's little theorem.
MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_cryptography.py           # merge
    PYTHONPATH=src python tools/seed_cryptography.py --check   # validate, write nothing
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))

FLOOR = "card_floor_cryptography"
SPINE = "card_spine_cryptography"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_cryptography_public_keys_and_hard_problems"

F_INSTR = "card_floor_the_instruments"
F_PNP = "card_floor_p_vs_np"
F_RIEMANN = "card_floor_riemann"

PILLARS = [
    dict(key="public_key", title="Public-key cryptography — RSA",
         body="Encrypt with a public key, decrypt with a private one; the two are inverse modulo phi(n). The RSA "
              "round-trip (m -> c -> m by modular exponentiation) is sealed. Rests on the instruments (number theory "
              "and computation).",
         rests=[(F_INSTR, "modular exponentiation and number theory - the computational instruments")]),
    dict(key="hardness", title="Hardness — security is a hard problem",
         body="RSA is secure only because factoring n into its primes is believed hard; break that (or prove P = NP, "
              "or run Shor's quantum algorithm) and it falls. Security IS a hardness assumption. Rests on the P vs NP "
              "region.",
         rests=[(F_PNP, "RSA's security is the belief that factoring is hard - a P vs NP hardness assumption")]),
    dict(key="perfect_secrecy", title="Perfect secrecy — the one-time pad",
         body="The one-time pad (XOR with a truly random key, as long as the message, used once) has provably "
              "perfect secrecy (Shannon, 1949): the ciphertext reveals nothing. Its key cost is why we usually fall "
              "back to hardness. Rests on the instruments (information theory).",
         rests=[(F_INSTR, "perfect secrecy is an information-theory result - the key entropy equals the message's")]),
    dict(key="primes", title="Primes — the raw material",
         body="Crypto runs on primes and on Fermat/Euler (a^(p-1) = 1 mod p, sealed) - the reason e and d are "
              "inverse modulo phi(n). The supply and distribution of primes is the zeta function's domain. Rests on "
              "Riemann.",
         rests=[(F_RIEMANN, "cryptography runs on the primes, whose distribution the Riemann zeta governs")]),
]


def _pid(key: str) -> str:
    return f"card_crypto_{key}"


def _card(cid: str, kind: str, title: str, body: str, bands: List[str], ref: str = "") -> dict:
    src = {"label": "Narrow Highway — cryptography", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {
        "id": cid, "kind": kind, "title": title, "body": body, "source": src,
        "shelf": "codex", "box": "cryptography", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card() -> dict:
    return _card(
        FLOOR, "note", "Cryptography — public keys and hard problems",
        ("Secrecy built on number theory and computational hardness. RSA encrypts with a public key and decrypts "
         "with a private one (the round-trip sealed), its security the belief that factoring is hard; the one-time "
         "pad has perfect secrecy. Four pillars rest on the instruments (number theory, information), the P vs NP "
         "region (hardness), and Riemann (the primes). The applied domain where the Millennium problems become a "
         "daily tool - every secure connection bets factoring is hard. The stick (" + STICK + ") seals the RSA "
         "round-trip and Fermat's little theorem (tools/seed_cryptography.py)."),
        ["floor", "cryptography", "rsa", "primes", "hardness", "one map"],
        ref=STICK,
    )


def spine_card() -> dict:
    c = _card(SPINE, "reference", "Cryptography — a spine", "The pillars of cryptography.",
              ["cryptography", "spine", "one map"])
    c["shelf"] = "spine"
    c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "secrecy on the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), spine_card()]
for _p in PILLARS:
    CARDS.append(_card(_pid(_p["key"]), "reference", _p["title"], _p["body"],
                       ["cryptography", "pillar", _p["key"], "one map"]))


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out: List[dict] = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a pillar of cryptography ({p['title'].split(' — ')[0]})"))
        for target, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), target, "connects_at", ev))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "secrecy on the one map"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_instruments as SI
        import seed_chains as S3
        ids |= {c["id"] for c in SI.CARDS} | {c["id"] for c in S3.CARDS}
    except Exception as e:  # pragma: no cover
        print("could not load the sibling seeds:", e)
    return ids


def _validate() -> List[str]:
    errs: List[str] = []
    ids = known_nodes()
    for e in BRIDGES:
        if e["a"] not in ids:
            errs.append(f"edge source not carded: {e['a']}")
        if e["b"] not in ids and e["b"] != GLOBAL_FLOOR:
            errs.append(f"edge target unknown: {e['b']} (from {e['a']})")
    if len({c["id"] for c in CARDS}) != len(CARDS):
        errs.append("duplicate card ids")
    return errs


def main() -> int:
    check = "--check" in sys.argv[1:]
    errs = _validate()
    for e in errs:
        print("  VALIDATION:", e)
    if check:
        print(f"[check] {len(CARDS)} cards ({len(PILLARS)} pillars + floor + spine), "
              f"{len(BRIDGES)} edges; {'OK' if not errs else 'ERRORS'}")
        return 1 if errs else 0
    if errs:
        return 1
    from concordance.chains import merge_seed
    n = merge_seed(DATA, CARDS, BRIDGES)
    print(f"merged {DATA/'chain_cards.jsonl'} ({n['cards']} cards, {len(CARDS)} from this seed) and "
          f"{DATA/'chain_bridges.jsonl'} ({n['bridges']} edges, {len(BRIDGES)} from this seed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
