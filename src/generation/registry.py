"""Module Config Registry — typed mapping from ModuleId to (output_schema, template).

This is the single source of truth for "which Pydantic schema validates
the LLM's structured output for module X" and "which Jinja2 template
renders X's prompt". The base module runner reads this; nothing else
hardcodes per-module wiring.

If `ModuleId` ever gains a new member, the registry test will fail
loud — that's the point: drift between the enum and the registry can
never go silent.
"""

from __future__ import annotations

from typing import NamedTuple

from pydantic import BaseModel

from src.domain.module import ModuleId
from src.domain.module_outputs import (
    NamingOutput,
    SloganOutput,
    StrategyThemeOutput,
    TaglineOutput,
    ToneOutput,
)


class ModuleConfig(NamedTuple):
    """Per-module wiring: which schema validates the LLM output and which
    template renders the prompt. Template paths are relative to
    `content/prompts/`.
    """

    output_schema: type[BaseModel]
    template_path: str


MODULE_REGISTRY: dict[ModuleId, ModuleConfig] = {
    ModuleId.STRATEGY_THEME: ModuleConfig(
        output_schema=StrategyThemeOutput,
        template_path="modules/strategy_theme.j2",
    ),
    ModuleId.TONE: ModuleConfig(
        output_schema=ToneOutput,
        template_path="modules/tone.j2",
    ),
    ModuleId.NAMING: ModuleConfig(
        output_schema=NamingOutput,
        template_path="modules/naming.j2",
    ),
    ModuleId.SLOGAN: ModuleConfig(
        output_schema=SloganOutput,
        template_path="modules/slogan.j2",
    ),
    ModuleId.TAGLINE: ModuleConfig(
        output_schema=TaglineOutput,
        template_path="modules/tagline.j2",
    ),
}


def get_module_config(module_id: ModuleId) -> ModuleConfig:
    """Return the registry entry for a module. Raises KeyError if missing."""
    return MODULE_REGISTRY[module_id]
