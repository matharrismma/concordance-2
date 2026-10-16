"""Single source of truth for MCP tool ROUTING (issue #2 — one declarative entry per tool).

Each tool appears ONCE here with its door (verb), kind, profile, and capability. `doors.py`
derives TOOL_VERB / TOOL_KIND from this, and `mcp/server.py` derives the PROFILES tool-lists
and the catalog counts from it. The tool's schema lives with it in
`server._secular_tools` / `_witness_tools`, and its handler in `server._call_tool`; both are
parity-checked against this registry by tests/test_tool_dispatch_parity.py, so adding a tool is
one entry here + a schema + a handler — co-located, mutually checked, never silent drift.

A leaf module: it imports nothing from the engine, so doors.py and server.py can both read it
without an import cycle. Do not add heavy imports here.
"""
from __future__ import annotations

from typing import Dict, List, NamedTuple


class ToolSpec(NamedTuple):
    name: str
    verb: str       # CHECK · FIND · WALK · KEEP · WORD  (the five doors)
    kind: str       # DOOR · INTERNAL · PLUMBING
    profile: str    # core · library · sovereign · coach · witness · community
    capability: str # read · derive · preserve · publish · external_action


# The profile planes, in mount order, with the metadata server.py pairs with the derived tool-lists.
PROFILE_ORDER: List[str] = [
    'core',
    'library',
    'sovereign',
    'coach',
    'witness',
    'community',
]

PROFILE_META: Dict[str, Dict[str, str]] = {
    'core': {"version": '1.0.0',
        "description": "Deterministic checks and receipts: verify a claim, audit a document, fetch and witness seals, read the engine's own capabilities and clock."},
    'library': {"version": '1.0.0',
        "description": 'Read-only retrieval over the keeping: search, cards, the grid, the conversational door. Provenance attached; nothing here writes.'},
    'sovereign': {"version": '1.0.0',
        "description": 'Identity, consent, and personal sovereignty: keys born on the device, signable payloads, the consent lock, private budgeting, redaction — and the one consent-gated external action (calendar).'},
    'coach': {"version": '1.0.0',
        "description": "Bounded curriculum access and learning records. Kept apart from the community plane on purpose — the assessment's child-surface isolation."},
    'witness': {"version": '1.0.0',
        "description": 'Attributed Scripture study: the text, the original words, the cross-references, the charts — found and cited, never generated. Gate semantics unchanged from the main door.'},
    'community': {"version": '1.0.0',
        "description": 'The social plane: groups, shelves, the commons, the mesh, moderation, and the want loop. Every publish-class tool in the catalog lives here, and this profile is OFF by default on a hosted box — publishing is a separate deployment decision with governance attached.'},
}

