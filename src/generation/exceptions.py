"""Generation-Service-specific exceptions.

`GenerationError` carries partial progress so a caller (Session 8) can
persist whatever modules completed before a failure. The records-so-far
are also surfaced so the audit trail does not lose the calls that
already happened — CLAUDE.md §2.8 holds even on the failure path.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.audit import LLMCallRecord
    from src.domain.module import ModuleId, ModuleOutput


class GenerationError(Exception):
    """Raised by `run_generation` when a module fails partway through.

    `completed_outputs` is the set of modules that successfully produced
    output before the failure (canonical order preserved by dict insertion
    order). `call_records_so_far` is every audit record collected — both
    successful calls and the failing call's record if the underlying
    LLM exception attached one.

    `original_exception` is the underlying error so the caller can
    distinguish (e.g.) timeout from schema-validation failures.
    """

    def __init__(
        self,
        message: str,
        *,
        completed_outputs: dict[ModuleId, ModuleOutput] | None = None,
        call_records_so_far: list[LLMCallRecord] | None = None,
        original_exception: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.completed_outputs = completed_outputs if completed_outputs is not None else {}
        self.call_records_so_far = call_records_so_far if call_records_so_far is not None else []
        self.original_exception = original_exception
