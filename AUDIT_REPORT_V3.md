# AUDIT REPORT V3 — 2026-04-30

## 1. Executive Summary

After 101 commits across 7 development sessions plus four bridge sessions, the Real-Time Brand Decision System's **M1 backend is feature-complete**: the full pipeline runs Discovery → Decision → Generation end-to-end against the Mock LLM provider, producing all five module outputs (Strategy Theme, Tone, Naming, Slogan, Tagline) with the audit chain intact across every module. **Completeness against M1 scope is roughly 80–85%** — every backend component named in `docs/M1_TODO.md` is delivered and tested, three concerns block declaring M1 done: (1) the frontend (deferred entirely; the M1_TODO had ~13 frontend tasks), (2) the real LLM provider adapter (the bake-off is unstarted; the `MockLLMProvider` is the only implementation), (3) the agency expert's content review pass (Arabic translations are machine-authored; pain rules and register rules need expert validation per CLAUDE.md §7's stop-and-ask gate). **The architecture has held**: every CLAUDE.md §2 invariant that V2 had to mark CANNOT VERIFY now has real implementation behind it, eight verdict HOLDS, two are PARTIAL with documented gaps, none are VIOLATED. **The single biggest concern** is that the `Rationale` model is generated as a `rationale_id` UUID by every module runner and the narrative generator, but no `Rationale` object is ever persisted — the persistence FK from `module_output.rationale_id` to `rationale.id` is currently RESTRICT on a row that doesn't exist, so the moment Session 8's persistence path tries to write a `ModuleOutput`, it'll fail until that gap is closed. **Recommendation: continue past Session 7 to Session 8** — the architecture is healthy, the test coverage is real (514 unit + 15 integration), and the rationale-persistence gap is well-scoped to Session 8's brief (the persistence layer that connects everything to the API).

## 2. File Inventory By Layer

### 2.1 `src/` — production source (4,051 LOC across 49 files)

#### `src/` root
| PATH | LINES | PURPOSE | STATE |
|---|---|---|---|
| `src/__init__.py` | 0 | Top-level package marker | EMPTY |
| `src/main.py` | 60 | FastAPI app factory, structlog config, `/health` route | COMPLETE |
| `src/config.py` | 28 | Pydantic Settings (APP_ENV, DATABASE_URL, LOG_LEVEL) | COMPLETE |

#### `src/domain/` — Pydantic models (16 files, ~1,084 LOC)
| PATH | LINES | PURPOSE | STATE |
|---|---|---|---|
| `__init__.py` | 102 | Public API; 53 exported symbols | COMPLETE |
| `language.py` | 35 | `Language` StrEnum + `LanguageTagged` mixin (with templates-rely-on-StrEnum doc-comment) | COMPLETE |
| `facilitator.py` | 17 | Facilitator (UUID + EmailStr + display_name) | COMPLETE |
| `session.py` | 33 | Session + `PhaseState` enum | COMPLETE |
| `questionnaire.py` | 115 | 7 entities including AnswerMechanic, Question, AnswerOption, SliderConfig (frozen), Answer (LanguageTagged), QuestionnaireInstance, QuestionnaireVersion | COMPLETE |
| `pain.py` | 73 | PainTaxonomy, PainCategory, RuleTrigger, Rule, PainAnalysis (LanguageTagged with `register_id` + `llm_call_record_ids: list[UUID]`) | COMPLETE |
| `register.py` | 45 | LanguageRegister + ArabicVariety + RegisterLevel enums | COMPLETE |
| `module.py` | 66 | ModuleId, DecisionScope, ExecutionPlan, ModuleOutput (LanguageTagged) | COMPLETE |
| `module_outputs.py` | 125 | StrategyThemeOutput, ToneOutput, NamingOutput, SloganOutput, TaglineOutput + sub-models (using canonical PriorityFactor) | COMPLETE |
| `narrative_output.py` | 21 | PainNarrativeOutput (LanguageTagged) | COMPLETE |
| `brand_dna_context.py` | 279 | BrandDNAContext + 5 sub-models + `build_brand_dna_context()` | COMPLETE |
| `rationale.py` | 37 | Rationale (LanguageTagged) + PriorityFactor (frozen) | COMPLETE |
| `audit.py` | 44 | LLMCallStatus enum, LLMCallRecord | COMPLETE |
| `prompt.py` | 45 | ModulePromptExtension (frozen), SessionSystemPrompt (frozen) | COMPLETE |
| `export.py` | 25 | ExportFormat enum, ExportArtifact | COMPLETE |
| `exceptions.py` | 22 | DomainError + 4 specific subclasses | COMPLETE |

#### `src/orchestration/` — pure-logic engine (4 files, 92 LOC)
| PATH | LINES | PURPOSE | STATE |
|---|---|---|---|
| `__init__.py` | 15 | Public API; 6 exports | COMPLETE |
| `engine.py` | 32 | `CANONICAL_MODULE_ORDER` + `build_execution_plan` | COMPLETE |
| `intersections.py` | 31 | `INTERSECTION_PAIRS` (the 7 pairs) + `applicable_intersection_pairs` | COMPLETE |
| `suppression.py` | 14 | `ALL_MODULES` + `compute_suppressed_modules` | COMPLETE |

#### `src/persistence/` — SQLAlchemy 2.0 async ORM (8 files, ~1,379 LOC)
| PATH | LINES | PURPOSE | STATE |
|---|---|---|---|
| `__init__.py` | 18 | Public API; 7 exports | COMPLETE |
| `base.py` | 23 | `Base(DeclarativeBase)` + `TimestampMixin` | COMPLETE |
| `session.py` | 51 | Async engine, `AsyncSessionLocal`, `get_session` FastAPI dep, `DbSession` alias | COMPLETE |
| `models.py` | 538 | All 19 ORM tables with CHECK constraints, FKs, indexes, JSONB columns | COMPLETE |
| `converters.py` | 646 | Domain ↔ ORM conversion for every persistable entity | COMPLETE |
| `repositories/__init__.py` | 6 | Re-exports SessionRepository + LLMCallRecordRepository | COMPLETE |
| `repositories/session_repository.py` | 52 | Canonical pattern: create / get / list_for_facilitator / update | COMPLETE |
| `repositories/llm_call_record_repository.py` | 45 | Audit record CRUD: create / get / list_for_session | COMPLETE |

#### `src/llm/` — LLM Provider Abstraction (5 files, 436 LOC)
| PATH | LINES | PURPOSE | STATE |
|---|---|---|---|
| `__init__.py` | 27 | Public API; 10 exports | COMPLETE |
| `provider.py` | 133 | `LLMProvider` Protocol + LLMCallRequest/Response/Parameters | COMPLETE |
| `mock.py` | 189 | MockLLMProvider with `register_response`, `inject_latency`, `inject_error`, audit on success and failure paths | COMPLETE |
| `models.py` | 24 | `ModelVersion` enum (MOCK_FIXED, MOCK_VARIABLE; real provider IDs deferred to bake-off) | COMPLETE |
| `exceptions.py` | 63 | LLMProviderError + LLMSchemaValidationError + LLMTimeoutError + LLMRateLimitError (each carries optional `call_record`) | COMPLETE |

#### `src/discovery/` — Discovery Service (7 files, 421 LOC)
| PATH | LINES | PURPOSE | STATE |
|---|---|---|---|
| `__init__.py` | 16 | Public API; 7 exports | COMPLETE |
| `loader.py` | 109 | `load_content_bundle()` with explicit `ContentLoadError` on every failure path | COMPLETE |
| `content_bundle.py` | 30 | ContentBundle (questionnaire_en/ar, pain_taxonomy, simple_rules, inferred_rules, register_rules) | COMPLETE |
| `condition_evaluator.py` | 75 | `evaluate_condition()` shared by Rules Engine + Register Resolver; operator dispatch with `all_of` / `any_of` recursion | COMPLETE |
| `rules_engine.py` | 55 | `tag_pain_categories()` — simple + inferred rules, dedup, canonical-order output | COMPLETE |
| `register_resolver.py` | 116 | `resolve_register()` — first-match-wins per section, cultural_anchors aggregation | COMPLETE |
| `exceptions.py` | 19 | DiscoveryError + ContentLoadError | COMPLETE |

#### `src/generation/` — Generation Service (9 files, 555 LOC)
| PATH | LINES | PURPOSE | STATE |
|---|---|---|---|
| `__init__.py` | 21 | Public API; 11 exports | COMPLETE |
| `narrative_generator.py` | 95 | `generate_pain_narrative()` — Discovery's only LLM consumer | COMPLETE |
| `registry.py` | 65 | `ModuleConfig` + `MODULE_REGISTRY` (5 entries) + `get_module_config` | COMPLETE |
| `prompt_builder.py` | 98 | `build_module_prompt()` — assembles unified preamble + module template + upstream | COMPLETE |
| `upstream.py` | 69 | `upstream_module_ids_for` (audit) + `build_upstream_outputs` (template — pre-fills None for un-completed) | COMPLETE |
| `module_runner.py` | 63 | `run_module()` — generic runner using registry + LLM provider chokepoint | COMPLETE |
| `orchestrator.py` | 99 | `run_generation()` walks ExecutionPlan; `GenerationResult` dataclass | COMPLETE |
| `exceptions.py` | 42 | GenerationError carries partial progress + call_records_so_far + original_exception | COMPLETE |
| `runners/__init__.py` | 0 | Reserved package marker (no per-module runner files; one generic in module_runner.py) | EMPTY (correctly) |

#### `src/observability/` and `src/api/` — placeholders
| PATH | LINES | PURPOSE | STATE |
|---|---|---|---|
| `src/observability/__init__.py` | 0 | Reserves location for `audit.py` (LLMCallRecord persistence) | EMPTY (Session 8 territory; persistence already in src/persistence/) |
| `src/api/__init__.py` | 0 | Reserves location for API package | EMPTY (Session 8) |
| `src/api/routes/__init__.py` | 0 | Reserves location for HTTP routes | EMPTY (Session 8) |

### 2.2 `tests/` — test suite (39 files, 311 tests)

| Directory | Test files | Test functions | Notes |
|---|---|---|---|
| `tests/unit/domain/` | 13 | 96 | Validation + frozen + language-required across 13 entity files including `test_brand_dna_context.py` |
| `tests/unit/discovery/` | 4 | 56 | Loader (incl. error paths via tmp_path), condition evaluator, rules engine, register resolver |
| `tests/unit/generation/` | 6 | 43 | Registry, upstream, prompt builder, module runner, orchestrator, narrative generator |
| `tests/unit/llm/` | 3 | 29 | Models, provider Protocol, MockLLMProvider |
| `tests/unit/persistence/` | 1 | 24 | Converter round-trips for every persistable entity |
| `tests/unit/content/` | 2 | 19 | YAML validates into Pydantic; templates render with synthetic context |
| `tests/unit/test_health.py` | 1 | 1 | Session 1's health endpoint test |
| `tests/orchestration/` | 4 | 28 | Engine, intersections, suppression, 31-combination coverage + invariants |
| `tests/integration/` | 5 | 15 | Migration up/down, SessionRepository, LLMCallRecordRepository, discovery end-to-end, **full session flow capstone** |

**Default `pytest -m "not integration"`: 514 tests pass in ~5s.**
**`pytest -m integration`: 15 tests pass in ~150s.**

### 2.3 `content/` — expert-authored YAML + Jinja2 (15 files)

```
content/
├── pain_taxonomy.yaml                              (10 categories, bilingual)
├── pain_rules.yaml                                 (13 simple rules + 2 inferred)
├── register_rules.yaml                             (4-section resolver DSL)
├── prompts/
│   ├── unified_preamble.j2                         (shared context block)
│   ├── pain_narrative.j2                           (standalone — for the narrative LLM call)
│   └── modules/
│       ├── strategy_theme.j2
│       ├── tone.j2
│       ├── naming.j2
│       ├── slogan.j2
│       └── tagline.j2
└── questionnaires/
    ├── v0.1.0/
    │   ├── questionnaire.en.yaml                   (22 questions, English-primary master)
    │   └── questionnaire.ar.yaml                   (22 questions, Arabic-primary master, machine-authored)
    └── v1.0.0/.gitkeep                             (reserved for the post-expert-review revision)
```

### 2.4 `migrations/` — Alembic

| PATH | PURPOSE | STATE |
|---|---|---|
| `migrations/env.py` | Async Alembic env wired to `Base.metadata`; URL pulled from `src.config.get_settings()` | COMPLETE |
| `migrations/script.py.mako` | Modernized template | COMPLETE |
| `migrations/versions/0001_initial_schema.py` | All 19 tables with CHECK constraints, JSONB columns, FK indexes, CASCADE/RESTRICT rules | COMPLETE |
| `migrations/versions/0002_add_question_constraints.py` | min_selections / max_selections / free_text_max_length on `question` table | COMPLETE |

### 2.5 `docs/` — design documents

| PATH | LINES | PURPOSE | STATE |
|---|---|---|---|
| `docs/TDD.md` | 574 | Full Technical Design Document v0.4, converted from .docx | COMPLETE |
| `docs/MVP_PLAN.md` | 368 | MVP plan v1.0, converted from .docx | COMPLETE |
| `docs/M1_TODO.md` | 147 | M1 task checklist | PARTIAL (every checkbox unchecked, including delivered work — drift) |
| `docs/METHODOLOGY.md` | 58 | 12-section template | STUBBED (awaiting agency expert per CLAUDE.md §7) |

### 2.6 Root configuration files

| PATH | LINES | PURPOSE | STATE |
|---|---|---|---|
| `CLAUDE.md` | 265 | Project bible — architectural invariants and conventions | COMPLETE |
| `pyproject.toml` | 58 | Project metadata, deps, ruff/black/pytest config (+ jinja2, pyyaml, pydantic[email] runtime deps) | COMPLETE |
| `alembic.ini` | 41 | Alembic config; URL pulled from env.py | COMPLETE |
| `docker-compose.yml` | 19 | Single Postgres 16-alpine service with healthcheck | COMPLETE |
| `.env.example` | 11 | Three documented vars (APP_ENV, DATABASE_URL, LOG_LEVEL) | COMPLETE |
| `.gitignore` | 47 | Python/IDE/OS/coverage + `.claude/` (added pre-push) | COMPLETE |
| `.github/workflows/ci.yml` | 30 | Lint + format + test on Python 3.11 | COMPLETE |
| `README.md` | 47 | **Stale Session-1 scaffold version** — replaced by V3 doc pass | OUTDATED (this audit's V3 README replaces it) |

### 2.7 Repo-root project artifacts

| PATH | SIZE | NOTES |
|---|---|---|
| `Brand_Decision_System_TDD_v0.4 (1).docx` | 573 KB | Source spec — `docs/TDD.md` was converted from this |
| `Brand_Decision_System_MVP_Plan_v1.0.docx` | 25 KB | Source spec — `docs/MVP_PLAN.md` was converted from this |
| `Brand_Decision_System_Product_Detailing.pdf` | 180 KB | Original product spec |
| `AUDIT_REPORT.md` | 18 KB | V1 audit (end of Session 1) |
| `AUDIT_REPORT_V2.md` | 45 KB | V2 audit (end of Session 4 paused state) |

## 3. CLAUDE.md Invariant Check

Eight HOLDS, two PARTIAL, none VIOLATED. The architecture has earned its keep across 101 commits.

1. **2.1 Orchestration never calls the LLM.**
   - **VERDICT: HOLDS.**
   - **EVIDENCE:** Three orchestration files import only stdlib + `src.domain.module`:
     - `src/orchestration/engine.py:1-4` — imports `datetime`, `src.domain.module`, `src.orchestration.intersections`
     - `src/orchestration/intersections.py:1` — imports `src.domain.module`
     - `src/orchestration/suppression.py:1` — imports `src.domain.module`
   - No `import anthropic`, no `import openai`, no HTTP client, no async I/O anywhere in `src/orchestration/`. Verified by repo-wide grep `grep -rE "import anthropic|import openai|google\.generativeai" src/` returning zero matches. The 31-combination parametrized tests in `tests/orchestration/test_combination_coverage.py:55-119` would fail if any LLM call were introduced (they assert determinism that LLM calls would break).

2. **2.2 LLM Provider Abstraction is the single chokepoint.**
   - **VERDICT: HOLDS.**
   - **EVIDENCE:** `src/llm/provider.py:1-133` defines the `LLMProvider` Protocol; `src/llm/mock.py` is the only implementation. Every consumer (the narrative generator at `src/generation/narrative_generator.py:60-66` and the module runner at `src/generation/module_runner.py:30-43`) constructs an `LLMCallRequest` and calls `llm_provider.call(request, output_schema)` — never imports an SDK directly. The repo-wide grep confirms zero SDK imports under `src/`. Tests: `tests/unit/llm/test_provider_protocol.py:test_stub_implementation_satisfies_protocol_structurally` proves the Protocol is structural; any future real adapter that conforms will plug in without touching the consumers.

3. **2.3 Modules never call each other directly.**
   - **VERDICT: HOLDS.**
   - **EVIDENCE:** No file under `src/generation/runners/` exists (the directory is an empty marker); there is one generic `run_module` in `src/generation/module_runner.py:21-58` that the orchestrator calls per-module. Upstream outputs flow into a module's prompt via `src/generation/prompt_builder.py:76-82` which unwraps `ModuleOutput.content` into the Jinja2 `upstream` dict — modules read prior outputs through the explicit feed, never via cross-module imports. `src/generation/orchestrator.py:62-89` is the sole mediator.

4. **2.4 Language is data, not a mode.**
   - **VERDICT: HOLDS.**
   - **EVIDENCE — domain layer:** `LanguageTagged` base in `src/domain/language.py:28-37` declares `language: Language` required. Subclassed by `Answer` (`questionnaire.py:78`), `PainAnalysis` (`pain.py:55`), `ModuleOutput` (`module.py:50`), `Rationale` (`rationale.py:24`), `PainNarrativeOutput` (`narrative_output.py:18`), and all 5 module outputs (`module_outputs.py`). Five validation tests prove the language requirement at boundary.
   - **EVIDENCE — ORM layer:** Every language column is `VARCHAR(8) NOT NULL` with a CHECK constraint via `LANGUAGE_VALUES = "('ar', 'en')"` constant (`src/persistence/models.py:46`).
   - **EVIDENCE — content layer:** Every YAML content object carries explicit language tagging — questionnaires keyed by `text_by_language: {ar: ..., en: ...}`, pain categories likewise.
   - **EVIDENCE — template layer:** `content/prompts/unified_preamble.j2` branches on `register.primary_language` for every block; the `Language` StrEnum's value-string equivalence is documented in `src/domain/language.py:6-13` so a future refactor doesn't silently break templates.

5. **2.5 Register is derived, not configured.**
   - **VERDICT: HOLDS.**
   - **EVIDENCE:** `src/discovery/register_resolver.py:24-49` is the deterministic resolver — walks `register_rules.yaml`'s 4 sections (primary_language / arabic_variety / register_level / cultural_anchors), first-match-wins per section. `LanguageRegister` (`src/domain/register.py:31-46`) has no operator-configurable field; the resolver is the only constructor in the project (verified by grep — no other code constructs a `LanguageRegister` outside tests). 16 tests in `tests/unit/discovery/test_register_resolver.py` cover Arabic-only / English-only / bilingual tie-breaker / formality bands / cultural anchors.

6. **2.6 Suppression is absolute.**
   - **VERDICT: HOLDS.**
   - **EVIDENCE:** `src/orchestration/suppression.py:7-15` is the single source of truth. `src/orchestration/intersections.py:18-29` `applicable_intersection_pairs` filters by scope membership; `src/generation/orchestrator.py:42` builds `scope_modules = set(execution_plan.ordered_modules)` and passes it through to every prompt-builder + audit-upstream call. The 31-combination parametrized tests in `tests/orchestration/test_combination_coverage.py:106-119` prove no suppressed module ever appears in any intersection pair, across all 31 valid Decision Scopes.

7. **2.7 Every generated output carries its rationale.**
   - **VERDICT: HOLDS at the schema level. PARTIAL at the persistence level (see Section 7 debt #1).**
   - **EVIDENCE — schema:** Every output schema's `priority_factors_addressed: list[PriorityFactor] = Field(..., min_length=2)` (e.g., `src/domain/module_outputs.py:29` for `StrategyThemeOutput`, same on Tone/Naming/Slogan/Tagline; `src/domain/narrative_output.py:18` for `PainNarrativeOutput`). `ModuleOutput.rationale_id: uuid.UUID` is required (`src/domain/module.py:64`). `PainAnalysis.rationale_id` required.
   - **EVIDENCE — runtime:** The module runner at `src/generation/module_runner.py:48` and the narrative generator at `src/generation/narrative_generator.py:74` generate fresh `rationale_id` UUIDs.
   - **GAP:** No `Rationale` object is ever persisted; the FK from `module_output.rationale_id` to `rationale.id` (RESTRICT) will fail when Session 8 attempts the first write. Documented in Section 7.

8. **2.8 Every LLM call is audited.**
   - **VERDICT: HOLDS.**
   - **EVIDENCE:** `src/llm/mock.py:84-105` builds an `LLMCallRecord` with all required fields on the success path; `src/llm/mock.py:131-168` `_raise_with_audit` builds one on the failure path and attaches it to the exception's `call_record` attribute. Every `LLMProviderError` subclass carries an optional `call_record` attribute (`src/llm/exceptions.py:25-30`). `src/generation/orchestrator.py:84-89` collects records into `call_records_so_far` even on exception. `src/persistence/repositories/llm_call_record_repository.py:23-40` provides the CRUD path for persisting them. `tests/integration/test_llm_call_record_repository.py` (4 tests) verifies the persistence path against live Postgres. The capstone test `tests/integration/test_full_session_flow.py:178` asserts `mock.call_count == 6` — narrative + 5 modules — and that every output has `len(llm_call_record_ids) == 1`.

9. **2.9 Determinism boundaries.**
   - **VERDICT: HOLDS for orchestration + register resolver + rules engine.**
   - **EVIDENCE — orchestration:** `src/orchestration/engine.py:24` builds `ordered_modules` by iterating `CANONICAL_MODULE_ORDER` (a tuple) and filtering — never iterates the scope's set. Same in `intersections.py:24-28`. No `random` imports anywhere under `src/`. Tests: `tests/orchestration/test_combination_coverage.py:80-92` `test_determinism_per_subset` covers all 31 subsets.
   - **EVIDENCE — discovery:** `src/discovery/rules_engine.py:34-52` iterates rule lists deterministically; `register_resolver.py:67-86` walks YAML-ordered conditions with first-match semantics. The resolver returns identical `LanguageRegister` directives for identical answer sets.
   - **EVIDENCE — persistence:** `src/persistence/converters.py:447-453` `decision_scope_to_orm` sorts modules before JSONB storage; verified by `tests/unit/persistence/test_converters.py:test_decision_scope_to_orm_emits_sorted_module_list`.

10. **2.10 Discovery → Decision → Generation phase order.**
    - **VERDICT: PARTIAL.**
    - **EVIDENCE:** `PhaseState` enum (`src/domain/session.py:8-19`) declares the four states. `Session.phase` defaults to `DISCOVERY` (line 31). The ORM CHECK constraint enforces the four valid string values (`models.py:96`).
    - **GAP:** No state-machine code enforces transitions. `Session.phase` is a mutable Pydantic field that accepts any `PhaseState` assignment. `tests/unit/domain/test_session.py:42` (`test_phase_can_advance`) sets `phase=PhaseState.GENERATION` directly with no preconditions. The `SessionRepository.update` method blindly persists whatever phase the caller passes. Phase-order enforcement is the Session Service's job — Session 8 territory.

## 4. Cross-Layer Architectural Consistency

### 4.1 Domain → Orchestration

`src/orchestration/{engine,intersections,suppression}.py` import only `src.domain.module` and stdlib. `DecisionScope` is consumed in the way Session 2 designed it (a non-empty `set[ModuleId]` with `min_length=1` validator); `ExecutionPlan` is constructed via its full Pydantic constructor — no field bypass, no monkey-patching.

### 4.2 Domain → Persistence

Every domain entity has an ORM equivalent. Sub-models embedded in JSONB (correctly, not as separate tables): `RuleTrigger`, `SliderConfig`, `PriorityFactor[]`, `ModulePromptExtension`. Repository methods accept and return domain models; `SessionRepository.create` and `LLMCallRecordRepository.create` both go through the converter functions (`session_to_orm`/`session_from_orm` and `llm_call_record_to_orm`/`llm_call_record_from_orm`). ORM types do not leak from public methods. The 24 converter round-trip tests in `tests/unit/persistence/test_converters.py` prove no information is lost across the JSONB / enum / UUID-string boundaries — including the hard cases (`set[ModuleId]` ↔ JSON list, `list[tuple]` ↔ JSON nested array, `dict[Language, str]` ↔ string-keyed dict, `list[UUID]` ↔ list[str]).

### 4.3 Domain → Discovery

`src/discovery/loader.py:65-90` validates every YAML through its corresponding Pydantic domain model and raises `ContentLoadError` on any failure (loud-fail per CLAUDE.md §5). `src/discovery/register_resolver.py:38-49` builds a fully-typed `LanguageRegister`. `src/discovery/rules_engine.py:32-52` returns `list[PainCategory]` — domain-typed.

### 4.4 Domain → Generation

`src/generation/module_runner.py:43-56` constructs a typed `ModuleOutput` with all 9 fields populated. `src/generation/orchestrator.py:64-89` propagates session_id, register_id, language across every output — verified by the capstone integration test's audit-chain assertions (`tests/integration/test_full_session_flow.py:178-211`).

### 4.5 Generation → LLM

The narrative generator and the module runner both go through the `LLMProvider` Protocol (`src/llm/provider.py:107-133`). Neither imports an SDK. `LLMCallRequest` is the typed contract. `LLMCallResponse[T]` carries the parsed Pydantic instance and the audit record.

### 4.6 Content → Domain

The content YAML files round-trip into their Pydantic domain models (verified by `tests/unit/content/test_content_validates.py` — 7 tests). The Jinja2 templates render with synthetic context under `StrictUndefined` (verified by `tests/unit/content/test_prompt_templates.py` — 12 tests across both languages and upstream-chain combinations).

### 4.7 Cross-session contracts

- **Session 2 + Session 3**: orchestration tests use domain types throughout (212 tests).
- **Session 2 + Session 4**: every domain entity has a converter round-trip test (24 tests).
- **Session 5 + Session 4**: `LLMCallRecordRepository` round-trip against live Postgres (4 integration tests).
- **Session 5 + Session 6**: `MockLLMProvider` is the only consumer in the discovery integration test.
- **Session 6 + Session 7**: the capstone full-session-flow test exercises all four discovery components plus all five generation components in one run, against the live Mock provider.

No regressions detected across 101 commits.

## 5. M1 Scope Delivery Status

Walking `docs/M1_TODO.md`'s checklist against what actually shipped.

| M1_TODO section | Status | Notes |
|---|---|---|
| **Setup** (8 tasks) | 7/8 ✅ delivered | Git repo, Python 3.11+ env, FastAPI/Pydantic v2, Postgres, SQLAlchemy 2.0 + Alembic, pytest, ruff+black all done in Session 1. Next.js front-end deferred to M2 per the original prompt. Schedule first session with the expert is the only undelivered task — agency-side. |
| **Bring PROTAGET to Table** (4 tasks) | 0/4 ❌ pending | Engineering hasn't pulled PROTAGET dimensions; this requires the agency expert / co-founder action. Captured as a §7 stop-and-ask gate per CLAUDE.md. |
| **With Expert** (11 tasks) | 0/11 ❌ pending | Knowledge sessions, expert-authored questionnaire, expert-authored pain taxonomy, expert-authored register rules, system prompt template signoff. **All blocked on the expert.** Engineering produced machine-authored v0.1 content (`content/questionnaires/v0.1.0/`) that explicitly says "machine-authored, pending native review" so the expert can react to a strawman rather than start from blank. |
| **Arabic Quality Diagnosis** (6 tasks) | 0/6 ❌ pending | Same — blocked on the expert review of PROTAGET sample outputs. |
| **LLM Provider Bake-off** (7 tasks) | 0/7 ❌ pending | The LLM Provider Abstraction (Session 5) is built and the `MockLLMProvider` is the only adapter today. Bake-off is a separate post-Session-7 effort. The architecture supports plugging in a real adapter without touching consumers. |
| **Domain Models** (7 tasks) | 7/7 ✅ delivered | All Pydantic models from Session 2 + Session 4 + Session 6 + Session 7 + bridges. 13 test files, 96 tests in `tests/unit/domain/`. |
| **Database** (3 tasks) | 3/3 ✅ delivered | Two Alembic migrations (`0001_initial_schema.py` for all 19 tables, `0002_add_question_constraints.py`); FK indexes on every FK column; the seed migration for the first QuestionnaireVersion is one item the YAML-loaded content currently sidesteps. Worth noting: `seed migration for first QuestionnaireVersion` is technically incomplete because v0.1.0 is loaded from YAML at app start (per CLAUDE.md §5) rather than seeded. The intent is satisfied. |
| **Orchestration** (4 tasks) | 4/4 ✅ delivered | Three-phase state machine stubs (PhaseState enum), `build_execution_plan` pure function, 31-combination parametrized tests, suppression-rule tests. Total 212 orchestration tests. |
| **Questionnaire Service** (5 tasks) | 1/5 partial | YAML loader done (`src/discovery/loader.py`); the API endpoints (fetch questionnaire, submit answer, complete Discovery) are Session 8 territory. |
| **Rules Engine (Pain Tagging)** (4 tasks) | 4/4 ✅ delivered | YAML rule DSL, loader with schema validation, evaluator (`tag_pain_categories`), 18 unit tests. |
| **Language Register Resolver** (2 tasks) | 2/2 ✅ delivered | Resolver function + 16 unit tests. |
| **LLM Layer** (5 tasks) | 4/5 delivered | Provider Abstraction interface, structured output configured, audit logging on every call, ModelVersion enum. The chosen-provider adapter is the one outstanding item (post-bake-off). |
| **Narrative Generator** (3 tasks) | 3/3 ✅ delivered | Generator function (`generate_pain_narrative`), 7 mocked unit tests, 1 integration test. |
| **Session System Prompt Builder** (6 tasks) | 4/6 partial | Unified preamble template, 5 per-module preamble extensions (Jinja2), prompt builder function, determinism implicit in StrictUndefined + canonical-order upstream filling. The "If diagnosis was (a) prompting: include explicit Arabic register/idiom instructions" is included — see `unified_preamble.j2`'s Arabic register block. The "inspection endpoint: view built prompt for a session" is Session 8 territory. |
| **Frontend** (9 tasks) | 0/9 ❌ pending | Deferred entirely to M2. |
| **Audit** (2 tasks) | 1/2 partial | Structured JSON logging is in place from Session 1 (`src/main.py:11-31`); the audit-trail inspection endpoint is Session 8 territory. The `LLMCallRecord` persistence path exists; only the API surface is missing. |
| **Exit Gate** (5 tasks) | 1/5 partial | All 31 orchestration tests pass ✅. The other four (real test brand through Discovery in Arabic / English with expert signoff, expert confirms Arabic quality improvement) require the agency expert. |

**Summary**: ~80–85% of the technical M1 scope is delivered. The pending items split into three categories:
- **Frontend** (M2)
- **Real LLM adapter** (post-bake-off)
- **Expert-authored content + signoff** (agency-side, not engineering-blocked)

## 6. End-to-End Verification State

`tests/integration/test_full_session_flow.py:124-211` is the capstone proving the whole stack works.

```
1. load_content_bundle()                  → ContentBundle (22 questions, 13+2 rules, 10 categories, 4 register sections)
2. tag_pain_categories(answers, ...)      → [PainCategory(obscurity), PainCategory(commoditization)]
3. resolve_register(answers, ...)         → LanguageRegister(primary=ENGLISH, anchors=[saudi_market_context, premium_positioning])
4. build_brand_dna_context(answers, ...)  → BrandDNAContext (5 typed sub-models)
5. generate_pain_narrative(...)           → (PainAnalysis, LLMCallRecord)
6. build_execution_plan(scope=all 5)      → ExecutionPlan in canonical order with 7 intersection pairs
7. run_generation(...)                    → GenerationResult(5 ModuleOutputs in canonical order, 5 LLMCallRecords)

Asserted invariants:
- mock.call_count == 6 (narrative + 5 modules)
- All 5 module outputs share session_id, register_id, language
- Every output has len(llm_call_record_ids) == 1
- Tagline.upstream_module_outputs == {Strategy.id, Tone.id} per intersection rules
- Tone.upstream_module_outputs == [Strategy.id]
- Each module's content round-trips back through its Pydantic schema
```

**The full backend pipeline runs end-to-end in 0.23 seconds against the Mock provider.** Once a real LLM adapter lands, the same test will run against it (probably ~3 minutes wall-time). The architecture is unchanged; only the provider implementation differs.

## 7. Accumulated Technical Debt

Twelve items, ordered by impact.

| # | Item | Where | Impact |
|---|---|---|---|
| 1 | **No `Rationale` is ever persisted.** Every `ModuleOutput` and `PainAnalysis` carries a fresh `rationale_id` UUID, but nothing writes a `Rationale` row. The FK `module_output.rationale_id → rationale.id` is RESTRICT. Session 8's first persistence write will fail. | `src/generation/module_runner.py:48`, `src/generation/narrative_generator.py:74`, `src/persistence/models.py:404` | **HIGH** — blocks Session 8's Day 1 |
| 2 | `docs/M1_TODO.md` checkboxes are entirely unchecked, including delivered work. | `docs/M1_TODO.md:9-15` and beyond | Medium — every contributor reads stale state |
| 3 | `docs/METHODOLOGY.md` is a 12-section template. CLAUDE.md §7 gates Discovery work behind it. | `docs/METHODOLOGY.md` | Medium — blocks expert-content review iteration |
| 4 | `Rule → PainCategory` has no DB-level FK. Service-layer validation only. | `src/persistence/models.py:175-189` | Low — content is YAML-loaded; runtime path doesn't write to DB |
| 5 | `inferred_rules` carry compound `all_of` triggers that don't round-trip into the domain `Rule` model. They sit in the YAML for the future evaluator. The Discovery rules engine handles them via a separate code path (`src/discovery/rules_engine.py:46-52`). | `content/pain_rules.yaml`, `src/discovery/rules_engine.py` | Low — doesn't break runtime; surfaces if the domain wants compound `RuleTrigger` |
| 6 | `SessionSystemPrompt.module_extensions` is `dict[ModuleId, ModulePromptExtension]` — at most one extension per module per session. Multi-pass / N-best is foreclosed. | `src/domain/prompt.py:41` | Low/Medium — relevant when N-best architecture (open question A10 in TDD §3.3) decides |
| 7 | `GenerationResult` is a frozen dataclass holding mutable `dict` and `list`. Dataclass-level immutability prevents reassignment, not mutation. | `src/generation/orchestrator.py:34-38` | Low — defensive; not currently exploited but cheap to fix |
| 8 | `Q1.1` is a single combined free-text field ("brand name? In one sentence, what does your brand do?"). `build_brand_dna_context` splits on first ". " heuristically. Gives awkward `brand.name` for users not following the convention. | `src/domain/brand_dna_context.py:160-170` | Low — Session 8's session-creation flow can override `brand.name` explicitly |
| 9 | Three large source artifacts (`Brand_Decision_System_TDD_v0.4 (1).docx`, `MVP_Plan_v1.0.docx`, `Product_Detailing.pdf` totaling ~778 KB) committed at repo root. | repo root | Low — they're versioned alongside the converted markdown; cost is git history size only |
| 10 | The capstone integration test (`test_full_session_flow.py`) is the only end-to-end assertion that registers Mock responses for ALL 6 schemas. A future test author who adds a 7th LLM call and forgets to register a response gets a `LLMSchemaValidationError` at runtime — fine, but adding a CI lint that walks all integration tests would catch it sooner. | `tests/integration/test_full_session_flow.py` | Low — current coverage works |
| 11 | `tests/unit/test_health.py:9` uses bare `@pytest.fixture` on an `async def` fixture. Functional only because `pyproject.toml:55` sets `asyncio_mode = "auto"`. Carryover from V1 audit. | `tests/conftest.py` | Trivial |
| 12 | No CI badge in README, no test-count badge, no coverage badge. | (the new README adds them) | Trivial |

## 8. Code Quality Observations

1. CLAUDE.md section citations appear in source docstrings (`src/main.py:11-15`, `src/config.py:8-12`, `migrations/env.py:1-6`, multiple in `src/domain/`, `src/persistence/models.py:8-12`, `src/generation/*`). Stable for now; brittle if CLAUDE.md sections are renumbered.
2. `pyproject.toml:30` has `pytest-cov` and coverage runs on every test invocation (`addopts = "-ra --cov=src --cov-report=term-missing -m 'not integration'"`). Current overall coverage: 95%.
3. `src/persistence/converters.py:16` uses `from __future__ import annotations` — Pydantic v2 supports this; documented inline.
4. `src/generation/upstream.py:53-69` `build_upstream_outputs` returns `dict[str, ModuleOutput | None]` — pre-fills None for un-completed slots so Jinja2 templates' defensive `{% if upstream.X %}` checks don't blow up under StrictUndefined. Counter-intuitive but documented in the docstring.
5. `src/llm/mock.py:131-168` `_raise_with_audit` is the failure-path audit-record builder. The pattern is: build the record, attach to exception, re-raise. Documented in the LLM exception hierarchy's docstring. The orchestrator (`src/generation/orchestrator.py:84-88`) uses `getattr(e, "call_record", None)` to collect failure records into `call_records_so_far`.
6. `tests/unit/generation/test_orchestrator.py:_SecondCallFails` — a custom `MockLLMProvider` subclass that fails on the 2nd call. Slightly clever but contained; comment-documented.
7. `src/domain/brand_dna_context.py:236-237` has explicit `_ = questionnaire.questions if questionnaire else None` and `_ = AnswerMechanic` to keep parameters/imports live for a future revision. Minor stylistic decision.
8. The `narrative_generator.py` lives in `src/generation/` (moved from `src/discovery/` in the Generation Boundary bridge) but raises `DiscoveryError` (the narrative is a Discovery-phase output even if produced by generation-shaped code). Documented inline.

## 9. Triage Recommendations

Decisive verdicts. Ordered DELETE → REWRITE → FIX → CONTINUE → KEEP.

| TARGET | VERDICT | REASON |
|---|---|---|
| **Rationale persistence gap (debt #1)** | **FIX** (Session 8 priority 1) | The first persistence write fails without it; the LLM output already carries the priority-factor data needed |
| `docs/M1_TODO.md` checkboxes (debt #2) | FIX (cheap) | Update progress to reflect the 7 sessions of delivered work |
| `docs/METHODOLOGY.md` empty template (debt #3) | KEEP | Awaiting agency expert per CLAUDE.md §7 — engineering shouldn't fill in |
| `GenerationResult` mutability (debt #7) | FIX | Cheap defensive switch to `MappingProxyType` or tuple of pairs |
| `Q1.1` brand-name parsing (debt #8) | KEEP | Pragmatic for v0.1; Session 8's session-creation can override |
| Compound `inferred_rules` DSL (debt #5) | KEEP | Functional; the cleanup is worth doing only when the domain wants compound `RuleTrigger` |
| `SessionSystemPrompt.module_extensions` shape (debt #6) | KEEP | Decide post-A10 (N-best architecture decision in TDD §3.3) |
| Three source-spec binaries at repo root (debt #9) | KEEP | Useful for diff-against-original when expert deliverables update |
| Source code (`src/domain/*`, `src/orchestration/*`, `src/persistence/*`, `src/llm/*`, `src/discovery/*`, `src/generation/*`) | KEEP | All complete, all consistent across 101 commits |
| Tests (514 unit + 15 integration) | KEEP | 95% coverage, multiple-layer assertion patterns, no flaky tests |
| `pyproject.toml`, `alembic.ini`, `docker-compose.yml`, `.env.example`, `.gitignore`, `.github/workflows/ci.yml`, `CLAUDE.md`, `migrations/env.py`, both migration files | KEEP | Stable foundation |
| **README.md** | REPLACE | The 47-line scaffold version is structurally inadequate for what's now in the repo — replaced by this audit's V3 doc pass |

## 10. The Three Questions

**A. The most important fix.** If the human can only act on one thing from this report before Session 8, that thing is: **build a `RationaleRepository` and have the module runner + narrative generator persist a `Rationale` (constructed from the LLM output's `priority_factors_addressed` block) before the calling code persists the `ModuleOutput` / `PainAnalysis` that references it.** The data is already in the LLM response; the FK requires the row to exist; nothing in the current path writes it. This is Session 8's Day 1 work.

**B. The most important question for the human.** **"Is the architecture-of-LLM-calls right? Specifically: should the orchestrator parallelize independent module runs (e.g., Strategy and Naming have no formal dependency in some scopes), or stay serial?"** A real LLM call is 30s–3min wall-time; serial-of-5 is 2.5–15 minutes, parallel-where-possible could halve that. The current serial implementation is correct and simple but may bite when the bake-off picks a real provider and live latency arrives.

**C. The state of the architecture.** After 7 sessions and 101 commits, the architecture is **healthy and consistent** — the three structural commitments that needed to hold (single LLM chokepoint, language-as-data invariant, deterministic orchestration verified across all 31 valid Decision Scopes) are all in place; the integration capstone test proves end-to-end composition works; no invariants are violated; eight of ten are HOLDS, two are PARTIAL with documented Session 8 paths. The remaining concerns are well-scoped (rationale persistence, frontend, expert-content review, real LLM adapter) and none of them require structural changes to what's been built.

## 11. What I Could Not Audit

- **The full pytest suite at the moment of writing this audit**, because the prompt forbids running tests inside an audit. The most recent in-conversation run reported 514 unit + 15 integration passing; I'm trusting that report.
- **Whether the integration tests still pass against the live Postgres at audit time** — same reason. The user can verify with `pytest -m integration`.
- **Real LLM behavior** — no real provider adapter exists. The `MockLLMProvider` is the only implementation. Whether Anthropic / Gemini / GPT-class models actually produce well-formed JSON matching the schemas under structured-output mode is the bake-off's question, not this audit's.
- **Arabic output quality** — the YAML translations are machine-authored, the Arabic Jinja2 templates are machine-authored, no native-speaker review has happened. CLAUDE.md §2.4 is held at the schema level; output quality is a future concern.
- **Whether the agency expert agrees with the v0.1 strawman content** — `content/pain_taxonomy.yaml` (10 categories), `content/pain_rules.yaml` (13 simple + 2 inferred), `content/register_rules.yaml`, and the v0.1.0 questionnaire are all engineering-authored placeholders waiting for the expert pass.
- **Production database behavior at scale** — Postgres tested with single-row inserts and small queries; no load testing.
- **Whether the GitHub Actions CI workflow is actually green on the current `main`** — the workflow runs on push and PR per `.github/workflows/ci.yml`; can be checked at https://github.com/MazharZiadeh/brand-decision-system/actions.
- **The two `.docx` and one `.pdf` source spec files at repo root** — text-readable through pandoc/python-docx but the audit doesn't re-validate that `docs/TDD.md` and `docs/MVP_PLAN.md` still match those originals after any subsequent expert updates. The conversion was done in Prompt A; subsequent updates to the `.docx` would silently diverge from the markdown.
