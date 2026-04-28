import uuid

from src.domain.module import DecisionScope, ModuleId
from src.orchestration.intersections import (
    INTERSECTION_PAIRS,
    applicable_intersection_pairs,
)


def _scope(modules: set[ModuleId]) -> DecisionScope:
    return DecisionScope(session_id=uuid.uuid4(), modules=modules)


def test_single_module_scope_produces_zero_pairs():
    pairs = applicable_intersection_pairs(_scope({ModuleId.NAMING}))
    assert pairs == []


def test_full_scope_produces_all_seven_pairs():
    pairs = applicable_intersection_pairs(_scope(set(ModuleId)))
    assert len(pairs) == 7
    assert tuple(pairs) == INTERSECTION_PAIRS


def test_strategy_and_slogan_only_yields_one_pair():
    pairs = applicable_intersection_pairs(_scope({ModuleId.STRATEGY_THEME, ModuleId.SLOGAN}))
    assert pairs == [(ModuleId.STRATEGY_THEME, ModuleId.SLOGAN)]


def test_tone_and_naming_only_yields_one_pair():
    pairs = applicable_intersection_pairs(_scope({ModuleId.TONE, ModuleId.NAMING}))
    assert pairs == [(ModuleId.TONE, ModuleId.NAMING)]


def test_naming_slogan_tagline_yields_zero_pairs_when_strategy_and_tone_absent():
    pairs = applicable_intersection_pairs(
        _scope({ModuleId.NAMING, ModuleId.SLOGAN, ModuleId.TAGLINE})
    )
    assert pairs == []


def test_pairs_returned_in_canonical_order_not_scope_iteration_order():
    # Insert in reverse — result must still match canonical INTERSECTION_PAIRS order.
    scope = _scope({ModuleId.TAGLINE, ModuleId.TONE, ModuleId.STRATEGY_THEME})
    pairs = applicable_intersection_pairs(scope)
    expected = [
        (ModuleId.STRATEGY_THEME, ModuleId.TONE),
        (ModuleId.STRATEGY_THEME, ModuleId.TAGLINE),
        (ModuleId.TONE, ModuleId.TAGLINE),
    ]
    assert pairs == expected


def test_intersection_lookup_is_deterministic():
    scope = _scope({ModuleId.STRATEGY_THEME, ModuleId.TONE, ModuleId.NAMING})
    assert applicable_intersection_pairs(scope) == applicable_intersection_pairs(scope)


def test_intersection_pairs_constant_has_seven_entries():
    assert len(INTERSECTION_PAIRS) == 7
