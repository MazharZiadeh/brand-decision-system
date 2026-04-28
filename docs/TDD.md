**Technical Design Document**

Real-Time Brand Decision System

*Facilitator-Operated Bilingual Ideation Tool*

Document Version: 0.4 (Draft for Stakeholder Review)

Date: April 25, 2026

Author: Technical Lead

Classification: Internal — Technical

***Status: Final draft for stakeholder review meeting. Next revision is v1.0 post-meeting.***

*Supersedes: v0.1, v0.2, v0.3 (April 24, 2026)*

*Source: Real-Time Brand Decision System, Product Detailing & System Logic v1.0 (April 22, 2026), extended by stakeholder clarifications captured April 24–25, 2026*

# Executive Summary

The Real-Time Brand Decision System is a facilitator-operated, bilingual (Arabic and English) web-based ideation tool used by an agency principal during live meetings with their clients. In a single 50-minute session, the tool guides participants through a fixed canonical questionnaire, extracts a structured Brand DNA Profile and Pain Analysis, and generates rationale-bearing creative outputs for any non-empty subset of five brand-decision modules (Strategy Theme, Tone, Naming, Slogan, Tagline).

The technical design separates the system into two internal layers: a deterministic Orchestration Layer governing phase flow, rule-based pain tagging, module activation and suppression, sequencing, and intersection logic; and a Generation Layer of constrained LLM-backed components producing schema-bound, traceable creative content.

Arabic and English are treated as first-class reasoning languages with full quality parity. The specific Arabic register used in a given session (Modern Standard Arabic, Saudi dialect, or English) is derived from the Brand DNA Profile captured in Discovery, not configured globally.

This document covers Layer 1 of the product roadmap only. It represents the final draft before stakeholder review; the meeting following this draft will close remaining open questions and yield v1.0.

# Revision History

| **Version** |** Date** |** Summary of Change** |
|---|---|---|
| 0.1 | April 24, 2026 | Initial draft. Modelled the system as a client-facing SaaS with a free-text Business Objective feeding five decision modules. |
| 0.2 | April 24, 2026 | Product reframed as facilitator-operated in-meeting ideation tool with three-phase session. Introduced fixed canonical questionnaire, hybrid rules+LLM pain analysis, bilingual with mid-session language switching, PDF export, session persistence. |
| 0.3 | April 24, 2026 | Agency principal recognized as senior marketing content partner. Arabic elevated to first-class reasoning language at parity with English. Native-speaker review embedded into phase exits. Arabic variety flagged as open question. |
| 0.4 | April 25, 2026 | Final pre-meeting draft. Arabic register resolved as derived from Brand DNA (per-session, not global). Latency budget set (≤3 min per module, 50 min session). N-best sampling architecture flagged for later; 'client judges final output only' recorded as constraint. PDF export scope fully specified (all artifacts, pure text). Simultaneous reveal confirmed — no facilitator review gate. Questionnaire versioning confirmed. |

# 1. Document Purpose & Scope

This Technical Design Document (v0.4) is the final draft for stakeholder review. It supersedes v0.1 through v0.3 and responds to the product specification Real-Time Brand Decision System — Product Detailing & System Logic v1.0 (April 22, 2026), incorporating stakeholder clarifications captured April 24–25, 2026.

The product is a facilitator-operated, bilingual web-based ideation tool used by an agency principal during live meetings with clients. The tool guides a three-phase session — Discovery, Decision, and Generation — producing rationale-bearing creative outputs for any non-empty subset of five brand-decision modules.

The agency principal is a senior marketing expert and is treated throughout this document as a content partner to the engineering effort. Their expertise is what the system operationalizes; the engineering responsibility is to translate that expertise accurately into executable rules, prompts, and evaluation criteria.

This document covers Layer 1 of the product roadmap only. Layers 2 through 5 are explicitly out of scope (Section 12).

**Document intent: this is the final draft issued for stakeholder review. The meeting following this draft is expected to close remaining open questions in Section 3.3 and yield v1.0 of this document, after which implementation planning (API specification, data schema, prompt engineering plan) can proceed.**

# 2. Problem Restatement (Technical Framing)

Expressed in engineering terms, the Real-Time Brand Decision System is a session-oriented, single-operator web application coupling a deterministic decision orchestrator to a constrained generative content engine. It is not a client-facing SaaS. The client participating in the session does not authenticate and does not interact with the software directly; the client's input is captured through the facilitator, who operates the tool on shared display (typically a laptop mirrored to a meeting-room TV via HDMI).

### 2.1 The three phases of a session

| **Phase** |** Purpose** |** Primary Artifact Produced** |
|---|---|---|
| Discovery | Capture fragments of the client's brand DNA and identify their pain points through a fixed canonical questionnaire authored by the agency's senior marketing expert. Derive the appropriate Language Register for this session. | Brand DNA Profile + Pain Analysis + Language Register |
| Decision | Client selects which of the five modules to address in this session (any non-empty subset of Strategy Theme, Tone, Naming, Slogan, Tagline). | Decision Scope |
| Generation | For each selected module, generate rationale-bearing creative output conditioned on the Brand DNA Profile, Pain Analysis, Language Register, and any upstream module outputs already produced. | Module Outputs + Rationales |

> Figure 1 — Three-Phase Session Flow. Discovery → Decision → Generation, with component colour-coded by type: yellow = deterministic (rules/orchestration), pink = LLM-backed (traceable), white = user input. (Diagram exists in source .docx; not embedded in markdown.)
### 2.2 The two internal layers of the system

- **Orchestration Layer.** Rule-driven, deterministic subsystem. Governs phase transitions, questionnaire flow, rule-based pain tagging, Language Register derivation, module activation and suppression, module sequencing, and intersection logic. Identical inputs produce identical routing behavior in every execution.
- **Generation Layer.** Module-specific LLM-backed generators plus the pain-narrative generator. Schema-bound and traceable. Not bit-exact reproducible due to inherent LLM inference non-determinism, but every output carries a structured rationale and full audit record.

### 2.3 Bilingual reasoning as a first-class property

**The product operates in Arabic and English with full reasoning parity. Parity is stronger than UI translation; it is a quality commitment at the reasoning level.**

