"""The Works — a technical volume bound into the one book.

Matt: "show the depth of mathematics, science, and engineering we can achieve with the tools …
a technical document that is available and could be a part of the concordance which is the
entire book/project … all packaged into one product experience."

This is that volume. It is NOT prose that *claims* capability — it is a set of worked
demonstrations that are each run through the SAME engine that guards the moat, and each carries
a permanent, re-checkable seal (cite_url → /s/<hash>). Proof, not assertion (docs discipline):
the reader does not trust us; they open the seal and re-check the math themselves.

Conduit, not source: the engine verifies a PROVIDED derivation line by line; it never generates
the answer. Every demonstration here is a claim we hand it and it either confirms or breaks.

It grows: add a demonstration to DEMONSTRATIONS, rebuild, and the book deepens. Only
demonstrations that actually HOLD are published; a demonstration the engine cannot confirm is
dropped and logged — never quietly shown as if it passed.

Build (run every demonstration through the engine + mint its seal + sign the volume):
    PYTHONPATH=src python -c "from concordance import compendium; compendium.build_all()"
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import EngineConfig
from .derivation import verify_derivation
from . import receipts

_log = logging.getLogger("concordance.compendium")


# ── spec helpers (mathematics moat) ──────────────────────────────────────────
def _eq(a: str, b: str) -> Dict[str, Any]:
    return {"mode": "equality", "params": {"expr_a": a, "expr_b": b, "variables": {}}}


def _dv(f: str, v: str, d: str) -> Dict[str, Any]:
    return {"mode": "derivative", "params": {"function": f, "variable": v, "claimed_derivative": d}}


# ── The demonstrations ───────────────────────────────────────────────────────
# Each: id, discipline (mathematics|science|engineering), field, title, narrative, steps.
# A step is a real verifier claim: {id, domain, spec, claim, uses?}. `spec` for math is
# {mode, params}; for every other domain it is that verifier's flat structured packet.
# EVERY value here is the CORRECT one — the engine is what proves that, not this file.
DEMONSTRATIONS: List[Dict[str, Any]] = [
    # ── MATHEMATICS ──
    {
        "id": "works_euler_identity",
        "discipline": "mathematics", "field": "Complex analysis",
        "title": "Euler's identity, assembled from its parts",
        "narrative": "Often called the most beautiful equation in mathematics: it binds e, i, "
                     "π, 1 and 0 in a single line. We do not assert it — we hand the engine each "
                     "piece and the whole, and it confirms every one.",
        "steps": [
            {"id": "e1", "domain": "mathematics", "spec": _eq("cos(pi)", "-1"),
             "claim": "cos(π) = −1"},
            {"id": "e2", "domain": "mathematics", "spec": _eq("sin(pi)", "0"),
             "claim": "sin(π) = 0"},
            {"id": "e3", "domain": "mathematics", "spec": _eq("exp(I*pi)+1", "0"),
             "claim": "e^{iπ} + 1 = 0", "uses": ["e1", "e2"]},
        ],
    },
    {
        "id": "works_calculus_chain",
        "discipline": "mathematics", "field": "Calculus",
        "title": "Differentiate twice: position → velocity → acceleration",
        "narrative": "A falling body's position goes as t³ in this toy law. Differentiate once "
                     "for its velocity, again for its acceleration. Each differentiation is "
                     "machine-checked, and the second is only allowed to stand on the first.",
        "steps": [
            {"id": "c1", "domain": "mathematics", "spec": _dv("t**3", "t", "3*t**2"),
             "claim": "d/dt (t³) = 3t²  (position → velocity)"},
            {"id": "c2", "domain": "mathematics", "spec": _dv("3*t**2", "t", "6*t"),
             "claim": "d/dt (3t²) = 6t  (velocity → acceleration)", "uses": ["c1"]},
        ],
    },
    {
        "id": "works_trig_identities",
        "discipline": "mathematics", "field": "Trigonometry",
        "title": "From the unit circle to the double-angle law",
        "narrative": "The Pythagorean identity is the unit circle written as algebra. The "
                     "double-angle law for cosine follows in its train. Both are confirmed exactly "
                     "(not sampled), for all x.",
        "steps": [
            {"id": "t1", "domain": "mathematics", "spec": _eq("sin(x)**2+cos(x)**2", "1"),
             "claim": "sin²x + cos²x = 1"},
            {"id": "t2", "domain": "mathematics", "spec": _eq("cos(2*x)", "1-2*sin(x)**2"),
             "claim": "cos 2x = 1 − 2 sin²x", "uses": ["t1"]},
        ],
    },
    {
        "id": "works_number_theory",
        "discipline": "mathematics", "field": "Number theory",
        "title": "The integers, examined: a prime and a common divisor",
        "narrative": "Two exact facts about whole numbers — that 97 has no divisor but itself and "
                     "one, and that 48 and 36 share a greatest common divisor of 12 — decided by "
                     "algorithm, not by eye.",
        "steps": [
            {"id": "p1", "domain": "number_theory",
             "spec": {"n_prime": 97, "claimed_prime": True},
             "claim": "97 is prime"},
            {"id": "g1", "domain": "number_theory",
             "spec": {"gcd_a": 48, "gcd_b": 36, "claimed_gcd": 12},
             "claim": "gcd(48, 36) = 12", "uses": ["p1"]},
        ],
    },
    # ── SCIENCE ──
    {
        "id": "works_mechanics",
        "discipline": "science", "field": "Classical mechanics",
        "title": "A 2 kg mass: the force to move it, the energy it carries",
        "narrative": "Newton's second law fixes the force needed to accelerate a mass; its "
                     "kinetic energy fixes what that motion is worth. Same mass, two laws, both "
                     "checked against the numbers.",
        "steps": [
            {"id": "n1", "domain": "physics",
             "spec": {"mass_kg": 2, "acceleration_m_per_s2": 5, "claimed_force_N": 10},
             "claim": "F = m·a = 2 kg · 5 m/s² = 10 N"},
            {"id": "k1", "domain": "physics",
             "spec": {"mass_kg": 2, "velocity_m_per_s": 3, "claimed_kinetic_energy_J": 9},
             "claim": "KE = ½·m·v² = ½·2·3² = 9 J", "uses": ["n1"]},
        ],
    },
    {
        "id": "works_free_fall",
        "discipline": "science", "field": "Kinematics",
        "title": "Free fall: how far in two seconds",
        "narrative": "Drop something from rest near Earth's surface. Constant acceleration g = "
                     "9.8 m/s² carries it 19.6 m in two seconds — s = ½·a·t².",
        "steps": [
            {"id": "d1", "domain": "physics",
             "spec": {"v0": 0, "a": 9.8, "t": 2, "claimed_displacement": 19.6},
             "claim": "s = ½·g·t² = ½·9.8·2² = 19.6 m"},
        ],
    },
    {
        "id": "works_thermo_carnot",
        "discipline": "science", "field": "Thermodynamics",
        "title": "The Carnot ceiling no engine can beat",
        "narrative": "Between a hot reservoir at 400 K and a cold one at 300 K, the second law "
                     "caps efficiency at 1 − T_cold/T_hot = 25%. Not an engineering target — a law.",
        "steps": [
            {"id": "ca1", "domain": "thermodynamics",
             "spec": {"T_hot_K": 400, "T_cold_K": 300, "claimed_efficiency": 0.25},
             "claim": "η_Carnot = 1 − 300/400 = 0.25"},
        ],
    },
    {
        "id": "works_chemistry",
        "discipline": "science", "field": "Chemistry",
        "title": "Chemistry, two ways: will it run, and is it acid",
        "narrative": "Gibbs free energy decides whether a reaction proceeds on its own "
                     "(ΔG = ΔH − TΔS < 0). And pH places a solution on the acid–base scale. Two "
                     "different questions, one deterministic answer each.",
        "steps": [
            {"id": "gi1", "domain": "chemistry",
             "spec": {"delta_H_kJ_mol": -100, "delta_S_J_mol_K": 50,
                      "temperature_K": 298, "claimed_spontaneous": True},
             "claim": "ΔG = −100 − 298·(0.050) < 0 → spontaneous"},
            {"id": "ph1", "domain": "chemistry",
             "spec": {"pH": 3.0, "claimed_classification": "acidic"},
             "claim": "pH 3.0 → acidic", "uses": ["gi1"]},
        ],
    },
    # ── ENGINEERING ──
    {
        "id": "works_ohms_law",
        "discipline": "engineering", "field": "Electrical engineering",
        "title": "A 12-volt circuit: the current it draws, the power it burns",
        "narrative": "Ohm's law ties voltage, current and resistance; the power law says how much "
                     "heat that makes. A 12 V source across 6 Ω draws 2 A and dissipates 24 W — "
                     "and the power line is only allowed to stand on the confirmed Ohm's-law line.",
        "steps": [
            {"id": "o1", "domain": "electrical",
             "spec": {"voltage_V": 12, "current_A": 2, "resistance_ohm": 6},
             "claim": "V = I·R → 12 = 2·6 (2 A through 6 Ω)"},
            {"id": "pw1", "domain": "electrical",
             "spec": {"voltage_V": 12, "current_A": 2, "power_W_claim": 24},
             "claim": "P = V·I = 12·2 = 24 W", "uses": ["o1"]},
        ],
    },
    {
        "id": "works_framing_square",
        "discipline": "engineering", "field": "Structural / construction",
        "title": "The 3-4-5 the builders use to square a corner",
        "narrative": "A triangle with sides 3, 4, 5 is exactly right-angled — 3² + 4² = 5². It is "
                     "why a knotted rope or a framing square gives a true corner without a "
                     "protractor, and the engine confirms the right angle exactly.",
        "steps": [
            {"id": "fs1", "domain": "geometry",
             "spec": {"pyth_a": 3, "pyth_b": 4, "pyth_c": 5, "claimed_right_triangle": True},
             "claim": "3² + 4² = 5² → a true right angle"},
        ],
    },
    {
        "id": "works_spherical_tank",
        "discipline": "engineering", "field": "Mechanical / geometry",
        "title": "Sizing a spherical tank of radius 3",
        "narrative": "For a sphere of radius 3, the volume is (4/3)πr³ and the surface area is "
                     "4πr² — the material you enclose and the material you must build with. Both "
                     "come out to 36π here, decided to full precision.",
        "steps": [
            {"id": "sv1", "domain": "geometry",
             "spec": {"sphere_radius": 3,
                      "claimed_sphere_volume": 113.09733552923255,
                      "claimed_sphere_surface_area": 113.09733552923255},
             "claim": "V = (4/3)π·3³ = 36π ≈ 113.097 ;  A = 4π·3² = 36π ≈ 113.097"},
        ],
    },
]


# ── build + seal ─────────────────────────────────────────────────────────────
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _data_dir() -> Path:
    d = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    return (Path(d) if d else Path("data"))


def _compiled_path() -> Path:
    return _data_dir() / "compendium" / "compiled" / "compendium_latest.json"


def _identity_path() -> Path:
    return _data_dir() / "compendium" / "compiled" / "compendium_identity.json"


def _config() -> EngineConfig:
    # secular surface → seals cite narrowhighway.com (the world-facing book).
    return EngineConfig(surface="secular")


# Each non-math verifier reads its claim from ONE typed artifact key. We keep the demonstrations
# above written as flat, readable specs and wrap them into the verifier's packet here — one place,
# so a new demonstration stays a plain dict of numbers.
_ARTIFACT_KEY = {
    "number_theory": "NUM_VERIFY", "physics": "PHYS_VERIFY", "electrical": "ELEC_VERIFY",
    "thermodynamics": "THERMO_VERIFY", "chemistry": "CHEM_VERIFY", "geometry": "GEOM_VERIFY",
}


def _packet_for(domain: str, spec: Dict[str, Any]) -> Dict[str, Any]:
    """Math specs ({mode, params}) pass through; a flat domain spec is wrapped under its
    verifier's artifact key (unless already wrapped)."""
    d = (domain or "").strip().lower()
    if d in ("mathematics", "math"):
        return spec
    key = _ARTIFACT_KEY.get(d)
    if not key:
        return spec
    if isinstance(spec, dict) and len(spec) == 1 and key in spec:
        return spec
    return {key: spec}


