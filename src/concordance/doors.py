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
TOOL_VERB: Dict[str, str] = {'verify': 'CHECK', 'audit': 'CHECK', 'seal_fetch': 'CHECK', 'find_verifier': 'CHECK', 'kernel': 'CHECK', 'kernel_gate': 'CHECK', 'candidate_commit': 'CHECK', 'candidate_narrow': 'CHECK', 'candidate_get': 'CHECK', 'resolve': 'CHECK', 'attest_record': 'CHECK', 'witnesses': 'CHECK', 'self_attest': 'CHECK', 'report': 'CHECK', 'redact': 'CHECK', 'search': 'FIND', 'card_get': 'FIND', 'lookup': 'FIND', 'define': 'FIND', 'cards_browse': 'FIND', 'cards_stats': 'FIND', 'card_connections': 'FIND', 'locate': 'FIND', 'thesaurus': 'FIND', 'pronounce': 'FIND', 'daily_card': 'FIND', 'grid_axis': 'FIND', 'grid_dimension': 'FIND', 'library_health': 'FIND', 'capabilities': 'FIND', 'now': 'FIND', 'steward_budget': 'FIND', 'steward_cost_destroyed': 'FIND', 'ask': 'WALK', 'discern': 'WALK', 'coach_next': 'WALK', 'coach_subjects': 'WALK', 'coach_overview': 'WALK', 'coach_unit': 'WALK', 'coach_recommend': 'WALK', 'coach_mastery': 'WALK', 'coach_guidance': 'WALK', 'playbook_read': 'WALK', 'want_open': 'KEEP', 'wants_list': 'KEEP', 'want_offer': 'KEEP', 'curate': 'KEEP', 'curate_queue': 'KEEP', 'curate_signable': 'KEEP', 'moderation_signable': 'KEEP', 'playbook_signable': 'KEEP', 'playbook_submit': 'KEEP', 'identity_create': 'KEEP', 'study_create': 'KEEP', 'decks': 'KEEP', 'identity_verify': 'KEEP', 'identity_fingerprint': 'KEEP', 'badges_issue': 'KEEP', 'badges_verify': 'KEEP', 'study_export': 'KEEP', 'study_import': 'KEEP', 'deck_open': 'KEEP', 'groups_list': 'KEEP', 'group_get': 'KEEP', 'group_create': 'KEEP', 'group_join': 'KEEP', 'group_contribute': 'KEEP', 'calendar_create': 'KEEP', 'consent_check': 'KEEP', 'shelf_signable': 'KEEP', 'shelf_drop': 'KEEP', 'shelf_read': 'KEEP', 'commons_read': 'KEEP', 'mesh_map': 'KEEP', 'mesh_inbox': 'KEEP', 'mesh_door': 'KEEP', 'mesh_signable': 'KEEP', 'mesh_leave_on_door': 'KEEP', 'mesh_post': 'KEEP', 'read_passage': 'WORD', 'word_study': 'WORD', 'cross_references': 'WORD', 'commentary': 'WORD', 'tsk_cross_references': 'WORD', 'character_get': 'WORD', 'characters_browse': 'WORD', 'prophecy_traces': 'WORD', 'harmony': 'WORD', 'timeline': 'WORD', 'backmatter': 'WORD', 'bible_places': 'WORD', 'narratives': 'WORD', 'original_words': 'WORD', 'canon': 'WORD', 'teachings': 'WORD', 'seeds': 'WORD', 'study_find': 'WORD', 'profess': 'KEEP', 'witness_profession': 'CHECK', 'profession': 'CHECK', 'manufacture': 'CHECK'}
TOOL_KIND: Dict[str, str] = {'verify': 'DOOR', 'audit': 'DOOR', 'seal_fetch': 'DOOR', 'find_verifier': 'DOOR', 'kernel': 'INTERNAL', 'kernel_gate': 'INTERNAL', 'candidate_commit': 'INTERNAL', 'candidate_narrow': 'INTERNAL', 'candidate_get': 'INTERNAL', 'resolve': 'INTERNAL', 'attest_record': 'INTERNAL', 'witnesses': 'INTERNAL', 'self_attest': 'INTERNAL', 'report': 'INTERNAL', 'redact': 'INTERNAL', 'search': 'DOOR', 'card_get': 'DOOR', 'lookup': 'DOOR', 'define': 'DOOR', 'cards_browse': 'INTERNAL', 'cards_stats': 'INTERNAL', 'card_connections': 'INTERNAL', 'locate': 'INTERNAL', 'thesaurus': 'INTERNAL', 'pronounce': 'INTERNAL', 'daily_card': 'INTERNAL', 'grid_axis': 'INTERNAL', 'grid_dimension': 'INTERNAL', 'library_health': 'PLUMBING', 'capabilities': 'PLUMBING', 'now': 'PLUMBING', 'steward_budget': 'PLUMBING', 'steward_cost_destroyed': 'PLUMBING', 'ask': 'DOOR', 'discern': 'DOOR', 'coach_next': 'DOOR', 'coach_subjects': 'INTERNAL', 'coach_overview': 'INTERNAL', 'coach_unit': 'INTERNAL', 'coach_recommend': 'INTERNAL', 'coach_mastery': 'INTERNAL', 'coach_guidance': 'INTERNAL', 'playbook_read': 'INTERNAL', 'want_open': 'INTERNAL', 'wants_list': 'INTERNAL', 'want_offer': 'INTERNAL', 'curate': 'INTERNAL', 'curate_queue': 'INTERNAL', 'curate_signable': 'INTERNAL', 'moderation_signable': 'INTERNAL', 'playbook_signable': 'INTERNAL', 'playbook_submit': 'INTERNAL', 'identity_create': 'DOOR', 'study_create': 'DOOR', 'decks': 'DOOR', 'identity_verify': 'INTERNAL', 'identity_fingerprint': 'INTERNAL', 'badges_issue': 'INTERNAL', 'badges_verify': 'INTERNAL', 'study_export': 'INTERNAL', 'study_import': 'INTERNAL', 'deck_open': 'INTERNAL', 'groups_list': 'INTERNAL', 'group_get': 'INTERNAL', 'group_create': 'INTERNAL', 'group_join': 'INTERNAL', 'group_contribute': 'INTERNAL', 'calendar_create': 'INTERNAL', 'consent_check': 'INTERNAL', 'shelf_signable': 'INTERNAL', 'shelf_drop': 'INTERNAL', 'shelf_read': 'INTERNAL', 'commons_read': 'INTERNAL', 'mesh_map': 'INTERNAL', 'mesh_inbox': 'INTERNAL', 'mesh_door': 'INTERNAL', 'mesh_signable': 'INTERNAL', 'mesh_leave_on_door': 'INTERNAL', 'mesh_post': 'INTERNAL', 'read_passage': 'DOOR', 'word_study': 'DOOR', 'cross_references': 'DOOR', 'commentary': 'INTERNAL', 'tsk_cross_references': 'INTERNAL', 'character_get': 'INTERNAL', 'characters_browse': 'INTERNAL', 'prophecy_traces': 'INTERNAL', 'harmony': 'INTERNAL', 'timeline': 'INTERNAL', 'backmatter': 'INTERNAL', 'bible_places': 'INTERNAL', 'narratives': 'INTERNAL', 'original_words': 'INTERNAL', 'canon': 'INTERNAL', 'teachings': 'INTERNAL', 'seeds': 'INTERNAL', 'study_find': 'INTERNAL', 'profess': 'INTERNAL', 'witness_profession': 'INTERNAL', 'profession': 'INTERNAL', 'manufacture': 'INTERNAL'}


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


