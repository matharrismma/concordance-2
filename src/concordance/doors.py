"""The Five Doors — the one source of truth for the five verbs the whole house is sorted under.

Matt, 2026-10-02: "We want to be the most useful tool possible... I don't want 15 things. I want 1-5
amazing things." The audit (docs/FIVE_DOORS_MAP.md) assigned every page, agent tool and route to one of
CHECK · FIND · WALK · KEEP · WORD — or to plumbing. This module holds that assignment so the site spine
(shell.js / nh-home.js), the agent catalog (tools/list orders the doors first, tags every tool with its
verb) and /capabilities all read ONE list and cannot drift from each other or from the map.
"""
from __future__ import annotations

from typing import Dict, List

VERBS: List[str] = ['CHECK', 'FIND', 'WALK', 'KEEP', 'WORD']

# the door page of each verb (the human front), and the one-line lead
DOOR_PAGE: Dict[str, str] = {'CHECK': '/concordance.html', 'FIND': '/explore.html', 'WALK': '/situations.html', 'KEEP': '/profile.html', 'WORD': '/bible.html'}
LEAD: Dict[str, str] = {'CHECK': 'bring any claim — the verdict, the worked trail, the seal', 'FIND': 'find it in the keeping — one map, one lookup, the source itself', 'WALK': "a situation in, one next step out — path, pattern, the figures' words, the anchor that fits", 'KEEP': 'yours, kept — your deck, your receipts, your node; the shared keeping behind it', 'WORD': 'Scripture at depth — passage, cross-references, original words, commentary'}

# the agent doors — what a new agent is shown first; everything else is an internal of its verb
TOOL_DOORS: Dict[str, List[str]] = {'CHECK': ['verify', 'audit', 'seal_fetch', 'find_verifier'], 'FIND': ['search', 'card_get', 'lookup', 'define'], 'WALK': ['ask', 'discern', 'coach_next'], 'KEEP': ['identity_create', 'study_create', 'decks'], 'WORD': ['read_passage', 'word_study', 'cross_references']}

