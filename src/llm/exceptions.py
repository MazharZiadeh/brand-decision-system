"""LLM provider exception hierarchy.

Every failure path inside `src/llm/` raises a subclass of `LLMProviderError`
so callers can `except LLMProviderError` once and route on the specific
subtype when they need to.

Errors carry an optional `call_record: LLMCallRecord` attribute populated
by the provider on the failure path so callers can persist an audit record
even when the call did not return a parsed output, honoring CLAUDE.md §2.8
(every LLM call is audited).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.audit import LLMCallRecord


class LLMProviderError(Exception):
    """Base class for LLM provider failures.

    `call_record` is populated by the provider on failure when enough context
    exists to build one (model version + prompt hash + status known). Callers
    that want a complete audit trail catch the exception and persist
    `e.call_record` if not None.
    """

    def __init__(
        self,
        message: str,
        *,
        call_record: LLMCallRecord | None = None,
    ) -> None:
        super().__init__(message)
        self.call_record = call_record


class LLMSchemaValidationError(LLMProviderError):
    """Provider response could not be parsed into the requested output schema."""


class LLMTimeoutError(LLMProviderError):
    """Provider call exceeded its timeout budget."""


class LLMRateLimitError(LLMProviderError):
    """Provider returned a rate-limit error.

    Carries optional `retry_after_seconds` metadata so callers can implement
    backoff without provider-specific knowledge.
    """

    def __init__(
        self,
        message: str,
        *,
        retry_after_seconds: float | None = None,
        call_record: LLMCallRecord | None = None,
    ) -> None:
        super().__init__(message, call_record=call_record)
        self.retry_after_seconds = retry_after_seconds
