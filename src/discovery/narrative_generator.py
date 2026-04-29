"""Pain Narrative Generator — the only LLM consumer in Discovery.

Renders `pain_narrative.j2` with the brand's DNA context plus the
tagged pain categories and language register, sends it through the
LLM Provider chokepoint, and returns a `(PainAnalysis, LLMCallRecord)`
pair. The caller persists both — typically inside the same DB
transaction — per CLAUDE.md §2.8.

The function does not mutate the inputs and does not directly persist
anything; it is the assembly seam between Discovery's deterministic
components (rules engine, resolver) and the LLM layer.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from src.discovery.exceptions import DiscoveryError
from src.domain.audit import LLMCallRecord
from src.domain.narrative_output import PainNarrativeOutput
from src.domain.pain import PainAnalysis, PainCategory
from src.domain.register import LanguageRegister
from src.llm.provider import LLMCallRequest, LLMProvider

_PROMPT_DIR = Path(__file__).resolve().parents[2] / "content" / "prompts"
_env = Environment(
    loader=FileSystemLoader(str(_PROMPT_DIR)),
    keep_trailing_newline=True,
    autoescape=False,
)


async def generate_pain_narrative(
    brand_dna_context: dict[str, Any],
    pain_categories: list[PainCategory],
    register: LanguageRegister,
    session_id: uuid.UUID,
    llm_provider: LLMProvider,
) -> tuple[PainAnalysis, LLMCallRecord]:
    """Generate the pain narrative for a session.

    `brand_dna_context` carries the keys the template expects: `brand`,
    `audience`, `voice`, `aspiration`. The function attaches `pain` and
    `register` itself (those are derived from the upstream Discovery
    components, not from the questionnaire directly).

    Returns the assembled `PainAnalysis` and the `LLMCallRecord` from
    the provider call. The caller persists both.
    """
    if not pain_categories:
        raise DiscoveryError(
            "Cannot generate a pain narrative without at least one tagged pain category."
        )

    template = _env.get_template("pain_narrative.j2")
    rendered_prompt = template.render(
        **brand_dna_context,
        pain={
            "tagged_categories": [c.model_dump() for c in pain_categories],
            "top_frustrations": brand_dna_context.get("top_frustrations", []),
        },
        register=register.model_dump(),
    )

    request = LLMCallRequest(
        rendered_prompt=rendered_prompt,
        output_schema_name="PainNarrativeOutput",
        language=register.primary_language,
        register_id=register.id,
        module=None,  # the pain narrative is not a module output
        session_id=session_id,
    )

    response = await llm_provider.call(request, PainNarrativeOutput)
    parsed = response.parsed_output

    pain_analysis = PainAnalysis(
        session_id=session_id,
        register_id=register.id,
        tagged_pain_categories=[c.id for c in pain_categories],
        narrative=parsed.narrative,
        rationale_id=uuid.uuid4(),
        llm_call_record_ids=[response.call_record.id],
        language=register.primary_language,
    )

    return pain_analysis, response.call_record
