"""Round-trip tests for every converter.

Every persistable domain entity is built, converted to ORM, then converted
back. The reconstructed Pydantic model must equal the original. This proves
no information is lost across the JSONB / enum / UUID-string boundaries.

The converters operate on ORM instances detached from any Session. SQLAlchemy
allows attribute access on transient instances, which is what these tests
exercise.
"""

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
from src.persistence.converters import (
    answer_from_orm,
    answer_option_from_orm,
    answer_option_to_orm,
    answer_to_orm,
    decision_scope_from_orm,
    decision_scope_to_orm,
    execution_plan_from_orm,
    execution_plan_to_orm,
    export_artifact_from_orm,
    export_artifact_to_orm,
    facilitator_from_orm,
    facilitator_to_orm,
    language_register_from_orm,
    language_register_to_orm,
    llm_call_record_from_orm,
    llm_call_record_to_orm,
    module_output_from_orm,
    module_output_to_orm,
    pain_analysis_from_orm,
    pain_analysis_to_orm,
    pain_category_from_orm,
    pain_category_to_orm,
    pain_taxonomy_from_orm,
    pain_taxonomy_to_orm,
    question_from_orm,
    question_to_orm,
    questionnaire_instance_from_orm,
    questionnaire_instance_to_orm,
    questionnaire_version_from_orm,
    questionnaire_version_to_orm,
    rationale_from_orm,
    rationale_to_orm,
    rule_from_orm,
    rule_to_orm,
    session_from_orm,
    session_system_prompt_from_orm,
    session_system_prompt_to_orm,
    session_to_orm,
)


def test_facilitator_round_trip():
    f = Facilitator(email="ops@example.com", display_name="Ops User")
    assert facilitator_from_orm(facilitator_to_orm(f)) == f


def test_session_round_trip():
    s = Session(
        facilitator_id=uuid.uuid4(),
        questionnaire_version_id=uuid.uuid4(),
        phase=PhaseState.GENERATION,
    )
    assert session_from_orm(session_to_orm(s)) == s


def test_questionnaire_version_round_trip_top_level_only():
    qv = QuestionnaireVersion(version="1.0.0", content_hash="abc123", questions=[])
    round_tripped = questionnaire_version_from_orm(questionnaire_version_to_orm(qv))
    assert round_tripped == qv


def test_question_round_trip_with_slider_config():
    q = Question(
        id="q1.1",
        section="identity",
        text_by_language={
            Language.ENGLISH: "Heritage or vision?",
            Language.ARABIC: "إرث أم رؤية؟",
        },
        mechanic=AnswerMechanic.SLIDER,
        slider_config=SliderConfig(
            left_label_by_language={
                Language.ENGLISH: "All heritage",
                Language.ARABIC: "إرث",
            },
            right_label_by_language={
                Language.ENGLISH: "All vision",
                Language.ARABIC: "رؤية",
            },
        ),
    )
    qv_id = uuid.uuid4()
    orm_id = uuid.uuid4()
    orm = question_to_orm(q, questionnaire_version_id=qv_id, orm_id=orm_id)
    round_tripped = question_from_orm(orm)
    assert round_tripped == q


def test_answer_option_round_trip():
    o = AnswerOption(
        value="pioneer",
        label_by_language={Language.ENGLISH: "Pioneer", Language.ARABIC: "رائد"},
    )
    orm = answer_option_to_orm(o, question_id=uuid.uuid4())
    assert answer_option_from_orm(orm) == o


def test_answer_int_value_for_slider_round_trip():
    a = Answer(question_id="q1.1", value=42, language=Language.ARABIC)
    orm = answer_to_orm(a, questionnaire_instance_id=uuid.uuid4())
    assert answer_from_orm(orm) == a


def test_answer_list_value_for_multi_choice_round_trip():
    a = Answer(question_id="q1.5", value=["hospitality", "faith"], language=Language.ENGLISH)
    orm = answer_to_orm(a, questionnaire_instance_id=uuid.uuid4())
    assert answer_from_orm(orm) == a