- Every reasoning component — LLM, prompts, rules engine, validators — operates on Arabic and English with equivalent quality.
- Creative output generated in Arabic is as idiomatic, register-appropriate, and culturally resonant as its English counterpart. Arabic is a generation language, not a translation target.
- Pain analysis works on answers in either language and produces narrative in the directed language.
- Intersection logic operates correctly across mixed-language upstream inputs and a directed downstream output language.
- PDF export honors per-object language with correct RTL rendering for Arabic content.

### 2.4 Language Register derivation

A distinctive design decision in v0.4: the specific Arabic register used for generation in a session is not configured by the operator. It is derived from the Brand DNA Profile. The Discovery phase produces a Language Register directive that flows into every downstream module's prompt.

Example derivations:

- Brand personality: formal. Target audience: Arab / pan-Gulf professionals → Modern Standard Arabic, culturally rich and register-appropriate.
- Brand personality: casual, youth-oriented. Target audience: Saudi consumers → Saudi dialect (informal).
- Brand personality: global or premium-international. Target audience: non-Arab or pan-global → English only.
- Brand personality: split audience (e.g., luxury Saudi with international positioning) → the Brand DNA Profile's resolution determines primary register; the open question of dual-output is flagged for later.

*This means Arabic register is answer-derived, not operator-configured. The agency expert's methodology embedded in the questionnaire and rule set is what determines the right linguistic choice for each session.*

### 2.5 What 'deterministic' means in this product

| **Property** |** Scope** |** Guarantee Level** |
|---|---|---|
| Routing Determinism | Questionnaire flow, rule-based pain tagging, Language Register derivation, module activation/suppression, sequencing, intersection rule application | Absolute — enforced in code |
| Output Traceability | Pain narrative and all five module outputs (LLM-generated content, in either language) | Enforced — every output carries a structured rationale and full audit record. Bit-exact reproducibility is not guaranteed. |

### 2.6 The product in one sentence

***A bilingual facilitator-operated web application that guides an in-meeting brand ideation session through a canonical questionnaire authored by a senior marketing expert, a deterministic decision-scope selector, a derived Language Register, and a constrained LLM-backed generation engine with full Arabic-English reasoning parity — producing exportable rationale-bearing outputs for a chosen subset of five brand modules within a 50-minute session budget.***

# 3. Assumptions & Open Questions

This section captures what has been confirmed, what is being assumed, and what remains open. Use of this section in the stakeholder meeting: walk Section 3.1 to confirm alignment; walk Section 3.2 to flag anything we're wrong about; walk Section 3.3 to close blocking questions.

- **[CONFIRMED]** Confirmed by stakeholder. Treated as fixed.
- **[ASSUMPTION]** Proceeding on this basis unless contradicted.
- **[OPEN QUESTION]** Blocks finalization of downstream components, or must be answered before specific phases.

### 3.1 Confirmed by stakeholder

**[CONFIRMED]** The tool is operated by a single facilitator at a time during a live meeting with a client. The client does not authenticate or interact with the software directly.

**[CONFIRMED]** The tool is a web application running in the facilitator's browser, typically mirrored to a meeting-room display (HDMI to TV). UI design is deferred but must be readable at meeting-room distance.

**[CONFIRMED]** The Brand DNA questionnaire is authored by the agency's senior marketing expert and is fixed across sessions. Content is not LLM-generated.

**[CONFIRMED]** Sessions are persistent: saved, resumable by the owning facilitator, and exportable to PDF.

**[CONFIRMED]** The tool is bilingual (Arabic and English). Mid-session language mixing is permitted at the per-content-object level. Arabic is a first-class reasoning language at parity with English.

**[CONFIRMED]** The specific Arabic register used for generation is derived from the Brand DNA Profile (A1). It is not a global configuration. Discovery produces a Language Register directive consumed by all downstream modules.

**[CONFIRMED]** Pain analysis is hybrid: deterministic rule-based tagging followed by LLM-elaborated structured narrative.

**[CONFIRMED]** The agency's senior marketing expert performs native-speaker review of Arabic outputs as part of the evaluation loop. Phase exits are gated on their signoff.

**[CONFIRMED]** Discovery budget: target 30 minutes or less (questionnaire + pain analysis surfaced). Per-module generation budget: up to 3 minutes acceptable, quality prioritized over speed. Total session budget: 50 minutes.

**[CONFIRMED]** PDF export includes all artifacts produced in the session (questionnaire answers, pain analysis, module outputs, rationales). Pure text, no graphical design, no agency branding.

**[CONFIRMED]** Output reveal: simultaneous to facilitator and client. No facilitator pre-review step. The system commits to its output. This places the quality burden on the evaluation loop and the content-safety filter.

**[CONFIRMED]** Questionnaire content is versioned. Each session is stamped with the QuestionnaireVersion used. Expert updates produce a new immutable version; previous sessions retain the exact content they were conducted against.

### 3.2 Working assumptions

**[ASSUMPTION]** Internet connectivity is available during the meeting. No offline mode in v1.

**[ASSUMPTION]** The facilitator authenticates with an account. Sessions belong to one facilitator and are not shared in v1.

**[ASSUMPTION]** v1 supports a single agency tenant. Multi-agency is v2.

**[ASSUMPTION]** Each session generates module outputs once per module (single-pass generation). Regeneration is v2 (product roadmap Layer 4).

**[ASSUMPTION]** PDF export is a structured text summary, not a designed presentation deck.

**[ASSUMPTION]** All LLM calls are logged with prompt hash, model version, language directive, parameters, and response. This is treated as a hard requirement regardless of further stakeholder input, because the product's 'rationally justified' claim cannot be defended without it.

### 3.3 Open Questions — Full Register

This section records every open question raised during the v0.1 → v0.4 working sessions. Questions are grouped by origin and tagged with gating information. The stakeholder should see the full list regardless of urgency — it is the map of what is still undecided across the whole project, not just what engineering needs this week.

Legend: GATE = phase or decision this question blocks. OWNER = who has the authority to answer. STATUS = current state of the question as of v0.4.

### Group A — Product-scope questions (from v0.1–v0.3)

These are questions raised directly out of reading the product specification and its subsequent clarifications.

**[A1 — RESOLVED]** Arabic variety for creative output. Resolution: Arabic register is derived per-session from the Brand DNA Profile, not configured globally. The Discovery phase produces a Language Register directive. See Section 2.4 and 5.7. Detailed resolver rules remain an expert deliverable folded into A4/A5.

**[A2 — OPEN]** Questionnaire detailed structure. Number of questions, thematic grouping, conditional branching logic, slider-based vs discrete answer types. GATE: Phase 1 entry. OWNER: Agency expert. STATUS: Confirmed 30-minute budget; detailed structure deferred to expert deliverable.

