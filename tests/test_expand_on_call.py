"""ONE MECHANISM, TWO PLANES — and the want list only when there is no way out.

Matt, 2026-08-01:
    "It should be the same just different planes."
    "The want list is for when we don't have internet. Otherwise, we just execute then and allow
     the user to assist."

WHAT WAS WRONG. `/ask` had run the tortoise for months; `/search` and the MCP `search` tool never
did. Proven live: `/search?q=Rigveda` returned 0, and two `/ask` calls later it returned three
public-domain Rigveda sources the tortoise had found and CARDED on the call. Same question, same
engine, two doors, two different answers — and the deaf one is the door agents use (~35% of
traffic). An agent got `count: 0` and concluded the library held nothing, while the other door was
busy acquiring it.

THE PLANE IS THE ONLY DIFFERENCE, and it is a real boundary rather than a label:
  human — the person's own ask authorises it; the card enters `public`.
  agent — the card enters `public_review`, which `corpus.is_public()` withholds from every public
          read path until a human looks at it. The agent still receives its answer.

That closes a live breach: `lifecycle_stage` was hardcoded `"public"`, so an agent calling the
`ask` tool minted straight into the shared keeping with no human ever seeing it — against the
covenant's "ask before writes".

AND THE WANT LIST IS THE OFFLINE QUEUE. Queueing something we could simply have fetched turns a
slower answer into a person's chore, which is backwards.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from concordance import corpus, expand, find  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402

DOC = {"title": "The Quintessence of the Rigveda", "url": "https://archive.org/details/xyz",
       "source": "Internet Archive", "license": "Public domain", "tier": "primary",
       "format": "text", "year": "1963"}


@pytest.fixture()
def offline(monkeypatch):
    monkeypatch.setenv("WEB_FIND_DISABLED", "1")


@pytest.fixture()
def online_with_a_find(monkeypatch, tmp_path):
    monkeypatch.delenv("WEB_FIND_DISABLED", raising=False)
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))

    def _fake(query, config, plane="human"):
        find._mint_doc(query, DOC, practical=False, plane=plane)
        return {"answer": None, "documents": [DOC], "source_note": "from the archives",
                "framed": "", "checks_verdict": None}

    monkeypatch.setattr(find, "find_and_check", _fake)


# ── the offline rule ───────────────────────────────────────────────────────────────────────────
def test_no_connection_is_the_only_thing_that_becomes_a_want(offline, monkeypatch, tmp_path):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    r = expand.expand("Rigveda", EngineConfig("secular"), plane="human")
    assert r["status"] == "queued", r
    assert r["want_id"]
    assert "connection" in r["message"].lower()


def test_looking_and_finding_nothing_is_not_a_want(monkeypatch, tmp_path):
    """Queueing this would ask a person to do what the miners just failed to do."""
    monkeypatch.delenv("WEB_FIND_DISABLED", raising=False)
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(find, "find_and_check", lambda *a, **k: None)

    r = expand.expand("a thing no archive holds", EngineConfig("secular"))
    assert r["status"] == "nothing_found"
    assert "want_id" not in r
    assert "invent" in r["message"]


def test_the_slow_lane_never_breaks_the_fast_one(monkeypatch, tmp_path):
    """A tortoise that raises must not take the caller down with it."""
    monkeypatch.delenv("WEB_FIND_DISABLED", raising=False)
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))

    def _boom(*a, **k):
        raise RuntimeError("the archives fell over")

    monkeypatch.setattr(find, "find_and_check", _boom)
    r = expand.expand("anything", EngineConfig("secular"))
    assert r["status"] == "nothing_found"


# ── the plane boundary ─────────────────────────────────────────────────────────────────────────
def test_a_humans_ask_authorises_itself(online_with_a_find):
    r = expand.expand("Rigveda", EngineConfig("secular"), plane="human")
    assert r["status"] == "acquired"
    assert r["held_for_review"] is False
    card = find._mint_doc("Rigveda", DOC, practical=False, plane="human")
    assert card["lifecycle_stage"] == "public"
    assert corpus.is_public(card) is True


def test_an_agents_acquisition_waits_for_a_human(online_with_a_find):
    """The agent gets its answer; the SHARED library waits. 'We ask the next human that looks.'"""
    r = expand.expand("Rigveda", EngineConfig("secular"), plane="agent")
    assert r["status"] == "acquired"
    assert r["held_for_review"] is True

    card = find._mint_doc("Rigveda", DOC, practical=False, plane="agent")
    assert card["lifecycle_stage"] == "public_review", (
        "an agent-plane acquisition must not enter the shared keeping unreviewed — "
        "lifecycle_stage was hardcoded 'public', which is how it did")
    assert corpus.is_public(card) is False, (
        "public_review must be withheld from every public read path — otherwise the plane is a "
        "label rather than a boundary")
    assert card.get("acquired_by_plane") == "agent"


def test_the_two_planes_differ_only_in_authority(online_with_a_find):
    """Same act, same card, same provenance — one field apart."""
    h = find._mint_doc("Rigveda", DOC, practical=False, plane="human")
    a = find._mint_doc("Rigveda", DOC, practical=False, plane="agent")
    for field in ("title", "shelf", "kind", "generated", "source"):
        assert h[field] == a[field], f"the planes must not change {field} — only who authorised it"
    assert h["lifecycle_stage"] != a["lifecycle_stage"]


def test_an_unknown_plane_falls_back_to_the_stricter_one(online_with_a_find):
    r = expand.expand("Rigveda", EngineConfig("secular"), plane="nonsense")
    assert r["plane"] == "human"          # normalised, never trusted as given


def test_an_empty_query_asks_nothing(monkeypatch, tmp_path):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    assert expand.expand("   ", EngineConfig("secular"))["status"] == "nothing_found"


def test_a_humans_ask_releases_what_an_agent_acquired(online_with_a_find, tmp_path, monkeypatch):
    """Withholding is a WAIT, not a grave.

    Caught on the live wire 2026-08-01: an agent-plane `Samkhya` acquisition held the cards in
    `public_review`; a following HUMAN /search returned count 0 with those very cards sitting in
    the store. The id was already present, so the mint was skipped, the stage never changed, and
    the material was invisible to everyone permanently. A person asking for exactly this thing IS
    the review the agent plane was waiting on.
    """
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    agent_card = find._mint_doc("Samkhya", DOC, practical=False, plane="agent")
    assert agent_card["lifecycle_stage"] == "public_review"
    assert corpus.is_public(agent_card) is False

    find._mint_doc("Samkhya", DOC, practical=False, plane="human")   # the next human looks

    store = tmp_path / "web_cache.jsonl"
    rows = [json.loads(l) for l in store.read_text(encoding="utf-8").splitlines() if l.strip()]
    held = [c for c in rows if c["id"] == agent_card["id"]]
    assert len(held) == 1, "promotion must not duplicate the card"
    assert held[0]["lifecycle_stage"] == "public", "a human's ask must release the held card"
    assert corpus.is_public(held[0]) is True


def test_promotion_never_disturbs_a_stewards_decision(tmp_path, monkeypatch):
    """Only public_review -> public. A retracted or quarantined card stays where it was put."""
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    store = tmp_path / "web_cache.jsonl"
    store.write_text(json.dumps({"id": "card_pd_x", "lifecycle_stage": "quarantine"}) + chr(10),
                     encoding="utf-8")
    assert find._promote_to_public(store, "card_pd_x") is False
    rows = [json.loads(l) for l in store.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert rows[0]["lifecycle_stage"] == "quarantine"


def test_a_held_acquisition_is_visible_to_a_human(tmp_path, monkeypatch):
    """A hold with no door is a grave, not a wait.

    The plane boundary worked — agent acquisitions really were withheld — but nothing SHOWED them
    to anyone: the review queue read only member-shelf drops. Measured live 2026-08-01: three
    Samkhya sources held in public_review, /curate/queue reporting a count of zero. Withholding is
    only legitimate if a person can see what is waiting.
    """
    from concordance import shelves
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    (tmp_path / "web_cache.jsonl").write_text(
        json.dumps({"id": "card_pd_held", "title": "A held source", "lifecycle_stage":
                    "public_review", "acquired_by_plane": "agent",
                    "source": {"label": "Internet Archive"}}) + chr(10), encoding="utf-8")

    q = shelves.review_queue()
    held = [i for i in q["items"] if i["card_id"] == "card_pd_held"]
    assert held, f"a held acquisition must appear in the one queue a human looks at: {q}"
    assert held[0]["kind"] == "acquisition"
    assert held[0]["waiting_on"] == "any human who looks"
    assert q["count"] >= 1


def test_a_public_acquisition_is_not_in_the_queue(tmp_path, monkeypatch):
    """Only what actually waits — a released card must not clutter the desk."""
    from concordance import shelves
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    (tmp_path / "web_cache.jsonl").write_text(
        json.dumps({"id": "card_pd_free", "title": "Released", "lifecycle_stage": "public"})
        + chr(10), encoding="utf-8")
    assert not [i for i in shelves.review_queue()["items"] if i["card_id"] == "card_pd_free"]


def _held(tmp_path, cid="card_pd_held"):
    (tmp_path / "web_cache.jsonl").write_text(
        json.dumps({"id": cid, "title": "A held source", "lifecycle_stage": "public_review",
                    "acquired_by_plane": "agent", "source": {"label": "Internet Archive"}})
        + chr(10), encoding="utf-8")
    return cid


def test_a_steward_can_release_a_held_acquisition(tmp_path, monkeypatch):
    """The queue must be a DOOR, not a window.

    Seeing what waits is only half of it. `curate` looked solely in drops.jsonl, so every attempt
    to release an acquisition answered "no such drop" — measured live 2026-08-01 with three Samkhya
    sources sitting on the desk and no way to act on any of them. Two stores, one act.
    """
    from concordance import shelves
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CONCORDANCE_KEEP_TOKEN", "t0ken-for-the-test")
    cid = _held(tmp_path)

    act = shelves.curate(cid, "promoted", "matt", "a real public-domain primary source",
                         token="t0ken-for-the-test")
    assert act["ok"], act
    assert act.get("kind") == "acquisition"

    rows = [json.loads(l) for l in (tmp_path / "web_cache.jsonl").read_text(
        encoding="utf-8").splitlines() if l.strip()]
    assert rows[0]["lifecycle_stage"] == "public", "promoting must actually release the card"
    assert not [i for i in shelves.review_queue()["items"] if i["card_id"] == cid],         "a released card must leave the desk"


def test_refusing_an_acquisition_is_recorded_not_erased(tmp_path, monkeypatch):
    from concordance import shelves
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CONCORDANCE_KEEP_TOKEN", "t0ken-for-the-test")
    cid = _held(tmp_path)

    act = shelves.curate(cid, "refused", "matt", "wrong edition, and the scan is unreadable",
                         token="t0ken-for-the-test")
    assert act["ok"] and act["reason"]
    rows = [json.loads(l) for l in (tmp_path / "web_cache.jsonl").read_text(
        encoding="utf-8").splitlines() if l.strip()]
    assert rows[0]["lifecycle_stage"] == "archived", "a refusal moves it aside; it never deletes"
    assert shelves.history(cid)["count"] == 1, "the act and its reason stay readable"


def test_an_acquisition_has_no_member_to_withdraw_it(tmp_path, monkeypatch):
    from concordance import shelves
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CONCORDANCE_KEEP_TOKEN", "t0ken-for-the-test")
    cid = _held(tmp_path)
    r = shelves.curate(cid, "withdrawn", "matt", "changed my mind", token="t0ken-for-the-test")
    assert not r["ok"] and "no member" in r["error"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