def test_questionnaire_instance_round_trip():
    qi = QuestionnaireInstance(
        session_id=uuid.uuid4(),
        questionnaire_version_id=uuid.uuid4(),
    )
    assert questionnaire_instance_from_orm(questionnaire_instance_to_orm(qi)) == qi


def test_pain_taxonomy_round_trip_top_level():
    t = PainTaxonomy(version="1.0.0", categories=[])
    assert pain_taxonomy_from_orm(pain_taxonomy_to_orm(t)) == t


def test_pain_category_round_trip():
    c = PainCategory(
        id="obscurity",
        name_by_language={Language.ENGLISH: "Obscurity", Language.ARABIC: "غموض"},
        description_by_language={
            Language.ENGLISH: "Brand is invisible.",
            Language.ARABIC: "العلامة غير مرئية.",
        },
    )
    orm = pain_category_to_orm(c, pain_taxonomy_id=uuid.uuid4())
    assert pain_category_from_orm(orm) == c


def test_rule_round_trip():
    r = Rule(
        id="r1",
        pain_category_id="obscurity",
        trigger=RuleTrigger(question_id="q3.1", operator="less_than", value=40),
    )
    assert rule_from_orm(rule_to_orm(r)) == r


def test_rationale_round_trip_with_priority_factors_and_uuids():
    upstream = uuid.uuid4()
    r = Rationale(
        priority_factors_addressed=[
            PriorityFactor(
                factor_name="Strategic positioning",
                how_addressed="Reinforces challenger stance.",
            ),
            PriorityFactor(
                factor_name="Audience perception",
                how_addressed="Lands clearly with Saudi pros.",
            ),
        ],
        narrative="The output expresses the brand's challenger posture.",
        language=Language.ENGLISH,
        upstream_inputs_referenced=[upstream],
    )
    round_tripped = rationale_from_orm(rationale_to_orm(r))
    assert round_tripped == r


def test_llm_call_record_round_trip_with_nested_parameters():
    rec = LLMCallRecord(
        session_id=uuid.uuid4(),
        module=ModuleId.STRATEGY_THEME,
        prompt_hash="a" * 64,
        model_version="claude-opus-4-7",
        language_directive=Language.ENGLISH,
        register_id=uuid.uuid4(),
        parameters={"temperature": 0.7, "max_tokens": 2048, "tools": [{"name": "x"}]},
        response_text="…",
        latency_ms=820,
        status=LLMCallStatus.SUCCESS,
    )
    assert llm_call_record_from_orm(llm_call_record_to_orm(rec)) == rec


def test_llm_call_record_round_trip_module_none_for_narrative_generator():
    rec = LLMCallRecord(
        session_id=uuid.uuid4(),
        prompt_hash="b" * 64,
        model_version="claude-opus-4-7",
        language_directive=Language.ARABIC,
        parameters={},
        response_text="…",
        latency_ms=1500,
        status=LLMCallStatus.SUCCESS,
    )
    assert llm_call_record_from_orm(llm_call_record_to_orm(rec)) == rec


def test_pain_analysis_round_trip():
    call_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
    pa = PainAnalysis(
        session_id=uuid.uuid4(),
        tagged_pain_categories=["obscurity", "stagnation"],
        register_id=uuid.uuid4(),
        narrative="The brand has lost momentum and visibility.",
        language=Language.ENGLISH,
        rationale_id=uuid.uuid4(),
        llm_call_record_ids=call_ids,
    )
    round_tripped = pain_analysis_from_orm(pain_analysis_to_orm(pa))
    assert round_tripped == pa
    # JSONB list ordering must survive the round-trip; later runs that
    # rely on call_ids[0] being the primary call depend on this.
    assert round_tripped.llm_call_record_ids == call_ids


