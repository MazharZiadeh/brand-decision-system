import uuid

import pytest
from pydantic import ValidationError

from src.domain.language import Language
from src.domain.pain import (
    PainAnalysis,
    PainCategory,
    PainTaxonomy,
    Rule,
    RuleTrigger,
)


def _category() -> PainCategory:
    return PainCategory(
        id="obscurity",
        name_by_language={Language.ENGLISH: "Obscurity", Language.ARABIC: "غموض"},
        description_by_language={
            Language.ENGLISH: "The brand is not known to its target audience.",
            Language.ARABIC: "العلامة غير معروفة لجمهورها المستهدف.",
        },
    )


def test_pain_category_is_frozen():
    c = _category()
    with pytest.raises(ValidationError):
        c.id = "other"  # type: ignore[misc]


def test_pain_taxonomy_is_frozen():
    t = PainTaxonomy(version="1.0.0", categories=[_category()])
    with pytest.raises(ValidationError):
        t.version = "2.0.0"  # type: ignore[misc]


def test_rule_trigger_is_frozen():
    rt = RuleTrigger(question_id="q3.1", operator="less_than", value=40)
    with pytest.raises(ValidationError):
        rt.value = 50  # type: ignore[misc]


def test_rule_is_frozen():
    r = Rule(
        id="r1",
        pain_category_id="obscurity",
        trigger=RuleTrigger(question_id="q3.1", operator="less_than", value=40),
    )
    with pytest.raises(ValidationError):
        r.id = "r2"  # type: ignore[misc]


def test_pain_analysis_requires_language():
    with pytest.raises(ValidationError):
        PainAnalysis(  # type: ignore[call-arg]
            session_id=uuid.uuid4(),
            tagged_pain_categories=["obscurity"],
            register_id=uuid.uuid4(),
            narrative="The brand is invisible.",
            rationale_id=uuid.uuid4(),
            llm_call_record_ids=[uuid.uuid4()],
        )


def test_pain_analysis_requires_register_id():
    with pytest.raises(ValidationError):
        PainAnalysis(  # type: ignore[call-arg]
            session_id=uuid.uuid4(),
            tagged_pain_categories=["obscurity"],
            narrative="The brand is invisible.",
            language=Language.ENGLISH,
            rationale_id=uuid.uuid4(),
            llm_call_record_ids=[uuid.uuid4()],
        )


def test_pain_analysis_requires_at_least_one_llm_call_record():
    with pytest.raises(ValidationError):
        PainAnalysis(
            session_id=uuid.uuid4(),
            tagged_pain_categories=["obscurity"],
            register_id=uuid.uuid4(),
            narrative="The brand is invisible.",
            language=Language.ENGLISH,
            rationale_id=uuid.uuid4(),
            llm_call_record_ids=[],
        )


def test_valid_pain_analysis():
    pa = PainAnalysis(
        session_id=uuid.uuid4(),
        tagged_pain_categories=["obscurity", "stagnation"],
        register_id=uuid.uuid4(),
        narrative="The brand has lost momentum and visibility.",
        language=Language.ENGLISH,
        rationale_id=uuid.uuid4(),
        llm_call_record_ids=[uuid.uuid4()],
    )
    assert pa.language == Language.ENGLISH
    assert "obscurity" in pa.tagged_pain_categories
    assert len(pa.llm_call_record_ids) == 1
