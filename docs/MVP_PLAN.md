**MVP Plan**

Real-Time Brand Decision System

*Technical Stack & Vertical-Slice Build Plan*

Document Version: 1.0

Date: April 25, 2026

*Companion to: TDD v0.4*

# 1. What This Document Is

This is the MVP plan for the Real-Time Brand Decision System. It is a companion to the Technical Design Document (v0.4); the TDD describes what the full system is, this document describes the smallest version that proves the product works.

This document is opinionated. It picks specific tools, specific cuts, and a specific build order. The TDD said 'Pydantic-class schema validation'; this document says Pydantic v2. The TDD said 'a frontier model with validated Arabic quality'; this document names candidates and picks one. Where the TDD held options open for the stakeholder, this document closes them down to what we will actually build.

**Every choice in this document can be revisited. None of them should be revisited mid-MVP without explicit reason.**

## 1.1 What the MVP must prove

Three things, in order of importance:

- Deterministic orchestration works correctly across all 31 Decision Scope combinations. Suppression holds. Sequencing holds. Intersection logic conditions downstream outputs as specified.
- The Discovery → Generation pipeline produces output the agency expert recognises as professionally usable. Not technically valid; actually good.
- Arabic and English produce output at quality parity. Arabic in particular meets the agency expert's bar for native-speaker work.

Anything that does not directly serve one of those three is out of MVP scope.

## 1.2 What the MVP is explicitly not

- Not multi-tenant. One agency, one set of facilitators, one deployment.
- Not a polished UI. The interface is functional, not designed.
- Not exception-handling-complete. Happy path works flawlessly; error states are minimally handled.
- Not feature-rich. Everything optional in the TDD that can be deferred is deferred.
- Not deployable to production for paid client use. The MVP is for the agency's own internal validation. Production-readiness is a follow-on phase.

# 2. Technology Stack

Every choice tied to a requirement. Read this section once, then never debate the stack again until MVP is done.

## 2.1 Backend

| **Layer** |** Choice** |** Why** |
|---|---|---|
| Language | Python 3.11+ | Fastest path to LLM tooling. Matches your existing skill set. Strong async story, mature ecosystem. |
| Web framework | FastAPI | Async by default. Pydantic integration native. Auto-generated OpenAPI for free. Tiny boilerplate. |
| Schema validation | Pydantic v2 | The determinism enforcer. Every input, output, and persisted object is a Pydantic model. The LLM cannot return anything that doesn't validate. |
| LLM client | Anthropic SDK (Claude) as primary | Reasoning for choice in section 2.4. Single SDK kept behind the LLM Provider Abstraction so it can be swapped. |
| Structured output | Anthropic tool use (function calling) | Forces schema-compliant JSON at the model boundary. No regex parsing of free text. |
| Async runtime | asyncio + httpx | Standard. No reason to overthink. |
| Testing | pytest + pytest-asyncio | Standard. Fixtures map cleanly onto session/module testing. |
| Linting / formatting | ruff + black | Fast, opinionated, zero-config. |

## 2.2 Persistence

| **Layer** |** Choice** |** Why** |
|---|---|---|
| Database | PostgreSQL 16 | Strong consistency, JSONB for flexible content objects, proven RTL/Unicode handling, easy local dev. |
| ORM / query layer | SQLAlchemy 2.0 (async) + Alembic for migrations | Standard, mature, async-native in 2.0. |
| Schema strategy | Relational core (Sessions, Facilitators, ModuleOutputs) + JSONB for variable-shape content (questionnaire answers, rationales, audit payloads) | Best of both worlds. Strong constraints on entities, flexible content. |
| Cache (deferred) | None for MVP | Latency budget is 3 minutes per module. Redis is unnecessary for MVP. Add only if measured latency demands it. |
| Migrations | Alembic | Standard with SQLAlchemy. Versioned migrations from day one even if schema is small. |

## 2.3 Frontend (minimal)

| **Layer** |** Choice** |** Why** |
|---|---|---|
| Framework | Next.js 15 (App Router) with TypeScript | You already use it. Server components handle most rendering. Trivial deployment. |
| UI library | Tailwind CSS + shadcn/ui | Functional, readable, no design work required. Components look professional out of the box. |
| RTL handling | Tailwind RTL utilities + dir attribute switching per content object | Per-object language tagging needs per-element direction. Tailwind handles this cleanly. |
| State | React Server Components + minimal client state | Sessions live on the server. Client state is interaction-only. |
| Auth | NextAuth.js with email + password (single-tenant) | Adequate for MVP. Production auth is a follow-on. |

