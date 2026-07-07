"""Grid atlas — the read-only exploration, rendering, and CLI layer over the scaffold.

Split out of grid.py (which kept the scaffold data, the live query API used by
record/ledger/api/mcp — axis_view / overview / dimension_axes / check_dimension_members —
and the axis write path). NONE of this module is on the engine's live path: it is the
human-facing analysis tooling — the prose->dimensions predictor, adjacency/depth queries,
the umbrella-coherence audit, the markdown renderers, and the CLI. Imported on demand for
exploration and audits, never at engine boot.

    python -m concordance.grid_atlas [depth | adjacent <axis> | dimension <dim>]
"""
from __future__ import annotations

from typing import Dict, FrozenSet, List, Tuple

from .grid import ALIASES, AXIS_DIMENSIONS, DIMENSIONS, UMBRELLAS, adjacent, dimension_axes


def is_alias(name: str) -> bool:
    """True if `name` is a known alias of another canonical axis."""
    return name in ALIASES


def canonical_axes() -> Dict[str, FrozenSet[str]]:
    """AXIS_DIMENSIONS with all aliases collapsed to their canonical
    entries. Useful for structural audits where aliases would create
    false redundancy clusters."""
    return {
        name: dims for name, dims in AXIS_DIMENSIONS.items()
        if not is_alias(name)
    }


def axis_dimensions(axis: str) -> FrozenSet[str]:
    """Dimensions an axis sits on. Raises KeyError for unknown axes."""
    return AXIS_DIMENSIONS[axis]


# ── Prose → dimensions (owned, deterministic) ───────────────────────────
# A keyword layer that places a plain-language claim on the scaffold: which
# dimensions it sits on. Owned (no LLM), broadened so far more real claims
# place. Multi-axis overlap is expected and fine.
_AXIS_STEMS: Dict[str, Tuple[str, ...]] = {
    "encoding":              ("encod", "encrypt", "decod", "symbol", "cipher", "code", "languag",
                              "word", "letter", "alphabet", "translat", "data", "informat", "messag", "text"),
    "metabolism":            ("metabol", "growth", "decay", "nutri", "energ", "food", "digest",
                              "cell", "flow", "transform", "burn", "calorie", "grow", "ferment", "photosynth"),
    "reasoning":             ("reason", "logic", "proof", "comput", "calculat", "infer", "math",
                              "equal", "sum", "number", "theorem", "equation", "deriv", "prime",
                              "arithmetic", "prov", "deduc", "solve", "algebra"),
    "physical_substance":    ("physic", "matter", "substanc", "spatial", "geometr", "light", "speed",
                              "mass", "force", "veloci", "atom", "particle", "wave", "gravit", "heat",
                              "temperatur", "distanc", "length", "meter", "molecul", "element", "pressure", "volume"),
    "authority_trust":       ("author", "trust", "consent", "consensus", "legitim", "sign", "law",
                              "govern", "vote", "witness", "testimon", "source", "cite", "scriptur", "verse"),
    "time_sequence":         ("time", "sequenc", "before", "after", "deadline", "period", "date",
                              "year", "day", "when", "schedul", "calendar", "histor", "event", "clock", "duration"),
    "conservation_balance":  ("balanc", "conserv", "equilibri", "invariant", "preserv", "momentum",
                              "charge", "budget", "account", "ledger", "total", "sum to", "first law"),
    # Dimensions added after the original seven — synonym stems so they place.
    "uncertainty":           ("uncertain", "probab", "random", "stochast", "risk", "confidence",
                              "estimat", "chance", "odds", "likely", "p-value", "noise", "variance"),
    "discreteness":          ("discret", "integer", "countab", "quantiz", "digital", "granular",
                              "count", "whole number", "digit", "unit", "step"),
    "order":                 ("order", "rank", "sort", "hierarch", "ordinal", "precede", "greater than", "less than"),
    "symmetry":              ("symmetr", "reflect", "rotation", "mirror", "group-theor"),
}


def predict_dimensions(text: str) -> FrozenSet[str]:
    """Place a plain-language claim on the scaffold: which dimensions it sits on.

    Three owned signals, unioned: (1) per-dimension keyword stems, (2) a literal
    dimension name in the text, (3) a domain name in the text -> that domain's
    dimensions. Returns the (possibly empty) set of dimensions. Deterministic,
    no LLM. Only the runtime DIMENSIONS / AXIS_DIMENSIONS are consulted, so any
    axis added at runtime participates automatically."""
    q = (text or "").lower()
    predicted: set = set()
    if q:
        for ax, stems in _AXIS_STEMS.items():
            if any(s in q for s in stems):
                predicted.add(ax)
        for dim in DIMENSIONS:
            if dim in q or dim.replace("_", " ") in q:
                predicted.add(dim)
        for dom, dims in AXIS_DIMENSIONS.items():
            stem = dom[:6] if len(dom) >= 6 else dom
            if dom in q or (len(stem) >= 5 and stem in q):
                predicted.update(dims)
    # Only keep dimensions that actually exist in the live scaffold.
    return frozenset(d for d in predicted if d in DIMENSIONS)


