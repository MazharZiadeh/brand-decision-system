"""Tests for BrandDNAContext, its sub-models, and the build helper."""

import pytest
from pydantic import ValidationError

from src.domain.brand_dna_context import (
    AspirationInfo,
    AudienceInfo,
    BrandDNAContext,
    BrandInfo,
    PainHints,
    VoiceInfo,
    _slider_band,
    _split_brand_name_and_description,
    build_brand_dna_context,
)
from src.domain.language import Language
from src.domain.questionnaire import Answer, QuestionnaireVersion


def _ans(question_id: str, value):
    return Answer(question_id=question_id, value=value, language=Language.ENGLISH)


def _full_answers() -> list[Answer]:
    return [
        _ans("q1.1", "TestBrand. We make premium leather goods."),
        _ans("q1.2", "growing"),
        _ans("q1.3", "premium"),
        _ans("q1.4", 50),
        _ans("q2.1", "Saudi professionals 30-45."),
        _ans("q2.2", 50),
        _ans("q2.3", 70),
        _ans("q2.4", 60),
        _ans("q2.5", "english_primary"),
        _ans("q3.4", ["obscurity"]),
        _ans("q4.1", 50),
        _ans("q4.2", 50),
        _ans("q4.3", 50),
        _ans("q4.4", 50),
        _ans("q4.5", ["confident_peer", "respected_expert"]),
        _ans("q5.1", 60),
        _ans("q5.2", "category_leader"),
        _ans("q5.3", "trust"),
    ]


def _empty_questionnaire() -> QuestionnaireVersion:
    return QuestionnaireVersion(version="0.1.0", content_hash="x", questions=[])


# ── model construction & frozen invariants ─────────────────────────


def test_brand_dna_context_validates_with_full_payload():
    ctx = BrandDNAContext(
        brand=BrandInfo(
            name="x",
            description="y",
            stage="early",
            position="premium",
            heritage_vs_vision_band="balanced",
            heritage_vs_vision_score=50,
        ),
        audience=AudienceInfo(
            description="…",
            age_band="middle",
            spend_band="aspirational",
            decision_band="mixed",
            language_preference="english_primary",
        ),
        voice=VoiceInfo(
            formality_band="semi_formal",
            warmth_band="warm",
            confidence_band="balanced",
            energy_band="balanced",
            characters=["confident_peer"],
        ),
        aspiration=AspirationInfo(
            posture_band="balanced",
            three_year="category_leader",
            emotion_target="trust",
            brand_premise="",
        ),
        pain=PainHints(top_frustrations=["obscurity"]),
    )
    assert ctx.brand.name == "x"


def test_brand_info_is_frozen():
    b = BrandInfo(
        name="x",
        description="y",
        stage="early",
        position="premium",
        heritage_vs_vision_band="balanced",
        heritage_vs_vision_score=50,
    )
    with pytest.raises(ValidationError):
        b.name = "z"  # type: ignore[misc]


def test_audience_info_is_frozen():
    a = AudienceInfo(
        description="…",
        age_band="middle",
        spend_band="aspirational",
        decision_band="mixed",
        language_preference="english_primary",
    )
    with pytest.raises(ValidationError):
        a.description = "x"  # type: ignore[misc]


def test_voice_info_is_frozen():
    v = VoiceInfo(
        formality_band="semi_formal",
        warmth_band="warm",
        confidence_band="balanced",
        energy_band="balanced",
        characters=["confident_peer"],
    )
    with pytest.raises(ValidationError):
        v.formality_band = "casual"  # type: ignore[misc]


def test_brand_info_score_must_be_in_range():
    with pytest.raises(ValidationError):
        BrandInfo(
            name="x",
            description="y",
            stage="early",
            position="premium",
            heritage_vs_vision_band="balanced",
            heritage_vs_vision_score=150,
        )
    with pytest.raises(ValidationError):
        BrandInfo(
            name="x",
            description="y",
            stage="early",
            position="premium",
            heritage_vs_vision_band="balanced",
            heritage_vs_vision_score=-1,
        )


