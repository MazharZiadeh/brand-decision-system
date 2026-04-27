# CLAUDE.md — Project Bible

> This file is the source of truth for any Claude Code session working on this repository. Read it in full before doing anything else. Do not skim. The architectural rules below are non-negotiable and exist for reasons documented in the TDD.

---

## 1. What This Project Is

This is the **Real-Time Brand Decision System** — a facilitator-operated, bilingual (Arabic + English) web application used by an agency principal during live meetings with brand clients. In a single 50-minute session, the tool guides participants through three phases:

1. **Discovery** — a fixed canonical questionnaire produces a Brand DNA Profile, a Pain Analysis, and a Language Register directive.
2. **Decision** — the client selects a non-empty subset of five brand modules (Strategy Theme, Tone, Naming, Slogan, Tagline).
3. **Generation** — module runners produce rationale-bearing creative outputs conditioned on Discovery outputs and upstream module outputs.

Companion documents in this repo (or referenced by it):
- `docs/TDD.md` — full Technical Design Document (v0.4)
- `docs/MVP_PLAN.md` — what the MVP includes and excludes
- `docs/M1_TODO.md` — current milestone task list
- `docs/METHODOLOGY.md` — agency expert's questionnaire methodology (filled in during M1)

We are currently building **Milestone 1 — the Input Layer**. Generation modules are stubs in M1; do not implement them.

---

## 2. Architectural Invariants — Never Violate

These rules come directly from the TDD. They are load-bearing. If a request appears to require violating one, **stop and ask** rather than violate it.

### 2.1 Orchestration never calls the LLM
The Orchestration Engine, Rules Engine, and Language Register Resolver are pure-logic components. **They do not import the LLM client. They do not make HTTP calls. They are deterministic.** All LLM calls are confined to the Narrative Generator and Module Runners, all routed through the LLM Provider Abstraction.

### 2.2 The LLM Provider Abstraction is the single chokepoint
There is exactly one place in the codebase that calls the LLM provider's SDK. Every other component requesting a generation goes through that abstraction. Never `import anthropic` (or `google.generativeai`, or `openai`) outside `src/llm/provider.py`.

### 2.3 Modules never call each other directly
Module Runners communicate only through the Session Service. A Module Runner receives upstream outputs as explicit inputs to its function. It does not import another Module Runner.

### 2.4 Language is data, not a mode
Every persisted content object carries a non-null `language` field tagged at authorship time. There is no global session language. There is no runtime language inference. If a content object would be created without a language tag, that is a bug.

### 2.5 Register is derived, not configured
The Language Register directive (primary language, Arabic variety, register level, cultural anchors) is computed by a deterministic resolver from the Brand DNA Profile. Operators do not choose it. Modules do not override it.

### 2.6 Suppression is absolute
A module not in the Decision Scope produces zero output, is not referenced in any prompt, has its priority hierarchy unconsulted, and participates in no intersection rule. Not "less", not "in the background" — zero.

### 2.7 Every generated output carries its rationale
Every LLM-backed output (Pain Narrative, Module Outputs) is a triple: `(output, rationale, priority_factors_addressed)`. Output without rationale is not valid output and must fail validation.

### 2.8 Every LLM call is audited
Every call through the LLM Provider Abstraction creates an `LLMCallRecord` with: prompt hash, model version, language directive, register directive, parameters, response, latency, status. No exceptions. This underpins the "rationally justified" product claim.

### 2.9 Determinism boundaries
- **Routing determinism is absolute.** Identical inputs to Orchestration / Rules Engine / Resolver / Prompt Builder produce identical outputs every time. Code accordingly.
- **Output traceability is enforced.** LLM-generated content is not bit-exact reproducible, but every output's rationale and audit record make it explainable.

### 2.10 Discovery → Decision → Generation order
Phases run in fixed order. Generation cannot start until Discovery has produced a complete Brand DNA Profile and the client has selected a Decision Scope. Do not allow phase skipping.

---

## 3. Repository Structure

