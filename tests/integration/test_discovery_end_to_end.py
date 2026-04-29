"""End-to-end Discovery flow with the Mock LLM provider.

Wires all four Discovery components — loader → rules engine → register
resolver → narrative generator — and verifies the audit chain stays
intact across the seam from deterministic logic into the LLM call.
The test does not touch the database (persistence is Session 8's
concern); it is marked `integration` because it loads the real content
tree and renders the real Jinja2 prompt template.
"""

from __future__ import annotations

import uuid

import pytest

from src.discovery import (
    load_content_bundle,
    resolve_register,
    tag_pain_categories,
)
from src.domain.brand_dna_context import build_brand_dna_context
from src.domain.language import Language
from src.domain.narrative_output import PainNarrativeOutput
from src.domain.questionnaire import Answer
from src.domain.rationale import PriorityFactor
from src.generation import generate_pain_narrative
from src.llm.mock import MockLLMProvider

pytestmark = pytest.mark.integration


def _ans(question_id: str, value):
    return Answer(question_id=question_id, value=value, language=Language.ENGLISH)


def _fixture_answers_for_invisible_premium_brand() -> list[Answer]:
    """A brand owner whose answers should yield obscurity + commoditization
    pains and an English-primary register (their audience is english_primary,
    formality is mid)."""
    return [
        _ans("q1.1", "TestBrand. We make premium professional bags."),
        _ans("q1.2", "early"),
        _ans("q1.3", "premium"),
        _ans("q1.4", 50),
        _ans("q2.1", "Saudi professionals 30-45 who want quality without theatre."),
        _ans("q2.2", 50),
        _ans("q2.3", 70),
        _ans("q2.4", 60),
        _ans("q2.5", "english_primary"),
        _ans("q3.1", 20),  # invisible (slider rule fires → obscurity)
        _ans("q3.2", 25),  # blends in (slider rule fires → commoditization)
        _ans("q3.3", 60),
        _ans("q3.4", ["obscurity", "commoditization"]),  # explicit selections too
        _ans("q4.1", 50),
        _ans("q4.2", 50),
        _ans("q4.3", 50),
        _ans("q4.4", 50),
        _ans("q4.5", ["confident_peer", "respected_expert"]),
        _ans("q5.1", 60),
        _ans("q5.2", "category_leader"),
        _ans("q5.3", "trust"),
    ]


async def test_full_discovery_flow_with_mock_provider():
    # 1. Load real content
    bundle = load_content_bundle()
    assert bundle.questionnaire_en.version == "0.1.0"

    # 2. Build fixture answers
    answers = _fixture_answers_for_invisible_premium_brand()

    # 3. Run the rules engine
    pain_categories = tag_pain_categories(
        answers,
        bundle.simple_rules,
        bundle.inferred_rules,
        bundle.pain_taxonomy,
    )
    assert len(pain_categories) >= 2
    tagged_ids = {c.id for c in pain_categories}
    assert "obscurity" in tagged_ids
    assert "commoditization" in tagged_ids

    # 4. Run the register resolver
    session_id = uuid.uuid4()
    register = resolve_register(answers, bundle.register_rules, session_id)
    assert register.session_id == session_id
    assert register.primary_language == Language.ENGLISH  # english_primary audience

    # 5. Build the typed brand DNA context (the canonical helper from src.domain)
    brand_dna_context = build_brand_dna_context(answers, bundle.questionnaire_en)

    # 6. Configure the Mock and run the narrative generator
    mock = MockLLMProvider()
    mock.register_response(
        "PainNarrativeOutput",
        PainNarrativeOutput(
            language=register.primary_language,
            narrative=(
                "TestBrand has earned the right shelf placement on quality "
                "but still hits sales calls cold — premium positioning is "
                "running ahead of recognition, and the market reads us as "
                "another option in the category rather than a specific bet."
            ),
            priority_factors_addressed=[
                PriorityFactor(factor_name="pain_alignment", how_addressed="…"),
                PriorityFactor(factor_name="position_fit", how_addressed="…"),
            ],
        ),
    )

    pain_analysis, call_record = await generate_pain_narrative(
        brand_dna_context, pain_categories, register, session_id, mock
    )

    # 7. End-to-end audit invariants
    assert pain_analysis.session_id == session_id
    assert pain_analysis.register_id == register.id
    assert pain_analysis.language == register.primary_language
    assert len(pain_analysis.llm_call_record_ids) == 1
    assert pain_analysis.llm_call_record_ids[0] == call_record.id
    assert call_record.session_id == session_id
    assert call_record.register_id == register.id
    assert call_record.module is None  # narrative is not a module
    assert call_record.language_directive == register.primary_language
    assert mock.call_count == 1
    assert set(pain_analysis.tagged_pain_categories) == tagged_ids