def test_language_register_round_trip():
    lr = LanguageRegister(
        session_id=uuid.uuid4(),
        primary_language=Language.ARABIC,
        arabic_variety=ArabicVariety.MSA,
        register_level=RegisterLevel.FORMAL,
        cultural_anchors=["hospitality", "craftsmanship"],
    )
    assert language_register_from_orm(language_register_to_orm(lr)) == lr


def test_decision_scope_set_round_trip_preserves_membership():
    s = DecisionScope(
        session_id=uuid.uuid4(),
        modules={ModuleId.TAGLINE, ModuleId.STRATEGY_THEME, ModuleId.NAMING},
    )
    round_tripped = decision_scope_from_orm(decision_scope_to_orm(s))
    # Membership preserved; ordering is a JSONB-list detail invisible to set.
    assert round_tripped.modules == s.modules
    assert round_tripped.session_id == s.session_id


def test_execution_plan_tuples_survive_jsonb_round_trip():
    plan = ExecutionPlan(
        session_id=uuid.uuid4(),
        ordered_modules=[ModuleId.STRATEGY_THEME, ModuleId.TONE, ModuleId.NAMING],
        intersection_pairs=[
            (ModuleId.STRATEGY_THEME, ModuleId.TONE),
            (ModuleId.STRATEGY_THEME, ModuleId.NAMING),
            (ModuleId.TONE, ModuleId.NAMING),
        ],
    )
    round_tripped = execution_plan_from_orm(execution_plan_to_orm(plan))
    assert round_tripped.ordered_modules == plan.ordered_modules
    # Tuples are reconstructed from inner JSON arrays.
    assert round_tripped.intersection_pairs == plan.intersection_pairs
    assert all(isinstance(pair, tuple) for pair in round_tripped.intersection_pairs)


def test_module_output_round_trip_with_nested_uuid_lists():
    mo = ModuleOutput(
        session_id=uuid.uuid4(),
        module=ModuleId.TONE,
        language=Language.ARABIC,
        register_id=uuid.uuid4(),
        content={"voice": "warm and direct", "examples": ["…", "…"]},
        upstream_module_outputs=[uuid.uuid4(), uuid.uuid4()],
        rationale_id=uuid.uuid4(),
        llm_call_record_ids=[uuid.uuid4(), uuid.uuid4(), uuid.uuid4()],
    )
    assert module_output_from_orm(module_output_to_orm(mo)) == mo


def test_session_system_prompt_round_trip_with_module_extensions():
    p = SessionSystemPrompt(
        session_id=uuid.uuid4(),
        unified_preamble="Brand DNA + Pain + Register…",
        module_extensions={
            ModuleId.STRATEGY_THEME: ModulePromptExtension(
                module=ModuleId.STRATEGY_THEME,
                extension_text="Strategy priorities…",
                schema_directive="Return {theme, justification}.",
            ),
            ModuleId.TONE: ModulePromptExtension(
                module=ModuleId.TONE,
                extension_text="Tone priorities…",
                schema_directive="Return {voice}.",
            ),
        },
        register_id=uuid.uuid4(),
        questionnaire_version_id=uuid.uuid4(),
        pain_analysis_id=uuid.uuid4(),
    )
    assert session_system_prompt_from_orm(session_system_prompt_to_orm(p)) == p


def test_export_artifact_round_trip():
    art = ExportArtifact(
        session_id=uuid.uuid4(),
        format=ExportFormat.PDF,
        file_path="/exports/session-abc.pdf",
        included_artifacts_manifest=["questionnaire", "pain_analysis", "module_outputs"],
    )
    assert export_artifact_from_orm(export_artifact_to_orm(art)) == art


def test_decision_scope_to_orm_emits_sorted_module_list():
    """Determinism: set order is unstable, but the JSONB representation
    is sorted so identical scopes produce identical JSON."""
    scope = DecisionScope(
        session_id=uuid.uuid4(),
        modules={ModuleId.TAGLINE, ModuleId.STRATEGY_THEME, ModuleId.NAMING},
    )
    orm = decision_scope_to_orm(scope)
    assert orm.modules == sorted(orm.modules)