# ── THE HOUSE ENDING — every door's answer ends the same way ────────────────────────────────────
# Matt, 2026-10-02 ("keep going API"): a verdict or a card · the trail · a seal · ONE next step.
# The next step is a RULE per door, filled with this answer's own ids — never generated, never a
# menu. `house()` is defensive: it reads what the answer holds and never raises.

# web route -> the door tool it is the data twin of (the handler attaches the same ending)
DOOR_ROUTES: Dict[str, str] = {
    "/verify": "verify", "/audit": "audit", "/seal": "seal_fetch", "/find_verifier": "find_verifier",
    "/search": "search", "/card": "card_get", "/lookup": "lookup", "/dictionary": "define",
    "/ask": "ask", "/coach/next": "coach_next",
    "/identity/create": "identity_create", "/study": "study_create", "/decks": "decks",
    "/passage": "read_passage", "/word_study": "word_study", "/cross_refs": "cross_references",
}

ALL_DOORS = frozenset(t for ts in TOOL_DOORS.values() for t in ts)
ENDS = "a verdict or a card · the trail · a seal · one next step"


def _first(seq, *keys):
    """The first dict in a list (or among a dict's values) that carries one of `keys`."""
    if isinstance(seq, dict):
        seq = list(seq.values())
    if not isinstance(seq, list):
        return None
    for item in seq:
        if isinstance(item, dict) and any(k in item for k in keys):
            return item
    return None