def _run_one(demo: Dict[str, Any], config: EngineConfig) -> Optional[Dict[str, Any]]:
    """Run one demonstration through the engine and seal it. Returns the published record,
    or None if it does not HOLD (dropped + logged — never shown as if it passed)."""
    steps = demo["steps"]
    runsteps = [dict(s, spec=_packet_for(s.get("domain", ""), s.get("spec") or {})) for s in steps]
    result = verify_derivation(runsteps)
    if result.get("verdict") != "HOLDS":
        _log.warning("compendium: DROPPED %s — verdict=%s broken_at=%s",
                     demo["id"], result.get("verdict"), result.get("broken_at"))
        return None
    seal_domain = str(steps[0].get("domain") or "mathematics")
    sealed = receipts.attach(result, config=config, domain=seal_domain, enabled=True)
    seal = sealed.get("seal") or {}
    return {
        "id": demo["id"], "discipline": demo["discipline"], "field": demo["field"],
        "title": demo["title"], "narrative": demo["narrative"],
        "verdict": result["verdict"], "steps": result["steps"],
        "confirmed_steps": result["confirmed_steps"],
        "trail": result["trail"],
        "seal": {"content_hash": seal.get("content_hash"), "cite_url": seal.get("cite_url"),
                 "ledgered": seal.get("ledgered")} if seal else None,
    }


