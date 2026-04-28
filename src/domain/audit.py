import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from src.domain.language import Language
from src.domain.module import ModuleId


class LLMCallStatus(StrEnum):
    """Outcome of one LLM Provider invocation."""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


class LLMCallRecord(BaseModel):
    """Audit record for a single LLM invocation.

    Per CLAUDE.md §2.8 every call through the LLM Provider Abstraction creates
    one of these. The record is not itself language-tagged content — it is
    metadata describing which language was directed.

    `module` is None for the Narrative Generator's call (which is not module-
    specific). `register_id` is None for calls made before the LanguageRegister
    has been derived (e.g., during Discovery before the resolver runs).
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    session_id: uuid.UUID
    module: ModuleId | None = None
    prompt_hash: str
    model_version: str
    language_directive: Language
    register_id: uuid.UUID | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    response_text: str
    latency_ms: int
    status: LLMCallStatus
    error_message: str | None = None
    called_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
