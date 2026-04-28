from enum import StrEnum

from pydantic import BaseModel


class Language(StrEnum):
    """Supported content languages.

    Per CLAUDE.md §2.4, every persisted content object carries a non-null
    language tag. There is no global session language; each object declares
    the language it was authored or generated in.
    """

    ARABIC = "ar"
    ENGLISH = "en"


class LanguageTagged(BaseModel):
    """Mixin for content objects that must carry a language tag.

    Models that represent persisted content (Answer, PainAnalysis,
    ModuleOutput, Rationale) inherit from this and gain a required
    `language: Language` field.
    """

    language: Language
