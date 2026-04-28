import uuid

import pytest
from pydantic import ValidationError

from src.domain.language import Language
from src.domain.register import ArabicVariety, LanguageRegister, RegisterLevel


def test_arabic_variety_includes_not_applicable():
    assert {v.value for v in ArabicVariety} == {"msa", "saudi_dialect", "not_applicable"}


def test_register_level_values():
    assert {r.value for r in RegisterLevel} == {"formal", "semi_formal", "casual"}


def test_valid_register_arabic_msa_formal():
    lr = LanguageRegister(
        session_id=uuid.uuid4(),
        primary_language=Language.ARABIC,
        arabic_variety=ArabicVariety.MSA,
        register_level=RegisterLevel.FORMAL,
        cultural_anchors=["hospitality", "craftsmanship"],
    )
    assert lr.primary_language == Language.ARABIC
    assert lr.cultural_anchors == ["hospitality", "craftsmanship"]


def test_english_register_uses_not_applicable_for_arabic_variety():
    lr = LanguageRegister(
        session_id=uuid.uuid4(),
        primary_language=Language.ENGLISH,
        arabic_variety=ArabicVariety.NOT_APPLICABLE,
        register_level=RegisterLevel.SEMI_FORMAL,
    )
    assert lr.arabic_variety == ArabicVariety.NOT_APPLICABLE


def test_register_requires_session_id():
    with pytest.raises(ValidationError):
        LanguageRegister(  # type: ignore[call-arg]
            primary_language=Language.ENGLISH,
            arabic_variety=ArabicVariety.NOT_APPLICABLE,
            register_level=RegisterLevel.FORMAL,
        )
