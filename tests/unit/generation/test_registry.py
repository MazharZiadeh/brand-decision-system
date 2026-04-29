"""Tests for the Module Config Registry."""

from pathlib import Path

import pytest
from pydantic import BaseModel

from src.domain.module import ModuleId
from src.domain.module_outputs import (
    NamingOutput,
    SloganOutput,
    StrategyThemeOutput,
    TaglineOutput,
    ToneOutput,
)
from src.generation.registry import MODULE_REGISTRY, get_module_config

_PROMPT_DIR = Path(__file__).resolve().parents[3] / "content" / "prompts"


def test_registry_has_entry_for_every_module_id():
    """If a new ModuleId lands but the registry entry doesn't, this fails loud."""
    missing = set(ModuleId) - set(MODULE_REGISTRY.keys())
    extra = set(MODULE_REGISTRY.keys()) - set(ModuleId)
    assert not missing, f"Modules missing from registry: {missing}"
    assert not extra, f"Registry has unknown modules: {extra}"


def test_each_config_has_output_schema_subclass_of_basemodel():
    for module_id, config in MODULE_REGISTRY.items():
        assert issubclass(
            config.output_schema, BaseModel
        ), f"{module_id} output_schema is not a BaseModel subclass"


def test_each_config_template_path_exists_on_disk():
    for module_id, config in MODULE_REGISTRY.items():
        full_path = _PROMPT_DIR / config.template_path
        assert full_path.exists(), f"{module_id} template missing on disk: {full_path}"


@pytest.mark.parametrize(
    "module_id,expected_schema",
    [
        (ModuleId.STRATEGY_THEME, StrategyThemeOutput),
        (ModuleId.TONE, ToneOutput),
        (ModuleId.NAMING, NamingOutput),
        (ModuleId.SLOGAN, SloganOutput),
        (ModuleId.TAGLINE, TaglineOutput),
    ],
)
def test_get_module_config_returns_correct_entries(module_id, expected_schema):
    config = get_module_config(module_id)
    assert config.output_schema is expected_schema
    assert config.template_path.startswith("modules/")
