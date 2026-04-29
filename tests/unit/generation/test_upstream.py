"""Tests for the upstream output assembly helpers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from src.domain.language import Language
from src.domain.module import ModuleId, ModuleOutput
from src.generation.upstream import build_upstream_outputs, upstream_module_ids_for


def _output(module: ModuleId, session_id: uuid.UUID) -> ModuleOutput:
    return ModuleOutput(
        session_id=session_id,
        module=module,
        language=Language.ENGLISH,
        register_id=uuid.uuid4(),
        content={"placeholder": "x"},
        rationale_id=uuid.uuid4(),
        llm_call_record_ids=[uuid.uuid4()],
        upstream_module_outputs=[],
        created_at=datetime.now(UTC),
    )


# ── upstream_module_ids_for ────────────────────────────────────────


def test_upstream_for_strategy_theme_is_empty():
    assert upstream_module_ids_for(ModuleId.STRATEGY_THEME, set(ModuleId)) == []


def test_upstream_for_tone_includes_strategy_when_both_active():
    upstream = upstream_module_ids_for(
        ModuleId.TONE,
        {ModuleId.STRATEGY_THEME, ModuleId.TONE},
    )
    assert upstream == [ModuleId.STRATEGY_THEME]


def test_upstream_for_tagline_includes_all_three_when_active():
    upstream = upstream_module_ids_for(ModuleId.TAGLINE, set(ModuleId))
    assert ModuleId.STRATEGY_THEME in upstream
    assert ModuleId.TONE in upstream
    # Slogan and Tagline don't share an intersection pair (per INTERSECTION_PAIRS)
    # — the only Tagline upstreams are Strategy and Tone.
    assert ModuleId.SLOGAN not in upstream
    assert ModuleId.NAMING not in upstream


def test_upstream_excluded_when_module_not_in_scope():
    upstream = upstream_module_ids_for(
        ModuleId.TAGLINE,
        {ModuleId.TONE, ModuleId.TAGLINE},  # no Strategy in scope
    )
    assert upstream == [ModuleId.TONE]


def test_upstream_returned_in_canonical_order():
    upstream = upstream_module_ids_for(ModuleId.TAGLINE, set(ModuleId))
    # Strategy must precede Tone
    assert upstream.index(ModuleId.STRATEGY_THEME) < upstream.index(ModuleId.TONE)


def test_upstream_for_target_outside_scope_returns_empty():
    assert upstream_module_ids_for(ModuleId.TONE, {ModuleId.STRATEGY_THEME}) == []


# ── build_upstream_outputs ─────────────────────────────────────────


def test_build_upstream_outputs_returns_completed_only():
    sid = uuid.uuid4()
    completed = {ModuleId.STRATEGY_THEME: _output(ModuleId.STRATEGY_THEME, sid)}
    # Tone's intersection upstreams are Strategy. Strategy is completed → returned.
    upstream = build_upstream_outputs(
        ModuleId.TONE,
        completed,
        {ModuleId.STRATEGY_THEME, ModuleId.TONE},
    )
    assert "strategy_theme" in upstream
    assert isinstance(upstream["strategy_theme"], ModuleOutput)
