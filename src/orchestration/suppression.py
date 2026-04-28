from src.domain.module import DecisionScope, ModuleId

ALL_MODULES: frozenset[ModuleId] = frozenset(ModuleId)


def compute_suppressed_modules(scope: DecisionScope) -> set[ModuleId]:
    """Return the set of modules NOT in the active DecisionScope.

    Per CLAUDE.md §2.6 suppression is absolute: a non-selected module
    contributes zero — no output, no prompt reference, no priority
    consultation, no intersection participation. This function is the
    single source of truth for "what is suppressed?".
    """
    return set(ALL_MODULES) - set(scope.modules)