def build_all() -> Dict[str, Any]:
    """Run every demonstration through the engine, mint each seal, sign the volume, persist it."""
    config = _config()
    published: List[Dict[str, Any]] = []
    dropped: List[str] = []
    for demo in DEMONSTRATIONS:
        rec = _run_one(demo, config)
        if rec is None:
            dropped.append(demo["id"])
        else:
            published.append(rec)

    by_discipline: Dict[str, int] = {}
    for r in published:
        by_discipline[r["discipline"]] = by_discipline.get(r["discipline"], 0) + 1

    manifest = {
        "work": "The Works — mathematics, science and engineering, worked and sealed",
        "part_of": "The Concordance (narrowhighway) — the whole book/project",
        "generated": _now(),
        "published": len(published), "dropped": dropped,
        "by_discipline": by_discipline,
        "seals": [r["seal"]["content_hash"] for r in published if r.get("seal")],
        "discipline_order": ["mathematics", "science", "engineering"],
    }
    manifest_hash = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    payload: Dict[str, Any] = {
        "manifest": manifest, "manifest_sha256": manifest_hash,
        "demonstrations": published,
    }
    _sign(payload)
    p = _compiled_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)
    _log.info("compendium: published %d, dropped %d -> %s", len(published), len(dropped), p)
    return payload