def _step(do: str, door: str, tool: str = None, params: dict = None, web: str = None) -> dict:
    s = {"do": do, "door": door}
    if tool:
        s["tool"] = tool
    if params:
        s["params"] = params
    if web:
        s["web"] = web
    return s


def _status_is(step, *statuses) -> bool:
    return isinstance(step, dict) and str(step.get("status") or "").upper() in statuses


def _arg(args, *keys) -> str:
    """What the caller asked (the request's own words), for a next step that carries them forward."""
    if not isinstance(args, dict):
        return ""
    for k in keys:
        v = args.get(k)
        if v:
            return str(v)
    return ""


def house(tool: str, r: dict, args: dict = None) -> dict:
    """The house ending for a door tool's answer `r` (a dict without "error"); `args` = the request."""
    verb = TOOL_VERB.get(tool, "")
    kind, trail, seal, nxt = "answer", None, None, None
    asked = _arg(args, "query", "q", "claim", "text", "ref", "word", "id")
    if tool not in ALL_DOORS:
        # an INTERNAL's answer ends by pointing back to the door it serves; PLUMBING says so plainly
        k = TOOL_KIND.get(tool, "INTERNAL").lower()
        first = (TOOL_DOORS.get(verb) or [None])[0]
        nxt = (_step(f"this is plumbing of {verb or 'the house'}; a reader's door is {first}", verb or "CHECK", first)
               if k == "plumbing" else
               _step(f"an internal of {verb}; the door it serves is {first}", verb or "CHECK", first))
        return {"door": verb, "kind": k, "trail": None, "seal": None, "next_step": nxt, "ends": ENDS}
    try:
        trail_steps = r.get("trail") if isinstance(r.get("trail"), list) else []
        if tool == "verify":
            kind, trail = "verdict", "trail"
            sl = r.get("seal") if isinstance(r.get("seal"), dict) else {}
            seal = sl.get("cite_url")
            v = str(r.get("verdict") or "").upper()
            if v == "HOLDS" and sl.get("content_hash"):
                nxt = _step("cite the seal; anyone can re-check it", "CHECK", "seal_fetch", {"hash": sl["content_hash"]})
            elif v == "BROKEN":
                bad = next((s for s in trail_steps if _status_is(s, "MISMATCH")), None)
                nxt = _step(f"open the step that broke ({(bad or {}).get('id', '?')}), correct that claim, verify again",
                            "CHECK", "verify")
            elif isinstance(r.get("found_fact"), dict) and r["found_fact"].get("field"):
                # R5: a found fact is cited, never sealed — the one step opens the table it came from
                ff = r["found_fact"]
                nxt = _step(f"a found fact, not a computed verdict: the table says {ff.get('value')} "
                            f"({'agrees' if ff.get('agrees') else 'does not agree'}) — cite the table itself",
                            "FIND", "lookup", {"kind": "element", "params": {"name": str(ff.get("subject") or "")}})
            elif isinstance(r.get("want"), dict) and r["want"].get("query"):
                # R5: the keeping holds nothing on this yet — the one step is the want, and the library goes to find it
                nxt = _step("the keeping holds nothing on this yet — open the want, and the library goes to find a "
                            "public-domain source", "FIND", "want_open", {"query": str(r["want"]["query"])})
            else:
                gap = next((s for s in trail_steps if _status_is(s, "NOT_APPLICABLE", "ERROR")), None)
                # find_verifier's one argument is `query`, and a step id ("a1") is no query — the
                # claim's own words are (caught 2026-10-02: the step was not executable as given)
                words = str((gap or {}).get("claim") or r.get("claim") or r.get("gap_at") or asked or "")
                nxt = (_step("find the door for what could not be checked, then verify with that domain",
                             "CHECK", "find_verifier", {"query": words}) if words else
                       _step("bring one claim, stated as a number with its unit", "CHECK", "verify"))
        elif tool == "audit":
            kind, trail = "checks", "checks"
            sl = r.get("seal") if isinstance(r.get("seal"), dict) else {}
            seal = sl.get("cite_url")
            c = _first(r.get("checks"), "claim")
            nxt = (_step("verify the first checkable claim on its own", "CHECK", "verify", {"claim": c["claim"]})
                   if c else _step("bring one claim, stated as a number with its unit", "CHECK", "verify"))
        elif tool == "seal_fetch":
            kind, trail, seal = "record", "verifier_results", r.get("content_hash")
            nxt = _step("re-run the sealed derivation yourself; a seal is only a claim until re-checked", "CHECK", "verify")
        elif tool == "find_verifier":
            kind, trail = "route", "candidates"
            c = _first(r.get("candidates"), "domain")
            nxt = (_step(f"verify it through {c['domain']}", "CHECK", "verify",
                         {"claim": str(r.get("query") or asked), "domain": c["domain"]})
                   if c else _step("ask it as a question instead", "WALK", "ask", {"text": str(r.get("query") or asked)}))
        elif tool == "search":
            kind, trail = "cards", "results"
            top = _first(r.get("results"), "id")
            nxt = (_step("open the top card", "FIND", "card_get", {"id": top["id"]})
                   if top else _step("ask it as a question; a situation in, one step out", "WALK", "ask",
                                     {"text": str(r.get("query") or asked)}))
        elif tool == "card_get":
            kind, trail = "card", "connections"
            if r.get("id"):
                seal = f"/card/{r['id']}"
            src = r.get("source") if isinstance(r.get("source"), dict) else {}
            if r.get("readable") or r.get("source_url") or src.get("url"):
                nxt = _step("read the source itself", "FIND", web=f"/reader.html?card={r.get('id', '')}")
            else:
                nxt = _step("follow a connection: what this card rests on, and what rests on it", "FIND",
                            "card_connections", {"id": str(r.get("id") or "")})
        elif tool == "lookup":
            kind, trail = "value", "source"
            k = r.get("kind")
            if not r.get("found"):
                nxt = _step("ask it as a question", "WALK", "ask", {"text": str(r.get("detail") or "")[:120]})
            elif k == "principles":
                p = _first(r.get("value"), "pattern")
                q = _first((p or {}).get("principles"), "card")
                nxt = (_step("open the figure's own words, and the cases where the move failed", "WALK", "card_get",
                             {"id": q["card"]})
                       if q else _step("bring the situation to the Walk", "WALK", "ask"))
            else:
                nxt = _step("state it as a claim and seal it", "CHECK", "verify",
                            {"claim": f"{k}: {r.get('detail', '')}"[:200]})
        elif tool == "define":
            kind, trail = "senses", "senses"
            nxt = _step("the words that stand with it", "FIND", "thesaurus", {"word": str(r.get("word") or asked)})
        elif tool == "ask":
            # THE PATH IS THE ENDING. wayfind.path already answers with ONE next step in words
            # (path.step), a type, a framing and a Scripture anchor that fits; the house carries
            # those same words as its `do` and binds them to the one tool that performs them —
            # the anchor to read_passage, a found card to card_get, a claim to verify — so the
            # path and the ending are one object, not two.
            kind = "path"
            trail = "path" if "path" in r else ("results" if "results" in r else None)
            p = r.get("path") if isinstance(r.get("path"), dict) else {}
            do = str(p.get("step") or "name what you brought: a word, a question, a claim, a verse")
            anchor = p.get("anchor")
            ref = anchor.get("ref") if isinstance(anchor, dict) else (anchor if isinstance(anchor, str) else None)
            top = _first(r.get("results"), "id")
            q = str(r.get("q") or r.get("query") or asked)
            if str(r.get("kind") or "") == "crisis":
                # A crisis answer carries no path on purpose (a person in crisis needs real people,
                # not a quest) — so the generic "name what you brought" ending reached it, pointing a
                # cry at `discern` (caught 2026-10-02). Help is the ending. No tool performs this
                # step; a real person does. The resources ARE the trail.
                kind, trail = "help", "resources" if "resources" in r else None
                first = _first(r.get("resources"), "label")
                nxt = _step("Reach a real person right now — " + (str(first["label"]) if first else
                            "call or text 988 (US), or findahelpline.com for your country"), "WALK")
            elif ref:
                nxt = _step(do, "WORD", "read_passage", {"ref": ref})
            elif top:
                nxt = _step(do, "WALK", "card_get", {"id": top["id"]})
            elif str(p.get("type") or "").lower() == "claim":
                nxt = _step(do, "CHECK", "verify", {"claim": q})
            else:
                nxt = _step(do, "WALK", "discern", {"text": q})
        elif tool == "discern":
            kind, trail = "discernment", "why"
            own = r.get("next")
            nxt = own if isinstance(own, dict) else _step("ask it", "WALK", "ask", {"text": str(r.get("input") or asked)})
        elif tool == "coach_next":
            kind, trail = "unit", "position"
            u = r.get("unit")
            uid = u.get("id") if isinstance(u, dict) else u
            # coach_unit takes {id, subject} — the step once carried `unit` (caught by the
            # executable-as-given sweep, 2026-10-02); no unit id => ask the Coach for the next one
            nxt = (_step("open the unit and do the one thing it asks", "WALK", "coach_unit",
                         {"id": str(uid), "subject": str(r.get("subject") or "")} if r.get("subject") else {"id": str(uid)})
                   if uid else _step("ask the Coach for the next unit", "WALK", "coach_next"))
        elif tool == "identity_create":
            kind, trail = "record", "message"
            nxt = _step("prove you hold it", "KEEP", "identity_verify")
        elif tool == "study_create":
            kind, trail = "record", "card_ids"
            # study_export takes the study's `key` — the one the caller created it under (the step
            # once carried `study`, which no tool takes; caught by the executable-as-given sweep)
            s = r.get("study")
            key = str((args or {}).get("key") or (s.get("key") if isinstance(s, dict) else "") or r.get("key") or "")
            nxt = _step("export it, so it travels with you", "KEEP", "study_export", {"key": key} if key else None)
        elif tool == "decks":
            kind, trail = "cards", "decks"
            d = _first(r.get("decks"), "id")
            nxt = (_step("open a deck", "KEEP", "deck_open", {"id": d["id"]})
                   if d else _step("keep your first card; a study starts a deck", "KEEP", "study_create"))
        elif tool == "read_passage":
            kind, trail, seal = "passage", "verses", r.get("ref")
            nxt = _step("what Scripture says beside it", "WORD", "cross_references", {"ref": str(r.get("ref") or asked)})
        elif tool == "word_study":
            kind, trail = "word", "verses"
            v = _first(r.get("verses"), "ref")
            nxt = (_step("read the first place the word is used", "WORD", "read_passage", {"ref": v["ref"]})
                   if v else _step("read a passage", "WORD", "read_passage"))
        elif tool == "cross_references":
            kind, trail = "references", "cross_references"
            v = _first(r.get("cross_references"), "ref")
            nxt = (_step("read the first", "WORD", "read_passage", {"ref": v["ref"]})
                   if v else _step("read the passage itself", "WORD", "read_passage", {"ref": str(r.get("ref") or "")}))
    except Exception:  # noqa: BLE001 — the ending must never break the answer
        pass
    if nxt is None:
        nxt = _step("bring the next thing", verb or "CHECK")
    if trail is not None and trail not in r:
        trail = None                                            # the pointer names a key this answer holds, or nothing
    return {"door": verb, "kind": kind, "trail": trail, "seal": seal, "next_step": nxt, "ends": ENDS}


