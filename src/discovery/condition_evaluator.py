"""Shared condition evaluator for the Rules Engine and Register Resolver.

Both consume the same condition DSL (single-question triggers and
compound `all_of` / `any_of` blocks). The evaluator dispatches by
operator and treats a missing answer as condition-false — that
behavior matches the existing rule semantics ("if the user didn't
answer Q3.1, no Q3.1-based rule fires").
"""

from __future__ import annotations

from typing import Any

from src.domain.questionnaire import Answer


def evaluate_condition(condition: dict[str, Any], answers: list[Answer]) -> bool:
    """Evaluate a single condition against a list of answers.

    Simple condition shape:
        {question_id: "q3.1", operator: "less_than", value: 40}

    Compound shapes:
        {all_of: [<condition>, ...]}
        {any_of: [<condition>, ...]}

    Returns True if the condition holds, False otherwise. Raises ValueError
    on malformed conditions (unknown operator, non-numeric comparison
    against a non-numeric answer).
    """
    if "all_of" in condition:
        return all(evaluate_condition(c, answers) for c in condition["all_of"])
    if "any_of" in condition:
        return any(evaluate_condition(c, answers) for c in condition["any_of"])

    qid = condition["question_id"]
    op = condition["operator"]
    expected = condition["value"]

    answer = next((a for a in answers if a.question_id == qid), None)
    if answer is None:
        return False  # missing answer treated as condition-false

    actual = answer.value

    match op:
        case "equals":
            return actual == expected
        case "less_than":
            return _coerce_number(actual) < expected
        case "greater_than":
            return _coerce_number(actual) > expected
        case "less_than_or_equal":
            return _coerce_number(actual) <= expected
        case "greater_than_or_equal":
            return _coerce_number(actual) >= expected
        case "in_set":
            # Multi-choice answers are list[str]; check intersection.
            if isinstance(actual, list):
                return any(item in expected for item in actual)
            return actual in expected
        case "contains":
            # Inverted in_set: any of `expected` present in actual list.
            if isinstance(actual, list):
                values = expected if isinstance(expected, list) else [expected]
                return any(v in actual for v in values)
            return False
        case _:
            raise ValueError(f"Unknown operator: {op!r}")


def _coerce_number(value: Any) -> int | float:
    if isinstance(value, int | float):
        return value
    raise ValueError(f"Cannot coerce {value!r} to number for slider comparison")
