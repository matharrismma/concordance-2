"""Concordance Conductor — a gated micro-agent engine for manufacturing.

`reference.py` is the canonical behavior (stdlib-only, patched against the 2026-08-24 red team).
The production package connects to the deployed Concordance engine (gates delegate to the kernel's
attest_red / attest_floor / validate_packet as a manufacturing DOMAIN PROFILE under the kernel RED);
it never rebuilds it. See conductor/CANON_CORRECTIONS.md for what the red team corrected and why.
"""
