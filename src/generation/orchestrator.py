"""Generation Orchestrator — walks the ExecutionPlan and runs every module.

Pure assembly: prompt builder + module runner + upstream helper, run
serially in canonical order. The orchestrator collects outputs and audit
records as it goes; on a module failure it raises `GenerationError`
with everything that already succeeded attached so the caller (Session
8) can persist partial progress.

The orchestrator does NOT persist anything itself. Per CLAUDE.md §2.1
it is pure-logic-plus-LLM-via-provider; the caller owns transactions
and DB writes.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from src.domain.audit import LLMCallRecord
from src.domain.brand_dna_context import BrandDNAContext
from src.domain.module import ExecutionPlan, ModuleId, ModuleOutput
from src.domain.pain import PainAnalysis, PainCategory
from src.domain.register import LanguageRegister
from src.generation.exceptions import GenerationError
from src.generation.module_runner import run_module
from src.generation.prompt_builder import build_module_prompt
from src.generation.upstream import upstream_module_ids_for
from src.llm.provider import LLMProvider


@dataclass(frozen=True)
class GenerationResult:
    """The outcome of a successful `run_generation`.

    `module_outputs` preserves canonical execution order via dict insertion
    order. `call_records` is one record per module, in call order.
    """

    module_outputs: dict[ModuleId, ModuleOutput] = field(default_factory=dict)
    call_records: list[LLMCallRecord] = field(default_factory=list)


async def run_generation(
    execution_plan: ExecutionPlan,
    brand_dna_context: BrandDNAContext,
    pain_analysis: PainAnalysis,
    pain_categories: list[PainCategory],
    register: LanguageRegister,
    session_id: uuid.UUID,
    llm_provider: LLMProvider,
) -> GenerationResult:
    """Run every module in the plan, in canonical order, returning the full result set.

    Raises `GenerationError` if any module fails; partial progress is attached.
    """
    scope_modules: set[ModuleId] = set(execution_plan.ordered_modules)
    completed: dict[ModuleId, ModuleOutput] = {}
    call_records: list[LLMCallRecord] = []

    for target in execution_plan.ordered_modules:
        try:
            rendered_prompt = build_module_prompt(
                target,
                brand_dna_context,
                pain_analysis,
                pain_categories,
                register,
                completed,
                scope_modules,
            )
            upstream_ids = [
                completed[m].id
                for m in upstream_module_ids_for(target, scope_modules)
                if m in completed
            ]
            output, record = await run_module(
                target,
                rendered_prompt=rendered_prompt,
                language=register.primary_language,
                register_id=register.id,
                session_id=session_id,
                upstream_module_output_ids=upstream_ids,
                llm_provider=llm_provider,
            )
            completed[target] = output
            call_records.append(record)
        except Exception as e:
            # Capture any audit record the LLM provider attached on failure.
            failure_record = getattr(e, "call_record", None)
            if failure_record is not None:
                call_records.append(failure_record)
            raise GenerationError(
                f"Generation failed at module {target.value}: {e}",
                completed_outputs=completed,
                call_records_so_far=call_records,
                original_exception=e,
            ) from e

    return GenerationResult(module_outputs=completed, call_records=call_records)
