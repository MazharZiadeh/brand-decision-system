from datetime import UTC, datetime

from src.domain.module import DecisionScope, ExecutionPlan, ModuleId
from src.orchestration.intersections import applicable_intersection_pairs

# Strategy Theme → Tone → Naming → Slogan → Tagline (TDD §5.3).
CANONICAL_MODULE_ORDER: tuple[ModuleId, ...] = (
    ModuleId.STRATEGY_THEME,
    ModuleId.TONE,
    ModuleId.NAMING,
    ModuleId.SLOGAN,
    ModuleId.TAGLINE,
)


def build_execution_plan(scope: DecisionScope) -> ExecutionPlan:
    """Convert a DecisionScope into a deterministic ExecutionPlan.

    Per CLAUDE.md §2.9 routing is deterministic: identical input produces
    identical `ordered_modules` and `intersection_pairs` every call. Per §2.6
    modules not in the scope appear nowhere in the output. The `created_at`
    timestamp is metadata; tests that check determinism compare routing
    content, not the timestamp.
    """
    ordered_modules = [m for m in CANONICAL_MODULE_ORDER if m in scope.modules]
    intersections = applicable_intersection_pairs(scope)
    return ExecutionPlan(
        session_id=scope.session_id,
        ordered_modules=ordered_modules,
        intersection_pairs=intersections,
        created_at=datetime.now(UTC),
    )
