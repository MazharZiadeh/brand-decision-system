# Real-Time Brand Decision System

> Facilitator-operated bilingual (Arabic + English) ideation tool that compresses weeks of agency-client iteration into a single 50-minute session.

The Real-Time Brand Decision System is a web application used by an agency principal during live meetings with brand clients. In a single facilitated session it walks the room through three phases — **Discovery**, **Decision**, and **Generation** — and produces five rationale-bearing brand artifacts (Strategy Theme, Tone, Naming, Slogan, Tagline) at the end. Every output is grounded in a deterministically derived Brand DNA Profile, a Pain Analysis with audited reasoning, and a Language Register directive computed from the client's own answers.

The product belief: brand strategy decisions are usually slow not because they are hard but because the iteration loop between agency and client is long and unstructured. Compressing that loop into a single live session, with the LLM acting as a fast and explainable creative partner rather than a black box, changes the economics of brand discovery for early-stage and rebrand engagements in the Saudi market.

---

## What this is

This repository is the **M1 backend** for that product. It is a Python 3.11+ FastAPI service that:

- Loads expert-authored content (questionnaires, pain taxonomy, register rules, prompt templates) from versioned YAML and Jinja2 files under `content/`.
- Runs a deterministic **Discovery Service** (rules engine + register resolver + narrative generator) that turns answers into a Brand DNA Profile, a Pain Analysis, and a Language Register directive.
- Runs a pure-logic **Orchestration Engine** that takes a Decision Scope (any non-empty subset of the five modules) and produces a deterministic ExecutionPlan — the 31 possible scope combinations are exhaustively tested.
- Runs a **Generation Service** that walks the plan, builds module prompts via Jinja2 + `StrictUndefined`, calls the LLM through a single Provider Abstraction chokepoint, and emits five rationale-bearing module outputs.
- Persists everything through SQLAlchemy 2.0 async + Alembic, with every LLM call captured in an `LLMCallRecord` audit trail.

The architectural rules — what touches the LLM, what cannot, what carries a language tag, what is suppressed under absolute scope, how rationale is required — are codified in [`CLAUDE.md`](./CLAUDE.md) and enforced both at the type level (Pydantic v2 + `LanguageTagged` mixin) and at runtime (the orchestrator scope filter, `StrictUndefined` in Jinja2, `priority_factors_addressed: min_length=2` on every module schema). They are non-negotiable: see §2 of CLAUDE.md.

The frontend, real LLM-provider adapter, PDF export, and resume UI flows are deliberately deferred past M1. The backend currently runs end-to-end against a **Mock LLM provider** that produces deterministic, schema-valid output — so the integration test (`tests/integration/test_full_session_flow.py`) actually exercises Discovery → Decision → Generation against live Postgres without burning model spend.

---

## Status — M1 backend

**Built and verified end-to-end:**

- ✅ 8 architectural layers across `src/`: `domain`, `orchestration`, `discovery`, `generation`, `llm`, `persistence`, `api`, `observability`
- ✅ Pydantic v2 domain models with `LanguageTagged` mixin enforcing the language-as-data invariant
- ✅ Pure-logic Orchestration Engine + 31-combination determinism coverage + invariant property tests
- ✅ Discovery Service: YAML loader, condition evaluator, rules engine, register resolver, narrative generator
- ✅ Generation Service: `ModuleConfig` registry, prompt builder with `StrictUndefined`, module runner, orchestrator with `GenerationResult` / `GenerationError`
- ✅ LLM Provider Abstraction (Protocol) with Mock provider — single `import anthropic` chokepoint reserved for `src/llm/provider.py`
- ✅ Audit chain: every LLM call produces an `LLMCallRecord` on both success and failure paths
- ✅ SQLAlchemy 2.0 async ORM + Alembic migration + `Session` repository pattern
- ✅ Capstone integration test running Discovery → Decision → Generation end-to-end against live Postgres + live Mock provider, all five module outputs produced
- ✅ ~514 unit tests + 15 integration tests, ruff + black + mypy configured

**Deferred past M1 (intentional):**

