"""Tests for the shared condition evaluator.

Parametrized across operators with both positive and negative cases,
plus compound `all_of` / `any_of` and missing-answer behavior.
"""

import uuid

import pytest

from src.discovery.condition_evaluator import evaluate_condition
from src.domain.language import Language
from src.domain.questionnaire import Answer


def _answer(question_id: str, value: str | int | list[str]) -> Answer:
    return Answer(question_id=question_id, value=value, language=Language.ENGLISH)


# ── equals ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "actual,expected,result",
    [
        ("premium", "premium", True),
        ("premium", "challenger", False),
        (42, 42, True),
        (42, 43, False),
        (["a", "b"], ["a", "b"], True),
    ],
)
def test_equals_operator(actual, expected, result):
    answers = [_answer("q1", actual)]
    assert (
        evaluate_condition({"question_id": "q1", "operator": "equals", "value": expected}, answers)
        is result
    )


# ── numeric comparisons ────────────────────────────────────────────


@pytest.mark.parametrize(
    "operator,actual,threshold,result",
    [
        ("less_than", 30, 40, True),
        ("less_than", 40, 40, False),
        ("greater_than", 50, 40, True),
        ("greater_than", 40, 40, False),
        ("less_than_or_equal", 40, 40, True),
        ("less_than_or_equal", 41, 40, False),
        ("greater_than_or_equal", 40, 40, True),
        ("greater_than_or_equal", 39, 40, False),
    ],
)
def test_numeric_comparison_operators(operator, actual, threshold, result):
    answers = [_answer("q1", actual)]
    assert (
        evaluate_condition({"question_id": "q1", "operator": operator, "value": threshold}, answers)
        is result
    )


def test_numeric_comparison_against_non_number_raises():
    answers = [_answer("q1", "not a number")]
    with pytest.raises(ValueError, match="Cannot coerce"):
        evaluate_condition({"question_id": "q1", "operator": "less_than", "value": 40}, answers)


# ── in_set ─────────────────────────────────────────────────────────


def test_in_set_with_single_value_actual_matches():
    answers = [_answer("q1.3", "premium")]
    assert evaluate_condition(
        {"question_id": "q1.3", "operator": "in_set", "value": ["premium", "challenger"]},
        answers,
    )


def test_in_set_with_single_value_actual_no_match():
    answers = [_answer("q1.3", "traditional")]
    assert not evaluate_condition(
        {"question_id": "q1.3", "operator": "in_set", "value": ["premium", "challenger"]},
        answers,
    )


def test_in_set_with_list_actual_intersects():
    answers = [_answer("q3.4", ["obscurity", "stagnation"])]
    assert evaluate_condition(
        {"question_id": "q3.4", "operator": "in_set", "value": ["obscurity"]},
        answers,
    )


def test_in_set_with_list_actual_no_intersection():
    answers = [_answer("q3.4", ["price_trap", "audience_drift"])]
    assert not evaluate_condition(
        {"question_id": "q3.4", "operator": "in_set", "value": ["obscurity"]},
        answers,
    )


# ── contains ───────────────────────────────────────────────────────


def test_contains_with_list_actual_finds_value():
    answers = [_answer("q3.4", ["obscurity", "confusion"])]
    assert evaluate_condition(
        {"question_id": "q3.4", "operator": "contains", "value": "confusion"},
        answers,
    )


def test_contains_with_list_actual_missing_value():
    answers = [_answer("q3.4", ["obscurity"])]
    assert not evaluate_condition(
        {"question_id": "q3.4", "operator": "contains", "value": "stagnation"},
        answers,
    )


def test_contains_with_non_list_actual_returns_false():
    answers = [_answer("q1", "premium")]
    assert not evaluate_condition(
        {"question_id": "q1", "operator": "contains", "value": "premium"},
        answers,
    )


# ── compound conditions ───────────────────────────────────────────


def test_all_of_requires_every_subcondition():
    answers = [_answer("q1.2", "established"), _answer("q5.1", 30)]
    cond = {
        "all_of": [
            {"question_id": "q1.2", "operator": "in_set", "value": ["established", "mature"]},
            {"question_id": "q5.1", "operator": "less_than", "value": 40},
        ]
    }
    assert evaluate_condition(cond, answers)


def test_all_of_fails_if_one_subcondition_fails():
    answers = [_answer("q1.2", "early"), _answer("q5.1", 30)]
    cond = {
        "all_of": [
            {"question_id": "q1.2", "operator": "in_set", "value": ["established", "mature"]},
            {"question_id": "q5.1", "operator": "less_than", "value": 40},
        ]
    }
    assert not evaluate_condition(cond, answers)


def test_any_of_passes_when_one_subcondition_passes():
    answers = [_answer("q1", "x")]
    cond = {
        "any_of": [
            {"question_id": "q1", "operator": "equals", "value": "x"},
            {"question_id": "q1", "operator": "equals", "value": "y"},
        ]
    }
    assert evaluate_condition(cond, answers)


def test_any_of_fails_when_all_fail():
    answers = [_answer("q1", "z")]
    cond = {
        "any_of": [
            {"question_id": "q1", "operator": "equals", "value": "x"},
            {"question_id": "q1", "operator": "equals", "value": "y"},
        ]
    }
    assert not evaluate_condition(cond, answers)


def test_nested_compound_condition():
    answers = [_answer("q1", "x"), _answer("q2", 50)]
    cond = {
        "all_of": [
            {"question_id": "q1", "operator": "equals", "value": "x"},
            {
                "any_of": [
                    {"question_id": "q2", "operator": "less_than", "value": 30},
                    {"question_id": "q2", "operator": "greater_than", "value": 40},
                ]
            },
        ]
    }
    assert evaluate_condition(cond, answers)


# ── missing answer + bad operator ─────────────────────────────────


def test_missing_answer_treated_as_condition_false():
    answers = [_answer("q1", "x")]
    assert not evaluate_condition(
        {"question_id": "q_missing", "operator": "equals", "value": "x"}, answers
    )


def test_unknown_operator_raises():
    answers = [_answer("q1", "x")]
    with pytest.raises(ValueError, match="Unknown operator"):
        evaluate_condition({"question_id": "q1", "operator": "fuzzy_match", "value": "x"}, answers)


def test_session_id_unused_helper():  # type: ignore
    # sanity import so pytest collects from a clean module
    assert uuid.uuid4()
