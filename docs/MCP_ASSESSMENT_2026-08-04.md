# Independent Technical Review — Narrow Highway MCP (2026-08-04)

> Provenance: extracted verbatim from `Narrow_Highway_MCP_Rigorous_Assessment.docx`, received by
> Matt Harris 2026-08-04 (external, independent, static review of the public repository). Adopted
> the same day as the SPEC for the MCP hardening arc (tasks #123-#127). Formatting flattened to
> plain text by extraction; wording untouched. The original .docx remains with Matt.
>
> Same-day vindication: finding F-03 (protocol version dictated, not negotiated) caused a real
> production outage on narrowhighway.com/mcp hours after this review was written; fixed in
> be2b6b0. F-01 (private keys) was stale — resolved 2026-07-28.

INDEPENDENT TECHNICAL REVIEW
Narrow Highway MCP
Rigorous Architecture, Protocol, Security, Product-Surface, and Strategic Assessment

CORE CONCLUSION
Narrow Highway is not merely an “AI fact-checker.” Its most defensible position is a deterministic control, authorization, provenance, and receipt layer placed between nondeterministic agents and human-controlled systems. The architecture contains genuine differentiation. The current MCP surface, however, exposes too many domains through one connector and requires a disciplined protocol, security, schema, and productization pass before it should be presented as mature infrastructure.

Prepared for Matt Harris4 August 2026

Executive Summary
This assessment reviews the public Concordance 2 repository and its Model Context Protocol implementation as a technical system, a governance model, and a product surface. The review is static: it evaluates the repository, declared behavior, schemas, transport code, and documentation visible at the time of review; it does not claim an independent runtime penetration test or benchmark reproduction.
OVERALL RATING
Promising architecture; pre-production MCP product surface. The implementation demonstrates an unusually coherent philosophy of bounded agency, deterministic checking, local key custody, delegated consent, append-only receipts, and differentiated authorship. The principal weakness is not lack of substance but insufficient separation: one server exposes verification, library, education, identity, community, finance, and witness functions with inconsistent risk signaling and underconstrained schemas.

Decision-grade findings
Area
Assessment
Implication
Strategic differentiation
HIGH
The strongest proposition is deterministic control and receipts for agent actions—not generalized truth generation.
Core architecture
STRONG
The claim → verifier → verdict/trail → seal → ledger model is coherent and technically legible.
MCP tool surface
WEAK
The catalog is too broad for reliable tool selection, permission review, and external comprehension.
Protocol conformance
MATERIAL RISK
The code declares MCP 2024-11-05 while implementing later Streamable HTTP concepts; compatibility should be explicit and tested.
Security model
MIXED
Local-key and scoped-consent ideas are strong, but transport sessions, authentication assumptions, secret handling, and remote deployment boundaries require hardening.
Schemas and errors
IMMATURE
Many input schemas lack enums, nested constraints, limits, and additionalProperties rules; business errors are frequently returned as ordinary data.
Evidence and claims
NEEDS QUALIFICATION
“0 false positives” should be stated as benchmark-bounded and accompanied by a reproducible benchmark package.
Commercial readiness
EARLY
The platform thesis is compelling, but developer onboarding, compatibility matrices, policy resources, profiles, observability, and release discipline are not yet at infrastructure-product maturity.

Recommended action
Treat the repository as a strong architectural prototype and begin a focused MCP hardening program. Do not expand the tool catalog until the existing surface is divided into profiles, protocol behavior is versioned, schemas are made strict, write-capable tools are explicitly classified, and security controls are documented and tested.

1. Scope, Method, and Confidence
1.1 Materials reviewed
Repository overview and README claims.
The stdlib JSON-RPC MCP server implementation in src/concordance/mcp/server.py.
The Streamable HTTP wrapper in src/concordance/mcp/http.py.
The V2 definition document describing the “one foundation, two surfaces” model and Calibre 44 engineering discipline.
Public repository structure and status statements.
1.2 Review lenses
Lens
Question
Architecture
Are the primitives coherent, bounded, and independently testable?
MCP protocol
Does the server present predictable, interoperable protocol behavior?
Agent usability
Can a model select the correct tool with low ambiguity?
Security &amp; privacy
Are authority, secrets, identity, consent, and remote exposure controlled?
Epistemics
Does the system distinguish source, claim, inference, verification, and uncertainty?
Product strategy
Is the external position narrow enough to understand and valuable enough to adopt?
Evidence
Are performance and reliability claims reproducible and properly scoped?

1.3 Confidence limits
Confidence is high regarding visible design choices and static implementation patterns. Confidence is moderate regarding runtime interoperability because no live client matrix or full test execution was available in this review. Confidence is low regarding production security posture because deployment configuration, secrets management, traffic controls, audit logs, dependency scanning, and operational procedures were not independently examined.
2. Architectural Thesis
2.1 What the system actually is
The repository describes seven primitives: structured claim, deterministic verifier, verdict, content-addressed seal, append-only ledger, retrieval ranker, and surface. Every answer is intended to produce a verdict, worked trail, and seal. This is a meaningful architecture because it separates nondeterministic discovery or agent reasoning from a deterministic adjudication path.
BEST STRATEGIC FORMULATION
A nondeterministic agent may propose, search, summarize, or plan. Concordance should constrain, verify where a deterministic test exists, establish delegated authority, and issue a durable receipt. The human remains principal; the agent is not the authority; Concordance is not the source.

2.2 Strength of the primitive model
Determinism
A pure verifier allows repeatability, regression testing, and independent re-checking. This is a stronger foundation than relying on an LLM to “judge” its own output.
Worked trail
A verdict without a trail is an assertion. A trail provides the evidence necessary to inspect whether the verifier tested the intended proposition.
Content addressing
A seal bound to claim, verdict, and trail can detect alteration and support reproducibility, provided canonicalization and versioning are specified precisely.
Append-only history
A ledger makes later mutation visible and supports precedent, revocation, and standing-status checks.
Surface separation
The secular and witness surfaces are intentionally differentiated while sharing one engine. This can be coherent if code/data isolation and tool discovery are tested—not merely described.
2.3 Essential distinction: deterministic verification is not universal truth adjudication
The engine can strongly verify a claim only when the claim is reduced to a determinate specification and a valid verifier exists. It cannot infer that every historical, medical, legal, theological, scientific, or social proposition is “true” merely because a domain label is supplied. The product language must therefore distinguish at least five states:
The source says X.
The structured claim is well formed.
The specified deterministic test passes.
The evidence is corroborated by independent sources.
The broader proposition is true in the real world.
Concordance is strongest at the third step. It may support the first, second, and fourth through provenance and retrieval, but it should not silently collapse all five into one “verified” label.
3. MCP Surface Analysis
3.1 Current surface breadth
The server exposes a large cross-domain catalog including core verification, document auditing, library search and cards, redaction, finance, education, identity, badges, shared studies, groups, and an additional witness-only Scripture and reference layer. This breadth demonstrates platform ambition but produces an overloaded connector.
Tool family
Examples
Primary risk
Verification
verify, audit, seal_fetch
Semantic overclaim; inconsistent error/result envelopes
Library
search, locate, card_get, cards_browse
Overlapping discovery verbs; provenance and access controls
Privacy
redact
Remote-use misconception; mapping exposure
Steward
steward_budget, steward_cost_destroyed
Financial-context sensitivity; misleading “verification” halo
Coach
coach_unit, coach_recommend, coach_mastery
Child-data and educational-claim boundaries
Identity &amp; badges
identity_create, identity_verify, badges_issue
Private-key handling, signature semantics, long-lived trust
Community
groups_list/create/join/contribute
Moderation, authorization, abuse, pseudonymity limits
Witness
resolve, word_study, commentary, prophecy_traces
Source attribution, interpretive status, surface isolation

3.2 Why one giant catalog is a technical problem
Tool-selection accuracy falls as semantically adjacent tools proliferate.
Every tool definition consumes context and competes for model attention.
A client cannot easily distinguish read-only tools from state-changing or open-world operations.
The platform’s core identity becomes less clear to developers and adopters.
Security review becomes more difficult because low-risk retrieval and consequential writes share one discovery surface.
Versioning becomes coupled: a change to a community tool can force release of a core verification connector.
3.3 Recommended profile architecture
Profile
Representative tools
Purpose
concordance-core
verify, audit, find_verifier, seal_fetch, capabilities
Deterministic checks and receipts
nh-library
search_library, locate_card, get_card, browse_cards, connections, health
Private/source-backed retrieval
nh-sovereign
identity, signable payloads, consent, authorization receipts
Identity and delegated agency
nh-coach
subjects, units, recommendations, progress receipts
Bounded curriculum access
nh-witness
passage, concordance, lexical, commentary, references
Attributed Scripture study
nh-community
groups, shelves, contributions, moderation
Separate high-risk social plane

Profiles should be deployment- and discovery-level boundaries, not merely documentation sections. A client should mount only the profile it needs. The same internal engine may serve several profiles, but each profile should have a separate manifest, permission model, test suite, and version.
4. MCP Protocol and Interoperability
4.1 Version/transport mismatch
The server advertises protocol version 2024-11-05. The HTTP wrapper describes and implements Streamable HTTP features, including POST /mcp, optional SSE responses, session IDs, and DELETE termination. Streamable HTTP belongs to later MCP revisions. The result is a blended compatibility posture: an older declared protocol paired with later transport behavior.
SEVERITY: MATERIAL
This may work with permissive clients, but it is not a durable interoperability strategy. MCP clients increasingly make behavior decisions from negotiated protocol versions. The server must either implement each supported revision explicitly or declare only the revision whose semantics it actually follows.

4.2 Required protocol work
Implement initialization negotiation using the client-requested protocol version and return the negotiated supported version.
Publish a compatibility matrix: client, transport, protocol revision, tested release, result.
Separate legacy and modern HTTP behavior when semantics differ.
Add conformance tests for initialize, notifications, batch handling, invalid requests, unknown methods, tool errors, SSE negotiation, origin checks, and connection termination.
Return JSON-RPC protocol errors for malformed methods/parameters and MCP tool errors with isError for execution failures.
Define whether resources, prompts, logging, progress, cancellation, and elicitation are unsupported or planned; do not leave their absence ambiguous.
4.3 Batch and notification behavior
The HTTP wrapper accepts batch payloads and skips non-dictionary items. A rigorous implementation should return the protocol-defined error for invalid request elements rather than silently dropping them. Notification-only batches should produce the exact expected status/body behavior for the negotiated revision. These edge conditions are where clients diverge and where conformance tests create disproportionate value.
5. Security, Privacy, and Authority Model
5.1 Strong design choices
The philosophy separates self-attestation from verified standing.
Detached signatures and fingerprints support portable identity.
Scoped, expiring grants can bind agent authority to a particular action.
Append-only receipts create an inspectable authorization trail.
Origin allowlisting addresses browser-origin DNS rebinding concerns.
Witness-only imports are lazy and surface-gated in the visible server code.
5.2 High-priority risks
Risk
Severity
Analysis
Private keys in MCP arguments
Critical design concern
Several tool schemas accept private_key. Even if not persisted, remote MCP transport, client logs, tracing, crash reports, proxies, and model context can expose it. Private keys should never be tool arguments.
Identity creation over remote MCP
High
Returning a private key once is not sufficient protection. Key generation should occur client-side or in a local secure enclave/keystore.
Authentication ambiguity
High
Origin checks are not authentication. Non-browser clients without Origin are allowed. Hosted deployment requires explicit client authentication and authorization.
Session token ambiguity
Medium
Lenient acceptance of missing/unknown session IDs means sessions are not a security boundary. Documentation must say so; modern profiles may omit them.
Redaction misconception
High
A remote redaction tool receives the unredacted text before stripping it. The tool description acknowledges local use, but the product UX must prevent a false sense of privacy.
Pseudonymity claims
Medium
Handles and absence of displayed PII do not guarantee anonymity; network, timing, content, and graph metadata can re-identify users.
Community abuse surface
High
Group creation, joining, and contribution introduce spam, harassment, illegal content, impersonation, and moderation obligations.
Child-related surfaces
High
Coach features should be physically and operationally isolated from community functions, with no shared identifiers or accidental cross-surface discovery.

5.3 Recommended key architecture
Replace private-key-bearing tools with a signable-payload protocol:
Server returns canonical payload bytes, purpose, expiry, nonce, and expected signer fingerprint.
Client signs locally using an OS keystore, hardware key, secure enclave, or local software wallet.
Client sends only public key/fingerprint, payload identifier, and detached signature.
Server verifies signature and records a receipt referencing the authorization basis.
Secrets are excluded from model context, tool arguments, HTTP logs, application traces, and error reports.
5.4 Threat model required before hosted release
The project should publish a concise threat model covering malicious clients, prompt-injected agents, compromised MCP hosts, replay, signature confusion, stale grants, privilege escalation across profiles, corpus poisoning, seal-store tampering, denial of service, metadata leakage, and hostile community content. Each threat should map to a control and a test.
6. Tool Contracts, Schemas, and Error Semantics
6.1 Schema rigor
Many tool schemas declare strings, arrays, or objects without constraining vocabulary, nested shape, length, numeric range, hash format, date format, or unexpected fields. Prose descriptions carry rules that should be machine-enforced.
Current pattern
Required improvement
Benefit
mode: string
enum of supported modes
Prevents unsupported calls
steps: array of object
required id/domain/spec; additionalProperties false
Validates packets before dispatch
hash: string
SHA-256 pattern and exact length
Rejects malformed content IDs
limit: integer
minimum 1; bounded maximum
DoS and response-size control
expenses/items: array
typed item schema with required fields
Predictable calculations
kind/ring/action: string
explicit enums
Reliable agent selection
dates/times: string
format plus timezone rules
Deterministic interpretation
private_key: string
remove from server tools
Eliminates secret transit

6.2 Error model
The dispatcher frequently returns ordinary objects such as {"error": "card not found"}. This forces clients and agents to inspect arbitrary result data to determine whether execution succeeded. Adopt a uniform error taxonomy and MCP-native error signaling.
Recommended application codes include: INVALID_SPEC, VERIFIER_NOT_FOUND, CLAIM_INCOMPLETE, SEAL_NOT_FOUND, CARD_NOT_FOUND, AUTHORIZATION_REQUIRED, GRANT_EXPIRED, SIGNATURE_INVALID, SURFACE_FORBIDDEN, RATE_LIMITED, and INTERNAL_FAILURE. Each error should state whether retry, user correction, additional evidence, or administrator action is appropriate.
6.3 Tool annotations and risk metadata
Every tool should declare read-only, destructive, idempotent, and open-world characteristics where supported. Narrow Highway should go further by publishing its own signed metadata fields:
data_classification: public | private | child | financial | identity
effect: read | derive | preserve | publish | external_action
authority_required: none | user_intent | signed_grant | administrator
secret_policy: none_allowed
network_scope: local_only | corpus_only | open_world
receipt_behavior: none | optional | mandatory
7. Epistemic and Provenance Model
7.1 Required status vocabulary
Dimension
Example values
Meaning
Execution
success, partial, failed
Did the operation run?
Claim completeness
complete, incomplete
Was there enough information to test?
Deterministic verdict
holds, broken, not-applicable
Did the specified verifier pass?
Evidence status
single-source, corroborated, conflicting
How broad is support?
Source authority
primary, official, secondary, user
What kind of source supplied the assertion?
Interpretive status
quotation, calculation, inference, opinion
What transformation occurred?
Receipt standing
standing, superseded, revoked, unverifiable
Does the record still validate?

7.2 “Conduit, not source” as a protocol rule
The phrase should become enforceable metadata, not only philosophy. Every returned proposition should identify its speaker/source, the operation applied, and whether the system is quoting, calculating, classifying, inferring, or merely locating. Generated explanatory text—if ever introduced—must be typed separately from source text and must never inherit the source’s authority.
7.3 Seal specification requirements
Canonical serialization standard and encoding.
Exact included/excluded fields and stable ordering.
Hash algorithm and algorithm agility/version field.
Verifier identifier and verifier version.
Corpus/source versions and retrieval timestamp where relevant.
Treatment of timestamps, nonces, locale, units, rounding, and floating-point behavior.
Replay procedure and independent verification utility.
Supersession, revocation, and standing rules.
8. Evidence, Benchmarking, and Public Claims
8.1 “0 false positives”
The repository states zero false positives and describes the result as benchmarked. The defensible wording is “0 false positives on the published benchmark for release X.” A universal zero-false-positive claim is stronger than a finite benchmark can establish.
8.2 Minimum benchmark package
Versioned dataset with licensing and provenance.
Per-domain positive, negative, incomplete, malformed, adversarial, and boundary cases.
Expected verdict and expected trail assertions.
Exact engine version, optional dependencies, platform, and configuration.
False positives, false negatives, quarantines/incompletes, and system errors reported separately.
Mutation tests proving that broken verifiers cause benchmark failures.
Independent reproduction command and machine-readable output.
Regression history across releases.
8.3 Additional quality measures
Measure
Why it matters
Determinism rate
Same input/config must yield identical semantic result and seal.
Coverage precision
Audit must not imply that unextracted claims were checked.
Schema rejection rate
Malformed requests should fail safely and predictably.
Tool-selection success
Agents should choose the intended tool in realistic prompts.
Authorization integrity
No action without a valid scoped grant; no replay after expiry.
Interoperability
Known clients and protocol revisions pass a repeatable suite.
Recovery
Ledger/corpus restore procedures preserve standing and provenance.

9. Product Positioning and Adoption
9.1 Recommended category
POSITION
Deterministic trust and control infrastructure for AI agents: verify structured claims, enforce delegated authority, preserve provenance, and issue re-checkable receipts before consequential actions.

This is more differentiated than “fact checker,” “Christian AI,” “knowledge base,” or “MCP toolbox.” Those descriptions capture modules but not the durable architectural value.
9.2 Ideal first adopter
The initial adopter should have high need for auditability but a bounded action surface—for example, an internal policy assistant, educational content system, regulated calculation workflow, grant/compliance review process, or source-grounded research environment. Avoid launching first as a broad public social platform; community moderation would consume attention before the core trust layer is proven.
9.3 Product wedge
Core verifier and receipt server with five excellent workflows.
Local-first library search with provenance.
Consent-gated single external action demonstrating delegated agency.
Independent receipt verifier CLI/library.
Published benchmark and client compatibility suite.
9.4 Licensing and ecosystem consideration
The repository identifies AGPL-3.0 software and CC-BY-SA content licensing. That can advance sovereignty and prevent proprietary enclosure, but enterprise adopters may require clear guidance on network-use obligations, separable content licensing, hosted-service terms, and commercial support. Licensing strategy should be deliberate and explained in plain language; this assessment is not legal advice.
10. Prioritized Remediation Roadmap
Priority
Action
Domain
Gate
P0
Remove private keys from MCP arguments; make signing local
Security
Before any remote hosted use
P0
Define authentication/authorization for non-browser clients
Security
Before public endpoint
P0
Align declared MCP version with implemented transport behavior
Interop
Before registry/client promotion
P0
Split read-only retrieval from state-changing/open-world tools
Safety
Before broad agent use
P1
Create profile-specific MCP manifests and deployments
Product/UX
Next release
P1
Tighten every input schema and add bounded limits
Reliability
Next release
P1
Adopt structured MCP error signaling and application codes
Interop
Next release
P1
Add annotations and Narrow Highway risk metadata
Safety/UX
Next release
P1
Publish seal canonicalization and independent verifier
Trust
Next release
P1
Publish reproducible benchmark and qualify claims
Evidence
Next release
P2
Add threat model, security tests, rate limits, audit controls
Operations
Before scale
P2
Create developer quickstart and compatibility matrix
Adoption
Before external beta
P2
Add release/version policy for tools, schemas, verifiers, receipts
Governance
Before third-party integration
P3
Expand tools only after selection and permission metrics are stable
Scope
Ongoing

10.1 Suggested 90-day sequence
Days 1–30: establish the trust boundary
Freeze tool expansion. Remove private-key inputs. Define profiles, protocol support, authentication assumptions, canonical receipt format, and error taxonomy. Build conformance and security test scaffolding.
Days 31–60: harden the connector
Implement strict schemas, annotations, profile manifests, version negotiation, local signing flow, authorization enforcement, rate limits, structured logs without secrets, and independent seal verification.
Days 61–90: prove the product
Publish benchmark package, client compatibility results, five reference workflows, threat model, deployment guide, and a limited external beta centered on concordance-core plus one consent-gated action.
11. Target Reference Architecture
A disciplined deployment should separate agent-facing protocol, deterministic computation, state, identity, and external effects:
Component
Responsibility
MCP profile gateway
Version negotiation, strict schemas, annotations, authentication, rate limits
Policy/authorization service
User intent, scoped grants, expiry, nonce/replay checks, profile boundaries
Deterministic verifier registry
Pure functions, explicit versions, domain packets, no network I/O
Receipt service
Canonicalization, hashing, signing/attestation metadata, standing/supersession
Corpus service
Provenance, access control, source licensing, immutable source snapshots
Local signer
Keys never cross MCP; hardware/OS keystore preferred
Effect adapters
Calendar/publish/send actions isolated, least privilege, mandatory receipt
Audit plane
Secret-free logs, security events, metrics, conformance evidence

11.1 Action classification
Class
Examples
Default policy
Read
Fetch card, passage, seal
Allowed within profile and data access rights
Derive
Verify, calculate, compare
Allowed; operation and verifier version disclosed
Preserve
Create seal, progress receipt, study entry
Requires explicit user intent; idempotency defined
Publish
Group contribution, shelf/commons promotion
Requires identity, audience preview, confirmation, moderation controls
External action
Calendar create, send, transact
Requires scoped signed grant, least privilege, mandatory receipt

12. Release Gates
12.1 Core beta: GO when
No private key can enter an MCP request.
At least two current MCP clients pass the published conformance suite.
Every exposed tool has strict schema, risk metadata, and deterministic error behavior.
The receipt format is independently verifiable.
The benchmark is public, reproducible, and claims are benchmark-bounded.
Read-only core profile is isolated from community and external-effect tools.
Authentication and rate limiting are enabled for hosted use.
12.2 Hosted broad release: NO-GO until
Threat model and security review completed.
Consent and replay controls tested adversarially.
Community moderation, abuse response, and child-surface isolation are operational.
Backup, restore, revocation, supersession, and incident response are documented.
Telemetry proves acceptable tool-selection accuracy and low failed-call ambiguity.

13. Final Assessment
Narrow Highway contains a serious and original architecture. Its strongest ideas are not cosmetic: deterministic verification, worked trails, content-addressed receipts, local key custody, scoped consent, append-only standing, and careful separation of author, curator, verifier, and source. Those elements can form a defensible trust layer for agentic systems.
The repository is not yet a mature general-purpose MCP platform. Its present surface is too broad, its schemas too permissive, its protocol posture too blended, and its secret-handling model too risky for remote deployment without revision. The correct response is not to reduce the ambition of the engine. It is to narrow and harden the connector.
BOTTOM LINE
Build the engine broadly; expose it narrowly. Make every boundary machine-readable. Keep keys local. Version the protocol and verifiers. Publish the benchmark. Let receipts—not rhetoric—carry the trust claim.

Appendix A — Finding Register
ID
Severity
Finding
Primary remedy
F-01
Critical
Private-key fields appear in MCP tool schemas
Remove; client-side signing only
F-02
High
Hosted non-browser clients appear unauthenticated at transport layer
Add explicit authn/authz
F-03
High
Protocol version and Streamable HTTP semantics are misaligned
Version negotiation and conformance tests
F-04
High
One connector mixes read, preserve, publish, and external effects
Profile separation
F-05
High
Input schemas are underconstrained
Strict JSON Schema
F-06
Medium
Business errors returned as successful tool data
isError plus typed codes
F-07
Medium
Sessions are lenient and may be misunderstood
Remove or label non-security semantics
F-08
High
Remote redaction can be mistaken for edge privacy
Local-only path and UX warnings
F-09
Medium
Tool names overlap semantically
Namespace/profile and naming revision
F-10
Medium
Long descriptions inflate context and hide contracts
Policy resources plus concise descriptions
F-11
High
Zero-false-positive claim is broader than visible evidence
Published benchmark-bounded wording
F-12
Medium
Seal canonicalization not sufficiently externalized
Formal receipt specification and verifier
F-13
High
Community tools create moderation/abuse obligations
Separate deployment and governance
F-14
High
Child education and adult community surfaces require hard isolation
Separate identifiers, stores, profiles
F-15
Medium
No visible release compatibility policy
Semantic versioning for tools/schemas/verifiers

Appendix B — Source Notes
This review relied on the following public materials accessed on 4 August 2026:
GitHub repository: matharrismma/concordance-2 (repository overview and file structure).
src/concordance/mcp/server.py (tool definitions, dispatch, initialization, surface gating).
src/concordance/mcp/http.py (HTTP transport, origin checks, sessions, content negotiation).
docs/V2_DEFINITION.md (strategic definition, two-surface model, engineering philosophy).
Public Model Context Protocol specification and documentation for protocol-version and transport comparison.
Repository observations may change after the review date. Before acting on a finding, compare it against the current commit and run the full test suite and interoperability matrix.
Appendix C — Questions for the Maintainer
Which MCP clients and protocol revisions are currently tested in CI?
Is the hosted /mcp endpoint intended for anonymous public use, authenticated tenants, or local-first deployment only?
Which tools presently accept or return private keys, and can those flows be removed in favor of local signing?
What exact canonicalization procedure creates a seal, and is an independent verifier available?
Which benchmark supports the zero-false-positive statement, and what were false negatives, incomplete results, and system errors?
Are community, coach, witness, and core verification data physically separated or only surface-gated?
What is the intended stable product wedge for the next release: verifier, library, sovereign agency, coach, or full platform?
What compatibility and deprecation policy will govern tool names, schemas, verifiers, and receipt formats?
