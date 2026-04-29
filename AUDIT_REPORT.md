# AUDIT REPORT — 2026-04-28

## 1. Executive Summary

The repository contains the Session 1 scaffold and nothing more — a working FastAPI shell with a `/health` route, structured logging, Pydantic settings, an Alembic harness with no migrations, a single passing health test, and a CI workflow. Against M1's stated scope (questionnaire service, rules engine, register resolver, narrative generator, LLM provider abstraction, domain models, persistence, API surface, audit log, expert content), completion is in the **5–10%** range — every domain-bearing package is an empty `__init__.py`. The single biggest concern is that `docs/M1_TODO.md` is a 7-line stub with no concrete task list, so there is no canonical "what gets built next" document to anchor Session 2. **Recommendation: continue on this foundation.** What exists is small, clean, and correct for a scaffold; nothing here needs to be torn out.

## 2. File Inventory

### 2.1 Source tree (`src/`)

| PATH | LINES | PURPOSE | STATE |
|---|---|---|---|
| `src/__init__.py` | 0 | Top-level package marker | EMPTY |
| `src/main.py` | 60 | FastAPI app factory, structlog config, `/health` route, lifespan logging | COMPLETE |
| `src/config.py` | 28 | Pydantic `Settings` (APP_ENV / DATABASE_URL / LOG_LEVEL) + cached `get_settings()` | COMPLETE |
| `src/domain/__init__.py` | 0 | Reserves location for Pydantic v2 domain models per CLAUDE.md §3 | EMPTY |
| `src/orchestration/__init__.py` | 0 | Reserves location for `engine.py` / `suppression.py` / `intersections.py` | EMPTY |
| `src/discovery/__init__.py` | 0 | Reserves location for questionnaire service / rules engine / register resolver | EMPTY |
| `src/generation/__init__.py` | 0 | Reserves location for narrative generator + prompt builder | EMPTY |
| `src/generation/runners/__init__.py` | 0 | Reserves location for module runners | EMPTY |
| `src/llm/__init__.py` | 0 | Reserves location for `provider.py` (the §2.2 single chokepoint) | EMPTY |
| `src/persistence/__init__.py` | 0 | Reserves location for ORM models + DB session management | EMPTY |
| `src/persistence/repositories/__init__.py` | 0 | Reserves location for repository pattern | EMPTY |
| `src/api/__init__.py` | 0 | Reserves location for API package | EMPTY |
| `src/api/routes/__init__.py` | 0 | Reserves location for HTTP routes | EMPTY |
| `src/observability/__init__.py` | 0 | Reserves location for `audit.py` (LLMCallRecord persistence) | EMPTY |

### 2.2 Tests (`tests/`)

| PATH | LINES | PURPOSE | STATE |
|---|---|---|---|
| `tests/__init__.py` | 0 | Package marker | EMPTY |
| `tests/conftest.py` | 13 | `httpx.ASGITransport` `AsyncClient` fixture against `src.main.app` | COMPLETE |
| `tests/unit/__init__.py` | 0 | Package marker | EMPTY |
| `tests/unit/test_health.py` | 8 | Single async test asserting `/health` returns 200 + service identity | COMPLETE |
| `tests/integration/__init__.py` | 0 | Reserves location for integration tests (DB-backed) | EMPTY |
| `tests/orchestration/__init__.py` | 0 | Reserves location for the 31-combination tests per CLAUDE.md §4.3 | EMPTY |

### 2.3 Content (`content/`)

| PATH | LINES | PURPOSE | STATE |
|---|---|---|---|
| `content/.gitkeep` | 0 | Reserves expert-authored content root | EMPTY |
| `content/questionnaires/v1.0.0/.gitkeep` | 0 | Reserves the v1.0.0 questionnaire directory | EMPTY |
| `content/prompts/modules/.gitkeep` | 0 | Reserves per-module Jinja2 prompt directory | EMPTY |

### 2.4 Migrations (`migrations/`)

