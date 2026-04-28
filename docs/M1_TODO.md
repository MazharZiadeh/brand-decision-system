# M1 — Input Layer

## Goal

Build the input layer. A facilitator can take a client through the questionnaire and the system produces a Session System Prompt at the end. Done.

## Setup

- [ ] Create Git repo *(done in Session 1)*
- [ ] Set up Python 3.11 + FastAPI + Pydantic v2 *(done in Session 1)*
- [ ] Set up Postgres locally *(done in Session 1)*
- [ ] Set up SQLAlchemy 2.0 async + Alembic *(done in Session 1)*
- [ ] Set up pytest *(done in Session 1)*
- [ ] Set up ruff + black *(done in Session 1)*
- [ ] Initialize Next.js 15 + TypeScript + Tailwind + shadcn/ui *(deferred — backend first)*
- [ ] Schedule first session with the expert

## Bring PROTAGET to the Table

- [ ] Pull the PROTAGET dimensions into a starter doc: 4 Brand DNA + 6 Audience + 4 Tensions
- [ ] Pull the slider band logic (<40 / 40-60 / >60) — use as starting pattern for rule DSL
- [ ] Pull a sample of PROTAGET Arabic outputs (good and bad ones) — use as evaluation reference
- [ ] Walk into expert session 1 with PROTAGET as the artifact to react to, not a blank page

## With Expert

- [ ] Knowledge session 1: walk through PROTAGET dimensions — what to keep, what to change, what's missing
- [ ] Knowledge session 2: question types, answer mechanics, branching
- [ ] Knowledge session 3: pain categories (expanding beyond PROTAGET's 4 tensions)
- [ ] Knowledge session 4: register rules (when MSA vs Saudi vs English)
- [ ] Knowledge session 5: what a good system prompt looks like
- [ ] Get the questionnaire authored in English
- [ ] Get the questionnaire authored in Arabic
- [ ] Get the pain taxonomy
- [ ] Get the pain-tagging rules
- [ ] Get the register resolver rules
- [ ] Get the system prompt template signed off

## Arabic Quality Diagnosis (do this early)

- [ ] With expert: review 5–10 sample PROTAGET Arabic outputs together
- [ ] Diagnose: was Arabic so-so because of (a) prompting, (b) wrong variety/register, or (c) model capability?
- [ ] Document the diagnosis — it determines what M1 prioritizes
- [ ] If (a) prompting: make Arabic-specific prompt instructions a first-class part of the system prompt builder
- [ ] If (b) variety/register: confirm the Resolver rules will fix it
- [ ] If (c) model: provider bake-off below is decisive

## LLM Provider Bake-off

- [ ] Define 5–7 test brand profiles spanning Arabic-led, English-led, formal, casual, premium, mass-market
- [ ] Build the prompt template once (provider-agnostic)
- [ ] Run each test profile through Gemini, Claude, and one more (GPT-class) — same prompt, same inputs
- [ ] Expert reviews outputs blind (provider names hidden) — picks favorite per profile
- [ ] Tally results, decide on primary provider, record decision in repo
- [ ] Pin the chosen model version in the LLM Provider Abstraction
- [ ] Time-box this to one working week max — don't let it become a research project

## Domain Models

- [ ] Pydantic: Facilitator, Session
- [ ] Pydantic: QuestionnaireVersion, Question, AnswerOption, QuestionnaireInstance, Answer
- [ ] Pydantic: PainTaxonomy, PainCategory, Rule, PainAnalysis
- [ ] Pydantic: LanguageRegister
- [ ] Pydantic: SessionSystemPrompt
- [ ] Pydantic: LLMCallRecord, Rationale
- [ ] Every content object has a language tag (enforced)

## Database

- [ ] Alembic migration: all tables
- [ ] Indexes on foreign keys
- [ ] Seed migration for first QuestionnaireVersion

## Orchestration

- [ ] Three-phase state machine (Discovery / Decision / Generation stubs)
- [ ] Decision Scope → Execution Plan pure function
- [ ] 31 unit tests, all combinations pass
- [ ] Suppression rule tests

## Questionnaire Service

- [ ] YAML loader for QuestionnaireVersion
- [ ] API: fetch questionnaire for session
- [ ] API: submit answer (with language tag)
- [ ] Validation: required answered, branching respected
- [ ] API: complete Discovery

## Rules Engine (Pain Tagging)

- [ ] Design YAML rule DSL (use PROTAGET getTrait pattern as seed)
- [ ] Rule loader with schema validation
- [ ] Rule evaluator: answers → pain tags
- [ ] Unit tests with synthetic answer sets

## Language Register Resolver

- [ ] Resolver function: Brand DNA → Register directive
- [ ] Unit tests: MSA case, Saudi case, English case, edge case

## LLM Layer

- [ ] LLM Provider Abstraction (interface, not provider-specific)
- [ ] Adapter for the provider chosen from bake-off
- [ ] Pinned model version captured as constant
- [ ] Structured output configured (tool use / response schema)
- [ ] Audit logging on every call

## Narrative Generator

- [ ] Generator: pain tags + Brand DNA → pain narrative + rationale
- [ ] Mocked unit tests
- [ ] Live integration test (small canned set)

## Session System Prompt Builder

- [ ] Unified preamble template (Jinja2)
- [ ] Per-module preamble extensions (5 modules)
- [ ] If diagnosis was (a) prompting: include explicit Arabic register/idiom instructions in templates
- [ ] Builder: returns prompt for a given module
- [ ] Inspection endpoint: view built prompt for a session
- [ ] Determinism test: same input → same prompt

## Frontend

- [ ] NextAuth login (email + password)
- [ ] Page: session list
- [ ] Page: new session
- [ ] Page: run Discovery (questionnaire UI)
- [ ] Page: view Brand DNA + Pain Analysis + Session System Prompt
- [ ] RTL handling per content object
- [ ] Question UI components: slider, single-choice, multi-choice, free-text
- [ ] Re-use PROTAGET slider visual style as starting point
- [ ] Wire frontend to backend

## Audit

- [ ] Structured JSON logging to stdout *(partially done in Session 1 — verify and extend in M1)*
- [ ] Audit-trail inspection endpoint

## Exit Gate

- [ ] Run a real test brand through Discovery in Arabic. Expert signs off on the Session System Prompt.
- [ ] Run a real test brand through Discovery in English. Expert signs off.
- [ ] Expert confirms Arabic quality has improved meaningfully over the PROTAGET baseline.
- [ ] All 31 orchestration tests pass.
- [ ] M1 done.