## 2.4 LLM provider — the decision and why

This is the most consequential stack decision for this project. The full TDD left it open; this MVP plan closes it.

**Recommendation: Anthropic Claude (latest available frontier model from the Claude family) as primary, behind an abstraction that allows swapping.**

Reasoning, in order:

- **Arabic quality.** Frontier models from Anthropic, OpenAI, and Google all handle Modern Standard Arabic competently. For Gulf dialect and culturally-grounded creative output, Claude has consistently strong results in informal benchmarking. This needs to be re-validated by the agency expert in Phase 1, but it is the strongest starting bet.
- **Structured output.** Anthropic's tool-use API enforces JSON schema rigorously. Every module output validates or fails — no "the model returned something close to JSON" parsing.
- **Reasoning quality on rationale generation.** Every module must produce a rationale citing priority factors. Claude is particularly strong at structured reasoning under explicit constraints, which is exactly what rationale generation is.
- **Token cost on Arabic.** All major models tokenize Arabic less efficiently than English. Cost difference between providers is in the same order of magnitude; not a decisive factor.
- **Provider lock-in mitigation.** The LLM Provider Abstraction (TDD §4.1) means model swap is a one-day change, not a one-month change. Pick the best for Arabic quality today; swap if a better option emerges.

*Pinned model version: the most recent Claude model available at MVP-start, captured as a constant in the LLM Provider Abstraction. Migrations require a full bilingual evaluation pass.*

## 2.5 Content storage — questionnaire, taxonomy, rules, prompts

| **Content type** |** Storage** |** Rationale** |
|---|---|---|
| Questionnaire content | YAML files in repo, versioned by Git tag | Expert-authored. Reviewed via pull request. Each session stamps the QuestionnaireVersion (Git tag or content hash) it used. |
| Pain taxonomy | YAML in repo | Same pattern. Small, stable, reviewed. |
| Pain-tagging rules | YAML in repo, evaluated by a small Python rule runner | Declarative DSL. Expert can read and review rules without engineering involvement. |
| Language Register Resolver rules | YAML in repo | Same pattern. |
| Module prompt templates | Python files (Jinja2 templates) in repo | Versioned with code. Prompt changes are PRs with mandatory bilingual eval-set pass. |
| LLM Judge prompt (deferred) | Same pattern, when A10 resolves | If/when N-best sampling is decided, the judge prompt joins the same versioned pool. |

*All expert-authored content lives in Git. There is no admin UI for editing content in MVP. Content updates are deployment events. This is a deliberate simplification — the alternative (in-app authoring) is months of work for marginal MVP value.*

## 2.6 Infrastructure (minimal)

| **Layer** |** Choice** |** Why** |
|---|---|---|
| Hosting (backend) | Single Docker container on a small VPS or single cloud VM (e.g., Hetzner, DigitalOcean droplet, AWS Lightsail) | MVP traffic is one facilitator at a time. A $20/month box is sufficient. No Kubernetes, no auto-scaling, no managed-services complexity. |
| Hosting (frontend) | Vercel free tier | Standard Next.js host. Zero ops. Free for this scale. |
| Database hosting | Managed Postgres on the same provider as backend, OR Postgres in the same Docker compose | Either works. Managed is slightly more reliable; bundled is cheaper. Pick based on hosting choice. |
| TLS | Caddy or Cloudflare in front | Free, automatic certificates. |
| Logging | stdout → file → tail/grep | Genuinely sufficient for MVP. Structured logs as JSON lines. Move to a real log aggregator only when MVP graduates. |
| LLM call audit | Postgres table | Same database. Same backups. No separate audit pipeline. |
| Backups | Daily pg_dump to object storage | Standard. Three-day retention is fine for MVP. |
| Monitoring | Healthcheck endpoint + uptime ping | Manual eyeballing the dashboard during dev sessions is acceptable for MVP. |

## 2.7 What is deliberately not in the MVP stack

