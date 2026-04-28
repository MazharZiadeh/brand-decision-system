"""SQLAlchemy 2.0 typed declarative ORM models for every persistable entity.

These are storage-layer types. They are NOT the canonical domain types — those
live in src/domain/ as Pydantic v2 models. The src/persistence/converters.py
module is the single boundary where the two layers meet; repositories accept
and return domain models, never ORM rows.

CHECK constraints back-stop the enum values (Language, PhaseState, ModuleId,
AnswerMechanic, ArabicVariety, RegisterLevel, LLMCallStatus, ExportFormat).
The Pydantic layer is the primary enforcement; the constraint is the database's
own safety net per CLAUDE.md §4.4 ("boundaries validate; internals trust"
applies to in-process code, not to external storage).

Foreign-key strategy: children of `session` cascade-delete with their parent.
Cross-child FKs (e.g., pain_analysis.llm_call_record_id, module_output.
rationale_id) are NO ACTION; the API layer never exposes direct deletion of
those entities, and a Session-level delete reaches them transitively. The
trade-off is documented in this session's report.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.persistence.base import Base, TimestampMixin

# ---------------------------------------------------------------------------
# CHECK-constraint expressions for enum-typed string columns
# ---------------------------------------------------------------------------

LANGUAGE_VALUES = "('ar', 'en')"
PHASE_VALUES = "('discovery', 'decision', 'generation', 'delivered')"
MODULE_VALUES = "('strategy_theme', 'tone', 'naming', 'slogan', 'tagline')"
ANSWER_MECHANIC_VALUES = (
    "('slider', 'single_choice', 'multi_choice', 'free_text', 'ranking', 'branching')"
)
ARABIC_VARIETY_VALUES = "('msa', 'saudi_dialect', 'not_applicable')"
REGISTER_LEVEL_VALUES = "('formal', 'semi_formal', 'casual')"
LLM_CALL_STATUS_VALUES = "('success', 'error', 'timeout')"
EXPORT_FORMAT_VALUES = "('pdf')"


# ---------------------------------------------------------------------------
# Facilitator
# ---------------------------------------------------------------------------


class Facilitator(Base, TimestampMixin):
    __tablename__ = "facilitator"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)


# ---------------------------------------------------------------------------
# Session and its children
# ---------------------------------------------------------------------------


class Session(Base):
    __tablename__ = "session"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    facilitator_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("facilitator.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    questionnaire_version_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("questionnaire_version.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    phase: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

    __table_args__ = (CheckConstraint(f"phase IN {PHASE_VALUES}", name="session_phase_valid"),)


# ---------------------------------------------------------------------------
# QuestionnaireVersion → Question → AnswerOption
# ---------------------------------------------------------------------------


class QuestionnaireVersion(Base, TimestampMixin):
    __tablename__ = "questionnaire_version"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class Question(Base):
    """One question inside a QuestionnaireVersion.

    `code` is the Pydantic-side stable identifier ("q1.1"). It is unique within
    a version but not globally — multiple versions may carry the same code.
    The synthetic `id` UUID is the FK target for child rows.
    """

    __tablename__ = "question"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    questionnaire_version_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("questionnaire_version.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    section: Mapped[str] = mapped_column(String(64), nullable=False)
    text_by_language: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)
    mechanic: Mapped[str] = mapped_column(String(32), nullable=False)
    slider_config: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    branching_rule: Mapped[str | None] = mapped_column(Text, nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint(
            "questionnaire_version_id", "code", name="question_code_unique_per_version"
        ),
        CheckConstraint(f"mechanic IN {ANSWER_MECHANIC_VALUES}", name="question_mechanic_valid"),
    )


class AnswerOption(Base):
    __tablename__ = "answer_option"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    question_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("question.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    value: Mapped[str] = mapped_column(String(64), nullable=False)
    label_by_language: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        UniqueConstraint("question_id", "value", name="answer_option_value_unique_per_question"),
    )


# ---------------------------------------------------------------------------
# QuestionnaireInstance → Answer
# ---------------------------------------------------------------------------


class QuestionnaireInstance(Base):
    __tablename__ = "questionnaire_instance"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    questionnaire_version_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("questionnaire_version.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)


class Answer(Base):
    """A captured response. `value` is JSONB because the Pydantic union is
    `str | int | list[str]`, all JSON-native. `question_code` is denormalized
    from Question and intentionally not a DB-level FK: Answer doesn't carry
    `questionnaire_version_id` directly, so the consistency invariant
    (Answer's question lives in the same version as the parent
    QuestionnaireInstance) is enforced by the Questionnaire Service, not by SQL.
    """

    __tablename__ = "answer"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    questionnaire_instance_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("questionnaire_instance.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_code: Mapped[str] = mapped_column(String(64), nullable=False)
    language: Mapped[str] = mapped_column(String(8), nullable=False)
    value: Mapped[Any] = mapped_column(JSONB, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(f"language IN {LANGUAGE_VALUES}", name="answer_language_valid"),
    )


# ---------------------------------------------------------------------------
# PainTaxonomy → PainCategory + Rule
# ---------------------------------------------------------------------------


class PainTaxonomy(Base, TimestampMixin):
    __tablename__ = "pain_taxonomy"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False)


class PainCategory(Base):
    __tablename__ = "pain_category"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    pain_taxonomy_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("pain_taxonomy.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name_by_language: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)
    description_by_language: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)
    example_by_language: Mapped[dict[str, str] | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint("pain_taxonomy_id", "code", name="pain_category_code_unique_per_taxonomy"),
    )


class Rule(Base):
    """Pain-tagging rule.

    `pain_category_code` is denormalized; the Pydantic Rule.pain_category_id
    is a string code (e.g., "obscurity") and Rule has no taxonomy version
    reference, so we cannot resolve a synthetic FK to PainCategory at write
    time without an extra query. The Rules Engine validates against the
    active PainTaxonomy at evaluation time. Documented in the session report.
    """

    __tablename__ = "rule"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    pain_category_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    trigger: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


# ---------------------------------------------------------------------------
# Rationale (referenced by PainAnalysis and ModuleOutput)
# ---------------------------------------------------------------------------


class Rationale(Base):
    __tablename__ = "rationale"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    language: Mapped[str] = mapped_column(String(8), nullable=False)
    priority_factors_addressed: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    narrative: Mapped[str] = mapped_column(Text, nullable=False)
    upstream_inputs_referenced: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(f"language IN {LANGUAGE_VALUES}", name="rationale_language_valid"),
    )


# ---------------------------------------------------------------------------
# LLMCallRecord (referenced by PainAnalysis and ModuleOutput)
# ---------------------------------------------------------------------------


class LLMCallRecord(Base):
    __tablename__ = "llm_call_record"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    module: Mapped[str | None] = mapped_column(String(32), nullable=True)
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    language_directive: Mapped[str] = mapped_column(String(8), nullable=False)
    register_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("language_register.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    called_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(
            f"module IS NULL OR module IN {MODULE_VALUES}",
            name="llm_call_record_module_valid",
        ),
        CheckConstraint(
            f"language_directive IN {LANGUAGE_VALUES}",
            name="llm_call_record_language_valid",
        ),
        CheckConstraint(f"status IN {LLM_CALL_STATUS_VALUES}", name="llm_call_record_status_valid"),
        Index("ix_llm_call_record_called_at", "called_at"),
    )


# ---------------------------------------------------------------------------
# PainAnalysis (FK to Rationale + LLMCallRecord)
# ---------------------------------------------------------------------------


class PainAnalysis(Base):
    __tablename__ = "pain_analysis"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tagged_pain_categories: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    narrative: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(8), nullable=False)
    register_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("language_register.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    rationale_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rationale.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    llm_call_record_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(f"language IN {LANGUAGE_VALUES}", name="pain_analysis_language_valid"),
    )


# ---------------------------------------------------------------------------
# LanguageRegister
# ---------------------------------------------------------------------------


class LanguageRegister(Base):
    __tablename__ = "language_register"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    primary_language: Mapped[str] = mapped_column(String(8), nullable=False)
    arabic_variety: Mapped[str] = mapped_column(String(32), nullable=False)
    register_level: Mapped[str] = mapped_column(String(16), nullable=False)
    cultural_anchors: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    derived_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(
            f"primary_language IN {LANGUAGE_VALUES}",
            name="language_register_primary_valid",
        ),
        CheckConstraint(
            f"arabic_variety IN {ARABIC_VARIETY_VALUES}",
            name="language_register_arabic_variety_valid",
        ),
        CheckConstraint(
            f"register_level IN {REGISTER_LEVEL_VALUES}",
            name="language_register_level_valid",
        ),
    )


# ---------------------------------------------------------------------------
# DecisionScope and ExecutionPlan (one per session, session_id is the PK)
# ---------------------------------------------------------------------------


class DecisionScope(Base):
    __tablename__ = "decision_scope"

    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("session.id", ondelete="CASCADE"),
        primary_key=True,
    )
    modules: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    selected_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)


class ExecutionPlan(Base):
    __tablename__ = "execution_plan"

    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("session.id", ondelete="CASCADE"),
        primary_key=True,
    )
    ordered_modules: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    intersection_pairs: Mapped[list[list[str]]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)


# ---------------------------------------------------------------------------
# ModuleOutput
# ---------------------------------------------------------------------------


class ModuleOutput(Base):
    __tablename__ = "module_output"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    module: Mapped[str] = mapped_column(String(32), nullable=False)
    language: Mapped[str] = mapped_column(String(8), nullable=False)
    register_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("language_register.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    upstream_module_outputs: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    rationale_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rationale.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    llm_call_record_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(f"module IN {MODULE_VALUES}", name="module_output_module_valid"),
        CheckConstraint(f"language IN {LANGUAGE_VALUES}", name="module_output_language_valid"),
        Index("ix_module_output_session_module", "session_id", "module"),
    )


# ---------------------------------------------------------------------------
# SessionSystemPrompt (one per session)
# ---------------------------------------------------------------------------


class SessionSystemPrompt(Base):
    __tablename__ = "session_system_prompt"

    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("session.id", ondelete="CASCADE"),
        primary_key=True,
    )
    unified_preamble: Mapped[str] = mapped_column(Text, nullable=False)
    module_extensions: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    register_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("language_register.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    questionnaire_version_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("questionnaire_version.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    pain_analysis_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("pain_analysis.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    built_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)


# ---------------------------------------------------------------------------
# ExportArtifact
# ---------------------------------------------------------------------------


class ExportArtifact(Base):
    __tablename__ = "export_artifact"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    format: Mapped[str] = mapped_column(String(8), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    included_artifacts_manifest: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(f"format IN {EXPORT_FORMAT_VALUES}", name="export_artifact_format_valid"),
    )
