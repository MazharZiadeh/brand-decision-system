import uuid

import pytest
from pydantic import ValidationError

from src.domain.module import DecisionScope, ExecutionPlan, ModuleId
from src.orchestration.engine import CANONICAL_MODULE_ORDER, build_execution_plan


def _scope(modules: set[ModuleId]) -> DecisionScope:
    return DecisionScope(session_id=uuid.uuid4(), modules=modules)


def test_single_module_scope_produces_single_module_plan():
    scope = _scope({ModuleId.STRATEGY_THEME})
    plan = build_execution_plan(scope)
    assert isinstance(plan, ExecutionPlan)
    assert plan.ordered_modules == [ModuleId.STRATEGY_THEME]
    assert plan.intersection_pairs == []


def test_full_scope_produces_all_five_in_canonical_order():
    plan = build_execution_plan(_scope(set(ModuleId)))
    assert plan.ordered_modules == list(CANONICAL_MODULE_ORDER)
    assert len(plan.intersection_pairs) == 7


def test_scope_in_arbitrary_input_order_is_emitted_in_canonical_order():
    # Set construction order in Python is unstable across processes; the
    # output ordering must come from CANONICAL_MODULE_ORDER, not the scope's
    # iteration order.
    scope = _scope({ModuleId.TAGLINE, ModuleId.STRATEGY_THEME, ModuleId.NAMING})
    plan = build_execution_plan(scope)
    assert plan.ordered_modules == [
        ModuleId.STRATEGY_THEME,
        ModuleId.NAMING,
        ModuleId.TAGLINE,
    ]


def test_routing_is_deterministic_across_calls():
    scope = _scope({ModuleId.STRATEGY_THEME, ModuleId.TONE, ModuleId.SLOGAN})
    plan_a = build_execution_plan(scope)
    plan_b = build_execution_plan(scope)
    # Routing content is deterministic; created_at metadata is not compared.
    assert plan_a.ordered_modules == plan_b.ordered_modules
    assert plan_a.intersection_pairs == plan_b.intersection_pairs


def test_session_id_propagates_from_scope_to_plan():
    sid = uuid.uuid4()
    scope = DecisionScope(session_id=sid, modules={ModuleId.TONE})
    plan = build_execution_plan(scope)
    assert plan.session_id == sid


def test_empty_decision_scope_is_rejected_by_pydantic():
    # The Session 2 validator on DecisionScope.modules enforces non-empty.
    # The engine should never receive an empty scope.
    with pytest.raises(ValidationError):
        DecisionScope(session_id=uuid.uuid4(), modules=set())