- No Redis, no message queue, no Celery.
- No Kubernetes.
- No multi-region, no CDN beyond what Vercel gives for free.
- No observability vendor (Datadog, New Relic, Sentry as paid tier) — stdout logging only.
- No analytics, no tracking, no telemetry beyond audit logs.
- No CI/CD pipeline beyond a single GitHub Actions workflow that runs tests.
- No staging environment. Local dev → production. Cut staging back in once MVP graduates.
- No second LLM provider behind the abstraction. The abstraction exists; the second implementation does not.
- No PDF design templates beyond minimal default styling with RTL support.

# 3. MVP Scope — What's In

## 3.1 Vertical slice

The MVP is a complete vertical slice through the system. Every layer present, every layer minimal. The slice can run an end-to-end session for a chosen Decision Scope and produce defensible output.

To bound the slice, MVP picks one specific Decision Scope as the showcase target:

**Strategy Theme + Tone + Slogan**

Why this combination:

- It exercises the full dependency graph (foundational → governance → expressive).
- It exercises intersection logic in two directions (Strategy→Tone, Strategy→Slogan, Tone→Slogan) — three of the seven intersection rules.
- It produces output the expert can judge tangibly: a strategic statement, a voice definition, three slogan styles. All are concrete artifacts.
- It avoids Naming and Tagline for MVP, which simplifies content authoring. Both come back online in Phase 2.

*All five modules will be supported in code. Only this combination is target-quality in the MVP. The other 30 combinations work end-to-end (suppression and sequencing correct) but their outputs are not yet expert-validated.*

## 3.2 What's in

| **Capability** |** In MVP?** |** Notes** |
|---|---|---|
| Facilitator login (email + password, single agency tenant) | Yes | NextAuth standard implementation. |
| Create new session | Yes | |
| Serve canonical questionnaire | Yes | From YAML, versioned. |
| Capture answers per question, with language tag | Yes | Discovery phase complete. |
| Rules-engine pain tagging | Yes | Reads YAML rules. Deterministic. |
| LLM-backed pain narrative generation | Yes | Schema-validated. |
| Language Register Resolver | Yes | From YAML rules. |
| Decision Scope selection by client (any subset) | Yes | Full 31-combination support at orchestration level. |
| Orchestration Engine: execution plan generation | Yes | Pure-function, fully tested across 31 combinations. |
| Module Runners for all 5 modules | Code-complete | Strategy, Tone, Slogan are quality-validated. Naming, Tagline run but aren't quality-bar gated for MVP. |
| Intersection logic across all 7 pairs | Yes | Code complete. Strategy→Tone, Strategy→Slogan, Tone→Slogan are quality-validated. |
| LLM Provider Abstraction with one provider (Anthropic) | Yes | Audit logging complete. |
| Persistence: sessions, answers, outputs, rationales, audit | Yes | All entities per TDD §7. |
| Session resume | Yes | Critical for in-meeting use. |
| PDF export (text-only, all artifacts, RTL-aware) | Yes | Per A7. |
| Bilingual support: Arabic + English, mid-session mixing | Yes | Critical. |
| Simultaneous output reveal (no review gate) | Yes | Per A9. |
| Single-output per module (no N-best sampling) | Yes | A10 deferred. MVP uses single-shot generation. |
| Basic observability: structured stdout logs | Yes | Sufficient for MVP. |

## 3.3 What's out

| **Capability** |** Why deferred** |
|---|---|
| N-best sampling (A10) | Architectural decision still open. MVP works with single-shot. Add when A10 resolves. |
| Quality-validated Naming and Tagline modules | Code present, but expert content (questionnaire fields driving them, prompt refinement, evaluation set) deferred to Phase 2. |
| Multi-tenancy | Single agency for MVP. |
| In-app content authoring | Content lives in Git for MVP. |
| Branded PDF design | Plain text PDF only. |
| Mobile or tablet native clients | Web only. |
| Offline mode | Online required. |
| Sharing sessions between facilitators | Single owner per session. |
| Regenerating module outputs in-session | v2 (Layer 4). |
| Layers 2–5 from product roadmap | Out of scope per TDD §12. |
| Production-grade auth (SSO, MFA) | Email+password adequate for MVP internal use. |
| Real-time collaboration | Single operator. |
| Analytics or usage dashboards | Not required for MVP validation. |
| Cost monitoring beyond audit-log totals | Manually computed during MVP. |
| Failover, redundancy, geographic distribution | Single VM for MVP. |

# 4. Milestones