- ❌ Frontend (the facilitator UI)
- ❌ Real LLM provider adapter (Anthropic / Google / OpenAI) — the bake-off decides
- ❌ PDF export, session resume UI flows, regeneration of any output
- ❌ Generation N-best sampling — open question A10
- ❌ Multi-tenancy, production-grade SSO/MFA
- ❌ Layers 2–5 of the product roadmap (Audience Intelligence, Competitive Context, Output Refinement, Decision Capture)

The capstone integration test is the proof: if `pytest -m integration tests/integration/test_full_session_flow.py` passes against a fresh `docker compose up -d` Postgres, the backend pipeline is functional end-to-end. See [`AUDIT_REPORT_V3.md`](./AUDIT_REPORT_V3.md) for a full post-Session-7 audit of every CLAUDE.md invariant with file:line evidence.

---

## Architecture at a glance

The system is a layer cake. Each layer talks only to the layers directly beneath it; none of them reach across.

```
┌─────────────────────────────────────────────────────────────────┐
│  api/         FastAPI routes — boundary validation, no logic    │
├─────────────────────────────────────────────────────────────────┤
│  generation/  Module runners + orchestrator + prompt builder    │  ← LLM-backed
│               (the only place — alongside narrative_generator — │
│                that issues LLM calls)                            │
├─────────────────────────────────────────────────────────────────┤
│  discovery/   YAML loader · rules engine · register resolver ·  │  ← Pure logic
│               narrative generator (boundary)                     │     (mostly)
├─────────────────────────────────────────────────────────────────┤
│  orchestration/  Decision Scope → ExecutionPlan                 │  ← Pure logic
│                  Suppression · Intersections · 31-combination   │     no I/O
│                  determinism tests                               │
├─────────────────────────────────────────────────────────────────┤
│  llm/         Provider Protocol — THE single chokepoint         │
│               (Mock provider in M1; real adapter post-bake-off) │
├─────────────────────────────────────────────────────────────────┤
│  persistence/ SQLAlchemy 2.0 async · Alembic · repositories ·   │
│               domain ↔ ORM converters                            │
├─────────────────────────────────────────────────────────────────┤
│  domain/      Pydantic v2 models. Types only, no logic, no I/O  │
│               LanguageTagged mixin enforces §2.4                 │
├─────────────────────────────────────────────────────────────────┤
│  observability/  LLMCallRecord persistence — every call audited │
└─────────────────────────────────────────────────────────────────┘

content/        Expert-authored YAML + Jinja2 — versioned with Git tags.
                Schema-validated at app start. Bad content fails loud.
```

Five rules govern dependencies:

1. **Orchestration never imports the LLM.** It is pure logic.
2. **The LLM Provider Abstraction is the single chokepoint.** Nothing else imports `anthropic` / `google.generativeai` / `openai`.
3. **Modules never call each other.** They receive upstream outputs as explicit inputs through the orchestrator.
4. **Language is data.** Every persisted content object carries a non-null `language` tag. There is no global session language.
5. **Register is derived, not configured.** The resolver computes it from the Brand DNA Profile.

---

## Quickstart

**Prerequisites:** Python 3.11+, Docker, git.

```bash
git clone https://github.com/MazharZiadeh/brand-decision-system
cd brand-decision-system
cp .env.example .env

# Start Postgres (port 5432)
docker compose up -d

# Create venv and install
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (Git Bash / WSL)
source .venv/Scripts/activate

pip install -e ".[dev]"

# Apply migrations (creates the schema)
alembic upgrade head

# Boot the API
uvicorn src.main:app --reload    # serves on :8000

# Smoke test
curl http://localhost:8000/health
```

The `--reload` flag is for development. Production deployment is post-M1 and will run under `gunicorn -k uvicorn.workers.UvicornWorker`.

---

## Tests

The test suite is split into three categories, each with a pytest marker so you can pick what runs.

```bash
# Default: fast, hermetic, no external dependencies. ~514 tests.
pytest

# Integration: needs `docker compose up -d` Postgres on :5432. ~15 tests.
pytest -m integration

# Orchestration determinism: 31-combination coverage + invariant property tests.
pytest tests/orchestration/
```

**What the suites cover:**

