"""Exhaustive coverage of all 31 valid Decision Scope combinations.

The 5 generation modules yield 2^5 - 1 = 31 non-empty subsets. Every
parametrized test in this file runs once per subset, which is what gives
the orchestration layer its routing-determinism guarantee per CLAUDE.md
§2.9 — every combination is checked, not a sample.

Layer 3 (property invariants) lives at the bottom of this file rather
than in a separate module so the parametrize fixture is reused.
"""

import itertools
import uuid

import pytest

from src.domain.module import DecisionScope, ExecutionPlan, ModuleId
from src.orchestration import (
    ALL_MODULES,
    CANONICAL_MODULE_ORDER,
    INTERSECTION_PAIRS,
    applicable_intersection_pairs,
    build_execution_plan,
    compute_suppressed_modules,
)


def _all_non_empty_subsets() -> list[frozenset[ModuleId]]:
    """All 2^5 - 1 = 31 non-empty subsets of the 5 modules.

    Listed in canonical order (sorted by canonical module index) so the
    parametrized test ids are stable across runs.
    """
    modules = list(CANONICAL_MODULE_ORDER)
    subsets = [
        frozenset(combo)
        for r in range(1, len(modules) + 1)
        for combo in itertools.combinations(modules, r)
    ]
    return subsets


ALL_VALID_SUBSETS = _all_non_empty_subsets()


def test_exactly_31_subsets():
    assert len(ALL_VALID_SUBSETS) == 31


# ---------------------------------------------------------------------------
# Layer 2 — every-subset coverage
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("module_set", ALL_VALID_SUBSETS)
def test_every_subset_produces_valid_plan(module_set: frozenset[ModuleId]) -> None:
    """For every valid Decision Scope, the engine produces an ExecutionPlan
    whose modules match the scope exactly, are ordered canonically, and
    whose intersection pairs only reference active modules."""
    scope = DecisionScope(session_id=uuid.uuid4(), modules=set(module_set))
    plan = build_execution_plan(scope)

    assert isinstance(plan, ExecutionPlan)

    # Suppression invariant: scope ⇔ ordered_modules (set equality).
    assert set(plan.ordered_modules) == set(module_set)

    # Canonical ordering invariant.
    canonical_indices = [CANONICAL_MODULE_ORDER.index(m) for m in plan.ordered_modules]
    assert canonical_indices == sorted(
        canonical_indices
    ), f"ordered_modules not in canonical order: {plan.ordered_modules}"

    # No suppressed module appears in any intersection pair.
    for upstream, downstream in plan.intersection_pairs:
        assert upstream in module_set
        assert downstream in module_set


@pytest.mark.parametrize("module_set", ALL_VALID_SUBSETS)
def test_determinism_per_subset(module_set: frozenset[ModuleId]) -> None:
    """Calling build_execution_plan twice for the same scope produces the
    same routing content (ordered_modules + intersection_pairs)."""
    session_id = uuid.uuid4()
    scope_1 = DecisionScope(session_id=session_id, modules=set(module_set))
    scope_2 = DecisionScope(session_id=session_id, modules=set(module_set))

    plan_1 = build_execution_plan(scope_1)
    plan_2 = build_execution_plan(scope_2)

    assert plan_1.ordered_modules == plan_2.ordered_modules
    assert plan_1.intersection_pairs == plan_2.intersection_pairs


@pytest.mark.parametrize("module_set", ALL_VALID_SUBSETS)
def test_suppression_complement(module_set: frozenset[ModuleId]) -> None:
    """suppressed ∪ active = ALL_MODULES, with no overlap, for every subset."""
    scope = DecisionScope(session_id=uuid.uuid4(), modules=set(module_set))
    suppressed = compute_suppressed_modules(scope)
    active = scope.modules

    assert suppressed.isdisjoint(active)
    assert suppressed | active == set(ALL_MODULES)


@pytest.mark.parametrize("module_set", ALL_VALID_SUBSETS)
def test_intersection_pairs_only_contain_active_modules(
    module_set: frozenset[ModuleId],
) -> None:
    """Per CLAUDE.md §2.6, suppressed modules participate in zero
    intersection rules across every one of the 31 subsets."""
    scope = DecisionScope(session_id=uuid.uuid4(), modules=set(module_set))
    pairs = applicable_intersection_pairs(scope)

    for upstream, downstream in pairs:
        assert upstream in module_set, f"Suppressed module {upstream} appeared in intersection pair"
        assert (
            downstream in module_set
        ), f"Suppressed module {downstream} appeared in intersection pair"


# ---------------------------------------------------------------------------
# Layer 3 — property-style invariants
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("module_set", ALL_VALID_SUBSETS)
def test_intersection_upstream_precedes_downstream_in_canonical_order(
    module_set: frozenset[ModuleId],
) -> None:
    """Every (u, d) returned must satisfy: u appears before d in
    CANONICAL_MODULE_ORDER. Upstream is upstream."""
    scope = DecisionScope(session_id=uuid.uuid4(), modules=set(module_set))
    for upstream, downstream in applicable_intersection_pairs(scope):
        u_idx = CANONICAL_MODULE_ORDER.index(upstream)
        d_idx = CANONICAL_MODULE_ORDER.index(downstream)
        assert u_idx < d_idx, f"Pair {(upstream, downstream)} has upstream not preceding downstream"


@pytest.mark.parametrize("module_set", ALL_VALID_SUBSETS)
def test_intersection_count_matches_filtered_constant(
    module_set: frozenset[ModuleId],
) -> None:
    """The returned pair count equals the number of pairs in
    INTERSECTION_PAIRS where BOTH modules are in the scope."""
    scope = DecisionScope(session_id=uuid.uuid4(), modules=set(module_set))
    expected_count = sum(1 for u, d in INTERSECTION_PAIRS if u in module_set and d in module_set)
    assert len(applicable_intersection_pairs(scope)) == expected_count


@pytest.mark.parametrize(
    "single_module",
    [
        ModuleId.STRATEGY_THEME,
        ModuleId.TONE,
        ModuleId.NAMING,
        ModuleId.SLOGAN,
        ModuleId.TAGLINE,
    ],
)
def test_single_module_scope_has_zero_pairs(single_module: ModuleId) -> None:
    """Any single-module scope produces zero intersection pairs."""
    scope = DecisionScope(session_id=uuid.uuid4(), modules={single_module})
    assert applicable_intersection_pairs(scope) == []


def test_full_set_has_exactly_seven_pairs():
    scope = DecisionScope(session_id=uuid.uuid4(), modules=set(ModuleId))
    assert len(applicable_intersection_pairs(scope)) == 7
