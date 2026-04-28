import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from src.domain.language import Language


class ArabicVariety(StrEnum):
    """Arabic varieties the resolver may select.

    NOT_APPLICABLE is used when the primary language is English; it keeps the
    field non-Optional so call sites do not need to handle None.
    """

    MSA = "msa"
    SAUDI_DIALECT = "saudi_dialect"
    NOT_APPLICABLE = "not_applicable"


class RegisterLevel(StrEnum):
    """Register level the resolver derives from the Brand DNA Profile."""

    FORMAL = "formal"
    SEMI_FORMAL = "semi_formal"
    CASUAL = "casual"


class LanguageRegister(BaseModel):
    """Per-session directive derived from the Brand DNA Profile.

    Per CLAUDE.md §2.5 this is computed by a deterministic resolver — operators
    do not configure it, modules do not override it. The model itself is not
    content-tagged: it specifies WHICH language to use, not content authored
    in a language.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    session_id: uuid.UUID
    primary_language: Language
    arabic_variety: ArabicVariety
    register_level: RegisterLevel
    cultural_anchors: list[str] = Field(default_factory=list)
    derived_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
