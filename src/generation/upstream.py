"""Upstream output assembly helpers — two distinct concerns.

`upstream_module_ids_for(target, scope_modules)` — the AUDIT relationship.
Returns the modules that formally feed `target` per the seven
(upstream, downstream) pairs in `INTERSECTION_PAIRS`, in canonical
execution order. The orchestrator uses this to populate
`ModuleOutput.upstream_module_outputs` (CLAUDE.md §2.7 audit chain).

`build_upstream_outputs(target, completed_outputs, scope_modules)` — the
TEMPLATE access shape. Returns every completed output in scope (excluding
the target itself), keyed by `module_id.value` for Jinja2 attribute
access. Templates conservatively reference prior outputs even outside
the formal intersection rules — e.g., `tagline.j2` reads
`upstream.slogan` to avoid duplicating the internal slogan, even
though (Slogan → Tagline) is not in INTERSECTION_PAIRS. Pre-populating
the template's upstream dict with every completed output makes those
defensive references safe under `StrictUndefined`.

Both helpers respect CLAUDE.md §2.3 (modules never call each other
directly) — modules read upstream outputs through the orchestrator's
explicit feed, never via cross-module imports.
"""

from __future__ import annotations

from src.domain.module import ModuleId, ModuleOutput
from src.orchestration.engine import CANONICAL_MODULE_ORDER
from src.orchestration.intersections import INTERSECTION_PAIRS


def upstream_module_ids_for(
    target: ModuleId,
    scope_modules: set[ModuleId],
) -> list[ModuleId]:
    """Audit relationship: modules formally feeding `target` per
    INTERSECTION_PAIRS, in canonical order.
    """
    if target not in scope_modules:
        return []
    upstream_in_scope: set[ModuleId] = set()
    for upstream, downstream in INTERSECTION_PAIRS:
        if downstream == target and upstream in scope_modules:
            upstream_in_scope.add(upstream)
    return [m for m in CANONICAL_MODULE_ORDER if m in upstream_in_scope]


def build_upstream_outputs(
    target: ModuleId,
    completed_outputs: dict[ModuleId, ModuleOutput],
    scope_modules: set[ModuleId],
) -> dict[str, ModuleOutput | None]:
    """Template access shape: an entry for EVERY `ModuleId` (excluding
    `target`), keyed by `module_id.value`. Value is the completed
    `ModuleOutput` if available; otherwise `None`.

    Pre-populating every key keeps Jinja2 conditionals like
    `{% if upstream.tone %}` safe under `StrictUndefined`: a None value
    is falsy so the block is skipped, but the attribute access does
    not raise. Modules out of scope or not yet completed produce None.
    """
    result: dict[str, ModuleOutput | None] = {
        m.value: None for m in CANONICAL_MODULE_ORDER if m != target
    }
    for m in CANONICAL_MODULE_ORDER:
        if m == target:
            continue
        if m in scope_modules and m in completed_outputs:
            result[m.value] = completed_outputs[m]
    return result
