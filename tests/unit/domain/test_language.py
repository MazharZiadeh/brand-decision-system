import pytest
from pydantic import ValidationError

from src.domain.language import Language, LanguageTagged


def test_language_values():
    assert Language.ARABIC.value == "ar"
    assert Language.ENGLISH.value == "en"


def test_language_tagged_requires_language():
    with pytest.raises(ValidationError):
        LanguageTagged()  # type: ignore[call-arg]


def test_language_tagged_accepts_valid_language():
    tagged = LanguageTagged(language=Language.ARABIC)
    assert tagged.language == Language.ARABIC


def test_language_tagged_rejects_unknown_language():
    with pytest.raises(ValidationError):
        LanguageTagged(language="fr")  # type: ignore[arg-type]
