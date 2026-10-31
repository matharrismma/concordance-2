"""The expert faces — a face is a deterministic COMPOSER over existing specialists, never a generator.

Pins the Phase 3 contract (docs/EXPERT_FACES.md): route to the right servant; crisis outranks the
servant; the served path gathers from the keeping + turns the eye upward; verifiers run only on a
checkable claim in the face's domain (honest GAP otherwise); it never crashes and never authors.
Runs with pytest OR directly; all dependencies injected, so no corpus/model is touched.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import faces  # noqa: E402


def test_route_picks_the_fitting_servant():
    assert faces.route("how should I budget my money and pay down debt") == "face_steward"
    assert faces.route("explain how photosynthesis works, help me learn") == "face_tutor"
    assert faces.route("I have no food and no power, I need help") == "face_social_worker"
    assert faces.route("why does the inverse square law hold, derive it") == "face_theorist"
    assert faces.route("I'm struggling in my faith — is it a sin to doubt, and how do I pray") == "face_shepherd"
    assert faces.route("coach me, what should I drill next to reach mastery") == "face_coach"
    assert faces.route("put it in a parable — tell me the story as a fable, with the figure who lived it") == "face_bard"
    assert faces.route("show me the original Greek word and the commentary, with cross references") == "face_scholar"
    assert faces.route("what should I eat for a balanced diet with enough protein and fiber") == "face_nutrition"
    assert faces.route("give me a survey of the literature and the major works in the field") == "face_professor"
    assert faces.route("size the beam and truss — the torque, the gears, and the tolerance") == "face_engineer"
    assert faces.route("how do I build a shed — the framing, the foundation, and the wiring") == "face_builder"
    assert faces.route("how do I grow a garden — the soil, the compost, and when to plant") == "face_gardener"
    assert faces.route("lay out the project plan — the schedule and the sequence") == "face_planner"
    assert faces.route("the music — the melody, the harmony, and writing a song") == "face_artisan"
    assert faces.route("what are my rights as a tenant, and is it legal for my landlord to do this") == "face_counsel"
    assert faces.route("what do these symptoms mean — the fever, the rash, and what treatment helps") == "face_physician"
    assert faces.route("my marriage is in conflict and I'm overwhelmed with grief — how do I cope") == "face_counselor"
    assert faces.route("") is None                       # nothing to route
    assert faces.route("the weather is nice") is None    # no scope overlap → ordinary front door


def test_crisis_outranks_the_servant():
    """A cry is handed to the crisis response before the servant gathers anything (help-first)."""
    out = faces.compose("face_steward", "I can't go on, I want to end it",
                        crisis_fn=lambda t: True,
                        search_fn=lambda q, shelves=None, limit=6: [{"id": "x", "title": "T"}])
    assert out["kind"] == "crisis" and out["handoff"] == "crisis"
    assert out["gathered"] == [] and out["verify"] is None   # nothing gathered over a cry


def test_served_path_gathers_and_turns_the_eye_upward():
    cards = [{"id": "card_a", "title": "Budgeting basics", "shelf": "economics", "body": "..."},
             {"id": "card_b", "title": "Debt", "shelf": "economics", "body": "..."}]
    out = faces.compose("face_steward", "how do I make a budget",
                        crisis_fn=lambda t: False,
                        search_fn=lambda q, shelves=None, limit=6: cards,
                        discern_fn=lambda t: {"kind": "guidance", "claim": None})
    assert out["kind"] == "served" and out["name"] == "the Bookkeeper"   # task determines title (2026-10-08)
    assert [g["id"] for g in out["gathered"]] == ["card_a", "card_b"]   # the keeping's substance
    assert "never" in out["manner"].lower()                            # steward never executes
    assert "upward" in out["means"]                                    # points beyond itself
    assert out["verify"] is None                                       # no checkable claim → honest GAP


def test_verifier_runs_only_on_a_checkable_claim_in_domain():
    """When discern proposes a structured claim in a domain the face verifies, compose runs it."""
    got = {}
    def fake_verify(steps):
        got["steps"] = steps
        return {"verdict": "HOLDS", "trail": [{"id": "s"}]}
    discern = {"kind": "verify", "claim": {"domain": "mathematics",
                                           "spec": {"mode": "arithmetic", "params": {"expr": "2+2"}}}}
    out = faces.compose("face_theorist", "is 2+2=4",
                        crisis_fn=lambda t: False,
                        search_fn=lambda q, shelves=None, limit=6: [],
                        discern_fn=lambda t: discern,
                        verify_fn=fake_verify)
    assert out["verify"] == {"verdict": "HOLDS", "trail": [{"id": "s"}]}
    assert got["steps"][0]["domain"] == "mathematics"       # routed to the face's verifier
    # a claim in a domain the face does NOT verify yields no steps (honest GAP), verifier never called
    out2 = faces.compose("face_theorist", "who won in 1815",
                         crisis_fn=lambda t: False,
                         search_fn=lambda q, shelves=None, limit=6: [],
                         discern_fn=lambda t: {"claim": {"domain": "history", "spec": {"mode": "x"}}},
                         verify_fn=lambda s: (_ for _ in ()).throw(AssertionError("must not run")))
    assert out2["verify"] is None


def test_unknown_face_is_an_honest_error():
    assert faces.compose("face_nope", "anything", crisis_fn=lambda t: False).get("error")


def test_shepherd_handles_faith_shows_discernment_and_turns_upward():
    """The Shepherd (faith) gathers from the Word, SHOWS the calibration (discernment on), and the
    eye turns to Christ, not to itself. No checkable claim -> honest GAP (never over-claims)."""
    out = faces.compose("face_shepherd", "is it a sin to doubt my faith",
                        crisis_fn=lambda t: False,
                        search_fn=lambda q, shelves=None, limit=6: [
                            {"id": "card_s", "title": "On doubt", "shelf": "scripture", "body": "..."}],
                        discern_fn=lambda t: {"kind": "guidance", "claim": None},
                        faculty_fn=lambda f, t: None)
    assert out["kind"] == "served" and out["name"] == "the Shepherd"
    assert [g["id"] for g in out["gathered"]] == ["card_s"]     # the Word's substance, gathered
    assert out["discern"] is not None                          # discernment=True -> calibration shown
    assert "christ" in out["manner"].lower()                   # points upward, never to itself
    assert out["verify"] is None                               # no checkable claim -> honest GAP


def test_coach_is_a_separate_servant_without_worldview_calibration():
    """The Coach is its OWN entity (not the Shepherd, not the Tutor): a skill path, so discernment is
    off and it carries no verifiers of its own — it never over-claims, it marks the next rep."""
    out = faces.compose("face_coach", "coach me, what should I drill next",
                        crisis_fn=lambda t: False,
                        search_fn=lambda q, shelves=None, limit=6: [
                            {"id": "card_c", "title": "Drill set", "shelf": "curriculum", "body": "..."}],
                        discern_fn=lambda t: {"kind": "guidance",
                                              "claim": {"domain": "mathematics", "spec": {"mode": "x"}}},
                        faculty_fn=lambda f, t: None)
    assert out["kind"] == "served" and out["name"] == "the Coach"
    assert out["discern"] is None                              # discernment=False -> not shown
    assert out["verify"] is None                               # no verifiers -> never over-claims


def test_bard_retells_the_found_parable_and_never_invents():
    """The Bard tells the truth back as the fitting parable from the keeping; the manner itself
    forbids invention (the no-generate covenant). A parable is not a checkable claim -> honest GAP."""
    out = faces.compose("face_bard", "put it in a parable — tell me the story as a fable",
                        crisis_fn=lambda t: False,
                        search_fn=lambda q, shelves=None, limit=6: [
                            {"id": "card_p", "title": "The lost sheep", "shelf": "scripture", "body": "..."}],
                        discern_fn=lambda t: {"kind": "guidance", "claim": None},
                        faculty_fn=lambda f, t: None)
    assert out["kind"] == "served" and out["name"] == "the Bard"
    assert [g["id"] for g in out["gathered"]] == ["card_p"]     # retells a FOUND parable
    assert out["discern"] is not None                          # discernment=True (parables carry weight)
    assert "invent" in out["manner"].lower()                   # never invents a story
    assert out["verify"] is None                               # not a checkable claim -> honest GAP


def test_scholar_presents_the_word_at_depth_cited_never_invented():
    """The Scholar presents the Word at academic depth from the keeping — each thing cited, never
    invented — and shows the calibration (it handles the Word). No checkable claim here -> honest GAP."""
    out = faces.compose("face_scholar", "show me the original Greek word and the commentary",
                        crisis_fn=lambda t: False,
                        search_fn=lambda q, shelves=None, limit=6: [
                            {"id": "card_w", "title": "agape", "shelf": "greek_nt", "body": "..."}],
                        discern_fn=lambda t: {"kind": "guidance", "claim": None})
    assert out["kind"] == "served" and out["name"] == "the Scholar"
    assert [g["id"] for g in out["gathered"]] == ["card_w"]     # the Word's substance, gathered
    assert out["discern"] is not None                          # the Word carries worldview weight -> shown
    assert "cited" in out["manner"].lower()                    # each one cited, never invented
    assert out["verify"] is None                               # no checkable claim here -> honest GAP


def test_nutrition_informs_but_is_not_your_doctor():
    """The Nutritionist informs on food and diet from the keeping, discernment off, and keeps the
    Steward-shaped boundary: it is not a doctor and points a medical question to a professional."""
    out = faces.compose("face_nutrition", "how much protein should be in a balanced diet",
                        crisis_fn=lambda t: False,
                        search_fn=lambda q, shelves=None, limit=6: [
                            {"id": "card_n", "title": "Protein", "shelf": "nutrition", "body": "..."}],
                        discern_fn=lambda t: {"kind": "guidance", "claim": None})
    assert out["kind"] == "served" and out["name"] == "the Nutritionist"
    assert [g["id"] for g in out["gathered"]] == ["card_n"]
    assert out["discern"] is None                              # discernment=False
    assert "doctor" in out["manner"].lower()                   # not your doctor -> points to a professional


def test_professor_surveys_the_field_and_cites():
    """The Professor surveys a field from its literature (academic shelves), discernment off, each
    work cited — distinct from the Tutor (a concept), the Theorist (the one form), the Scholar (the Word)."""
    out = faces.compose("face_professor", "give me a survey of the literature in this field",
                        crisis_fn=lambda t: False,
                        search_fn=lambda q, shelves=None, limit=6: [
                            {"id": "card_f", "title": "Historiography", "shelf": "history", "body": "..."}],
                        discern_fn=lambda t: {"kind": "guidance", "claim": None})
    assert out["kind"] == "served" and out["name"] == "the Professor"
    assert [g["id"] for g in out["gathered"]] == ["card_f"]
    assert out["discern"] is None                              # discernment=False
    assert "cited" in out["manner"].lower()                    # lectures from the sources, cited


# ── The credential boundary (Matt, 2026-10-29: serve the FUNCTION, never claim the CREDENTIAL).
# Each professional face names its boundary in its own manner; these pin that it is there.

def test_engineer_serves_the_function_not_the_credential():
    out = faces.compose("face_engineer", "size a steel beam and the torque",
                        crisis_fn=lambda t: False,
                        search_fn=lambda q, shelves=None, limit=6: [
                            {"id": "card_e", "title": "Beams", "shelf": "construction", "body": "..."}],
                        discern_fn=lambda t: {"kind": "guidance", "claim": None})
    assert out["kind"] == "served" and out["name"] == "the Engineer"
    assert "licensed" in out["manner"].lower()                 # not a licensed engineer -> serves the function
    assert out["discern"] is None                              # discernment=False


def test_counsel_serves_the_function_not_the_credential():
    out = faces.compose("face_counsel", "is it legal for my landlord to do this",
                        crisis_fn=lambda t: False,
                        search_fn=lambda q, shelves=None, limit=6: [
                            {"id": "card_l", "title": "Tenancy", "shelf": "law", "body": "..."}],
                        discern_fn=lambda t: {"kind": "guidance", "claim": None})
    assert out["kind"] == "served" and out["name"] == "the Counsel"
    assert "attorney" in out["manner"].lower()                 # not a licensed attorney
    assert out["discern"] is None


def test_physician_serves_the_function_not_the_credential():
    out = faces.compose("face_physician", "what do these symptoms mean, the fever and rash",
                        crisis_fn=lambda t: False,
                        search_fn=lambda q, shelves=None, limit=6: [
                            {"id": "card_m", "title": "Fever", "shelf": "medicine", "body": "..."}],
                        discern_fn=lambda t: {"kind": "guidance", "claim": None})
    assert out["kind"] == "served" and out["name"] == "the Physician"
    assert "doctor" in out["manner"].lower()                   # not your doctor, no diagnosis
    assert out["discern"] is None


def test_counselor_serves_the_function_and_shows_discernment():
    out = faces.compose("face_counselor", "my marriage is in conflict and I'm overwhelmed with grief",
                        crisis_fn=lambda t: False,
                        search_fn=lambda q, shelves=None, limit=6: [
                            {"id": "card_c2", "title": "Grief", "shelf": "narratives", "body": "..."}],
                        discern_fn=lambda t: {"kind": "guidance", "claim": None})
    assert out["kind"] == "served" and out["name"] == "the Counselor"
    assert "therapist" in out["manner"].lower()                # not a licensed therapist; crisis net first
    assert out["discern"] is not None                          # discernment=True (relational weight)


# ── The deeper binding: a bound face reaches its specialist for an extra OFFERING, fail-closed.

def test_faculty_hook_is_injectable_and_attaches_an_offering():
    """A bound face calls its specialist for an extra offering. Bard is bound to 'parable', Coach to
    'coach_recommend'; the hook is injected so no real specialist/corpus is touched here."""
    assert faces.faces()["face_bard"]["faculty"] == "parable"
    assert faces.faces()["face_coach"]["faculty"] == "coach_recommend"
    out = faces.compose("face_bard", "put it in a parable",
                        crisis_fn=lambda t: False,
                        search_fn=lambda q, shelves=None, limit=6: [],
                        discern_fn=lambda t: {"claim": None},
                        faculty_fn=lambda f, t: {"parable": "The lost sheep", "ref": "Luke 15"})
    assert out["offering"] == {"parable": "The lost sheep", "ref": "Luke 15"}


def test_faculty_fails_closed_to_a_gap_never_crashes():
    """If the specialist raises, the face still serves — offering is None (honest GAP), never a crash."""
    def boom(f, t):
        raise RuntimeError("specialist down")
    out = faces.compose("face_coach", "coach me",
                        crisis_fn=lambda t: False,
                        search_fn=lambda q, shelves=None, limit=6: [],
                        discern_fn=lambda t: {"claim": None},
                        faculty_fn=boom)
    assert out["kind"] == "served" and out["offering"] is None


def test_unbound_face_has_no_offering():
    """A face with no faculty (the Bookkeeper) carries offering None — the hook is default-off."""
    out = faces.compose("face_steward", "how do I budget",
                        crisis_fn=lambda t: False,
                        search_fn=lambda q, shelves=None, limit=6: [],
                        discern_fn=lambda t: {"claim": None})
    assert out["offering"] is None


# ── The cloud of witnesses (Heb 12:1): named real figures, cited, surfaced only when the query names one.

def test_witnesses_for_surfaces_named_figures_cited_and_is_precise():
    """A query naming a figure surfaces that figure (cited); a topical query naming none -> [] (0-FP).
    Browse injected, so no data file is read here."""
    def fake_get(tok):
        data = {"moses": {"slug": "moses", "name": "Moses", "summary": "The lawgiver...", "ref_count": 40,
                          "category": "person", "scripture_refs": ["Ex 2:10"]},
                "ruth": {"slug": "ruth", "name": "Ruth", "summary": "A Moabite woman...", "ref_count": 12,
                         "category": "person", "scripture_refs": ["Ruth 1:4"]},
                "faith": {"slug": "faith", "name": "Faith", "summary": "Belief...", "category": "concept"}}
        return data.get((tok or "").lower())
    out = faces.witnesses_for("what did Moses and Ruth do", get_fn=fake_get)
    assert [w["name"] for w in out] == ["Moses", "Ruth"] and out[0]["cited"] is True
    assert faces.witnesses_for("by faith alone", get_fn=fake_get) == []   # Faith is a concept, not a witness


def test_compose_attaches_witnesses_only_for_a_worldview_face_and_opt_in():
    stub = lambda t: [{"name": "Paul", "cited": True}]
    worldview = faces.compose("face_shepherd", "what did Paul teach",
                        crisis_fn=lambda t: False, search_fn=lambda q, shelves=None, limit=6: [],
                        discern_fn=lambda t: {"claim": None}, faculty_fn=lambda f, t: None, witness_fn=stub)
    assert worldview["witnesses"] == [{"name": "Paul", "cited": True}]          # discernment face + opt-in
    plain = faces.compose("face_tutor", "what did Paul teach",
                        crisis_fn=lambda t: False, search_fn=lambda q, shelves=None, limit=6: [],
                        discern_fn=lambda t: {"claim": None}, witness_fn=stub)
    assert plain["witnesses"] == []                                            # Tutor: discernment off
    off = faces.compose("face_shepherd", "anything",
                        crisis_fn=lambda t: False, search_fn=lambda q, shelves=None, limit=6: [],
                        discern_fn=lambda t: {"claim": None}, faculty_fn=lambda f, t: None)
    assert off["witnesses"] == []                                              # default off (no witness_fn)


def test_bard_depth_never_cheapens_the_cost():
    """Depth: the bard refuses platitudes and keeps the cost real; it is the vessel, not the light."""
    m = faces.faces()["face_bard"]["manner"].lower()
    assert "platitude" in m and "vessel" in m and "invented" in m


def test_scholar_depth_shows_both_readings():
    """Depth: where a text is read two ways, the scholar shows both and whose each is — cited, not flattened."""
    m = faces.faces()["face_scholar"]["manner"].lower()
    assert "both" in m and "cited" in m


def test_shepherd_is_deepened_from_the_shepherd_principle():
    """The depth pass, grounded in the operator's own Shepherd Principle (archetypal, no proprietary
    names): the Shepherd NOTICES rather than controls, tends toward flourishing, points to Christ, and
    is bound to `parable` so it offers the fitting parable as the anchor for a situation."""
    s = faces.faces()["face_shepherd"]
    assert s["faculty"] == "parable"
    m = s["manner"].lower()
    assert "notices" in m and "flourishing" in m and "christ" in m


def test_social_worker_depth_person_not_inventory():
    """Depth (The Way, care for the least): a person in the body, not a reimbursement unit; holds a floor."""
    m = faces.faces()["face_social_worker"]["manner"].lower()
    assert "person" in m and "floor" in m and "belonging" in m


def test_bookkeeper_depth_honest_weights_and_cost_destroyed():
    """Depth (The Way's economy): honest weights; value as reclaimed time / cost destroyed, not growth."""
    m = faces.faces()["face_steward"]["manner"].lower()
    assert "honest weights" in m and "kill rent" in m


def test_counselor_depth_belongs_and_meets_you_where_you_are():
    """Depth: a person who belongs, met where they are — not a case to be processed."""
    m = faces.faces()["face_counselor"]["manner"].lower()
    assert "belongs" in m and "where you are" in m


def test_engineer_depth_wear_surface_and_margins():
    m = faces.faces()["face_engineer"]["manner"].lower()
    assert "wear surface" in m and "licensed" in m


def test_builder_depth_repair_and_commodity():
    m = faces.faces()["face_builder"]["manner"].lower()
    assert "repair" in m and "commodity" in m


def test_planner_depth_gated_stages():
    m = faces.faces()["face_planner"]["manner"].lower()
    assert "gated" in m and "stage" in m


def test_artisan_depth_useful_before_interesting():
    m = faces.faces()["face_artisan"]["manner"].lower()
    assert "interesting after" in m and "ornament" in m


def test_gardener_depth_staple_and_season():
    m = faces.faces()["face_gardener"]["manner"].lower()
    assert "staple" in m and "season" in m


def test_tutor_depth_unpack_and_own_it():
    m = faces.faces()["face_tutor"]["manner"].lower()
    assert "unpack" in m and "own it" in m


def test_theorist_depth_one_form_at_the_floor():
    m = faces.faces()["face_theorist"]["manner"].lower()
    assert "one form" in m and "floor" in m


def test_professor_depth_evidence_not_authority():
    m = faces.faces()["face_professor"]["manner"].lower()
    assert "evidence" in m and "cited" in m


def test_coach_depth_not_from_zero():
    m = faces.faces()["face_coach"]["manner"].lower()
    assert "zero" in m and "teaching is training" in m


def test_physician_depth_person_not_case():
    m = faces.faces()["face_physician"]["manner"].lower()
    assert "person" in m and "doctor" in m


def test_nutritionist_depth_staple():
    m = faces.faces()["face_nutrition"]["manner"].lower()
    assert "staple" in m and "doctor" in m


def test_counsel_depth_exit():
    m = faces.faces()["face_counsel"]["manner"].lower()
    assert "exit" in m and "attorney" in m


# ── The Conductor: one AI to direct — pull a named expert, or direct to the fitting one.

def test_conductor_directs_to_the_fitting_expert():
    out = faces.direct("how should I budget my money and pay down debt",
                       crisis_fn=lambda t: False, search_fn=lambda q, shelves=None, limit=6: [],
                       discern_fn=lambda t: {"claim": None})
    assert out["ok"] and out["routed"] == "face_steward" and out["how"] == "directed"
    assert out["served"]["name"] == "the Bookkeeper"


def test_conductor_pulls_a_named_expert_by_id_or_name():
    for handle in ["the Shepherd", "shepherd", "face_shepherd", "Shepherd"]:
        out = faces.direct("whatever the visitor brings", expert=handle,
                           crisis_fn=lambda t: False, search_fn=lambda q, shelves=None, limit=6: [],
                           discern_fn=lambda t: {"claim": None}, faculty_fn=lambda f, t: None)
        assert out["ok"] and out["routed"] == "face_shepherd" and out["how"] == "pulled"


def test_conductor_unknown_expert_is_honest():
    out = faces.direct("x", expert="the Wizard")
    assert not out["ok"] and "experts" in out and len(out["experts"]) == 18


def test_conductor_forces_no_expert_where_none_fits():
    out = faces.direct("the weather is nice")
    assert out["ok"] and out["routed"] is None and out["expert"] is None   # defer to the front door


def test_roster_lists_all_pullable_experts():
    r = faces.roster()
    assert len(r) == 18
    assert any(x["name"] == "the Shepherd" for x in r)
    assert all(x["id"].startswith("face_") and x["name"] for x in r)


if __name__ == "__main__":
    import pytest
    sys.exit(int(pytest.main([__file__, "-q"])))
