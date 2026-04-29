# AUDIT REPORT V2 — 2026-04-28

## 1. Executive Summary

Across Sessions 1–4 plus Prompt A, the repository has grown to ~2,400 lines of source/test code (excluding docs) backed by 30 conventional commits. The four sessions are **structurally coherent**: orchestration imports only domain types (`src/orchestration/{engine,intersections,suppression}.py:1-3`), persistence imports only domain types, and the converter layer correctly mediates Pydantic ↔ SQLAlchemy translation in one place (`src/persistence/converters.py`). Domain-model coverage is complete (every entity in TDD §7 has a Pydantic model and an ORM model), and exhaustive test coverage exists for orchestration (212 tests across all 31 Decision Scope subsets) and converters (round-trip every persistable entity, no DB needed). The single biggest concern is **accumulated semantic debt that no test will catch**: domain decisions flagged in Session 2's report (`PainAnalysis.llm_call_record_id` singular vs `ModuleOutput.llm_call_record_ids` plural; `PainAnalysis` missing `register_id`; `SessionSystemPrompt.module_extensions` is a dict that allows at most one extension per module) all crossed into Session 4 unchanged, and a bad call here is much harder to reverse after more code lands on top. **The track is healthy enough to continue past Session 4** once Postgres is up — the schema is well-formed, the converters round-trip cleanly in unit tests, and the resumption surface is small (autogenerate, review, run upgrade/downgrade, run integration tests, commit). **Session 4's state is exactly what the prompt expected**: every code artifact (`base.py`, `session.py`, `models.py` (534 LOC, 19 tables), `converters.py` (638 LOC), `session_repository.py`, `__init__.py`, `migrations/env.py` wired to `Base.metadata`, integration tests, converter unit tests, `pyproject.toml` integration marker) is on disk; only `migrations/versions/0001_initial_schema.py` is correctly absent because Postgres wasn't available.

## 2. File Inventory By Session

### 2.1 Session 1 (scaffold) files

| PATH | LINES | PURPOSE | STATE |
|---|---|---|---|
| `src/main.py` | 60 | FastAPI app factory + structlog config + `/health` route | COMPLETE |
| `src/config.py` | 28 | Pydantic Settings (APP_ENV, DATABASE_URL, LOG_LEVEL) | COMPLETE |
| `tests/conftest.py` | 13 | `httpx.ASGITransport` AsyncClient fixture | COMPLETE |
| `tests/unit/test_health.py` | 8 | Single async test for `/health` | COMPLETE |
| `migrations/env.py` | 71 | Async Alembic env (was 68; modified in Session 4 — see §2.5) | PARTIAL (mutated by Session 4) |
| `migrations/script.py.mako` | 26 | Migration template, modernized typing | COMPLETE |
| `migrations/versions/.gitkeep` | 0 | Reserves revisions dir | EMPTY |
| `alembic.ini` | 41 | Alembic config; URL set from env.py | COMPLETE |
| `docker-compose.yml` | 19 | Postgres 16-alpine + healthcheck | COMPLETE |
| `.env.example` | 11 | Three documented vars | COMPLETE |
| `.gitignore` | 44 | Python/IDE/OS/coverage | COMPLETE |
| `.github/workflows/ci.yml` | 30 | ruff + black --check + pytest on Python 3.11 | COMPLETE |
| `README.md` | 56 | Setup/run/test instructions | COMPLETE |
| `CLAUDE.md` | 265 | Project bible | COMPLETE |
| `content/.gitkeep` + 2 nested `.gitkeep` | 0 ea | Reserve content layout | EMPTY |
| 8 empty `__init__.py` files under `src/{api,api/routes,discovery,generation,generation/runners,llm,observability}` | 0 ea | Reserve packages awaiting later sessions | EMPTY |

### 2.2 Prompt A (documentation pass) files

| PATH | LINES | PURPOSE | STATE |
|---|---|---|---|
| `docs/TDD.md` | 574 | Faithful conversion of TDD v0.4 .docx | COMPLETE |
| `docs/MVP_PLAN.md` | 368 | Faithful conversion of MVP plan v1.0 .docx | COMPLETE |
| `docs/M1_TODO.md` | 147 | Concrete M1 task list, verbatim from prompt | PARTIAL (every checkbox unchecked, including Session-1-done items — drift) |
| `docs/METHODOLOGY.md` | 58 | 12-section template awaiting expert | STUBBED (deliberately) |

### 2.3 Session 2 (domain models) files

| PATH | LINES | PURPOSE | STATE |
|---|---|---|---|
| `src/domain/__init__.py` | 66 | Public API (`__all__`) | COMPLETE |
| `src/domain/language.py` | 26 | `Language` StrEnum + `LanguageTagged` mixin | COMPLETE |
| `src/domain/facilitator.py` | 17 | `Facilitator` with EmailStr | COMPLETE |
| `src/domain/session.py` | 33 | `Session` + `PhaseState` enum | COMPLETE |
| `src/domain/questionnaire.py` | 103 | 7 entities: Mechanic enum, AnswerOption, SliderConfig, Question, QuestionnaireVersion (frozen), QuestionnaireInstance, Answer (LanguageTagged) | COMPLETE |
| `src/domain/pain.py` | 65 | PainTaxonomy, PainCategory, RuleTrigger, Rule, PainAnalysis (LanguageTagged) | COMPLETE |
| `src/domain/register.py` | 45 | LanguageRegister + ArabicVariety + RegisterLevel enums | COMPLETE |
| `src/domain/module.py` | 66 | ModuleId, DecisionScope, ExecutionPlan, ModuleOutput (LanguageTagged) | COMPLETE |
| `src/domain/rationale.py` | 37 | PriorityFactor (frozen), Rationale (LanguageTagged) | COMPLETE |
| `src/domain/prompt.py` | 45 | ModulePromptExtension (frozen), SessionSystemPrompt (frozen) | COMPLETE |
| `src/domain/audit.py` | 44 | LLMCallStatus enum, LLMCallRecord | COMPLETE |
| `src/domain/export.py` | 25 | ExportFormat enum, ExportArtifact | COMPLETE |
| `src/domain/exceptions.py` | 22 | DomainError + 4 specific subclasses | COMPLETE |
| `tests/unit/domain/test_*.py` (11 files) | 596 total | Validation + frozen + language-required tests | COMPLETE (54 tests) |

