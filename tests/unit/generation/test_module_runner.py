"""Tests for the base module runner."""

from __future__ import annotations

import uuid

import pytest

from src.domain.language import Language
from src.domain.module import ModuleId
from src.domain.module_outputs import (
    NameCandidate,
    NamingOutput,
    SloganOption,
    SloganOutput,
    StrategyThemeOutput,
    TaglineOption,
    TaglineOutput,
    ToneOutput,
)
from src.domain.rationale import PriorityFactor
from src.generation.module_runner import run_module
from src.llm.exceptions import LLMTimeoutError
from src.llm.mock import MockLLMProvider


def _factors() -> list[PriorityFactor]:
    return [
        PriorityFactor(factor_name="A", how_addressed="…"),
        PriorityFactor(factor_name="B", how_addressed="…"),
    ]


def _strategy_output() -> StrategyThemeOutput:
    return StrategyThemeOutput(
        language=Language.ENGLISH,
        theme="Quietly engineered for the Saudi professional who wants quality without theatre.",
        elaboration="The brand commits to substance over signal across every customer touchpoint.",
        priority_factors_addressed=_factors(),
    )


def _tone_output() -> ToneOutput:
    return ToneOutput(
        language=Language.ENGLISH,
        descriptor="Quietly confident.",
        do_examples=["one", "two", "three"],
        dont_examples=["a", "b", "c"],
        priority_factors_addressed=_factors(),
    )


def _naming_output() -> NamingOutput:
    return NamingOutput(
        language=Language.ENGLISH,
        candidates=[
            NameCandidate(name="A", rationale="…"),
            NameCandidate(name="B", rationale="…"),
            NameCandidate(name="C", rationale="…"),
        ],
        priority_factors_addressed=_factors(),
    )


def _slogan_output() -> SloganOutput:
    return SloganOutput(
        language=Language.ENGLISH,
        options=[
            SloganOption(slogan="X", rationale="…"),
            SloganOption(slogan="Y", rationale="…"),
        ],
        priority_factors_addressed=_factors(),
    )


def _tagline_output() -> TaglineOutput:
    return TaglineOutput(
        language=Language.ENGLISH,
        options=[
            TaglineOption(tagline="P", rationale="…", intended_feeling="trust"),
            TaglineOption(tagline="Q", rationale="…", intended_feeling="trust"),
        ],
        priority_factors_addressed=_factors(),
    )


# ── happy path ─────────────────────────────────────────────────────


async def test_run_strategy_theme_with_mock_returns_well_formed_output():
    provider = MockLLMProvider()
    expected = _strategy_output()
    provider.register_response("StrategyThemeOutput", expected)
    sid = uuid.uuid4()
    register_id = uuid.uuid4()

    output, record = await run_module(
        ModuleId.STRATEGY_THEME,
        rendered_prompt="…",
        language=Language.ENGLISH,
        register_id=register_id,
        session_id=sid,
        upstream_module_output_ids=[],
        llm_provider=provider,
    )

    assert output.module == ModuleId.STRATEGY_THEME
    assert output.session_id == sid
    assert output.register_id == register_id
    assert output.content["theme"] == expected.theme


async def test_run_module_uses_correct_output_schema_per_registry():
    """The LLM provider receives the right output_schema_name based on the registry."""
    provider = MockLLMProvider()
    provider.register_response("StrategyThemeOutput", _strategy_output())
    await run_module(
        ModuleId.STRATEGY_THEME,
        rendered_prompt="…",
        language=Language.ENGLISH,
        register_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        upstream_module_output_ids=[],
        llm_provider=provider,
    )
    # The mock would have raised LLMSchemaValidationError if the wrong schema name had been used.
    assert provider.call_count == 1


async def test_module_output_carries_register_id():
    provider = MockLLMProvider()
    provider.register_response("StrategyThemeOutput", _strategy_output())
    register_id = uuid.uuid4()
    output, _ = await run_module(
        ModuleId.STRATEGY_THEME,
        rendered_prompt="…",
        language=Language.ENGLISH,
        register_id=register_id,
        session_id=uuid.uuid4(),
        upstream_module_output_ids=[],
        llm_provider=provider,
    )
    assert output.register_id == register_id


async def test_module_output_carries_llm_call_record_ids():
    provider = MockLLMProvider()
    provider.register_response("StrategyThemeOutput", _strategy_output())
    output, record = await run_module(
        ModuleId.STRATEGY_THEME,
        rendered_prompt="…",
        language=Language.ENGLISH,
        register_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        upstream_module_output_ids=[],
        llm_provider=provider,
    )
    assert output.llm_call_record_ids == [record.id]


async def test_module_output_content_is_parsed_pydantic_dump():
    provider = MockLLMProvider()
    expected = _strategy_output()
    provider.register_response("StrategyThemeOutput", expected)
    output, _ = await run_module(
        ModuleId.STRATEGY_THEME,
        rendered_prompt="…",
        language=Language.ENGLISH,
        register_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        upstream_module_output_ids=[],
        llm_provider=provider,
    )
    expected_dump = expected.model_dump(mode="json")
    assert output.content == expected_dump


@pytest.mark.parametrize(
    "module_id,output_factory,schema_name",
    [
        (ModuleId.STRATEGY_THEME, _strategy_output, "StrategyThemeOutput"),
        (ModuleId.TONE, _tone_output, "ToneOutput"),
        (ModuleId.NAMING, _naming_output, "NamingOutput"),
        (ModuleId.SLOGAN, _slogan_output, "SloganOutput"),
        (ModuleId.TAGLINE, _tagline_output, "TaglineOutput"),
    ],
)
async def test_run_module_for_each_module_id(module_id, output_factory, schema_name):
    provider = MockLLMProvider()
    provider.register_response(schema_name, output_factory())
    output, _ = await run_module(
        module_id,
        rendered_prompt="…",
        language=Language.ENGLISH,
        register_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        upstream_module_output_ids=[],
        llm_provider=provider,
    )
    assert output.module == module_id


async def test_run_module_passes_upstream_ids_through_to_module_output():
    provider = MockLLMProvider()
    provider.register_response("ToneOutput", _tone_output())
    upstream_ids = [uuid.uuid4(), uuid.uuid4()]
    output, _ = await run_module(
        ModuleId.TONE,
        rendered_prompt="…",
        language=Language.ENGLISH,
        register_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        upstream_module_output_ids=upstream_ids,
        llm_provider=provider,
    )
    assert output.upstream_module_outputs == upstream_ids


async def test_run_module_propagates_provider_error():
    provider = MockLLMProvider()
    provider.inject_error(LLMTimeoutError("simulated"))
    with pytest.raises(LLMTimeoutError) as ei:
        await run_module(
            ModuleId.STRATEGY_THEME,
            rendered_prompt="…",
            language=Language.ENGLISH,
            register_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            upstream_module_output_ids=[],
            llm_provider=provider,
        )
    # Per Session 5's failure-path pattern, the exception carries the audit record.
    assert ei.value.call_record is not None


async def test_run_module_language_matches_request():
    provider = MockLLMProvider()
    provider.register_response("StrategyThemeOutput", _strategy_output())
    output, _ = await run_module(
        ModuleId.STRATEGY_THEME,
        rendered_prompt="…",
        language=Language.ARABIC,
        register_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        upstream_module_output_ids=[],
        llm_provider=provider,
    )
    assert output.language == Language.ARABIC
