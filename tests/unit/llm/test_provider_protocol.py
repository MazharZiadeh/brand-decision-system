"""Contract tests against the LLMProvider Protocol and request/response shapes.

These tests do NOT exercise the Mock — they exercise the Protocol itself,
including a tiny ad-hoc implementation that proves any class with the
right surface satisfies the Protocol without inheriting from it.
"""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import BaseModel, ValidationError

from src.domain.audit import LLMCallRecord, LLMCallStatus
from src.domain.language import Language
from src.domain.module import ModuleId
from src.llm.models import ModelVersion
from src.llm.provider import (
    LLMCallParameters,
    LLMCallRequest,
    LLMCallResponse,
    LLMProvider,
)


class _TinyOutput(BaseModel):
    """Local Pydantic model used only by these contract tests."""

    answer: str


# ── LLMCallParameters ──────────────────────────────────────────────────


def test_parameters_defaults_are_reasonable():
    p = LLMCallParameters()
    assert 0.0 <= p.temperature <= 2.0
    assert p.max_tokens > 0


def test_parameters_temperature_must_be_in_range():
    with pytest.raises(ValidationError):
        LLMCallParameters(temperature=2.5)


def test_parameters_max_tokens_must_be_positive():
    with pytest.raises(ValidationError):
        LLMCallParameters(max_tokens=0)


def test_parameters_is_frozen():
    p = LLMCallParameters()
    with pytest.raises(ValidationError):
        p.temperature = 1.0  # type: ignore[misc]


# ── LLMCallRequest ─────────────────────────────────────────────────────


def test_request_round_trips_required_fields():
    sid = uuid.uuid4()
    req = LLMCallRequest(
        rendered_prompt="…full rendered prompt…",
        output_schema_name="StrategyThemeOutput",
        language=Language.ENGLISH,
        session_id=sid,
    )
    assert req.session_id == sid
    assert req.module is None
    assert req.register_id is None


def test_request_session_id_is_required():
    with pytest.raises(ValidationError):
        LLMCallRequest(  # type: ignore[call-arg]
            rendered_prompt="…",
            output_schema_name="X",
            language=Language.ENGLISH,
        )


def test_request_module_passes_through():
    req = LLMCallRequest(
        rendered_prompt="…",
        output_schema_name="ToneOutput",
        language=Language.ARABIC,
        session_id=uuid.uuid4(),
        module=ModuleId.TONE,
        register_id=uuid.uuid4(),
    )
    assert req.module == ModuleId.TONE
    assert req.register_id is not None


def test_request_is_frozen():
    req = LLMCallRequest(
        rendered_prompt="…",
        output_schema_name="X",
        language=Language.ENGLISH,
        session_id=uuid.uuid4(),
    )
    with pytest.raises(ValidationError):
        req.rendered_prompt = "different"  # type: ignore[misc]


# ── LLMCallResponse ────────────────────────────────────────────────────


def _sample_call_record(session_id: uuid.UUID) -> LLMCallRecord:
    return LLMCallRecord(
        session_id=session_id,
        prompt_hash="a" * 16,
        model_version=ModelVersion.MOCK_FIXED.value,
        language_directive=Language.ENGLISH,
        response_text="…",
        latency_ms=42,
        status=LLMCallStatus.SUCCESS,
        called_at=datetime.now(UTC),
    )


def test_response_carries_parsed_output_and_record():
    sid = uuid.uuid4()
    resp = LLMCallResponse[_TinyOutput](
        parsed_output=_TinyOutput(answer="hi"),
        raw_response_text='{"answer":"hi"}',
        call_record=_sample_call_record(sid),
    )
    assert resp.parsed_output.answer == "hi"
    assert resp.call_record.session_id == sid


# ── LLMProvider Protocol ───────────────────────────────────────────────


class _StubProvider:
    """Minimal Protocol implementation, distinct from MockLLMProvider.

    Proves a class with the right surface satisfies LLMProvider without
    inheriting — the Protocol is structural, not nominal.
    """

    model_version = ModelVersion.MOCK_FIXED

    async def call(self, request, output_schema):  # type: ignore[no-untyped-def]
        return LLMCallResponse[output_schema](
            parsed_output=output_schema(answer="stub"),
            raw_response_text='{"answer":"stub"}',
            call_record=_sample_call_record(request.session_id),
        )


def test_stub_implementation_satisfies_protocol_structurally():
    stub: LLMProvider = _StubProvider()  # mypy / runtime: structural fit
    assert stub.model_version == ModelVersion.MOCK_FIXED


async def test_stub_implementation_can_be_called_through_protocol_surface():
    stub: LLMProvider = _StubProvider()
    req = LLMCallRequest(
        rendered_prompt="…",
        output_schema_name="_TinyOutput",
        language=Language.ENGLISH,
        session_id=uuid.uuid4(),
    )
    resp = await stub.call(req, _TinyOutput)
    assert resp.parsed_output.answer == "stub"
    assert resp.call_record.model_version == ModelVersion.MOCK_FIXED.value
