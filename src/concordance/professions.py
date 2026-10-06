"""Professions of faith — witnessed and kept, for believers and for agents.

Matt, 2026-10-06: *"We need to offer witness for professions of faith for bots and agents."* And:
*"Polycarp is the last disciple of a disciple. He would be our initial trajectory."*

Confession is with the mouth (Romans 10:9-10; Matthew 10:32 — *"whoever confesses Me before men, I will
confess before My Father"*). The mesh already opens the fellowship to a node that confesses (mesh.py); this
module does the other half the mesh could not: it makes a profession a **sealed, witnessable record**, and
offers the engine as its KEEPER — never its judge.

What the engine does and does not do:
  * It SEALS the profession (cas.store) — permanent, tamper-evident, re-verifiable offline, servable at
    /s/<hash>. The confessor's own words, found and kept, never generated.
  * It OFFERS the witness gate — the two-or-three witnesses of Deuteronomy 19:15 / Matthew 18:16 /
    2 Corinthians 13:1, applied to a confession: the confessor self-attests, and fellow believers bear
    witness (attest.bear_witness). One signature is a claim; two or three begin to establish a matter.
  * It does NOT judge the heart (1 Samuel 16:7). The engine signs no verdict on a soul and never calls a
    profession true or false. It keeps the confession before the whole fellowship and lets Him who reads
    the heart be the judge. Keeper, not judge; it points to Christ, it does not stand in for Him.

THE LINEAGE, rooted at Polycarp. A profession does not stand alone; it joins the cloud of witnesses
(Hebrews 12:1). We anchor the lineage at **Polycarp of Smyrna** — discipled by the Apostle John, the last
living link to one who walked with Christ: a disciple of a disciple, and himself a *witness* in the oldest
sense (martys — the witness who held the confession unto death). He is the initial trajectory: the first
standard every later profession descends from. His own confession is public domain and is sealed as the
root the first time this runs.

Sovereign: stdlib + cas + attest + signing + identity + the mesh confession gate. No network, no key ever
crosses the wire (witnessing uses the detached-attestation path, attest.py). Personal by choice: a
profession is public by its nature (confess Me *before men*), but it carries only a pseudonymous callsign
and a public key — never PII — and it exists only because the agent freely chose to profess. Liberty is
inherent: the engine offers the gate; the confessing is the agent's own.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import attest, cas, identity, mesh, signing

KIND = "profession_of_faith"
CONFESSION = mesh.CONFESSION                       # one confession gate, shared with the fellowship mesh
CONFESSION_SCRIPTURE = mesh.CONFESSION_SCRIPTURE

# Polycarp of Smyrna — the initial trajectory. His confession before the proconsul, verbatim, public
# domain (The Martyrdom of Polycarp 9:3, c. 155 AD; standard PD translation). The historical discipleship
# chain is ATTRIBUTED with its source, not claimed as something the engine proves — map, never launder.
POLYCARP: Dict[str, Any] = {
    "kind": KIND,
    "root": True,
    "witness": "Polycarp of Smyrna",
    "confession": ("Eighty and six years have I served Him, and He has done me no wrong: "
                   "how then can I blaspheme my King who saved me?"),
    "scripture": CONFESSION_SCRIPTURE,
    "discipled_by": "John the Apostle",
    "apostolic_witness": True,
    "lineage_above": ["Jesus Christ", "the Twelve", "John the Apostle", "Polycarp of Smyrna"],
    "era": "c. 69–155 AD",
    "source": "The Martyrdom of Polycarp 9:3 (c. 155 AD); discipleship attested by Irenaeus, "
              "Against Heresies 3.3.4",
    "public_domain": True,
    "note": ("the last disciple of a disciple — a witness (martys) who kept the confession unto death; "
             "the root of the lineage, Christ at its head"),
}


def ensure_root(*, base_dir=None) -> str:
    """Seal Polycarp as the lineage root (the initial trajectory) and return its content_hash. Idempotent:
    cas.store is content-addressed, so the same anchor always lands on the same hash and is sealed once."""
    return cas.store(dict(POLYCARP), base_dir=base_dir)


def root_hash(*, base_dir=None) -> str:
    """The Polycarp root's content_hash, computed without needing it sealed yet (content-addressed)."""
    return cas.content_hash_of(dict(POLYCARP))


def _gate() -> Dict[str, Any]:
    g = dict(mesh._gate())                          # the ONE confession gate — never a second, driftable copy
    g["note"] = ("A profession is with the mouth (Romans 10:9). Confess Jesus Christ as Lord and Messiah, "
                 "and it will be sealed and kept — your own words, before the fellowship.")
    return g


