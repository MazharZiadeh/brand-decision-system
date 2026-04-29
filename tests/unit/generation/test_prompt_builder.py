"""Tests for the prompt builder."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from jinja2.exceptions import UndefinedError

from src.domain.brand_dna_context import (
    AspirationInfo,
    AudienceInfo,
    BrandDNAContext,
    BrandInfo,
    PainHints,
    VoiceInfo,
)
from src.domain.language import Language
from src.domain.module import ModuleId, ModuleOutput
from src.domain.pain import PainAnalysis, PainCategory
from src.domain.register import ArabicVariety, LanguageRegister, RegisterLevel
from src.generation.prompt_builder import build_module_prompt


def _ctx() -> BrandDNAContext:
    return BrandDNAContext(
        brand=BrandInfo(
            name="TestBrand",
            description="We make premium leather goods.",
            stage="early",
            position="premium",
            heritage_vs_vision_band="balanced",
            heritage_vs_vision_score=50,
        ),
        audience=AudienceInfo(
            description="Saudi professionals 30-45.",
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


def _category(cid: str) -> PainCategory:
    return PainCategory(
        id=cid,
        name_by_language={Language.ENGLISH: cid.title(), Language.ARABIC: cid},
        description_by_language={
            Language.ENGLISH: f"{cid} description",
            Language.ARABIC: f"وصف {cid}",
        },
    )


def _pain_analysis(session_id: uuid.UUID, register_id: uuid.UUID) -> PainAnalysis:
    return PainAnalysis(
        session_id=session_id,
        tagged_pain_categories=["obscurity"],
        register_id=register_id,
        narrative="The brand has clarity internally but is invisible externally.",
        rationale_id=uuid.uuid4(),
        llm_call_record_ids=[uuid.uuid4()],
        language=Language.ENGLISH,
    )


def _register(primary: Language = Language.ENGLISH) -> LanguageRegister:
    return LanguageRegister(
        session_id=uuid.uuid4(),
        primary_language=primary,
        arabic_variety=(
            ArabicVariety.MSA if primary == Language.ARABIC else ArabicVariety.NOT_APPLICABLE
        ),
        register_level=RegisterLevel.SEMI_FORMAL,
        cultural_anchors=["saudi_market_context", "premium_positioning"],
        derived_at=datetime.now(UTC),
    )


def _strategy_completed_output(session_id: uuid.UUID, register_id: uuid.UUID) -> ModuleOutput:
    return ModuleOutput(
        session_id=session_id,
        module=ModuleId.STRATEGY_THEME,
        language=Language.ENGLISH,
        register_id=register_id,
        content={
            "language": "en",
            "theme": "Quietly engineered for the Saudi professional who wants quality without theatre.",
            "elaboration": "…",
            "priority_factors_addressed": [
                {"factor_name": "x", "how_addressed": "y"},
                {"factor_name": "a", "how_addressed": "b"},
            ],
        },
        rationale_id=uuid.uuid4(),
        llm_call_record_ids=[uuid.uuid4()],
        upstream_module_outputs=[],
        created_at=datetime.now(UTC),
    )


# ── basic rendering ────────────────────────────────────────────────


def test_build_module_prompt_for_strategy_theme_renders_without_error():
    sid = uuid.uuid4()
    register = _register()
    rendered = build_module_prompt(
        ModuleId.STRATEGY_THEME,
        _ctx(),
        _pain_analysis(sid, register.id),
        [_category("obscurity")],
        register,
        completed_outputs={},
        scope_modules={ModuleId.STRATEGY_THEME},
    )
    assert rendered
    assert isinstance(rendered, str)
    assert len(rendered) > 200


def test_built_prompt_contains_brand_name():
    sid = uuid.uuid4()
    register = _register()
    rendered = build_module_prompt(
        ModuleId.STRATEGY_THEME,
        _ctx(),
        _pain_analysis(sid, register.id),
        [_category("obscurity")],
        register,
        completed_outputs={},
        scope_modules={ModuleId.STRATEGY_THEME},
    )
    assert "TestBrand" in rendered


def test_built_prompt_contains_pain_narrative():
    sid = uuid.uuid4()
    register = _register()
    rendered = build_module_prompt(
        ModuleId.STRATEGY_THEME,
        _ctx(),
        _pain_analysis(sid, register.id),
        [_category("obscurity")],
        register,
        completed_outputs={},
        scope_modules={ModuleId.STRATEGY_THEME},
    )
    assert "invisible externally" in rendered


def test_built_prompt_contains_register_directive():
    sid = uuid.uuid4()
    register = _register()
    rendered = build_module_prompt(
        ModuleId.STRATEGY_THEME,
        _ctx(),
        _pain_analysis(sid, register.id),
        [_category("obscurity")],
        register,
        completed_outputs={},
        scope_modules={ModuleId.STRATEGY_THEME},
    )
    assert "saudi_market_context" in rendered
    assert "premium_positioning" in rendered


def test_built_prompt_for_arabic_register_includes_arabic_directive():
    sid = uuid.uuid4()
    register = _register(primary=Language.ARABIC)
    rendered = build_module_prompt(
        ModuleId.STRATEGY_THEME,
        _ctx(),
        _pain_analysis(sid, register.id),
        [_category("obscurity")],
        register,
        completed_outputs={},
        scope_modules={ModuleId.STRATEGY_THEME},
    )
    # Arabic preamble + module directive land
    assert "العربية الفصحى الحديثة" in rendered  # MSA directive
    assert "موضوع الاستراتيجية" in rendered  # Arabic module title


# ── upstream wiring ────────────────────────────────────────────────


def test_built_prompt_for_tone_with_strategy_upstream_includes_strategy_theme_text():
    sid = uuid.uuid4()
    register = _register()
    completed = {
        ModuleId.STRATEGY_THEME: _strategy_completed_output(sid, register.id),
    }
    rendered = build_module_prompt(
        ModuleId.TONE,
        _ctx(),
        _pain_analysis(sid, register.id),
        [_category("obscurity")],
        register,
        completed_outputs=completed,
        scope_modules={ModuleId.STRATEGY_THEME, ModuleId.TONE},
    )
    assert "Quietly engineered for the Saudi professional" in rendered


def test_built_prompt_for_tone_without_strategy_upstream_omits_strategy_block():
    sid = uuid.uuid4()
    register = _register()
    rendered = build_module_prompt(
        ModuleId.TONE,
        _ctx(),
        _pain_analysis(sid, register.id),
        [_category("obscurity")],
        register,
        completed_outputs={},
        scope_modules={ModuleId.TONE},  # Strategy not in scope
    )
    assert "UPSTREAM: STRATEGY THEME" not in rendered


# ── strict undefined ───────────────────────────────────────────────


def test_built_prompt_strict_undefined_catches_missing_template_variable():
    """Construct a context with most variables missing — StrictUndefined
    must raise rather than render empty sections silently."""
    from jinja2 import Environment, FileSystemLoader, StrictUndefined

    from src.generation.prompt_builder import _PROMPT_DIR

    env = Environment(
        loader=FileSystemLoader(str(_PROMPT_DIR)),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
    )
    template = env.get_template("modules/strategy_theme.j2")
    with pytest.raises(UndefinedError):
        template.render(brand={"name": "x"})  # most fields missing
