import uuid

from src.domain.module import DecisionScope, ModuleId
from src.orchestration.suppression import ALL_MODULES, compute_suppressed_modules


def test_single_module_scope_suppresses_the_other_four():
    scope = DecisionScope(session_id=uuid.uuid4(), modules={ModuleId.STRATEGY_THEME})
    suppressed = compute_suppressed_modules(scope)
    assert suppressed == {
        ModuleId.TONE,
        ModuleId.NAMING,
        ModuleId.SLOGAN,
        ModuleId.TAGLINE,
    }


def test_full_scope_suppresses_zero():
    scope = DecisionScope(session_id=uuid.uuid4(), modules=set(ModuleId))
    assert compute_suppressed_modules(scope) == set()


def test_suppressed_and_active_partition_all_modules():
    scope = DecisionScope(
        session_id=uuid.uuid4(),
        modules={ModuleId.STRATEGY_THEME, ModuleId.SLOGAN},
    )
    suppressed = compute_suppressed_modules(scope)
    active = scope.modules

    assert suppressed.isdisjoint(active)
    assert suppressed | active == set(ALL_MODULES)


def test_result_is_a_set_not_a_list():
    scope = DecisionScope(session_id=uuid.uuid4(), modules={ModuleId.TONE})
    result = compute_suppressed_modules(scope)
    assert isinstance(result, set)
    assert not isinstance(result, list)


def test_all_modules_constant_is_frozen():
    assert isinstance(ALL_MODULES, frozenset)
    assert frozenset(ModuleId) == ALL_MODULES