REGISTRY: List[ToolSpec] = [
    # ── CHECK ──
    ToolSpec('audit',                   'CHECK',      'DOOR',       'core', 'derive'),
    ToolSpec('find_verifier',           'CHECK',      'DOOR',    'library', 'read'),
    ToolSpec('seal_fetch',              'CHECK',      'DOOR',       'core', 'read'),
    ToolSpec('verify',                  'CHECK',      'DOOR',       'core', 'derive'),
    ToolSpec('attest_record',           'CHECK',  'INTERNAL',       'core', 'preserve'),
    ToolSpec('candidate_commit',        'CHECK',  'INTERNAL',       'core', 'preserve'),
    ToolSpec('candidate_get',           'CHECK',  'INTERNAL',       'core', 'read'),
    ToolSpec('candidate_narrow',        'CHECK',  'INTERNAL',       'core', 'preserve'),
    ToolSpec('kernel',                  'CHECK',  'INTERNAL',       'core', 'read'),
    ToolSpec('kernel_gate',             'CHECK',  'INTERNAL',       'core', 'derive'),
    ToolSpec('manufacture',             'CHECK',  'INTERNAL',       'core', 'preserve'),
    ToolSpec('profession',              'CHECK',  'INTERNAL',  'sovereign', 'read'),
    ToolSpec('redact',                  'CHECK',  'INTERNAL',  'sovereign', 'derive'),
    ToolSpec('report',                  'CHECK',  'INTERNAL',  'community', 'publish'),
    ToolSpec('resolve',                 'CHECK',  'INTERNAL',    'witness', 'read'),
    ToolSpec('self_attest',             'CHECK',  'INTERNAL',  'sovereign', 'preserve'),
    ToolSpec('witness_profession',      'CHECK',  'INTERNAL',  'sovereign', 'preserve'),
    ToolSpec('witnesses',               'CHECK',  'INTERNAL',       'core', 'read'),
    # ── FIND ──
    ToolSpec('card_get',                 'FIND',      'DOOR',    'library', 'read'),
    ToolSpec('define',                   'FIND',      'DOOR',    'library', 'derive'),
    ToolSpec('lookup',                   'FIND',      'DOOR',    'library', 'derive'),
    ToolSpec('search',                   'FIND',      'DOOR',    'library', 'read'),
    ToolSpec('card_connections',         'FIND',  'INTERNAL',    'library', 'read'),
    ToolSpec('cards_browse',             'FIND',  'INTERNAL',    'library', 'read'),
    ToolSpec('cards_stats',              'FIND',  'INTERNAL',    'library', 'read'),
    ToolSpec('daily_card',               'FIND',  'INTERNAL',    'library', 'read'),
    ToolSpec('grid_axis',                'FIND',  'INTERNAL',    'library', 'read'),
    ToolSpec('grid_dimension',           'FIND',  'INTERNAL',    'library', 'read'),
    ToolSpec('locate',                   'FIND',  'INTERNAL',    'library', 'read'),
    ToolSpec('pronounce',                'FIND',  'INTERNAL',    'library', 'derive'),
    ToolSpec('thesaurus',                'FIND',  'INTERNAL',    'library', 'derive'),
    ToolSpec('capabilities',             'FIND',  'PLUMBING',       'core', 'read'),
    ToolSpec('library_health',           'FIND',  'PLUMBING',    'library', 'read'),
    ToolSpec('now',                      'FIND',  'PLUMBING',       'core', 'read'),
    ToolSpec('steward_budget',           'FIND',  'PLUMBING',  'sovereign', 'derive'),
    ToolSpec('steward_cost_destroyed',   'FIND',  'PLUMBING',  'sovereign', 'derive'),
    # ── WALK ──
    ToolSpec('ask',                      'WALK',      'DOOR',    'library', 'read'),
    ToolSpec('coach_next',               'WALK',      'DOOR',      'coach', 'read'),
    ToolSpec('discern',                  'WALK',      'DOOR',    'library', 'read'),
    ToolSpec('coach_guidance',           'WALK',  'INTERNAL',      'coach', 'read'),
    ToolSpec('coach_mastery',            'WALK',  'INTERNAL',      'coach', 'preserve'),
    ToolSpec('coach_overview',           'WALK',  'INTERNAL',      'coach', 'read'),
    ToolSpec('coach_recommend',          'WALK',  'INTERNAL',      'coach', 'read'),
    ToolSpec('coach_subjects',           'WALK',  'INTERNAL',      'coach', 'read'),
    ToolSpec('coach_unit',               'WALK',  'INTERNAL',      'coach', 'read'),
    ToolSpec('parable',                  'WALK',  'INTERNAL',    'library', 'read'),
    ToolSpec('playbook_read',            'WALK',  'INTERNAL',  'community', 'read'),
    # ── KEEP ──
    ToolSpec('decks',                    'KEEP',      'DOOR',    'library', 'read'),
    ToolSpec('identity_create',          'KEEP',      'DOOR',  'sovereign', 'preserve'),
    ToolSpec('study_create',             'KEEP',      'DOOR',      'coach', 'preserve'),
    ToolSpec('badges_issue',             'KEEP',  'INTERNAL',  'sovereign', 'preserve'),
    ToolSpec('badges_verify',            'KEEP',  'INTERNAL',  'sovereign', 'derive'),
    ToolSpec('calendar_create',          'KEEP',  'INTERNAL',  'sovereign', 'external_action'),
    ToolSpec('commons_read',             'KEEP',  'INTERNAL',  'community', 'read'),
    ToolSpec('consent_check',            'KEEP',  'INTERNAL',  'sovereign', 'read'),
    ToolSpec('curate',                   'KEEP',  'INTERNAL',  'community', 'publish'),
    ToolSpec('curate_queue',             'KEEP',  'INTERNAL',  'community', 'read'),
    ToolSpec('curate_signable',          'KEEP',  'INTERNAL',  'community', 'derive'),
    ToolSpec('deck_open',                'KEEP',  'INTERNAL',    'library', 'read'),
    ToolSpec('group_contribute',         'KEEP',  'INTERNAL',  'community', 'publish'),
    ToolSpec('group_create',             'KEEP',  'INTERNAL',  'community', 'publish'),
    ToolSpec('group_get',                'KEEP',  'INTERNAL',  'community', 'read'),
    ToolSpec('group_join',               'KEEP',  'INTERNAL',  'community', 'publish'),
    ToolSpec('groups_list',              'KEEP',  'INTERNAL',  'community', 'read'),
    ToolSpec('identity_fingerprint',     'KEEP',  'INTERNAL',  'sovereign', 'derive'),
    ToolSpec('identity_verify',          'KEEP',  'INTERNAL',  'sovereign', 'derive'),
    ToolSpec('mesh_door',                'KEEP',  'INTERNAL',  'community', 'read'),
    ToolSpec('mesh_inbox',               'KEEP',  'INTERNAL',  'community', 'read'),
    ToolSpec('mesh_leave_on_door',       'KEEP',  'INTERNAL',  'community', 'publish'),
    ToolSpec('mesh_map',                 'KEEP',  'INTERNAL',  'community', 'read'),
    ToolSpec('mesh_post',                'KEEP',  'INTERNAL',  'community', 'publish'),
    ToolSpec('mesh_signable',            'KEEP',  'INTERNAL',  'community', 'derive'),
    ToolSpec('moderation_signable',      'KEEP',  'INTERNAL',  'community', 'derive'),
    ToolSpec('playbook_signable',        'KEEP',  'INTERNAL',  'community', 'derive'),
    ToolSpec('playbook_submit',          'KEEP',  'INTERNAL',  'community', 'publish'),
    ToolSpec('profess',                  'KEEP',  'INTERNAL',  'sovereign', 'preserve'),
    ToolSpec('shelf_drop',               'KEEP',  'INTERNAL',  'community', 'publish'),
    ToolSpec('shelf_read',               'KEEP',  'INTERNAL',  'community', 'read'),
    ToolSpec('shelf_signable',           'KEEP',  'INTERNAL',  'community', 'derive'),
    ToolSpec('study_export',             'KEEP',  'INTERNAL',      'coach', 'read'),
    ToolSpec('study_import',             'KEEP',  'INTERNAL',      'coach', 'preserve'),
    ToolSpec('want_offer',               'KEEP',  'INTERNAL',  'community', 'publish'),
    ToolSpec('want_open',                'KEEP',  'INTERNAL',  'community', 'preserve'),
    ToolSpec('wants_list',               'KEEP',  'INTERNAL',  'community', 'read'),
    # ── WORD ──
    ToolSpec('cross_references',         'WORD',      'DOOR',    'witness', 'read'),
    ToolSpec('read_passage',             'WORD',      'DOOR',    'witness', 'read'),
    ToolSpec('word_study',               'WORD',      'DOOR',    'witness', 'read'),
    ToolSpec('backmatter',               'WORD',  'INTERNAL',    'witness', 'read'),
    ToolSpec('bible_places',             'WORD',  'INTERNAL',    'witness', 'read'),
    ToolSpec('canon',                    'WORD',  'INTERNAL',    'witness', 'read'),
    ToolSpec('character_get',            'WORD',  'INTERNAL',    'witness', 'read'),
    ToolSpec('characters_browse',        'WORD',  'INTERNAL',    'witness', 'read'),
    ToolSpec('commentary',               'WORD',  'INTERNAL',    'witness', 'read'),
    ToolSpec('harmony',                  'WORD',  'INTERNAL',    'witness', 'read'),
    ToolSpec('narratives',               'WORD',  'INTERNAL',    'witness', 'read'),
    ToolSpec('original_words',           'WORD',  'INTERNAL',    'witness', 'read'),
    ToolSpec('prophecy_traces',          'WORD',  'INTERNAL',    'witness', 'read'),
    ToolSpec('seeds',                    'WORD',  'INTERNAL',    'library', 'read'),
    ToolSpec('study_find',               'WORD',  'INTERNAL',    'library', 'read'),
    ToolSpec('teachings',                'WORD',  'INTERNAL',    'witness', 'read'),
    ToolSpec('timeline',                 'WORD',  'INTERNAL',    'witness', 'read'),
    ToolSpec('tsk_cross_references',     'WORD',  'INTERNAL',    'witness', 'read'),
]

# Derived lookups (name -> field), built once.
BY_NAME: Dict[str, ToolSpec] = {t.name: t for t in REGISTRY}
VERB: Dict[str, str] = {t.name: t.verb for t in REGISTRY}
KIND: Dict[str, str] = {t.name: t.kind for t in REGISTRY}
PROFILE: Dict[str, str] = {t.name: t.profile for t in REGISTRY}
CAPABILITY: Dict[str, str] = {t.name: t.capability for t in REGISTRY}
NAMES: List[str] = [t.name for t in REGISTRY]
