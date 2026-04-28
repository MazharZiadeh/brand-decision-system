"""The LLM Provider Protocol — the single chokepoint per CLAUDE.md §2.2.

Every LLM call in the entire system goes through a class implementing
`LLMProvider`. Code outside `src/llm/` never imports an LLM SDK; it builds
an `LLMCallRequest`, calls `provider.call(request, OutputSchema)`, and
receives a typed `LLMCallResponse[OutputSchema]` plus an `LLMCallRecord`
ready to persist.

Design choices encoded here:
- Structured output is the only contract. Free-text LLM output is not in
  M1 — every call returns a Pydantic instance that validated against a
  schema.
- `LLMCallRequest.output_schema_name` is a string so the request itself is
  serializable for audit; the actual `output_schema` class is passed
  separately to `call()`. The provider verifies they match.
- The provider type itself is a `typing.Protocol`, not an ABC. Implementations
  do not need to inherit from `LLMProvider` — they just need to expose the
  same surface. Mocks, real adapters, and test stubs all coexist.
"""

from __future__ import annotations

import uuid
from typing import Generic, Protocol, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from src.domain.audit import LLMCallRecord
from src.domain.language import Language
from src.domain.module import ModuleId
from src.llm.models import ModelVersion

T = TypeVar("T", bound=BaseModel)


class LLMCallParameters(BaseModel):
    """Provider-agnostic call parameters.

    Each provider adapter maps these to its SDK's parameter names. New
    parameters are added here only when at least one provider needs them
    AND the cross-provider semantics are well-defined.
    """

    model_config = ConfigDict(frozen=True)

    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, gt=0)


class LLMCallRequest(BaseModel):
    """Everything needed to make one LLM call.

    `rendered_prompt` is the FULL string sent to the model — preamble + module
    extension already merged by the prompt builder.

    `output_schema_name` is the Pydantic class's `__name__`. The actual class
    object is passed alongside the request to `call()` because Pydantic class
    objects do not serialize cleanly into an audit record.

    `language` is the directive language for this call — drives audit and
    register-tagging at the persistence boundary.

    `register_id` ties the call back to the `LanguageRegister` that shaped
    it (per §2.4 audit chain). May be None for calls made before the
    resolver runs (e.g., the initial Pain Narrative call during Discovery).

    `module` is None for non-module calls (e.g., the Pain Narrative
    Generator). When set, downstream queries can group records per module.

    `session_id` ties the call to a `Session` for audit + cleanup.
    """

    model_config = ConfigDict(frozen=True)

    rendered_prompt: str
    output_schema_name: str
    language: Language
    register_id: uuid.UUID | None = None
    module: ModuleId | None = None
    session_id: uuid.UUID
    parameters: LLMCallParameters = Field(default_factory=LLMCallParameters)


class LLMCallResponse(BaseModel, Generic[T]):
    """The result of one successful LLM call.

    `parsed_output` is the typed Pydantic instance, already validated.
    `raw_response_text` is what the model literally returned, for audit and
    debugging. `call_record` is the audit record — every call produces one,
    no exceptions; persist it via `LLMCallRecordRepository`.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    parsed_output: T
    raw_response_text: str
    call_record: LLMCallRecord


class LLMProvider(Protocol):
    """The single chokepoint for every LLM call in the system.

    Implementations MUST:
      - Honor the `LLMCallRequest` contract.
      - Return a typed `LLMCallResponse[T]` whose `parsed_output` is an
        instance of the `output_schema` passed to `call()`.
      - Produce an `LLMCallRecord` on every call attempt — populated on the
        success path inside the response, populated on the failure path on
        the raised exception's `call_record` attribute.
      - Raise `LLMSchemaValidationError` when the model response cannot be
        parsed into `output_schema`.
      - Raise `LLMTimeoutError` when the provider's deadline is exceeded.
      - Raise other `LLMProviderError` subclasses for everything else.

    Implementations MAY:
      - Accept additional configuration through their `__init__` (model
        selection, system-prompt overrides, retry policies, etc.).

    Implementations MUST NOT:
      - Import an LLM SDK from outside `src/llm/`.
      - Persist the audit record themselves — the caller does that via the
        repository, after every call.
    """

    model_version: ModelVersion

    async def call(
        self,
        request: LLMCallRequest,
        output_schema: type[T],
    ) -> LLMCallResponse[T]:
        """Make one LLM call, return parsed output + audit record."""
        ...
