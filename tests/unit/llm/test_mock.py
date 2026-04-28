"""Behavioral tests for MockLLMProvider.

These cover the registration/lookup contract, the audit-record fields the
mock must populate, latency injection, error injection, and the
hash-specific-vs-default response precedence.
"""

import uuid

import pytest

from src.domain.audit import LLMCallStatus
from src.domain.language import Language
from src.domain.module import ModuleId
from src.domain.module_outputs import StrategyThemeOutput, ToneOutput
from src.domain.rationale import PriorityFactor
from src.llm.exceptions import (
    LLMProviderError,
    LLMSchemaValidationError,
    LLMTimeoutError,
)
from src.llm.mock import MockLLMProvider
from src.llm.models import ModelVersion
from src.llm.provider import LLMCallRequest


def _factors() -> list[PriorityFactor]:
    return [
        PriorityFactor(factor_name="A", how_addressed="…"),
        PriorityFactor(factor_name="B", how_addressed="…"),
    ]


def _strategy_output() -> StrategyThemeOutput:
    return StrategyThemeOutput(
        language=Language.ENGLISH,
        theme="Quietly engineered for substance over signal.",
        elaboration="The brand commits to substance over signal across every customer touchpoint.",
        priority_factors_addressed=_factors(),
    )


def _tone_output() -> ToneOutput:
    return ToneOutput(
        language=Language.ENGLISH,
        descriptor="Quietly confident.",
        do_examples=["a", "b", "c"],
        dont_examples=["x", "y", "z"],
        priority_factors_addressed=_factors(),
    )


def _request(schema_name: str = "StrategyThemeOutput", **overrides) -> LLMCallRequest:
    base = {
        "rendered_prompt": "…rendered prompt for tests…",
        "output_schema_name": schema_name,
        "language": Language.ENGLISH,
        "session_id": uuid.uuid4(),
    }
    base.update(overrides)
    return LLMCallRequest(**base)


# ── happy path ─────────────────────────────────────────────────────────


async def test_call_with_registered_response_returns_typed_instance():
    provider = MockLLMProvider()
    expected = _strategy_output()
    provider.register_response("StrategyThemeOutput", expected)

    response = await provider.call(_request(), StrategyThemeOutput)

    assert response.parsed_output is expected
    assert isinstance(response.parsed_output, StrategyThemeOutput)


# ── registration failures ──────────────────────────────────────────────


async def test_call_without_registered_response_raises():
    provider = MockLLMProvider()
    with pytest.raises(LLMSchemaValidationError) as ei:
        await provider.call(_request(), StrategyThemeOutput)
    assert "register_response" in str(ei.value)


async def test_registered_wrong_schema_raises():
    provider = MockLLMProvider()
    provider.register_response("StrategyThemeOutput", _tone_output())
    with pytest.raises(LLMSchemaValidationError) as ei:
        await provider.call(_request(), StrategyThemeOutput)
    assert "ToneOutput" in str(ei.value)
    assert "StrategyThemeOutput" in str(ei.value)


# ── audit record correctness ──────────────────────────────────────────


async def test_call_record_populated_with_required_fields():
    provider = MockLLMProvider()
    provider.register_response("StrategyThemeOutput", _strategy_output())
    register_id = uuid.uuid4()
    response = await provider.call(
        _request(module=ModuleId.STRATEGY_THEME, register_id=register_id),
        StrategyThemeOutput,
    )
    rec = response.call_record
    assert rec.session_id == response.call_record.session_id
    assert rec.module == ModuleId.STRATEGY_THEME
    assert rec.register_id == register_id
    assert rec.language_directive == Language.ENGLISH
    assert rec.model_version == ModelVersion.MOCK_FIXED.value
    assert rec.prompt_hash  # non-empty
    assert rec.response_text  # JSON-dumped
    assert rec.status == LLMCallStatus.SUCCESS
    assert rec.latency_ms >= 0
    assert rec.parameters == {"temperature": 0.7, "max_tokens": 2000}


async def test_call_record_prompt_hash_is_deterministic():
    provider = MockLLMProvider()
    provider.register_response("StrategyThemeOutput", _strategy_output())
    req1 = _request()
    # Re-use the same prompt by constructing two requests with identical text
    req2 = LLMCallRequest(
        rendered_prompt=req1.rendered_prompt,
        output_schema_name=req1.output_schema_name,
        language=req1.language,
        session_id=uuid.uuid4(),
    )
    r1 = await provider.call(req1, StrategyThemeOutput)
    r2 = await provider.call(req2, StrategyThemeOutput)
    assert r1.call_record.prompt_hash == r2.call_record.prompt_hash


