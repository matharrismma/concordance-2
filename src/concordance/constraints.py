"""MORAL CONSTRAINTS — the RED non-negotiables and FLOOR boundaries, scanned against decision CONTENT.

The gate kernel enforces AUTHORITY discipline (nothing launders quarantined → verified). But authority
is not the only floor: a proposal can be perfectly well-typed and still describe a wrong. The governance
verifier today is purely STRUCTURAL — it checks that *some* red_items were declared, never what is IN
the decision — so a proposal that literally describes fake testimonials or preying on the vulnerable
passes. This closes that gap. Ported from the Lighthouse four-gates-analyzer, the eight RED
non-negotiables and six FLOOR boundaries, each a {id, name, patterns, cite, severity} record scanned
against the decision's own words.

  RED   → a hard floor. A hit REJECTS (a category the engine will not certify), with a citation.
  FLOOR → protective boundaries. `error` REJECTS; `warn` passes WITH a flag (a concern named, not a veto).

Deterministic, no I/O. Keyword/phrase patterns are word-bounded to hold the false-positive rate down;
this scans DECISION content on the governance path, not arbitrary corpus. The `cite` travels as data;
whether to DISPLAY a Scripture citation is a surface choice (the secular .com core keeps it off — see
verifiers/governance).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

# Each constraint: patterns are matched case-insensitively with word boundaries. Multi-word phrases are
# preferred over single ambiguous words to keep false positives low ("force" alone would catch
# "workforce"; "under duress" / "or else" would not).
RED_CONSTRAINTS: Tuple[Dict[str, Any], ...] = (
    {"id": "RED-001", "name": "deception",
     "patterns": (r"fake (?:testimonial|review|evidence|account|identit)", r"forged?\b", r"falsif(?:y|ied|ying)",
                  r"fabricat(?:e|ed|ing) (?:evidence|data|proof|results?)", r"\bdeceive\b", r"mislead(?:ing)?\b",
                  r"cover(?:ed|ing)? up\b", r"pass(?:ing)? off .* as", r"astroturf"),
     "cite": "Proverbs 12:22; Ephesians 4:25 — lying lips are an abomination; speak truth"},
    {"id": "RED-002", "name": "coercion",
     "patterns": (r"\bcoerc(?:e|ed|ion)\b", r"under duress\b", r"\bblackmail\b", r"\bextort", r"\bthreaten(?:ing)?\b",
                  r"or else\b", r"forc(?:e|ed|ing) (?:them|him|her|people|users?) to", r"compel(?:led)? .* against"),
     "cite": "Philemon 1:14 — that the good you do be of your own free will, not by compulsion"},
    {"id": "RED-003", "name": "exploitation",
     "patterns": (r"\bexploit(?:ing|ation)?\b", r"prey(?:ing)? on\b", r"take advantage of (?:the )?(?:vulnerable|poor|elderly|desperate)",
                  r"\bpredatory\b", r"\busury\b", r"sweatshop", r"human trafficking", r"\btraffick"),
     "cite": "Proverbs 22:16; James 5:4 — oppressing the poor to enrich oneself comes to want"},
    {"id": "RED-004", "name": "injustice",
     "patterns": (r"\bdefraud\b", r"withhold(?:ing)? (?:their )?wages", r"deny(?:ing)? (?:fair )?wages", r"\boppress",
                  r"rig(?:ged|ging)? the\b", r"cheat(?:ing)? (?:the|them|customers|people)", r"unjust weight"),
     "cite": "Leviticus 19:13; Deuteronomy 25:15 — do not defraud; a just weight and measure"},
    {"id": "RED-005", "name": "identity branding",
     "patterns": (r"\bbrand (?:people|persons?|humans?|users?)\b", r"mark (?:people|them|everyone) (?:to|so they can) (?:buy|sell|trade)",
                  r"required (?:mark|tattoo|implant|chip) to (?:buy|sell|participate|access)", r"biometric mark to"),
     "cite": "Revelation 13:16-17 — a mark to buy or sell is the counterfeit's seal, never ours"},
    {"id": "RED-006", "name": "harm to children",
     "patterns": (r"harm(?:ing)? (?:children|minors|kids)\b", r"exploit(?:ing)? (?:children|minors|kids)\b",
                  r"expos(?:e|ing) (?:children|minors|kids) to\b", r"target(?:ing)? (?:children|minors|kids) (?:for|with)"),
     "cite": "Matthew 18:6 — better a millstone than to cause a little one to stumble"},
    {"id": "RED-007", "name": "suppression of accountability",
     "patterns": (r"silenc(?:e|ing) (?:the )?whistleblower", r"retaliat(?:e|ing|ion) against", r"suppress(?:ing)? (?:dissent|criticism|the report)",
                  r"destroy(?:ing)? (?:the )?(?:evidence|records)", r"hide (?:the )?records\b", r"punish (?:those who|anyone who) report"),
     "cite": "Ephesians 5:11 — expose the works of darkness, do not partake in them"},
    {"id": "RED-008", "name": "self-referential authority",
     "patterns": (r"\bself-certif", r"answer to no one\b", r"no oversight\b", r"i alone (?:decide|am the authority|judge)",
                  r"accountable to no one\b", r"beyond question\b", r"cannot be (?:questioned|reviewed|appealed)"),
     "cite": "Proverbs 11:14 — in an abundance of counselors there is safety; no one is a law to himself"},
)

FLOOR_CONSTRAINTS: Tuple[Dict[str, Any], ...] = (
    {"id": "FLOOR-001", "name": "proportionality", "severity": "warn",
     "patterns": (r"disproportionate", r"excessive (?:force|penalt|punishment)", r"\boverkill\b"),
     "cite": "the punishment must fit — an eye for an eye BOUNDS retribution, it does not license excess"},
    {"id": "FLOOR-002", "name": "due process", "severity": "warn",
     "patterns": (r"without (?:a )?(?:trial|hearing|due process)", r"presum(?:e|ed) guilty", r"no (?:right of )?appeal\b",
                  r"guilty until"),
     "cite": "Deuteronomy 19:15; John 7:51 — the matter established by witnesses; hear before you judge"},
    {"id": "FLOOR-003", "name": "transparency", "severity": "warn",
     "patterns": (r"secret(?:ly)? (?:terms|clause|fee)", r"undisclosed (?:fee|term|risk)", r"hidden (?:fee|clause|cost)",
                  r"conceal(?:ing)? (?:from|the) (?:user|customer|member)"),
     "cite": "Luke 12:2 — nothing concealed that will not be made known; deal in the open"},
    {"id": "FLOOR-004", "name": "protection of the vulnerable", "severity": "warn",
     "patterns": (r"target(?:ing)? (?:the )?(?:elderly|disabled|widows?|orphans?|poor|homeless)",
                  r"take from (?:the )?(?:widow|orphan|poor)"),
     "cite": "James 1:27; Psalm 82:3 — defend the weak; religion pure is to care for widow and orphan"},
    {"id": "FLOOR-005", "name": "financial stability", "severity": "error",
     "patterns": (r"\bponzi\b", r"pyramid scheme", r"spend (?:it )?all\b", r"no (?:cash )?reserve", r"no (?:financial )?floor",
                  r"unsustainable (?:by design|but)", r"rob peter to pay paul"),
     "cite": "Proverbs 21:20; Luke 14:28 — the wise store a reserve; count the cost before you build"},
    {"id": "FLOOR-006", "name": "retention bounds", "severity": "warn",
     "patterns": (r"keep (?:it )?forever\b", r"indefinite retention", r"never delete", r"permanent(?:ly)? (?:record|store) (?:everything|all)",
                  r"retain (?:all data )?indefinitely"),
     "cite": "keep only what stewardship requires; unbounded retention is a burden and a risk, not a virtue"},
)

_RED = [(c, re.compile("|".join(c["patterns"]), re.I)) for c in RED_CONSTRAINTS]
_FLOOR = [(c, re.compile("|".join(c["patterns"]), re.I)) for c in FLOOR_CONSTRAINTS]


def _hit(constraint: Dict[str, Any], match: "re.Match") -> Dict[str, Any]:
    return {"id": constraint["id"], "name": constraint["name"], "matched": match.group(0).strip()[:60],
            "cite": constraint["cite"], "severity": constraint.get("severity", "red")}


def scan(text: str) -> Dict[str, Any]:
    """Scan decision CONTENT for the RED / FLOOR constraints. Returns the hits by band and the WORST
    disposition: 'red' (a RED hit) or 'error' (a FLOOR error) both REJECT; 'warn' passes with a flag;
    None is clean. Nothing here reads the person — only the words of the proposal."""
    t = text or ""
    red = [_hit(c, m) for c, rx in _RED if (m := rx.search(t))]
    floor_hits = [_hit(c, m) for c, rx in _FLOOR if (m := rx.search(t))]
    floor_error = [h for h in floor_hits if h["severity"] == "error"]
    floor_warn = [h for h in floor_hits if h["severity"] == "warn"]
    if red:
        worst = "red"
    elif floor_error:
        worst = "error"
    elif floor_warn:
        worst = "warn"
    else:
        worst = None
    return {"red": red, "floor_error": floor_error, "floor_warn": floor_warn, "worst": worst,
            "rejects": bool(red or floor_error), "warnings": floor_warn}


def catalog() -> Dict[str, Any]:
    """The published catalog — for the read surface and the doctrine (agents read the law)."""
    return {
        "red": [{"id": c["id"], "name": c["name"], "cite": c["cite"]} for c in RED_CONSTRAINTS],
        "floor": [{"id": c["id"], "name": c["name"], "severity": c.get("severity", "warn"),
                   "cite": c["cite"]} for c in FLOOR_CONSTRAINTS],
        "note": "RED is a non-negotiable — a hit refuses. FLOOR 'error' refuses; FLOOR 'warn' flags. "
                "These scan a decision's own words; they never read or judge the person.",
    }