def _sign(payload: Dict[str, Any]) -> None:
    """Ed25519-sign the volume (degraded-but-honest if `cryptography` is absent), mirroring
    the codex artifact so the whole book is signed the same way."""
    try:
        from . import identity as _id
        idp = _identity_path()
        if idp.exists():
            ident = json.loads(idp.read_text(encoding="utf-8"))
        else:
            ident = _id.create_identity()
            idp.parent.mkdir(parents=True, exist_ok=True)
            idp.write_text(json.dumps(ident, indent=2), encoding="utf-8")
        payload["signature"] = _id.sign(ident["private_key"], payload["manifest_sha256"])
        payload["public_key"] = ident["public_key"]
        payload["fingerprint"] = _id.fingerprint(ident["public_key"])
        payload["signed"] = bool(_id.signing_available())
    except Exception as e:  # never crash the volume over signing
        payload["signature"] = None
        payload["signed"] = False
        payload["sign_error"] = str(e)[:120]


# ── serve ────────────────────────────────────────────────────────────────────
_CACHE: Optional[Dict[str, Any]] = None


def load(force: bool = False) -> Dict[str, Any]:
    """The compiled volume. Reads the sealed file; builds it lazily if absent. Cached in-process."""
    global _CACHE
    if _CACHE is not None and not force:
        return _CACHE
    p = _compiled_path()
    if p.exists() and not force:
        try:
            _CACHE = json.loads(p.read_text(encoding="utf-8"))
            return _CACHE
        except Exception:  # corrupt file — rebuild
            pass
    _CACHE = build_all()
    return _CACHE


