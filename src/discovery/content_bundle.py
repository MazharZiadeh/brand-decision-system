"""ContentBundle — the validated content loaded at app startup.

`simple_rules` is a list of domain `Rule` objects (single-question
RuleTrigger). `inferred_rules` and `register_rules` are dicts because
the corresponding Pydantic models do not yet support the compound
condition shapes those YAML blocks use; they are structurally validated
by the Discovery Service components that consume them, not by Pydantic.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from src.domain.pain import PainTaxonomy, Rule
from src.domain.questionnaire import QuestionnaireVersion


class ContentBundle(BaseModel):
    """Everything the Discovery Service needs to start, validated and ready."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    questionnaire_en: QuestionnaireVersion
    questionnaire_ar: QuestionnaireVersion
    pain_taxonomy: PainTaxonomy
    simple_rules: list[Rule]
    inferred_rules: list[dict[str, Any]]
    register_rules: dict[str, Any]
