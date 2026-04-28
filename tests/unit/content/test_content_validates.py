"""Schema validation for the v0.1 content layer.

Every YAML must round-trip into the corresponding Pydantic domain model
(or, for the resolver rules, into a structurally-validated dict). If any
file drifts away from the schema the loader will assume, this test fails
loud at CI time — not silently at app start.
"""

from pathlib import Path

import yaml

from src.domain.pain import PainTaxonomy, Rule
from src.domain.questionnaire import AnswerMechanic, QuestionnaireVersion

CONTENT_ROOT = Path(__file__).resolve().parents[3] / "content"


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_questionnaire_en_validates():
    data = _load_yaml(CONTENT_ROOT / "questionnaires" / "v0.1.0" / "questionnaire.en.yaml")
    version = QuestionnaireVersion(**data)
    assert version.version == "0.1.0"
    assert len(version.questions) == 22
    q11 = next(q for q in version.questions if q.id == "q1.1")
    assert q11.mechanic == AnswerMechanic.FREE_TEXT
    assert q11.free_text_max_length == 200
    q14 = next(q for q in version.questions if q.id == "q1.4")
    assert q14.mechanic == AnswerMechanic.SLIDER
    assert q14.slider_config is not None
    # SLIDER carries no constraint fields.
    assert q14.min_selections is None
    assert q14.max_selections is None
    assert q14.free_text_max_length is None
    q34 = next(q for q in version.questions if q.id == "q3.4")
    assert q34.mechanic == AnswerMechanic.MULTI_CHOICE
    assert q34.options is not None
    assert len(q34.options) == 10
    assert q34.min_selections == 1
    assert q34.max_selections == 3
    q54 = next(q for q in version.questions if q.id == "q5.4")
    assert q54.mechanic == AnswerMechanic.FREE_TEXT
    assert q54.free_text_max_length == 500
    assert q54.required is False


def test_questionnaire_ar_validates():
    data = _load_yaml(CONTENT_ROOT / "questionnaires" / "v0.1.0" / "questionnaire.ar.yaml")
    version = QuestionnaireVersion(**data)
    assert version.version == "0.1.0"
    assert len(version.questions) == 22


def test_pain_taxonomy_validates():
    data = _load_yaml(CONTENT_ROOT / "pain_taxonomy.yaml")
    taxonomy = PainTaxonomy(**data)
    assert len(taxonomy.categories) == 10
    ids = {c.id for c in taxonomy.categories}
    expected = {
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
    }
    assert (
        ids == expected
    ), f"Pain category set drift: missing {expected - ids}, extra {ids - expected}"


def test_pain_rules_yaml_is_well_formed():
    data = _load_yaml(CONTENT_ROOT / "pain_rules.yaml")
    assert "rules" in data
    assert len(data["rules"]) >= 13
    for rule_dict in data["rules"]:
        rule = Rule(**rule_dict)
        assert rule.id
        assert rule.pain_category_id
        assert rule.trigger.question_id


def test_pain_rules_inferred_section_present_for_future_evaluator():
    data = _load_yaml(CONTENT_ROOT / "pain_rules.yaml")
    assert "inferred_rules" in data, "Compound rules block missing"
    assert len(data["inferred_rules"]) >= 2
    for rule in data["inferred_rules"]:
        assert "id" in rule
        assert "pain_category_id" in rule
        assert "all_of" in rule["trigger"]


def test_register_rules_yaml_is_well_formed():
    data = _load_yaml(CONTENT_ROOT / "register_rules.yaml")
    assert "register_rules" in data
    rules = data["register_rules"]
    for key in ["primary_language", "arabic_variety", "register_level", "cultural_anchors"]:
        assert key in rules, f"Missing {key} in register rules"


def test_pain_rule_categories_match_taxonomy():
    """Every pain_category_id referenced by a rule must exist in the taxonomy."""
    rules_data = _load_yaml(CONTENT_ROOT / "pain_rules.yaml")
    taxonomy_data = _load_yaml(CONTENT_ROOT / "pain_taxonomy.yaml")
    taxonomy_ids = {c["id"] for c in taxonomy_data["categories"]}
    for rule in rules_data["rules"]:
        assert (
            rule["pain_category_id"] in taxonomy_ids
        ), f"Rule {rule['id']} references unknown pain category {rule['pain_category_id']}"
    for rule in rules_data["inferred_rules"]:
        assert rule["pain_category_id"] in taxonomy_ids