**[A3 — RESOLVED]** Questionnaire presentation model. Resolution: HDMI-to-TV deployment; both facilitator and client view the same display. UI does not need to privilege one viewer over the other but must be readable at meeting-room distance.

**[A4 — OPEN]** Pain taxonomy. The fixed set of pain categories the Rules Engine tags into and the Narrative Generator reasons over. GATE: Phase 1 entry. OWNER: Agency expert. STATUS: Flagged by stakeholder as deferred to expert delivery.

**[A5 — OPEN]** Rule set. Declarative mapping from questionnaire answers to pain-taxonomy categories. Depends on A2 (questionnaire structure) and A4 (pain taxonomy). GATE: Phase 1 entry. OWNER: Agency expert. STATUS: Flagged by stakeholder as deferred to expert delivery.

**[A6 — RESOLVED]** Latency expectations. Resolution: up to 3 minutes per module acceptable; quality over speed. Total session budget 50 minutes. See NFR latency row.

**[A7 — RESOLVED]** PDF export content and format. Resolution: pure text PDF, no graphical design, no agency branding, includes all session artifacts (questionnaire answers, pain analysis, module outputs, rationales).

**[A8 — OPEN]** Confidentiality classification of client data captured in Discovery. Retention policy, access policy, data-processing agreements. GATE: Phase 5/6. OWNER: Agency business side. STATUS: Stakeholder flagged as out of current concern; deferred. Engineering proceeds with defensive defaults (encryption in transit and at rest, restricted access) until classification is formalized.

**[A9 — RESOLVED]** Facilitator review step. Resolution: no pre-review gate. Outputs reveal simultaneously to facilitator and client. Quality burden shifts to evaluation and content-safety filtering. This is a deliberate product stance, not a simplification.

**[A10 — OPEN (NEW)]** N-best sampling architecture inside each Module Runner. Three options: (A) single-shot generation; (B) hidden N-best with LLM judge selecting the winner; (C) transparent N-best with client selecting among alternatives. GATE: Phase 2 entry. OWNER: Facilitator/agency jointly — this is a product-positioning decision. STATUS: Flagged for deliberation with agency expert. Constraint recorded: client judges final output only, never internal generation candidates.

### Group B — Project-shape questions (surfaced during v0.3 working session)

These are questions the technical lead surfaced while writing the TDD. None are strictly gating, but several influence resourcing, commercial framing, and long-term architecture. The stakeholder should see them because they touch business-side decisions that typically sit outside the technical lead's authority.

**[B1 — OPEN]** LLM provider data-residency constraints. Whether Saudi data-residency requirements, or any industry-specific compliance obligations the agency's clients bring (banking, government, healthcare), limit the LLM provider pool. GATE: Phase 2 (model selection). OWNER: Agency business side. STATUS: Flagged in v0.3. Not yet surfaced with the stakeholder.

**[B2 — OPEN]** Availability of historical agency work as a golden evaluation set. Whether the agency can share 5–10 examples of past brand briefs and their resulting outputs (or what they would consider ideal outputs), to build the evaluation harness used at every phase exit. STATUS: Highly valuable. Strengthens evaluation beyond synthetic test cases.

**[B3 — OPEN]** Knowledge-engineering capacity. Whether the technical lead is alone on translating expert methodology into rules and prompts, or whether a collaborator (junior engineer, prompt engineer) is available. STATUS: Affects timeline. Needed before Phase 1 starts.

**[B4 — OPEN]** Front-end UI ownership. Who designs and builds the web client. STATUS: Explicitly out of scope for this technical lead per original briefing. But if no other owner is named, UI quality becomes a risk — a bare-bones interface undercuts the 'agency uses sophisticated AI' pitch in front of paying clients.

**[B5 — OPEN]** Commercial trajectory. Whether the tool is for the agency's internal use only, will eventually be licensed to other agencies, or will be offered directly to the agency's clients. STATUS: Affects multi-tenancy design decisions. Assumed single-tenant for v1 (C3); forward-looking decisions should be aware.

**[B6 — OPEN]** IP ownership of agency-authored content (questionnaire, pain taxonomy, rule set, register resolver rules, prompt templates). Whether the agency owns these, the expert owns them personally, or the engineering team co-owns them. STATUS: Matters on personnel changes and any future commercialization.

**[B7 — OPEN]** Future facilitator population. Whether the expert is the sole facilitator or other agency staff will be trained to use the tool. STATUS: Affects UX — whether the interface can be terse and expert-oriented or must guide less-experienced operators.

**[B8 — OPEN]** Quality bar for v1. Whether v1 is used in real paying-client engagements or serves as a demo/pitch tool. STATUS: Materially affects what 'done' means for every phase.

**[B9 — OPEN]** Success criteria. How project success is measured — increased agency win rate, compressed delivery time, client satisfaction, some combination. STATUS: Without measurable criteria, the team cannot know whether the right thing was built.

**[B10 — OPEN]** Compliance framework binding client data. Saudi PDPL, GDPR (for international clients), industry-specific regulations. STATUS: Overlaps with A8. Defensive defaults in place until formalized.

**[B11 — OPEN]** LLM cost budget. Target per-session and per-month cost envelopes. Arabic content tokenizes less efficiently than English on most models, materially affecting per-session cost. STATUS: No target set; unit economics unknown.

**[B12 — OPEN]** Expert post-launch iteration capacity. How much of the agency expert's time is available after v1 launch to review prompt changes, refine rules, update the questionnaire. STATUS: Affects the product's rate of improvement over its life.

### Group C — Working assumptions (proceeding unless contradicted)

These are items we proceeded on without explicit confirmation at the time they were raised. Several have since been confirmed by the stakeholder; those are marked.

**[C1 — CONFIRMED]** Internet connectivity available during every meeting. No offline mode in v1.

**[C2 — CONFIRMED]** Facilitator has an authenticated account. Sessions per-facilitator, not shared.

**[C3 — CONFIRMED]** Single agency tenant for v1. Multi-agency is v2.

**[C4 — CLARIFIED, BECAME A10]** Parallel multi-output per module. Originally assumed to mean the product-spec-defined output shape; clarified by stakeholder to mean N-best sampling (generate the same module twice in parallel to pick the best). Absorbed into open question A10.

**[C5 — CONFIRMED]** PDF export is a structured text summary, not a designed presentation deck.