| PATH | LINES | PURPOSE | STATE |
|---|---|---|---|
| `migrations/env.py` | 68 | Async Alembic env; pulls URL from `src.config.get_settings()`; `target_metadata = None` | COMPLETE |
| `migrations/script.py.mako` | 26 | Migration template, modernized typing | COMPLETE |
| `migrations/versions/.gitkeep` | 0 | Reserves migration revisions directory | EMPTY |

### 2.5 Docs (`docs/`)

| PATH | LINES | PURPOSE | STATE |
|---|---|---|---|
| `docs/TDD.md` | 6 | Stub pointing at `Brand_Decision_System_TDD_v0.4 (1).docx` at repo root | STUBBED |
| `docs/MVP_PLAN.md` | 6 | Stub pointing at `Brand_Decision_System_MVP_Plan_v1.0.docx` at repo root | STUBBED |
| `docs/M1_TODO.md` | 7 | Stub stating "to be populated when M1 is fully scoped" | STUBBED |
| `docs/METHODOLOGY.md` | 11 | Stub stating it is filled in during M1 with the agency expert | STUBBED |

### 2.6 Configuration & root files

| PATH | LINES | PURPOSE | STATE |
|---|---|---|---|
| `CLAUDE.md` | 265 | Project bible — architectural invariants and scope boundaries | COMPLETE |
| `pyproject.toml` | 58 | Project metadata, deps, ruff/black/pytest configuration | COMPLETE |
| `alembic.ini` | 41 | Alembic configuration; `sqlalchemy.url` empty (set by env.py from settings) | COMPLETE |
| `docker-compose.yml` | 19 | Single Postgres 16-alpine service with healthcheck | COMPLETE |
| `.env.example` | 11 | Documented env vars (APP_ENV / DATABASE_URL / LOG_LEVEL) | COMPLETE |
| `.gitignore` | 44 | Python / venv / IDE / OS / coverage / caches | COMPLETE |
| `README.md` | 47 | Setup, run, test, lint instructions; pointer to CLAUDE.md and docs/ | COMPLETE |
| `.github/workflows/ci.yml` | 30 | One ubuntu-latest job: install → ruff → black --check → pytest on Python 3.11 | COMPLETE |

## 3. CLAUDE.md Invariant Check

Every invariant below comes back **CANNOT VERIFY** for the same root reason: every domain-bearing package (`src/orchestration`, `src/discovery`, `src/generation`, `src/llm`, `src/persistence`, `src/observability`, `src/domain`, `src/api/routes`) currently consists of a single empty `__init__.py`. There is no implementation to inspect for compliance, and there is no implementation that *violates* the invariants either — the scaffold is structurally consistent with all ten.

1. **2.1 Orchestration never calls the LLM** — VERDICT: **CANNOT VERIFY**. EVIDENCE: `src/orchestration/__init__.py` is 0 bytes; no `engine.py`, `suppression.py`, or `intersections.py` exists. No code imports any LLM SDK anywhere in `src/`.
2. **2.2 LLM Provider Abstraction is the single chokepoint** — VERDICT: **CANNOT VERIFY**. EVIDENCE: `src/llm/__init__.py` is 0 bytes; `provider.py` does not exist. No `import anthropic` / `import openai` / `import google.generativeai` appears anywhere under `src/`.
3. **2.3 Modules never call each other directly** — VERDICT: **CANNOT VERIFY**. EVIDENCE: `src/generation/runners/__init__.py` is 0 bytes; no runners exist.
4. **2.4 Language is data, not a mode** — VERDICT: **CANNOT VERIFY**. EVIDENCE: `src/domain/__init__.py` is 0 bytes; no Pydantic models exist with or without `language` fields. `migrations/env.py:25` sets `target_metadata = None`, confirming no ORM mapping is yet in place.
5. **2.5 Register is derived, not configured** — VERDICT: **CANNOT VERIFY**. EVIDENCE: `src/discovery/__init__.py` is 0 bytes; no `register_resolver.py` exists.
6. **2.6 Suppression is absolute** — VERDICT: **CANNOT VERIFY**. EVIDENCE: no orchestration code exists (see 2.1).
7. **2.7 Every generated output carries its rationale** — VERDICT: **CANNOT VERIFY**. EVIDENCE: no `ModuleOutput` or `Rationale` Pydantic models exist (`src/domain/__init__.py` empty).
8. **2.8 Every LLM call is audited** — VERDICT: **CANNOT VERIFY**. EVIDENCE: `src/observability/__init__.py` is 0 bytes; no `audit.py`, no `LLMCallRecord` model, and no LLM call sites that would produce audit records.
9. **2.9 Determinism boundaries** — VERDICT: **CANNOT VERIFY**. EVIDENCE: there is no logic in `src/orchestration/`, `src/discovery/`, or `src/generation/prompt_builder.py` to assess for determinism.
10. **2.10 Discovery → Decision → Generation phase order** — VERDICT: **CANNOT VERIFY**. EVIDENCE: no phase machinery, state model, or session lifecycle code exists.

