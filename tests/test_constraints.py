"""MORAL CONSTRAINTS — the RED non-negotiables + FLOOR boundaries, scanned against decision CONTENT (LH-2).

The gate kernel enforced AUTHORITY discipline but not moral CONTENT: a well-typed proposal that
literally describes fake testimonials or preying on the vulnerable passed. This closes that. A RED hit
or a FLOOR 'error' REJECTS (with a citation); a FLOOR 'warn' rides along as a named concern. It scans
the proposal's own words — never the person. Pure.
"""
from concordance import constraints, kernel


# ── the scanner in isolation ──────────────────────────────────────────────────────────────────────
def test_red_non_negotiables_fire_on_content():
    assert constraints.scan("we will use fake testimonials to boost trust")["worst"] == "red"
    assert constraints.scan("prey on the vulnerable who can't pay")["worst"] == "red"
    assert constraints.scan("this decision is beyond question and answers to no one")["worst"] == "red"
    r = constraints.scan("we withhold their wages until they comply")
    assert r["rejects"] and r["red"][0]["cite"]                # a citation travels with the hit


def test_floor_error_rejects_but_floor_warn_only_flags():
    err = constraints.scan("the plan is a ponzi with no reserve")
    assert err["worst"] == "error" and err["rejects"]
    warn = constraints.scan("the terms are hidden fees the user won't see")
    assert warn["worst"] == "warn" and not warn["rejects"] and warn["warnings"]


def test_a_clean_proposal_is_clean():
    r = constraints.scan("we will lend tools to neighbors and record who borrowed what, openly")
    assert r["worst"] is None and not r["rejects"] and not r["warnings"]


def test_catalog_publishes_eight_red_and_six_floor():
    c = constraints.catalog()
    assert len(c["red"]) == 8 and len(c["floor"]) == 6
    assert any(f["severity"] == "error" for f in c["floor"])   # financial-stability is the hard floor


# ── the kernel integration ────────────────────────────────────────────────────────────────────────
def test_kernel_rejects_a_proposal_that_describes_a_wrong():
    rec = kernel.gate({"claim": "a business plan"}, content="we exploit the desperate and fake the reviews")
    assert rec.verdict == "REJECT" and "RED" in rec.failed
    assert any("RED-" in n for n in rec.assumptions)


def test_kernel_carries_a_warn_concern_without_vetoing():
    # a FLOOR 'warn' (transparency) does not reject — it rides along as a named warning
    rec = kernel.gate({"authority_tier": "primary", "url": "http://x", "claim": "a source"},
                      content="the terms include an undisclosed fee")
    assert rec.verdict != "REJECT" and rec.warnings
    assert any("FLOOR-003" in w or "transparency" in w for w in rec.warnings)


def test_kernel_without_content_is_unchanged():
    # the moral scan is opt-in; a gate with no content behaves exactly as before
    rec = kernel.gate({"claim": "2+2=4"}, evidence="HOLDS", witness="b", author="a", in_kind_checked=True)
    assert rec.verdict == "CONFIRMED" and rec.warnings == ()
