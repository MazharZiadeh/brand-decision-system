"""Register Resolver tests against the real loaded register rules."""

from __future__ import annotations

import uuid

from src.discovery.loader import load_content_bundle
from src.discovery.register_resolver import resolve_register
from src.domain.language import Language
from src.domain.questionnaire import Answer
from src.domain.register import ArabicVariety, LanguageRegister, RegisterLevel

_BUNDLE = load_content_bundle()


def _ans(question_id: str, value):
    return Answer(question_id=question_id, value=value, language=Language.ENGLISH)


def _resolve(answers: list[Answer]) -> LanguageRegister:
    return resolve_register(answers, _BUNDLE.register_rules, uuid.uuid4())


def _baseline() -> list[Answer]:
    """A balanced answer set — used as a starting point each test mutates."""
    return [
        _ans("q1.3", "specialist"),
        _ans("q1.4", 50),  # heritage/vision balanced
        _ans("q2.5", "bilingual"),
        _ans("q4.1", 50),  # formality semi
        _ans("q4.2", 50),  # warmth balanced
    ]


# ── primary_language ─────────────────────────────────────────────


def test_arabic_only_audience_yields_arabic_primary():
    answers = _baseline()
    answers = [a for a in answers if a.question_id != "q2.5"]
    answers.append(_ans("q2.5", "arabic_only"))
    assert _resolve(answers).primary_language == Language.ARABIC


def test_english_only_audience_yields_english_primary():
    answers = _baseline()
    answers = [a for a in answers if a.question_id != "q2.5"]
    answers.append(_ans("q2.5", "english_only"))
    assert _resolve(answers).primary_language == Language.ENGLISH


def test_bilingual_falls_to_arabic_per_saudi_market_tiebreaker():
    answers = _baseline()  # already bilingual
    assert _resolve(answers).primary_language == Language.ARABIC


# ── arabic_variety ───────────────────────────────────────────────


def test_arabic_only_with_high_formality_yields_msa():
    answers = _baseline()
    answers = [a for a in answers if a.question_id not in {"q2.5", "q4.1"}]
    answers.extend([_ans("q2.5", "arabic_only"), _ans("q4.1", 80)])
    assert _resolve(answers).arabic_variety == ArabicVariety.MSA


def test_arabic_primary_with_low_formality_yields_saudi_dialect():
    answers = _baseline()
    answers = [a for a in answers if a.question_id not in {"q2.5", "q4.1"}]
    answers.extend([_ans("q2.5", "arabic_primary"), _ans("q4.1", 20)])
    assert _resolve(answers).arabic_variety == ArabicVariety.SAUDI_DIALECT


def test_english_only_yields_not_applicable_arabic_variety():
    answers = _baseline()
    answers = [a for a in answers if a.question_id != "q2.5"]
    answers.append(_ans("q2.5", "english_only"))
    assert _resolve(answers).arabic_variety == ArabicVariety.NOT_APPLICABLE


def test_default_arabic_variety_is_msa_when_no_condition_matches():
    """Bilingual + mid-formality (40-70) hits no arabic_variety condition;
    the YAML's default is `msa`."""
    answers = _baseline()  # bilingual + q4.1=50
    assert _resolve(answers).arabic_variety == ArabicVariety.MSA


# ── register_level ───────────────────────────────────────────────


def test_high_formality_yields_formal_level():
    answers = _baseline()
    answers = [a for a in answers if a.question_id != "q4.1"]
    answers.append(_ans("q4.1", 90))
    assert _resolve(answers).register_level == RegisterLevel.FORMAL


def test_low_formality_yields_casual_level():
    answers = _baseline()
    answers = [a for a in answers if a.question_id != "q4.1"]
    answers.append(_ans("q4.1", 20))
    assert _resolve(answers).register_level == RegisterLevel.CASUAL


def test_mid_formality_yields_semi_formal_level():
    answers = _baseline()  # q4.1=50
    assert _resolve(answers).register_level == RegisterLevel.SEMI_FORMAL


# ── cultural_anchors ─────────────────────────────────────────────


def test_saudi_market_context_anchor_is_always_present():
    register = _resolve(_baseline())
    assert "saudi_market_context" in register.cultural_anchors


def test_heritage_leaning_brand_adds_heritage_anchors():
    answers = _baseline()
    answers = [a for a in answers if a.question_id != "q1.4"]
    answers.append(_ans("q1.4", 20))  # heritage-leaning
    anchors = _resolve(answers).cultural_anchors
    assert "heritage_oriented" in anchors
    assert "respect_for_tradition" in anchors


def test_vision_leaning_brand_adds_vision_anchors():
    answers = _baseline()
    answers = [a for a in answers if a.question_id != "q1.4"]
    answers.append(_ans("q1.4", 80))
    anchors = _resolve(answers).cultural_anchors
    assert "innovation_oriented" in anchors
    assert "vision_2030_aligned" in anchors


def test_premium_position_adds_premium_anchor():
    answers = _baseline()
    answers = [a for a in answers if a.question_id != "q1.3"]
    answers.append(_ans("q1.3", "premium"))
    assert "premium_positioning" in _resolve(answers).cultural_anchors


def test_high_warmth_adds_warmth_anchor():
    answers = _baseline()
    answers = [a for a in answers if a.question_id != "q4.2"]
    answers.append(_ans("q4.2", 80))
    assert "warmth_culturally_appropriate" in _resolve(answers).cultural_anchors


# ── output shape ─────────────────────────────────────────────────


def test_returns_well_formed_language_register():
    sid = uuid.uuid4()
    register = resolve_register(_baseline(), _BUNDLE.register_rules, sid)
    assert isinstance(register, LanguageRegister)
    assert register.session_id == sid
    assert register.primary_language in {Language.ARABIC, Language.ENGLISH}
    assert isinstance(register.arabic_variety, ArabicVariety)
    assert isinstance(register.register_level, RegisterLevel)
    assert isinstance(register.cultural_anchors, list)