The MVP is broken into five milestones. Each milestone has a concrete deliverable and an exit gate. No milestone is 'done' until its gate passes.

*Estimated total duration: 8–10 working weeks for a single technical lead, assuming the agency expert delivers content (questionnaire, taxonomy, rules) on the schedule below. Slippage in expert deliverables slips the entire timeline.*

## M0 — Foundations (week 1)

| **Item** |** Detail** |
|---|---|
| Goal | Project skeleton. Domain model. Empty Orchestration Engine. No LLM calls anywhere yet. |
| Deliverables | FastAPI app shell. Pydantic v2 domain models for every entity in TDD §7. Postgres + Alembic + initial migration. SQLAlchemy async setup. pytest scaffolding. |
| Orchestration | Hand-rolled state machine for the three phases. Module dependency graph encoded. Suppression rule enforced. |
| Tests | Unit tests for all 31 Decision Scope combinations producing correct execution plans. This is the milestone's hard gate — 31/31 pass or M0 is not done. |
| What's not yet present | No LLM calls. No questionnaire content. No frontend. No real outputs. |
| Exit gate | 31/31 combination tests pass. Domain model reviewed and accepted. Database migrations apply cleanly on a fresh Postgres instance. |

## M1 — Discovery end-to-end (weeks 2–3)

| **Item** |** Detail** |
|---|---|
| Goal | A facilitator can authenticate, create a session, run through the questionnaire, and see a complete Pain Analysis and Language Register at the end of Discovery. In both languages. |
| Dependency on agency expert | Questionnaire (A2), pain taxonomy (A4), rule set (A5), and Register Resolver rules must be delivered by end of week 2. Without these, M1 cannot complete. |
| Deliverables | Questionnaire Service serving versioned YAML content. Answer capture with language tagging. Rules Engine implementing the YAML rule DSL. Narrative Generator with LLM call + schema validation + audit logging. Language Register Resolver. NextAuth login. Bare-minimum frontend for these flows. |
| LLM Provider Abstraction | Built. Single provider (Anthropic). Pinned model version. Full audit logging. |
| Tests | Discovery flow runs end-to-end on representative test inputs in both languages. Pain Analysis schema-validates. Register directive schema-validates. |
| Exit gate | Agency expert sits through a full Discovery for a real test brand in Arabic and another in English. Expert signs off that the resulting Pain Analysis and Register directive are usable. This is a quality gate, not just a 'tests pass' gate. |

## M2 — Strategy Theme module live (weeks 4–5)

| **Item** |** Detail** |
|---|---|
| Goal | First Generation module producing real LLM output. Strategy Theme produces a single strategic statement with rationale, in the directed language and register, schema-validated, audit-logged. |
| Why Strategy Theme first | It is the most constrained output (one statement in a fixed format), the easiest to evaluate, and the foundational module other expressive modules condition on. |
| Deliverables | Strategy Theme Module Runner. Prompt template (versioned in repo). Schema validation. Output displayed in frontend with rationale visible. PDF export starts working for Discovery + Strategy. |
| Evaluation | Build a small evaluation set: 5–10 hypothetical brand briefs (mix of Arabic and English target audiences). Run Strategy Theme against each. Expert reviews. |
| Exit gate | Expert signs off on Arabic and English Strategy Theme output quality at parity. Output passes content-safety filter. Audit trail visible. |

## M3 — Tone and Slogan modules + intersection logic (weeks 6–7)

| **Item** |** Detail** |
|---|---|
| Goal | Tone module and Slogan module live. Three intersection pairs working: Strategy→Tone, Strategy→Slogan, Tone→Slogan. |
| Deliverables | Tone Module Runner. Slogan Module Runner. Intersection injection in prompts (downstream prompts include upstream outputs as constraints). Schema validation per module. |
| Multi-module session | A facilitator can run Strategy + Tone + Slogan as a single Decision Scope and receive coherent, conditioned outputs. |
| Evaluation | Extend the eval set to multi-module cases. Expert reviews coherence: does the Tone reflect the Strategy? Do the Slogans honor the Tone? |
| Exit gate | Expert signs off on multi-module coherence in both languages. Three intersection pairs demonstrably influence outputs (we can show: same Strategy, different Tones → different Slogans). |

## M4 — Naming and Tagline + full PDF + hardening (weeks 8–10)