async def test_call_record_prompt_hash_differs_for_different_prompts():
    provider = MockLLMProvider()
    provider.register_response("StrategyThemeOutput", _strategy_output())
    r1 = await provider.call(
        _request(rendered_prompt="prompt one"),
        StrategyThemeOutput,
    )
    r2 = await provider.call(
        _request(rendered_prompt="prompt two — different"),
        StrategyThemeOutput,
    )
    assert r1.call_record.prompt_hash != r2.call_record.prompt_hash


async def test_module_field_passes_through_to_record():
    provider = MockLLMProvider()
    provider.register_response("StrategyThemeOutput", _strategy_output())
    response = await provider.call(
        _request(module=ModuleId.STRATEGY_THEME),
        StrategyThemeOutput,
    )
    assert response.call_record.module == ModuleId.STRATEGY_THEME


async def test_register_id_passes_through_to_record():
    provider = MockLLMProvider()
    provider.register_response("StrategyThemeOutput", _strategy_output())
    rid = uuid.uuid4()
    response = await provider.call(_request(register_id=rid), StrategyThemeOutput)
    assert response.call_record.register_id == rid


def test_session_id_required_on_request():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        LLMCallRequest(  # type: ignore[call-arg]
            rendered_prompt="…",
            output_schema_name="StrategyThemeOutput",
            language=Language.ENGLISH,
        )


# ── injection helpers ──────────────────────────────────────────────────


async def test_inject_latency_simulates_delay():
    provider = MockLLMProvider()
    provider.register_response("StrategyThemeOutput", _strategy_output())
    provider.inject_latency(50)
    response = await provider.call(_request(), StrategyThemeOutput)
    assert response.call_record.latency_ms >= 40  # tolerate small jitter


async def test_inject_error_raises_then_resets():
    provider = MockLLMProvider()
    provider.register_response("StrategyThemeOutput", _strategy_output())
    provider.inject_error(LLMTimeoutError("simulated timeout"))

    with pytest.raises(LLMTimeoutError) as ei:
        await provider.call(_request(), StrategyThemeOutput)
    # Exception carries the audit record
    assert ei.value.call_record is not None
    assert ei.value.call_record.status == LLMCallStatus.TIMEOUT

    # Second call succeeds (one-shot reset)
    response = await provider.call(_request(), StrategyThemeOutput)
    assert response.parsed_output.theme.startswith("Quietly")


async def test_injected_provider_error_carries_call_record_with_error_status():
    provider = MockLLMProvider()
    provider.register_response("StrategyThemeOutput", _strategy_output())
    provider.inject_error(LLMProviderError("simulated failure"))

    with pytest.raises(LLMProviderError) as ei:
        await provider.call(_request(), StrategyThemeOutput)
    assert ei.value.call_record is not None
    assert ei.value.call_record.status == LLMCallStatus.ERROR


# ── call counting ──────────────────────────────────────────────────────


async def test_call_count_increments():
    provider = MockLLMProvider()
    provider.register_response("StrategyThemeOutput", _strategy_output())
    assert provider.call_count == 0
    await provider.call(_request(), StrategyThemeOutput)
    await provider.call(_request(), StrategyThemeOutput)
    assert provider.call_count == 2


async def test_call_count_increments_on_error_too():
    """Failed calls still consumed the slot — counter reflects attempts, not successes."""
    provider = MockLLMProvider()
    provider.inject_error(LLMTimeoutError("…"))
    with pytest.raises(LLMTimeoutError):
        await provider.call(_request(), StrategyThemeOutput)
    assert provider.call_count == 1


# ── precedence: hash-specific vs default ───────────────────────────────


async def test_prompt_hash_specific_response_takes_precedence_over_default():
    provider = MockLLMProvider()
    default = _strategy_output()
    specific = StrategyThemeOutput(
        language=Language.ENGLISH,
        theme="Specific theme for the matching prompt.",
        elaboration="…",
        priority_factors_addressed=_factors(),
    )
    matching_prompt = "exact prompt text"
    matching_hash = MockLLMProvider._compute_prompt_hash(matching_prompt)

    provider.register_response("StrategyThemeOutput", default)
    provider.register_response("StrategyThemeOutput", specific, prompt_hash=matching_hash)

    # Matching prompt → specific
    matching_resp = await provider.call(
        _request(rendered_prompt=matching_prompt),
        StrategyThemeOutput,
    )
    assert matching_resp.parsed_output is specific

    # Non-matching prompt → default
    other_resp = await provider.call(
        _request(rendered_prompt="some other prompt"),
        StrategyThemeOutput,
    )
    assert other_resp.parsed_output is default