```
.
├── CLAUDE.md                    # This file
├── README.md
├── pyproject.toml               # Python project config, deps, ruff/black
├── alembic.ini
├── docker-compose.yml           # local Postgres
├── .env.example
├── src/
│   ├── main.py                  # FastAPI entrypoint
│   ├── config.py                # Settings via Pydantic
│   ├── domain/                  # Pydantic v2 models. No I/O. No side effects.
│   │   ├── session.py
│   │   ├── questionnaire.py
│   │   ├── pain.py
│   │   ├── register.py
│   │   ├── prompt.py
│   │   ├── module.py
│   │   └── audit.py
│   ├── orchestration/           # Pure logic. No LLM. No I/O.
│   │   ├── engine.py            # Decision Scope → ExecutionPlan
│   │   ├── suppression.py
│   │   └── intersections.py
│   ├── discovery/
│   │   ├── questionnaire_service.py
│   │   ├── rules_engine.py      # Pain tagging. Pure logic.
│   │   └── register_resolver.py # Pure logic.
│   ├── generation/              # Module Runners + Narrative Generator. LLM-backed.
│   │   ├── narrative_generator.py
│   │   ├── prompt_builder.py    # Session System Prompt builder
│   │   └── runners/             # M1: stubs only. Filled in M2-M4.
│   ├── llm/
│   │   └── provider.py          # THE ONLY PLACE that calls model SDKs
│   ├── persistence/
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   ├── session.py           # DB session management
│   │   └── repositories/
│   ├── api/
│   │   ├── routes/
│   │   └── auth.py
│   └── observability/
│       └── audit.py             # LLMCallRecord persistence
├── content/                     # Expert-authored content. Versioned with Git tags.
│   ├── questionnaires/
│   │   └── v1.0.0/
│   │       ├── questionnaire.en.yaml
│   │       └── questionnaire.ar.yaml
│   ├── pain_taxonomy.yaml
│   ├── pain_rules.yaml
│   ├── register_rules.yaml
│   └── prompts/
│       ├── unified_preamble.j2
│       └── modules/             # one per module
├── migrations/                  # Alembic
├── tests/
│   ├── unit/
│   ├── integration/
│   └── orchestration/           # The 31-combination tests live here
└── docs/
    ├── TDD.md
    ├── MVP_PLAN.md
    ├── M1_TODO.md
    └── METHODOLOGY.md
```

**Rule:** if you find yourself wanting to put code somewhere this structure doesn't accommodate, stop and ask. Don't invent new top-level directories.

---

## 4. Conventions

### 4.1 Python
- Python 3.11+, type hints everywhere, no untyped functions.
- `async def` for all I/O-bound functions. Sync only for pure-compute helpers.
- Pydantic v2 for all data validation at boundaries (API, DB, LLM, content files).
- SQLAlchemy 2.0 async for all DB access. No raw SQL in business logic.
- No bare `except:`. Catch specific exceptions or let them propagate.
- No `print()`. Use the configured logger.
- Imports sorted by ruff. Code formatted by black. Don't fight the formatter.

### 4.2 Naming
- Modules and files: `snake_case`
- Classes: `PascalCase`
- Functions and variables: `snake_case`
- Constants: `SCREAMING_SNAKE_CASE`
- Pydantic model classes mirror the domain entity names exactly: `Session`, `QuestionnaireInstance`, `Answer`, `PainAnalysis`, `LanguageRegister`, `ModuleOutput`, `Rationale`, `LLMCallRecord`, `SessionSystemPrompt`.

### 4.3 Tests
- pytest for all tests. pytest-asyncio for async.
- Three categories: `unit/` (pure logic, no I/O, fast), `integration/` (DB + services, slower), `orchestration/` (the 31-combination tests).
- Every pure-logic function (orchestration, rules, resolver, prompt builder) gets a unit test with synthetic inputs.
- Every Pydantic model gets validation tests for at least one valid input and one invalid input.
- Tests are deterministic. No `time.sleep()`, no real network calls in unit tests, no model calls in unit tests.

### 4.4 Errors and validation
- Boundaries validate. Internals trust. The API layer validates inputs into Pydantic models; downstream code can assume types are correct.
- Failed validation returns `422 Unprocessable Entity` with structured error details.
- Domain exceptions live in `src/domain/exceptions.py`. They inherit from a single `DomainError` base.
- Never swallow an exception. Either handle it specifically or let it propagate.

### 4.5 Logging
- Structured JSON logs to stdout. One log entry per significant event.
- Required fields on every log entry: `timestamp`, `level`, `event`, `session_id` (when applicable).
- LLM call logs include all `LLMCallRecord` fields.

