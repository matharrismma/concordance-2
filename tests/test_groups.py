"""Groups — pseudonymous shared-study groups (Arc 4 community).

Proves: create/discover-by-topic/join/contribute; membership is pseudonymous and deduped; the public
view exposes HANDLES only (never member ids / PII); contributions are attributed + land in the shared
study (superposition). Hermetic (tmp data dir). Runs under pytest OR directly.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
_TMP = tempfile.mkdtemp(prefix="nh-groups-")
os.environ["CONCORDANCE_DATA_DIR"] = _TMP
os.environ["CONCORDANCE_GROUPS_DIR"] = _TMP + "/groups"

from concordance import groups  # noqa: E402


def test_create_and_discover_by_topic():
    g = groups.create_group("The Gospel of John", description="reading John together",
                            creator_id="nh_abc", handle="Pilgrim")
    assert g["ok"] and g["topic"] == "The Gospel of John"
    assert g["member_count"] == 1 and g["members"][0]["role"] == "founder"
    hit = groups.list_groups("john")
    assert any(x["id"] == g["id"] for x in hit["groups"])   # discovered by topic substring
    assert groups.list_groups("nonexistent-topic")["total"] == 0


def test_public_view_hides_ids_and_pii():
    g = groups.create_group("Psalms", creator_id="nh_secret_fingerprint_xyz", handle="Asaph")
    full = groups.get_group(g["id"])
    blob = str(full)
    assert "nh_secret_fingerprint_xyz" not in blob   # member id NEVER surfaced
    assert full["members"][0]["handle"] == "Asaph"    # only the handle is public
    assert "id" not in full["members"][0]


def test_join_is_pseudonymous_and_deduped():
    g = groups.create_group("Romans", creator_id="nh_1", handle="Paul")
    groups.join_group(g["id"], member_id="nh_2", handle="Phoebe")
    again = groups.join_group(g["id"], member_id="nh_2", handle="Phoebe")   # idempotent
    assert again["member_count"] == 2
    assert {m["handle"] for m in again["members"]} == {"Paul", "Phoebe"}


def test_contribute_lands_in_shared_study_attributed():
    g = groups.create_group("Grace", creator_id="nh_1", handle="Mercy")
    r = groups.contribute(g["id"], member_id="nh_1", handle="Mercy",
                          text="Ephesians 2:8 — by grace you have been saved through faith.",
                          kind="verse", refs=["Ephesians 2:8"])
    assert r["ok"] and r["by"] == "Mercy"
    full = groups.get_group(g["id"])
    assert full["card_count"] == 1
    card = full["cards"][0]
    assert "Ephesians 2:8" in card["text"] and card["source"] == "member:Mercy"


def test_handle_is_sanitized_never_pii_shaped():
    g = groups.create_group("Prayer", creator_id="nh_1", handle="  <script>evil@email.com  ")
    # angle brackets/@ stripped to a safe display pseudonym; empty falls back to 'anon'
    h = g["members"][0]["handle"]
    assert "<" not in h and ">" not in h
    assert groups.create_group("X", handle="")["members"][0]["handle"] == "anon"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} group tests passed — connect by topic, pseudonymous, no PII, attributed.")