**[C6 — CONFIRMED]** Questionnaire is versioned. Each session stamped with QuestionnaireVersion used. Updates produce new immutable versions.

**[C7 — CONFIRMED]** All LLM calls are logged with prompt hash, model version, language directive, parameters, response. Non-negotiable requirement underpinning the 'rationally justified' claim.

### 3.4 Summary — What the stakeholder meeting needs to close

Not every open question above needs to close in the meeting. Here is the triage for the meeting itself:

- **Must close (or commit to a delivery date):** A2, A4, A5 (content deliverables from the agency expert, required for Phase 1). A10 (architectural decision, required for Phase 2).
- **Should be routed to the right owner:** A8, B1, B5, B6, B10, B11 (business or commercial side, not technical).
- **Should be answered by the stakeholder if they can:** B3, B4, B7, B8, B9 (project-shape questions the stakeholder has context to answer).
- **Can remain open without blocking work:** B2, B12 (valuable but do not gate any specific phase).

# 4. System Architecture (Conceptual)

Component-level design, implementation-agnostic. Technology recommendations in Section 6.

### 4.1 Component inventory

| **Component** |** Responsibility** |
|---|---|
| Web Client | Browser UI for the facilitator, typically displayed on a meeting-room TV via HDMI. Renders questionnaire, captures answers, triggers phase transitions, displays outputs, triggers export. Supports Arabic RTL and English LTR rendering. Detailed UI design out of scope for this TDD. |
| API Gateway | Accepts web-client requests, authenticates the facilitator, routes to the Session Service. |
| Session Service | Owns session lifecycle across Discovery, Decision, Generation phases. Persists state after every meaningful action for resume support. |
| Questionnaire Service | Serves the canonical questionnaire (versioned). Captures answers (each tagged with language). Validates completeness before the session advances. |
| Pain Analysis Engine | Two-stage. (1) Rules Engine deterministically tags answers to pain categories from a fixed taxonomy. (2) Narrative Generator produces structured pain narrative via LLM call. |
| Language Register Resolver | Derives the session's Language Register directive from the Brand DNA Profile. Deterministic function. Output is consumed by downstream Module Runners. |
| Orchestration Engine | Pure-logic. Converts the Decision Scope into an Execution Plan (ordered module list + applicable intersection rules). |
| Module Runners (×5) | One per logic module (Strategy Theme, Tone, Naming, Slogan, Tagline). Each wraps LLM call(s) with module-specific prompts, priority constraints, language and register directives, and output schema validation. |
| LLM Provider Abstraction | Single chokepoint for all LLM access. Enforces model pinning, structured output, audit logging, retries, language parameterization. |
| Persistence Layer | Stores sessions, answers, pain analyses, module outputs, rationales, and the full LLM audit trail. |
| Export Service | Produces PDF from a completed or partial session, honoring per-object language and correct RTL/LTR rendering. Pure text content, no graphical design. |
| Observability Layer | Structured logs, traces, metrics for every session action and every LLM call. |

> Figure 2 — Component Architecture. Orchestration components (yellow) contain no LLM calls. Generation components (pink) route through the single LLM Provider Abstraction. Persistence and audit trail are continuous across the whole system. (Diagram exists in source .docx; not embedded in markdown.)
### 4.2 Data flow — the life of a session

- Facilitator authenticates, creates a new session. Session stamped with current QuestionnaireVersion.
- Questionnaire Service serves the canonical questionnaire. Facilitator captures client answers; each answer is tagged with the language it was given in.
- On questionnaire completion, the Pain Analysis Engine runs: Rules Engine tags pains deterministically; Narrative Generator produces a structured pain narrative via LLM.
- Language Register Resolver processes the completed Brand DNA Profile and emits a Language Register directive for the session.
- Facilitator presents the Brand DNA Profile and Pain Analysis to the client.
- Client selects the Decision Scope — any non-empty subset of five modules.
- Orchestration Engine consumes the Decision Scope and produces an Execution Plan (pure function, no I/O).
- Session Service iterates the Execution Plan. Each Module Runner receives the Brand DNA Profile, Pain Analysis, Language Register directive, upstream module outputs, and target output language. It invokes the LLM Provider Abstraction under structured-output constraints.
- Each output is persisted with its rationale, language tag, and audit record. Output is revealed to both facilitator and client simultaneously (no review gate).
- When all modules complete, the session is marked delivered. PDF export can be triggered at any time — on a completed or partial session.

### 4.3 Architectural boundaries

- **Orchestration never calls the LLM.** Orchestration Engine, Rules Engine, and Language Register Resolver are pure-logic. LLM calls are confined to the Narrative Generator and Module Runners, all routed through the LLM Provider Abstraction.
- **Modules never call each other directly.** Modules communicate only via the Session Service, which injects upstream outputs and context into downstream prompts.
- **The LLM Provider Abstraction is the single chokepoint.** No direct calls to any model provider anywhere else in the system.
- **Language is data, not a mode.** Every persisted content object carries a language tag. There is no global session language. Prompts declare each input's language and direct the output's language explicitly.
- **Register is derived, not configured.** The Language Register for generation is computed from the Brand DNA Profile by a deterministic resolver. Operators do not override it; the methodology of the questionnaire is what shapes the register choice.

# 5. The Logic Model

Reasoning rules the system implements. Derived from the source product specification, extended by v0.2–v0.4 clarifications. The most stable part of this document.

## 5.1 Governing Axioms

- Nothing exists until scope is declared. With no Decision Scope, no Generation phase executes.
- Every module is a closed world. A module knows only its own priorities and explicit inputs provided by the Session Service.
- Suppression is absolute. A non-selected module contributes zero to outputs, prompts, and intersection logic.
- Every creative output carries its rationale. Pain narrative and module outputs are always a triple: output, rationale, priority factors served.
- Intersections are explicit, not emergent. Named pre-defined conditioning rules govern module interaction.
- Discovery precedes Decision precedes Generation. Phases execute in fixed order.
- Language parity is invariant. Arabic and English are treated as equal reasoning languages throughout the system.
- Language register is derived from Brand DNA. The register directive for generation is produced by a deterministic resolver over the Brand DNA Profile, not set by configuration or operator choice.
- The client judges final outputs only. Internal generation candidates and architectural details are not exposed for client judgement. (Constraint recorded pending A10 resolution of N-best architecture.)

## 5.2 Phase Dependency