### 4.6 Configuration
- All configuration via environment variables, loaded through a Pydantic `Settings` class in `src/config.py`.
- `.env.example` is committed; `.env` is git-ignored.
- Never hardcode model names, API keys, database URLs, or feature flags.

### 4.7 Git
- Conventional commits (`feat:`, `fix:`, `chore:`, `test:`, `docs:`, `refactor:`).
- Small commits, focused changes. One logical change per commit.
- Never commit secrets, `.env` files, or generated files.

---

## 5. Content Files (expert-authored)

The agency expert authors content in YAML and Jinja2 files under `content/`. These are NOT code. They are versioned with Git tags (e.g., `questionnaire-v1.0.0`). When the expert delivers an update, it lands as a new tag.

- Questionnaire content lives in `content/questionnaires/<version>/`.
- Pain taxonomy, pain rules, register rules each live in their own YAML file.
- Module prompt templates live as Jinja2 in `content/prompts/`.

**Rule:** code does not embed expert content. Code loads expert content from these files. If you find yourself writing `pain_categories = ["obscurity", "stagnation", ...]` in Python, stop — that belongs in YAML.

**Rule:** schema validation on content files happens at app start. Bad content fails loud and prevents the app from starting. Better than silent miscalibration.

---

## 6. What is OUT of M1 Scope

Do not implement these in M1, even if a task seems to call for them:

- Generation Module Runners (Strategy/Tone/Naming/Slogan/Tagline) — stubs only in M1
- N-best sampling architecture — single-shot generation only, this is open question A10
- PDF export — M2+
- Session resume UI flows — backend support yes, frontend M2+
- Multi-tenancy — single agency
- Regeneration of any output
- Production-grade auth (SSO, MFA) — basic email+password is fine
- Layers 2–5 from the product roadmap (Audience Intelligence, Competitive Context, Output Refinement, Decision Capture)
- Content authoring UI for the expert — content is files in repo
- Streaming output

If unsure whether something is in scope, check `docs/M1_TODO.md`. If still unsure, ask.

---

## 7. Stop and Ask Cases

Pause and ask the human before proceeding when:

- A requested change would violate one of the architectural invariants in §2.
- A task description is ambiguous about which phase or module it applies to.
- An LLM provider choice needs to be made (provider is decided by the bake-off in M1, not by Claude Code).
- A piece of expert content is required but the corresponding YAML file is empty or missing.
- A new top-level directory or major architectural component would need to be added.
- Adding a third-party dependency that isn't already in `pyproject.toml`.
- The implementation would require knowledge of the agency expert's methodology that isn't documented in `docs/METHODOLOGY.md`.

It is always better to stop and ask than to guess. Guesses become technical debt; questions become clarity.

---

## 8. Working Patterns

### 8.1 When implementing a new component
1. Check this file's §3 for where it lives.
2. Read the relevant section of the TDD if it exists.
3. Write the Pydantic models (or extend existing ones) first.
4. Write the unit tests next, with synthetic inputs covering happy paths and obvious edge cases.
5. Implement the function/class to make the tests pass.
6. Run `ruff` and `black` before committing.

### 8.2 When implementing an LLM-backed component
1. Define the structured output schema as a Pydantic model.
2. Write the prompt template in `content/prompts/` (Jinja2).
3. Implement the runner that loads the template, builds the prompt, and calls through `src/llm/provider.py`.
4. Write a mocked unit test (no real LLM call) for the runner's logic.
5. Write at most one integration test that hits the live LLM with a canned input. Mark it `@pytest.mark.integration` so it's not in the default test run.
6. Audit logging is mandatory and verified by the test.

### 8.3 When ambiguity arises during implementation
Do not paper over with default values, hardcoded fallbacks, or "TODO" comments that hide a missing decision. Surface the ambiguity in your reply and let the human decide.

---

## 9. The "Three Things" Test

Every change should pass this check before commit:

1. **Does it preserve the architectural invariants in §2?**
2. **Does it have at least one test that fails meaningfully if the change regresses?**
3. **Could a future contributor read the diff and understand the why, not just the what?**

If any answer is "no", the change isn't ready.

---

*Last updated: M1 kickoff. This file evolves as the project does. Update it when invariants are added, removed, or refined — never when they're temporarily inconvenient.*