def overview() -> Dict[str, Any]:
    """The volume's front matter: what it is, how many demonstrations stand, by discipline."""
    v = load()
    man = v.get("manifest") or {}
    return {
        "work": man.get("work"), "part_of": man.get("part_of"),
        "generated": man.get("generated"),
        "published": man.get("published", 0), "by_discipline": man.get("by_discipline", {}),
        "signed": v.get("signed", False), "fingerprint": v.get("fingerprint"),
        "manifest_sha256": v.get("manifest_sha256"),
        "note": ("Every demonstration below was run through the same engine that guards the moat "
                 "and carries a permanent, re-checkable seal. Proof, not assertion — open a seal "
                 "and re-check the math yourself. The engine verifies a provided derivation; it "
                 "does not generate the answer."),
    }


def demonstrations() -> List[Dict[str, Any]]:
    """Every published demonstration, in discipline order (mathematics → science → engineering)."""
    v = load()
    order = {d: i for i, d in enumerate((v.get("manifest") or {}).get("discipline_order", []))}
    demos = list(v.get("demonstrations") or [])
    demos.sort(key=lambda r: (order.get(r.get("discipline"), 99), r.get("id", "")))
    return demos


def demonstration(demo_id: str) -> Optional[Dict[str, Any]]:
    for r in (load().get("demonstrations") or []):
        if r.get("id") == demo_id:
            return r
    return None


def artifact() -> Dict[str, Any]:
    """The signed volume: manifest + signature + public key (the book as of a date, Ed25519-sealed)."""
    v = load()
    return {"manifest": v.get("manifest"), "manifest_sha256": v.get("manifest_sha256"),
            "signature": v.get("signature"), "public_key": v.get("public_key"),
            "fingerprint": v.get("fingerprint"), "signed": v.get("signed", False)}


def verify_artifact() -> Dict[str, Any]:
    """Re-check the volume's signature and manifest hash."""
    v = load()
    man = v.get("manifest")
    if not man:
        return {"ok": False, "reason": "no volume compiled yet"}
    recomputed = hashlib.sha256(
        json.dumps(man, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    hash_ok = recomputed == v.get("manifest_sha256")
    sig_ok = None
    if v.get("signature") and v.get("public_key"):
        try:
            from . import identity as _id
            sig_ok = _id.verify(v["public_key"], v["manifest_sha256"], v["signature"])
        except Exception:
            sig_ok = None
    return {"ok": bool(hash_ok and (sig_ok is not False)),
            "manifest_hash_ok": hash_ok, "signature_ok": sig_ok,
            "published": man.get("published"), "generated": man.get("generated")}


if __name__ == "__main__":  # sovereign self-run (droplet gate has no pytest)
    logging.basicConfig(level=logging.INFO)
    out = build_all()
    m = out["manifest"]
    print(f"The Works: published {m['published']} demonstrations "
          f"({m['by_discipline']}), dropped {len(m['dropped'])}: {m['dropped']}")
    print(f"signed={out.get('signed')} fingerprint={out.get('fingerprint')}")
    va = verify_artifact()
    print(f"verify: {va}")