- `tests/unit/` — pure logic across all 8 layers. Pydantic validation tests for every model, condition-evaluator tests, rules-engine tests, register-resolver tests, prompt-builder tests, module-runner tests with a Mock provider injected, persistence converter round-trip tests.
- `tests/orchestration/` — every one of the 31 possible Decision Scopes is exercised; suppression invariants and intersection rules verified against synthetic inputs.
- `tests/integration/` — live Postgres round-trips through the `Session` repository, Alembic migration smoke tests, and the **capstone end-to-end test** (`test_full_session_flow.py`) that runs Discovery → Decision → Generation across all five modules with the audit chain intact.

The capstone test is the structural proof of the product. If it passes, the M1 backend is wired correctly: questionnaire answers flow through rules → register → narrative → orchestrator → module runners → persisted outputs, with `LLMCallRecord` rows landing for every call.

Run `ruff check .` and `black .` before commits — CI runs both on every push.

---

## Project structure

```
.
├── CLAUDE.md                         # The project bible — read this first
├── README.md                         # You are here
├── AUDIT_REPORT_V3.md                # Current post-Session-7 audit (V1, V2 are historical)
├── pyproject.toml                    # Deps, ruff, black, mypy, pytest config
├── alembic.ini
├── docker-compose.yml                # Local Postgres 16-alpine
├── .env.example
├── src/
│   ├── main.py                       # FastAPI entrypoint
│   ├── config.py                     # Pydantic Settings
│   ├── domain/                       # Pydantic v2 models. No I/O.
│   │   ├── session.py
│   │   ├── questionnaire.py
│   │   ├── pain.py
│   │   ├── register.py
│   │   ├── module.py
│   │   ├── audit.py
│   │   ├── language.py               # StrEnum + LanguageTagged mixin
│   │   ├── brand_dna_context.py
│   │   ├── rationale.py
│   │   └── exceptions.py
│   ├── orchestration/                # Pure logic. No LLM. No I/O.
│   │   ├── engine.py                 # Decision Scope → ExecutionPlan
│   │   ├── suppression.py
│   │   └── intersections.py
│   ├── discovery/
│   │   ├── content_loader.py         # Loads + validates YAML at boot
│   │   ├── condition_evaluator.py
│   │   ├── rules_engine.py           # Pain tagging
│   │   └── register_resolver.py
│   ├── generation/                   # Module runners + narrative — LLM-backed
│   │   ├── registry.py               # ModuleConfig registry (5 modules)
│   │   ├── prompt_builder.py         # Jinja2 + StrictUndefined
│   │   ├── module_runner.py
│   │   ├── orchestrator.py           # GenerationResult / GenerationError
│   │   ├── upstream.py               # Builds upstream inputs per module
│   │   ├── narrative_generator.py    # Pain narrative (Discovery boundary)
│   │   └── exceptions.py
│   ├── llm/
│   │   ├── provider.py               # THE Provider Protocol — single chokepoint
│   │   └── mock.py                   # Deterministic Mock provider
│   ├── persistence/
│   │   ├── base.py
│   │   ├── models.py                 # SQLAlchemy 2.0 ORM
│   │   ├── session.py                # Async session management
│   │   ├── converters.py             # Domain ↔ ORM
│   │   └── repositories/
│   │       └── session_repository.py
│   ├── api/
│   │   └── routes/
│   └── observability/
│       └── audit.py                  # LLMCallRecord persistence
├── content/                          # Expert-authored. Versioned with Git tags.
│   ├── questionnaires/v1.0.0/        # questionnaire.{en,ar}.yaml
│   ├── pain_taxonomy.yaml
│   ├── pain_rules.yaml
│   ├── register_rules.yaml
│   └── prompts/
│       ├── unified_preamble.j2
│       ├── pain_narrative.j2
│       └── modules/                  # one per module — strategy_theme.j2, tone.j2, …
├── migrations/                       # Alembic
├── tests/
│   ├── unit/                         # Per-layer pure-logic tests
│   ├── integration/                  # Live Postgres + capstone E2E
│   └── orchestration/                # 31-combination tests
└── docs/
    ├── TDD.md                        # Technical Design Document v0.4
    ├── MVP_PLAN.md                   # What M1 ships, build order, stack decisions
    ├── M1_TODO.md                    # Concrete M1 task list
    └── METHODOLOGY.md                # Agency expert authoring surface
```

---

## Development guide

### Adding a domain model

