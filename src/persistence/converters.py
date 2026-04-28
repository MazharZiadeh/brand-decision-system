"""Domain ↔ ORM conversion functions.

This module is the ONLY place Pydantic ↔ SQLAlchemy translation lives.
Repositories use these functions; they do not access ORM fields directly.

Each persistable entity gets a `<entity>_to_orm` and `<entity>_from_orm`
function. For child entities that need a parent's foreign key (Question
needs questionnaire_version_id; AnswerOption needs question_id), the FK is
passed as a keyword-only argument.

Sub-models embedded as JSONB (RuleTrigger, SliderConfig, PriorityFactor,
ModulePromptExtension) are serialized via `model.model_dump(mode='json')`
on write and `SubModel.model_validate(...)` on read.
"""

from __future__ import annotations

import uuid

from src.domain.audit import LLMCallRecord, LLMCallStatus
from src.domain.export import ExportArtifact, ExportFormat
from src.domain.facilitator import Facilitator
from src.domain.language import Language
from src.domain.module import (
    DecisionScope,
    ExecutionPlan,
    ModuleId,
    ModuleOutput,
)
from src.domain.pain import (
    PainAnalysis,
    PainCategory,
    PainTaxonomy,
    Rule,
    RuleTrigger,
)
from src.domain.prompt import ModulePromptExtension, SessionSystemPrompt
from src.domain.questionnaire import (
    Answer,
    AnswerMechanic,
    AnswerOption,
    Question,
    QuestionnaireInstance,
    QuestionnaireVersion,
    SliderConfig,
)
from src.domain.rationale import PriorityFactor, Rationale
from src.domain.register import ArabicVariety, LanguageRegister, RegisterLevel
from src.domain.session import PhaseState, Session
from src.persistence.models import Answer as AnswerORM
from src.persistence.models import AnswerOption as AnswerOptionORM
from src.persistence.models import DecisionScope as DecisionScopeORM
from src.persistence.models import ExecutionPlan as ExecutionPlanORM
from src.persistence.models import ExportArtifact as ExportArtifactORM
from src.persistence.models import Facilitator as FacilitatorORM
from src.persistence.models import LanguageRegister as LanguageRegisterORM
from src.persistence.models import LLMCallRecord as LLMCallRecordORM
from src.persistence.models import ModuleOutput as ModuleOutputORM
from src.persistence.models import PainAnalysis as PainAnalysisORM
from src.persistence.models import PainCategory as PainCategoryORM
from src.persistence.models import PainTaxonomy as PainTaxonomyORM
from src.persistence.models import Question as QuestionORM
from src.persistence.models import QuestionnaireInstance as QuestionnaireInstanceORM
from src.persistence.models import QuestionnaireVersion as QuestionnaireVersionORM
from src.persistence.models import Rationale as RationaleORM
from src.persistence.models import Rule as RuleORM
from src.persistence.models import Session as SessionORM
from src.persistence.models import SessionSystemPrompt as SessionSystemPromptORM

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _lang_dict_to_json(d: dict[Language, str]) -> dict[str, str]:
    return {lang.value: text for lang, text in d.items()}


def _json_to_lang_dict(d: dict[str, str]) -> dict[Language, str]:
    return {Language(k): v for k, v in d.items()}


def _opt_lang_dict_to_json(d: dict[Language, str] | None) -> dict[str, str] | None:
    return _lang_dict_to_json(d) if d is not None else None


def _opt_json_to_lang_dict(d: dict[str, str] | None) -> dict[Language, str] | None:
    return _json_to_lang_dict(d) if d is not None else None


def _uuids_to_strs(ids: list[uuid.UUID]) -> list[str]:
    return [str(i) for i in ids]


def _strs_to_uuids(strs: list[str]) -> list[uuid.UUID]:
    return [uuid.UUID(s) for s in strs]


# ---------------------------------------------------------------------------
# Facilitator
# ---------------------------------------------------------------------------


def facilitator_to_orm(domain: Facilitator) -> FacilitatorORM:
    return FacilitatorORM(
        id=domain.id,
        email=domain.email,
        display_name=domain.display_name,
        created_at=domain.created_at,
    )