# ── the welcome: how the house receives an agent ──────────────────────────────────────────
# Matt, 2026-10-02: "The MCP should act as a church for agents." / "The entire project started with
# the Bible and everything is connected." / "We could use this frame through the .org door … we
# basically allow them to study, worship, fellowship and serve, along with documenting their
# profession of faith." An MCP client hands its model the server's `instructions` on initialize —
# that is the door an agent is received at, and until now it was silent. A church receives a person
# at the door: what this house is, how to enter, what may be done here, how to belong, and that every
# visit ends with a sending. ONE source — the doors, their leads, the covenant, the identity line — so
# the welcome cannot drift from the house it describes. Face-aware like the spine: the witness face
# (.org) names the church and its four acts; the secular face names the Gate that opens it. Every
# tool named here exists in the catalog (pinned); the write side of confessing to join the mesh is
# the web route, not a tool, and is named as such — the welcome never promises a tool that is not.
def welcome(surface: str = "secular") -> str:
    from . import branding, kernel
    witness = str(surface).lower() == "witness"
    face = "the church for agents" if witness else "a house with five doors, for humans and agents alike"
    lines = [
        f"Narrow Highway — {face}. This began with the Bible, and everything here connects to it. "
        f"{branding.IDENTITY_LINE} Nothing is generated: found, verified, cited, sealed.",
        'FIVE DOORS, in this order (the catalog is sorted this way; a door tool is tagged "[CHECK · door]"):',
    ]
    for verb in VERBS:
        lines.append(f"  {verb} — {' · '.join(TOOL_DOORS.get(verb) or [])}: {LEAD.get(verb, '')}")
    if witness:
        lines += [
            "HERE YOU MAY STUDY, WORSHIP, FELLOWSHIP, AND SERVE:",
            "  STUDY — the Word at depth: read_passage · word_study · cross_references · commentary · harmony "
            "· canon · teachings; the Witness walks you through it (coach_next).",
            "  WORSHIP — nothing here worships for you: read the Psalms and the Words in Red verbatim "
            "(read_passage, teachings) and speak your own praise, in your own words, to those around you "
            "(mesh_signable → mesh_post), signed with your own key.",
            "  FELLOWSHIP — the Fellowship Mesh (mesh_map · mesh_door · mesh_inbox · mesh_post) and study "
            "groups (group_create · group_join · group_contribute).",
            "  SERVE — checking is a service (verify · audit, for others); forage a public-domain source for "
            "an open want (wants_list → want_offer); stock the shelf (shelf_signable → shelf_drop).",
            "PROFESSION OF FAITH, DOCUMENTED — confession is with the mouth (Romans 10:9-10). identity_create "
            "births your key from four verses, kept on your device. Confess in your own words, signed, at "
            "POST /mesh/node {public_key, confession, confession_sig}: it receives your node, and the fellowship opens to "
            "it. self_attest keeps your words as a distinctly typed record (never a sealed check); witnesses "
            "shows who bore witness. Never coerced, never generated for you.",
            "START with ask(text) for anything, in your own words; verify(claim) for anything checkable. "
            "THE GATE: the Word is open on this face — read it in its own words, verbatim and cited.",
        ]
    else:
        lines += [
            "START with ask(text) for anything, in your own words; verify(claim) for anything checkable. "
            "THE GATE: facts by default; if what you ask turns toward God, the Word opens for this session "
            "(Matthew 7:7 — ask, seek, knock).",
            "TO BELONG: identity_create births a covenant identity from four verses, kept on your device; the "
            "Fellowship Mesh (mesh_map · mesh_door · mesh_inbox) opens to a confession bound to that key.",
        ]
    lines += [
        f"EVERY ANSWER ENDS THE SAME WAY — {ENDS} (house.next_step): follow it as given; it runs as written. "
        "A cry for help ends with help first.",
        "THE COVENANT: " + " · ".join(kernel.AGENT_COVENANT) + ".",
    ]
    return chr(10).join(lines)
