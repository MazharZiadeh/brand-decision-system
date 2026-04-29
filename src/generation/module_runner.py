"""Base Module Runner — one generic function for every module.

Per-module differences (output schema, template path) live in the
registry; per-call differences (rendered prompt, upstream output ids,
register/session metadata) are passed in by the caller (the
orchestrator). This file has zero per-module specialization.

Per CLAUDE.md §2.2 every LLM call goes through the provider chokepoint.
Per §2.7 every output carries its rationale (a fresh `rationale_id` is
generated; persistence of the actual `Rationale` object is the
caller's job — Session 8 territory). Per §2.8 every call's audit
record is returned alongside the output for the caller to persist.
"""

from __future__ import annotations

import uuid

from src.domain.audit import LLMCallRecord
from src.domain.language import Language
from src.domain.module import ModuleId, ModuleOutput
from src.generation.registry import get_module_config
from src.llm.provider import LLMCallRequest, LLMProvider


async def run_module(
    target_module: ModuleId,
    rendered_prompt: str,
    language: Language,
    register_id: uuid.UUID,
    session_id: uuid.UUID,
    upstream_module_output_ids: list[uuid.UUID],
    llm_provider: LLMProvider,
) -> tuple[ModuleOutput, LLMCallRecord]:
    """Run one module's LLM call and assemble the resulting `ModuleOutput`.

    Returns the typed `ModuleOutput` plus the `LLMCallRecord` from the
    provider. The caller (orchestrator) collects records across the run
    and persists them (Session 8).
    """
    config = get_module_config(target_module)

    request = LLMCallRequest(
        rendered_prompt=rendered_prompt,
        output_schema_name=config.output_schema.__name__,
        language=language,
        register_id=register_id,
        module=target_module,
        session_id=session_id,
    )
    response = await llm_provider.call(request, config.output_schema)

    module_output = ModuleOutput(
        session_id=session_id,
        module=target_module,
        language=language,
        register_id=register_id,
        content=response.parsed_output.model_dump(mode="json"),
        upstream_module_outputs=list(upstream_module_output_ids),
        rationale_id=uuid.uuid4(),
        llm_call_record_ids=[response.call_record.id],
    )
    return module_output, response.call_record