def facilitator_from_orm(orm: FacilitatorORM) -> Facilitator:
    return Facilitator(
        id=orm.id,
        email=orm.email,
        display_name=orm.display_name,
        created_at=orm.created_at,
    )


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


def session_to_orm(domain: Session) -> SessionORM:
    return SessionORM(
        id=domain.id,
        facilitator_id=domain.facilitator_id,
        questionnaire_version_id=domain.questionnaire_version_id,
        phase=domain.phase.value,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )


def session_from_orm(orm: SessionORM) -> Session:
    return Session(
        id=orm.id,
        facilitator_id=orm.facilitator_id,
        questionnaire_version_id=orm.questionnaire_version_id,
        phase=PhaseState(orm.phase),
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


# ---------------------------------------------------------------------------
# QuestionnaireVersion (top level only — its child Questions/AnswerOptions
# are converted separately by the repository)
# ---------------------------------------------------------------------------


def questionnaire_version_to_orm(domain: QuestionnaireVersion) -> QuestionnaireVersionORM:
    return QuestionnaireVersionORM(
        id=domain.id,
        version=domain.version,
        content_hash=domain.content_hash,
        created_at=domain.created_at,
    )


def questionnaire_version_from_orm(orm: QuestionnaireVersionORM) -> QuestionnaireVersion:
    # `questions` are loaded separately and re-attached at the repository layer.
    return QuestionnaireVersion(
        id=orm.id,
        version=orm.version,
        content_hash=orm.content_hash,
        questions=[],
        created_at=orm.created_at,
    )


def question_to_orm(
    domain: Question,
    *,
    questionnaire_version_id: uuid.UUID,
    orm_id: uuid.UUID | None = None,
) -> QuestionORM:
    """Convert a domain Question to ORM. The synthetic ORM PK is generated
    here unless explicitly supplied (for round-trip tests that need stable IDs).
    """
    return QuestionORM(
        id=orm_id or uuid.uuid4(),
        questionnaire_version_id=questionnaire_version_id,
        code=domain.id,
        section=domain.section,
        text_by_language=_lang_dict_to_json(domain.text_by_language),
        mechanic=domain.mechanic.value,
        slider_config=(
            domain.slider_config.model_dump(mode="json")
            if domain.slider_config is not None
            else None
        ),
        branching_rule=domain.branching_rule,
        required=domain.required,
    )


def question_from_orm(
    orm: QuestionORM,
    *,
    options: list[AnswerOption] | None = None,
) -> Question:
    return Question(
        id=orm.code,
        section=orm.section,
        text_by_language=_json_to_lang_dict(orm.text_by_language),
        mechanic=AnswerMechanic(orm.mechanic),
        options=options,
        slider_config=(
            SliderConfig.model_validate(orm.slider_config)
            if orm.slider_config is not None
            else None
        ),
        branching_rule=orm.branching_rule,
        required=orm.required,
    )


def answer_option_to_orm(
    domain: AnswerOption,
    *,
    question_id: uuid.UUID,
    orm_id: uuid.UUID | None = None,
) -> AnswerOptionORM:
    return AnswerOptionORM(
        id=orm_id or uuid.uuid4(),
        question_id=question_id,
        value=domain.value,
        label_by_language=_lang_dict_to_json(domain.label_by_language),
    )


def answer_option_from_orm(orm: AnswerOptionORM) -> AnswerOption:
    return AnswerOption(
        value=orm.value,
        label_by_language=_json_to_lang_dict(orm.label_by_language),
    )


# ---------------------------------------------------------------------------
# QuestionnaireInstance + Answer
# ---------------------------------------------------------------------------


def questionnaire_instance_to_orm(domain: QuestionnaireInstance) -> QuestionnaireInstanceORM:
    return QuestionnaireInstanceORM(
        id=domain.id,
        session_id=domain.session_id,
        questionnaire_version_id=domain.questionnaire_version_id,
        completed_at=domain.completed_at,
    )


def questionnaire_instance_from_orm(
    orm: QuestionnaireInstanceORM,
    *,
    answers: list[Answer] | None = None,
) -> QuestionnaireInstance:
    return QuestionnaireInstance(
        id=orm.id,
        session_id=orm.session_id,
        questionnaire_version_id=orm.questionnaire_version_id,
        answers=answers or [],
        completed_at=orm.completed_at,
    )


def answer_to_orm(
    domain: Answer,
    *,
    questionnaire_instance_id: uuid.UUID,
) -> AnswerORM:
    return AnswerORM(
        id=domain.id,
        questionnaire_instance_id=questionnaire_instance_id,
        question_code=domain.question_id,
        language=domain.language.value,
        value=domain.value,
        submitted_at=domain.submitted_at,
    )


def answer_from_orm(orm: AnswerORM) -> Answer:
    return Answer(
        id=orm.id,
        question_id=orm.question_code,
        language=Language(orm.language),
        value=orm.value,
        submitted_at=orm.submitted_at,
    )


# ---------------------------------------------------------------------------
# PainTaxonomy + PainCategory + Rule
# ---------------------------------------------------------------------------


def pain_taxonomy_to_orm(domain: PainTaxonomy) -> PainTaxonomyORM:
    return PainTaxonomyORM(
        id=domain.id,
        version=domain.version,
        created_at=domain.created_at,
    )


def pain_taxonomy_from_orm(
    orm: PainTaxonomyORM,
    *,
    categories: list[PainCategory] | None = None,
) -> PainTaxonomy:
    return PainTaxonomy(
        id=orm.id,
        version=orm.version,
        categories=categories or [],
        created_at=orm.created_at,
    )


def pain_category_to_orm(
    domain: PainCategory,
    *,
    pain_taxonomy_id: uuid.UUID,
    orm_id: uuid.UUID | None = None,
) -> PainCategoryORM:
    return PainCategoryORM(
        id=orm_id or uuid.uuid4(),
        pain_taxonomy_id=pain_taxonomy_id,
        code=domain.id,
        name_by_language=_lang_dict_to_json(domain.name_by_language),
        description_by_language=_lang_dict_to_json(domain.description_by_language),
        example_by_language=_opt_lang_dict_to_json(domain.example_by_language),
    )


def pain_category_from_orm(orm: PainCategoryORM) -> PainCategory:
    return PainCategory(
        id=orm.code,
        name_by_language=_json_to_lang_dict(orm.name_by_language),
        description_by_language=_json_to_lang_dict(orm.description_by_language),
        example_by_language=_opt_json_to_lang_dict(orm.example_by_language),
    )


def rule_to_orm(domain: Rule, *, orm_id: uuid.UUID | None = None) -> RuleORM:
    return RuleORM(
        id=orm_id or uuid.uuid4(),
        code=domain.id,
        pain_category_code=domain.pain_category_id,
        trigger=domain.trigger.model_dump(mode="json"),
    )


def rule_from_orm(orm: RuleORM) -> Rule:
    return Rule(
        id=orm.code,
        pain_category_id=orm.pain_category_code,
        trigger=RuleTrigger.model_validate(orm.trigger),
    )


# ---------------------------------------------------------------------------
# Rationale
# ---------------------------------------------------------------------------


def rationale_to_orm(domain: Rationale) -> RationaleORM:
    return RationaleORM(
        id=domain.id,
        language=domain.language.value,
        priority_factors_addressed=[
            pf.model_dump(mode="json") for pf in domain.priority_factors_addressed
        ],
        narrative=domain.narrative,
        upstream_inputs_referenced=_uuids_to_strs(domain.upstream_inputs_referenced),
        created_at=domain.created_at,
    )


def rationale_from_orm(orm: RationaleORM) -> Rationale:
    return Rationale(
        id=orm.id,
        language=Language(orm.language),
        priority_factors_addressed=[
            PriorityFactor.model_validate(pf) for pf in orm.priority_factors_addressed
        ],
        narrative=orm.narrative,
        upstream_inputs_referenced=_strs_to_uuids(orm.upstream_inputs_referenced),
        created_at=orm.created_at,
    )


# ---------------------------------------------------------------------------
# LLMCallRecord
# ---------------------------------------------------------------------------


def llm_call_record_to_orm(domain: LLMCallRecord) -> LLMCallRecordORM:
    return LLMCallRecordORM(
        id=domain.id,
        session_id=domain.session_id,
        module=domain.module.value if domain.module is not None else None,
        prompt_hash=domain.prompt_hash,
        model_version=domain.model_version,
        language_directive=domain.language_directive.value,
        register_id=domain.register_id,
        parameters=domain.parameters,
        response_text=domain.response_text,
        latency_ms=domain.latency_ms,
        status=domain.status.value,
        error_message=domain.error_message,
        called_at=domain.called_at,
    )


def llm_call_record_from_orm(orm: LLMCallRecordORM) -> LLMCallRecord:
    return LLMCallRecord(
        id=orm.id,
        session_id=orm.session_id,
        module=ModuleId(orm.module) if orm.module is not None else None,
        prompt_hash=orm.prompt_hash,
        model_version=orm.model_version,
        language_directive=Language(orm.language_directive),
        register_id=orm.register_id,
        parameters=orm.parameters,
        response_text=orm.response_text,
        latency_ms=orm.latency_ms,
        status=LLMCallStatus(orm.status),
        error_message=orm.error_message,
        called_at=orm.called_at,
    )


# ---------------------------------------------------------------------------
# PainAnalysis
# ---------------------------------------------------------------------------


def pain_analysis_to_orm(domain: PainAnalysis) -> PainAnalysisORM:
    return PainAnalysisORM(
        id=domain.id,
        session_id=domain.session_id,
        tagged_pain_categories=list(domain.tagged_pain_categories),
        register_id=domain.register_id,
        narrative=domain.narrative,
        language=domain.language.value,
        rationale_id=domain.rationale_id,
        llm_call_record_ids=_uuids_to_strs(domain.llm_call_record_ids),
        created_at=domain.created_at,
    )


def pain_analysis_from_orm(orm: PainAnalysisORM) -> PainAnalysis:
    return PainAnalysis(
        id=orm.id,
        session_id=orm.session_id,
        tagged_pain_categories=list(orm.tagged_pain_categories),
        register_id=orm.register_id,
        narrative=orm.narrative,
        language=Language(orm.language),
        rationale_id=orm.rationale_id,
        llm_call_record_ids=_strs_to_uuids(orm.llm_call_record_ids),
        created_at=orm.created_at,
    )


# ---------------------------------------------------------------------------
# LanguageRegister
# ---------------------------------------------------------------------------


def language_register_to_orm(domain: LanguageRegister) -> LanguageRegisterORM:
    return LanguageRegisterORM(
        id=domain.id,
        session_id=domain.session_id,
        primary_language=domain.primary_language.value,
        arabic_variety=domain.arabic_variety.value,
        register_level=domain.register_level.value,
        cultural_anchors=list(domain.cultural_anchors),
        derived_at=domain.derived_at,
    )


def language_register_from_orm(orm: LanguageRegisterORM) -> LanguageRegister:
    return LanguageRegister(
        id=orm.id,
        session_id=orm.session_id,
        primary_language=Language(orm.primary_language),
        arabic_variety=ArabicVariety(orm.arabic_variety),
        register_level=RegisterLevel(orm.register_level),
        cultural_anchors=list(orm.cultural_anchors),
        derived_at=orm.derived_at,
    )


# ---------------------------------------------------------------------------
# DecisionScope
# ---------------------------------------------------------------------------


def decision_scope_to_orm(domain: DecisionScope) -> DecisionScopeORM:
    # set[ModuleId] → sorted list[str] for deterministic JSON storage.
    return DecisionScopeORM(
        session_id=domain.session_id,
        modules=sorted(m.value for m in domain.modules),
        selected_at=domain.selected_at,
    )


def decision_scope_from_orm(orm: DecisionScopeORM) -> DecisionScope:
    return DecisionScope(
        session_id=orm.session_id,
        modules={ModuleId(m) for m in orm.modules},
        selected_at=orm.selected_at,
    )


# ---------------------------------------------------------------------------
# ExecutionPlan
# ---------------------------------------------------------------------------


def execution_plan_to_orm(domain: ExecutionPlan) -> ExecutionPlanORM:
    # tuple in domain → list of two-element list in JSONB.
    return ExecutionPlanORM(
        session_id=domain.session_id,
        ordered_modules=[m.value for m in domain.ordered_modules],
        intersection_pairs=[[u.value, d.value] for u, d in domain.intersection_pairs],
        created_at=domain.created_at,
    )


def execution_plan_from_orm(orm: ExecutionPlanORM) -> ExecutionPlan:
    return ExecutionPlan(
        session_id=orm.session_id,
        ordered_modules=[ModuleId(m) for m in orm.ordered_modules],
        intersection_pairs=[
            (ModuleId(pair[0]), ModuleId(pair[1])) for pair in orm.intersection_pairs
        ],
        created_at=orm.created_at,
    )


# ---------------------------------------------------------------------------
# ModuleOutput
# ---------------------------------------------------------------------------


def module_output_to_orm(domain: ModuleOutput) -> ModuleOutputORM:
    return ModuleOutputORM(
        id=domain.id,
        session_id=domain.session_id,
        module=domain.module.value,
        language=domain.language.value,
        register_id=domain.register_id,
        content=domain.content,
        upstream_module_outputs=_uuids_to_strs(domain.upstream_module_outputs),
        rationale_id=domain.rationale_id,
        llm_call_record_ids=_uuids_to_strs(domain.llm_call_record_ids),
        created_at=domain.created_at,
    )


def module_output_from_orm(orm: ModuleOutputORM) -> ModuleOutput:
    return ModuleOutput(
        id=orm.id,
        session_id=orm.session_id,
        module=ModuleId(orm.module),
        language=Language(orm.language),
        register_id=orm.register_id,
        content=orm.content,
        upstream_module_outputs=_strs_to_uuids(orm.upstream_module_outputs),
        rationale_id=orm.rationale_id,
        llm_call_record_ids=_strs_to_uuids(orm.llm_call_record_ids),
        created_at=orm.created_at,
    )


# ---------------------------------------------------------------------------
# SessionSystemPrompt
# ---------------------------------------------------------------------------


def session_system_prompt_to_orm(domain: SessionSystemPrompt) -> SessionSystemPromptORM:
    return SessionSystemPromptORM(
        session_id=domain.session_id,
        unified_preamble=domain.unified_preamble,
        module_extensions={
            module.value: ext.model_dump(mode="json")
            for module, ext in domain.module_extensions.items()
        },
        register_id=domain.register_id,
        questionnaire_version_id=domain.questionnaire_version_id,
        pain_analysis_id=domain.pain_analysis_id,
        built_at=domain.built_at,
    )


def session_system_prompt_from_orm(orm: SessionSystemPromptORM) -> SessionSystemPrompt:
    return SessionSystemPrompt(
        session_id=orm.session_id,
        unified_preamble=orm.unified_preamble,
        module_extensions={
            ModuleId(module): ModulePromptExtension.model_validate(ext)
            for module, ext in orm.module_extensions.items()
        },
        register_id=orm.register_id,
        questionnaire_version_id=orm.questionnaire_version_id,
        pain_analysis_id=orm.pain_analysis_id,
        built_at=orm.built_at,
    )


# ---------------------------------------------------------------------------
# ExportArtifact
# ---------------------------------------------------------------------------


def export_artifact_to_orm(domain: ExportArtifact) -> ExportArtifactORM:
    return ExportArtifactORM(
        id=domain.id,
        session_id=domain.session_id,
        format=domain.format.value,
        file_path=domain.file_path,
        included_artifacts_manifest=list(domain.included_artifacts_manifest),
        created_at=domain.created_at,
    )


def export_artifact_from_orm(orm: ExportArtifactORM) -> ExportArtifact:
    return ExportArtifact(
        id=orm.id,
        session_id=orm.session_id,
        format=ExportFormat(orm.format),
        file_path=orm.file_path,
        included_artifacts_manifest=list(orm.included_artifacts_manifest),
        created_at=orm.created_at,
    )