The scaffold introduces no invariant violations. It is also too thin to confirm any invariant is held in practice — that confirmation lives in Session 2+ tests and code review.

## 4. M1 Scope Check

### 4.1 OUT-of-M1 items (CLAUDE.md §6)

Every out-of-scope item is correctly absent from the codebase:

- **Generation Module Runners (Strategy/Tone/Naming/Slogan/Tagline)** — `src/generation/runners/__init__.py:0` empty; no runners exist. COMPLIANT (not even stubbed yet, which is fine pre-M1).
- **N-best sampling** — no code anywhere. COMPLIANT.
- **PDF export** — no `reportlab` / `weasyprint` / similar dep in `pyproject.toml:13-24`. COMPLIANT.
- **Session resume UI flows** — no frontend in repo. COMPLIANT.
- **Multi-tenancy** — no tenant model. COMPLIANT.
- **Regeneration** — no regeneration endpoints or services. COMPLIANT.
- **Production-grade auth (SSO, MFA)** — none present. *Caveat:* `pyproject.toml:21-22` includes `python-jose[cryptography]` and `passlib[bcrypt]` as runtime deps; these are listed but unused. This is consistent with the "basic email+password is fine" allowance in §6, but the deps are present without any consuming code.
- **Layers 2–5 (Audience Intelligence, Competitive Context, Output Refinement, Decision Capture)** — no code. COMPLIANT.
- **Content authoring UI** — no UI. COMPLIANT.
- **Streaming output** — no `StreamingResponse` or SSE wiring. COMPLIANT.

### 4.2 IN-M1 items

`docs/M1_TODO.md:1-7` is a 7-line stub that names the M1 components only by reference: "questionnaire service, rules engine, register resolver, narrative generator, etc." There is no concrete checklist. Mapping the named components against the file inventory:

| M1 Component | Referenced In | Current State |
|---|---|---|
| Pydantic v2 domain models | CLAUDE.md §3 | NOT STARTED — `src/domain/__init__.py:0` empty |
| Questionnaire Service | CLAUDE.md §3, M1_TODO.md:5 | NOT STARTED — `src/discovery/__init__.py:0` empty |
| Rules Engine (pain tagging) | CLAUDE.md §2.5, §3 | NOT STARTED — `src/discovery/__init__.py:0` empty |
| Language Register Resolver | CLAUDE.md §2.5, §3 | NOT STARTED — `src/discovery/__init__.py:0` empty |
| LLM Provider Abstraction | CLAUDE.md §2.2, §3 | NOT STARTED — `src/llm/__init__.py:0` empty |
| Narrative Generator | CLAUDE.md §3 | NOT STARTED — `src/generation/__init__.py:0` empty |
| Session System Prompt builder | CLAUDE.md §3 | NOT STARTED — `src/generation/__init__.py:0` empty |
| Persistence (ORM models, repositories) | CLAUDE.md §3 | NOT STARTED — `src/persistence/__init__.py:0` empty; `migrations/env.py:25` `target_metadata = None` |
| Audit log (LLMCallRecord) | CLAUDE.md §2.8, §3 | NOT STARTED — `src/observability/__init__.py:0` empty |
| API routes (sessions, answers, modules) | CLAUDE.md §3 | NOT STARTED — `src/api/routes/__init__.py:0` empty; only `/health` exists at `src/main.py:53-55` |
| Content YAML (questionnaire, pain taxonomy, register rules, prompts) | CLAUDE.md §5 | NOT STARTED — `content/**/.gitkeep` only |
| Module Runner stubs | CLAUDE.md §6 | NOT STARTED — `src/generation/runners/__init__.py:0` empty |