| **Item** |** Detail** |
|---|---|
| Goal | All five modules code-complete. PDF export covers all artifacts. Session resume works reliably. Internal demo-ready. |
| Deliverables | Naming Module Runner. Tagline Module Runner. All seven intersection pairs implemented. PDF export covering Discovery + all module outputs + rationales, RTL-aware. Session resume tested. Audit trail review UI for the expert. |
| Note on Naming and Tagline quality bar | Code complete but quality validation of these two modules is best-effort for MVP. Full expert signoff happens in the post-MVP polish phase. This is a deliberate compromise: it lets the MVP demonstrate the whole system shape without gating MVP exit on content readiness for two more modules. |
| Hardening | Error states for the happy path's adjacent failures (session not found, expired token, LLM provider timeout). Graceful messages, not crashes. |
| Exit gate | End-to-end demo session: facilitator logs in, runs Discovery in Arabic, picks Strategy + Tone + Slogan, gets quality outputs, exports PDF, expert signs off. Then a second demo: same flow in English with Strategy + Tone + Slogan + Tagline, demonstrating Tagline runs (lower-bar) and PDF handles bilingual session. |

# 5. Working With the Agency Expert

The agency expert is on the project's critical path. The MVP cannot complete without their content deliverables and quality signoffs. This needs to be operational, not aspirational.

## 5.1 Expert deliverables and when they're needed

| **Deliverable** |** Owner** |** Needed by** |** Format** |
|---|---|---|---|
| Canonical questionnaire | Expert | End of week 2 | YAML structure, with question text in both languages, answer options, optional branching |
| Pain taxonomy | Expert | End of week 2 | Flat list of pain category identifiers + description per category |
| Rule set: answer → pain mapping | Expert | End of week 2 | YAML rule format provided by engineering |
| Register Resolver rules | Expert | End of week 2 | YAML rule format. Maps Brand DNA fields to register directive. |
| Strategy Theme prompt review | Expert | Week 5 | Engineering drafts; expert reviews and refines wording |
| Strategy Theme evaluation set | Expert + Engineering | Week 5 | 5–10 hypothetical brand briefs with expected output shapes |
| Tone and Slogan prompt review | Expert | Week 7 | Same pattern as Strategy |
| Tone and Slogan evaluation set | Expert + Engineering | Week 7 | Same pattern |
| Final MVP demo signoff | Expert | Week 10 | Two end-to-end sessions, one Arabic-led, one English-led |

## 5.2 Working pattern with the expert

The expert is not authoring code. The technical lead translates expert methodology into machine-executable form. The pattern:

- Schedule a 90-minute session with the expert. Recorded, with notes.
- Expert explains methodology in their own language. Technical lead asks clarifying questions until rules become unambiguous.
- Technical lead translates methodology into YAML rules / prompt drafts. Done within 24–48 hours.
- Expert reviews. Iterate until expert signs off.
- Once signed off, the rule or prompt is committed to repo with a Git tag the session can reference.

*This pattern is repeated for each major content area. Estimated time per area: one 90-minute session, plus 1–2 follow-up shorter sessions for refinement.*

## 5.3 Risks specific to expert collaboration

| **Risk** |** Mitigation** |
|---|---|
| Expert delivers content late | Build the engineering pieces that don't depend on expert content first (M0, the orchestration shell, the LLM Provider Abstraction). Don't burn the calendar waiting. |
| Expert's methodology is harder to formalize than expected | Schedule the first knowledge-engineering session in week 1, not week 2. Discover difficulty early. |
| Expert disagrees with output quality at signoff | Build evaluation iteration into the schedule. Don't treat signoff as a one-shot binary; treat it as 1–3 review rounds with prompt refinement between. |
| Expert is unavailable when needed | Get a written commitment to specific review windows at the start of the project. The expert's signoff is on the critical path; their calendar slots are not optional. |

# 6. MVP-Specific Risks