| **Phase** |** Completion Criterion** |** Output Handed Forward** |
|---|---|---|
| Discovery | All required questionnaire questions answered; Rules Engine has produced pain-tag set; Narrative Generator has produced structured pain narrative; Language Register Resolver has produced register directive. | Brand DNA Profile + Pain Analysis + Language Register |
| Decision | Client has selected a non-empty Decision Scope. | Ordered Execution Plan |
| Generation | Every module in the Execution Plan has produced a valid, schema-compliant, rationale-bearing output in the directed language and register. | Final output set (ready for export) |

## 5.3 Module Dependency Graph

Among active modules, execution order is strict: abstract before concrete, governance before expression.

**Strategy Theme → Tone → Naming → Slogan → Tagline**

Modules not in scope are skipped. Active modules always receive the Brand DNA Profile, Pain Analysis, and Language Register directive as context, regardless of what other modules are active.

> Figure 3 — Module Dependency Graph. Foundational modules condition governance modules; both condition expressive modules. Only the modules included in the active Decision Scope are run. (Diagram exists in source .docx; not embedded in markdown.)
## 5.4 Suppression Rule

For Decision Scope S (non-empty subset of five modules), the active set is exactly S. For every module m not in S: no output, no prompt reference, no priority consultation, no intersection participation.

Discovery-phase outputs (Brand DNA Profile, Pain Analysis, Language Register) are not subject to the Suppression Rule — they are context, always available to active modules.

## 5.5 Intersection Logic (unified rule)

All seven intersection rules reduce to one shape: the downstream module's output is conditioned on the upstream module's output.

| **Pair** |** Upstream → Downstream** |** Effect** |
|---|---|---|
| Strategy + Tone | Strategy → Tone | Voice articulated consistently with the strategic statement. |
| Strategy + Naming | Strategy → Naming | Only names supporting the strategic positioning are presented. |
| Strategy + Slogan | Strategy → Slogan | Slogans are expressions of the strategic statement. |
| Strategy + Tagline | Strategy → Tagline | Only taglines serving the strategy are presented. |
| Tone + Naming | Tone → Naming | Only names tonally consistent with the voice are presented. |
| Tone + Slogan | Tone → Slogan | Slogans are written within the defined voice's constraints. |
| Tone + Tagline | Tone → Tagline | Taglines are written within the defined voice's constraints. |

## 5.6 Language Handling Rules

- Every persisted content object carries a non-null language tag recording the language it was authored in.
- There is no global session language. There is a per-module output-language directive selected by the facilitator at generation time, and a derived Language Register directive that accompanies it.
- When a module runs, its inputs may be in multiple languages. The prompt declares each input's language explicitly; the model is directed to produce output in the specified output language and register.
- Rules in the pain-tagging Rules Engine operate on structural tags (selected option, slider value, numeric range), not on raw free-text. This keeps the Rules Engine language-neutral.
- Where rules must operate on free-text, matching is done against a normalized representation with separate match patterns maintained per language.
- Arabic output quality is evaluated on the same terms as English output quality. Native-speaker review by the agency expert is the authoritative Arabic-quality judgement.

## 5.7 Language Register Derivation Rule

The Language Register directive is derived by the Language Register Resolver from the Brand DNA Profile at the end of Discovery. The resolver is a deterministic function — identical Brand DNA Profiles produce identical register directives.

The directive has the general shape:

- Primary language: Arabic | English
- Arabic variety (if applicable): Modern Standard Arabic | Saudi dialect | (to be specified by agency expert for edge cases)
- Register: formal | semi-formal | casual
- Cultural anchors: (tags derived from audience and personality fields)

The precise resolver rules — which Brand DNA fields drive which directive values — are part of the expert-authored content dependencies (A1 detail, A4, A5). The system architecture supports any resolver shape; the specific rules are agency deliverables.

> Figure 4 — Language & Register Flow. Mixed-language answers feed the deterministic Register Resolver, which produces a single per-session directive. The directive flows into every downstream module prompt. Three example derivations illustrate how brand personality and audience shape the output. (Diagram exists in source .docx; not embedded in markdown.)
## 5.8 The Combination Space

31 valid Decision Scope combinations (non-empty subsets of five modules). Test coverage must be exhaustive. Discovery is constant across all 31.

# 6. Technology Stack & Justification

Recommendations tied to requirements. Subject to stakeholder review. Not locked until Section 3.3 open questions (especially B1) are resolved.

| **Layer** |** Proposed Choice** |** Justification** |
|---|---|---|
| API framework | Python with an async web framework (FastAPI-class) | Typed async APIs, strong LLM-tooling ecosystem, native integration with schema-validation libraries. |
| Schema & validation | Pydantic-class typed models with per-field language tagging | Structured outputs at the Python boundary. Every content object has a language field; validation enforces it. |
| Orchestration engine | Hand-rolled state logic over an enum-driven module graph | Fixed dependency order, seven intersection pairs, 31 combinations do not warrant a rule-engine framework. Hand-rolled is more auditable and easier to test exhaustively. |
| Rules engine (pain tagging) + Register resolver | Declarative rule sets in YAML or a small DSL, evaluated by a Python rules runner | Keeps expert-authored content versioned independently of code. Same engine pattern serves both pain tagging and register derivation. |
| LLM access | Single provider abstraction over a pinned frontier model with validated Arabic creative-generation quality at parity with English | Model selection gated on measured Arabic performance. Migration requires full bilingual regression. Subject to B1 data-residency resolution. |
| Structured output | Provider-native structured output mode | Prevents free-text JSON parsing. Schema enforced on the generation side. |
| Persistence | Relational store (Postgres-class) with JSON columns for flexible content objects | Strong consistency for session state. JSON for variable-shape answers and outputs. SQL auditing. |
| Session cache | In-memory cache (Redis-class) | Sub-millisecond reads. Optional given the 3-minute generation budget, but useful for interactive answer capture. |
| Multi-pass generation capacity | Supported by latency budget | 3-minute per-module budget enables multi-pass techniques (N-best sampling, self-critique loops) pending A10 resolution. Stack does not foreclose any of A/B/C. |
| PDF export | Server-side templated HTML-to-PDF with verified RTL support | RTL-aware from day one. Pure text templates, no design assets required. |
| Internationalization | Explicit per-object language tags plus UI translation catalogs for static labels | Matches the 'language is data' boundary. No runtime language inference. |
| Observability | Structured logs + traces + metrics via OpenTelemetry-compatible pipeline | Every session action and LLM call traceable, both languages. |

