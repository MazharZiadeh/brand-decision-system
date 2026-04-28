from src.domain.module import DecisionScope, ModuleId

# (upstream, downstream) — the downstream module's output is conditioned on
# the upstream module's output. Order is canonical: iterating this tuple is
# what gives applicable_intersection_pairs its deterministic ordering, per
# CLAUDE.md §2.9.
INTERSECTION_PAIRS: tuple[tuple[ModuleId, ModuleId], ...] = (
    (ModuleId.STRATEGY_THEME, ModuleId.TONE),
    (ModuleId.STRATEGY_THEME, ModuleId.NAMING),
    (ModuleId.STRATEGY_THEME, ModuleId.SLOGAN),
    (ModuleId.STRATEGY_THEME, ModuleId.TAGLINE),
    (ModuleId.TONE, ModuleId.NAMING),
    (ModuleId.TONE, ModuleId.SLOGAN),
    (ModuleId.TONE, ModuleId.TAGLINE),
)


def applicable_intersection_pairs(
    scope: DecisionScope,
) -> list[tuple[ModuleId, ModuleId]]:
    """Return the (upstream, downstream) pairs whose BOTH modules are in scope.

    Order matches INTERSECTION_PAIRS, not the order modules appear in the
    scope, so that identical inputs always produce identical outputs.
    """
    active = scope.modules
    return [
        (upstream, downstream)
        for upstream, downstream in INTERSECTION_PAIRS
        if upstream in active and downstream in active
    ]
