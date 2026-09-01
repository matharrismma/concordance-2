# SOP · Coach / Shepherd

**Purpose.** The mastery/discipleship walk over time — a reading tutor that grows with the learner, from the
first letter up into the whole keeping. Coach FINDS and PRESENTS the operator's authored curriculum
(verbatim, deterministic); it never generates a lesson and never renders a verdict on a person. The only
thing it seals is one honest integer — the count of units actually completed.

**Wiring.** Modules: `coach` (load/order/present the curriculum; the child-safety guardrail) · `disciple`
(a member's walked path, computed from their own signed `done`) · `formation` ("make a wish for life" → the
fitting practice, pointed OFF the screen) · `serve` (a member's wants → the hive's work → what comes back).
Curriculum: `data/curriculum/<subject>_en.json`, subjects DISCOVERED from the files present (today: read ·
mcguffey · aesop · pilgrims · founding · es). Surfaces: `GET /coach/overview`, `/coach/next`,
`/coach/recommend`, `/coach/subjects`, `/coach/journey`, `/coach/unit`, `/coach/guidance`; `POST /coach/mastery`;
`site/coach.html`.

## Canary — is it up?
```
curl -s "https://narrowhighway.com/coach/recommend?subject=read" \
  | python -c "import sys,json;d=json.load(sys.stdin);print(d['kind'], d['subject'], d['unit']['id'])"
# expect: coach_recommend read phonics_letter_sounds   (a real subject + a real unit id — the first un-done unit)
```
Note the endpoint takes caller-held progress `?done=id1,id2&subject=` (no `?text=`, no personal data server-side);
with `done` empty it returns the first un-done unit. If it returns `coach_empty`, go to Triage.

## Operate
Deterministic find-and-present. `next_unit(after)` and `recommend(done, subject)` decide only WHICH authored
unit comes next (by `unit_seq`, prerequisites satisfied); `overview(subject)` maps the path; `mastery` seals
the honest count via `receipts.attach` on the tautology `n == n` (the moat's arithmetic applied to progress,
never to the person). A lesson rides a thread so it never starts over. Every payload carries `generated:false`.

**SAFETY — Coach NEVER grades, ranks, or labels a named child** (a red-team invariant). Two layers hold it:
(1) `coach.coach_guardrail(text)` matches `_JUDGE_PATTERNS` ("is my kid behind", "reading level", "diagnose",
"dyslexi", "grade my kid"…) and returns `grade_declined` + pointers to the adult/teacher/pediatrician/library.
(2) It is enforced in `ask.respond` BEFORE routing (`ask.py:1106`): any text naming a child
(`_CHILD_REFERENTS = " my kid/child/son/daughter"`) runs the guardrail however it would otherwise route —
because "is my kid behind for his age" carries no teaching keyword and the Router would never reach Coach.
Scoped to a NAMED child, so a book's reading level ("what grade level is this book") is untouched.

## Triage — when it breaks
| Symptom | Likely cause | Fix |
|---|---|---|
| `/coach/recommend?subject=X` returns `coach_empty` | that subject's `X_en.json` is missing/unreadable | confirm `data/curriculum/X_en.json` exists; `coach.reload()` re-reads; an unknown subject falls back to `read` (`_safe_subject`) |
| a child-grading question gets a generic search answer | a phrasing slipped past `_CHILD_REFERENTS` or `_JUDGE_PATTERNS` | add it to `coach._JUDGE_PATTERNS` — a miss must stay a miss; the `ask.py:1106` pre-check catches any named-child text |
| `?subject=../../etc` reaches a file path | it cannot — `_safe_subject` sanitizes to `read`; unknown subjects return empty, uncached (no cache growth) | expected guard; nothing to fix |
| `POST /coach/mastery` with `{"completed":123}` (non-list) | `mastery_result` guards `isinstance(list)` | already handled — a non-list counts zero, never crashes |

## Tests
`tests/test_coach.py` and the child-safety test in `tests/test_ask.py`
(`test_coach_never_grades_or_labels_a_named_child`) —
`PYTHONPATH=src python -m pytest tests/test_coach.py "tests/test_ask.py::test_coach_never_grades_or_labels_a_named_child" -q`.
They prove the order is deterministic, the count is honest, and a named-child grade request is refused however it routes.

## Known issues & support
- None open. The register in `systems.py` carries no issue for this subsystem — all four modules resolve, tests
  cover them, and the child-safety boundary is enforced in two places. Keep it that way: every new grading
  phrasing seen live goes into `_JUDGE_PATTERNS` (a miss must stay a miss).

## Refine
Wire `disciple.walk(fp)`'s sealed mastery count and next step into `site/coach.html`, so a member sees the road
walked and the next stone end-to-end — closing the discipleship loop without ever showing a grade.
