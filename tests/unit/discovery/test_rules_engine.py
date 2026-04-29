"""Rules Engine tests against the real loaded content.

Each test constructs fixture answers designed to trigger a specific
pain category (or set of categories) and asserts the result. The real
content is loaded once per module so the tests exercise the actual
shipping rules, not a fake mini-set.
"""

from __future__ import annotations

import pytest

from src.discovery.loader import load_content_bundle
from src.discovery.rules_engine import tag_pain_categories
from src.domain.language import Language
from src.domain.questionnaire import Answer

_BUNDLE = load_content_bundle()


def _ans(question_id: str, value):
    return Answer(question_id=question_id, value=value, language=Language.ENGLISH)


def _baseline_answers() -> list[Answer]:
    """Bland answers that should NOT trigger any pain rule."""
    return [
        _ans("q1.2", "growing"),
        _ans("q1.3", "specialist"),
        _ans("q3.1", 70),  # high visibility (above the <40 threshold)
        _ans("q3.2", 70),  # differentiated
        _ans("q3.3", 70),  # clear
        _ans("q3.4", []),  # nothing selected
        _ans("q5.1", 70),  # reinventing posture
        _ans("q2.3", 70),  # aspirational audience
    ]


def _tag(answers: list[Answer]) -> set[str]:
    cats = tag_pain_categories(
        answers, _BUNDLE.simple_rules, _BUNDLE.inferred_rules, _BUNDLE.pain_taxonomy
    )
    return {c.id for c in cats}


# ── per-category: explicit Q3.4 selections ───────────────────────


@pytest.mark.parametrize(
    "selected_id",
    [
        "obscurity",
        "commoditization",
        "confusion",
        "stagnation",
        "price_trap",
        "audience_drift",
        "internal_misalignment",
        "action_misalignment",
        "wrong_recognition",
        "loyalty_no_referral",
    ],
)
def test_explicit_q34_selection_tags_corresponding_category(selected_id: str):
    answers = _baseline_answers()
    # Replace q3.4 with the single explicit selection.
    answers = [a for a in answers if a.question_id != "q3.4"]
    answers.append(_ans("q3.4", [selected_id]))
    assert selected_id in _tag(answers)


# ── slider rules ──────────────────────────────────────────────────


def test_visibility_slider_below_40_tags_obscurity():
    answers = _baseline_answers()
    answers = [a for a in answers if a.question_id != "q3.1"]
    answers.append(_ans("q3.1", 30))
    assert "obscurity" in _tag(answers)


def test_differentiation_slider_below_40_tags_commoditization():
    answers = _baseline_answers()
    answers = [a for a in answers if a.question_id != "q3.2"]
    answers.append(_ans("q3.2", 30))
    assert "commoditization" in _tag(answers)


def test_clarity_slider_below_40_tags_confusion():
    answers = _baseline_answers()
    answers = [a for a in answers if a.question_id != "q3.3"]
    answers.append(_ans("q3.3", 30))
    assert "confusion" in _tag(answers)


# ── inferred rules ────────────────────────────────────────────────


def test_inferred_stagnation_triggers_for_established_brand_defending():
    """Q1.2 ∈ {established, mature} AND Q5.1 < 40 → stagnation (latent)."""
    answers = _baseline_answers()
    answers = [a for a in answers if a.question_id not in {"q1.2", "q5.1", "q3.4"}]
    answers.extend(
        [
            _ans("q1.2", "established"),
            _ans("q5.1", 30),
            _ans("q3.4", []),  # no explicit stagnation selection
        ]
    )
    assert "stagnation" in _tag(answers)


def test_inferred_action_misalignment_triggers_for_premium_in_value_market():
    """Q2.3 < 30 AND Q1.3 == 'premium' → action_misalignment."""
    answers = _baseline_answers()
    answers = [a for a in answers if a.question_id not in {"q2.3", "q1.3", "q3.4"}]
    answers.extend(
        [
            _ans("q1.3", "premium"),
            _ans("q2.3", 20),
            _ans("q3.4", []),  # no explicit selection
        ]
    )
    assert "action_misalignment" in _tag(answers)


# ── multi-pain, no-pain, ordering, dedup ─────────────────────────


def test_multiple_pains_tagged_in_one_run():
    answers = _baseline_answers()
    answers = [a for a in answers if a.question_id not in {"q3.1", "q3.2", "q3.4"}]
    answers.extend(
        [
            _ans("q3.1", 20),  # obscurity (slider)
            _ans("q3.2", 20),  # commoditization (slider)
            _ans("q3.4", ["wrong_recognition"]),  # explicit selection
        ]
    )
    tagged = _tag(answers)
    assert {"obscurity", "commoditization", "wrong_recognition"} <= tagged


def test_no_rules_fire_for_baseline_answers():
    assert _tag(_baseline_answers()) == set()


def test_result_order_matches_taxonomy_canonical_order():
    answers = _baseline_answers()
    answers = [a for a in answers if a.question_id not in {"q3.1", "q3.2", "q3.4"}]
    # Trigger out of canonical order: confusion before obscurity in the trigger args.
    answers.extend(
        [
            _ans("q3.1", 20),  # obscurity (canonical index 0)
            _ans("q3.2", 20),  # commoditization (canonical index 1)
            _ans("q3.3", 20),  # confusion (canonical index 2)
            _ans("q3.4", []),
        ]
    )
    cats = tag_pain_categories(
        answers, _BUNDLE.simple_rules, _BUNDLE.inferred_rules, _BUNDLE.pain_taxonomy
    )
    canonical_ids = [c.id for c in _BUNDLE.pain_taxonomy.categories]
    result_indices = [canonical_ids.index(c.id) for c in cats]
    assert result_indices == sorted(result_indices)


def test_category_dedup_when_triggered_via_two_paths():
    """Obscurity is tagged by Q3.1 < 40 AND by explicit Q3.4 selection.
    Both fire; result lists obscurity exactly once."""
    answers = _baseline_answers()
    answers = [a for a in answers if a.question_id not in {"q3.1", "q3.4"}]
    answers.extend(
        [
            _ans("q3.1", 20),
            _ans("q3.4", ["obscurity"]),
        ]
    )
    cats = tag_pain_categories(
        answers, _BUNDLE.simple_rules, _BUNDLE.inferred_rules, _BUNDLE.pain_taxonomy
    )
    obscurity_count = sum(1 for c in cats if c.id == "obscurity")
    assert obscurity_count == 1


def test_returns_pain_category_objects_not_ids():
    answers = _baseline_answers()
    answers = [a for a in answers if a.question_id != "q3.1"]
    answers.append(_ans("q3.1", 20))
    cats = tag_pain_categories(
        answers, _BUNDLE.simple_rules, _BUNDLE.inferred_rules, _BUNDLE.pain_taxonomy
    )
    assert cats
    cat = cats[0]
    assert hasattr(cat, "id")
    assert hasattr(cat, "name_by_language")
    assert hasattr(cat, "description_by_language")
