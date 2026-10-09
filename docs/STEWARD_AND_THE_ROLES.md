# The Steward and the roles — complications on the movement

*A charter for review, 2026-10-08. Nothing in it is built beyond what §1 lists; the names in §3 are proposals.*

Matt, 2026-10-08: "I think of this layer as adding useful complications to the mechanism. Useful language and
context to make the answers applicable and practical. The start of this was the almanac work." … "A banking
module would be useful or finance. However it should be best termed. There are other practical ones like
government and manufacturing. These are skins we can use to make the system applicable, practical and
acceptable without weighing down the base tool." … "The Coach should help you interact with the site, call the
correct skin and apply it in a useful manner. Coach should use each tool well. Think of him as the Steward. We
need Steward to become a full personality. Think of a role for each job and a secondary role can develop into
a separate entity. We always optimize by having multiple capabilities complimentary to our core. We can use
these as live tests of what should become a full agent in our community. These are combining a set of
historical figures and knowledge into a single assistant or tool. We aren't generating. We are serving as a
bridge between history and current need."

## 1. What already exists (the substrate — no new brain is needed)

| Piece | Where | What it already does |
|---|---|---|
| The movement | verify · discern · the keeping · the seals | the base tool; runs and gates alone |
| Expert faces | `src/concordance/faces.py`, `docs/EXPERT_FACES.md` | a face is DATA (scope, shelves, verifiers, discernment, a fixed manner); `faces.route(text)` picks one, `faces.compose(face, text)` runs crisis-gate → scoped search → verify → discern → render. Four faces: **the Steward** (money: counts the cost, never acts), the Tutor, the Social Worker, the Theorist |
| Principles | `src/concordance/principles.py`, `lookup(kind="principles")` | the stated rules of 23 figures who repeatedly won, verbatim from public-domain works, tagged to patterns, proven by count, applied to a situation |
| The coach doors | `coach.py`: subjects · overview · next_unit · recommend · guidance · check_answer | finds and presents authored curriculum; judges only against the authored check (now by Cubo's answer law) |
| Ask | `ask.py` | a situation in, one next step out; finds, verifies, cites; crisis first |
| The complications so far | the almanac · the language cubes (Cubo: es, pt, ja, + fr, de, la, he, zh, grc) · wordcraft, etymology, phonics, formal logic (this week) | language and context on the movement, each a verifier/extractor module + data + phrasings |

So the Steward Matt describes is not a new component. It is `faces.route` grown into a personality that
holds the coach doors and ask in one hand and the complications in the other.

## 2. The rule that keeps the base light

*Matt, 2026-10-08: "Think of postulates and a fractal is the complication that we create to add on the core
engine."* A complication is two things and nothing more. Its **postulates**: the working assumptions that domain
takes as true and the engine keeps as cited, never sealed (money is counted in a ledger where debits equal
credits; a long a is EY; the cube is five anchors across three times). They work, so the truth is inferred there,
and the tick-stick store now carries them as the kind `postulate`, counted in every fit as inferred, never proven.
And its **fractal**: the kernel's own shape, find → distinguish → verify → serve → keep the trail, repeated inside
the complication at a smaller scale. That is why a complication adds no mechanism to the core: it is a smaller
copy of the mechanism plus the postulates of its domain. Cubo is the proof. Its README inherits the design law
word for word, and the kernel has been written five times across Matt's own domains and converged on the same
shape each time.

In the engine's terms, a complication is:

- a **verifier/extractor module** (found, never generated; declines what it cannot tell),
- its **data** (shelves that can be frozen; found-fact tables; coach tracks), box-local, never in core,
- its **phrasings** (recall families) and **live rows**, so its reach is measured and ratcheted,
- its **cost at boot**, measured by `systems.checkin()`,
- **removable**: the base must boot, serve and pass its four gate lines with the complication absent.

No complication adds a core dependency, a runtime model, or a shelf the base cannot shed.

## 3. A role for each job (names are proposals — Matt decides)

| Job | The role (proposed name) | Composed from (found, cited) | Complication it applies | Exists today as |
|---|---|---|---|---|
| Guide the visitor through the site; choose the right role; use every tool well | **the Steward** (Matt's word) | the five doors; the faces registry; coach doors; ask | all of them | `faces.route` + `ask` + `coach` (not yet one personality) |
| Money: accounts, loans, budgets, amortization, statements | **the Bookkeeper**, or keep **the Steward** here and name the guide **the Host** — *this is the collision to settle: faces.py already calls the money face "the Steward"* | Franklin, Carnegie, Ford on money and thrift (principles shelf); the finance/economics verifiers; the stewardship gate (counts, never executes) | finance / banking → **Stewardship** | `face_steward` |
| Teach a language through the body | **the Teacher** (Cubo) | the cubes; the pronunciation, etymology and dictionary shelves | the language complication | `face_tutor` + the coach tracks |
| Reading, arithmetic, the sciences | **the Tutor** | McGuffey, Aesop, OpenStax; the math/science verifiers | the subject shelves | `face_tutor` |
| Forms, rights, process, the founding documents | **the Clerk** | the Founding documents track; Lincoln, Washington (principles); the federal shelf | government → **Civics** | none |
| Tolerances, bills of material, process capability, the shop floor | **the Foreman** | Ford (My Life and Work), the trades handbooks, the Lean/Six-Sigma kernel that this engine came from | manufacturing → **the Shop** | none |
| Seasons, planting, weather, the sky, dates | **the Almanac-keeper** | the ephemeris, timekeeping, USDA/foods, the farmers' bulletins | the almanac (the first complication) | the almanac doors |
| Care, crisis, the household | **the Social Worker** | the crisis net first; the practical shelf | — | `face_social_worker` |

How a role is made, and why it is not generation: a role is a **composition** — the figures who held that job
and what they wrote (the principles shelf, the witnesses, the public-domain manuals), chosen by the
situation through the Wisdom Engine (front-load → recall → narrow → parable), served verbatim with the
receipt. The role's *manner* is a fixed frame. The role bridges history to the present need; it never speaks
a sentence the keeping does not hold.

## 4. The ladder: a secondary role becomes an entity

1. **A manner inside the Steward** — the Steward answers in that role's frame for that kind of need.
2. **A face** — its own entry in `faces.py` (scope, shelves, verifiers, discernment, manner), routable by text.
3. **A measured capability** — its own recall families, live rows, and a coach track; the deploy gate carries it.
4. **A community agent** — once it has held its rows across deploys, it is the proving ground for a full agent
   in the Living Community (callable faces, one body, never a swarm).

Each rung is a live test of the next. Nothing on the ladder uses a model.

## 5. What to build first (proposed order)

1. **The Steward as one personality**: one door that reads the need, picks the role (`faces.route` widened to
   the coach tracks and the complications), applies it, and says which tool it used and why — with recall
   families for "which role should answer this" so routing is measured like everything else.
2. **Stewardship** (finance/banking), because Matt named it first and `face_steward` already stands: the
   practical vocabulary (statements, amortization, a household budget), phrasings, a coach track, and
   Franklin/Carnegie/Ford's rules on money as the role's voice.
3. **Civics**, then **the Shop**.

## 6. Decided (Matt, 2026-10-08)

- **Task determines title.** A role is named by its task. The money face's task is to count the cost, so it is
  **the Bookkeeper** (faces.py; the id `face_steward` stays, an id is an address). **The Steward** is the one
  voice that meets the visitor and brings the right role.
- **Lowest-hanging fruit first.** The order in §5 is read in that light: the Steward speaking came first because
  `ask` already routed to the faces.
- **The Steward speaks through `ask`, in the same voice. "Just another role."** There is no second voice. When a
  situation fits a face, `ask.respond` carries `role` — the face's name, manner and the material it gathered,
  verified and discerned — and nothing about how the door speaks changes. Crisis is byte-identical; a role never
  sounds over a cry; a walk never seals.
- **Harmonics.** "Chords are different shapes of the same note." A role is a harmonic of the one voice: the same
  fundamental, the kernel (found, verified, cited, crisis first), in a different shape (the face's manner, shelves
  and verifiers are its timbre). Two roles sounding together is a chord, not two voices. Pinned in
  tests/test_steward_speaks.py.