1. Define the Pydantic model in `src/domain/<area>.py`. If it represents persisted content, inherit from `LanguageTagged` so it gets a required `language: Language` field (CLAUDE.md §2.4).
2. Add validation tests in `tests/unit/domain/` — at minimum one valid and one invalid payload.
3. If the model needs to be persisted, add the SQLAlchemy ORM model in `src/persistence/models.py`, write a converter pair in `src/persistence/converters.py`, and add a round-trip test in `tests/integration/`.
4. Generate a migration: `alembic revision --autogenerate -m "add <thing>"` — review the generated SQL before committing.

### Adding content (the expert's authoring surface)

Content is YAML and Jinja2 under `content/`. **Code does not embed expert content.** If you find yourself writing `pain_categories = [...]` in Python, stop — that belongs in `content/pain_taxonomy.yaml`.

1. Edit the relevant YAML file under `content/`.
2. Schema validation runs at app start (`src/discovery/content_loader.py`). Bad content fails loud and prevents boot.
3. For new pain rules, add fixture coverage in `tests/unit/discovery/test_rules_engine.py`.
4. Tag the content version: `git tag content-v1.1.0`. Code references content by tag.

### Adding a generation module

Don't, in M1 — the five modules are fixed. If you're writing a sixth module you've left M1 scope; see CLAUDE.md §6 and stop to ask.

For reference, the existing five live in:
- `src/generation/registry.py` — register the `ModuleConfig`
- `content/prompts/modules/<module>.j2` — Jinja2 template
- `src/domain/module.py` — output schema with `priority_factors_addressed: min_length=2` (CLAUDE.md §2.7)
- `tests/unit/generation/` — module-runner tests with the Mock provider

### Common Alembic operations

```bash
alembic upgrade head                       # apply all pending migrations
alembic downgrade -1                       # roll back one
alembic revision --autogenerate -m "..."   # generate a migration from model diffs
alembic current                            # show current revision
alembic history                            # show migration history
```

### Lint, format, type-check

```bash
ruff check .          # lint
ruff check . --fix    # autofix where safe
black .               # format
mypy src/             # type-check
```

CI runs ruff + black on every push. Don't fight the formatter.

### Stop-and-ask cases

CLAUDE.md §7 lists the situations where you must pause and ask the human rather than guess:

- A change would violate one of the §2 invariants.
- An LLM provider choice needs to be made (decided by the M1 bake-off, not by code).
- Required expert content is missing or empty.
- A new top-level directory or third-party dependency is needed.

It is always better to stop and ask than to guess. Guesses become technical debt; questions become clarity.

---

## Documentation map

| Document | Purpose |
|---|---|
| [`CLAUDE.md`](./CLAUDE.md) | **The project bible.** Architectural invariants (§2), conventions (§4), what's out of M1 scope (§6), stop-and-ask cases (§7). Read in full before changing code. |
| [`docs/TDD.md`](./docs/TDD.md) | Full Technical Design Document v0.4 — system architecture, logic model, data model, schemas. |
| [`docs/MVP_PLAN.md`](./docs/MVP_PLAN.md) | What M1 ships and excludes, build order, stack decisions, open questions. |
| [`docs/M1_TODO.md`](./docs/M1_TODO.md) | Concrete M1 task list. |
| [`docs/METHODOLOGY.md`](./docs/METHODOLOGY.md) | Agency expert's questionnaire methodology — the expert's authoring surface. |
| [`AUDIT_REPORT_V3.md`](./AUDIT_REPORT_V3.md) | **Current audit** (post-Session-7). Every CLAUDE.md invariant verified with file:line evidence, M1 scope-delivery status, technical debt, triage recommendations. |
| [`AUDIT_REPORT_V2.md`](./AUDIT_REPORT_V2.md) | Historical audit (end of Session 4, pre-migration). |
| [`AUDIT_REPORT.md`](./AUDIT_REPORT.md) | Historical audit (end of Session 1, scaffold-only). |

The `Brand_Decision_System_*.docx` and `Brand_Decision_System_Product_Detailing.pdf` at the repo root are the original product spec deliverables. They are reference material — `CLAUDE.md` and `docs/TDD.md` are the authoritative engineering documents.

---

## License

Proprietary. All rights reserved. Not for redistribution.

For contributing guidance, see CLAUDE.md §4 (conventions), §7 (stop-and-ask cases), §8 (working patterns), and §9 (the "three things" pre-commit check).