*Explicitly deferred: specific cloud provider, specific LLM provider (subject to B1), specific monitoring vendor, specific CI/CD pipeline, specific PDF template content.*

# 7. High-Level Data Model

Conceptual entities. Field-level schemas belong in a separate Data Schema document.

| **Entity** |** Purpose** |** Key Relationships** |
|---|---|---|
| Facilitator | Authenticated agency operator. | Has many Sessions. |
| Session | Top-level container. Phase state, timestamps, QuestionnaireVersion used. | Belongs to one Facilitator. Has one QuestionnaireInstance, one PainAnalysis, one LanguageRegister, one DecisionScope, one ExecutionPlan, many ModuleOutputs, many ExportArtifacts. |
| QuestionnaireVersion | Immutable expert-authored version of questionnaire content. | Referenced by many QuestionnaireInstances. |
| QuestionnaireInstance | Captured answers for one session, stamped with QuestionnaireVersion. | Belongs to one Session. Has many Answers. |
| Answer | Single captured response, tagged with language. | Belongs to one QuestionnaireInstance. |
| PainAnalysis | Combined Rules-Engine tags and LLM-elaborated narrative, with language tag. | Belongs to one Session. Has one Rationale. Has one LLMCallRecord. |
| PainTaxonomy | Fixed set of pain categories authored by the agency expert. | Referenced by Rules and PainAnalyses. |
| Rule | Declarative mapping from answer patterns to pain categories. | Belongs to a Rule Set version. References PainTaxonomy entries. |
| LanguageRegister | Derived directive for generation: primary language, variety/register, cultural anchors. | Belongs to one Session. Referenced by every ModuleOutput produced in that session. |
| DecisionScope | Set of selected module identifiers. | Belongs to one Session. |
| ExecutionPlan | Ordered list of module runs and applicable intersection rules. | Belongs to one Session. |
| ModuleOutput | One module's generated result, tagged with language. | Belongs to one Session. Has one Rationale. Has one or more LLMCallRecords. References upstream ModuleOutputs. References LanguageRegister. |
| Rationale | Structured justification citing priority factors addressed and upstream inputs. | Belongs to one ModuleOutput or one PainAnalysis. |
| LLMCallRecord | Full audit record: prompt hash, model version, language directive, register directive, parameters, response, latency. | Belongs to one ModuleOutput or one PainAnalysis. |
| ExportArtifact | Generated PDF with timestamp and manifest of content objects included. | Belongs to one Session. |

Persistence-layer invariants:

- Every ModuleOutput links to exactly one Rationale and at least one LLMCallRecord.
- Every PainAnalysis links to exactly one Rationale and one LLMCallRecord.
- Every Answer and every generated output carries a non-null language tag.
- Every Session references exactly one QuestionnaireVersion, fixed at creation.
- Every ModuleOutput in a Session references that Session's LanguageRegister.
- Every Rule references a PainTaxonomy entry; orphan rules are rejected.

# 8. Conceptual API Contract

Operation, input, output. Endpoint specification belongs in a separate API Spec document.

| **Operation** |** Input** |** Output** |
|---|---|---|
| Create Session | Facilitator credentials | Session identifier, initial state (phase: Discovery), active QuestionnaireVersion |
| Fetch Questionnaire | Session identifier | Full questionnaire content in both supported languages |
| Submit Answer | Session identifier, question identifier, answer content, language tag | Acknowledgement, updated session state |
| Complete Discovery | Session identifier | PainAnalysis (tagged pains + narrative + rationale) + derived LanguageRegister |
| Submit Decision Scope | Session identifier, subset of module identifiers, output-language directive per module | Execution Plan |
| Run Generation | Session identifier | Module outputs in dependency order, each with rationale, language tag, and register metadata |
| Fetch Session | Session identifier | Full session state and all produced artifacts |
| List Sessions | Facilitator credentials, optional filters | Facilitator's sessions with summary metadata |
| Resume Session | Session identifier | Session state and next actionable phase |
| Export PDF | Session identifier, export options | PDF artifact containing all session content, text-only |
| Fetch Audit Trail | Session identifier (authorized) | Ordered list of LLMCallRecords |

Excluded from v1: regenerate module output, edit module output, share session between facilitators, real-time multi-user editing.

# 9. Non-Functional Requirements

| **Category** |** Requirement** |** Rationale** |
|---|---|---|
| Correctness | Every one of the 31 Decision Scope combinations produces a well-formed output set in expected order with correct suppression. Rules Engine and Language Register Resolver are deterministic for identical inputs. | Foundational product behavior. |
| Routing determinism | Identical inputs produce identical phase transitions, pain tags, register directives, and Execution Plans. | Orchestration guarantee. |
| Output traceability | Every generated output has a linked Rationale and at least one LLMCallRecord. | Defends the 'rationally justified' product claim. |
| Language parity — continuous | Arabic output quality measured as equivalent to English output quality at every phase exit and continuously in production. Every prompt change, model update, rule change regression-tested in both languages. Parity certified by agency-expert native-speaker review. | Highest-priority NFR. Core market (Saudi) depends on it. |
| Language integrity | Every persisted object carries a non-null language tag. No runtime language inference. | Invariant. |
| Register fidelity | Every generated output carries and honors the session's LanguageRegister directive. Register violations detected in evaluation. | Answer-derived register is a product differentiator and must hold in production. |
| Latency (live-meeting context) | Interactive answer capture under 200ms. PainAnalysis under 60 seconds. Per-module generation up to 3 minutes acceptable. Total session within 50-minute budget. | Confirmed stakeholder budget. Favors quality over speed. |
| Session persistence | State persisted after every meaningful action. Resume from any phase without loss. | Sessions outlive the meeting. |
| Concurrency | Facilitator can hold multiple sessions in any state without cross-session interference. | Agency teams juggle multiple client engagements. |
| Auditability | All LLM calls logged with prompt hash, model version, language directive, register directive, parameters, response, latency. Retention per A8 resolution. | Compliance and product-credibility defense. |
| Security | Facilitator authentication required. Client data encrypted in transit and at rest. Access restricted to owning facilitator and agency administrators. Defensive defaults pending A8. | Confidentiality. |
| Content safety | Generated content screened for disallowed categories in both languages before being revealed. | No pre-review gate — quality burden is on the system. Content safety filter becomes a non-negotiable checkpoint. |
| Observability | Structured logs and traces for every session action and LLM call. | Debugging and audit. |
| Operational dependency | Internet connectivity required; tool surfaces connectivity status clearly. | No offline mode in v1. |
| UI readability | Text and UI elements readable at meeting-room TV distance (typical 2–5 metres). | HDMI-to-TV deployment pattern. |

