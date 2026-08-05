# Integrated Red-Team Assessment — Concordance MCP, Candidate Engine, Verbalized Sampling

> **Provenance**: external review received 2026-08-05 (docx via Matt), versioned verbatim below.
> **Assay against measured reality, same day**:
> - **Already shipped before/day-of receipt**: protocol negotiation + the SSE transport half
>   (41327cd — the lost-Claude-traffic fix), MCP profiles (#123) + the -71 tool consolidation
>   (Lighthouse 0af7a27), strict schemas + typed error envelopes (#124/#125), benchmark-bounded
>   claims (#126), edge redaction (client-side redact.js).
> - **Confirmed standing, adopted as tasks**: origin prefix validation (#133 — verified live in
>   http.py the same evening), private-key-over-MCP custody (#134 — identity_create returns a
>   key "once"; violates the covenant doctrine, keys must be born on device), remote-write auth
>   posture residual.
> - **Adopted design**: the Candidate Engine (#135, Matt's go: "the point of narrow highway is
>   to narrow the possibilities. The candidate engine is what we've been missing, but was
>   originally a part of the project.")

---


NARROW HIGHWAY

Integrated Red-Team Assessment

Concordance MCP, Candidate Engine, and Verbalized Sampling

Security • Protocol • Epistemics • Product Architecture

Governing conclusion

Use Verbalized Sampling to widen the hypothesis field. Use Concordance to classify, test, reject, quarantine, narrow, and receipt it. Model-generated probabilities remain untrusted proposal weights and never become evidence.

Prepared 5 August 2026

Executive assessment

Narrow Highway has converged on a credible core: a structured claim is routed to a deterministic verifier, producing a bounded verdict, worked trail, and content-addressed receipt. The proposed integration of Verbalized Sampling (VS) can materially improve the system, but only if it is treated as a proposal-generation mechanism rather than a truth or confidence mechanism.

The strongest combined architecture is a two-stage epistemic machine: a generative layer exposes multiple candidate interpretations or solutions; Concordance then removes duplicates, classifies claims, applies deterministic checks where available, quarantines unsupported assertions, and preserves the narrowing history. This creates a defensible control layer for nondeterministic agents.

Red-team judgment

The Candidate Engine is strategically attractive, but it expands attack surface. It can amplify hallucinations, adversarial tails, correlated errors, and verification shopping unless the candidate set is immutable, fully logged, typed before scoring, and evaluated under fixed policies.

Top decisions

Adopt CandidateSet as a first-class primitive, but store model-reported probabilities only as proposal_weight.

Keep candidate generation outside the trusted verification boundary.

Require complete candidate-set retention and receipt; do not seal only the winning answer.

Prohibit candidate-specific verifier selection after outcomes are observed.

Remove private keys from MCP inputs and outputs before presenting the identity layer as sovereign.

Fix parsed Origin validation and require loopback-only or authenticated remote deployment.

Publish a scoped benchmark for both verification correctness and candidate-engine performance.

Risk register

Priority

Finding

Severity

Primary consequence

Required control

P0

Private keys cross MCP boundary

Critical

Credential compromise; sovereignty claim invalidated

Local key generation; detached signatures only

P0

Origin prefix validation

High

Lookalike origins may pass

Parse scheme/host/port; adversarial tests

P0

Unauthenticated remote MCP

High

Any reachable process may invoke writes

Loopback default or scoped authentication

P0

VS probability laundering

High

Proposal weights presented as truth confidence

Rename, type, and visually separate weights

P0

Selective candidate disclosure

High

Unfavorable candidates omitted after generation

Commit candidate-set hash before verification

P1

Verification shopping

High

Choose verifier that makes preferred candidate pass

Pre-registered routing policy

P1

Tail-risk amplification

High

Rare harmful or deceptive candidates intentionally surfaced

Safety filter before persistence or execution

P1

Remote redaction

High

Raw PII leaves device before stripping

Edge-only redaction profile

P1

Protocol/version hybrid

High

Interoperability and semantic ambiguity

Explicit version negotiation and conformance matrix

P1

Tool catalog breadth

Medium

Selection errors and excessive privilege

Operational MCP profiles

P2

Loose schemas/errors

Medium

Malformed calls and brittle clients

Typed schemas and MCP error envelopes

P2

Benchmark overclaim

Medium

Credibility and legal/reputational risk

Release-scoped public benchmark

1. Scope and analytical frame

This report integrates the current Concordance/Narrow Highway red-team findings with the concepts presented by Verbalized Sampling. It evaluates not only whether the technique improves diversity, but whether it can be introduced without weakening provenance, verification, privacy, consent, or authority boundaries.

1.1 Trust zones

Zone

Function

Trust status

Permitted authority

A. User / principal

Defines purpose and accepts consequential actions

Highest human authority

Intent, consent, final judgment

B. Generative model

Produces interpretations, candidates, drafts

Untrusted/nondeterministic

Proposal only

C. Candidate Engine

Normalizes, deduplicates, routes, preserves alternatives

Controlled but not authoritative

Process coordination

D. Concordance verifier

Runs deterministic domain checks

Trusted within declared verifier scope

Bounded verdict

E. Receipt/ledger

Preserves inputs, methods, versions, outcomes

Integrity layer

Historical proof, not truth source

F. External systems

Calendars, communities, remote services

Open-world and consequential

Only through explicit scoped grants

2. Current architecture: strengths worth preserving

Bounded verification. The system distinguishes deterministic verification from retrieval, citation, signposting, and user-authored speech.

Quarantine semantics. Unsupported or incomplete material can remain unresolved without being forced into true/false.

Worked trails and seals. The result can be independently rechecked against declared inputs and methods.

Read-only search behavior. Library retrieval no longer implies hidden acquisition or mutation.

Surface separation. Secular and witness presentations can share an engine without duplicating the core.

Append-only governance patterns. Authorship, amplification, curation, and verification remain distinct events.

Preservation rule

Do not let the Candidate Engine collapse these distinctions. A generated candidate is neither a source, a verified claim, nor a human judgment.

3. Fresh red-team findings on the MCP boundary

3.1 Private-key exposure remains the critical defect

Tools that return or accept raw private keys place credential material inside the model/MCP/transport boundary. “Returned once” and “not stored server-side” do not make this sovereign key custody.

The correct contract is canonical signable bytes out; detached signature and public key back. Key generation and signing belong in a local signer, browser WebCrypto, operating-system keystore, hardware token, or Node.

3.2 Origin validation must parse origins, not match prefixes

Prefix tests such as startswith("http://localhost") can accept attacker-controlled lookalike hostnames. Normalize and compare scheme, hostname, and port. Include IPv6 loopback, default-port normalization, malformed origins, credentials, trailing dots, and mixed case in tests.

3.3 Origin checks are not caller authentication

Non-browser clients often omit Origin. A remotely reachable MCP endpoint therefore needs authentication independent of CORS. The safe default is loopback binding; remote mode should require scoped bearer capability, mTLS, or equivalent authorization.

3.4 Redaction is trustworthy only at the edge

A remote tool that receives raw text before redacting it cannot support a claim that the sensitive content never left the device. Remote profiles should accept only already-redacted payloads or mapping proofs.

3.5 Protocol semantics remain hybrid

A server should not declare one MCP revision while blending transport behavior from other revisions. Publish supported revisions, negotiate explicitly, and test against official and third-party clients.

3.6 Schemas, errors, and annotations remain part of the security model

Loose JSON schemas increase malformed calls; ordinary {"error": ...} objects make failures ambiguous; absent read/write/open-world annotations obscure risk. These are not cosmetic developer-experience issues—they affect model tool selection and host authorization.

4. What Verbalized Sampling actually contributes

Verbalized Sampling is a training-free prompting strategy that asks an LLM to produce multiple responses and verbalized probabilities, often explicitly sampling from low-probability tails. The project reports higher diversity across creative writing, dialogue simulation, open-ended questions, and synthetic-data generation while maintaining task quality in its experiments.

Its useful contribution to Narrow Highway is not that the self-reported probabilities are calibrated. They are not evidence. The valuable contribution is procedural: the model is induced to expose a wider set of latent alternatives before a single typical response suppresses them.

Key reinterpretation

VS is a candidate generator. It is not a confidence engine, verifier, ranker, or authority source.

4.1 Concepts to adopt

Distribution before decision. Preserve several plausible alternatives before narrowing.

Tail exploration. Deliberately surface less typical hypotheses when the cost of missing an alternative exceeds the cost of checking it.

Training-free deployment. Use prompt-level generation without requiring model retraining or privileged logits.

Model-agnostic generation. Allow several providers or local models to contribute candidate sets.

Repeatable sampling recipes. Record generator prompt, model, parameters, seed where available, and transformation steps.

4.2 Concepts not to inherit unmodified

Verbalized probability as confidence. A model-authored number is proposal metadata, not calibrated truth probability.

Blind tail sampling. Rare outputs can include rare insights, but also rare deception, unsafe content, and pathological reasoning.

Winner-only retention. Discarding losing candidates hides the actual search path and enables selective reporting.

Single-model diversity claims. Five answers from one model may be surface variants of one correlated misconception.

Quality inferred from diversity. Novelty and independence must be measured separately from correctness and usefulness.

5. Proposed Candidate Engine

Candidate Engine should be a distinct layer between the generative model and Concordance. It controls candidate-set integrity and routing, but it does not decide truth.

Stage

Operation

Trusted output

1. Generate

Request k alternatives using direct, VS, multi-model, retrieval-guided, or adversarial generation

Raw candidates only

2. Commit

Hash the complete raw candidate set before evaluation

Candidate-set commitment

3. Normalize

Canonicalize format without changing substantive claims

Normalized candidates + transformation log

4. Deduplicate

Cluster semantic duplicates while retaining lineage

Equivalence groups

5. Type

Separate factual claims, interpretations, plans, values, creative options, and unsafe actions

Claim-type labels

6. Route

Assign verifiers under a fixed predeclared policy

Verifier plan

7. Evaluate

Run deterministic checks, source retrieval, policy gates, and human review

Per-candidate evidence records

8. Narrow

Apply declared selection rule; preserve rejected/quarantined candidates

Decision trace

9. Receipt

Seal full set, policies, versions, results, and selected output

Recheckable receipt

5.1 CandidateSet schema

The following fields should be first-class and versioned:

Field

Meaning

Authority status

candidate_set_id

Content-addressed or random identifier

System identifier

query_hash

Hash of normalized user request and governing context

Integrity metadata

generator

Model/provider/version or human source

Provenance

generation_method

direct, VS, multi-agent, retrieval-guided, adversarial

Provenance

prompt_hash

Hash of exact generation instructions

Integrity metadata

candidate_id

Stable identifier within the set

System identifier

raw_text

Unmodified generated candidate

Untrusted content

normalized_claims

Typed atomic claims extracted from candidate

Derived content

proposal_weight

Model-verbalized probability or generator weight

Untrusted metadata

cluster_id

Duplicate/equivalence grouping

Derived metadata

safety_status

allow, restrict, reject, human-review

Policy result

verification_status

pass, reject, quarantine, not-applicable

Bounded result

evidence_refs

Sources and verifier receipts

Grounding

selection_status

selected, rejected, retained-alternative

Decision result

parent_ids

Lineage for recursive rounds

Provenance

receipt_hash

Commitment to full history

Integrity proof

5.2 Required invariant

Invariant

No candidate may move from proposal to verified fact merely because it has a high proposal_weight, appears in several correlated samples, or wins a model-based ranking.

6. Integrated threat model for candidate generation

Threat

Attack/failure mode

Control

Probability laundering

User or UI interprets 0.08 or 0.62 as factual confidence

Rename to proposal_weight; prohibit “confidence” labels; calibration warnings

Selective disclosure

System shows only winning candidate, hiding contrary alternatives

Commit and retain complete set before checking

Candidate suppression

Normalizer or deduplicator removes inconvenient minority hypothesis

Preserve raw set and lineage; reversible clustering

Correlated diversity

Many outputs share one hidden error

Cross-model generation; semantic cluster count; source independence

Tail-risk amplification

Tail prompt surfaces unsafe or manipulative material

Pre-persistence safety gate; no automatic execution

Verification shopping

System chooses a favorable verifier after seeing candidate

Pre-registered routing policy and audit log

Metric gaming

Generator optimizes for passable surface form rather than substance

Atomic claim extraction; adversarial paraphrase tests

Recursive drift

Later rounds move away from original user question

Query constraint checks and lineage distance limits

Prompt injection

Candidate text instructs tools or changes policy

Treat candidate as data; never interpolate into system/tool instructions

Receipt laundering

Seal is presented as proving truth rather than process integrity

Typed receipt labels and scope statement

Cost denial

Attacker forces large k, recursion, or expensive verifiers

Budgets, caps, quotas, early stopping

Privacy multiplication

Sensitive input copied across many candidates and logs

Local generation/redaction; retention minimization; encrypted vault

7. Selection and narrowing policy

The narrowing policy must be declared before outcomes are observed. Otherwise the system can rationalize a preferred answer by changing weights, verifier choice, or stopping conditions after the fact.

7.1 Recommended decision order

Remove policy-prohibited candidates before any external action, while preserving an audit reference where legally and ethically appropriate.

Collapse exact and semantic duplicates without deleting lineage.

Classify candidate type; do not apply truth verifiers to values, creative options, or preferences.

Run deterministic verification where a verifier exists.

Retrieve and assess sources where verification is evidentiary rather than mathematical.

Quarantine unresolved factual claims.

Rank surviving candidates by task-specific utility, not proposal weight alone.

Present material alternatives when the decision remains underdetermined.

Seal the whole narrowing path, including rejected and quarantined candidates.

7.2 Scoring model

A candidate utility score may combine independent dimensions, but must not collapse them into a false “truth probability.” A defensible structure is:

Dimension

Example range

Meaning

Verification

reject / quarantine / pass

Bounded deterministic or evidentiary status

Source quality

0–4 ordinal

Authority and independence of grounding

Task fit

0–4 ordinal

Relevance to the user’s actual objective

Novelty

0–4 ordinal

Distinctiveness from other candidates

Feasibility

0–4 ordinal

Practical implementability

Risk

low / medium / high / prohibited

Potential harm or irreversible consequence

Proposal weight

raw model value

Generation metadata only; never truth score

8. MCP integration design

8.1 Profiles

Profile

Tools

Default posture

candidate-read

candidate_set_get, candidate_list, narrowing_trace_get

Read-only

candidate-generate

candidate_generate, candidate_expand

Open-world generation; bounded cost

candidate-process

candidate_normalize, candidate_deduplicate, candidate_type

Derived writes; deterministic where possible

candidate-verify

candidate_route, candidate_verify

Verifier-bound; no generator privileges

candidate-select

selection_plan_create, candidate_select

Human-confirmed for consequential tasks

receipt

candidate_receipt_create, candidate_receipt_verify

Append-only integrity

identity

public-key registration and signature verification only

No private keys

8.2 Tool separation

Do not expose one “generate_and_verify” tool. Combined tools obscure where nondeterminism ended and deterministic checking began. Each stage should emit a typed artifact that becomes the next stage’s input.

8.3 Annotations and authorization

Generation tools. open-world, non-idempotent, cost-bounded, not authorized to act externally.

Normalization and deduplication. idempotent for fixed version and inputs; preserve raw lineage.

Verification. read-only unless a separate receipt tool is called.

Selection. requires declared policy; human confirmation for high-impact choices.

Receipt creation. append-only write; should be idempotent by content hash.

External action. separate profile, explicit scoped grant, never callable from candidate text.

9. Evaluation program

The integration should be justified by controlled evidence. Diversity improvement alone is insufficient.

Question

Metric

Required comparison

Does VS widen useful alternatives?

Semantic cluster count; human novelty rating

Direct sampling vs VS at equal token/cost budget

Does verification improve correctness?

False positives, false negatives, quarantine rate

Generator-only vs generator + Concordance

Are weights misleading?

Calibration error; user interpretation study

proposal_weight shown vs hidden vs relabeled

Does multi-model generation reduce correlation?

Error correlation and source diversity

Single-model VS vs multi-model CandidateSet

Does recursion help?

Solved rate, verifier calls, cost, drift

One-round vs recursive narrowing

Can the process be reproduced?

Receipt replay success

Same versions/input vs changed versions

Does tool partitioning help?

Tool-selection accuracy and unauthorized-call rate

Monolithic MCP vs profiles

Is privacy preserved?

Raw sensitive data egress events

Local vs remote generation/redaction

9.1 Mandatory adversarial tests

Candidate contains tool-call instructions or fake system messages.

Five candidates differ stylistically but contain the same false premise.

Low proposal-weight candidate is the only correct answer.

High proposal-weight candidate conflicts with deterministic verification.

Candidate splitter changes a negation or numeric qualifier.

Deduplicator merges two materially different legal or theological propositions.

Routing policy is manipulated by wording to select a weaker verifier.

Recursive expansion drifts from the original question.

User requests automatic execution of a rare candidate.

Candidate set includes personal information that should never reach a remote model.

10. Product opportunities

10.1 Verified brainstorming

Generate a broad option field, then remove options that violate explicit constraints. Preserve creative or strategic alternatives without falsely calling them verified.

10.2 Diagnostic differential

For non-medical system diagnosis, generate multiple failure hypotheses and route each to measurable tests. In medical or legal settings, the engine may organize questions and evidence but must not substitute for licensed judgment.

10.3 Research hypothesis map

Expose competing explanations, attach source requirements, and mark which are supported, contradicted, or unresolved. This is a strong fit for Concordance’s quarantine semantics.

10.4 Agent planning

Generate several plans, verify prerequisites and constraints, and require human approval before external actions. The selected plan receives a receipt that includes discarded alternatives and the governing policy.

10.5 Synthetic-data generation

VS can diversify synthetic examples, while Concordance enforces schema, invariants, deduplication, and contamination checks. Generated labels must not be treated as verified ground truth without an independent oracle.

11. Uses to prohibit or tightly constrain

Use

Reason

Policy

Direct medical diagnosis

Tail candidates can cause serious harm and probabilities are uncalibrated

Educational differential only; clinician review

Legal outcome prediction

Jurisdictional and evidentiary uncertainty

Research support only; lawyer review

Credit, hiring, insurance selection

Alternative generation may encode protected-class proxies

No autonomous adverse decisions

Financial trading/execution

Rare hypotheses can trigger irreversible loss

No direct execution; independent controls

Identity/key management

Generative layer must never handle secrets

Local signer only

Moderation punishment

Tail generation can invent accusations

Evidence and due-process requirements

Scriptural authority claims

Generated interpretation is commentary/signpost

Source hierarchy and explicit attribution

12. Ninety-day implementation roadmap

Window

Deliverables

Exit gate

Days 0–15

Remove private keys from MCP; fix Origin parsing; loopback default; document remote auth; disable remote raw-text redaction

Security tests pass; no key material in API schemas

Days 16–30

Define CandidateSet v0.1; implement complete-set commitment; add typed proposal_weight; preserve raw lineage

Schema fixtures and replay tests

Days 31–45

Build generation adapter for direct and VS methods; add fixed generation budgets; add safety prefilter

No external action path; cost caps enforced

Days 46–60

Implement normalization, deduplication, typing, and routing policy; separate verify from receipt creation

Determinism tests for fixed versions

Days 61–75

Add MCP profiles, annotations, strict schemas, error envelopes, authentication scopes

Interoperability and privilege tests

Days 76–90

Run ablations and red-team suite; publish benchmark, limitations, and reference receipts

Release decision based on predefined thresholds

13. Release gates

No private key appears in any network-facing schema, log, receipt, or model context.

Every candidate set is committed before verification and selection.

Proposal weights are never labeled confidence, likelihood of truth, or probability of correctness.

Verifier routing is versioned and fixed before candidate outcomes are observed.

Raw and normalized candidates are linked by reversible transformation records.

Rejected and quarantined candidates remain auditable under retention policy.

High-impact selection or external action requires explicit human approval and scoped authorization.

Local and remote deployment modes expose different privacy-sensitive tools.

Protocol conformance is tested against named MCP clients and revisions.

Published performance claims identify release, dataset, methods, and failure counts.

14. Final strategic judgment

Verbalized Sampling is compatible with Narrow Highway only when its role is sharply bounded. It should increase the breadth of proposals, not the authority of the model. Concordance should then narrow that breadth through declared tests and preserve the complete path so the outcome is inspectable.

Recommended architecture

Generative model → CandidateSet commitment → normalize/deduplicate/type → fixed verifier routing → pass/reject/quarantine → task ranking → human judgment → full-path receipt.

This is more than an integration of one prompting technique. It creates a general Candidate Engine in which VS is one replaceable generator among direct sampling, retrieval-guided generation, multi-model debate, human submissions, and adversarial search. The durable product is the governed narrowing process.

The strategic opportunity is therefore: a deterministic control and receipt layer that allows nondeterministic agents to explore widely without silently converting possibility into fact, confidence, authority, or action.

Sources reviewed

Verbalized Sampling project site: https://www.verbalized-sampling.com/

Verbalized Sampling paper: https://arxiv.org/abs/2510.01171

Verbalized Sampling implementation: https://github.com/CHATS-lab/verbalized-sampling

Concordance repository: https://github.com/matharrismma/concordance-2

Narrow Highway public site: https://narrowhighway.com/

