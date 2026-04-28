"""In-memory mock implementation of `LLMProvider`.

Test code configures responses via `register_response()` BEFORE calling.
The mock does not synthesize realistic outputs and does not silently
fall back when no response is registered — both are properties tests
should explicitly opt into. Tests pass because the configured response
is what the test specified, not because the mock guessed correctly.

Latency and errors are injectable for one-shot use:
- `inject_latency(ms)` — next call sleeps that long, then resets
- `inject_error(exc)` — next call raises `exc`, then resets

Every call increments `call_count`, including failed calls.
"""

from __future__ import annotations

import asyncio
import hashlib
import uuid
from datetime import UTC, datetime
from typing import TypeVar

from pydantic import BaseModel

from src.domain.audit import LLMCallRecord, LLMCallStatus
from src.llm.exceptions import (
    LLMProviderError,
    LLMRateLimitError,
    LLMSchemaValidationError,
    LLMTimeoutError,
)
from src.llm.models import ModelVersion
from src.llm.provider import LLMCallRequest, LLMCallResponse

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider:
    """`LLMProvider`-compatible in-memory mock for tests."""

    model_version: ModelVersion = ModelVersion.MOCK_FIXED

    def __init__(self) -> None:
        # (schema_name, optional_prompt_hash) -> registered response instance
        self._responses: dict[tuple[str, str | None], BaseModel] = {}
        self._injected_latency_ms: int = 0
        self._injected_error: Exception | None = None
        self._call_count: int = 0

    # ── Configuration API used by tests ─────────────────────────────────

    def register_response(
        self,
        schema_name: str,
        instance: BaseModel,
        prompt_hash: str | None = None,
    ) -> None:
        """Register a response for a given schema.

        If `prompt_hash` is supplied, the registration applies only to calls
        whose computed prompt hash matches; the prompt-hash-specific entry
        wins over the default `(schema_name, None)` entry when both exist.
        """
        self._responses[(schema_name, prompt_hash)] = instance

    def inject_latency(self, ms: int) -> None:
        """Cause the next `call()` to sleep for `ms` milliseconds, then reset."""
        self._injected_latency_ms = ms

    def inject_error(self, error: Exception) -> None:
        """Cause the next `call()` to raise `error`, then reset."""
        self._injected_error = error

    @property
    def call_count(self) -> int:
        return self._call_count

    # ── LLMProvider Protocol implementation ─────────────────────────────

    async def call(
        self,
        request: LLMCallRequest,
        output_schema: type[T],
    ) -> LLMCallResponse[T]:
        self._call_count += 1
        started_at = datetime.now(UTC)
        prompt_hash = self._compute_prompt_hash(request.rendered_prompt)

        if self._injected_latency_ms:
            await asyncio.sleep(self._injected_latency_ms / 1000.0)
            self._injected_latency_ms = 0

        if self._injected_error is not None:
            err = self._injected_error
            self._injected_error = None
            self._raise_with_audit(err, request, prompt_hash, started_at)

        instance = self._responses.get(
            (request.output_schema_name, prompt_hash)
        ) or self._responses.get((request.output_schema_name, None))
        if instance is None:
            raise LLMSchemaValidationError(
                f"No mock response registered for schema {request.output_schema_name!r}. "
                "Call register_response() in your test setup."
            )

        if not isinstance(instance, output_schema):
            raise LLMSchemaValidationError(
                f"Registered response is {type(instance).__name__}, "
                f"but call requested {output_schema.__name__}."
            )

        ended_at = datetime.now(UTC)
        latency_ms = max(0, int((ended_at - started_at).total_seconds() * 1000))
        raw_text = instance.model_dump_json()

        call_record = LLMCallRecord(
            id=uuid.uuid4(),
            session_id=request.session_id,
            module=request.module,
            register_id=request.register_id,
            language_directive=request.language,
            model_version=self.model_version.value,
            prompt_hash=prompt_hash,
            parameters=request.parameters.model_dump(),
            response_text=raw_text,
            latency_ms=latency_ms,
            status=LLMCallStatus.SUCCESS,
            called_at=started_at,
        )

        return LLMCallResponse[output_schema](
            parsed_output=instance,
            raw_response_text=raw_text,
            call_record=call_record,
        )

    # ── helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _compute_prompt_hash(prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]

    def _raise_with_audit(
        self,
        error: Exception,
        request: LLMCallRequest,
        prompt_hash: str,
        started_at: datetime,
    ) -> None:
        """Build an LLMCallRecord with the right status and re-raise.

        Maps the exception type to a `LLMCallStatus`:
          - LLMTimeoutError → TIMEOUT
          - everything else → ERROR
        Attaches the record to the exception's `call_record` attribute so the
        caller can still persist an audit row for the failure.
        """
        status = (
            LLMCallStatus.TIMEOUT if isinstance(error, LLMTimeoutError) else LLMCallStatus.ERROR
        )
        ended_at = datetime.now(UTC)
        latency_ms = max(0, int((ended_at - started_at).total_seconds() * 1000))
        record = LLMCallRecord(
            id=uuid.uuid4(),
            session_id=request.session_id,
            module=request.module,
            register_id=request.register_id,
            language_directive=request.language,
            model_version=self.model_version.value,
            prompt_hash=prompt_hash,
            parameters=request.parameters.model_dump(),
            response_text="",
            latency_ms=latency_ms,
            status=status,
            error_message=str(error),
            called_at=started_at,
        )

        if isinstance(error, LLMProviderError | LLMRateLimitError):
            error.call_record = record
            raise error

        # Non-provider exception (programmer error in tests). Wrap so the
        # caller still gets a populated audit record.
        wrapped = LLMProviderError(str(error), call_record=record)
        wrapped.__cause__ = error
        raise wrapped
