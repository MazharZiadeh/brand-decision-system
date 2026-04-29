"""LLM output schema for the Pain Narrative Generator.

The pain narrative is the only LLM call inside Discovery: a 3-5 sentence
elaboration of the brand's tagged pains, contextualizing them with the
Brand DNA. Per CLAUDE.md §2.7 it carries `priority_factors_addressed`
just like every module output.
"""

from __future__ import annotations

from pydantic import Field

from src.domain.language import LanguageTagged
from src.domain.rationale import PriorityFactor


class PainNarrativeOutput(LanguageTagged):
    """Pain Narrative Generator output: a structured narrative + rationale."""

    narrative: str = Field(..., min_length=50, max_length=2000)
    priority_factors_addressed: list[PriorityFactor] = Field(..., min_length=2)