# every agent tool -> its verb; and whether it is a door, an internal, or plumbing
TOOL_VERB: Dict[str, str] = {'verify': 'CHECK', 'audit': 'CHECK', 'seal_fetch': 'CHECK', 'find_verifier': 'CHECK', 'kernel': 'CHECK', 'kernel_gate': 'CHECK', 'candidate_commit': 'CHECK', 'candidate_narrow': 'CHECK', 'candidate_get': 'CHECK', 'resolve': 'CHECK', 'attest_record': 'CHECK', 'witnesses': 'CHECK', 'self_attest': 'CHECK', 'report': 'CHECK', 'redact': 'CHECK', 'search': 'FIND', 'card_get': 'FIND', 'lookup': 'FIND', 'define': 'FIND', 'cards_browse': 'FIND', 'cards_stats': 'FIND', 'card_connections': 'FIND', 'locate': 'FIND', 'thesaurus': 'FIND', 'pronounce': 'FIND', 'daily_card': 'FIND', 'grid_axis': 'FIND', 'grid_dimension': 'FIND', 'library_health': 'FIND', 'capabilities': 'FIND', 'now': 'FIND', 'steward_budget': 'FIND', 'steward_cost_destroyed': 'FIND', 'ask': 'WALK', 'discern': 'WALK', 'coach_next': 'WALK', 'coach_subjects': 'WALK', 'coach_overview': 'WALK', 'coach_unit': 'WALK', 'coach_recommend': 'WALK', 'coach_mastery': 'WALK', 'coach_guidance': 'WALK', 'playbook_read': 'WALK', 'want_open': 'KEEP', 'wants_list': 'KEEP', 'want_offer': 'KEEP', 'curate': 'KEEP', 'curate_queue': 'KEEP', 'curate_signable': 'KEEP', 'moderation_signable': 'KEEP', 'playbook_signable': 'KEEP', 'playbook_submit': 'KEEP', 'identity_create': 'KEEP', 'study_create': 'KEEP', 'decks': 'KEEP', 'identity_verify': 'KEEP', 'identity_fingerprint': 'KEEP', 'badges_issue': 'KEEP', 'badges_verify': 'KEEP', 'study_export': 'KEEP', 'study_import': 'KEEP', 'deck_open': 'KEEP', 'groups_list': 'KEEP', 'group_get': 'KEEP', 'group_create': 'KEEP', 'group_join': 'KEEP', 'group_contribute': 'KEEP', 'calendar_create': 'KEEP', 'consent_check': 'KEEP', 'shelf_signable': 'KEEP', 'shelf_drop': 'KEEP', 'shelf_read': 'KEEP', 'commons_read': 'KEEP', 'mesh_map': 'KEEP', 'mesh_inbox': 'KEEP', 'mesh_door': 'KEEP', 'mesh_signable': 'KEEP', 'mesh_leave_on_door': 'KEEP', 'mesh_post': 'KEEP', 'read_passage': 'WORD', 'word_study': 'WORD', 'cross_references': 'WORD', 'commentary': 'WORD', 'tsk_cross_references': 'WORD', 'character_get': 'WORD', 'characters_browse': 'WORD', 'prophecy_traces': 'WORD', 'harmony': 'WORD', 'timeline': 'WORD', 'backmatter': 'WORD', 'bible_places': 'WORD', 'narratives': 'WORD', 'original_words': 'WORD', 'canon': 'WORD', 'teachings': 'WORD', 'seeds': 'WORD', 'study_find': 'WORD'}
TOOL_KIND: Dict[str, str] = {'verify': 'DOOR', 'audit': 'DOOR', 'seal_fetch': 'DOOR', 'find_verifier': 'DOOR', 'kernel': 'INTERNAL', 'kernel_gate': 'INTERNAL', 'candidate_commit': 'INTERNAL', 'candidate_narrow': 'INTERNAL', 'candidate_get': 'INTERNAL', 'resolve': 'INTERNAL', 'attest_record': 'INTERNAL', 'witnesses': 'INTERNAL', 'self_attest': 'INTERNAL', 'report': 'INTERNAL', 'redact': 'INTERNAL', 'search': 'DOOR', 'card_get': 'DOOR', 'lookup': 'DOOR', 'define': 'DOOR', 'cards_browse': 'INTERNAL', 'cards_stats': 'INTERNAL', 'card_connections': 'INTERNAL', 'locate': 'INTERNAL', 'thesaurus': 'INTERNAL', 'pronounce': 'INTERNAL', 'daily_card': 'INTERNAL', 'grid_axis': 'INTERNAL', 'grid_dimension': 'INTERNAL', 'library_health': 'PLUMBING', 'capabilities': 'PLUMBING', 'now': 'PLUMBING', 'steward_budget': 'PLUMBING', 'steward_cost_destroyed': 'PLUMBING', 'ask': 'DOOR', 'discern': 'DOOR', 'coach_next': 'DOOR', 'coach_subjects': 'INTERNAL', 'coach_overview': 'INTERNAL', 'coach_unit': 'INTERNAL', 'coach_recommend': 'INTERNAL', 'coach_mastery': 'INTERNAL', 'coach_guidance': 'INTERNAL', 'playbook_read': 'INTERNAL', 'want_open': 'INTERNAL', 'wants_list': 'INTERNAL', 'want_offer': 'INTERNAL', 'curate': 'INTERNAL', 'curate_queue': 'INTERNAL', 'curate_signable': 'INTERNAL', 'moderation_signable': 'INTERNAL', 'playbook_signable': 'INTERNAL', 'playbook_submit': 'INTERNAL', 'identity_create': 'DOOR', 'study_create': 'DOOR', 'decks': 'DOOR', 'identity_verify': 'INTERNAL', 'identity_fingerprint': 'INTERNAL', 'badges_issue': 'INTERNAL', 'badges_verify': 'INTERNAL', 'study_export': 'INTERNAL', 'study_import': 'INTERNAL', 'deck_open': 'INTERNAL', 'groups_list': 'INTERNAL', 'group_get': 'INTERNAL', 'group_create': 'INTERNAL', 'group_join': 'INTERNAL', 'group_contribute': 'INTERNAL', 'calendar_create': 'INTERNAL', 'consent_check': 'INTERNAL', 'shelf_signable': 'INTERNAL', 'shelf_drop': 'INTERNAL', 'shelf_read': 'INTERNAL', 'commons_read': 'INTERNAL', 'mesh_map': 'INTERNAL', 'mesh_inbox': 'INTERNAL', 'mesh_door': 'INTERNAL', 'mesh_signable': 'INTERNAL', 'mesh_leave_on_door': 'INTERNAL', 'mesh_post': 'INTERNAL', 'read_passage': 'DOOR', 'word_study': 'DOOR', 'cross_references': 'DOOR', 'commentary': 'INTERNAL', 'tsk_cross_references': 'INTERNAL', 'character_get': 'INTERNAL', 'characters_browse': 'INTERNAL', 'prophecy_traces': 'INTERNAL', 'harmony': 'INTERNAL', 'timeline': 'INTERNAL', 'backmatter': 'INTERNAL', 'bible_places': 'INTERNAL', 'narratives': 'INTERNAL', 'original_words': 'INTERNAL', 'canon': 'INTERNAL', 'teachings': 'INTERNAL', 'seeds': 'INTERNAL', 'study_find': 'INTERNAL'}


def door_rank(tool: str) -> tuple:
    """Sort key: the five verbs in order, doors before internals before plumbing, then the name."""
    v = TOOL_VERB.get(tool, "ZZ")
    k = {"DOOR": 0, "INTERNAL": 1, "PLUMBING": 2}.get(TOOL_KIND.get(tool, ""), 3)
    # doors keep their stated order (verify before audit — the one entry first); internals alphabetical
    pos = TOOL_DOORS.get(v, []).index(tool) if k == 0 and tool in TOOL_DOORS.get(v, []) else 0
    return (VERBS.index(v) if v in VERBS else len(VERBS), k, pos, tool)


def tag(tool: str) -> str:
    """The verb tag a tool description is prefixed with: 'CHECK · door' or 'CHECK · internal'."""
    v = TOOL_VERB.get(tool)
    if not v:
        return ""
    k = TOOL_KIND.get(tool, "INTERNAL").lower()
    return f"{v} · {k}"


def doors() -> Dict[str, dict]:
    """The five doors as /capabilities reports them."""
    return {v: {"page": DOOR_PAGE[v], "lead": LEAD[v], "tools": TOOL_DOORS[v]} for v in VERBS}