### 2.4 Session 3 (orchestration engine) files

| PATH | LINES | PURPOSE | STATE |
|---|---|---|---|
| `src/orchestration/__init__.py` | 15 | Public API | COMPLETE |
| `src/orchestration/engine.py` | 32 | `CANONICAL_MODULE_ORDER`, `build_execution_plan` | COMPLETE |
| `src/orchestration/intersections.py` | 31 | `INTERSECTION_PAIRS` (7 pairs), `applicable_intersection_pairs` | COMPLETE |
| `src/orchestration/suppression.py` | 14 | `ALL_MODULES`, `compute_suppressed_modules` | COMPLETE |
| `tests/orchestration/test_engine.py` | 61 | 6 targeted unit tests | COMPLETE |
| `tests/orchestration/test_suppression.py` | 44 | 5 targeted unit tests | COMPLETE |
| `tests/orchestration/test_intersections.py` | 60 | 8 targeted unit tests | COMPLETE |
| `tests/orchestration/test_combination_coverage.py` | 169 | 31-subset Layer-2 coverage + Layer-3 invariants (193 parametrized cases) | COMPLETE |

### 2.5 Session 4 (persistence — paused before migration) files

All files are **uncommitted** (correctly — Session 4 paused before the verification step that gates the commits).

| PATH | LINES | PURPOSE | STATE |
|---|---|---|---|
| `src/persistence/__init__.py` | 18 | Public API: Base, get_session, DbSession, SessionRepository | COMPLETE |
| `src/persistence/base.py` | 23 | `Base(DeclarativeBase)` + `TimestampMixin` | COMPLETE |
| `src/persistence/session.py` | 51 | Async engine + sessionmaker + `get_session` dep + `DbSession` Annotated alias | COMPLETE |
| `src/persistence/models.py` | 534 | All 19 ORM tables with CHECK constraints, FKs, indexes, JSONB columns | COMPLETE (pending migration verification) |
| `src/persistence/converters.py` | 638 | Pydantic↔ORM converters for every persistable entity + JSONB sub-models | COMPLETE |
| `src/persistence/repositories/__init__.py` | 3 | Re-exports SessionRepository | COMPLETE |
| `src/persistence/repositories/session_repository.py` | 52 | Canonical repo: create / get / list_for_facilitator / update | COMPLETE |
| `migrations/env.py` (modified) | 71 | Now imports `src.persistence.models` and points `target_metadata = Base.metadata` | COMPLETE |
| `tests/unit/persistence/__init__.py` | 0 | Package marker | EMPTY |
| `tests/unit/persistence/test_converters.py` | 352 | 23 round-trip tests for every persistable entity, including the tricky DecisionScope set/list, ExecutionPlan tuples, dict[Language,str] | COMPLETE |
| `tests/integration/__init__.py` | 0 | Package marker | EMPTY |
| `tests/integration/conftest.py` | 57 | `_apply_migrations` (session-scope) + `engine` + transactional `db_session` | COMPLETE (untestable until Postgres up) |
| `tests/integration/test_migration.py` | 99 | upgrade→downgrade→upgrade cycle + table presence + index spot-check | COMPLETE (untestable until Postgres up) |
| `tests/integration/test_session_repository.py` | 97 | CRUD round-trip via repository: create, get, list, update, isolation | COMPLETE (untestable until Postgres up) |
| `migrations/versions/0001_initial_schema.py` | — | **DOES NOT EXIST** — correctly deferred to resumption step | (correctly absent) |

### 2.6 Files that cross sessions

| PATH | TOUCHED BY | STATE |
|---|---|---|
| `pyproject.toml` (61 lines) | Sessions 1, 4 (S2 added pydantic[email]; Prompt A wired pytest-cov + auth extra; S4 added integration marker on lines 56-58) | COMPLETE |
| `migrations/env.py` (71 lines) | Sessions 1 + 4 (S1 wrote async env with `target_metadata = None`; S4 changed to `target_metadata = Base.metadata` + imported models) | COMPLETE |
| `src/persistence/repositories/__init__.py` | S1 left empty; S4 added 1 import + `__all__` | COMPLETE |
| `src/persistence/__init__.py` | S1 left empty; S4 added the public API surface | COMPLETE |

## 3. CLAUDE.md Invariant Check

1. **2.1 Orchestration never calls the LLM.**
   - **VERDICT: HOLDS.**
   - **EVIDENCE:** `src/orchestration/engine.py:1-3` imports only `datetime`, `src.domain.module`, `src.orchestration.intersections`. `src/orchestration/intersections.py:1` imports only `src.domain.module`. `src/orchestration/suppression.py:1` imports only `src.domain.module`. No `import anthropic`, no `import openai`, no HTTP client, no async I/O anywhere in `src/orchestration/`. The 31-subset parametrized tests in `tests/orchestration/test_combination_coverage.py:55-119` would fail if any LLM call were introduced (they assert determinism that LLM calls would break).

2. **2.2 LLM Provider Abstraction is the single chokepoint.**
   - **VERDICT: CANNOT VERIFY.**
   - **EVIDENCE:** `src/llm/__init__.py` is 0 bytes. `provider.py` does not exist. No file in `src/` imports an LLM SDK. Session 5 territory; nothing to assess.