| **Risk** |** Severity** |** Mitigation** |
|---|---|---|
| Arabic output below expert's bar | High | Validated against expert from M1 onward. Quality is a release gate at every milestone, not a final check. |
| LLM provider model deprecation mid-MVP | Low (but irrecoverable if it happens) | Pin a stable model version. If a deprecation notice arrives, treat as a P0 — schedule re-evaluation immediately. |
| Expert availability slips | High | Section 5.3. The single biggest schedule risk is non-engineering. |
| Latency exceeds 3-min budget per module | Medium | Measure from M2 onward. Budget allows headroom; if exceeded, options are: simpler prompts, pre-warming, or a faster model. Decide based on data. |
| LLM cost during evaluation runs higher than expected | Low | Budget for evaluation is finite. Use cheaper model variants for evaluation iteration; switch to pinned production model only for final acceptance runs. |
| MVP stack doesn't scale beyond MVP | Acceptable | By design. Single-VM, no Redis, no message queue. Production scaling is a deliberate follow-on phase. |
| Frontend looks unprofessional in expert demo | Medium | Use shadcn/ui defaults. Functional and presentable without design work. If demo polish becomes a blocker, allocate one week post-M4 to UI cleanup. |
| Single technical lead (capacity risk) | High | No mitigation in this document. Captured as a project-level concern. If capacity is a real problem, the MVP scope must shrink — drop the Naming and Tagline modules from M4 entirely, defer to post-MVP. |
| A10 (N-best) pressure resurfaces mid-MVP | Low | Resist. Single-shot generation is the MVP rule. A10 is a post-MVP decision. |

# 7. After the MVP

The MVP exits. The next stages are decided based on what the expert and stakeholder learn from running real sessions on the MVP. This section is a roadmap, not a commitment.

## 7.1 Likely immediate follow-ons

- Quality validation for Naming and Tagline modules to the same bar as Strategy/Tone/Slogan.
- Resolution of A10 (N-best architecture) and implementation.
- Production-readiness pass: error handling, logging vendor, monitoring, real auth, real backups.
- Frontend polish: typography, layout, RTL refinements, possibly engaging a designer.
- PDF design template (still text-heavy but with branded styling).
- Session sharing between facilitators within an agency.

## 7.2 Roadmap layers from the original product spec

Layers 2 through 5 from the source product specification (Audience Intelligence, Competitive Context, Output Refinement, Decision Capture) remain on the roadmap but are explicitly post-MVP. They should not be scoped or designed until the MVP is in real use and the agency has data on which layer the market actually wants next.

# 8. Appendix

## 8.1 First-week task list

If you sit down Monday and want to start, this is the order:

- Set up Git repo, Python 3.11+ environment, FastAPI hello-world, Postgres locally.
- Define Pydantic v2 models for Session, Facilitator, QuestionnaireInstance, Answer, ModuleOutput, Rationale, LLMCallRecord. From TDD §7.
- Set up Alembic; first migration creates all tables corresponding to the Pydantic models.
- Implement the Orchestration Engine as a pure-function module. Input: Decision Scope. Output: ExecutionPlan.
- Write the 31 unit tests covering all combinations. They should all pass against your Orchestration Engine.
- In parallel, schedule the first knowledge-engineering session with the expert for end of week 1 / start of week 2. Don't wait until week 2 to schedule.
- By end of week 1, M0 should be exitable: 31/31 tests pass, domain model committed, database migrations work.

## 8.2 Stack quick reference

| **Layer** |** Tool** |** Version** |
|---|---|---|
| Language | Python | 3.11+ |
| Web framework | FastAPI | latest |
| Schema | Pydantic | v2 |
| Database | PostgreSQL | 16 |
| ORM | SQLAlchemy | 2.0 (async) |
| Migrations | Alembic | latest |
| LLM provider | Anthropic Claude | Pinned model version (latest at MVP-start) |
| LLM SDK | anthropic-sdk-python | latest |
| Frontend | Next.js | 15 (App Router) |
| Frontend language | TypeScript | 5.x |
| UI library | Tailwind + shadcn/ui | latest |
| Auth | NextAuth.js | latest |
| Testing | pytest + pytest-asyncio | latest |
| Lint/format | ruff + black | latest |
| Hosting (backend) | Single VM (Hetzner / DO / Lightsail) | — |
| Hosting (frontend) | Vercel free tier | — |
| TLS | Caddy or Cloudflare | — |

## 8.3 Things this document doesn't decide

Listing them so they're on record as 'decided later':

- Specific cloud provider for the VM.
- Specific Postgres host (managed vs bundled).
- Domain name and DNS provider.
- Email-sending provider for password reset (only needed if/when password reset is built).
- Backup retention beyond 'three days, daily.'
- Anthropic API account ownership (whose account funds the calls during MVP).

*End of MVP Plan v1.0*