def deep_axes(min_dimensions: int = 3) -> List[Tuple[str, int]]:
    """Axes ranked by dimension count, descending."""
    ranked = [(a, len(d)) for a, d in AXIS_DIMENSIONS.items() if len(d) >= min_dimensions]
    ranked.sort(key=lambda t: (-t[1], t[0]))
    return ranked


def verify_umbrella_coherence() -> Dict[str, List[str]]:
    """Verify each umbrella's dimensions cover the union of its subsystems' dimensions.

    The doctrinal claim: an umbrella subsumes its subsystems. If `agriculture` sits on
    `time_sequence` but the `biology` umbrella doesn't, the umbrella isn't actually carrying
    what its children carry. Returns a dict umbrella name → list of missing dimensions;
    empty list = coherent, empty dict = all umbrellas coherent."""
    breaks: Dict[str, List[str]] = {}
    for parent, children in UMBRELLAS.items():
        if not children:
            continue
        if parent not in AXIS_DIMENSIONS:
            continue
        parent_dims = AXIS_DIMENSIONS[parent]
        children_union = frozenset()
        for c in children:
            if c in AXIS_DIMENSIONS:
                children_union = children_union | AXIS_DIMENSIONS[c]
        missing = sorted(children_union - parent_dims)
        if missing:
            breaks[parent] = missing
    return breaks


# ── Rendering ──────────────────────────────────────────────────────────

def render_matrix() -> str:
    """Markdown matrix: rows = axes (alphabetical), cols = dimensions."""
    axes = sorted(AXIS_DIMENSIONS.keys())
    short = {
        "encoding": "enc",
        "metabolism": "met",
        "reasoning": "rsn",
        "physical_substance": "phy",
        "authority_trust": "aut",
        "time_sequence": "tim",
        "conservation_balance": "csv",
        "uncertainty": "unc",
        "discreteness": "dsc",
        "order": "ord",
        "symmetry": "sym",
    }
    header = "| axis | " + " | ".join(short[d] for d in DIMENSIONS) + " | depth |"
    sep = "|------|" + "|".join(["----"] * len(DIMENSIONS)) + "|------:|"
    rows = []
    for a in axes:
        dims = AXIS_DIMENSIONS[a]
        cells = [" x  " if d in dims else "    " for d in DIMENSIONS]
        rows.append(f"| {a:<22} | " + " | ".join(cells) + f" | {len(dims):>5} |")
    return "\n".join([header, sep, *rows])


def render_depth() -> str:
    """Axes ranked by dimensional depth."""
    ranked = sorted(AXIS_DIMENSIONS.items(), key=lambda t: (-len(t[1]), t[0]))
    lines = [f"{len(dims)}  {axis:<22} {' '.join(sorted(dims))}" for axis, dims in ranked]
    return "\n".join(lines)


def render_adjacent(axis: str) -> str:
    """Adjacency report for a single axis."""
    if axis not in AXIS_DIMENSIONS:
        return f"unknown axis: {axis}"
    own = sorted(AXIS_DIMENSIONS[axis])
    lines = [f"{axis} sits on: {', '.join(own)}", "", "shares dimensions with:"]
    for other, shared in adjacent(axis):
        lines.append(f"  {len(shared)}  {other:<22} {' '.join(sorted(shared))}")
    return "\n".join(lines)


def render_dimension(dim: str) -> str:
    """All axes on a given dimension."""
    if dim not in DIMENSIONS:
        return f"unknown dimension: {dim}; valid: {', '.join(DIMENSIONS)}"
    axes = dimension_axes(dim)
    return f"axes on {dim} ({len(axes)}):\n" + "\n".join(f"  {a}" for a in axes)


# ── CLI ────────────────────────────────────────────────────────────────

def _main(argv: List[str]) -> int:
    if len(argv) <= 1:
        print(render_matrix())
        return 0
    cmd = argv[1]
    if cmd == "depth":
        print(render_depth())
        return 0
    if cmd == "adjacent" and len(argv) >= 3:
        print(render_adjacent(argv[2]))
        return 0
    if cmd == "dimension" and len(argv) >= 3:
        print(render_dimension(argv[2]))
        return 0
    print("usage: python -m concordance.grid_atlas [depth | adjacent <axis> | dimension <dim>]")
    return 2


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv))