# 10. Risks & Mitigations

| **Risk** |** Impact** |** Mitigation** |
|---|---|---|
| Arabic creative output below the expert's quality bar. | Core market degraded. Facilitator credibility damaged. Product loses primary differentiation in Saudi Arabia. | Arabic parity is the top NFR. Model selection gated on Arabic evaluation. Native-speaker review by the agency expert required at every phase exit. Regression set covers both languages. No phase exits on English-only evidence. |
| Register derivation produces the wrong register for a session (e.g., MSA when Saudi dialect would resonate). | Outputs feel off to the audience. The product's differentiator (answer-derived register) is the thing that fails. | Register Resolver rules are expert-authored and versioned. Evaluation includes register-fit review across representative brand-personality combinations. Register metadata logged with every output for post-hoc audit. |
| Translating expert methodology into declarative rules introduces distortion. | Pain tagging and register derivation feel 'algorithmic' or miss nuance the expert would catch in person. | Structured knowledge-engineering sessions between technical lead and expert during Phase 1. Every rule reviewed and signed off by the expert. Rule firings logged in production for ongoing expert audit. |
| Simultaneous-reveal stance produces an embarrassing output in front of the client. | Major reputational incident in a single meeting. No safety valve — by design. | Rigorous evaluation gates. Content-safety filter between generation and display is non-negotiable. High-quality rule set from the expert. Agency expert signs off before any phase exit. The design consciously trades a safety net for product coherence; mitigation lies in the quality floor. |
| Latency spikes during generation undermine facilitator's composure. | Client perceives the tool as uncertain. Agency loses presence. | 3-minute per-module budget is generous. Clear 'working' UI states. Pre-warm caches. Observability surfaces slow calls immediately. |
| Network failure mid-meeting. | Session cannot continue. Facilitator falls back to manual methods. | Client-side caching of in-progress state. Graceful degradation messaging. Documented fallback protocol for facilitators. Full offline mode is v2. |
| Determinism claim meets LLM non-determinism. | Client or competitor reruns same inputs, gets different outputs. | Formal separation of Routing Determinism (absolute) from Output Traceability (rationale-backed). Product messaging aligned. |
| Mid-session language mixing produces inconsistent outputs. | Module outputs reference upstream content awkwardly across languages. | Language as first-class data per object. Prompts declare each input's language. Output language explicitly directed. Multi-language session evaluation in Phase 4. |
| PDF export mishandles RTL layout or mixed-language pages. | Arabic exports are unusable or embarrassing. | RTL-aware pipeline from day one. Bilingual test artifacts in Phase 5. Expert review of sample exports. |
| Scope creep toward Layers 2 through 5. | v1 timeline slips. | Section 12 is the contract. Any Layer 2+ request triggers formal change control. |
| Model provider deprecates the pinned model version. | Silent behavior change in both languages. | LLM Provider Abstraction centralizes the pin. Migration requires full bilingual regression including expert signoff. |
| Rules or register resolver drift behind evolving expert methodology. | Analysis becomes stale versus current best practice. | Rule Sets and Resolver Rules versioned. Periodic review cadence with expert. Deprecations handled without breaking session history. |
| A10 (N-best architecture) remains unresolved deep into Phase 2. | Module Runners cannot be finalized; phase blocked. | Open question flagged before Phase 2. Stack and latency budget already support any of A/B/C resolutions — the decision is product-positioning, not architectural capacity. |

# 11. Phased Delivery Plan

Technical-dependency order. No calendar dates. Every phase exit from Phase 1 onward requires Arabic–English parity demonstrated to the agency expert.

| **Phase** |** Goal** |** Entry Criterion** |** Exit Criterion** |
|---|---|---|---|
| Phase 0 — Foundations | Domain model; Session Service skeleton; Orchestration Engine with mocked module outputs; hard-coded questionnaire fixture; language-tag invariants enforced. | TDD v1.0 signed off. | All 31 Decision Scope combinations produce correct Execution Plans. Unit tests cover 31/31. Language-tag invariants enforced end to end. |
| Phase 1 — Discovery end-to-end | Questionnaire Service; Rules Engine with expert-authored rules and pain taxonomy; Narrative Generator; Language Register Resolver with expert-authored resolution rules. | Phase 0 exit met. Questionnaire, pain taxonomy, rule set, and register resolver rules delivered by agency expert. | Discovery produces valid PainAnalyses and LanguageRegister directives on a representative test set in both languages. Expert signs off on quality parity. |
| Phase 2 — First Generation module | Strategy Theme module: LLM output with rationale, schema validation, audit logging, bilingual support, register-aware. A10 (N-best architecture) resolved. | Phase 1 exit met. A10 resolved. | Strategy Theme passes evaluation set in both languages. Expert signs off on Arabic parity and register fidelity. |
| Phase 3 — Remaining four modules | Tone, Naming, Slogan, Tagline implemented. | Phase 2 exit met. | All five modules pass single-scope evaluation sets in both languages. Expert signs off per module on Arabic parity and register fidelity. |
| Phase 4 — Intersection logic and multi-module sessions | Upstream/downstream conditioning across all seven intersection pairs; multi-language session handling. | Phase 3 exit met. | Multi-module sessions produce coherent outputs. Multi-language sessions pass evaluation. Expert signs off on coherence. |
| Phase 5 — Persistence, resume, export | Saved/resumable sessions; PDF export supporting both languages and mixed-language sessions with correct RTL. | Phase 4 exit met. | Resume works across all phase states. Expert reviews and signs off on PDF exports in both languages. |
| Phase 6 — Hardening | Observability, audit, security, content safety, latency budget adherence. | Phase 5 exit met. | All Section 9 NFRs met. Load testing confirms 50-minute session budget achievable at target concurrency. Audit trail complete. |
| Phase 7 — v1 Release Readiness | Final integration, stakeholder acceptance, facilitator training materials. | Phase 6 exit met. | Stakeholder signoff on a full demonstration session covering representative scope combinations in both languages. |

# 12. Out of Scope (v1)

The following are explicitly out of scope for v1 and this TDD.