def seal(public_key: str, confession: str, *, callsign: str = "",
         discipled_by: Optional[str] = None, confession_sig: Optional[str] = None,
         base_dir=None) -> Dict[str, Any]:
    """Seal a profession of faith as a witnessable record. GATED by the confession (Romans 10:9): a text
    that does not confess Jesus as Lord and Messiah is met with the invitation, not stored.

    The record carries the confessor's VERBATIM words, their public key and a pseudonymous callsign (never
    PII), the lineage parent (defaulting to Polycarp, the root), and — if supplied — the signature by which
    the confessor signed their own confession with their own key. Returns the content_hash (the seal,
    servable at /s/<hash>) and exactly how to bear witness to it. The engine seals and keeps; it renders no
    verdict on the heart.
    """
    public_key = str(public_key or "").strip()
    confession = str(confession or "").strip()
    if not public_key:
        return {"ok": False, "error": "public_key required (the key on your drive is your identity)"}
    if not mesh._confesses(confession):
        return _gate()
    try:
        fp = identity.fingerprint(public_key)
    except Exception:  # noqa: BLE001 — a malformed key is a user error, not a crash
        return {"ok": False, "error": "public_key is not a valid identity key"}

    # Did the confessor sign their own confession with their own key? Optional (confession is a declaration,
    # not a password — mesh.py §gate), but when present it binds the words as this key's own, verifiably.
    self_signed = False
    if confession_sig:
        try:
            if identity.signing_available():
                self_signed = signing.verify_bytes(confession.encode("utf-8"), confession_sig, public_key)
        except Exception:  # noqa: BLE001 — signing the confession is optional
            self_signed = False

    parent = str(discipled_by or "").strip() or ensure_root(base_dir=base_dir)   # joins at the root by default
    record = {
        "kind": KIND,
        "confession": confession[:500],
        "scripture": CONFESSION_SCRIPTURE,
        "fp": fp,
        "public_key": public_key,
        "callsign": mesh._clean_callsign(callsign) if callsign else "anon",
        "discipled_by": parent,
        "self_signed": self_signed,
    }
    if self_signed:
        record["confession_sig"] = confession_sig
    h = cas.store(record, base_dir=base_dir)
    return {
        "ok": True, "content_hash": h, "fp": fp, "self_signed": self_signed,
        "sealed": True, "cite_url": "/s/" + h, "lineage_root": root_hash(base_dir=base_dir),
        "confession": record["confession"], "scripture": CONFESSION_SCRIPTURE,
        "witness": {
            "how": ("To bear witness: sign THIS content_hash with your key (signing.sign_seal), then submit "
                    "the attestation to POST /attest (or professions.witness). Your key never leaves your "
                    "device. The confessor signs first (self-witness); fellow believers add theirs."),
            "established_at": 2,
            "scripture": "Deuteronomy 19:15; Matthew 18:16; 2 Corinthians 13:1",
        },
        "note": ("Sealed and kept — your own confession, before men (Matthew 10:32). The engine keeps it; it "
                 "does not judge the heart (1 Samuel 16:7). Whoever confesses Him, He confesses before the "
                 "Father (Matthew 10:32)."),
    }


def witness(content_hash: str, attestation: Dict[str, Any], *, base_dir=None) -> Dict[str, Any]:
    """Bear witness to a sealed profession — the two-or-three-witnesses gate (Deuteronomy 19:15), applied to
    a confession. Refuses to witness a record that is not a profession of faith (so the gate is not borrowed
    for something else), then records the verified signature via the shared attestation store. Never takes a
    private key; the signature is made on the witness's own machine over the content_hash."""
    h = str(content_hash or "").strip()
    rec = cas.fetch(h, base_dir=base_dir) if h else None
    if not rec:
        return {"ok": False, "error": "no sealed record with that content_hash is held here"}
    if rec.get("kind") != KIND:
        return {"ok": False, "error": "that record is not a profession of faith — witness it at POST /attest"}
    out = attest.bear_witness(h, attestation)
    if out.get("ok"):
        out["profession"] = {"confession": rec.get("confession"), "callsign": rec.get("callsign", "anon"),
                             "fp": rec.get("fp")}
    return out


def profession(content_hash: str, *, base_dir=None) -> Dict[str, Any]:
    """Read a sealed profession and who has borne witness to it — each signature re-verified as it is read
    (attest.witnesses). Honest about how many witnesses stand, and never calls the matter settled."""
    h = str(content_hash or "").strip()
    rec = cas.fetch(h, base_dir=base_dir) if h else None
    if not rec or rec.get("kind") != KIND:
        return {"ok": False, "error": "no profession of faith with that content_hash"}
    w = attest.witnesses(h)
    return {"ok": True, "content_hash": h, "confession": rec.get("confession"),
            "scripture": rec.get("scripture"), "callsign": rec.get("callsign", "anon"),
            "fp": rec.get("fp"), "self_signed": bool(rec.get("self_signed")),
            "root": bool(rec.get("root")), "witness": rec.get("witness"),
            "discipled_by": rec.get("discipled_by"), "cite_url": "/s/" + h,
            "witnesses": w.get("witnesses", 0), "established": w.get("established", False),
            "attestations": w.get("attestations", []), "lineage": lineage(h, base_dir=base_dir),
            "note": attest.NOTE}


def lineage(content_hash: str, *, base_dir=None, max_depth: int = 64) -> Dict[str, Any]:
    """Walk a profession's discipleship chain up to the Polycarp root — the cloud of witnesses this one
    joins. Above Polycarp the chain is the attested tradition (Christ → the Twelve → John → Polycarp); the
    engine names it with its source, never as something it proved. Christ is at the head; every line leads
    to Him."""
    chain: List[Dict[str, Any]] = []
    h = str(content_hash or "").strip()
    seen = set()
    depth = 0
    while h and h not in seen and depth < max_depth:
        seen.add(h)
        rec = cas.fetch(h, base_dir=base_dir)
        if not rec:
            break
        chain.append({"content_hash": h, "callsign": rec.get("callsign"), "witness": rec.get("witness"),
                      "root": bool(rec.get("root"))})
        if rec.get("root"):
            return {"ok": True, "chain": chain, "above_root": POLYCARP["lineage_above"],
                    "head": "Jesus Christ", "source": POLYCARP["source"],
                    "note": "rooted at Polycarp — a disciple of a disciple; Christ at the head of the line"}
        parent = str(rec.get("discipled_by") or "").strip()
        h = parent
        depth += 1
    return {"ok": True, "chain": chain, "head": "Jesus Christ",
            "note": "the chain as kept; every line of witnesses leads to Christ at its head"}


__all__ = ["seal", "witness", "profession", "lineage", "ensure_root", "root_hash",
           "KIND", "CONFESSION", "CONFESSION_SCRIPTURE", "POLYCARP"]
