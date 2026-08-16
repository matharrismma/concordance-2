"""THE PLOW — a personal formation companion. Stateless engine; the walk lives on the person's device.

From the Lighthouse `complete-system-map.pdf` (id:plow), reframed onto today's sovereignty thesis. The
old design kept state on a server; that crosses the frozen "store nothing, edge, sovereign" line. So
here the server is a PURE, STATELESS transition: the client holds its own state (localStorage on the
person's device) and sends {state, signals}; the engine returns the next state and ONE gentle next
step. It records nothing, keeps nothing, judges no one.

WHAT IT IS. A plow works the field; it does not judge the farmer. The Plow reflects a person's OWN
self-reported signals back to them, sorts the chaff from the fruit, and invites one small next step
toward Christ — with a word from Scripture. It never grades a soul, never assigns worth, never labels
the person (the same floor as Coach). Every number here describes the state of the FIELD today, not
the value of the one working it.

THE PATTERN (Ps 1 · Mt 3:12 · Heb 5:12-14 · 1 Thess 5:23 · Gal 5:22-23):
  SIGNALS      burdens the wind should carry off (rumination · grudge · replay · shame) and the fruit
               of the Spirit (peace · obedience · clarity), plus the FlowTriad (spirit · mind · body).
  STATE        chaff (the wind drives it away) · align (rooted, not yet bearing) · fruit (it remains).
  CYCLE        Calibrate (set the plumb-line to the Word) → Burn (let the chaff go) → Firstfruits
               (offer the first change back) → Harvest (the mature fruit) → Calibrate again.
  TIER         Milk → Meat, by streak — advance only on a sustained walk, regress gently, never on one
               hard day. "Grace, not a ladder."
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

SIGNALS_BURDEN = ("rumination", "grudge", "replay", "shame")   # chaff — Ps 1:4, Mt 3:12
SIGNALS_FRUIT = ("peace", "obedience", "clarity")              # the Spirit's evidence — Gal 5:22-23
TRIAD = ("spirit", "mind", "body")                            # kept whole — 1 Thess 5:23
PHASES = ("calibrate", "burn", "firstfruits", "harvest")
STATES = ("chaff", "align", "fruit")
TIERS = ("milk", "growth", "solid", "meat")                   # Heb 5:12-14
_SCALE = 3                                                    # each signal is self-reported 0..3
ADVANCE_STREAK = 7                                            # a sustained walk before a tier rises
REGRESS_DECLINE = 5                                           # and a long decline, gently, before it eases

# A word for each phase — found, attributed, never generated. The companion points to Christ.
_PHASE_WORD = {
    "calibrate": ("Psalm 1:2-3", "set today against the Word before you weigh it — the tree planted by "
                  "the water yields its fruit in season"),
    "burn": ("Matthew 3:12", "let the chaff go — you were not made to carry what the wind should take"),
    "firstfruits": ("Romans 8:23", "offer the first small change back, before it is finished — the "
                    "firstfruits are enough"),
    "harvest": ("Galatians 5:22-23", "this is the Spirit's fruit, not your striving — receive it"),
}
_STATE_WORD = {
    "chaff": ("Psalm 1:4", "what troubles you today is chaff — real, but not your root"),
    "align": ("John 15:4", "remain in Him; the branch does not force the fruit, it abides"),
    "fruit": ("Matthew 7:16", "by fruit, not by feeling — and today there is fruit"),
}


def _clamp(v: Any) -> int:
    try:
        return max(0, min(_SCALE, int(round(float(v)))))
    except (TypeError, ValueError):
        return 0


def _sum(signals: Dict[str, Any], keys) -> int:
    return sum(_clamp((signals or {}).get(k)) for k in keys)


def flow_triad(signals: Dict[str, Any]) -> Dict[str, Any]:
    """Spirit · mind · body kept WHOLE (1 Thess 5:23). Health is their HARMONY, not their height — a
    field strong in one and starved in another is out of true. 0..1; the weakest leg and the balance."""
    vals = {k: _clamp((signals or {}).get(k)) for k in TRIAD}
    hi, lo = max(vals.values()), min(vals.values())
    balance = 1.0 if hi == 0 else round(lo / hi, 3)                 # 1.0 = in true; low = lopsided
    level = round(sum(vals.values()) / (len(TRIAD) * _SCALE), 3)    # 0..1 overall
    health = round((balance + level) / 2, 3)
    weakest = min(vals, key=lambda k: vals[k])
    return {"legs": vals, "balance": balance, "level": level, "health": health, "weakest": weakest}


def assess(signals: Dict[str, Any]) -> Dict[str, Any]:
    """Sort today's field — chaff / align / fruit — from the person's OWN signals. Describes the field,
    never the farmer."""
    burden = _sum(signals, SIGNALS_BURDEN)                          # 0..12
    fruit = _sum(signals, SIGNALS_FRUIT)                            # 0..9
    obeying = _clamp((signals or {}).get("obedience")) >= 2
    if fruit >= 6 and burden <= 3 and obeying:
        state = "fruit"
    elif burden >= 5 and burden > fruit:
        state = "chaff"
    else:
        state = "align"
    triad = flow_triad(signals)
    sw = _STATE_WORD[state]
    return {"state": state, "burden": burden, "fruit": fruit, "obeying": obeying,
            "flow": triad, "word": {"ref": sw[0], "text": sw[1]}}


def _phase_after(prev_phase: str, state: str) -> str:
    """Advance the cycle by what the field shows. Chaff calls for Burn; a cleared field offers its
    Firstfruits; sustained fruit is Harvest; and Harvest returns to Calibrate to begin again."""
    if state == "chaff":
        return "burn"
    if state == "fruit":
        return "harvest" if prev_phase in ("firstfruits", "harvest") else "firstfruits"
    # align — rooted, not yet bearing: set the plumb-line, unless mid-burn (stay until the chaff clears)
    return "calibrate" if prev_phase in ("harvest", "calibrate") else "firstfruits"


def _tier_step(prev_tier: str, streak: int) -> str:
    i = TIERS.index(prev_tier) if prev_tier in TIERS else 0
    if streak >= ADVANCE_STREAK and i < len(TIERS) - 1:
        return TIERS[i + 1]
    if streak <= -REGRESS_DECLINE and i > 0:                        # ease down only on a LONG decline
        return TIERS[i - 1]
    return TIERS[i]


def step(state: Optional[Dict[str, Any]], signals: Dict[str, Any]) -> Dict[str, Any]:
    """The one transition: prior client state + today's signals → the next state + ONE next step. PURE
    and STATELESS — nothing is stored; the returned state is the client's to keep on its own device."""
    prev = state if isinstance(state, dict) else {}
    prev_phase = prev.get("phase") if prev.get("phase") in PHASES else "calibrate"
    prev_tier = prev.get("tier") if prev.get("tier") in TIERS else "milk"
    try:
        prev_streak = int(prev.get("streak") or 0)
    except (TypeError, ValueError):
        prev_streak = 0
    try:
        day = int(prev.get("day") or 0) + 1
    except (TypeError, ValueError):
        day = 1

    a = assess(signals)
    # the streak counts fruit-bearing days up, chaff days down, and align holds it steady (grace, not
    # a ladder): a single hard day does not undo a season, and a season is not built in a day.
    streak = prev_streak + (1 if a["state"] == "fruit" else -1 if a["state"] == "chaff" else 0)
    phase = _phase_after(prev_phase, a["state"])
    tier = _tier_step(prev_tier, streak)
    pw = _PHASE_WORD[phase]
    next_state = {"day": day, "phase": phase, "tier": tier, "streak": streak, "state": a["state"]}
    return {
        "generated": False,
        "assess": a,
        "next_state": next_state,
        "advanced": tier != prev_tier and TIERS.index(tier) > TIERS.index(prev_tier),
        "step": {"phase": phase, "invitation": pw[1], "word": {"ref": pw[0]},
                 "flow_note": (f"your {a['flow']['weakest']} is the weakest leg today — tend it"
                               if a["flow"]["balance"] < 0.5 else "spirit, mind, and body are near in true")},
        "note": ("The Plow works the field; it does not judge the farmer. This reflects your own signals "
                 "and points to Christ — it keeps nothing, and it is not a verdict on your soul."),
        "held": "Nothing here is stored on the server. Your walk lives on your device.",
    }


def blank() -> Dict[str, Any]:
    """A fresh field, for a first-time device with no state yet."""
    return {"day": 0, "phase": "calibrate", "tier": "milk", "streak": 0, "state": "align"}