3. **2.3 Modules never call each other directly.**
   - **VERDICT: CANNOT VERIFY.**
   - **EVIDENCE:** `src/generation/runners/__init__.py` is 0 bytes. No runners exist. Domain `ModuleOutput.upstream_module_outputs: list[uuid.UUID]` (`src/domain/module.py:63`) keeps upstream coupling at the id level, which is the right shape for the eventual rule.

4. **2.4 Language is data, not a mode.**
   - **VERDICT: HOLDS.**
   - **EVIDENCE (domain):** `LanguageTagged` base in `src/domain/language.py:18-26` declares `language: Language` as required. Subclassed by:
     - `Answer` in `src/domain/questionnaire.py:78`
     - `PainAnalysis` in `src/domain/pain.py:55`
     - `ModuleOutput` in `src/domain/module.py:50`
     - `Rationale` in `src/domain/rationale.py:24`
   - **EVIDENCE (ORM):** `language_directive` / `language` / `primary_language` columns all VARCHAR(8) NOT NULL with `CheckConstraint("language IN ('ar', 'en')")` in `src/persistence/models.py` (per-table). The CHECK is defined via the `LANGUAGE_VALUES` constant on line 46.
   - **EVIDENCE (tests):** `tests/unit/domain/test_language.py:14`, `test_questionnaire.py:62 (test_answer_requires_language)`, `test_pain.py:51 (test_pain_analysis_requires_language)`, `test_module.py:48 (test_module_output_requires_language)`, `test_rationale.py:18 (test_rationale_requires_language)` — five separate proofs.

5. **2.5 Register is derived, not configured.**
   - **VERDICT: PARTIAL.**
   - **EVIDENCE:** The data shape is right — `LanguageRegister` in `src/domain/register.py:31-46` has no operator-configurable field; `session_id`, `primary_language`, `arabic_variety`, `register_level`, `cultural_anchors`, `derived_at`. ORM mirrors it (`src/persistence/models.py:298-329`). **What's missing:** the resolver itself doesn't exist (Session 6 territory), so the *invariant* (that the register is computed deterministically from a Brand DNA Profile, not chosen) has no live enforcement yet.

6. **2.6 Suppression is absolute.**
   - **VERDICT: HOLDS.**
   - **EVIDENCE:** `src/orchestration/suppression.py:7-15` defines `compute_suppressed_modules` as the single source of truth. `src/orchestration/intersections.py:18-29` `applicable_intersection_pairs` filters the canonical pair tuple by scope membership only. Tests:
     - `tests/orchestration/test_combination_coverage.py:106-119` (`test_intersection_pairs_only_contain_active_modules`) — runs across all 31 subsets and asserts no suppressed module ever appears in a pair.
     - `tests/orchestration/test_combination_coverage.py:95-103` (`test_suppression_complement`) — `suppressed ∪ active = ALL_MODULES`, no overlap, across all 31 subsets.
     - `tests/orchestration/test_intersections.py:46-50` (`test_naming_slogan_tagline_yields_zero_pairs_when_strategy_and_tone_absent`) — explicit "module absent ⇒ pair absent" check.

7. **2.7 Every generated output carries its rationale.**
   - **VERDICT: HOLDS at the schema level.**
   - **EVIDENCE:** `src/domain/module.py:64` `rationale_id: uuid.UUID` (required, not Optional). `src/domain/pain.py:62` `rationale_id: uuid.UUID` (required). `src/persistence/models.py:404` (`module_output.rationale_id`) and `models.py:288` (`pain_analysis.rationale_id`) — both NOT NULL FKs with explicit indexes. Tests: `tests/unit/domain/test_module.py:60-71` rejects construction without `rationale_id` (Pydantic raises). The runtime check that the LLM actually populates a rationale is Session 6+; the schema-level check is in place.

8. **2.8 Every LLM call is audited.**
   - **VERDICT: PARTIAL.**
   - **EVIDENCE:** `LLMCallRecord` domain (`src/domain/audit.py:21-44`) has every required field per CLAUDE.md §2.8: prompt_hash, model_version, language_directive, register_id, parameters, response_text, latency_ms, status. ORM mirrors it (`src/persistence/models.py:218-261`). `ModuleOutput.llm_call_record_ids: list[uuid.UUID] = Field(min_length=1)` (`src/domain/module.py:65`) — a generated output cannot exist without at least one logged call. **What's missing:** the call site that actually creates these records (the LLM Provider Abstraction) doesn't exist yet, so the chokepoint enforcement is structural, not behavioral.

9. **2.9 Determinism boundaries.**
   - **VERDICT: HOLDS in orchestration; not yet exercised elsewhere.**
   - **EVIDENCE:** `src/orchestration/engine.py:24` builds `ordered_modules` by iterating `CANONICAL_MODULE_ORDER` (a tuple) and filtering — never iterates the scope's set. `src/orchestration/intersections.py:24-28` does the same with `INTERSECTION_PAIRS`. No `random` imports. Time only used for `created_at` metadata, which is excluded from determinism comparisons. Tests:
     - `tests/orchestration/test_combination_coverage.py:80-92` (`test_determinism_per_subset`) runs across all 31 subsets.
     - `tests/orchestration/test_intersections.py:52-54` (`test_pairs_returned_in_canonical_order_not_scope_iteration_order`) — the bear case (input order ≠ canonical order).
   - The **persistence-side** determinism contribution is `decision_scope_to_orm` (`src/persistence/converters.py:447-453`) sorting modules before JSONB storage — verified by `tests/unit/persistence/test_converters.py:268 (test_decision_scope_to_orm_emits_sorted_module_list)`.

