import uuid

import pytest
from pydantic import ValidationError

from src.domain.language import Language
from src.domain.module import (
    DecisionScope,
    ExecutionPlan,
    ModuleId,
    ModuleOutput,
)


def test_module_id_members():
    assert {m.value for m in ModuleId} == {
        "strategy_theme",
        "tone",
        "naming",
        "slogan",
        "tagline",
    }


def test_valid_decision_scope():
    s = DecisionScope(
        session_id=uuid.uuid4(),
        modules={ModuleId.STRATEGY_THEME, ModuleId.TONE},
    )
    assert ModuleId.STRATEGY_THEME in s.modules
    assert len(s.modules) == 2


def test_empty_decision_scope_rejected():
    with pytest.raises(ValidationError):
        DecisionScope(session_id=uuid.uuid4(), modules=set())


def test_full_decision_scope_accepted():
    s = DecisionScope(session_id=uuid.uuid4(), modules=set(ModuleId))
    assert len(s.modules) == 5


def test_execution_plan_holds_ordering_and_pairs():
    plan = ExecutionPlan(
        session_id=uuid.uuid4(),
        ordered_modules=[ModuleId.STRATEGY_THEME, ModuleId.TONE],
        intersection_pairs=[(ModuleId.STRATEGY_THEME, ModuleId.TONE)],
    )
    assert plan.ordered_modules[0] == ModuleId.STRATEGY_THEME
    assert plan.intersection_pairs[0] == (ModuleId.STRATEGY_THEME, ModuleId.TONE)


def test_module_output_requires_language():
    with pytest.raises(ValidationError):
        ModuleOutput(  # type: ignore[call-arg]
            session_id=uuid.uuid4(),
            module=ModuleId.STRATEGY_THEME,
            register_id=uuid.uuid4(),
            content={"theme": "human-centred craftsmanship"},
            rationale_id=uuid.uuid4(),
            llm_call_record_ids=[uuid.uuid4()],
        )


def test_module_output_requires_at_least_one_call_record():
    with pytest.raises(ValidationError):
        ModuleOutput(
            session_id=uuid.uuid4(),
            module=ModuleId.STRATEGY_THEME,
            language=Language.ENGLISH,
            register_id=uuid.uuid4(),
            content={"theme": "x"},
            rationale_id=uuid.uuid4(),
            llm_call_record_ids=[],
        )


def test_valid_module_output():
    out = ModuleOutput(
        session_id=uuid.uuid4(),
        module=ModuleId.TONE,
        language=Language.ARABIC,
        register_id=uuid.uuid4(),
        content={"voice": "warm and direct"},
        rationale_id=uuid.uuid4(),
        llm_call_record_ids=[uuid.uuid4()],
    )
    assert out.module == ModuleId.TONE
    assert out.language == Language.ARABIC