def test_voice_info_characters_min_max_bounds():
    with pytest.raises(ValidationError):
        VoiceInfo(
            formality_band="semi_formal",
            warmth_band="warm",
            confidence_band="balanced",
            energy_band="balanced",
            characters=[],
        )
    with pytest.raises(ValidationError):
        VoiceInfo(
            formality_band="semi_formal",
            warmth_band="warm",
            confidence_band="balanced",
            energy_band="balanced",
            characters=["a", "b", "c"],
        )
    # 1 and 2 are both fine
    VoiceInfo(
        formality_band="semi_formal",
        warmth_band="warm",
        confidence_band="balanced",
        energy_band="balanced",
        characters=["a"],
    )
    VoiceInfo(
        formality_band="semi_formal",
        warmth_band="warm",
        confidence_band="balanced",
        energy_band="balanced",
        characters=["a", "b"],
    )


# ── _slider_band ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    "value,expected",
    [
        (0, "low"),
        (39, "low"),
        (40, "mid"),
        (50, "mid"),
        (60, "mid"),
        (61, "high"),
        (100, "high"),
    ],
)
def test_slider_band_boundaries(value, expected):
    assert _slider_band(value, "low", "mid", "high") == expected


# ── _split_brand_name_and_description ─────────────────────────────


def test_split_brand_name_with_period():
    name, desc = _split_brand_name_and_description("TestBrand. We make bags.")
    assert name == "TestBrand"
    assert desc == "We make bags."


def test_split_brand_name_without_period_returns_full_text():
    text = "Just one combined sentence with no period separator"
    name, desc = _split_brand_name_and_description(text)
    assert name == text
    assert desc == text


# ── build_brand_dna_context ───────────────────────────────────────


def test_build_brand_dna_context_succeeds_with_realistic_answers():
    ctx = build_brand_dna_context(_full_answers(), _empty_questionnaire())
    assert isinstance(ctx, BrandDNAContext)
    assert ctx.brand.name == "TestBrand"
    assert ctx.brand.description == "We make premium leather goods."
    assert ctx.brand.stage == "growing"
    assert ctx.brand.position == "premium"
    assert ctx.brand.heritage_vs_vision_score == 50
    assert ctx.audience.language_preference == "english_primary"
    assert ctx.voice.characters == ["confident_peer", "respected_expert"]
    assert ctx.aspiration.three_year == "category_leader"
    assert ctx.pain.top_frustrations == ["obscurity"]


def test_build_brand_dna_context_slider_bands_match_convention():
    """value < 40 → low; 40-60 inclusive → mid; > 60 → high."""
    answers = _full_answers()
    # Replace q1.4 (heritage/vision) and q4.1 (formality) to test the bands.
    answers = [a for a in answers if a.question_id not in {"q1.4", "q4.1"}]
    answers.extend([_ans("q1.4", 30), _ans("q4.1", 80)])
    ctx = build_brand_dna_context(answers, _empty_questionnaire())
    assert ctx.brand.heritage_vs_vision_band == "heritage"
    assert ctx.voice.formality_band == "formal"


def test_build_brand_dna_context_raises_on_missing_required_answer():
    answers = [a for a in _full_answers() if a.question_id != "q1.1"]
    with pytest.raises(ValueError, match="q1.1"):
        build_brand_dna_context(answers, _empty_questionnaire())


def test_build_brand_dna_context_handles_optional_brand_premise():
    # No q5.4 in answers — should yield empty brand_premise, not raise.
    answers = _full_answers()
    assert "q5.4" not in {a.question_id for a in answers}
    ctx = build_brand_dna_context(answers, _empty_questionnaire())
    assert ctx.aspiration.brand_premise == ""


def test_build_brand_dna_context_passes_through_multi_choice_lists():
    answers = _full_answers()
    answers = [a for a in answers if a.question_id != "q4.5"]
    answers.append(_ans("q4.5", ["wise_elder"]))
    ctx = build_brand_dna_context(answers, _empty_questionnaire())
    assert ctx.voice.characters == ["wise_elder"]


def test_build_brand_dna_context_q34_optional_yields_empty_top_frustrations():
    answers = [a for a in _full_answers() if a.question_id != "q3.4"]
    ctx = build_brand_dna_context(answers, _empty_questionnaire())
    assert ctx.pain.top_frustrations == []