The scaffold honors the directory layout in §3 down to the package level. Nothing inside those packages is built.

## 5. Architectural Concerns

1. **WHAT:** `docs/M1_TODO.md` is a stub with no concrete task list. **WHERE:** `docs/M1_TODO.md:1-7`. **WHY IT MATTERS:** Every future session will need to re-derive M1 priorities from CLAUDE.md and the `.docx` files. There is no canonical dependency-ordered roadmap, which means each Session-N kickoff will spend time re-planning rather than executing.

2. **WHAT:** The two source-of-truth design documents (TDD, MVP plan) live in repo root as `.docx` files; their `docs/*.md` counterparts are 6-line pointer stubs. Nothing inside the design is searchable by code-reading tools or visible in PR diffs. **WHERE:** `docs/TDD.md:1-6`, `docs/MVP_PLAN.md:1-6`, plus `Brand_Decision_System_TDD_v0.4 (1).docx` and `Brand_Decision_System_MVP_Plan_v1.0.docx` at repo root. **WHY IT MATTERS:** CLAUDE.md is the only consultable design source-of-truth right now. Any architectural decision documented in the TDD but not re-stated in CLAUDE.md is effectively invisible to a code-reading session.

3. **WHAT:** `docs/METHODOLOGY.md` is empty, but CLAUDE.md §7 explicitly gates code that needs methodology behind "stop and ask if not documented here." **WHERE:** `docs/METHODOLOGY.md:1-11`. **WHY IT MATTERS:** The Pain Taxonomy, the questionnaire content, and the register rules all depend on agency-expert methodology. Any session that touches Discovery will hit the §7 stop-and-ask gate and have nothing to read.

4. **WHAT:** `python-jose[cryptography]` and `passlib[bcrypt]` are declared as runtime dependencies but are not imported anywhere in `src/`. **WHERE:** `pyproject.toml:21-22`. **WHY IT MATTERS:** Either auth is in M1 scope (in which case the absence of code is a gap) or it is not (in which case the runtime deps are speculative and inflate the install footprint). CLAUDE.md §6 hints "basic email+password is fine" but does not commit to M1, so the present state is ambiguous.

5. **WHAT:** CLAUDE.md §5 mandates that "schema validation on content files happens at app start" with "loud failure" semantics, but no content loader, no Pydantic content schemas, and no app-start validation hook exist. **WHERE:** `src/main.py:46-57` (no content load in `create_app`); `content/**/.gitkeep` only. **WHY IT MATTERS:** Currently there is no content to validate, so this is latent rather than broken — but the wiring needs to land alongside the first authored YAML, otherwise the loud-fail invariant becomes "silent succeed" by default.

## 6. Code Quality Notes

