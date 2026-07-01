"""Port the Read-school curriculum (window.NH_UNITS) -> data/curriculum/read_en.json.

CONDUIT, NOT SOURCE: the units are copied VERBATIM. We locate the `window.NH_UNITS = [ ... ]`
assignment in the 1.0 school.html, take the JSON array EXACTLY as written (json.JSONDecoder().
raw_decode from the '[' offset — no re-serialization surprises, no paraphrase), and persist it.
The curriculum is the operator's authored teaching; the engine finds and presents it, it never
rewrites a lesson. Expect ~35 units. Deterministic, no network.

    python -m tools.migrate_school [--src <path to school.html>] [--out <read_en.json>]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from concordance import coach  # noqa: E402

# The 1.0 offline reading school; the units live in a `window.NH_UNITS = [ ... ]` assignment.
_DEFAULT_SRC = Path(
    "C:/Users/hdven/OneDrive/Documents/Claude/Projects/Lighthouse/site/school.html"
)
_MARKER = "window.NH_UNITS"


def extract_units(html: str) -> list:
    """Find `window.NH_UNITS = [ ... ]` and return the array parsed VERBATIM from the '[' offset."""
    i = html.find(_MARKER)
    if i < 0:
        raise ValueError(f"marker {_MARKER!r} not found in source")
    eq = html.find("=", i)
    if eq < 0:
        raise ValueError("no '=' after the NH_UNITS marker")
    br = html.find("[", eq)
    if br < 0:
        raise ValueError("no '[' opening the NH_UNITS array")
    units, _end = json.JSONDecoder().raw_decode(html[br:])  # verbatim, exactly as authored
    if not isinstance(units, list):
        raise ValueError("NH_UNITS did not decode to a list")
    return units


def build(src: Path, out: Path) -> int:
    html = src.read_text(encoding="utf-8")
    units = extract_units(html)
    out.parent.mkdir(parents=True, exist_ok=True)
    # A verbatim copy — same objects, canonical UTF-8 JSON. No field is added, dropped, or reworded.
    out.write_text(json.dumps(units, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(units)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Port the Read-school curriculum verbatim into 2.0.")
    ap.add_argument("--src", default=str(_DEFAULT_SRC), help="path to the 1.0 school.html")
    ap.add_argument("--out", default=None, help="output path (default: data/curriculum/read_en.json)")
    a = ap.parse_args(argv)
    out = Path(a.out) if a.out else coach._file()
    n = build(Path(a.src), out)
    print(f"wrote {n} curriculum units (verbatim) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
