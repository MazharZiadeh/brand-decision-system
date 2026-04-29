"""Pain Narrative Generator unit tests with the Mock LLM provider."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from src.discovery.exceptions import DiscoveryError
from src.discovery.narrative_generator import generate_pain_narrative
from src.domain.language import Language
from src.domain.narrative_output import PainNarrativeOutput
from src.domain.pain import PainAnalysis, PainCategory
from src.domain.rationale import PriorityFactor
from src.domain.register import ArabicVariety, LanguageRegister, RegisterLevel
from src.llm.mock import MockLLMProvider


def _category(cid: str = "obscurity") -> PainCategory:
    return PainCategory(
        id=cid,
        name_by_language={Language.ENGLISH: cid.title(), Language.ARABIC: cid},
        description_by_language={
            Language.ENGLISH: f"{cid} description",
            Language.ARABIC: f"وصف {cid}",
        },
    )


def _register(
    primary: Language = Language.ENGLISH,
    *,
    session_id: uuid.UUID | None = None,
) -> LanguageRegister:
    return LanguageRegister(
        session_id=session_id or uuid.uuid4(),
        primary_language=primary,
        arabic_variety=(
            ArabicVariety.MSA if primary == Language.ARABIC else ArabicVariety.NOT_APPLICABLE
        ),
        register_level=RegisterLevel.SEMI_FORMAL,
        cultural_anchors=["saudi_market_context"],
        derived_at=datetime.now(UTC),
    )


def _brand_dna_context() -> dict:
    return {
        "brand": {
            "name": "TestBrand",
            "description": "Test brand description.",
            "stage": "early",
            "position": "premium",
            "heritage_vs_vision_band": "balanced",
        },
        "audience": {
            "description": "Saudi professionals 30-45.",
            "age_band": "middle",
            "spend_band": "aspirational",
            "decision_band": "mixed",
            "language_preference": "english_primary",
        },
        "voice": {
            "formality_band": "semi_formal",
            "warmth_band": "warm",
            "confidence_band": "balanced",
            "energy_band": "balanced",
        },
        "aspiration": {
            "posture_band": "balanced",
            "three_year": "category_leader",
            "emotion_target": "trust",
        },
        "top_frustrations": ["obscurity"],
    }


def _narrative_response(language: Language = Language.ENGLISH) -> PainNarrativeOutput:
    return PainNarrativeOutput(
        language=language,
        narrative=(
            "The brand is invisible to its target audience despite holding a premium position — "
            "a familiar early-stage trap for ambition that runs ahead of recognition."
        ),
        priority_factors_addressed=[
            PriorityFactor(factor_name="pain_alignment", how_addressed="…"),
            PriorityFactor(factor_name="position_fit", how_addressed="…"),
        ],
    )


# ── happy path + audit invariants ──────────────────────────────────


async def test_generate_pain_narrative_returns_well_formed_pain_analysis():
    provider = MockLLMProvider()
    provider.register_response("PainNarrativeOutput", _narrative_response())
    sid = uuid.uuid4()
    register = _register(session_id=sid)

    pain_analysis, call_record = await generate_pain_narrative(
        _brand_dna_context(),
        [_category("obscurity")],
        register,
        sid,
        provider,
    )

    assert isinstance(pain_analysis, PainAnalysis)
    assert pain_analysis.session_id == sid
    assert pain_analysis.tagged_pain_categories == ["obscurity"]
    assert "invisible" in pain_analysis.narrative.lower()


async def test_pain_analysis_carries_register_id():
    provider = MockLLMProvider()
    provider.register_response("PainNarrativeOutput", _narrative_response())
    sid = uuid.uuid4()
    register = _register(session_id=sid)

    pain_analysis, _ = await generate_pain_narrative(
        _brand_dna_context(), [_category()], register, sid, provider
    )
    assert pain_analysis.register_id == register.id


async def test_pain_analysis_carries_llm_call_record_id():
    provider = MockLLMProvider()
    provider.register_response("PainNarrativeOutput", _narrative_response())
    sid = uuid.uuid4()
    register = _register(session_id=sid)

    pain_analysis, call_record = await generate_pain_narrative(
        _brand_dna_context(), [_category()], register, sid, provider
    )
    assert pain_analysis.llm_call_record_ids == [call_record.id]


async def test_pain_analysis_language_matches_register_primary_language_arabic():
    provider = MockLLMProvider()
    provider.register_response("PainNarrativeOutput", _narrative_response(language=Language.ARABIC))
    sid = uuid.uuid4()
    register = _register(primary=Language.ARABIC, session_id=sid)

    pain_analysis, _ = await generate_pain_narrative(
        _brand_dna_context(), [_category()], register, sid, provider
    )
    assert pain_analysis.language == Language.ARABIC


async def test_call_record_session_id_and_register_id_propagate():
    provider = MockLLMProvider()
    provider.register_response("PainNarrativeOutput", _narrative_response())
    sid = uuid.uuid4()
    register = _register(session_id=sid)

    _, call_record = await generate_pain_narrative(
        _brand_dna_context(), [_category()], register, sid, provider
    )
    assert call_record.session_id == sid
    assert call_record.register_id == register.id
    assert call_record.module is None  # narrative is not a module


# ── failure / pre-condition tests ─────────────────────────────────


async def test_no_tagged_pains_raises_and_does_not_call_llm():
    provider = MockLLMProvider()
    sid = uuid.uuid4()
    register = _register(session_id=sid)

    with pytest.raises(DiscoveryError):
        await generate_pain_narrative(_brand_dna_context(), [], register, sid, provider)
    assert provider.call_count == 0


async def test_mock_called_exactly_once_per_invocation():
    provider = MockLLMProvider()
    provider.register_response("PainNarrativeOutput", _narrative_response())
    sid = uuid.uuid4()
    register = _register(session_id=sid)

    await generate_pain_narrative(_brand_dna_context(), [_category()], register, sid, provider)
    assert provider.call_count == 1
