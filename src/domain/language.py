from enum import StrEnum

from pydantic import BaseModel


# IMPORTANT: Language is a StrEnum and prompt templates rely on this.
# Jinja2 attribute access in templates uses patterns like
# `{{ obj.name_by_language.ar }}`, which works because Language.ARABIC.value
# == "ar" — StrEnum values ARE strings, so dicts keyed by Language enum
# members can be accessed by their string value via Jinja2's attribute lookup.
# If Language is ever refactored to a non-StrEnum, every prompt template
# breaks silently. Templates affected: content/prompts/unified_preamble.j2,
# content/prompts/pain_narrative.j2, and all module templates under
# content/prompts/modules/.
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
