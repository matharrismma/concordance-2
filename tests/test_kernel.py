"""THE GATE KERNEL — the five moves and the nine-field record, enforced as pure runtime doctrine.

Matt, 2026-07-25: "This must remain in all decisions." These tests hold the kernel to the whole of
it — type every artifact, verify only the verifiable (a system ERROR is never a false verdict),
preserve the nine-field trail, and NEVER silently upgrade authority (only a witnessed, evidenced gate
reaches 'verified'; never self-confirm). Pure — no corpus, no I/O.
"""
from concordance import kernel


# ── move 2: the classifier types the six kinds ──────────────────────────────────────────────────
def test_classify_types_the_six_kinds():
    assert kernel.classify({"generated": True, "authority_tier": "primary"}) == "generated_draft"  # generation wins
    assert kernel.classify({"code": "rm -rf /"}) == "executable"
    assert kernel.classify({"authority_tier": "user"}) == "user_note"
    assert kernel.classify({"authority_tier": "member"}) == "community"
    assert kernel.classify({"lifecycle_stage": "public_review"}) == "community"
    assert kernel.classify({"authority_tier": "primary_pd", "url": "https://loc.gov/x"}) == "source"
    assert kernel.classify({"claim": "the sky is green"}) == "claim"
    assert kernel.classify({"claim": "x"}, hint="source") == "source"          # a valid hint wins


# ── the three-state verdict ─────────────────────────────────────────────────────────────────────
def test_confirmed_only_with_evidence_an_independent_witness_and_the_wait():
    r = kernel.gate({"claim": "2+2=4"}, evidence="HOLDS", witness="checker", author="proposer",
                    wait_satisfied=True, in_kind_checked=True)
    assert r.verdict == "CONFIRMED" and r.authority_out == "verified"
    assert "WITNESS" in r.passed and "WAIT" in r.passed and "VERIFY" in r.passed


def test_never_self_confirm():
    # the thing that produced the artifact can never be the thing that confirms it
    r = kernel.gate({"claim": "trust me"}, evidence="HOLDS", witness="alice", author="alice",
                    in_kind_checked=True)
    assert r.verdict == "QUARANTINE" and r.authority_out != "verified"
    assert "WITNESS" in r.failed
    assert any("self-confirmation" in a for a in r.assumptions)


def test_a_system_error_is_never_a_false_verdict():
    for ev in ("ERROR", "SYSTEM_ERROR", "INCOMPLETE"):
        r = kernel.gate({"claim": "x"}, evidence=ev, witness="w", author="a")
        assert r.verdict == "QUARANTINE", f"{ev} must quarantine, not reject"
        assert r.verdict != "REJECT"
    r2 = kernel.gate({"claim": "x"}, error="verifier crashed")
    assert r2.verdict == "QUARANTINE"


def test_a_real_mismatch_or_retraction_rejects():
    assert kernel.gate({"claim": "2+2=5"}, evidence="BROKEN").verdict == "REJECT"
    assert kernel.gate({"claim": "x", "retracted": True}).verdict == "REJECT"
    assert kernel.gate({"claim": "x"}, contradicts=True).verdict == "REJECT"


# ── move 5: monotonic authority — never launder low into high ────────────────────────────────────
def test_born_quarantined_kinds_enter_quarantined_regardless_of_claimed_authority():
    # a community card that CLAIMS verified, with no gate, is capped to quarantined — no laundering
    r = kernel.gate({"authority_tier": "member", "claim": "our doctrine is true", "url": "http://x"},
                    authority_in="verified")
    assert r.verdict == "QUARANTINE" and r.authority_out == "quarantined"


def test_generated_material_never_becomes_authority_by_itself():
    r = kernel.gate({"generated": True, "claim": "an LLM said so"}, authority_in="verified")
    assert r.kind == "generated_draft" and r.authority_out == "quarantined"


def test_citing_makes_a_source_cited_never_verified():
    # a curated source with provenance is CITABLE — but a citation is not a proof
    r = kernel.gate({"authority_tier": "primary_pd", "url": "https://loc.gov/x"}, authority_in="quarantined")
    assert r.verdict == "QUARANTINE" and r.authority_out == "cited"
    # and no non-gate op may reach verified
    assert not kernel.monotonic_ok("cite", "cited", "verified")
    assert not kernel.monotonic_ok("seal", "quarantined", "verified")
    assert not kernel.monotonic_ok("popularity", "cited", "verified")
    assert kernel.monotonic_ok("gate", "quarantined", "verified")        # only the gate raises
    assert kernel.monotonic_ok("cite", "quarantined", "cited")           # cited is free (asserts no proof)


# ── move 4: the nine-field trail is always present ───────────────────────────────────────────────
def test_every_verdict_writes_the_nine_field_record():
    fields = ("entered", "kind", "authority_in", "passed", "failed",
              "assumptions", "changed", "preserved", "safe_next")
    for r in (kernel.gate({"claim": "x"}, evidence="HOLDS", witness="b", author="a", in_kind_checked=True),
              kernel.gate({"claim": "x"}),
              kernel.gate({"claim": "x", "retracted": True})):
        d = r.to_dict()
        for f in fields:
            assert f in d, f"missing gate-record field {f!r}"
        assert d["verdict"] in kernel.VERDICTS
        assert d["authority_out"] in kernel.AUTHORITY


def test_in_kind_lookup_is_recorded_as_an_assumption_when_absent():
    r = kernel.gate({"claim": "x"}, evidence="HOLDS", witness="b", author="a", in_kind_checked=False)
    assert any("in-kind" in a for a in r.assumptions)


def test_doctrine_publishes_the_five_moves_and_the_covenant():
    d = kernel.doctrine()
    assert len(d["five_moves"]) == 5 and len(d["agent_covenant"]) == 8
    assert set(d["kinds"]) == set(kernel.KINDS)
    assert d["authority_lattice"] == list(kernel.AUTHORITY)