- Layer 2 — Audience Intelligence.
- Layer 3 — Competitive Context.
- Layer 4 — Output Refinement (in-session regenerate/edit of module outputs).
- Layer 5 — Decision Capture beyond the v1 PDF summary.
- Branded presentation deck export (PowerPoint-style) and any graphical design elements in export.
- Multi-user collaborative sessions (sessions are single-facilitator).
- Multi-agency (multi-tenant) deployment.
- Offline operation. Internet connectivity required in the meeting.
- Mobile-native or tablet-native clients. Web app only for v1.
- Real-time facilitator console features beyond the core session flow.
- Third-party integrations (CRM, project management, brand asset systems).
- Analytics dashboards aggregating across sessions or facilitators.
- Fine-tuning of any model. v1 uses a pinned stock model.
- On-premise or self-hosted deployment.
- In-app content authoring tools for the expert to edit questionnaire, rules, or resolver rules inside the app. v1 treats content updates as deployment events.
- Languages beyond Arabic and English.
- Facilitator pre-review gate for generated outputs (confirmed out by A9).

# 13. Appendix

## Appendix A — Glossary

| **Term** |** Definition** |
|---|---|
| Facilitator | Authenticated agency operator running a session in a live meeting. Sole human user of the tool. |
| Agency Expert | Senior marketing principal who authors the questionnaire, pain taxonomy, rule set, and register resolver rules, and performs native-speaker review of Arabic outputs. |
| Session | One meeting's state, spanning Discovery, Decision, Generation phases. |
| Discovery Phase | First phase. Captures questionnaire answers, produces Brand DNA Profile, Pain Analysis, and Language Register directive. |
| Brand DNA Profile | Structured representation of the client's brand from the canonical questionnaire. |
| Pain Analysis | Combined output of rule-based pain tagging and LLM-elaborated pain narrative. |
| Language Register | A per-session directive derived from the Brand DNA Profile: primary language, Arabic variety if applicable, register level, cultural anchors. Consumed by all Generation-phase modules. |
| Language Register Resolver | Deterministic component that computes the Language Register from the Brand DNA Profile. |
| Decision Phase | Phase where the client selects the Decision Scope. |
| Decision Scope | Non-empty subset of the five modules selected for generation. |
| Generation Phase | Phase where selected modules produce outputs. |
| Orchestration Engine | Rule-driven subsystem producing Execution Plans. No LLM calls. |
| Rules Engine | Deterministic component mapping questionnaire answers to pain-taxonomy tags. No LLM calls. |
| Narrative Generator | LLM-backed component producing structured pain narrative from rule-tagged pains. |
| Module Runner | Per-module component wrapping LLM call(s) with prompt, constraints, schema validation, language and register directives. |
| LLM Provider Abstraction | Single internal interface for all LLM access. |
| Execution Plan | Ordered list of module runs produced by the Orchestration Engine. |
| Rationale | Structured justification on every generated artifact citing priority factors and upstream inputs. |
| LLMCallRecord | Audit record of a single LLM invocation. |
| Routing Determinism | Absolute property: identical inputs yield identical orchestration behavior. |
| Output Traceability | Property that every generated output is explainable via rationale and audit record. |
| Language Parity | Property that Arabic and English are treated as equal reasoning languages throughout the system. |
| N-Best Sampling | Technique of generating multiple candidates in parallel for one module. Architecture open (A10). |
| QuestionnaireVersion | Immutable versioned instance of canonical questionnaire content. |
| Pain Taxonomy | Fixed set of pain categories authored by the agency expert. |
| Rule Set | Versioned set of declarative rules mapping answers to pain-taxonomy categories. |
| Combination Space | The 31 valid non-empty subsets of the five modules. |

## Appendix B — Stakeholder Meeting Guide

Recommended structure for the stakeholder review meeting following this draft.

**Total: 60 minutes. This document is the agenda.**

| **Time** |** Section** |** Purpose** |
|---|---|---|
| 0–5 min | Revision History + Executive Summary | Confirm stakeholder and expert see the same product we designed for. |
| 5–15 min | Section 2 — Problem Restatement | Confirm the three-phase framing, bilingual parity, Arabic register derivation. This is where misunderstanding would cost most; linger here. |
| 15–30 min | Section 3.3 — Open Questions | Walk every open question. Close what can be closed. Schedule delivery dates for content items (A2, A4, A5). Assign A10 to the next working session. Route A8 and B1 to the agency business side. |
| 30–40 min | Section 5 — Logic Model | Demonstrate the axioms and intersection logic. This is where the expert confirms the product thinks the way their methodology thinks. |
| 40–50 min | Section 11 — Phased Delivery | Confirm the phase ordering is acceptable. Identify which phases depend on which expert deliverables. Agree on cadence of expert review sessions. |
| 50–58 min | Section 12 — Out of Scope | Read aloud. Explicit agreement. This is the single strongest tool for preventing scope creep at month three. |
| 58–60 min | Signoff plan | Identify what needs to happen for v1.0 of this document to be signed off. |

## Appendix C — Reference to Source Documents

Real-Time Brand Decision System — Product Detailing & System Logic Document, v1.0, April 22, 2026.

Stakeholder clarifications captured April 24–25, 2026, covering: facilitator-operated tool model; HDMI-to-TV deployment pattern; canonical questionnaire authored by agency senior marketing expert; sessions saved, resumable, exportable; bilingual Arabic-English at reasoning parity; Arabic register derived per-session from Brand DNA Profile; hybrid rules+LLM pain analysis; 50-minute session budget with up to 3 minutes per module; simultaneous output reveal with no facilitator pre-review gate; text-only PDF export covering all session artifacts; questionnaire versioning for auditable history; N-best sampling architecture open for later resolution with constraint that client judges final output only.

## Appendix D — Diagrams

Four diagrams are embedded in this document at the sections where they provide the most context:

- Figure 1 — Three-Phase Session Flow (Section 2.1)
- Figure 2 — Component Architecture (Section 4.1)
- Figure 3 — Module Dependency Graph (Section 5.3)
- Figure 4 — Language & Register Flow (Section 5.7)

*All four diagrams use the same colour convention: yellow for deterministic pure-logic components (orchestration, rules engine, resolver), pink for LLM-backed components (generation, narrative), grey for infrastructure, and phase-themed backgrounds for session flow diagrams.*

*End of Document — Technical Design Document, v0.4 (Final Draft for Stakeholder Review)*
