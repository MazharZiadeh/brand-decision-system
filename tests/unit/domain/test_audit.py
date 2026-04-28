import uuid

import pytest
from pydantic import ValidationError

from src.domain.audit import LLMCallRecord, LLMCallStatus
from src.domain.language import Language
from src.domain.module import ModuleId


def test_llm_call_status_values():
    assert {s.value for s in LLMCallStatus} == {"success", "error", "timeout"}


def test_valid_call_record_for_module():
    r = LLMCallRecord(
        session_id=uuid.uuid4(),
        module=ModuleId.STRATEGY_THEME,
        prompt_hash="a" * 64,
        model_version="claude-opus-4-7",
        language_directive=Language.ENGLISH,
        register_id=uuid.uuid4(),
        parameters={"temperature": 0.7},
        response_text="…",
        latency_ms=820,
        status=LLMCallStatus.SUCCESS,
    )
    assert r.module == ModuleId.STRATEGY_THEME
    assert r.error_message is None


def test_module_optional_for_narrative_generator_call():
    r = LLMCallRecord(
        session_id=uuid.uuid4(),
        prompt_hash="b" * 64,
        model_version="claude-opus-4-7",
        language_directive=Language.ARABIC,
        response_text="…",
        latency_ms=1500,
        status=LLMCallStatus.SUCCESS,
    )
    assert r.module is None


def test_register_id_optional_for_pre_register_calls():
    r = LLMCallRecord(
        session_id=uuid.uuid4(),
        prompt_hash="c" * 64,
        model_version="claude-opus-4-7",
        language_directive=Language.ENGLISH,
        register_id=None,
        response_text="…",
        latency_ms=400,
        status=LLMCallStatus.SUCCESS,
    )
    assert r.register_id is None


def test_required_fields_enforced():
    with pytest.raises(ValidationError):
        LLMCallRecord(  # type: ignore[call-arg]
            session_id=uuid.uuid4(),
            prompt_hash="d" * 64,
            model_version="claude-opus-4-7",
            language_directive=Language.ENGLISH,
            response_text="…",
            latency_ms=100,
        )