1. `pyproject.toml:30` declares `pytest-cov` as a dev dependency but no `--cov` configuration is wired into `[tool.pytest.ini_options].addopts` (line 58 has `addopts = "-ra"` only). Coverage will not run by default.
2. `pyproject.toml:21-22` lists `python-jose` and `passlib` as runtime deps with no consuming code (also covered as concern #4).
3. `README.md:25` interleaves Linux (`source .venv/bin/activate`) and Windows (`.venv\Scripts\activate`) activation commands on a single line; will confuse a Windows reader expecting copy-paste fidelity.
4. `README.md:28` describes `alembic upgrade head` as exiting cleanly with no migrations, but this only holds when Postgres is already running. The line implies the command is independent of Docker state.
5. `src/main.py:11-15`, `src/config.py:8-12`, and `migrations/env.py:1-6` cite CLAUDE.md section numbers inside docstrings. Stable for now; brittle if CLAUDE.md sections are renumbered, since the references will silently rot.
6. `tests/conftest.py:9` uses bare `@pytest.fixture` on an `async def` fixture. Functional only because `pyproject.toml:56` sets `asyncio_mode = "auto"`; would break under `strict` mode. Worth knowing.

## 7. Triage Recommendations

Ordered DELETE → REWRITE → FIX → KEEP. There are no DELETEs and no REWRITEs.

| TARGET | VERDICT | REASON |
|---|---|---|
| `docs/M1_TODO.md` | FIX | Populate with the concrete dependency-ordered M1 task list; needed before Session 2 has a defensible plan |
| `docs/TDD.md` | FIX | Convert canonical `.docx` to in-repo markdown so design is searchable and diff-visible |
| `docs/MVP_PLAN.md` | FIX | Same — convert canonical `.docx` to in-repo markdown |
| `docs/METHODOLOGY.md` | FIX | Capture agency-expert methodology output as soon as it exists, ahead of Discovery work |
| `pyproject.toml:21-22` | FIX | Move `python-jose` / `passlib` to a deferred extra (e.g. `auth`) or drop until needed |
| `pyproject.toml:55-58` | FIX | Decide whether `pytest-cov` should be wired into `addopts`, or drop the dep |
| `README.md:25,28` | FIX | Split venv activation into OS-specific lines; clarify alembic step requires Postgres running |
| `src/main.py` | KEEP | FastAPI app shell is correct for scaffold; structlog and lifespan logging both honor §4.5 |
| `src/config.py` | KEEP | Pydantic Settings honors §4.6; cached `get_settings()` is conventional |
| `migrations/env.py` | KEEP | Async env, URL pulled from settings per §4.6, `target_metadata=None` is correct until ORM lands |
| `migrations/script.py.mako` | KEEP | Modernized template ready for first migration |
| `alembic.ini` | KEEP | URL deliberately empty so env.py owns the source-of-truth |
| `docker-compose.yml` | KEEP | Single Postgres service with healthcheck, matches dev `DATABASE_URL` |
| `.env.example` | KEEP | Three documented vars cover scaffold needs |
| `.gitignore` | KEEP | Standard Python coverage; no obvious gaps |
| `.github/workflows/ci.yml` | KEEP | Lint + format + test on the project's minimum Python version |
| `tests/conftest.py` | KEEP | Async client fixture is correct for in-process FastAPI testing |
| `tests/unit/test_health.py` | KEEP | Single asserting test, deterministic, no I/O |
| All `__init__.py` and `.gitkeep` markers | KEEP | Reserve the §3 layout; should not become non-empty until each package gains code |
| `CLAUDE.md` | KEEP | Project bible; the only consultable architecture document right now |

## 8. The One Question

If the human can only act on one thing from this report, that thing is: **populate `docs/M1_TODO.md` with a concrete dependency-ordered task list for M1** — every subsequent session will otherwise re-derive priorities from `CLAUDE.md` and the `.docx` specs, and that re-derivation is the highest-frequency tax this project will pay.

## 9. What I Could Not Audit

- I did not run `pytest`, so I cannot independently confirm `tests/unit/test_health.py` passes.
- I did not run `alembic current` or `alembic upgrade head`, so I cannot confirm `migrations/env.py` actually executes against a live Postgres or exits cleanly with no migrations.
- I did not run `uvicorn src.main:app`, so I cannot confirm the FastAPI lifespan emits `app.start` / `app.shutdown` log records as designed.
- I did not run `docker compose up -d`, so I cannot confirm the Postgres healthcheck transitions to `healthy`.
- The two `.docx` files at repo root (`Brand_Decision_System_TDD_v0.4 (1).docx`, `Brand_Decision_System_MVP_Plan_v1.0.docx`) and the PDF (`Brand_Decision_System_Product_Detailing.pdf`) were not text-readable through my tools in this session, so the architectural-rule baseline I used was CLAUDE.md alone. Anything in those documents that contradicts or extends CLAUDE.md is unaccounted for in this audit.
- I did not verify the GitHub Actions workflow syntax against the actual GitHub runner; static read only.
- I did not assess whether the scaffold's choice of dependencies (e.g. `structlog`, `python-jose`, `passlib`) is the right long-term call for the eventual auth and observability requirements; that assessment requires the MVP plan content I could not read.
