"""Render-time tests for the prompt templates.

Renders each .j2 with synthetic context in both English and Arabic and
asserts the rendered output contains the markers we expect — system role
declaration, brand name, schema directive, language register block.
This guards against template parse errors and against silent variable
typos that would otherwise only fail at runtime in Session 7's prompt
builder.
"""

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined

PROMPTS_ROOT = Path(__file__).resolve().parents[3] / "content" / "prompts"


@pytest.fixture(scope="module")
def env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(PROMPTS_ROOT)),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
    )


def _synthetic_context(language: str = "en") -> dict:
    """Minimal-but-complete context covering every variable the templates use."""
    is_ar = language == "ar"
    return {
        "brand": {
            "name": "TestBrand",
            "description": "An MVP brand used to render templates in tests.",
            "stage": "early",
            "position": "premium",
            "heritage_vs_vision_band": "balanced",
            "heritage_vs_vision_score": 50,
        },
        "audience": {
            "description": "Saudi professionals 30-45 who choose by quality first.",
            "age_band": "middle",
            "spend_band": "aspirational",
            "decision_band": "mixed",
            "language_preference": "arabic_primary" if is_ar else "english_primary",
        },
        "pain": {
            "tagged_categories": [
                {
                    "id": "obscurity",
                    "name": "Obscurity" if not is_ar else "الغموض",
                    "description": "Brand awareness gap.",
                },
                {
                    "id": "commoditization",
                    "name": "Commoditization" if not is_ar else "التنميط",
                    "description": "Perceived sameness with peers.",
                },
            ],
            "narrative": "The brand has clarity internally but is invisible to its target buyer.",
            "top_frustrations": ["obscurity", "commoditization"],
        },
        "voice": {
            "formality_band": "semi_formal",
            "warmth_band": "warm",
            "confidence_band": "balanced",
            "energy_band": "balanced",
            "characters": ["confident_peer", "trusted_guide"],
        },
        "aspiration": {
            "posture_band": "balanced",
            "three_year": "category_leader",
            "emotion_target": "trust",
            "brand_premise": "We exist to build quietly excellent things our customers can trust.",
        },
        "register": {
            "primary_language": language,
            "arabic_variety": "msa" if is_ar else "not_applicable",
            "register_level": "semi_formal",
            "cultural_anchors": ["saudi_market_context", "premium_positioning"],
        },
        "upstream": {},
    }


# ── unified preamble ─────────────────────────────────────────────────


def test_unified_preamble_renders_english(env: Environment):
    rendered = env.get_template("unified_preamble.j2").render(**_synthetic_context("en"))
    assert "Brand DNA" in rendered
    assert "TestBrand" in rendered
    assert "Saudi market" in rendered
    assert "Language Register Directive" in rendered
    assert "Primary language: English" in rendered


def test_unified_preamble_renders_arabic(env: Environment):
    rendered = env.get_template("unified_preamble.j2").render(**_synthetic_context("ar"))
    assert "TestBrand" in rendered
    assert "الحمض النووي للعلامة" in rendered
    assert "اللغة الأساسية: العربية" in rendered
    assert "العربية الفصحى الحديثة" in rendered  # arabic_variety msa


# ── strategy_theme ───────────────────────────────────────────────────


def test_strategy_theme_renders_english(env: Environment):
    rendered = env.get_template("modules/strategy_theme.j2").render(**_synthetic_context("en"))
    assert "MODULE TASK: STRATEGY THEME" in rendered
    assert "PRIORITY HIERARCHY" in rendered
    assert "OUTPUT SCHEMA" in rendered
    assert "priority_factors_addressed" in rendered
    assert "TestBrand" in rendered  # preamble flowed through


def test_strategy_theme_renders_arabic(env: Environment):
    rendered = env.get_template("modules/strategy_theme.j2").render(**_synthetic_context("ar"))
    assert "موضوع الاستراتيجية" in rendered
    assert "priority_factors_addressed" in rendered
    assert "TestBrand" in rendered


# ── tone ─────────────────────────────────────────────────────────────


def test_tone_renders_english(env: Environment):
    rendered = env.get_template("modules/tone.j2").render(**_synthetic_context("en"))
    assert "MODULE TASK: TONE" in rendered
    assert "do_examples" in rendered
    assert "dont_examples" in rendered
    assert "arabic_note" in rendered


def test_tone_renders_arabic_with_upstream_strategy(env: Environment):
    ctx = _synthetic_context("ar")
    ctx["upstream"] = {
        "strategy_theme": {
            "theme": "حِرفية معاصرة لجيل سعودي يطلب الجودة دون فخامة متكلَّفة.",
        }
    }
    rendered = env.get_template("modules/tone.j2").render(**ctx)
    assert "نبرة العلامة" in rendered
    assert "حِرفية معاصرة" in rendered  # upstream theme flowed through


# ── naming ───────────────────────────────────────────────────────────


def test_naming_renders_english(env: Environment):
    rendered = env.get_template("modules/naming.j2").render(**_synthetic_context("en"))
    assert "MODULE TASK: NAMING" in rendered
    assert "candidates" in rendered
    assert "arabic_form" in rendered


def test_naming_renders_arabic_with_mature_brand_note(env: Environment):
    ctx = _synthetic_context("ar")
    ctx["brand"]["stage"] = "mature"
    rendered = env.get_template("modules/naming.j2").render(**ctx)
    assert "التسمية" in rendered
    # mature brand note: candidates are for sub-brands, not full rename
    assert "العلامات الفرعية" in rendered or "إعادة تسمية كاملة" in rendered


# ── slogan ───────────────────────────────────────────────────────────


def test_slogan_renders_english(env: Environment):
    rendered = env.get_template("modules/slogan.j2").render(**_synthetic_context("en"))
    assert "MODULE TASK: SLOGAN" in rendered
    assert "INTERNAL" in rendered
    assert "DO NOT duplicate" in rendered
    assert "options" in rendered


def test_slogan_renders_arabic(env: Environment):
    rendered = env.get_template("modules/slogan.j2").render(**_synthetic_context("ar"))
    assert "الشعار الداخلي" in rendered
    assert "options" in rendered


# ── tagline ──────────────────────────────────────────────────────────


def test_tagline_renders_english(env: Environment):
    rendered = env.get_template("modules/tagline.j2").render(**_synthetic_context("en"))
    assert "MODULE TASK: TAGLINE" in rendered
    assert "intended_feeling" in rendered
    assert "trust" in rendered  # the synthetic emotion_target


def test_tagline_renders_arabic_with_full_upstream_chain(env: Environment):
    ctx = _synthetic_context("ar")
    ctx["upstream"] = {
        "strategy_theme": {"theme": "حِرفية معاصرة."},
        "tone": {"descriptor": "واثق، دافئ، متأنٍّ."},
        "slogan": {
            "options": [
                {"slogan": "ابنِ بهدوء.", "rationale": "…"},
            ]
        },
    }
    rendered = env.get_template("modules/tagline.j2").render(**ctx)
    assert "الشعار التسويقي" in rendered
    # all three upstream blocks should appear
    assert "حِرفية معاصرة" in rendered
    assert "واثق، دافئ" in rendered
    assert "ابنِ بهدوء" in rendered