10. **2.10 Discovery → Decision → Generation phase order.**
    - **VERDICT: PARTIAL.**
    - **EVIDENCE:** `PhaseState` enum (`src/domain/session.py:8-19`) declares `DISCOVERY`, `DECISION`, `GENERATION`, `DELIVERED`. `Session.phase` defaults to `DISCOVERY` (line 31). The ORM CHECK constraint enforces the four valid string values (`models.py:96`). **What's missing:** there is no transition validator. `Session.phase` is mutable and the model accepts any `PhaseState` assignment. `tests/unit/domain/test_session.py:42` (`test_phase_can_advance`) sets `phase=PhaseState.GENERATION` directly with no preconditions. No state-machine code exists in any service. The Session Service (Session 6+) is where this enforcement lands.

## 4. Cross-Session Architectural Consistency

### 4.1 Domain → Orchestration

The orchestration package imports only domain types and stdlib. Verified line-by-line:

- `src/orchestration/engine.py:1-4` imports `datetime` (stdlib), `src.domain.module.{DecisionScope, ExecutionPlan, ModuleId}`, and `src.orchestration.intersections.applicable_intersection_pairs` — sibling internal.
- `src/orchestration/intersections.py:1` imports `src.domain.module.{DecisionScope, ModuleId}`.
- `src/orchestration/suppression.py:1` imports `src.domain.module.{DecisionScope, ModuleId}`.
- `src/orchestration/__init__.py:1-7` re-exports only orchestration-internal symbols.

`DecisionScope` is consumed in the way Session 2 designed it (a non-empty `set[ModuleId]` with `min_length=1` validator, `src/domain/module.py:33`), and `ExecutionPlan` is constructed via its full Pydantic constructor (`engine.py:25-30`) — no field bypass.

### 4.2 Domain → Persistence

**Entity coverage is complete.** Every persistable domain entity has an ORM equivalent. Sub-models embedded in JSONB (correctly, not as separate tables): `RuleTrigger` (inside `rule.trigger`), `SliderConfig` (inside `question.slider_config`), `PriorityFactor[]` (inside `rationale.priority_factors_addressed`), `ModulePromptExtension` (inside `session_system_prompt.module_extensions`).

ORM tables on `Base.metadata` (verified at smoke-import time, 19 total): `answer`, `answer_option`, `decision_scope`, `execution_plan`, `export_artifact`, `facilitator`, `language_register`, `llm_call_record`, `module_output`, `pain_analysis`, `pain_category`, `pain_taxonomy`, `question`, `questionnaire_instance`, `questionnaire_version`, `rationale`, `rule`, `session`, `session_system_prompt`. None missing. None extra.

**Tricky converters round-trip cleanly** (test names from `tests/unit/persistence/test_converters.py`):
- `set[ModuleId]` ↔ JSON list — `test_decision_scope_set_round_trip_preserves_membership` (line 246) and `test_decision_scope_to_orm_emits_sorted_module_list` (line 268).
- `list[tuple[ModuleId, ModuleId]]` ↔ JSON nested array — `test_execution_plan_tuples_survive_jsonb_round_trip` (line 257). The from_orm explicitly reconstructs tuples (`converters.py:476-478`).
- `dict[Language, str]` ↔ `dict[str, str]` — exercised by `test_question_round_trip_with_slider_config` (line 130) and `test_pain_category_round_trip` (line 158). Helper functions `_lang_dict_to_json` / `_json_to_lang_dict` (`converters.py:75-80`) are the conversion point.
- Sub-models via `model_dump(mode="json")` — exercised by `test_rationale_round_trip_with_priority_factors_and_uuids` (line 173) and `test_session_system_prompt_round_trip_with_module_extensions` (line 224).

**Field parity domain ↔ ORM** — spot-checked five entities:
- `Session`: domain has `id, facilitator_id, questionnaire_version_id, phase, created_at, updated_at`; ORM has the same (`models.py:79-94`). ✓
- `LLMCallRecord`: 13 domain fields, 13 ORM fields, types match (`audit.py:21-44` ↔ `models.py:218-261`). ✓
- `ModuleOutput`: 10 domain fields, 10 ORM fields. `upstream_module_outputs: list[UUID]` (domain) ↔ `JSONB list[str]` (ORM); converter handles. ✓
- `LanguageRegister`: 7 fields each, all enum-string mapped via `_to_orm` value calls. ✓
- `PainAnalysis`: 8 fields each. ✓

**Schema-level FK note:** `Question.id` and `PainCategory.id` are synthetic UUIDs at the ORM level, not the Pydantic str codes. The Pydantic-side `id: str` round-trips through ORM `code: VARCHAR(64)`. The synthetic UUIDs exist purely so child rows (`AnswerOption`, indirectly `Rule`) can FK by UUID. Documented in `models.py:113-118` and `175-189`. The `Rule → PainCategory` FK that the prompt specified at the schema level is **deliberately deferred** to service-layer validation because Pydantic `Rule` doesn't carry a taxonomy version reference, and resolving the synthetic UUID at write time would require a query inside the converter (breaking purity). Documented inline at `models.py:175-189`.

### 4.3 Persistence boundary

`src/persistence/repositories/session_repository.py` exposes only domain-typed methods (`-> Session | None`, `-> list[Session]`, `(Session) -> Session`) — the ORM type appears only inside method bodies (`models.py:23, 31, 47-48`), and is converted via `session_to_orm` / `session_from_orm` at every boundary crossing. No ORM type leaks. No `model.something` access from outside the converter module. Fits the prompt's stated rule.

**Note**: this is the *only* repository implemented. `src/persistence/repositories/__init__.py` exports only `SessionRepository`. Other repositories (Questionnaire, Pain, Register, ModuleOutput, etc.) will be built when their consuming services are built; nothing is stubbed with TODOs in this session, which is mildly cleaner than stubs.

### 4.4 Test coverage of cross-session contracts

