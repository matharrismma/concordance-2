"""The theory map's interactive layer — the contract between the drawing and the cards.

Every one of these guards a defect that was found by DRIVING the live page on 2026-08-03, not by
reading the source. They are here because the source read correctly in each case:

  * the cells carry data-i, an index into a payload emitted further down the same page. Nothing
    checks that link at runtime -- a wrong index silently opens the wrong theory's card, which is
    the worst failure this page can have: a confident answer about the wrong thing.
  * the 'depth' angle sorts by how much a card says beyond the template. _depth() clamps that at
    400 characters because it answers "is this a stub?"; 177 of 178 cards now peg at its ceiling,
    so sorting by it arranged the floor by TIE-BREAK and presented the result as a finding.
  * the controls describe dragging, zooming and clicking. With scripting off none of that works,
    so they must not paint at all -- a dead control that describes itself as live tells the reader
    the library is broken rather than that the feature is absent.

The page itself is generated, so these read the generated artifact the way a browser would.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import theory_map as T  # noqa: E402


def _floor():
    th = T._load(str(ROOT / "data" / "theory_cards.jsonl"))
    return th, T._edges(th)


def _payload(html):
    """Pull the THEORIES payload back out of the page exactly as the browser's parser would."""
    i = html.index("var TH = ")
    j = html.index("];", i)
    return json.loads(html[i + 9:j + 1].replace("<\\/", "</"))


def test_every_cell_indexes_the_right_theory():
    """data-i must be an index into the payload, and cell k must BE payload row k.

    This is the whole interaction in one assertion. If the drawing's order and the payload's order
    ever diverge, every card opens on a neighbour and nothing in the page complains.
    """
    th, edges = _floor()
    html = T.page(th, edges, T.gaps(th, edges))
    rows = _payload(html)

    body = html[html.index('<svg id="vortex"'):]
    body = body[:body.index("</svg>")]
    cells = re.findall(r'<polygon class="cell" data-i="(\d+)"[^>]*>'
                       r'<title>([^<]*)</title>', body)

    assert len(cells) == len(rows) == len(th), (len(cells), len(rows), len(th))
    assert [int(i) for i, _ in cells] == list(range(len(rows))), "data-i is not 0..n-1 in order"
    for (idx, title), row in zip(cells, rows):
        # the <title> is truncated for the tooltip; it must still be this row's own theory
        assert row["t"].startswith(title.replace("&amp;", "&")[:40].rstrip()), (idx, title, row["t"])


def test_the_red_rings_point_at_the_cells_they_ring():
    """A thin-ring marks a theory resting on almost nothing. It must ring THAT theory."""
    th, edges = _floor()
    html = T.page(th, edges, T.gaps(th, edges))
    rows = _payload(html)
    rings = [int(i) for i in re.findall(r'<polygon class="thinring" data-i="(\d+)"', html)]
    assert rings, "no thin rings drawn at all — the warning has gone silent"
    for i in rings:
        assert rows[i]["g"] <= 1, f"{rows[i]['t']} is ringed as thin but holds {rows[i]['g']}"
    thin = [k for k, r in enumerate(rows) if r["g"] <= 1]
    assert sorted(rings) == sorted(thin), "a thin theory exists that carries no ring"


def test_every_card_can_actually_be_explained():
    """The card renders title, section, domain, calibration, degree, substance and body.

    A blank in any of them is a card that opens and says nothing, which is worse than a cell that
    does not open: the reader concludes the theory is empty rather than that the page failed.
    """
    th, edges = _floor()
    rows = _payload(T.page(th, edges, T.gaps(th, edges)))
    for r in rows:
        for field in ("t", "s", "c", "d"):
            assert str(r[field]).strip() not in ("", "?"), (r["t"], field, r[field])
        assert len(r["b"].strip()) > 80, f"{r['t']} has no body to show"
        assert isinstance(r["g"], int) and r["g"] >= 0
        assert isinstance(r["w"], int) and r["w"] > 0
        for rel in r["r"]:
            assert len(rel) == 2 and rel[0].strip() and rel[1].strip(), (r["t"], rel)


def test_the_depth_angle_is_not_flat():
    """REGRESSION. _substance must keep its range, or the 'depth' spiral asserts an order that isn't there.

    Measured 2026-08-03: _depth() saturates, 177/178 cards sit at exactly 1.0. Sorting on that put
    the floor in title order and drew it as a finding. _substance is the same count unclamped;
    if anyone gives it a ceiling again, this fails.
    """
    th, _ = _floor()
    w = sorted(T._substance(c) for c in th.values())
    assert len(set(w)) > len(w) * 0.5, f"only {len(set(w))} distinct values across {len(w)} cards"
    assert w[-1] > w[0] * 3, f"range {w[0]}..{w[-1]} is too flat to order by"
    # and the clamped one is still clamped — it has a different job (brightness), keep it honest
    assert max(T._depth(c) for c in th.values()) <= 1.0


def test_the_map_is_whole_with_scripting_off():
    """The drawing must be complete before a single line of JavaScript runs.

    This library is for people whose only device may be old, borrowed or locked down. A page that
    is blank without JavaScript has chosen who it serves.
    """
    th, edges = _floor()
    html = T.page(th, edges, T.gaps(th, edges))
    nojs = re.sub(r"<script\b.*?</script>", "", html, flags=re.S | re.I)

    assert '<svg id="vortex"' in nojs
    assert nojs.count('class="cell"') == len(th), "cells are drawn by script, not by the server"
    assert nojs.count("<path d=") == len(edges), "relations are drawn by script, not by the server"
    assert 'role="img"' in nojs and "aria-label=" in nojs

    # ...and no control may paint, because none of them would work
    assert ".controls,.ifjs{display:none}" in nojs
    assert not re.search(r'class=["\'][^"\']*\bready\b', nojs), "a control is revealed without JS"


def test_the_payload_cannot_break_out_of_its_script_tag():
    """A card body containing </script> would end the block and spill the corpus into the page."""
    th, edges = _floor()
    html = T.page(th, edges, T.gaps(th, edges))
    block = html[html.index("var TH = "):]
    block = block[:block.index("</script>")]
    assert "</" not in block.split("];", 1)[0], "an unescaped </ survives inside the payload"
