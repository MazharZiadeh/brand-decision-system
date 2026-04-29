"""Pain-tagging Rules Engine.

Pure-logic component per CLAUDE.md §2.1 — no LLM, no I/O, no async.
Two phases:
  1. Simple rules (`Rule` objects from src.domain.pain) with a
     single-question RuleTrigger.
  2. Inferred rules (dicts with compound `trigger.all_of` blocks) —
     these live as raw dicts because the domain RuleTrigger does not
     yet model compound conditions.

Output is a deduplicated list of `PainCategory` objects in the
canonical taxonomy order (so the same rule set always produces the
same list, satisfying CLAUDE.md §2.9 routing determinism).
"""

from __future__ import annotations

from typing import Any

from src.discovery.condition_evaluator import evaluate_condition
from src.domain.pain import PainCategory, PainTaxonomy, Rule
from src.domain.questionnaire import Answer


def tag_pain_categories(
    answers: list[Answer],
    simple_rules: list[Rule],
    inferred_rules: list[dict[str, Any]],
    pain_taxonomy: PainTaxonomy,
) -> list[PainCategory]:
    """Apply rules to answers and return tagged pain categories.

    The result is in canonical taxonomy order, deduplicated by id. A
    pain category triggered through both a simple rule and an inferred
    rule appears exactly once.
    """
    tagged_ids: set[str] = set()

    # Phase 1: simple rules — each Rule has a single-question RuleTrigger.
    for rule in simple_rules:
        condition = {
            "question_id": rule.trigger.question_id,
            "operator": rule.trigger.operator,
            "value": rule.trigger.value,
        }
        if evaluate_condition(condition, answers):
            tagged_ids.add(rule.pain_category_id)

    # Phase 2: inferred rules — compound conditions kept in dict form.
    # The YAML stores the compound condition under the `trigger` key.
    for inferred in inferred_rules:
        if evaluate_condition(inferred["trigger"], answers):
            tagged_ids.add(inferred["pain_category_id"])

    return [c for c in pain_taxonomy.categories if c.id in tagged_ids]