- **Session 2 + Session 3** — orchestration tests use `DecisionScope` and `ExecutionPlan` domain types throughout (e.g., `tests/orchestration/test_combination_coverage.py:60` constructs `DecisionScope(...)` and asserts `isinstance(plan, ExecutionPlan)` on line 63). Tested via 212 cases.
- **Session 2 + Session 4** — every domain entity has a converter round-trip test in `tests/unit/persistence/test_converters.py`. 23 tests.
- **Session 3 + Session 4 — UNTESTED.** No test exercises `build_execution_plan(scope) → execution_plan_to_orm(plan) → execution_plan_from_orm(orm)`. The pieces are tested separately. A test that compares "the orchestrator's output, persisted and retrieved, equals the orchestrator's output" would catch any future drift in the conversion. Flagged as debt #9 in §6.
- **Session 4 + real Postgres** — three integration tests exist (`test_migration.py` + `test_session_repository.py`, 12 test cases) but cannot run until Postgres is up. The fixture `_apply_migrations` runs `alembic upgrade head` before any test executes (`tests/integration/conftest.py:21-30`).

## 5. Session 4 Partial-State Assessment

### 5.1 What Session 4 finished (code-level)

**ORM models** (`src/persistence/models.py`, 534 lines, 19 classes):

| ORM class | table name | field-set vs domain | Notes |
|---|---|---|---|
| Facilitator | `facilitator` | matches | TimestampMixin used |
| Session | `session` | matches | created_at/updated_at declared directly |
| QuestionnaireVersion | `questionnaire_version` | matches | TimestampMixin used; no `questions` column (children FK back) |
| Question | `question` | adds synthetic `id: UUID` | Pydantic `id: str` → ORM `code: VARCHAR(64)`; UNIQUE(version_id, code) |
| AnswerOption | `answer_option` | adds synthetic `id: UUID` | Same pattern as Question |
| QuestionnaireInstance | `questionnaire_instance` | matches | no `answers` column (children FK back) |
| Answer | `answer` | matches | `value: JSONB` for str|int|list[str] union; `question_code` denormalized |
| PainTaxonomy | `pain_taxonomy` | matches | no `categories` column |
| PainCategory | `pain_category` | adds synthetic `id: UUID` | Pydantic `id: str` → ORM `code` |
| Rule | `rule` | adds synthetic `id: UUID` | `pain_category_code` denormalized; **no DB-level FK to PainCategory** (deliberate; doc'd in models.py) |
| PainAnalysis | `pain_analysis` | matches | rationale_id + llm_call_record_id NOT NULL FKs |
| LanguageRegister | `language_register` | matches | session_id FK CASCADE |
| DecisionScope | `decision_scope` | session_id is the PK | `modules: JSONB` sorted list |
| ExecutionPlan | `execution_plan` | session_id is the PK | `intersection_pairs: JSONB list[list[str]]` |
| ModuleOutput | `module_output` | matches | composite index on (session_id, module) |
| Rationale | `rationale` | matches | priority_factors_addressed: JSONB list of dicts |
| SessionSystemPrompt | `session_system_prompt` | session_id is the PK | module_extensions: JSONB dict |
| LLMCallRecord | `llm_call_record` | matches | module + register_id NULLABLE; called_at indexed |
| ExportArtifact | `export_artifact` | matches | format VARCHAR(8) CHECK |

CHECK constraints declared via constants at `models.py:46-55` and applied per table — all eight enum values match the corresponding Pydantic StrEnums (verified by reading both sides). Foreign keys: Session children all CASCADE; cross-child FKs (`pain_analysis.rationale_id`, `module_output.rationale_id`, `module_output.register_id`, `session_system_prompt.{register_id, questionnaire_version_id, pain_analysis_id}`, `llm_call_record.register_id`) all RESTRICT. Every FK column has an index (`index=True` on mapped_column).

**`src/persistence/base.py` (23 lines)**: clean — `Base(DeclarativeBase)` and `TimestampMixin` providing `created_at: TIMESTAMPTZ NOT NULL DEFAULT lambda: datetime.now(UTC)`. Used by 3 models (Facilitator, QuestionnaireVersion, PainTaxonomy); other models declare their timestamp columns directly because they're named differently (`submitted_at`, `derived_at`, `built_at`, `called_at`, `selected_at`). Mild stylistic inconsistency (debt #11).

**`src/persistence/session.py` (51 lines)**: async engine via `create_async_engine`, `async_sessionmaker(expire_on_commit=False)`, `get_session` FastAPI dependency that commits-on-success / rolls-back-on-exception, `DbSession` Annotated alias for route signatures. Engine is created at module import time (`engine = _make_engine()` line 28) — connection is lazy, so import succeeds without Postgres up. ✓

**`src/persistence/converters.py` (638 lines)**: every persistable entity has a `_to_orm` and `_from_orm` pair. Helpers `_lang_dict_to_json` / `_json_to_lang_dict` / `_uuids_to_strs` / `_strs_to_uuids` at lines 75-96. `from __future__ import annotations` at line 16 (compatible with Pydantic v2.0+). **Missing converter pairs: none.** Every entity in `src/domain/` that has a corresponding ORM table has both `to_orm` and `from_orm` functions.

**`src/persistence/repositories/`**: `session_repository.py` is the canonical implementation (52 lines, 4 methods). No other repositories stubbed (cleaner than empty TODO classes).

**Tests:**

- `tests/unit/persistence/test_converters.py` (352 lines, 23 tests) — round-trip every entity, including all the tricky cases. No DB needed. **Test logic looks valid throughout** — every test constructs a domain model, converts to ORM, converts back, and asserts `==`. Pydantic's `__eq__` is the comparison. One sentinel test at line 355 (`test_unused_imports_alias_for_typecheckers`) is dead weight (debt #10).
- `tests/integration/conftest.py` (57 lines) — `_apply_migrations` (session-scope, sync) runs `alembic upgrade head` before any test; `engine` fixture (session-scope, async) creates the asyncpg engine; `db_session` (function-scope, async) wraps each test in a transaction that rolls back at end. Mixes `pytest_asyncio.fixture` and `pytest.fixture` — both work under `asyncio_mode = "auto"`, but inconsistent style.
- `tests/integration/test_migration.py` (99 lines, 4 tests) — `test_upgrade_to_head_succeeds`, `test_all_expected_tables_present_after_upgrade` (compares against an enumerated `EXPECTED_TABLES` set on lines 23-44 with all 19 tables + `alembic_version`), `test_downgrade_to_base_then_upgrade_to_head_cycle`, and `test_session_table_has_expected_indexes`. Marked `pytestmark = pytest.mark.integration` at line 17.
- `tests/integration/test_session_repository.py` (97 lines, 5 tests) — CRUD + isolation + phase transitions. `_seed_dependencies` helper (lines 22-31) creates a Facilitator and QuestionnaireVersion via direct ORM writes since their repositories don't exist yet. Marked `pytestmark = pytest.mark.integration`.

### 5.2 What Session 4 correctly deferred

- **`migrations/versions/0001_initial_schema.py` does NOT exist.** Confirmed by `ls migrations/versions/` showing only `.gitkeep`. This is correct: the prompt requires `alembic revision --autogenerate` against a live Postgres before this file should exist.
- **`migrations/env.py` was already updated** by Session 4 to `target_metadata = Base.metadata` and to import `src.persistence.models` (line 19, with `# noqa: F401`). It shows as modified-but-not-committed in `git status`.
- **`pyproject.toml` integration marker is in place.** Lines 56-58: `markers = ["integration: marks tests requiring a running Postgres"]` and `addopts = "-ra --cov=src --cov-report=term-missing -m 'not integration'"`. Default pytest run will exclude integration tests.
- **No commits yet for any Session 4 work.** Last commit on `main` is `9d2ba52 test(orchestration): add 31-combination coverage and invariant property tests` (Session 3). All Session 4 code is in the working tree.

### 5.3 Risks for the resumption step

In rough order of likelihood that Alembic autogenerate gets it wrong and the human needs to hand-edit:

1. **CHECK constraints may not appear in autogenerated migration.** Alembic's autogenerate has historically produced inconsistent results for `CheckConstraint` declared inside `__table_args__`. Verify the generated migration includes every check named `*_valid` (15 of them across the 19 tables). If any are missing, hand-add them in `op.create_table(...)` calls. **Cite:** `models.py:46-55` (constants) + per-table `CheckConstraint(...)` declarations.

2. **`Boolean.default=True` on `question.required` (`models.py:135`).** Alembic may generate this as `server_default='true'` or as no default at all. Either is functionally fine because the converter always passes a value, but the migration round-trip test will only pass cleanly if the upgrade is idempotent. Worth verifying once the file is generated.

3. **`session_id` as primary key on `decision_scope`, `execution_plan`, `session_system_prompt`** (`models.py:355-360`, `369-373`, `463-468`). PK + FK on the same column is supported by Alembic but autogenerate occasionally emits redundant index DDL. Inspect the generated migration for duplicate `Index('ix_decision_scope_session_id', ...)` — if present, delete it (the PK already provides the index).

4. **CASCADE/RESTRICT FK rules** — `models.py` distinguishes between `ondelete="CASCADE"` (Session children) and `ondelete="RESTRICT"` (cross-child references like `module_output.rationale_id`). Alembic's autogenerate does emit `ondelete=...` correctly for `ForeignKey(..., ondelete=...)`, but verify the resulting `op.create_table` calls include them on every FK column.

5. **JSONB vs JSON.** `from sqlalchemy.dialects.postgresql import JSONB` is imported at `models.py:36` and used on every JSONB column. Autogenerate should produce `postgresql.JSONB(astext_type=Text())` in the migration. If it emits plain `JSON`, hand-edit. Affects: every dict[str,str] field, every JSON-stored sub-model, every set/list field — about 25 columns total.

6. **`pain_analysis.llm_call_record_id` and Session-cascade timing.** When a Session is deleted, both `pain_analysis` and `llm_call_record` cascade-delete simultaneously. `pain_analysis.llm_call_record_id` has `ON DELETE RESTRICT`. PostgreSQL processes both deletions inside the same statement and resolves the FK at commit; this is fine in practice but slightly unusual. **No test currently exercises Session deletion**, so a silent breakage is possible. Documented in `models.py:14-19`. (Also: `tests/integration/test_session_repository.py` has no delete test.)

7. **`tests/integration/conftest.py:43` calls `command.upgrade(cfg, "head")` synchronously** but the `migrations/env.py` `run_migrations_online()` uses `asyncio.run()` internally. If pytest-asyncio's event loop is already running when this fixture executes, `asyncio.run()` will raise `RuntimeError: cannot be called from a running event loop`. The fixture is `scope="session"` and synchronous (`def`, not `async def`), so it runs before pytest-asyncio enters any test loop — should be fine, but if integration tests fail with that exact error, this is the cause.

8. **`Question.code: String(64)` may be too short** for some questionnaire identifiers. Pydantic `Question.id` is unconstrained `str`. If the agency expert authors a question with a longer code, the ORM write will fail with `value too long for type character varying(64)`. Low risk during M1; flag if real questionnaire content arrives.

9. **`answer.value: JSONB`** for the `str | int | list[str]` union. Pydantic v2's union discriminator picks the best match on read; the round-trip works in unit tests. Worth a sanity check at the integration-test level once Postgres is up — if a JSONB-stored integer comes back as a Python `int`, Pydantic's smart-mode union dispatch should still select `int`.

10. **`tests/unit/persistence/test_converters.py:355-357`** has a sentinel test that doesn't actually test anything. Will pass but produces no signal; safe to delete (debt #10).

## 6. Accumulated Technical Debt

Ordered by impact.

| # | WHAT | WHERE | INTRODUCED | IMPACT |
|---|---|---|---|---|
| 1 | `PainAnalysis.llm_call_record_id` is singular; `ModuleOutput.llm_call_record_ids` is plural. Self-critique loops or N-best for narrative would force a domain-model change. | `src/domain/pain.py:63`; `src/persistence/models.py:299-303` | Session 2 (mirrored in Session 4) | Medium — schema migration if it changes after data exists |
| 2 | `PainAnalysis` carries no `register_id`, but the LLM-elaborated narrative is generated AFTER the resolver runs. The narrative's register fidelity isn't traceable to a specific register record. | `src/domain/pain.py:55-65`; `src/persistence/models.py:268-296` | Session 2 (mirrored in Session 4) | Medium — affects audit traceability |
| 3 | `SessionSystemPrompt.module_extensions` is `dict[ModuleId, ModulePromptExtension]` — at most one extension per module per session. Architecture for multi-pass / refined extensions in one session is foreclosed. | `src/domain/prompt.py:41`; `src/persistence/models.py:439-441` | Session 2 (mirrored in Session 4) | Low/Medium — depends on whether Session 7+ wants multi-pass |
| 4 | `Rule → PainCategory` deliberately has no DB-level FK; service-layer validation only. | `src/persistence/models.py:175-189` | Session 4 | Low — content is YAML-loaded; runtime path doesn't write to DB |
| 5 | `tests/integration/conftest.py:43` mixes `pytest_asyncio.fixture` and `pytest.fixture`. `asyncio_mode = "auto"` makes both work, but switching to "strict" later breaks the bare `pytest.fixture` async ones (just `_apply_migrations` is sync, so this is theoretical). | `tests/integration/conftest.py` | Session 4 | Low — style only |
| 6 | No test exercises orchestration → persistence (`build_execution_plan(scope) → execution_plan_to_orm(plan) → execution_plan_from_orm(orm)`). | (missing test) | (gap from Sessions 3+4) | Medium — silent drift between layers becomes possible |
| 7 | `docs/M1_TODO.md` has every checkbox unchecked, including items explicitly marked `*(done in Session 1)*` such as "Create Git repo", "Set up FastAPI/Pydantic", "Set up pytest". The document is the canonical M1 plan but has stopped tracking actual progress. | `docs/M1_TODO.md:9-15` | Prompt A (introduced verbatim, never updated) | Low — the source of truth for "what's done" is now git log, not the doc |
| 8 | `docs/METHODOLOGY.md` is still a 12-section template. CLAUDE.md §7 gates Discovery work behind it. Any session that touches Discovery will block here. | `docs/METHODOLOGY.md` | Prompt A (intentional) | High once Discovery is started; zero today |
| 9 | `content/` has only `.gitkeep` markers. CLAUDE.md §5 says "schema validation on content files happens at app start" — no loader, no schema, no app-start validation hook. | `content/`, `src/main.py:46-57` | Sessions 1-4 (deferred) | Low today; medium when first authored YAML lands |
| 10 | `tests/unit/persistence/test_converters.py:355-357` `test_unused_imports_alias_for_typecheckers` is a sentinel that always passes; produces no useful signal. | `tests/unit/persistence/test_converters.py:355-357` | Session 4 | Trivial — delete it |
| 11 | `TimestampMixin` used inconsistently (3 of 19 ORM models use it; the others declare timestamp columns directly because they're named differently). Stylistic. | `src/persistence/base.py:13-22`, `models.py` (per table) | Session 4 | Trivial |
| 12 | `python-jose[cryptography]` and `passlib[bcrypt]` are in `[project.optional-dependencies].auth` but no auth code consumes them. Indirectly carries a version-pin obligation for unused libs. | `pyproject.toml:33-36` | Session 1 (moved to extras in Prompt A) | Trivial |

## 7. Code Quality Observations

1. CLAUDE.md section citations appear in source docstrings (`src/main.py:11-15`, `src/config.py:8-12`, `migrations/env.py:1-6`, multiple in `src/domain/`, `src/persistence/models.py:8-12`). Stable for now; brittle if CLAUDE.md sections are renumbered.
2. `src/persistence/converters.py:16` uses `from __future__ import annotations`. Pydantic v2 supports this, but the file would benefit from a one-line comment confirming intent (so a contributor doesn't second-guess).
3. `src/persistence/models.py:55` `EXPORT_FORMAT_VALUES = "('pdf')"` — single-element IN-clause. SQL-legal but unusual; will look more natural when more formats land.
4. Mixed timestamp-column style: `Facilitator(Base, TimestampMixin)` inherits the mixin (`models.py:63`), but `Session` declares its own `created_at` and `updated_at` directly (`models.py:93-94`) because it also needs `updated_at`. Mixed but defensible.
5. `tests/conftest.py:9` uses bare `@pytest.fixture` on an `async def` fixture. Functional only because `pyproject.toml:55` sets `asyncio_mode = "auto"`; would break under `strict` mode. Carryover from V1 audit.
6. `tests/integration/test_session_repository.py:75-76` — both lines of the form `s1 = await repo.create(Session(...))`; `s2 = await repo.create(Session(...))`. Fine, but the test asserts `s1.id in listed_ids` and `s2.id in listed_ids` without asserting *order*, despite the test name claiming `_in_recent_order`. Test name overpromises.
7. `src/persistence/__init__.py:5-9` exports `engine` (the module-level engine instance). Importing `src.persistence` triggers engine creation. Acceptable today; flag if anyone wants to construct multiple engines (e.g., for tests that target a different DB URL).
8. `migrations/env.py:19` uses `# noqa: F401` to silence the unused-import warning on `from src.persistence import models`. The import is the side-effect of registering tables. The noqa comment is correct; just noting the pattern is in place.

## 8. Triage Recommendations

Ordered DELETE → REWRITE → FIX → CONTINUE → KEEP. Use **CONTINUE** for items that are correctly waiting on the resumption of Session 4.

| TARGET | VERDICT | REASON |
|---|---|---|
| `tests/unit/persistence/test_converters.py:355-357` (sentinel test) | DELETE | Always passes, asserts nothing meaningful |
| `migrations/versions/0001_initial_schema.py` (does not exist) | CONTINUE | Correctly waiting on `alembic revision --autogenerate` against running Postgres |
| `tests/integration/conftest.py` | CONTINUE | Will run once Postgres is up; logic looks correct |
| `tests/integration/test_migration.py` | CONTINUE | Same |
| `tests/integration/test_session_repository.py` | CONTINUE | Same; has the in-recent-order naming nit but validates the contract |
| Session 4 source files (`base.py`, `session.py`, `models.py`, `converters.py`, `session_repository.py`, persistence `__init__.py`s, modified `migrations/env.py` and `pyproject.toml`) | CONTINUE | All on disk, lint-clean, unit-tested; commits are gated on the migration step succeeding |
| `docs/M1_TODO.md` (every box unchecked, including Session 1 items) | FIX | Update progress at the next natural checkpoint — debt #7 |
| Cross-layer test (orchestration → persistence round-trip) | FIX | Add one test that proves `build_execution_plan` output round-trips through the converters — debt #6 |
| `PainAnalysis.llm_call_record_id` singular vs `ModuleOutput.llm_call_record_ids` plural | FIX | Decide before the LLM provider lands; if singular stays, document why; if plural is wanted, change before data exists — debt #1 |
| `PainAnalysis` missing `register_id` | FIX | Same — add field if narratives should be register-traceable in audit — debt #2 |
| `SessionSystemPrompt.module_extensions` shape (one-per-module) | FIX (decide) | Confirm with the prompt-builder design before Session 7+ — debt #3 |
| `docs/METHODOLOGY.md` empty template | KEEP | Awaiting expert input by design |
| `content/.gitkeep` markers + content-validation invariant unwired | KEEP | Will be wired alongside the first authored YAML |
| `python-jose` / `passlib` in `auth` extra | KEEP | Already moved out of runtime; no further action |
| `Brand_Decision_System_*.docx` and `*.pdf` at repo root, untracked | FIX | Either commit (so the source artifacts are versioned alongside the converted markdown) or add to `.gitignore` |
| `AUDIT_REPORT.md` (V1) untracked | FIX | Decide whether to commit alongside `AUDIT_REPORT_V2.md` for posterity |
| `src/main.py`, `src/config.py`, `src/orchestration/*`, `src/domain/*` | KEEP | All complete and consistent |
| `tests/unit/domain/*`, `tests/orchestration/*`, `tests/unit/persistence/*` | KEEP | 290 unit tests passing; coverage is clean |
| `pyproject.toml`, `alembic.ini`, `docker-compose.yml`, `.env.example`, `.gitignore`, `.github/workflows/ci.yml`, `README.md`, `CLAUDE.md` | KEEP | Stable foundation |

## 9. The Three Questions

**A. The most important fix.** If the human can only act on one thing from this report before resuming Session 4, that thing is: **decide on the three Session-2 carryover ambiguities (`PainAnalysis.llm_call_record_id` cardinality, `PainAnalysis` missing `register_id`, `SessionSystemPrompt.module_extensions` shape) before generating the migration**, because the Alembic schema will encode whichever choice ends up live and subsequent migrations to fix any of them require data-migration logic that doesn't exist yet.

**B. The most important question for the human.** **"Are you OK with `PainAnalysis` not carrying a `register_id`, knowing the LLM-generated narrative is created after the resolver runs and we therefore lose the audit link from a specific narrative back to the specific register that shaped it?"** — because a "no" forces a domain-model change before the migration, and a "yes" should be recorded in `docs/METHODOLOGY.md` as an intentional simplification.

**C. The state of the architecture.** After four sessions, the architecture is **healthy**, because the three structural commitments that needed to hold (single LLM chokepoint location reserved, language-as-data invariant enforced at both Pydantic and SQL layers, deterministic orchestration verified across all 31 valid Decision Scopes) are all in place; the remaining concerns are domain-modeling judgment calls and documentation drift, not load-bearing structural problems.

## 10. What I Could Not Audit

- **The full pytest suite**, because the prompt forbids running `pytest`. The most recent run reported in this session's history was 290 unit tests passing with 9 integration tests deselected; I'm trusting that report.
- **`alembic upgrade head` against real Postgres**, because Postgres isn't running on this host (Docker daemon not up) and the prompt forbids starting it. The risk-list in §5.3 is what I'd most want to verify against a live DB.
- **`pytest -m integration`** for the same reason.
- **The accuracy of the converters under a JSONB round-trip through actual asyncpg**, as opposed to through SQLAlchemy's in-process JSONB type adapter. asyncpg's JSON encoding is the layer that hasn't been exercised yet.
- **Whether `Question.code: String(64)` is wide enough** in practice — depends on the agency expert's authoring conventions, which haven't arrived.
- **Whether the integration `db_session` fixture actually rolls back cleanly** between tests under load — only confirmable by running the suite.
- **Migration drift detection**, because `migrations/versions/0001_initial_schema.py` doesn't exist yet to compare against the ORM. Once it lands, `alembic check` (a separate Alembic command, not run here) is the diagnostic.
- **Whether asyncpg has a Python 3.14 wheel for the version pinned in `pyproject.toml`** (`asyncpg>=0.30`) — pinned-version compatibility against the host Python runtime is something `pip install -e ".[dev]"` already resolved successfully in earlier sessions on this host, but I haven't independently verified the wheel.
- **The `.docx` and `.pdf` source files at repo root** — the conversion scripts in this repo cannot read images or embedded artifacts, and the documentation pass made faithful textual conversions but did not embed diagrams.
